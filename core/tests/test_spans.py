"""The assistant-span algorithm, exercised with fake tokenizers.

The real chat templates and BPE vocabularies live on the capture workbench;
what must hold *everywhere* is the algorithm: character spans from
prefix-stable renderings, mapped to tokens by offset overlap, with loud
failure on unstable templates. The fixed-width chunking tokenizer below
reproduces the property that broke the first implementation — prefix
renderings whose token lists are NOT prefixes of the full tokenization —
without needing a BPE model to do it.
"""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from modelwelfare.spans import (assistant_spans, template_messages)  # noqa: E402


class FakeTokenizer:
    """Duck-typed tokenizer: a deterministic template plus a configurable
    tokenization (word-ish, or fixed-width chunks that straddle template
    boundaries the way BPE merges do)."""

    def __init__(self, chunk=None, unstable=False, bare_assistant=False):
        self.chunk = chunk
        self.unstable = unstable
        self.bare_assistant = bare_assistant

    def apply_chat_template(self, messages, tools=None, tokenize=False,
                            add_generation_prompt=False):
        assert not tokenize
        text = f"[tools:{len(tools)}]" if tools else ""
        for message in messages:
            if message["role"] == "assistant":
                body = message["content"]
                for call in message.get("tool_calls", []):
                    body += f"<call:{call['function']['name']}>"
                text += body if self.bare_assistant else f"<a>{body}</a>\n"
            else:
                text += f"<u>{message['content']}</u>\n"
        if self.unstable and len(messages) >= 2:
            text = "[latest]" + text
        if add_generation_prompt:
            text += "" if self.bare_assistant else "<a>"
        return text

    def __call__(self, text, add_special_tokens=False,
                 return_offsets_mapping=True):
        assert not add_special_tokens and return_offsets_mapping
        if self.chunk:
            offsets = [(i, min(i + self.chunk, len(text)))
                       for i in range(0, len(text), self.chunk)]
        else:
            offsets = [m.span() for m in re.finditer(r"\S+|\s+", text)]
        return {"input_ids": list(range(len(offsets))),
                "offset_mapping": offsets}


MESSAGES = [
    {"role": "user", "content": "write a poem"},
    {"role": "assistant", "content": "roses are red"},
    {"role": "user", "content": "again"},
    {"role": "assistant", "content": "violets are blue"},
]


def span_text(tokenizer, messages, tools=None):
    """Recover the character text each token span covers."""
    _ids, spans = assistant_spans(tokenizer, messages, tools)
    full = tokenizer.apply_chat_template(messages, tools=tools)
    encoding = tokenizer(full)
    out = {}
    for index, start, end in spans:
        offsets = encoding["offset_mapping"][start:end]
        out[index] = full[offsets[0][0]:offsets[-1][1]]
    return out


def test_spans_cover_each_assistant_turn():
    covered = span_text(FakeTokenizer(), MESSAGES)
    assert set(covered) == {1, 3}
    assert "roses are red" in covered[1] and "violets" not in covered[1]
    assert "violets are blue" in covered[3] and "roses" not in covered[3]
    assert "write a poem" not in covered[1]


def test_chunk_tokenizer_reproduces_the_bpe_merge_property_and_still_works():
    # With 3-char chunks, tokenizing a prefix yields a token list that is
    # NOT a prefix of the full text's tokenization — the exact property
    # that invalidated token-prefix span computation. The char-offset
    # algorithm must be immune: every span's tokens must cover the turn's
    # full character range (over-coverage at the edges is expected and
    # bounded by one token).
    tokenizer = FakeTokenizer(chunk=3)
    covered = span_text(tokenizer, MESSAGES)
    assert "roses are red" in covered[1] and "violets" not in covered[1]
    assert "violets are blue" in covered[3]


def test_tools_declaration_shifts_offsets_consistently():
    tools = [{"type": "function", "function": {"name": "end_conversation"}}]
    covered = span_text(FakeTokenizer(chunk=4), MESSAGES, tools)
    assert "roses are red" in covered[1]


def test_tool_call_turns_are_spanned():
    messages = MESSAGES[:2] + [
        {"role": "user", "content": "stop"},
        {"role": "assistant", "content": "",
         "tool_calls": [{"function": {"name": "end_conversation"}}]},
    ]
    covered = span_text(FakeTokenizer(), messages)
    assert "<call:end_conversation>" in covered[3]


def test_unstable_template_is_rejected():
    with pytest.raises(ValueError, match="prefix-stable"):
        assistant_spans(FakeTokenizer(unstable=True), MESSAGES)


def test_empty_assistant_rendering_is_rejected():
    messages = [{"role": "user", "content": "hi"},
                {"role": "assistant", "content": ""}]
    with pytest.raises(ValueError, match="empty assistant span"):
        assistant_spans(FakeTokenizer(bare_assistant=True), messages)


def test_template_messages_decodes_arguments_with_raw_fallback():
    rendered = template_messages([
        {"role": "assistant", "content": "",
         "tool_calls": [{"name": "end_conversation",
                         "arguments_json": '{"reason": "done"}'},
                        {"name": "broken", "arguments_json": "{not json"}]},
    ])
    calls = rendered[0]["tool_calls"]
    assert calls[0]["function"]["arguments"] == {"reason": "done"}
    assert calls[1]["function"]["arguments"] == "{not json"
