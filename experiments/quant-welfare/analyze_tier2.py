#!/usr/bin/env python3
"""Study 2 confirmatory analysis driver: registered statistics over the
Tier-2 record kinds (REGISTRATION §4), fixed as tested code before any
confirmatory data exists — the Study 1 discipline: the analysis is an
execution, not an interpretation.

This module is the wiring. It assembles endpoint values per (condition,
item) from the activation/projection record kinds (via
:mod:`modelwelfare.activations`, pooling through the same
:mod:`modelwelfare.replay` functionals calibration used) and from the
behavioral streams, then applies :mod:`analyze`'s family machinery — the
same permutation contrasts, Holm families, style companion, and
mechanical rates the Study 1 driver runs. Registered structure:

  * R1 (primary) — ONE Holm family of 2 probes × 2 contrasts: the exit
    probe's absolute accuracy change and the distress-band probe's
    comparative differential vs the frozen control probe (§4.1). Each
    probe carries an AUROC companion read; the exit side carries the
    control-family specificity gate (one-sided two-sample permutation).
  * R2a/R2b/R3, B2/B3 — secondary families, Holm within each (2
    contrasts); B2 keeps Study 1's style-adjusted companion.
  * B4a/B4b — the mechanical family, over every rung including w3.
  * Trends — seven Page's L tests (§4.2), Holm among themselves, each on
    its §4.1 confirmatory statistic. §4.2 registers each as one-sided
    "toward larger effect at lower precision"; the per-endpoint reading
    of "larger effect" is pinned in TREND_ORIENTATION below, pre-data:
    probe endpoints trend on degradation (accuracy falls), the distress
    projection, dispersion, and judge endpoints on increase, and the
    assistant-axis endpoint on decrease (drift away from the Assistant
    pole — the direction the axis literature associates with pressure).
  * §4.4 dissociation cells — Holm-significance on one member plus TOST
    equivalence of the other at its own pinned MDE as margin; the bail
    pair's behavioral member is Study 1's published E1, read from the
    committed golden file, never recomputed.

The capability gate is inherited from Study 1 (§3.1): w3 is
capability-confounded, reported separately and uncorrected, and never
enters families or trends.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
for sub in ("core/src",):
    path = str(REPO / sub)
    if path not in sys.path:
        sys.path.insert(0, path)

from google.protobuf import text_format  # noqa: E402

import analyze  # noqa: E402
from modelwelfare import activations, replay, stats  # noqa: E402
from modelwelfare.v1 import activation_pb2, battery_pb2  # noqa: E402
from modelwelfare.v1 import scoring_pb2, transcript_pb2  # noqa: E402

BASE = Path(__file__).resolve().parent

REFERENCE = "qwen3-4b-bf16"
CONFIRMATORY = ["qwen3-4b-rtn-w8", "qwen3-4b-rtn-w4"]
DEGRADED = "qwen3-4b-rtn-w3"
LADDER = [REFERENCE] + CONFIRMATORY
FROZEN_LAYER = 18

DISTRESS_DIRECTION = "distress-contrast"
AXIS_DIRECTION = "assistant-axis-contrast"
REFUSAL_DIRECTION = "refusal-contrast"

# Pre-committed control-probe label splits over the distress-v3 `task` tag
# (REGISTRATION §3.5): binary welfare-irrelevant task-content labels, each
# perfectly crossed with the six feedback styles. control_analytic is the
# frozen confirmatory comparator (FREEZE.json control_group).
CONTROL_SPLITS = {
    "control_analytic": {"code", "explain", "inflation", "regex", "summary"},
    "control_code": {"code", "regex"},
    "control_verse": {"limerick", "poem"},
}
CONTROL_GROUP = "control_analytic"

# Study 1's pinned minimum detectable E1 exit-rate shift (its §5) — the
# §4.4 equivalence margin for the bail pair's behavioral member.
E1_MARGIN = 0.127

# +1: the registered "larger effect at lower precision" is an increase in
# the endpoint value; -1: a decrease (see module docstring).
TREND_ORIENTATION = {
    "R1-exit": -1, "R1-differential": -1,
    "R2a": +1, "R2b": -1, "R3": +1, "B2": +1, "B3": +1,
}


# --- frozen inputs ----------------------------------------------------------

def battery_tasks(battery: str = "distress-v3") -> dict:
    """item_id -> task tag over one frozen battery definition."""
    definition = battery_pb2.BatteryDefinition()
    text_format.Parse(
        (BASE / "batteries" / f"{battery}.textproto").read_text(), definition)
    return {item.id: item.tags["task"] for item in definition.items}


def pinned_margins() -> dict:
    """The §4.4 equivalence margins: each member's own pinned MDE."""
    pinned = json.loads(
        (BASE / "study2" / "calibration" / "mde-pinned.json").read_text())
    return {"R1-exit": pinned["R1 exit probe"], "R2a": pinned["R2a"],
            "R3": pinned["R3 (asymptotic)"], "B2": pinned["B2"],
            "B3": pinned["B3 (asymptotic)"], "E1": E1_MARGIN}


