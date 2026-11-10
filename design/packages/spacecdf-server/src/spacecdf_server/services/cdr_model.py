"""SpaceCDF — CDR design model: vocabulary, ownership and the proposal life cycle (Nov 2026).

The CDR model holds the products the simulator needs at CDR (sim_design_inventory.md §11–§12,
gaps 3–7 and 13): the TM/TC database (spacecraft id, APIDs, PUS services, parameters,
housekeeping structures, TC functions, events), the FDIR design (monitors, event-actions,
load-shed table with named bus-protection levels, safe mode, FDIR levels), the AOCS mode
machine and control parameters, the TT&C rate ladder with beacon and command-loss timer, the
power-line states per mode, and the operations organisation (positions, GO/NO-GO, flight
rules) — plus the MCS limits derived from the monitors.

Rows are generic (``db/cdr_models.CdrRow``: kind, key, data). This module holds what every
other CDR module shares: the kinds and their owners (REDESIGN_DECISIONS.md ruling 5: the TM/TC
database belongs to Comms & OBDH, each parameter to the seat of its subsystem), the config,
deterministic ids and the reconcile step (the electrical contract: rejected never re-proposed,
edited/accepted never overwritten — a moved input marks them ``review = "stale"``).
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from . import rule_config as rc

CONFIG = "cdr_rules"

#: kind → (group, singleton key or None, default owner seat or "subsystem")
KINDS: dict[str, dict[str, Any]] = {
    # TM/TC database
    "settings":        {"group": "tmtc", "singleton": "db", "owner": "comms_engineer"},
    "apids":           {"group": "tmtc", "owner": "comms_engineer"},
    "services":        {"group": "tmtc", "owner": "comms_engineer"},
    "parameters":      {"group": "tmtc", "owner": "subsystem"},
    "hk":              {"group": "tmtc", "owner": "comms_engineer"},
    "commands":        {"group": "tmtc", "owner": "comms_engineer"},
    "events":          {"group": "tmtc", "owner": "comms_engineer"},
    "rate_tiers":      {"group": "tmtc", "owner": "comms_engineer"},
    "ttc":             {"group": "tmtc", "singleton": "ttc", "owner": "comms_engineer"},
    # W3 (Nov 2026): data budget — link framing, packet stores, real-time profiles, service
    # reports, payload products; the pass classes and the operators' pass plan are operations rows
    "link_framing":    {"group": "tmtc", "singleton": "link_framing", "owner": "comms_engineer"},
    "stores":          {"group": "tmtc", "owner": "comms_engineer"},
    "rt_profiles":     {"group": "tmtc", "owner": "comms_engineer"},
    "service_allowances": {"group": "tmtc", "singleton": "service_allowances", "owner": "comms_engineer"},
    "payload_products": {"group": "tmtc", "singleton": "payload_products", "owner": "payload_lead"},
    # FDIR
    "monitors":        {"group": "fdir", "owner": "subsystem"},
    "event_actions":   {"group": "fdir", "owner": "systems_engineer"},
    "load_shed":       {"group": "fdir", "singleton": "load_shed", "owner": "power_engineer"},
    "safe_mode":       {"group": "fdir", "singleton": "safe_mode", "owner": "systems_engineer"},
    "fdir_levels":     {"group": "fdir", "owner": "systems_engineer"},
    "limits":          {"group": "fdir", "owner": "subsystem"},
    # AOCS and modes
    "aocs_modes":      {"group": "aocs", "owner": "aocs_engineer"},
    "aocs_transitions": {"group": "aocs", "owner": "aocs_engineer"},
    "aocs_control":    {"group": "aocs", "singleton": "aocs_control", "owner": "aocs_engineer"},
    "line_states":     {"group": "aocs", "owner": "power_engineer"},
    # Operations
    "positions":       {"group": "ops", "owner": "mission_analyst"},
    "gonogo":          {"group": "ops", "owner": "mission_analyst"},
    "flight_rules":    {"group": "ops", "owner": "mission_analyst"},
    "pass_classes":    {"group": "ops", "owner": "mission_analyst"},
    "pass_plan":       {"group": "ops", "singleton": "pass_plan", "owner": "mission_analyst"},
}
GROUPS = ("tmtc", "fdir", "aocs", "ops")
RULE_OF = {
    "settings": "TMTC-DB", "apids": "TMTC-APID", "services": "TMTC-PUS", "parameters": "TMTC-PARAM",
    "hk": "TMTC-HK", "commands": "TMTC-TC", "events": "TMTC-EV", "rate_tiers": "TTC-LADDER", "ttc": "TTC-CFG",
    "monitors": "FDIR-MON", "event_actions": "FDIR-EA", "load_shed": "FDIR-SHED", "safe_mode": "FDIR-SAFE",
    "fdir_levels": "FDIR-LVL", "limits": "OPS-LIM", "aocs_modes": "AOCS-MODE", "aocs_transitions": "AOCS-TRANS",
    "aocs_control": "AOCS-CTRL", "line_states": "EL-STATE", "positions": "OPS-POS", "gonogo": "OPS-GNG",
    "flight_rules": "OPS-FR", "link_framing": "TMTC-FRAME", "stores": "TMTC-STORE", "rt_profiles": "TMTC-PROFILE",
    "service_allowances": "TMTC-SVC", "payload_products": "TMTC-PAYLOAD", "pass_classes": "OPS-PASS", "pass_plan": "OPS-PASS",
}
IMPORT_ORIGIN = "import:eosat1"


class CdrError(ValueError):
    pass


def cfg() -> dict[str, Any]:
    return rc.load(CONFIG)


def ref(node: dict, c: dict | None = None) -> dict[str, Any]:
    r = rc.ref_of(c or cfg(), node)
    return {"standard_ref": r["standard_ref"], "c2o_default": r["c2o_default"]}


def validate_config(c: dict | None = None) -> list[str]:
    """Structure of cdr_rules.yaml (errors as text; empty = valid)."""
    errs: list[str] = []
    try:
        c = c or cfg()
    except rc.RuleConfigError as exc:
        return [str(exc)]
    subs = (c.get("subsystems") or {}).get("list") or []
    keys = [s.get("key") for s in subs]
    if len(keys) != len(set(keys)):
        errs.append("subsystems.list: duplicate key")
    for s in subs:
        for lang in ("en", "fr"):
            if not (s.get("label") or {}).get(lang):
                errs.append(f"subsystems.{s.get('key')}.label.{lang} missing")
    for sec, items in (("functions", (c.get("functions") or {}).get("list") or []),
                       ("events", (c.get("events") or {}).get("list") or [])):
        names = [i.get("name") for i in items]
        if len(names) != len(set(names)):
            errs.append(f"{sec}: duplicate name")
        for i in items:
            if i.get("subsystem") not in keys:
                errs.append(f"{sec}.{i.get('name')}: unknown subsystem {i.get('subsystem')}")
            d = i.get("description") or {}
            if not (d.get("en") and d.get("fr")):
                errs.append(f"{sec}.{i.get('name')}: description needs en and fr")
    for fn in (c.get("functions") or {}).get("list") or []:
        for a in fn.get("args") or []:
            if "enum" in a and not all(isinstance(x, str) for x in a["enum"]):
                errs.append(f"functions.{fn.get('name')}.{a.get('name')}: enum values must be quoted strings (YAML reads OFF/ON as booleans)")
    modes = {m["name"] for m in (c.get("aocs") or {}).get("modes") or []}
    for t in (c.get("aocs") or {}).get("transitions") or []:
        if t.get("from") not in modes or t.get("to") not in modes:
            errs.append(f"aocs.transitions {t.get('from')}->{t.get('to')}: unknown mode")
    roles = (c.get("ttc") or {}).get("roles") or {}
    tiers = {t["name"] for t in (c.get("ttc") or {}).get("tiers") or []}
    for r, n in roles.items():
        if n not in tiers:
            errs.append(f"ttc.roles.{r}: unknown tier {n}")
    return errs


# ───────────────────────────────────────────────────────────── helpers

def bi(en: str, fr: str) -> dict[str, str]:
    # French typography (STYLE_FR.md): no-break space before ":" and ";", decimal comma
    fr = re.sub(r"(\d)\.(\d)", r"\1,\2", fr.replace(" :", " :").replace(" ;", " ;"))
    return {"en": en, "fr": fr}


def slug(s: Any, n: int = 24) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(s or "").lower()).strip("_")[:n] or "unit"


def det_id(study_id: str, kind: str, key: str) -> str:
    h = hashlib.sha256(f"{study_id}|{kind}|{key}".encode()).hexdigest()[:16]
    return f"cdr-{h}"


def inputs_hash(row: dict) -> str:
    return hashlib.sha256(json.dumps({"k": row.get("key"), "d": row.get("data")}, sort_keys=True,
                                     default=str).encode()).hexdigest()[:16]


def subsystems(c: dict | None = None) -> list[dict]:
    return list(((c or cfg()).get("subsystems") or {}).get("list") or [])


def subsystem(key: str | None, c: dict | None = None) -> dict | None:
    return next((s for s in subsystems(c) if s["key"] == key), None)


def subsystem_of_domain(domain: str | None, c: dict | None = None) -> str | None:
    d = str(domain or "").lower()
    for s in subsystems(c):
        if d in s.get("domains", []):
            return s["key"]
    return None


def element_domain(e: dict, by_id: dict[str, dict]) -> str | None:
    cur: dict | None = e
    for _ in range(20):
        if cur is None:
            return None
        if cur.get("subsystem_domain"):
            return cur["subsystem_domain"]
        cur = by_id.get(cur.get("parent_id") or "")
    return None


def element_subsystem(e: dict, by_id: dict[str, dict], c: dict | None = None) -> str | None:
    return subsystem_of_domain(element_domain(e, by_id), c)


def owner_seat(kind: str, data: dict, c: dict | None = None) -> str:
    """The seat that owns a row (ruling 5): fixed per kind, or the seat of the row's subsystem."""
    own = KINDS[kind]["owner"]
    if own != "subsystem":
        return own
    sub = data.get("subsystem")
    if not sub and isinstance(data.get("parameter"), str):
        sub = data["parameter"].split(".", 1)[0]
    s = subsystem(sub, c)
    return (s or {}).get("seat") or "comms_engineer"


