"""SpaceCDF — the CDR model and the EOSAT-1 simulator configuration (Nov 2026).

* :func:`import_eosat1` reads the simulator's EOSAT-1 configuration (read-only:
  ``sim/configs/eosat1``, or ``$SPACECDF_SIM_CONFIG_DIR``) into CDR rows with
  ``origin = "import:eosat1"``, so a study can hold a complete reference database for
  students to study (458 parameters, 11 HK structures, 220 commands, 155 events, the S12 /
  S19 / rule tables, load shed, AOCS modes and control, rate ladder, positions, GO/NO-GO,
  MCS limits).
* :func:`export_sim` writes CDR rows back in the simulator's shapes (``telemetry/
  parameters.yaml`` …) — the design-to-simulator export contract (sim_design_inventory.md
  §15.10). Importing EOSAT-1 then exporting round-trips the ids, names and lists.
* :data:`EXPORT_MAP` is the field mapping CDR kind/field → simulator file/key.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

from . import cdr_model as cm

PACK_TYPE = {"B": "uint8", "b": "int8", "H": "uint16", "h": "int16", "I": "uint32", "i": "int32", "f": "float32", "d": "float64"}
TYPE_PACK = {v: k for k, v in PACK_TYPE.items()}

#: CDR kind.field → simulator file : key (the export contract; "—" = simulator has no key yet)
EXPORT_MAP: list[dict[str, str]] = [
    {"kind": "settings", "field": "spacecraft_id", "file": "rfsim.yaml", "key": "ccsds.scid"},
    {"kind": "settings", "field": "application_apid / bootloader_apid", "file": "mission.yaml", "key": "spacecraft_apid / bootloader_apid"},
    {"kind": "settings", "field": "pus_version", "file": "mission.yaml", "key": "pus_version"},
    {"kind": "apids", "field": "apid (role subsystem) via hk.apid", "file": "mission.yaml", "key": "hk_apids{sid: apid} (application image; S1/S5 and service reports stay on spacecraft_apid)"},
    {"kind": "services", "field": "service, used, capacities", "file": "mcs/pus_services.yaml", "key": "s<N>.enabled, max_sids, max_definitions …"},
    {"kind": "parameters", "field": "param_id, name, subsystem, unit, description, on_demand", "file": "telemetry/parameters.yaml", "key": "parameters[].id, name, subsystem, units, description, on_demand"},
    {"kind": "parameters", "field": "type, calibration.scale", "file": "telemetry/hk_structures.yaml", "key": "structures[].parameters[].pack_format, scale"},
    {"kind": "hk", "field": "sid, name, period_s, parameter_ids", "file": "telemetry/hk_structures.yaml", "key": "structures[].sid, name, interval_s, parameters[].param_id"},
    {"kind": "hk", "field": "enabled_at_boot", "file": "simulation.yaml", "key": "housekeeping.default_enabled_sids"},
    {"kind": "hk", "field": "beacon", "file": "subsystems/ttc.yaml", "key": "beacon.hk_sid"},
    {"kind": "commands", "field": "name, service, subtype, func_id, args, position, criticality", "file": "commands/tc_catalog.yaml", "key": "commands[].name, service, subtype, func_id, fields[]{name,type,unit,range,enum}, position, criticality"},
    {"kind": "commands", "field": "arm_execute", "file": "commands/tc_catalog.yaml", "key": "commands[].arm_execute (absent = inferred from criticality: critical)"},
    {"kind": "events", "field": "event_id, name, severity, subsystem, description", "file": "events/event_catalog.yaml", "key": "events[].id, name, severity, subsystem, description"},
    {"kind": "monitors", "field": "param_id, check, low, high, severity, repetition, validity", "file": "monitoring/s12_definitions.yaml", "key": "s12_definitions[].param_id, check_type (0 limit / 1 delta), low_limit, high_limit, severity, repetition, validity{param_id,mask,value}"},
    {"kind": "event_actions", "field": "ea_id, trigger{kind,id,limit}, action_func_id, action_data", "file": "monitoring/s19_rules.yaml", "key": "s19_rules[].ea_id, trigger.kind/id/limit, action_func_id, action_data"},
    {"kind": "event_actions", "field": "trigger.kind threshold, level, on_clear, persist_s, min_phase", "file": "subsystems/fdir.yaml", "key": "rules[].parameter, condition, threshold, threshold_ref, level, action, on_clear, persist_s, min_phase"},
    {"kind": "load_shed", "field": "bus_protection.*", "file": "simulation.yaml", "key": "eps.bus_protection.uv_v, eps_safe_v, aocs_safe_v, ov_v"},
    {"kind": "load_shed", "field": "order, soc stages, restore_hysteresis_v, auto_restore", "file": "simulation.yaml", "key": "eps.load_shed.order, soc_stage_thresholds_pct, restore_hysteresis_v, auto_restore"},
    {"kind": "safe_mode", "field": "aocs_mode, rate_tier, lines_off, exit", "file": "fdir/procedures/safe_mode_entry.yaml + subsystems/ttc.yaml", "key": "steps[] (S8 func + data); ttc.yaml safe_tier"},
    {"kind": "fdir_levels", "field": "level, persistence, attempts", "file": "subsystems/fdir.yaml, fdir/fault_propagation.yaml", "key": "rules[].level; recovery escalation"},
    {"kind": "aocs_modes", "field": "code, name, description", "file": "aocs/aocs_mode_codes.yaml", "key": "modes.<code>.name, description"},
    {"kind": "aocs_modes", "field": "gains, min_dwell_s, power_w, pointing_sigma_deg", "file": "subsystems/aocs.yaml", "key": "control.modes.<NAME>.omega_n_rad_s, zeta, min_dwell_s, power_w, pointing_sigma_deg"},
    {"kind": "aocs_transitions", "field": "guards (detumble exit rate …)", "file": "subsystems/aocs.yaml", "key": "control.transitions.* (the transition logic itself is the simulator's)"},
    {"kind": "aocs_control", "field": "bdot_gain, desaturation.*, wheel_*, inertia, deadband", "file": "subsystems/aocs.yaml", "key": "magnetorquers.bdot_gain_am2_per_tps, magnetorquers.desaturation.*, reaction_wheels.*, mass_properties.inertia_kgm2, attitude_error_deadband_deg"},
    {"kind": "rate_tiers", "field": "name, bps, modulation, coding, coding_gain_db, gating", "file": "subsystems/ttc.yaml", "key": "tm_rate_tiers[].name, bps, modulation, coding, coding_gain_db, bootloader_only, requires_antenna, requires_downlink_mode, min_elevation_deg"},
    {"kind": "ttc", "field": "default/beacon/safe tier, uplink, command loss, beacon", "file": "subsystems/ttc.yaml", "key": "default_tier, beacon_tier, safe_tier, tc_uplink_rate_bps, cmd_loss_switch_timeout_s, cmd_loss_rssi_threshold_dbm, beacon.*"},
    {"kind": "line_states", "field": "states per mode", "file": "subsystems/eps.yaml (+ planner activities)", "key": "power_lines{name: default_on} for the boot row; per-mode states → planning/activity_types.yaml line steps"},
    {"kind": "positions", "field": "id, label, subsystems, allowed_services, allowed_func_ids", "file": "mcs/positions.yaml", "key": "positions.<id>.display_name, subsystems, allowed_services, allowed_func_ids"},
    {"kind": "gonogo", "field": "situation, who_calls, who_responds, decision, critical", "file": "mcs/gonogo_matrix.yaml", "key": "gonogo_matrix[].situation, who_calls, who_responds, fd_decision, critical"},
    {"kind": "flight_rules", "field": "rule_id, text", "file": "ops/flight_rules.yaml", "key": "flight_rules[].id, text, text_fr, ref (exported as a document; read by nothing yet)"},
    {"kind": "limits", "field": "yellow/red low/high, check_interval_s, valid_when", "file": "mcs/limits.yaml", "key": "limits[].param_id, yellow_low, yellow_high, red_low, red_high, check_interval_s, valid_when"},
]


def sim_dir() -> Path | None:
    env = os.environ.get("SPACECDF_SIM_CONFIG_DIR")
    if env:
        p = Path(env)
        return p if p.is_dir() else None
    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "sim" / "configs" / "eosat1"
        if (cand / "telemetry" / "parameters.yaml").is_file():
            return cand
    return None


def _y(root: Path, rel: str) -> Any:
    p = root / rel
    if not p.is_file():
        return None
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def _bi(text: Any) -> dict[str, str]:
    s = str(text or "").strip()
    return {"en": s, "fr": s}


def _code_tables(root: Path) -> dict[str, dict[str, Any]]:
    """Per-mode tables the simulator keeps in aocs_basic.py (read-only, best effort)."""
    src = root.parents[1] / "packages" / "smo-simulator" / "src" / "smo_simulator" / "models" / "aocs_basic.py"
    out: dict[str, dict[str, Any]] = {}
    if not src.is_file():
        return out
    text = src.read_text(encoding="utf-8")
    for table in ("_MODE_CTRL", "_MIN_DWELL", "_MODE_POWER_W"):
        m = re.search(table + r"\s*=\s*\{(.*?)\n\}", text, re.S)
        if not m:
            continue
        body = m.group(1)
        vals: dict[str, Any] = {}
        for mm in re.finditer(r"MODE_([A-Z_]+)\s*:\s*(\([^)]*\)|[-0-9.eE]+)", body):
            raw = mm.group(2)
            if raw.startswith("("):
                vals[mm.group(1)] = [float(x) for x in raw.strip("()").split(",") if x.strip()]
            else:
                vals[mm.group(1)] = float(raw)
        out[table] = vals
    return out


def import_eosat1(study_id: str, root: Path | None = None) -> list[dict]:  # noqa: C901
    """CDR rows (accepted, origin import:eosat1) from the EOSAT-1 configuration."""
    root = root or sim_dir()
    if root is None:
        raise FileNotFoundError("EOSAT-1 simulator configuration not found (set SPACECDF_SIM_CONFIG_DIR)")
    c = cm.cfg()
    rows: list[dict] = []
    std = cm.ref({"source": "eosat1"}, c)["standard_ref"]

    def add(kind: str, data: dict) -> None:
        key = cm.key_of(kind, data)
        n = sum(1 for r in rows if r["kind"] == kind)
        rows.append({"id": f"ref-{study_id[:12]}-{kind[:10]}-{n}", "study_id": study_id, "kind": kind, "key": key,
                     "data": data, "owner_seat": cm.owner_seat(kind, data, c), "status": "accepted",
                     "origin": cm.IMPORT_ORIGIN, "standard_ref": std, "edited": False, "review": None, "proposed": None,
                     "rationale": {"en": "EOSAT-1 reference database (read-only import).",
                                   "fr": "Base de référence EOSAT-1 (import en lecture seule)."}})

    mission = _y(root, "mission.yaml") or {}
    rfsim = _y(root, "rfsim.yaml") or {}
    sim = _y(root, "simulation.yaml") or {}
    ttc = _y(root, "subsystems/ttc.yaml") or {}
    add("settings", {"spacecraft_id": ((rfsim.get("ccsds") or {}).get("scid")), "pus_version": mission.get("pus_version"),
                     "time_code": f"CUC coarse + fine, epoch {mission.get('time_epoch', 'J2000')}",
                     "application_apid": mission.get("spacecraft_apid"), "bootloader_apid": mission.get("bootloader_apid")})
    add("apids", {"apid": mission.get("spacecraft_apid"), "name": "OBC application", "role": "application", "subsystem": "obdh"})
    add("apids", {"apid": mission.get("bootloader_apid"), "name": "OBC bootloader", "role": "bootloader", "subsystem": "obdh"})
    for k, v in ((_y(root, "mcs/pus_services.yaml") or {}).get("services") or {}).items():
        try:
            n = int(str(k).lstrip("s"))
        except ValueError:
            continue
        add("services", {"service": n, "name": _bi(v.get("label")), "used": bool(v.get("enabled", True)),
                         "capacities": {kk: vv for kk, vv in v.items() if kk not in ("label", "enabled", "description")},
                         "description": _bi(v.get("description"))})

    hk = (_y(root, "telemetry/hk_structures.yaml") or {}).get("structures") or []
    pack: dict[int, dict] = {}
    period: dict[int, float] = {}
    for s in hk:
        for p in s.get("parameters") or []:
            pack.setdefault(p["param_id"], p)
            period.setdefault(p["param_id"], float(s.get("interval_s") or 0))
    params = (_y(root, "telemetry/parameters.yaml") or {}).get("parameters") or []
    pname = {}
    for p in params:
        pk = pack.get(p["id"]) or {}
        t = PACK_TYPE.get(pk.get("pack_format")) or ("float32" if p.get("type") == "float" else None)
        sc = pk.get("scale")
        d = {"param_id": p["id"], "name": p["name"], "subsystem": p.get("subsystem"), "type": t, "unit": p.get("units", ""),
             "calibration": {"type": "linear", "scale": sc} if sc not in (None, 1) else {"type": "none"},
             "range": None, "source_element_id": None, "sampling_s": period.get(p["id"]), "on_demand": bool(p.get("on_demand")),
             "description": _bi(p.get("description"))}
        for extra in ("visibility", "stub"):
            if p.get(extra) is not None:
                d[extra] = p[extra]
        if p.get("type") is not None:
            d["sim_type"] = p["type"]
        pname[p["id"]] = p["name"]
        add("parameters", d)
    enabled = set((sim.get("housekeeping") or {}).get("default_enabled_sids") or [])
    beacon_sid = (ttc.get("beacon") or {}).get("hk_sid")
    for s in hk:
        add("hk", {"sid": s["sid"], "name": s.get("name"), "subsystem": None,
                   "apid": mission.get("bootloader_apid") if s["sid"] == beacon_sid else mission.get("spacecraft_apid"),
                   "period_s": s.get("interval_s"), "parameter_ids": [p["param_id"] for p in s.get("parameters") or []],
                   "pack": [{"param_id": p["param_id"], "pack_format": p.get("pack_format"), "scale": p.get("scale")}
                            for p in s.get("parameters") or []],
                   "enabled_at_boot": s["sid"] in enabled, "beacon": s["sid"] == beacon_sid})

    cat = _y(root, "commands/tc_catalog.yaml") or {}
    fname: dict[int, str] = {}
    for t in cat.get("commands") or []:
        args = []
        for fl in t.get("fields") or []:
            a = {"name": fl.get("name"), "type": fl.get("type"), "unit": fl.get("unit", "")}
            r = fl.get("range")
            if isinstance(r, dict):
                a["range"] = [r.get("min"), r.get("max")]
            if fl.get("enum"):
                a["enum"] = [e.get("label") for e in fl["enum"]]
            args.append(a)
        d = {"name": t["name"], "service": t.get("service"), "subtype": t.get("subtype"), "func_id": t.get("func_id"),
             "subsystem": None, "role": None, "args": args, "position": t.get("position"),
             "criticality": t.get("criticality") or "normal",
             "arm_execute": bool(t["arm_execute"]) if t.get("arm_execute") is not None else t.get("criticality") == "critical",
             "description": _bi(t.get("description")), "fields": t.get("fields") or []}
        for extra in ("aliases", "readback", "arg_schema_version", "deprecated_aliases"):
            if t.get(extra) is not None:
                d[extra] = t[extra]
        if t.get("service") == 8 and t.get("func_id") is not None:
            fname[t["func_id"]] = t["name"]
        add("commands", d)
    for e in (_y(root, "events/event_catalog.yaml") or {}).get("events") or []:
        add("events", {"event_id": e["id"], "name": e["name"], "severity": e.get("severity"), "subsystem": e.get("subsystem"),
                       "role": None, "description": _bi(e.get("description"))})

    for i, m in enumerate((_y(root, "monitoring/s12_definitions.yaml") or {}).get("s12_definitions") or []):
        v = m.get("validity")
        add("monitors", {"pmon_id": f"S12-{i + 1:02d}", "name": m.get("name"), "parameter": pname.get(m["param_id"]),
                         "param_id": m["param_id"], "subsystem": (pname.get(m["param_id"]) or "sys").split(".")[0],
                         "check": "limit" if int(m.get("check_type") or 0) == 0 else "delta", "check_type": m.get("check_type"),
                         "low": m.get("low_limit"), "high": m.get("high_limit"), "expected": None, "severity": m.get("severity"),
                         "repetition": m.get("repetition", 1),
                         "validity": ({"parameter": pname.get(v["param_id"]), **v} if v else None),
                         "element_id": None, "fmeca_row_ids": [], "description": _bi(m.get("description"))})
    for r in (_y(root, "monitoring/s19_rules.yaml") or {}).get("s19_rules") or []:
        tr = dict(r.get("trigger") or {})
        if "kind" not in tr and r.get("event_type") is not None:
            tr = {"kind": "event", "id": r["event_type"]}
        if tr.get("kind") == "param":
            tr["parameter"] = pname.get(tr.get("id"))
            tr.setdefault("limit", "any")
        add("event_actions", {"ea_id": r.get("ea_id"), "name": r.get("name"), "trigger": tr,
                              "action": fname.get(r.get("action_func_id")), "action_func_id": r.get("action_func_id"),
                              "action_data": list(r.get("action_data") or []), "on_clear": None, "level": None,
                              "enabled": bool(r.get("enabled", True)), "source": "s19", "description": _bi(r.get("description"))})
    fdir = _y(root, "subsystems/fdir.yaml") or {}
    for i, r in enumerate(fdir.get("rules") or []):
        add("event_actions", {"ea_id": None, "name": f"rule_{i + 1:02d}_{r.get('parameter')}_{r.get('action')}",
                              "trigger": {"kind": "threshold", "parameter": r.get("parameter"), "condition": r.get("condition"),
                                          "threshold": r.get("threshold"), "threshold_ref": r.get("threshold_ref"),
                                          "persist_s": r.get("persist_s"), "min_phase": r.get("min_phase")},
                              "action": None, "engine_action": r.get("action"), "action_func_id": None, "action_data": [],
                              "on_clear": r.get("on_clear"), "level": r.get("level"), "enabled": True, "source": "rule_table",
                              "description": _bi(r.get("description"))})

    eps_sim = sim.get("eps") or {}
    bp = eps_sim.get("bus_protection") or {}
    labels = {**c["fdir"]["bus_protection"],
              "cascade_v": {"label": {"en": "Fault-cascade level", "fr": "Seuil de cascade de pannes"}}}
    ls = eps_sim.get("load_shed") or {}
    add("load_shed", {"bus_protection": {k: {"value": v, "label": (labels.get(k) or {}).get("label") or _bi(k)} for k, v in bp.items()},
                      "bus_rail_id": None, "bus_range_v": [None, None],
                      "stages": [{"stage": i + 1, "lines": [n], "line_ids": [], "soc_pct": None, "bus_level": "uv_v"}
                                 for i, n in enumerate(ls.get("order") or [])],
                      "order": list(ls.get("order") or []), "soc_stage_thresholds_pct": ls.get("soc_stage_thresholds_pct"),
                      "restore_hysteresis_v": ls.get("restore_hysteresis_v"), "auto_restore": ls.get("auto_restore"),
                      "overcurrent": eps_sim.get("overcurrent")})
    safe = _y(root, "fdir/procedures/safe_mode_entry.yaml") or {}
    steps = safe.get("steps") or []
    add("safe_mode", {"entry": [{"kind": "engine", "ref": a} for a in sorted({r.get("action") for r in fdir.get("rules") or []
                                                                               if str(r.get("action") or "").startswith("safe_mode")})],
                      "aocs_mode": "COARSE_SUN", "rate_tier": ttc.get("safe_tier"), "lines_off": [], "line_ids_off": [],
                      "heaters": "duty-limited", "payload_off": True,
                      "steps": [{"name": s.get("name"), "func_id": (s.get("params") or {}).get("func_id"),
                                 "function": fname.get((s.get("params") or {}).get("func_id")),
                                 "data": (s.get("params") or {}).get("data")} for s in steps],
                      "exit": {"function": None, "condition": _bi("Ground procedure (manual 08)")}})
    lv = sorted({r.get("level") for r in fdir.get("rules") or [] if r.get("level") is not None})
    for x in c["fdir"]["levels"]:
        if x["level"] in lv:
            add("fdir_levels", {**x, "rules": sum(1 for r in fdir.get("rules") or [] if r.get("level") == x["level"])})

    codes = (_y(root, "aocs/aocs_mode_codes.yaml") or {}).get("modes") or {}
    aocs = _y(root, "subsystems/aocs.yaml") or {}
    # aocs.yaml control.modes (2026-11) is the source; the aocs_basic.py tables are the fallback
    ctl_modes = ((aocs.get("control") or {}).get("modes") or {})
    tables = _code_tables(root)
    for code, m in sorted(codes.items()):
        n = m.get("name")
        cm_ = ctl_modes.get(n) or {}
        g = (tables.get("_MODE_CTRL") or {}).get(n)
        if cm_.get("omega_n_rad_s") is not None:
            g = [cm_.get("omega_n_rad_s"), cm_.get("zeta") if cm_.get("zeta") is not None else (g or [0, 0.7])[1]]
        dwell = cm_.get("min_dwell_s", (tables.get("_MIN_DWELL") or {}).get(n))
        pw = cm_.get("power_w", (tables.get("_MODE_POWER_W") or {}).get(n))
        add("aocs_modes", {"code": int(code), "name": n, "description": _bi(m.get("description")), "sensors": [], "actuators": [],
                           "gains": {"omega_n": g[0], "zeta": g[1]} if g else None, "deadband_deg": None,
                           "min_dwell_s": dwell, "power_w": pw, "pointing_sigma_deg": cm_.get("pointing_sigma_deg"),
                           "gains_source": ("aocs.yaml control.modes" if cm_ else "aocs_basic.py _MODE_CTRL") if g else None})
    mtq = aocs.get("magnetorquers") or {}
    rw = aocs.get("reaction_wheels") or {}
    add("aocs_control", {"bdot_gain_am2_per_tps": mtq.get("bdot_gain_am2_per_tps"), "mtq_max_dipole_am2": mtq.get("max_dipole_am2"),
                         "mtq_count": mtq.get("count"),
                         "detumble_exit_rate_dps": ((aocs.get("control") or {}).get("transitions") or {}).get("detumble_exit_rate_dps", 0.5),
                         "desaturation": dict(mtq.get("desaturation") or {}),
                         "wheel_count": rw.get("count"), "wheel_max_speed_rpm": rw.get("max_speed_rpm"),
                         "wheel_max_torque_nm": rw.get("max_torque_nm"), "wheel_momentum_nms": None,
                         "wheel_bias_rpm": rw.get("nominal_speed_rpm"), "wheel_geometry": rw.get("geometry"),
                         "attitude_error_deadband_deg": aocs.get("attitude_error_deadband_deg"),
                         "inertia_kgm2": (aocs.get("mass_properties") or {}).get("inertia_kgm2"),
                         "mass_kg": (aocs.get("mass_properties") or {}).get("mass_kg")})

    roles = {ttc.get("default_tier"): "default", ttc.get("beacon_tier"): "beacon"}
    for t in ttc.get("tm_rate_tiers") or []:
        add("rate_tiers", {"name": t["name"], "role": "downlink" if t.get("requires_downlink_mode") else roles.get(t["name"], "tier"),
                           "bps": t.get("bps"), "command_code": t.get("command_code"), "modulation": t.get("modulation"),
                           "coding": t.get("coding"), "coding_gain_db": t.get("coding_gain_db"),
                           "bootloader_only": bool(t.get("bootloader_only")), "requires_antenna": bool(t.get("requires_antenna")),
                           "requires_downlink_mode": bool(t.get("requires_downlink_mode")), "min_elevation_deg": t.get("min_elevation_deg")})
    add("ttc", {"default_tier": ttc.get("default_tier"), "beacon_tier": ttc.get("beacon_tier"), "safe_tier": ttc.get("safe_tier"),
                "tc_uplink_rate_bps": ttc.get("tc_uplink_rate_bps"), "cmd_loss_switch_timeout_s": ttc.get("cmd_loss_switch_timeout_s"),
                "cmd_loss_rssi_threshold_dbm": ttc.get("cmd_loss_rssi_threshold_dbm"), "cmd_loss_action": None,
                "beacon": {k: v for k, v in (ttc.get("beacon") or {}).items()}})

    eps = _y(root, "subsystems/eps.yaml") or {}
    pl = eps.get("power_lines") or {}
    if pl:
        add("line_states", {"mode_id": "boot", "mode": "Boot (separation)", "mode_kind": "leop",
                            "states": {k: ("on" if v else "off") for k, v in pl.items()}, "line_names": {k: k for k in pl}})

    for pid_, p in ((_y(root, "mcs/positions.yaml") or {}).get("positions") or {}).items():
        add("positions", {"id": pid_, "label": _bi(p.get("display_name") or p.get("label")), "subsystems": list(p.get("subsystems") or []),
                          "allowed_services": list(p.get("allowed_services") or []), "allowed_func_ids": list(p.get("allowed_func_ids") or []),
                          "design_seat": None, "all_commands": p.get("allowed_commands") == "all",
                          "visible_tabs": list(p.get("visible_tabs") or [])})
    for g in (_y(root, "mcs/gonogo_matrix.yaml") or {}).get("gonogo_matrix") or []:
        add("gonogo", {"situation": _bi(g.get("situation")), "who_calls": g.get("who_calls"), "who_responds": list(g.get("who_responds") or []),
                       "decision": _bi(g.get("fd_decision")), "critical": bool(g.get("critical"))})
    for lim in (_y(root, "mcs/limits.yaml") or {}).get("limits") or []:
        vw = lim.get("valid_when")
        add("limits", {"parameter": pname.get(lim["param_id"]), "param_id": lim["param_id"],
                       "subsystem": (pname.get(lim["param_id"]) or "sys").split(".")[0],
                       **{k: lim.get(k) for k in ("yellow_low", "yellow_high", "red_low", "red_high", "check_interval_s")},
                       "valid_when": ({"parameter": pname.get(vw["param_id"]), **vw} if vw else None)})
    return rows


# ───────────────────────────────────────────────────────────── export

def export_sim(rows: list[dict]) -> dict[str, Any]:
    """The CDR rows in the simulator's file shapes (the files that have one)."""
    D = lambda k: cm.live_data(rows, k)  # noqa: E731
    params = D("parameters")
    out: dict[str, Any] = {}
    ptype = {p.get("param_id"): p for p in params}

    def desc(d: Any) -> str:
        return d.get("en", "") if isinstance(d, dict) else str(d or "")
    out["telemetry/parameters.yaml"] = {"parameters": [
        {k: v for k, v in {"id": p["param_id"], "name": p["name"], "subsystem": p.get("subsystem"), "units": p.get("unit") or None,
                           "description": desc(p.get("description")), "on_demand": True if p.get("on_demand") else None,
                           "type": p.get("sim_type"), "visibility": p.get("visibility")}.items() if v is not None}
        for p in sorted(params, key=lambda p: p.get("param_id") or 0)]}

    def pack_of(pid: int) -> dict:
        p = ptype.get(pid) or {}
        cal = p.get("calibration") or {}
        return {"param_id": pid, "pack_format": TYPE_PACK.get(p.get("type") or "uint16", "H"),
                "scale": cal.get("scale", 1) if cal.get("type") == "linear" else 1}
    out["telemetry/hk_structures.yaml"] = {"structures": [
        {"sid": h["sid"], "name": h.get("name"), "interval_s": h.get("period_s"),
         "parameters": list(h.get("pack") or [pack_of(i) for i in h.get("parameter_ids") or []])}
        for h in D("hk")]}
    out["simulation.yaml#housekeeping"] = {"default_enabled_sids": sorted(h["sid"] for h in D("hk") if h.get("enabled_at_boot"))}

    def cmd(t: dict) -> dict:
        fields = t.get("fields") or [{k: v for k, v in {"name": a.get("name"), "type": a.get("type"), "unit": a.get("unit") or None,
                                                         "range": {"min": a["range"][0], "max": a["range"][1]} if a.get("range") else None,
                                                         "enum": [{"value": i, "label": lab} for i, lab in enumerate(a["enum"])] if a.get("enum") else None}.items()
                                      if v is not None} for a in t.get("args") or []]
        arm = t.get("arm_execute")
        inferred = t.get("criticality") == "critical"
        d = {"name": t["name"], "service": t.get("service"), "subtype": t.get("subtype"), "func_id": t.get("func_id"),
             "position": t.get("position"), "criticality": t.get("criticality") if t.get("criticality") != "normal" else None,
             # written only when it differs from the simulator's inference (criticality: critical arms)
             "arm_execute": bool(arm) if arm is not None and bool(arm) != inferred else None,
             "description": desc(t.get("description")), "fields": fields}
        return {k: v for k, v in d.items() if v is not None}
    out["commands/tc_catalog.yaml"] = {"commands": [cmd(t) for t in D("commands")]}
    out["events/event_catalog.yaml"] = {"events": [{"id": e["event_id"], "name": e["name"], "severity": e.get("severity"),
                                                    "subsystem": e.get("subsystem"), "description": desc(e.get("description"))}
                                                   for e in D("events")]}

    def mon(m: dict) -> dict:
        v = m.get("validity")
        d = {"param_id": m.get("param_id"), "name": m.get("name"), "check_type": 0 if m.get("check", "limit") == "limit" else 1,
             "low_limit": m.get("low"), "high_limit": m.get("high"), "severity": m.get("severity"),
             "description": desc(m.get("description")) or None,
             "repetition": m.get("repetition") if (m.get("repetition") or 1) != 1 else None,
             "validity": {"param_id": v.get("param_id"), "mask": v.get("mask"), "value": v.get("value")} if v else None}
        return {k: x for k, x in d.items() if x is not None}
    out["monitoring/s12_definitions.yaml"] = {"s12_definitions": [mon(m) for m in D("monitors")]}
    eas = D("event_actions")
    out["monitoring/s19_rules.yaml"] = {"s19_rules": [
        {k: v for k, v in {"name": a.get("name"), "ea_id": a.get("ea_id"),
                           "trigger": {k2: v2 for k2, v2 in {"kind": (a.get("trigger") or {}).get("kind"),
                                                             "id": (a.get("trigger") or {}).get("id", (a.get("trigger") or {}).get("param_id") or (a.get("trigger") or {}).get("event_id")),
                                                             "limit": (a.get("trigger") or {}).get("limit") if (a.get("trigger") or {}).get("kind") == "param" else None}.items() if v2 is not None},
                           "action_func_id": a.get("action_func_id"), "action_data": a.get("action_data") or None,
                           "description": desc(a.get("description")) or None, "enabled": a.get("enabled", True)}.items() if v is not None}
        for a in eas if (a.get("trigger") or {}).get("kind") in ("param", "event")]}
    out["subsystems/fdir.yaml#rules"] = {"rules": [
        {k: v for k, v in {"parameter": (a.get("trigger") or {}).get("parameter"), "condition": (a.get("trigger") or {}).get("condition"),
                           "threshold": (a.get("trigger") or {}).get("threshold"), "threshold_ref": (a.get("trigger") or {}).get("threshold_ref"),
                           "level": a.get("level"), "action": a.get("engine_action"), "on_clear": a.get("on_clear"),
                           "persist_s": (a.get("trigger") or {}).get("persist_s"), "min_phase": (a.get("trigger") or {}).get("min_phase")}.items()
         if v is not None}
        for a in eas if (a.get("trigger") or {}).get("kind") == "threshold"]}
    shed = cm.singleton(rows, "load_shed")
    if shed:
        out["simulation.yaml#eps"] = {"bus_protection": {k: (v or {}).get("value") for k, v in (shed.get("bus_protection") or {}).items()},
                                      "load_shed": {"order": shed.get("order"), "restore_hysteresis_v": shed.get("restore_hysteresis_v"),
                                                    "auto_restore": shed.get("auto_restore"),
                                                    "soc_stage_thresholds_pct": shed.get("soc_stage_thresholds_pct") or
                                                    [s.get("soc_pct") for s in shed.get("stages") or [] if s.get("soc_pct") is not None]}}
    out["aocs/aocs_mode_codes.yaml"] = {"modes": {m["code"]: {"name": m["name"], "description": desc(m.get("description"))}
                                                  for m in sorted(D("aocs_modes"), key=lambda m: m.get("code") or 0)}}
    ttc = cm.singleton(rows, "ttc")
    tiers = D("rate_tiers")
    if tiers or ttc:
        out["subsystems/ttc.yaml"] = {
            "tm_rate_tiers": [{k: t.get(k) for k in ("name", "bps", "command_code", "modulation", "coding", "coding_gain_db",
                                                    "bootloader_only", "requires_antenna", "requires_downlink_mode", "min_elevation_deg")
                               if t.get(k) is not None} for t in tiers],
            **{k: ttc.get(k) for k in ("default_tier", "beacon_tier", "safe_tier", "tc_uplink_rate_bps",
                                       "cmd_loss_switch_timeout_s", "cmd_loss_rssi_threshold_dbm") if ttc.get(k) is not None}}
    out["mcs/positions.yaml"] = {"positions": {p["id"]: {"display_name": desc(p.get("label")), "subsystems": p.get("subsystems"),
                                                         "allowed_services": p.get("allowed_services"), "allowed_func_ids": p.get("allowed_func_ids")}
                                               for p in D("positions")}}
    out["mcs/gonogo_matrix.yaml"] = {"gonogo_matrix": [{"situation": desc(g.get("situation")), "who_calls": g.get("who_calls"),
                                                        "who_responds": g.get("who_responds"), "fd_decision": desc(g.get("decision")),
                                                        "critical": g.get("critical")} for g in D("gonogo")]}
    out["mcs/limits.yaml"] = {"limits": [{k: v for k, v in {"param_id": lim.get("param_id"), "yellow_low": lim.get("yellow_low"),
                                                           "yellow_high": lim.get("yellow_high"), "red_low": lim.get("red_low"),
                                                           "red_high": lim.get("red_high"), "check_interval_s": lim.get("check_interval_s"),
                                                           "valid_when": ({"param_id": lim["valid_when"].get("param_id"), "mask": lim["valid_when"].get("mask"),
                                                                           "value": lim["valid_when"].get("value")} if lim.get("valid_when") else None)}.items()
                                          if v is not None} for lim in D("limits")]}
    return out
