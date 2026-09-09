"""Capella project -> SpaceCDF spine (SCDF-160 Phase 2c).

    result = await import_capella_model(study_id, Path("x.capella.zip"))

Reads LA/PA component trees, SA/LA/PA functions (+ ports), component
exchanges (-> ``ElementInterface``), exchange items, functional exchanges,
function allocations, requirements (+ relations) and the
``SpaceCDF.Budgets`` property values, and upserts them into the spine.

Matching order for every entity: ``external_ids['capella']`` == Capella UUID
-> ``SpaceCDF.Meta.spine_id`` (written by our exporter) == an id in this study
-> create.  Elements created from a model without ``SpaceCDF.Meta`` get their
``subsystem_domain`` guessed from the name (:func:`mapping.guess_subsystem_domain`).
"""
from __future__ import annotations

import html
import logging
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import _spine
from ._compat import patch_capellambse
from .exporter import _materialise_base, load_model
from .mapping import (
    BUDGET_GROUP, COMPONENTS_ATTR, META_GROUP, RELATION_KINDS, capella_uuid,
    guess_subsystem_domain,
)

logger = logging.getLogger(__name__)

__all__ = ["ImportResult", "import_capella_model", "read_model_summary"]

_WELL_KNOWN = ("mass_kg", "power_avg_w", "power_peak_w", "cost_nre_keur", "cost_recurring_keur", "volume_cm3")


@dataclass
class ImportResult:
    study_id: str
    created: dict[str, int] = field(default_factory=dict)
    updated: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    #: ``{kind: {capella_uuid: spine_id}}``
    id_map: dict[str, dict[str, str]] = field(default_factory=dict)


# ── model readers ───────────────────────────────────────────────────────

def _pv_group(obj, name: str) -> dict[str, Any]:
    try:
        for g in obj.property_value_groups:
            if g.name == name:
                return {pv.name: pv.value for pv in g.property_values}
    except Exception:
        pass
    return {}


def _meta(obj) -> dict[str, str]:
    return {k: (str(v) if v is not None else "") for k, v in _pv_group(obj, META_GROUP).items()}


def _budgets(obj) -> dict[str, float]:
    out = {}
    for k, v in _pv_group(obj, BUDGET_GROUP).items():
        try:
            out[k] = float(v)
        except (TypeError, ValueError):
            continue
    return out


def _plain(text: Any) -> str:
    s = str(text or "")
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).strip()


def _children(comp, layer: str):
    try:
        return list(getattr(comp, COMPONENTS_ATTR[layer]))
    except Exception:
        return []


def _subfunctions(fn):
    try:
        return list(fn.functions)
    except Exception:
        return []


def _ext_uuid(d: dict) -> str | None:
    ext = d.get("external_ids")
    if isinstance(ext, dict) and ext.get("capella"):
        return str(ext["capella"])
    ext_id = d.get("external_id")
    if isinstance(ext_id, str) and ext_id.startswith("capella:"):
        return ext_id[len("capella:"):]
    return None


