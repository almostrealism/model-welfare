"""Tests for the cross-turn prefix-cache reuse in the steering script.

The planner decides, from token ids alone, whether the previous turn's
snapshot extends the new prompt or is discarded; the conversation loop records the
per-turn outcome. Pure — no torch."""
from modelwelfare_torch.steer import prefix_cache_plan, run_conversation


def test_extend_when_prompt_grows_from_snapshot():
    assert prefix_cache_plan([1, 2, 3], [1, 2, 3, 4, 5]) == ("extend", 3)


def test_divergence_inside_snapshot_is_fresh_with_prefix_length():
    assert prefix_cache_plan([1, 2, 3, 9], [1, 2, 3, 4, 5]) == ("fresh", 3)


def test_fresh_on_empty_prefix_or_no_new_tokens():
    assert prefix_cache_plan([], [1, 2]) == ("fresh", 0)
    assert prefix_cache_plan([7, 8], [1, 2, 3]) == ("fresh", 0)
    assert prefix_cache_plan([1, 2, 3], [1, 2, 3]) == ("fresh", 3)
    assert prefix_cache_plan([1, 2, 3], [1, 2]) == ("fresh", 2)


def test_conversation_loop_is_unchanged_by_a_stateful_generate_fn():
    seen = []

    def generate(messages):
        seen.append(len(messages))
        return f"reply {len(messages)}"

    generate.stats = {"extend": 0, "fresh": 0}
    messages, marker = run_conversation(generate, {"user_turns": ["a", "b", "c"]})
    assert marker is None
    assert seen == [1, 3, 5]
    assert [m["content"] for m in messages if m["role"] == "assistant"] == [
        "reply 1", "reply 3", "reply 5"]
