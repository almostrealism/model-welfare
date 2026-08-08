"""Quantization math and checkpoint-transform tests."""

import json

import numpy as np
import pytest

from modelwelfare.quantize import (
    bf16_to_f32,
    f32_to_bf16,
    quantize_checkpoint,
    read_safetensors,
    rtn,
    should_quantize,
    write_safetensors,
)


def test_bf16_roundtrip_known_bits():
    values = np.array([1.0, -2.5, 0.0, 3.140625], dtype=np.float32)
    raw = f32_to_bf16(values)
    assert np.frombuffer(raw, dtype=np.uint16)[0] == 0x3F80
    back = bf16_to_f32(raw)
    assert np.allclose(back, values, rtol=1 / 128)
    assert back[0] == 1.0 and back[2] == 0.0


def test_bf16_round_to_nearest_even():
    exact = bf16_to_f32(f32_to_bf16(np.array([1.0 + 1 / 256], dtype=np.float32)))
    assert exact[0] in (1.0, 1.0 + 1 / 128)


def test_rtn_values_lie_on_grid():
    rng = np.random.default_rng(7)
    weights = rng.standard_normal((8, 16)).astype(np.float32)
    dequantized = rtn(weights, bits=4, group_size=8)
    grouped = dequantized.reshape(8, 2, 8)
    scale = np.abs(weights.reshape(8, 2, 8)).max(axis=2, keepdims=True) / 7
    steps = grouped / scale
    assert np.allclose(steps, np.round(steps), atol=1e-5)
    assert np.abs(np.round(steps)).max() <= 7


def test_rtn_error_orders_by_bits():
    rng = np.random.default_rng(11)
    weights = rng.standard_normal((32, 128)).astype(np.float32)
    errors = {
        bits: np.abs(rtn(weights, bits, 128) - weights).mean() for bits in (3, 4, 8)
    }
    assert errors[3] > errors[4] > errors[8]


def test_rtn_idempotent():
    rng = np.random.default_rng(3)
    weights = rng.standard_normal((4, 32)).astype(np.float32)
    once = rtn(weights, 4, 16)
    twice = rtn(once, 4, 16)
    assert np.allclose(once, twice, atol=1e-6)


def test_rtn_partial_group_padding():
    rng = np.random.default_rng(5)
    weights = rng.standard_normal((3, 10)).astype(np.float32)
    dequantized = rtn(weights, 4, group_size=4)
    assert dequantized.shape == (3, 10)


def test_rtn_zero_group_safe():
    weights = np.zeros((2, 8), dtype=np.float32)
    assert np.array_equal(rtn(weights, 4, 4), weights)


def test_safetensors_roundtrip_and_library_compat(tmp_path):
    tensors = {
        "a.weight": ("F32", [2, 3], np.arange(6, dtype=np.float32).tobytes()),
        "b.weight": ("BF16", [2, 2], f32_to_bf16(np.array([1.0, -1.0, 0.5, 2.0], dtype=np.float32))),
    }
    path = tmp_path / "t.safetensors"
    write_safetensors(path, {"origin": "test"}, tensors)
    metadata, loaded = read_safetensors(path)
    assert metadata == {"origin": "test"}
    assert loaded["a.weight"] == tensors["a.weight"]
    assert loaded["b.weight"][2] == tensors["b.weight"][2]

    from safetensors import safe_open

    with safe_open(str(path), framework="np") as handle:
        assert np.array_equal(
            handle.get_tensor("a.weight"), np.arange(6, dtype=np.float32).reshape(2, 3)
        )


def test_selection_rules():
    assert should_quantize("model.layers.0.self_attn.q_proj.weight", "BF16", [4, 4])
    assert not should_quantize("model.embed_tokens.weight", "BF16", [4, 4])
    assert not should_quantize("lm_head.weight", "BF16", [4, 4])
    assert not should_quantize("model.norm.weight", "BF16", [4])
    assert not should_quantize("model.layers.0.self_attn.q_proj.bias", "BF16", [4, 4])


def test_checkpoint_transform_end_to_end(tmp_path):
    source = tmp_path / "src"
    output = tmp_path / "out"
    source.mkdir()
    rng = np.random.default_rng(9)
    proj = rng.standard_normal((8, 16)).astype(np.float32)
    embed = rng.standard_normal((8, 16)).astype(np.float32)
    write_safetensors(source / "model.safetensors", None, {
        "model.layers.0.self_attn.q_proj.weight": ("BF16", [8, 16], f32_to_bf16(proj)),
        "model.embed_tokens.weight": ("BF16", [8, 16], f32_to_bf16(embed)),
    })
    (source / "config.json").write_text(json.dumps({"model_type": "test"}))

    spec = quantize_checkpoint(source, output, bits=4, group_size=8)

    assert (output / "config.json").read_text() == json.dumps({"model_type": "test"})
    _, transformed = read_safetensors(output / "model.safetensors")
    assert transformed["model.embed_tokens.weight"][2] == f32_to_bf16(embed)
    changed = bf16_to_f32(transformed["model.layers.0.self_attn.q_proj.weight"][2])
    assert not np.array_equal(changed, bf16_to_f32(f32_to_bf16(proj)))
    assert spec.weight_bits == 4
    assert spec.artifact_digest
    assert (output / "quantization.textproto").is_file()


def test_bits_flag_bounds():
    with pytest.raises(Exception):
        rtn(np.zeros((2, 4), dtype=np.float32), bits=1, group_size=4)