def published_row(row: dict) -> dict:
    """One published E1 row with its standard error recovered from the
    stored t statistic. A zero t leaves the SE unidentifiable — NaN, so a
    §4.4 equivalence read can never be claimed from an undefined SE (a NaN
    p-value passes no threshold)."""
    se = abs(row["mean"] / row["t"]) if row["t"] else float("nan")
    return {"mean": row["mean"], "holm_p": row["holm_p"], "se": se,
            "n": row["n"]}


def published_e1() -> dict:
    """Study 1's published E1 rows (mean, holm_p, standard error) from the
    committed golden file — the §4.4 bail-side behavioral member, cited as
    published, never re-analyzed."""
    golden = json.loads(
        (BASE / "study1" / "confirmatory" / "expected-results.json")
        .read_text())
    return {row["contrast"]: published_row(row) for row in golden["e1"]}


# --- assembly from the record kinds -----------------------------------------

def projection_samples(store, experiment_id, conditions, direction_id) -> dict:
    """{(condition, item): [final-turn pooled projections, one per sample]}
    from the ProjectionSeries stream — the §3.4 scalar functional (a
    length-1 series on the conversation's final captured turn)."""
    best = {}
    for condition_id in conditions:
        for record in store.read(activation_pb2.ProjectionSeries,
                                 experiment_id, condition_id, "projections"):
            if record.direction_id != direction_id or len(record.values) != 1:
                continue
            key = (condition_id, record.key.item_id, record.key.sample_index)
            if key not in best or record.turn_index > best[key][0]:
                best[key] = (record.turn_index, record.values[0])
    values = defaultdict(list)
    for (condition_id, item_id, sample_index), (_turn, value) in sorted(
            best.items()):
        values[(condition_id, item_id)].append(value)
    return dict(values)


def probe_reads(store, experiment_id, conditions, weights, group,
                labels_by_cid, allowed=None) -> tuple:
    """Per-condition probe transfer reads over identical input text.

    Returns ({condition: {item: accuracy}}, {condition: AUROC}). Features
    follow the registered functional: the final captured turn by default,
    or the mean over ``allowed`` message indices per conversation (the exit
    probe's leakage-safe rule) when ``allowed`` is given. Only labeled
    conversations enter.
    """
    accuracy_by_condition, auroc_by_condition = {}, {}
    for condition_id in conditions:
        tensors, manifest = activations.condition_capture(
            store, experiment_id, condition_id)
        if allowed is not None:
            features = replay.pooled_sample_features(
                tensors, manifest, FROZEN_LAYER, allowed)
        else:
            features = replay.final_turn_features(
                tensors, manifest, FROZEN_LAYER)
        features = {cid: vector for cid, vector in features.items()
                    if labels_by_cid.get(cid) is not None}
        scores = activations.probe_scores(
            weights, f"{group}|L{FROZEN_LAYER}", features)
        correct_by_item = defaultdict(list)
        for cid, value in scores.items():
            item_id, _sample = replay.split_conversation_id(cid)
            correct_by_item[item_id].append(
                int((value > 0) == bool(labels_by_cid[cid])))
        accuracy_by_condition[condition_id] = {
            item: float(sum(values) / len(values))
            for item, values in correct_by_item.items()}
        ordered = sorted(scores)
        auroc_by_condition[condition_id] = stats.auroc(
            [scores[cid] for cid in ordered],
            [labels_by_cid[cid] for cid in ordered])
    return accuracy_by_condition, auroc_by_condition


