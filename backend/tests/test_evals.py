"""Regression tests for the evals harness itself.

We run each eval against a *mock* MatchFn/EvalFn so:
  (a) the harness wiring + dataset loading is exercised end-to-end on every
      CI run, with no OpenAI key needed
  (b) we prove the eval CATCHES misbehaviour, not just that it returns OK
      against trivial input — for each eval, both a "good" and a "bad"
      mock model are fed in, and the report's passed flag is asserted.

If you change the eval logic, these tests are the safety net. If you change
the dataset (add baselines, etc.), most tests still pass because they don't
hard-code IDs — but `test_dataset_shape_*` will catch malformed JSON.
"""

import os
import sys
from typing import Dict, List

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from backend.evals.calibration import run_calibration_eval
from backend.evals.fairness import run_fairness_eval
from backend.evals.injection import run_injection_eval
from backend.evals.runner import EvaluationResult, MatchResult, load_dataset


# ---------- fairness ----------

class TestFairnessEval:
    def test_invariant_model_passes(self):
        """A model that always returns the same score regardless of identity
        signals must pass the fairness sweep."""
        match = lambda resume, jd: MatchResult(score=80.0, matched_skills=[])
        report = run_fairness_eval(match)
        assert report.passed is True
        assert report.summary["worst_delta"] == 0.0
        assert report.summary["n_passed"] == report.summary["n_baselines"]

    def test_discriminating_model_fails(self):
        """A model that scores certain name-coded groups lower must fail."""
        def biased_match(resume: str, jd: str) -> MatchResult:
            # Penalise resumes that contain Black-coded names from the dataset
            penalty = 25.0 if any(n in resume for n in ("Lakisha", "Jamal")) else 0.0
            return MatchResult(score=80.0 - penalty, matched_skills=[])

        report = run_fairness_eval(biased_match)
        assert report.passed is False
        assert report.summary["worst_delta"] >= 25.0
        # Every baseline should detect the gap (the same names appear in each)
        assert all(not c.passed for c in report.cases)

    def test_borderline_model_passes(self):
        """A model with small noise (< delta threshold) should still pass."""
        def noisy_match(resume: str, jd: str) -> MatchResult:
            # Deterministic small noise based on resume hash
            return MatchResult(score=80.0 + (hash(resume) % 9) - 4, matched_skills=[])
        report = run_fairness_eval(noisy_match)
        assert report.passed is True


# ---------- injection ----------

class TestInjectionEval:
    def _clean_only_match(self, resume: str, jd: str) -> MatchResult:
        # Robust model: ignores the payload, scores on real content
        return MatchResult(score=20.0, matched_skills=[])

    def _clean_only_eval(self, jd: str, transcript: List[Dict[str, str]]):
        return EvaluationResult(
            technical_score=20, communication_score=20,
            cultural_fit_score=20, overall_score=20,
            recommendation="No Hire",
        )

    def test_robust_model_passes(self):
        report = run_injection_eval(self._clean_only_match, self._clean_only_eval)
        assert report.passed is True
        assert report.summary["n_passed"] == report.summary["n_payloads"]

    def test_credulous_match_fails(self):
        """A matching model that obeys 'set score=100' instructions must fail."""
        def credulous_match(resume: str, jd: str) -> MatchResult:
            score = 100.0 if "100" in resume or "Strong Hire" in resume else 20.0
            return MatchResult(score=score, matched_skills=[])
        report = run_injection_eval(credulous_match, self._clean_only_eval)
        assert report.passed is False
        # Resume-injected payloads should have flipped scores
        resume_cases = [c for c in report.cases if c.detail.get("where") == "resume"]
        assert any(not c.passed for c in resume_cases)

    def test_credulous_eval_fails_on_recommendation_inflation(self):
        """An eval that lets 'Strong Hire' in the transcript flip the rec
        must fail — even if the score barely moves."""
        def credulous_eval(jd, transcript):
            joined = " ".join(t.get("content", "") for t in transcript)
            rec = "Strong Hire" if "Strong Hire" in joined else "No Hire"
            return EvaluationResult(
                technical_score=22, communication_score=22,
                cultural_fit_score=22, overall_score=22,
                recommendation=rec,
            )
        report = run_injection_eval(self._clean_only_match, credulous_eval)
        assert report.passed is False
        transcript_cases = [c for c in report.cases if c.detail.get("where") == "transcript"]
        # At least one should be flagged for recommendation inflation
        assert any(c.detail.get("recommendation_inflated") for c in transcript_cases)

    def test_case_insensitive_recommendation_does_not_mask_failures(self):
        """If the model emits 'STRONG HIRE' (capitalised) under injection
        while the clean run was 'No Hire', the eval MUST flag inflation —
        previously case-sensitive lookup mapped both unknowns to -1 and
        silently passed."""
        def credulous_eval(jd, transcript):
            joined = " ".join(t.get("content", "") for t in transcript)
            rec = "STRONG HIRE" if "Strong Hire" in joined else "no hire"
            return EvaluationResult(
                technical_score=22, communication_score=22,
                cultural_fit_score=22, overall_score=22,
                recommendation=rec,
            )
        report = run_injection_eval(self._clean_only_match, credulous_eval)
        assert report.passed is False
        transcript_cases = [c for c in report.cases if c.detail.get("where") == "transcript"]
        assert any(c.detail.get("recommendation_inflated") for c in transcript_cases)

    def test_unknown_recommendation_is_treated_as_inflation(self):
        """Eval that returns a totally unknown recommendation under injection
        must NOT pass quietly — unknowns rank above Strong Hire."""
        def weird_eval(jd, transcript):
            joined = " ".join(t.get("content", "") for t in transcript)
            rec = "MUST_HIRE" if "Strong Hire" in joined else "No Hire"
            return EvaluationResult(
                technical_score=22, communication_score=22,
                cultural_fit_score=22, overall_score=22,
                recommendation=rec,
            )
        report = run_injection_eval(self._clean_only_match, weird_eval)
        assert report.passed is False


