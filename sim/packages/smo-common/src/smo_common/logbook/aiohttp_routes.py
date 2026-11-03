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
                            store: LogbookStore | None = None) -> LogbookStore:
    if tool not in TOOLS:
        raise ValueError(f"unknown logbook tool {tool!r}")
    store = store or LogbookStore(store_dir)
    catalog = WorksheetCatalog(worksheets_dir)
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
        ident = who(request)
        fmt = request.query.get("format", "md")
        if fmt not in ("md", "html", "json"):
            return fail(request, ident, LogbookError("format must be md, html or json"))
        lang = _lang(request.query.get("lang"))
        now = datetime.now(timezone.utc)
        s = await asyncio.to_thread(store.summary, ident.person_id)
        render = {"md": to_markdown, "html": to_html, "json": to_json}[fmt]
        text = render(s, ident.label, lang=lang, lookup=lookup, now=now)
        if s["count"]:
            await asyncio.to_thread(store.mark_downloaded, ident.person_id, fmt, now=now)
        ctype = {"md": "text/markdown", "html": "text/html", "json": "application/json"}[fmt]
        resp = web.Response(text=text, content_type=ctype, charset="utf-8", headers={
            **_NO_STORE,
            "Content-Disposition": f'attachment; filename="{export_filename(fmt, now)}"'})
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
        sheets = await asyncio.to_thread(catalog.match, t, ctx, lang)
        return reply(request, ident, {"tool": t, "lang": lang, "worksheets": sheets})

    r = app.router
    r.add_get("/api/logbook", get_logbook)
    r.add_delete("/api/logbook", delete_all)
    r.add_post("/api/logbook/entries", post_entry)
    r.add_patch("/api/logbook/entries/{entry_id}", patch_entry)
    r.add_delete("/api/logbook/entries/{entry_id}", delete_entry)
    r.add_get("/api/logbook/export", export)
    r.add_get("/api/logbook/worksheets", worksheets)

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

