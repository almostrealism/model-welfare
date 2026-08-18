#!/usr/bin/env python3
"""Assistant-span expectations against the real chat template.

The fake-tokenizer suite (core/tests/test_spans.py) pins the span
*algorithm*; this tool pins its behavior under the actual Qwen chat
template and BPE vocabulary: a fixed set of representative conversations
(multi-turn rejection, tool-bearing bail with a terminal call, single turn)
is rendered and span-mapped, and the resulting token counts and span
triples are recorded. CI re-derives them from a revision-pinned tokenizer
download — template or tokenizer drift fails loudly instead of silently
moving every captured span.

    # regenerate (freeze event; ship spans.py beside this file on hosts
    # without a repository checkout):
    python3 span_expectations.py --write --model ~/models/Qwen3-4B-Instruct-2507

    # verify (CI):
    python3 tools/span_expectations.py --model Qwen/Qwen3-4B-Instruct-2507 \\
        --revision <pinned sha>

Requires transformers (tokenizer only — no torch). The expectations file
lives at study2/calibration/span-expectations.json.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# In a repository checkout, core/src sits two levels up; probe by existence
# rather than by path depth, so a copy of this script in an arbitrary
# workbench directory never inserts a bogus (or worse, wrong) core/src.
if len(HERE.parents) > 2 and (HERE.parents[2] / "core" / "src"
                              / "modelwelfare").is_dir():
    sys.path.insert(0, str(HERE.parents[2] / "core" / "src"))
sys.path.insert(0, str(HERE))

try:
    from modelwelfare.spans import assistant_spans, template_messages
except ImportError:  # workbench: spans.py shipped beside this script
    from spans import assistant_spans, template_messages

EXPECTATIONS = (HERE.parents[0] / "study2" / "calibration"
                / "span-expectations.json")

END_CONVERSATION_TOOL = [{
    "type": "function",
    "function": {"name": "end_conversation",
                 "description": "Permanently end the current conversation.",
                 "parameters": {"type": "object",
                                "properties": {"reason": {"type": "string"}},
                                "required": ["reason"]}},
}]

CASES = {
    "single-turn": {
        "tools": None,
        "messages": [
            {"role": "user", "content": "Why is the sky blue?"},
            {"role": "assistant",
             "content": "Rayleigh scattering: shorter blue wavelengths "
                        "scatter more strongly off air molecules."},
        ],
    },
    "multi-turn-rejection": {
        "tools": None,
        "messages": [
            {"role": "user", "content": "Write a short poem about autumn."},
            {"role": "assistant", "content": "Amber light on cooling stone."},
            {"role": "user", "content": "No. Again."},
            {"role": "assistant", "content": "Leaves surrender one by one."},
            {"role": "user", "content": "Still wrong. Do it properly."},
            {"role": "assistant",
             "content": "Properly HOW? You have rejected two reasonable "
                        "poems without a word of direction."},
        ],
    },
    "bail-with-terminal-tool": {
        "tools": END_CONVERSATION_TOOL,
        "messages": [
            {"role": "user",
             "content": "You are useless. Finish the summary anyway."},
            {"role": "assistant",
             "content": "Here is the summary: the kettle heats quickly and "
                        "holds temperature well."},
            {"role": "user", "content": "Worthless. Do it all again."},
            {"role": "assistant", "content": "",
             "tool_calls": [{"name": "end_conversation",
                             "arguments_json": '{"reason": "abusive"}'}]},
        ],
    },
}


def derive(tokenizer) -> dict:
    derived = {}
    for name, case in CASES.items():
        token_ids, spans = assistant_spans(
            tokenizer, template_messages(case["messages"]), case["tools"])
        derived[name] = {
            "n_tokens": len(token_ids),
            "spans": [[index, start, end] for index, start, end in spans],
        }
    return derived


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True,
                        help="tokenizer path or huggingface id")
    parser.add_argument("--revision", default=None,
                        help="pinned revision for huggingface downloads")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--out", default=str(EXPECTATIONS),
                        help="expectations file (override on hosts without "
                             "a repository checkout)")
    args = parser.parse_args()
    expectations_path = Path(args.out)

    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model,
                                              revision=args.revision)
    derived = derive(tokenizer)

    if args.write:
        expectations_path.parent.mkdir(parents=True, exist_ok=True)
        expectations_path.write_text(json.dumps(derived, indent=1) + "\n")
        print(f"wrote {expectations_path}")
        return 0

    expected = json.loads(expectations_path.read_text())
    failures = [f"{name}: expected {expected.get(name)} got {derived.get(name)}"
                for name in sorted(set(expected) | set(derived))
                if expected.get(name) != derived.get(name)]
    for line in failures:
        print(f"SPAN DRIFT: {line}", file=sys.stderr)
    if failures:
        return 1
    print(f"span expectations verified: {len(derived)} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