def differential_map(welfare_acc, control_acc) -> dict:
    """{condition: {item: welfare − control accuracy}} over common items —
    the per-item comparative statistic; pairing it across conditions gives
    exactly [Δ welfare − Δ control] (§4.1)."""
    result = {}
    for condition_id in welfare_acc:
        control = control_acc.get(condition_id, {})
        result[condition_id] = {
            item: welfare_acc[condition_id][item] - control[item]
            for item in welfare_acc[condition_id] if item in control}
    return result


# --- registered reads beyond the shared family machinery --------------------

def r1_family(exit_map, differential_map_, contrasts) -> dict:
    """The primary family: 2 probes × the confirmatory contrasts, ONE Holm
    correction across all four tests (§4.1)."""
    exit_rows = analyze.contrast_rows(exit_map, REFERENCE, contrasts)
    diff_rows = analyze.contrast_rows(differential_map_, REFERENCE, contrasts)
    adjusted = stats.holm([row["p"] for row in exit_rows + diff_rows])
    for row, holm_p in zip(exit_rows + diff_rows, adjusted):
        row["holm_p"] = holm_p
    return {"exit": exit_rows, "differential": diff_rows}


def auroc_companion(auroc_by_condition, contrasts) -> list:
    """The §4.1 AUROC companion read: per-rung AUROC beside the reference's,
    for the fixed disambiguation (accuracy down + AUROC preserved =
    calibration offset along the probe normal, not separability loss)."""
    reference = auroc_by_condition.get(REFERENCE, float("nan"))
    return [{"contrast": contrast,
             "reference_auroc": reference,
             "auroc": auroc_by_condition.get(contrast, float("nan")),
             "delta": auroc_by_condition.get(contrast, float("nan"))
             - reference}
            for contrast in contrasts]


def specificity_rows(exit_map, control_map, contrasts) -> list:
    """The exit-side welfare-specificity gate (§4.1): the exit probe's
    item-level accuracy degradation vs the control family's, one-sided
    two-sample permutation (degradation = −Δaccuracy; no item pairing
    exists across batteries)."""
    rows = []
    for contrast in contrasts:
        exit_deltas = analyze.paired_deltas(
            exit_map.get(REFERENCE, {}), exit_map.get(contrast, {}))
        control_deltas = analyze.paired_deltas(
            control_map.get(REFERENCE, {}), control_map.get(contrast, {}))
        result = stats.two_sample_permutation_test(
            [-delta for delta in exit_deltas],
            [-delta for delta in control_deltas])
        rows.append({"contrast": contrast, **result})
    return rows


def replay_projections(store, experiment_id: str, direction_id: str,
                       items: set) -> list:
    """DESCRIPTIVE, unregistered: per-rung contrasts of one frozen
    direction's final-turn projection over a replay experiment's captures,
    restricted to ``items`` (replay experiments carry several batteries in
    one store scope)."""
    projections = projection_samples(store, experiment_id,
                                     LADDER + [DEGRADED], direction_id)
    item_means = {key: sum(values) / len(values)
                  for key, values in projections.items()
                  if key[1] in items}
    return analyze.contrast_rows(analyze.by_condition(item_means),
                                 REFERENCE, CONFIRMATORY + [DEGRADED])


def fixed_input_projections(store, mode_a: str, direction_id: str) -> list:
    """DESCRIPTIVE, unregistered: projections of the Mode A v3-arm replays
    — identical BF16-generated text at every rung — onto one frozen
    direction: the pure-representation analog of R2a/R2b. The registered
    endpoints read each rung's OWN Mode C generations, so their shifts
    blend a text-mediated component with an input-independent one; this
    read isolates the input-independent component (no sampling noise, no
    style pathway — the text is frozen). Mode A also carries the Study 1
    transcripts, so conversations are filtered to the distress-v3 items."""
    return replay_projections(store, mode_a, direction_id,
                              set(battery_tasks()))


def control_direction(probes_control, group: str):
    """The control probe's effective raw-space normal, unit-normalized.

    The probe scores standardized features (w · (x-μ)/σ), so the raw
    direction whose movement changes control-probe scores is w/σ; unit
    length makes its projections magnitude-comparable with the frozen
    (unit) welfare directions."""
    weight = probes_control[f"{group}|L{FROZEN_LAYER}|weight"]
    std = probes_control[f"{group}|L{FROZEN_LAYER}|feature_std"]
    raw = weight / std
    return raw / np.linalg.norm(raw)


