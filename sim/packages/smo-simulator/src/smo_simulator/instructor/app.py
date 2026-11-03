"""SMO Simulator — Instructor Web App.

aiohttp app for the instructor control interface:
scenario management, failure injection, breakpoint control, time controls.
"""
import asyncio
import json
import logging
import os
from pathlib import Path

from aiohttp import web

logger = logging.getLogger(__name__)


def create_instructor_app(engine, ui_mode: str | None = None) -> web.Application:
    """Create the instructor aiohttp application.

    ``ui_mode`` selects which console ``/`` serves (design_2026-08 plan
    §1.2): explicit arg (from the simulator's --ui CLI) > SMO_UI env >
    default "classic" (flips to modern only after the Agent-5 verification
    gate). Per-request ``?ui=`` and the /classic and /modern routes override
    it for a single response, and ``?ui=`` COMPOSES with the existing
    ``?sub=`` deep-dive parameter — the query string is passed through to
    whichever page is served, never consumed here.
    """
    # FIELD DEFECT 2026-08-20 (owner: "you wiped out almost all the quick
    # commands"): a module referenced with a HARD-CODED `?v=1` was cached
    # heuristically by Chrome and ran against a fresh index.html. The shared
    # HTTP policy (smo_common.web.http, R3 audit A8) keeps that fixed while
    # adding gzip: the modern index's /static/ URLs are stamped with their
    # real content hash (immutable in the browser, new URL on every change);
    # any other own asset is `no-cache` (revalidate, a bodiless 304 when
    # unchanged); a hand-written ?v= is never trusted.
    app = web.Application()
    from smo_common.web.http import apply_http_policy
    apply_http_policy(app, revalidate_prefixes=("/static/",),
                      max_age_prefixes={"/static/vendor/": 86400})
    app["engine"] = engine
    app["ws_clients"] = []
    # default flipped to modern (Agent-5 gate passed)
    resolved_ui = (ui_mode or os.environ.get("SMO_UI") or "modern").strip().lower()
    if resolved_ui not in ("classic", "modern"):
        logger.warning("Unknown ui mode %r — falling back to classic",
                       resolved_ui)
        resolved_ui = "classic"
    app["ui_mode"] = resolved_ui
    # UI language default (i18n S0): SMO_LANG env > mission `ui_lang:` > "en".
    # Injected as <html data-default-lang> into the modern page only when not
    # English; the browser's ?lang= / toggle wins.
    from smo_common.i18n import mission_ui_lang, server_default_lang
    app["ui_lang"] = server_default_lang(mission_lang=mission_ui_lang(
        getattr(engine, "config_dir", None) or "configs/eosat1"))

    # Participant logbook (LOGBOOK_SPEC.md §6): the instructor's own private
    # logbook and the worksheet lists. Behind smo-link the GSG serves these
    # routes itself (they are not on the link allowlist).
    try:
        from smo_common.logbook import register_logbook_routes
        _cfg = Path(getattr(engine, "config_dir", None) or "configs/eosat1")
        register_logbook_routes(app, tool="instructor", worksheets_dir=_cfg / "worksheets")
    except Exception as e:  # noqa: BLE001 — never block the sim UI
        logger.warning("Logbook not mounted: %s", e)

    app.router.add_get("/", handle_index)
    # Explicit generation routes (plan §1.2): live A/B comparison in two tabs.
    app.router.add_get("/classic", handle_index_classic)
    app.router.add_get("/modern", handle_index_modern)
    app.router.add_get("/ws", handle_ws)
    app.router.add_get("/api/state", handle_state)
    app.router.add_get("/api/instructor/snapshot", handle_instructor_snapshot)
    # Instructor console redesign (docs/plan_2026-11/INSTRUCTOR_CONSOLE_DESIGN.md).
    # Truth views, the truth-vs-trainee divergence, the one timeline and the
    # fault menu. INSTRUCTOR ONLY: never mounted by the MCS or planner, never
    # put in /api/state or on /ws (rfsim and the planner read those), and
    # listed one by one on the space-link proxy allowlist (smo_link.httpproxy).
    app.router.add_get("/api/instructor/views", handle_instructor_views)
    app.router.add_get("/api/instructor/timeline", handle_instructor_timeline)
    app.router.add_get("/api/instructor/fault-menu", handle_fault_menu)
    app.router.add_get("/api/instructor/history", handle_instructor_history)
    app.router.add_get("/api/instructor/debrief", handle_instructor_debrief)
    # VR visualisation bridge (smo-vr/1): headset link status + latest frame.
    app.router.add_get("/api/vr", handle_vr)
    app.router.add_post("/api/command", handle_command)
    app.router.add_get("/api/scenarios", handle_scenarios)
    app.router.add_get("/api/scenario/debrief", handle_scenario_debrief)
    app.router.add_get("/api/failures", handle_failures)
    # Declarative failure-injection parameter specs. The UI GENERATES its
    # injection form from this (typed unit selectors, real engineering units,
    # real ranges) instead of hard-coding a single 0..1 severity slider.
    app.router.add_get("/api/failure-catalog", handle_failure_catalog)
    app.router.add_get("/api/breakpoints", handle_breakpoint_list)
    app.router.add_post("/api/breakpoint/save", handle_breakpoint_save)
    app.router.add_post("/api/breakpoint/load", handle_breakpoint_load)

    # Delayed-TM (S15) dump store. This process is the WRITER of the archive
    # files, so it can always serve them even when the MCS runs on another
    # machine with no shared filesystem (defect #90). The MCS mounts the same
    # routes; students normally use the MCS copy.
    try:
        from smo_common.dump_store import register_dump_routes
        register_dump_routes(
            app,
            lambda: getattr(engine, "_dump_dir", Path("workspace/dumps")),
            owner="simulator",
        )
    except Exception as e:  # noqa: BLE001 — never let this block the sim UI
        logger.warning("Delayed-TM dump API not mounted: %s", e)

    # Delayed-TM report generator (Phase F §A) — same library/routes the MCS
    # mounts, so a split deployment still has a report surface on 8080.
    try:
        from smo_common.reporting import register_report_routes
        register_report_routes(
            app,
            lambda: getattr(engine, "_dump_dir", Path("workspace/dumps")),
            getattr(engine, "config_dir", Path("configs/eosat1")),
            owner="simulator",
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("Delayed-TM report API not mounted: %s", e)

    # Safe config editor (Phase F §B). Port 8080 is the INSTRUCTOR's door
    # (docs/DEPLOYMENT.md) — this is the only host that mounts the write
    # surface; the MCS/planner mount the same routes readonly, so students
    # can browse configuration and its history but can never mutate it.
    # While a training scenario is active, apply/revert are refused unless
    # explicitly forced with a recorded reason (brief 06 safety rule 3).
    try:
        from smo_common.confedit import register_config_routes

        def _scenario_active() -> bool:
            se = getattr(engine, "_scenario_engine", None)
            try:
                return bool(se and se.is_active())
            except Exception:  # noqa: BLE001
                return False

        register_config_routes(
            app,
            getattr(engine, "config_dir", Path("configs/eosat1")),
            readonly=False,
            page_path="/config",
            owner="instructor",
            scenario_active=_scenario_active,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("Config editor not mounted: %s", e)

    # Course PDFs, instructor list (every entry, incl. instructor-only
    # books): smo_common/downloads.yaml. The GSG serves the same routes
    # locally in a split deployment (smo_link.gateway).
    try:
        from smo_common.downloads import register_download_routes
        register_download_routes(app, audience="instructor")
    except Exception as e:  # noqa: BLE001
        logger.warning("Course PDF downloads not mounted: %s", e)

    # Shared design system (design_2026-08 plan §1.1): one canonical runtime
    # copy served from smo_common package data at the SAME URL on all three
    # servers. Mounted BEFORE /static/ so the broader mount cannot shadow it
    # (aiohttp resolves routes in registration order).
    try:
        import smo_common as _smo_common
        _shared_ui = Path(_smo_common.__file__).parent / "ui"
        if _shared_ui.is_dir():
            app.router.add_static("/static/shared/", _shared_ui)
        else:  # pragma: no cover — packaging error, say so loudly
            logger.warning("smo_common ui/ package data missing (%s) — "
                           "modern pages will render unstyled", _shared_ui)
    except Exception as e:  # noqa: BLE001 — never block the sim UI
        logger.warning("Shared UI assets not mounted: %s", e)

    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.router.add_static("/static/", static_dir)

    return app



TC_BACK_CHANNEL_DENIED = (
    "Spacecraft telecommands must be sent via the TC TCP socket (port 8001), "
    "not via HTTP. The MCS uses /api/pus-command on the TC socket."
)


# Keys of a `failure_inject` payload that belong to the failure MANAGER
# (severity/timing), not to the failure's own declarative parameter spec.
_INJECT_META_KEYS = ("type", "subsystem", "failure", "mode", "magnitude",
                     "onset", "duration_s", "onset_duration_s",
                     "snapshot_before", "label")

#: Commands whose refusal reason the console must see: run synchronously on
#: the tick thread instead of fire-and-forget on the queue.
_SYNC_CMDS = ("failure_schedule", "schedule_cancel", "timeline_mark")


def _validate_failure_inject(cmd) -> tuple[bool, str]:
    """Validate a `failure_inject` payload against the failure catalogue.

    The engine's own allowlist only range-checks magnitude/durations; it has
    no idea that `wheel` must be 0-3 or that `line_index` must name one of the
    nine EPS power lines. Checking here means the operator gets the REASON in
    the HTTP/WS response instead of the injection being rejected later, inside
    the tick thread, where only the log sees it. FailureManager.inject
    re-validates — this is the client-facing half of the same check, and both
    reject rather than clamp.
    """
    if isinstance(cmd, dict) and cmd.get("type") == "failure_schedule":
        injects = cmd.get("injects")
        if not isinstance(injects, list) or not injects:
            return False, "failure_schedule needs a non-empty injects list"
        for i, inj in enumerate(injects):
            if not isinstance(inj, dict):
                return False, f"injects[{i}] must be an object"
            ok, reason = _validate_failure_inject({**inj, "type": "failure_inject"})
            if not ok:
                return False, f"injects[{i}]: {reason}"
        return True, ""
    if not isinstance(cmd, dict) or cmd.get("type") != "failure_inject":
        return True, ""
    try:
        from smo_simulator.failure_catalog import validate
        from smo_simulator.failure_spec import FailureParamError
    except Exception as e:  # noqa: BLE001 — never block the UI on this
        logger.warning("Failure catalogue unavailable, skipping check: %s", e)
        return True, ""
    params = {k: v for k, v in cmd.items() if k not in _INJECT_META_KEYS}
    try:
        validate(cmd.get("subsystem", ""),
                 cmd.get("failure") or cmd.get("mode", ""),
                 cmd.get("magnitude"), params)
    except FailureParamError as e:
        return False, str(e)
    return True, ""


def _is_spacecraft_telecommand(cmd) -> bool:
    """True if `cmd` looks like a PUS TC smuggled onto the instructor channel."""
    if not isinstance(cmd, dict):
        return False
    cmd_type = cmd.get("type", "")
    return ("service" in cmd or "subtype" in cmd or "data_hex" in cmd
            or (isinstance(cmd_type, str) and cmd_type.startswith(("S", "TC"))))


def _resolve_ui(request) -> str:
    """Per-request UI mode: ?ui= wins over the app's resolved mode.

    ?ui= composes with ?sub= (and any other query param): resolution reads
    only `ui`; the full query string still reaches the served page, whose
    JS handles `sub` exactly as before.
    """
    q = (request.query.get("ui") or "").strip().lower()
    if q in ("classic", "modern"):
        return q
    return request.app.get("ui_mode", "classic")


def _serve_index(mode: str, lang: str = "en", app: web.Application | None = None):
    static_dir = Path(__file__).parent / "static"
    index_file = (static_dir / "modern" / "index.html" if mode == "modern"
                  else static_dir / "index.html")
    if index_file.exists() and mode == "modern":
        from smo_common.i18n import inject_default_lang
        from smo_common.web.http import stamp_asset_versions
        html = index_file.read_text(encoding="utf-8")
        if lang != "en":
            html = inject_default_lang(html, lang)
        if app is not None:
            html = stamp_asset_versions(html, app)
        return web.Response(text=html, content_type="text/html",
                            headers={"Cache-Control": "no-cache"})
    if index_file.exists():
        # no-cache: a UI-mode flip must never be masked by a cached index (R9)
        return web.FileResponse(
            index_file, headers={"Cache-Control": "no-cache"})
    if mode == "modern":
        return web.Response(
            text="<h1>SMO Instructor — modern UI assets not installed</h1>"
                 "<p>The classic console is at <a href=\"/classic\">"
                 "/classic</a>.</p>",
            content_type="text/html",
            headers={"Cache-Control": "no-cache"})
    return web.Response(
        text="<h1>SMO Instructor — static/index.html not found</h1>",
        content_type="text/html",
        headers={"Cache-Control": "no-cache"})


async def handle_index(request):
    return _serve_index(_resolve_ui(request), request.app.get("ui_lang", "en"),
                        request.app)


async def handle_index_classic(request):
    """GET /classic — always the classic page (live A/B comparison)."""
    return _serve_index("classic")


async def handle_index_modern(request):
    """GET /modern — always the modern page (live A/B comparison)."""
    return _serve_index("modern", request.app.get("ui_lang", "en"), request.app)


async def handle_ws(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    engine = request.app["engine"]
    ws_clients = request.app["ws_clients"]
    ws_clients.append(ws)
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                # Roadmap N-1 / DI-01: this path had NO allowlist and no type
                # validation, while the HTTP path did — two channels, two trust
                # levels, one queue. A malformed payload (e.g.
                # {"type":"set_speed","value":"fast"}) reached the tick thread
                # and killed it silently. Both channels now go through the same
                # SimulationEngine.submit_instructor_cmd validator.
                try:
                    cmd = json.loads(msg.data)
                except (ValueError, TypeError) as e:
                    await ws.send_str(json.dumps(
                        {"status": "denied", "message": f"malformed JSON: {e}"}))
                    continue
                if _is_spacecraft_telecommand(cmd):
                    await ws.send_str(json.dumps(
                        {"status": "denied",
                         "message": TC_BACK_CHANNEL_DENIED}))
                    continue
                ok, reason = _validate_failure_inject(cmd)
                if ok:
                    ok, reason = engine.submit_instructor_cmd(cmd)
                await ws.send_str(json.dumps(
                    {"status": "ok"} if ok
                    else {"status": "denied", "message": reason}))
    except Exception:
        pass
    finally:
        if ws in ws_clients:
            ws_clients.remove(ws)
    return ws


async def handle_state(request):
    engine = request.app["engine"]
    return web.json_response(engine.get_state_summary())


async def handle_vr(request):
    """VR bridge status: who is connected, their status words, and the frame
    the headsets are being sent (docs/VR_INTERFACE_ICD.md)."""
    engine = request.app["engine"]
    link = getattr(engine, "vr_link", None)
    get = getattr(engine, "get_vr_state", None)
    return web.json_response({
        "link": link if link is not None else {"enabled": False},
        "frame": get() if callable(get) else None,
    })


async def handle_command(request):
    """Instructor-only command handler.

    Accepts only simulation control commands: set_speed, freeze, resume,
    inject, clear_failure, failure_inject, failure_clear, override_passes,
    set_phase, scenario_* operations.

    Rejects spacecraft telecommands with HTTP 403. The MCS must use the TC TCP
    socket for all commands, not this HTTP back-channel.
    """
    engine = request.app["engine"]
    try:
        cmd = await request.json()
        cmd_type = cmd.get("type", "")

        # Reject spacecraft telecommands (look like svc/sub/data_hex)
        if _is_spacecraft_telecommand(cmd):
            return web.json_response(
                {"status": "denied", "message": TC_BACK_CHANNEL_DENIED},
                status=403,
            )

        # Typed failure-injection parameters, checked against the model-declared
        # specs so the caller gets the reason rather than a silent no-op.
        ok, reason = _validate_failure_inject(cmd)
        if not ok:
            return web.json_response(
                {"status": "denied", "message": reason}, status=400)

        if cmd_type in _SYNC_CMDS:
            ok, reason = engine.validate_instructor_cmd(cmd)
            if ok:
                ok, reason = await asyncio.get_running_loop().run_in_executor(
                    None, engine.submit_instructor_cmd_sync, cmd)
            if not ok:
                return web.json_response({"status": "denied", "message": reason},
                                         status=400)
            return web.json_response({"status": "ok"})

        # One allowlist + type/range validator for every channel (roadmap N-1);
        # SimulationEngine.INSTRUCTOR_CMD_TYPES is its single definition.
        ok, reason = engine.submit_instructor_cmd(cmd)
        if not ok:
            return web.json_response(
                {"status": "denied", "message": reason
                 + ". Allowed types: "
                 + ", ".join(sorted(type(engine).INSTRUCTOR_CMD_TYPES))},
                status=403,
            )
        return web.json_response({"status": "ok"})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=400)


async def handle_scenarios(request):
    engine = request.app["engine"]
    if hasattr(engine, '_scenario_engine'):
        return web.json_response(engine._scenario_engine.list_scenarios())
    return web.json_response([])


async def handle_scenario_debrief(request):
    """Return the debrief for the most recently finished scenario.

    A scenario can now end on its own when its ``duration_s`` elapses (it no
    longer runs forever). The auto-stop builds and caches a debrief; this
    endpoint lets the instructor UI poll for and display it once the scenario
    has finished, whether it ended automatically or via stop_scenario.

    Also reports whether a scenario is currently active so the UI can poll.
    """
    engine = request.app["engine"]
    se = getattr(engine, "_scenario_engine", None)
    if se is None:
        return web.json_response({"active": False, "debrief": None})
    debrief = se.last_debrief()
    # The whole debrief: score, every expected response with its status and
    # evidence (command, time) or none, harmful commands, mean times with
    # their source, the commands sent (scenario_scoring.py).
    payload = debrief.to_dict() if debrief is not None else None
    return web.json_response({
        "active": se.is_active(),
        "current": se.current_name(),
        "debrief": payload,
    })


async def handle_failures(request):
    engine = request.app["engine"]
    return web.json_response(engine._failure_manager.active_failures())


async def handle_failure_catalog(request):
    """Serve the declarative failure-injection parameter specs.

    Built from each subsystem model's own ``FAILURE_SPECS`` table (see
    ``smo_simulator/failure_spec.py``), so the instructor form is generated
    from the implementation and cannot drift from it. Adding a failure to a
    model puts it in this response — and therefore in the UI — with no UI edit.
    """
    from smo_simulator import failure_catalog
    return web.json_response(failure_catalog.to_dict())


async def handle_breakpoint_list(request):
    """List the breakpoints the engine currently holds (defect #10).

    Lets the instructor UI render LOAD buttons for breakpoints saved earlier,
    including across page reloads, rather than only for same-session saves.
    """
    engine = request.app["engine"]
    store = getattr(engine, "_breakpoints", {}) or {}
    out = []
    for name, state in store.items():
        out.append({
            "name": name,
            "tick": (state or {}).get("tick_count"),
            "sim_time": (state or {}).get("sim_time"),
            "auto": bool((state or {}).get("auto")),
        })
    # Auto snapshots taken before injected faults (memory + disk, survive a
    # restart): auto_snapshots.py. Restored with the same /api/breakpoint/load.
    autos = getattr(engine, "_auto_snapshots", None)
    for row in (autos.list() if autos is not None else []):
        out.append({
            "name": row["name"], "tick": None, "sim_time": row["sim_time"],
            "auto": True, "fault": row.get("fault"), "on_disk": bool(row.get("on_disk")),
            "bytes": row.get("bytes"), "previous_process": bool(row.get("previous_process")),
            "note": row.get("note") or "",
        })
    return web.json_response(out)


async def handle_breakpoint_save(request):
    """POST /api/breakpoint/save — routed through the instructor queue (A-3).

    `BreakpointManager.save()/load()` reassign `engine.params`, `_sim_time` and
    every model's state. They used to run inline on the aiohttp thread with no
    coordination with `_tick_once`, so a load landing mid-tick produced a
    spacecraft state with no physical cause. Both now execute on the tick
    thread between ticks and the handler waits for the result.
    """
    engine = request.app["engine"]
    data = await request.json()
    name = data.get("name", "")
    ok, reason = await asyncio.get_running_loop().run_in_executor(
        None, engine.submit_instructor_cmd_sync,
        {"type": "save_breakpoint", "name": name})
    if not ok:
        return web.json_response({"status": "failed", "error": reason},
                                 status=500)
    return web.json_response({"status": "saved", "name": name})


async def handle_breakpoint_load(request):
    """POST /api/breakpoint/load — routed through the instructor queue (A-3)."""
    engine = request.app["engine"]
    data = await request.json()
    cmd = {"type": "load_breakpoint", "name": data.get("name", "")}
    if data.get("state") is not None:
        cmd["state"] = data["state"]
    ok, reason = await asyncio.get_running_loop().run_in_executor(
        None, engine.submit_instructor_cmd_sync, cmd)
    return web.json_response({"status": "loaded" if ok else "failed",
                              **({"error": reason} if not ok else {})})


async def handle_instructor_snapshot(request):
    """Instructor-only endpoint returning ground-truth state, bypassing RF link gating.

    This endpoint exposes the complete internal state of all subsystem models
    and the simulation engine, suitable for the instructor/operator display which
    has god-mode visibility into the sim (not constrained by simulated RF link status).
    """
    engine = request.app["engine"]
    return web.json_response(engine.get_instructor_snapshot())


# ── instructor console redesign (INSTRUCTOR_CONSOLE_DESIGN.md) ─────────────

def _recorder(request):
    return getattr(request.app["engine"], "instructor_rec", None)


def _no_store(payload, status=200):
    # Truth must not sit in a shared cache (the GSG relays Cache-Control).
    return web.json_response(payload, status=status,
                             headers={"Cache-Control": "no-store"})


async def handle_instructor_views(request):
    """GET /api/instructor/views — the truth views, the divergence table and
    the overview tiles, as last built on the tick thread (<= 1 Hz)."""
    rec = _recorder(request)
    if rec is None:
        return _no_store({"error": "instructor recorder not available"}, 503)
    views = rec.published()
    if views is None:
        return _no_store({"pending": True, "reason": "first views not built yet"})
    return _no_store(views)


async def handle_instructor_timeline(request):
    """GET /api/instructor/timeline?since=<seq> — timeline items after
    ``since``, the pending (future) injects and the fault swimlanes."""
    rec = _recorder(request)
    if rec is None:
        return _no_store({"error": "instructor recorder not available"}, 503)
    try:
        since = int(request.query.get("since", "0"))
    except ValueError:
        return _no_store({"error": "since must be an integer"}, 400)
    return _no_store(rec.timeline_since(max(0, since)))


async def handle_fault_menu(request):
    """GET /api/instructor/fault-menu — the failure catalogue grouped by
    control-loop element (form specs stay in /api/failure-catalog)."""
    from smo_simulator.instructor import taxonomy
    return _no_store(taxonomy.fault_menu())


async def handle_instructor_history(request):
    """GET /api/instructor/history[?seg=N] — sampled truth / onboard / ground
    triples (every 10 sim s) for the debrief replay."""
    rec = _recorder(request)
    if rec is None:
        return _no_store({"error": "instructor recorder not available"}, 503)
    seg = request.query.get("seg")
    try:
        seg_n = int(seg) if seg not in (None, "") else rec.segment
    except ValueError:
        return _no_store({"error": "seg must be an integer"}, 400)
    return _no_store({"segment": seg_n, "samples": rec.history(seg_n)})


async def handle_instructor_debrief(request):
    """GET /api/instructor/debrief — everything the debrief view and its
    export need in one document: the scenario debrief, the fault swimlanes
    with their latencies, and the current segment's timeline."""
    rec = _recorder(request)
    engine = request.app["engine"]
    if rec is None:
        return _no_store({"error": "instructor recorder not available"}, 503)
    tl = rec.timeline_since(0, limit=MAX_DEBRIEF_ITEMS)
    seg = tl["segment"]
    se = getattr(engine, "_scenario_engine", None)
    d = se.last_debrief() if se is not None else None
    return _no_store({
        "segment": seg,
        "now": tl["now"],
        "scenario": None if d is None else d.to_dict(),
        "faults": [f for f in tl["faults"] if f.get("seg") == seg],
        "items": [i for i in tl["items"] if i.get("seg") == seg],
    })


MAX_DEBRIEF_ITEMS = 6000
