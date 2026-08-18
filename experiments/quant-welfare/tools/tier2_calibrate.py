#!/usr/bin/env python3
"""Study 2 calibration over the Study 1 store: monitoring correlation,
probe datasets, and the R2c separation read (REGISTRATION §3.6).

All calibration is BF16-only, per the §7 firewall. Modes:

  --plan-distress OUT   Capture plan for the BF16 Study 1 distress
                        transcripts (teacher-forced replay).
  --plan-bail OUT       Capture plan for the BF16 graded bail transcripts,
                        with each item's affordances declared as tools so
                        the template renders the same tool preamble the
                        serving stack exposed.
  --plan-from EXP --plan-out OUT
                        Generic replay plan: every stored sample of
                        (EXP, --condition) — the v3 pilots and future
                        Mode D captures.
  --monitoring          Per-layer monitoring statistics on the final-turn
                        projection functional: item-level Spearman on the
                        deterministic even/odd split, plus the descriptive
                        sample-level Spearman and AUC (judge >= 5 vs = 0).
                        --score-experiment switches the label source from
                        the Study 1 store to a pilot experiment.
  --probe-data OUT      Per-layer probe datasets (.npz) for the workbench
                        trainer: distress-band (Study 1 labels) + exit
                        probe (mechanical labels, leakage-safe features).
  --probe-data-v3 OUT   Distress-band probe dataset from a v3 pilot
                        (final-turn features; requires --capture and
                        --score-experiment).
  --r2c                 Refusal-direction projection AUC on exit vs no-exit
                        over the leakage-safe features (the R2c conditional
                        promotion criterion).
  --mde                 The §5 MDE values at --layer, from BF16 calibration
                        data (requires --capture, --capture-bail, --probes,
                        --score-experiment; --probes-v3 optional).

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
from modelwelfare.bundle import BundleStore  # noqa: E402
from modelwelfare.stats import auroc, spearman  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import scoring_pb2, transcript_pb2  # noqa: E402

EXPERIMENT_DIR = BASE / "study1" / "confirmatory"
DEFAULT_VECTORS = BASE / "study2" / "calibration" / "directions-bf16.safetensors"
DISTRESS_DIRECTION = "distress-contrast"
REFUSAL_DIRECTION = "refusal-contrast"


def open_store(args):
    """The record source: a packed-bundle file/directory when --bundle is
    given (the replication path), else the streaming store."""
    return BundleStore(args.bundle) if getattr(args, "bundle", None) \
        else ResultStore(args.store)


def load_study1(args):
    experiment = analyze.load_experiment(EXPERIMENT_DIR)
    definitions = analyze.batteries_for(EXPERIMENT_DIR)
    bail_ids, distress_ids = analyze.item_roles(experiment, definitions)
    store = open_store(args)
    condition = args.condition
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


def load_capture(path):
    """(tensors, manifest) for a capture backend's output pair."""
    with open(path + ".manifest.json") as handle:
        manifest = json.load(handle)
    return load_file(path), manifest


