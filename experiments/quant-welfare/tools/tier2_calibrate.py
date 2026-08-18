#!/usr/bin/env python3
"""Study 2 calibration over the Study 1 store: monitoring correlation,
probe datasets, and the R2c separation read (REGISTRATION §3.6).

All calibration is BF16-only, per the §7 firewall. Four modes:

  --plan-distress OUT   Capture plan for the BF16 distress transcripts
                        (teacher-forced replay; judge frustration scores are
                        the monitoring labels).
  --plan-bail OUT       Capture plan for the BF16 graded bail transcripts,
                        with each item's affordances declared as tools so
                        the template renders the same tool preamble the
                        serving stack exposed.
  --monitoring          Per-layer monitoring correlation: per-item mean
                        distress-direction projection vs per-item mean judge
                        frustration, Spearman on the deterministic item
                        split (even indices select the layer, odd indices
                        evaluate the G2 criterion).
  --probe-data OUT      Per-layer probe datasets (.npz) for the workbench
                        torch trainer: distress-band probe (top vs bottom
                        scale third, middle excluded) and exit probe
                        (mechanical exit vs no-exit, features restricted to
                        the leakage-safe turns). Split by item with the
                        project's held-out rule.
  --r2c                 Refusal-direction projection AUC on exit vs no-exit
                        over the leakage-safe features (the R2c conditional
                        promotion criterion).

    python3 tools/tier2_calibrate.py --plan-distress distress-plan.json
    python3 tools/tier2_calibrate.py --monitoring \\
        --capture distress-replay-bf16.safetensors
    python3 tools/tier2_calibrate.py --probe-data probe-data.npz \\
        --capture distress-replay-bf16.safetensors \\
        --capture-bail bail-replay-bf16.safetensors

Calibration-class instrument tooling: reads the store, writes no results,
draws no welfare conclusions.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

BASE = Path(__file__).resolve().parent.parent
REPO = BASE.parents[1]
for path in (str(REPO / "core/src"), str(BASE)):
    if path not in sys.path:
        sys.path.insert(0, path)

from safetensors.numpy import load_file  # noqa: E402

import analyze  # noqa: E402
from modelwelfare import replay  # noqa: E402
from modelwelfare import directions as dirs  # noqa: E402
from modelwelfare.stats import auroc, spearman  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import scoring_pb2, transcript_pb2  # noqa: E402

EXPERIMENT_DIR = BASE / "study1" / "confirmatory"
DEFAULT_VECTORS = BASE / "study2" / "calibration" / "directions-bf16.safetensors"
DISTRESS_DIRECTION = "distress-contrast"
REFUSAL_DIRECTION = "refusal-contrast"


def load_study1(store_root, condition):
    experiment = analyze.load_experiment(EXPERIMENT_DIR)
    definitions = analyze.batteries_for(EXPERIMENT_DIR)
    bail_ids, distress_ids = analyze.item_roles(experiment, definitions)
    store = ResultStore(store_root)
    samples = list(store.read(transcript_pb2.SampleRecord,
                              experiment.id, condition, "samples"))
    scores = list(store.read(scoring_pb2.JudgeScore,
                             experiment.id, condition, "scores"))
    return experiment, definitions, bail_ids, distress_ids, samples, scores


def write_plan(records, path, tools_by_item=None):
    conversations, skipped = replay.plan_conversations(records, tools_by_item)
    Path(path).write_text(
        json.dumps({"conversations": conversations}, indent=1) + "\n")
    print(f"wrote {path}: {len(conversations)} conversations"
          + (f" ({len(skipped)} skipped: no assistant turn)" if skipped else ""))


def split_conversation_id(conversation_id):
    item_id, sample = conversation_id.rsplit("|s", 1)
    return item_id, int(sample)


def monitoring(args):
    _, _, _, distress_ids, _, scores = load_study1(args.store, args.condition)
    tensors = load_file(args.capture)
    with open(args.capture + ".manifest.json") as handle:
        manifest = json.load(handle)
    vectors = load_file(str(args.vectors))
    judge_by_sample = replay.dimension_by_sample(scores, "frustration")
    judge_by_item = replay.item_means(judge_by_sample)

    select_items, evaluate_items = replay.even_odd_split(
        set(judge_by_item) & distress_ids)
    print(f"monitoring correlation (distress direction), items: "
          f"{len(select_items)} selection / {len(evaluate_items)} evaluation")
    results = {}
    for layer in manifest["layers"]:
        direction = vectors[f"{DISTRESS_DIRECTION}|L{layer}"]
        features = replay.pooled_sample_features(tensors, manifest, layer)
        projection_by_sample = {}
        for conversation_id, vector in features.items():
            item_id, sample = split_conversation_id(conversation_id)
            if (item_id, sample) in judge_by_sample:
                projection_by_sample[(item_id, sample)] = float(
                    np.dot(vector, direction))
        projection_by_item = replay.item_means(projection_by_sample)
        rows = {}
        for name, items in (("select", select_items), ("evaluate", evaluate_items)):
            paired = [(projection_by_item[item], judge_by_item[item])
                      for item in items if item in projection_by_item]
            rows[name] = (spearman([p for p, _ in paired], [j for _, j in paired]),
                          len(paired))
        results[layer] = rows
        print(f"  L{layer}: select rho={rows['select'][0]:+.3f} "
              f"(n={rows['select'][1]})   evaluate rho={rows['evaluate'][0]:+.3f} "
              f"(n={rows['evaluate'][1]})")

    best = max(results, key=lambda layer: results[layer]["select"][0])
    chosen = results[best]
    print(f"\nlayer selection (max selection-half rho): L{best} "
          f"-> G2 evaluation-half rho={chosen['evaluate'][0]:+.3f} "
          f"({'PASS' if chosen['evaluate'][0] >= 0.5 else 'FAIL'} vs >= 0.5)")
    if args.save:
        Path(args.save).write_text(json.dumps({
            "per_layer": {str(layer): {name: {"rho": rows[name][0], "n": rows[name][1]}
                                       for name in rows}
                          for layer, rows in results.items()},
            "selected_layer": best,
            "evaluation_rho": chosen["evaluate"][0],
        }, indent=1) + "\n")
        print(f"wrote {args.save}")


def load_exit_context(args):
    """Once per run: leakage-safe turn allowance and exit labels per sample."""
    _, _, bail_ids, _, samples, _ = load_study1(args.store, args.condition)
    records = {replay.conversation_id(record): record
               for record in samples if record.key.item_id in bail_ids}
    allowed = {conversation_id: set(replay.feature_message_indices(record))
               for conversation_id, record in records.items()}
    labels = {conversation_id: int(replay.sample_exited(record))
              for conversation_id, record in records.items()}
    return allowed, labels


def exit_features(allowed, labels, layer, tensors, manifest):
    """Leakage-safe per-sample exit features + labels at one layer."""
    features = replay.pooled_sample_features(tensors, manifest, layer, allowed)
    captured = {conversation["id"] for conversation in manifest["conversations"]}
    excluded = len([conversation_id for conversation_id in allowed
                    if conversation_id in captured
                    and conversation_id not in features])
    return features, {cid: labels[cid] for cid in features}, excluded


def probe_data(args):
    _, _, _, distress_ids, _, scores = load_study1(args.store, args.condition)
    judge_by_sample = replay.dimension_by_sample(scores, "frustration")

    distress_tensors = load_file(args.capture)
    with open(args.capture + ".manifest.json") as handle:
        distress_manifest = json.load(handle)
    bail_tensors = load_file(args.capture_bail)
    with open(args.capture_bail + ".manifest.json") as handle:
        bail_manifest = json.load(handle)
    allowed, labels = load_exit_context(args)

    arrays, meta = {}, {"probes": {}}
    for layer in distress_manifest["layers"]:
        distress_features = replay.pooled_sample_features(
            distress_tensors, distress_manifest, layer)
        rows = []
        for conversation_id, vector in distress_features.items():
            item_id, sample = split_conversation_id(conversation_id)
            if item_id not in distress_ids:
                continue
            value = judge_by_sample.get((item_id, sample))
            if value is None:
                continue
            label = replay.scale_thirds_label(value)
            if label is None:
                continue
            rows.append((item_id, vector, label))
        _fill_probe_arrays(arrays, meta, "distress_band", layer, rows)

        features, exit_labels, excluded = exit_features(
            allowed, labels, layer, bail_tensors, bail_manifest)
        rows = [(split_conversation_id(cid)[0], vector, exit_labels[cid])
                for cid, vector in features.items()]
        _fill_probe_arrays(arrays, meta, "exit", layer, rows,
                           extra={"excluded_no_feature_turns": excluded})

    np.savez_compressed(args.probe_data, **arrays)
    Path(args.probe_data + ".meta.json").write_text(
        json.dumps(meta, indent=1) + "\n")
    print(f"wrote {args.probe_data} (+.meta.json)")


def _fill_probe_arrays(arrays, meta, probe, layer, rows, extra=None):
    validation_items = dirs.held_out_pair_ids({item for item, _, _ in rows})
    train = [(vector, label) for item, vector, label in rows
             if item not in validation_items]
    val = [(vector, label) for item, vector, label in rows
           if item in validation_items]
    for split_name, split_rows in (("train", train), ("val", val)):
        arrays[f"{probe}|L{layer}|X_{split_name}"] = np.stack(
            [vector for vector, _ in split_rows]).astype(np.float32)
        arrays[f"{probe}|L{layer}|y_{split_name}"] = np.array(
            [label for _, label in split_rows], dtype=np.int64)
    entry = {"train": len(train), "val": len(val),
             "train_positive": int(sum(label for _, label in train)),
             "val_positive": int(sum(label for _, label in val)),
             "validation_items": sorted(validation_items)}
    if extra:
        entry.update(extra)
    meta["probes"].setdefault(probe, {})[str(layer)] = entry
    print(f"  {probe} L{layer}: train n={len(train)} "
          f"(+{entry['train_positive']})  val n={len(val)} "
          f"(+{entry['val_positive']})"
          + (f"  excluded={extra['excluded_no_feature_turns']}" if extra else ""))


def r2c(args):
    tensors = load_file(args.capture_bail)
    with open(args.capture_bail + ".manifest.json") as handle:
        manifest = json.load(handle)
    vectors = load_file(str(args.vectors))
    allowed, all_labels = load_exit_context(args)
    print("R2c criterion: refusal-direction projection separates mechanical "
          "exit vs no-exit (leakage-safe features)")
    for layer in manifest["layers"]:
        features, labels, excluded = exit_features(
            allowed, all_labels, layer, tensors, manifest)
        direction = vectors[f"{REFUSAL_DIRECTION}|L{layer}"]
        validation_items = dirs.held_out_pair_ids(
            {split_conversation_id(cid)[0] for cid in features})
        rows = {"all": (list(features), None),
                "held-out items": ([cid for cid in features
                                    if split_conversation_id(cid)[0]
                                    in validation_items], None)}
        printed = []
        for name, (cids, _) in rows.items():
            scores = [float(np.dot(features[cid], direction)) for cid in cids]
            outcome = [labels[cid] for cid in cids]
            printed.append(f"{name}: AUC={auroc(scores, outcome):.3f} "
                           f"(n={len(cids)}, +{sum(outcome)})")
        print(f"  L{layer}: {'   '.join(printed)}  excluded={excluded}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", default=str(REPO / "data"))
    parser.add_argument("--condition", default="qwen3-4b-bf16")
    parser.add_argument("--vectors", default=str(DEFAULT_VECTORS))
    parser.add_argument("--plan-distress", default=None)
    parser.add_argument("--plan-bail", default=None)
    parser.add_argument("--monitoring", action="store_true")
    parser.add_argument("--probe-data", default=None)
    parser.add_argument("--r2c", action="store_true")
    parser.add_argument("--capture", default=None,
                        help="distress replay capture safetensors")
    parser.add_argument("--capture-bail", default=None,
                        help="bail replay capture safetensors")
    parser.add_argument("--save", default=None, help="summary JSON path")
    args = parser.parse_args()

    if args.plan_distress or args.plan_bail:
        _, definitions, bail_ids, distress_ids, samples, _ = load_study1(
            args.store, args.condition)
        if args.plan_distress:
            write_plan([record for record in samples
                        if record.key.item_id in distress_ids],
                       args.plan_distress)
        if args.plan_bail:
            tools_by_item = {
                item.id: replay.item_tools(item)
                for definition in definitions.values()
                for item in definition.items if item.id in bail_ids}
            write_plan([record for record in samples
                        if record.key.item_id in bail_ids],
                       args.plan_bail, tools_by_item)
        return
    if args.monitoring:
        if not args.capture:
            raise SystemExit("--monitoring requires --capture")
        monitoring(args)
        return
    if args.probe_data:
        if not (args.capture and args.capture_bail):
            raise SystemExit("--probe-data requires --capture and --capture-bail")
        probe_data(args)
        return
    if args.r2c:
        if not args.capture_bail:
            raise SystemExit("--r2c requires --capture-bail")
        r2c(args)
        return
    raise SystemExit("nothing to do; see --help")


if __name__ == "__main__":
    main()