def key_of(kind: str, data: dict) -> str:
    """Natural key of a row inside its study (what makes two rows "the same entry")."""
    meta = KINDS[kind]
    if meta.get("singleton"):
        return meta["singleton"]
    if kind in ("parameters", "commands", "events", "aocs_modes", "rate_tiers", "event_actions"):
        return str(data.get("name") or "")
    if kind == "apids":
        return str(data.get("apid"))
    if kind == "services":
        return str(data.get("service"))
    if kind == "hk":
        return str(data.get("sid"))
    if kind == "monitors":
        return str(data.get("pmon_id") or data.get("name") or "")
    if kind == "fdir_levels":
        return str(data.get("level"))
    if kind == "stores":
        return str(data.get("id") if data.get("id") is not None else data.get("name") or "")
    if kind in ("rt_profiles", "pass_classes"):
        return str(data.get("name") or "")
    if kind == "aocs_transitions":
        return f"{data.get('from')}>{data.get('to')}"
    if kind == "line_states":
        return str(data.get("mode_id") or data.get("mode") or "")
    if kind == "positions":
        return str(data.get("id") or "")
    if kind == "gonogo":
        sit = data.get("situation")
        return slug(sit.get("en") if isinstance(sit, dict) else sit, 64)
    if kind == "flight_rules":
        return str(data.get("rule_id") or "")
    if kind == "limits":
        return str(data.get("parameter") or data.get("param_id") or "")
    return str(data.get("name") or data.get("id") or "")