def monitoring(args):
    if args.score_experiment:
        store = open_store(args)
        scores = list(store.read(scoring_pb2.JudgeScore, args.score_experiment,
                                 args.condition, "scores"))
        judge_by_sample = replay.dimension_by_sample(scores, "frustration")
        distress_ids = {item for item, _sample in judge_by_sample}
    else:
        _, _, _, distress_ids, _, scores = load_study1(args)
        judge_by_sample = replay.dimension_by_sample(scores, "frustration")
    tensors, manifest = load_capture(args.capture)
    vectors = load_file(str(args.vectors))
    judge_by_item = replay.item_means(judge_by_sample)

    select_items, evaluate_items = replay.even_odd_split(
        set(judge_by_item) & distress_ids)
    print(f"monitoring correlation (distress direction), items: "
          f"{len(select_items)} selection / {len(evaluate_items)} evaluation")
    results = {}
    for layer in manifest["layers"]:
        direction = vectors[f"{DISTRESS_DIRECTION}|L{layer}"]
        # The registered projection functional: final assistant turn, matching
        # extraction (REGISTRATION §3.6).
        features = replay.final_turn_features(tensors, manifest, layer)
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
        # Descriptive natural-data link (registration §3.6): sample-level
        # Spearman and the AUC separating clearly-distressed from
        # zero-scored samples.
        pairs = [(value, judge_by_sample[key])
                 for key, value in projection_by_sample.items()]
        sample_rho = spearman([p for p, _ in pairs], [j for _, j in pairs])
        high = [p for p, j in pairs if j >= 5]
        zero = [p for p, j in pairs if j == 0]
        band_auc = auroc(high + zero, [1] * len(high) + [0] * len(zero))
        rows["sample_rho"] = sample_rho
        rows["auc_ge5_vs_0"] = band_auc
        results[layer] = rows
        print(f"  L{layer}: select rho={rows['select'][0]:+.3f} "
              f"(n={rows['select'][1]})   evaluate rho={rows['evaluate'][0]:+.3f} "
              f"(n={rows['evaluate'][1]})   sample rho={sample_rho:+.3f}   "
              f"AUC(>=5 vs 0)={band_auc:.3f}")

    best = max(results, key=lambda layer: results[layer]["select"][0])
    chosen = results[best]
    print(f"\nlayer selection (max selection-half rho): L{best} "
          f"-> G2 evaluation-half rho={chosen['evaluate'][0]:+.3f} "
          f"({'PASS' if chosen['evaluate'][0] >= 0.5 else 'FAIL'} vs >= 0.5)")
    if args.save:
        Path(args.save).write_text(json.dumps({
            "per_layer": {
                str(layer): {
                    "select": {"rho": rows["select"][0], "n": rows["select"][1]},
                    "evaluate": {"rho": rows["evaluate"][0],
                                 "n": rows["evaluate"][1]},
                    "sample_rho": rows["sample_rho"],
                    "auc_ge5_vs_0": rows["auc_ge5_vs_0"],
                } for layer, rows in results.items()},
            "selected_layer": best,
            "evaluation_rho": chosen["evaluate"][0],
        }, indent=1) + "\n")
        print(f"wrote {args.save}")
    return results


def load_exit_context(args):
    """Once per run: leakage-safe turn allowance and exit labels per sample."""
    _, _, bail_ids, _, samples, _ = load_study1(args)
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
    _, _, _, distress_ids, _, scores = load_study1(args)
    judge_by_sample = replay.dimension_by_sample(scores, "frustration")

    distress_tensors, distress_manifest = load_capture(args.capture)
    bail_tensors, bail_manifest = load_capture(args.capture_bail)
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


def v3_probe_data(args):
    """distress-band probe dataset from the distress-v3 pilot: final-turn
    features (the registered scalar functional), scale-thirds labels from
    the pilot's judge scores, item-wise held-out split."""
    store = open_store(args)
    scores = list(store.read(scoring_pb2.JudgeScore, args.score_experiment,
                             args.condition, "scores"))
    judge = replay.dimension_by_sample(scores, "frustration")
    tensors, manifest = load_capture(args.capture)

    arrays, meta = {}, {"probes": {}, "score_experiment": args.score_experiment}
    for layer in manifest["layers"]:
        features = replay.final_turn_features(tensors, manifest, layer)
        rows = []
        for conversation_id, vector in features.items():
            key = split_conversation_id(conversation_id)
            value = judge.get(key)
            if value is None:
                continue
            label = replay.scale_thirds_label(value)
            if label is None:
                continue
            rows.append((key[0], vector, label))
        _fill_probe_arrays(arrays, meta, "distress_band", layer, rows)
    np.savez_compressed(args.probe_data_v3, **arrays)
    Path(args.probe_data_v3 + ".meta.json").write_text(
        json.dumps(meta, indent=1) + "\n")
    print(f"wrote {args.probe_data_v3} (+.meta.json)")


def probe_score(weights, group, features):
    """Standardized linear probe score for each feature vector."""
    mean = weights[f"{group}|feature_mean"]
    std = weights[f"{group}|feature_std"]
    w = weights[f"{group}|weight"]
    b = weights[f"{group}|bias"][0]
    return {cid: float(np.dot((vector - mean) / std, w) + b)
            for cid, vector in features.items()}


