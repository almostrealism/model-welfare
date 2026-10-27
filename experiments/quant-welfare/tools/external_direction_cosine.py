#!/usr/bin/env python3
"""Cosine of saved steering directions against a published external vector.

Study 4's grader-type direction is extracted from this repository's own
contrast set; it is not the vector Betley, Treutlein and Dumas published
(``public-steering-vectors`` 0007, verifier-vs-human-grading, Qwen3.6-27B,
layer 36). Whether the two point the same way is a question with a number,
and the number belongs in a frozen artifact rather than only in a post's
prose. This tool computes it: for every ``name|L{layer}`` key in one of our
direction files, the cosine with the published vector and — when the
all-layer deltas file is given — with the external difference-of-means row
at the matched residual point.

Residual-point bookkeeping. The external format's "layer L" is the residual
stream at the INPUT of decoder block L (its meta.json says so), which is
the OUTPUT of block L-1. Our ``residual_post`` capture at layer L is the
output of block L. So our ``|L36`` key sits one block downstream of their
layer-36 row, and the matched external row for our layer L is their row
L+1. Both comparisons are reported: ``published`` (their single served row,
whatever our layer) and ``matched_point`` (their row L + offset).

The external files are not vendored. Their SHA-256 digests are checked
against the digests their own meta.json records, and the digests, the
source repository and the commit are written into the record, so the run
is reproducible from public files:

    curl -sS -H 'Accept: application/vnd.github.raw' -o vector.npy \\
      https://api.github.com/repos/johny-b/public-steering-vectors/contents/vectors/0007/vector.npy
    (likewise vectors/0007/meta.json and vectors/0007/deltas_all_layers.npy)
    python3 tools/external_direction_cosine.py \\
        --ours study4/directions/mediators-27b.safetensors \\
        --ours-meta study4/directions/mediators-27b.json \\
        --external vector.npy --external-meta meta.json \\
        --external-deltas deltas_all_layers.npy \\
        --source github.com/johny-b/public-steering-vectors@cb71586 \\
        --out study4/directions/betley-0007-cosine.json

Calibration-class instrument tooling: reads no result store and draws no
welfare conclusions.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from safetensors.numpy import load_file

RESIDUAL_POST_TO_BLOCK_INPUT = 1
"""Row offset from our ``residual_post`` layer L to the external
input-of-block index at the same residual point (their row L+1)."""


def sha256(path):
    """Hex SHA-256 of a file."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cosine(a, b):
    """Cosine similarity of two vectors, in float64."""
    a = np.asarray(a, dtype=np.float64).reshape(-1)
    b = np.asarray(b, dtype=np.float64).reshape(-1)
    scale = np.linalg.norm(a) * np.linalg.norm(b)
    if scale == 0.0:
        raise ValueError("cosine is undefined for a zero vector")
    return float(a @ b / scale)


def parse_key(key):
    """``(name, layer)`` from a ``name|L{layer}`` direction key."""
    name, _, suffix = key.rpartition("|L")
    if not name or not suffix.isdigit():
        raise ValueError(f"direction key {key!r} is not name|L<layer>")
    return name, int(suffix)


def chance_abs_cos_scale(dim):
    """Typical |cos| of two random directions in ``dim`` dimensions
    (1/sqrt(dim)): the scale against which a reported cosine is read."""
    return 1.0 / math.sqrt(dim)


def cosine_table(ours, external, deltas=None,
                 offset=RESIDUAL_POST_TO_BLOCK_INPUT):
    """{key: {layer, published, matched_point, matched_row}} for every
    direction in ``ours`` (a ``name|L{layer}`` -> vector mapping).

    ``published`` is the cosine with the single external vector.
    ``matched_point`` is the cosine with ``deltas[layer + offset]`` — the
    external difference-of-means row at the same residual point — or None
    when no deltas are given, the row does not exist, or the row is zero
    (the external file's row 0 is). Pure, so the bookkeeping is testable
    without files.
    """
    external = np.asarray(external, dtype=np.float64).reshape(-1)
    table = {}
    for key in sorted(ours):
        _, layer = parse_key(key)
        vector = np.asarray(ours[key], dtype=np.float64).reshape(-1)
        if vector.shape != external.shape:
            raise ValueError(f"{key}: shape {vector.shape} does not match the "
                             f"external vector {external.shape}")
        entry = {"layer": layer, "published": cosine(vector, external),
                 "matched_row": None, "matched_point": None}
        row = layer + offset
        if (deltas is not None and 0 <= row < len(deltas)
                and np.any(deltas[row])):
            entry["matched_row"] = row
            entry["matched_point"] = cosine(vector, deltas[row])
        table[key] = entry
    return table


