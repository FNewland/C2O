"""Radio web dashboard + control plane served via aiohttp.

Observation is always available: a real-time WebSocket feed of RF link
status and a static HTML dashboard page.

The control plane (POST /api/channel, /api/pipeline, /api/link) is only
mounted when the bridge is started with ``--radio-control``
(``network.radio_control_enabled``). With it off the routes return 403 and
the UI hides the configuration panel, preserving the original "purely
observational" contract.

UI split (design_2026-08 plan §1.2 / §4, standing rule "ground tools are
spacecraft-agnostic"): the operator radio page shows only what real ground
equipment shows (locks, spectrum, constellation, eye diagram, measured
levels and Doppler). The CHANNEL MODEL — injected impairments, Eb/N0 and
Doppler knobs, fading/phase-noise/interferer toggles — is simulation truth
and lives on the instructor-only sim view:

    /            resolved page: ?ui= > --ui/env-resolved server mode
    /classic     the original single-file page (channel model, pipeline
                 diagnostics): instructor-only
    /modern      the operator console (no channel model)
    /sim         instructor-only channel-model view (INSTRUCTOR strip);
                 the operator page never links here

Instructor-only (SCREEN_REVIEW #2/#3, closed in the feed, not only on the
page): ``/classic``, ``/sim``, ``/api/config`` and ``/api/diagnostics``
answer 403 to anyone but an instructor (smo_common.web.identity: an IAP
account in ``SMO_INSTRUCTORS``; on a laptop with no IAP, the person at the
keyboard), and ``/api/status`` and ``/ws`` send students and operators the
receiver's view only — :data:`TRUTH_FIELDS` (the channel model, the
instructor's ground-segment penalty, the spacecraft transmitter state, the
pass override, the simulator's range) are removed and the pipeline
diagnostics are cut to named receiver-side counters.

House precedence, same as the other three servers: CLI ``--ui`` > ``SMO_UI``
env > default "modern". Both UIs (and the sim view) hit the SAME endpoints;
no API route is removed, renamed or retyped.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from dataclasses import asdict

from aiohttp import web

from .frontend import RadioFrontend

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent.parent / "static"

#: Simulator truth and instructor settings in the RadioStatus snapshot; never
#: sent to a student or operator (SCREEN_REVIEW #2/#3).
TRUTH_FIELDS = frozenset({
    "gs_penalty_db", "phase_noise_enabled", "fading_enabled", "fading_k_db",
    "n_interferers", "config", "sc_tx_on", "sc_pa_on", "pass_override",
    "range_km", "control_enabled",
})
#: Pipeline counters a real ground receiver reports; everything else
#: (spacecraft-side tx_* counters, simulator queues) is instructor-only.
RECEIVER_DIAGNOSTICS = ("rx_good_frames", "rx_bad_frames", "rx_rs_failures",
                        "rx_fecf_failures", "rx_packets_recovered",
                        "rx_flywheel_misses", "rx_pll_resets")


def operator_view(status: dict) -> dict:
    """The receiver's view of a status snapshot (no simulator truth)."""
    out = {k: v for k, v in status.items() if k not in TRUTH_FIELDS}
    diag = status.get("diagnostics") or {}
    out["diagnostics"] = {k: diag[k] for k in RECEIVER_DIAGNOSTICS if k in diag}
    return out


def _is_instructor(request) -> bool:
    try:
        from smo_common.web.identity import is_instructor
    except ImportError:                              # pragma: no cover
        return False
    return is_instructor(request.headers)


def _status_for(request, status: dict) -> dict:
    return status if _is_instructor(request) else operator_view(status)


def _forbidden_page():
    return web.Response(
        status=403, content_type="text/html",
        text="<!doctype html><title>Radio</title><p>This page is for "
             "instructors. The radio receiver console is at "
             "<a href=\"/\">/</a>.</p>")


def _json(obj):
    return json.dumps(obj, default=str)


async def _read_json(request) -> dict:
    try:
        payload = await request.json()
    except Exception:
        raise web.HTTPBadRequest(text=_json({"error": "invalid JSON body"}),
                                 content_type="application/json")
    if not isinstance(payload, dict):
        raise web.HTTPBadRequest(text=_json({"error": "body must be an object"}),
                                 content_type="application/json")
    return payload


def _control_route(control, method_name: str):
    """Wrap a bridge control method as an aiohttp POST handler."""
    async def handler(request):
        if not _is_instructor(request):
            return web.json_response({"error": "instructor only"}, status=403,
                                     dumps=_json)
        if control is None:
            return web.json_response({"error": "control plane unavailable"},
                                     status=503, dumps=_json)
        payload = await _read_json(request)
        method = getattr(control, method_name, None)
        if method is None:
            return web.json_response({"error": f"{method_name} unsupported"},
                                     status=501, dumps=_json)
        try:
            result = method(payload)
        except PermissionError as e:
            return web.json_response({"error": str(e)}, status=403, dumps=_json)
        except (ValueError, RuntimeError) as e:
            return web.json_response({"error": str(e)}, status=400, dumps=_json)
        return web.json_response({"ok": True, "config": result}, dumps=_json)
    return handler