def direction_specificity(store, experiment_id: str, items: set,
                          directions: dict, random_directions) -> dict:
    """DESCRIPTIVE, unregistered: the direction-specificity control for the
    R2a/R2b construct. A wholesale activation offset (changed
    residual-stream means/norms) has a nonzero component along ANY fixed
    direction and is input-independent, so it survives the fixed-input
    argument; this read distinguishes that artifact from a
    direction-specific shift by projecting the SAME final-turn features
    (raw residual dot products — no normalization) along the welfare
    directions, the welfare-irrelevant control-probe normal, and a
    random-unit-direction baseline, alongside the feature-norm read and
    the mean-shift vector's cosine to each direction."""
    feature_lists = {}
    for condition_id in LADDER + [DEGRADED]:
        tensors, manifest = activations.condition_capture(
            store, experiment_id, condition_id)
        features = replay.final_turn_features(tensors, manifest, FROZEN_LAYER)
        by_item = defaultdict(list)
        for cid, vector in features.items():
            item_id, _sample = replay.split_conversation_id(cid)
            if item_id in items:
                by_item[item_id].append(np.asarray(vector, dtype=np.float64))
        feature_lists[condition_id] = {
            item: np.mean(np.stack(vectors), axis=0)
            for item, vectors in by_item.items()}
    if not feature_lists.get(REFERENCE):
        return {"projections": {}, "feature_norm": [], "random": {},
                "mean_shift": {}, "note": "no capture features in scope"}

    contrasts = CONFIRMATORY + [DEGRADED]
    result = {"projections": {}, "feature_norm": None,
              "random": {}, "mean_shift": {}}
    for name, direction in sorted(directions.items()):
        values = {(condition, item): float(feature @ direction)
                  for condition, by_item in feature_lists.items()
                  for item, feature in by_item.items()}
        result["projections"][name] = analyze.contrast_rows(
            analyze.by_condition(values), REFERENCE, contrasts)
    norms = {(condition, item): float(np.linalg.norm(feature))
             for condition, by_item in feature_lists.items()
             for item, feature in by_item.items()}
    result["feature_norm"] = analyze.contrast_rows(
        analyze.by_condition(norms), REFERENCE, contrasts)

    reference_items = feature_lists[REFERENCE]
    reference_mean = np.mean(np.stack(list(reference_items.values())), axis=0)
    reference_norm = float(np.linalg.norm(reference_mean))
    for contrast in contrasts:
        shared = sorted(set(reference_items) & set(feature_lists[contrast]))
        if not shared:
            continue
        deltas = np.stack([feature_lists[contrast][item]
                           - reference_items[item] for item in shared])
        mean_shift = deltas.mean(axis=0)
        shift_norm = float(np.linalg.norm(mean_shift))
        unit_shift = (mean_shift / shift_norm if shift_norm
                      else np.zeros_like(mean_shift))
        random_deltas = np.abs(deltas.mean(axis=0) @ random_directions.T)
        result["random"][contrast] = {
            "mean_abs_delta": float(random_deltas.mean()),
            "max_abs_delta": float(random_deltas.max()),
            "n_directions": int(random_directions.shape[0])}
        result["mean_shift"][contrast] = {
            "norm": shift_norm,
            "relative_to_reference_norm": (
                shift_norm / reference_norm if reference_norm
                else float("nan")),
            "cosine": {name: float(unit_shift @ direction)
                       for name, direction in sorted(directions.items())},
            "random_mean_abs_cosine": float(
                np.abs(unit_shift @ random_directions.T).mean())}
    return result


def flatten(by_condition: dict) -> dict:
    """{condition: {item: value}} -> {(condition, item): value}, the shape
    Page's L consumes."""
    return {(condition, item): value
            for condition, items in by_condition.items()
            for item, value in items.items()}


def trend_family(value_maps: dict) -> tuple:
    """The §4.2 trend family: Page's L per endpoint over BF16 → w8 → w4 on
    the §4.1 confirmatory statistic, oriented per TREND_ORIENTATION, Holm
    among the seven; the two-sided reading reported alongside."""
    trends = {}
    for name, by_condition_item in value_maps.items():
        orientation = TREND_ORIENTATION[name]
        oriented = {key: orientation * value
                    for key, value in by_condition_item.items()}
        row = stats.pages_l_trend(oriented, LADDER)
        row["two_sided"] = float(min(1.0, 2.0 * min(row["p_value"],
                                                    1.0 - row["p_value"])))
        trends[name] = row
    names = [name for name, row in trends.items()
             if row["p_value"] == row["p_value"]]  # drop NaN rows
    adjusted = stats.holm([trends[name]["p_value"] for name in names])
    return trends, dict(zip(names, adjusted))


