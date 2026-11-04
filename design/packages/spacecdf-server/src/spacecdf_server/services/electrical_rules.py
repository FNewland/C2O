"""Power distribution and data-bus rules (design rules EI-01, EI-02, EB-08, EI-10; §2.1, §2.4).

Pure functions, no I/O apart from the cached config and KB. ``routers/electrical.py``
applies the result.

* :func:`plan` derives the rows the accepted and suggested links imply:
  - **rails** per EPS/PCDU: the EPS KB rails, the rails its power links use and the
    unregulated battery bus (``EL-RAIL``);
  - **power lines** (switches/LCLs), one per load fed by the EPS, with the LCL trip from
    the load's peak current (P/V × 1.5, C2O default), switchable / always-on and the default
    state at separation and at boot from the line policy (``EL-LINE``);
  - **data buses** per master and protocol (two CAN segments A/B when the CAN bus is big
    enough, as on EOSAT-1) and **bus nodes** with a default address that is unique on the
    segment (``DH-BUS``, ``DH-ADDR``);
  - **ports** on each element, bound to the links that use them (``EL-PORT``).
* :func:`reconcile` turns the plan into create / update / stale / remove operations with
  the same contract as the interface proposer: rejected rows are never re-proposed, edited
  and accepted rows are never overwritten (a changed input marks them ``review = "stale"``
  with the new values in ``proposed``), suggested rows follow the rules.
* :func:`run_checks` evaluates line current vs LCL, rail capacity, EPS output-channel count,
  rail/voltage and protocol compatibility, address uniqueness and range, device limits and
  bus load.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from .electrical_kb import kb_data_protocols, kb_output_channels, kb_voltage_range
from .interface_model import is_active

logger = logging.getLogger(__name__)

KINDS = ("rails", "lines", "buses", "nodes", "ports")
RULE_OF = {"rails": "EL-RAIL", "lines": "EL-LINE", "buses": "DH-BUS", "nodes": "DH-ADDR", "ports": "EL-PORT"}
ID_PREFIX = {"rails": "rail", "lines": "pl", "buses": "bus", "nodes": "node", "ports": "port"}
#: Fields a rule sets per kind (what reconcile compares and what "proposed" carries)
RULE_FIELDS: dict[str, tuple[str, ...]] = {
    "rails": ("eps_element_id", "name", "voltage_v", "regulated", "max_current_a", "v_min", "v_max"),
    "lines": ("eps_element_id", "rail_id", "line_no", "name", "switchable", "lcl_limit_a",
              "default_on_separation", "default_on_boot", "inhibits", "load_element_ids"),
    "buses": ("name", "protocol", "segment", "bit_rate_bps", "redundancy", "master_element_id", "max_devices"),
    "nodes": ("bus_id", "element_id", "role", "address", "data_rate_bps", "interface_id"),
    "ports": ("element_id", "kind", "name", "connector", "properties", "interface_ids", "line_id", "bus_id"),
}
#: User-editable fields per kind (PATCH)
EDITABLE: dict[str, tuple[str, ...]] = {
    "rails": ("name", "voltage_v", "regulated", "max_current_a", "v_min", "v_max", "notes", "eps_element_id"),
    "lines": ("name", "rail_id", "line_no", "switchable", "lcl_limit_a", "default_on_separation",
              "default_on_boot", "inhibits", "load_element_ids", "notes", "eps_element_id"),
    "buses": ("name", "protocol", "segment", "bit_rate_bps", "redundancy", "redundant_with_id",
              "master_element_id", "max_devices", "notes"),
    "nodes": ("bus_id", "element_id", "role", "address", "data_rate_bps"),
    "ports": ("name", "kind", "connector", "properties", "interface_ids", "line_id", "bus_id"),
}
PORT_KIND_BY_TYPE = {"data": "data", "rf": "rf", "mechanical": "mechanical", "thermal": "thermal",
                     "timing": "timing", "optical": "optical", "fluid": "fluid", "electrical_signal": "signal"}

_RATIONALE = {
    "rails": {"en": "Rail offered by the EPS (KB rails, the rails its power links use, and the battery bus).",
              "fr": "Rail fourni par l'EPS (rails de la base de connaissances, rails utilisés par ses liaisons d'alimentation et bus batterie)."},
    "lines": {"en": "One switched, current-limited line per load; LCL trip = 1.5 × peak current (C2O default); state at separation and boot from the line policy.",
              "fr": "Une ligne commutée et limitée en courant par charge ; déclenchement du LCL = 1,5 × courant crête (valeur par défaut C2O) ; état à la séparation et au démarrage selon la politique de ligne."},
    "buses": {"en": "Bus per master and protocol, from the accepted and suggested data links; large CAN buses split into segments A and B as on EOSAT-1.",
              "fr": "Un bus par maître et par protocole, d'après les liaisons de données acceptées et suggérées ; les grands bus CAN sont scindés en segments A et B comme sur EOSAT-1."},
    "nodes": {"en": "Default address from the C2O address plan, unique on the bus segment.",
              "fr": "Adresse par défaut tirée du plan d'adressage C2O, unique sur le segment de bus."},
    "ports": {"en": "Port implied by the links of this element.",
              "fr": "Port impliqué par les liaisons de cet élément."},
}


# ═══════════════════════════════════════════════════════════════════════
# Config
# ═══════════════════════════════════════════════════════════════════════

def config_path() -> Path:
    env = os.environ.get("SPACECDF_ELECTRICAL_RULES")
    if env:
        return Path(env)
    for parent in Path(__file__).resolve().parents:
        cand = parent / "configs" / "electrical_rules.yaml"
        if cand.exists():
            return cand
    return Path(__file__).resolve().parents[5] / "configs" / "electrical_rules.yaml"


@lru_cache(maxsize=4)
def _load_cached(path: str, mtime: float) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config(path: str | Path | None = None) -> dict:
    p = Path(path) if path else config_path()
    return _load_cached(str(p), p.stat().st_mtime)


def _proto_cfg(cfg: dict, protocol: str | None) -> dict:
    return (cfg.get("protocols") or {}).get(protocol or "", {}) or {}


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

def det_id(kind: str, study_id: str, *parts: Any) -> str:
    h = hashlib.sha1("|".join([kind, study_id, *[str(p) for p in parts]]).encode()).hexdigest()[:12]
    return f"{ID_PREFIX[kind]}-{h}"


def inputs_hash(kind: str, row: dict) -> str:
    vals = {k: row.get(k) for k in RULE_FIELDS[kind]}
    return hashlib.sha1(json.dumps(vals, sort_keys=True, default=str).encode()).hexdigest()[:16]


def _num(v: Any) -> float | None:
    try:
        return float(v) if v is not None and v != "" else None
    except (TypeError, ValueError):
        return None


def element_power_w(el: dict, peak: bool = True) -> float | None:
    q = max(1, int(el.get("quantity") or 1))
    p = _num(el.get("power_peak_w")) if peak else None
    if p is None:
        p = _num(el.get("power_avg_w"))
    if p is None and not peak:
        p = _num(el.get("power_peak_w"))
    return p * q if p is not None else None


def _ceil_tenth(x: float) -> float:
    return math.ceil(x * 10 - 1e-9) / 10.0


def lcl_for(peak_a: float | None, cfg: dict) -> float | None:
    if peak_a is None or peak_a <= 0:
        return None
    pc = cfg.get("power") or {}
    return max(float(pc.get("lcl_min_a", 0.1)), _ceil_tenth(float(pc.get("lcl_factor", 1.5)) * peak_a))


def _level_of(el: dict | None) -> str | None:
    return (el or {}).get("element_type")


def _bi(en: str, fr: str) -> dict[str, str]:
    return {"en": en, "fr": fr}


def _fmt(v: Any, nd: int = 2) -> str:
    if isinstance(v, float):
        s = f"{v:.{nd}f}".rstrip("0").rstrip(".")
        return s or "0"
    return str(v)


# ═══════════════════════════════════════════════════════════════════════
# Planning
# ═══════════════════════════════════════════════════════════════════════

def _links_for_level(links: list[dict], els: dict[str, dict]) -> list[dict]:
    """Component-level links when the study has any, otherwise subsystem-level ones."""
    comp = [i for i in links if _level_of(els.get(i["from_element_id"])) == "component"
            and _level_of(els.get(i["to_element_id"])) == "component"]
    if comp:
        return comp
    return [i for i in links if _level_of(els.get(i["from_element_id"])) == "subsystem"
            and _level_of(els.get(i["to_element_id"])) == "subsystem"]


def _role(ctx: Any, eid: str) -> str | None:
    u = ctx.units.get(eid) if ctx else None
    return u.role if u else None


def _domain(ctx: Any, eid: str, els: dict[str, dict]) -> str | None:
    u = ctx.units.get(eid) if ctx else None
    if u:
        return ctx.domain_of(u)
    return (els.get(eid) or {}).get("subsystem_domain")


def plan(study_id: str, elements: list[dict], interfaces: list[dict], cfg: dict,
         existing: dict[str, list[dict]] | None = None, ctx: Any = None) -> dict[str, dict[str, dict]]:
    """Rows the links imply, keyed ``{kind: {id: row}}`` (ids are deterministic)."""
    existing = existing or {k: [] for k in KINDS}
    els = {e["id"]: e for e in elements if not e.get("deleted_at")}
    links = [i for i in interfaces if is_active(i) and i["from_element_id"] in els and i["to_element_id"] in els]
    out: dict[str, dict[str, dict]] = {k: {} for k in KINDS}
    pc = cfg.get("power") or {}
    profile: dict = {}
    if ctx is not None:
        from .interface_proposer import kb_profile
        profile = kb_profile(ctx)

    # ── power: rails and lines ─────────────────────────────────────────
    power = [i for i in links if i.get("type", i.get("interface_type")) == "power"]
    supply = _links_for_level([i for i in power if (i.get("subtype") or "regulated") in ("regulated", "switched")], els)
    battery_links = [i for i in power if i.get("subtype") == "battery_bus"]
    providers: dict[str, list[dict]] = {}
    for i in supply:
        providers.setdefault(i["from_element_id"], []).append(i)
    for i in battery_links:   # an EPS with only a battery link still offers the battery bus
        providers.setdefault(i["to_element_id"], [])

    taken_loads: dict[str, str] = {}   # load id -> line id of a non-rule (or edited) line
    for ln in existing.get("lines", []):
        if ln.get("status") == "rejected" or ln.get("deleted_at"):
            continue
        if not str(ln.get("origin") or "").startswith("rule:") or ln.get("edited"):
            for lid in ln.get("load_element_ids") or []:
                taken_loads[lid] = ln["id"]

    order = list(pc.get("line_order") or [])
    policy = pc.get("line_policy") or {}
    for eps_id, feeds in providers.items():
        u = ctx.units.get(eps_id) if ctx else None
        kb_rails = list(u.facts.get("rails") or []) if (u and u.role == "eps") else []
        bat_v = vmin = vmax = None
        for bl in battery_links:
            if bl["to_element_id"] == eps_id:
                bu = ctx.units.get(bl["from_element_id"]) if ctx else None
                nom, lo, hi = kb_voltage_range(bu.kb if bu else None)
                bat_v = _num((bl.get("properties") or {}).get("rail_voltage")) or nom
                vmin, vmax = lo, hi
                break
        if bat_v is None:
            bat_v = profile.get("unregulated_bus_v")
        used = [_num((i.get("properties") or {}).get("rail_voltage")) for i in feeds]
        volts: list[float] = []
        for v in kb_rails + [x for x in used if x is not None] + ([bat_v] if bat_v else []):
            v = round(float(v), 2)
            if v not in volts:
                volts.append(v)
        rail_by_v: dict[float, str] = {}
        for v in volts:
            unreg = bat_v is not None and abs(v - float(bat_v)) < 0.05
            rid = det_id("rails", study_id, eps_id, v)
            rail_by_v[v] = rid
            out["rails"][rid] = {
                "id": rid, "eps_element_id": eps_id, "name": f"{_fmt(v)} V", "voltage_v": v,
                "regulated": not unreg, "max_current_a": pc.get("default_rail_max_current_a"),
                "v_min": vmin if unreg else None, "v_max": vmax if unreg else None,
            }

        def sort_key(i: dict) -> tuple:
            r = _role(ctx, i["to_element_id"])
            return (order.index(r) if r in order else len(order), (els[i["to_element_id"]].get("name") or "").lower())

        n = 0
        for i in sorted(feeds, key=sort_key):
            load_id = i["to_element_id"]
            lid = det_id("lines", study_id, eps_id, load_id)
            if taken_loads.get(load_id) not in (None, lid):
                continue
            v = _num((i.get("properties") or {}).get("rail_voltage"))
            v = round(v, 2) if v is not None else None
            rail_id = rail_by_v.get(v) if v is not None else None
            p_peak = element_power_w(els[load_id], peak=True)
            i_peak = (p_peak / v) if (p_peak is not None and v) else None
            pol = dict(policy.get("default") or {})
            pol.update(policy.get(_role(ctx, load_id) or "", {}) or {})
            out["lines"][lid] = {
                "id": lid, "eps_element_id": eps_id, "rail_id": rail_id, "line_no": n,
                "name": els[load_id].get("name") or load_id,
                "switchable": bool(pol.get("switchable", True)),
                "lcl_limit_a": lcl_for(i_peak, cfg),
                "default_on_separation": bool(pol.get("default_on_separation", False)),
                "default_on_boot": bool(pol.get("default_on_boot", False)),
                "inhibits": list(pol.get("inhibits") or []),
                "load_element_ids": [load_id],
                "_interface_id": i["id"],
            }
            n += 1

    # ── data: buses and nodes ──────────────────────────────────────────
    bc = cfg.get("buses") or {}
    data = _links_for_level([i for i in links if i.get("type", i.get("interface_type")) == "data"
                             and (i.get("subtype") or "tm_tc") in ("tm_tc", "bus", "payload_data")
                             and (i.get("properties") or {}).get("protocol")], els)
    groups: dict[tuple[str, str], list[dict]] = {}
    for i in data:
        proto = str((i.get("properties") or {}).get("protocol"))
        if proto == "analog":
            continue
        groups.setdefault((i["from_element_id"], proto), []).append(i)

    ex_nodes = {n["id"]: n for n in existing.get("nodes", []) if not n.get("deleted_at")}
    for (master, proto), ls in sorted(groups.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        pcfg = _proto_cfg(cfg, proto)
        multidrop = (pcfg.get("topology") or "multidrop") != "point_to_point"
        slaves = sorted(ls, key=lambda i: (els[i["to_element_id"]].get("name") or "").lower())
        segs: dict[str, list[dict]] = {}
        if multidrop:
            split = proto == "CAN" and len({i["to_element_id"] for i in slaves}) + 1 >= int(bc.get("can_split_min_nodes", 4))
            for i in slaves:
                seg = "A"
                if split:
                    dom = _domain(ctx, i["to_element_id"], els) or "other"
                    seg = next((s for s, doms in (bc.get("can_split") or {}).items() if dom in doms),
                               "B" if "B" in (bc.get("can_split") or {}) else "A")
                segs.setdefault(seg, []).append(i)
        else:
            for i in slaves:
                segs.setdefault(i["to_element_id"], []).append(i)
        for seg, items in sorted(segs.items()):
            p2p = not multidrop
            bid = det_id("buses", study_id, master, proto, seg)
            mname = els[master].get("name") or master
            name = (f"{proto} {mname} – {els[seg].get('name') or seg}" if p2p else f"{proto}-{seg}")
            out["buses"][bid] = {
                "id": bid, "name": name, "protocol": proto, "segment": "A" if p2p else seg,
                "bit_rate_bps": _num(pcfg.get("bit_rate_bps")), "redundancy": "none",
                "master_element_id": master, "max_devices": pcfg.get("max_devices"),
            }
            members = [(master, "master", None, None)] + [
                (i["to_element_id"], "node", i["id"], _num((i.get("properties") or {}).get("data_rate_bps")))
                for i in items]
            _plan_nodes(study_id, bid, proto, members, ctx, els, cfg, ex_nodes, out)

    # ── ports ──────────────────────────────────────────────────────────
    line_of_load = {}
    for ln in list(out["lines"].values()) + [x for x in existing.get("lines", []) if x.get("status") != "rejected"]:
        for lid in ln.get("load_element_ids") or []:
            line_of_load.setdefault(lid, ln["id"])
    bus_of = {}
    for nd in list(out["nodes"].values()):
        proto = out["buses"].get(nd["bus_id"], {}).get("protocol")
        bus_of.setdefault((nd["element_id"], proto), nd["bus_id"])
    for i in links:
        t = i.get("type", i.get("interface_type"))
        props = i.get("properties") or {}
        for end in ("from", "to"):
            eid = i[f"{end}_element_id"]
            if t == "power":
                kind = "power_out" if end == "from" else "power_in"
                if i.get("direction") == "bidirectional" and i.get("subtype") == "battery_bus":
                    kind = "power_out" if end == "from" else "power_in"
                qual = _fmt(_num(props.get("rail_voltage"))) if props.get("rail_voltage") is not None else "power"
                name = f"{qual} V {'out' if kind == 'power_out' else 'in'}" if qual != "power" else ("Power out" if kind == "power_out" else "Power in")
                pprops = {"rail_voltage": _num(props.get("rail_voltage"))} if props.get("rail_voltage") is not None else {}
            else:
                kind = PORT_KIND_BY_TYPE.get(t, "signal")
                qual = str(props.get("protocol") or props.get("band") or t)
                name = {"data": f"{qual}", "rf": f"{qual}-band RF" if props.get("band") else "RF"}.get(kind, t.replace("_", " ").capitalize())
                pprops = {k: props[k] for k in ("protocol", "band", "mount_type") if props.get(k) is not None}
            pid = det_id("ports", study_id, eid, kind, qual)
            port = out["ports"].get(pid)
            if port is None:
                port = out["ports"][pid] = {
                    "id": pid, "element_id": eid, "kind": kind, "name": name,
                    "connector": props.get("connector"), "properties": pprops, "interface_ids": [],
                    "line_id": line_of_load.get(eid) if kind == "power_in" else None,
                    "bus_id": bus_of.get((eid, props.get("protocol"))) if kind == "data" else None,
                }
            if i["id"] not in port["interface_ids"]:
                port["interface_ids"].append(i["id"])
    for p in out["ports"].values():
        p["interface_ids"].sort()
    return out


def _plan_nodes(study_id: str, bus_id: str, proto: str, members: list[tuple], ctx: Any,
                els: dict[str, dict], cfg: dict, ex_nodes: dict[str, dict], out: dict) -> None:
    pcfg = _proto_cfg(cfg, proto)
    amin, amax = pcfg.get("address_min"), pcfg.get("address_max")
    addressed = amin is not None and amax is not None
    acfg = cfg.get("addresses") or {}
    taken: set[int] = set()
    rows = []
    for eid, role, iface_id, rate in members:
        nid = det_id("nodes", study_id, bus_id, eid)
        ex = ex_nodes.get(nid)
        keep = ex.get("address") if ex and ex.get("status") != "rejected" else None
        rows.append((nid, eid, role, iface_id, rate, keep))
        if keep is not None:
            taken.add(int(keep))
    for nid, eid, role, iface_id, rate, keep in rows:
        addr = keep
        if addr is None and addressed:
            if role == "master":
                start = int(acfg.get("master", amin))
            else:
                r = _role(ctx, eid)
                dom = _domain(ctx, eid, els)
                start = (acfg.get("roles") or {}).get(r or "")
                if start is None:
                    start = (acfg.get("domains") or {}).get(dom or "", acfg.get("other", amin))
                start = int(start)
            if not (amin <= start <= amax):
                start = int(amin)
            addr = next((a for a in list(range(start, amax + 1)) + list(range(amin, start)) if a not in taken), None)
            if addr is not None:
                taken.add(addr)
        out["nodes"][nid] = {"id": nid, "bus_id": bus_id, "element_id": eid, "role": role,
                             "address": addr, "data_rate_bps": rate, "interface_id": iface_id}


# ═══════════════════════════════════════════════════════════════════════
# Reconcile
# ═══════════════════════════════════════════════════════════════════════

def _fields(kind: str, row: dict) -> dict:
    return {k: row.get(k) for k in RULE_FIELDS[kind]}


def reconcile(desired: dict[str, dict[str, dict]], existing: dict[str, list[dict]],
              cfg: dict) -> dict[str, list]:
    """Operations: ``create [(kind,row)]``, ``update [(kind,id,changes)]``, ``remove [(kind,id)]``;
    plus counters ``unchanged`` and ``skipped_rejected``."""
    ops: dict[str, Any] = {"create": [], "update": [], "remove": [], "unchanged": 0, "skipped_rejected": 0}
    std = {"rails": (cfg.get("power") or {}).get("standard_ref"), "lines": (cfg.get("power") or {}).get("standard_ref"),
           "buses": (cfg.get("buses") or {}).get("standard_ref"), "nodes": (cfg.get("buses") or {}).get("standard_ref"),
           "ports": "ECSS-E-ST-10-24C (interface definition); C2O default"}
    for kind in KINDS:
        ex_by_id = {r["id"]: r for r in existing.get(kind, []) if not r.get("deleted_at")}
        want = desired.get(kind, {})
        for rid, row in want.items():
            fields = _fields(kind, row)
            h = inputs_hash(kind, row)
            ex = ex_by_id.get(rid)
            if ex is None:
                ops["create"].append((kind, {**fields, "id": rid, "status": "suggested", "origin": f"rule:{RULE_OF[kind]}",
                                             "rationale": _RATIONALE[kind], "standard_ref": std[kind],
                                             "inputs_hash": h, "edited": False, "review": None, "proposed": None}))
                continue
            if ex.get("status") == "rejected":
                ops["skipped_rejected"] += 1
                continue
            mine = str(ex.get("origin") or "").startswith("rule:")
            if ex.get("status") == "suggested" and mine and not ex.get("edited"):
                changes = {k: v for k, v in fields.items() if ex.get(k) != v}
                if changes or ex.get("inputs_hash") != h:
                    ops["update"].append((kind, rid, {**changes, "inputs_hash": h, "review": None, "proposed": None}))
                else:
                    ops["unchanged"] += 1
                continue
            # accepted, edited or user rows: never overwritten; flag when the rule's facts moved
            if ex.get("inputs_hash") != h and any(ex.get(k) != v for k, v in fields.items()):
                if ex.get("proposed") != fields or ex.get("review") != "stale":
                    ops["update"].append((kind, rid, {"review": "stale", "proposed": fields}))
                else:
                    ops["unchanged"] += 1
            else:
                if ex.get("review") == "stale" and ex.get("inputs_hash") != h:
                    ops["update"].append((kind, rid, {"review": None, "proposed": None, "inputs_hash": h}))
                else:
                    ops["unchanged"] += 1
        for rid, ex in ex_by_id.items():
            if rid in want or not str(ex.get("origin") or "").startswith("rule:"):
                continue
            if ex.get("status") == "suggested" and not ex.get("edited"):
                ops["remove"].append((kind, rid))
            elif ex.get("status") == "accepted" and ex.get("review") != "orphan":
                ops["update"].append((kind, rid, {"review": "orphan", "proposed": None}))
    return ops


# ═══════════════════════════════════════════════════════════════════════
# Checks
# ═══════════════════════════════════════════════════════════════════════

def _finding(fid: str, rule: str, severity: str, target_kind: str, target_id: str, element_ids: list[str],
             en: str, fr: str, **values: Any) -> dict:
    # French typography (STYLE_FR.md): no-break space before ":" and ";", decimal comma
    fr = re.sub(r"(\d)\.(\d)", r"\1,\2", fr.replace(" :", "\u00a0:").replace(" ;", "\u202f;"))
    return {"id": fid, "rule": rule, "severity": severity, "target_kind": target_kind, "target_id": target_id,
            "element_ids": element_ids, "message": {"en": en, "fr": fr}, "values": values}


def run_checks(elements: list[dict], interfaces: list[dict], rows: dict[str, list[dict]], cfg: dict,
               ctx: Any = None) -> list[dict]:
    """Findings ``{id, rule, severity: caution|alarm, target_kind, target_id, element_ids,
    message{en,fr}, values}``. A finding that involves only suggested rows is a caution."""
    els = {e["id"]: e for e in elements if not e.get("deleted_at")}
    live = {k: [r for r in rows.get(k, []) if r.get("status") != "rejected" and not r.get("deleted_at")] for k in KINDS}
    rails = {r["id"]: r for r in live["rails"]}
    buses = {b["id"]: b for b in live["buses"]}
    pc = cfg.get("power") or {}
    out: list[dict] = []
    name = lambda eid: (els.get(eid) or {}).get("name") or eid

    def sev(base: str, *involved: dict) -> str:
        if base == "alarm" and any((r or {}).get("status") == "suggested" for r in involved):
            return "caution"
        return base

    # ── lines ──
    line_current: dict[str, float] = {}
    for ln in live["lines"]:
        rail = rails.get(ln.get("rail_id") or "")
        v = _num((rail or {}).get("voltage_v"))
        loads = [els[e] for e in ln.get("load_element_ids") or [] if e in els]
        p_pk = sum(element_power_w(e, True) or 0.0 for e in loads)
        p_av = sum(element_power_w(e, False) or 0.0 for e in loads)
        if not rail:
            out.append(_finding(f"PWR-LINE-RAIL:{ln['id']}", "EI-01", sev("alarm", ln), "lines", ln["id"],
                                [e["id"] for e in loads],
                                f"Line {ln.get('line_no')} ({ln.get('name')}) has no rail.",
                                f"La ligne {ln.get('line_no')} ({ln.get('name')}) n'a pas de rail."))
            continue
        i_pk = p_pk / v if v else 0.0
        i_av = p_av / v if v else 0.0
        line_current[ln["id"]] = i_av
        lcl = _num(ln.get("lcl_limit_a"))
        if loads and lcl is None:
            out.append(_finding(f"PWR-LCL-NONE:{ln['id']}", "EI-01", "caution", "lines", ln["id"], [e["id"] for e in loads],
                                f"Line {ln.get('line_no')} ({ln.get('name')}): no LCL trip current set.",
                                f"Ligne {ln.get('line_no')} ({ln.get('name')}) : aucun courant de déclenchement du LCL.",
                                current_a=round(i_pk, 3)))
        elif lcl is not None and i_pk > lcl:
            out.append(_finding(f"PWR-LCL-OVER:{ln['id']}", "EI-01", sev("alarm", ln), "lines", ln["id"], [e["id"] for e in loads],
                                f"Line {ln.get('line_no')} ({ln.get('name')}): peak current {_fmt(i_pk, 3)} A = {_fmt(p_pk)} W / {_fmt(v)} V exceeds the LCL trip {_fmt(lcl)} A.",
                                f"Ligne {ln.get('line_no')} ({ln.get('name')}) : le courant crête {_fmt(i_pk, 3)} A = {_fmt(p_pk)} W / {_fmt(v)} V dépasse le déclenchement du LCL {_fmt(lcl)} A.",
                                current_a=round(i_pk, 3), lcl_a=lcl))
        elif lcl is not None and i_pk > 0 and lcl < float(pc.get("lcl_caution_factor", 1.2)) * i_pk:
            out.append(_finding(f"PWR-LCL-TIGHT:{ln['id']}", "EI-01", "caution", "lines", ln["id"], [e["id"] for e in loads],
                                f"Line {ln.get('line_no')} ({ln.get('name')}): LCL trip {_fmt(lcl)} A is within {int((float(pc.get('lcl_caution_factor', 1.2)) - 1) * 100)} % of the peak current {_fmt(i_pk, 3)} A.",
                                f"Ligne {ln.get('line_no')} ({ln.get('name')}) : le déclenchement du LCL {_fmt(lcl)} A est à moins de {int((float(pc.get('lcl_caution_factor', 1.2)) - 1) * 100)} % du courant crête {_fmt(i_pk, 3)} A.",
                                current_a=round(i_pk, 3), lcl_a=lcl))
        for e in loads:
            u = ctx.units.get(e["id"]) if ctx else None
            need = [r for r in (u.facts.get("rails") if u else []) or []] if (u and u.role not in ("eps", "battery")) else []
            if need and v and all(abs(float(n) - v) > 0.05 for n in need):
                out.append(_finding(f"PWR-RAIL-MISMATCH:{ln['id']}:{e['id']}", "EI-01", sev("alarm", ln), "lines", ln["id"], [e["id"]],
                                    f"{name(e['id'])} needs {', '.join(_fmt(float(n)) for n in need)} V but line {ln.get('line_no')} is on the {_fmt(v)} V rail.",
                                    f"{name(e['id'])} demande {', '.join(_fmt(float(n)) for n in need)} V mais la ligne {ln.get('line_no')} est sur le rail de {_fmt(v)} V."))
            if u and u.role == "obc" and ln.get("switchable"):
                out.append(_finding(f"PWR-OBC-SWITCHABLE:{ln['id']}", "EI-01", "caution", "lines", ln["id"], [e["id"]],
                                    f"The on-board computer {name(e['id'])} is on a switchable line: a command or FDIR action could switch off the computer that sends it.",
                                    f"L'ordinateur de bord {name(e['id'])} est sur une ligne commutable : une commande ou une action FDIR pourrait éteindre l'ordinateur qui l'envoie."))

    # duplicate line numbers per EPS
    seen: dict[tuple, dict] = {}
    for ln in live["lines"]:
        key = (ln.get("eps_element_id"), ln.get("line_no"))
        if key in seen:
            out.append(_finding(f"PWR-LINE-NO:{ln['id']}", "EI-01", sev("alarm", ln, seen[key]), "lines", ln["id"], [],
                                f"Line number {ln.get('line_no')} is used twice on {name(key[0])}.",
                                f"Le numéro de ligne {ln.get('line_no')} est utilisé deux fois sur {name(key[0])}."))
        else:
            seen[key] = ln

    # powered loads with no line (only where the study has lines at all)
    if live["lines"]:
        on_line = {e for ln in live["lines"] for e in ln.get("load_element_ids") or []}
        fed = {i["to_element_id"] for i in interfaces if is_active(i) and i.get("type", i.get("interface_type")) == "power"
               and (i.get("subtype") or "regulated") in ("regulated", "switched")
               and _level_of(els.get(i["to_element_id"])) == "component"}
        for eid in sorted(fed - on_line):
            if eid in els:
                out.append(_finding(f"PWR-UNASSIGNED:{eid}", "EI-01", "caution", "elements", eid, [eid],
                                    f"{name(eid)} is powered but on no power line.",
                                    f"{name(eid)} est alimenté mais n'est sur aucune ligne d'alimentation."))

    # ── rails: capacity ──
    for r in live["rails"]:
        cap = _num(r.get("max_current_a"))
        tot = sum(line_current.get(ln["id"], 0.0) for ln in live["lines"] if ln.get("rail_id") == r["id"])
        if cap is not None and tot > cap:
            out.append(_finding(f"PWR-RAIL-CAP:{r['id']}", "EB-08", sev("alarm", r), "rails", r["id"], [r.get("eps_element_id") or ""],
                                f"Rail {r.get('name')}: {_fmt(tot, 3)} A drawn by its lines exceeds the converter rating {_fmt(cap)} A.",
                                f"Rail {r.get('name')} : les {_fmt(tot, 3)} A tirés par ses lignes dépassent la capacité du convertisseur, {_fmt(cap)} A.",
                                current_a=round(tot, 3), max_a=cap))

    # ── EPS output channels ──
    by_eps: dict[str, list[dict]] = {}
    for ln in live["lines"]:
        if ln.get("switchable"):
            by_eps.setdefault(ln.get("eps_element_id") or "", []).append(ln)
    for eps_id, lns in by_eps.items():
        u = ctx.units.get(eps_id) if ctx else None
        ch = kb_output_channels(u.kb if u else None)
        if ch is not None and len(lns) > ch:
            out.append(_finding(f"PWR-EPS-CHANNELS:{eps_id}", "EB-08", sev("alarm", *lns), "elements", eps_id, [eps_id],
                                f"{name(eps_id)} has {ch} switched output channels; {len(lns)} switchable lines are assigned.",
                                f"{name(eps_id)} a {ch} sorties commutées ; {len(lns)} lignes commutables lui sont affectées.",
                                channels=ch, lines=len(lns)))

    # ── buses and nodes ──
    nodes_by_bus: dict[str, list[dict]] = {}
    for nd in live["nodes"]:
        nodes_by_bus.setdefault(nd["bus_id"], []).append(nd)
    for bid, nds in nodes_by_bus.items():
        b = buses.get(bid)
        if not b:
            continue
        pcfg = _proto_cfg(cfg, b.get("protocol"))
        amin, amax = pcfg.get("address_min"), pcfg.get("address_max")
        by_addr: dict[int, list[dict]] = {}
        for nd in nds:
            a = nd.get("address")
            if a is None:
                continue
            by_addr.setdefault(int(a), []).append(nd)
            if amin is not None and amax is not None and not (amin <= int(a) <= amax):
                out.append(_finding(f"DATA-ADDR-RANGE:{nd['id']}", "EI-02", sev("alarm", nd), "nodes", nd["id"], [nd["element_id"]],
                                    f"{name(nd['element_id'])}: address 0x{int(a):02X} is outside the {b.get('protocol')} range 0x{amin:02X}–0x{amax:02X}.",
                                    f"{name(nd['element_id'])} : l'adresse 0x{int(a):02X} est hors de la plage {b.get('protocol')} 0x{amin:02X}–0x{amax:02X}.",
                                    address=int(a)))
        for a, same in by_addr.items():
            if len(same) > 1:
                for nd in same:
                    out.append(_finding(f"DATA-ADDR-DUP:{nd['id']}", "EI-02", sev("alarm", *same), "nodes", nd["id"],
                                        [x["element_id"] for x in same],
                                        f"Address 0x{a:02X} is used by {len(same)} nodes on {b.get('name')}: {', '.join(name(x['element_id']) for x in same)}.",
                                        f"L'adresse 0x{a:02X} est utilisée par {len(same)} nœuds sur {b.get('name')} : {', '.join(name(x['element_id']) for x in same)}.",
                                        address=a, bus=b.get("name")))
        maxd = b.get("max_devices") or pcfg.get("max_devices")
        if maxd is not None and len(nds) > int(maxd):
            out.append(_finding(f"DATA-BUS-DEVICES:{bid}", "EI-02", sev("alarm", b), "buses", bid, [n["element_id"] for n in nds],
                                f"{b.get('name')}: {len(nds)} nodes exceed the {b.get('protocol')} limit of {maxd}.",
                                f"{b.get('name')} : {len(nds)} nœuds dépassent la limite {b.get('protocol')} de {maxd}.",
                                nodes=len(nds), max=maxd))
        rate = _num(b.get("bit_rate_bps"))
        load = sum(_num(n.get("data_rate_bps")) or 0.0 for n in nds)
        frac = float((cfg.get("buses") or {}).get("max_load_fraction", 0.5))
        if rate and load > rate:
            out.append(_finding(f"DATA-BUS-LOAD:{bid}", "IF-07", sev("alarm", b), "buses", bid, [],
                                f"{b.get('name')}: node data rates {_fmt(load / 1000)} kbit/s exceed the bus rate {_fmt(rate / 1000)} kbit/s.",
                                f"{b.get('name')} : les débits des nœuds, {_fmt(load / 1000)} kbit/s, dépassent le débit du bus, {_fmt(rate / 1000)} kbit/s.",
                                load_bps=load, rate_bps=rate))
        elif rate and load > frac * rate:
            out.append(_finding(f"DATA-BUS-LOAD:{bid}", "IF-07", "caution", "buses", bid, [],
                                f"{b.get('name')}: bus load {_fmt(100 * load / rate, 1)} % is above the {int(frac * 100)} % margin limit.",
                                f"{b.get('name')} : la charge du bus, {_fmt(100 * load / rate, 1)} %, dépasse la limite de marge de {int(frac * 100)} %.",
                                load_bps=load, rate_bps=rate))
        for nd in nds:
            u = ctx.units.get(nd["element_id"]) if ctx else None
            protos = kb_data_protocols(u.kb) if (u and u.kb) else []
            if protos and b.get("protocol") not in protos:
                out.append(_finding(f"DATA-PROTO:{nd['id']}", "EI-02", sev("alarm", nd, b), "nodes", nd["id"], [nd["element_id"]],
                                    f"{name(nd['element_id'])} does not speak {b.get('protocol')} (KB: {', '.join(protos)}).",
                                    f"{name(nd['element_id'])} ne parle pas {b.get('protocol')} (base : {', '.join(protos)}).",
                                    protocol=b.get("protocol")))
    return out
