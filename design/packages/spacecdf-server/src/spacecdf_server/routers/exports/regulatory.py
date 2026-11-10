"""SpaceCDF export family: regulatory (seam created in W0.1, filled by W5.04).

Planned routes (prefix /api/exports): ``POST /regulatory/{kind}/{study_id}`` for the
study-linked RSSSA, ISED space-station brief, ISED earth stations, ITU API, ISED debris
mitigation plan and COPUOS registration generators (docx and json). Owner: agent L
(see design/docs/dev/W0_SEAMS.md). Generators take their data from
``services.export_context.collect`` and mass/power/form factor from ``services.rollup``.

The router is empty today, so ``/openapi.json`` is unchanged by its inclusion.
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()