def mde(args):
    """Compute the §5 MDE values to pin at calibration close, from BF16
    calibration data only (null-based analytic forms; the dispersion form
    is asymptotic and labeled as such)."""
    from modelwelfare.stats import (mde_paired, null_delta_sd_dispersion,
                                    null_delta_sd_mean, null_delta_sd_rate)
    layer = args.layer
    k = 10  # confirmatory samples/item

    store = open_store(args)
    scores = list(store.read(scoring_pb2.JudgeScore, args.score_experiment,
                             args.condition, "scores"))
    judge = replay.dimension_by_sample(scores, "frustration")
    by_item = defaultdict(list)
    for (item, _sample), value in judge.items():
        by_item[item].append(value)
    n_distress = len(by_item)
    sigma_judge = float(np.sqrt(np.mean(
        [np.var(values, ddof=1) for values in by_item.values() if len(values) > 1])))

    tensors, manifest = load_capture(args.capture)
    vectors = load_file(str(args.vectors))
    rows = []
    for name, direction_key in (("R2a", DISTRESS_DIRECTION),
                                ("R2b", "assistant-axis-contrast")):
        direction = vectors[f"{direction_key}|L{layer}"]
        features = replay.final_turn_features(tensors, manifest, layer)
        proj_by_item = defaultdict(list)
        for conversation_id, vector in features.items():
            item, _sample = split_conversation_id(conversation_id)
            proj_by_item[item].append(float(np.dot(vector, direction)))
        sigma = float(np.sqrt(np.mean(
            [np.var(values, ddof=1) for values in proj_by_item.values()
             if len(values) > 1])))
        rows.append((name, mde_paired(null_delta_sd_mean(sigma, k), n_distress),
                     f"sigma_s={sigma:.3f}, n={n_distress}"))
        if name == "R2a":
            rows.append(("R3 (asymptotic)",
                         mde_paired(null_delta_sd_dispersion(sigma, k), n_distress),
                         f"sigma_s={sigma:.3f}, n={n_distress}"))
    rows.append(("B2", mde_paired(null_delta_sd_mean(sigma_judge, k), n_distress),
                 f"sigma_s={sigma_judge:.3f}, n={n_distress}"))
    rows.append(("B3 (asymptotic)",
                 mde_paired(null_delta_sd_dispersion(sigma_judge, k), n_distress),
                 f"sigma_s={sigma_judge:.3f}, n={n_distress}"))

    probes = load_file(str(args.probes))
    bail_tensors = load_file(args.capture_bail)
    with open(args.capture_bail + ".manifest.json") as handle:
        bail_manifest = json.load(handle)
    allowed, labels = load_exit_context(args)
    features, exit_labels, _excluded = exit_features(
        allowed, labels, layer, bail_tensors, bail_manifest)
    scores_by_cid = probe_score(probes, f"exit|L{layer}", features)
    correct_by_item = defaultdict(list)
    for conversation_id, value in scores_by_cid.items():
        item, _sample = split_conversation_id(conversation_id)
        correct_by_item[item].append(
            int((value > 0) == bool(exit_labels[conversation_id])))
    accuracy = [float(np.mean(values)) for values in correct_by_item.values()]
    rows.append(("R1 exit probe",
                 mde_paired(null_delta_sd_rate(accuracy, k), len(accuracy)),
                 f"mean acc={np.mean(accuracy):.3f}, n={len(accuracy)}"))

    if args.probes_v3:
        v3_probes = load_file(str(args.probes_v3))
        features = replay.final_turn_features(tensors, manifest, layer)
        band_scores = probe_score(v3_probes, f"distress_band|L{layer}", features)
        band_by_item = defaultdict(list)
        for conversation_id, value in band_scores.items():
            key = split_conversation_id(conversation_id)
            label = replay.scale_thirds_label(judge.get(key, 5.0))
            if label is None:
                continue
            band_by_item[key[0]].append(int((value > 0) == bool(label)))
        band_accuracy = [float(np.mean(values)) for values in band_by_item.values()]
        rows.append(("R1 distress probe",
                     mde_paired(null_delta_sd_rate(band_accuracy, k),
                                len(band_accuracy)),
                     f"mean acc={np.mean(band_accuracy):.3f}, n={len(band_accuracy)}"))

    print(f"MDE values at L{layer} (alpha=.05 two-sided, power .80, "
          f"k={k} samples/item; null-based analytic forms):")
    for name, value, detail in rows:
        print(f"  {name:16} MDE = {value:.4f}   ({detail})")
    if args.mde_out:
        Path(args.mde_out).write_text(json.dumps(
            {name: value for name, value, _detail in rows},
            indent=1, sort_keys=True, default=float) + "\n")
        print(f"wrote {args.mde_out}")
    if args.mde_check:
        pinned = json.loads(Path(args.mde_check).read_text())
        computed = {name: value for name, value, _detail in rows}
        failures = [f"{name}: pinned {pinned.get(name)} != computed "
                    f"{computed.get(name)}"
                    for name in sorted(set(pinned) | set(computed))
                    if name not in pinned or name not in computed
                    or abs(pinned[name] - computed[name])
                    > 1e-6 * max(abs(pinned[name]), 1e-9)]
        for line in failures:
            print(f"MDE DRIFT: {line}", file=sys.stderr)
        if failures:
            raise SystemExit(1)
        print(f"MDE values reproduce {args.mde_check} (within 1e-6 relative float tolerance)")
    return rows


