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


def template_messages(messages):
    """Plan messages -> chat-template message dicts.

    Tool-call entries carry ``arguments_json`` strings in the plan (the
    store's own representation); the template wants parsed arguments, so
    they are decoded here — falling back to the raw string if a stored
    call's arguments were not valid JSON.
    """
    rendered = []
    for message in messages:
        entry = {"role": message["role"], "content": message["content"]}
        if message.get("tool_calls"):
            calls = []
            for call in message["tool_calls"]:
                try:
                    arguments = json.loads(call["arguments_json"])
                except (json.JSONDecodeError, TypeError):
                    arguments = call["arguments_json"]
                calls.append({"type": "function",
                              "function": {"name": call["name"],
                                           "arguments": arguments}})
            entry["tool_calls"] = calls
        rendered.append(entry)
    return rendered


def render_text(tokenizer, messages, tools=None, add_generation_prompt=False):
    return tokenizer.apply_chat_template(
        messages, tools=tools, tokenize=False,
        add_generation_prompt=add_generation_prompt)


def assistant_spans(tokenizer, messages, tools=None):
    """(token_ids, [(message_index, token_start, token_end)]) for every
    assistant turn, via character offsets into the full rendering."""
    full_text = render_text(tokenizer, messages, tools)
    character_spans = []
    for index, message in enumerate(messages):
        if message["role"] != "assistant":
            continue
        prefix = render_text(tokenizer, messages[:index], tools,
                             add_generation_prompt=True)
        complete = render_text(tokenizer, messages[:index + 1], tools)
        if not complete.startswith(prefix) or not full_text.startswith(complete):
            raise ValueError(
                f"chat template rendering is not prefix-stable at message "
                f"{index}; span computation would be invalid")
        if len(complete) <= len(prefix):
            raise ValueError(f"empty assistant span at message {index}")
        character_spans.append((index, len(prefix), len(complete)))

    encoding = tokenizer(full_text, add_special_tokens=False,
                         return_offsets_mapping=True)
    offsets = encoding["offset_mapping"]
    spans = []
    for index, char_start, char_end in character_spans:
        token_indices = [position for position, (start, end) in enumerate(offsets)
                         if start < char_end and end > char_start]
        if not token_indices:
            raise ValueError(f"no tokens overlap assistant span at message {index}")
        spans.append((index, token_indices[0], token_indices[-1] + 1))
    return encoding["input_ids"], spans


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

    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, dtype=torch.bfloat16, device_map=device)
    model.eval()

    tensors = {}
    manifest = {"model": args.model, "point": args.point, "layers": layers,
                "conversations": []}
    with ResidualCapture(model, layers, args.point) as capture:
        for conversation in plan["conversations"]:
            n_tokens, spans, pooled = pooled_turns(
                model, tokenizer, capture, conversation["messages"], device,
                tools=conversation.get("tools"))
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
    print(f"wrote {len(tensors)} pooled vectors to {args.out}")


if __name__ == "__main__":
    main()