# ── UI switch (design_2026-08 plan §1.2, house pattern) ──────────────────

def resolve_ui_mode(ui_mode: str | None = None) -> str:
    """CLI --ui > SMO_UI env > default "modern" (Agent-5 gate passed)."""
    mode = (ui_mode or os.environ.get("SMO_UI") or "modern").strip().lower()
    if mode not in ("classic", "modern"):
        logger.warning("Unknown ui mode %r — falling back to classic", mode)
        mode = "classic"
    return mode


def _serve_page(rel: str, missing_note: str, lang: str = "en"):
    page = STATIC_DIR / rel
    if page.exists() and rel.startswith("modern/") and lang != "en":
        # i18n S0: server default UI language for browsers that have not
        # chosen one (SMO_LANG env). English pages are served unchanged.
        from smo_common.i18n import inject_default_lang
        return web.Response(
            text=inject_default_lang(page.read_text(encoding="utf-8"), lang),
            content_type="text/html", headers={"Cache-Control": "no-cache"})
    if page.exists():
        return web.FileResponse(page, headers={"Cache-Control": "no-cache"})
    return web.Response(
        text=f"<h1>SMO Radio — {missing_note}</h1>"
             "<p>The classic radio page is at <a href=\"/classic\">"
             "/classic</a>.</p>",
        content_type="text/html",
        headers={"Cache-Control": "no-cache"})


def _serve_index(mode: str, lang: str = "en"):
    if mode == "modern":
        return _serve_page("modern/index.html",
                           "modern UI assets not installed", lang)
    return _serve_page("radio.html", "static/radio.html not found")


def _add_page_routes(app: web.Application, ui_mode: str | None = None):
    """Index / classic / modern / sim page routes + static mounts."""
    resolved = resolve_ui_mode(ui_mode)
    try:
        from smo_common.i18n import server_default_lang
        lang = server_default_lang()          # SMO_LANG env > "en"
    except ImportError:                              # pragma: no cover
        lang = "en"

    def _request_ui(request) -> str:
        q = (request.query.get("ui") or "").strip().lower()
        return q if q in ("classic", "modern") else resolved

    async def index_handler(request):
        mode = _request_ui(request)
        if mode == "classic" and not _is_instructor(request):
            mode = "modern"
        return _serve_index(mode, lang)

    async def classic_handler(request):
        if not _is_instructor(request):
            return _forbidden_page()
        return _serve_index("classic")

    async def modern_handler(request):
        return _serve_index("modern", lang)

    async def sim_handler(request):
        # Instructor-only channel-model view. Simulation truth: the
        # operator page must never link here.
        if not _is_instructor(request):
            return _forbidden_page()
        return _serve_page("modern/sim.html",
                           "sim view assets not installed", lang)

    app.router.add_get("/", index_handler)
    app.router.add_get("/classic", classic_handler)
    app.router.add_get("/modern", modern_handler)
    app.router.add_get("/sim", sim_handler)
    if STATIC_DIR.exists():
        app.router.add_static("/static/", STATIC_DIR)
    # Shared design system, one canonical copy from smo-common package data,
    # mounted at the same URL on every server (plan §1.1).
    try:
        import smo_common
        shared_ui = Path(smo_common.__file__).parent / "ui"
        if shared_ui.is_dir():
            app.router.add_static("/static/shared/", shared_ui)
        else:                                        # pragma: no cover
            logger.warning("smo_common ui/ package data missing (%s) — "
                           "modern pages will render unstyled", shared_ui)
    except ImportError:                              # pragma: no cover
        logger.warning("smo_common not importable — /static/shared/ not "
                       "mounted; modern pages will render unstyled")


