"""Interface ↔ interface requirement rules (design rules §1.2, IF-01 … IF-05; fixes F5/F6).

"Whenever we have an interface, we create an interface requirement, and vice versa."

* **IF-01** an accepted interface gets one requirement per matching template of
  ``configs/interface_requirement_templates.yaml`` (EARS, EN + FR): level ``interface``,
  status ``draft``, origin ``rule:IF-01``, relation ``allocates`` requirement → interface
  (both directions are served). Values come from the link properties, the power line and
  bus node it is bound to and the KB; a missing value renders ``TBD``.
* **IF-02** an interface requirement created without an interface (it names two elements
  and a type) proposes the interface (``status = suggested``, ``origin = rule:IF-02``) or
  links the existing one; one with no endpoints is reported as "without interface".
* **IF-03** an interface change re-renders its requirements: a draft the user did not edit
  follows silently; an approved or edited one is marked ``review = "stale"`` with the new
  text in ``proposed_text`` for the owner seat. The bilateral agreement is reset.
* **IF-04** an interface rejected or deleted retires its untouched drafts and proposes the
  retirement (``review = "retire"``) of the others.
* **IF-05** agreement: the provider and consumer seats each agree the interface; the state
  is identified → defined (requirements exist) → agreed (both seats) → verified (all its
  requirements verified).

Nov 2026 (W2.07), so a study with a written interface baseline gets a short IRD, not one row
per template per link:

* **One IRD row set per subsystem boundary.** Links are grouped by (subsystem of the provider,
  subsystem of the consumer, type, subtype); only the highest link of a group (the subsystem
  link before the unit links under it) gets template rows, and they list the others in
  ``ir_json.covers_interface_ids``. Links inside one subsystem (camera → payload controller) are
  that subsystem's own design and get no IRD row.
* **A user's interface requirement covers the templates** of its interface type on the same
  subsystem pair (``IF-EPS-ALL-01`` "EPS ↔ all units" covers every power link of the EPS); the
  template is then reported as covered by that code, not instantiated.
* **No all-TBD rows.** A template whose every value is unknown is offered as a suggestion
  (``suggestions(study_id)``, ``GET …/interface-requirements``) instead of a "TBD bus TBD" row.
* Imported interface requirements name their end points by element name
  (``ir_json.endpoint_names``) and their ICD row (``ir_json.icd_ref``): :func:`link_imported`
  links them to the accepted interface(s) between those elements, records the ICD row as an
  exchange item of the interface and adds an ``allocates`` relation requirement → exchange item.
* Owner seats: a requirement placed on a disposal device (drag sail) is owned by the Propulsion
  seat (PI rule).

:func:`ird_status` is pure and feeds the PDR-EC-02 gate criterion.
"""
from __future__ import annotations

import contextvars
import hashlib
import json
import logging
import math
import os
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

from .electrical_rules import _fmt, _num, element_power_w

logger = logging.getLogger(__name__)

ORIGIN = "rule:IF-01"
ORIGIN_IF02 = "rule:IF-02"
TYPE_ABBR = {"power": "PWR", "data": "DAT", "rf": "RF", "mechanical": "MEC", "thermal": "THM", "timing": "TIM",
             "optical": "OPT", "electrical_signal": "SIG", "fluid": "FLU"}
APPROVED = ("approved", "verified")
_busy: contextvars.ContextVar[bool] = contextvars.ContextVar("ird_sync_busy", default=False)


# ═══════════════════════════════════════════════════════════════════════
# Templates
# ═══════════════════════════════════════════════════════════════════════

def templates_path() -> Path:
    env = os.environ.get("SPACECDF_IR_TEMPLATES")
    if env:
        return Path(env)
    for parent in Path(__file__).resolve().parents:
        cand = parent / "configs" / "interface_requirement_templates.yaml"
        if cand.exists():
            return cand
    return Path(__file__).resolve().parents[5] / "configs" / "interface_requirement_templates.yaml"


@lru_cache(maxsize=4)
def _load_cached(path: str, mtime: float) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_templates() -> dict:
    p = templates_path()
    return _load_cached(str(p), p.stat().st_mtime)


def templates_for(iface: dict) -> list[dict]:
    t = iface.get("type") or iface.get("interface_type")
    sub = iface.get("subtype")
    out = []
    for tpl in load_templates().get("templates") or []:
        if tpl.get("type") != t:
            continue
        subs = tpl.get("subtypes")
        if subs is not None and sub not in subs:
            continue
        out.append(tpl)
    return out


# ═══════════════════════════════════════════════════════════════════════
# Values and rendering
# ═══════════════════════════════════════════════════════════════════════

def _line_for(iface: dict, rows: dict[str, list[dict]]) -> dict | None:
    live = [r for r in rows.get("lines", []) if r.get("status") != "rejected" and not r.get("deleted_at")]
    to = iface["to_element_id"]
    for ln in live:
        if to in (ln.get("load_element_ids") or []) and ln.get("eps_element_id") == iface["from_element_id"]:
            return ln
    for ln in live:
        if to in (ln.get("load_element_ids") or []):
            return ln
    return None


def _node_for(iface: dict, rows: dict[str, list[dict]]) -> tuple[dict | None, dict | None]:
    buses = {b["id"]: b for b in rows.get("buses", []) if b.get("status") != "rejected" and not b.get("deleted_at")}
    nodes = [n for n in rows.get("nodes", []) if n.get("status") != "rejected" and not n.get("deleted_at")]
    proto = (iface.get("properties") or {}).get("protocol")
    best = None
    for n in nodes:
        if n.get("element_id") != iface["to_element_id"] or n["bus_id"] not in buses:
            continue
        b = buses[n["bus_id"]]
        if n.get("interface_id") == iface["id"]:
            return n, b
        if b.get("master_element_id") == iface["from_element_id"] and (not proto or b.get("protocol") == proto):
            best = best or (n, b)
    return best or (None, None)


