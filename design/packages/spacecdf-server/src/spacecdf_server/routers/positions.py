"""SpaceCDF — Position-Based Guidance API.

Serves engineering position definitions and computes per-position guidance
from the current design state, telling each engineer which questions are
answered, open, or in warning.
"""
from __future__ import annotations

import fnmatch
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from spacecdf_common.config.loader import load_yaml
from spacecdf_common.models.positions import (
    DesignQuestion,
    ParameterOwnership,
    Position,
    PositionGuidance,
    QuestionStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Data loading ───────────────────────────────────────────────────────

_KB_DATA_DIR = (
    Path(__file__).resolve().parents[4]
    / "spacecdf-kb"
    / "src"
    / "spacecdf_kb"
    / "data"
    / "positions"
)

# Fallback: search for it relative to the packages directory
if not _KB_DATA_DIR.exists():
    _alt = Path(__file__).resolve()
    while _alt != _alt.parent:
        candidate = _alt / "packages" / "spacecdf-kb" / "src" / "spacecdf_kb" / "data" / "positions"
        if candidate.exists():
            _KB_DATA_DIR = candidate
            break
        _alt = _alt.parent

_positions_cache: list[Position] | None = None


def _load_positions() -> list[Position]:
    """Load position definitions from YAML (cached after first call)."""
    global _positions_cache
    if _positions_cache is not None:
        return _positions_cache

    yaml_path = _KB_DATA_DIR / "positions.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(f"Positions YAML not found at {yaml_path}")

    data = load_yaml(yaml_path)
    raw_positions = data.get("positions", [])
    if not raw_positions:
        raise ValueError("No positions defined in positions.yaml")

    positions: list[Position] = []
    for item in raw_positions:
        # Parse nested models explicitly to handle YAML structures
        key_questions = [
            DesignQuestion.model_validate(q) for q in item.get("key_questions", [])
        ]
        parameters = [
            ParameterOwnership.model_validate(p) for p in item.get("parameters", [])
        ]
        positions.append(
            Position(
                id=item["id"],
                name=item["name"],
                domain=item["domain"],
                icon=item.get("icon", ""),
                description=item.get("description", ""),
                key_questions=key_questions,
                parameters=parameters,
                depends_on=item.get("depends_on", []),
                feeds_into=item.get("feeds_into", []),
            )
        )

    _positions_cache = positions
    logger.info("Loaded %d position definitions", len(positions))
    return positions


def _get_position(position_id: str) -> Position:
    """Get a single position by ID or raise 404."""
    for pos in _load_positions():
        if pos.id == position_id:
            return pos
    raise HTTPException(status_code=404, detail=f"Position '{position_id}' not found")


# ── Guidance computation ───────────────────────────────────────────────

def _get_current_design_state() -> dict[str, Any]:
    """Retrieve the current design state parameters.

    Returns a flat dict of {param_id: ParameterValue-like dict} from the
    in-memory study store.  Falls back to an empty dict if no active study.
    """
    try:
        from .studies import get_study_store

        studies = get_study_store()
        if not studies:
            return {}

        # Use the most recently created study
        latest = max(studies.values(), key=lambda s: s.created)
        if not hasattr(latest, "design_state") or latest.design_state is None:
            return {}

        state = latest.design_state
        if hasattr(state, "parameters"):
            return state.parameters
        return {}
    except Exception:
        logger.debug("Could not load design state; returning empty", exc_info=True)
        return {}


def _match_params(pattern: str, all_param_ids: set[str]) -> list[str]:
    """Return parameter IDs matching a glob pattern (e.g. 'power.*')."""
    return [pid for pid in all_param_ids if fnmatch.fnmatch(pid, pattern)]


def _evaluate_question(
    question: DesignQuestion,
    params: dict[str, Any],
) -> QuestionStatus:
    """Evaluate one design question against the current parameter state.

    Status logic:
      - "answered" — all related parameters exist, confidence > 0.5, no warnings
      - "warning"  — parameters exist but have low confidence or known warnings
      - "open"     — one or more related parameters are missing or at defaults
    """
    if not question.related_parameters:
        return QuestionStatus(
            question_id=question.id,
            question=question.question,
            priority=question.priority,
            status="not_applicable",
            assessment="No related parameters to check.",
        )

    found = 0
    warnings = 0
    values_summary: list[str] = []

    for pid in question.related_parameters:
        p = params.get(pid)
        if p is None:
            values_summary.append(f"{pid}: missing")
            continue

        found += 1

        # Extract value and confidence from ParameterValue or plain dict
        if hasattr(p, "value"):
            val = p.value
            confidence = getattr(p, "confidence", 0.5)
            source = getattr(p, "source", "unknown")
        elif isinstance(p, dict):
            val = p.get("value")
            confidence = p.get("confidence", 0.5)
            source = p.get("source", "unknown")
        else:
            val = p
            confidence = 0.5
            source = "unknown"

        values_summary.append(f"{pid}={val}")

        # Check for warning conditions
        source_str = source.value if hasattr(source, "value") else str(source)
        if confidence < 0.5 or source_str == "assumed":
            warnings += 1

    current_value = "; ".join(values_summary)

    if found == 0:
        return QuestionStatus(
            question_id=question.id,
            question=question.question,
            priority=question.priority,
            status="open",
            current_value=current_value,
            assessment="Parameters not yet computed.",
        )

    if found < len(question.related_parameters):
        return QuestionStatus(
            question_id=question.id,
            question=question.question,
            priority=question.priority,
            status="open",
            current_value=current_value,
            assessment=f"Only {found}/{len(question.related_parameters)} parameters available.",
        )

    if warnings > 0:
        return QuestionStatus(
            question_id=question.id,
            question=question.question,
            priority=question.priority,
            status="warning",
            current_value=current_value,
            assessment=f"{warnings} parameter(s) have low confidence or are assumed values.",
        )

    return QuestionStatus(
        question_id=question.id,
        question=question.question,
        priority=question.priority,
        status="answered",
        current_value=current_value,
        assessment="All parameters available with adequate confidence.",
    )


def _compute_guidance(position: Position, params: dict[str, Any]) -> PositionGuidance:
    """Build a full PositionGuidance for one position."""
    answered: list[QuestionStatus] = []
    open_qs: list[QuestionStatus] = []
    warnings: list[QuestionStatus] = []

    for q in position.key_questions:
        qs = _evaluate_question(q, params)
        if qs.status == "answered":
            answered.append(qs)
        elif qs.status == "warning":
            warnings.append(qs)
        else:
            open_qs.append(qs)

    # Completion: must_answer questions that are answered / total must_answer
    must_answer_total = sum(
        1 for q in position.key_questions if q.priority == "must_answer"
    )
    must_answer_done = sum(
        1 for qs in answered if qs.priority == "must_answer"
    )
    completion = (
        (must_answer_done / must_answer_total * 100.0)
        if must_answer_total > 0
        else 100.0
    )

    # Collect owned and consumed parameter values
    all_param_ids = set(params.keys())
    owned: dict[str, Any] = {}
    consumed: dict[str, Any] = {}
    for po in position.parameters:
        matched = _match_params(po.param_pattern, all_param_ids)
        for pid in matched:
            p = params[pid]
            val = p.value if hasattr(p, "value") else (p.get("value") if isinstance(p, dict) else p)
            if po.role == "owns":
                owned[pid] = val
            else:
                consumed[pid] = val

    # Generate recommendations for open must_answer questions
    recommendations: list[str] = []
    for qs in open_qs:
        if qs.priority == "must_answer":
            recommendations.append(f"[{qs.question_id}] {qs.question}")
    for qs in warnings:
        if qs.priority == "must_answer":
            recommendations.append(
                f"[{qs.question_id}] Review: {qs.assessment}"
            )

    return PositionGuidance(
        position_id=position.id,
        position_name=position.name,
        answered_questions=answered,
        open_questions=open_qs,
        warning_questions=warnings,
        owned_parameters=owned,
        consumed_parameters=consumed,
        recommendations=recommendations,
        completion_percent=round(completion, 1),
    )


# ── Routes ─────────────────────────────────────────────────────────────

@router.get("/")
async def list_positions() -> list[dict]:
    """List all engineering positions with summary info."""
    positions = _load_positions()
    return [
        {
            "id": p.id,
            "name": p.name,
            "domain": p.domain,
            "icon": p.icon,
            "description": p.description,
            "question_count": len(p.key_questions),
            "depends_on": p.depends_on,
            "feeds_into": p.feeds_into,
        }
        for p in positions
    ]


@router.get("/{position_id}")
async def get_position(position_id: str) -> Position:
    """Get full details of a single engineering position."""
    return _get_position(position_id)


@router.get("/{position_id}/guidance")
async def get_position_guidance(position_id: str) -> PositionGuidance:
    """Compute guidance for a position based on the current design state.

    For each key question, checks related parameters:
    - answered: all params present, confidence > 0.5, not assumed
    - warning: params present but low confidence or assumed
    - open: one or more params missing

    Returns completion_percent based on must_answer questions answered.
    """
    position = _get_position(position_id)
    params = _get_current_design_state()
    return _compute_guidance(position, params)


# In-memory answer store (in production, persist to DB)
_answers: dict[str, dict] = {}


@router.post("/answers")
async def save_answer(body: dict) -> dict:
    """Save a position question answer."""
    qid = body.get("question_id", "")
    _answers[qid] = {
        "question_id": qid,
        "position_id": body.get("position_id", ""),
        "text": body.get("text", ""),
        "confidence": body.get("confidence", "medium"),
        "timestamp": body.get("timestamp", ""),
    }
    return {"saved": True, "total_answers": len(_answers)}


@router.get("/answers")
async def get_answers() -> dict:
    """Get all saved position answers."""
    return {"answers": list(_answers.values()), "count": len(_answers)}
