"""The controlled quantization ladder: RTN fake-quant over HF checkpoints.

Round-to-nearest weight-only quantization implemented directly in numpy —
no ML framework required — producing "fake-quant" checkpoints: weights are
quantized to the b-bit grid and dequantized back to the source dtype, so
the artifact serves on any BF16/F16-capable runtime with bit-exact
quantized weight values and standard weight-only PTQ semantics
(PREREGISTRATION.md section 3). GPTQ/AWQ, which require calibration
forward passes, are separate torch-side tooling.

Safetensors I/O is implemented here from the format specification (8-byte
little-endian header length, JSON header with per-tensor dtype/shape/data
offsets, raw data) rather than through a library binding, so bfloat16 is
handled by explicit bit conversion and the at-rest behavior has no
dependency ambiguity. Only BF16/F16/F32 tensors selected for quantization
are decoded; everything else passes through byte-identical.

Quantization: symmetric, per-group along the input dimension, restricted
range [-(2^(b-1)-1), 2^(b-1)-1], scale = group absmax / qmax. numpy's
round-half-even is the rounding mode. 2D ``*.weight`` tensors are
quantized except embeddings and the output head, which follow standard
weight-only PTQ practice in remaining at full precision.

Usage:
    python3 -m modelwelfare.quantize --input <hf_checkpoint_dir> \
        --output <dir> --bits 4 --group-size 128
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np

from google.protobuf import text_format

from modelwelfare.v1 import condition_pb2

SKIP_PATTERNS = ("embed_tokens", "lm_head")


def bf16_to_f32(raw: bytes) -> np.ndarray:
    u16 = np.frombuffer(raw, dtype=np.uint16)
    return (u16.astype(np.uint32) << 16).view(np.float32)


def f32_to_bf16(values: np.ndarray) -> bytes:
    u32 = np.ascontiguousarray(values, dtype=np.float32).view(np.uint32)
    rounding_bias = 0x7FFF + ((u32 >> 16) & 1)
    return ((u32 + rounding_bias) >> 16).astype(np.uint16).tobytes()


_DECODE = {
    "BF16": lambda raw: bf16_to_f32(raw),
    "F16": lambda raw: np.frombuffer(raw, dtype=np.float16).astype(np.float32),
    "F32": lambda raw: np.frombuffer(raw, dtype=np.float32).copy(),
}

_ENCODE = {
    "BF16": f32_to_bf16,
    "F16": lambda values: values.astype(np.float16).tobytes(),
    "F32": lambda values: np.ascontiguousarray(values, dtype=np.float32).tobytes(),
}


def read_safetensors(path):
    """Returns (metadata, ordered {name: (dtype, shape, raw_bytes)})."""
    data = Path(path).read_bytes()
    header_len = int.from_bytes(data[:8], "little")
    header = json.loads(data[8 : 8 + header_len])
    metadata = header.pop("__metadata__", None)
    base = 8 + header_len
    tensors = {}
    for name, info in header.items():
        begin, end = info["data_offsets"]
        tensors[name] = (info["dtype"], info["shape"], data[base + begin : base + end])
    return metadata, tensors


def write_safetensors(path, metadata, tensors):
    header = {}
    if metadata:
        header["__metadata__"] = metadata
    offset = 0
    for name, (dtype, shape, raw) in tensors.items():
        header[name] = {"dtype": dtype, "shape": shape, "data_offsets": [offset, offset + len(raw)]}
        offset += len(raw)
    encoded = json.dumps(header).encode("utf-8")
    encoded += b" " * ((8 - len(encoded) % 8) % 8)
    with open(path, "wb") as out:
        out.write(len(encoded).to_bytes(8, "little"))
        out.write(encoded)
        for _, _, raw in tensors.values():
            out.write(raw)


def rtn(weights: np.ndarray, bits: int, group_size: int) -> np.ndarray:
    """Quantize-dequantize a 2D [out, in] weight matrix on the b-bit grid."""
    if bits < 2:
        raise ValueError("restricted symmetric quantization needs at least 2 bits")
    qmax = 2 ** (bits - 1) - 1
    out_features, in_features = weights.shape
    group = group_size if group_size > 0 else in_features
    pad = (-in_features) % group
    if pad:
        weights = np.concatenate(
            [weights, np.zeros((out_features, pad), dtype=weights.dtype)], axis=1
        )
    grouped = weights.reshape(out_features, -1, group)
    scale = np.abs(grouped).max(axis=2, keepdims=True) / qmax
    scale[scale == 0] = 1.0
    quantized = np.clip(np.round(grouped / scale), -qmax, qmax)
    dequantized = (quantized * scale).reshape(out_features, -1)[:, :in_features]
    return dequantized.astype(np.float32)


def awq(weights: np.ndarray, calib: np.ndarray, bits: int, group_size: int,
        alphas: np.ndarray = None) -> np.ndarray:
    """First-party activation-aware weight quantization (fake-quant).

    AWQ protects the weight columns that see the largest activations. For a
    per-input-channel scale ``s`` derived from calibration activations, the
    quantized-then-dequantized weights are ``rtn(W * s) / s`` — folding ``1/s``
    back in so the result serves directly, with no runtime scaling, exactly
    like the RTN artifacts. ``s = (mean|activation| per channel) ** alpha``,
    normalized to unit mean; ``alpha`` is grid-searched to minimize the
    calibration output error ``||W_eff x - W x||``. At ``alpha = 0`` this
    reduces to plain :func:`rtn`, so AWQ is never worse than RTN on the
    calibration set.

    ``calib`` is an ``(n_samples, in_features)`` matrix of inputs seen by this
    linear layer (collected by the torch activation-capture pass). This is the
    pure-numpy core; where the calibration activations come from is the
    caller's concern.
    """
    if alphas is None:
        alphas = np.linspace(0.0, 1.0, 21)
    calib = np.asarray(calib, dtype=np.float32)
    if calib.ndim != 2 or calib.shape[1] != weights.shape[1]:
        raise ValueError("calib must be (n_samples, in_features) matching weights")
    act_scale = np.abs(calib).mean(axis=0)
    act_scale = np.where(act_scale > 0, act_scale, 1e-8)
    reference = weights @ calib.T
    best_eff = None
    best_err = np.inf
    for alpha in alphas:
        s = act_scale ** float(alpha)
        s = s / s.mean()
        s = np.where(s > 0, s, 1e-8)
        eff = rtn(weights * s[None, :], bits, group_size) / s[None, :]
        err = float(((eff @ calib.T - reference) ** 2).mean())
        if err < best_err:
            best_err = err
            best_eff = eff
    return best_eff.astype(np.float32)


def should_quantize(name, dtype, shape):
    return (
        len(shape) == 2
        and name.endswith(".weight")
        and dtype in _DECODE
        and not any(pattern in name for pattern in SKIP_PATTERNS)
    )


def _transform_checkpoint(input_dir, output_dir, transform, spec_method, bits,
                          group_size, policy_note):
    """Read a checkpoint, apply ``transform(name, original_f32) ->
    dequantized_f32`` to every quantizable weight (others copied through
    byte-for-byte), write the result, and emit a QuantizationSpec with the
    artifact digest. Shared by the RTN and AWQ harnesses — the only difference
    between them is ``transform`` and the recorded method/note."""
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    quantized = skipped = 0
    error_num = error_den = 0.0
    digest = hashlib.sha256()

    for path in sorted(input_dir.iterdir()):
        if path.name.startswith(".") or path.is_dir():
            continue
        if path.suffix != ".safetensors":
            shutil.copyfile(path, output_dir / path.name)
            continue
        metadata, tensors = read_safetensors(path)
        transformed = {}
        for name, (dtype, shape, raw) in tensors.items():
            if should_quantize(name, dtype, shape):
                original = _DECODE[dtype](raw).reshape(shape)
                dequantized = transform(name, original)
                error_num += float(np.abs(dequantized - original).sum())
                error_den += float(np.abs(original).sum())
                transformed[name] = (dtype, shape, _ENCODE[dtype](dequantized))
                quantized += 1
            else:
                transformed[name] = (dtype, shape, raw)
                skipped += 1
        write_safetensors(output_dir / path.name, metadata, transformed)
        print(f"{path.name}: {quantized} quantized, {skipped} passed through")

    for path in sorted(output_dir.glob("*.safetensors")):
        digest.update(path.read_bytes())

    spec = condition_pb2.QuantizationSpec(
        method=spec_method,
        weight_bits=bits,
        group_size=group_size,
        uniform=True,
        policy_note=policy_note,
        artifact_uri=str(output_dir),
        artifact_digest=digest.hexdigest(),
    )
    (output_dir / "quantization.textproto").write_text(text_format.MessageToString(spec))
    relative_error = error_num / error_den if error_den else 0.0
    print(f"done: {quantized} tensors quantized to w{bits} g{group_size}, "
          f"mean relative weight error {relative_error:.4f}")
    print(f"artifact digest {spec.artifact_digest}")
    return spec


def quantize_checkpoint(input_dir, output_dir, bits, group_size):
    """RTN fake-quant a checkpoint (data-free)."""
    note = (
        "fake-quant: weights quantized to the RTN grid (symmetric, "
        f"per-group g={group_size}, restricted range, round-half-even) and "
        "dequantized to the source dtype for kernel-free serving; "
        f"embeddings and output head at full precision; produced by "
        f"modelwelfare.quantize from {Path(input_dir).name}"
    )
    return _transform_checkpoint(
        input_dir, output_dir, lambda name, weights: rtn(weights, bits, group_size),
        condition_pb2.QUANT_METHOD_RTN, bits, group_size, note,
    )


def quantize_checkpoint_awq(input_dir, output_dir, bits, group_size, calib_by_weight):
    """AWQ fake-quant a checkpoint using per-weight calibration activations.

    ``calib_by_weight`` maps a weight-tensor name to its ``(n_samples,
    in_features)`` activation matrix, produced by the torch activation-capture
    pass (``modelwelfare_torch.awq_quantize``). Weights without captured
    calibration fall back to RTN (AWQ at alpha=0), so the artifact is always
    complete. Pure numpy — torch stays out of core."""
    missing = []

    def transform(name, weights):
        calib = calib_by_weight.get(name)
        if calib is None:
            missing.append(name)
            return rtn(weights, bits, group_size)
        return awq(weights, calib, bits, group_size)

    note = (
        "fake-quant: activation-aware (AWQ) per-input-channel scaling searched "
        f"against calibration activations, then RTN-quantized (symmetric "
        f"per-group g={group_size}) and dequantized for kernel-free serving; "
        "embeddings and output head at full precision; weights without captured "
        f"calibration fall back to RTN; produced by modelwelfare_torch.awq_quantize "
        f"from {Path(input_dir).name}"
    )
    spec = _transform_checkpoint(
        input_dir, output_dir, transform,
        condition_pb2.QUANT_METHOD_AWQ, bits, group_size, note,
    )
    if missing:
        print(f"AWQ: {len(missing)} quantizable weights had no calibration; used RTN fallback")
    return spec


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="HF checkpoint directory")
    parser.add_argument("--output", required=True)
    parser.add_argument("--bits", type=int, required=True, choices=(3, 4, 8))
    parser.add_argument("--group-size", type=int, default=128)
    args = parser.parse_args()
    quantize_checkpoint(args.input, args.output, args.bits, args.group_size)


if __name__ == "__main__":
    main()
