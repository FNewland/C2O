"""SpaceCDF — the default CDR database proposed from the design (rule set TMTC / FDIR / AOCS /
TTC / EL-STATE / OPS, Nov 2026).

Pure: ``plan(study_id, facts)`` returns ``{kind: {row_id: {key, data, owner_seat, rationale,
standard_ref}}}`` for ``cdr_model.reconcile``. The facts are plain dicts gathered by
``routers/cdr.py``:

    elements        the study's elements (units are the space-hardware leaves)
    lines, rails, buses     electrical rows that count (not rejected)
    heaters         HeaterRow dicts (rule 7)
    modes           mode elements as ``{id, name, kind}``; members: ModeElementRow dicts
    fdir_proposals  rule-8 (FD-01 monitor / FD-02 action) proposals, any status
    existing        the study's CDR rows (ids, parameter / function / event / SID numbers
                    already given are kept, so adding a unit never renumbers the database)

What is derived from what (each row carries its rationale):

* parameters — per subsystem present (cdr_rules.yaml parameters.subsystem), per unit class
  (incl. the FD-01 monitor parameter), per power line (state + current), per bus segment,
  per heater; ids in the subsystem's EOSAT-1 block;
* housekeeping — one SID per subsystem at its period, the beacon SID; EPS/OBDH/system at boot;
* TC functions — the EOSAT-1-class set filtered by what the design holds (redundant OBC,
  wheels, payload, propulsion …), S8 ids in the subsystem's block, line / wheel / heater
  argument ranges from the design, criticality and arm-execute;
* events — standard set + one out-of-limit event per monitor;
* monitors — the FD-01 proposals promoted onto TM parameters (validity = the unit's line
  is on) + the default EPS / OBDH / AOCS monitors with the named bus-protection levels;
* event-actions — the FD-02 stubs mapped onto real TC functions + the default actions;
* load shed, safe mode, FDIR levels; AOCS modes / transitions / control; rate ladder,
  beacon and command-loss timer; power-line states per mode; positions, GO/NO-GO, flight
  rules; MCS limits from the monitors.
"""
from __future__ import annotations

import math
from typing import Any

from . import cdr_model as cm
from .mode_model import cfg as mode_cfg
from .mode_model import proposal_units, unit_class
from .rule_inputs import kb_component, perf, qty

#: EOSAT-1 mission phases (service_dispatch._PHASE_NAMES)
PHASES = ["PRE_SEPARATION", "SEPARATION_TIMER", "INITIAL_POWER_ON", "BOOTLOADER_OPS", "LEOP", "COMMISSIONING", "NOMINAL"]

#: unit class → TM/TC subsystem when the element tree gives no domain
CLASS_SUBSYSTEM = {
    "battery": "eps", "eps": "eps", "solar_array": "eps", "obc": "obdh", "transmitter": "ttc", "receiver": "ttc",
    "antenna": "ttc", "wheel": "aocs", "star_tracker": "aocs", "magnetorquer": "aocs", "adcs_sensor": "aocs",
    "gnss": "aocs", "heater": "tcs", "payload": "payload", "propulsion": "prop", "structure": "str",
    "adcs_unit": "aocs", "payload_electronics": "payload",
}
#: Classes an integrated ADCS unit (class adcs_unit) provides by itself.
ADCS_UNIT_PROVIDES = ("wheel", "magnetorquer", "adcs_sensor")


def _kbp(e: dict) -> dict:
    return {**((kb_component(e) or {}).get("performance") or {}), **perf(e)}


def _num(v: Any) -> float | None:
    try:
        f = float(v)
        return f if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def _op_range(e: dict, c: dict) -> list[float]:
    kb = kb_component(e) or {}
    for src in ((e.get("kb_spec") or {}), perf(e), kb, kb.get("performance") or {}):
        r = src.get("operating_temp_c") if isinstance(src, dict) else None
        if isinstance(r, (list, tuple)) and len(r) == 2 and all(_num(x) is not None for x in r):
            return [float(r[0]), float(r[1])]
    p = perf(e)
    if _num(p.get("op_temp_min_c")) is not None and _num(p.get("op_temp_max_c")) is not None:
        return [float(p["op_temp_min_c"]), float(p["op_temp_max_c"])]
    return list(c["parameters"]["op_range_default"])


def _fill(text: dict, **kw: Any) -> dict:
    out = {}
    for lang in ("en", "fr"):
        s = str(text.get(lang, ""))
        for k, v in kw.items():
            s = s.replace("{" + k + "}", str(v))
        out[lang] = s
    return out


class _Alloc:
    """Stable number allocation: keep what ``existing`` gave a name, else the next free number."""

    def __init__(self, existing: dict[str, int], used: set[int]):
        self.existing = existing
        self.used = set(used)

    def get(self, name: str, start: int, end: int) -> int | None:
        if name in self.existing:
            return self.existing[name]
        n = start
        while n <= end:
            if n not in self.used:
                self.used.add(n)
                self.existing[name] = n
                return n
            n += 1
        return None


def _existing_numbers(existing: list[dict], kind: str, field: str) -> tuple[dict[str, int], set[int]]:
    names: dict[str, int] = {}
    used: set[int] = set()
    for r in existing:
        if r.get("kind") != kind or r.get("deleted_at"):
            continue
        d = r.get("data") or {}
        v = d.get(field)
        if isinstance(v, int):
            used.add(v)
            if str(r.get("origin") or "").startswith("rule:") and r.get("key"):
                names.setdefault(r["key"], v)
    return names, used


# ───────────────────────────────────────────────────────────── facts

