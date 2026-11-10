"""Complete project file: export one study as a JSON document and import it as a new study.

Format (``FORMAT`` / ``VERSION`` 2)::

    {"format": "spacecdf-project", "version": 2, "exported_at": "...",
     "generator": {"app": "SpaceCDF", "version": "2.0.0"},
     "study":   {"id": "<old id>", "name": "..."},
     "tables":  {"<table>": [ {<column>: <value>, ...}, ... ], ...},   # every study-owned row
     "globals": {"parameter_definitions": [...]},                        # shared rows the study uses
     "files":   {"analysis/<run id>.json": <series JSON>, ...},          # state kept on disk
     "logbook": [ <entry>, ... ],      # the exporting person's entries tagged with this study
     "state":   {"fresh_analysis_runs": [<run id>, ...]}}

**Which tables.** The list is derived from the ORM metadata (``Base.metadata``), not written
by hand: a table belongs to a study when it has a ``study_id`` column, or (for tables without
one) a foreign key to a table that belongs to a study (``function_ports`` → ``functions``,
``mode_elements`` → ``design_elements``, ``parameter_edits`` → ``sessions`` …). A new table is
therefore exported automatically; ``tests/test_project_file.py`` fails if a table is neither
exported nor listed in ``GLOBAL_TABLES`` / ``EXCLUDED_TABLES``. Rows are copied column for
column (soft-deleted and rejected rows included: they stop the rules re-proposing them).

**Import** creates a NEW study in one database transaction. Every primary key gets a new id and
every reference is rewritten with the same map: declared foreign keys, undeclared id columns
(``bus_id``, ``from_mode_id``, ``source_id`` …) and ids inside JSON columns and composite strings
(requirement parent links, trace links, interface endpoints, ``monitor:<element id>:…`` keys,
``analysis/<run id>.json``, layout placements …) — any string equal to an exported id, or
containing one between non-alphanumeric characters, is rewritten. Rows whose ids the design
rules derive from the study id (electrical rows, CDR rows) get the id the rules would compute in
the new study, so a later "Propose" updates them instead of adding duplicates. The rows are
written straight to the database: no element/interface/requirement route runs, so the link
proposer and the interface-requirement generator are never triggered (no duplication).
The in-memory caches (studies, elements, interfaces, requirements, stack layouts, budget
allocations, seats) are then filled for the new study.

Hashes over ids are re-stamped where the source was current: interface agreements, electrical
and CDR rule hashes, and analysis runs that were fresh when exported (``state``).

**Version 1** (the old browser-built Save file ``{studyId, elements, interfaces, requirements,
allocations, studyMetadata, riskRegister, pughMatrix, uiState}`` and the old "Full Study Export"
``{studyId, elements, interfaces, requirements}``) is converted to version 2 and imported the same
way, so old files still open — without duplicates and with requirement parents remapped (links
to rows that are not in the file are dropped). It restores what those files held, nothing more.
"""
from __future__ import annotations

import json
import logging
import math
import re
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Integer, DateTime, Table, insert, literal_column, select

from ..db.engine import get_session_factory
from ..db.models import Base

logger = logging.getLogger(__name__)

FORMAT = "spacecdf-project"
VERSION = 2

#: Tables shared by every study. Rows the study references are exported under ``globals`` and
#: matched by their natural key on import (never duplicated, never remapped).
GLOBAL_TABLES: dict[str, str] = {
    # parameter catalogue (ECSS-E-TM-10-25 ParameterType); unique by name, seeded at start-up
    "parameter_definitions": "name",
}

#: Tables deliberately left out of the project file, each with the reason. Everything transient
#: (WebSocket presence and edit locks, seat heartbeats, compliance trackers, the legacy
#: ``_mode_elements`` list) lives only in memory and never reaches the database, so no database
#: table is excluded today. Add a table here only with a comment saying why it is transient.
EXCLUDED_TABLES: dict[str, str] = {}

#: Integer references the schema does not declare as foreign keys: (table, column) → table.
UNDECLARED_INT_REFS: dict[tuple[str, str], str] = {
    ("design_states", "parent_snapshot_id"): "design_states",
}

_TOKEN = re.compile(r"[0-9A-Za-z][0-9A-Za-z_-]*")
_SEP = re.compile(r"([-_])")
_HEX_TAIL = re.compile(r"^(.*?)([0-9a-f]{8,})$")
_FLOAT_MARK = "__float__"
_CHUNK = 400


class ProjectFileError(Exception):
    """A document the importer refuses; ``status`` is the HTTP status to answer."""

    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status
        self.message = message


# ═══════════════════════════════════════════════════════════════════════
# Table plan (derived from the ORM metadata)
# ═══════════════════════════════════════════════════════════════════════

