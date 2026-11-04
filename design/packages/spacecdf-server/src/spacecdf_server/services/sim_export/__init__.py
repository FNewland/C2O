"""SpaceCDF design -> simulator configuration export (design-to-ops, Nov 2026).

``facts.gather(study_id)`` reads the study, ``builder.build(facts, template_dir)`` writes the
configuration (with per-value provenance and a readiness checklist), ``validate.validate_dir``
loads it with the simulator's own strict loaders. See docs/plan_2026-11/design_sim/SIM_EXPORT.md.
"""
from __future__ import annotations

from pathlib import Path


def template_dir() -> Path | None:
    """The EOSAT-1 reference configuration (defaults); ``$SPACECDF_SIM_CONFIG_DIR`` overrides."""
    from ..cdr_sim import sim_dir
    return sim_dir()