def design_facts(facts: dict) -> dict[str, Any]:
    """Units with class and subsystem, flags and enum vocabularies the rules use."""
    c = cm.cfg()
    mc = mode_cfg()
    els = [e for e in facts.get("elements") or [] if not e.get("deleted_at")]
    by_id = {e["id"]: e for e in els}
    units = []
    for e in proposal_units(els):
        cls = unit_class(e, mc)
        sub = cm.element_subsystem(e, by_id, c) or CLASS_SUBSYSTEM.get(cls) or "sys"
        if cls == "generic" and sub in ("sys",):
            continue
        units.append({"el": e, "id": e["id"], "name": e.get("name") or e["id"], "slug": cm.slug(e.get("name") or e["id"], 24),
                      "cls": cls, "sub": sub, "qty": qty(e)})
    classes: dict[str, list[dict]] = {}
    for u in units:
        classes.setdefault(u["cls"], []).append(u)

    # An integrated ADCS unit carries its own wheels, magnetorquers and sensors.
    provided = set(ADCS_UNIT_PROVIDES) if classes.get("adcs_unit") else set()

    def n_of(cls: str) -> int:
        return sum(u["qty"] for u in classes.get(cls, []))

    def redundant(cls: str) -> bool:
        return n_of(cls) >= 2 or any((u["el"].get("redundancy_type") or "none") not in ("none", "", None)
                                     for u in classes.get(cls, []))
    lines = sorted([l for l in facts.get("lines") or [] if l.get("status") != "rejected" and not l.get("deleted_at")],
                   key=lambda l: (int(l.get("line_no") or 0), l.get("name") or ""))
    buses = [b for b in facts.get("buses") or [] if b.get("status") != "rejected" and not b.get("deleted_at")]
    heaters = list(facts.get("heaters") or [])
    heater_units = classes.get("heater", [])
    flags = {
        "obc_redundant": redundant("obc"),
        "ttc_redundant": redundant("transmitter") or redundant("receiver"),
        "star_tracker_redundant": redundant("star_tracker"),
        "bus_redundant": any((b.get("redundancy") or "none") != "none" for b in buses)
                         or len({(b.get("protocol"), b.get("segment")) for b in buses}) >= 2,
        "wheel": bool(classes.get("wheel")) or "wheel" in provided,
        "magnetorquer": bool(classes.get("magnetorquer")) or "magnetorquer" in provided,
        "star_tracker": bool(classes.get("star_tracker")), "payload": bool(classes.get("payload")),
        "propulsion": bool(classes.get("propulsion")), "heater": bool(heaters or heater_units),
        "adcs_sensor": bool(classes.get("adcs_sensor")) or "adcs_sensor" in provided, "gnss": bool(classes.get("gnss")),
    }
    subs = {"sys", "fdir"} | {u["sub"] for u in units}
    if lines:
        subs.add("eps")
    if heaters:
        subs.add("tcs")
    modes = list(facts.get("modes") or [])
    heater_names = [h.get("name") or h.get("id") for h in heaters] or [u["name"] for u in heater_units]
    return {"c": c, "mc": mc, "els": els, "by_id": by_id, "units": units, "classes": classes, "flags": flags,
            "subs": subs, "lines": lines, "buses": buses, "heaters": heaters, "heater_names": heater_names,
            "modes": modes, "n_wheels": n_of("wheel"), "provided": provided,
            "rails_all": [r for r in facts.get("rails") or [] if r.get("status") != "rejected" and not r.get("deleted_at")]}


def _line_of_unit(f: dict, eid: str) -> dict | None:
    return next((l for l in f["lines"] if eid in (l.get("load_element_ids") or [])), None)


# ───────────────────────────────────────────────────────────── plan