def _tables() -> list[Table]:
    import spacecdf_server.db.models  # noqa: F401  (registers every model module)
    return list(Base.metadata.sorted_tables)


def _int_pk(t: Table) -> str | None:
    pks = list(t.primary_key.columns)
    if len(pks) == 1 and isinstance(pks[0].type, Integer):
        return pks[0].key
    return None


def _pk(t: Table) -> str:
    return list(t.primary_key.columns)[0].key


def _fk_targets(t: Table) -> dict[str, tuple[str, str]]:
    """column → (referenced table, referenced column) for declared foreign keys."""
    out: dict[str, tuple[str, str]] = {}
    for c in t.columns:
        for fk in c.foreign_keys:
            out[c.key] = (fk.column.table.name, fk.column.key)
    return out


def study_tables() -> list[str]:
    """Names of the tables whose rows belong to one study, in dependency order."""
    owned: list[str] = []
    for t in _tables():
        name = t.name
        if name in GLOBAL_TABLES or name in EXCLUDED_TABLES:
            continue
        if name == "studies" or "study_id" in t.columns:
            owned.append(name)
            continue
        if any(ref in owned and ref != name for ref, _ in _fk_targets(t).values()):
            owned.append(name)
    return owned


def unclassified_tables() -> list[str]:
    """Tables that are neither exported, global nor excluded (should be empty)."""
    known = set(study_tables()) | set(GLOBAL_TABLES) | set(EXCLUDED_TABLES)
    return sorted(t.name for t in _tables() if t.name not in known)


# ═══════════════════════════════════════════════════════════════════════
# Value encoding
# ═══════════════════════════════════════════════════════════════════════