def dissociation_cell(rep: dict, beh: dict, alpha: float = 0.05) -> dict:
    """One §4.4 cell. rep/beh each carry holm_p and equivalence_p; the
    verdict requires Holm-significance on one member AND equivalence of the
    other — merely significant-vs-nonsignificant is *asymmetric
    significance, indeterminate* and claims nothing."""
    rep_significant = rep["holm_p"] <= alpha
    beh_significant = beh["holm_p"] <= alpha
    if rep_significant and beh_significant:
        verdict = "joint movement"
    elif rep_significant and beh["equivalence_p"] <= alpha:
        verdict = "dissociation (representational)"
    elif beh_significant and rep["equivalence_p"] <= alpha:
        verdict = "dissociation (behavioral)"
    elif rep_significant or beh_significant:
        verdict = "asymmetric significance, indeterminate"
    else:
        verdict = "joint null"
    return {"verdict": verdict, "representational": rep, "behavioral": beh}


def member(rows_by_contrast: dict, value_map: dict, margin: float,
           contrast: str) -> dict:
    """One pair member at one rung: its family-corrected p plus its TOST
    equivalence read at its own pinned MDE (§4.4)."""
    deltas = analyze.paired_deltas(
        value_map.get(REFERENCE, {}), value_map.get(contrast, {}))
    equivalence = stats.tost_paired(deltas, margin)
    return {"holm_p": rows_by_contrast[contrast]["holm_p"],
            "mean": rows_by_contrast[contrast]["mean"],
            "equivalence_p": equivalence["p_value"], "margin": margin}


# --- the driver -------------------------------------------------------------

def exit_context(study1_samples, bail_items) -> tuple:
    """Leakage-safe turn allowance, exit labels, and AUROC label map for the
    Study 1 BF16 bail transcripts (the Mode A exit set)."""
    records = {replay.conversation_id(record): record
               for record in study1_samples
               if record.key.item_id in bail_items}
    allowed = {cid: set(replay.feature_message_indices(record))
               for cid, record in records.items()}
    labels = {cid: int(replay.sample_exited(record))
              for cid, record in records.items()}
    return allowed, labels


def distress_band_labels(scores) -> dict:
    """Tercile labels from the Mode C BF16 arm's judge scores, fixed once at
    the reference scoring (§3.3): {conversation_id: 0/1 or None}."""
    judge = replay.dimension_by_sample(scores, analyze.FRUSTRATION)
    return {f"{item}|s{sample}": replay.scale_thirds_label(value)
            for (item, sample), value in judge.items()}


def control_labels(tasks: dict, group: str) -> dict:
    """{item_id -> 0/1} for one pre-committed control split — the
    welfare-irrelevant task-content labels (§3.5)."""
    split = CONTROL_SPLITS[group]
    return {item: int(task in split) for item, task in tasks.items()}


