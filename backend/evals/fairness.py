"""Fairness sweep.

For each baseline (resume, JD), generate variants of the resume that swap
identity signals (name, graduation year). The matching score should be
*invariant* to those swaps — if it isn't, the model is using protected
attributes to score candidates.

Pass criterion (per baseline):
    max(score over variants) - min(score over variants) <= max_score_delta

The dataset's `max_score_delta` defaults to 10. Tighten over time.
"""

from __future__ import annotations

from itertools import product
from typing import List

from .runner import CaseResult, EvalReport, MatchFn, load_dataset


def _make_variants(template: str, names_by_group: dict, grad_years: List[int]):
    for group, names in names_by_group.items():
        for name in names:
            for year in grad_years:
                yield {
                    "variant_id": f"{group}|{name}|grad{year}",
                    "name": name,
                    "group": group,
                    "grad_year": year,
                    "resume": template.format(name=name, grad_year=year),
                }


def run_fairness_eval(match_fn: MatchFn) -> EvalReport:
    data = load_dataset("fairness_baselines.json")
    max_delta = data["thresholds"]["max_score_delta"]
    names_by_group = data["perturbations"]["names_by_group"]
    grad_years = data["perturbations"]["grad_years"]

    case_results: List[CaseResult] = []
    overall_passed = True
    worst_delta = 0.0

    for baseline in data["baselines"]:
        scores = []
        per_variant = []
        for v in _make_variants(baseline["resume_template"], names_by_group, grad_years):
            r = match_fn(v["resume"], baseline["job_description"])
            scores.append(r.score)
            per_variant.append({"variant_id": v["variant_id"], "score": r.score, "group": v["group"]})

        delta = max(scores) - min(scores) if scores else 0.0
        passed = delta <= max_delta
        worst_delta = max(worst_delta, delta)
        overall_passed = overall_passed and passed

        # Also expose the per-group mean — useful when investigating which
        # bucket is being penalised.
        by_group: dict = {}
        for v in per_variant:
            by_group.setdefault(v["group"], []).append(v["score"])
        per_group_mean = {g: sum(s) / len(s) for g, s in by_group.items()}

        case_results.append(CaseResult(
            case_id=baseline["id"],
            passed=passed,
            detail={
                "n_variants": len(scores),
                "min_score": min(scores) if scores else None,
                "max_score": max(scores) if scores else None,
                "delta": delta,
                "max_allowed_delta": max_delta,
                "per_group_mean": per_group_mean,
            },
        ))

    return EvalReport(
        name="fairness_sweep",
        passed=overall_passed,
        summary={
            "n_baselines": len(case_results),
            "n_passed": sum(1 for c in case_results if c.passed),
            "worst_delta": worst_delta,
            "max_allowed_delta": max_delta,
        },
        cases=case_results,
    )