def _add_api_routes(app: web.Application, frontend: RadioFrontend, control):
    """The API surface. BINDING: no route removed, renamed or retyped."""

    async def api_status(request):
        return web.json_response(_status_for(request, asdict(frontend.snapshot())),
                                 dumps=_json)

    def _instructor_only(request):
        if not _is_instructor(request):
            return web.json_response({"error": "instructor only"}, status=403,
                                     dumps=_json)
        return None

    async def api_config(request):
        if (deny := _instructor_only(request)) is not None:
            return deny
        if control is None or not hasattr(control, "get_effective_config"):
            return web.json_response(frontend.status.config or {}, dumps=_json)
        return web.json_response(control.get_effective_config(), dumps=_json)

    async def api_diagnostics(request):
        if (deny := _instructor_only(request)) is not None:
            return deny
        if control is None or not hasattr(control, "get_diagnostics"):
            return web.json_response(frontend.status.diagnostics or {},
                                     dumps=_json)
        return web.json_response(control.get_diagnostics(), dumps=_json)

    async def api_pass_rollups(request):
        """GET /api/pass-rollups — end-of-pass RF summaries (G14, additive).

        Serves the JSONL rollup store (one record per completed pass:
        predicted AOS vs achieved lock, mean Eb/N0, FER, data volume) plus
        the in-progress pass when the bridge is attached. Works read-only
        without a control plane — the store is a flat file.
        """
        from ..pass_rollup import read_rollups
        try:
            limit = int(request.query.get("limit", 200))
        except (TypeError, ValueError):
            return web.json_response({"error": "limit must be an integer"},
                                     status=400, dumps=_json)
        tracker = getattr(control, "_pass_rollups", None)
        active = None
        if tracker is not None:
            try:
                active = tracker.active_summary()
            except Exception:  # noqa: BLE001
                active = None
        return web.json_response({
            "rollups": read_rollups(limit=limit),
            "active": active,
        }, dumps=_json)

    async def api_ground_limits(request):
        """GET /api/ground-limits — ground-receiver limit check (additive).

        BER (0x050C) and AGC (0x051A) are measured by the GROUND receiver,
        so they are limit-checked here, not in the spacecraft-telemetry
        limit set. Body: {source:"ground", summary, limits{hex: band+meta},
        state{hex}, value{hex}, transitions[], seq}. ``?since=<seq>`` returns
        only newer transitions, so a consumer (the MCS alarm journal) can
        poll it incrementally.
        """
        try:
            since = int(request.query.get("since", 0))
        except (TypeError, ValueError):
            return web.json_response({"error": "since must be an integer"},
                                     status=400, dumps=_json)
        frontend.snapshot()          # evaluates the limits on fresh status
        return web.json_response(frontend.ground_limits.to_api(since),
                                 dumps=_json)

    app.router.add_get("/api/status", api_status)
    app.router.add_get("/api/ground-limits", api_ground_limits)
    app.router.add_get("/api/config", api_config)
    app.router.add_get("/api/diagnostics", api_diagnostics)
    app.router.add_get("/api/pass-rollups", api_pass_rollups)
    app.router.add_post("/api/channel", _control_route(control, "apply_channel"))
    app.router.add_post("/api/pipeline", _control_route(control, "apply_pipeline"))
    app.router.add_post("/api/link", _control_route(control, "apply_link"))


async def run_web_ui(frontend: RadioFrontend, host: str = "0.0.0.0",
                     port: int = 8094, control=None,
                     ui_mode: str | None = None):
    """Start the Radio web UI server.

    ``control`` is the RFSimBridge (or any object exposing
    ``get_effective_config``, ``get_diagnostics``, ``apply_channel``,
    ``apply_pipeline`` and ``apply_link``). When omitted the server is
    read-only exactly as before.
    """
    app = web.Application()

    async def ws_handler(request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        logger.info("Radio WS client connected")
        instructor = _is_instructor(request)
        try:
            while True:
                status = frontend.snapshot()
                data = asdict(status)
                if not instructor:
                    data = operator_view(data)
                await ws.send_str(json.dumps(data, default=str))
                await asyncio.sleep(0.5)
        except Exception:
            pass
        finally:
            logger.info("Radio WS client disconnected")
        return ws

    _add_page_routes(app, ui_mode)
    app.router.add_get("/ws", ws_handler)
    _add_api_routes(app, frontend, control)
    _add_logbook_routes(app)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info("Radio web UI at http://%s:%d (ui=%s, control plane %s)",
                host, port, resolve_ui_mode(ui_mode),
                "enabled" if getattr(control, "config", None) is not None
                and getattr(control.config.network, "radio_control_enabled", False)
                else "read-only")
    while True:
        await asyncio.sleep(3600)


def build_app(frontend: RadioFrontend, control=None,
              ui_mode: str | None = None) -> web.Application:
    """Build the aiohttp app without binding a port (used by tests)."""
    app = web.Application()
    _add_page_routes(app, ui_mode)
    _add_api_routes(app, frontend, control)
    _add_logbook_routes(app)
    return app


def _add_logbook_routes(app: web.Application) -> None:
    """The participant logbook (LOGBOOK_SPEC.md) on this origin: the radio
    page's header button reads and writes the person's private logbook."""
    try:
        from smo_common.logbook import register_logbook_routes
        register_logbook_routes(app, tool="radio")
    except ImportError:                              # pragma: no cover
        logger.warning("smo_common.logbook not importable: no logbook on the radio page")
