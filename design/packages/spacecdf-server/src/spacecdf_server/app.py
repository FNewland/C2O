"""SpaceCDF — FastAPI Application.

Main entry point for the SpaceCDF server. Provides REST API and WebSocket
endpoints for study management, design execution, and real-time updates.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routers import studies, design, agents, kb, exports, positions, engineering, sessions, ws, templates, ecss, snapshots, optimize, compliance, lifecycle, ai, requirements, conops, thermal, ground, fmeca, elements
from .routers import options as options_router, analyses_simulation as analyses_simulation_router, analyses_ground as analyses_ground_router, analyses_vv as analyses_vv_router, analyses_physics as analyses_physics_router
from .routers import functions as functions_router, exchange_items as exchange_items_router, relations as relations_router, parameters as parameters_router, exchange as exchange_router
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

    # Start WebSocket edit-lock heartbeat checker
    from .routers.ws import start_heartbeat_checker
    start_heartbeat_checker()

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

# CORS for frontend development
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
app.include_router(relations_router.router, prefix="/api", tags=["Traceability"])
app.include_router(parameters_router.router, prefix="/api", tags=["Parameters"])
app.include_router(exchange_router.router, prefix="/api", tags=["Model Exchange"])
# SCDF-170 closing-the-loop routers
app.include_router(options_router.router, prefix="/api", tags=["Options"])
app.include_router(analyses_simulation_router.router, prefix="/api", tags=["Analyses: Mission Simulation"])
app.include_router(analyses_ground_router.router, prefix="/api", tags=["Analyses: Ground Segment"])
app.include_router(analyses_vv_router.router, prefix="/api", tags=["Analyses: V&V"])
app.include_router(analyses_physics_router.router, prefix="/api", tags=["Analyses: Physics"])
app.include_router(ws.router, tags=["WebSocket"])


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