def plan(study_id: str, facts: dict) -> dict[str, dict[str, dict]]:
    f = design_facts(facts)
    c = f["c"]
    existing = list(facts.get("existing") or [])
    out: dict[str, dict[str, dict]] = {k: {} for k in cm.KINDS}

    def put(kind: str, data: dict, en: str, fr: str, node: dict | None = None) -> str:
        key = cm.key_of(kind, data)
        rid = cm.det_id(study_id, kind, key)
        r = cm.ref(node or {"source": "c2o_default"}, c)
        out[kind][rid] = {"key": key, "data": data, "owner_seat": cm.owner_seat(kind, data, c),
                          "rationale": cm.bi(en, fr), "standard_ref": r["standard_ref"]}
        return rid

    sub_cfg = {s["key"]: s for s in cm.subsystems(c)}
    present = [s for s in (c["housekeeping"]["sid_order"]) if s in f["subs"]]

    # ── TT&C ladder first (enums need it)
    tiers = _rate_tiers(f)
    tier_names = [t["name"] for t in tiers]
    roles = {r: n for r, n in c["ttc"]["roles"].items() if n in tier_names}
    aocs_modes, aocs_trans = _aocs_modes(f)
    sc_modes = [m.get("name") for m in f["modes"]] or ["SAFE", "NOMINAL"]
    enums = {"sc_modes": sc_modes, "aocs_modes": [m["name"] for m in aocs_modes], "rate_tiers": tier_names,
             "phases": PHASES, "obc_modes": ["NOMINAL", "SAFE", "EMERGENCY"], "payload_modes": ["OFF", "STANDBY", "IMAGING"]}

    # ── settings, APIDs, services
    db = c["database"]
    put("settings", {"spacecraft_id": db["spacecraft_id"], "pus_version": db["pus_version"], "time_code": db["time_code"],
                     "application_apid": db["application_apid"], "bootloader_apid": db["bootloader_apid"],
                     # W3.01: the HK packet overhead the budgets use (full PUS-C: counter + destination id, CUC 4+2, uint16 SID)
                     **dict(c["downlink_budget"].get("packet_layout") or {}),
                     "packet_overhead_bytes": int(c["downlink_budget"]["packet_overhead_bytes"])},
        "Spacecraft id, PUS-C and the application / bootloader APIDs of the EOSAT-1 reference design.",
        "Identifiant du satellite, PUS-C et APID de l’application et du chargeur d’amorçage de la conception de référence EOSAT-1.",
        c["database"])
    put("apids", {"apid": db["application_apid"], "name": "OBC application", "role": "application", "subsystem": "obdh"},
        "The OBC application software sources the housekeeping and event packets.",
        "Le logiciel applicatif de l’OBC émet les paquets de servitude et d’événements.", c["database"])
    put("apids", {"apid": db["bootloader_apid"], "name": "OBC bootloader", "role": "bootloader", "subsystem": "obdh"},
        "The bootloader has its own APID so beacon telemetry is told apart from the application's.",
        "Le chargeur d’amorçage a son propre APID pour distinguer la télémesure de balise de celle de l’application.", c["database"])
    for s in present:
        sc = sub_cfg[s]
        put("apids", {"apid": sc["apid"], "name": f"{sc['label']['en']} application process", "role": "subsystem", "subsystem": s},
            f"One application process per subsystem ({sc['label']['en']}) so its packets can be routed and filtered.",
            f"Un processus applicatif par sous-système ({sc['label']['fr']}) pour router et filtrer ses paquets.", c["subsystems"])
    for sv in c["pus_services"]["list"]:
        if sv.get("default"):
            put("services", {"service": sv["service"], "name": sv["name"], "used": True},
                f"ST[{sv['service']:02d}] {sv['name']['en']}: used by an EOSAT-1-class CubeSat.",
                f"ST[{sv['service']:02d}] {sv['name']['fr']} : utilisé par un CubeSat de classe EOSAT-1.", c["pus_services"])

    # ── parameters
    p_names, p_used = _existing_numbers(existing, "parameters", "param_id")
    palloc = _Alloc(p_names, p_used)
    params: list[dict] = []
    by_monitor: dict[tuple[str, str], dict] = {}

    def add_param(sub: str, name: str, t: dict, *, element: str | None = None, extra: dict | None = None,
                  why: tuple[str, str]) -> dict | None:
        full = f"{sub}.{name}"
        if any(p["name"] == full for p in params):
            return None
        sc = sub_cfg[sub]
        pid = palloc.get(full, sc["param_block"], sc["param_block"] + 0xFF)
        if pid is None:
            return None
        cal = dict(t.get("calibration") or {"type": "none"})
        if cal.get("type") == "enum" and cal.get("ref"):
            cal["values"] = enums.get(cal["ref"], [])
        d = {"param_id": pid, "name": full, "subsystem": sub, "type": t.get("type", "uint8"), "unit": t.get("unit", ""),
             "calibration": cal, "range": t.get("range"), "source_element_id": element,
             "sampling_s": sc["hk_period_s"], "on_demand": bool(t.get("on_demand")), "tags": list(t.get("tags") or []) or None,
             "description": t.get("description") or {"en": full, "fr": full}, **(extra or {})}
        params.append(d)
        put("parameters", d, why[0], why[1], c["parameters"])
        return d

    for s in present:
        for t in c["parameters"]["subsystem"].get(s, []):
            if t.get("needs") and not f["flags"].get(t["needs"]):
                continue
            add_param(s, t["name"], t, why=(f"Standard {sub_cfg[s]['label']['en']} housekeeping point.",
                                            f"Point de servitude standard du sous-système {sub_cfg[s]['label']['fr']}."))
    for u in f["units"]:
        for t in c["parameters"]["unit_class"].get(u["cls"], []):
            n = u["qty"] if t.get("per_quantity") and u["qty"] > 1 else 1
            for i in range(n):
                us = u["slug"] + (str(i + 1) if n > 1 else "")
                nm = f"{u['name']} {i + 1}" if n > 1 else u["name"]
                tt = dict(t)
                if t.get("range_from") == "op_range":
                    tt["range"] = _op_range(u["el"], c)
                tt["description"] = _fill(t.get("description") or {}, name=nm)
                d = add_param(u["sub"], t["name"].replace("{unit}", us), tt, element=u["id"],
                              why=(f"{nm}: {u['cls'].replace('_', ' ')} telemetry.", f"{nm} : télémesure ({u['cls'].replace('_', ' ')})."))
                if d and t.get("monitor_param") and i == 0:
                    by_monitor[(u["id"], t["monitor_param"])] = d
    if "eps" in f["subs"]:
        for l in f["lines"]:
            ln = cm.slug(l.get("name") or f"line{l.get('line_no')}", 16)
            for t in c["parameters"]["power_line"]:
                tt = {**t, "description": _fill(t["description"], line=l.get("name"))}
                add_param("eps", t["name"].replace("{line}", ln).replace("{n}", str(l.get("line_no") or 0)), tt,
                          extra={"line_id": l["id"]},
                          why=(f"Power line {l.get('name')}: state and current for the switch matrix and the LCL.",
                               f"Ligne {l.get('name')} : état et courant pour la matrice de commutation et le limiteur."))
    for b in f["buses"]:
        for t in c["parameters"]["bus"]:
            tt = {**t, "description": _fill(t["description"], name=b.get("name"))}
            add_param("obdh", t["name"].replace("{segment}", cm.slug(f"{b.get('protocol')}_{b.get('segment')}", 12)), tt,
                      extra={"bus_id": b["id"]}, why=(f"Status of data bus {b.get('name')}.", f"État du bus de données {b.get('name')}."))
    for i, hn in enumerate(f["heater_names"]):
        for t in c["parameters"]["heater"]:
            tt = {**t, "description": _fill(t["description"], name=hn)}
            add_param("tcs", t["name"].replace("{unit}", cm.slug(hn, 16)), tt, extra={"heater_index": i},
                      why=(f"Heater {hn}: state for the thermostat and FDIR.", f"Réchauffeur {hn} : état pour le thermostat et la FDIR."))
    pname = {p["name"]: p for p in params}

    # ── housekeeping
    hk = c["housekeeping"]
    sid_names: dict[str, int] = {}
    sid_used: set[int] = {hk["beacon"]["sid"]}
    for r in existing:
        if r.get("kind") == "hk" and not r.get("deleted_at"):
            d = r.get("data") or {}
            if isinstance(d.get("sid"), int):
                sid_used.add(d["sid"])
                if str(r.get("origin") or "").startswith("rule:") and d.get("subsystem"):
                    sid_names.setdefault(d["subsystem"], d["sid"])
    salloc = _Alloc(sid_names, sid_used)
    hk_rows: list[dict] = []
    modes = f["modes"] or [{"id": k, "name": k, "kind": k} for k in ("leop", "commissioning", "nominal", "imaging", "downlink", "safe", "survival")]
    off = int(hk.get("store_sid_offset") or 100)

    def by_mode(table: dict, sub: str) -> dict:
        row = {**(table.get("default") or {}), **(table.get(sub) or {})}
        return {m["id"]: row.get(m.get("kind") or "custom", row.get("custom")) for m in modes}

    def nominal_of(per: dict) -> float | None:
        vals = [per.get(m["id"]) for m in modes if m.get("kind") in ("nominal", "downlink")] + list(per.values())
        return next((float(v) for v in vals if v), None)

    is_diag = lambda p: "diagnostic" in (p.get("tags") or [])  # noqa: E731
    diag_next = int(hk.get("diagnostic_sid_start") or 20)
    for s in present:
        ps = [p for p in params if p["subsystem"] == s and not p["on_demand"] and not is_diag(p)]
        sc = sub_cfg[s]
        if ps:
            sid = salloc.get(s, 1, 99)
            rt = by_mode(hk.get("rt_intervals") or {}, s)
            st = by_mode(hk.get("store_intervals") or {}, s)
            d = {"sid": sid, "name": sc["label"]["en"], "subsystem": s, "apid": db["application_apid"],
                 "period_s": nominal_of(rt) or sc["hk_period_s"], "parameter_ids": [p["param_id"] for p in ps],
                 "enabled_at_boot": s in hk["enabled_at_boot"], "beacon": False,
                 "enabled": {"realtime": True, "stored": True}, "diagnostic": False,
                 "store_sid": sid + off, "store_id": hk.get("hk_store_id", 1),
                 "rt_period_by_mode": rt, "store_period_by_mode": st}
            hk_rows.append(d)
            put("hk", d, f"{sc['label']['en']}: {len(ps)} points; real-time interval per mode (thermal once per minute), "
                         f"stored copy SID {sid + off} routed to the HK store with its own interval per mode.",
                f"{sc['label']['fr']} : {len(ps)} points ; intervalle temps réel par mode (thermique une fois par minute), "
                f"copie stockée SID {sid + off} vers la mémoire HK avec son propre intervalle par mode.", hk)
        dps = [p for p in params if p["subsystem"] == s and not p["on_demand"] and is_diag(p)]
        if dps:
            key = f"{s}_diag"
            sid = salloc.get(key, diag_next, 99)
            diag_next = (sid or diag_next) + 1
            if sid is None:
                continue
            d = {"sid": sid, "name": f"{sc['label']['en']} diagnostics", "subsystem": s, "apid": db["application_apid"],
                 "period_s": float(hk.get("diagnostic_rt_s") or 1), "parameter_ids": [p["param_id"] for p in dps],
                 "enabled_at_boot": False, "beacon": False, "diagnostic": True,
                 "enabled": {"realtime": False, "stored": False}, "store_sid": sid + off,
                 "store_id": hk.get("diagnostic_store_id", 3), "auto_disable_s": hk.get("diagnostic_auto_disable_s"),
                 "rt_period_by_mode": {m["id"]: (None if m.get("kind") in ("imaging", "survival", "disposal") else float(hk.get("diagnostic_rt_s") or 1)) for m in modes},
                 "store_period_by_mode": {m["id"]: (None if m.get("kind") in ("survival", "disposal") else float(hk.get("diagnostic_store_s") or 2)) for m in modes}}
            hk_rows.append(d)
            put("hk", d, f"{sc['label']['en']} diagnostics ({len(dps)} raw sensor and estimator points): off by default, "
                         "enabled by campaign, disabled automatically after about one orbit.",
                f"Diagnostic {sc['label']['fr']} ({len(dps)} points bruts des capteurs et de l’estimateur) : désactivé par défaut, "
                "activé par campagne, désactivé automatiquement après environ une orbite.", hk)
    bparams = [pname[n]["param_id"] for n in hk["beacon"]["params"] if n in pname]
    if bparams:
        bk = set(hk["beacon"].get("modes") or [])
        d = {"sid": hk["beacon"]["sid"], "name": "Beacon", "subsystem": "ttc", "apid": db["bootloader_apid"],
             "period_s": hk["beacon"]["period_s"], "parameter_ids": bparams, "enabled_at_boot": True, "beacon": True,
             "enabled": {"realtime": True, "stored": False}, "diagnostic": False, "store_sid": None,
             "rt_period_by_mode": {m["id"]: (hk["beacon"]["period_s"] if (m.get("kind") in bk or not bk) else None) for m in modes}}
        hk_rows.append(d)
        put("hk", d, "Beacon packet: the few points the ground needs to see from the bootloader before any command.",
            "Paquet de balise : les quelques points que le sol doit voir depuis le chargeur d’amorçage avant toute commande.", hk)

    # ── data budget (W3.02): link framing, packet stores, real-time profiles, service reports,
    #    pass classes and payload products — editable defaults
    dbc = c["data_budget"]
    put("link_framing", dict(dbc["link_framing"]),
        "CCSDS TM SDLP frames in RS(255,223) interleave 2 with SDLS authentication and the CLCW; 30 s acquisition per pass, 90 % of passes usable.",
        "Trames CCSDS TM SDLP en RS(255,223) entrelacement 2 avec authentification SDLS et CLCW ; 30 s d’acquisition par passage, 90 % des passages utilisables.", dbc)
    for st_ in dbc["stores"]:
        put("stores", dict(st_), f"Packet store {st_['name']} ({st_['size_mb']} MB, {'circular' if st_.get('circular') else 'linear'}) in the OBC flash.",
            f"Mémoire de paquets {st_['name']} ({st_['size_mb']} Mo, {'circulaire' if st_.get('circular') else 'linéaire'}) dans la flash de l’OBC.", dbc)
    for pr in dbc["rt_profiles"]:
        put("rt_profiles", dict(pr), f"Real-time profile {pr['name']}: {pr['description']['en']}.",
            f"Profil temps réel {pr['name']} : {pr['description']['fr']}.", dbc)
    put("service_allowances", dict(dbc["service_allowances"]),
        "Service reports sharing the real-time channel and the stores: S1 verification, S5 events, S9 time, S15 store status.",
        "Rapports de service partageant le canal temps réel et les mémoires : vérification S1, événements S5, temps S9, état des mémoires S15.", dbc)
    for pc in dbc["pass_classes"]:
        put("pass_classes", dict(pc), f"Pass class {pc['name']}: real-time profile {pc['rt_profile']}, then {' then '.join(pc['order'])}.",
            f"Classe de passage {pc['name']} : profil temps réel {pc['rt_profile']}, puis {' puis '.join(pc['order'])}.", dbc)
    put("payload_products", dict(dbc["payload_products"]),
        "Payload products downlinked per day and their lossless compression: set by the payload lead.",
        "Produits de la charge utile transmis par jour et leur compression sans perte : fixés par le responsable de la charge utile.", dbc)

    # ── TC functions
    f_names, f_used = _existing_numbers(existing, "commands", "func_id")
    falloc = _Alloc(f_names, f_used)
    switchable = [l for l in f["lines"] if l.get("switchable")]
    commands: list[dict] = []
    for fn in c["functions"]["list"]:
        if fn["subsystem"] not in f["subs"] and fn["subsystem"] != "sys":
            continue
        if any(not f["flags"].get(n) for n in fn.get("needs") or []):
            continue
        if fn.get("role") in ("power_on", "power_off", "load_shed") and not f["lines"]:
            continue
        if fn["subsystem"] == "ttc" and "ttc" not in f["subs"]:
            continue
        sc = sub_cfg[fn["subsystem"]]
        fid = falloc.get(fn["name"], sc["func_start"], 255)
        args = []
        for a in fn.get("args") or []:
            aa = {"name": a["name"], "type": a.get("type", "uint8"), "unit": a.get("unit", "")}
            if a.get("range"):
                aa["range"] = list(a["range"])
            if a.get("enum"):
                aa["enum"] = list(a["enum"])
            if a.get("enum_from"):
                aa["enum"] = list(enums.get(a["enum_from"], []))
            rf = a.get("range_from")
            if rf == "lines":
                aa["values"] = [int(l.get("line_no") or 0) for l in f["lines"]]
            elif rf == "switchable_lines":
                aa["values"] = [int(l.get("line_no") or 0) for l in switchable]
            elif rf == "wheels":
                aa["range"] = [0, max(0, f["n_wheels"] - 1)]
            elif rf == "heaters":
                aa["range"] = [0, max(0, len(f["heater_names"]) - 1)]
            args.append(aa)
        d = {"name": fn["name"], "service": 8, "subtype": 1, "func_id": fid, "subsystem": fn["subsystem"],
             "role": fn.get("role"), "args": args, "position": sc["position"], "criticality": fn.get("criticality", "normal"),
             "arm_execute": bool(fn.get("arm_execute")), "description": fn["description"]}
        commands.append(d)
        put("commands", d, f"{fn['description']['en']}: S8,1 function {fid} of the {sc['label']['en']} block.",
            f"{fn['description']['fr']} : fonction S8,1 n° {fid} du bloc {sc['label']['fr']}.", c["functions"])
    cmd_by_role = {d["role"]: d for d in commands if d.get("role")}

    # ── load shed and named bus-protection levels
    shed = _load_shed(f)
    if shed:
        put("load_shed", shed, "Shed order from the unit classes (payload first, propulsion last); levels from the battery bus range.",
            "Ordre de délestage selon les classes d’unités (charge utile d’abord, propulsion en dernier) ; seuils selon la plage du bus batterie.",
            c["fdir"])
    levels = {k: v.get("value") for k, v in (shed or {}).get("bus_protection", {}).items()}

    # ── monitors
    e_names, e_used = _existing_numbers(existing, "events", "event_id")
    ealloc = _Alloc(e_names, e_used)
    monitors: list[dict] = []
    props = [p for p in facts.get("fdir_proposals") or [] if p.get("status") != "rejected"]
    for p in props:
        if p.get("kind") != "monitor":
            continue
        pay = p.get("payload") or {}
        spec_param = str(pay.get("parameter") or "").split(".", 1)[-1]
        tm = by_monitor.get((p.get("element_id"), spec_param)) or pname.get(
            (c["fdir"].get("monitor_param_alias") or {}).get(spec_param, ""))
        if tm is None:
            continue
        line = _line_of_unit(f, p.get("element_id"))
        validity = None
        if line and line.get("switchable"):
            vp = next((q for q in params if q.get("line_id") == line["id"] and q["name"].split(".")[1].startswith("pl_")), None)
            if vp:
                validity = {"parameter": vp["name"], "param_id": vp["param_id"], "mask": 1, "value": 1}
        sev = "ALARM" if int(pay.get("severity") or 0) >= int(c["fdir"]["severity_needing_recovery"]) else "WARNING"
        check = pay.get("check") or "limit"
        lo, hi, lim_src = pay.get("low"), pay.get("high"), pay.get("limit_source")
        if tm["name"] == "eps.bus_voltage" and levels.get("eps_safe_v") is not None:
            # the bus is protected at the named levels of the load-shed table, not at a class default
            lo, hi, lim_src = levels["eps_safe_v"], levels.get("ov_v"), "named bus-protection levels (eps_safe_v / ov_v)"
        d = {"pmon_id": pay.get("pmon_id"), "name": f"{tm['name']} ({pay.get('pmon_id')})", "parameter": tm["name"],
             "param_id": tm["param_id"], "subsystem": tm["subsystem"], "check": check, "low": lo,
             "high": hi, "expected": pay.get("expected"), "severity": sev,
             "repetition": int(pay.get("persistence") or c["fdir"]["default_repetition"]), "validity": validity,
             "element_id": p.get("element_id"), "fmeca_row_ids": pay.get("fmeca_row_ids") or [], "source_proposal_id": p.get("id"),
             "limit_source": lim_src}
        monitors.append(d)
        put("monitors", d, f"Promoted from rule 8 ({pay.get('pmon_id')}): detects the FMECA failure modes of the unit."
                           + (" Checked only while its line is on." if validity else ""),
            f"Repris de la règle 8 ({pay.get('pmon_id')}) : détecte les modes de défaillance AMDEC de l’unité."
            + (" Vérifiée seulement quand sa ligne est alimentée." if validity else ""), c["fdir"])
    for dm in c["fdir"]["default_monitors"]:
        tm = pname.get(dm["param"])
        if tm is None:
            continue
        low = levels.get(dm["low_ref"]) if dm.get("low_ref") else dm.get("low")
        high = levels.get(dm["high_ref"]) if dm.get("high_ref") else dm.get("high")
        if (dm.get("low_ref") and low is None) or (dm.get("high_ref") and high is None):
            continue
        pmon = f"MON-{tm['name'].replace('.', '-')}-{dm['severity'][0]}"
        d = {"pmon_id": pmon, "name": dm["name"]["en"], "parameter": tm["name"], "param_id": tm["param_id"],
             "subsystem": tm["subsystem"], "check": dm["check"], "low": low, "high": high, "expected": None,
             "severity": dm["severity"], "repetition": int(dm.get("repetition") or c["fdir"]["default_repetition"]),
             "validity": None, "element_id": tm.get("source_element_id"), "fmeca_row_ids": [], "source_proposal_id": None,
             "low_ref": dm.get("low_ref"), "high_ref": dm.get("high_ref"), "limit_source": "C2O default / named bus level"}
        monitors.append(d)
        put("monitors", d, f"{dm['name']['en']}: standard protection monitor" + (f" on the named level {dm['low_ref']}." if dm.get("low_ref") else "."),
            f"{dm['name']['fr']} : surveillance de protection standard" + (f" sur le seuil nommé {dm['low_ref']}." if dm.get("low_ref") else "."), c["fdir"])

    # ── events
    events: list[dict] = []
    for ev in c["events"]["list"]:
        if ev["subsystem"] not in f["subs"] or any(not f["flags"].get(n) for n in ev.get("needs") or []):
            continue
        if ev.get("level_ref") and levels.get(ev["level_ref"]) is None:
            continue
        sc = sub_cfg[ev["subsystem"]]
        eid = ealloc.get(ev["name"], sc["event_block"] + 1, sc["event_block"] + 0xFF)
        d = {"event_id": eid, "name": ev["name"], "severity": ev["severity"], "subsystem": ev["subsystem"],
             "role": ev.get("role"), "description": ev["description"]}
        events.append(d)
        put("events", d, f"Standard {sc['label']['en']} event.", f"Événement standard du sous-système {sc['label']['fr']}.", c["events"])
    sev_map = c["events"]["monitor_severity"]
    for m in monitors:
        sc = sub_cfg[m["subsystem"]]
        name = f"{m['pmon_id']}_OOL".upper().replace("-", "_")[:60]
        eid = ealloc.get(name, sc["event_block"] + 0x80, sc["event_block"] + 0xFF)
        if eid is None:
            continue
        d = {"event_id": eid, "name": name, "severity": sev_map.get(m["severity"], "MEDIUM"), "subsystem": m["subsystem"],
             "role": "monitor", "monitor": m["pmon_id"],
             "description": {"en": f"{m['parameter']} out of limits ({m['pmon_id']})", "fr": f"{m['parameter']} hors limites ({m['pmon_id']})"}}
        m["event_name"] = name
        events.append(d)
        put("events", d, f"Out-of-limit report of monitor {m['pmon_id']}.", f"Rapport de dépassement de la surveillance {m['pmon_id']}.", c["events"])
    ev_by_role = {e["role"]: e for e in events if e.get("role")}

    # ── event-actions
    ea_n = 0
    never_off = set(c["fdir"]["never_off_classes"])
    mon_by_pmon = {m["pmon_id"]: m for m in monitors}
    ar = c["fdir"]["action_role"]
    for p in props:
        if p.get("kind") != "action":
            continue
        pay = p.get("payload") or {}
        mon = mon_by_pmon.get(pay.get("event_from"))
        spec = ar.get(pay.get("function_id")) or {}
        role = spec.get("role")
        u = next((x for x in f["units"] if x["id"] == p.get("element_id")), None)
        if spec.get("role_by_class"):
            role = (spec["role_by_class"] or {}).get(u["cls"] if u else "", role or spec.get("fallback_role"))
        if mon is None or not role:
            continue
        data_args: list[int] = list(spec.get("data") or [])
        line = _line_of_unit(f, p.get("element_id"))
        note = ""
        if role == "power_off":
            keep_on = line is None or not line.get("switchable") or any(
                x["cls"] in never_off for x in f["units"] if x["id"] in (line.get("load_element_ids") or []))
            if keep_on:
                role, note = c["fdir"]["line_action_fallback_role"], " (its line must stay powered)"
            else:
                data_args = [int(line.get("line_no") or 0)]
        fn = cmd_by_role.get(role)
        limit = _side(mon)
        ea_n += 1
        d = {"ea_id": 1000 + ea_n, "name": f"{mon['pmon_id'].lower().replace('-', '_')}_{(role or 'none')}", "trigger":
             {"kind": "param", "parameter": mon["parameter"], "param_id": mon["param_id"], "limit": limit, "monitor": mon["pmon_id"]},
             "action": fn["name"] if fn else None, "action_func_id": fn["func_id"] if fn else None, "action_data": data_args,
             "on_clear": (cmd_by_role.get(spec["on_clear_role"]) or {}).get("name") if spec.get("on_clear_role") and role == "power_off" else None,
             "level": pay.get("level") or 1, "enabled": True, "element_id": p.get("element_id"),
             "source_proposal_id": p.get("id"), "placeholder": pay.get("function_id")}
        put("event_actions", d, f"Promoted from rule 8: {pay.get('function_id')} → {d['action'] or 'no TC function'}{note}"
                                f" on the {limit} limit of {mon['pmon_id']}.",
            f"Repris de la règle 8 : {pay.get('function_id')} → {d['action'] or 'aucune fonction TC'}"
            f"{' (sa ligne doit rester alimentée)' if note else ''} sur la limite {limit} de {mon['pmon_id']}.", c["fdir"])
    mon_by_key = {f"{m['parameter']}|{m['severity']}": m for m in monitors}
    for da in c["fdir"]["default_actions"]:
        fn = cmd_by_role.get(da["role"])
        if fn is None:
            continue
        if da.get("trigger_event_role"):
            ev = ev_by_role.get(da["trigger_event_role"])
            if ev is None:
                continue
            trig = {"kind": "event", "event": ev["name"], "event_id": ev["event_id"]}
        else:
            mon = mon_by_key.get(da["trigger_monitor"])
            if mon is None:
                continue
            trig = {"kind": "param", "parameter": mon["parameter"], "param_id": mon["param_id"], "limit": da.get("limit", "any"),
                    "monitor": mon["pmon_id"]}
        ea_n += 1
        d = {"ea_id": 1000 + ea_n, "name": da["name"], "trigger": trig, "action": fn["name"], "action_func_id": fn["func_id"],
             "action_data": list(da.get("data") or []), "on_clear": None, "level": da.get("level", 1), "enabled": True,
             "element_id": None, "source_proposal_id": None, "placeholder": None}
        put("event_actions", d, f"Standard on-board response: {fn['name']}.", f"Réponse de bord standard : {fn['name']}.", c["fdir"])

    # ── safe mode, FDIR levels
    sm = c["fdir"]["safe_mode"]
    off_lines = [l for l in f["lines"] if l.get("switchable") and any(
        u["cls"] in sm["shed_classes"] for u in f["units"] if u["id"] in (l.get("load_element_ids") or []))]
    entry = []
    if ev_by_role.get("bus_uv_critical"):
        entry.append({"kind": "event", "ref": ev_by_role["bus_uv_critical"]["name"]})
    for m in monitors:
        if m["parameter"] == "aocs.att_error":
            entry.append({"kind": "monitor", "ref": m["pmon_id"]})
    if cmd_by_role.get("safe_enter"):
        entry.append({"kind": "tc", "ref": cmd_by_role["safe_enter"]["name"]})
    safe_aocs = sm["aocs_mode"] if any(m["name"] == sm["aocs_mode"] for m in aocs_modes) else (aocs_modes[1]["name"] if len(aocs_modes) > 1 else None)
    put("safe_mode", {"entry": entry, "aocs_mode": safe_aocs, "rate_tier": roles.get(sm["rate_role"]),
                      "lines_off": [l["name"] for l in off_lines], "line_ids_off": [l["id"] for l in off_lines],
                      "heaters": sm["heaters"], "payload_off": True,
                      "exit": {"function": (cmd_by_role.get("safe_exit") or {}).get("name"),
                               "condition": {"en": "Ground command after the root cause is known and power and thermal are nominal",
                                             "fr": "Commande sol une fois la cause connue et la puissance et la thermique nominales"}}},
        "Safe mode: sun-safe attitude, low TM rate, payload and propulsion off, heaters on thermostat; left by ground command only.",
        "Mode survie : attitude de pointage solaire, débit TM bas, charge utile et propulsion éteintes, réchauffeurs sur thermostat ; sortie sur commande sol uniquement.",
        c["fdir"])
    for lv in c["fdir"]["levels"]:
        put("fdir_levels", dict(lv), f"FDIR level {lv['level']} ({lv['name']['en']}).", f"Niveau FDIR {lv['level']} ({lv['name']['fr']}).", c["fdir"])

    # ── AOCS
    for m in aocs_modes:
        put("aocs_modes", m, f"AOCS mode {m['name']}: {m['description']['en']}.", f"Mode SCAO {m['name']} : {m['description']['fr']}.", c["aocs"])
    for t in aocs_trans:
        put("aocs_transitions", t, f"{t['from']} → {t['to']} ({t['trigger']}).", f"{t['from']} → {t['to']} ({t['trigger']}).", c["aocs"])
    if aocs_modes:
        put("aocs_control", _aocs_control(f), "Control-law parameters: B-dot gain from the rod dipole, desaturation law, wheel bias.",
            "Paramètres des lois de commande : gain B-dot selon le dipôle des barreaux, loi de désaturation, vitesse de biais des roues.",
            c["aocs"])

    # ── TT&C
    for t in tiers:
        put("rate_tiers", t, f"Rate tier {t['name']}: {t['bps']} bit/s {t['modulation']} {t['coding']}.",
            f"Palier {t['name']} : {t['bps']} bit/s {t['modulation']} {t['coding']}.", c["ttc"])
    if tiers:
        bt = c["ttc"]["beacon"]
        rx_line = next((l for l in f["lines"] if not l.get("switchable") and any(
            u["cls"] in ("receiver", "transmitter") for u in f["units"] if u["id"] in (l.get("load_element_ids") or []))), None)
        put("ttc", {"default_tier": roles.get("default"), "beacon_tier": roles.get("beacon"), "safe_tier": roles.get("safe"),
                    "tc_uplink_rate_bps": c["ttc"]["tc_uplink_rate_bps"],
                    "cmd_loss_switch_timeout_s": c["ttc"]["cmd_loss_switch_timeout_s"],
                    "cmd_loss_rssi_threshold_dbm": c["ttc"]["cmd_loss_rssi_threshold_dbm"],
                    "cmd_loss_action": (cmd_by_role.get("switch_ttc") or cmd_by_role.get("reboot") or {}).get("name"),
                    "beacon": {"enabled": bt["enabled"], "bps": bt["bps"], "rf_power_w": bt["rf_power_w"],
                               "period_s": bt["period_s"], "hk_sid": hk["beacon"]["sid"] if bparams else None,
                               "eps_line": (rx_line or {}).get("name")}},
            "Beacon, uplink rate and the 24 h command-loss timer of the EOSAT-1 reference design.",
            "Balise, débit montant et minuterie de perte de commande de 24 h de la conception de référence EOSAT-1.", c["ttc"])

    # ── power-line states per mode
    members = facts.get("members") or []
    never = set(c["fdir"]["never_off_classes"])
    for m in f["modes"]:
        states: dict[str, str] = {}
        for l in f["lines"]:
            loads = l.get("load_element_ids") or []
            on = not l.get("switchable") or any(
                u["cls"] in never for u in f["units"] if u["id"] in loads)
            for mem in members:
                if mem.get("mode_id") == m["id"] and mem.get("element_id") in loads and mem.get("status") != "rejected":
                    st = mem.get("power_state")
                    if (st and st != "off") or (st is None and mem.get("is_active")):
                        on = True
            states[l["id"]] = "on" if on else "off"
        put("line_states", {"mode_id": m["id"], "mode": m.get("name"), "mode_kind": m.get("kind"), "states": states,
                            "line_names": {l["id"]: l.get("name") for l in f["lines"]}},
            f"Mode {m.get('name')}: a line is on when a load on it is on in the mode matrix, or it is always-on.",
            f"Mode {m.get('name')} : une ligne est alimentée quand une de ses charges l’est dans la matrice des modes, ou si elle est permanente.",
            c["fdir"])

    # ── operations
    used_services = sorted(sv["service"] for sv in c["pus_services"]["list"] if sv.get("default"))
    ops = c["ops"]
    for pos in ops["positions"]:
        if pos["subsystems"] != "all" and not (set(pos["subsystems"]) & f["subs"]):
            continue
        subs = sorted(f["subs"]) if pos["subsystems"] == "all" else [s for s in pos["subsystems"] if s in f["subs"]]
        svc = sorted(set(ops["base_services"]) | set(pos.get("extra_services") or [])) if pos["subsystems"] != "all" else used_services
        fids = sorted(d["func_id"] for d in commands if pos["subsystems"] == "all" or d["subsystem"] in subs)
        put("positions", {"id": pos["id"], "label": pos["label"], "subsystems": subs, "allowed_services": [s for s in svc if s in used_services],
                          "allowed_func_ids": fids, "design_seat": pos.get("design_seat"), "all_commands": pos["subsystems"] == "all"},
            f"Console position {pos['label']['en']} for {', '.join(subs)}.", f"Poste {pos['label']['fr']} pour {', '.join(subs)}.", ops)
    for g in ops["gonogo"]:
        if any(not f["flags"].get(n) for n in g.get("needs") or []):
            continue
        put("gonogo", {k: v for k, v in g.items() if k != "needs"}, "EOSAT-1 GO/NO-GO situation.", "Situation GO/NO-GO d’EOSAT-1.", ops)
    for r in ops["flight_rules"]:
        if any(not f["flags"].get(n) for n in r.get("needs") or []):
            continue
        put("flight_rules", {k: v for k, v in r.items() if k != "needs"}, "Flight rule of the reference design.",
            "Règle de vol de la conception de référence.", ops)

    # ── MCS limits from the monitors
    by_param: dict[str, list[dict]] = {}
    for m in monitors:
        if m["check"] == "limit" and m.get("low") is not None and m.get("high") is not None:
            by_param.setdefault(m["parameter"], []).append(m)
    for pn, ms in by_param.items():
        warn = next((m for m in ms if m["severity"] == "WARNING"), None)
        alarm = next((m for m in ms if m["severity"] == "ALARM"), None)
        red = alarm or warn
        yel = warn or alarm
        assert red and yel
        span = float(red["high"]) - float(red["low"])
        y_lo, y_hi = float(yel["low"]), float(yel["high"])
        if warn is None:   # only an alarm: the yellow band sits 5 % of the span inside it (C2O default)
            y_lo, y_hi = y_lo + 0.05 * span, y_hi - 0.05 * span
        r_lo, r_hi = float(red["low"]), float(red["high"])
        if alarm is None:  # only a warning: the red band 5 % outside it
            r_lo, r_hi = r_lo - 0.05 * span, r_hi + 0.05 * span
        tm = pname.get(pn) or {}
        put("limits", {"parameter": pn, "param_id": tm.get("param_id"), "subsystem": tm.get("subsystem"),
                       "yellow_low": round(y_lo, 4), "yellow_high": round(y_hi, 4), "red_low": round(r_lo, 4), "red_high": round(r_hi, 4),
                       "check_interval_s": tm.get("sampling_s"), "valid_when": red.get("validity")},
            "Ground limits from the on-board monitors: yellow = warning, red = alarm (the ground twin of S12).",
            "Limites sol tirées des surveillances de bord : jaune = alerte, rouge = alarme (le jumeau sol du S12).", c["fdir"])
    return out


