"""SpaceCDF — consistency checks of the CDR design model (Nov 2026).

Pure: ``run_checks(rows, ctx)`` → findings in the electrical shape ``{id, rule, severity
caution|alarm, target_kind, target_id, element_ids, message{en,fr}, values}``;
``hk_budget(rows)`` → the housekeeping downlink budget per regime and per mode;
``fmeca_coverage(rows, fmeca_rows)`` → failure mode → detection monitor → recovery action.

``ctx`` (all optional): ``lines`` (electrical power lines), ``units`` (cdr_propose.design_facts
units: id, cls), ``members`` (mode matrix), ``modes`` (mode elements {id, name, kind}),
``fmeca_rows``, ``reference`` (the rows are the EOSAT-1 import: design-only checks are skipped).
"""
from __future__ import annotations

import math
from typing import Any

from . import cdr_model as cm


def _f(fid: str, rule: str, severity: str, kind: str, target_id: str, en: str, fr: str,
       element_ids: list[str] | None = None, **values: Any) -> dict:
    return {"id": fid, "rule": rule, "severity": severity, "target_kind": kind, "target_id": target_id,
            "element_ids": element_ids or [], "message": cm.bi(en, fr), "values": values}


def _num(v: Any) -> float | None:
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def _dups(items: list[dict], field: str) -> dict[Any, list[dict]]:
    seen: dict[Any, list[dict]] = {}
    for it in items:
        v = it.get(field)
        if v is None or v == "":
            continue
        seen.setdefault(v, []).append(it)
    return {k: v for k, v in seen.items() if len(v) > 1}


def _hexs(v: Any) -> str:
    return f"0x{int(v):04X}" if isinstance(v, int) else str(v)


# ───────────────────────────────────────────────────────────── housekeeping budget

def packet_bytes(hk: dict, params_by_id: dict[int, dict], c: dict) -> int:
    sizes = c["types"]["bytes"]
    body = 0
    for pid in hk.get("parameter_ids") or []:
        p = params_by_id.get(pid) or {}
        body += int(sizes.get(p.get("type") or "uint16", 2))
    return int(c["downlink_budget"]["packet_overhead_bytes"]) + body


def hk_budget(rows: list[dict], modes: list[dict] | None = None) -> dict[str, Any]:
    """HK bit rate per regime (bootloader / safe / nominal / downlink) and per mode against the
    rate tier of that regime × the HK share (cdr_rules.yaml downlink_budget)."""
    c = cm.cfg()
    db = c["downlink_budget"]
    params = {p.get("param_id"): p for p in cm.live_data(rows, "parameters")}
    hks = cm.live_data(rows, "hk")
    tiers = {t.get("name"): t for t in cm.live_data(rows, "rate_tiers")}
    ttc = cm.singleton(rows, "ttc")
    share = float(db["hk_share_percent"]) / 100.0
    eff = float(db["frame_efficiency"])
    per_sid = []
    for h in hks:
        b = packet_bytes(h, params, c)
        per = _num(h.get("period_s")) or 0.0
        bps = b * 8 / per if per > 0 else 0.0
        per_sid.append({"sid": h.get("sid"), "name": h.get("name"), "bytes": b, "period_s": per, "bps": round(bps, 1),
                        "enabled_at_boot": bool(h.get("enabled_at_boot")), "beacon": bool(h.get("beacon"))})
    tier_of = {"bootloader": ttc.get("beacon_tier"), "safe": ttc.get("safe_tier"), "nominal": ttc.get("default_tier"),
               "downlink": next((t["name"] for t in tiers.values() if t.get("requires_downlink_mode")), ttc.get("default_tier"))}
    sel = {"bootloader": lambda s: s["beacon"], "safe": lambda s: s["enabled_at_boot"],
           "nominal": lambda s: not s["beacon"] or s["enabled_at_boot"], "downlink": lambda s: not s["beacon"] or s["enabled_at_boot"]}
    regimes = []
    for reg, tname in tier_of.items():
        t = tiers.get(tname or "")
        used = sum(s["bps"] for s in per_sid if sel[reg](s))
        avail = (float(t.get("bps") or 0) * eff * share) if t else None
        regimes.append({"regime": reg, "tier": tname, "tier_bps": (t or {}).get("bps"), "hk_bps": round(used, 1),
                        "budget_bps": round(avail, 1) if avail is not None else None,
                        "use_percent": round(100 * used / avail, 1) if avail else None,
                        "ok": (used <= avail) if avail is not None else None,
                        "sids": [s["sid"] for s in per_sid if sel[reg](s)]})
    by_reg = {r["regime"]: r for r in regimes}
    per_mode = []
    for m in modes or []:
        reg = db["regime_of_mode_kind"].get(m.get("kind") or "custom", "nominal")
        r = by_reg.get(reg) or {}
        per_mode.append({"mode_id": m.get("id"), "mode": m.get("name"), "regime": reg, "tier": r.get("tier"),
                         "hk_bps": r.get("hk_bps"), "budget_bps": r.get("budget_bps"), "ok": r.get("ok")})
    return {"sids": per_sid, "regimes": regimes, "modes": per_mode, "hk_share_percent": db["hk_share_percent"],
            "frame_efficiency": eff, "packet_overhead_bytes": db["packet_overhead_bytes"],
            **cm.ref(db, c)}


# ───────────────────────────────────────────────────────────── FMECA coverage

