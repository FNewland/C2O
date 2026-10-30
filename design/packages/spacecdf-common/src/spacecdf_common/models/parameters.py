"""Typed parameters + equations (SCDF-160 §1.5; ECSS-E-TM-10-25 Annex A shapes,
Virtual Satellite ``Ref:``/``Calc:``).

Pydantic mirrors of ``ParameterDefinitionRow`` and ``ElementParameterRow``.
The six well-known element columns (mass_kg, power_avg_w, power_peak_w,
volume_cm3, cost_nre_keur, cost_recurring_keur) stay the fast path on
``DesignElementRow``; the element repo mirrors them into ElementParameter
rows so every quantity is reachable through one API.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ValueSwitch(str, Enum):
    """Which of the three stored values is the effective one (10-25 ParameterSwitchKind)."""
    MANUAL = "manual"
    COMPUTED = "computed"
    REFERENCE = "reference"


class FormulaKind(str, Enum):
    """Virtual Satellite style: ``ref`` evaluates and persists computed_value;
    ``calc`` evaluates on read only."""
    REF = "ref"
    CALC = "calc"


#: Names of the element columns that are mirrored to ElementParameter rows.
WELL_KNOWN_PARAMETERS: tuple[str, ...] = (
    "mass_kg",
    "power_avg_w",
    "power_peak_w",
    "volume_cm3",
    "cost_nre_keur",
    "cost_recurring_keur",
)


class ParameterDefinition(BaseModel):
    """Global parameter definition: name + quantity kind + unit."""
    id: str = ""
    name: str = Field(description="Snake-case name, e.g. 'mass_kg', 'data_rate_bps'")
    quantity_kind: str = ""
    unit: str = ""
    scale: str | None = None
    description: str = ""
    is_well_known: bool = False
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class ElementParameter(BaseModel):
    """A typed value of one parameter on one element (10-25 ParameterValueSet)."""
    id: str = ""
    study_id: str
    element_id: str
    definition_id: str
    owner_domain: str | None = None
    manual_value: float | None = None
    computed_value: float | None = None
    reference_value: float | None = None
    value_switch: ValueSwitch = ValueSwitch.COMPUTED
    formula: str | None = None
    formula_kind: FormulaKind | None = None
    option_id: str | None = None
    iteration: int = 1
    version: int = 1
    deleted_at: datetime | None = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    @property
    def effective_value(self) -> float | None:
        """The value selected by ``value_switch``."""
        if self.value_switch == ValueSwitch.MANUAL:
            return self.manual_value
        if self.value_switch == ValueSwitch.REFERENCE:
            return self.reference_value
        return self.computed_value