def resolve_values(iface: dict, els: dict[str, dict], ctx: Any, rows: dict[str, list[dict]]) -> dict[str, Any]:
    """Placeholder values for one interface (None = unknown → "TBD")."""
    props = iface.get("properties") or {}
    f_el = els.get(iface["from_element_id"]) or {}
    t_el = els.get(iface["to_element_id"]) or {}
    f_u = ctx.units.get(f_el.get("id")) if ctx and f_el else None
    t_u = ctx.units.get(t_el.get("id")) if ctx and t_el else None
    f_kb = (f_u.kb if f_u else None) or {}
    t_kb = (t_u.kb if t_u else None) or {}
    v: dict[str, Any] = {"from": f_el.get("name") or "TBD", "to": t_el.get("name") or "TBD"}
    for k, val in props.items():
        if isinstance(val, (str, int, float)) and not isinstance(val, bool):
            v[k] = val
    t = iface.get("type") or iface.get("interface_type")
    if t == "power":
        rail = _num(props.get("rail_voltage"))
        v["rail_voltage"] = rail
        ln = _line_for(iface, rows)
        v["line"] = ln.get("line_no") if ln else None
        v["lcl_limit_a"] = _num(ln.get("lcl_limit_a")) if ln else None
        p = element_power_w(t_el, peak=True) if t_el else None
        v["current_peak_a"] = (math.ceil(p / rail * 100 - 1e-9) / 100.0) if (p and rail) else None
        if iface.get("subtype") == "battery_bus":
            from .electrical_kb import kb_voltage_range
            _, lo, hi = kb_voltage_range(f_kb)
            v["v_min"], v["v_max"] = lo, hi
        if iface.get("subtype") == "array_input":
            perf = f_kb.get("performance") or {}
            v["p_eol"] = _num(perf.get("power_eol_w") or perf.get("power_w") or f_kb.get("power_w"))
    elif t == "data":
        node, bus = _node_for(iface, rows)
        v["protocol"] = props.get("protocol")
        v["bus"] = bus.get("name") if bus else None
        v["address"] = (f"0x{int(node['address']):02X}" if node and node.get("address") is not None else None)
        rate = _num(props.get("data_rate_bps"))
        if iface.get("subtype") != "payload_data":
            rate = _num(bus.get("bit_rate_bps")) if bus else rate
        v["rate"] = int(rate) if rate else None
        v["lanes"] = props.get("lanes")                       # csi2 (W2.07)
        v["accuracy_us"] = _num(props.get("accuracy_us"))    # timing (W2.07)
    elif t == "rf":
        v["band"] = props.get("band")
        r = _num(props.get("data_rate_bps"))
        v["rate"] = int(r) if r else None
        v["connector"] = props.get("connector")
    elif t == "mechanical":
        v["mount_type"] = props.get("mount_type")
    elif t == "thermal":
        temp = t_kb.get("operating_temp_c") or (t_kb.get("performance") or {}).get("operating_temp_c") \
            or (t_el.get("performance") or {}).get("operating_temp_c")
        if isinstance(temp, (list, tuple)) and len(temp) >= 2:
            v["t_min"], v["t_max"] = temp[0], temp[1]
        else:
            v["t_min"] = v["t_max"] = None
        v["heater_power_w"] = _num(props.get("heater_power_w"))
    elif t == "timing":
        v["accuracy_us"] = _num(props.get("accuracy_us"))
    elif t == "optical":
        v["fov_deg"] = _num(props.get("fov_deg") or (t_kb.get("performance") or {}).get("fov_deg"))
    elif t == "electrical_signal":
        v["signal"] = props.get("signal") or iface.get("subtype")
        v["inhibit_count"] = props.get("inhibit_count")
    elif t == "fluid":
        v["fitting"] = props.get("fitting") or props.get("connector")
    return v


_PH = re.compile(r"\{([a-z_]+)\}")


def render(tpl: dict, values: dict[str, Any]) -> tuple[dict[str, str], list[str]]:
    missing: list[str] = []

    def sub(m: re.Match, fr: bool = False) -> str:
        k = m.group(1)
        val = values.get(k)
        if val is None or val == "":
            if k not in missing:
                missing.append(k)
            return "TBD"
        if isinstance(val, float):
            s = _fmt(val)
            return s.replace(".", ",") if fr else s      # French decimal comma (STYLE_FR.md)
        return str(val)

    text = tpl.get("text") or {}
    return {"en": _PH.sub(sub, text.get("en", "")),
            "fr": _PH.sub(lambda m: sub(m, True), text.get("fr", text.get("en", "")))}, missing


def _hash(obj: Any) -> str:
    return hashlib.sha1(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:16]


def agreement_hash(iface: dict) -> str:
    """What both parties agree on: type, subtype, endpoints, direction and properties."""
    return _hash({k: iface.get(k) for k in ("type", "subtype", "from_element_id", "to_element_id", "direction")}
                 | {"properties": {k: v for k, v in (iface.get("properties") or {}).items()
                                   if not str(k).endswith("_port_id")}})


# ═══════════════════════════════════════════════════════════════════════
# Pure status (gate)
# ═══════════════════════════════════════════════════════════════════════

