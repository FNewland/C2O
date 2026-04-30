"""SpaceCDF — Component Fit-Gap Analysis Engine.

For each KB component, compares every specification against derived
requirements. Shows fit percentage, identifies gaps, quantifies
downstream consequences. Replaces the crude "fit_score" with real
requirement-by-requirement gap analysis.

This supports Decision B.3 (Component Selection) in the lifecycle framework.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SpecComparison:
    """Comparison of a single component spec against a requirement."""
    parameter: str                # e.g. "capacity_wh", "mass_kg"
    required_value: float
    required_operator: str        # <=, >=, ==
    component_value: float
    unit: str
    status: str                   # "meets", "exceeds", "gap", "marginal"
    margin_percent: float         # Positive = meets with margin, negative = gap
    gap_description: str = ""     # Human-readable gap explanation


@dataclass
class DownstreamConsequence:
    """What happens to the system if we accept a gap or choose this component."""
    parameter_affected: str       # e.g. "mass.dry_mass_kg"
    current_value: float
    new_value: float
    delta: float
    description: str              # e.g. "Mass margin drops from 15% to 8%"


@dataclass
class ComponentFitGap:
    """Complete fit-gap analysis for one component against requirements."""
    component_id: str
    component_name: str
    category: str
    manufacturer: str
    heritage: str

    # Spec-by-spec comparison
    comparisons: list[SpecComparison] = field(default_factory=list)

    # Aggregate scores
    fit_percent: float = 0.0      # What % of requirements are met
    gap_count: int = 0            # How many specs fall short
    critical_gaps: list[str] = field(default_factory=list)  # Gaps that can't be accepted

    # Downstream consequences of selecting this component
    consequences: list[DownstreamConsequence] = field(default_factory=list)

    # Decision support
    recommendation: str = ""      # "select", "consider", "reject"
    rationale: str = ""


def analyze_component_fit(
    component: dict[str, Any],
    requirements: dict[str, Any],
    current_budgets: dict[str, float] | None = None,
) -> ComponentFitGap:
    """Analyze how well a component fits the derived requirements.

    Args:
        component: KB component dict with specs (mass_kg, power_w, performance, etc.)
        requirements: Dict of {spec_name: {value, operator, unit}} derived from the design
        current_budgets: Current system budgets for consequence calculation
    """
    result = ComponentFitGap(
        component_id=component.get("id", ""),
        component_name=component.get("name", ""),
        category=component.get("category", ""),
        manufacturer=component.get("manufacturer", ""),
        heritage=", ".join(component.get("heritage_missions", [])),
    )

    comparisons: list[SpecComparison] = []
    perf = component.get("performance", {})

    for spec_name, req in requirements.items():
        req_value = req.get("value", 0)
        req_op = req.get("operator", ">=")
        req_unit = req.get("unit", "")

        # Get component value — check both top-level and performance sub-dict
        comp_value = component.get(spec_name)
        if comp_value is None:
            comp_value = perf.get(spec_name)
        if comp_value is None:
            continue
        if not isinstance(comp_value, (int, float)):
            continue

        # Compare
        if req_op == "<=":
            margin = ((req_value - comp_value) / max(abs(req_value), 1e-9)) * 100
        elif req_op == ">=":
            margin = ((comp_value - req_value) / max(abs(req_value), 1e-9)) * 100
        else:  # ==
            margin = (1 - abs(comp_value - req_value) / max(abs(req_value), 1e-9)) * 100

        if margin >= 20:
            status = "exceeds"
        elif margin >= 0:
            status = "meets" if margin >= 5 else "marginal"
        else:
            status = "gap"

        gap_desc = ""
        if status == "gap":
            gap_desc = f"{spec_name}: component provides {comp_value} {req_unit} but need {req_op} {req_value} {req_unit} (gap: {abs(margin):.0f}%)"

        comparisons.append(SpecComparison(
            parameter=spec_name,
            required_value=req_value,
            required_operator=req_op,
            component_value=comp_value,
            unit=req_unit,
            status=status,
            margin_percent=round(margin, 1),
            gap_description=gap_desc,
        ))

    result.comparisons = comparisons

    # Aggregate
    if comparisons:
        meets = sum(1 for c in comparisons if c.status in ("meets", "exceeds", "marginal"))
        result.fit_percent = (meets / len(comparisons)) * 100
        result.gap_count = sum(1 for c in comparisons if c.status == "gap")
        result.critical_gaps = [c.gap_description for c in comparisons if c.status == "gap"]

    # Downstream consequences
    if current_budgets:
        comp_mass = component.get("mass_kg", 0)
        if comp_mass and "mass_allocation_kg" in current_budgets:
            alloc = current_budgets["mass_allocation_kg"]
            current_margin = current_budgets.get("mass_margin_percent", 20)
            new_margin = current_margin - (comp_mass / max(alloc, 1)) * 100
            result.consequences.append(DownstreamConsequence(
                parameter_affected="mass_margin_percent",
                current_value=current_margin,
                new_value=round(new_margin, 1),
                delta=round(new_margin - current_margin, 1),
                description=f"Mass margin: {current_margin:.0f}% → {new_margin:.0f}%",
            ))

    # Recommendation
    if result.fit_percent >= 90 and result.gap_count == 0:
        result.recommendation = "select"
        result.rationale = "Meets all requirements with margin"
    elif result.fit_percent >= 70 and result.gap_count <= 1:
        result.recommendation = "consider"
        result.rationale = f"Meets most requirements; {result.gap_count} gap(s) may be acceptable"
    else:
        result.recommendation = "reject"
        result.rationale = f"Does not meet {result.gap_count} requirement(s)"

    return result


def analyze_category(
    components: list[dict],
    requirements: dict[str, Any],
    current_budgets: dict[str, float] | None = None,
) -> list[ComponentFitGap]:
    """Analyze all components in a category and rank by fit."""
    results = []
    for comp in components:
        fg = analyze_component_fit(comp, requirements, current_budgets)
        results.append(fg)

    # Sort: select first, then consider, then reject; within each, by fit%
    order = {"select": 0, "consider": 1, "reject": 2}
    results.sort(key=lambda r: (order.get(r.recommendation, 3), -r.fit_percent))
    return results
