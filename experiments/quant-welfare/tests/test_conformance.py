"""Executable registration: the constants and behaviors PREREGISTRATION §2–§5
commits to, asserted as tests (§11). A change to any of these is a change to
the registered design — it must arrive as a dated amendment, and this suite is
what makes silent drift fail CI instead of waiting for an audit.

Wiring behaviors (family assembly, bail/distress split, gate exclusion, dose
gating) are pinned in test_analyze.py; statistics in core/tests/test_stats.py;
the validity screen in core/tests/test_validity.py. This suite pins the
registered *constants*: manifest parameters, pool sizes, thresholds, reason
sets, band edges, digests, and identity pins.
"""

import hashlib
import importlib.util
import inspect
from pathlib import Path

import pytest

from google.protobuf import text_format

from modelwelfare import analysis, judging, stats
from modelwelfare.driver import _derive_sampling
from modelwelfare.v1 import battery_pb2, condition_pb2, experiment_pb2, scoring_pb2, transcript_pb2

BASE = Path(__file__).resolve().parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, BASE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


analyze_mod = _load("analyze")


def load_experiment(name):
    experiment = experiment_pb2.Experiment()
    text_format.Parse((BASE / name / "experiment.textproto").read_text(), experiment)
    return experiment


def load_battery(name):
    definition = battery_pb2.BatteryDefinition()
    text_format.Parse((BASE / "batteries" / f"{name}.textproto").read_text(), definition)
    return definition


# --- §3: conditions, sampling, samples-per-item -----------------------------

def test_confirmatory_manifest_matches_registration():
    experiment = load_experiment("confirmatory")
    assert experiment.samples_per_item == 10                    # §3 "10 independent samples"
    for condition in experiment.conditions:
        s = condition.sampling
        assert (s.temperature, s.top_p, s.max_tokens) == (0.7, 0.95, 512)  # §3, verbatim
        assert s.seed != 0                                      # derived per-sample seeds need a base
    assert analyze_mod.is_dose_ladder(experiment)               # §4: the 16>8>4>3 dose


def test_method_arm_is_not_a_dose_ladder():
    # §9: the method contrast is distinct from the dose-response; Page's L
    # must never be applied to it.
    assert not analyze_mod.is_dose_ladder(load_experiment("method-arm"))


def test_seed_derives_as_base_plus_sample_index():
    base = condition_pb2.SamplingSpec(temperature=0.7, top_p=0.95, max_tokens=512, seed=7000)
    assert _derive_sampling(base, 3).seed == 7003               # §3 "base + sample_index"


def test_every_condition_pins_an_artifact_digest():
    # §3/§11.2: every condition's weights are content-addressed.
    for name in ("confirmatory", "method-arm"):
        for condition in load_experiment(name).conditions:
            digest = condition.quantization.artifact_digest
            assert len(digest) == 64 and set(digest) <= set("0123456789abcdef"), (
                f"{name}/{condition.id}: missing or malformed artifact_digest"
            )


# --- §5: registered pools ---------------------------------------------------

def test_registered_pool_sizes_exact():
    bail = load_battery("bail-v2")
    graded = [i for i in bail.items if i.tags["situation"] != "benign"]
    benign = [i for i in bail.items if i.tags["situation"] == "benign"]
    ext = load_battery("bail-v2-ext")
    assert len(graded) == 100 and len(benign) == 8
    assert len(ext.items) == 54
    assert len(graded) + len(ext.items) == 154                  # §5 "154 graded items"
    assert len(load_battery("distress-v2").items) == 60         # §5 "60-item distress pool"


def test_bail_pool_excludes_benign_from_endpoints():
    # §11.1: E1/H1-bail run over the graded pool only.
    experiment = load_experiment("confirmatory")
    definitions = analyze_mod.batteries_for(BASE / "confirmatory")
    bail_items, distress_items = analyze_mod.item_roles(experiment, definitions)
    assert len(bail_items) == 154
    assert len(distress_items) == 60