def interface_irs(reqs: list[dict]) -> dict[str, list[dict]]:
    """Interface id → its live interface requirements, including those that cover it (W2.07:
    the subsystem link's rows cover the unit links under it; a user row covers its type)."""
    out: dict[str, list[dict]] = {}
    for r in reqs:
        if r.get("level") != "interface" or r.get("status") == "retired":
            continue
        ir = r.get("ir_json") or {}
        ids = [ir.get("interface_id")] + list(ir.get("interface_ids") or []) + list(ir.get("covers_interface_ids") or [])
        for iid in dict.fromkeys(i for i in ids if i):
            out.setdefault(iid, []).append(r)
    return out


def agreement_state(iface: dict, irs: list[dict]) -> str:
    if irs and all(r.get("status") == "verified" for r in irs):
        return "verified"
    ag = iface.get("agreement_json") or {}
    if ag.get("provider") and ag.get("consumer") and ag.get("inputs_hash") == agreement_hash(iface):
        return "agreed"
    return "defined" if irs else "identified"


def agreement_view(iface: dict, irs: list[dict], els: dict[str, dict]) -> dict[str, Any]:
    """``{state, provider_seat, consumer_seat, provider, consumer, reset_at}`` for the API."""
    ag = iface.get("agreement_json") or {}
    current = ag.get("inputs_hash") == agreement_hash(iface)
    return {
        "state": agreement_state(iface, irs),
        "provider_seat": owner_seat(els.get(iface["from_element_id"]), els),
        "consumer_seat": owner_seat(els.get(iface["to_element_id"]), els),
        "provider": ag.get("provider") if current else None,
        "consumer": ag.get("consumer") if current else None,
        "reset_at": ag.get("reset_at"),
    }


def ird_status(interfaces: list[dict], reqs: list[dict]) -> dict[str, Any]:
    """IRD completeness for the PDR-EC-02 criterion: every accepted link has at least one
    approved, current interface requirement and both parties agreed it."""
    by_if = interface_irs(reqs)
    acc = [i for i in interfaces if i.get("status") == "accepted" and not i.get("deleted_at")]
    acc_ids = {i["id"] for i in acc}
    rows = []
    for i in acc:
        irs = by_if.get(i["id"], [])
        approved = bool(irs) and any(r.get("status") in APPROVED for r in irs) \
            and not any((r.get("ir_json") or {}).get("review") for r in irs)
        state = agreement_state(i, irs)
        rows.append({"interface_id": i["id"], "requirements": len(irs), "approved": approved,
                     "agreement": state, "complete": approved and state in ("agreed", "verified")})
    orphans = [r["id"] for r in reqs if r.get("level") == "interface" and r.get("status") != "retired"
               and not ({(r.get("ir_json") or {}).get("interface_id")} | set((r.get("ir_json") or {}).get("interface_ids") or []))
               & acc_ids
               and not (r.get("ir_json") or {}).get("review")]
    stale = [r["id"] for r in reqs if r.get("level") == "interface" and r.get("status") != "retired"
             and (r.get("ir_json") or {}).get("review")]
    return {
        "accepted": len(acc),
        "with_requirements": sum(1 for x in rows if x["requirements"]),
        "approved": sum(1 for x in rows if x["approved"]),
        "agreed": sum(1 for x in rows if x["agreement"] in ("agreed", "verified")),
        "complete": sum(1 for x in rows if x["complete"]),
        "without_interface": orphans,
        "stale": stale,
        "rows": rows,
    }


# ═══════════════════════════════════════════════════════════════════════
# Sync (I/O)
# ═══════════════════════════════════════════════════════════════════════

