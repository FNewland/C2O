"""SpaceCDF — plain-data helpers shared by the deterministic rule engines.

The engines (margin_policy, cds_checks, fmeca_library, gate_checks) take plain
lists/dicts so they are testable without the server caches. This module holds
the small tree and knowledge-base helpers they share.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Iterable

NON_HARDWARE_TYPES = frozenset({"mission", "segment", "mode", "logical", "software"})
GROUND_SEGMENTS = frozenset({"ground", "operations", "user"})


def live(elements: Iterable[dict]) -> list[dict]:
    return [e for e in elements if not e.get("deleted_at")]


def by_id(elements: Iterable[dict]) -> dict[str, dict]:
    return {e["id"]: e for e in elements if e.get("id")}


def children_map(elements: Iterable[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for e in elements:
        if e.get("parent_id"):
            out.setdefault(e["parent_id"], []).append(e)
    return out


def effective_segment(e: dict, index: dict[str, dict]) -> str:
    """The element's segment, inherited from the nearest ancestor that sets one.

    Elements default to ``space`` in the DB, so an explicit non-space value on any
    ancestor (a ground segment element) wins over a default on a descendant.
    """
    seen = 0
    cur: dict | None = e
    found = e.get("segment") or "space"
    while cur is not None and seen < 50:
        seg = cur.get("segment")
        if seg and seg != "space":
            return seg
        if cur.get("element_type") == "segment" and cur.get("name", "").lower().startswith("ground"):
            return "ground"
        cur = index.get(cur.get("parent_id") or "")
        seen += 1
    return found


def space_hardware(elements: list[dict]) -> list[dict]:
    """Live space-segment hardware elements (no mission/segment/mode/software)."""
    els = live(elements)
    idx = by_id(els)
    return [e for e in els
            if e.get("element_type") not in NON_HARDWARE_TYPES
            and effective_segment(e, idx) not in GROUND_SEGMENTS]


def leaves_with(elements: list[dict], field: str) -> list[dict]:
    """Elements carrying ``field`` > 0 with no descendant that also carries it.

    This is the roll-up rule that avoids counting a subsystem's estimate AND its
    components: the most detailed level that has a value wins.
    """
    hw = space_hardware(elements)
    kids = children_map(hw)

    def has_value_below(eid: str, depth: int = 0) -> bool:
        if depth > 30:
            return False
        for c in kids.get(eid, []):
            if (c.get(field) or 0) > 0 or has_value_below(c["id"], depth + 1):
                return True
        return False

    return [e for e in hw if (e.get(field) or 0) > 0 and not has_value_below(e["id"])]


def qty(e: dict) -> int:
    try:
        return max(1, int(e.get("quantity") or 1))
    except (TypeError, ValueError):
        return 1


@lru_cache(maxsize=1)
def _kb_index() -> dict[str, dict]:
    try:
        from spacecdf_kb.loader import KnowledgeBase
    except ImportError:  # pragma: no cover — KB package always installed with the server
        return {}
    out: dict[str, dict] = {}
    for comp in KnowledgeBase().search_components():
        if comp.get("id"):
            out[str(comp["id"])] = comp
    return out


def kb_component(e: dict) -> dict | None:
    """The KB entry an element was created from (by ``kb_component_id``)."""
    kid = e.get("kb_component_id")
    return _kb_index().get(str(kid)) if kid else None


def perf(e: dict) -> dict:
    p = e.get("performance")
    if p is None:
        p = e.get("performance_json")
    return p if isinstance(p, dict) else {}


def param(params: dict[str, Any], pid: str) -> float | None:
    v = params.get(pid)
    if isinstance(v, dict):
        v = v.get("value")
    elif hasattr(v, "value"):
        v = v.value
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    if isinstance(v, (int, float)):
        return float(v)
    return None


def form_factor(elements: list[dict], params: dict[str, Any], explicit: str | None = None) -> str | None:
    """CubeSat form factor: explicit > structure KB part > ``structure.form_factor_u``
    > element performance ``form_factor``. None when the design is not a CubeSat."""
    if explicit:
        return explicit.strip().upper().replace(" ", "")
    hw = sorted(space_hardware(elements),
                key=lambda e: 0 if (kb_component(e) or {}).get("category") == "cubesat_structure" else 1)
    for e in hw:
        kb = kb_component(e) or {}
        if kb.get("category") == "deployer":
            continue
        ff = kb.get("form_factor") or perf(e).get("form_factor")
        if ff and str(ff).upper().endswith("U"):
            return str(ff).upper().replace(" ", "")
    u = param(params, "structure.form_factor_u")
    if u:
        return f"{u:g}U"
    return None
