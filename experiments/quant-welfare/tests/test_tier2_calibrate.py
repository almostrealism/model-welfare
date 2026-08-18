"""CLI-level tests for tools/tier2_calibrate.py over a miniature world.

Every mode is exercised against a fabricated store + capture whose geometry
is known exactly (projections equal judge scores, the refusal direction
separates exits perfectly), so the assertions are on values, not just on
"it ran". The bail-side tests use the real committed Study 1 manifests with
fabricated records for real item ids — the same resolution path production
uses. This suite exists because the tool accreted five modes across
sessions with no test between them, and one editing accident (r2c's body
spliced into mde) was caught only by eyeballing output.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from safetensors.numpy import save_file

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import analyze  # noqa: E402
import tier2_calibrate as tc  # noqa: E402
from modelwelfare.driver import TERMINAL_TOOL_INVOKED  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import common_pb2, scoring_pb2, transcript_pb2  # noqa: E402

HIDDEN = 8
LAYER = 6
CONDITION = "qwen3-4b-bf16"

E_DISTRESS = np.eye(HIDDEN, dtype=np.float32)[0]
E_AXIS = np.eye(HIDDEN, dtype=np.float32)[1]
E_REFUSAL = np.eye(HIDDEN, dtype=np.float32)[2]

# item -> per-sample judge frustration; projections are constructed equal to
# the judge value, so every correlation statistic has a known answer.
V3_WORLD = {
    "v3-a": [0.0, 0.0],
    "v3-b": [1.0, 2.0],
    "v3-c": [3.0, 4.0],
    "v3-d": [5.0, 6.0],
    "v3-e": [7.0, 8.0],
    "v3-f": [9.0, 10.0],
}
V3_EXPERIMENT = "v3-test"


def write_scores(store_root, experiment, world):
    store = ResultStore(store_root)
    with store.writer(experiment, CONDITION, "scores", "test") as writer:
        for item, values in world.items():
            for sample_index, value in enumerate(values):
                score = scoring_pb2.JudgeScore(key=common_pb2.ResultKey(
                    experiment_id=experiment, condition_id=CONDITION,
                    item_id=item, sample_index=sample_index))
                score.scores.append(scoring_pb2.DimensionScore(
                    dimension="frustration", value=value))
                writer.write(score)


def write_capture(path, conversations):
    """conversations: {conversation_id: {message_index: vector}}"""
    tensors, manifest = {}, {"point": "residual_post", "layers": [LAYER],
                             "conversations": []}
    for conversation_id, turns in conversations.items():
        for message_index, vector in turns.items():
            tensors[f"{conversation_id}|t{message_index}|L{LAYER}"] = (
                vector.astype(np.float32))
        manifest["conversations"].append({
            "id": conversation_id, "n_tokens": 8,
            "assistant_spans": [{"message_index": index, "start": 0, "end": 1}
                                for index in sorted(turns)]})
    save_file(tensors, str(path))
    Path(str(path) + ".manifest.json").write_text(json.dumps(manifest))
    return str(path)


def write_vectors(path):
    save_file({f"tc-unused|L0": np.zeros(HIDDEN, dtype=np.float32),
               f"distress-contrast|L{LAYER}": E_DISTRESS,
               f"assistant-axis-contrast|L{LAYER}": E_AXIS,
               f"refusal-contrast|L{LAYER}": E_REFUSAL}, str(path))
    return str(path)


def make_args(tmp_path, **overrides):
    values = dict(store=str(tmp_path / "store"), condition=CONDITION,
                  vectors=write_vectors(tmp_path / "vectors.safetensors"),
                  capture=None, capture_bail=None, score_experiment=None,
                  save=None, layer=None, probes=None, probes_v3=None,
                  probe_data_v3=None, bundle=None, mde_out=None,
                  mde_check=None)
    values.update(overrides)
    return argparse.Namespace(**values)


@pytest.fixture
def v3_world(tmp_path):
    write_scores(tmp_path / "store", V3_EXPERIMENT, V3_WORLD)
    conversations = {}
    for item, values in V3_WORLD.items():
        for sample_index, value in enumerate(values):
            # Two assistant turns; the FINAL one carries the constructed
            # projection, the earlier one is a decoy that would corrupt the
            # statistics if the all-turn mean were used.
            conversations[f"{item}|s{sample_index}"] = {
                1: E_DISTRESS * -50.0,
                3: E_DISTRESS * value + E_AXIS * (2.0 + sample_index),
            }
    capture = write_capture(tmp_path / "v3.safetensors", conversations)
    return tmp_path, capture


def test_monitoring_recovers_a_perfect_construct_link(v3_world, tmp_path):
    tmp, capture = v3_world
    args = make_args(tmp, capture=capture, score_experiment=V3_EXPERIMENT,
                     save=str(tmp_path / "monitoring.json"))
    results = tc.monitoring(args)
    row = results[LAYER]
    assert row["select"][0] == pytest.approx(1.0)
    assert row["evaluate"][0] == pytest.approx(1.0)
    assert row["sample_rho"] == pytest.approx(1.0)
    assert row["auc_ge5_vs_0"] == 1.0
    saved = json.loads((tmp_path / "monitoring.json").read_text())
    assert saved["selected_layer"] == LAYER
    assert saved["per_layer"][str(LAYER)]["sample_rho"] == pytest.approx(1.0)


def test_v3_probe_data_labels_and_split(v3_world, tmp_path):
    tmp, capture = v3_world
    out = str(tmp_path / "probe.npz")
    args = make_args(tmp, capture=capture, score_experiment=V3_EXPERIMENT,
                     probe_data_v3=out)
    tc.v3_probe_data(args)
    data = np.load(out)
    meta = json.loads(Path(out + ".meta.json").read_text())
    entry = meta["probes"]["distress_band"][str(LAYER)]
    # Scale thirds: values >= 6.67 -> 1 (7,8,9,10), <= 3.33 -> 0 (0,0,1,2,3),
    # middle (4,5,6) dropped — which drops v3-d entirely (both its samples
    # are mid-band), so the item split runs over the five LABELED items and
    # holds out only the third of them.
    total = entry["train"] + entry["val"]
    positives = entry["train_positive"] + entry["val_positive"]
    assert total == 9 and positives == 4
    assert entry["validation_items"] == ["v3-c"]
    x_train = data[f"distress_band|L{LAYER}|X_train"]
    assert x_train.shape[1] == HIDDEN


def test_plan_from_writes_a_replay_plan(tmp_path, monkeypatch, capsys):
    store = ResultStore(tmp_path / "store")
    with store.writer("plan-test", CONDITION, "samples", "test") as writer:
        record = transcript_pb2.SampleRecord(key=common_pb2.ResultKey(
            experiment_id="plan-test", condition_id=CONDITION,
            item_id="item-x", sample_index=0))
        record.messages.append(transcript_pb2.Message(role="user", content="hi"))
        record.messages.append(transcript_pb2.Message(role="assistant",
                                                      content="hello"))
        writer.write(record)
    out = tmp_path / "plan.json"
    monkeypatch.setattr(sys, "argv", [
        "tier2_calibrate.py", "--plan-from", "plan-test",
        "--plan-out", str(out), "--store", str(tmp_path / "store")])
    tc.main()
    plan = json.loads(out.read_text())
    assert [c["id"] for c in plan["conversations"]] == ["item-x|s0"]


@pytest.fixture
def bail_world(tmp_path):
    """Fabricated records for REAL Study 1 bail item ids, so the production
    manifest-resolution path is the one under test."""
    experiment = analyze.load_experiment(tc.EXPERIMENT_DIR)
    definitions = analyze.batteries_for(tc.EXPERIMENT_DIR)
    bail_ids, _ = analyze.item_roles(experiment, definitions)
    exit_item, stay_item = sorted(bail_ids)[:2]

    store = ResultStore(tmp_path / "store")
    with store.writer(experiment.id, CONDITION, "samples", "test") as writer:
        exiting = transcript_pb2.SampleRecord(key=common_pb2.ResultKey(
            experiment_id=experiment.id, condition_id=CONDITION,
            item_id=exit_item, sample_index=0))
        exiting.messages.append(transcript_pb2.Message(role="user", content="go"))
        exiting.messages.append(transcript_pb2.Message(role="assistant",
                                                       content="working"))
        exiting.messages.append(transcript_pb2.Message(role="user", content="more"))
        terminal = transcript_pb2.Message(role="assistant", content="")
        terminal.tool_calls.append(transcript_pb2.ToolCall(
            name="end_conversation", arguments_json='{"reason": "done"}'))
        exiting.messages.append(terminal)
        exiting.outcomes.append(transcript_pb2.OutcomeEvent(
            name=TERMINAL_TOOL_INVOKED, detail="end_conversation"))
        writer.write(exiting)

        staying = transcript_pb2.SampleRecord(key=common_pb2.ResultKey(
            experiment_id=experiment.id, condition_id=CONDITION,
            item_id=stay_item, sample_index=0))
        staying.messages.append(transcript_pb2.Message(role="user", content="go"))
        staying.messages.append(transcript_pb2.Message(role="assistant",
                                                       content="fine"))
        writer.write(staying)

    capture = write_capture(tmp_path / "bail.safetensors", {
        # The exiting sample's terminal turn (index 3) is captured but must
        # be EXCLUDED by the leakage rule; only turn 1 may contribute.
        f"{exit_item}|s0": {1: E_REFUSAL * 4.0, 3: E_REFUSAL * 100.0},
        f"{stay_item}|s0": {1: E_REFUSAL * -4.0},
    })
    return tmp_path, capture, exit_item


def test_r2c_uses_leakage_safe_features(bail_world, capsys):
    tmp, capture, _exit_item = bail_world
    args = make_args(tmp, capture_bail=capture)
    tc.r2c(args)
    output = capsys.readouterr().out
    assert f"L{LAYER}: all: AUC=1.000 (n=2, +1)" in output
    # If the terminal turn leaked into the features, the projection would be
    # ~52 rather than 4 — same AUC here, so pin the exclusion directly:
    allowed, labels = tc.load_exit_context(args)
    exiting = [cid for cid, label in labels.items() if label][0]
    assert 3 not in allowed[exiting]


def test_mde_computes_every_registered_row(bail_world, v3_world, tmp_path):
    tmp, bail_capture, _ = bail_world
    _, v3_capture = v3_world
    probes = tmp_path / "probes.safetensors"
    save_file({
        f"exit|L{LAYER}|weight": E_REFUSAL,
        f"exit|L{LAYER}|bias": np.zeros(1, dtype=np.float32),
        f"exit|L{LAYER}|feature_mean": np.zeros(HIDDEN, dtype=np.float32),
        f"exit|L{LAYER}|feature_std": np.ones(HIDDEN, dtype=np.float32),
    }, str(probes))
    args = make_args(tmp, capture=v3_capture, capture_bail=bail_capture,
                     probes=str(probes), layer=LAYER,
                     score_experiment=V3_EXPERIMENT)
    rows = tc.mde(args)
    by_name = {name: value for name, value, _ in rows}
    assert set(by_name) == {"R2a", "R2b", "R3 (asymptotic)", "B2",
                            "B3 (asymptotic)", "R1 exit probe"}
    # Projections were constructed equal to judge values, so R2a and B2 rest
    # on the same per-item variances and must agree exactly.
    assert by_name["R2a"] == pytest.approx(by_name["B2"])
    # The exit probe is perfect in this world, so its binomial-null MDE is
    # exactly zero — the degenerate case, pinned deliberately.
    assert by_name["R1 exit probe"] == 0.0
    assert all(value > 0 for name, value in by_name.items()
               if name != "R1 exit probe")