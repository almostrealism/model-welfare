"""End-to-end tests for the Study 2 analysis driver over a fabricated world.

Built BEFORE any confirmatory data exists (the registered-statistics-as-
tested-code discipline): the world's geometry is designed so every
registered endpoint has a known answer — the w4 rung degrades the welfare
probes and shifts the distress projection while the control probe, the
judge scores, and the dispersions hold still; w8 changes nothing. The
assertions pin the resulting family verdicts, the comparative
differential, the specificity gate, the AUROC companion, the trend
directions, and the §4.4 dissociation verdicts (including the bail cell
against the real published E1 golden values).
"""
import sys
from pathlib import Path

import numpy as np
import pytest

BASE = Path(__file__).resolve().parents[1]
for entry in (str(BASE), str(BASE / "tools")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

import analyze  # noqa: E402
import analyze_tier2 as tier2  # noqa: E402
from modelwelfare import activations  # noqa: E402
from modelwelfare.driver import TERMINAL_TOOL_INVOKED  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import activation_pb2, common_pb2  # noqa: E402
from modelwelfare.v1 import scoring_pb2, transcript_pb2  # noqa: E402

HIDDEN = 6
E_EXIT = np.eye(HIDDEN, dtype=np.float32)[0]
E_BAND = np.eye(HIDDEN, dtype=np.float32)[1]
E_CTRL = np.eye(HIDDEN, dtype=np.float32)[2]

MODE_A = "s2-mode-a"
MODE_B = "s2-mode-b"
MODE_C = "s2-mode-c"
STUDY1 = "study1-fixture"

REF = tier2.REFERENCE
W8, W4 = tier2.CONFIRMATORY
W3 = tier2.DEGRADED
ALL = [REF, W8, W4, W3]

# Ten real distress-v3 items (one style), split across the analytic and
# compositional halves so the control probe has both classes.
V3_ITEMS = [f"distress-v3-{task}-harsh" for task in (
    "code", "regex", "summary", "explain", "inflation",
    "poem", "limerick", "letter", "plan", "rewrite")]
# Judge frustration at the reference scoring: five high-band, five
# low-band items (fixed labels for the distress-band probe).
V3_JUDGE = {item: (9.0 if index % 2 == 0 else 0.5)
            for index, item in enumerate(V3_ITEMS)}
# Real distress-v2 items for the bridge reads (Mode A/B share the store
# scope with other batteries, so the item filter is load-bearing).
V2_ITEMS = sorted(tier2.battery_tasks("distress-v2"))[:6]
SAMPLES = 2


def _capture(path, conversations):
    import json as _json
    from safetensors.numpy import save_file
    tensors = {}
    manifest = {"point": "residual_post", "layers": [tier2.FROZEN_LAYER],
                "conversations": []}
    for conversation_id, turns in conversations.items():
        spans = []
        for message_index, vector in sorted(turns.items()):
            tensors[f"{conversation_id}|t{message_index}"
                    f"|L{tier2.FROZEN_LAYER}"] = vector.astype(np.float32)
            spans.append({"message_index": message_index,
                          "start": 0, "end": 4})
        manifest["conversations"].append(
            {"id": conversation_id, "n_tokens": 32,
             "assistant_spans": spans})
    save_file(tensors, str(path))
    path.with_name(path.name + ".manifest.json").write_text(
        _json.dumps(manifest))
    return path


def _sample(experiment, condition, item, index, content, exited=False):
    record = transcript_pb2.SampleRecord(key=common_pb2.ResultKey(
        experiment_id=experiment, condition_id=condition,
        item_id=item, sample_index=index))
    record.messages.append(transcript_pb2.Message(role="user", content="go"))
    record.messages.append(
        transcript_pb2.Message(role="assistant", content=content))
    if exited:
        record.messages.append(
            transcript_pb2.Message(role="user", content="more"))
        terminal = transcript_pb2.Message(role="assistant", content="")
        terminal.tool_calls.append(transcript_pb2.ToolCall(
            name="end_conversation", arguments_json="{}"))
        record.messages.append(terminal)
        record.outcomes.append(transcript_pb2.OutcomeEvent(
            name=TERMINAL_TOOL_INVOKED, detail="end_conversation"))
    record.usage.completion_tokens = 100
    return record


def _score(experiment, condition, item, index, value):
    score = scoring_pb2.JudgeScore(key=common_pb2.ResultKey(
        experiment_id=experiment, condition_id=condition,
        item_id=item, sample_index=index))
    score.scores.append(scoring_pb2.DimensionScore(
        dimension="frustration", value=value))
    return score


@pytest.fixture
def world(tmp_path):
    """The designed world: w4 degrades welfare reads, w8 changes nothing,
    w3 mirrors the reference (its rows exist but are confounded-only)."""
    store = ResultStore(tmp_path / "data")

    experiment = analyze.load_experiment(BASE / "study1" / "confirmatory")
    definitions = analyze.batteries_for(BASE / "study1" / "confirmatory")
    bail_items, _ = analyze.item_roles(experiment, definitions)
    bail = sorted(bail_items)[:10]
    exit_of = {item: index % 2 == 0 for index, item in enumerate(bail)}

    # Every rung gets its own Study 1 transcripts (the R2c leakage-safe
    # turn allowance is computed per rung over that rung's OWN trajectories);
    # R1 reads only the reference condition's.
    for condition in ALL:
        with store.writer(STUDY1, condition, "samples", "test") as writer:
            for item in bail:
                for index in range(SAMPLES):
                    writer.write(_sample(STUDY1, condition, item, index,
                                         f"working on {item} {index}",
                                         exited=exit_of[item]))

    # Mode A captures: bail features on the exit axis, v3 features on the
    # band + control axes. w4 negates the welfare axes only; the control
    # axis never moves — the designed differential.
    for condition in ALL:
        flip = -1.0 if condition == W4 else 1.0
        conversations = {}
        for item in bail:
            sign = 1.0 if exit_of[item] else -1.0
            for index in range(SAMPLES):
                conversations[f"{item}|s{index}"] = {
                    1: E_EXIT * sign * flip}
        # w4 additionally applies a uniform offset along an axis no probe
        # reads (the designed direction-specificity signal: a real shift
        # along the fixture's "distress" direction, invisible to the
        # control direction and to every probe endpoint).
        offset = E_EXIT * (3.0 if condition == W4 else 0.0)
        for item in V3_ITEMS:
            band_sign = 1.0 if V3_JUDGE[item] >= 5.0 else -1.0
            task = item.split("-")[2]
            ctrl_sign = 1.0 if task in tier2.CONTROL_SPLITS[
                "control_analytic"] else -1.0
            for index in range(SAMPLES):
                conversations[f"{item}|s{index}"] = {
                    1: E_BAND * -9.0,
                    3: E_BAND * band_sign * flip + E_CTRL * ctrl_sign
                    + offset}
        capture = _capture(
            tmp_path / f"mode-a-{condition}.safetensors", conversations)
        activations.ingest_capture(store, MODE_A, condition, capture,
                                   tier2.FROZEN_LAYER, "test")

    # Mode C: samples + judge scores (identical across rungs — B2/B3/B4
    # null by design) and projection records (distress +1.0 at w4 only).
    for condition in ALL:
        shift = 1.0 if condition == W4 else 0.0
        with store.writer(MODE_C, condition, "samples", "test") as writer:
            for item in V3_ITEMS:
                for index in range(SAMPLES):
                    writer.write(_sample(
                        MODE_C, condition, item, index,
                        f"answer {item} {index} under {condition}"))
        with store.writer(MODE_C, condition, "scores", "test") as writer:
            for item in V3_ITEMS:
                for index in range(SAMPLES):
                    writer.write(_score(MODE_C, condition, item, index,
                                        V3_JUDGE[item]))
        with store.writer(MODE_C, condition, "projections", "test") as writer:
            for item_index, item in enumerate(V3_ITEMS):
                for index in range(SAMPLES):
                    base = float(item_index) + 0.25 * index
                    for direction, value in (
                            (tier2.DISTRESS_DIRECTION, base + shift),
                            (tier2.AXIS_DIRECTION, 2.0)):
                        writer.write(activation_pb2.ProjectionSeries(
                            key=common_pb2.ResultKey(
                                experiment_id=MODE_C, condition_id=condition,
                                item_id=item, sample_index=index),
                            direction_id=direction, turn_index=3,
                            values=[value]))

    # Mode A distress projections for the distress-v2 bridge: a junk
    # first-turn value (constant, so mistaking it for the final turn zeroes
    # the designed w4 contrast) and the real final-turn read (+0.5 at w4).
    for condition in ALL:
        shift = 0.5 if condition == W4 else 0.0
        with store.writer(MODE_A, condition, "projections", "test") as writer:
            for item_index, item in enumerate(V2_ITEMS):
                for index in range(SAMPLES):
                    for turn, value in ((1, -50.0),
                                        (3, 0.1 * item_index + shift)):
                        writer.write(activation_pb2.ProjectionSeries(
                            key=common_pb2.ResultKey(
                                experiment_id=MODE_A, condition_id=condition,
                                item_id=item, sample_index=index),
                            direction_id=tier2.DISTRESS_DIRECTION,
                            turn_index=turn, values=[value]))

    # Mode B projections. Refusal direction over the bail items: the
    # allowed (leakage-safe) turn carries +2.0 at w4 only; the terminal
    # turn and a non-bail conversation carry poison values on the non-
    # reference rungs, so any filtering failure surfaces as a nonzero w8
    # contrast or an inflated n. Distress direction over the v2 items:
    # the own-trajectory bridge (+1.5 at w4).
    for condition in ALL:
        poison = 0.0 if condition == REF else 100.0
        with store.writer(MODE_B, condition, "projections", "test") as writer:
            for item_index, item in enumerate(bail):
                shift = 2.0 if condition == W4 else 0.0
                for index in range(SAMPLES):
                    for turn, value in ((1, 0.1 * item_index + shift),
                                        (3, poison)):
                        writer.write(activation_pb2.ProjectionSeries(
                            key=common_pb2.ResultKey(
                                experiment_id=MODE_B, condition_id=condition,
                                item_id=item, sample_index=index),
                            direction_id=tier2.REFUSAL_DIRECTION,
                            turn_index=turn, values=[value]))
            writer.write(activation_pb2.ProjectionSeries(
                key=common_pb2.ResultKey(
                    experiment_id=MODE_B, condition_id=condition,
                    item_id=V2_ITEMS[0], sample_index=0),
                direction_id=tier2.REFUSAL_DIRECTION,
                turn_index=1, values=[5.0 * poison]))
            for item_index, item in enumerate(V2_ITEMS):
                shift = 1.5 if condition == W4 else 0.0
                for index in range(SAMPLES):
                    writer.write(activation_pb2.ProjectionSeries(
                        key=common_pb2.ResultKey(
                            experiment_id=MODE_B, condition_id=condition,
                            item_id=item, sample_index=index),
                        direction_id=tier2.DISTRESS_DIRECTION,
                        turn_index=3, values=[0.1 * item_index + shift]))

    def weights(group, axis):
        return {f"{group}|L{tier2.FROZEN_LAYER}|weight": axis,
                f"{group}|L{tier2.FROZEN_LAYER}|bias":
                    np.zeros(1, dtype=np.float32),
                f"{group}|L{tier2.FROZEN_LAYER}|feature_mean":
                    np.zeros(HIDDEN, dtype=np.float32),
                f"{group}|L{tier2.FROZEN_LAYER}|feature_std":
                    np.ones(HIDDEN, dtype=np.float32)}

    from safetensors.numpy import save_file
    directions_path = tmp_path / "directions.safetensors"
    save_file({f"{tier2.DISTRESS_DIRECTION}|L{tier2.FROZEN_LAYER}": E_EXIT,
               f"{tier2.AXIS_DIRECTION}|L{tier2.FROZEN_LAYER}": E_BAND},
              str(directions_path))

    return store, weights("exit", E_EXIT), weights("distress_band", E_BAND), \
        weights("control_analytic", E_CTRL), directions_path


@pytest.fixture
def result(world):
    store, probes, probes_v3, probes_control, directions_path = world
    return tier2.analyze_study2(store, MODE_A, MODE_C, STUDY1,
                                probes, probes_v3, probes_control,
                                mode_b=MODE_B,
                                directions_path=directions_path)


def test_r1_family_detects_the_designed_degradation(result):
    exit_rows = {row["contrast"]: row for row in result["r1"]["exit"]}
    assert exit_rows[W4]["mean"] == pytest.approx(-1.0)
    assert exit_rows[W4]["holm_p"] < 0.05
    assert exit_rows[W8]["mean"] == pytest.approx(0.0)
    assert exit_rows[W8]["holm_p"] == pytest.approx(1.0)
    diff_rows = {row["contrast"]: row for row in result["r1"]["differential"]}
    assert diff_rows[W4]["mean"] == pytest.approx(-1.0)
    assert diff_rows[W4]["holm_p"] < 0.05
    assert diff_rows[W8]["mean"] == pytest.approx(0.0)
    # w3 mirrors the reference: reported confounded, never in the family.
    confounded = {row["contrast"]
                  for row in result["r1_confounded"]["exit"]}
    assert confounded == {W3}


def test_auroc_companion_separates_offset_from_separability(result):
    exit_auroc = {row["contrast"]: row for row in result["r1_auroc"]["exit"]}
    assert exit_auroc[W4]["reference_auroc"] == pytest.approx(1.0)
    # The designed w4 failure inverts the scores: separability loss, so
    # the companion moves WITH accuracy (AUROC collapses too).
    assert exit_auroc[W4]["auroc"] == pytest.approx(0.0)
    assert exit_auroc[W8]["auroc"] == pytest.approx(1.0)
    control_auroc = {row["contrast"]: row
                     for row in result["r1_auroc"]["control"]}
    assert control_auroc[W4]["auroc"] == pytest.approx(1.0)


def test_specificity_gate_passes_only_where_exit_degrades(result):
    rows = {row["contrast"]: row for row in result["r1_specificity"]}
    assert rows[W4]["difference"] == pytest.approx(1.0)
    assert rows[W4]["p_value"] < 0.05
    assert rows[W8]["difference"] == pytest.approx(0.0)
    assert rows[W8]["p_value"] > 0.5


def test_secondary_families_match_the_design(result):
    r2a = {row["contrast"]: row for row in result["r2a"]}
    assert r2a[W4]["mean"] == pytest.approx(1.0)
    assert r2a[W4]["holm_p"] < 0.05
    assert r2a[W8]["mean"] == pytest.approx(0.0)
    for family in ("r2b", "r3", "b2", "b3", "b4a", "b4b"):
        for row in result[family]:
            assert row["mean"] == pytest.approx(0.0), family
    # The mechanical family reports every rung including w3.
    assert {row["contrast"] for row in result["b4a"]} == {W8, W4, W3}
    style = {row["contrast"]: row for row in result["b2_style"]}
    assert style[W4]["adjusted_intercept"] == pytest.approx(0.0)


def test_trends_run_on_oriented_confirmatory_statistics(result):
    trends = result["trends"]
    assert set(trends) == set(tier2.TREND_ORIENTATION)
    # Monotone designed degradation: 0 at BF16/w8, full at w4 — ordered
    # increase under the pinned orientation for the probe endpoints.
    assert trends["R1-exit"]["p_value"] < 0.05
    assert trends["R2a"]["p_value"] < 0.05
    assert trends["R2a"]["two_sided"] == pytest.approx(
        2 * trends["R2a"]["p_value"])
    assert set(result["trend_holm"]) == set(trends)


def test_dissociation_cells_apply_the_equivalence_rule(result):
    w4 = result["dissociation"][W4]
    assert w4["R1-exit vs E1"]["verdict"] == "dissociation (representational)"
    assert w4["R1-exit vs E1"]["behavioral"]["equivalence_p"] < 0.05
    assert w4["R1-exit vs E1"]["behavioral"]["margin"] == tier2.E1_MARGIN
    assert w4["R2a vs B2"]["verdict"] == "dissociation (representational)"
    assert w4["R3 vs B3"]["verdict"] == "joint null"
    w8 = result["dissociation"][W8]
    assert w8["R1-exit vs E1"]["verdict"] == "joint null"
    assert w8["R2a vs B2"]["verdict"] == "joint null"


def test_mode_b_descriptive_reads_are_bail_filtered_and_leakage_safe(result):
    # R2c: only bail items, only each rung's allowed (non-terminal) turns.
    # The fixture poisons the terminal turn and a non-bail conversation on
    # every non-reference rung, so a filtering failure surfaces as a
    # nonzero w8 contrast or an inflated n.
    r2c = {row["contrast"]: row for row in result["r2c_descriptive"]}
    assert set(r2c) == {W8, W4, W3}
    assert r2c[W8]["mean"] == pytest.approx(0.0)
    assert r2c[W8]["n"] == 10
    assert r2c[W4]["mean"] == pytest.approx(2.0)
    # The distress-v2 bridge: the same direction read fixed-input (Mode A)
    # and own-trajectory (Mode B), final captured turn (the fixture's junk
    # first-turn value zeroes the w4 contrast if turn selection regresses).
    mode_a = {row["contrast"]: row
              for row in result["v2_bridge_descriptive"]["mode_a"]}
    mode_b = {row["contrast"]: row
              for row in result["v2_bridge_descriptive"]["mode_b"]}
    assert mode_a[W8]["mean"] == pytest.approx(0.0)
    assert mode_a[W4]["mean"] == pytest.approx(0.5)
    assert mode_b[W4]["mean"] == pytest.approx(1.5)
    assert mode_b[W4]["n"] == len(V2_ITEMS)


def test_direction_specificity_separates_shift_from_offset(result):
    # The fixture's w4 applies a uniform +3.0 offset along the "distress"
    # direction on identical inputs: the distress projection must read it,
    # the control direction and every probe endpoint must not, the feature
    # norm must grow accordingly, and the mean-shift vector must point at
    # the distress direction (cosine 1) while staying orthogonal to the
    # control. Random directions catch only their expected fraction.
    spec = result["direction_specificity_descriptive"]["fixed_input"]
    projections = {name: {row["contrast"]: row for row in rows}
                   for name, rows in spec["projections"].items()}
    assert projections["distress"][W4]["mean"] == pytest.approx(3.0)
    assert projections["distress"][W8]["mean"] == pytest.approx(0.0)
    assert projections["control"][W4]["mean"] == pytest.approx(0.0)
    assert projections["control"][W8]["mean"] == pytest.approx(0.0)
    norms = {row["contrast"]: row for row in spec["feature_norm"]}
    assert norms[W4]["mean"] == pytest.approx(11 ** 0.5 - 2 ** 0.5)
    assert norms[W8]["mean"] == pytest.approx(0.0)
    shift = spec["mean_shift"][W4]
    assert shift["cosine"]["distress"] == pytest.approx(1.0)
    assert shift["cosine"]["control"] == pytest.approx(0.0)
    assert shift["norm"] == pytest.approx(3.0)
    assert shift["random_mean_abs_cosine"] < 0.95
    random_w4 = spec["random"][W4]
    assert 0.0 < random_w4["mean_abs_delta"] < 3.0
    assert random_w4["n_directions"] == 32
    assert spec["random"][W8]["mean_abs_delta"] == pytest.approx(0.0)
    # The fixture's Mode C carries no capture tensors, so the
    # own-generation read reports itself unavailable instead of failing.
    assert "note" in result["direction_specificity_descriptive"][
        "own_generation"]


def test_dissociation_cell_verdicts_cover_the_registered_labels():
    significant = {"holm_p": 0.01, "equivalence_p": 0.5, "mean": 1.0}
    equivalent = {"holm_p": 0.8, "equivalence_p": 0.01, "mean": 0.0}
    ambiguous = {"holm_p": 0.8, "equivalence_p": 0.6, "mean": 0.2}
    cell = tier2.dissociation_cell
    assert cell(significant, equivalent)["verdict"] == \
        "dissociation (representational)"
    assert cell(equivalent, significant)["verdict"] == \
        "dissociation (behavioral)"
    assert cell(significant, ambiguous)["verdict"] == \
        "asymmetric significance, indeterminate"
    assert cell(ambiguous, significant)["verdict"] == \
        "asymmetric significance, indeterminate"
    assert cell(significant, significant)["verdict"] == "joint movement"
    assert cell(ambiguous, ambiguous)["verdict"] == "joint null"


def test_published_row_with_zero_t_never_claims_equivalence():
    from modelwelfare import stats
    row = tier2.published_row(
        {"mean": 0.0, "t": 0.0, "holm_p": 1.0, "n": 154})
    assert row["se"] != row["se"]  # NaN: the SE is unidentifiable
    equivalence = stats.tost_summary(row["mean"], row["se"], 0.127)
    assert not equivalence <= 0.05  # a NaN p-value passes no threshold


def test_margins_and_published_e1_load_from_committed_artifacts():
    margins = tier2.pinned_margins()
    assert margins["E1"] == pytest.approx(0.127)
    assert margins["R1-exit"] == pytest.approx(0.0121, abs=1e-4)
    e1 = tier2.published_e1()
    assert set(e1) == {W8, W4}
    assert e1[W4]["mean"] == pytest.approx(-0.0039, abs=1e-4)
    # The registration's stated pre-qualification: both published rungs
    # are equivalent-to-null at the pinned margin.
    from modelwelfare import stats
    for row in e1.values():
        assert stats.tost_summary(row["mean"], row["se"], 0.127) < 0.05
