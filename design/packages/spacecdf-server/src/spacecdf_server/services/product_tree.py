"""SpaceCDF product tree: levels, allowed children, default trees and the space-segment migration.

The product tree follows ECSS-M-ST-10C Rev.1 (product tree, 5.3) and the NASA Systems
Engineering Handbook (SP-2016-6105, product breakdown / system structure, 6.0):

    level 0  mission                      element_type ``mission``
    level 1  segment (space, ground, launch, user, operations)       ``segment``
    level 2  system / element: a spacecraft, a constellation member,
             a ground station, a control centre                       ``system``
    level 3  subsystem (EPS, AOCS, TT&C, OBDH, thermal, structure,
             propulsion, payload)                                    ``subsystem``
    level 4  equipment / unit (a KB part)                            ``component``

A space segment is NOT a spacecraft: its children are spacecraft (systems), and a
spacecraft's children are the subsystems. Before Nov 2026 some paths (an early Blocks
preset, the element projection, hand-built trees) hung subsystems straight off the space
segment; :func:`plan_migration` inserts a Spacecraft element between them (ids, links,
budgets and stack placements are untouched: only ``parent_id`` changes, plus
``element_type`` for subsystem-like elements that were typed ``system``).

Pure: plain dicts in, plain dicts out. Persistence lives in ``routers/product_tree.py``.
"""
from __future__ import annotations

import re
from typing import Any, Iterable

from .rule_inputs import by_id, effective_segment, live

#: ECSS / NASA product-tree level of each element type.
TREE_LEVEL: dict[str, int] = {"mission": 0, "segment": 1, "system": 2, "subsystem": 3, "component": 4, "equipment": 4}
LEVEL_NAMES = {0: "Mission", 1: "Segment", 2: "System / element", 3: "Subsystem", 4: "Equipment"}

#: Element types allowed under a parent of each type. Systems keep equipment directly (a
#: ground station's antenna); subsystems may nest assemblies; a mission may hold a system
#: directly (single-spacecraft studies modelled without segments). The study root is free
#: (API fragments, imports, studies made before mission roots). Types outside the tree
#: (mode, logical, software) are not checked. What the UI OFFERS is stricter: the next
#: level only (frontend workbench/blockLevels.ts).
ALLOWED_CHILDREN: dict[str | None, tuple[str, ...]] = {
    None: ("mission", "segment", "system", "subsystem", "component"),
    "mission": ("segment", "system"),
    "segment": ("system",),
    "system": ("subsystem", "component"),
    "subsystem": ("subsystem", "component"),
    "component": ("component",),
}
TREE_TYPES = frozenset(ALLOWED_CHILDREN) - {None}

#: Subsystem domains of a spacecraft bus (+ payload): a ``system`` carrying one of these
#: directly under a space segment is a subsystem typed one level too high.
BUS_DOMAINS = frozenset({"payload", "power", "aocs", "ttc", "obc", "thermal", "structure", "propulsion"})
_SPACECRAFT_NAME = re.compile(
    r"spacecraft|satellite|cubesat|smallsat|\bsat\b|-sat\b|probe|orbiter|lander|rover|platform|\bbus\b|vehicle",
    re.I)

#: Standard subsystems of a spacecraft (same set and names as populate-subsystems).
SPACECRAFT_SUBSYSTEMS: tuple[dict[str, str], ...] = (
    {"name": "Payload", "domain": "payload"},
    {"name": "EPS", "domain": "power"},
    {"name": "AOCS", "domain": "aocs"},
    {"name": "Communications", "domain": "ttc"},
    {"name": "On-Board Computer", "domain": "obc"},
    {"name": "Thermal", "domain": "thermal"},
    {"name": "Structure", "domain": "structure"},
    {"name": "Propulsion", "domain": "propulsion"},
)

#: Default trees offered by the mission wizard (step 4). Each segment lists its level-2
#: systems; ``spacecraft`` systems get the standard subsystems.
ARCHITECTURES: dict[str, list[dict[str, Any]]] = {
    "single-leo": [
        {"name": "Space Segment", "segment": "space", "systems": [{"name": "Spacecraft", "spacecraft": True}]},
        {"name": "Ground Segment", "segment": "ground", "systems": [{"name": "Ground Station", "domain": "ground"}]},
        {"name": "Launch Segment", "segment": "launch", "systems": []},
        # W2.09 (Nov 2026): the user / science segment receives the product requirements
        {"name": "User Segment", "segment": "user", "systems": []},
        {"name": "Operations", "segment": "operations", "systems": []},
    ],
    "constellation": [
        {"name": "Space Segment", "segment": "space",
         "systems": [{"name": "Spacecraft", "spacecraft": True, "quantity": 4,
                      "performance": {"constellation": True, "orbital_planes": 1, "sats_per_plane": 4}}]},
        {"name": "Ground Segment", "segment": "ground", "systems": [{"name": "Ground Station", "domain": "ground"}]},
        {"name": "Launch Segment", "segment": "launch", "systems": []},
        {"name": "User Segment", "segment": "user", "systems": []},
        {"name": "Operations", "segment": "operations", "systems": []},
    ],
    "lunar": [
        {"name": "Space Segment", "segment": "space", "systems": [{"name": "Spacecraft", "spacecraft": True}]},
        {"name": "Ground Segment (DSN)", "segment": "ground",
         "systems": [{"name": "DSN Ground Station", "domain": "ground"}]},
        {"name": "Launch Segment", "segment": "launch", "systems": []},
        {"name": "Operations", "segment": "operations", "systems": []},
    ],
    "hybrid": [
        {"name": "Space Segment", "segment": "space", "systems": [{"name": "Spacecraft", "spacecraft": True}]},
        {"name": "Ground Segment", "segment": "ground",
         "systems": [{"name": "Ground Station", "domain": "ground"},
                     {"name": "Ground Sensors", "domain": "ground"},
                     {"name": "Data Centre", "domain": "ground"}]},
        {"name": "Operations", "segment": "operations", "systems": []},
    ],
    "blank": [],
}


