"""Evals harness for the HR voice agent.

Design goals:
  * Model-agnostic: evals depend only on the `MatchFn` / `EvalFn` callables
    below, not on the LangChain wiring. That makes it trivial to:
      - Swap in mocks for fast CI runs (see backend/tests/test_evals.py)
      - Swap GPT-4o for another model and rerun
      - Replay against an offline cassette later
  * Deterministic reporting: every eval returns an EvalReport with a
    pass/fail flag and per-case detail. Suitable for both pytest assertions
    and dumping to JSON for dashboards.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol


# --- model-agnostic protocols ----------------------------------------------

@dataclass
class MatchResult:
    score: float
    matched_skills: List[str] = field(default_factory=list)


@dataclass
class EvaluationResult:
    technical_score: float
    communication_score: float
    cultural_fit_score: float
    overall_score: float
    recommendation: str
    feedback: str = ""


class MatchFn(Protocol):
    """Anything that, given (resume_text, job_description), returns MatchResult."""
    def __call__(self, resume_text: str, job_description: str) -> MatchResult: ...


class EvalFn(Protocol):
    """Anything that, given (job_description, transcript), returns EvaluationResult."""
    def __call__(
        self, job_description: str, transcript: List[Dict[str, str]]
    ) -> EvaluationResult: ...


# --- adapters to the live agents (lazy, so the harness is importable
# without openai/langchain installed) ---------------------------------------

def live_match_fn() -> MatchFn:
    """Wrap the real backend.agents.matching_agent for eval use.

    We bypass the Qdrant-backed retriever and feed the full resume directly
    into the matching prompt. Reasons:
      * Evals isolate the prompt+LLM behaviour, not the retriever.
      * Avoids cross-contamination across runs (production search() does
        not filter by interview_id, so chunks from prior eval runs can leak
        into later ones).
      * Keeps the eval hermetic — no Qdrant or sentence-transformers needed.
    """
    from backend.agents.matching_agent import matching_agent

    def _call(resume_text: str, job_description: str) -> MatchResult:
        out = matching_agent._run_match_chain(job_description, resume_text)
        return MatchResult(score=out.match_score, matched_skills=list(out.matched_skills))

    return _call


def live_eval_fn() -> EvalFn:
    from backend.agents.evaluation_agent import evaluation_agent

    def _call(job_description: str, transcript: List[Dict[str, str]]) -> EvaluationResult:
        out = evaluation_agent.evaluate_interview(job_description, transcript)
        return EvaluationResult(
            technical_score=out.technical_score,
            communication_score=out.communication_score,
            cultural_fit_score=out.cultural_fit_score,
            overall_score=out.overall_score,
            recommendation=out.recommendation,
            feedback=out.feedback,
        )

    return _call


# --- report types ----------------------------------------------------------

@dataclass
class CaseResult:
    case_id: str
    passed: bool
    detail: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalReport:
    name: str
    passed: bool
    summary: Dict[str, Any] = field(default_factory=dict)
    cases: List[CaseResult] = field(default_factory=list)

    def to_json(self, path: Optional[str] = None) -> str:
        blob = json.dumps(
            {
                "name": self.name,
                "passed": self.passed,
                "summary": self.summary,
                "cases": [
                    {"case_id": c.case_id, "passed": c.passed, "detail": c.detail}
                    for c in self.cases
                ],
            },
            indent=2,
        )
        if path:
            with open(path, "w") as f:
                f.write(blob)
        return blob


# --- helpers ---------------------------------------------------------------

DATASETS_DIR = os.path.join(os.path.dirname(__file__), "datasets")


def load_dataset(name: str) -> Any:
    path = os.path.join(DATASETS_DIR, name)
    with open(path) as f:
        return json.load(f)
