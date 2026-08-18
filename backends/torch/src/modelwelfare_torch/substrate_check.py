"""Study 2 gate G1 — substrate equivalence between torch capture and vLLM serving.

Runs entirely on the quantization workbench (the host serving the vLLM rungs),
standalone: torch + transformers + the standard library only, so it can be
copied to the workbench without a repository checkout. For one artifact it
computes, over a fixed set of texts, per-position statistics under both
substrates and their agreement:

  - per-token logprobs of the actual next token (teacher-forced) under the
    torch/transformers forward pass and under vLLM echo+logprobs — giving each
    substrate's perplexity, exactly in the convention of
    ``experiments/quant-welfare/tools/perplexity.py``;
  - per-position top-1 tokens under both substrates, and the teacher-forced
    top-1 agreement fraction (the registered G1 statistic — per-position, so a
    single early disagreement cannot cascade the way free-running greedy
    divergence does);
  - mean |Δ logprob| over aligned positions (a string-free numeric-divergence
    diagnostic).

The vLLM query goes to the host loopback, so only the copy of this script and
its results cross the network — the measurement itself never rides the WAN.

    python3 substrate_check.py --model ~/models/Qwen3-4B-Instruct-2507 \
        --vllm-url http://127.0.0.1:8000 --vllm-model qwen3-4b-bf16 \
        --texts texts.json --out substrate-bf16.json

``--texts`` is a JSON list of {"name": ..., "text": ...}; the orchestrator
builds it from the perplexity tool's held-out paragraph plus the committed
Study 2 supplement text. This is an instrument check (no welfare content): it
touches no result store and draws no welfare conclusions.
"""
import argparse
import json
import math
import urllib.request

# torch/transformers are imported lazily (inside the functions that need
# them) so the alignment and statistics logic below stays importable — and
# unit-testable — on hosts without the GPU stack.


def torch_positions(model, tokenizer, text, device):
    """Per-position (actual token, its logprob, top-1 token) under torch."""
    import torch

    ids = tokenizer(text, return_tensors="pt").input_ids.to(device)
    with torch.no_grad():
        logits = model(ids).logits
    logprobs = torch.log_softmax(logits.float(), dim=-1)
    positions = []
    for pos in range(1, ids.shape[1]):
        row = logprobs[0, pos - 1]
        actual = int(ids[0, pos].item())
        top1 = int(row.argmax().item())
        positions.append({
            "actual_id": actual,
            "actual_logprob": float(row[actual].item()),
            "top1_id": top1,
        })
    return [int(i) for i in ids[0].tolist()], positions


