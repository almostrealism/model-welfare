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
