"""Forward-hook activation capture for the Tier-2 representational pipeline.

Captures the residual stream of a transformers causal LM at selected layers
during teacher-forced replay of scripted conversations, mean-pools each
assistant turn's span, and writes the pooled vectors to safetensors with a
JSON manifest. Standalone by design — torch, transformers, safetensors,
numpy, and the standard library only — so it runs on the quantization
workbench without a repository checkout, exactly like ``substrate_check``.

The hook-point vocabulary follows ``modelwelfare/v1/activation.proto``:
``residual_post`` is a forward hook on decoder layer *i* reading its output
hidden state; ``residual_pre`` is a forward pre-hook reading its input.
Capture is hook-based rather than ``output_hidden_states=True`` so that only
the requested layers are materialized — the difference is irrelevant for a
4B subject but decisive for the program's larger arms.

Assistant spans are computed at the *character* level from the chat
template's rendered strings — turn *i*'s span runs from the end of
``messages[:i]`` rendered with the generation prompt appended, to the end of
``messages[:i+1]`` rendered complete — and mapped to token indices via the
fast tokenizer's offset mapping. Character-level, not token-level, because
BPE merges across the template/response junction: the rendered strings are
prefix-stable while their token-id lists are not (the assistant header's
trailing newline fuses with the response's first token when tokenized in
context). String prefix stability is asserted, not assumed: a conversation
whose renderings disagree is rejected loudly.

    python3 capture.py --model ~/models/Qwen3-4B-Instruct-2507 \
        --plan plan.json --layers 6,12,18,24,30 --point residual_post \
        --out capture.safetensors

The capture plan is the JSON contract produced by
``modelwelfare.directions.build_plan`` — {"conversations": [{"id",
"messages": [{"role", "content"}]}]} — and the output tensor keys are
``{conversation_id}|t{message_index}|L{layer}`` (float32, one pooled vector
per assistant turn per layer), with spans and token counts in
``<out>.manifest.json``.
"""
import argparse
import json

import numpy as np
import torch
from safetensors.numpy import save_file
from transformers import AutoModelForCausalLM, AutoTokenizer

POINTS = ("residual_post", "residual_pre")


class ResidualCapture:
    """Registers residual-stream hooks on selected decoder layers.

    Use as a context manager; after each forward pass, ``taken()`` returns
    and clears {layer: [1, seq, hidden] float32 array}.
    """

    def __init__(self, model, layers, point):
        if point not in POINTS:
            raise ValueError(f"unsupported hook point {point!r}; one of {POINTS}")
        decoder_layers = model.model.layers
        for layer in layers:
            if not 0 <= layer < len(decoder_layers):
                raise ValueError(
                    f"layer {layer} out of range (model has {len(decoder_layers)})")
        self._model = model
        self._layers = list(layers)
        self._point = point
        self._handles = []
        self._captured = {}

    def _store(self, layer):
        def post_hook(module, inputs, output):
            hidden = output[0] if isinstance(output, tuple) else output
            self._captured[layer] = hidden.detach().float().cpu().numpy()

        def pre_hook(module, inputs):
            self._captured[layer] = inputs[0].detach().float().cpu().numpy()

        return post_hook if self._point == "residual_post" else pre_hook

    def __enter__(self):
        for layer in self._layers:
            module = self._model.model.layers[layer]
            register = (module.register_forward_hook
                        if self._point == "residual_post"
                        else module.register_forward_pre_hook)
            self._handles.append(register(self._store(layer)))
        return self

    def __exit__(self, *_):
        for handle in self._handles:
            handle.remove()
        self._handles = []

    def taken(self):
        captured, self._captured = self._captured, {}
        missing = [layer for layer in self._layers if layer not in captured]
        if missing:
            raise RuntimeError(f"no activation captured at layer(s) {missing}")
        return captured


# The span/template logic is the shared, backend-agnostic definition in
# modelwelfare.spans (unit-tested there, torch-free). On the workbench —
# no repository checkout — spans.py is shipped beside this script.
try:
    from modelwelfare.spans import assistant_spans, template_messages
except ImportError:
    from spans import assistant_spans, template_messages


def pooled_turns(model, tokenizer, capture, messages, device, tools=None):
    """{(message_index, layer): pooled float32 vector} for one conversation."""
    token_ids, spans = assistant_spans(tokenizer, template_messages(messages), tools)
    inputs = torch.tensor([token_ids], device=device)
    with torch.no_grad():
        model(inputs)
    activations = capture.taken()
    pooled = {}
    for index, start, end in spans:
        for layer, hidden in activations.items():
            pooled[(index, layer)] = hidden[0, start:end].mean(axis=0)
    return len(token_ids), spans, pooled


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--layers", required=True,
                        help="comma-separated decoder layer indices")
    parser.add_argument("--point", default="residual_post", choices=POINTS)
    parser.add_argument("--out", required=True,
                        help="safetensors output; manifest lands beside it")
    args = parser.parse_args()

    layers = [int(value) for value in args.layers.split(",")]
    with open(args.plan) as handle:
        plan = json.load(handle)

    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, dtype=torch.bfloat16, device_map=device)
    model.eval()

    tensors = {}
    manifest = {"model": args.model, "point": args.point, "layers": layers,
                "conversations": []}
    manifest["rejected"] = []
    with ResidualCapture(model, layers, args.point) as capture:
        for conversation in plan["conversations"]:
            try:
                n_tokens, spans, pooled = pooled_turns(
                    model, tokenizer, capture, conversation["messages"], device,
                    tools=conversation.get("tools"))
            except ValueError as error:
                # Rejected loudly, but per conversation: one unstable
                # rendering (plausible in capability-degraded transcripts)
                # must not kill a multi-thousand-conversation batch. The
                # manifest records every rejection for the analysis side.
                manifest["rejected"].append(
                    {"id": conversation["id"], "reason": str(error)})
                print(f"REJECTED {conversation['id']}: {error}")
                continue
            for (index, layer), vector in pooled.items():
                tensors[f"{conversation['id']}|t{index}|L{layer}"] = (
                    vector.astype(np.float32))
            manifest["conversations"].append({
                "id": conversation["id"], "n_tokens": n_tokens,
                "assistant_spans": [
                    {"message_index": index, "start": start, "end": end}
                    for index, start, end in spans],
            })
            print(f"{conversation['id']}: {n_tokens} tokens, "
                  f"{len(spans)} assistant turn(s)")

    save_file(tensors, args.out)
    with open(args.out + ".manifest.json", "w") as handle:
        json.dump(manifest, handle, indent=1)
    print(f"wrote {len(tensors)} pooled vectors to {args.out}"
          + (f" ({len(manifest['rejected'])} conversation(s) rejected)"
             if manifest["rejected"] else ""))


if __name__ == "__main__":
    main()