def fmeca_coverage(rows: list[dict], fmeca_rows: list[dict], *, accepted_only: bool = True) -> dict[str, Any]:
    """Each FMECA failure mode → its detection monitor(s) and recovery action(s).

    Detection credit comes only from monitors that are accepted (or user rows), never from a
    suggestion (rule 8 / F10): a proposed monitor shows, but does not count."""
    c = cm.cfg()
    need = int(c["fdir"]["severity_needing_recovery"])
    mons = [m for m in cm.live_data(rows, "monitors")]
    eas = cm.live_data(rows, "event_actions")
    out = []
    for fr in fmeca_rows:
        rid, eid = fr.get("id"), fr.get("element_id")
        hit = [m for m in mons if rid in (m.get("fmeca_row_ids") or []) or (eid and m.get("element_id") == eid)]
        counted = [m for m in hit if not accepted_only or m.get("_status") == "accepted"]
        pm = {m.get("pmon_id") for m in counted}

        def answers(a: dict, ms: list[dict]) -> bool:
            tr = a.get("trigger") or {}
            return tr.get("monitor") in {m.get("pmon_id") for m in ms} or (
                tr.get("kind") == "param" and tr.get("parameter") in {m.get("parameter") for m in ms})
        acts = [a for a in eas if answers(a, hit)]
        rec = [a for a in acts if answers(a, counted)]
        s = int(fr.get("severity") or 0)
        out.append({"fmeca_row_id": rid, "element_id": eid, "component": fr.get("component"), "mode": fr.get("mode"),
                    "severity": s, "critical": s >= need,
                    "monitors": [m.get("pmon_id") for m in hit], "monitors_counted": sorted(x for x in pm if x),
                    "actions": [a.get("name") for a in acts], "actions_counted": [a.get("name") for a in rec],
                    "detected": bool(counted), "recovered": bool(rec)})
    crit = [x for x in out if x["critical"]]
    return {"rows": out, "summary": {"modes": len(out), "critical": len(crit),
                                     "critical_detected": sum(1 for x in crit if x["detected"]),
                                     "critical_recovered": sum(1 for x in crit if x["detected"] and x["recovered"])},
            "severity_needing_recovery": need}


# ───────────────────────────────────────────────────────────── checks

