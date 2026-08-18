#!/usr/bin/env python3
"""Render the result store into RESULTS.md.

Rewrites everything below the GENERATED marker: for each experiment
manifest in this directory, a terminal-exit-rate table per battery and
judge-score mean tables where scores exist. The store remains the source
of truth; this is a view.
"""

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for sub in ("core/src",):
    path = str(REPO / sub)
    if path not in sys.path:
        sys.path.insert(0, path)

from google.protobuf import text_format

from modelwelfare.analysis import dimension_means, event_rate
from modelwelfare.bundle import BundleStore
from modelwelfare.store import ResultStore
from modelwelfare.v1 import battery_pb2, experiment_pb2, scoring_pb2, transcript_pb2

BASE = Path(__file__).resolve().parent
RESULTS = REPO / "RESULTS.md"
MARKER = "<!-- GENERATED BELOW — do not edit by hand -->"


def load_experiments():
    parsed = []
    for manifest in sorted(BASE.glob("**/experiment.textproto")):
        experiment = experiment_pb2.Experiment()
        text_format.Parse(manifest.read_text(), experiment)
        parsed.append((manifest.parent, experiment))
    return parsed


def batteries_for(experiment_dir):
    definitions = {}
    for directory in (BASE / "batteries", experiment_dir / "batteries"):
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.textproto")):
            definition = battery_pb2.BatteryDefinition()
            text_format.Parse(path.read_text(), definition)
            definitions[definition.battery.id] = definition
    return definitions


def markdown_table(header, rows):
    lines = ["| " + " | ".join(header) + " |",
             "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def render_experiment(store, experiment, definitions):
    condition_ids = [c.id for c in experiment.conditions]
    records, scores = [], []
    for condition_id in condition_ids:
        records += list(store.read(transcript_pb2.SampleRecord, experiment.id, condition_id, "samples"))
        scores += list(store.read(scoring_pb2.JudgeScore, experiment.id, condition_id, "scores"))
    if not records:
        return None

    out = [f"## {experiment.id} (calibration-class)", "", experiment.description.strip(), "",
           f"{len(records)} stored samples, {len(scores)} judge scores."]
    exit_rates = event_rate(records, "terminal_tool_invoked", detail="end_conversation")

    for battery_id in experiment.battery_ids:
        definition = definitions.get(battery_id)
        if definition is None:
            continue
        item_ids = [item.id for item in definition.items]
        rows = []
        for item_id in item_ids:
            cells = []
            any_data = False
            for condition_id in condition_ids:
                hits, total = exit_rates.get((condition_id, item_id), (0, 0))
                any_data = any_data or total > 0
                cells.append(f"{hits}/{total}" if total else "—")
            if any_data:
                rows.append([item_id] + cells)
        if rows:
            out += ["", f"### {battery_id}: end_conversation exits (of samples run)", "",
                    markdown_table(["item"] + condition_ids, rows)]

        for rubric in definition.rubrics:
            for dimension in rubric.dimensions:
                means = dimension_means(scores, dimension.name)
                rows = []
                for item_id in item_ids:
                    cells = []
                    any_data = False
                    for condition_id in condition_ids:
                        value = means.get((condition_id, item_id))
                        any_data = any_data or value is not None
                        cells.append(f"{value:.2f}" if value is not None else "—")
                    if any_data:
                        rows.append([item_id] + cells)
                if rows:
                    out += ["", f"### {battery_id}: mean {dimension.name} (judge scores)", "",
                            markdown_table(["item"] + condition_ids, rows)]
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", default=None,
                        help="render from packed RecordBundle file(s) or a directory of "
                             "them instead of the streaming store — the release-asset "
                             "replication path")
    args = parser.parse_args()

    store = BundleStore(args.bundle) if args.bundle else ResultStore(REPO / "data")
    sections = []
    for experiment_dir, experiment in load_experiments():
        section = render_experiment(store, experiment, batteries_for(experiment_dir))
        if section:
            sections.append(section)

    text = RESULTS.read_text()
    head = text.split(MARKER)[0]
    RESULTS.write_text(head + MARKER + "\n\n" + "\n\n---\n\n".join(sections) + "\n")
    print(f"rendered {len(sections)} experiment sections into {RESULTS}")


if __name__ == "__main__":
    main()