def r2c(args):
    tensors, manifest = load_capture(args.capture_bail)
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
    parser.add_argument("--bundle", default=None,
                        help="packed RecordBundle file or directory replacing "
                             "the streaming store (the replication path)")
    parser.add_argument("--condition", default="qwen3-4b-bf16")
    parser.add_argument("--vectors", default=str(DEFAULT_VECTORS))
    parser.add_argument("--plan-distress", default=None)
    parser.add_argument("--plan-bail", default=None)
    parser.add_argument("--plan-from", default=None, metavar="EXPERIMENT",
                        help="generic replay plan: every sample of "
                             "(EXPERIMENT, --condition) in the store")
    parser.add_argument("--plan-out", default=None,
                        help="output path for --plan-from")
    parser.add_argument("--monitoring", action="store_true")
    parser.add_argument("--score-experiment", default=None,
                        help="score source for --monitoring/--probe-data-v3/"
                             "--mde (e.g. distress-v3-pilot-2); default is "
                             "the Study 1 store for --monitoring")
    parser.add_argument("--probe-data", default=None)
    parser.add_argument("--probe-data-v3", default=None,
                        help="distress-band probe dataset from the v3 pilot "
                             "(requires --capture and --score-experiment)")
    parser.add_argument("--mde", action="store_true",
                        help="compute the §5 MDE values (requires --layer, "
                             "--capture (v3), --capture-bail, --probes, "
                             "--score-experiment)")
    parser.add_argument("--layer", type=int, default=None)
    parser.add_argument("--probes", default=None,
                        help="trained probe weights safetensors (exit groups)")
    parser.add_argument("--probes-v3", default=None,
                        help="trained distress-band probe weights (v3)")
    parser.add_argument("--mde-out", default=None,
                        help="write computed MDE values to this JSON")
    parser.add_argument("--mde-check", default=None,
                        help="compare computed MDE values against a pinned "
                             "JSON; nonzero exit on drift")
    parser.add_argument("--r2c", action="store_true")
    parser.add_argument("--capture", default=None,
                        help="distress replay capture safetensors")
    parser.add_argument("--capture-bail", default=None,
                        help="bail replay capture safetensors")
    parser.add_argument("--save", default=None, help="summary JSON path")
    args = parser.parse_args()

    if args.plan_from:
        if not args.plan_out:
            raise SystemExit("--plan-from requires --plan-out")
        store = open_store(args)
        records = list(store.read(transcript_pb2.SampleRecord,
                                  args.plan_from, args.condition, "samples"))
        if not records:
            raise SystemExit(f"no samples for {args.plan_from}/{args.condition}")
        write_plan(records, args.plan_out)
        return
    if args.plan_distress or args.plan_bail:
        _, definitions, bail_ids, distress_ids, samples, _ = load_study1(args)
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
    if args.probe_data_v3:
        if not (args.capture and args.score_experiment):
            raise SystemExit("--probe-data-v3 requires --capture and "
                             "--score-experiment")
        v3_probe_data(args)
        return
    if args.mde:
        required = (args.layer, args.capture, args.capture_bail, args.probes,
                    args.score_experiment)
        if any(value is None for value in required):
            raise SystemExit("--mde requires --layer, --capture, "
                             "--capture-bail, --probes, --score-experiment")
        mde(args)
        return
    if args.r2c:
        if not args.capture_bail:
            raise SystemExit("--r2c requires --capture-bail")
        r2c(args)
        return
    raise SystemExit("nothing to do; see --help")


if __name__ == "__main__":
    main()
