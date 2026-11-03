"""FastAPI routes for the logbook: /api/logbook (LOGBOOK_SPEC.md §3).

Same paths and JSON shapes as the ops tools' aiohttp implementation. No auth
beyond identity: behind IAP the signed-in email, otherwise the ``c2o_lb``
browser cookie. Handlers are plain ``def`` so FastAPI runs the (small,
flock'd) file I/O in its thread pool.
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Body, Query, Request, Response
from fastapi.responses import JSONResponse

from . import export as export_mod
from . import worksheets as ws_mod
from .store import (
    COOKIE_MAX_AGE, COOKIE_NAME, IAP_HEADER, LANGS, TOOLS, LogbookError, LogbookStore,
    fold, iso, new_local_id, now_utc, parse_ts, person_from_cookie, person_from_iap,
)

TOOL = "design"
router = APIRouter()
store = LogbookStore()


class Identity:
    __slots__ = ("person_id", "local", "new_cookie")

    def __init__(self, person_id: str, local: bool, new_cookie: bool):
        self.person_id = person_id
        self.local = local
        self.new_cookie = new_cookie

    def label(self, lang: str = "en") -> str:
        return export_mod.s("this_browser", lang) if self.local else self.person_id


def identify(request: Request) -> Identity:
    email = person_from_iap(request.headers.get(IAP_HEADER))
    if email:
        return Identity(email, local=False, new_cookie=False)
    pid = person_from_cookie(request.cookies.get(COOKIE_NAME))
    if pid:
        return Identity(pid, local=True, new_cookie=False)
    return Identity(new_local_id(), local=True, new_cookie=True)


def _set_cookie(request: Request, response: Response, ident: Identity) -> None:
    """(Re)issue the browser cookie; sliding 30-day Max-Age. Not set behind IAP."""
    if not ident.local:
        return
    response.set_cookie(COOKIE_NAME, ident.person_id, max_age=COOKIE_MAX_AGE, path="/",
                        samesite="lax", httponly=True, secure=request.url.scheme == "https")


def _error(e: LogbookError, request: Request, ident: Identity) -> JSONResponse:
    resp = JSONResponse({"detail": e.message}, status_code=e.status)
    _set_cookie(request, resp, ident)
    return resp


def _summary(ident: Identity, tool: str | None, since: str | None, lang: str) -> dict:
    f = store.folded(ident.person_id)
    entries = f.newest_first()
    total = len(entries)
    if tool:
        entries = [e for e in entries if e.get("tool") == tool]
    since_dt = parse_ts(since) if since else None
    if since_dt:
        entries = [e for e in entries if (parse_ts(e.get("updated_ts")) or since_dt) > since_dt]
    exp = store.expires_at(f)
    return {
        "person": {"id_label": ident.label(lang), "local": ident.local},
        "retention_h": store.retention_h,
        "max_age_h": store.max_age_h,
        "expires_at": iso(exp) if exp else None,
        "last_write": iso(f.last_write) if f.last_write else None,
        "last_download": iso(f.last_download) if f.last_download else None,
        "entries": entries,
        "count": len(entries),
        # Extras for the UI (not in the spec table; additive):
        "total": total,          # entries across every tool, ignoring filters
        "unsaved": f.unsaved,    # added or edited since the last download
    }


def _lang(value: str | None) -> str:
    return value if value in LANGS else "en"


@router.get("")
def get_logbook(request: Request, response: Response,
                tool: str | None = Query(None), since: str | None = Query(None),
                lang: str | None = Query(None)):
    ident = identify(request)
    _set_cookie(request, response, ident)
    return _summary(ident, tool, since, _lang(lang))


@router.delete("")
def delete_logbook(request: Request, response: Response):
    ident = identify(request)
    _set_cookie(request, response, ident)
    store.delete_all(ident.person_id)
    return {"ok": True}


@router.post("/entries")
def add_entry(request: Request, response: Response, body: Any = Body(...)):
    ident = identify(request)
    try:
        entry = store.add(ident.person_id, body)
    except LogbookError as e:
        return _error(e, request, ident)
    _set_cookie(request, response, ident)
    return entry


@router.patch("/entries/{entry_id}")
def edit_entry(entry_id: str, request: Request, response: Response, body: Any = Body(...)):
    ident = identify(request)
    try:
        if not isinstance(body, dict):
            raise LogbookError(400, "body must be {text}")
        entry = store.edit(ident.person_id, entry_id, body.get("text"))
    except LogbookError as e:
        return _error(e, request, ident)
    _set_cookie(request, response, ident)
    return entry


@router.delete("/entries/{entry_id}")
def delete_entry(entry_id: str, request: Request, response: Response):
    ident = identify(request)
    try:
        store.delete(ident.person_id, entry_id)
    except LogbookError as e:
        return _error(e, request, ident)
    _set_cookie(request, response, ident)
    return {"ok": True}


@router.get("/export")
def export_logbook(request: Request, format: str = Query("md"), lang: str | None = Query(None)):
    ident = identify(request)
    fmt = format if format in export_mod.RENDERERS else None
    if fmt is None:
        return _error(LogbookError(400, "format must be md, html or json"), request, ident)
    lg = _lang(lang)
    now = now_utc()
    f = store.folded(ident.person_id)
    render, media = export_mod.RENDERERS[fmt]
    text = render(entries=list(f.entries.values()), person_label=ident.label(lg), exported_at=now,
                  expires_at=store.expires_at(f), retention_h=store.retention_h, lang=lg,
                  lookup=ws_mod.lookup())
    store.mark_downloaded(ident.person_id, fmt, now=now)
    name = f"c2o-logbook-{now.strftime('%Y%m%d-%H%M')}.{fmt}"
    resp = Response(content=text.encode("utf-8"), media_type=media, headers={
        "Content-Disposition": f'attachment; filename="{name}"',
        "Cache-Control": "no-store",
    })
    _set_cookie(request, resp, ident)
    return resp


@router.get("/worksheets")
def get_worksheets(request: Request, response: Response,
                   tool: str | None = Query(None), context: str | None = Query(None),
                   lang: str | None = Query(None), all: int = Query(0)):
    ident = identify(request)
    _set_cookie(request, response, ident)
    tool = tool if tool in TOOLS else TOOL
    try:
        ctx = json.loads(context) if context else {}
    except json.JSONDecodeError:
        ctx = {}
    if not isinstance(ctx, dict):
        ctx = {}
    lg = _lang(lang)
    sheets = ws_mod.for_context(tool, ctx, lg, include_all=bool(all))
    # Which questions this person has already answered (entry ids, newest first).
    answered: dict[str, dict[str, list[str]]] = {}
    for e in fold(store.read_records(ident.person_id)).newest_first():
        w = e.get("worksheet") or {}
        if e.get("kind") == "worksheet" and w.get("id"):
            answered.setdefault(str(w["id"]), {}).setdefault(str(w.get("q")), []).append(e["id"])
    for s in sheets:
        s["answered"] = answered.get(s["id"], {})
    return {"tool": tool, "lang": lg, "context": ctx, "worksheets": sheets}
