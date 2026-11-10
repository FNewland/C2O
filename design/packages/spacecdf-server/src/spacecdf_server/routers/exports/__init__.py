"""SpaceCDF — Export API Router (package since W0.1).

Endpoints for generating SMO simulator configs, design review documents, ECSS Word documents,
launch/regulatory/thermal/test reports and flight software architecture from a design study.
Mounted by ``app.py`` at ``/api/exports``.

One module per document family, each with its own ``router`` (see
``design/docs/dev/W0_SEAMS.md`` for the module map and which agent owns which file):

========================  =========================================================
module                    routes (prefix /api/exports)
========================  =========================================================
``smo``                   POST /smo/{id}, GET /smo/{id}/validate
``packs``                 POST /docs/{id}   (SRR/PDR/CDR review data packs)
``fsw``                   POST /fsw/{id}
``mbse``                  POST /mbse/{id}
``docx``                  POST /docx/{doc_type}
``launch_icd``            POST /launch-icd/{id}
``rsssa``                 POST /rsssa/{id}
``deorbit``               POST /deorbit/{id}
``thermal``               POST /thermal-report/{id}
``test_plan``             POST /test-plan/{id}
``worksheet``             POST /worksheet/{template_id}
``regulatory``            (empty seam for W5.04: POST /regulatory/{kind}/{id})
========================  =========================================================

``_common`` holds the shared helpers. The sub-routers are included in the order the routes
had in the single-file router, so ``/openapi.json`` is unchanged by the split.
"""
from __future__ import annotations

from fastapi import APIRouter

from . import (  # noqa: F401  (order = route registration order)
    _common,
    smo,
    packs,
    fsw,
    mbse,
    docx,
    launch_icd,
    rsssa,
    deorbit,
    thermal,
    test_plan,
    worksheet,
    regulatory,
)
# Backwards-compatible names (routers/compliance.py and routers/lifecycle.py import these).
from ._common import _form_factor_from_mass, _read_orbit_params, _run_design_for_study  # noqa: F401
from .docx import generate_docx  # noqa: F401
from .fsw import (  # noqa: F401
    _derive_fault_handlers,
    _derive_memory_map,
    _derive_state_machine,
    _derive_task_list,
    _derive_tm_tc,
    export_fsw_architecture,
)
from .mbse import (  # noqa: F401
    _derive_allocation_matrix,
    _derive_functional_architecture,
    _derive_logical_architecture,
    _derive_physical_architecture,
    _derive_traceability,
    export_mbse,
)
from .packs import export_design_document  # noqa: F401
from .smo import export_smo_config, validate_smo_export  # noqa: F401
from .launch_icd import export_launch_icd  # noqa: F401
from .rsssa import export_rsssa  # noqa: F401
from .deorbit import export_deorbit  # noqa: F401
from .thermal import export_thermal_report  # noqa: F401
from .test_plan import export_test_plan  # noqa: F401
from .worksheet import WORKSHEET_TEMPLATES, generate_worksheet  # noqa: F401

#: Every export family, in route registration order. A new family module is added here (one line)
#: by the agent that owns it; nothing else in this file changes.
FAMILIES = (smo, packs, fsw, mbse, docx, launch_icd, rsssa, deorbit, thermal, test_plan, worksheet, regulatory)

router = APIRouter()
for _family in FAMILIES:
    router.include_router(_family.router)
