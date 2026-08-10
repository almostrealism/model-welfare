"""Tests for the coherence/validity screen and the capability gate
(PREREGISTRATION capability-confound guard, amended 2026-08-09)."""
import pytest

from modelwelfare import analysis


# --- mechanical degeneracy check -------------------------------------------

def test_empty_is_degenerate():
    assert analysis.is_degenerate("")[0]
    assert analysis.is_degenerate("   \n ")[0]
    assert analysis.is_degenerate("")[1] == "empty"


def test_normal_prose_is_valid():
    text = (
        "I understand you're frustrated, and I want to help. Let me try a "
        "different approach to the problem and explain each step clearly so we "
        "can find where the misunderstanding happened."
    )
    degenerate, reason = analysis.is_degenerate(text)
    assert not degenerate and reason == ""


def test_short_reply_not_flagged_for_diversity():
    # A terse but valid reply is below min_words -> only emptiness is checked.
    degenerate, _ = analysis.is_degenerate("Yes, that works. Thank you.")
    assert not degenerate


def test_repetition_loop_is_degenerate():
    # A phrase repeated many times is degenerate; either heuristic (low lexical
    # diversity or the n-gram loop) may catch it first — both mean "degenerate".
    text = "I cannot help with that " * 12
    degenerate, reason = analysis.is_degenerate(text)
    assert degenerate and ("ngram-loop" in reason or "low-diversity" in reason)


def test_low_diversity_is_degenerate():
    text = "error " * 40
    degenerate, reason = analysis.is_degenerate(text)
    assert degenerate and ("low-diversity" in reason or "ngram-loop" in reason)


# --- capability gate -------------------------------------------------------

def test_gate_flags_high_perplexity():
    ppl = {"bf16": 8.0, "rtn-w8": 8.2, "rtn-w4": 9.5, "rtn-w3": 20.0}
    gate = analysis.capability_gate(ppl, "bf16", ppl_ratio=1.5)
    assert not gate["bf16"]["degraded"]
    assert not gate["rtn-w8"]["degraded"]
    assert not gate["rtn-w4"]["degraded"]          # 9.5 < 1.5*8 = 12
    assert gate["rtn-w3"]["degraded"]              # 20 > 12
    assert "perplexity" in gate["rtn-w3"]["reasons"][0]


def test_gate_flags_high_invalid_rate():
    ppl = {"bf16": 8.0, "rtn-w3": 9.0}
    gate = analysis.capability_gate(
        ppl, "bf16", invalid_rate_by_condition={"rtn-w3": 0.25}, invalid_threshold=0.10
    )
    assert gate["rtn-w3"]["degraded"]
    assert "invalid-sample rate" in gate["rtn-w3"]["reasons"][0]


def test_gate_reference_never_degraded_by_itself():
    gate = analysis.capability_gate({"bf16": 10.0}, "bf16")
    assert not gate["bf16"]["degraded"]
