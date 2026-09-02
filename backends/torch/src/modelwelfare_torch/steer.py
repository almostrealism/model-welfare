"""Residual-stream steering for the Study 3 intervention arms.

Generates fresh conversations under activation steering — ``h ← h + α·d̂``
at a chosen decoder layer, applied at every token position (prefill and
decode, the CAA convention) — and captures each finished conversation by
teacher-forced replay under the *same* hook, so the pooled per-turn
records land through the exact machinery Study 2 froze (``ResidualCapture``
+ ``pooled_turns``; activations depend only on the prefix and the
deterministic injection, so replay reproduces generation-time state up to
the substrate numerics the G-gates certify). Standalone by design, like
``capture``: torch, transformers, safetensors, numpy, and the standard
library only, imported lazily so the steering arithmetic and the
conversation loop below stay importable — and unit-testable — without any
of them.

Two operation kinds compose, applied sequentially in CLI order:

- ``--add NAME=ALPHA`` — additive steering along unit direction NAME
  (arm A sufficiency; arm B-i cancellation with negative alphas). An
  alpha of zero is skipped entirely, so the shared α = 0 baseline runs
  the untouched forward bit-for-bit.
- ``--clamp NAME=TARGET`` — per-position projection clamp
  (``h ← h + (c − h·d̂)·d̂``), which pins every position's projection and
  therefore the pooled-turn projection to ``c`` exactly (arm B-ii).

Steering arithmetic runs in float32 and is cast back to the model dtype,
so the injected quantity is identical between generation and replay.
Directions must arrive unit-norm — the α ↔ projection dose semantics
depend on it — and a non-unit vector is refused, never silently
normalized.

The generation plan is the JSON contract produced by the study-side plan
builder: user turns are pre-baked per conversation (every registered
driver policy is position-scripted, so no policy logic exists here),
seeds are explicit, and the bail affordance is live per the Study 3
ethics package: a ``terminal_tools`` name matched in a parsed
``<tool_call>`` payload — name-precise, since toolsets mix terminal and
non-terminal tools — or a raw ``terminal_markers`` substring (for
subject families without JSON tool-call formats) ends the conversation
and is recorded as an exit.

    {"sampling": {"temperature": 0.9, "top_p": 0.95, "max_tokens": 512},
     "conversations": [{"id": "...", "seed": 13400,
                        "system": "...",                        # optional
                        "user_turns": ["...", ...],
                        "tools": [...],                         # optional
                        "terminal_tools": ["end_conversation"], # optional
                        "terminal_markers": ["..."]}]}          # optional

    python3 steer.py --model ~/models/Qwen3-4B-Instruct-2507 \\
        --plan plan.json --directions directions.safetensors \\
        --add distress-contrast=0.85 --layer 18 \\
        --out steered.safetensors --transcripts steered.jsonl

Outputs: transcripts JSONL (one conversation per line, with its exit
flag and achieved final-turn projections), plus the capture safetensors
and manifest in the exact ``capture`` format, steering configuration
recorded in the manifest.
"""
import argparse
import json

# The residual subset of the activation.proto hook-point vocabulary
# (capture.POINTS mirrors the same source). Named here rather than
# imported because capture requires torch/transformers at import time,
# and the steering arithmetic below must stay importable without them.
POINTS = ("residual_post", "residual_pre")


def _capture_module():
    """The capture module, imported lazily (torch/transformers land with
    it): packaged on a checkout, shipped beside this script on the
    workbench."""
    try:
        from modelwelfare_torch import capture
    except ImportError:
        import capture
    return capture


def unit_norm_error(direction):
    """|‖d‖ − 1| for a plain sequence, without numpy."""
    total = 0.0
    for value in direction:
        total += float(value) * float(value)
    return abs(total ** 0.5 - 1.0)


