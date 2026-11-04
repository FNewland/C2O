"""Everything the simulator export reads from a stored study (Nov 2026).

``gather(study_id)`` returns plain data only, so :mod:`.builder` stays a pure function of
the facts (tests can hand it a dict). Every source is optional: a study with no electrical
model, no CDR rows or no stack layout still exports, with defaults the readiness checklist
names.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def gather(study_id: str) -> dict[str, Any]:
    from ...db import cdr_repo, electrical_repo, mode_repo
    from ..analysis_context import build_context
    from ..physics_closure import place_elements, run_mass_properties, run_thermal_closure

    ctx = await build_context(study_id)
    study = ctx.study
    req = getattr(study, "requirements", None)
    facts: dict[str, Any] = {
        "study_id": study_id,
        "study_name": str(getattr(study, "name", "") or ""),
        "requirements": req.model_dump(mode="json") if req is not None else {},
        "elements": [e for e in ctx.elements if not e.get("deleted_at")],
        "interfaces": list(ctx.interfaces),
        "orbit": dict(ctx.orbit),
        "power": dict(ctx.power),
        "ground_stations": list(ctx.ground_stations),
        "modes": [{"id": m.id, "name": m.name, "kind": m.kind, "power_w": m.power_w, "source": m.source,
                   "members": list(m.members)} for m in ctx.modes],
        "flat": {k: v for k, v in ctx.flat.items() if isinstance(v, (int, float, str, bool))},
    }
    try:
        facts["electrical"] = await electrical_repo.load_all(study_id)
    except Exception:  # noqa: BLE001
        logger.debug("no electrical model for %s", study_id, exc_info=True)
        facts["electrical"] = {}
    try:
        facts["heaters"] = await mode_repo.list_heaters(study_id)
    except Exception:  # noqa: BLE001
        facts["heaters"] = []
    try:
        facts["cdr_rows"] = await cdr_repo.list_rows(study_id)
    except Exception:  # noqa: BLE001
        facts["cdr_rows"] = []
    # physics closure (pure; nothing is written)
    facts["mass_properties"] = None
    facts["thermal"] = None
    if ctx.elements:
        try:
            mp = run_mass_properties(ctx, place_elements(ctx))
            r = mp.result
            facts["mass_properties"] = {
                "total_mass_kg": r.total_mass_kg, "com_m": [r.com_x_m, r.com_y_m, r.com_z_m],
                "inertia": {"ixx": r.ixx, "iyy": r.iyy, "izz": r.izz, "ixy": r.ixy, "ixz": r.ixz, "iyz": r.iyz},
                "cp_cg_offset_m": mp.cp_cg_offset_m,
            }
        except Exception:  # noqa: BLE001
            logger.debug("mass properties failed for %s", study_id, exc_info=True)
        try:
            th = run_thermal_closure(ctx)
            facts["thermal"] = {"nodes": [{"element_id": n.element_id, "name": n.name, "domain": n.domain, "kind": n.kind,
                                           "mass_kg": n.mass_kg, "allow_min_c": n.allow_min_c, "allow_max_c": n.allow_max_c,
                                           "t_hot_c": n.t_hot_c, "t_cold_c": n.t_cold_c} for n in th.nodes],
                                "worst_margin_c": th.worst_margin_c, "inputs": {k: v for k, v in th.inputs.items()
                                                                                if k != "cold_orbit_avg_c"}}
        except Exception:  # noqa: BLE001
            logger.debug("thermal closure failed for %s", study_id, exc_info=True)
    try:
        from ...routers.stack import study_geometry
        facts["geometry"] = await study_geometry(study_id, "approved")
    except Exception:  # noqa: BLE001
        logger.debug("no stack geometry for %s", study_id, exc_info=True)
        facts["geometry"] = None
    return facts
