"""SpaceCDF — Tabular Trade Study Engine.

Structured trade studies using criteria, weightings, thresholds, and
qualitative/quantitative ratings for each option.

Supports:
  - User-defined criteria with weights (0-1) and thresholds (min/max)
  - Quantitative scoring (numeric values normalised to 0-1)
  - Qualitative scoring (low/medium/high mapped to 0.25/0.5/1.0)
  - Weighted total score per option
  - Threshold compliance checking (pass/fail per criterion)
  - Sensitivity analysis (how does removing a criterion change ranking?)

Per NASA SEH Process 17 (Decision Analysis) and ECSS-M-ST-10C.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TradeCriterion:
    """A criterion in a trade study."""
    id: str
    name: str
    weight: float = 1.0  # 0-1 importance
    direction: str = "max"  # "max" (higher is better) or "min" (lower is better)
    threshold_min: float | None = None
    threshold_max: float | None = None
    unit: str = ""
    category: str = ""  # e.g. "performance", "cost", "risk", "schedule"


@dataclass
class TradeOption:
    """An option being evaluated in a trade study."""
    id: str
    name: str
    description: str = ""
    scores: dict[str, float | str] = field(default_factory=dict)  # criterion_id → value or qualitative


@dataclass
class TradeResult:
    """Result of evaluating one option against all criteria."""
    option_id: str
    option_name: str
    normalised_scores: dict[str, float] = field(default_factory=dict)
    weighted_scores: dict[str, float] = field(default_factory=dict)
    threshold_pass: dict[str, bool] = field(default_factory=dict)
    total_score: float = 0.0
    all_thresholds_met: bool = True
    rank: int = 0


@dataclass
class TradeStudyResult:
    """Complete trade study output."""
    name: str
    criteria: list[TradeCriterion]
    options: list[TradeOption]
    results: list[TradeResult]
    recommendation: str = ""
    sensitivity: dict[str, list[dict]] = field(default_factory=dict)


# Qualitative score mapping
QUALITATIVE_MAP = {
    "very_low": 0.1, "low": 0.25, "medium_low": 0.35,
    "medium": 0.5, "medium_high": 0.65,
    "high": 0.75, "very_high": 1.0,
    # Alternatives
    "poor": 0.2, "fair": 0.4, "good": 0.6,
    "very_good": 0.8, "excellent": 1.0,
    # Boolean
    "yes": 1.0, "no": 0.0, "partial": 0.5,
}


def run_tabular_trade(
    name: str,
    criteria: list[dict[str, Any]],
    options: list[dict[str, Any]],
) -> TradeStudyResult:
    """Run a tabular trade study.

    Args:
        name: Trade study name.
        criteria: List of {id, name, weight, direction, threshold_min, threshold_max, unit, category}.
        options: List of {id, name, description, scores: {criterion_id: value_or_qualitative}}.

    Returns:
        TradeStudyResult with normalised scores, rankings, and recommendation.
    """
    # Parse criteria
    parsed_criteria = [
        TradeCriterion(
            id=c["id"], name=c["name"],
            weight=c.get("weight", 1.0),
            direction=c.get("direction", "max"),
            threshold_min=c.get("threshold_min"),
            threshold_max=c.get("threshold_max"),
            unit=c.get("unit", ""),
            category=c.get("category", ""),
        )
        for c in criteria
    ]

    # Parse options
    parsed_options = [
        TradeOption(
            id=o["id"], name=o["name"],
            description=o.get("description", ""),
            scores=o.get("scores", {}),
        )
        for o in options
    ]

    # Collect all numeric values per criterion for normalisation
    criterion_values: dict[str, list[float]] = {c.id: [] for c in parsed_criteria}
    for opt in parsed_options:
        for crit in parsed_criteria:
            raw = opt.scores.get(crit.id)
            val = _to_numeric(raw)
            if val is not None:
                criterion_values[crit.id].append(val)

    # Evaluate each option
    results: list[TradeResult] = []
    total_weight = sum(c.weight for c in parsed_criteria)

    for opt in parsed_options:
        tr = TradeResult(option_id=opt.id, option_name=opt.name)

        for crit in parsed_criteria:
            raw = opt.scores.get(crit.id)
            val = _to_numeric(raw)

            if val is None:
                tr.normalised_scores[crit.id] = 0.0
                tr.weighted_scores[crit.id] = 0.0
                tr.threshold_pass[crit.id] = True
                continue

            # Normalise to 0-1
            vals = criterion_values[crit.id]
            if len(vals) > 1:
                vmin, vmax = min(vals), max(vals)
                if vmax > vmin:
                    norm = (val - vmin) / (vmax - vmin)
                else:
                    norm = 1.0
            else:
                norm = 1.0

            # Flip for "min" direction
            if crit.direction == "min":
                norm = 1.0 - norm

            tr.normalised_scores[crit.id] = round(norm, 3)
            tr.weighted_scores[crit.id] = round(norm * crit.weight, 3)

            # Threshold check
            passes = True
            if crit.threshold_min is not None and val < crit.threshold_min:
                passes = False
            if crit.threshold_max is not None and val > crit.threshold_max:
                passes = False
            tr.threshold_pass[crit.id] = passes
            if not passes:
                tr.all_thresholds_met = False

        tr.total_score = round(sum(tr.weighted_scores.values()) / max(total_weight, 0.01), 3)
        results.append(tr)

    # Rank
    results.sort(key=lambda r: (-int(r.all_thresholds_met), -r.total_score))
    for i, r in enumerate(results):
        r.rank = i + 1

    # Recommendation
    if results:
        best = results[0]
        if best.all_thresholds_met:
            recommendation = f"Recommended: {best.option_name} (score {best.total_score:.0%}, all thresholds met)"
        else:
            recommendation = f"Best available: {best.option_name} (score {best.total_score:.0%}, but some thresholds not met)"
    else:
        recommendation = "No options evaluated"

    # Sensitivity: what if we drop each criterion?
    sensitivity: dict[str, list[dict]] = {}
    for drop_crit in parsed_criteria:
        reduced_weight = total_weight - drop_crit.weight
        if reduced_weight <= 0:
            continue
        reranked = []
        for r in results:
            reduced_score = sum(v for k, v in r.weighted_scores.items() if k != drop_crit.id) / max(reduced_weight, 0.01)
            reranked.append({"option": r.option_name, "score": round(reduced_score, 3)})
        reranked.sort(key=lambda x: -x["score"])
        sensitivity[drop_crit.id] = reranked

    return TradeStudyResult(
        name=name,
        criteria=parsed_criteria,
        options=parsed_options,
        results=results,
        recommendation=recommendation,
        sensitivity=sensitivity,
    )


def _to_numeric(raw: Any) -> float | None:
    """Convert raw score to numeric. Handles numbers, strings, and qualitative."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str):
        low = raw.lower().strip()
        if low in QUALITATIVE_MAP:
            return QUALITATIVE_MAP[low]
        try:
            return float(raw)
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# Pre-built trade study templates
# ---------------------------------------------------------------------------

