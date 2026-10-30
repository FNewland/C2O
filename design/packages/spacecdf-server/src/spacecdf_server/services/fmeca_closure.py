"""FMECA closure — failure modes from the element tree (SCDF-177, design
SCDF-170 §2.5).

``run_fmeca_closure(ctx)`` builds one failure-mode table for the study:

* **catalogue by subsystem domain / element type** — every space subsystem
  receives the domain entries of ``services.fmeca._CUBESAT_CATALOGUE``
  (EPS / AOCS / TTC / OBC / Thermal / Structure) plus a generic entry for
  domains without one; every leaf component receives one generic
  "loss of function" mode, specialised by keyword (battery, solar array,
  wheel, star tracker, transponder, antenna, heater ...). Occurrence is
  derated by TRL (< 6 → +1), detection by the presence of a ``data``
  interface (telemetry → -1);
* **single points** — severity >= 4 without redundancy; subsystem-level
  catalogue entries only count when the subsystem has no components (the
  flags belong to the modelled hardware otherwise);
* **redundancy** — ``redundancy_type`` on the element (``cold`` / ``hot`` /
  ``warm`` / ``dual`` / ``n+1`` ...) or ``quantity > 1`` suppresses the
  single-point flag and lowers the severity by one;
* **functions** — each mode carries the ids of the functions allocated to
  its element (``ctx.allocations``), so the UI can show what is lost;
* **propagation** — effects are traced along the study's interfaces
  (``from_element_id -> to_element_id``, subsystem level) with
  ``services.fmeca.propagate_effects``;
* outputs: ``fmeca_max_rpn``, ``fmeca_single_point_failures``,
  ``fmeca_modes`` on the mission root and one ``FMECA_SINGLE_POINT`` (major)
  conflict per single-point failure on a *critical* element — an allocated
  function in the ``critical`` list (ids or names; default: functions flagged
  ``critical`` / ``function_type == 'critical'``) or a subsystem domain in
  ``CRITICAL_DOMAINS`` (power / obc / ttc).

Public API:
    run_fmeca_closure(ctx, *, critical=None) -> AnalysisOutput
    ANALYSIS, OUTPUT_PARAMETERS, CONFLICT_CODES, CRITICAL_DOMAINS
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from .analysis_context import AnalysisContext
from .analysis_results import ANALYSIS_INPUT_KEYS, Conflict, ParamWrite
from .fmeca import _CUBESAT_CATALOGUE, FailureMode, propagate_effects

logger = logging.getLogger(__name__)

ANALYSIS = "fmeca"
ANALYSIS_INPUT_KEYS.setdefault(ANALYSIS, ("elements",))

OUTPUT_PARAMETERS: tuple[str, ...] = ("fmeca_max_rpn", "fmeca_single_point_failures", "fmeca_modes", "fmeca_critical_modes")
CONFLICT_CODES: tuple[str, ...] = ("FMECA_SINGLE_POINT",)
CRITICAL_DOMAINS: frozenset[str] = frozenset({"power", "eps", "obc", "cdh", "ttc", "comms"})
SINGLE_POINT_SEVERITY = 4          # a failure mode is single-point when severity >= this and nothing backs it up
REDUNDANT_TYPES: frozenset[str] = frozenset({"cold", "hot", "warm", "dual", "n+1", "2oo3", "triple", "standby", "active", "redundant"})

#: catalogue component name -> subsystem domains it applies to
_DOMAIN_OF_CATALOGUE: dict[str, tuple[str, ...]] = {
    "EPS": ("power", "eps"), "AOCS": ("aocs", "adcs"), "TTC": ("ttc", "comms", "communications"),
    "OBC": ("obc", "cdh", "data_handling"), "Thermal": ("thermal",), "Structure": ("structure", "mechanical"),
}
#: generic component mode by keyword: (mode, cause, local effect, system effect, S, O, D, mitigation)
_COMPONENT_MODES: tuple[tuple[tuple[str, ...], tuple], ...] = (
    (("batter",), ("Battery capacity loss / cell short", "Cell ageing, over-discharge, manufacturing defect",
                   "Reduced or lost energy storage", "Eclipse power loss, mission loss", 5, 2, 3,
                   "Cell balancing, DoD limit, redundant string, temperature control")),
    (("solar", "array", "panel"), ("Solar array string open", "Cell crack, interconnect fatigue, deployment failure",
                                   "Reduced generation", "Negative energy balance, degraded operations", 4, 2, 3,
                                   "String redundancy, bypass diodes, deployment test")),
    (("wheel",), ("Reaction wheel bearing failure", "Lubricant loss, contamination",
                  "Loss of one control axis", "Degraded pointing or safe mode", 4, 2, 2,
                  "4th wheel, bearing heaters, speed monitoring")),
    (("star",), ("Star tracker loss", "Radiation damage, optics contamination",
                 "Loss of fine attitude knowledge", "Degraded pointing", 3, 2, 2, "Second star tracker, gyro propagation")),
    (("magnetorquer", "torquer", "mtq"), ("Magnetorquer coil open", "Wire fatigue, driver failure",
                                          "Loss of momentum dumping on one axis", "Wheel saturation over time", 3, 1, 2,
                                          "Three-axis MTQ redundancy, driver protection")),
    (("transponder", "transceiver", "radio", "tx", "rx"), ("Transponder failure", "Component degradation, SEE",
                                                           "Loss of uplink/downlink", "Loss of commanding, mission loss", 5, 1, 4,
                                                           "Cold-spare transponder, watchdog reset")),
    (("antenna",), ("Antenna deployment failure", "Release mechanism malfunction",
                    "Reduced RF gain", "Degraded link, possible loss of comm", 4, 2, 3, "Redundant release, backup antenna")),
    (("obc", "computer", "processor"), ("Processor latch-up / firmware corruption", "SEE, bit-flips in flash",
                                        "Processor halt", "Loss of control, safe mode", 4, 3, 2,
                                        "Latch-up protection, watchdog, dual-bank firmware")),
    (("heater",), ("Heater stuck on/off", "Relay failure, command error",
                   "Component out of temperature range", "Component damage or power drain", 3, 2, 2,
                   "Thermostat backup, SW limits")),
    (("thruster", "tank", "valve", "propul"), ("Propulsion leak / valve stuck", "Seal degradation, contamination",
                                               "Loss of propellant or thrust", "Loss of orbit maintenance / deorbit", 4, 2, 3,
                                               "Latch valve redundancy, pressure telemetry")),
    (("camera", "imager", "instrument", "payload", "sensor", "detector"), ("Instrument failure", "Detector degradation, electronics failure",
                                                                           "Loss of science data", "Mission objective not met", 4, 2, 2,
                                                                           "Derating, screening, graceful degradation modes")),
    (("pcdu", "eps", "distribution", "regulator", "converter"), ("Power converter / distribution failure", "Component failure, over-current",
                                                                 "Loss of a power bus", "Loss of the loads on that bus", 5, 2, 2,
                                                                 "Redundant converters, LCL protection")),
)
_GENERIC_MODE = ("Loss of function", "Component failure", "Function of the element unavailable", "Degraded mission", 3, 2, 3,
                 "Screening, derating, health telemetry")


@dataclass
class AnalysisOutput:
    parameters: list[ParamWrite] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    series: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def _is_redundant(e: dict) -> bool:
    rt = str(e.get("redundancy_type") or "").strip().lower()
    if rt in ("", "none", "single", "simplex", "no"):
        return int(e.get("quantity") or 1) > 1
    return True


def _catalogue_for_domain(domain: str) -> list[FailureMode]:
    for comp, domains in _DOMAIN_OF_CATALOGUE.items():
        if domain in domains:
            return [fm for fm in _CUBESAT_CATALOGUE if fm.component == comp]
    return []


def _component_mode(e: dict, kb: dict | None) -> tuple:
    text = f"{e.get('name', '')} {(kb or {}).get('category', '')} {e.get('subsystem_domain', '')}".lower()
    for words, mode in _COMPONENT_MODES:
        if any(w in text for w in words):
            return mode
    return _GENERIC_MODE


def _kb(kb_id: str | None) -> dict | None:
    if not kb_id:
        return None
    try:
        from .physics_closure import _kb_component
        return _kb_component(kb_id)
    except Exception:
        return None


def _critical_functions(ctx: AnalysisContext, critical: list[str] | None) -> set[str]:
    wanted = {str(c) for c in (critical or [])}
    out: set[str] = set()
    for f in ctx.functions:
        fid, name = str(f.get("id")), str(f.get("name") or "")
        if fid in wanted or name in wanted:
            out.add(fid)
        elif str(f.get("function_type") or "").lower() == "critical" or str(f.get("criticality") or "").lower() == "critical":
            out.add(fid)
        elif isinstance(f.get("properties"), dict) and f["properties"].get("critical"):
            out.add(fid)
    return out


def run_fmeca_closure(ctx: AnalysisContext, *, critical: list[str] | None = None) -> AnalysisOutput:
    out = AnalysisOutput()
    by_id = ctx.elements_by_id
    space = [e for e in ctx.elements if e.get("element_type") in ("subsystem", "component")
             and (e.get("segment") or "space") == "space" and e.get("in_scope", True) is not False]
    if not space:
        out.warnings.append("no space subsystem / component in the model — nothing to analyse")
    crit_funcs = _critical_functions(ctx, critical)
    alloc: dict[str, list[str]] = {}
    for a in ctx.allocations:
        alloc.setdefault(str(a.get("element_id")), []).append(str(a.get("function_id")))
    func_name = {str(f.get("id")): str(f.get("name") or f.get("id")) for f in ctx.functions}
    kids: dict[str, list[dict]] = {}
    for e in ctx.elements:
        if e.get("parent_id"):
            kids.setdefault(e["parent_id"], []).append(e)

    def subsystem_of(e: dict) -> dict | None:
        cur = e
        while cur is not None and cur.get("element_type") != "subsystem":
            cur = by_id.get(cur.get("parent_id") or "")
        return cur

    # subsystem dependency graph from interfaces (name keyed, for propagate_effects)
    graph: dict[str, list[str]] = {}
    for itf in ctx.interfaces:
        a, b = by_id.get(itf.get("from_element_id") or ""), by_id.get(itf.get("to_element_id") or "")
        sa, sb = (subsystem_of(a) if a else None), (subsystem_of(b) if b else None)
        if sa is None or sb is None or sa["id"] == sb["id"]:
            continue
        graph.setdefault(str(sa.get("name")), [])
        if str(sb.get("name")) not in graph[str(sa.get("name"))]:
            graph[str(sa.get("name"))].append(str(sb.get("name")))
        if str(itf.get("direction") or "") == "bidirectional":
            graph.setdefault(str(sb.get("name")), [])
            if str(sa.get("name")) not in graph[str(sb.get("name"))]:
                graph[str(sb.get("name"))].append(str(sa.get("name")))
    has_telemetry = {str(itf.get("from_element_id")) for itf in ctx.interfaces if str(itf.get("interface_type") or "") == "data"} | \
                    {str(itf.get("to_element_id")) for itf in ctx.interfaces if str(itf.get("interface_type") or "") == "data"}

    modes: list[dict] = []
    n = 0

    def add(e: dict, template: tuple, source: str, allow_single: bool = True) -> None:
        nonlocal n
        mode, cause, local, system, sev, occ, det, mit = template
        redundant = _is_redundant(e)
        trl = e.get("trl")
        if isinstance(trl, (int, float)) and trl < 6:
            occ = min(5, occ + 1)
        if e["id"] in has_telemetry or (subsystem_of(e) or {}).get("id") in has_telemetry:
            det = max(1, det - 1)
        if redundant:
            sev = max(1, sev - 1)
        sub = subsystem_of(e)
        domain = str(e.get("subsystem_domain") or (sub or {}).get("subsystem_domain") or "")
        funcs = list(alloc.get(e["id"], []))
        if e.get("element_type") == "subsystem":
            for k in kids.get(e["id"], []):
                funcs.extend(f for f in alloc.get(k["id"], []) if f not in funcs)
        single = allow_single and sev >= SINGLE_POINT_SEVERITY and not redundant
        is_critical = domain in CRITICAL_DOMAINS or any(f in crit_funcs for f in funcs)
        n += 1
        fm = FailureMode(id=f"FM-{n:03d}", component=str((sub or e).get("name")), mode=mode, cause=cause, local_effect=local,
                         system_effect=system, severity=sev, occurrence=occ, detection=det, mitigation=mit)
        chain = propagate_effects(fm, graph) if graph else []
        modes.append({
            "id": fm.id, "element_id": e["id"], "element_name": e.get("name"), "element_type": e.get("element_type"),
            "subsystem_id": (sub or {}).get("id"), "subsystem": (sub or {}).get("name"), "domain": domain,
            "mode": mode, "cause": cause, "local_effect": local, "system_effect": system,
            "severity": sev, "occurrence": occ, "detection": det, "rpn": fm.rpn, "mitigation": mit,
            "redundancy_type": e.get("redundancy_type"), "quantity": e.get("quantity") or 1, "redundant": redundant,
            "single_point": single, "critical": is_critical, "function_ids": funcs,
            "functions": [func_name.get(f, f) for f in funcs],
            "affected": [c["subsystem"] for c in chain if c["level"] == "subsystem"], "source": source,
        })

    for e in space:
        if e.get("element_type") == "subsystem":
            comps = [k for k in kids.get(e["id"], []) if k.get("element_type") == "component"]
            for fm in _catalogue_for_domain(str(e.get("subsystem_domain") or "")):
                if comps and any(w in fm.mode.lower() for w in ("battery", "solar array", "reaction wheel", "star tracker",
                                                                 "transponder", "antenna", "heater")):
                    # the component-level entry covers it when such a component exists
                    if any(any(w in str(k.get("name", "")).lower() for w in fm.mode.lower().split()[:2]) for k in comps):
                        continue
                # with components modelled, the subsystem-level entries are generic risks (single-point
                # flags belong to the components); without, the subsystem stands in for its hardware
                add(e, (fm.mode, fm.cause, fm.local_effect, fm.system_effect, fm.severity, fm.occurrence, fm.detection, fm.mitigation),
                    "catalogue", allow_single=not comps)
            if not comps and not _catalogue_for_domain(str(e.get("subsystem_domain") or "")):
                add(e, _component_mode(e, _kb(e.get("kb_component_id"))), "generic")
        else:
            add(e, _component_mode(e, _kb(e.get("kb_component_id"))), "component")

    modes.sort(key=lambda m: (-m["rpn"], m["id"]))
    max_rpn = max((m["rpn"] for m in modes), default=0)
    single_points = [m for m in modes if m["single_point"]]
    critical_sp = [m for m in single_points if m["critical"]]

    P = out.parameters
    P.append(ParamWrite("fmeca_max_rpn", float(max_rpn), unit="", description="Highest risk priority number (S x O x D)"))
    P.append(ParamWrite("fmeca_single_point_failures", float(len(single_points)), unit="", description="Failure modes with severity >= 4 and no redundancy"))
    P.append(ParamWrite("fmeca_modes", float(len(modes)), unit="", description="Failure modes in the table"))
    P.append(ParamWrite("fmeca_critical_modes", float(len(critical_sp)), unit="", description="Single-point failures on critical elements"))

    seen: set[str] = set()
    for m in critical_sp:
        if m["element_id"] in seen:
            continue
        seen.add(m["element_id"])
        el = by_id.get(m["element_id"], {})
        why = (f"function(s) {', '.join(m['functions'])}" if any(f in crit_funcs for f in m["function_ids"])
               else f"{m['domain']} subsystem")
        out.conflicts.append(Conflict(
            "major", "FMECA_SINGLE_POINT",
            f"Single-point failure: {m['element_name']} — {m['mode']}",
            f"Severity {m['severity']}, RPN {m['rpn']}; critical because of the {why}. System effect: {m['system_effect']}."
            + (f" Downstream: {', '.join(m['affected'])}." if m["affected"] else ""),
            element_ids=[m["element_id"]], requirement_ids=[],
            suggested_fix=f"set redundancy_type='cold' (or quantity 2) on {m['element_name']}, or accept the risk with rationale; "
                          f"mitigation: {m['mitigation']}"))

    out.series = {"analysis": ANALYSIS, "modes": modes, "graph": graph,
                  "critical_function_ids": sorted(crit_funcs)}
    out.summary = {
        **{p.name: p.value for p in P},
        "modes": len(modes), "single_points": [m["element_id"] for m in single_points],
        "critical_single_points": [m["element_id"] for m in critical_sp],
        "top": [{"id": m["id"], "element": m["element_name"], "mode": m["mode"], "rpn": m["rpn"]} for m in modes[:5]],
        "conflict_codes": [c.code for c in out.conflicts], "warnings": out.warnings,
    }
    return out