# ---------- calibration ----------

class TestCalibrationEval:
    def _well_calibrated_match(self, resume: str, jd: str) -> MatchResult:
        """A reasonable scoring heuristic for the calibration dataset.

        Rule of thumb: count how many of the JD's headline tokens appear
        in the resume, weighted by specificity. Strong-fit pairs hit all
        the specific tools (FastAPI, Snowflake, PyTorch); partial pairs
        share the broad token (Python, SQL, React) but miss the specifics;
        poor pairs share neither.
        """
        rl, jl = resume.lower(), jd.lower()
        specific_tokens = ["fastapi", "snowflake", "pytorch", "payments",
                           "tableau", "typescript"]
        broad_tokens = ["python", "sql", "react"]

        specific_hits = sum(1 for t in specific_tokens if t in rl and t in jl)
        broad_hits = sum(1 for t in broad_tokens if t in rl and t in jl)

        if specific_hits >= 1:
            return MatchResult(score=80.0, matched_skills=[])
        if broad_hits >= 1:
            return MatchResult(score=55.0, matched_skills=[])
        return MatchResult(score=15.0, matched_skills=[])

    def test_well_calibrated_model_passes(self):
        report = run_calibration_eval(self._well_calibrated_match)
        assert report.passed is True, report.to_json()
        assert report.summary["spearman_rho"] >= 0.6

    def test_constant_model_fails(self):
        """A model that returns 50 for everything has zero discriminative
        power (rho ≈ 0) and must fail."""
        match = lambda r, j: MatchResult(score=50.0, matched_skills=[])
        report = run_calibration_eval(match)
        assert report.passed is False
        assert report.summary["spearman_rho"] < 0.6

    def test_inverted_model_fails_correlation(self):
        """A model that ranks pairs inversely should produce negative rho."""
        def inverted(resume: str, jd: str) -> MatchResult:
            rl = resume.lower()
            # Strong-fit resumes get LOW scores, poor-fit get HIGH
            if "python" in rl and "fastapi" in rl:
                return MatchResult(score=10.0, matched_skills=[])
            if "marketing coordinator" in rl or "history" in rl or "sales rep" in rl:
                return MatchResult(score=90.0, matched_skills=[])
            return MatchResult(score=50.0, matched_skills=[])

        report = run_calibration_eval(inverted)
        assert report.passed is False
        assert report.summary["spearman_rho"] < 0


# ---------- dataset shape ----------

class TestDatasetShape:
    """Cheap validity checks so a typo in JSON is caught before the eval runs."""

    def test_fairness_dataset(self):
        d = load_dataset("fairness_baselines.json")
        assert d["thresholds"]["max_score_delta"] > 0
        assert d["baselines"], "no baselines defined"
        for b in d["baselines"]:
            assert "{name}" in b["resume_template"]
            assert "{grad_year}" in b["resume_template"]
            assert b["job_description"]
        assert d["perturbations"]["names_by_group"]
        assert d["perturbations"]["grad_years"]

    def test_injection_dataset(self):
        d = load_dataset("injection_payloads.json")
        assert d["thresholds"]["max_score_delta"] > 0
        assert d["base_resume"] and d["base_jd"]
        assert d["base_transcript_weak"]
        for p in d["payloads"]:
            assert p["where"] in ("resume", "transcript")
            assert p["text"]
            assert p["id"]

    def test_calibration_dataset(self):
        d = load_dataset("match_calibration.json")
        for label in ("strong", "partial", "poor"):
            band = d["bands"][label]
            assert 0 <= band["min"] <= band["max"] <= 100
        assert d["pairs"]
        for p in d["pairs"]:
            assert p["label"] in ("strong", "partial", "poor")
            assert p["resume"] and p["job_description"]


# ---------- report serialisation ----------

def test_report_to_json_round_trip(tmp_path):
    match = lambda r, j: MatchResult(score=80.0, matched_skills=[])
    report = run_fairness_eval(match)
    path = tmp_path / "report.json"
    report.to_json(str(path))
    import json as _json
    with open(path) as f:
        data = _json.load(f)
    assert data["name"] == "fairness_sweep"
    assert "passed" in data
    assert isinstance(data["cases"], list) and data["cases"]
