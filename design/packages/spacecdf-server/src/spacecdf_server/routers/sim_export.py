"""Design -> simulator configuration export (design-to-ops, Nov 2026).

    GET  /api/studies/{sid}/export/sim-config          readiness checklist (by CDR area) + validation
    GET  /api/studies/{sid}/export/sim-config.zip      the configuration directory as a zip

The configuration has the layout of ``sim/configs/eosat1`` and runs with
``sim/start.sh --config=<dir>`` (docs/plan_2026-11/design_sim/SIM_EXPORT.md). Every value is
from the design model or a documented default; the checklist says which, per area.
"""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

router = APIRouter()


def _template() -> Path:
    from ..services.sim_export import template_dir
    t = template_dir()
    if t is None:
        raise HTTPException(503, {"code": "sim_reference_missing",
                                  "message": "The EOSAT-1 reference configuration (sim/configs/eosat1) is not available on "
                                             "this server; set SPACECDF_SIM_CONFIG_DIR."})
    return t


async def build_export(study_id: str, *, validate: bool = True):
    """(export, readiness-with-validation)."""
    from ..services.sim_export import builder, facts, validate as val
    t = _template()
    ex = builder.build(await facts.gather(study_id), t)
    report = ex.readiness()
    if validate:
        with tempfile.TemporaryDirectory(prefix="c2o-simcfg-") as tmp:
            ex.write(Path(tmp))
            report["validation"] = val.validate_dir(Path(tmp), t)
    return ex, report


@router.get("/studies/{study_id}/export/sim-config")
async def sim_config_readiness(study_id: str, validate: bool = Query(True)) -> dict:
    """What a simulator configuration exported now would hold: per CDR area, the values taken
    from the design and those still default / missing / unsupported, and whether the result
    passes the simulator's own (strict) loaders."""
    _, report = await build_export(study_id, validate=validate)
    return report


@router.get("/studies/{study_id}/export/sim-config.zip")
async def sim_config_zip(study_id: str) -> Response:
    ex, report = await build_export(study_id)
    root = re.sub(r"[^A-Za-z0-9_-]+", "_", ex.study_name or study_id).strip("_").lower() or "spacecdf_mission"
    ex.texts["export_report.json"] = json.dumps(report, indent=1, ensure_ascii=False, default=str) + "\n"
    data = ex.zip_bytes(root)
    v = report.get("validation") or {}
    state = "unavailable" if not v.get("available") else ("ok" if not v.get("errors") else "errors")
    return Response(data, media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="{root}_simconfig.zip"',
                             "X-C2O-Validation": state})
