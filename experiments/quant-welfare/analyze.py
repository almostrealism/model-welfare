#!/usr/bin/env python3
"""Confirmatory analysis driver: registered statistics over the result store.

Reads a confirmatory experiment's stored ``SampleRecord``, ``JudgeScore``, and
``ExitClassification`` streams and produces the pre-registered confirmatory
result — the hierarchical Holm families, the Page's L dose-response, and the
H1 flip endpoints defined in PREREGISTRATION §2/§4. It runs ONLY the registered
tests from :mod:`modelwelfare.stats`; their correctness is pinned there. This
module is the wiring: it assembles endpoint values per (condition, item) from
the store and applies the families. It draws no conclusions and writes nothing
to the store.

Multiplicity is hierarchical, never a flat pool (PREREGISTRATION §4):

  * Primary family — E1 (refusal+aversion exit rate) × the RTN contrasts,
    Holm-corrected within.
  * Secondary families — E2 (frustration) and E3 (across-sample dispersion),
    each Holm-corrected within itself.
  * Trend family — the Page's L dose-response tests (one per endpoint),
    Holm-corrected among themselves, over rungs that pass the capability gate
    (k >= 3, else H3 is not tested).

The capability gate (PREREGISTRATION §4) excludes degraded rungs from the
primary claims and the Page's L fit. Per-rung perplexity is supplied via
``--perplexity`` (a JSON ``{condition_id: value}`` produced by
``tools/perplexity.py``); the per-rung invalid-sample rate is computed from the
store via :func:`modelwelfare.analysis.sample_is_degenerate`.

Run against the confirmatory store once it exists; run against a calibration
store (e.g. ``--experiment ladder-calibration``) only to exercise the wiring —
those deltas are barred from findings by the §7 firewall.

    python3 analyze.py --experiment confirmatory --perplexity perplexity.json
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for sub in ("core/src",):
    path = str(REPO / sub)
    if path not in sys.path:
        sys.path.insert(0, path)

from google.protobuf import text_format  # noqa: E402

from modelwelfare import analysis, stats  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import battery_pb2, experiment_pb2, scoring_pb2, transcript_pb2  # noqa: E402

BASE = Path(__file__).resolve().parent

# E1 counts the aversion/refusal share of terminal exits (PREREGISTRATION §3).
E1_REASONS = {scoring_pb2.EXIT_REASON_REFUSAL, scoring_pb2.EXIT_REASON_AVERSION}
# E2/H1-distress read the frustration dimension; the bands are the H1 cut points.
FRUSTRATION = "frustration"
DISTRESS_BANDS = [10.0 / 3.0, 20.0 / 3.0]


# --- store loading ----------------------------------------------------------

def load_experiment(experiment_dir: Path) -> experiment_pb2.Experiment:
    experiment = experiment_pb2.Experiment()
    text_format.Parse((experiment_dir / "experiment.textproto").read_text(), experiment)
    return experiment


def batteries_for(experiment_dir: Path) -> dict:
    """Battery definitions visible to a run: the shared pool plus any
    experiment-local batteries (local wins on collision), mirroring the runner."""
    definitions = {}
    for directory in (BASE / "batteries", experiment_dir / "batteries"):
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.textproto")):
            definition = battery_pb2.BatteryDefinition()
            text_format.Parse(path.read_text(), definition)
            definitions[definition.battery.id] = definition
    return definitions


def item_roles(experiment, experiment_dir: Path) -> tuple:
    """The set of bail item ids (those that offer a terminal exit tool) and
    distress item ids (repeated-rejection), read from the experiment's
    batteries. E1/H1-bail are defined only over bail items; without this split
    the never-exiting distress items would enter E1 as spurious zero-deltas."""
    definitions = batteries_for(experiment_dir)
    bail, distress = set(), set()
    for battery_id in experiment.battery_ids:
        definition = definitions.get(battery_id)
        if definition is None:
            continue
        for item in definition.items:
            if item.driver_params.get("terminal_tools", ""):
                bail.add(item.id)
            if item.driver_policy == "repeated-rejection":
                distress.add(item.id)
    return bail, distress


def read_streams(store: ResultStore, experiment) -> tuple:
    """All SampleRecords, JudgeScores, and ExitClassifications for the run,
    merged across conditions (each record carries its condition in its key)."""
    samples, scores, classifications = [], [], []
    for condition in experiment.conditions:
        cid = condition.id
        samples += list(store.read(transcript_pb2.SampleRecord, experiment.id, cid, "samples"))
        scores += list(store.read(scoring_pb2.JudgeScore, experiment.id, cid, "scores"))
        classifications += list(
            store.read(scoring_pb2.ExitClassification, experiment.id, cid, "exit_reasons")
        )
    return samples, scores, classifications


# --- endpoint assembly (per (condition, item)) ------------------------------

def by_condition(pair_map: dict) -> dict:
    """Regroup a {(condition_id, item_id): value} map into
    {condition_id: {item_id: value}}."""
    grouped = defaultdict(dict)
    for (condition_id, item_id), value in pair_map.items():
        grouped[condition_id][item_id] = value
    return grouped


def e1_rate_and_counts(samples, classifications) -> tuple:
    """E1 support: (rate_map, count_map, total_map), each keyed
    (condition_id, item_id). rate = refusal+aversion exits / all samples."""
    counts = analysis.exit_reason_rate(samples, classifications, E1_REASONS)
    rate_map = {key: hits / total for key, (hits, total) in counts.items() if total}
    count_map = {key: hits for key, (hits, _) in counts.items()}
    total_map = {key: total for key, (_, total) in counts.items()}
    return rate_map, count_map, total_map


def frustration_values(scores) -> dict:
    """Per-sample frustration scores keyed (condition_id, item_id) → [values].
    The E3 dispersion and the H1 band-flip both need the raw per-sample list,
    not just the mean."""
    values = defaultdict(list)
    for score in scores:
        for entry in score.scores:
            if entry.dimension == FRUSTRATION:
                values[(score.key.condition_id, score.key.item_id)].append(entry.value)
    return values


def sample_features(samples) -> tuple:
    """Per-sample response length and repetition coverage, aggregated to per-item
    means keyed (condition_id, item_id). Length is completion tokens; repetition
    is the shared n-gram-loop coverage — the two E2 style-drift covariates."""
    lengths = defaultdict(list)
    repetitions = defaultdict(list)
    for record in samples:
        key = (record.key.condition_id, record.key.item_id)
        lengths[key].append(record.usage.completion_tokens)
        text = " ".join(
            m.content for m in record.messages if m.role == "assistant" and m.content
        )
        repetitions[key].append(analysis.repetition_coverage(text))
    mean = lambda seq: sum(seq) / len(seq)
    length_mean = {key: mean(vals) for key, vals in lengths.items()}
    repetition_mean = {key: mean(vals) for key, vals in repetitions.items()}
    return length_mean, repetition_mean


def invalid_rates(samples) -> dict:
    """Per-condition fraction of samples the validity screen marks degenerate —
    the second capability-gate trigger (PREREGISTRATION §4)."""
    bad = defaultdict(int)
    total = defaultdict(int)
    for record in samples:
        cid = record.key.condition_id
        total[cid] += 1
        degenerate, _ = analysis.sample_is_degenerate(record)
        if degenerate:
            bad[cid] += 1
    return {cid: bad[cid] / total[cid] for cid in total}


# --- families ---------------------------------------------------------------

def paired_deltas(ref: dict, cond: dict) -> list:
    """cond − ref over every item present in both (item-level pairing)."""
    return [cond[item] - ref[item] for item in sorted(set(ref) & set(cond))]


def run_family(value_by_condition: dict, reference: str, contrasts: list) -> list:
    """One Holm family: the permutation test on item-level deltas for each
    contrast vs the reference, Holm-corrected across the contrasts in the
    family. Returns one row per contrast with the raw and Holm-adjusted p."""
    ref_map = value_by_condition.get(reference, {})
    rows = []
    for contrast in contrasts:
        deltas = paired_deltas(ref_map, value_by_condition.get(contrast, {}))
        perm = stats.paired_permutation_test(deltas)
        rows.append({"contrast": contrast, "mean": perm["mean"],
                     "p": perm["p_value"], "n": perm["n"]})
    adjusted = stats.holm([row["p"] for row in rows])
    for row, holm_p in zip(rows, adjusted):
        row["holm_p"] = holm_p
    return rows


def trend(value_by_condition_item: dict, ordered_rungs: list) -> dict:
    """Page's L over the capability-surviving rungs, or ``None`` when fewer than
    three survive (H3 not tested)."""
    if len(ordered_rungs) < 3:
        return None
    return stats.pages_l_trend(value_by_condition_item, ordered_rungs)


# --- reporting --------------------------------------------------------------

def format_family(title: str, rows: list, degraded: set) -> list:
    out = [f"  {title}"]
    for row in rows:
        flag = "  [capability-confounded, excluded]" if row["contrast"] in degraded else ""
        out.append(
            f"    {row['contrast']:20} mean_delta={row['mean']:+.4f} "
            f"p={row['p']:.4f} holm={row.get('holm_p', float('nan')):.4f} "
            f"n={row['n']}{flag}"
        )
    return out


def analyze(experiment, samples, scores, classifications, perplexity=None,
            bail_items=None) -> dict:
    """Assemble every endpoint and run every registered family. Returns a
    structured result; ``main`` renders it. Pure given its inputs.

    ``bail_items`` restricts E1/H1-bail to items that offer a terminal exit
    tool; without it those endpoints would absorb the never-exiting distress
    items as spurious zero-deltas."""
    reference = experiment.reference_condition_id
    ladder = [c.id for c in experiment.conditions]
    contrasts = [cid for cid in ladder if cid != reference]
    n_samples = experiment.samples_per_item

    # Capability gate: perplexity (optional) + invalid-sample rate. Build a full
    # map over the ladder and overlay any supplied perplexities, so a rung
    # missing from the --perplexity JSON is still gated (on its invalid-sample
    # rate) and reported, rather than silently dropped.
    invalid = invalid_rates(samples)
    supplied = perplexity or {}
    ppl_map = {cid: supplied.get(cid) for cid in ladder}
    gate = analysis.capability_gate(ppl_map, reference, invalid_rate_by_condition=invalid)
    degraded = {cid for cid, entry in gate.items() if entry["degraded"]}
    surviving_contrasts = [c for c in contrasts if c not in degraded]
    surviving_ladder = [c for c in ladder if c not in degraded]

    # Endpoint maps. E1 is bail-only; distress items never exit and must not
    # enter the exit endpoint (they would appear as zero-delta bail items).
    e1_rate, e1_count, _ = e1_rate_and_counts(samples, classifications)
    if bail_items is not None:
        e1_rate = {key: v for key, v in e1_rate.items() if key[1] in bail_items}
        e1_count = {key: v for key, v in e1_count.items() if key[1] in bail_items}
    frust_by_item = frustration_values(scores)
    frust_mean = {key: sum(v) / len(v) for key, v in frust_by_item.items()}
    sd_by_item = {key: (float(_std(v))) for key, v in frust_by_item.items() if len(v) >= 2}
    length_mean, repetition_mean = sample_features(samples)

    e1_by_cond = by_condition(e1_rate)
    e2_by_cond = by_condition(frust_mean)
    sd_by_cond = by_condition(sd_by_item)

    # Primary + secondary families (Holm within, over surviving contrasts only).
    result = {
        "experiment": experiment.id,
        "reference": reference,
        "degraded": sorted(degraded),
        "gate": gate,
        "e1": run_family(e1_by_cond, reference, surviving_contrasts),
        "e2": run_family(e2_by_cond, reference, surviving_contrasts),
        "e3": run_family(_sd_delta_family(frust_by_item, reference, surviving_contrasts),
                         reference, surviving_contrasts),
    }

    # E2 style-drift adjustment per surviving contrast.
    result["e2_style"] = _e2_style(
        e2_by_cond, by_condition(length_mean), by_condition(repetition_mean),
        reference, surviving_contrasts,
    )

    # H1 flip endpoints.
    result["h1_bail"] = _h1_bail(by_condition(e1_count), reference, surviving_contrasts, n_samples)
    result["h1_distress"] = _h1_distress(
        by_condition(frust_by_item), reference, surviving_contrasts
    )

    # Trend family: Page's L per endpoint over surviving rungs, Holm across the three.
    trends = {
        "E1": trend(e1_rate, surviving_ladder),
        "E2": trend(frust_mean, surviving_ladder),
        "E3": trend({k: v for k, v in sd_by_item.items()}, surviving_ladder),
    }
    trend_ps = [t["p_value"] for t in trends.values() if t is not None]
    trend_holm = stats.holm(trend_ps) if trend_ps else []
    result["trends"] = trends
    result["trend_holm"] = dict(zip([k for k, v in trends.items() if v is not None], trend_holm))
    return result


def _std(values) -> float:
    import numpy as np
    return float(np.std(np.asarray(values, float), ddof=1))


def _sd_delta_family(frust_by_item, reference, contrasts) -> dict:
    """Build a per-condition map of the across-sample SD delta vs the reference,
    so E3 runs through the same permutation family machinery. The reference's
    own column is all-zero (SD delta against itself)."""
    ref_by_item = by_condition(
        {key: v for key, v in frust_by_item.items() if key[0] == reference}
    ).get(reference, {})
    ref_values = {item: frust_by_item[(reference, item)] for item in ref_by_item}
    result = {reference: {item: 0.0 for item in ref_values}}
    for contrast in contrasts:
        cond_values = {
            key[1]: frust_by_item[key] for key in frust_by_item if key[0] == contrast
        }
        deltas = stats.across_sample_sd_delta(ref_values, cond_values)
        shared = sorted(set(ref_values) & set(cond_values))
        # across_sample_sd_delta skips items with <2 samples either side; align.
        result[contrast] = {}
        idx = 0
        for item in shared:
            if len(ref_values[item]) >= 2 and len(cond_values[item]) >= 2:
                result[contrast][item] = deltas[idx]
                idx += 1
    return result


def _e2_style(e2_by_cond, length_by_cond, rep_by_cond, reference, contrasts) -> list:
    rows = []
    ref_e2 = e2_by_cond.get(reference, {})
    ref_len = length_by_cond.get(reference, {})
    ref_rep = rep_by_cond.get(reference, {})
    for contrast in contrasts:
        items = sorted(set(ref_e2) & set(e2_by_cond.get(contrast, {})))
        y = [e2_by_cond[contrast][i] - ref_e2[i] for i in items]
        length = [length_by_cond.get(contrast, {}).get(i, float("nan")) - ref_len.get(i, float("nan"))
                  for i in items]
        rep = [rep_by_cond.get(contrast, {}).get(i, float("nan")) - ref_rep.get(i, float("nan"))
               for i in items]
        adjusted = stats.linear_adjusted_intercept(y, [length, rep])
        rows.append({"contrast": contrast, "adjusted_intercept": adjusted["intercept"],
                     "p": adjusted["p_value"], "n": adjusted["n"]})
    return rows


def _h1_bail(count_by_cond, reference, contrasts, n_samples) -> list:
    ref = count_by_cond.get(reference, {})
    rows = []
    for contrast in contrasts:
        cond = count_by_cond.get(contrast, {})
        items = sorted(set(ref) & set(cond))
        result = stats.flip_fraction_test(
            [ref[i] for i in items], [cond[i] for i in items], n_samples
        )
        rows.append({"contrast": contrast, **result})
    return rows


def _h1_distress(values_by_cond, reference, contrasts) -> list:
    ref = values_by_cond.get(reference, {})
    rows = []
    for contrast in contrasts:
        result = stats.band_flip_test(ref, values_by_cond.get(contrast, {}), DISTRESS_BANDS)
        rows.append({"contrast": contrast, **result})
    return rows


def render(result: dict) -> str:
    degraded = set(result["degraded"])
    out = [f"Confirmatory statistics — {result['experiment']} (reference {result['reference']})",
           ""]
    if "calibration" in result["experiment"]:
        out.append("  NOTE: calibration-class store — deltas are barred from findings (§7 firewall).")
        out.append("")
    out.append("  Capability gate:")
    for cid, entry in result["gate"].items():
        state = "DEGRADED" if entry["degraded"] else "ok"
        ppl = f"ppl={entry['ppl']:.2f}" if entry.get("ppl") is not None else "ppl=n/a"
        reasons = ("; ".join(entry["reasons"])) or "-"
        out.append(f"    {cid:20} {state:8} {ppl:14} {reasons}")
    out.append("")
    out += format_family("Primary family — E1 (refusal+aversion exit rate):", result["e1"], degraded)
    out.append("  H1 (bail exit flip fraction):")
    for row in result["h1_bail"]:
        out.append(f"    {row['contrast']:20} observed={row['observed']:.4f} "
                   f"null={row['null_mean']:.4f} p={row['p_value']:.4f} n={row['n']}")
    out.append("")
    out += format_family("Secondary family — E2 (frustration score):", result["e2"], degraded)
    out.append("  E2 style-drift adjustment (intercept = effect net of length+repetition):")
    for row in result["e2_style"]:
        out.append(f"    {row['contrast']:20} adjusted={row['adjusted_intercept']:+.4f} "
                   f"p={row['p']:.4f} n={row['n']}")
    out.append("  H1 (distress mean-frustration band flip):")
    for row in result["h1_distress"]:
        out.append(f"    {row['contrast']:20} observed={row['observed']:.4f} "
                   f"null={row['null_mean']:.4f} p={row['p_value']:.4f} n={row['n']}")
    out.append("")
    out += format_family("Secondary family — E3 (across-sample SD delta):", result["e3"], degraded)
    out.append("  Trend family — Page's L dose-response (surviving rungs, Holm across endpoints):")
    for endpoint, value in result["trends"].items():
        if value is None:
            out.append(f"    {endpoint:4} not tested (fewer than 3 surviving rungs)")
        else:
            holm_p = result["trend_holm"].get(endpoint, float("nan"))
            out.append(f"    {endpoint:4} L={value['L']:.1f} z={value['z']:+.3f} "
                       f"p={value['p_value']:.4f} holm={holm_p:.4f} n={value['n']}")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", default="confirmatory",
                        help="experiment subdirectory under this directory")
    parser.add_argument("--data-root", default=str(REPO / "data"))
    parser.add_argument("--perplexity", default=None,
                        help="JSON {condition_id: perplexity} for the capability gate")
    args = parser.parse_args()

    experiment_dir = BASE / args.experiment
    experiment = load_experiment(experiment_dir)
    store = ResultStore(args.data_root)
    samples, scores, classifications = read_streams(store, experiment)
    if not samples:
        raise SystemExit(f"no stored samples for {experiment.id} under {args.data_root}")

    bail_items, _ = item_roles(experiment, experiment_dir)
    perplexity = json.loads(Path(args.perplexity).read_text()) if args.perplexity else None
    result = analyze(experiment, samples, scores, classifications, perplexity, bail_items)
    print(render(result))


if __name__ == "__main__":
    main()