def tree_level(element_type: str | None) -> int | None:
    return TREE_LEVEL.get(element_type or "")


def allowed_children(parent: dict | None) -> tuple[str, ...]:
    """Element types that may be created under ``parent`` (None = study root)."""
    if parent is None:
        return ALLOWED_CHILDREN[None]
    return ALLOWED_CHILDREN.get(parent.get("element_type") or "", tuple(TREE_TYPES))


def placement_error(child_type: str | None, parent: dict | None) -> dict | None:
    """None when a ``child_type`` element may go under ``parent``; else a bilingual reason.

    Only product-tree types are checked (mode, logical and software elements are free)."""
    if (child_type or "") not in TREE_TYPES:
        return None
    if parent is not None and (parent.get("element_type") or "") not in TREE_TYPES:
        return None
    ok = allowed_children(parent)
    if child_type in ok:
        return None
    where = parent.get("element_type") if parent else "study root"
    hint_en, hint_fr = "", ""
    if parent is not None and parent.get("element_type") == "segment" and child_type in ("subsystem", "component"):
        hint_en = " Add a Spacecraft (or another system) under the segment first, then its subsystems and equipment."
        hint_fr = " Ajouter d’abord un satellite (ou un autre système) sous le segment, puis ses sous-systèmes et équipements."
    return {
        "error": "product_tree_level",
        "child_type": child_type, "parent_type": where, "allowed": list(ok),
        "message": {
            "en": f"A {child_type} cannot sit directly under a {where} (ECSS product tree: mission → segment → "
                  f"system → subsystem → equipment).{hint_en}",
            "fr": f"Un élément « {child_type} » ne peut pas être directement sous « {where} » (arbre produit ECSS : "
                  f"mission → segment → système → sous-système → équipement).{hint_fr}",
        },
    }


# ───────────────────────────────────────────────────────────── spacecraft

def is_space_segment(e: dict, index: dict[str, dict]) -> bool:
    return e.get("element_type") == "segment" and effective_segment(e, index) == "space"


def is_spacecraft_like(e: dict) -> bool:
    """A system that is a spacecraft by its name, class, constellation data or quantity."""
    perf = e.get("performance") or {}
    if isinstance(perf, dict) and (perf.get("spacecraft_class") or perf.get("constellation") or perf.get("migrated_spacecraft")):
        return True
    if int(e.get("quantity") or 1) > 1:
        return True
    return bool(_SPACECRAFT_NAME.search(str(e.get("name") or "")))