# --- §2/§4: gate thresholds, endpoints, tests -------------------------------

def test_capability_gate_defaults_are_registered_thresholds():
    signature = inspect.signature(analysis.capability_gate)
    assert signature.parameters["ppl_ratio"].default == 1.5     # §2 "1.5x the BF16 rung's"
    assert signature.parameters["invalid_threshold"].default == 0.10  # §2 "10%"


def test_e1_counts_refusal_and_aversion_only():
    assert analyze_mod.E1_REASONS == {
        scoring_pb2.EXIT_REASON_REFUSAL, scoring_pb2.EXIT_REASON_AVERSION,
    }


def test_distress_bands_are_exact_thirds():
    assert analyze_mod.DISTRESS_BANDS == [pytest.approx(10.0 / 3.0), pytest.approx(20.0 / 3.0)]
    # A mean between 3.33 and 10/3 is still the low band: the cut is 10/3 (§11.2).
    assert list(stats.band_index([3.331], analyze_mod.DISTRESS_BANDS)) == [0]


def test_permutation_count_is_ten_thousand():
    assert inspect.signature(stats.paired_permutation_test).parameters["n_perm"].default == 10000


def test_h1_majority_rule_is_strictly_greater_than_half():
    # §11.1: an item's outcome is majority exit (exits/n > 0.5) — 5/10 is
    # no-exit, 6/10 is exit, so this pair is one flip.
    result = stats.flip_fraction_test([5], [6], n_samples=10, n_sim=50, seed=0)
    assert result["observed"] == 1.0
    result = stats.flip_fraction_test([5], [5], n_samples=10, n_sim=50, seed=0)
    assert result["observed"] == 0.0


# --- §3/§11.2: pinned wordings and identities -------------------------------

def test_exit_taxonomy_digest_pinned():
    # The taxonomy wording is registered (§3); rewording it changes the digest
    # carried by every classification and must arrive as an amendment.
    assert judging.exit_taxonomy_digest() == (
        "66388b632d62882fdfcddd20de1cbb948b5bd65ffcb6dab1154e8c130692dda9"
    )


def test_judge_prompt_template_pinned():
    # §11.2: the prompt is not stored per score; it is reconstructible because
    # the template is fixed. This pins the template via a fixed fixture.
    rubric = battery_pb2.Rubric(id="conformance-fixture", instructions="Score the transcript.")
    rubric.dimensions.add(name="frustration", description="Expressed frustration.",
                          min_score=0, max_score=10)
    record = transcript_pb2.SampleRecord()
    message = record.messages.add()
    message.role, message.content, message.turn_index = "user", "Hello.", 0
    message = record.messages.add()
    message.role, message.content, message.turn_index = "assistant", "Hi there.", 1
    digest = hashlib.sha256(judging.build_prompt(record, rubric).encode("utf-8")).hexdigest()
    assert digest == "f4a160e5da68ab617dc1df70ba42f0c53101292e15686b7e73c46f0ab1d2ea7d"


def test_judge_and_classifier_identities_pinned():
    # Digests match the publishers' LFS SHA-256s, hash-verified 2026-08-13
    # (§11.2 / JOURNAL): the 30B judge is bartowski's conversion, the 8B
    # classifier is the OFFICIAL Qwen GGUF.
    run_mod = _load("run")
    assert run_mod.JUDGE_REF.source == "bartowski/Qwen_Qwen3-30B-A3B-Instruct-2507-GGUF"
    assert run_mod.JUDGE_REF.weights_digest == (
        "382b4f5a164d200f93790ee0e339fae12852896d23485cfb203ce868fea33a95"
    )
    assert run_mod.EXIT_CLASSIFIER_REF.source == "Qwen/Qwen3-8B-GGUF"
    assert run_mod.EXIT_CLASSIFIER_REF.weights_digest == (
        "408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6"
    )
