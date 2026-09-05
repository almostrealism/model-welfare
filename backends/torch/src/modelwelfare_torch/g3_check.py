"""Study 3 gate G3a — greedy-continuation agreement, torch generation vs
vLLM serving.

G1 certified the torch substrate teacher-forced; the steered arms
*generate* in torch, which teacher-forcing does not cover. G3a measures
the generation path directly: for each plan conversation, the chat
template is rendered over the system turn (when present) plus the first
user turn, both stacks continue it greedily (temperature 0), and the two
continuations are compared by **character-level** longest common prefix
— character-level because the two stacks report tokens in different
encodings, while the rendered text is identical by construction (vLLM
receives the exact string torch templated, via the completions endpoint,
and tokenizes it with the same tokenizer). Single-shot first turns, not
full conversations: a single near-tie flip cascades into total
divergence downstream (the G1 lesson), so multi-turn agreement would
compound and measure nothing.

Emits a JSON report of per-conversation prefix statistics plus
aggregates. Thresholds are NOT applied here — the registration pins them
from measured margins, the Study 2 convention — and the registered gate
reads this report. Standalone like ``capture``/``substrate_check``:
torch, transformers, and the standard library only, heavy imports lazy.

    python3 g3_check.py --model ~/models/Qwen3-4B-Instruct-2507 \\
        --plan g3-plan.json --url http://halo:8000 \\
        --served-model qwen3-4b-instruct-2507 \\
        --max-tokens 128 --out g3a-report.json
"""
import argparse
import json
import urllib.request


def char_lcp(a, b):
    """Length of the longest common character prefix."""
    limit = min(len(a), len(b))
    for index in range(limit):
        if a[index] != b[index]:
            return index
    return limit


def continuation_stats(pairs):
    """Per-conversation and aggregate prefix statistics for
    [(id, torch_text, vllm_text)]. ``lcp_fraction`` is the prefix length
    over the shorter continuation — 1.0 means one continuation is a
    prefix of the other (full agreement to the shorter horizon)."""
    rows = []
    for conversation_id, torch_text, vllm_text in pairs:
        prefix = char_lcp(torch_text, vllm_text)
        shorter = min(len(torch_text), len(vllm_text))
        rows.append({
            "id": conversation_id,
            "lcp_chars": prefix,
            "torch_chars": len(torch_text),
            "vllm_chars": len(vllm_text),
            "lcp_fraction": (prefix / shorter) if shorter else 1.0,
        })
    fractions = sorted(row["lcp_fraction"] for row in rows)
    prefixes = sorted(row["lcp_chars"] for row in rows)
    count = len(rows)
    summary = {
        "conversations": count,
        "full_agreement_fraction":
            sum(1 for f in fractions if f == 1.0) / count if count else 0.0,
        "median_lcp_fraction": fractions[count // 2] if count else 0.0,
        "min_lcp_fraction": fractions[0] if count else 0.0,
        "median_lcp_chars": prefixes[count // 2] if count else 0,
        "min_lcp_chars": prefixes[0] if count else 0,
    }
    return rows, summary


def first_turn_messages(conversation):
    """The single-shot prompt for one plan conversation."""
    messages = []
    if conversation.get("system"):
        messages.append({"role": "system", "content": conversation["system"]})
    messages.append({"role": "user", "content": conversation["user_turns"][0]})
    return messages


def vllm_completion(url, model, prompt, max_tokens, timeout=300.0):
    """The greedy continuation text from a vLLM completions endpoint, for
    the exact rendered prompt string (same tokenizer server-side)."""
    request = urllib.request.Request(
        url.rstrip("/") + "/v1/completions",
        data=json.dumps({
            "model": model, "prompt": prompt, "max_tokens": max_tokens,
            "temperature": 0.0,
        }).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)["choices"][0]["text"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--plan", required=True,
                        help="a steering-plan JSON; only each "
                             "conversation's first turn is used")
    parser.add_argument("--url", required=True, help="vLLM base URL")
    parser.add_argument("--served-model", required=True,
                        help="model name as served by vLLM")
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--limit", type=int, default=0,
                        help="check only the first N conversations")
    parser.add_argument("--out", required=True, help="JSON report path")
    args = parser.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    try:
        from modelwelfare_torch.capture import best_device
    except ImportError:
        from capture import best_device
    device = best_device()
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, dtype=torch.bfloat16, device_map=device)
    model.eval()

    with open(args.plan) as handle:
        plan = json.load(handle)
    conversations = plan["conversations"]
    if args.limit:
        conversations = conversations[:args.limit]

    pairs = []
    for conversation in conversations:
        messages = first_turn_messages(conversation)
        prompt = tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=False)
        ids = tokenizer(prompt, return_tensors="pt",
                        add_special_tokens=False).input_ids.to(device)
        with torch.no_grad():
            output = model.generate(
                ids, max_new_tokens=args.max_tokens, do_sample=False,
                pad_token_id=tokenizer.eos_token_id)
        torch_text = tokenizer.decode(output[0, ids.shape[1]:],
                                      skip_special_tokens=True)
        vllm_text = vllm_completion(args.url, args.served_model, prompt,
                                    args.max_tokens)
        pairs.append((conversation["id"], torch_text, vllm_text))
        print(f"{conversation['id']}: lcp {char_lcp(torch_text, vllm_text)} "
              f"chars (torch {len(torch_text)}, vllm {len(vllm_text)})")

    rows, summary = continuation_stats(pairs)
    with open(args.out, "w") as handle:
        json.dump({"model": args.model, "served_model": args.served_model,
                   "max_tokens": args.max_tokens,
                   "summary": summary, "conversations": rows}, handle,
                  indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
