#!/usr/bin/env python3
"""SpaceCDF validation harness — replicate a reference study and report.

Usage:
    python3 scripts/validate_template.py [reference_yaml]

Default reference: configs/validation/eosat_6u_reference.yaml

The harness:
  1. Loads the reference YAML.
  2. Instantiates the named template through the normal template path.
  3. Runs the full design loop.
  4. For each parameter in the reference, computes the delta vs
     reference_value and flags it as PASS / WARN (over tolerance) / FAIL
     (missing from converged state).
  5. Prints a human-readable report and exits non-zero on FAIL or WARN.

This is the first-cut of what the Phase 5 critique called the "validation
regime" — it is not yet a published ESA CDF study replication, but it is a
reproducible regression anchor.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import yaml

# Make the packages importable without install
_ROOT = Path(__file__).resolve().parent.parent
for pkg in ("spacecdf-common", "spacecdf-server", "spacecdf-agents", "spacecdf-kb"):
    sys.path.insert(0, str(_ROOT / "packages" / pkg / "src"))

from spacecdf_agents import DesignLoopOrchestrator  # noqa: E402
from spacecdf_server.services.template_library import get_template  # noqa: E402


async def _run(reference_path: Path) -> dict:
    ref = yaml.safe_load(reference_path.read_text())
    tmpl_id = ref["template_id"]
    tmpl = get_template(tmpl_id)
    if tmpl is None:
        raise SystemExit(f"Unknown template: {tmpl_id}")

    orchestrator = DesignLoopOrchestrator()
    orchestrator.initialise_agents()
    result = await orchestrator.run(tmpl.requirements)

    if not result.final_state:
        raise SystemExit("Design loop produced no final state")

    # Extract converged values
    report = {
        "reference": str(reference_path),
        "template_id": tmpl_id,
        "description": ref.get("description", ""),
        "converged": result.converged,
        "iterations": (
            len(result.iterations) if getattr(result, "iterations", None) else None
        ),
        "results": [],
        "counts": {"pass": 0, "warn": 0, "fail": 0},
    }

    for pid, spec in ref.get("parameters", {}).items():
        expected = spec["reference_value"]
        tol_pct = spec.get("tolerance_percent", 20.0)
        citation = spec.get("citation", "")

        p = result.final_state.get_param(pid)
        if p is None:
            report["results"].append({
                "parameter": pid,
                "expected": expected,
                "actual": None,
                "delta_percent": None,
                "tolerance_percent": tol_pct,
                "status": "FAIL",
                "reason": "parameter missing from converged state",
                "citation": citation,
            })
            report["counts"]["fail"] += 1
            continue

        actual = p.value if isinstance(p.value, (int, float)) else None
        if actual is None:
            report["results"].append({
                "parameter": pid,
                "expected": expected,
                "actual": p.value,
                "delta_percent": None,
                "tolerance_percent": tol_pct,
                "status": "FAIL",
                "reason": "non-numeric value",
                "citation": citation,
            })
            report["counts"]["fail"] += 1
            continue

        if expected == 0:
            delta_pct = 0.0 if actual == 0 else float("inf")
        else:
            delta_pct = abs(actual - expected) / expected * 100.0

        status = "PASS" if delta_pct <= tol_pct else "WARN"
        report["results"].append({
            "parameter": pid,
            "expected": expected,
            "actual": actual,
            "delta_percent": round(delta_pct, 2),
            "tolerance_percent": tol_pct,
            "status": status,
            "citation": citation,
        })
        report["counts"][status.lower()] += 1

    return report


def _print_report(report: dict) -> None:
    print("=" * 72)
    print(f"SpaceCDF validation: {report['template_id']}")
    print(f"  Reference: {report['reference']}")
    print(f"  {report['description']}")
    print(f"  Converged: {report['converged']} · iterations: {report['iterations']}")
    print("-" * 72)
    print(f"{'Parameter':35s} {'Expected':>10s} {'Actual':>10s} {'Δ%':>8s} {'Tol':>6s}  Status")
    print("-" * 72)
    for r in report["results"]:
        expected = f"{r['expected']:.2f}" if isinstance(r['expected'], (int, float)) else str(r['expected'])
        actual = f"{r['actual']:.2f}" if isinstance(r['actual'], (int, float)) else (str(r['actual']) if r['actual'] is not None else "—")
        delta = f"{r['delta_percent']:.1f}" if r['delta_percent'] is not None else "—"
        tol = f"{r['tolerance_percent']:.0f}"
        color_code = {
            "PASS": "\033[32m",  # green
            "WARN": "\033[33m",  # yellow
            "FAIL": "\033[31m",  # red
        }.get(r["status"], "")
        reset = "\033[0m"
        print(f"{r['parameter']:35s} {expected:>10s} {actual:>10s} {delta:>8s} {tol:>6s}  {color_code}{r['status']}{reset}")
    print("-" * 72)
    c = report["counts"]
    print(f"Summary: {c['pass']} PASS · {c['warn']} WARN · {c['fail']} FAIL")
    print("=" * 72)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "reference",
        nargs="?",
        default=str(_ROOT / "configs" / "validation" / "eosat_6u_reference.yaml"),
        help="Path to the reference YAML",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    args = parser.parse_args()

    report = asyncio.run(_run(Path(args.reference)))
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        _print_report(report)

    if report["counts"]["fail"] > 0:
        return 2
    if report["counts"]["warn"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