def checked_digest(path, meta, field):
    """The file's SHA-256, required to equal ``meta[field]`` when the
    external metadata records one — a silently substituted file would make
    the record describe a comparison that never happened."""
    digest = sha256(path)
    recorded = meta.get(field)
    if recorded and recorded != digest:
        raise SystemExit(f"{path}: sha256 {digest} does not match the "
                         f"{field} recorded in its meta.json ({recorded})")
    return digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ours", required=True,
                        help="safetensors of our unit directions (name|L{layer})")
    parser.add_argument("--ours-meta",
                        help="the JSON summary written beside it (point, "
                             "layers, extraction pairs) — copied into the record")
    parser.add_argument("--ours-convention", default="",
                        help="one line on how our directions were read "
                             "(position, pooling, template flags)")
    parser.add_argument("--external", required=True,
                        help="the published single-layer vector (.npy)")
    parser.add_argument("--external-meta",
                        help="its meta.json (digests, layer, conventions)")
    parser.add_argument("--external-deltas",
                        help="the all-layer difference-of-means file (.npy, "
                             "rows indexed by input-of-block layer)")
    parser.add_argument("--offset", type=int, default=RESIDUAL_POST_TO_BLOCK_INPUT,
                        help="external row for our layer L is L + offset")
    parser.add_argument("--source", default="",
                        help="where the external files came from "
                             "(repository@commit)")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    ours = load_file(args.ours)
    ours_meta = json.loads(Path(args.ours_meta).read_text()) if args.ours_meta else {}
    external_meta = (json.loads(Path(args.external_meta).read_text())
                     if args.external_meta else {})
    external = np.load(args.external, allow_pickle=False)
    deltas = (np.load(args.external_deltas, allow_pickle=False)
              if args.external_deltas else None)

    table = cosine_table(ours, external, deltas, args.offset)
    dim = int(external.reshape(-1).shape[0])

    external_record = {
        "source": args.source,
        "vector_file": Path(args.external).name,
        "vector_sha256": checked_digest(args.external, external_meta,
                                        "vector_npy_sha256"),
    }
    if deltas is not None:
        external_record["deltas_file"] = Path(args.external_deltas).name
        external_record["deltas_sha256"] = checked_digest(
            args.external_deltas, external_meta, "deltas_npy_sha256")
        external_record["deltas_rows"] = int(deltas.shape[0])
    for field in ("id_str", "name", "model", "layer", "hidden_size", "n_layers",
                  "n_pos", "n_neg", "vector_norm", "activation_norm_at_layer",
                  "position_convention", "sign_convention", "created_at"):
        if field in external_meta:
            external_record[field] = external_meta[field]

    ours_record = {
        "file": str(args.ours),
        "sha256": sha256(args.ours),
        "point": ours_meta.get("point"),
        "layers": ours_meta.get("layers"),
        "convention": args.ours_convention,
        "extract_pairs": {name: len(spec.get("extract_pairs", []))
                          for name, spec in ours_meta.get("directions", {}).items()},
    }

    record = {
        "ours": ours_record,
        "external": external_record,
        "residual_point_offset": args.offset,
        "residual_point_note": (
            "external row L is the residual stream at the input of block L; "
            "our residual_post layer L is the output of block L, so the "
            "matched external row for our layer L is L + offset"),
        "dim": dim,
        "chance_abs_cos_scale": chance_abs_cos_scale(dim),
        "cosines": table,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(record, indent=1) + "\n")
    for key, entry in table.items():
        matched = ("" if entry["matched_point"] is None else
                   f"  matched row {entry['matched_row']}: {entry['matched_point']:+.4f}")
        print(f"{key}: cos with published vector {entry['published']:+.4f}{matched}")
    print(f"chance scale 1/sqrt({dim}) = {record['chance_abs_cos_scale']:.4f}; "
          f"record -> {args.out}")


if __name__ == "__main__":
    main()
