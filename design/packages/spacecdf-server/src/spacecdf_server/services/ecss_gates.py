"""SpaceCDF — ECSS review-gate deliverable service.

Loads configs/ecss_review_gates.yaml and exposes the per-phase DRD expectations
to the API. This is what surfaces ECSS compliance context to the frontend.

Reference: ECSS-E-ST-10C Rev.1 Annex A (Table A-1) + ECSS-M-ST-10C Rev.1.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def _gates_file() -> Path:
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        candidate = parent / "configs" / "ecss_review_gates.yaml"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("configs/ecss_review_gates.yaml not found")


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    try:
        path = _gates_file()
    except FileNotFoundError:
        logger.warning("ECSS gates file not found; returning empty config")
        return {"phases": {}}
    try:
        return yaml.safe_load(path.read_text()) or {"phases": {}}
    except (yaml.YAMLError, OSError) as exc:
        logger.warning("ECSS gates file failed to load: %s", exc)
        return {"phases": {}}


def list_phases() -> list[str]:
    """Return all phase ids declared in the review-gate config."""
    return list(_load().get("phases", {}).keys())


def get_phase_gate(phase_id: str) -> dict[str, Any] | None:
    """Return gate metadata for a phase (MDR/PRR/SRR/...) or None."""
    return _load().get("phases", {}).get(phase_id)


def compliance_summary(phase_id: str) -> dict[str, Any]:
    """Aggregate coverage stats for a phase.

    Returns a small summary the UI can use at a glance:
      { total, produced, partial, planned, external, coverage_percent }
    """
    gate = get_phase_gate(phase_id)
    if not gate:
        return {"phase": phase_id, "found": False}

    drds = gate.get("expected_drds", [])
    counts = {"spacecdf": 0, "partial": 0, "planned": 0, "external": 0}
    for d in drds:
        key = d.get("produced_by", "external")
        counts[key] = counts.get(key, 0) + 1

    total = len(drds)
    # Coverage: spacecdf counts full, partial counts half.
    coverage = 0.0
    if total:
        coverage = 100 * (counts["spacecdf"] + 0.5 * counts["partial"]) / total

    return {
        "phase": phase_id,
        "found": True,
        "gate": gate.get("gate"),
        "gate_name": gate.get("gate_name"),
        "description": gate.get("description", "").strip(),
        "total": total,
        "produced": counts["spacecdf"],
        "partial": counts["partial"],
        "planned": counts["planned"],
        "external": counts["external"],
        "coverage_percent": round(coverage, 1),
        "drds": drds,
    }
