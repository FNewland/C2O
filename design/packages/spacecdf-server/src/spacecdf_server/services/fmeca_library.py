"""SpaceCDF — FMECA skeleton from a failure-mode library (replaces AI "FMEA generation").

``configs/failure_modes.yaml`` holds a failure-mode library keyed by unit type. Each
space-segment hardware element is matched to a type (KB category, then name keyword,
then subsystem domain) and receives that type's modes, adjusted per element:

* redundancy (``redundancy_type`` set or ``quantity`` > 1) → severity − 1;
* TRL < 6 (element or KB part)                          → occurrence + 1;
* the element has a ``data`` interface (telemetry)      → detection − 1.

The method follows ECSS-Q-ST-30-02C; the library, the 1–5 scales and the thresholds
are C2O defaults (see the file header). The rows have the same fields as the existing
FMECA table (``services/fmeca.FailureMode``) plus EN/FR text, so the FMECA panel can
show them and the designer edits from there.
"""
from __future__ import annotations

from typing import Any

from . import rule_config as rc
from .rule_inputs import children_map, kb_component, space_hardware

CONFIG = "failure_modes"
_REDUNDANT = frozenset({"cold", "hot", "warm", "dual", "n+1", "2oo3", "triple", "standby", "active", "redundant"})


def _redundant(e: dict) -> bool:
    rt = str(e.get("redundancy_type") or "").strip().lower()
    if rt in _REDUNDANT:
        return True
    try:
        return int(e.get("quantity") or 1) > 1
    except (TypeError, ValueError):
        return False


def match_type(e: dict, cfg: dict) -> str | None:
    kb = kb_component(e) or {}
    cat = kb.get("category")
    types = cfg["types"]
    if cat:
        for tid, t in types.items():
            if cat in (t.get("kb_categories") or []):
                return tid
    name = (e.get("name") or "").lower()
    for tid, t in types.items():
        if any(k in name for k in (t.get("keywords") or [])):
            return tid
    dom = e.get("subsystem_domain")
    if dom:
        for tid, t in types.items():
            if dom in (t.get("domains") or []):
                return tid
    return None


def _clamp(v: int) -> int:
    return max(1, min(5, v))


def build_skeleton(elements: list[dict], interfaces: list[dict] | None = None) -> dict[str, Any]:
    """FMECA rows for every leaf hardware element (and childless subsystems)."""
    cfg = rc.load(CONFIG)
    hw = space_hardware(elements)
    kids = children_map(hw)
    data_linked: set[str] = set()
    for i in interfaces or []:
        if i.get("deleted_at") or i.get("status") == "rejected":
            continue
        if str(i.get("type") or i.get("interface_type") or "").lower() == "data":
            data_linked.update(x for x in (i.get("from_element_id"), i.get("to_element_id")) if x)

    crit_rpn = int(cfg.get("critical_rpn", 60))
    sp_sev = int(cfg.get("single_point_severity", 4))
    ref_method = rc.ref_of(cfg, {"source": "ecss_q_30_02"})
    ref_lib = rc.ref_of(cfg, {"source": "c2o_default"})
    rows: list[dict[str, Any]] = []
    unmatched: list[str] = []
    for e in hw:
        if e.get("element_type") not in ("component", "subsystem"):
            continue
        if e.get("element_type") == "subsystem" and kids.get(e["id"]):
            continue   # the components carry the modes
        tid = match_type(e, cfg)
        modes = (cfg["types"][tid]["modes"] if tid else cfg["generic"]["modes"])
        if not tid:
            unmatched.append(e["id"])
        kb = kb_component(e) or {}
        trl = e.get("trl") if e.get("trl") is not None else kb.get("trl")
        red = _redundant(e)
        for m in modes:
            s = _clamp(m["s"] - (1 if red else 0))
            o = _clamp(m["o"] + (1 if trl is not None and int(trl) < 6 else 0))
            d = _clamp(m["d"] - (1 if e["id"] in data_linked else 0))
            rpn = s * o * d
            rows.append({
                "id": f"{m['id']}:{e['id']}", "library_id": m["id"], "library_type": tid or "generic",
                "element_id": e["id"], "component": e.get("name", ""),
                "mode": m["mode"], "cause": m["cause"], "local_effect": m["local"],
                "system_effect": m["system"], "mitigation": m["mitigation"],
                "severity": s, "occurrence": o, "detection": d, "rpn": rpn,
                "severity_label": cfg["severity_categories"].get(s) or cfg["severity_categories"].get(str(s)),
                "single_point": s >= sp_sev and not red, "critical": rpn >= crit_rpn,
                "adjustments": {"redundant": red, "low_trl": trl is not None and int(trl) < 6,
                                "telemetry": e["id"] in data_linked},
            })
    rows.sort(key=lambda r: -r["rpn"])
    return {
        "rows": rows,
        "summary": {"modes": len(rows), "elements": len({r["element_id"] for r in rows}),
                    "single_points": sum(1 for r in rows if r["single_point"]),
                    "critical": sum(1 for r in rows if r["critical"]),
                    "max_rpn": max((r["rpn"] for r in rows), default=0),
                    "generic_only": len(unmatched)},
        "method_standard_ref": ref_method["standard_ref"],
        "library_standard_ref": ref_lib["standard_ref"], "library_c2o_default": True,
        "thresholds": {"critical_rpn": crit_rpn, "single_point_severity": sp_sev},
    }