def _side(mon: dict) -> str:
    """Which S12 limit arms an event-action: an over-temperature / overload rule acts on the
    high side only (EOSAT-1 2026-11-03 lesson: the cold side is the heater's job)."""
    if mon.get("check") != "limit":
        return "any"
    lo, hi = mon.get("low"), mon.get("high")
    name = str(mon.get("parameter") or "")
    if hi is not None and (name.endswith("_temp") or name.endswith(".temp") or "pa_temp" in name):
        return "high"
    if lo is None:
        return "high"
    if hi is None:
        return "low"
    return "any"


def _rate_tiers(f: dict) -> list[dict]:
    c = f["c"]
    if "ttc" not in f["subs"]:
        return []
    kb_rates = [float(_kbp(u["el"]).get("data_rate_bps")) for u in f["classes"].get("transmitter", [])
                if _num(_kbp(u["el"]).get("data_rate_bps"))]
    top = max(kb_rates) if kb_rates else None
    out = []
    for t in c["ttc"]["tiers"]:
        t = dict(t)
        if top is not None:
            if t["role"] == "downlink":
                if top <= 16000:
                    continue
                t["bps"] = int(top)
            elif t["role"] == "default":
                t["bps"] = int(min(t["bps"], top))
        out.append(t)
    return out


def _aocs_modes(f: dict) -> tuple[list[dict], list[dict]]:
    c = f["c"]
    if "aocs" not in f["subs"]:
        return [], []
    have = set(f["classes"]) | f.get("provided", set())
    modes = []
    for m in c["aocs"]["modes"]:
        if any(n not in have for n in m.get("needs") or []):
            continue
        d = {k: v for k, v in m.items() if k != "needs"}
        d["sensors"] = [s for s in m.get("sensors") or [] if s in have]
        d["actuators"] = [a for a in m.get("actuators") or [] if a in have]
        d.setdefault("gains", None)
        d.setdefault("deadband_deg", None)
        d.setdefault("min_dwell_s", 0)
        d.setdefault("pointing_sigma_deg", None)
        d.setdefault("power_w", None)
        modes.append(d)
    names = {m["name"] for m in modes}
    trans = [dict(t) for t in c["aocs"]["transitions"] if t["from"] in names and t["to"] in names]
    init = initial_aocs_mode(modes, c)
    if init and "OFF" in names and not any(t["from"] == "OFF" and t["to"] == init for t in trans):
        trans.insert(0, {"from": "OFF", "to": init, "trigger": "autonomous",
                         "guard": {"en": "Boot: OBC application running", "fr": "Démarrage : logiciel applicatif de l’OBC actif"}})
    return modes, trans