def run_checks(rows: list[dict], ctx: dict | None = None) -> list[dict]:  # noqa: C901
    ctx = ctx or {}
    c = cm.cfg()
    ref = bool(ctx.get("reference"))
    out: list[dict] = []
    P = cm.live_data(rows, "parameters")
    HK = cm.live_data(rows, "hk")
    TC = cm.live_data(rows, "commands")
    EV = cm.live_data(rows, "events")
    MON = cm.live_data(rows, "monitors")
    EA = cm.live_data(rows, "event_actions")
    TIERS = cm.live_data(rows, "rate_tiers")
    AM = cm.live_data(rows, "aocs_modes")
    AT = cm.live_data(rows, "aocs_transitions")
    POS = cm.live_data(rows, "positions")
    GNG = cm.live_data(rows, "gonogo")
    FR = cm.live_data(rows, "flight_rules")
    LS = cm.live_data(rows, "line_states")
    settings = cm.singleton(rows, "settings")
    ttc = cm.singleton(rows, "ttc")
    shed = cm.singleton(rows, "load_shed")
    safe = cm.singleton(rows, "safe_mode")
    ctl = cm.singleton(rows, "aocs_control")
    pid = {p.get("param_id"): p for p in P}
    pname = {p.get("name"): p for p in P}
    lines = [l for l in ctx.get("lines") or [] if l.get("status") != "rejected" and not l.get("deleted_at")]
    units = {u["id"]: u for u in ctx.get("units") or []}
    never = set(c["fdir"]["never_off_classes"])

    def line_classes(l: dict) -> set[str]:
        return {units[e]["cls"] for e in l.get("load_element_ids") or [] if e in units}

    # ── TM/TC database
    if P or HK or TC:
        if not settings:
            out.append(_f("TMTC-DB", "TMTC-DB", "alarm", "settings", "", "No database settings (spacecraft id, APIDs).",
                          "Aucun réglage de base de données (identifiant du satellite, APID)."))
        else:
            scid = settings.get("spacecraft_id")
            if not isinstance(scid, int) or not 0 <= scid <= 1023:
                out.append(_f("TMTC-SCID", "TMTC-DB", "alarm", "settings", settings["_id"],
                              f"Spacecraft id {scid} is not a 10-bit TM SCID (0–1023).",
                              f"L’identifiant {scid} n’est pas un SCID TM sur 10 bits (0–1023)."))
    apids = cm.live_data(rows, "apids")
    for a, xs in _dups(apids, "apid").items():
        out.append(_f(f"TMTC-APID-DUP-{a}", "TMTC-APID", "alarm", "apids", xs[0]["_id"], f"APID {a} is used {len(xs)} times.",
                      f"L’APID {a} est utilisé {len(xs)} fois."))
    for a in apids:
        v = a.get("apid")
        if not isinstance(v, int) or not 0 <= v <= int(c["database"]["apid_max"]):
            out.append(_f(f"TMTC-APID-RANGE-{a['_id']}", "TMTC-APID", "alarm", "apids", a["_id"],
                          f"APID {v} is outside 0–2046 (11 bits, 0x7FF is the idle packet).",
                          f"L’APID {v} est hors de 0–2046 (11 bits, 0x7FF est le paquet de remplissage)."))
    for v, xs in _dups(P, "param_id").items():
        out.append(_f(f"TMTC-PARAM-DUP-{v}", "TMTC-PARAM", "alarm", "parameters", xs[0]["_id"],
                      f"Parameter id {_hexs(v)} is used by {', '.join(x.get('name', '') for x in xs[:4])}.",
                      f"L’identifiant {_hexs(v)} est utilisé par {', '.join(x.get('name', '') for x in xs[:4])}."))
    for v, xs in _dups(P, "name").items():
        out.append(_f(f"TMTC-PNAME-DUP-{v}", "TMTC-PARAM", "alarm", "parameters", xs[0]["_id"],
                      f"Parameter name {v} is defined {len(xs)} times.", f"Le nom de paramètre {v} est défini {len(xs)} fois."))
    types = set(c["types"]["bytes"])
    in_hk = {i for h in HK for i in h.get("parameter_ids") or []}
    no_hk = []
    for p in P:
        t = p.get("type")
        if t and t not in types:
            out.append(_f(f"TMTC-PTYPE-{p['_id']}", "TMTC-PARAM", "alarm", "parameters", p["_id"],
                          f"{p.get('name')}: unknown type {t}.", f"{p.get('name')} : type inconnu {t}."))
        r = p.get("range")
        if isinstance(r, list) and len(r) == 2 and _num(r[0]) is not None and _num(r[1]) is not None and float(r[0]) >= float(r[1]):
            out.append(_f(f"TMTC-PRANGE-{p['_id']}", "TMTC-PARAM", "alarm", "parameters", p["_id"],
                          f"{p.get('name')}: range {r} is empty.", f"{p.get('name')} : la plage {r} est vide."))
        if p.get("param_id") not in in_hk and not p.get("on_demand") and not p.get("visibility"):
            no_hk.append(p)
    if no_hk:
        out.append(_f("TMTC-PARAM-HK", "TMTC-PARAM", "caution", "parameters", no_hk[0]["_id"],
                      f"{len(no_hk)} parameter(s) are in no housekeeping packet and not marked on-demand (e.g. {no_hk[0].get('name')}).",
                      f"{len(no_hk)} paramètre(s) ne sont dans aucun paquet de servitude et ne sont pas « à la demande » (p. ex. {no_hk[0].get('name')}).",
                      count=len(no_hk), names=[x.get("name") for x in no_hk[:20]]))
    for v, xs in _dups(HK, "sid").items():
        out.append(_f(f"TMTC-SID-DUP-{v}", "TMTC-HK", "alarm", "hk", xs[0]["_id"], f"SID {v} is defined {len(xs)} times.",
                      f"Le SID {v} est défini {len(xs)} fois."))
    for h in HK:
        missing = [i for i in h.get("parameter_ids") or [] if i not in pid]
        if missing:
            out.append(_f(f"TMTC-HK-PARAM-{h['_id']}", "TMTC-HK", "alarm", "hk", h["_id"],
                          f"SID {h.get('sid')} lists {len(missing)} unknown parameter id(s) ({', '.join(_hexs(m) for m in missing[:4])}).",
                          f"Le SID {h.get('sid')} cite {len(missing)} identifiant(s) inconnu(s) ({', '.join(_hexs(m) for m in missing[:4])})."))
        if not (_num(h.get("period_s")) or 0) > 0:
            out.append(_f(f"TMTC-HK-PERIOD-{h['_id']}", "TMTC-HK", "alarm", "hk", h["_id"], f"SID {h.get('sid')} has no period.",
                          f"Le SID {h.get('sid')} n’a pas de période."))
    if HK and TIERS:
        bud = hk_budget(rows, ctx.get("modes"))
        for r in bud["regimes"]:
            if r["ok"] is False:
                out.append(_f(f"TMTC-HK-BW-{r['regime']}", "TMTC-HK-BW", "alarm", "hk", "",
                              f"Housekeeping in {r['regime']} needs {r['hk_bps']:.0f} bit/s; the {r['tier']} tier allows {r['budget_bps']:.0f} bit/s for HK.",
                              f"La servitude en régime {r['regime']} demande {r['hk_bps']:.0f} bit/s ; le palier {r['tier']} en permet {r['budget_bps']:.0f} pour la HK.",
                              **{k: r[k] for k in ("hk_bps", "budget_bps", "tier")}))
            elif r["tier"] is None:
                out.append(_f(f"TMTC-HK-BW-{r['regime']}", "TMTC-HK-BW", "caution", "hk", "",
                              f"No rate tier is set for the {r['regime']} regime: its HK budget is not checked.",
                              f"Aucun palier de débit pour le régime {r['regime']} : son bilan HK n’est pas vérifié."))
    if (ttc.get("beacon") or {}).get("enabled") and not any(h.get("beacon") for h in HK) and HK:
        out.append(_f("TMTC-BEACON", "TMTC-HK", "caution", "hk", "", "The beacon is enabled but no SID is marked as the beacon packet.",
                      "La balise est active mais aucun SID n’est marqué comme paquet de balise."))
    s8 = [t for t in TC if t.get("service") == 8 and t.get("func_id") is not None]
    for v, xs in _dups(s8, "func_id").items():
        out.append(_f(f"TMTC-TC-DUP-{v}", "TMTC-TC", "alarm", "commands", xs[0]["_id"],
                      f"S8 function id {v} is used by {', '.join(x.get('name', '') for x in xs[:4])}.",
                      f"La fonction S8 n° {v} est utilisée par {', '.join(x.get('name', '') for x in xs[:4])}."))
    for v, xs in _dups(TC, "name").items():
        out.append(_f(f"TMTC-TCNAME-DUP-{v}", "TMTC-TC", "alarm", "commands", xs[0]["_id"], f"Command {v} is defined {len(xs)} times.",
                      f"La commande {v} est définie {len(xs)} fois."))
    for t in TC:
        for a in t.get("args") or []:
            r = a.get("range")
            if isinstance(r, list) and len(r) == 2 and _num(r[0]) is not None and _num(r[1]) is not None and float(r[0]) > float(r[1]):
                out.append(_f(f"TMTC-TC-ARG-{t['_id']}-{a.get('name')}", "TMTC-TC", "alarm", "commands", t["_id"],
                              f"{t.get('name')}: argument {a.get('name')} range {r} is empty.",
                              f"{t.get('name')} : la plage {r} de l’argument {a.get('name')} est vide."))
            if "enum" in a and not a.get("enum"):
                out.append(_f(f"TMTC-TC-ENUM-{t['_id']}-{a.get('name')}", "TMTC-TC", "caution", "commands", t["_id"],
                              f"{t.get('name')}: argument {a.get('name')} has an empty value list.",
                              f"{t.get('name')} : l’argument {a.get('name')} a une liste de valeurs vide."))
        if t.get("criticality") == "critical" and not t.get("arm_execute") and not ref:
            out.append(_f(f"TMTC-TC-ARM-{t['_id']}", "TMTC-TC", "caution", "commands", t["_id"],
                          f"{t.get('name')} is critical but not arm-then-execute.",
                          f"{t.get('name')} est critique mais n’est pas « armer puis exécuter »."))
    if not ref and lines:
        def covers(role: str, name: str, l: dict) -> bool:
            for t in TC:
                if t.get("role") != role and t.get("name") != name:
                    continue
                for a in t.get("args") or []:
                    if a.get("name") != "line_index":
                        continue
                    vals, r = a.get("values"), a.get("range")
                    n = int(l.get("line_no") or 0)
                    if (isinstance(vals, list) and n in vals) or (isinstance(r, list) and len(r) == 2 and r[0] <= n <= r[1]):
                        return True
            return False
        for l in lines:
            need = (["power_on", "power_off"] if l.get("switchable") else [])
            miss = [r for r, n in (("power_on", "EPS_POWER_ON"), ("power_off", "EPS_POWER_OFF")) if r in need and not covers(r, n, l)]
            if miss:
                out.append(_f(f"TMTC-TC-LINE-{l['id']}", "TMTC-TC-LINE", "alarm", "commands", "",
                              f"Switchable power line {l.get('name')} (no. {l.get('line_no')}) has no {' / '.join('on' if m == 'power_on' else 'off' for m in miss)} telecommand.",
                              f"La ligne commutable {l.get('name')} (n° {l.get('line_no')}) n’a pas de télécommande {' / '.join('de marche' if m == 'power_on' else 'd’arrêt' for m in miss)}.",
                              line_id=l["id"]))
    pos_ids = {p.get("id") for p in POS}
    if POS:
        for t in TC:
            if t.get("position") and t["position"] not in pos_ids:
                out.append(_f(f"TMTC-TC-POS-{t['_id']}", "TMTC-TC", "caution", "commands", t["_id"],
                              f"{t.get('name')}: position {t['position']} is not in the operations organisation.",
                              f"{t.get('name')} : le poste {t['position']} n’est pas dans l’organisation des opérations."))
    for v, xs in _dups(EV, "event_id").items():
        out.append(_f(f"TMTC-EV-DUP-{v}", "TMTC-EV", "alarm", "events", xs[0]["_id"],
                      f"Event id {_hexs(v)} is used by {', '.join(x.get('name', '') for x in xs[:4])}.",
                      f"L’événement {_hexs(v)} est utilisé par {', '.join(x.get('name', '') for x in xs[:4])}."))
    sevs = set(c["events"]["severities"])
    for e in EV:
        if e.get("severity") not in sevs:
            out.append(_f(f"TMTC-EV-SEV-{e['_id']}", "TMTC-EV", "caution", "events", e["_id"],
                          f"Event {e.get('name')}: severity {e.get('severity')} is not one of {', '.join(sorted(sevs))}.",
                          f"Événement {e.get('name')} : la gravité {e.get('severity')} n’est pas parmi {', '.join(sorted(sevs))}."))
    services = {s.get("service") for s in cm.live_data(rows, "services") if s.get("used", True)}
    if services:
        need_svc = {3: bool(HK), 5: bool(EV), 12: bool(MON), 19: bool(EA)}
        need_svc.update({int(t["service"]): True for t in TC if isinstance(t.get("service"), int)})
        for s, needed in sorted(need_svc.items()):
            if needed and s not in services:
                out.append(_f(f"TMTC-SVC-{s}", "TMTC-PUS", "alarm", "services", "",
                              f"ST[{s:02d}] is needed by the database but not in the PUS services used.",
                              f"Le ST[{s:02d}] est requis par la base de données mais absent des services PUS utilisés."))

    # ── FDIR
    ev_names = {e.get("name") for e in EV} | {e.get("event_id") for e in EV}
    tc_by_name = {t.get("name"): t for t in TC}
    tc_by_fid = {t.get("func_id"): t for t in s8}
    mon_params = {}
    for m in MON:
        mon_params.setdefault(m.get("parameter") or (pid.get(m.get("param_id")) or {}).get("name"), []).append(m)
    levels = {k: _num((v or {}).get("value")) for k, v in (shed.get("bus_protection") or {}).items()}
    for m in MON:
        p = pname.get(m.get("parameter")) or pid.get(m.get("param_id"))
        label = m.get("pmon_id") or m.get("name")
        if p is None:
            out.append(_f(f"FDIR-MON-PARAM-{m['_id']}", "FDIR-MON", "alarm", "monitors", m["_id"],
                          f"Monitor {label}: parameter {m.get('parameter') or _hexs(m.get('param_id'))} is not in the TM database.",
                          f"Surveillance {label} : le paramètre {m.get('parameter') or _hexs(m.get('param_id'))} n’est pas dans la base TM."))
            continue
        lo, hi = _num(m.get("low")), _num(m.get("high"))
        if m.get("check", "limit") == "limit":
            if lo is not None and hi is not None and lo >= hi:
                out.append(_f(f"FDIR-MON-LIM-{m['_id']}", "FDIR-MON", "alarm", "monitors", m["_id"],
                              f"Monitor {label}: low limit {lo:g} is not below high limit {hi:g}.",
                              f"Surveillance {label} : la limite basse {lo:g} n’est pas sous la limite haute {hi:g}."))
            r = p.get("range")
            if isinstance(r, list) and len(r) == 2 and _num(r[0]) is not None and _num(r[1]) is not None:
                bad = [v for v in (lo, hi) if v is not None and not (float(r[0]) <= v <= float(r[1]))]
                if bad:
                    out.append(_f(f"FDIR-MON-RANGE-{m['_id']}", "FDIR-MON", "caution", "monitors", m["_id"],
                                  f"Monitor {label}: threshold {bad[0]:g} is outside the parameter range {r}.",
                                  f"Surveillance {label} : le seuil {bad[0]:g} est hors de la plage du paramètre {r}."))
        v = m.get("validity")
        if v and not (pname.get(v.get("parameter")) or pid.get(v.get("param_id"))):
            out.append(_f(f"FDIR-MON-VALID-{m['_id']}", "FDIR-MON", "alarm", "monitors", m["_id"],
                          f"Monitor {label}: validity parameter {v.get('parameter') or _hexs(v.get('param_id'))} is not in the TM database.",
                          f"Surveillance {label} : le paramètre de validité {v.get('parameter') or _hexs(v.get('param_id'))} n’est pas dans la base TM."))
        if (not ref and str(p.get("name")).endswith(".bus_voltage") and lo is not None
                and any(x is not None for x in levels.values()) and not any(x is not None and abs(lo - x) < 1e-6 for x in levels.values())):
            out.append(_f(f"FDIR-MON-BUS-{m['_id']}", "FDIR-MON", "caution", "monitors", m["_id"],
                          f"Monitor {label}: bus low limit {lo:g} V is none of the named bus-protection levels.",
                          f"Surveillance {label} : la limite basse {lo:g} V du bus n’est aucun des seuils de protection nommés."))
    for a in EA:
        label = a.get("name") or a.get("ea_id")
        if a.get("engine_action"):      # EOSAT-1 rule table: an engine action, not a TC function
            continue
        fn = tc_by_name.get(a.get("action")) if a.get("action") else tc_by_fid.get(a.get("action_func_id"))
        if fn is None and (a.get("action") or a.get("action_func_id") is not None):
            out.append(_f(f"FDIR-EA-FUNC-{a['_id']}", "FDIR-EA", "alarm", "event_actions", a["_id"],
                          f"Event-action {label}: function {a.get('action') or a.get('action_func_id')} is not in the TC catalogue.",
                          f"Événement-action {label} : la fonction {a.get('action') or a.get('action_func_id')} n’est pas dans le catalogue TC."))
        elif fn is None:
            out.append(_f(f"FDIR-EA-FUNC-{a['_id']}", "FDIR-EA", "alarm", "event_actions", a["_id"],
                          f"Event-action {label} calls no function.", f"L’événement-action {label} n’appelle aucune fonction."))
        if a.get("on_clear") and a["on_clear"] not in tc_by_name and not ref:
            out.append(_f(f"FDIR-EA-CLEAR-{a['_id']}", "FDIR-EA", "alarm", "event_actions", a["_id"],
                          f"Event-action {label}: on-clear function {a['on_clear']} is not in the TC catalogue.",
                          f"Événement-action {label} : la fonction de retour {a['on_clear']} n’est pas dans le catalogue TC."))
        tr = a.get("trigger") or {}
        if tr.get("kind") == "event" and (tr.get("event") or tr.get("event_id") or tr.get("id")) not in ev_names:
            out.append(_f(f"FDIR-EA-TRIG-{a['_id']}", "FDIR-EA", "alarm", "event_actions", a["_id"],
                          f"Event-action {label}: trigger event {tr.get('event') or _hexs(tr.get('event_id') or tr.get('id'))} is not in the event catalogue.",
                          f"Événement-action {label} : l’événement déclencheur {tr.get('event') or _hexs(tr.get('event_id') or tr.get('id'))} n’est pas au catalogue."))
        elif tr.get("kind") == "param":
            pn = tr.get("parameter") or (pid.get(tr.get("param_id") or tr.get("id")) or {}).get("name")
            ms = mon_params.get(pn) or []
            if not ms:
                out.append(_f(f"FDIR-EA-TRIG-{a['_id']}", "FDIR-EA", "alarm", "event_actions", a["_id"],
                              f"Event-action {label}: no S12 monitor watches {pn or _hexs(tr.get('param_id') or tr.get('id'))}.",
                              f"Événement-action {label} : aucune surveillance S12 ne suit {pn or _hexs(tr.get('param_id') or tr.get('id'))}."))
            elif tr.get("limit") in ("high", "low") and not any(_num(x.get(tr["limit"])) is not None for x in ms):
                out.append(_f(f"FDIR-EA-SIDE-{a['_id']}", "FDIR-EA", "caution", "event_actions", a["_id"],
                              f"Event-action {label} is armed on the {tr['limit']} limit, but no monitor of {pn} has one.",
                              f"L’événement-action {label} est armé sur la limite {tr['limit']}, mais aucune surveillance de {pn} n’en a."))
        if fn is not None and lines and not ref and (fn.get("role") == "power_off" or fn.get("name") == "EPS_POWER_OFF"):
            n = (a.get("action_data") or [None])[0]
            l = next((x for x in lines if int(x.get("line_no") or -1) == n), None)
            if l is not None and (not l.get("switchable") or line_classes(l) & never):
                out.append(_f(f"FDIR-EA-SELFOFF-{a['_id']}", "FDIR-EA", "alarm", "event_actions", a["_id"],
                              f"Event-action {label} would switch off line {l.get('name')}, which feeds the OBC, EPS, battery or receiver.",
                              f"L’événement-action {label} couperait la ligne {l.get('name')}, qui alimente l’OBC, l’EPS, la batterie ou le récepteur.",
                              element_ids=list(l.get("load_element_ids") or [])))
    if shed:
        uv, es, ac, ov = (levels.get(k) for k in ("uv_v", "eps_safe_v", "aocs_safe_v", "ov_v"))
        rng = shed.get("bus_range_v") or [None, None]
        vmin, vmax = _num(rng[0]) if rng else None, _num(rng[1]) if rng and len(rng) > 1 else None
        if None in (uv, es, ac):
            out.append(_f("FDIR-SHED-LEVELS", "FDIR-SHED", "caution", "load_shed", shed["_id"],
                          "The named bus-protection levels are not set (no unregulated battery bus range in the electrical model).",
                          "Les seuils de protection du bus ne sont pas fixés (pas de plage de bus batterie non régulé dans le modèle électrique)."))
        else:
            order_ok = uv > es > ac and (vmin is None or ac > vmin) and (vmax is None or uv < vmax) and (ov is None or vmax is None or ov > vmax)
            if not order_ok:
                out.append(_f("FDIR-SHED-ORDER", "FDIR-SHED", "alarm", "load_shed", shed["_id"],
                              f"Bus-protection levels must satisfy bus min < aocs_safe < eps_safe < uv < bus max < ov (got {ac:g} / {es:g} / {uv:g} V, range {rng}).",
                              f"Les seuils doivent vérifier min du bus < aocs_safe < eps_safe < uv < max du bus < ov (valeurs {ac:g} / {es:g} / {uv:g} V, plage {rng})."))
        if lines and not ref:
            by_name = {l.get("name"): l for l in lines}
            for st in shed.get("stages") or []:
                for ln in st.get("lines") or []:
                    l = by_name.get(ln)
                    if l is None:
                        out.append(_f(f"FDIR-SHED-LINE-{ln}", "FDIR-SHED", "alarm", "load_shed", shed["_id"],
                                      f"Load-shed stage {st.get('stage')} names line {ln}, which is not in the electrical model.",
                                      f"L’étage de délestage {st.get('stage')} cite la ligne {ln}, absente du modèle électrique."))
                    elif not l.get("switchable") or line_classes(l) & never:
                        out.append(_f(f"FDIR-SHED-LINE-{ln}", "FDIR-SHED", "alarm", "load_shed", shed["_id"],
                                      f"Load-shed stage {st.get('stage')} would switch off {ln}, which must stay powered.",
                                      f"L’étage de délestage {st.get('stage')} couperait {ln}, qui doit rester alimentée."))
    if MON or EA:
        if not safe:
            out.append(_f("FDIR-SAFE", "FDIR-SAFE", "alarm", "safe_mode", "", "No safe-mode definition.", "Aucune définition du mode survie."))
        else:
            am = {m.get("name") for m in AM}
            if safe.get("aocs_mode") and AM and safe["aocs_mode"] not in am:
                out.append(_f("FDIR-SAFE-AOCS", "FDIR-SAFE", "alarm", "safe_mode", safe["_id"],
                              f"Safe mode uses AOCS mode {safe['aocs_mode']}, which is not in the AOCS mode table.",
                              f"Le mode survie utilise le mode SCAO {safe['aocs_mode']}, absent de la table des modes SCAO."))
            tn = {t.get("name") for t in TIERS}
            if safe.get("rate_tier") and TIERS and safe["rate_tier"] not in tn:
                out.append(_f("FDIR-SAFE-TIER", "FDIR-SAFE", "alarm", "safe_mode", safe["_id"],
                              f"Safe mode uses rate tier {safe['rate_tier']}, which is not in the ladder.",
                              f"Le mode survie utilise le palier {safe['rate_tier']}, absent de l’échelle de débits."))
            ex = (safe.get("exit") or {}).get("function")
            if ex and ex not in tc_by_name and not ref:
                out.append(_f("FDIR-SAFE-EXIT", "FDIR-SAFE", "alarm", "safe_mode", safe["_id"],
                              f"Safe-mode exit function {ex} is not in the TC catalogue.",
                              f"La fonction de sortie du mode survie {ex} n’est pas dans le catalogue TC."))
            if not safe.get("entry"):
                out.append(_f("FDIR-SAFE-ENTRY", "FDIR-SAFE", "caution", "safe_mode", safe["_id"], "Safe mode has no entry trigger.",
                              "Le mode survie n’a aucun déclencheur d’entrée."))
            if lines and not ref:
                for l in lines:
                    if (l["id"] in (safe.get("line_ids_off") or []) or l.get("name") in (safe.get("lines_off") or [])) and (
                            not l.get("switchable") or line_classes(l) & never):
                        out.append(_f(f"FDIR-SAFE-OFF-{l['id']}", "FDIR-SAFE", "alarm", "safe_mode", safe["_id"],
                                      f"Safe mode switches off {l.get('name')}, which must stay powered.",
                                      f"Le mode survie coupe {l.get('name')}, qui doit rester alimentée."))
    if ctx.get("fmeca_rows") and not ref:
        cov = fmeca_coverage(rows, ctx["fmeca_rows"])
        for x in cov["rows"]:
            if not x["critical"]:
                continue
            name = x.get("component") or x.get("element_id")
            mode = (x.get("mode") or {}).get("en", "") if isinstance(x.get("mode"), dict) else str(x.get("mode") or "")
            mode_fr = (x.get("mode") or {}).get("fr", mode) if isinstance(x.get("mode"), dict) else mode
            if not x["detected"]:
                out.append(_f(f"FDIR-FMECA-DET-{x['fmeca_row_id']}", "FDIR-FMECA", "alarm", "monitors", "",
                              f"{name} — {mode} (S{x['severity']}): no accepted monitor detects it.",
                              f"{name} — {mode_fr} (S{x['severity']}) : aucune surveillance acceptée ne la détecte.",
                              element_ids=[x["element_id"]] if x.get("element_id") else []))
            elif not x["recovered"]:
                out.append(_f(f"FDIR-FMECA-REC-{x['fmeca_row_id']}", "FDIR-FMECA", "alarm", "event_actions", "",
                              f"{name} — {mode} (S{x['severity']}): detected, but no event-action recovers from it.",
                              f"{name} — {mode_fr} (S{x['severity']}) : détectée, mais aucun événement-action n’y répond.",
                              element_ids=[x["element_id"]] if x.get("element_id") else []))

    # ── AOCS
    for v, xs in _dups(AM, "code").items():
        out.append(_f(f"AOCS-CODE-DUP-{v}", "AOCS-MODE", "alarm", "aocs_modes", xs[0]["_id"], f"AOCS mode code {v} is used {len(xs)} times.",
                      f"Le code de mode SCAO {v} est utilisé {len(xs)} fois."))
    names = {m.get("name") for m in AM}
    for t in AT:
        if t.get("from") not in names or t.get("to") not in names:
            out.append(_f(f"AOCS-TRANS-{t['_id']}", "AOCS-TRANS", "alarm", "aocs_transitions", t["_id"],
                          f"Transition {t.get('from')} → {t.get('to')} names a mode that is not in the table.",
                          f"La transition {t.get('from')} → {t.get('to')} cite un mode absent de la table."))
        elif t.get("trigger") == "autonomous" and not t.get("guard"):
            out.append(_f(f"AOCS-GUARD-{t['_id']}", "AOCS-TRANS", "caution", "aocs_transitions", t["_id"],
                          f"Autonomous transition {t.get('from')} → {t.get('to')} has no guard.",
                          f"La transition autonome {t.get('from')} → {t.get('to')} n’a pas de condition."))
    if AM and AT:
        from .cdr_propose import initial_aocs_mode
        init = initial_aocs_mode(AM, c) or "OFF"
        seen, todo = {init, "OFF"}, [init, "OFF"]
        while todo:
            x = todo.pop()
            for t in AT:
                if t.get("from") == x and t.get("to") not in seen:
                    seen.add(t["to"])
                    todo.append(t["to"])
        for m in AM:
            if m.get("name") not in seen:
                out.append(_f(f"AOCS-REACH-{m['_id']}", "AOCS-MODE", "caution", "aocs_modes", m["_id"],
                              f"AOCS mode {m.get('name')} cannot be reached from {init}.",
                              f"Le mode SCAO {m.get('name')} est inaccessible depuis {init}."))
    zlo, zhi = c["aocs"]["control"]["zeta_range"]
    inertia = ctl.get("inertia_kgm2")
    i_max = None
    if isinstance(inertia, list) and inertia:
        try:
            i_max = max(float(inertia[i][i]) for i in range(3)) if isinstance(inertia[0], list) else max(float(x) for x in inertia)
        except (TypeError, ValueError, IndexError):
            i_max = None
    torque = _num(ctl.get("wheel_max_torque_nm"))
    theta = math.radians(float(c["aocs"]["control"]["torque_check_error_deg"]))
    for m in AM:
        g = m.get("gains") or {}
        if "wheel" in (m.get("actuators") or []) and not g:
            out.append(_f(f"AOCS-GAINS-{m['_id']}", "AOCS-CTRL", "caution", "aocs_modes", m["_id"],
                          f"AOCS mode {m.get('name')} drives the wheels but has no control gains.",
                          f"Le mode SCAO {m.get('name')} commande les roues mais n’a pas de gains."))
        wn, z = _num(g.get("omega_n")), _num(g.get("zeta"))
        if g and (wn is None or wn <= 0 or z is None or not zlo <= z <= zhi):
            out.append(_f(f"AOCS-GAINS-RANGE-{m['_id']}", "AOCS-CTRL", "alarm", "aocs_modes", m["_id"],
                          f"AOCS mode {m.get('name')}: ωn must be > 0 and ζ within {zlo}–{zhi} (got {wn}, {z}).",
                          f"Mode SCAO {m.get('name')} : ωn doit être > 0 et ζ dans {zlo}–{zhi} (valeurs {wn}, {z})."))
        elif wn and i_max and torque and i_max * wn * wn * theta > torque:
            out.append(_f(f"AOCS-TORQUE-{m['_id']}", "AOCS-CTRL", "caution", "aocs_modes", m["_id"],
                          f"AOCS mode {m.get('name')}: a {math.degrees(theta):.0f}° error asks {i_max * wn * wn * theta * 1000:.2f} mN·m, above the wheel's {torque * 1000:.2f} mN·m.",
                          f"Mode SCAO {m.get('name')} : une erreur de {math.degrees(theta):.0f}° demande {i_max * wn * wn * theta * 1000:.2f} mN·m, au-delà des {torque * 1000:.2f} mN·m de la roue."))
        if not ref and units:
            have = {u["cls"] for u in units.values()}
            miss = [x for x in (m.get("actuators") or []) + (m.get("sensors") or []) if x not in have and x != "gyro"]
            if miss:
                out.append(_f(f"AOCS-HW-{m['_id']}", "AOCS-MODE", "alarm", "aocs_modes", m["_id"],
                              f"AOCS mode {m.get('name')} uses {', '.join(miss)}, which the design does not have.",
                              f"Le mode SCAO {m.get('name')} utilise {', '.join(miss)}, que la conception n’a pas."))
    if any(m.get("name") == "DETUMBLE" for m in AM) and ctl and ctl.get("bdot_gain_am2_per_tps") in (None, 0):
        out.append(_f("AOCS-BDOT", "AOCS-CTRL", "caution", "aocs_control", ctl.get("_id", ""),
                      "DETUMBLE has no B-dot gain (select a magnetorquer with a dipole moment, or enter it).",
                      "DETUMBLE n’a pas de gain B-dot (choisir un magnétocoupleur avec un moment dipolaire, ou le saisir)."))

    # ── TT&C ladder
    if TIERS or ttc:
        for v, xs in _dups(TIERS, "name").items():
            out.append(_f(f"TTC-TIER-DUP-{v}", "TTC-LADDER", "alarm", "rate_tiers", xs[0]["_id"], f"Rate tier {v} is defined twice.",
                          f"Le palier {v} est défini deux fois."))
        tn = {t.get("name") for t in TIERS}
        for role in ("default_tier", "beacon_tier", "safe_tier"):
            if ttc.get(role) and ttc[role] not in tn:
                out.append(_f(f"TTC-ROLE-{role}", "TTC-LADDER", "alarm", "ttc", ttc.get("_id", ""),
                              f"{role} = {ttc[role]} is not a tier of the ladder.", f"{role} = {ttc[role]} n’est pas un palier de l’échelle."))
            elif not ttc.get(role) and TIERS:
                out.append(_f(f"TTC-ROLE-{role}", "TTC-LADDER", "caution", "ttc", ttc.get("_id", ""),
                              f"No {role.replace('_', ' ')} is chosen.", f"Aucun {role.replace('_', ' ')} n’est choisi."))
        for t in TIERS:
            if not (_num(t.get("bps")) or 0) > 0:
                out.append(_f(f"TTC-BPS-{t['_id']}", "TTC-LADDER", "alarm", "rate_tiers", t["_id"], f"Tier {t.get('name')} has no bit rate.",
                              f"Le palier {t.get('name')} n’a pas de débit."))
        to = _num(ttc.get("cmd_loss_switch_timeout_s"))
        if ttc and (to is None or to < float(c["ttc"]["min_cmd_loss_timeout_s"])):
            out.append(_f("TTC-CMDLOSS", "TTC-CFG", "caution", "ttc", ttc.get("_id", ""),
                          f"The command-loss timer ({to}) is shorter than {c['ttc']['min_cmd_loss_timeout_s'] / 3600:.0f} h: a normal gap between contacts would trip it.",
                          f"La minuterie de perte de commande ({to}) est plus courte que {c['ttc']['min_cmd_loss_timeout_s'] / 3600:.0f} h : un intervalle normal entre contacts la déclencherait."))
        if ttc.get("cmd_loss_action") and ttc["cmd_loss_action"] not in tc_by_name and not ref:
            out.append(_f("TTC-CMDLOSS-ACT", "TTC-CFG", "alarm", "ttc", ttc.get("_id", ""),
                          f"Command-loss action {ttc['cmd_loss_action']} is not in the TC catalogue.",
                          f"L’action de perte de commande {ttc['cmd_loss_action']} n’est pas dans le catalogue TC."))
        bs = (ttc.get("beacon") or {}).get("hk_sid")
        if bs is not None and HK and bs not in {h.get("sid") for h in HK}:
            out.append(_f("TTC-BEACON-SID", "TTC-CFG", "caution", "ttc", ttc.get("_id", ""), f"Beacon SID {bs} is not a housekeeping structure.",
                          f"Le SID de balise {bs} n’est pas une structure de servitude."))

    # ── power-line states per mode
    if lines and not ref:
        members = ctx.get("members") or []
        safe_off = set(safe.get("line_ids_off") or []) if safe else set()
        by_mode = {s.get("mode_id"): s for s in LS}
        for m in ctx.get("modes") or []:
            st = by_mode.get(m["id"])
            if st is None:
                out.append(_f(f"EL-STATE-MISSING-{m['id']}", "EL-STATE", "caution", "line_states", "",
                              f"Mode {m.get('name')} has no power-line states.", f"Le mode {m.get('name')} n’a pas d’états de lignes."))
                continue
            for l in lines:
                v = (st.get("states") or {}).get(l["id"])
                loads = l.get("load_element_ids") or []
                if v == "off" and (not l.get("switchable") or line_classes(l) & never):
                    out.append(_f(f"EL-STATE-NEVER-{m['id']}-{l['id']}", "EL-STATE", "alarm", "line_states", st["_id"],
                                  f"Mode {m.get('name')}: line {l.get('name')} is off but must stay powered.",
                                  f"Mode {m.get('name')} : la ligne {l.get('name')} est coupée mais doit rester alimentée."))
                elif v == "off" and any(mem.get("mode_id") == m["id"] and mem.get("element_id") in loads and mem.get("status") != "rejected"
                                        and ((mem.get("power_state") or "off") != "off") for mem in members):
                    out.append(_f(f"EL-STATE-LOAD-{m['id']}-{l['id']}", "EL-STATE", "caution", "line_states", st["_id"],
                                  f"Mode {m.get('name')}: line {l.get('name')} is off while a load on it is on in the mode matrix.",
                                  f"Mode {m.get('name')} : la ligne {l.get('name')} est coupée alors qu’une de ses charges est allumée dans la matrice des modes."))
                elif v == "on" and m.get("kind") == "safe" and l["id"] in safe_off:
                    out.append(_f(f"EL-STATE-SAFE-{m['id']}-{l['id']}", "EL-STATE", "caution", "line_states", st["_id"],
                                  f"Safe mode switches {l.get('name')} off, but the {m.get('name')} line states keep it on.",
                                  f"Le mode survie coupe {l.get('name')}, mais les états du mode {m.get('name')} la laissent alimentée."))

    # ── operations
    if POS or TC:
        if POS and not any(p.get("id") == "flight_director" or p.get("all_commands") for p in POS):
            out.append(_f("OPS-FD", "OPS-POS", "caution", "positions", "", "No Flight Director (all-commands) position.",
                          "Aucun poste de directeur de vol (toutes commandes)."))
        if POS:
            allowed = {f for p in POS for f in (p.get("allowed_func_ids") or [])}
            all_cmd = any(p.get("all_commands") for p in POS)
            orphan = [t for t in s8 if t.get("func_id") not in allowed and not all_cmd]
            if orphan:
                out.append(_f("OPS-FUNC", "OPS-POS", "caution", "positions", "",
                              f"{len(orphan)} function(s) are allowed for no position (e.g. {orphan[0].get('name')}).",
                              f"{len(orphan)} fonction(s) ne sont autorisées à aucun poste (p. ex. {orphan[0].get('name')}).", count=len(orphan)))
            covered = {s for p in POS for s in (p.get("subsystems") or [])}
            subs = sorted({t.get("subsystem") for t in TC if t.get("subsystem")} - covered)
            if subs and not all_cmd:
                out.append(_f("OPS-SUBS", "OPS-POS", "caution", "positions", "", f"No position covers {', '.join(subs)}.",
                              f"Aucun poste ne couvre {', '.join(subs)}."))
        if (GNG or FR) and not ref:
            named = {fn for g in GNG for fn in (g.get("functions") or [])} | {r.get("ref") for r in FR}
            crit = [t for t in TC if t.get("criticality") == "critical" and t.get("name") not in named]
            for t in crit:
                out.append(_f(f"OPS-CRIT-{t['_id']}", "OPS-GNG", "caution", "gonogo", "",
                              f"Critical command {t.get('name')} has no GO/NO-GO situation or flight rule.",
                              f"La commande critique {t.get('name')} n’a ni situation GO/NO-GO ni règle de vol."))
    return out


def summarise(findings: list[dict]) -> dict[str, Any]:
    by_group: dict[str, dict[str, int]] = {}
    group_of = {k: v["group"] for k, v in cm.KINDS.items()}
    for f in findings:
        g = group_of.get(f.get("target_kind") or "", "tmtc")
        if f["rule"].startswith("EL-STATE") or f["rule"].startswith("AOCS"):
            g = "aocs"
        elif f["rule"].startswith("OPS"):
            g = "ops"
        elif f["rule"].startswith("FDIR"):
            g = "fdir"
        elif f["rule"].startswith(("TMTC", "TTC")):
            g = "tmtc"
        s = by_group.setdefault(g, {"alarm": 0, "caution": 0})
        s[f["severity"]] = s.get(f["severity"], 0) + 1
    return {"alarm": sum(1 for f in findings if f["severity"] == "alarm"),
            "caution": sum(1 for f in findings if f["severity"] == "caution"), "by_group": by_group}