class _Importer:
    def __init__(self, study_id: str, model, snap) -> None:
        self.study_id = study_id
        self.model = model
        self.snap = snap
        self.result = ImportResult(study_id=study_id)
        # existing spine entities by capella uuid / by spine id
        self.el_by_uuid = {u: e for e in snap.elements if (u := _ext_uuid(e))}
        self.el_by_id = {e["id"]: e for e in snap.elements}
        self.if_by_uuid = {u: i for i in snap.interfaces if (u := _ext_uuid(i))}
        self.if_by_id = {i["id"]: i for i in snap.interfaces}
        self.fn_by_uuid = {u: f for f in snap.functions if (u := _ext_uuid(f))}
        self.fn_by_id = {f["id"]: f for f in snap.functions}
        self.xi_by_uuid = {u: x for x in snap.exchange_items if (u := _ext_uuid(x))}
        self.xi_by_id = {x["id"]: x for x in snap.exchange_items}
        self.fx_by_uuid = {u: x for x in snap.functional_exchanges if (u := _ext_uuid(x))}
        self.req_by_uuid = {u: r for r in snap.requirements if (u := _ext_uuid(r))}
        self.req_by_id = {r["id"]: r for r in snap.requirements}
        self.req_by_code = {r.get("code"): r for r in snap.requirements if r.get("code")}
        self.port_by_uuid = {capella_uuid(study_id, "function_port", p["id"]): p for p in snap.function_ports}
        self.port_by_key = {(p["function_id"], p.get("direction"), p.get("name")): p for p in snap.function_ports}
        # capella uuid -> spine id (this run)
        self.el_map: dict[str, str] = {}
        self.fn_map: dict[str, str] = {}
        self.function_layer: dict[str, str] = {}
        self.port_map: dict[str, str] = {}
        self.xi_map: dict[str, str] = {}
        self.if_map: dict[str, str] = {}
        self.req_map: dict[str, str] = {}
        # source-study spine ids (from SpaceCDF.Meta) -> ids in this study
        self.src_elements: dict[str, str] = {}

    # -- bookkeeping -----------------------------------------------------
    def _count(self, kind: str, created: bool) -> None:
        bucket = self.result.created if created else self.result.updated
        bucket[kind] = bucket.get(kind, 0) + 1

    def _record(self, kind: str, uuid: str, spine_id: str) -> None:
        self.result.id_map.setdefault(kind, {})[uuid] = spine_id

    # -- exchange items --------------------------------------------------
    async def exchange_items(self) -> None:
        for xi in self.model.search("ExchangeItem"):
            meta = _meta(xi)
            existing = self.xi_by_uuid.get(xi.uuid) or self.xi_by_id.get(meta.get("spine_id", ""))
            kind = meta.get("kind") or "data"
            data = {"name": xi.name or "", "kind": kind, "description": _plain(xi.description)}
            row = await _spine.upsert_exchange_item(self.study_id, existing, data, xi.uuid)
            self.xi_map[xi.uuid] = row["id"]
            self._record("exchange_item", xi.uuid, row["id"])
            self._count("exchange_item", existing is None)

    # -- components ------------------------------------------------------
    async def components(self) -> None:
        for layer, root in (("LA", self.model.la.root_component), ("PA", self.model.pa.root_component)):
            for child in _children(root, layer):
                await self._component(child, layer, None)

    async def _component(self, comp, layer: str, parent_id: str | None) -> None:
        meta = _meta(comp)
        src_id = meta.get("spine_id", "")
        existing = self.el_by_uuid.get(comp.uuid) or (self.el_by_id.get(src_id) if src_id else None)
        kids = _children(comp, layer)
        nature = getattr(getattr(comp, "nature", None), "name", "") or ""
        etype = meta.get("element_type") or (
            "software" if nature == "BEHAVIOR" else "logical" if layer == "LA"
            else "subsystem" if kids else "component")
        domain = meta.get("subsystem_domain") or (existing or {}).get("subsystem_domain") \
            or guess_subsystem_domain(comp.name)
        data: dict[str, Any] = {
            "name": comp.name or "", "description": _plain(comp.description),
            "element_type": etype, "subsystem_domain": domain or None,
            "layer": layer, "parent_id": parent_id,
        }
        budgets = _budgets(comp)
        for col in _WELL_KNOWN:
            if col in budgets:
                data[col] = budgets[col]
        row = await _spine.upsert_element(self.study_id, existing, data, comp.uuid)
        self.el_map[comp.uuid] = row["id"]
        if src_id:
            self.src_elements[src_id] = row["id"]
        self._record("element", comp.uuid, row["id"])
        self._count("element", existing is None)
        for name, value in budgets.items():
            try:
                await _spine.upsert_parameter(self.study_id, row["id"], name, value)
            except Exception as exc:
                self.result.warnings.append(f"parameter {name} on {comp.name!r}: {exc}")
        for child in kids:
            await self._component(child, layer, row["id"])

    # -- functions -------------------------------------------------------
    async def functions(self) -> None:
        for layer, root in (("SA", self.model.sa.root_function), ("LA", self.model.la.root_function),
                            ("PA", self.model.pa.root_function)):
            for child in _subfunctions(root):
                await self._function(child, layer, None)

    async def _function(self, fn, layer: str, parent_id: str | None) -> None:
        meta = _meta(fn)
        src_id = meta.get("spine_id", "")
        existing = self.fn_by_uuid.get(fn.uuid) or (self.fn_by_id.get(src_id) if src_id else None)
        data = {"name": fn.name or "", "description": _plain(fn.description), "layer": layer,
                "parent_id": parent_id, "function_type": meta.get("function_type") or None,
                "level": (existing or {}).get("level") if existing else 0}
        if data["level"] is None:
            data["level"] = 0
        row = await _spine.upsert_function(self.study_id, existing, data, fn.uuid)
        self.fn_map[fn.uuid] = row["id"]
        self.function_layer[row["id"]] = layer
        self._record("function", fn.uuid, row["id"])
        self._count("function", existing is None)
        # ports
        for direction, attr in (("in", "inputs"), ("out", "outputs")):
            try:
                ports = list(getattr(fn, attr))
            except Exception:
                ports = []
            for p in ports:
                pexisting = self.port_by_uuid.get(p.uuid) or self.port_by_key.get((row["id"], direction, p.name))
                prow = await _spine.upsert_function_port(
                    pexisting, {"function_id": row["id"], "name": p.name or "", "direction": direction})
                self.port_map[p.uuid] = prow["id"]
                self._count("function_port", pexisting is None)
        # allocation hint from the exporter (cross-layer allocations)
        alloc_src = meta.get("allocated_element")
        if alloc_src:
            target = self.src_elements.get(alloc_src) or (alloc_src if alloc_src in self.el_by_id else None)
            if target:
                await _spine.set_allocation(self.study_id, row["id"], target, layer)
                self._count("allocation", True)
        for child in _subfunctions(fn):
            await self._function(child, layer, row["id"])

    # -- allocations from components -------------------------------------
    async def allocations(self) -> None:
        for layer in ("LA", "PA"):
            root = self.model.la.root_component if layer == "LA" else self.model.pa.root_component
            stack = _children(root, layer)
            while stack:
                comp = stack.pop()
                stack.extend(_children(comp, layer))
                eid = self.el_map.get(comp.uuid)
                if not eid:
                    continue
                try:
                    fns = list(comp.allocated_functions)
                except Exception:
                    fns = []
                for fn in fns:
                    fid = self.fn_map.get(fn.uuid)
                    if fid:
                        await _spine.set_allocation(self.study_id, fid, eid, self.function_layer.get(fid, layer))
                        self._count("allocation", True)

    # -- functional exchanges --------------------------------------------
    async def functional_exchanges(self) -> None:
        for layer in (self.model.sa, self.model.la, self.model.pa):
            try:
                fxs = list(layer.all_function_exchanges)
            except Exception:
                fxs = []
            for fx in fxs:
                src = self.port_map.get(getattr(fx.source, "uuid", ""))
                dst = self.port_map.get(getattr(fx.target, "uuid", ""))
                if not src or not dst:
                    self.result.warnings.append(f"functional exchange {fx.name!r}: unresolved port; skipped")
                    continue
                try:
                    items = [self.xi_map[i.uuid] for i in fx.exchanged_items if i.uuid in self.xi_map]
                except Exception:
                    items = []
                existing = self.fx_by_uuid.get(fx.uuid)
                data = {"name": fx.name or "", "from_port_id": src, "to_port_id": dst,
                        "exchange_item_ids": items}
                row = await _spine.upsert_functional_exchange(self.study_id, existing, data, fx.uuid)
                self._record("functional_exchange", fx.uuid, row["id"])
                self._count("functional_exchange", existing is None)

    # -- interfaces ------------------------------------------------------
    async def interfaces(self) -> None:
        for layer in (self.model.la, self.model.pa):
            try:
                ces = list(layer.all_component_exchanges)
            except Exception:
                ces = []
            for ce in ces:
                try:
                    a = self.el_map.get(ce.source.parent.uuid)
                    b = self.el_map.get(ce.target.parent.uuid)
                except Exception:
                    a = b = None
                if not a or not b:
                    self.result.warnings.append(f"component exchange {ce.name!r}: endpoint not imported; skipped")
                    continue
                meta = _meta(ce)
                src_id = meta.get("spine_id", "")
                existing = self.if_by_uuid.get(ce.uuid) or (self.if_by_id.get(src_id) if src_id else None)
                orient = getattr(getattr(ce.source, "orientation", None), "name", "") or ""
                direction = meta.get("direction") or ("bidirectional" if orient == "INOUT" else "unidirectional")
                try:
                    items = [self.xi_map[i.uuid] for i in ce.convoyed_informations if i.uuid in self.xi_map]
                except Exception:
                    items = []
                data = {"name": ce.name or "", "interface_type": meta.get("interface_type") or "data",
                        "direction": direction, "from_element_id": a, "to_element_id": b,
                        "exchange_item_ids": items}
                row = await _spine.upsert_interface(self.study_id, existing, data, ce.uuid)
                self.if_map[ce.uuid] = row["id"]
                self._record("interface", ce.uuid, row["id"])
                self._count("interface", existing is None)

    # -- requirements ----------------------------------------------------
    async def requirements(self) -> None:
        modules = []
        for layer in (self.model.oa, self.model.sa, self.model.la, self.model.pa):
            try:
                modules.extend(list(layer.requirement_modules))
            except Exception:
                continue
        pending: list[tuple[Any, str]] = []
        for mod in modules:
            for req in list(mod.requirements):
                pending.extend(self._requirement(req, None, 0))
        # relations after all requirements exist
        for req, rid in pending:
            await self._relations(req, rid)

    def _requirement(self, req, parent_id: str | None, depth: int) -> list[tuple[Any, str]]:
        code = req.identifier or req.long_name or req.name or req.uuid[:8]
        existing = self.req_by_uuid.get(req.uuid) or self.req_by_code.get(code)
        level = req.chapter_name if req.chapter_name in ("mission", "system", "subsystem") else \
            ("mission", "system", "subsystem")[min(depth, 2)]
        data = {"code": code, "text": _plain(req.text), "rationale": _plain(req.description) or None,
                "level": level, "parent_id": parent_id}
        if existing is None:
            data["id"] = code if code not in self.req_by_id else None
            if data["id"] is None:
                data.pop("id")
        row = _spine.upsert_requirement(self.study_id, existing, data, req.uuid)
        self.req_map[req.uuid] = row["id"]
        self.req_by_id[row["id"]] = row
        self._record("requirement", req.uuid, row["id"])
        self._count("requirement", existing is None)
        out = [(req, row["id"])]
        # Only ``Folder`` owns requirements; on a plain Requirement ``.requirements``
        # is the reqif glue's "related requirements" accessor.
        kids = []
        if type(req).__name__ == "Folder":
            try:
                kids = list(req.requirements)
            except Exception:
                kids = []
        for k in kids:
            out.extend(self._requirement(k, row["id"], depth + 1))
        return out

    async def _relations(self, req, rid: str) -> None:
        try:
            rels = list(req.owned_relations)
        except Exception:
            return
        for rel in rels:
            kind = getattr(getattr(rel, "type", None), "long_name", None) or "traces"
            if kind not in RELATION_KINDS:
                kind = "traces"
            cls = type(rel).__name__
            tgt = getattr(rel, "target", None)
            src = getattr(rel, "source", None)
            other = tgt if cls != "CapellaIncomingRelation" else tgt
            if other is None:
                continue
            okind, oid = self._entity(other)
            if oid is None:
                self.result.warnings.append(f"relation on {req.identifier!r}: target not imported; skipped")
                continue
            if cls == "CapellaOutgoingRelation" and kind == "allocates" and okind == "element":
                live = self.req_by_id.get(rid)
                if live is not None:
                    live["element_id"] = oid
                continue
            if cls == "CapellaIncomingRelation":
                data = {"kind": kind, "source_kind": okind, "source_id": oid,
                        "target_kind": "requirement", "target_id": rid}
            else:
                data = {"kind": kind, "source_kind": "requirement", "source_id": rid,
                        "target_kind": okind, "target_id": oid}
            try:
                await _spine.upsert_relation(self.study_id, data, rel.uuid)
                self._count("relation", True)
            except ValueError as exc:
                self.result.warnings.append(f"relation on {req.identifier!r}: {exc}")
            del src

    def _entity(self, obj) -> tuple[str, str | None]:
        u = getattr(obj, "uuid", "")
        if u in self.req_map:
            return "requirement", self.req_map[u]
        if u in self.el_map:
            return "element", self.el_map[u]
        if u in self.fn_map:
            return "function", self.fn_map[u]
        if u in self.if_map:
            return "interface", self.if_map[u]
        return "element", None

    async def run(self) -> ImportResult:
        await self.exchange_items()
        await self.components()
        await self.functions()
        await self.allocations()
        await self.functional_exchanges()
        await self.interfaces()
        await self.requirements()
        return self.result


async def import_capella_model(study_id: str, source: Path | bytes) -> ImportResult:
    """Import a Capella project (dir, ``.aird`` or zip) into ``study_id``."""
    patch_capellambse()
    snap = await _spine.load_snapshot(study_id)
    with tempfile.TemporaryDirectory(prefix="spacecdf-capella-import-") as td:
        workdir = Path(td)
        aird = _materialise_base(source, workdir)
        model = load_model(aird)
        return await _Importer(study_id, model, snap).run()


def read_model_summary(source: Path | bytes) -> dict[str, Any]:
    """Counts/names of a Capella project without touching the spine (for previews)."""
    from .exporter import _counts
    patch_capellambse()
    with tempfile.TemporaryDirectory(prefix="spacecdf-capella-peek-") as td:
        workdir = Path(td)
        aird = _materialise_base(source, workdir)
        model = load_model(aird)
        return {"project": model.project.name, "counts": _counts(model)}