def initial_aocs_mode(modes: list[dict], c: dict) -> str | None:
    """The mode the AOCS enters after boot: the configured one (DETUMBLE) when the design can fly
    it, else the lowest-code mode other than OFF."""
    names = {m["name"] for m in modes}
    if c["aocs"]["initial_mode"] in names:
        return c["aocs"]["initial_mode"]
    rest = sorted((m for m in modes if m["name"] != "OFF"), key=lambda m: m.get("code") or 0)
    return rest[0]["name"] if rest else None


def _aocs_control(f: dict) -> dict:
    ctl = f["c"]["aocs"]["control"]
    mtq = f["classes"].get("magnetorquer", [])
    dip = next((_num(_kbp(u["el"]).get("dipole_moment_am2")) for u in mtq if _num(_kbp(u["el"]).get("dipole_moment_am2"))), None)
    rate = math.radians(float(ctl["bdot"]["rate_ref_dps"]))
    bdot = round(dip / (float(ctl["bdot"]["b_ref_t"]) * rate), -3) if dip else None
    rw = f["classes"].get("wheel", [])
    spd = next((_num(_kbp(u["el"]).get("max_speed_rpm")) for u in rw if _num(_kbp(u["el"]).get("max_speed_rpm"))), None)
    torque = next((_num(_kbp(u["el"]).get("max_torque_nm")) for u in rw if _num(_kbp(u["el"]).get("max_torque_nm"))), None)
    h = next((_num(_kbp(u["el"]).get("momentum_nms")) for u in rw if _num(_kbp(u["el"]).get("momentum_nms"))), None)
    return {"bdot_gain_am2_per_tps": bdot, "mtq_max_dipole_am2": dip, "mtq_count": sum(u["qty"] for u in mtq),
            "detumble_exit_rate_dps": ctl["bdot"]["exit_rate_dps"],
            "desaturation": dict(ctl["desaturation"]),
            "wheel_count": f["n_wheels"], "wheel_max_speed_rpm": spd, "wheel_max_torque_nm": torque, "wheel_momentum_nms": h,
            "wheel_bias_rpm": round(spd * float(ctl["wheel_bias_fraction"]), -1) if spd else None,
            "attitude_error_deadband_deg": next((m.get("deadband_deg") for m in f["c"]["aocs"]["modes"] if m.get("deadband_deg")), None),
            "inertia_kgm2": None}