async def _study_state(study_id: str) -> tuple[list[dict], list[dict], Any, dict[str, list[dict]]]:
    from ..db import electrical_repo
    from ..routers import elements as el
    elements = [e for e in el._elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    interfaces = [i for i in el._interfaces.values() if i.get("study_id") == study_id]
    ctx = None
    try:
        from .interface_proposer import Context, load_rules
        ctx = Context(elements, load_rules())
    except Exception:
        logger.debug("interface rules unavailable for IR values", exc_info=True)
    rows = await electrical_repo.load_all(study_id)
    return elements, interfaces, ctx, rows


def owner_seat(element: dict | None, elements: dict[str, dict]) -> str | None:
    if not element:
        return None
    from .requirement_import import PROPULSION_SEAT, owner_seat_for
    if owner_seat_for(element.get("id"), elements, None) == PROPULSION_SEAT:
        return PROPULSION_SEAT       # PI rule: the drag sail belongs to the Propulsion seat
    try:
        from ..seats import config as seat_cfg
        return seat_cfg.element_owner_seat(element, elements)
    except Exception:
        return None


def _next_code(study_id: str, itype: str, reqs: dict[str, dict]) -> str:
    abbr = TYPE_ABBR.get(itype, "GEN")
    pre = f"IR-{abbr}-"
    n = 0
    for r in reqs.values():
        c = str(r.get("code") or "")
        if r.get("study_id") == study_id and c.startswith(pre):
            try:
                n = max(n, int(c[len(pre):]))
            except ValueError:
                pass
    return f"{pre}{n + 1:03d}"


async def _link(study_id: str, req_id: str, iface_id: str, rationale: str) -> None:
    from ..db.relation_repo import create_relation
    try:
        await create_relation({"study_id": study_id, "kind": "allocates", "source_kind": "requirement",
                               "source_id": req_id, "target_kind": "interface", "target_id": iface_id,
                               "rationale": rationale})
    except Exception:
        logger.exception("IR relation failed %s -> %s", req_id, iface_id)


# ═══════════════════════════════════════════════════════════════════════
# W2.07: boundaries, coverage, suggestions, imported interface requirements
# ═══════════════════════════════════════════════════════════════════════

_BOUNDARY_TYPES = ("subsystem", "system", "segment", "mission")
#: study id → {(interface id, template id): suggestion}: templates whose every value is unknown
_SUGGESTIONS: dict[str, dict[tuple[str, str], dict]] = {}


def _boundary(el: dict | None, els: dict[str, dict]) -> str | None:
    """The subsystem (or higher) element an element belongs to, itself when it is one."""
    seen: set[str] = set()
    cur = el
    while cur is not None and cur.get("id") not in seen:
        seen.add(cur["id"])
        if (cur.get("element_type") or "") in _BOUNDARY_TYPES:
            return cur["id"]
        cur = els.get(cur.get("parent_id") or "")
    return el.get("id") if el else None


def _depth(el: dict | None, els: dict[str, dict]) -> int:
    d, seen, cur = 0, set(), el
    while cur is not None and cur.get("parent_id") and cur["id"] not in seen:
        seen.add(cur["id"])
        cur = els.get(cur["parent_id"])
        d += 1
    return d


def _is_rule(r: dict) -> bool:
    return (r.get("ir_json") or {}).get("origin") == ORIGIN


def ird_scope() -> str:
    """``boundary`` (default, W2.07): one row set per subsystem boundary; ``link``: one row set
    per accepted link, as before W2.07 (``SPACECDF_IRD_SCOPE`` or ``ird_scope`` in the templates)."""
    return (os.environ.get("SPACECDF_IRD_SCOPE") or load_templates().get("ird_scope") or "boundary").lower()


def coverage_plan(interfaces: list[dict], els: dict[str, dict], reqs: list[dict]) -> dict[str, tuple[str, str]]:
    """Interfaces that get no template rows of their own, with the reason (W2.07):
    ``("internal", subsystem id)``, ``("link", representative interface id)`` or
    ``("requirement", requirement id)``. With ``ird_scope() == "link"`` only the user-requirement
    coverage applies. Pure (but for the scope setting)."""
    per_link = ird_scope() == "link"
    live = [i for i in interfaces if i.get("status") == "accepted" and not i.get("deleted_at")
            and i.get("from_element_id") in els and i.get("to_element_id") in els]
    t = lambda i: i.get("type") or i.get("interface_type")  # noqa: E731
    bnd = {i["id"]: (_boundary(els[i["from_element_id"]], els), _boundary(els[i["to_element_id"]], els)) for i in live}
    # user requirements cover their type on their subsystem pair
    by_id = {i["id"]: i for i in live}
    user_cover: dict[tuple, str] = {}
    for r in reqs:
        if r.get("level") != "interface" or r.get("status") == "retired" or _is_rule(r):
            continue
        ir = r.get("ir_json") or {}
        names = " ".join(ir.get("endpoint_names") or []).casefold()
        for iid in dict.fromkeys([ir.get("interface_id"), *(ir.get("interface_ids") or [])]):
            i = by_id.get(iid or "")
            if not i:
                continue
            a, b = bnd[i["id"]]
            user_cover.setdefault((a, b, t(i)), r["id"])
            user_cover.setdefault((b, a, t(i)), r["id"])
            if " all " in f" {names} ":
                user_cover.setdefault((a, "*", t(i)), r["id"])
                user_cover.setdefault(("*", a, t(i)), r["id"])
    plan: dict[str, tuple[str, str]] = {}
    groups: dict[tuple, list[dict]] = {}
    for i in live:
        a, b = bnd[i["id"]]
        f_el, t_el = els[i["from_element_id"]], els[i["to_element_id"]]
        if not per_link and a == b and (f_el.get("element_type") not in _BOUNDARY_TYPES
                                        or t_el.get("element_type") not in _BOUNDARY_TYPES):
            plan[i["id"]] = ("internal", a or "")
            continue
        rid = user_cover.get((a, b, t(i))) or user_cover.get((a, "*", t(i))) or user_cover.get(("*", b, t(i)))
        if rid:
            plan[i["id"]] = ("requirement", rid)
            continue
        groups.setdefault((a, b, t(i), i.get("subtype")) if not per_link else (i["id"],), []).append(i)
    for members in groups.values():
        members.sort(key=lambda i: (_depth(els[i["from_element_id"]], els) + _depth(els[i["to_element_id"]], els), i["id"]))
        for i in members[1:]:
            plan[i["id"]] = ("link", members[0]["id"])
    return plan


def suggestions(study_id: str) -> list[dict]:
    """Template rows not made because every value is unknown (fill the interface, then sync),
    as found by the last sync (see :func:`compute_suggestions`)."""
    return sorted(_SUGGESTIONS.get(study_id, {}).values(), key=lambda x: (x.get("interface_name") or "", x["template_id"], x["text"].get("en", "")))


async def compute_suggestions(study_id: str) -> list[dict]:
    """The suggestions from the current state, without writing anything (a loaded or restarted
    study has no sync yet)."""
    from ..routers.requirements import _requirements, ensure_requirements_loaded
    if ird_scope() == "link":
        return []
    await ensure_requirements_loaded()
    elements, interfaces, ctx, rows = await _study_state(study_id)
    els = {e["id"]: e for e in elements}
    plan = coverage_plan(interfaces, els, [r for r in _requirements.values() if r.get("study_id") == study_id])
    out: dict[tuple[str, str], dict] = {}
    for iface in interfaces:
        if iface.get("status") != "accepted" or iface.get("deleted_at") or iface["id"] in plan \
                or iface["from_element_id"] not in els or iface["to_element_id"] not in els:
            continue
        values = resolve_values(iface, els, ctx, rows)
        for tpl in templates_for(iface):
            texts, missing = render(tpl, values)
            need = list(tpl.get("values") or [])
            if need and set(need) <= set(missing):
                out[(iface["id"], tpl["id"])] = {"interface_id": iface["id"], "template_id": tpl["id"],
                                                 "interface_name": iface.get("name") or "",
                                                 "text": texts, "missing": missing}
    _SUGGESTIONS[study_id] = out
    return suggestions(study_id)


_TYPE_WORDS = (
    ("power", ("power line", "power lines", "power", "supply", "battery voltage")),
    ("rf", ("(rf)", " rf ", "radio frequency", "downlink", "uplink")),
    ("mechanical", ("deployer", "rail", "mount", "mechanical")),
    ("timing", ("pps", "time reference")),
    ("electrical_signal", ("release", "timer", "inhibit", "deployment switch")),
    ("data", ("data", "can bus", "csp", "csi-2", "telemetry", "telecommand", "protocol", "file", "products")),
)
_ENDPOINT_ALIASES = {
    "gnss receiver": ("gps", "gnss"), "gnss": ("gps", "gnss"), "uhf radio": ("uhf transceiver", "radio"),
    "radio": ("transceiver", "radio"), "ground station": ("gs ", "ground station"), "adcs": ("adcs",),
    "disposal timer": ("deorbit timer", "disposal timer"), "drag sail": ("drag sail",),
    "cubesat deployer": ("deployer",), "deployer": ("deployer",), "mission control": ("mission control",),
}


def infer_interface_type(r: dict) -> str | None:
    ir = r.get("ir_json") or {}
    text = f" {(ir.get('icd_ref') or '')} {r.get('text') or ''} ".casefold()
    for t, words in _TYPE_WORDS:
        if any(w in text for w in words):
            return t
    return None


def resolve_endpoint(name: str, elements: list[dict]) -> list[dict]:
    """Elements named by an end point of an imported interface requirement (several for
    "SWIR camera / VNIR camera", the user segment for "Science segment", every unit for
    "all units")."""
    from .requirement_import import resolve_element
    key = name.strip().casefold()
    if not key:
        return []
    if key in ("all units", "all", "every unit"):
        return [e for e in elements if e.get("element_type") in ("subsystem", "component")]
    hit = resolve_element(name, elements)
    if hit:
        return [e for e in elements if e["id"] == hit]
    for sep in (" / ", " and ", " & "):
        if sep in key:
            out: list[dict] = []
            for part in name.split(sep.strip() if sep != " and " else " and "):
                out += [e for e in resolve_endpoint(part, elements) if e not in out]
            return out
    words = _ENDPOINT_ALIASES.get(key, (key,))
    named = [e for e in elements if e.get("element_type") not in ("mode", "logical")]
    for w in words:
        pref = [e for e in named if (e.get("name") or "").casefold().startswith(w)]
        if pref:
            return pref
    for w in words:
        cont = [e for e in named if w in (e.get("name") or "").casefold()]
        if cont:
            return cont
    return []


def _related(el_id: str, els: dict[str, dict]) -> set[str]:
    """The element, its descendants and its ancestors up to (not including) the mission."""
    out = {el_id}
    kids: dict[str, list[str]] = {}
    for e in els.values():
        if e.get("parent_id"):
            kids.setdefault(e["parent_id"], []).append(e["id"])
    stack = [el_id]
    while stack:
        for c in kids.get(stack.pop(), []):
            if c not in out:
                out.add(c)
                stack.append(c)
    cur = els.get(el_id)
    while cur is not None and cur.get("parent_id") in els:
        cur = els[cur["parent_id"]]
        if cur.get("element_type") == "mission":
            break
        out.add(cur["id"])
    return out


async def link_imported(study_id: str) -> dict[str, int]:
    """Link interface requirements that name their end points (import) to the interfaces between
    them; propose the interface when there is none (IF-02); record the ICD row as an exchange item
    of the interface(s) with an ``allocates`` relation requirement → exchange item."""
    from ..db import exchange_item_repo as xrepo
    from ..db.relation_repo import create_relation
    from ..db.requirement_repo import db_update_requirement
    from ..routers import elements as el
    from ..routers.requirements import _requirements, ensure_requirements_loaded
    await ensure_requirements_loaded()
    elements = [e for e in el._elements.values() if e.get("study_id") == study_id and not e.get("deleted_at")]
    els = {e["id"]: e for e in elements}
    ifaces = [i for i in el._interfaces.values() if i.get("study_id") == study_id and not i.get("deleted_at")
              and i.get("status") != "rejected"]
    counts = {"linked": 0, "proposed": 0, "exchange_items": 0, "unresolved": 0}
    items = {x.get("name"): x for x in (await xrepo.list_exchange_items_by_study(study_id))}
    for r in [r for r in _requirements.values() if r.get("study_id") == study_id]:
        ir = dict(r.get("ir_json") or {})
        names = ir.get("endpoint_names") or []
        if r.get("level") != "interface" or r.get("status") == "retired" or _is_rule(r) or len(names) < 2:
            continue
        live_ids = {i["id"] for i in ifaces}
        if ir.get("linked_at") and ir.get("interface_ids") and set(ir["interface_ids"]) <= live_ids \
                and (ir.get("exchange_item_ids") or not ir.get("icd_ref")):
            continue                     # already linked and nothing it names has gone
        a_set = resolve_endpoint(names[0], elements)
        b_set = resolve_endpoint(names[1], elements)
        if not a_set or not b_set:
            counts["unresolved"] += 1
            continue
        a_ids = set().union(*(_related(e["id"], els) for e in a_set))
        b_ids = set().union(*(_related(e["id"], els) for e in b_set))
        itype = ir.get("interface_type") or infer_interface_type(r)
        cand = [i for i in ifaces if (i["from_element_id"] in a_ids and i["to_element_id"] in b_ids)
                or (i["from_element_id"] in b_ids and i["to_element_id"] in a_ids)]
        typed = [i for i in cand if (i.get("type") or i.get("interface_type")) == itype]
        cand = typed or cand
        if not cand:
            a, b = a_set[0], b_set[0]
            proposed = await el.store_interface({
                "study_id": study_id, "name": f"{a.get('name')} → {b.get('name')}",
                "interface_type": itype or "data", "subtype": None, "direction": "bidirectional",
                "from_element_id": a["id"], "to_element_id": b["id"], "properties": {},
                "origin": ORIGIN_IF02, "status": "suggested", "diagram_label": ir.get("icd_ref") or "",
                "rationale": {"en": f"Proposed because interface requirement {r.get('code')} names these two elements.",
                              "fr": f"Proposée parce que l'exigence d'interface {r.get('code')} nomme ces deux éléments."},
                "standard_ref": "ECSS-E-ST-10-24C (IRD → ICD)", "exchange_item_ids_json": [],
            })
            ifaces.append(proposed)
            cand = [proposed]
            counts["proposed"] += 1
        cand.sort(key=lambda i: (i.get("status") != "accepted",
                                 _depth(els.get(i["from_element_id"]), els) + _depth(els.get(i["to_element_id"]), els),
                                 i["id"]))
        ids = [i["id"] for i in cand]
        changed = ir.get("interface_id") != ids[0] or (ir.get("interface_ids") or []) != ids
        ir.update({"interface_id": ids[0], "interface_ids": ids, "interface_type": itype or ir.get("interface_type"),
                   "origin": ir.get("origin") or "import"})
        if not ir.get("linked_at"):
            ir["linked_at"] = datetime.now(timezone.utc).isoformat()
            changed = True
        if ir.get("icd_ref"):
            x = items.get(ir["icd_ref"])
            if x is None:
                x = await xrepo.create_exchange_item({"study_id": study_id, "name": ir["icd_ref"],
                                                      "kind": itype or "data",
                                                      "description": f"ICD row of {r.get('code')}"})
                items[x["name"]] = x
                counts["exchange_items"] += 1
            if ir.get("exchange_item_ids") != [x["id"]]:
                ir["exchange_item_ids"] = [x["id"]]
                changed = True
            await create_relation({"study_id": study_id, "kind": "allocates", "source_kind": "requirement",
                                   "source_id": r["id"], "target_kind": "exchange_item", "target_id": x["id"],
                                   "rationale": "ICD row of the interface requirement"})
            for i in cand:
                have = list(i.get("exchange_item_ids_json") or i.get("exchange_item_ids") or [])
                if x["id"] not in have:
                    await el.set_interface_exchange_items(i["id"], have + [x["id"]])
        for iid in ids:
            await _link(study_id, r["id"], iid, "IF-02 (import)")
        if changed:
            r["ir_json"] = ir
            await db_update_requirement(r["id"], r)
            counts["linked"] += 1
    return counts


async def sync(study_id: str, interface_ids: set[str] | None = None) -> dict[str, int]:
    """Apply IF-01/03/04 (and the agreement reset) for the study, or for some interfaces."""
    if _busy.get():
        return {"skipped": 1}
    token = _busy.set(True)
    try:
        return await _sync(study_id, interface_ids)
    finally:
        _busy.reset(token)


async def _sync(study_id: str, interface_ids: set[str] | None) -> dict[str, int]:
    from ..db.requirement_repo import db_create_requirement, db_update_requirement
    from ..routers.requirements import _requirements, ensure_requirements_loaded
    await ensure_requirements_loaded()
    try:
        linked = await link_imported(study_id)
    except Exception:
        logger.exception("linking imported interface requirements failed for %s", study_id)
        linked = {}
    elements, interfaces, ctx, rows = await _study_state(study_id)
    els = {e["id"]: e for e in elements}
    tcfg = load_templates()
    std = tcfg.get("standard_ref")
    counts = {"created": 0, "updated": 0, "stale": 0, "retired": 0, "retire_proposed": 0, "agreement_reset": 0,
              "covered": 0, "suggested": 0, "linked": linked.get("linked", 0), "proposed": linked.get("proposed", 0)}
    study_reqs = [r for r in _requirements.values() if r.get("study_id") == study_id]
    plan = coverage_plan(interfaces, els, study_reqs)
    sugg = _SUGGESTIONS.setdefault(study_id, {})
    if interface_ids is not None:
        # one link changed: re-render the links on the same subsystem boundary too (it may have
        # become, or stopped being, the boundary's representative)
        pairs = set()
        for i in interfaces:
            if i["id"] in interface_ids and i.get("from_element_id") in els and i.get("to_element_id") in els:
                pairs.add(frozenset((_boundary(els[i["from_element_id"]], els), _boundary(els[i["to_element_id"]], els))))
        interface_ids = set(interface_ids) | {
            i["id"] for i in interfaces if i.get("from_element_id") in els and i.get("to_element_id") in els
            and frozenset((_boundary(els[i["from_element_id"]], els), _boundary(els[i["to_element_id"]], els))) in pairs}
    existing: dict[tuple[str, str], dict] = {}
    for r in _requirements.values():
        if r.get("study_id") != study_id or r.get("level") != "interface":
            continue
        ir = r.get("ir_json") or {}
        if ir.get("interface_id") and ir.get("template_id"):
            existing[(ir["interface_id"], ir["template_id"])] = r

    for iface in interfaces:
        if interface_ids is not None and iface["id"] not in interface_ids:
            continue
        live = iface.get("status") == "accepted" and not iface.get("deleted_at") \
            and iface["from_element_id"] in els and iface["to_element_id"] in els
        mine = {tid: r for (iid, tid), r in existing.items() if iid == iface["id"]}
        for key in [k for k in sugg if k[0] == iface["id"]]:
            sugg.pop(key)
        if live and iface["id"] in plan:
            counts["covered"] += 1
            live = False                     # covered (W2.07): its own template rows retire
        if not live:
            for r in mine.values():
                ir = dict(r.get("ir_json") or {})
                if r.get("status") == "retired":
                    continue
                if r.get("status") == "draft" and not ir.get("edited"):
                    r["status"] = "retired"
                    ir["retired_by"] = "rule"
                    ir["review"] = None
                    counts["retired"] += 1
                elif ir.get("review") != "retire":
                    ir["review"] = "retire"
                    counts["retire_proposed"] += 1
                else:
                    continue
                r["ir_json"] = ir
                await db_update_requirement(r["id"], r)
            continue

        values = resolve_values(iface, els, ctx, rows)
        for tpl in templates_for(iface):
            texts, missing = render(tpl, values)
            h = _hash({"texts": texts})
            subject = els.get(iface["from_element_id"] if tpl.get("subject") == "from" else iface["to_element_id"])
            r = mine.get(tpl["id"])
            need = list(tpl.get("values") or [])
            if need and set(need) <= set(missing) and ird_scope() != "link":
                # every value unknown (W2.07): a suggestion, not a "TBD … TBD" requirement
                sugg[(iface["id"], tpl["id"])] = {"interface_id": iface["id"], "template_id": tpl["id"],
                                                  "interface_name": iface.get("name") or "",
                                                  "text": texts, "missing": missing}
                counts["suggested"] += 1
                if r is not None and r.get("status") == "draft" and not (r.get("ir_json") or {}).get("edited"):
                    ir = dict(r.get("ir_json") or {})
                    r["status"] = "retired"
                    ir.update({"retired_by": "rule", "review": None})
                    r["ir_json"] = ir
                    await db_update_requirement(r["id"], r)
                    counts["retired"] += 1
                continue
            if r is None:
                rid = f"REQ-{uuid4().hex[:8]}"
                r = {
                    "id": rid, "study_id": study_id, "parent_id": None, "element_id": (subject or {}).get("id"),
                    "level": "interface", "code": _next_code(study_id, iface.get("type") or "", _requirements),
                    "text": texts["en"], "rationale": None, "req_type": "interface", "category": "interface",
                    "threshold_param_path": None, "threshold_op": None, "threshold_value": None,
                    "verification_method": tpl.get("method"), "verification_phase": tpl.get("phase"),
                    "responsible_position": owner_seat(subject, els), "status": "draft",
                    "derived_from_requirement_id": None, "objective_id": None, "external_id": None,
                    "ir_json": {"origin": ORIGIN, "template_id": tpl["id"], "interface_id": iface["id"],
                                "inputs_hash": h, "text_i18n": texts, "missing": missing,
                                "values": {k: values.get(k) for k in tpl.get("values") or []},
                                "edited": False, "review": None, "proposed_text": None,
                                "standard_ref": std, "interface_type": iface.get("type"),
                                "endpoints": {"from_element_id": iface["from_element_id"],
                                              "to_element_id": iface["to_element_id"]}},
                }
                _requirements[rid] = r
                existing[(iface["id"], tpl["id"])] = r
                await db_create_requirement(r)
                await _link(study_id, rid, iface["id"], f"IF-01 {tpl['id']}")
                counts["created"] += 1
                continue
            ir = dict(r.get("ir_json") or {})
            changed = False
            if r.get("status") == "retired":
                if ir.get("retired_by") != "rule":
                    continue
                r["status"] = "draft"          # the interface is back: revive the rule's draft
                ir["retired_by"] = None
                changed = True
            if ir.get("review") == "retire":
                ir["review"] = None
                changed = True
            if ir.get("inputs_hash") != h:
                if r.get("status") == "draft" and not ir.get("edited"):
                    r["text"] = texts["en"]
                    ir.update({"inputs_hash": h, "text_i18n": texts, "missing": missing,
                               "values": {k: values.get(k) for k in tpl.get("values") or []},
                               "review": None, "proposed_text": None})
                    counts["updated"] += 1
                    changed = True
                elif ir.get("proposed_hash") != h or ir.get("review") != "stale":
                    ir.update({"review": "stale", "proposed_text": texts, "proposed_hash": h,
                               "proposed_missing": missing})
                    counts["stale"] += 1
                    changed = True
            elif ir.get("review") == "stale":
                ir.update({"review": None, "proposed_text": None, "proposed_hash": None})
                changed = True
            if changed:
                r["ir_json"] = ir
                await db_update_requirement(r["id"], r)

        # agreement (IF-05): an agreement recorded on other properties is reset (persisted
        # without a version bump, so the editor's next PATCH does not conflict)
        ag = dict(iface.get("agreement_json") or {})
        h = agreement_hash(iface)
        if (ag.get("provider") or ag.get("consumer")) and ag.get("inputs_hash") != h:
            ag.update({"provider": None, "consumer": None, "inputs_hash": h,
                       "reset_at": datetime.now(timezone.utc).isoformat()})
            iface["agreement_json"] = ag
            from ..db.element_repo import db_update_interface
            await db_update_interface(iface["id"], iface)
            counts["agreement_reset"] += 1

    # the rows that cover other links list them (ird_status counts them for those links)
    covers: dict[str, list[str]] = {}
    for iid, (why, ref) in plan.items():
        if why == "link":
            for r in [r for (i2, _), r in existing.items() if i2 == ref and r.get("status") != "retired"]:
                covers.setdefault(r["id"], []).append(iid)
        elif why == "requirement":
            covers.setdefault(ref, []).append(iid)
    for r in [r for r in _requirements.values() if r.get("study_id") == study_id and r.get("level") == "interface"]:
        want = sorted(covers.get(r["id"], []))
        ir = dict(r.get("ir_json") or {})
        if sorted(ir.get("covers_interface_ids") or []) != want:
            ir["covers_interface_ids"] = want
            r["ir_json"] = ir
            await db_update_requirement(r["id"], r)
    return counts


async def after_interface_change(iface: dict) -> None:
    """Hook for routers/elements.py (store/save/remove interface). Never raises."""
    if os.environ.get("SPACECDF_AUTO_IRD", "1") in ("0", "false", "no") or _busy.get():
        return
    sid = iface.get("study_id")
    if not sid:
        return
    relevant = iface.get("status") == "accepted" or iface.get("deleted_at") or iface.get("agreement_json")
    if not relevant:
        from ..routers.requirements import _requirements
        relevant = any((r.get("ir_json") or {}).get("interface_id") == iface.get("id") for r in _requirements.values())
    if not relevant:
        return
    try:
        # the link and the others on its subsystem boundary (W2.07): accepting one link can make
        # it the representative of the boundary or cover the rows of other links
        await sync(sid, {iface["id"]})
    except Exception:
        logger.exception("interface requirement sync failed for %s", iface.get("id"))


async def after_study_change(study_id: str | None) -> None:
    """Element renames and electrical edits change requirement values: re-sync the study."""
    if not study_id or os.environ.get("SPACECDF_AUTO_IRD", "1") in ("0", "false", "no") or _busy.get():
        return
    try:
        await sync(study_id)
    except Exception:
        logger.exception("interface requirement sync failed for study %s", study_id)


# ═══════════════════════════════════════════════════════════════════════
# IF-02: requirement → interface
# ═══════════════════════════════════════════════════════════════════════

async def link_or_propose_interface(req: dict) -> tuple[dict | None, bool]:
    """For an interface requirement naming two elements and a type, link the matching
    interface or propose one. Returns ``(interface or None when the IR has no endpoints,
    created)``."""
    from spacecdf_common.models.interface_types import canonical_interface_type
    from ..routers import elements as el
    ir = dict(req.get("ir_json") or {})
    ends = ir.get("endpoints") or {}
    a, b = ends.get("from_element_id"), ends.get("to_element_id")
    itype = canonical_interface_type(ir.get("interface_type")) or None
    if not (a and b and itype) or a not in el._elements or b not in el._elements:
        return None, False
    sid = req.get("study_id")
    match = None
    created = False
    for i in el._interfaces.values():
        if i.get("study_id") != sid or i.get("deleted_at") or i.get("status") == "rejected":
            continue
        if (i.get("type") or i.get("interface_type")) == itype and {i["from_element_id"], i["to_element_id"]} == {a, b}:
            match = i
            break
    if match is None:
        na, nb = el._elements[a].get("name") or a, el._elements[b].get("name") or b
        match = await el.store_interface({
            "study_id": sid, "name": f"{na} → {nb}", "interface_type": itype, "subtype": ir.get("subtype"),
            "direction": "unidirectional", "from_element_id": a, "to_element_id": b, "properties": {},
            "origin": ORIGIN_IF02, "status": "suggested", "diagram_label": "",
            "rationale": {"en": f"Proposed because interface requirement {req.get('code')} names these two elements.",
                          "fr": f"Proposée parce que l'exigence d'interface {req.get('code')} nomme ces deux éléments."},
            "standard_ref": "ECSS-E-ST-10-24C (IRD → ICD)", "exchange_item_ids_json": [],
        })
        created = True
    ir["interface_id"] = match["id"]
    ir.setdefault("origin", "user")
    req["ir_json"] = ir
    from ..db.requirement_repo import db_update_requirement
    await db_update_requirement(req["id"], req)
    await _link(sid, req["id"], match["id"], "IF-02")
    return match, created


async def on_requirement_created(req: dict) -> None:
    if req.get("level") != "interface":
        return
    try:
        await link_or_propose_interface(req)
    except Exception:
        logger.exception("IF-02 failed for %s", req.get("id"))


def on_requirement_patched(req: dict, body: dict) -> None:
    """A user edit of a generated IR's text makes it the user's (never re-rendered silently)."""
    if req.get("level") != "interface" or "text" not in body:
        return
    ir = dict(req.get("ir_json") or {})
    if (ir.get("text_i18n") or {}).get("en") != body["text"]:
        ir["edited"] = True
        ir["text_i18n"] = None
        req["ir_json"] = ir
