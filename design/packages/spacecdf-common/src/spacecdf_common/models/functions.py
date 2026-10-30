"""SpaceCDF — Functional decomposition model.

Implements NASA SEH Process 3 (Logical Decomposition): objectives
decompose into functions, functions into subfunctions, each function
generates derived requirements. This is the missing middle layer
between "observe crop health" and "orbit altitude = 450 km."

The decomposition tree enables:
  - Traceability: every requirement traces to a function traces to an objective
  - Completeness checking: are all functions covered by requirements?
  - Change impact: if a function changes, which requirements are affected?
  - Allocation: which subsystem is responsible for each function?

Aligned with:
  - NASA SEH §4.3: Logical Decomposition
  - NASA SEH §4.2: Technical Requirements Definition (derived reqs)
  - ECSS-E-ST-10C Rev.1 §5.2: Functional analysis
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FunctionType(str, Enum):
    """Taxonomy of spacecraft functions."""
    OBSERVE = "observe"                   # Sensing / measurement
    COMMUNICATE = "communicate"           # Data transmission
    NAVIGATE = "navigate"                 # Orbit determination / maintenance
    POINT = "point"                       # Attitude control / pointing
    POWER = "power"                       # Generate / store / distribute power
    PROTECT = "protect"                   # Thermal / radiation / debris protection
    PROCESS = "process"                   # Onboard data processing
    STORE = "store"                       # Data / propellant storage
    PROPEL = "propel"                     # Orbit manoeuvres
    SUPPORT = "support"                   # Structure / mechanisms
    COMMAND = "command"                   # Ground commanding / autonomy
    DISPOSE = "dispose"                   # End-of-life disposal
    LAUNCH = "launch"                     # Survive launch environment
    DEPLOY = "deploy"                     # Deploy appendages


class Function(BaseModel):
    """A function in the functional decomposition tree.

    Each function represents something the system must DO (verb-noun form)
    to satisfy one or more objectives. Functions decompose into subfunctions
    until they're concrete enough to generate "shall" requirements.
    """
    id: str = ""
    name: str = Field(description="Verb-noun form: e.g. 'Acquire multispectral imagery'")
    function_type: FunctionType = FunctionType.OBSERVE
    description: str = ""

    # Traceability
    parent_function_id: str | None = Field(default=None, description="Parent function (for decomposition)")
    objective_ids: list[str] = Field(default_factory=list, description="Objectives this function serves")
    derived_requirement_ids: list[str] = Field(default_factory=list, description="Requirements generated from this function")

    # Allocation
    allocated_to: str = Field(default="", description="Subsystem/domain responsible: power, aocs, link, etc.")
    position_responsible: str = Field(default="", description="Engineering position responsible")

    # Performance criteria
    performance_criteria: list[str] = Field(default_factory=list,
        description="Quantitative criteria: e.g. 'GSD <= 10m', 'pointing <= 0.1 deg'")

    # Analysis
    level: int = Field(default=0, description="Decomposition depth (0=top-level)")
    is_leaf: bool = Field(default=False, description="No further decomposition needed — generates requirements directly")
    modes: list[str] = Field(default_factory=list, description="ConOps mode IDs where this function is active")


class FunctionalDecomposition(BaseModel):
    """The complete functional decomposition tree for a mission.

    Provides the structured flow: Objective → Function → Subfunction → Requirement
    that the current tool skips entirely (jumping from objective to orbit parameters).
    """
    functions: list[Function] = Field(default_factory=list)

    def get_function(self, function_id: str) -> Function | None:
        for f in self.functions:
            if f.id == function_id:
                return f
        return None

    def get_children(self, function_id: str) -> list[Function]:
        return [f for f in self.functions if f.parent_function_id == function_id]

    def get_roots(self) -> list[Function]:
        return [f for f in self.functions if f.parent_function_id is None]

    def get_leaves(self) -> list[Function]:
        """Leaf functions — these should each map to derived requirements."""
        parent_ids = {f.parent_function_id for f in self.functions if f.parent_function_id}
        return [f for f in self.functions if f.id not in parent_ids]

    def get_by_objective(self, objective_id: str) -> list[Function]:
        return [f for f in self.functions if objective_id in f.objective_ids]

    def get_by_subsystem(self, domain: str) -> list[Function]:
        return [f for f in self.functions if f.allocated_to == domain]

    @property
    def uncovered_functions(self) -> list[Function]:
        """Functions with no derived requirements — potential gaps."""
        return [f for f in self.get_leaves() if not f.derived_requirement_ids]

    @property
    def unallocated_functions(self) -> list[Function]:
        """Functions not assigned to any subsystem."""
        return [f for f in self.functions if not f.allocated_to]

    def completeness_report(self) -> dict[str, Any]:
        """How complete is the decomposition?"""
        total = len(self.functions)
        leaves = self.get_leaves()
        uncovered = self.uncovered_functions
        unallocated = self.unallocated_functions

        return {
            "total_functions": total,
            "leaf_functions": len(leaves),
            "uncovered_leaves": len(uncovered),
            "unallocated": len(unallocated),
            "coverage_percent": ((len(leaves) - len(uncovered)) / max(len(leaves), 1)) * 100,
            "allocation_percent": ((total - len(unallocated)) / max(total, 1)) * 100,
            "uncovered_function_ids": [f.id for f in uncovered],
            "unallocated_function_ids": [f.id for f in unallocated],
        }


# ---------------------------------------------------------------------------
# Template: auto-generate a starter functional decomposition from objectives
# ---------------------------------------------------------------------------

def generate_starter_decomposition(objectives: list[dict]) -> FunctionalDecomposition:
    """Generate a starting functional decomposition from mission objectives.

    Creates a top-level function per objective, with generic subfunctions
    based on the objective type. The engineer then refines, adds, removes.
    """
    fd = FunctionalDecomposition()
    fid = 0

    for obj in objectives:
        obj_id = obj.get("id", f"obj-{fid}")
        obj_text = obj.get("text", "")
        obj_type = obj.get("type", "performance")

        # Top-level function from objective
        fid += 1
        root = Function(
            id=f"F-{fid:03d}",
            name=f"Achieve: {obj_text[:60]}",
            function_type=FunctionType.OBSERVE,
            objective_ids=[obj_id],
            level=0,
        )
        fd.functions.append(root)

        # Generate generic subfunctions based on objective type
        subfunctions = _generic_subfunctions(obj_type, obj_text, root.id)
        for sf in subfunctions:
            fid += 1
            sf.id = f"F-{fid:03d}"
            sf.level = 1
            fd.functions.append(sf)

    # Add universal functions that every mission needs
    for uf in _universal_functions():
        fid += 1
        uf.id = f"F-{fid:03d}"
        fd.functions.append(uf)

    return fd


def _generic_subfunctions(obj_type: str, obj_text: str, parent_id: str) -> list[Function]:
    """Generate generic subfunctions based on objective type."""
    text_lower = obj_text.lower()
    subs: list[Function] = []

    if "image" in text_lower or "observe" in text_lower or "monitor" in text_lower or obj_type == "coverage":
        subs.extend([
            Function(name="Acquire imagery/data", function_type=FunctionType.OBSERVE,
                     parent_function_id=parent_id, allocated_to="payload"),
            Function(name="Point instrument at target", function_type=FunctionType.POINT,
                     parent_function_id=parent_id, allocated_to="aocs"),
            Function(name="Store acquired data onboard", function_type=FunctionType.STORE,
                     parent_function_id=parent_id, allocated_to="data"),
            Function(name="Downlink data to ground", function_type=FunctionType.COMMUNICATE,
                     parent_function_id=parent_id, allocated_to="link"),
            Function(name="Process data to user products", function_type=FunctionType.PROCESS,
                     parent_function_id=parent_id, allocated_to="data"),
        ])
    elif "communi" in text_lower:
        subs.extend([
            Function(name="Receive uplink signals", function_type=FunctionType.COMMUNICATE,
                     parent_function_id=parent_id, allocated_to="link"),
            Function(name="Process and route data", function_type=FunctionType.PROCESS,
                     parent_function_id=parent_id, allocated_to="data"),
            Function(name="Transmit downlink signals", function_type=FunctionType.COMMUNICATE,
                     parent_function_id=parent_id, allocated_to="link"),
        ])
    else:
        subs.append(
            Function(name=f"Perform: {obj_text[:40]}", function_type=FunctionType.OBSERVE,
                     parent_function_id=parent_id, allocated_to="payload")
        )

    return subs


def _universal_functions() -> list[Function]:
    """Functions every space mission needs regardless of objectives."""
    return [
        Function(name="Generate electrical power", function_type=FunctionType.POWER,
                 allocated_to="power", level=0, description="SA + battery + regulation"),
        Function(name="Maintain orbit", function_type=FunctionType.NAVIGATE,
                 allocated_to="propulsion", level=0),
        Function(name="Maintain thermal environment", function_type=FunctionType.PROTECT,
                 allocated_to="thermal", level=0),
        Function(name="Survive launch environment", function_type=FunctionType.LAUNCH,
                 allocated_to="structure", level=0),
        Function(name="Communicate with ground (TTC)", function_type=FunctionType.COMMAND,
                 allocated_to="link", level=0),
        Function(name="Dispose of spacecraft at end of life", function_type=FunctionType.DISPOSE,
                 allocated_to="propulsion", level=0),
    ]
