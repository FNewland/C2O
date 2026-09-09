"""Spine dicts -> capellambse declarative-modelling instructions (SCDF-160 §2).

Pure functions: no I/O, no model access.  :func:`build_instructions` turns a
:class:`SpineSnapshot` (plain dicts as returned by the ``db/*_repo`` loaders
and the requirements store) into a list of ``capellambse.decl`` instructions
plus the ``(kind, spine_id) -> capella_uuid`` map that the exporter writes back
into ``external_ids['capella']``.

Mapping (design §2, "capella" row)
----------------------------------
* functions                 -> ``<layer>.root_function.functions`` tree
                               (``SystemFunction`` / ``LogicalFunction`` /
                               ``PhysicalFunction``); ports -> ``inputs`` /
                               ``outputs``
* elements ``layer='LA'``   -> ``la.root_component.components`` tree
* elements (other)          -> ``pa.root_component.owned_components`` tree;
                               ``element_type='software'`` -> ``nature: BEHAVIOR``
                               else ``NODE``; ``element_type='mode'`` skipped
* interfaces                -> ``ComponentExchange`` (owned by the layer root
                               component) between two ``ComponentPort``s
                               created on the from/to components
* exchange items            -> ``ExchangeItem`` in ``sa.data_pkg``
* functional exchanges      -> ``FunctionalExchange`` owned by the layer root
                               function, linked via ``!promise``
* function allocations      -> ``allocated_functions`` on the component
* requirements              -> one ``CapellaModule`` in ``oa.requirement_modules``,
                               nested by ``parent_id``; relations ->
                               ``CapellaOutgoingRelation`` (req -> model element),
                               ``CapellaIncomingRelation`` (model element -> req),
                               ``InternalRelation`` (req -> req), typed by a
                               ``RelationType`` per relation kind
* parameters / budgets      -> core ``PropertyValueGroup`` "SpaceCDF.Budgets"
                               of ``FloatPropertyValue``s applied to the component
* provenance                -> ``PropertyValueGroup`` "SpaceCDF.Meta" of
                               ``StringPropertyValue``s (spine_id, element_type,
                               subsystem_domain, kind, ...) so an import can
                               match entities even without ``external_ids``

UUIDs
-----
Every exported entity gets a *stable* Capella UUID: the one recorded in the
spine's ``external_ids['capella']`` if present, else ``uuid5`` of
``(study_id, kind, spine_id)``.  Hence exporting twice yields the same UUIDs
(diagram references in Capella survive), and re-exporting on top of a
previously exported model (``existing_uuids``) updates in place via ``set``
instead of duplicating.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from capellambse.decl import Promise, UUIDReference

__all__ = [
    "SpineSnapshot", "ModelAnchors", "MappingResult", "build_instructions",
    "capella_uuid", "promise_id", "BUDGET_GROUP", "META_GROUP", "MODULE_NAME",
    "TYPES_FOLDER_NAME", "RELATION_KINDS", "guess_subsystem_domain",
    "FUNCTION_CLASS", "COMPONENTS_ATTR", "EXCHANGE_MECHANISM", "candidate_uuids",
]

#: Namespace for deterministic Capella UUIDs.
CAPELLA_NAMESPACE = uuid.UUID("6f0c2c1e-3a5c-5f3e-9a3a-5c0d4b2e1a10")
BUDGET_GROUP = "SpaceCDF.Budgets"
META_GROUP = "SpaceCDF.Meta"
MODULE_NAME = "SpaceCDF requirements"
TYPES_FOLDER_NAME = "SpaceCDF relation types"
RELATION_KINDS = ("satisfies", "verifies", "refines", "derives", "traces", "allocates")

FUNCTION_CLASS = {"SA": "SystemFunction", "LA": "LogicalFunction", "PA": "PhysicalFunction"}
#: child-component containment differs per layer in capellambse 0.8
COMPONENTS_ATTR = {"LA": "components", "PA": "owned_components"}
EXCHANGE_MECHANISM = {
    "data": "FLOW", "power": "FLOW", "rf": "FLOW", "thermal": "FLOW",
    "mechanical": "FLOW", "optical": "FLOW", "fluid": "FLOW",
}

_DOMAIN_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("power", ("eps", "power", "battery", "solar")),
    ("aocs", ("aocs", "adcs", "attitude")),
    ("ttc", ("ttc", "tt&c", "comm", "radio", "transceiver", "antenna")),
    ("thermal", ("thermal", "tcs")),
    ("structure", ("structure", "structural", "chassis")),
    ("propulsion", ("prop", "thruster")),
    ("obc", ("obc", "obdh", "cdh", "c&dh", "computer")),
    ("payload", ("payload", "camera", "instrument")),
)


def guess_subsystem_domain(name: str | None) -> str | None:
    """Small keyword map name -> subsystem_domain (used on import)."""
    if not name:
        return None
    low = name.lower()
    tokens = set(re.split(r"[^a-z0-9&]+", low))
    for domain, keys in _DOMAIN_KEYWORDS:
        for k in keys:
            if k in tokens or (len(k) > 3 and k in low):
                return domain
    return None


def capella_uuid(study_id: str, kind: str, spine_id: str) -> str:
    return str(uuid.uuid5(CAPELLA_NAMESPACE, f"{study_id}:{kind}:{spine_id}"))


def promise_id(kind: str, spine_id: str) -> str:
    return f"{kind}:{spine_id}"


def _ext(d: dict, key: str = "external_ids") -> dict:
    v = d.get(key) or d.get(f"{key}_json") or {}
    return v if isinstance(v, dict) else {}


def _recorded_uuid(d: dict) -> str | None:
    cap = _ext(d).get("capella")
    if cap:
        return str(cap)
    ext_id = d.get("external_id")
    if isinstance(ext_id, str) and ext_id.startswith("capella:"):
        return ext_id[len("capella:"):]
    return None


def _list(d: dict, key: str) -> list:
    v = d.get(key)
    if v is None:
        v = d.get(f"{key}_json")
    return list(v) if isinstance(v, (list, tuple)) else []


# ── Inputs / outputs ────────────────────────────────────────────────────

@dataclass
class SpineSnapshot:
    """Everything the mapper needs, as plain dicts (API-level keys)."""
    study_id: str
    study_name: str = ""
    elements: list[dict] = field(default_factory=list)
    interfaces: list[dict] = field(default_factory=list)
    functions: list[dict] = field(default_factory=list)
    function_ports: list[dict] = field(default_factory=list)
    allocations: list[dict] = field(default_factory=list)
    functional_exchanges: list[dict] = field(default_factory=list)
    exchange_items: list[dict] = field(default_factory=list)
    requirements: list[dict] = field(default_factory=list)
    relations: list[dict] = field(default_factory=list)
    #: ``{element_id, name, unit, value}`` – already resolved (value_switch applied)
    parameters: list[dict] = field(default_factory=list)


@dataclass
class ModelAnchors:
    """UUIDs of the template roots the instructions attach to."""
    sa_root_function: str
    la_root_function: str
    pa_root_function: str
    sa_root_component: str
    la_root_component: str
    pa_root_component: str
    oa: str
    data_pkg: str
    #: UUIDs already present in the model (for update-in-place)
    existing_uuids: set[str] = field(default_factory=set)
    #: uuid -> parent uuid for existing objects (reparent detection)
    existing_parents: dict[str, str] = field(default_factory=dict)


@dataclass
class MappingResult:
    instructions: list[dict[str, Any]]
    #: (kind, spine_id) -> capella uuid; kinds: element, interface, function,
    #: function_port, functional_exchange, exchange_item, requirement, relation
    id_map: dict[tuple[str, str], str]
    warnings: list[str] = field(default_factory=list)
    #: uuids that exist in the model under a different parent than the spine
    #: says; the exporter deletes them before applying so they are recreated.
    reparented: list[str] = field(default_factory=list)


# ── Builder ─────────────────────────────────────────────────────────────

class _Builder:
    def __init__(self, snap: SpineSnapshot, anchors: ModelAnchors) -> None:
        self.snap = snap
        self.anchors = anchors
        self.instructions: list[dict[str, Any]] = []
        self.id_map: dict[tuple[str, str], str] = {}
        self.warnings: list[str] = []
        self.reparented: list[str] = []
        self.el_by_id = {e["id"]: e for e in snap.elements if not e.get("deleted_at")}
        self.fn_by_id = {f["id"]: f for f in snap.functions if not f.get("deleted_at")}
        self.port_by_id = {p["id"]: p for p in snap.function_ports if not p.get("deleted_at")}
        self.xi_by_id = {x["id"]: x for x in snap.exchange_items if not x.get("deleted_at")}
        self.req_by_id = {r["id"]: r for r in snap.requirements if r.get("status") != "retired"}
        self.exported_elements: dict[str, str] = {}   # spine id -> layer
        self.exported_functions: dict[str, str] = {}  # spine id -> layer
        self.alloc_by_function: dict[str, str] = {
            a["function_id"]: a["element_id"] for a in snap.allocations
            if a.get("function_id") and a.get("element_id")
        }

    # -- helpers ---------------------------------------------------------
    def uuid_for(self, kind: str, d: dict) -> str:
        u = _recorded_uuid(d) or capella_uuid(self.snap.study_id, kind, d["id"])
        self.id_map[(kind, d["id"])] = u
        return u

    def exists(self, u: str) -> bool:
        return u in self.anchors.existing_uuids

    def emit(self, parent: Promise | UUIDReference, **ops: Any) -> None:
        self.instructions.append({"parent": parent, **ops})

    def upsert(self, kind: str, d: dict, parent: Promise | UUIDReference, parent_uuid_hint: str | None,
               attr: str, props: dict[str, Any], *, list_props: dict[str, list] | None = None,
               nested: dict[str, list] | None = None) -> tuple[str, Promise]:
        """Create (``extend``) or update (``set``) one object; returns (uuid, promise).

        ``props`` are simple attributes, ``list_props`` are reference lists that
        must be *replaced* on update (e.g. ``allocated_functions``), ``nested``
        are containments to sync by name/uuid on update.
        """
        u = self.uuid_for(kind, d)
        pid = promise_id(kind, d["id"])
        list_props = list_props or {}
        nested = nested or {}
        if self.exists(u):
            cur_parent = self.anchors.existing_parents.get(u)
            if parent_uuid_hint and cur_parent and cur_parent != parent_uuid_hint:
                self.reparented.append(u)
                self.warnings.append(f"{kind} {d['id']!r} moved to a different parent; recreated")
            else:
                ops: dict[str, Any] = {"promise_id": pid}
                simple = {k: v for k, v in props.items() if k != "_type"}
                if simple:
                    ops["set"] = simple
                if list_props:
                    ops.setdefault("set", {}).update({k: list(v) for k, v in list_props.items()})
                if nested:
                    ops["sync"] = nested
                self.emit(UUIDReference(u), **ops)
                return u, Promise(pid)
        obj: dict[str, Any] = {"uuid": u, "promise_id": pid, **props}
        for k, v in nested.items():
            obj[k] = [self._sync_to_create(x) for x in v]
        for k, v in list_props.items():
            obj[k] = list(v)
        self.emit(parent, extend={attr: [obj]})
        return u, Promise(pid)

    @staticmethod
    def _sync_to_create(entry: dict) -> dict:
        """Turn a ``sync`` entry (find/set/sync) into a plain create dict."""
        out: dict[str, Any] = {}
        out.update(entry.get("find", {}))
        out.update(entry.get("set", {}))
        if "promise_id" in entry:
            out["promise_id"] = entry["promise_id"]
        for k, v in entry.get("sync", {}).items():
            out[k] = [_Builder._sync_to_create(x) for x in v]
        for k, v in entry.get("extend", {}).items():
            out[k] = list(v)
        return out

    @staticmethod
    def pv_group(name: str, values: dict[str, Any], *, kind: str = "float",
                 pid: str | None = None) -> dict:
        cls = "FloatPropertyValue" if kind == "float" else "StringPropertyValue"
        entry: dict[str, Any] = {
            "find": {"name": name},
            "sync": {"property_values": [
                {"find": {"_type": cls, "name": k}, "set": {"value": v}}
                for k, v in values.items()
            ]},
        }
        if pid:
            entry["promise_id"] = pid
        return entry

    # -- layers ----------------------------------------------------------
    def element_layer(self, e: dict) -> str:
        layer = (e.get("layer") or "PA").upper()
        return "LA" if layer == "LA" or e.get("element_type") == "logical" else "PA"

    def root_component(self, layer: str) -> str:
        return self.anchors.la_root_component if layer == "LA" else self.anchors.pa_root_component

    def root_function(self, layer: str) -> str:
        return {"SA": self.anchors.sa_root_function, "LA": self.anchors.la_root_function,
                "PA": self.anchors.pa_root_function}[layer]

    # -- exchange items ------------------------------------------------
    def exchange_items(self) -> None:
        for x in self.xi_by_id.values():
            meta = {"spine_id": x["id"], "kind": x.get("kind") or "data"}
            self.upsert(
                "exchange_item", x, UUIDReference(self.anchors.data_pkg), self.anchors.data_pkg,
                "exchange_items",
                {"name": x.get("name") or x["id"],
                 "description": x.get("description") or "",
                 "exchange_mechanism": EXCHANGE_MECHANISM.get(x.get("kind") or "data", "FLOW")},
                nested={"property_value_groups": [self.pv_group(META_GROUP, meta, kind="string")]},
            )

    # -- elements --------------------------------------------------------
    def elements(self) -> None:
        params: dict[str, dict[str, float]] = {}
        for p in self.snap.parameters:
            if p.get("value") is None:
                continue
            try:
                params.setdefault(p["element_id"], {})[p["name"]] = float(p["value"])
            except (TypeError, ValueError):
                continue
        # Well-known columns as a fallback when no parameter row exists
        wk = ("mass_kg", "power_avg_w", "power_peak_w", "cost_nre_keur", "cost_recurring_keur", "volume_cm3")

        done: set[str] = set()

        def visit(e: dict) -> None:
            if e["id"] in done:
                return
            done.add(e["id"])
            if e.get("element_type") == "mode":
                return
            layer = self.element_layer(e)
            parent = self.el_by_id.get(e.get("parent_id") or "")
            if parent is not None and parent.get("element_type") != "mode":
                visit(parent)
                if self.exported_elements.get(parent["id"]) == layer:
                    parent_ref: Promise | UUIDReference = Promise(promise_id("element", parent["id"]))
                    parent_hint = self.id_map[("element", parent["id"])]
                else:
                    self.warnings.append(
                        f"element {e['id']!r} ({e.get('name')}) parent is on another layer; attached to root")
                    parent_ref = UUIDReference(self.root_component(layer))
                    parent_hint = self.root_component(layer)
            else:
                parent_ref = UUIDReference(self.root_component(layer))
                parent_hint = self.root_component(layer)

            budgets = dict(params.get(e["id"], {}))
            for col in wk:
                if col not in budgets and e.get(col) is not None:
                    budgets[col] = float(e[col])
            meta = {
                "spine_id": e["id"],
                "element_type": e.get("element_type") or "",
                "subsystem_domain": e.get("subsystem_domain") or "",
                "layer": layer,
            }
            props: dict[str, Any] = {"name": e.get("name") or e["id"],
                                     "description": e.get("description") or ""}
            if layer == "PA":
                props["nature"] = "BEHAVIOR" if e.get("element_type") == "software" else "NODE"
            groups = [self.pv_group(META_GROUP, meta, kind="string",
                                    pid=promise_id("meta", e["id"]))]
            list_props: dict[str, list] = {}
            if budgets:
                groups.append(self.pv_group(BUDGET_GROUP, budgets,
                                            pid=promise_id("budget", e["id"])))
                list_props["applied_property_value_groups"] = [Promise(promise_id("budget", e["id"]))]
            self.upsert("element", e, parent_ref, parent_hint, COMPONENTS_ATTR[layer], props,
                        list_props=list_props, nested={"property_value_groups": groups})
            self.exported_elements[e["id"]] = layer

        for e in self.el_by_id.values():
            visit(e)

    # -- functions -------------------------------------------------------
    def functions(self) -> None:
        done: set[str] = set()

        def visit(f: dict) -> None:
            if f["id"] in done:
                return
            done.add(f["id"])
            layer = (f.get("layer") or "SA").upper()
            if layer not in FUNCTION_CLASS:
                self.warnings.append(f"function {f['id']!r} layer {layer!r} not exported (OA unsupported)")
                return
            parent = self.fn_by_id.get(f.get("parent_id") or "")
            if parent is not None:
                visit(parent)
            if parent is not None and self.exported_functions.get(parent["id"]) == layer:
                parent_ref: Promise | UUIDReference = Promise(promise_id("function", parent["id"]))
                parent_hint = self.id_map[("function", parent["id"])]
            else:
                if parent is not None:
                    self.warnings.append(f"function {f['id']!r} parent on another layer; attached to root")
                parent_ref = UUIDReference(self.root_function(layer))
                parent_hint = self.root_function(layer)
            ports_in = [p for p in self.port_by_id.values()
                        if p.get("function_id") == f["id"] and p.get("direction") == "in"]
            ports_out = [p for p in self.port_by_id.values()
                         if p.get("function_id") == f["id"] and p.get("direction") != "in"]
            nested: dict[str, list] = {
                "property_value_groups": [self.pv_group(
                    META_GROUP, {"spine_id": f["id"], "function_type": f.get("function_type") or "",
                                 "layer": layer,
                                 "allocated_element": self.alloc_by_function.get(f["id"], "")},
                    kind="string")],
            }
            for attr, plist in (("inputs", ports_in), ("outputs", ports_out)):
                entries = []
                for p in plist:
                    pu = self.uuid_for("function_port", p)
                    entries.append({"find": {"uuid": pu}, "set": {"name": p.get("name") or ""},
                                    "promise_id": promise_id("function_port", p["id"])})
                if entries:
                    nested[attr] = entries
            self.upsert("function", f, parent_ref, parent_hint, "functions",
                        {"_type": FUNCTION_CLASS[layer], "name": f.get("name") or f["id"],
                         "description": f.get("description") or ""},
                        nested=nested)
            self.exported_functions[f["id"]] = layer

        for f in self.fn_by_id.values():
            visit(f)

    # -- functional exchanges -------------------------------------------
    def functional_exchanges(self) -> None:
        for fx in self.snap.functional_exchanges:
            if fx.get("deleted_at"):
                continue
            src = self.port_by_id.get(fx.get("from_port_id") or "")
            dst = self.port_by_id.get(fx.get("to_port_id") or "")
            if not src or not dst:
                self.warnings.append(f"functional exchange {fx['id']!r}: unknown port; skipped")
                continue
            l1 = self.exported_functions.get(src["function_id"])
            l2 = self.exported_functions.get(dst["function_id"])
            if not l1 or l1 != l2:
                self.warnings.append(f"functional exchange {fx['id']!r} crosses layers or has unexported function; skipped")
                continue
            items = [Promise(promise_id("exchange_item", i)) for i in _list(fx, "exchange_item_ids")
                     if i in self.xi_by_id]
            self.upsert(
                "functional_exchange", fx, UUIDReference(self.root_function(l1)), self.root_function(l1),
                "exchanges",
                {"name": fx.get("name") or fx["id"],
                 "source": Promise(promise_id("function_port", src["id"])),
                 "target": Promise(promise_id("function_port", dst["id"]))},
                list_props={"exchanged_items": items},
            )

    # -- allocations -----------------------------------------------------
    def allocations(self) -> None:
        """Same-layer allocations go on the element's component.  Capella (and
        capellambse) refuse cross-layer allocations, so e.g. an SA function
        allocated to a PA element is allocated to the SA root component
        ("System") instead; the intended element is kept in the function's
        ``SpaceCDF.Meta.allocated_element`` so an import restores it."""
        per_element: dict[str, list[Promise]] = {}
        per_root: dict[str, list[Promise]] = {}
        cross = 0
        for a in self.snap.allocations:
            fid, eid = a.get("function_id"), a.get("element_id")
            if fid not in self.exported_functions or eid not in self.exported_elements:
                continue
            fl = self.exported_functions[fid]
            if fl == self.exported_elements[eid]:
                per_element.setdefault(eid, []).append(Promise(promise_id("function", fid)))
            else:
                cross += 1
                root = {"SA": self.anchors.sa_root_component, "LA": self.anchors.la_root_component,
                        "PA": self.anchors.pa_root_component}[fl]
                per_root.setdefault(root, []).append(Promise(promise_id("function", fid)))
        if cross:
            self.warnings.append(
                f"{cross} function allocation(s) cross layers (e.g. SA function -> PA element); "
                "allocated to the layer root component in Capella, element kept in SpaceCDF.Meta")
        for eid, fns in per_element.items():
            self.emit(Promise(promise_id("element", eid)), set={"allocated_functions": fns})
        for root, fns in per_root.items():
            self.emit(UUIDReference(root), set={"allocated_functions": fns})

    # -- interfaces ------------------------------------------------------
    def interfaces(self) -> None:
        for i in self.snap.interfaces:
            if i.get("deleted_at"):
                continue
            a, b = i.get("from_element_id"), i.get("to_element_id")
            la, lb = self.exported_elements.get(a or ""), self.exported_elements.get(b or "")
            if not la or not lb:
                self.warnings.append(f"interface {i['id']!r}: endpoint not exported; skipped")
                continue
            if la != lb:
                self.warnings.append(f"interface {i['id']!r} crosses LA/PA; skipped")
                continue
            direction = i.get("direction") or "bidirectional"
            o_from, o_to = ("INOUT", "INOUT") if direction == "bidirectional" else ("OUT", "IN")
            name = i.get("name") or i["id"]
            port_ids = []
            for side, eid, orient in (("from", a, o_from), ("to", b, o_to)):
                pd = {"id": f"{i['id']}:{side}"}
                pu = self.uuid_for("port", pd)
                port_ids.append(promise_id("port", pd["id"]))
                self.upsert("port", pd, Promise(promise_id("element", eid)), self.id_map[("element", eid)],
                            "ports", {"name": f"{name} ({side})", "orientation": orient})
            items = [Promise(promise_id("exchange_item", x)) for x in _list(i, "exchange_item_ids")
                     if x in self.xi_by_id]
            meta = {"spine_id": i["id"], "interface_type": i.get("interface_type") or "",
                    "direction": direction}
            self.upsert(
                "interface", i, UUIDReference(self.root_component(la)), self.root_component(la),
                "component_exchanges",
                {"name": name, "source": Promise(port_ids[0]), "target": Promise(port_ids[1])},
                list_props={"convoyed_informations": items},
                nested={"property_value_groups": [self.pv_group(META_GROUP, meta, kind="string")]},
            )

    # -- requirements ----------------------------------------------------
    def requirements(self) -> None:
        if not self.req_by_id and not self.snap.relations:
            return
        mod = {"id": "module"}
        mod_uuid = self.uuid_for("requirement_module", mod)
        self.upsert("requirement_module", mod, UUIDReference(self.anchors.oa), self.anchors.oa,
                    "requirement_modules",
                    {"long_name": MODULE_NAME, "name": MODULE_NAME,
                     "identifier": self.snap.study_id})
        folder = {"id": "types"}
        self.upsert("requirement_types_folder", folder, UUIDReference(self.anchors.oa), self.anchors.oa,
                    "requirement_types_folders", {"long_name": TYPES_FOLDER_NAME})
        for kind in RELATION_KINDS:
            rt = {"id": kind}
            self.upsert("relation_type", rt, Promise(promise_id("requirement_types_folder", "types")),
                        self.id_map[("requirement_types_folder", "types")], "types",
                        {"_type": "RelationType", "long_name": kind})

        has_children = {r.get("parent_id") for r in self.req_by_id.values() if r.get("parent_id")}
        done: set[str] = set()

        def visit(r: dict) -> None:
            if r["id"] in done:
                return
            done.add(r["id"])
            parent = self.req_by_id.get(r.get("parent_id") or "")
            if parent is not None:
                visit(parent)
                parent_ref: Promise | UUIDReference = Promise(promise_id("requirement", parent["id"]))
                parent_hint = self.id_map[("requirement", parent["id"])]
            else:
                parent_ref = Promise(promise_id("requirement_module", "module"))
                parent_hint = mod_uuid
            code = r.get("code") or r["id"]
            # A requirement with children is a ``Folder`` (a Requirement subclass
            # that owns requirements) - the only way to nest in the VP.
            cls = "Requirements:Folder" if r["id"] in has_children else "Requirement"
            self.upsert("requirement", r, parent_ref, parent_hint, "requirements",
                        {"_type": cls, "identifier": code, "long_name": code, "name": code,
                         "text": r.get("text") or "",
                         "description": r.get("rationale") or "",
                         "chapter_name": r.get("level") or ""})

        for r in self.req_by_id.values():
            visit(r)

        # implicit satisfies: requirement.element_id
        for r in self.req_by_id.values():
            eid = r.get("element_id")
            if eid and eid in self.exported_elements:
                self._relation({"id": f"{r['id']}:element", "kind": "allocates",
                                "source_kind": "requirement", "source_id": r["id"],
                                "target_kind": "element", "target_id": eid})
        for rel in self.snap.relations:
            if rel.get("deleted_at"):
                continue
            self._relation(rel)

    def _target_promise(self, kind: str, ident: str) -> Promise | None:
        if kind == "requirement" and ident in self.req_by_id:
            return Promise(promise_id("requirement", ident))
        if kind == "element" and ident in self.exported_elements:
            return Promise(promise_id("element", ident))
        if kind == "function" and ident in self.exported_functions:
            return Promise(promise_id("function", ident))
        if kind == "interface" and ("interface", ident) in self.id_map:
            return Promise(promise_id("interface", ident))
        return None

    def _relation(self, rel: dict) -> None:
        kind = rel.get("kind") or "traces"
        if kind not in RELATION_KINDS:
            kind = "traces"
        sk, sid, tk, tid = rel.get("source_kind"), rel.get("source_id"), rel.get("target_kind"), rel.get("target_id")
        src = self._target_promise(sk, sid)
        dst = self._target_promise(tk, tid)
        if src is None or dst is None:
            self.warnings.append(f"relation {rel.get('id')!r}: endpoint not exported; skipped")
            return
        rtype = Promise(promise_id("relation_type", kind))
        if sk == "requirement" and tk == "requirement":
            owner, props = src, {"_type": "InternalRelation", "source": src, "target": dst, "type": rtype}
        elif sk == "requirement":
            owner, props = src, {"_type": "CapellaOutgoingRelation", "source": src, "target": dst, "type": rtype}
        elif tk == "requirement":
            owner, props = dst, {"_type": "CapellaIncomingRelation", "source": dst, "target": src, "type": rtype}
        else:
            self.warnings.append(f"relation {rel.get('id')!r}: neither end is a requirement; skipped")
            return
        owner_uuid = self.id_map.get(("requirement", sid if owner is src else tid))
        self.upsert("relation", rel, owner, owner_uuid, "owned_relations", props)


def candidate_uuids(snap: SpineSnapshot) -> dict[str, tuple[str, str]]:
    """All Capella UUIDs an export of ``snap`` would use: ``uuid -> (kind, spine_id)``.

    The exporter probes these against the base model to fill
    :attr:`ModelAnchors.existing_uuids` / ``existing_parents``.
    """
    out: dict[str, tuple[str, str]] = {}
    sid = snap.study_id

    def add(kind: str, d: dict) -> None:
        u = _recorded_uuid(d) or capella_uuid(sid, kind, d["id"])
        out[u] = (kind, d["id"])

    for e in snap.elements:
        add("element", e)
    for i in snap.interfaces:
        add("interface", i)
        for side in ("from", "to"):
            add("port", {"id": f"{i['id']}:{side}"})
    for f in snap.functions:
        add("function", f)
    for p in snap.function_ports:
        add("function_port", p)
    for fx in snap.functional_exchanges:
        add("functional_exchange", fx)
    for x in snap.exchange_items:
        add("exchange_item", x)
    for r in snap.requirements:
        add("requirement", r)
        add("relation", {"id": f"{r['id']}:element"})
    for rel in snap.relations:
        add("relation", rel)
    add("requirement_module", {"id": "module"})
    add("requirement_types_folder", {"id": "types"})
    for k in RELATION_KINDS:
        add("relation_type", {"id": k})
    return out


def build_instructions(snap: SpineSnapshot, anchors: ModelAnchors) -> MappingResult:
    """Pure: spine snapshot + template anchors -> decl instructions + id map."""
    b = _Builder(snap, anchors)
    b.exchange_items()
    b.elements()
    b.functions()
    b.functional_exchanges()
    b.allocations()
    b.interfaces()
    b.requirements()
    return MappingResult(instructions=b.instructions, id_map=b.id_map,
                         warnings=b.warnings, reparented=b.reparented)
