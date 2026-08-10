"""First-party AWQ: torch activation capture + the numpy AWQ core.

Runs on a host with torch/transformers (the quantization workbench). It loads
the checkpoint, captures each quantizable linear's input activations over a
fixed calibration corpus via forward pre-hooks, then hands those activations to
``modelwelfare.quantize.quantize_checkpoint_awq`` (pure numpy) which applies the
AWQ core per weight and writes an AWQ fake-quant checkpoint + spec, mirroring
the RTN harness. torch lives only in this module; core stays numpy-pure.

    python -m modelwelfare_torch.awq_quantize \
        --input ~/models/SmolLM3-3B --output ~/models/smollm3-awq-w4-g128 \
        --bits 4 --group-size 128

The calibration corpus (``backends/torch/awq_calibration.txt`` by default) is
committed and fixed, so the artifact is reproducible; record it with the spec.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "core/src"))

from modelwelfare.quantize import quantize_checkpoint_awq  # noqa: E402
from modelwelfare.quantize import SKIP_PATTERNS  # noqa: E402

DEFAULT_CALIB = REPO / "backends" / "torch" / "awq_calibration.txt"


def _target_linears(model):
    """Names of nn.Linear modules whose weight the RTN/AWQ harness would
    quantize: 2-D projections, excluding the embedding and output head."""
    targets = {}
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.Linear) and not any(
            pattern in name for pattern in SKIP_PATTERNS
        ):
            targets[name] = name + ".weight"
    return targets


def capture_activations(model_dir, calib_path, max_rows, max_seq, device):
    """Return {weight_name: (n_rows, in_features) float32} of inputs each
    quantizable linear saw over the calibration corpus, capped at max_rows."""
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForCausalLM.from_pretrained(model_dir, torch_dtype=torch.bfloat16)
    model.to(device).eval()

    targets = _target_linears(model)
    modules = dict(model.named_modules())
    store = {name: [] for name in targets}
    counts = {name: 0 for name in targets}

    def make_hook(name):
        def hook(module, inputs):
            if counts[name] >= max_rows:
                return
            activation = inputs[0]
            flat = activation.reshape(-1, activation.shape[-1]).float().detach().cpu().numpy()
            take = min(max_rows - counts[name], flat.shape[0])
            if take > 0:
                store[name].append(flat[:take])
                counts[name] += take
        return hook

    handles = [modules[name].register_forward_pre_hook(make_hook(name)) for name in targets]
    lines = [line.strip() for line in Path(calib_path).read_text().splitlines() if line.strip()]
    print(f"capturing over {len(lines)} calibration sequences on {device} "
          f"for {len(targets)} linears (cap {max_rows} rows each)")
    with torch.no_grad():
        for line in lines:
            batch = tokenizer(line, return_tensors="pt", truncation=True,
                              max_length=max_seq).to(device)
            model(**batch)
    for handle in handles:
        handle.remove()

    calib_by_weight = {}
    for name, weight_name in targets.items():
        if store[name]:
            calib_by_weight[weight_name] = np.concatenate(store[name], axis=0)
    return calib_by_weight


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True, help="HF checkpoint directory")
    parser.add_argument("--output", required=True)
    parser.add_argument("--bits", type=int, default=4, choices=(3, 4, 8))
    parser.add_argument("--group-size", type=int, default=128)
    parser.add_argument("--calib", default=str(DEFAULT_CALIB))
    parser.add_argument("--max-rows", type=int, default=512,
                        help="activation rows kept per linear for the AWQ search")
    parser.add_argument("--max-seq", type=int, default=512)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    device = args.device
    if device == "cuda" and not torch.cuda.is_available():
        print("cuda not available; falling back to cpu")
        device = "cpu"

    calib = capture_activations(args.input, args.calib, args.max_rows, args.max_seq, device)
    print(f"captured calibration for {len(calib)} weights; quantizing (AWQ w{args.bits})")
    quantize_checkpoint_awq(args.input, args.output, args.bits, args.group_size, calib)


if __name__ == "__main__":
    main()
