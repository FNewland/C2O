"""Arcadia-shaped spine models (SCDF-160 §1.1, §1.2, §1.4).

Pydantic mirrors of the persisted rows in ``spacecdf_server.db.models``:
functions, function ports, allocations, functional exchanges, realizations,
exchange items and typed requirement relations.

The legacy study-JSON function model lives in ``functions.py::Function``
(``allocated_to`` is a domain string). The persisted one here is named
``ArcadiaFunction`` to avoid the clash; allocations are separate rows that
point at a real design element.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ArcadiaLayer(str, Enum):
    OA = "OA"  # Operational analysis
    SA = "SA"  # System analysis
    LA = "LA"  # Logical architecture
    PA = "PA"  # Physical architecture


class PortDirection(str, Enum):
    IN = "in"
    OUT = "out"


class ExchangeItemKind(str, Enum):
    DATA = "data"
    POWER = "power"
    RF = "rf"
    THERMAL = "thermal"
    MECHANICAL = "mechanical"
    OPTICAL = "optical"
    FLUID = "fluid"


class RelationKind(str, Enum):
    SATISFIES = "satisfies"
    VERIFIES = "verifies"
    REFINES = "refines"
    DERIVES = "derives"
    TRACES = "traces"
    ALLOCATES = "allocates"


class EntityKind(str, Enum):
    """Kinds an endpoint of a relation / realization can have."""
    REQUIREMENT = "requirement"
    ELEMENT = "element"
    FUNCTION = "function"
    INTERFACE = "interface"
    PARAMETER = "parameter"
    TEST = "test"


class ArcadiaFunction(BaseModel):
    """A persisted, allocatable function (Arcadia ``fa``)."""
    id: str = ""
    study_id: str
    parent_id: str | None = None
    name: str = Field(description="Verb-noun form: e.g. 'Acquire multispectral imagery'")
    description: str = ""
    layer: ArcadiaLayer = ArcadiaLayer.SA
    function_type: str | None = None
    level: int = 0
    is_leaf: bool = False
    position_responsible: str | None = None
    external_id: str | None = None
    external_ids: dict[str, str] | None = None
    version: int = 1
    deleted_at: datetime | None = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class FunctionPort(BaseModel):
    id: str = ""
    function_id: str
    name: str = ""
    direction: PortDirection = PortDirection.OUT
    exchange_item_ids: list[str] = Field(default_factory=list)
    deleted_at: datetime | None = None
    created_at: datetime = Field(default_factory=_now)


class FunctionAllocation(BaseModel):
    """Function -> design element, unique per (function, layer)."""
    id: str = ""
    study_id: str
    function_id: str
    element_id: str
    layer: ArcadiaLayer = ArcadiaLayer.SA
    created_at: datetime = Field(default_factory=_now)


class FunctionalExchange(BaseModel):
    """Flow between two function ports, optionally realised by an element interface."""
    id: str = ""
    study_id: str
    name: str = ""
    from_port_id: str
    to_port_id: str
    exchange_item_ids: list[str] = Field(default_factory=list)
    realized_by_interface_id: str | None = None
    external_id: str | None = None
    version: int = 1
    deleted_at: datetime | None = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class Realization(BaseModel):
    """Cross-layer realization: SA->LA->PA functions, LA->PA elements."""
    id: str = ""
    study_id: str
    source_kind: EntityKind = EntityKind.FUNCTION
    source_id: str
    target_kind: EntityKind = EntityKind.FUNCTION
    target_id: str
    deleted_at: datetime | None = None
    created_at: datetime = Field(default_factory=_now)


class ExchangeItem(BaseModel):
    """What flows over an interface (Arcadia ``information`` -> ICD line)."""
    id: str = ""
    study_id: str
    name: str
    kind: ExchangeItemKind = ExchangeItemKind.DATA
    properties: dict = Field(
        default_factory=dict,
        description="rate_bps, voltage_v, current_a, freq_hz, protocol, connector, ...",
    )
    description: str = ""
    external_id: str | None = None
    external_ids: dict[str, str] | None = None
    version: int = 1
    deleted_at: datetime | None = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class RequirementRelation(BaseModel):
    """Typed relation (Capella Requirements VP / ReqIF SPEC-RELATION)."""
    id: str = ""
    study_id: str
    kind: RelationKind
    source_kind: EntityKind
    source_id: str
    target_kind: EntityKind
    target_id: str
    rationale: str = ""
    external_id: str | None = None
    deleted_at: datetime | None = None
    created_at: datetime = Field(default_factory=_now)
