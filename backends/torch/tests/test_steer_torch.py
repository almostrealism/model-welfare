"""Hook-level steering tests against a fabricated torch model.

Skipped wherever torch is not installed (CI and dev laptops run the pure
suite in ``test_steer``); on the workbench these pin the hook mechanics
the pure tests cannot reach: exact injected offsets through a real
forward, bit-identity of the no-op path, per-position clamping under a
hook, tuple-shaped layer outputs, hook ordering against
``ResidualCapture`` (capture must read the post-injection state), and
the pre-hook point.
"""
import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")

from modelwelfare_torch.capture import ResidualCapture  # noqa: E402
from modelwelfare_torch.steer import SteeredInjection  # noqa: E402


class Passthrough(torch.nn.Module):
    def forward(self, hidden):
        return hidden


class TuplePassthrough(torch.nn.Module):
    def forward(self, hidden):
        return (hidden, None)


class FakeModel(torch.nn.Module):
    """The ``model.model.layers`` shape the hooks expect, nothing more."""

    def __init__(self, layer_modules):
        super().__init__()
        inner = torch.nn.Module()
        inner.layers = torch.nn.ModuleList(layer_modules)
        self.model = inner

    def forward(self, hidden):
        for layer in self.model.layers:
            output = layer(hidden)
            hidden = output[0] if isinstance(output, tuple) else output
        return hidden


def unit(index, size=4):
    direction = torch.zeros(size)
    direction[index] = 1.0
    return direction.numpy()


HIDDEN = torch.tensor([[[1.0, 2.0, 3.0, 4.0],
                        [5.0, -6.0, 7.0, 8.0]]])


def test_add_injects_exact_offset_and_propagates():
    model = FakeModel([Passthrough(), Passthrough()])
    with SteeredInjection(model, 0, "residual_post",
                          [("add", "d", 0.5)], {"d": unit(1)}):
        steered = model(HIDDEN.clone())
    expected = HIDDEN.clone()
    expected[..., 1] += 0.5
    assert torch.equal(steered, expected)


def test_no_ops_is_bit_identical_and_returns_none_from_hook():
    model = FakeModel([Passthrough()])
    plain = model(HIDDEN.clone())
    with SteeredInjection(model, 0, "residual_post", [], {}):
        hooked = model(HIDDEN.clone())
    assert torch.equal(plain, hooked)


def test_clamp_pins_every_position():
    model = FakeModel([Passthrough()])
    with SteeredInjection(model, 0, "residual_post",
                          [("clamp", "d", 2.5)], {"d": unit(1)}):
        steered = model(HIDDEN.clone())
    assert torch.allclose(steered[..., 1],
                          torch.full_like(steered[..., 1], 2.5))
    assert torch.equal(steered[..., [0, 2, 3]], HIDDEN[..., [0, 2, 3]])


def test_tuple_output_layers_keep_their_shape():
    model = FakeModel([TuplePassthrough()])
    with SteeredInjection(model, 0, "residual_post",
                          [("add", "d", 1.0)], {"d": unit(2)}):
        steered = model(HIDDEN.clone())
    expected = HIDDEN.clone()
    expected[..., 2] += 1.0
    assert torch.equal(steered, expected)


def test_capture_reads_post_injection_state():
    model = FakeModel([Passthrough(), Passthrough()])
    with SteeredInjection(model, 0, "residual_post",
                          [("add", "d", 0.5)], {"d": unit(1)}):
        with ResidualCapture(model, [0], "residual_post") as capture:
            model(HIDDEN.clone())
            captured = capture.taken()[0]
    expected = HIDDEN.clone()
    expected[..., 1] += 0.5
    assert torch.equal(torch.from_numpy(captured), expected)


def test_pre_hook_point_steers_layer_input():
    model = FakeModel([Passthrough()])
    with SteeredInjection(model, 0, "residual_pre",
                          [("add", "d", -1.0)], {"d": unit(0)}):
        steered = model(HIDDEN.clone())
    expected = HIDDEN.clone()
    expected[..., 0] -= 1.0
    assert torch.equal(steered, expected)


def test_bfloat16_hidden_keeps_its_dtype():
    model = FakeModel([Passthrough()])
    hidden = HIDDEN.clone().to(torch.bfloat16)
    with SteeredInjection(model, 0, "residual_post",
                          [("add", "d", 0.5)], {"d": unit(1)}):
        steered = model(hidden)
    assert steered.dtype == torch.bfloat16
    assert torch.allclose(steered.float()[..., 1],
                          hidden.float()[..., 1] + 0.5, atol=0.05)
