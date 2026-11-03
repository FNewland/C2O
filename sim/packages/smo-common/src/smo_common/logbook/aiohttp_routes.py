"""``/api/logbook`` for an aiohttp tool server (LOGBOOK_SPEC §3).

    from smo_common.logbook import register_logbook_routes
    register_logbook_routes(app, tool="mcs")

Adds the routes, and an hourly purge task started on app start-up (and
cancelled on cleanup). Call it before the app starts, and before any
catch-all route (aiohttp resolves routes in registration order).
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from datetime import datetime, timezone
from aiohttp import web

from .export import export_filename, to_html, to_json, to_markdown
from .identity import cookie_header, identify
from .store import TOOLS, LogbookError, LogbookStore
from .worksheets import WorksheetCatalog

logger = logging.getLogger(__name__)

__all__ = ["register_logbook_routes", "STORE_KEY", "PURGE_INTERVAL_S"]

STORE_KEY = web.AppKey("smo_logbook_store", LogbookStore)
PURGE_INTERVAL_S = 3600
_PURGE_TASK = web.AppKey("smo_logbook_purge_task", asyncio.Task)
_NO_STORE = {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}
_MAX_BODY = 64 * 1024


def _lang(v) -> str:
    return "fr" if str(v or "").lower().startswith("fr") else "en"


def register_logbook_routes(app: web.Application, tool: str, store_dir=None, *,
                            worksheets_dir=None, purge_interval_s: float = PURGE_INTERVAL_S,
                            store: LogbookStore | None = None,
                            checklists=None) -> LogbookStore:
    """``checklists``: optional ``provider(procedure_id, lang) -> dict | None``
    (``checklist.ChecklistProvider``) serving ``GET /api/logbook/checklist``;
    a callable taking the worksheet catalogue is also accepted, so a tool can
    build the provider around the same catalogue."""
    if tool not in TOOLS:
        raise ValueError(f"unknown logbook tool {tool!r}")
    store = store or LogbookStore(store_dir)
    catalog = WorksheetCatalog(worksheets_dir)
    if checklists is not None and getattr(checklists, "wants_catalog", False):
        checklists = checklists(catalog)
    app[STORE_KEY] = store

    def who(request: web.Request):
        return identify(request.headers, request.cookies)

    def reply(request: web.Request, ident, data, status: int = 200) -> web.Response:
        resp = web.json_response(data, status=status, headers=_NO_STORE)
        if ident.new_cookie:
            secure = request.secure or request.headers.get("X-Forwarded-Proto") == "https"
            resp.headers.add("Set-Cookie", cookie_header(ident.new_cookie, secure))
        return resp

    def fail(request, ident, e: LogbookError) -> web.Response:
        return reply(request, ident, {"error": str(e)}, e.status)

    async def body_of(request: web.Request) -> dict:
        # JSON only: a cross-site form post (text/plain, no preflight) cannot
        # write into someone's logbook.
        if request.content_type != "application/json":
            raise LogbookError("send the entry as application/json", 415)
        if request.content_length and request.content_length > _MAX_BODY:
            raise LogbookError("request body too large", 413)
        raw = await request.content.read(_MAX_BODY + 1)
        if len(raw) > _MAX_BODY:
            raise LogbookError("request body too large", 413)
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError):
            raise LogbookError("body must be JSON") from None
        if not isinstance(body, dict):
            raise LogbookError("body must be a JSON object")
        return body

    def lookup(wid, qid, lang):
        return catalog.question(wid, qid, lang)

    async def get_logbook(request: web.Request) -> web.Response:
        ident = who(request)
        s = await asyncio.to_thread(store.summary, ident.person_id,
                                    tool=request.query.get("tool") or None,
                                    since=request.query.get("since") or None)
        s["person"] = {"id_label": ident.label, "local": ident.local}
        s["tool"] = tool
        return reply(request, ident, s)

    async def post_entry(request: web.Request) -> web.Response:
        ident = who(request)
        try:
            body = await body_of(request)
            body.setdefault("tool", tool)
            ws = body.get("worksheet")
            if isinstance(ws, dict) and ws.get("id"):
                # Self-contained exports: keep the question text with the answer.
                hit = catalog.question(str(ws["id"]), str(ws.get("q") or ""), _lang(body.get("lang")))
                if hit:
                    ws.setdefault("title", hit[0])
                    if hit[1]:
                        ws.setdefault("q_text", hit[1])
            entry = await asyncio.to_thread(store.add, ident.person_id, body)
        except LogbookError as e:
            return fail(request, ident, e)
        return reply(request, ident, entry, 201)

    async def patch_entry(request: web.Request) -> web.Response:
        ident = who(request)
        try:
            body = await body_of(request)
            entry = await asyncio.to_thread(store.edit, ident.person_id,
                                            request.match_info["entry_id"], body)
        except LogbookError as e:
            return fail(request, ident, e)
        return reply(request, ident, entry)

    async def delete_entry(request: web.Request) -> web.Response:
        ident = who(request)
        try:
            await asyncio.to_thread(store.delete, ident.person_id, request.match_info["entry_id"])
        except LogbookError as e:
            return fail(request, ident, e)
        return reply(request, ident, {"ok": True})

    async def delete_all(request: web.Request) -> web.Response:
        ident = who(request)
        existed = await asyncio.to_thread(store.delete_all, ident.person_id)
        return reply(request, ident, {"ok": True, "deleted": existed})

    async def export(request: web.Request) -> web.Response:
        """``?format=md|html|json&lang=`` plus, optional (ops workbook):
        ``team, position, scenario, session`` for the hand-in header,
        ``sheet=<worksheet id>`` for one sheet only, and ``copy=1`` when the
        text goes to the clipboard (no download marker: nothing was saved)."""
        ident = who(request)
        q = request.query
        fmt = q.get("format", "md")
        if fmt not in ("md", "html", "json"):
            return fail(request, ident, LogbookError("format must be md, html or json"))
        lang = _lang(q.get("lang"))
        now = datetime.now(timezone.utc)
        header = {k: q.get(k, "")[:120] for k in ("team", "position", "scenario", "session")
                  if q.get(k, "").strip()}
        sheet = (q.get("sheet") or "").strip()[:64] or None
        s = await asyncio.to_thread(store.summary, ident.person_id)
        render = {"md": to_markdown, "html": to_html, "json": to_json}[fmt]
        text = render(s, ident.label, lang=lang, lookup=lookup, now=now,
                      order=catalog.order, header=header, sheet=sheet)
        if s["count"] and q.get("copy") != "1":
            await asyncio.to_thread(store.mark_downloaded, ident.person_id, fmt, now=now)
        ctype = {"md": "text/markdown", "html": "text/html", "json": "application/json"}[fmt]
        disp = "inline" if q.get("copy") == "1" else "attachment"
        resp = web.Response(text=text, content_type=ctype, charset="utf-8", headers={
            **_NO_STORE,
            "Content-Disposition": f'{disp}; filename="{export_filename(fmt, now, sheet)}"'})
        if ident.new_cookie:
            resp.headers.add("Set-Cookie", cookie_header(ident.new_cookie))
        return resp

    async def worksheets(request: web.Request) -> web.Response:
        ident = who(request)
        try:
            ctx = json.loads(request.query.get("context") or "{}")
        except ValueError:
            ctx = {}
        if not isinstance(ctx, dict):
            ctx = {}
        t = request.query.get("tool") or tool
        lang = _lang(request.query.get("lang"))
        if request.query.get("all") == "1":
            sheets = await asyncio.to_thread(catalog.all_for, t, ctx, lang)
        else:
            sheets = await asyncio.to_thread(catalog.match, t, ctx, lang)
        return reply(request, ident, {"tool": t, "lang": lang, "worksheets": sheets})

    async def checklist(request: web.Request) -> web.Response:
        """The live checklist of a procedure (``?procedure=NOM-001&lang=``),
        built from its card; 404 where this tool has no procedures."""
        ident = who(request)
        pid = (request.query.get("procedure") or "").strip()[:32]
        if checklists is None or not pid:
            return fail(request, ident, LogbookError("no checklist here", 404))
        lang = _lang(request.query.get("lang"))
        try:
            cl = await asyncio.to_thread(checklists, pid, lang)
        except Exception:  # noqa: BLE001 - a bad card must not break the panel
            logger.exception("checklist for %s", pid)
            cl = None
        if not cl:
            return fail(request, ident, LogbookError(f"no checklist for {pid}", 404))
        return reply(request, ident, cl)

    r = app.router
    r.add_get("/api/logbook", get_logbook)
    r.add_delete("/api/logbook", delete_all)
    r.add_post("/api/logbook/entries", post_entry)
    r.add_patch("/api/logbook/entries/{entry_id}", patch_entry)
    r.add_delete("/api/logbook/entries/{entry_id}", delete_entry)
    r.add_get("/api/logbook/export", export)
    r.add_get("/api/logbook/worksheets", worksheets)
    r.add_get("/api/logbook/checklist", checklist)

    async def _purge_loop():
        while True:
            try:
                stats = await asyncio.to_thread(store.purge)
                if stats["files_deleted"] or stats["entries_dropped"]:
                    logger.info("logbook purge: %s", stats)
            except Exception:  # noqa: BLE001 — never let the loop die
                logger.exception("logbook purge failed")
            await asyncio.sleep(purge_interval_s)

    async def _start(app_: web.Application):
        if store.dir_mode != 0o700:
            # shared store: create it now, as this service's user and group,
            # before another service (SpaceCDF) would create it as its own
            try:
                await asyncio.to_thread(store.ensure_dir)
            except OSError as e:
                logger.warning("logbook store %s: %s", store.dir, e)
        app_[_PURGE_TASK] = asyncio.create_task(_purge_loop())

    async def _stop(app_: web.Application):
        task = app_.get(_PURGE_TASK)
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task

    app.on_startup.append(_start)
    app.on_cleanup.append(_stop)
    return store

