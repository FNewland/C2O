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
from .db.engine import DATABASE_URL, dispose_engine, get_engine
from .db.write_queue import start_worker, stop_worker

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Create DB tables from SQLAlchemy metadata (idempotent).

    Also runs a tiny additive-column migrator for Phase 5B snapshot columns
    (name, label, parent_snapshot_id, tags_json). SQLite-only; Postgres
    users must run the migration documented in the Phase 5B release notes.
    """
    from sqlalchemy import text

    from .db.models import Base

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Additive-migration: snapshot columns
    if DATABASE_URL.startswith("sqlite"):
        async with engine.begin() as conn:
            rows = (await conn.execute(text("PRAGMA table_info(design_states)"))).fetchall()
            existing_cols = {row[1] for row in rows}
            additions = [
                ("name", "VARCHAR(128)"),
                ("label", "VARCHAR(32) DEFAULT 'auto'"),
                ("parent_snapshot_id", "INTEGER"),
                ("tags_json", "JSON"),
            ]
            for col, typ in additions:
                if col not in existing_cols:
                    await conn.execute(text(f"ALTER TABLE design_states ADD COLUMN {col} {typ}"))
                    logger.info("Added column design_states.%s", col)

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
    except Exception as e:
        logger.warning("Persistence layer failed to start (continuing in-memory only): %s", e)

    # Load persisted design elements into the write-through cache
    try:
        from .routers.elements import init_element_cache
        await init_element_cache()
    except Exception as e:
        logger.warning("Element cache init failed (continuing with empty cache): %s", e)

    # Load persisted studies into the write-through cache
    try:
        from .routers.studies import init_study_cache
        await init_study_cache()
    except Exception as e:
        logger.warning("Study cache init failed (continuing with empty cache): %s", e)

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
    version="0.1.0",
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
app.include_router(ws.router, tags=["WebSocket"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "spacecdf"}