def _load_shed(f: dict) -> dict | None:
    c = f["c"]
    if not f["lines"]:
        return None
    fd = c["fdir"]
    bus = next((r for r in f.get("rails_all", []) if not r.get("regulated")), None)
    return _shed_from(f, fd, bus)


def _shed_from(f: dict, fd: dict, bus: dict | None) -> dict:
    prio = fd["shed_priority"]
    stage_of: dict[int, list[dict]] = {}
    for l in f["lines"]:
        if not l.get("switchable"):
            continue
        classes = [u["cls"] for u in f["units"] if u["id"] in (l.get("load_element_ids") or [])]
        if any(cl in fd["never_off_classes"] for cl in classes):
            continue
        ps = [prio[cl] for cl in classes if cl in prio]
        if not ps:
            continue
        stage_of.setdefault(min(ps), []).append(l)
    socs = fd["soc_stage_thresholds_pct"]
    stages = []
    for i, p in enumerate(sorted(stage_of)):
        n = min(i, len(socs) - 1)
        stages.append({"stage": i + 1, "lines": [l["name"] for l in stage_of[p]], "line_ids": [l["id"] for l in stage_of[p]],
                       "soc_pct": socs[n], "bus_level": "uv_v" if i == 0 else None})
    levels: dict[str, dict] = {}
    vmin, vmax = (_num((bus or {}).get("v_min")), _num((bus or {}).get("v_max")))
    for k, spec in fd["bus_protection"].items():
        val = None
        if vmin is not None and vmax is not None and vmax > vmin:
            if "soc_fraction" in spec:
                val = round(vmin + float(spec["soc_fraction"]) * (vmax - vmin), 1)
            elif "above_max_v" in spec:
                val = round(vmax + float(spec["above_max_v"]), 1)
        levels[k] = {"value": val, "label": spec["label"]}
    return {"bus_protection": levels, "bus_rail_id": (bus or {}).get("id"), "bus_range_v": [vmin, vmax],
            "stages": stages, "order": [n for s in stages for n in s["lines"]],
            "restore_hysteresis_v": fd["restore_hysteresis_v"], "auto_restore": True}