def _enc(v: Any) -> Any:
    """Make a column value JSON-safe (datetimes → ISO, non-finite floats → marker)."""
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, float) and not math.isfinite(v):
        return {_FLOAT_MARK: repr(v)}
    if isinstance(v, dict):
        return {k: _enc(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_enc(x) for x in v]
    return v


def _dec(v: Any) -> Any:
    if isinstance(v, dict):
        if len(v) == 1 and _FLOAT_MARK in v:
            return float(v[_FLOAT_MARK])
        return {k: _dec(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_dec(x) for x in v]
    return v


def _to_column(t: Table, key: str, v: Any) -> Any:
    v = _dec(v)
    col = t.columns[key]
    if isinstance(col.type, DateTime) and isinstance(v, str):
        try:
            return datetime.fromisoformat(v)
        except ValueError:
            return None
    return v


# ═══════════════════════════════════════════════════════════════════════
# Export
# ═══════════════════════════════════════════════════════════════════════

_ROWID = "__rowid"


def _sel(t: Table, sqlite: bool):
    """``select(t)``, plus SQLite's rowid so rows keep the order they were written in."""
    return select(t, literal_column(f"{t.name}.rowid").label(_ROWID)) if sqlite else select(t)


async def _select_in(session, t: Table, col: str, values: list, sqlite: bool = False) -> list:
    rows: list = []
    for i in range(0, len(values), _CHUNK):
        chunk = values[i:i + _CHUNK]
        rows += (await session.execute(_sel(t, sqlite).where(t.c[col].in_(chunk)))).mappings().all()
    return rows


def _write_order(t: Table, rows: list[dict], sqlite: bool) -> list[dict]:
    """Rows in the order they were written (lists in the UI follow it); rowid on SQLite,
    else ``created_at`` then the key."""
    if sqlite:
        rows = sorted(rows, key=lambda r: r.get(_ROWID) or 0)
        for r in rows:
            r.pop(_ROWID, None)
        return rows
    pk = _pk(t)
    if "created_at" in t.columns:
        return sorted(rows, key=lambda r: (str(r.get("created_at") or ""), str(r.get(pk))))
    return sorted(rows, key=lambda r: str(r.get(pk)))


async def collect_rows(study_id: str) -> dict[str, list[dict]]:
    """Every row of every study-owned table, as plain column dicts (raw values), in write order."""
    tables = {t.name: t for t in _tables()}
    out: dict[str, list[dict]] = {}
    pks: dict[str, list] = {}
    async with get_session_factory()() as s:
        sqlite = s.bind.dialect.name == "sqlite"
        for name in study_tables():
            t = tables[name]
            fks = {c: ref for c, ref in _fk_targets(t).items() if ref[0] != name and ref[0] in pks}
            found: dict[Any, dict] = {}
            pk = _pk(t)
            if name == "studies":
                rows = (await s.execute(_sel(t, sqlite).where(t.c.id == study_id))).mappings().all()
            elif "study_id" in t.columns:
                rows = (await s.execute(_sel(t, sqlite).where(t.c.study_id == study_id))).mappings().all()
                if t.c.study_id.nullable and fks:
                    # legacy rows that only reach the study through a parent (design_states → sessions)
                    for col, (ref, _) in fks.items():
                        for r in await _select_in(s, t, col, pks[ref], sqlite):
                            if r["study_id"] is None:
                                found[r[pk]] = dict(r)
            else:
                rows = []
                for col, (ref, _) in fks.items():
                    rows += await _select_in(s, t, col, pks[ref], sqlite)
            for r in rows:
                found[r[pk]] = dict(r)
            ordered = _write_order(t, list(found.values()), sqlite)
            out[name] = ordered
            pks[name] = [r[pk] for r in ordered]
    return out


async def _fresh_runs(study_id: str, runs: list[dict]) -> list[str]:
    """Analysis runs whose inputs hash matches the live context (not stale)."""
    if not runs:
        return []
    from .analysis_context import build_context, context_hash
    from .analysis_results import input_keys_for
    ctxs: dict[Any, Any] = {}
    fresh: list[str] = []
    for r in runs:
        if not r.get("inputs_hash"):
            continue
        opt = r.get("option_id")
        try:
            if opt not in ctxs:
                ctxs[opt] = await build_context(study_id, option_id=opt)
            if context_hash(ctxs[opt], input_keys_for(r["analysis"])) == r["inputs_hash"]:
                fresh.append(r["id"])
        except Exception:  # noqa: BLE001 - a run we cannot judge is simply not re-stamped
            logger.debug("freshness of run %s not known", r.get("id"), exc_info=True)
    return fresh


def _logbook_entries(person_id: str | None, study_id: str) -> list[dict]:
    if not person_id:
        return []
    try:
        from ..logbook.router import store
        entries = store.folded(person_id).newest_first()
    except Exception:  # noqa: BLE001
        logger.debug("logbook not readable", exc_info=True)
        return []
    mine = [e for e in entries if (e.get("context") or {}).get("study_id") == study_id]
    return list(reversed(mine))          # oldest first, the order they were written


async def export_study(study_id: str, *, person_id: str | None = None) -> dict:
    """The complete project document of one study (raises ``ProjectFileError`` 404)."""
    from ..routers.studies import get_study_store
    from .analysis_results import load_series

    rows = await collect_rows(study_id)
    if not rows.get("studies"):
        raise ProjectFileError(f"Study {study_id} not found", 404)
    st = rows["studies"][0]
    cached = get_study_store().get(study_id)
    if cached is not None:
        # the in-memory Study is the read path every route uses; the row mirrors it
        st["meta_json"] = cached.model_dump(mode="json")
        st["name"] = cached.name

    globals_: dict[str, list[dict]] = {}
    defs_used = sorted({r["definition_id"] for r in rows.get("element_parameters", []) if r.get("definition_id")})
    if defs_used:
        t = {x.name: x for x in _tables()}["parameter_definitions"]
        async with get_session_factory()() as s:
            globals_["parameter_definitions"] = [dict(r) for r in await _select_in(s, t, "id", defs_used)]

    files: dict[str, Any] = {}
    for r in rows.get("analysis_runs", []):
        ref = r.get("series_ref")
        if ref:
            data = load_series(ref)
            if data is not None:
                files[ref] = data

    fresh = await _fresh_runs(study_id, rows.get("analysis_runs", []))

    return {
        "format": FORMAT,
        "version": VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "generator": {"app": "SpaceCDF", "version": "2.0.0"},
        "study": {"id": study_id, "name": st.get("name")},
        "tables": {name: [_enc(r) for r in rs] for name, rs in rows.items()},
        "globals": {name: [_enc(r) for r in rs] for name, rs in globals_.items()},
        "files": _enc(files),
        "logbook": _enc(_logbook_entries(person_id, study_id)),
        "state": {"fresh_analysis_runs": fresh},
    }


# ═══════════════════════════════════════════════════════════════════════
# Version 1 (browser-built Save file) → version 2
# ═══════════════════════════════════════════════════════════════════════

def is_v1(doc: Any) -> bool:
    return isinstance(doc, dict) and "format" not in doc and isinstance(doc.get("elements"), list)


def _api_to_columns(t: Table, d: dict, skip: tuple[str, ...] = ()) -> dict:
    """An API dict (``performance``, ``properties`` …) → column dict (``performance_json`` …)."""
    alias = {"dimensions_mm": "dimensions_json"}
    out: dict[str, Any] = {}
    for k, v in d.items():
        if k in skip or k == "children":
            continue
        col = alias.get(k) or (k + "_json" if (k + "_json") in t.columns else k)
        if col in t.columns and col not in out:
            out[col] = v
    return out


def convert_v1(doc: dict) -> dict:
    """Version-1 Save / Full Study Export file → a version-2 document (ids still the old ones)."""
    from spacecdf_common.models.study import Study
    tables = {t.name: t for t in _tables()}
    old_sid = str(doc.get("studyId") or "v1-study")
    meta = doc.get("studyMetadata") if isinstance(doc.get("studyMetadata"), dict) else None
    if meta is None:
        meta = Study(id=old_sid, name="Loaded Mission").model_dump(mode="json")
        meta["requirements"]["name"] = "Loaded Mission"
    meta = dict(meta)
    meta["id"] = old_sid
    if doc.get("riskRegister") and not meta.get("risk_register"):
        meta["risk_register"] = doc["riskRegister"]
    if doc.get("pughMatrix") and not (meta.get("trade_records") or {}).get("pugh"):
        meta.setdefault("trade_records", {})
        meta["trade_records"] = {**(meta.get("trade_records") or {}), "pugh": {"state": doc["pughMatrix"]}}
    name = meta.get("name") or "Loaded Mission"

    def rows(key: str, table: str, skip: tuple[str, ...] = ()) -> list[dict]:
        out = []
        for d in doc.get(key) or []:
            if isinstance(d, dict):
                r = _api_to_columns(tables[table], d, skip)
                r["study_id"] = old_sid
                out.append(r)
        return out

    reqs = rows("requirements", "requirements", ("created_at", "updated_at"))
    for r in reqs:
        tv = r.get("threshold_value")
        if tv is not None and not isinstance(tv, str):
            r["threshold_value"] = json.dumps(tv)
    allocs = []
    for a in doc.get("allocations") or []:
        if isinstance(a, dict) and a.get("element_id") and a.get("budget_type"):
            allocs.append({"study_id": old_sid, "element_id": a["element_id"], "budget_type": a["budget_type"],
                           "allocation_value": a.get("allocation_value") or 0.0, "unit": a.get("unit") or "",
                           "source": a.get("source") or "manual", "rationale": a.get("rationale") or ""})
    return {
        "format": FORMAT, "version": VERSION, "converted_from": 1,
        "study": {"id": old_sid, "name": name},
        "tables": {
            "studies": [{"id": old_sid, "name": name, "meta_json": meta}],
            "design_elements": rows("elements", "design_elements", ("created_at", "updated_at", "margin_percent")),
            "element_interfaces": rows("interfaces", "element_interfaces", ("type", "created_at", "updated_at")),
            "requirements": reqs,
            "budget_allocations": allocs,
        },
        "globals": {}, "files": {}, "logbook": [], "state": {},
        "ui": doc.get("uiState") if isinstance(doc.get("uiState"), dict) else None,
    }


# ═══════════════════════════════════════════════════════════════════════
# Id remapping
# ═══════════════════════════════════════════════════════════════════════

class IdMap:
    """old id → new id for every string primary key, plus string rewriting."""

    def __init__(self, old_sid: str, new_sid: str):
        self.old_sid, self.new_sid = old_sid, new_sid
        self.ids: dict[str, str] = {old_sid: new_sid}

    def new_for(self, old: str) -> str:
        """A fresh id shaped like ``old``."""
        if old == self.old_sid:
            return self.new_sid
        sub = self._tokens(old, {self.old_sid: self.new_sid})
        if sub != old:                                    # ref-<study id>-… : follows the study
            return sub
        m = _HEX_TAIL.match(old)
        if m:
            n = len(m.group(2))
            return m.group(1) + (uuid.uuid4().hex * 2)[:n]
        return f"{old}-{uuid.uuid4().hex[:8]}"

    def _tokens(self, s: str, table: dict[str, str]) -> str:
        def one(m: re.Match) -> str:
            tok = m.group(0)
            hit = table.get(tok)
            if hit is not None:
                return hit
            parts = _SEP.split(tok)              # [seg, sep, seg, …]
            segs = parts[0::2]
            if len(segs) < 2:
                return tok
            out: list[str] = []
            i, n = 0, len(segs)
            while i < n:
                done = False
                for j in range(n, i, -1):
                    span = "".join(parts[2 * i:2 * j - 1])
                    if len(span) >= 8 and span in table:
                        out.append(table[span])
                        if j < n:
                            out.append(parts[2 * j - 1])
                        i, done = j, True
                        break
                if not done:
                    out.append(segs[i])
                    if i < n - 1:
                        out.append(parts[2 * i + 1])
                    i += 1
            return "".join(out)

        return _TOKEN.sub(one, s)

    def str(self, s: str) -> str:
        hit = self.ids.get(s)
        if hit is not None:
            return hit
        if len(s) < 8:
            return s
        return self._tokens(s, self.ids)

    def value(self, v: Any) -> Any:
        if isinstance(v, str):
            return self.str(v)
        if isinstance(v, dict):
            return {(self.str(k) if isinstance(k, str) else k): self.value(x) for k, x in v.items()}
        if isinstance(v, list):
            return [self.value(x) for x in v]
        return v


def _fake_row(t: Table, row: dict) -> Any:
    """An object with ``__table__`` and column attributes, for the repos' ``row_to_dict``."""
    class _R:  # noqa: D401 - tiny adapter
        __table__ = t
    r = _R()
    for c in t.columns:
        setattr(r, c.key, row.get(c.key))
    return r


def _det_ids(tables_rows: dict[str, list[dict]], idm: IdMap) -> None:
    """Rows whose id the rules derive from the study id: compute the id they get in the new study.

    Each candidate is verified against the old id first, so a user-created row (random id) keeps
    its random new id."""
    try:
        from .electrical_rules import det_id as edet, _fmt
        from .cdr_model import det_id as cdet
    except Exception:  # noqa: BLE001
        logger.debug("deterministic id helpers unavailable", exc_info=True)
        return
    old, new = idm.old_sid, idm.new_sid
    m = idm.str
    element_ids = [r["id"] for r in tables_rows.get("design_elements", [])]

    def settle(kind: str, row: dict, candidates: list[tuple]) -> None:
        for parts in candidates:
            if edet(kind, old, *parts) == row["id"]:
                idm.ids[row["id"]] = edet(kind, new, *[m(p) if isinstance(p, str) else p for p in parts])
                return

    for r in tables_rows.get("power_rails", []):
        settle("rails", r, [(r.get("eps_element_id"), r.get("voltage_v"))])
    for r in tables_rows.get("power_lines", []):
        settle("lines", r, [(r.get("eps_element_id"), lid) for lid in (r.get("load_element_ids_json") or [])])
    for r in tables_rows.get("data_buses", []):
        segs = [r.get("segment")] + element_ids
        settle("buses", r, [(r.get("master_element_id"), r.get("protocol"), sg) for sg in segs])
    for r in tables_rows.get("bus_nodes", []):          # after buses: the parts hold the bus id
        settle("nodes", r, [(r.get("bus_id"), r.get("element_id"))])
    for r in tables_rows.get("element_ports", []):
        props = r.get("properties_json") or {}
        quals = ["power"]
        if props.get("rail_voltage") is not None:
            try:
                quals.append(_fmt(float(props["rail_voltage"])))
            except Exception:  # noqa: BLE001
                pass
        quals += [str(props[k]) for k in ("protocol", "band") if props.get(k) is not None]
        quals += ["data", "rf", "mechanical", "thermal", "timing", "optical", "fluid", "electrical_signal", "power"]
        settle("ports", r, [(r.get("element_id"), r.get("kind"), q) for q in dict.fromkeys(quals)])
    for r in tables_rows.get("cdr_rows", []):
        key = r.get("key") or ""
        if cdet(old, r.get("kind"), key) == r["id"]:
            idm.ids[r["id"]] = cdet(new, r.get("kind"), m(key))


# ═══════════════════════════════════════════════════════════════════════
# Import
# ═══════════════════════════════════════════════════════════════════════

def _topo(rows: list[dict], pk: str, self_cols: list[str]) -> list[dict]:
    """Parents before children for self-referencing tables."""
    if not self_cols:
        return rows
    by_id = {r[pk]: r for r in rows}
    done: set = set()
    out: list[dict] = []

    def visit(r: dict, depth: int = 0) -> None:
        if r[pk] in done or depth > 1000:
            return
        for c in self_cols:
            p = r.get(c)
            if p is not None and p in by_id and p != r[pk]:
                visit(by_id[p], depth + 1)
        if r[pk] not in done:
            done.add(r[pk])
            out.append(r)

    for r in rows:
        visit(r)
    return out


def _check_doc(doc: Any) -> dict:
    if not isinstance(doc, dict):
        raise ProjectFileError("A project file is a JSON object.")
    if is_v1(doc):
        return convert_v1(doc)
    if doc.get("format") != FORMAT:
        raise ProjectFileError("This is not a SpaceCDF project file.")
    v = doc.get("version")
    if not isinstance(v, int) or v < 2:
        raise ProjectFileError(f"Unsupported project file version {v!r}.")
    if v > VERSION:
        raise ProjectFileError(f"This project file was written by a newer SpaceCDF (format version {v}); "
                               f"this server reads up to version {VERSION}.")
    if not isinstance(doc.get("tables"), dict) or not doc["tables"].get("studies"):
        raise ProjectFileError("The project file holds no study.")
    return doc


async def import_study(doc: Any, *, person_id: str | None = None, include_id_map: bool = False) -> dict:
    """Create a new study from a project document. Returns ``{id, name, counts, warnings, ui}``."""
    from spacecdf_common.models.study import Study

    doc = _check_doc(doc)
    tables = {t.name: t for t in _tables()}
    src = {name: [dict(r) for r in (rows or []) if isinstance(r, dict)]
           for name, rows in doc["tables"].items()}
    unknown = sorted(set(src) - set(tables))
    warnings: list[str] = [f"table {n} is not known to this server; its rows were skipped" for n in unknown]
    owned = [n for n in study_tables() if n in src]

    old_sid = str(src["studies"][0].get("id") or "")
    if not old_sid:
        raise ProjectFileError("The study row has no id.")
    new_sid = str(uuid.uuid4())[:8]
    idm = IdMap(old_sid, new_sid)

    # 1. new ids for every string primary key (study id first, then the rest)
    int_tables = {n for n in owned if _int_pk(tables[n])}
    for name in owned:
        if name in int_tables:
            continue
        pk = _pk(tables[name])
        for r in src[name]:
            old = r.get(pk)
            if isinstance(old, str) and old and old not in idm.ids:
                idm.ids[old] = idm.new_for(old)
    _det_ids(src, idm)

    # 2. global rows the study uses (matched by natural key)
    gdefs = [dict(r) for r in ((doc.get("globals") or {}).get("parameter_definitions") or []) if isinstance(r, dict)]

    # 3. rewrite every row
    new_ids = set(idm.ids.values())
    out: dict[str, list[dict]] = {}
    for name in owned:
        t = tables[name]
        fks = _fk_targets(t)
        new_rows = []
        for r in src[name]:
            row: dict[str, Any] = {}
            drop = False
            for k, v in r.items():
                if k not in t.columns:
                    continue
                if isinstance(v, (str, dict, list)):
                    v = idm.value(_dec(v))
                ref = fks.get(k)
                if ref and isinstance(v, str) and ref[0] in src and ref[0] not in GLOBAL_TABLES \
                        and not _int_pk(tables[ref[0]]) and v not in new_ids:
                    # dangling reference into a row that is not in the file (v1: old study's ids)
                    if t.columns[k].nullable:
                        v = None
                    else:
                        drop = True
                row[k] = v
            if drop:
                warnings.append(f"{name}: a row referring to a missing record was skipped")
                continue
            if "study_id" in t.columns and name != "studies" and row.get("study_id") is None \
                    and not t.columns["study_id"].nullable:
                row["study_id"] = new_sid
            new_rows.append(row)
        out[name] = new_rows

    st = out["studies"][0]
    st["id"] = new_sid
    meta = st.get("meta_json") or {}
    meta["id"] = new_sid
    try:
        study = Study(**meta)
    except Exception as exc:  # noqa: BLE001
        raise ProjectFileError(f"The study in the file is not valid: {exc}") from exc
    st["meta_json"] = study.model_dump(mode="json")
    st["name"] = study.name

    # 4. hashes over ids: re-stamp where the source was current
    _restamp_hashes(src, out, tables, idm)

    # 5. one transaction
    int_map: dict[str, dict[int, int]] = defaultdict(dict)
    counts: dict[str, int] = {}
    try:
        async with get_session_factory()() as s:
            async with s.begin():
                if gdefs:
                    await _merge_definitions(s, tables["parameter_definitions"], gdefs, out)
                for name in owned:
                    t = tables[name]
                    rows = out[name]
                    pk = _pk(t)
                    fks = _fk_targets(t)
                    self_cols = [c for c, (ref, _) in fks.items() if ref == name]
                    rows = _topo(rows, pk, self_cols)
                    int_cols = {c: ref for c, (ref, _) in fks.items() if _int_pk(tables[ref])}
                    int_cols.update({c: ref for (tn, c), ref in UNDECLARED_INT_REFS.items() if tn == name})
                    ipk = _int_pk(t)
                    if ipk:
                        rows = sorted(rows, key=lambda r: (r.get(ipk) is None, r.get(ipk) or 0))
                    for r in rows:
                        vals = {k: _to_column(t, k, v) for k, v in r.items()}
                        for c, ref in int_cols.items():
                            if vals.get(c) is not None:
                                vals[c] = int_map[ref].get(vals[c])
                        if ipk:
                            old = vals.pop(ipk, None)
                            res = await s.execute(insert(t).values(**vals))
                            if old is not None:
                                int_map[name][old] = res.inserted_primary_key[0]
                    if not ipk:
                        batch = [{k: _to_column(t, k, v) for k, v in r.items()} for r in rows]
                        groups: dict[tuple, list[dict]] = defaultdict(list)
                        for b in batch:
                            groups[tuple(sorted(b))].append(b)
                        for g in groups.values():
                            for i in range(0, len(g), 500):
                                await s.execute(insert(t), g[i:i + 500])
                    counts[name] = len(rows)
    except ProjectFileError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("project import failed")
        raise ProjectFileError(f"The project could not be imported: {exc}", 500) from exc

    # 6. state on disk, caches, logbook, fresh analysis runs
    _write_files(doc.get("files") or {}, idm)
    await reload_study_caches(new_sid, study)
    n_log = _import_logbook(person_id, doc.get("logbook") or [], idm)
    if n_log:
        counts["logbook"] = n_log
    fresh = [idm.ids.get(x) for x in ((doc.get("state") or {}).get("fresh_analysis_runs") or [])]
    await _restamp_runs(new_sid, [x for x in fresh if x])

    result = {"id": new_sid, "name": study.name, "counts": counts, "warnings": warnings,
              "converted_from": doc.get("converted_from"),
              "ui": idm.value(doc.get("ui")) if isinstance(doc.get("ui"), dict) else None}
    if include_id_map:
        result["id_map"] = dict(idm.ids)
        result["int_id_map"] = {k: {str(a): b for a, b in v.items()} for k, v in int_map.items()}
    return result


async def _merge_definitions(s, t: Table, defs: list[dict], out: dict[str, list[dict]]) -> None:
    """Insert the parameter definitions this server lacks; repoint ids that differ by name."""
    remap: dict[str, str] = {}
    for d in defs:
        name, did = d.get("name"), d.get("id")
        if not name or not did:
            continue
        row = (await s.execute(select(t).where(t.c.name == name))).mappings().first()
        if row is not None:
            if row["id"] != did:
                remap[did] = row["id"]
            continue
        taken = (await s.execute(select(t.c.id).where(t.c.id == did))).first()
        if taken is not None:
            new_id = f"{did}-{uuid.uuid4().hex[:6]}"
            remap[did] = new_id
            d = {**d, "id": new_id}
        await s.execute(insert(t).values(**{k: _to_column(t, k, v) for k, v in d.items() if k in t.columns}))
    if remap:
        for r in out.get("element_parameters", []):
            if r.get("definition_id") in remap:
                r["definition_id"] = remap[r["definition_id"]]


def _restamp_hashes(src: dict[str, list[dict]], out: dict[str, list[dict]], tables: dict[str, Table],
                    idm: IdMap) -> None:
    """Re-stamp hashes computed over ids, where the stored hash matched its source row."""
    # interface agreements (design rule IF-05): hash over type, subtype, endpoints, direction
    try:
        from .interface_requirements import agreement_hash
        from ..db.element_repo import _interface_row_to_dict
        t = tables["element_interfaces"]
        for old, new in zip(src.get("element_interfaces", []), out.get("element_interfaces", [])):
            ag_old, ag_new = old.get("agreement_json"), new.get("agreement_json")
            if not isinstance(ag_old, dict) or not ag_old.get("inputs_hash") or not isinstance(ag_new, dict):
                continue
            if ag_old["inputs_hash"] == agreement_hash(_interface_row_to_dict(_fake_row(t, _dec(old)))):
                ag_new["inputs_hash"] = agreement_hash(_interface_row_to_dict(_fake_row(t, new)))
    except Exception:  # noqa: BLE001
        logger.debug("agreement hashes not re-stamped", exc_info=True)
    # electrical rule rows
    try:
        from .electrical_rules import inputs_hash as ehash
        from ..db.electrical_repo import row_to_dict as erow
        for table, kind in (("power_rails", "rails"), ("power_lines", "lines"), ("data_buses", "buses"),
                            ("bus_nodes", "nodes"), ("element_ports", "ports")):
            t = tables[table]
            for old, new in zip(src.get(table, []), out.get(table, [])):
                if old.get("inputs_hash") and old["inputs_hash"] == ehash(kind, erow(_fake_row(t, _dec(old)))):
                    new["inputs_hash"] = ehash(kind, erow(_fake_row(t, new)))
    except Exception:  # noqa: BLE001
        logger.debug("electrical hashes not re-stamped", exc_info=True)
    # CDR rows: hash over key + data
    try:
        from .cdr_model import inputs_hash as chash
        from ..db.cdr_repo import row_to_dict as crow
        t = tables["cdr_rows"]
        for old, new in zip(src.get("cdr_rows", []), out.get("cdr_rows", [])):
            if old.get("inputs_hash") and old["inputs_hash"] == chash(crow(_fake_row(t, _dec(old)))):
                new["inputs_hash"] = chash(crow(_fake_row(t, new)))
    except Exception:  # noqa: BLE001
        logger.debug("cdr hashes not re-stamped", exc_info=True)


def _write_files(files: dict, idm: IdMap) -> None:
    from .analysis_results import data_dir
    root = data_dir().resolve()
    for ref, data in files.items():
        if not isinstance(ref, str):
            continue
        new_ref = idm.str(ref)
        path = (root / new_ref).resolve()
        if root not in path.parents:          # never write outside the data directory
            logger.warning("project import: file %s skipped (outside the data directory)", ref)
            continue
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(idm.value(_dec(data)), fh, default=str, separators=(",", ":"))
        except Exception:  # noqa: BLE001
            logger.exception("project import: file %s not written", new_ref)


async def reload_study_caches(sid: str, study: Any = None) -> None:
    """(Re)fill the write-through caches of one study from the database, as a restart would."""
    from ..db.element_repo import _element_row_to_dict, _interface_row_to_dict
    from ..db.models import BudgetAllocationRow, DesignElementRow, ElementInterfaceRow, RequirementRow
    from ..db.requirement_repo import _row_to_dict as req_row_to_dict
    from ..routers import elements as el_router, requirements as req_router, studies as st_router

    from ..db.models import StudyRow
    from spacecdf_common.models.study import Study
    async with get_session_factory()() as s:
        if study is None:
            row = await s.get(StudyRow, sid)
            if row is None:
                return
            study = Study(**row.meta_json)
    st_router.get_study_store()[sid] = study
    el_router._budget_allocations[:] = [a for a in el_router._budget_allocations if a.get("study_id") != sid]
    async with get_session_factory()() as s:
        for row in (await s.execute(select(DesignElementRow).where(
                DesignElementRow.study_id == sid, DesignElementRow.deleted_at.is_(None)))).scalars():
            d = _element_row_to_dict(row)
            el_router._elements[d["id"]] = d
        for row in (await s.execute(select(ElementInterfaceRow).where(
                ElementInterfaceRow.study_id == sid, ElementInterfaceRow.deleted_at.is_(None)))).scalars():
            d = _interface_row_to_dict(row)
            el_router._interfaces[d["id"]] = d
        for row in (await s.execute(select(RequirementRow).where(RequirementRow.study_id == sid))).scalars():
            d = req_row_to_dict(row)
            req_router._requirements[d["id"]] = d
        for row in (await s.execute(select(BudgetAllocationRow).where(BudgetAllocationRow.study_id == sid))).scalars():
            el_router._budget_allocations.append({
                "element_id": row.element_id, "study_id": row.study_id, "budget_type": row.budget_type,
                "allocation_value": row.allocation_value, "unit": row.unit, "source": row.source,
                "rationale": row.rationale})
    try:
        from ..routers import stack as stack_router
        from ..db.models import StackLayoutRow
        async with get_session_factory()() as s:
            row = await s.get(StackLayoutRow, sid)
            if row is not None:
                stack_router._layouts[sid] = {"form_factor": row.form_factor or "", "approved": row.approved_json,
                                              "proposal": row.proposal_json, "version": int(row.version or 0)}
    except Exception:  # noqa: BLE001
        logger.debug("stack cache not refreshed", exc_info=True)
    try:
        from ..seats import store as seat_store
        seat_store._team.pop(sid, None)
        seat_store._loaded.discard(sid)
        await seat_store.get_team(sid)
    except Exception:  # noqa: BLE001
        logger.debug("seat cache not refreshed", exc_info=True)


def _import_logbook(person_id: str | None, entries: list, idm: IdMap) -> int:
    """Write the file's logbook entries into the importing person's logbook (new ids, now)."""
    if not person_id or not entries:
        return 0
    from ..logbook.router import store
    n = 0
    for e in entries:
        if not isinstance(e, dict):
            continue
        payload = {k: idm.value(_dec(e.get(k))) for k in ("tool", "kind", "text", "context", "worksheet",
                                                          "sim_ts", "lang", "record") if e.get(k) is not None}
        try:
            store.add(person_id, payload)
            n += 1
        except Exception as exc:  # noqa: BLE001 - a bad entry must not fail the whole import
            logger.warning("project import: logbook entry skipped: %s", exc)
    return n


async def _restamp_runs(sid: str, run_ids: list[str]) -> None:
    if not run_ids:
        return
    from ..db.models import AnalysisRunRow
    from .analysis_results import current_hash
    for rid in run_ids:
        try:
            async with get_session_factory()() as s:
                row = await s.get(AnalysisRunRow, rid)
                if row is None or row.study_id != sid:
                    continue
                row.inputs_hash = await current_hash(sid, row.analysis, row.option_id)
                await s.commit()
        except Exception:  # noqa: BLE001
            logger.debug("analysis hash not re-stamped for run %s", rid, exc_info=True)


def file_name(name: str | None, when: datetime | None = None) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", name or "study").strip("_")[:60] or "study"
    return f"{slug}_{(when or datetime.now(timezone.utc)).strftime('%Y-%m-%d')}.spacecdf.json"