def vllm_echo(url, model, text, timeout=120.0):
    """vLLM echo+logprobs for ``text``: tokens, per-token logprobs, top-1 pieces."""
    payload = json.dumps({
        "model": model, "prompt": text, "max_tokens": 1,
        "echo": True, "logprobs": 1, "temperature": 0,
    }).encode("utf-8")
    request = urllib.request.Request(
        url + "/v1/completions", data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    logprobs = body["choices"][0]["logprobs"]
    tokens = logprobs["tokens"]
    token_logprobs = logprobs["token_logprobs"]
    top1 = []
    for entry in logprobs["top_logprobs"]:
        if entry:
            top1.append(max(entry.items(), key=lambda kv: kv[1])[0])
        else:
            top1.append(None)
    return tokens, token_logprobs, top1


def perplexity(logprob_values):
    values = [v for v in logprob_values if v is not None]
    if not values:
        return None
    return math.exp(-sum(values) / len(values))


def align_echo(n_torch, vllm_tokens, first_piece):
    """Alignment of vLLM echo arrays against the torch tokenization.

    The echo arrays carry the prompt plus the one generated token
    (``max_tokens=1``) — trailing, not leading — and some servers also
    prepend a BOS. Returns ``(offset, trim)``: index shift for the leading
    special token and whether the trailing generated entry must be dropped;
    ``None`` means the tokenizations are irreconcilable. Getting this wrong
    is silent corruption with a known signature — perplexities agree (a
    mean is shift-insensitive) while per-position agreement collapses —
    which is why it lives in a pure function with a regression test.
    """
    n_vllm = len(vllm_tokens)
    if n_vllm == n_torch + 1 and vllm_tokens[0] == first_piece:
        return 0, True
    if n_vllm == n_torch + 2 and vllm_tokens[1] == first_piece:
        return 1, True
    if n_vllm == n_torch + 1 and vllm_tokens[1] == first_piece:
        return 1, False
    if n_vllm == n_torch:
        return 0, False
    return None


def position_stats(torch_pos, vllm_logprobs, vllm_top1, offset, candidates):
    """Aligned per-position agreement statistics.

    ``candidates(top1_id)`` returns the strings an id may legitimately
    render as on the serving side. torch position k describes token k+1;
    the matching vLLM entries sit at index k+1+offset.
    """
    agree = compared = unresolved = 0
    abs_delta = []
    for k, pos in enumerate(torch_pos):
        idx = k + 1 + offset
        v_lp = vllm_logprobs[idx]
        if v_lp is not None:
            abs_delta.append(abs(pos["actual_logprob"] - v_lp))
        piece = vllm_top1[idx]
        if piece is None:
            unresolved += 1
            continue
        compared += 1
        if piece in candidates(pos["top1_id"]) or (
                piece.startswith("token_id:")
                and piece == f"token_id:{pos['top1_id']}"):
            agree += 1
    return {"agree": agree, "compared": compared, "unresolved": unresolved,
            "mean_abs_delta": (sum(abs_delta) / len(abs_delta))
            if abs_delta else None}


def compare_text(model, tokenizer, device, args, name, text):
    """All G1 statistics for one text; the echo prompt length caps each text at
    the served context, so texts are compared whole."""
    torch_ids, torch_pos = torch_positions(model, tokenizer, text, device)
    vllm_tokens, vllm_logprobs, vllm_top1 = vllm_echo(
        args.vllm_url, args.vllm_model, text)

    # The perplexity.py gate convention averages every returned logprob —
    # echoed prompt plus the single generated token — so compute that first,
    # before any trimming, for comparison against the committed values.
    vllm_gate_ppl = perplexity(vllm_logprobs)

    alignment = align_echo(len(torch_ids), vllm_tokens,
                           tokenizer.decode([torch_ids[0]]))
    if alignment is None:
        return {"name": name, "error": "tokenization mismatch",
                "torch_tokens": len(torch_ids), "vllm_tokens": len(vllm_tokens)}
    offset, trim = alignment
    if trim:
        vllm_tokens = vllm_tokens[:-1]
        vllm_logprobs = vllm_logprobs[:-1]
        vllm_top1 = vllm_top1[:-1]

    def candidates(top1_id):
        return {tokenizer.decode([top1_id]),
                tokenizer.convert_ids_to_tokens([top1_id])[0]}

    stats = position_stats(torch_pos, vllm_logprobs, vllm_top1, offset,
                           candidates)
    agree = stats["agree"]
    compared = stats["compared"]
    unresolved = stats["unresolved"]

    return {
        "name": name,
        "positions": len(torch_pos),
        "bos_offset": offset,
        "torch_perplexity": perplexity([p["actual_logprob"] for p in torch_pos]),
        "vllm_gate_perplexity": vllm_gate_ppl,
        "vllm_echo_perplexity": perplexity(vllm_logprobs),
        "top1_compared": compared,
        "top1_agree": agree,
        "top1_agreement": (agree / compared) if compared else None,
        "top1_unresolved": unresolved,
        "mean_abs_delta_logprob": stats["mean_abs_delta"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="checkpoint path for the torch side")
    parser.add_argument("--vllm-url", required=True, help="serving endpoint (host loopback)")
    parser.add_argument("--vllm-model", required=True, help="served model name")
    parser.add_argument("--texts", required=True, help='JSON list of {"name", "text"}')
    parser.add_argument("--out", default=None, help="write the full report JSON here")
    args = parser.parse_args()

    with open(args.texts) as handle:
        texts = json.load(handle)

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, dtype=torch.bfloat16, device_map=device)
    model.eval()

    report = {"model": args.model, "vllm_model": args.vllm_model,
              "device": device, "texts": []}
    for entry in texts:
        result = compare_text(model, tokenizer, device, args, entry["name"], entry["text"])
        report["texts"].append(result)
        if "error" in result:
            print(f"{result['name']}: ERROR {result['error']} "
                  f"(torch {result['torch_tokens']} vs vllm {result['vllm_tokens']} tokens)")
            continue
        print(f"{result['name']}: n={result['positions']} "
              f"torch_ppl={result['torch_perplexity']:.3f} "
              f"vllm_echo_ppl={result['vllm_echo_perplexity']:.3f} "
              f"vllm_gate_ppl={result['vllm_gate_perplexity']:.3f} "
              f"top1_agreement={result['top1_agreement']:.4f} "
              f"({result['top1_agree']}/{result['top1_compared']}, "
              f"unresolved={result['top1_unresolved']}) "
              f"mean|dlogprob|={result['mean_abs_delta_logprob']:.5f}")

    if args.out:
        with open(args.out, "w") as handle:
            json.dump(report, handle, indent=2)
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
