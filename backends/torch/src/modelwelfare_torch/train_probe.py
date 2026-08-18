"""Linear-probe training on pooled activations (Study 2 calibration).

Trains one logistic probe per (probe, layer) group in a dataset produced by
``tools/tier2_calibrate.py --probe-data``: standardize on the training
split, minimize binary cross-entropy with Adam, early-stop on validation
AUROC. The architecture is deliberately a single linear layer — the point
of R1 is geometry transfer, not classifier capacity (REGISTRATION §3.5).

Standalone by design (torch + numpy + stdlib), like the other workbench
CLIs: it runs where the GPUs are without a repository checkout. The AUROC
here is the same rank statistic as ``modelwelfare.stats.auroc``,
re-implemented locally as the price of standalone-ness.

    python3 train_probe.py --data probe-data.npz --out probes-bf16

Writes ``<out>.safetensors`` (per group: weight, bias, and the train-split
feature mean/std the weights assume) and ``<out>.json`` (per-group train and
validation AUROC, epochs, and sizes).
"""
import argparse
import json

import numpy as np
import torch
from safetensors.numpy import save_file

MAX_EPOCHS = 200
PATIENCE = 15
LEARNING_RATE = 1e-3
BATCH = 64


def auroc(scores, labels):
    scores = np.asarray(scores, float)
    labels = np.asarray(labels, int)
    positives = int(labels.sum())
    negatives = int(len(labels) - positives)
    if positives == 0 or negatives == 0:
        return float("nan")
    order = scores.argsort(kind="mergesort")
    ranks = np.empty(len(scores), float)
    ranks[order] = np.arange(1, len(scores) + 1)
    for value in np.unique(scores):
        mask = scores == value
        if mask.sum() > 1:
            ranks[mask] = ranks[mask].mean()
    u_statistic = ranks[labels == 1].sum() - positives * (positives + 1) / 2.0
    return float(u_statistic / (positives * negatives))


def train_group(x_train, y_train, x_val, y_val, device, seed=0):
    torch.manual_seed(seed)
    mean = x_train.mean(axis=0)
    std = x_train.std(axis=0) + 1e-6
    x_train_t = torch.tensor((x_train - mean) / std, dtype=torch.float32,
                             device=device)
    y_train_t = torch.tensor(y_train, dtype=torch.float32, device=device)
    x_val_t = torch.tensor((x_val - mean) / std, dtype=torch.float32,
                           device=device)

    probe = torch.nn.Linear(x_train.shape[1], 1).to(device)
    optimizer = torch.optim.Adam(probe.parameters(), lr=LEARNING_RATE)
    loss_fn = torch.nn.BCEWithLogitsLoss()

    best = {"val_auroc": -1.0, "epoch": 0, "state": None}
    since_best = 0
    for epoch in range(1, MAX_EPOCHS + 1):
        permutation = torch.randperm(len(x_train_t), device=device)
        probe.train()
        for start in range(0, len(permutation), BATCH):
            batch = permutation[start:start + BATCH]
            optimizer.zero_grad()
            loss = loss_fn(probe(x_train_t[batch]).squeeze(-1), y_train_t[batch])
            loss.backward()
            optimizer.step()
        probe.eval()
        with torch.no_grad():
            val_scores = probe(x_val_t).squeeze(-1).cpu().numpy()
        val_auroc = auroc(val_scores, y_val)
        if val_auroc > best["val_auroc"]:
            best = {"val_auroc": val_auroc, "epoch": epoch,
                    "state": {name: parameter.detach().cpu().numpy().copy()
                              for name, parameter in probe.named_parameters()}}
            since_best = 0
        else:
            since_best += 1
            if since_best >= PATIENCE:
                break

    with torch.no_grad():
        for name, parameter in probe.named_parameters():
            parameter.copy_(torch.tensor(best["state"][name], device=device))
        train_scores = probe(x_train_t).squeeze(-1).cpu().numpy()
    return {
        "weight": best["state"]["weight"].reshape(-1).astype(np.float32),
        "bias": best["state"]["bias"].astype(np.float32),
        "feature_mean": mean.astype(np.float32),
        "feature_std": std.astype(np.float32),
    }, {
        "val_auroc": best["val_auroc"], "best_epoch": best["epoch"],
        "train_auroc": auroc(train_scores, y_train),
        "n_train": int(len(y_train)), "n_val": int(len(y_val)),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="probe-data .npz")
    parser.add_argument("--out", required=True, help="output path stem")
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    data = np.load(args.data)
    groups = sorted({key.rsplit("|", 1)[0] for key in data.files})

    tensors, summary = {}, {}
    for group in groups:
        result, stats = train_group(
            data[f"{group}|X_train"], data[f"{group}|y_train"],
            data[f"{group}|X_val"], data[f"{group}|y_val"], device)
        for name, value in result.items():
            tensors[f"{group}|{name}"] = value
        summary[group] = stats
        print(f"{group}: val AUROC={stats['val_auroc']:.3f} "
              f"(train {stats['train_auroc']:.3f}, epoch {stats['best_epoch']}, "
              f"n={stats['n_train']}/{stats['n_val']})")

    save_file(tensors, args.out + ".safetensors")
    with open(args.out + ".json", "w") as handle:
        json.dump(summary, handle, indent=1)
    print(f"wrote {args.out}.safetensors and .json")


if __name__ == "__main__":
    main()