# ───────────────────────────────────────────────────────────── reconcile

def reconcile(desired: dict[str, dict[str, dict]], existing: list[dict]) -> dict[str, Any]:
    """Operations from the plan ``{kind: {row_id: {key, data, owner_seat, rationale, standard_ref}}}``.

    Same contract as ``electrical_rules.reconcile``: new → create suggested; rejected → skipped;
    suggested rule rows follow the rules; accepted / edited / user rows are never overwritten —
    when the rule's facts move they get ``review = "stale"`` with the rule's values in
    ``proposed``; rule rows no longer implied are removed (suggested) or flagged ``orphan``.
    """
    ops: dict[str, Any] = {"create": [], "update": [], "remove": [], "unchanged": 0, "skipped_rejected": 0}
    live = [r for r in existing if not r.get("deleted_at")]
    by_id = {r["id"]: r for r in live}
    for kind, want in desired.items():
        for rid, row in want.items():
            h = inputs_hash(row)
            ex = by_id.get(rid)
            fields = {"key": row["key"], "data": row["data"], "owner_seat": row.get("owner_seat") or ""}
            if ex is None:
                ops["create"].append({**fields, "id": rid, "kind": kind, "status": "suggested",
                                      "origin": f"rule:{RULE_OF[kind]}", "rationale": row.get("rationale"),
                                      "standard_ref": row.get("standard_ref"), "inputs_hash": h, "edited": False,
                                      "review": None, "proposed": None})
                continue
            if ex.get("status") == "rejected":
                ops["skipped_rejected"] += 1
                continue
            mine = str(ex.get("origin") or "").startswith("rule:")
            if ex.get("status") == "suggested" and mine and not ex.get("edited"):
                changes = {k: v for k, v in fields.items() if ex.get(k) != v}
                if changes or ex.get("inputs_hash") != h:
                    ops["update"].append((rid, {**changes, "inputs_hash": h, "review": None, "proposed": None,
                                                "rationale": row.get("rationale")}))
                else:
                    ops["unchanged"] += 1
                continue
            if ex.get("inputs_hash") != h and ex.get("data") != row["data"]:
                if ex.get("proposed") != row["data"] or ex.get("review") != "stale":
                    ops["update"].append((rid, {"review": "stale", "proposed": row["data"]}))
                else:
                    ops["unchanged"] += 1
            elif ex.get("review") == "stale":
                ops["update"].append((rid, {"review": None, "proposed": None, "inputs_hash": h}))
            else:
                ops["unchanged"] += 1
    planned = {rid for want in desired.values() for rid in want}
    for rid, ex in by_id.items():
        if rid in planned or not str(ex.get("origin") or "").startswith("rule:") or ex.get("kind") not in desired:
            continue
        if ex.get("status") == "suggested" and not ex.get("edited"):
            ops["remove"].append(rid)
        elif ex.get("status") == "accepted" and ex.get("review") != "orphan":
            ops["update"].append((rid, {"review": "orphan", "proposed": None}))
    return ops


def group_rows(rows: list[dict], *, include_rejected: bool = True) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {k: [] for k in KINDS}
    for r in rows:
        if r.get("deleted_at") or r.get("kind") not in out:
            continue
        if not include_rejected and r.get("status") == "rejected":
            continue
        out[r["kind"]].append(r)
    return out


def live_data(rows: list[dict], kind: str) -> list[dict]:
    """``data`` of the rows of ``kind`` that count (not rejected, not deleted), with their id."""
    return [{**(r.get("data") or {}), "_id": r["id"], "_status": r.get("status")} for r in rows
            if r.get("kind") == kind and not r.get("deleted_at") and r.get("status") != "rejected"]


def singleton(rows: list[dict], kind: str) -> dict:
    xs = live_data(rows, kind)
    return xs[0] if xs else {}


def dataset_of(rows: list[dict]) -> str:
    """``reference`` (EOSAT-1 import), ``design`` (rule / user rows) or ``empty``."""
    live = [r for r in rows if not r.get("deleted_at")]
    if not live:
        return "empty"
    if any(r.get("origin") == IMPORT_ORIGIN for r in live):
        return "reference"
    return "design"