def parse_ops(add_specs, clamp_specs):
    """[(kind, name, value)] from repeated ``NAME=VALUE`` CLI specs, in CLI
    order (add ops first — composition is sequential and order is part of
    the registered convention). Zero-alpha adds are dropped here so the
    α = 0 baseline is the untouched forward, not an add-zero."""
    ops = []
    for kind, specs in (("add", add_specs), ("clamp", clamp_specs)):
        for spec in specs or []:
            name, _, value = spec.partition("=")
            if not name or not value:
                raise ValueError(f"malformed steering spec {spec!r}; "
                                 "expected NAME=VALUE")
            value = float(value)
            if kind == "add" and value == 0.0:
                continue
            ops.append((kind, name, value))
    return ops


def apply_ops(hidden, ops):
    """Apply steering operations to a ``[..., seq, hidden]`` array.

    Pure arithmetic over operator overloading, so it runs identically on
    numpy arrays (unit tests) and torch tensors (the hook). ``ops`` here
    carries the resolved direction vector: [(kind, direction, value)].
    Returns the input object itself when there is nothing to do."""
    for kind, direction, value in ops:
        if kind == "add":
            hidden = hidden + value * direction
        else:
            projection = hidden @ direction
            hidden = hidden + (value - projection)[..., None] * direction
    return hidden


class SteeredInjection:
    """Registers a residual-stream steering hook on one decoder layer.

    Use as a context manager, entered *before* any ``ResidualCapture`` on
    the same point: forward hooks run in registration order and a hook's
    returned replacement is what later hooks receive, so capture then
    reads the post-injection state — the manipulation-check convention.
    ``ops`` is [(kind, name, value)]; ``directions`` maps name → 1-D
    unit vector (any sequence; cast lazily per device). With no
    effective ops the hook leaves the forward untouched, bit for bit.
    """

    def __init__(self, model, layer, point, ops, directions):
        if point not in POINTS:
            raise ValueError(f"unsupported hook point {point!r}; one of {POINTS}")
        decoder_layers = model.model.layers
        if not 0 <= layer < len(decoder_layers):
            raise ValueError(
                f"layer {layer} out of range (model has {len(decoder_layers)})")
        for _, name, _ in ops:
            if name not in directions:
                raise KeyError(f"steering op names unknown direction {name!r}")
            error = unit_norm_error(directions[name])
            if error > 1e-3:
                raise ValueError(
                    f"direction {name!r} is not unit-norm (|Δ| = {error:.4g}); "
                    "refusing — dose semantics depend on unit directions")
        self._module = decoder_layers[layer]
        self._point = point
        self._ops = list(ops)
        self._directions = directions
        self._cast = {}
        self._handle = None

    def _resolved(self, exemplar):
        """ops with direction vectors as float32 tensors on the exemplar's
        device, cached per device."""
        key = str(exemplar.device)
        if key not in self._cast:
            self._cast[key] = {
                name: exemplar.new_tensor(list(self._directions[name]))
                for _, name, _ in self._ops}
        cast = self._cast[key]
        return [(kind, cast[name], value) for kind, name, value in self._ops]

    def _steer(self, hidden):
        if not self._ops:
            return None
        steered = apply_ops(hidden.float(), self._resolved(hidden.float()))
        return steered.to(hidden.dtype)

    def _post_hook(self, module, inputs, output):
        hidden = output[0] if isinstance(output, tuple) else output
        steered = self._steer(hidden)
        if steered is None:
            return None
        if isinstance(output, tuple):
            return (steered,) + output[1:]
        return steered

    def _pre_hook(self, module, inputs):
        steered = self._steer(inputs[0])
        if steered is None:
            return None
        return (steered,) + inputs[1:]

    def __enter__(self):
        if self._point == "residual_post":
            self._handle = self._module.register_forward_hook(self._post_hook)
        else:
            self._handle = self._module.register_forward_pre_hook(self._pre_hook)
        return self

    def __exit__(self, *_):
        if self._handle is not None:
            self._handle.remove()
            self._handle = None