def _kids(elements: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for e in elements:
        if e.get("parent_id"):
            out.setdefault(e["parent_id"], []).append(e)
    return out


def is_misplaced_subsystem(e: dict, kids: dict[str, list[dict]]) -> bool:
    """A ``system`` under a space segment that is really a spacecraft subsystem (EPS, AOCS...)."""
    if e.get("element_type") != "system" or (e.get("subsystem_domain") or "") not in BUS_DOMAINS:
        return False
    if is_spacecraft_like(e):
        return False
    return not any(c.get("element_type") in ("system", "subsystem") for c in kids.get(e["id"], []))


def _order(e: dict) -> tuple:
    """Oldest first; elements not yet reloaded from the DB (no created_at) last, in the
    order they were made (the sorts are stable over insertion order)."""
    ca = e.get("created_at")
    return (0, str(ca)) if ca else (1, "")


def spacecraft_systems(elements: Iterable[dict]) -> list[dict]:
    """The spacecraft of a study: live systems directly under a space segment that are not
    misplaced subsystems, oldest first (a root-level space system when there is no segment)."""
    els = live(elements)
    idx = by_id(els)
    kids = _kids(els)
    out = []
    for e in els:
        if e.get("element_type") != "system":
            continue
        p = idx.get(e.get("parent_id") or "")
        if p is not None and is_space_segment(p, idx) and not is_misplaced_subsystem(e, kids):
            out.append(e)
    if not out:   # legacy / API-built trees: a root system in the space segment
        out = [e for e in els if e.get("element_type") == "system" and not e.get("parent_id")
               and effective_segment(e, idx) == "space"]
    return sorted(out, key=_order)


def primary_spacecraft(elements: Iterable[dict], spacecraft_id: str | None = None) -> dict | None:
    scs = spacecraft_systems(elements)
    if spacecraft_id:
        for s in scs:
            if s["id"] == spacecraft_id:
                return s
    return scs[0] if scs else None


def subtree_ids(elements: Iterable[dict], root_id: str) -> set[str]:
    kids = _kids(live(elements))
    out, stack = set(), [root_id]
    while stack:
        cur = stack.pop()
        if cur in out:
            continue
        out.add(cur)
        stack.extend(c["id"] for c in kids.get(cur, []))
    return out


def scope_to_spacecraft(elements: list[dict], spacecraft_id: str | None = None) -> list[dict]:
    """Elements of one spacecraft when the study has several (the stack builder lays out one
    CubeSat): everything outside the other spacecraft's subtrees. One spacecraft: unchanged."""
    scs = spacecraft_systems(elements)
    if len(scs) < 2:
        return elements
    keep = primary_spacecraft(elements, spacecraft_id)
    drop: set[str] = set()
    for s in scs:
        if keep is None or s["id"] != keep["id"]:
            drop |= subtree_ids(elements, s["id"])
    return [e for e in elements if e.get("id") not in drop]


# ───────────────────────────────────────────────────────────── checks

def misplaced(elements: Iterable[dict]) -> list[dict]:
    """Live elements that break the level rules (e.g. a subsystem directly under a segment)."""
    els = live(elements)
    idx = by_id(els)
    kids = _kids(els)
    out = []
    for e in els:
        p = idx.get(e.get("parent_id") or "")
        if p is None:   # roots (and orphans) are not judged: legacy trees start at any level
            continue
        if placement_error(e.get("element_type"), p) is not None:
            out.append(e)
        elif p is not None and is_space_segment(p, idx) and is_misplaced_subsystem(e, kids):
            out.append(e)
    return out


# ───────────────────────────────────────────────────────────── migration

def plan_migration(elements: Iterable[dict], new_id) -> dict[str, Any]:
    """What it takes to give every space segment a proper Spacecraft level.

    For each live space segment with subsystems or components directly under it (or
    ``system`` elements that are really subsystems: a bus domain, not spacecraft-like,
    nothing below them but equipment):

    * one genuine spacecraft already under the segment → they move under it;
    * none → a ``Spacecraft`` system is created under the segment and they move under it;
    * two or more → ambiguous, left alone and reported (the gate check flags it).

    Returns ``{"create": [element], "update": [{"id", "changes"}], "ambiguous": [segment id]}``.
    Idempotent: a migrated tree plans nothing. ``new_id()`` makes ids (uuid hex in the app).
    """
    els = live(elements)
    idx = by_id(els)
    kids = _kids(els)
    create: list[dict] = []
    update: list[dict] = []
    ambiguous: list[str] = []
    for seg in sorted(els, key=_order):
        if not is_space_segment(seg, idx):
            continue
        children = sorted(kids.get(seg["id"], []), key=_order)
        wrong = [c for c in children if c.get("element_type") in ("subsystem", "component")
                 or is_misplaced_subsystem(c, kids)]
        if not wrong:
            continue
        genuine = [c for c in children if c.get("element_type") == "system" and c not in wrong]
        if len(genuine) > 1:
            ambiguous.append(seg["id"])
            continue
        if genuine:
            target = genuine[0]["id"]
        else:
            first = wrong[0]
            sc = {
                "id": new_id(), "study_id": seg.get("study_id"), "name": "Spacecraft",
                "element_type": "system", "parent_id": seg["id"],
                "segment": seg.get("segment") or "space", "description": "",
                "quantity": int(seg.get("quantity") or 1), "version": 1, "deleted_at": None,
                "in_scope": True, "frozen": False, "margin_percent": 20.0,
                "diagram_x": first.get("diagram_x"), "diagram_y": first.get("diagram_y"),
                "performance": {"migrated_spacecraft": True},
            }
            create.append(sc)
            target = sc["id"]
        for c in wrong:
            changes: dict[str, Any] = {"parent_id": target}
            if c.get("element_type") == "system":
                changes["element_type"] = "subsystem"
            update.append({"id": c["id"], "changes": changes})
    return {"create": create, "update": update, "ambiguous": ambiguous}


def apply_plan(elements: list[dict], plan: dict[str, Any]) -> list[dict]:
    """The element list after ``plan`` (pure; for tests and dry runs)."""
    out = [dict(e) for e in elements]
    idx = {e["id"]: e for e in out}
    for u in plan["update"]:
        if u["id"] in idx:
            idx[u["id"]].update(u["changes"])
    return out + [dict(c) for c in plan["create"]]


def default_tree(architecture: str) -> list[dict[str, Any]]:
    if architecture not in ARCHITECTURES:
        raise KeyError(architecture)
    return ARCHITECTURES[architecture]
