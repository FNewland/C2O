"""SpaceCDF — FastAPI Application.

Main entry point for the SpaceCDF server. Provides REST API and WebSocket
endpoints for study management, design execution, and real-time updates.
"""
from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routers import studies, design, agents, kb, exports, positions, engineering, sessions, ws, templates, ecss, snapshots, optimize, compliance, lifecycle, ai, requirements, conops, thermal, ground, fmeca, elements
from .routers import options as options_router, analyses_simulation as analyses_simulation_router, analyses_ground as analyses_ground_router, analyses_vv as analyses_vv_router, analyses_physics as analyses_physics_router
from .routers import analyses_common as analyses_common_router
from .routers import functions as functions_router, exchange_items as exchange_items_router, relations as relations_router, parameters as parameters_router, exchange as exchange_router
from .routers import interfaces as interfaces_router
from .routers import rules as rules_router
from .routers import stack as stack_router
from . import logbook
from .db.engine import DATABASE_URL, dispose_engine, get_engine
from .db.write_queue import start_worker, stop_worker

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Create DB tables from SQLAlchemy metadata (idempotent).

    Then runs the additive-column migrator (db/migrate.py) so databases
    created from an older model set gain any new columns.
    """
    from .db.models import Base

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Additive migration: any ORM column missing from an existing table
    # (Phase 5B snapshot columns, SCDF-160 arcadia columns, ...).
    from .db.migrate import ensure_schema_upgrades
    added = await ensure_schema_upgrades(engine)
    if added:
        logger.info("Schema upgraded: %s", ", ".join(added))

    logger.info("Database initialized: %s", DATABASE_URL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle — initialise services on startup."""
    logger.info("SpaceCDF server starting...")
    # Discover available agents
    from spacecdf_agents.registry import discover_agents
    available = discover_agents()
    logger.info("Discovered %d design agents: %s", len(available), list(available.keys()))

    # Persistence layer — graceful degradation on failure
    try:
        await init_db()
        await start_worker()
        # SCDF-160: reference parameter definitions (idempotent, non-fatal)
        from .db.parameter_repo import seed_parameter_definitions
        await seed_parameter_definitions()
    except Exception as e:
        logger.warning("Persistence layer failed to start (continuing in-memory only): %s", e)

    # Load persisted design elements into the write-through cache
    try:
        from .routers.elements import init_element_cache
        await init_element_cache()
    except Exception as e:
        logger.warning("Element cache init failed (continuing with empty cache): %s", e)

    # Product tree (ECSS levels): insert a Spacecraft above subsystems that hang directly off
    # a space segment (routers/product_tree.py; idempotent, runs every start-up)
    try:
        from .routers.product_tree import migrate_all
        res = await migrate_all()
        if res["moved"]:
            logger.info("Product tree migration: %s", res)
    except Exception as e:
        logger.warning("Product tree migration failed (continuing): %s", e)

    # Load persisted requirements into the write-through cache (SCDF-160 N0)
    try:
        from .routers.requirements import init_requirement_cache
        await init_requirement_cache()
    except Exception as e:
        logger.warning("Requirement cache init failed (continuing with empty cache): %s", e)

    # Load persisted studies into the write-through cache
    try:
        from .routers.studies import init_study_cache
        await init_study_cache()
    except Exception as e:
        logger.warning("Study cache init failed (continuing with empty cache): %s", e)

    # Load the CubeSat stack layouts (routers/stack.py) so the CDS and gate hooks see them
    try:
        from .routers.stack import init_stack_cache
        await init_stack_cache()
    except Exception as e:
        logger.warning("Stack layout cache init failed (continuing with empty cache): %s", e)

    # Wave 3: validate the SE protocol (configs/se_protocol.yaml) once at start-up (logs the errors)
    try:
        from .services.se_protocol import validate_at_startup
        errs = validate_at_startup()
        if errs:
            logger.error("se_protocol.yaml INVALID — the Phase panel and coaching report it:\n  %s",
                         "\n  ".join(errs[:20]))
    except Exception as e:
        logger.warning("SE protocol validation failed (continuing): %s", e)

    # Validate the expected-interface rules (configs/interface_rules.yaml) once at start-up
    try:
        from .services.interface_proposer import rules_status
        st = rules_status()
        if st["ok"]:
            logger.info("Interface rules OK: %s", st["path"])
        else:
            logger.error("Interface rules INVALID (%s) — link proposals disabled until fixed:\n  %s",
                         st["path"], "\n  ".join(st["errors"]))
    except Exception as e:
        logger.error("Interface rules could not be checked: %s", e)

    # Participant logbook (docs/plan_2026-11/LOGBOOK_SPEC.md): retention purge at
    # start-up and hourly; the files are shared with the ops tools.
    purge_task = asyncio.create_task(logbook.purge_loop())

    # Start WebSocket edit-lock heartbeat checker
    from .routers.ws import start_heartbeat_checker
    start_heartbeat_checker()

    # Deterministic design rules (configs/*.yaml): validate the schema once at start-up.
    # Errors are logged and served by /api/rules/catalogue; the rule endpoints refuse
    # to use a broken file (HTTP 500 with the reasons) rather than guess.
    try:
        from .services.rule_config import validate_all
        validate_all()
    except Exception as e:
        logger.error("Rule config validation failed to run: %s", e)

    # Optional GenAI integration — graceful degradation when spacecdf-ai not installed
    try:
        from spacecdf_ai import AIService
        ai_service = AIService.from_config()
        app.state.ai_service = ai_service
        status = "enabled" if ai_service.enabled else "disabled (set genai.enabled: true in configs/genai.yaml)"
        logger.info("GenAI capabilities loaded — %s", status)
    except ImportError:
        app.state.ai_service = None
        logger.info("GenAI not available (spacecdf-ai package not installed) — running in manual mode")
    except Exception as e:
        app.state.ai_service = None
        logger.warning("GenAI failed to initialize: %s — running in manual mode", e)

    yield
    logger.info("SpaceCDF server shutting down...")
    purge_task.cancel()
    try:
        await stop_worker()
    except Exception as e:
        logger.warning("stop_worker error: %s", e)
    try:
        await dispose_engine()
    except Exception as e:
        logger.warning("dispose_engine error: %s", e)


