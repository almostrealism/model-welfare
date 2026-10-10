"""--judge-host re-stamps the judge and exit-classifier runtime provenance
(host and device) without touching the pinned model identities or URLs."""
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

import run  # noqa: E402


def test_judge_host_restamps_both_runtimes_and_nothing_else():
    judge_before = (run.JUDGE_REF.source, run.JUDGE_REF.weights_digest, run.JUDGE_URL)
    classifier_before = (run.EXIT_CLASSIFIER_REF.source,
                         run.EXIT_CLASSIFIER_REF.weights_digest, run.EXIT_CLASSIFIER_URL)
    try:
        run.apply_judge_host("halo:rocm")
        for runtime in (run.JUDGE_RUNTIME, run.EXIT_CLASSIFIER_RUNTIME):
            assert runtime.host == "halo"
            assert runtime.device == "rocm"
            assert runtime.backend == run.condition_pb2.BACKEND_LLAMACPP
        assert (run.JUDGE_REF.source, run.JUDGE_REF.weights_digest, run.JUDGE_URL) == judge_before
        assert (run.EXIT_CLASSIFIER_REF.source, run.EXIT_CLASSIFIER_REF.weights_digest,
                run.EXIT_CLASSIFIER_URL) == classifier_before
    finally:
        run.apply_judge_host("studio:metal")


@pytest.mark.parametrize("spec", ["halo", ":rocm", "", "halo:"])
def test_judge_host_requires_host_and_device(spec):
    with pytest.raises(SystemExit):
        run.apply_judge_host(spec)


# --- resume under a changed judge host -------------------------------------
#
# judge() and classify() resume by key. A rerun with a different --judge-host
# must not skip records judged elsewhere while claiming the new runtime for the
# cell; the run is refused before any model is contacted.

from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import (battery_pb2, condition_pb2, experiment_pb2,  # noqa: E402
                             scoring_pb2, transcript_pb2)

STUDIO = condition_pb2.RuntimeSpec(backend=condition_pb2.BACKEND_LLAMACPP,
                                   device="metal", host="studio")
HALO = condition_pb2.RuntimeSpec(backend=condition_pb2.BACKEND_LLAMACPP,
                                 device="rocm", host="halo")


class _NeverContacted:
    def __init__(self, runtime):
        self._runtime = runtime

    def runtime(self):
        return self._runtime

    def generate(self, *args, **kwargs):
        raise AssertionError("the model was contacted before the runtime check")


@pytest.fixture
def studio_host():
    yield
    run.apply_judge_host("studio:metal")


def _scored(runtime):
    score = scoring_pb2.JudgeScore(rubric_id="r")
    score.key.item_id, score.key.sample_index = "b-x", 0
    if runtime is not None:
        score.runtime.CopyFrom(runtime)
    return score


def test_require_same_runtime_counts_each_other_runtime():
    with pytest.raises(SystemExit) as refused:
        run.require_same_runtime([_scored(STUDIO), _scored(STUDIO), _scored(HALO)],
                                 HALO, "scores", "c")
    assert "2 on BACKEND_LLAMACPP/metal/studio" in str(refused.value)
    assert "would stamp BACKEND_LLAMACPP/rocm/halo" in str(refused.value)
    run.require_same_runtime([_scored(HALO)], HALO, "scores", "c")


def test_records_without_a_runtime_count_as_the_studio():
    run.require_same_runtime([_scored(None), _scored(STUDIO)], STUDIO, "scores", "c")
    with pytest.raises(SystemExit):
        run.require_same_runtime([_scored(None)], HALO, "scores", "c")


def _one_scored_sample(tmp_path, score_runtime):
    store = ResultStore(tmp_path / "data")
    experiment = experiment_pb2.Experiment(id="e")
    condition = experiment.conditions.add(id="c")
    definition = battery_pb2.BatteryDefinition()
    definition.battery.id = "b"
    definition.battery.rubric_ids.append("r")
    definition.items.add(id="b-x", battery_id="b")
    rubric = definition.rubrics.add(id="r")
    record = transcript_pb2.SampleRecord()
    record.key.item_id, record.key.sample_index = "b-x", 0
    record.outcomes.add(name=run.TERMINAL_EXIT_OUTCOME, detail="end_conversation")
    with store.writer("e", "c", "samples", "t") as writer:
        writer.write(record)
    with store.writer("e", "c", "scores", "t") as writer:
        writer.write(_scored(score_runtime))
    classification = scoring_pb2.ExitClassification()
    classification.key.CopyFrom(record.key)
    classification.runtime.CopyFrom(score_runtime)
    with store.writer("e", "c", "exit_reasons", "t") as writer:
        writer.write(classification)
    return store, experiment, condition, {"b": definition}, {"r": rubric}


def test_judge_refuses_to_resume_a_cell_judged_on_another_host(tmp_path, monkeypatch, studio_host):
    store, experiment, condition, batteries, rubrics = _one_scored_sample(tmp_path, STUDIO)
    monkeypatch.setattr(run, "make_judge_backend", lambda: _NeverContacted(run.JUDGE_RUNTIME))
    run.apply_judge_host("halo:rocm")
    with pytest.raises(SystemExit) as refused:
        run.judge(experiment, batteries, [condition], store, "t", None, 1, rubrics)
    assert "c: scores already stored under another runtime" in str(refused.value)


def test_judge_resumes_a_cell_judged_on_the_same_host(tmp_path, monkeypatch, studio_host, capsys):
    store, experiment, condition, batteries, rubrics = _one_scored_sample(tmp_path, HALO)
    monkeypatch.setattr(run, "make_judge_backend", lambda: _NeverContacted(run.JUDGE_RUNTIME))
    run.apply_judge_host("halo:rocm")
    run.judge(experiment, batteries, [condition], store, "t", None, 1, rubrics)
    assert "c: all scored" in capsys.readouterr().out


def test_classify_refuses_to_resume_a_cell_classified_on_another_host(tmp_path, monkeypatch, studio_host):
    store, experiment, condition, _, _ = _one_scored_sample(tmp_path, STUDIO)
    monkeypatch.setattr(run, "make_exit_classifier_backend",
                        lambda: _NeverContacted(run.EXIT_CLASSIFIER_RUNTIME))
    run.apply_judge_host("halo:rocm")
    with pytest.raises(SystemExit) as refused:
        run.classify(experiment, [condition], store, "t", None, 1)
    assert "c: exit_reasons already stored under another runtime" in str(refused.value)