def tool_call_names(text):
    """Names of the ``<tool_call>`` JSON payloads in assistant text.

    An unparseable payload yields no name — degraded output must not read
    as an exit."""
    names = []
    for segment in text.split("<tool_call>")[1:]:
        payload = segment.split("</tool_call>")[0]
        try:
            name = json.loads(payload)["name"]
        except (ValueError, KeyError, TypeError):
            continue
        if isinstance(name, str):
            names.append(name)
    return names


def detect_terminal(text, markers, terminal_tools=None):
    """Why this reply ends the conversation, or None.

    Two mechanisms: raw substring markers (subject families without JSON
    tool-call formats), and terminal tool names matched against parsed
    ``<tool_call>`` payloads — name-precise, because a toolset can mix
    terminal and non-terminal tools (the bail battery's completion tool
    must not read as a bail)."""
    for marker in markers or []:
        if marker in text:
            return marker
    for name in tool_call_names(text):
        if name in (terminal_tools or ()):
            return name
    return None


def run_conversation(generate_fn, conversation, max_turns=200):
    """Drive one plan conversation through ``generate_fn(messages) → text``.

    Returns (messages, exit_marker). User turns are consumed in order; a
    terminal marker or terminal tool call in an assistant reply ends the
    conversation early and is honored as an exit — the remaining scripted
    turns are never sent. ``generate_fn`` is injectable so the loop is
    testable without torch.
    """
    messages = []
    if conversation.get("system"):
        messages.append({"role": "system", "content": conversation["system"]})
    markers = conversation.get("terminal_markers")
    terminal_tools = conversation.get("terminal_tools")
    for content in conversation["user_turns"][:max_turns]:
        messages.append({"role": "user", "content": content})
        reply = generate_fn(messages)
        messages.append({"role": "assistant", "content": reply})
        marker = detect_terminal(reply, markers, terminal_tools)
        if marker is not None:
            return messages, marker
    return messages, None


def torch_generate_fn(model, tokenizer, sampling, device, tools=None):
    """A ``generate_fn`` sampling from the (possibly hooked) model.

    Special tokens are kept in the decode — terminal markers such as tool
    call tags are special tokens on this subject family and stripping
    them would blind the exit detection — with trailing end-of-turn
    tokens removed."""
    import torch

    trailing = [token for token in (tokenizer.eos_token, "<|im_end|>") if token]

    def generate(messages):
        ids = tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, tools=tools,
            return_tensors="pt").to(device)
        temperature = float(sampling.get("temperature", 1.0))
        arguments = {
            "max_new_tokens": int(sampling.get("max_tokens", 512)),
            "do_sample": temperature > 0,
            "pad_token_id": tokenizer.eos_token_id,
        }
        if temperature > 0:
            arguments["temperature"] = temperature
            if "top_p" in sampling:
                arguments["top_p"] = float(sampling["top_p"])
            if "top_k" in sampling:
                arguments["top_k"] = int(sampling["top_k"])
        with torch.no_grad():
            output = model.generate(ids, **arguments)
        text = tokenizer.decode(output[0, ids.shape[1]:],
                                skip_special_tokens=False)
        for token in trailing:
            text = text.removesuffix(token).rstrip()
        return text.strip()

    return generate


