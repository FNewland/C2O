"""Participant logbook and course worksheets (docs/plan_2026-11/LOGBOOK_SPEC.md).

Private to the participant: entries are kept on the ground server for
``SMO_LOGBOOK_RETENTION_H`` (48 h) after the person's last write and never
longer than ``SMO_LOGBOOK_MAX_AGE_H`` (168 h); the person downloads them as
Markdown or printable HTML. The browser panel is ``smo_common/ui/logbook.js``.
"""
from .identity import Identity, identify
from .store import KINDS, TOOLS, LogbookError, LogbookStore, default_store_dir
from .worksheets import WorksheetCatalog, default_worksheets_dir


def register_logbook_routes(app, tool, store_dir=None, **kw):
    """Mount ``/api/logbook`` on an aiohttp app (lazy import: aiohttp)."""
    from .aiohttp_routes import register_logbook_routes as _reg
    return _reg(app, tool, store_dir, **kw)


__all__ = ["Identity", "KINDS", "LogbookError", "LogbookStore", "TOOLS",
           "WorksheetCatalog", "default_store_dir", "default_worksheets_dir",
           "identify", "register_logbook_routes"]