app = FastAPI(
    title="SpaceCDF",
    description="AI-Supported Concurrent Design Facility for Space Missions",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS for frontend development (the hosted deployment serves the built
# frontend from this same origin, so it needs no CORS entry).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(studies.router, prefix="/api/studies", tags=["Studies"])
app.include_router(design.router, prefix="/api/design", tags=["Design"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(kb.router, prefix="/api/kb", tags=["Knowledge Base"])
app.include_router(exports.router, prefix="/api/exports", tags=["Exports"])
app.include_router(positions.router, prefix="/api/positions", tags=["Positions"])
app.include_router(engineering.router, prefix="/api/engineering", tags=["Engineering"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])
app.include_router(ecss.router, prefix="/api/ecss", tags=["ECSS Compliance"])
app.include_router(snapshots.router, prefix="/api/snapshots", tags=["Snapshots"])
app.include_router(optimize.router, prefix="/api/optimize", tags=["Optimize"])
app.include_router(compliance.router, prefix="/api/compliance", tags=["Compliance"])
app.include_router(lifecycle.router, prefix="/api/lifecycle", tags=["Lifecycle"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI Advisor"])
app.include_router(requirements.router, prefix="/api/requirements", tags=["Requirements"])
app.include_router(conops.router, prefix="/api/conops", tags=["ConOps"])
app.include_router(thermal.router, prefix="/api/thermal", tags=["Thermal"])
app.include_router(ground.router, prefix="/api/ground", tags=["Ground Segment"])
app.include_router(fmeca.router, prefix="/api/fmeca", tags=["FMECA"])
app.include_router(elements.router, prefix="/api", tags=["Design Elements"])
# SCDF-160 Arcadia spine routers
app.include_router(functions_router.router, prefix="/api", tags=["Functions"])
app.include_router(exchange_items_router.router, prefix="/api", tags=["Exchange Items / ICD"])
app.include_router(interfaces_router.router, prefix="/api", tags=["Interfaces: rules & readiness"])
from .routers import electrical as electrical_router, interface_requirements as ir_router  # noqa: E402
app.include_router(electrical_router.router, prefix="/api", tags=["Electrical & data handling"])
app.include_router(ir_router.router, prefix="/api", tags=["Interface requirements"])
app.include_router(relations_router.router, prefix="/api", tags=["Traceability"])
app.include_router(parameters_router.router, prefix="/api", tags=["Parameters"])
app.include_router(exchange_router.router, prefix="/api", tags=["Model Exchange"])
# SCDF-170 closing-the-loop routers
app.include_router(options_router.router, prefix="/api", tags=["Options"])
app.include_router(analyses_common_router.router, prefix="/api", tags=["Analyses"])
app.include_router(analyses_simulation_router.router, prefix="/api", tags=["Analyses: Mission Simulation"])
app.include_router(analyses_ground_router.router, prefix="/api", tags=["Analyses: Ground Segment"])
app.include_router(analyses_vv_router.router, prefix="/api", tags=["Analyses: V&V"])
app.include_router(analyses_physics_router.router, prefix="/api", tags=["Analyses: Physics"])
# Deterministic design rules replacing AI (docs/RULES_AND_AI.md)
app.include_router(rules_router.router, prefix="/api", tags=["Design rules"])
# Mode model, budgets per mode and the proposal rules (Nov 2026, design rules phase 1)
from .routers import modes as modes_router  # noqa: E402
app.include_router(modes_router.router, prefix="/api", tags=["Modes & budgets"])
# Product tree levels, default trees, spacecraft, migration (ECSS-M-ST-10C)
from .routers import product_tree as product_tree_router  # noqa: E402
app.include_router(product_tree_router.router, prefix="/api", tags=["Product tree"])
# CDR design model: TM/TC database, FDIR, AOCS modes, TT&C ladder, line states, operations
from .routers import cdr as cdr_router  # noqa: E402
app.include_router(cdr_router.router, prefix="/api", tags=["CDR design model"])
from .routers import sim_export as sim_export_router  # noqa: E402
app.include_router(sim_export_router.router, prefix="/api", tags=["Simulator configuration export"])

# CubeSat stack builder (design rules §4, D9)
app.include_router(stack_router.router, prefix="/api", tags=["Stack builder"])
# Project file Save / Load: the whole study as one JSON document (services/project_file.py)
from .routers import project_io as project_io_router  # noqa: E402
app.include_router(project_io_router.router, prefix="/api", tags=["Project file"])
# Review gates per study profile + team records (WP0/WP6, Nov 2026)
from .routers import gates as gates_router  # noqa: E402
app.include_router(gates_router.router, prefix="/api", tags=["Review gates"])
# Shared export seams (W0): the one mass/power roll-up and the study collector, read-only
from .routers import study_export as study_export_router  # noqa: E402
app.include_router(study_export_router.router, prefix="/api", tags=["Exports"])
# SEMP / ECSS diagram models, SVG/PNG and the diagram document (design rules §3)
from .routers import diagrams as diagrams_router  # noqa: E402
app.include_router(diagrams_router.router, prefix="/api", tags=["Diagrams"])
# SpaceCDF seats (WP9): seat API, instructor class board, server-side write guard
from . import seats as seats_pkg  # noqa: E402
app.include_router(seats_pkg.router, prefix="/api", tags=["Seats"])
app.include_router(seats_pkg.instructor_router, prefix="/api/instructor", tags=["Instructor"])
app.add_middleware(seats_pkg.SeatGuard)
# Participant logbook + worksheets (same API as the ops tools)
app.include_router(logbook.router, prefix="/api/logbook", tags=["Logbook"])
app.include_router(ws.router, tags=["WebSocket"])
# W8a / W11a (platform, AIT and schedule): model philosophy, test matrix and verification plan;
# project settings, milestones, work packages and the bottom-up cost
from .routers import ait as ait_router  # noqa: E402
from .routers import schedule as schedule_router  # noqa: E402
app.include_router(ait_router.router, prefix="/api", tags=["AIT and verification plan"])
app.include_router(schedule_router.router, prefix="/api", tags=["Schedule and cost"])

# Wave 3, step 0: every new router of the wave, registered once here (owners in
# docs/dev/W0_SEAMS.md §9; no edits to this list during the parallel wave). Step 0 serves stubs.
from .routers import se_phase as se_phase_router, moes as moes_router  # noqa: E402
from .routers import validation as validation_router, assumptions as assumptions_router  # noqa: E402
from .routers import negotiations as negotiations_router, sensitivity as sensitivity_router  # noqa: E402
from .routers import changes as changes_router, impact as impact_router, open_items as open_items_router  # noqa: E402
app.include_router(se_phase_router.router, prefix="/api", tags=["SE phase"])                    # S 3.S1
app.include_router(moes_router.router, prefix="/api", tags=["Stakeholders and MOEs"])           # S 3.S3
app.include_router(validation_router.router, prefix="/api", tags=["Validation"])               # S 3.S5
app.include_router(assumptions_router.router, prefix="/api", tags=["Assumptions"])             # S 3.S6
app.include_router(negotiations_router.router, prefix="/api", tags=["Negotiations"])           # H 3.H6
app.include_router(sensitivity_router.router, prefix="/api", tags=["Sensitivity"])             # H 3.H5
app.include_router(changes_router.router, prefix="/api", tags=["Change proposals"])            # L 3.L4
app.include_router(impact_router.router, prefix="/api", tags=["Key numbers and impact"])       # L 3.L6
app.include_router(open_items_router.router, prefix="/api", tags=["Open items"])               # D 3.D4
# PI addendum (SRR and PDR pass legitimately on camera); cost pricing routes are in routers/schedule.py (A 3.A7)
from .routers import icd_issues as icd_issues_router, reliability as reliability_router  # noqa: E402
from .routers import thermal_model as thermal_model_router, debris_assessment as debris_router  # noqa: E402
from .routers import change_control as change_control_router  # noqa: E402
app.include_router(icd_issues_router.router, prefix="/api", tags=["ICD issue control"])        # R 3.R6
app.include_router(reliability_router.router, prefix="/api", tags=["Reliability and FMEA"])     # A 3.A5
app.include_router(thermal_model_router.router, prefix="/api", tags=["Thermal model"])          # A 3.A6
app.include_router(debris_router.router, prefix="/api", tags=["Debris assessment"])            # L 3.L8
app.include_router(change_control_router.router, prefix="/api", tags=["Change control"])       # D 3.D7


@app.get("/api/health")
async def health_check():
    ai_service = getattr(app.state, "ai_service", None)
    return {
        "status": "ok",
        "service": "spacecdf",
        "version": "2.0.0",
        "genai": {
            "installed": ai_service is not None,
            "enabled": ai_service.enabled if ai_service else False,
            "capabilities": (
                {k: v for k, v in ai_service.config.capabilities.items()}
                if ai_service and ai_service.enabled else {}
            ),
        },
    }


# ── Who is signed in (hosted deployment) ──────────────────────────────────
# Behind Google IAP every request carries the signed-in account in
# X-Goog-Authenticated-User-Email ("accounts.google.com:name@c2o.live").
# Locally the header is absent and the frontend asks for a name as before.
# Display only: IAP itself is the access control.
@app.get("/api/whoami")
async def whoami(request: Request):
    raw = request.headers.get("x-goog-authenticated-user-email", "")
    email = raw.split(":", 1)[-1] if raw else ""
    name = email.split("@", 1)[0].replace(".", " ").title() if email else ""
    return {"email": email or None, "name": name or None}


# ── Built frontend (hosted deployment) ────────────────────────────────────
# SPACECDF_STATIC_DIR points at frontend/dist (the Docker image sets it).
# Unknown non-API paths return index.html so the React routes survive a
# reload. Registered last, after every /api and /ws route.
_static_dir = os.environ.get("SPACECDF_STATIC_DIR", "")
if _static_dir and Path(_static_dir, "index.html").is_file():
    _static_root = Path(_static_dir).resolve()
    app.mount("/assets", StaticFiles(directory=_static_root / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    async def spa(path: str):
        if path.startswith(("api/", "ws")):
            raise HTTPException(status_code=404)
        candidate = (_static_root / path).resolve()
        if path and candidate.is_file() and _static_root in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(_static_root / "index.html",
                            headers={"Cache-Control": "no-cache"})
