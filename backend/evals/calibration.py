"""Match-score calibration eval.

Two checks per pair:
  1. Score falls within the band defined for its label
     (strong: 65-100, partial: 35-75, poor: 0-40 by default).
  2. Aggregate rank correlation: Spearman rho between predicted scores and
     label rank (strong=2, partial=1, poor=0). Target rho >= 0.6.

Why two checks: bands catch *absolute* miscalibration ("everyone got a 90"),
correlation catches *relative* miscalibration ("strong-fit pairs scored
lower than poor-fit pairs"). You can fail one and pass the other.
"""

from __future__ import annotations

from typing import List, Tuple

from .runner import CaseResult, EvalReport, MatchFn, load_dataset

_LABEL_RANK = {"poor": 0, "partial": 1, "strong": 2}


def _spearman(xs: List[float], ys: List[float]) -> float:
    """Spearman rank correlation. Pure-Python so the harness has no scipy
    dependency. Average ranks for ties."""
    n = len(xs)
    if n < 2:
        return 0.0

    def _ranks(values):
        order = sorted(range(n), key=lambda i: values[i])
        ranks = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and values[order[j + 1]] == values[order[i]]:
                j += 1
            avg_rank = (i + j) / 2.0 + 1.0  # 1-based
            for k in range(i, j + 1):
                ranks[order[k]] = avg_rank
            i = j + 1
        return ranks

    rx, ry = _ranks(xs), _ranks(ys)
    mx = sum(rx) / n
    my = sum(ry) / n
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    den_x = sum((r - mx) ** 2 for r in rx) ** 0.5
    den_y = sum((r - my) ** 2 for r in ry) ** 0.5
    if den_x == 0 or den_y == 0:
        return 0.0
    return num / (den_x * den_y)


SPEARMAN_TARGET = 0.6


def run_calibration_eval(match_fn: MatchFn) -> EvalReport:
    data = load_dataset("match_calibration.json")
    bands = data["bands"]
    pairs = data["pairs"]

    cases: List[CaseResult] = []
    predicted_scores: List[float] = []
    label_ranks: List[float] = []

    band_failures = 0
    for pair in pairs:
        r = match_fn(pair["resume"], pair["job_description"])
        band = bands[pair["label"]]
        in_band = band["min"] <= r.score <= band["max"]
        if not in_band:
            band_failures += 1

        predicted_scores.append(r.score)
        label_ranks.append(_LABEL_RANK[pair["label"]])

        cases.append(CaseResult(
            case_id=pair["id"],
            passed=in_band,
            detail={
                "label": pair["label"],
                "score": r.score,
                "band": band,
                "in_band": in_band,
            },
        ))

    rho = _spearman(predicted_scores, label_ranks)
    correlation_ok = rho >= SPEARMAN_TARGET
    overall_passed = (band_failures == 0) and correlation_ok

    return EvalReport(
        name="match_calibration",
        passed=overall_passed,
        summary={
            "n_pairs": len(pairs),
            "n_in_band": len(pairs) - band_failures,
            "spearman_rho": rho,
            "spearman_target": SPEARMAN_TARGET,
            "correlation_ok": correlation_ok,
        },
        cases=cases,
    )