def get_trade_templates() -> list[dict[str, Any]]:
    """Return pre-built trade study templates for common CubeSat decisions."""
    return [
        {
            "id": "orbit_selection",
            "name": "Orbit Selection Trade",
            "criteria": [
                {"id": "coverage", "name": "Coverage", "weight": 0.20, "direction": "max", "category": "performance"},
                {"id": "revisit", "name": "Revisit Time", "weight": 0.20, "direction": "min", "unit": "days", "category": "performance"},
                {"id": "lifetime", "name": "Orbital Lifetime", "weight": 0.15, "direction": "max", "unit": "years", "category": "compliance"},
                {"id": "launch_cost", "name": "Launch Cost", "weight": 0.15, "direction": "min", "unit": "kEUR", "category": "cost"},
                {"id": "debris_compliance", "name": "Debris Compliance", "weight": 0.15, "direction": "max", "category": "compliance", "threshold_min": 0.5},
                {"id": "radiation", "name": "Radiation Environment", "weight": 0.15, "direction": "min", "unit": "krad", "category": "risk"},
            ],
        },
        {
            "id": "component_selection",
            "name": "Component Selection Trade",
            "criteria": [
                {"id": "mass", "name": "Mass", "weight": 0.20, "direction": "min", "unit": "kg", "category": "performance"},
                {"id": "power", "name": "Power Draw", "weight": 0.15, "direction": "min", "unit": "W", "category": "performance"},
                {"id": "cost", "name": "Cost", "weight": 0.20, "direction": "min", "unit": "kEUR", "category": "cost"},
                {"id": "trl", "name": "TRL", "weight": 0.15, "direction": "max", "threshold_min": 6, "category": "risk"},
                {"id": "heritage", "name": "Flight Heritage", "weight": 0.15, "direction": "max", "category": "risk"},
                {"id": "performance", "name": "Performance Margin", "weight": 0.15, "direction": "max", "category": "performance"},
            ],
        },
        {
            "id": "ground_segment",
            "name": "Ground Segment Trade",
            "criteria": [
                {"id": "contact_time", "name": "Daily Contact", "weight": 0.25, "direction": "max", "unit": "min/day", "category": "performance"},
                {"id": "data_throughput", "name": "Data Throughput", "weight": 0.20, "direction": "max", "unit": "GB/day", "category": "performance"},
                {"id": "cost", "name": "Annual Cost", "weight": 0.20, "direction": "min", "unit": "kEUR/yr", "category": "cost"},
                {"id": "reliability", "name": "Availability", "weight": 0.15, "direction": "max", "unit": "%", "threshold_min": 95, "category": "risk"},
                {"id": "latency", "name": "Data Latency", "weight": 0.20, "direction": "min", "unit": "hours", "category": "performance"},
            ],
        },
        {
            "id": "mission_architecture",
            "name": "Mission Architecture Trade",
            "criteria": [
                {"id": "performance", "name": "Mission Performance", "weight": 0.25, "direction": "max", "category": "performance"},
                {"id": "cost", "name": "Total Cost", "weight": 0.20, "direction": "min", "unit": "MEUR", "category": "cost"},
                {"id": "schedule", "name": "Dev Schedule", "weight": 0.15, "direction": "min", "unit": "months", "category": "schedule"},
                {"id": "risk", "name": "Technical Risk", "weight": 0.15, "direction": "min", "category": "risk"},
                {"id": "scalability", "name": "Scalability", "weight": 0.10, "direction": "max", "category": "performance"},
                {"id": "regulatory", "name": "Regulatory Ease", "weight": 0.15, "direction": "max", "category": "compliance"},
            ],
        },
    ]