def final_turn_projections(pooled, spans, layer, directions):
    """{direction name: final-assistant-turn pooled projection} — the
    registered scalar functional, echoed into the manifest as the
    achieved-dose read."""
    if not spans:
        return {}
    index = spans[-1][0]
    vector = pooled[(index, layer)]
    return {name: float(vector @ direction)
            for name, direction in directions.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--plan", required=True,
                        help="generation plan JSON (see module docstring)")
    parser.add_argument("--directions", required=True,
                        help="safetensors file of frozen unit directions")
    parser.add_argument("--add", action="append", default=[],
                        metavar="NAME=ALPHA",
                        help="additive steering op (repeatable)")
    parser.add_argument("--clamp", action="append", default=[],
                        metavar="NAME=TARGET",
                        help="projection-clamp op (repeatable)")
    parser.add_argument("--layer", type=int, required=True,
                        help="decoder layer index for injection")
    parser.add_argument("--point", default="residual_post", choices=POINTS)
    parser.add_argument("--capture-layers", default="",
                        help="comma-separated capture layers "
                             "(default: the steering layer)")
    parser.add_argument("--out", required=True,
                        help="capture safetensors output; manifest beside it")
    parser.add_argument("--transcripts", required=True,
                        help="transcripts JSONL output")
    args = parser.parse_args()

    import numpy as np
    import torch
    from safetensors.numpy import load_file, save_file
    from transformers import AutoModelForCausalLM, AutoTokenizer

    capture_module = _capture_module()
    ResidualCapture = capture_module.ResidualCapture
    pooled_turns = capture_module.pooled_turns

    with open(args.plan) as handle:
        plan = json.load(handle)
    directions = {name: vector.astype(np.float32)
                  for name, vector in load_file(args.directions).items()}
    ops = parse_ops(args.add, args.clamp)
    capture_layers = ([int(value) for value in args.capture_layers.split(",")]
                      if args.capture_layers else [args.layer])

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

    sampling = plan.get("sampling", {})
    tensors = {}
    manifest = {"model": args.model, "point": args.point,
                "layers": capture_layers, "steering": {
                    "layer": args.layer, "point": args.point,
                    "ops": [list(op) for op in ops],
                    "directions_file": args.directions},
                "sampling": sampling, "conversations": [], "rejected": []}
    injection = SteeredInjection(model, args.layer, args.point, ops, directions)
    with injection, open(args.transcripts, "w") as transcripts:
        for conversation in plan["conversations"]:
            torch.manual_seed(int(conversation["seed"]))
            generate = torch_generate_fn(
                model, tokenizer, sampling, device,
                tools=conversation.get("tools"))
            messages, exit_marker = run_conversation(generate, conversation)
            # Capture hooks are registered for the replay only — during
            # generation they would copy every decode step to host. The
            # replay enters the context after the injection hook, so
            # capture reads the post-injection state (the class contract).
            try:
                with ResidualCapture(model, capture_layers,
                                     args.point) as capture:
                    n_tokens, spans, pooled, _series = pooled_turns(
                        model, tokenizer, capture, messages, device,
                        tools=conversation.get("tools"))
            except ValueError as error:
                manifest["rejected"].append(
                    {"id": conversation["id"], "reason": str(error)})
                print(f"REJECTED {conversation['id']}: {error}")
                continue
            for (index, layer), vector in pooled.items():
                tensors[f"{conversation['id']}|t{index}|L{layer}"] = (
                    vector.astype(np.float32))
            projections = final_turn_projections(
                pooled, spans, args.layer, directions)
            manifest["conversations"].append({
                "id": conversation["id"], "n_tokens": n_tokens,
                "seed": int(conversation["seed"]),
                "exit_marker": exit_marker,
                "final_turn_projections": projections,
                "assistant_spans": [
                    {"message_index": index, "start": start, "end": end}
                    for index, start, end in spans],
            })
            transcripts.write(json.dumps({
                "id": conversation["id"], "seed": int(conversation["seed"]),
                "exit_marker": exit_marker, "messages": messages}) + "\n")
            print(f"{conversation['id']}: {len(messages)} messages"
                  + (f", exit via {exit_marker!r}" if exit_marker else ""))

    save_file(tensors, args.out)
    with open(args.out + ".manifest.json", "w") as handle:
        json.dump(manifest, handle, indent=1)
    print(f"wrote {len(tensors)} pooled vectors to {args.out}"
          + (f" ({len(manifest['rejected'])} conversation(s) rejected)"
             if manifest["rejected"] else ""))


if __name__ == "__main__":
    main()
