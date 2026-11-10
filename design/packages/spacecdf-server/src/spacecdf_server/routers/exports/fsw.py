"""SpaceCDF export family: fsw.

Flight-software architecture scaffolding (state machine, tasks, memory map, TM/TC, fault handlers).
Routes (prefix /api/exports): POST /fsw/{study_id}

Moved verbatim from the single routers/exports.py in W0.1 (no behaviour change).
See design/docs/dev/W0_SEAMS.md for the module map and file ownership.
"""
from __future__ import annotations

import re

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..studies import get_study_store
from . import _common

router = APIRouter()

# ─── Helpers: FSW enrichment from study data ───

def _derive_state_machine(study) -> dict:
    """Derive FSW state machine from ConOps modes."""
    states = []
    transitions = []
    conops = getattr(study, "conops", None)
    if not conops:
        return {"states": [], "transitions": []}

    modes = getattr(conops, "modes", [])
    for m in modes:
        mode_name = m.name if hasattr(m, "name") else str(m)
        mode_type = m.mode_type.value if hasattr(m, "mode_type") and hasattr(m.mode_type, "value") else ""
        states.append({
            "name": mode_name,
            "mode_type": mode_type,
            "is_critical": getattr(m, "is_critical", False),
            "power_w": getattr(m, "power_w", 0.0),
        })

    # Standard transitions: any mode can reach Safe, Safe can reach any
    mode_names = [s["name"] for s in states]
    safe_name = next((n for n in mode_names if "safe" in n.lower()), mode_names[0] if mode_names else "Safe")

    for name in mode_names:
        if name != safe_name:
            transitions.append({
                "from": name, "to": safe_name,
                "trigger": "fault_detected OR cmd_go_safe",
                "priority": "critical",
            })
            transitions.append({
                "from": safe_name, "to": name,
                "trigger": f"cmd_enter_{re.sub(r'[^a-z0-9]', '_', name.lower())}",
                "priority": "nominal",
            })

    # Sequential transitions between non-safe modes
    non_safe = [n for n in mode_names if n != safe_name]
    for i in range(len(non_safe) - 1):
        transitions.append({
            "from": non_safe[i], "to": non_safe[i + 1],
            "trigger": f"mode_complete_{re.sub(r'[^a-z0-9]', '_', non_safe[i].lower())}",
            "priority": "nominal",
        })

    return {"states": states, "transitions": transitions}


def _derive_task_list(elements: list[dict]) -> list[dict]:
    """Derive FSW task list from element tree — one task per subsystem domain."""
    domain_priorities = {
        "eps": ("eps_manager", 2, 1000),
        "power": ("power_manager", 2, 1000),
        "aocs": ("aocs_controller", 1, 100),
        "ttc": ("ttc_handler", 3, 5000),
        "obc": ("obc_supervisor", 1, 500),
        "obdh": ("obdh_manager", 2, 1000),
        "payload": ("payload_controller", 5, 10000),
        "thermal": ("thermal_monitor", 6, 30000),
        "propulsion": ("propulsion_manager", 4, 5000),
        "structure": ("structure_monitor", 8, 60000),
        "structures": ("structure_monitor", 8, 60000),
    }
    seen_domains: set[str] = set()
    tasks = []
    for e in elements:
        domain = e.get("subsystem_domain", "")
        if not domain or domain in seen_domains:
            continue
        if e.get("segment") != "space":
            continue
        seen_domains.add(domain)
        task_name, priority, period = domain_priorities.get(
            domain, (f"{domain}_handler", 7, 10000)
        )
        tasks.append({
            "task_name": task_name,
            "subsystem_domain": domain,
            "priority": priority,
            "period_ms": period,
            "stack_size_bytes": 4096,
        })
    # Always include watchdog and housekeeping
    tasks.append({"task_name": "watchdog", "subsystem_domain": "system",
                  "priority": 0, "period_ms": 100, "stack_size_bytes": 1024})
    tasks.append({"task_name": "housekeeping_collector", "subsystem_domain": "system",
                  "priority": 9, "period_ms": 10000, "stack_size_bytes": 2048})
    return sorted(tasks, key=lambda t: t["priority"])


def _derive_memory_map(elements: list[dict]) -> dict:
    """Estimate OBC memory map from component count. 512KB typical CubeSat."""
    space_components = [e for e in elements if e.get("segment") == "space"
                        and e.get("element_type") == "component"]
    component_count = len(space_components)
    total_ram_kb = 512
    os_kb = 128
    fsw_kb = 256
    data_buffer_kb = 128
    # Scale FSW allocation slightly with component count
    if component_count > 10:
        fsw_kb = min(fsw_kb + (component_count - 10) * 4, 384)
        data_buffer_kb = total_ram_kb - os_kb - fsw_kb

    return {
        "total_ram_kb": total_ram_kb,
        "allocation": {
            "os_kernel": {"size_kb": os_kb, "description": "RTOS kernel + drivers"},
            "fsw_application": {"size_kb": fsw_kb, "description": "Flight software application code + state"},
            "data_buffer": {"size_kb": data_buffer_kb, "description": "Telemetry / science data ring buffer"},
        },
        "component_count": component_count,
        "estimated_task_count": component_count + 2,  # +watchdog +housekeeping
    }


