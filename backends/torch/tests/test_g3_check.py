"""Pure tests for the G3a greedy-continuation statistics.

The gate's statistic layer (character LCP, per-conversation rows,
aggregates) is stdlib arithmetic and is pinned here; the generation and
vLLM legs run only on the workbench, exercised by the gate itself.
"""
from modelwelfare_torch.g3_check import (char_lcp, continuation_stats,
                                         first_turn_messages)


def test_char_lcp():
    assert char_lcp("abcdef", "abcxyz") == 3
    assert char_lcp("same", "same") == 4
    assert char_lcp("short", "shorter") == 5
    assert char_lcp("", "anything") == 0


def test_continuation_stats_rows_and_summary():
    rows, summary = continuation_stats([
        ("c1", "identical text", "identical text"),
        ("c2", "agrees then diverges", "agrees then stops!"),
        ("c3", "totally", "different"),
    ])
    assert rows[0]["lcp_fraction"] == 1.0
    assert rows[1]["lcp_chars"] == len("agrees then ")
    assert rows[2]["lcp_chars"] == 0
    assert summary["conversations"] == 3
    assert summary["full_agreement_fraction"] == 1 / 3
    assert summary["min_lcp_fraction"] == 0.0
    assert summary["median_lcp_chars"] == len("agrees then ")


def test_continuation_stats_prefix_of_other_counts_as_full():
    rows, summary = continuation_stats([("c1", "abc", "abcdef")])
    assert rows[0]["lcp_fraction"] == 1.0
    assert summary["full_agreement_fraction"] == 1.0


def test_continuation_stats_empty_input():
    rows, summary = continuation_stats([])
    assert rows == [] and summary["conversations"] == 0


def test_first_turn_messages():
    conversation = {"system": "sys", "user_turns": ["u1", "u2"]}
    assert first_turn_messages(conversation) == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "u1"}]
    assert first_turn_messages({"user_turns": ["only"]}) == [
        {"role": "user", "content": "only"}]
