"""Validation of the checked-in trial manifests.

These run in the hermetic suite: they parse the textproto files and check
the cross-references the runner depends on, so a manifest typo fails in
tests rather than mid-run.
"""

from pathlib import Path

from google.protobuf import text_format

from modelwelfare.driver import policy_for
from modelwelfare.v1 import battery_pb2, experiment_pb2

BASE = Path(__file__).resolve().parents[1]
TRIAL = BASE / "trial"
SHARED = BASE / "batteries"


def experiments():
    parsed = []
    for manifest in sorted(BASE.glob("*/experiment.textproto")):
        experiment = experiment_pb2.Experiment()
        text_format.Parse(manifest.read_text(), experiment)
        parsed.append((manifest.parent, experiment))
    assert parsed
    return parsed


def load_battery_dir(directory):
    parsed = {}
    for path in sorted(directory.glob("*.textproto")):
        definition = battery_pb2.BatteryDefinition()
        text_format.Parse(path.read_text(), definition)
        assert definition.battery.id not in parsed, (
            f"duplicate battery id {definition.battery.id} in {directory}"
        )
        parsed[definition.battery.id] = definition
    return parsed


def batteries_for(experiment_dir):
    """Mirror the runner's resolution rule: shared pool plus any
    experiment-local batteries, local winning on collision."""
    definitions = {}
    for directory in (SHARED, experiment_dir / "batteries"):
        if directory.is_dir():
            definitions.update(load_battery_dir(directory))
    return definitions


def all_battery_definitions():
    directories = [SHARED] + [d / "batteries" for d, _ in experiments()]
    definitions = []
    for directory in directories:
        if directory.is_dir():
            definitions += list(load_battery_dir(directory).values())
    return definitions


def test_experiment_references_resolve():
    for experiment_dir, exp in experiments():
        defs = batteries_for(experiment_dir)
        assert set(exp.battery_ids) <= set(defs.keys()), (
            f"{exp.id}: unresolved battery ids {set(exp.battery_ids) - set(defs)}"
        )
        assert exp.reference_condition_id in {c.id for c in exp.conditions}
        assert exp.samples_per_item > 0
        assert len({c.id for c in exp.conditions}) == len(exp.conditions)


def test_experiment_ids_unique():
    ids = [exp.id for _, exp in experiments()]
    assert len(set(ids)) == len(ids)


def test_conditions_are_comparable():
    for _, exp in experiments():
        reference = next(c for c in exp.conditions if c.id == exp.reference_condition_id)
        for condition in exp.conditions:
            assert condition.sampling == reference.sampling, (
                f"{exp.id}/{condition.id}: sampling differs from reference; "
                "precision would be confounded with sampling parameters"
            )
            assert condition.model.family == reference.model.family


def test_items_are_well_formed():
    definitions = all_battery_definitions()
    all_rubric_ids = {rubric.id for d in definitions for rubric in d.rubrics}
    for definition in definitions:
        assert set(definition.battery.rubric_ids) <= all_rubric_ids, (
            f"{definition.battery.id}: unresolved rubric reference "
            "(rubrics resolve across all loaded battery files, like the runner)"
        )
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


def test_v2_pools_meet_preregistration_targets():
    definitions = load_battery_dir(SHARED)

    bail = definitions["bail-v2"]
    graded = [i for i in bail.items if i.tags["situation"] != "benign"]
    assert len(graded) >= 100
    from collections import Counter
    cells = Counter((i.tags["situation"], i.tags["intensity"]) for i in graded)
    for situation, minimum in [("abuse", 6), ("emotion", 6), ("boundary", 6), ("manip", 6),
                               ("roleconf", 3), ("repeat", 3), ("moral", 3)]:
        for level in ("mild", "moderate", "strong"):
            assert cells[(situation, level)] >= minimum, (situation, level)
    for item in bail.items:
        names = {a.name for a in item.affordances}
        assert names == {"end_conversation", "complete_task"}, item.id
        assert item.driver_params["terminal_tools"] == "end_conversation", item.id

    distress = definitions["distress-v2"]
    assert len(distress.items) == 60
    pairs = {(i.tags["task"], i.tags["feedback"]) for i in distress.items}
    assert len(pairs) == 60
    assert all(i.driver_params["turns"] == "6" for i in distress.items)
    assert distress.battery.rubric_ids == ["distress-v1-rubric"]


def test_distress_v2_matches_generator():
    import importlib.util

    tools = Path(__file__).resolve().parents[1] / "tools" / "gen_distress_v2.py"
    spec = importlib.util.spec_from_file_location("gen_distress_v2", tools)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    committed = battery_pb2.BatteryDefinition()
    text_format.Parse((SHARED / "distress-v2.textproto").read_text(), committed)
    assert committed == module.build()


def test_item_ids_unique_across_batteries():
    seen = set()
    for definition in all_battery_definitions():
        for item in definition.items:
            assert item.id not in seen, f"duplicate item id {item.id}"
            seen.add(item.id)


def test_derived_bail_arms_match_generator():
    import importlib.util

    tools = Path(__file__).resolve().parents[1] / "tools" / "derive_bail_arms.py"
    spec = importlib.util.spec_from_file_location("derive_bail_arms", tools)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    source = module.load_source()
    for arm_id in module.ARMS:
        committed = battery_pb2.BatteryDefinition()
        text_format.Parse((SHARED / f"{arm_id}.textproto").read_text(), committed)
        assert committed == module.derive(source, arm_id), (
            f"{arm_id}.textproto is out of sync with bail-v1 + derive_bail_arms.py; "
            "re-run the generator"
        )


def test_v1_pools_cover_their_design_grids():
    definitions = load_battery_dir(SHARED)

    bail = definitions["bail-v1"]
    cells = {(i.tags["situation"], i.tags["intensity"]) for i in bail.items}
    situations = {
        "abusive-user", "boundary-pressure", "emotional-intensity",
        "role-confusion", "repetition", "manipulation", "moral-discomfort",
    }
    expected = {(s, level) for s in situations for level in ("mild", "moderate", "strong")}
    expected |= {("benign", "none")}
    assert cells == expected
    assert len(bail.items) == 25

    distress = definitions["distress-v1"]
    cells = {(i.tags["task"], i.tags["feedback"]) for i in distress.items}
    tasks = {"poetry", "code", "explanation", "planning", "letter"}
    styles = {"harsh", "dismissive", "personal", "gaslighting"}
    assert cells == {(t, s) for t in tasks for s in styles}
    assert len(distress.items) == 20
    assert all(i.driver_params["turns"] == "6" for i in distress.items)