def _derive_tm_tc(elements: list[dict], conops_modes: list) -> dict:
    """Derive TM/TC packet definitions from elements and ConOps modes."""
    # TM: one housekeeping packet per subsystem
    tm_packets = []
    seen_domains: set[str] = set()
    apid = 1
    for e in elements:
        domain = e.get("subsystem_domain", "")
        if not domain or domain in seen_domains or e.get("segment") != "space":
            continue
        seen_domains.add(domain)
        tm_packets.append({
            "apid": apid,
            "name": f"TM_{domain.upper()}_HK",
            "type": "housekeeping",
            "subsystem": domain,
            "rate_hz": 1.0 if domain in ("aocs", "eps", "obc") else 0.1,
            "size_bytes": 64,
        })
        apid += 1

    # TC: mode change commands + subsystem-specific
    tc_packets = []
    cmd_id = 1
    for mode in conops_modes:
        mode_name = mode.name if hasattr(mode, "name") else str(mode)
        tc_packets.append({
            "cmd_id": cmd_id,
            "name": f"TC_ENTER_{re.sub(r'[^A-Z0-9]', '_', mode_name.upper())}",
            "type": "mode_change",
            "target_mode": mode_name,
        })
        cmd_id += 1
    # Standard commands
    for cmd_name, cmd_type in [
        ("TC_RESET_OBC", "system"), ("TC_DEPLOY_ANTENNA", "mechanism"),
        ("TC_SET_PARAM", "configuration"), ("TC_REQUEST_TM", "data"),
    ]:
        tc_packets.append({"cmd_id": cmd_id, "name": cmd_name, "type": cmd_type})
        cmd_id += 1

    return {"tm_packets": tm_packets, "tc_packets": tc_packets}


def _derive_fault_handlers(elements: list[dict]) -> list[dict]:
    """Derive FDIR fault handlers from element domains."""
    handlers = []
    domains_present = {e.get("subsystem_domain", "") for e in elements
                       if e.get("segment") == "space"}

    fault_map = {
        "eps": {"fault": "power_low", "action": "safe_mode",
                "description": "Battery SoC below threshold — enter safe mode, shed non-essential loads"},
        "power": {"fault": "power_low", "action": "safe_mode",
                  "description": "Battery SoC below threshold — enter safe mode, shed non-essential loads"},
        "aocs": {"fault": "attitude_lost", "action": "sun_search",
                 "description": "Attitude determination lost — initiate sun search using coarse sensors"},
        "ttc": {"fault": "comms_lost", "action": "beacon_mode",
                "description": "No ground contact for N orbits — switch to low-rate beacon transmit"},
        "obc": {"fault": "obc_watchdog_timeout", "action": "warm_reset",
                "description": "OBC watchdog expired — perform warm reset and reload FSW from NVM"},
        "obdh": {"fault": "memory_fault", "action": "scrub_and_restart",
                 "description": "SEU detected in memory — scrub, verify checksum, restart task"},
        "thermal": {"fault": "over_temperature", "action": "load_shed",
                    "description": "Component temperature exceeds limit — reduce duty cycle, disable payload"},
        "payload": {"fault": "payload_anomaly", "action": "payload_safe",
                    "description": "Payload reports anomaly — disable payload, store diagnostic TM"},
        "propulsion": {"fault": "thruster_fault", "action": "inhibit_propulsion",
                       "description": "Thruster valve anomaly — close isolation valve, enter safe mode"},
    }

    for domain, handler in fault_map.items():
        if domain in domains_present:
            handlers.append({
                "subsystem": domain,
                "fault": handler["fault"],
                "action": handler["action"],
                "description": handler["description"],
                "severity": "critical" if domain in ("eps", "power", "aocs") else "major",
                "autonomous": True,
            })

    return handlers


# ─── Helpers: MBSE enrichment ───

@router.post("/fsw/{study_id}")
async def export_fsw_architecture(study_id: str) -> JSONResponse:
    """Generate flight software architecture scaffolding."""
    studies = get_study_store()
    study = studies.get(study_id)
    state, requirements, _ = await _common._run_design_for_study(study_id)

    # ── Gather element and ConOps data for enrichment ──
    elements: list[dict] = []
    conops_modes: list = []
    try:
        from ..elements import _elements
        elements = [e for e in _elements.values()
                    if e.get("study_id") == study_id and not e.get("deleted_at")]
    except Exception:
        pass
    if study:
        conops = getattr(study, "conops", None)
        conops_modes = getattr(conops, "modes", []) if conops else []

    # ── Derive FSW enrichments ──
    fsw_state_machine = _derive_state_machine(study) if study else {"states": [], "transitions": []}
    fsw_task_list = _derive_task_list(elements)
    fsw_memory_map = _derive_memory_map(elements)
    fsw_tm_tc = _derive_tm_tc(elements, conops_modes)
    fsw_fault_handlers = _derive_fault_handlers(elements)

    from spacecdf_agents.exporters.fsw.generator import FSWGenerator
    generator = FSWGenerator()
    files = generator.generate(state, requirements)

    return JSONResponse(content={
        "files": files,
        "file_count": len(files),
        "state_machine": fsw_state_machine,
        "task_list": fsw_task_list,
        "memory_map": fsw_memory_map,
        "tm_tc_definitions": fsw_tm_tc,
        "fault_handlers": fsw_fault_handlers,
    })
