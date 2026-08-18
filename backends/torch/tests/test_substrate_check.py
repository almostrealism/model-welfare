"""Echo alignment and agreement statistics for the G1 substrate check.

The alignment regression here encodes the 2026-08-17 incident: vLLM's echo
arrays carry the prompt plus one trailing generated token, and misreading
that surplus as a leading BOS shifts every per-position comparison by one —
with the treacherous signature that perplexities still agree (a mean is
shift-insensitive) while top-1 agreement collapses. The fixture asserts
both halves of that signature so the bug class cannot return silently.
"""
import math

import pytest

from modelwelfare_torch.substrate_check import (align_echo, perplexity,
                                                position_stats)


def test_alignment_trailing_generated_token():
    assert align_echo(3, ["a", "b", "c", "gen"], "a") == (0, True)


def test_alignment_bos_plus_trailing():
    assert align_echo(3, ["<bos>", "a", "b", "c", "gen"], "a") == (1, True)


def test_alignment_bos_only():
    assert align_echo(3, ["<bos>", "a", "b", "c"], "a") == (1, False)


def test_alignment_equal_lengths():
    assert align_echo(3, ["a", "b", "c"], "a") == (0, False)


def test_alignment_irreconcilable():
    assert align_echo(3, ["x", "y"], "a") is None
    assert align_echo(3, ["x", "y", "z", "w", "v", "u"], "a") is None


def fixture_arrays():
    """A 4-token conversation as both substrates see it, agreeing exactly."""
    torch_pos = [
        {"actual_id": 11, "actual_logprob": -1.0, "top1_id": 11},
        {"actual_id": 12, "actual_logprob": -2.0, "top1_id": 12},
        {"actual_id": 13, "actual_logprob": -3.0, "top1_id": 13},
    ]
    # vLLM echo: [None-prefixed prompt logprobs] + trailing generated entry.
    vllm_logprobs = [None, -1.0, -2.0, -3.0, -0.5]
    vllm_top1 = [None, "t11", "t12", "t13", "t99"]
    candidates = {11: {"t11"}, 12: {"t12"}, 13: {"t13"}}.get
    return torch_pos, vllm_logprobs, vllm_top1, lambda i: candidates(i, set())


def test_correct_alignment_gives_perfect_agreement():
    torch_pos, vllm_logprobs, vllm_top1, candidates = fixture_arrays()
    # Correct handling trims the trailing generated entry first.
    stats = position_stats(torch_pos, vllm_logprobs[:-1], vllm_top1[:-1],
                           offset=0, candidates=candidates)
    assert stats == {"agree": 3, "compared": 3, "unresolved": 0,
                     "mean_abs_delta": 0.0}


def test_the_misalignment_signature_perplexity_agrees_agreement_collapses():
    torch_pos, vllm_logprobs, vllm_top1, candidates = fixture_arrays()
    # The original bug: the trailing surplus misread as a leading BOS,
    # shifting every comparison by one WITHOUT trimming.
    stats = position_stats(torch_pos, vllm_logprobs, vllm_top1,
                           offset=1, candidates=candidates)
    assert stats["agree"] == 0
    assert stats["mean_abs_delta"] > 0.5
    # ...while the two perplexities remain close: the misalignment only
    # rotates which logprob pairs with which, barely moving the mean.
    torch_ppl = perplexity([p["actual_logprob"] for p in torch_pos])
    vllm_echo_ppl = perplexity(vllm_logprobs[:-1])
    assert torch_ppl == pytest.approx(vllm_echo_ppl)


def test_token_id_form_is_accepted():
    torch_pos = [{"actual_id": 5, "actual_logprob": -1.0, "top1_id": 5}]
    stats = position_stats(torch_pos, [None, -1.0], [None, "token_id:5"],
                           offset=0, candidates=lambda i: set())
    assert stats["agree"] == 1


def test_perplexity_convention():
    assert perplexity([-1.0, -3.0]) == pytest.approx(math.exp(2.0))
    assert perplexity([None, -2.0]) == pytest.approx(math.exp(2.0))
    assert perplexity([None]) is None