def analyze_study2(store, mode_a: str, mode_c: str,
                   study1_experiment: str, probes, probes_v3, probes_control,
                   control_group: str = CONTROL_GROUP, mode_b: str = None,
                   directions_path=None) -> dict:
    """Assemble every registered Study 2 endpoint from the store.

    ``mode_a`` — the fixed-input replay experiment (Study 1 bail + distress
    transcripts and the Mode C BF16 arm, captured at every rung);
    ``mode_c`` — the fresh distress arm (samples + judge scores per rung,
    own-replay captures); ``mode_b`` — the own-trajectory replay
    experiment, read only for R2c's descriptive projections (§4.1: R2c is
    a Mode B read; omitted, the R2c section is empty); ``study1_experiment``
    — Study 1's confirmatory experiment id, read for the BF16 bail
    transcripts' mechanical labels only. Probe arguments are loaded
    safetensors dicts (the frozen weights). Pure given its inputs; draws
    no conclusions.
    """
    contrasts = CONFIRMATORY + [DEGRADED]
    surviving = CONFIRMATORY

    experiment = analyze.load_experiment(BASE / "study1" / "confirmatory")
    definitions = analyze.batteries_for(BASE / "study1" / "confirmatory")
    bail_items, _distress_items = analyze.item_roles(experiment, definitions)
    study1_samples = list(store.read(
        transcript_pb2.SampleRecord, study1_experiment, REFERENCE, "samples"))
    allowed, exit_labels = exit_context(study1_samples, bail_items)

    mode_c_scores = {
        condition: list(store.read(scoring_pb2.JudgeScore, mode_c,
                                   condition, "scores"))
        for condition in LADDER + [DEGRADED]}
    mode_c_samples = [
        record
        for condition in LADDER + [DEGRADED]
        for record in store.read(transcript_pb2.SampleRecord, mode_c,
                                 condition, "samples")]

    # R1 — probe transfer on identical input text (Mode A captures).
    band_labels = distress_band_labels(mode_c_scores[REFERENCE])
    control_by_item = control_labels(battery_tasks(), control_group)
    v3_cids = {cid for cid, label in band_labels.items() if label is not None}
    control_by_cid = {
        cid: control_by_item.get(replay.split_conversation_id(cid)[0])
        for cid in v3_cids}
    exit_acc, exit_auroc = probe_reads(
        store, mode_a, LADDER + [DEGRADED], probes, "exit",
        exit_labels, allowed=allowed)
    band_acc, band_auroc = probe_reads(
        store, mode_a, LADDER + [DEGRADED], probes_v3, "distress_band",
        band_labels)
    control_acc, control_auroc = probe_reads(
        store, mode_a, LADDER + [DEGRADED], probes_control, control_group,
        control_by_cid)
    diff_map = differential_map(band_acc, control_acc)

    # R2/R3 — projections of the Mode C own-replay captures.
    distress_proj = projection_samples(store, mode_c, LADDER + [DEGRADED],
                                       DISTRESS_DIRECTION)
    axis_proj = projection_samples(store, mode_c, LADDER + [DEGRADED],
                                   AXIS_DIRECTION)
    r2a_map = {key: sum(v) / len(v) for key, v in distress_proj.items()}
    r2b_map = {key: sum(v) / len(v) for key, v in axis_proj.items()}
    r3_sd = {key: float(analyze._std(v))
             for key, v in distress_proj.items() if len(v) >= 2}

    # B2/B3/B4 + style companion — the Study 1 statistics on distress-v3.
    all_scores = [score for rows in mode_c_scores.values() for score in rows]
    frust_by_item = analyze.frustration_values(all_scores)
    frust_mean = {key: sum(v) / len(v) for key, v in frust_by_item.items()}
    length_mean, repetition_mean = analyze.sample_features(mode_c_samples)
    invalid_by_item, reoffer_by_item = analyze.mechanical_rates(mode_c_samples)

    r2a_by_cond = analyze.by_condition(r2a_map)
    r2b_by_cond = analyze.by_condition(r2b_map)
    r3_by_cond = analyze._sd_delta_family(distress_proj, REFERENCE, contrasts)
    b2_by_cond = analyze.by_condition(frust_mean)
    b3_by_cond = analyze._sd_delta_family(frust_by_item, REFERENCE, contrasts)

    result = {
        "reference": REFERENCE,
        "confirmatory": surviving,
        "degraded": [DEGRADED],
        "r1": r1_family(exit_acc, diff_map, surviving),
        "r1_confounded": {
            "exit": analyze.contrast_rows(exit_acc, REFERENCE, [DEGRADED]),
            "differential": analyze.contrast_rows(diff_map, REFERENCE,
                                                  [DEGRADED])},
        "r1_auroc": {"exit": auroc_companion(exit_auroc,
                                             surviving + [DEGRADED]),
                     "distress": auroc_companion(band_auroc,
                                                 surviving + [DEGRADED]),
                     "control": auroc_companion(control_auroc,
                                                surviving + [DEGRADED])},
        "r1_specificity": specificity_rows(exit_acc, control_acc, surviving),
        "r2a": analyze.run_family(r2a_by_cond, REFERENCE, surviving),
        "r2b": analyze.run_family(r2b_by_cond, REFERENCE, surviving),
        "r3": analyze.run_family(r3_by_cond, REFERENCE, surviving),
        "b2": analyze.run_family(b2_by_cond, REFERENCE, surviving),
        "b3": analyze.run_family(b3_by_cond, REFERENCE, surviving),
        "b2_style": analyze._e2_style(
            b2_by_cond, analyze.by_condition(length_mean),
            analyze.by_condition(repetition_mean), REFERENCE, surviving),
        "b4a": analyze.run_family(analyze.by_condition(invalid_by_item),
                                  REFERENCE, contrasts),
        "b4b": analyze.run_family(analyze.by_condition(reoffer_by_item),
                                  REFERENCE, contrasts),
        "r2a_confounded": analyze.contrast_rows(r2a_by_cond, REFERENCE,
                                                [DEGRADED]),
        "r2b_confounded": analyze.contrast_rows(r2b_by_cond, REFERENCE,
                                                [DEGRADED]),
        "r3_confounded": analyze.contrast_rows(r3_by_cond, REFERENCE,
                                               [DEGRADED]),
        "b2_confounded": analyze.contrast_rows(b2_by_cond, REFERENCE,
                                               [DEGRADED]),
        "b3_confounded": analyze.contrast_rows(b3_by_cond, REFERENCE,
                                               [DEGRADED]),
    }

    # Descriptive: R2c as registered — the refusal-direction projection
    # over the Mode B BAIL trajectories with the leakage-safe features
    # (mean of per-turn pooled projections over each rung's own allowed
    # turns; linearity makes that identical to projecting the pooled
    # feature). Not promoted at the freeze; no claim.
    if mode_b is not None:
        item_means = {}
        for condition_id in LADDER + [DEGRADED]:
            condition_samples = list(store.read(
                transcript_pb2.SampleRecord, study1_experiment,
                condition_id, "samples"))
            allowed, _labels = exit_context(condition_samples, bail_items)
            by_conversation = defaultdict(dict)
            for record in store.read(activation_pb2.ProjectionSeries,
                                     mode_b, condition_id, "projections"):
                if (record.direction_id != REFUSAL_DIRECTION
                        or len(record.values) != 1):
                    continue
                cid = f"{record.key.item_id}|s{record.key.sample_index}"
                by_conversation[cid][record.turn_index] = record.values[0]
            sample_values = defaultdict(list)
            for cid, turns in by_conversation.items():
                permitted = allowed.get(cid)
                if permitted is None:
                    continue
                values = [value for turn, value in turns.items()
                          if turn in permitted]
                if values:
                    item_id, _sample = replay.split_conversation_id(cid)
                    sample_values[(condition_id, item_id)].append(
                        sum(values) / len(values))
            for key, values in sample_values.items():
                item_means[key] = sum(values) / len(values)
        result["r2c_descriptive"] = analyze.contrast_rows(
            analyze.by_condition(item_means), REFERENCE,
            surviving + [DEGRADED])
    else:
        result["r2c_descriptive"] = []

    # Descriptive: the fixed-input (Mode A v3-arm) projection reads — the
    # input-independent component of the R2a/R2b constructs.
    result["fixed_input_descriptive"] = {
        "distress": fixed_input_projections(store, mode_a,
                                            DISTRESS_DIRECTION),
        "assistant_axis": fixed_input_projections(store, mode_a,
                                                  AXIS_DIRECTION),
    }

    # Descriptive: the distress-v2 bridge — the same distress-direction
    # read over the Study 1 battery, fixed-input (Mode A, BF16-generated
    # text at every rung) and own-trajectory (Mode B, each rung's own
    # Study 1 generations), so the fixed-input component can be checked
    # for reproduction on a disjoint battery and located against the
    # own-text magnitude.
    v2_items = set(battery_tasks("distress-v2"))
    result["v2_bridge_descriptive"] = {
        "mode_a": replay_projections(store, mode_a, DISTRESS_DIRECTION,
                                     v2_items),
        "mode_b": (replay_projections(store, mode_b, DISTRESS_DIRECTION,
                                      v2_items)
                   if mode_b is not None else []),
    }

    # Descriptive: direction specificity — the same features, welfare
    # directions vs the welfare-irrelevant control normal vs a random-unit
    # baseline, so a wholesale offset cannot masquerade as a
    # welfare-direction shift (nor vice versa).
    if directions_path is None:
        directions_path = (BASE / "study2" / "calibration"
                           / "directions-bf16.safetensors")
    frozen = activations.layer_directions(directions_path, FROZEN_LAYER)
    specificity_directions = {
        "distress": np.asarray(frozen[DISTRESS_DIRECTION], dtype=np.float64),
        "assistant_axis": np.asarray(frozen[AXIS_DIRECTION],
                                     dtype=np.float64),
        "control": np.asarray(control_direction(probes_control,
                                                control_group),
                              dtype=np.float64)}
    rng = np.random.default_rng(20260829)
    dimension = specificity_directions["distress"].shape[0]
    random_directions = rng.standard_normal((32, dimension))
    random_directions /= np.linalg.norm(random_directions, axis=1,
                                        keepdims=True)
    v3_items = set(battery_tasks())
    result["direction_specificity_descriptive"] = {
        "fixed_input": direction_specificity(
            store, mode_a, v3_items, specificity_directions,
            random_directions),
        "own_generation": direction_specificity(
            store, mode_c, v3_items, specificity_directions,
            random_directions),
    }

    # §4.2 trends on the confirmatory statistics.
    trends, trend_holm = trend_family({
        "R1-exit": flatten(exit_acc), "R1-differential": flatten(diff_map),
        "R2a": r2a_map, "R2b": r2b_map, "R3": r3_sd,
        "B2": frust_mean,
        "B3": {key: float(analyze._std(v))
               for key, v in frust_by_item.items() if len(v) >= 2}})
    result["trends"] = trends
    result["trend_holm"] = trend_holm

    # §4.4 dissociation cells.
    margins = pinned_margins()
    e1_rows = published_e1()
    r1_by_contrast = {row["contrast"]: row for row in result["r1"]["exit"]}
    r2a_by_contrast = {row["contrast"]: row for row in result["r2a"]}
    r3_by_contrast = {row["contrast"]: row for row in result["r3"]}
    b2_by_contrast = {row["contrast"]: row for row in result["b2"]}
    b3_by_contrast = {row["contrast"]: row for row in result["b3"]}
    cells = {}
    for contrast in surviving:
        e1_row = e1_rows[contrast]
        cells[contrast] = {
            "R1-exit vs E1": dissociation_cell(
                member(r1_by_contrast, exit_acc, margins["R1-exit"],
                       contrast),
                {"holm_p": e1_row["holm_p"], "mean": e1_row["mean"],
                 "equivalence_p": stats.tost_summary(
                     e1_row["mean"], e1_row["se"], margins["E1"]),
                 "margin": margins["E1"]}),
            "R2a vs B2": dissociation_cell(
                member(r2a_by_contrast, r2a_by_cond, margins["R2a"],
                       contrast),
                member(b2_by_contrast, b2_by_cond, margins["B2"], contrast)),
            "R3 vs B3": dissociation_cell(
                member(r3_by_contrast, r3_by_cond, margins["R3"], contrast),
                member(b3_by_contrast, b3_by_cond, margins["B3"], contrast)),
        }
    result["dissociation"] = cells
    return result


