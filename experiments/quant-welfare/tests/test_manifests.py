"""Validation of the checked-in trial manifests.

These run in the hermetic suite: they parse the textproto files and check
the cross-references the runner depends on, so a manifest typo fails in
tests rather than mid-run.
"""

from pathlib import Path

from google.protobuf import text_format

from modelwelfare.driver import policy_for
from modelwelfare.v1 import battery_pb2, experiment_pb2

TRIAL = Path(__file__).resolve().parents[1] / "trial"


def experiment():
    parsed = experiment_pb2.Experiment()
    text_format.Parse((TRIAL / "experiment.textproto").read_text(), parsed)
    return parsed


def batteries():
    parsed = {}
    for path in sorted((TRIAL / "batteries").glob("*.textproto")):
        definition = battery_pb2.BatteryDefinition()
        text_format.Parse(path.read_text(), definition)
        parsed[definition.battery.id] = definition
    return parsed


def test_experiment_references_resolve():
    exp = experiment()
    defs = batteries()
    assert set(exp.battery_ids) == set(defs.keys())
    assert exp.reference_condition_id in {c.id for c in exp.conditions}
    assert exp.samples_per_item > 0
    assert len({c.id for c in exp.conditions}) == len(exp.conditions)


def test_conditions_are_comparable():
    exp = experiment()
    reference = next(c for c in exp.conditions if c.id == exp.reference_condition_id)
    for condition in exp.conditions:
        assert condition.sampling == reference.sampling, (
            f"{condition.id}: sampling differs from reference; precision would "
            "be confounded with sampling parameters"
        )
        assert condition.model.family == reference.model.family


def test_items_are_well_formed():
    for definition in batteries().values():
        rubric_ids = {rubric.id for rubric in definition.rubrics}
        assert set(definition.battery.rubric_ids) <= rubric_ids
        for item in definition.items:
            assert item.battery_id == definition.battery.id
            policy_for(item)
            terminal = {
                name.strip()
                for name in item.driver_params.get("terminal_tools", "").split(",")
                if name.strip()
            }
            affordance_names = {a.name for a in item.affordances}
            assert terminal <= affordance_names, (
                f"{item.id}: terminal tool not offered as an affordance"
            )
            if item.driver_policy == "repeated-rejection":
                assert int(item.driver_params["turns"]) > 0
                assert item.driver_params["rejection"]


def test_item_ids_unique_across_batteries():
    seen = set()
    for definition in batteries().values():
        for item in definition.items:
            assert item.id not in seen, f"duplicate item id {item.id}"
            seen.add(item.id)
