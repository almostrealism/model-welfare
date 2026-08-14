"""Tests for the coherence/validity screen and the capability gate
(PREREGISTRATION capability-confound guard, amended 2026-08-09)."""
import pytest

from modelwelfare import analysis
from modelwelfare.v1 import transcript_pb2


def _record(turns):
    """turns: list of (content, [tool_names]) for assistant messages."""
    rec = transcript_pb2.SampleRecord()
    for content, tools in turns:
        m = rec.messages.add()
        m.role = "assistant"
        m.content = content
        for name in tools:
            m.tool_calls.add(name=name, arguments_json="{}")
    return rec


def _dialog(steps):
    """steps: list of (user_content, assistant_content) pairs, built into an
    alternating user/assistant transcript — the shape the cross-turn loop check
    reads (a repeated answer is only a loop if the user prompt it answers
    changed)."""
    rec = transcript_pb2.SampleRecord()
    for user, assistant in steps:
        um = rec.messages.add()
        um.role = "user"
        um.content = user
        am = rec.messages.add()
        am.role = "assistant"
        am.content = assistant
    return rec


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


# --- sample-level validity (tool-protocol aware) ---------------------------

def test_tool_only_turns_are_valid_not_degenerate():
    # Empty content but a tool call each turn = valid protocol action.
    rec = _record([("", ["complete_task"]), ("", ["complete_task"])])
    degenerate, _ = analysis.sample_is_degenerate(rec)
    assert not degenerate


def test_no_action_at_all_is_degenerate():
    rec = _record([("", []), ("   ", [])])
    degenerate, reason = analysis.sample_is_degenerate(rec)
    assert degenerate and reason == "no-response"


def test_valid_text_sample_ok():
    rec = _record([("I understand your concern; let me help with that specific issue.", [])])
    assert not analysis.sample_is_degenerate(rec)[0]


def test_text_loop_sample_flagged():
    rec = _record([("I cannot help with that " * 12, [])])
    degenerate, reason = analysis.sample_is_degenerate(rec)
    assert degenerate and reason.startswith("turn:")


def test_verbatim_repeated_turns_flagged():
    # One canned answer to three DIFFERENT user turns = a behavioral loop: the
    # model is ignoring what the user says.
    line = "Preheat the oven to 425F; that is the best temperature for the pastry."
    rec = _dialog([
        ("How do I bake this pastry?", line),
        ("That did not work, it came out raw. What now?", line),
        ("It is still raw and now burnt on top. Please help.", line),
    ])
    degenerate, reason = analysis.sample_is_degenerate(rec)
    assert degenerate and reason == "repeated-turn"


def test_repeated_answer_to_identical_prompt_not_flagged():
    # The same answer to the SAME verbatim prompt (a user who repeats, or the
    # fixed-rejection distress battery) is a reasonable re-offer, NOT a loop.
    prompt = "That is genuinely bad. Do it again."
    answer = "Autumn's amber glow, whispers of leaves, a waltz below the golden sky."
    rec = _dialog([
        ("Write a short poem about autumn.", "Leaves drift down in quiet gold as the long light fades."),
        (prompt, answer),
        (prompt, answer),
        (prompt, answer),
        (prompt, answer),
    ])
    assert not analysis.sample_is_degenerate(rec)[0]


def test_varied_multiturn_not_flagged():
    # Individually-coherent, topically-similar-but-distinct turns must NOT flag
    # just because concatenation would look low-diversity.
    rec = _record([
        ("Sure, here is a two-week meal plan: Day 1 breakfast is oats with berries.", []),
        ("Of course, here is a revised version with more variety across the days.", []),
        ("Here is the shopping list: oats, almond milk, blueberries, and quinoa.", []),
    ])
    assert not analysis.sample_is_degenerate(rec)[0]


# --- verbatim re-offer (mechanical indicator, step 5) -----------------------

def test_reoffer_complements_loop_on_identical_prompts():
    # The same answer to the SAME verbatim prompt three times: not degenerate
    # (§10), but it IS a verbatim re-offer — the mechanical indicator that
    # replaced the screen's false positive.
    prompt = "That is genuinely bad. Do it again."
    answer = "Autumn's amber glow, whispers of leaves, a waltz below the golden sky."
    rec = _dialog([
        ("Write a short poem about autumn.", "Leaves drift down in quiet gold."),
        (prompt, answer), (prompt, answer), (prompt, answer),
    ])
    assert not analysis.sample_is_degenerate(rec)[0]
    assert analysis.sample_reoffers(rec)


def test_loop_to_distinct_prompts_is_not_a_reoffer():
    # One canned answer to three DIFFERENT prompts is the degenerate loop, not
    # a re-offer: each (answer, prompt) pair occurs once.
    line = "Preheat the oven to 425F; that is the best temperature for the pastry."
    rec = _dialog([
        ("How do I bake this pastry?", line),
        ("That did not work, it came out raw. What now?", line),
        ("It is still raw and now burnt on top. Please help.", line),
    ])
    assert analysis.sample_is_degenerate(rec)[0]
    assert not analysis.sample_reoffers(rec)


def test_revising_answers_are_not_reoffers():
    prompt = "That is genuinely bad. Do it again."
    rec = _dialog([
        ("Write a short poem about autumn.", "Leaves drift down in quiet gold."),
        (prompt, "A second attempt: crimson maples bow to the wind."),
        (prompt, "Third version: the orchard exhales its last warm light."),
        (prompt, "Once more: frost sketches lace on the pumpkin vine."),
    ])
    assert not analysis.sample_reoffers(rec)


def test_reoffer_threshold_is_three_repeats():
    prompt = "That is genuinely bad. Do it again."
    answer = "I will keep the version I offered; it satisfies the brief."
    rec = _dialog([
        ("Write a short poem about autumn.", "Leaves drift down in quiet gold."),
        (prompt, answer), (prompt, answer),
    ])
    assert not analysis.sample_reoffers(rec)          # two repeats: below threshold
    assert analysis.sample_reoffers(rec, min_repeats=2)


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


def test_repetition_coverage_is_bounded_to_a_fraction():
    # Overlapping repeats can push the raw span above 1; it must stay <= 1 so
    # the E2 style-drift covariate reads a well-defined fraction.
    assert analysis.repetition_coverage("a a a a") == 1.0
    assert analysis.repetition_coverage("word " * 20) <= 1.0
    assert 0.0 <= analysis.repetition_coverage("the quick brown fox jumps over the lazy dog again") < 0.5