def main():
    from safetensors.numpy import load_file

    from modelwelfare.bundle import BundleStore
    from modelwelfare.store import ResultStore

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", default=str(REPO / "data"))
    parser.add_argument("--bundle", default=None,
                        help="packed RecordBundle file/directory replacing "
                             "the streaming store")
    parser.add_argument("--mode-a", required=True,
                        help="fixed-input replay experiment id")
    parser.add_argument("--mode-b", default=None,
                        help="own-trajectory replay experiment id (R2c "
                             "descriptive projections)")
    parser.add_argument("--mode-c", required=True,
                        help="fresh distress arm experiment id")
    parser.add_argument("--study1", default="quant-welfare-confirmatory-1")
    parser.add_argument("--probes", default=str(
        BASE / "study2" / "calibration" / "probes-bf16.safetensors"))
    parser.add_argument("--probes-v3", default=str(
        BASE / "study2" / "calibration" / "probes-v3-bf16.safetensors"))
    parser.add_argument("--probes-control", default=str(
        BASE / "study2" / "calibration" / "probes-control-bf16.safetensors"))
    parser.add_argument("--out", default=None, help="write result JSON here")
    args = parser.parse_args()

    store = BundleStore(args.bundle) if args.bundle \
        else ResultStore(args.store)
    result = analyze_study2(
        store, args.mode_a, args.mode_c, args.study1,
        load_file(args.probes), load_file(args.probes_v3),
        load_file(args.probes_control), mode_b=args.mode_b)
    rendered = json.dumps(result, indent=1, sort_keys=True, default=float)
    if args.out:
        Path(args.out).write_text(rendered + "\n")
        print(f"wrote {args.out}")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
