"""SpaceCDF — Parameter and Budget data models.

The fundamental units of the concurrent design model. Parameters flow
between engineering domains via a dependency DAG; budgets aggregate
parameters with ECSS-compliant margins.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ParameterSource(str, Enum):
    REQUIREMENT = "requirement"
    COMPUTED = "computed"
    SELECTED = "selected"
    ASSUMED = "assumed"
    USER_OVERRIDE = "user_override"
    KB_COMPONENT = "kb_component"       # Selected from knowledge base
    POSITION_OVERRIDE = "position_override"  # Engineer override from position view

    @property
    def is_sticky(self) -> bool:
        """Sticky sources are NOT overwritten by agents during re-convergence."""
        return self in (
            ParameterSource.KB_COMPONENT,
            ParameterSource.POSITION_OVERRIDE,
            ParameterSource.REQUIREMENT,
        )


class ParameterValue(BaseModel):
    """A single design parameter — the atomic unit of the design model."""

    id: str = Field(description="Dot-separated path, e.g. 'sc.eps.solar_array.area_m2'")
    name: str = Field(description="Human-readable name")
    value: float | str | bool = Field(description="Current value")
    unit: str = Field(default="", description="SI unit string")
    domain: str = Field(description="Owning engineering domain (e.g. 'power', 'thermal')")
    source: ParameterSource = ParameterSource.ASSUMED
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Agent confidence in this value")
    margin_percent: float = Field(default=20.0, description="Design margin applied to this parameter")
    min_value: float | None = Field(default=None, description="Physical minimum")
    max_value: float | None = Field(default=None, description="Physical maximum or allocation")
    trl: int | None = Field(default=None, ge=1, le=9, description="Technology Readiness Level")
    heritage: str | None = Field(default=None, description="Heritage mission or component reference")
    equipment_id: str | None = Field(default=None, description="KB component ID if selected from knowledge base")
    equipment_name: str | None = Field(default=None, description="Human-readable component name")
    override_by: str | None = Field(default=None, description="Position ID that overrode this value")
    dependencies: list[str] = Field(default_factory=list, description="Parameter IDs this depends on")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: str = Field(default="system", description="Agent name or user ID")
    rationale: str = Field(default="", description="Why this value was chosen")

    @property
    def value_with_margin(self) -> float | None:
        if isinstance(self.value, (int, float)):
            return self.value * (1.0 + self.margin_percent / 100.0)
        return None


class BudgetLine(BaseModel):
    """A single line in a system budget (mass, power, cost, etc.)."""

    subsystem: str
    equipment: str = ""
    nominal_value: float
    margin_percent: float = 20.0
    unit: str = ""
    trl: int | None = None
    notes: str = ""

    @property
    def with_margin(self) -> float:
        return self.nominal_value * (1.0 + self.margin_percent / 100.0)


class BudgetStatus(str, Enum):
    GREEN = "green"    # >20% margin remaining
    AMBER = "amber"    # 10-20% margin remaining
    RED = "red"        # <10% margin remaining
    EXCEEDED = "exceeded"  # Over allocation


class SystemBudget(BaseModel):
    """Aggregated budget across all subsystems for one resource."""

    budget_type: Literal["mass", "power", "data", "delta_v", "cost"]
    lines: list[BudgetLine] = Field(default_factory=list)
    allocation: float = Field(description="System allocation (e.g. LV capacity for mass)")
    unit: str = ""

    @property
    def total_nominal(self) -> float:
        return sum(line.nominal_value for line in self.lines)

    @property
    def total_with_margin(self) -> float:
        return sum(line.with_margin for line in self.lines)

    @property
    def remaining_margin(self) -> float:
        return self.allocation - self.total_with_margin

    @property
    def margin_percent(self) -> float:
        if self.allocation <= 0:
            return 0.0
        return (self.remaining_margin / self.allocation) * 100.0

    @property
    def status(self) -> BudgetStatus:
        mp = self.margin_percent
        if mp < 0:
            return BudgetStatus.EXCEEDED
        if mp < 10:
            return BudgetStatus.RED
        if mp < 20:
            return BudgetStatus.AMBER
        return BudgetStatus.GREEN


class TRLAssessment(BaseModel):
    """TRL assessment for a subsystem or component, with innovation option."""

    subsystem: str
    baseline_component: str = Field(description="Proven high-TRL component name")
    baseline_trl: int = Field(ge=1, le=9)
    baseline_mass_kg: float = 0.0
    baseline_power_w: float = 0.0
    baseline_cost_keur: float = 0.0
    innovation_component: str | None = Field(default=None, description="Low-TRL innovative alternative")
    innovation_trl: int | None = Field(default=None, ge=1, le=9)
    innovation_mass_kg: float | None = None
    innovation_power_w: float | None = None
    innovation_cost_keur: float | None = None
    innovation_benefit: str = Field(default="", description="What the innovation offers")
    innovation_risk: str = Field(default="", description="Key risk of the innovation")
    recommendation: Literal["baseline", "innovation", "carry_both"] = "baseline"
    rationale: str = ""

    @property
    def innovation_benefit_score(self) -> float:
        """Score = (mass_saving + power_saving + cost_saving) / trl_gap. Higher is better."""
        if not self.innovation_trl or self.innovation_trl >= self.baseline_trl:
            return 0.0
        trl_gap = self.baseline_trl - self.innovation_trl
        mass_saving = max(0, self.baseline_mass_kg - (self.innovation_mass_kg or self.baseline_mass_kg))
        power_saving = max(0, self.baseline_power_w - (self.innovation_power_w or self.baseline_power_w))
        cost_saving = max(0, self.baseline_cost_keur - (self.innovation_cost_keur or self.baseline_cost_keur))
        # Normalise to baseline values
        ms = mass_saving / self.baseline_mass_kg if self.baseline_mass_kg > 0 else 0
        ps = power_saving / self.baseline_power_w if self.baseline_power_w > 0 else 0
        cs = cost_saving / self.baseline_cost_keur if self.baseline_cost_keur > 0 else 0
        return (ms + ps + cs) / trl_gap
