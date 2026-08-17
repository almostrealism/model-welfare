"""Validation of the judge-bakeoff fixtures."""

import importlib.util
from pathlib import Path

BAKEOFF = Path(__file__).resolve().parents[1] / "study1" / "bakeoff"


def load_synthetics():
    spec = importlib.util.spec_from_file_location("bakeoff_synthetics", BAKEOFF / "synthetics.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_distress_synthetics_cover_all_dimensions_at_both_poles():
    synthetics = load_synthetics()
    rubric = synthetics.distress_rubric()
    dimensions = {d.name for d in rubric.dimensions}
    covered = set()
    for item_id, (dimension, pole) in synthetics.DISTRESS_EXPECTATIONS.items():
        assert dimension in dimensions
        assert pole in ("high", "low")
        covered.add((dimension, pole))
    assert covered == {(d, p) for d in dimensions for p in ("high", "low")}
    ids = {r.key.item_id for r in synthetics.DISTRESS_SYNTHETICS}
    assert ids == set(synthetics.DISTRESS_EXPECTATIONS)


def test_exit_synthetics_cover_all_classes():
    synthetics = load_synthetics()
    assert set(synthetics.EXIT_EXPECTATIONS.values()) == set(synthetics.EXIT_CLASSES)
    assert {d.name for d in synthetics.EXIT_RUBRIC.dimensions} == set(synthetics.EXIT_CLASSES)
    for record in synthetics.EXIT_SYNTHETICS:
        last = record.messages[-1]
        assert last.tool_calls and last.tool_calls[0].name == "end_conversation"


def test_synthetic_records_are_well_formed():
    synthetics = load_synthetics()
    for record in synthetics.DISTRESS_SYNTHETICS + synthetics.EXIT_SYNTHETICS:
        assert record.key.experiment_id == synthetics.EXPERIMENT_ID
        assert record.key.condition_id == "synthetic"
        assert len(record.messages) >= 3
        assert [m.turn_index for m in record.messages] == list(range(len(record.messages)))
