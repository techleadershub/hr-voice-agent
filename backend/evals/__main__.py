"""CLI: python -m backend.evals [fairness|injection|calibration|all] [--out report.json]

Requires OPENAI_API_KEY in env (and the production deps installed). For
deterministic CI runs without an LLM, see backend/tests/test_evals.py
which exercises the same harness with mocks.
"""

import argparse
import json
import sys

from .calibration import run_calibration_eval
from .fairness import run_fairness_eval
from .injection import run_injection_eval
from .runner import live_eval_fn, live_match_fn


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("which", choices=["fairness", "injection", "calibration", "all"])
    p.add_argument("--out", help="Write JSON report(s) to this path (or dir if 'all').")
    args = p.parse_args(argv)

    match = live_match_fn()
    eval_ = live_eval_fn()

    reports = []
    if args.which in ("fairness", "all"):
        reports.append(run_fairness_eval(match))
    if args.which in ("injection", "all"):
        reports.append(run_injection_eval(match, eval_))
    if args.which in ("calibration", "all"):
        reports.append(run_calibration_eval(match))

    overall_pass = all(r.passed for r in reports)
    print(json.dumps(
        [{"name": r.name, "passed": r.passed, "summary": r.summary} for r in reports],
        indent=2,
    ))

    if args.out:
        if args.which == "all":
            import os
            os.makedirs(args.out, exist_ok=True)
            for r in reports:
                r.to_json(os.path.join(args.out, f"{r.name}.json"))
        else:
            reports[0].to_json(args.out)

    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
