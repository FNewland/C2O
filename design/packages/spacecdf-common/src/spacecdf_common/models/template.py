"""SpaceCDF — Mission Design Template model.

A MissionTemplate packages a MissionRequirements baseline plus SE metadata
(archetype, ECSS phase, equipment hints) so that a new study can be seeded
from a canonical starting point instead of an empty form.

Phase 5A deliverable. Aligns with the ECSS project phase structure defined
in ECSS-M-ST-10C Rev.1 (see ~/.claude/skills/ecss-m-st-10/SKILL.md, or the
canonical reference under ecss-standards/references/M/).
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from .study import MissionRequirements, StudyPhase


class Archetype(str, Enum):
    """Canonical mission archetypes for template filtering."""

    CUBESAT_TECH_DEMO = "cubesat_tech_demo"
    CUBESAT_EO = "cubesat_eo"
    SMALLSAT_EO = "smallsat_eo"
    COMSAT_LEO = "comsat_leo"
    COMSAT_GEO = "comsat_geo"
    LUNAR_ORBITER = "lunar_orbiter"
    MARS_ORBITER = "mars_orbiter"
    CONSTELLATION_MEMBER = "constellation_member"
    SCIENCE_L2 = "science_l2"


class EquipmentHint(BaseModel):
    """Hint at a commonly used equipment option for this archetype.

    Points at a Knowledge-Base component ID that the user can adopt via the
    existing EquipmentBrowser flow. Non-binding — the template just suggests.
    """

    category: str = Field(description="KB category, e.g. 'batteries', 'star_trackers'")
    component_id: str | None = Field(default=None, description="Specific KB component ID")
    rationale: str = Field(default="", description="Why this is a reasonable default")


class MissionTemplate(BaseModel):
    """A canonical starting point for a new design study.

    Exposed read-only via GET /api/templates. A user picks one and POSTs to
    /api/studies/from-template; the server creates a Study seeded from
    `requirements` and returns it. The ECSS metadata feeds the compliance
    panel: knowing the target phase lets us surface the expected DRDs.
    """

    id: str = Field(description="Stable slug, e.g. '6u_eo_cubesat'")
    name: str = Field(description="Human-friendly name")
    archetype: Archetype
    description: str = Field(description="One-paragraph overview shown in the gallery")
    typical_use_cases: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    # The seeded MissionRequirements — directly consumable by the study router.
    requirements: MissionRequirements

    # SE metadata
    target_phase: StudyPhase = StudyPhase.PHASE_0
    margin_policy_percent: float = Field(
        default=20.0,
        description="Recommended margin policy. Phase 0/A typically 20%, Phase B 10%.",
    )
    applicable_ecss: list[str] = Field(
        default_factory=list,
        description="ECSS standard IDs expected to apply at this phase for this archetype",
    )
    equipment_hints: list[EquipmentHint] = Field(default_factory=list)
    notes: str = ""
