"""SpaceCDF — Flight Software Architecture Generator.

Generates cFS-style FSW scaffolding: C headers for parameter databases,
telemetry/telecommand packet definitions, mode tables, FDIR rule tables,
and app skeletons for each subsystem.
"""
from __future__ import annotations

from spacecdf_common.agents.base import DesignState
from spacecdf_common.models.parameter import ParameterSource
from spacecdf_common.models.study import MissionRequirements
from spacecdf_agents.exporters.smo.param_id_allocator import ParamIDAllocator, BASE_PARAMS, SUBSYSTEM_BASE


# CCSDS APID assignment per subsystem (11-bit, SMO convention)
SUBSYSTEM_APID = {
    "eps":      0x100,
    "aocs":     0x200,
    "obdh":     0x300,
    "tcs":      0x400,
    "ttc":      0x500,
    "payload":  0x600,
    "propulsion": 0x700,
    "structure":  0x080,
}

# For each component category, the telemetry fields that make sense. Each
# tuple is (c_type, field_name, unit_comment).
CATEGORY_TM_FIELDS: dict[str, list[tuple[str, str, str]]] = {
    "batteries": [
        ("float",   "voltage_v",    "V"),
        ("float",   "current_a",    "A"),
        ("float",   "soc_percent",  "%"),
        ("float",   "temp_c",       "degC"),
        ("uint8_t", "status_flags", ""),
    ],
    "solar_cells": [
        ("float",   "current_a",    "A"),
        ("float",   "voltage_v",    "V"),
        ("float",   "power_w",      "W"),
        ("float",   "temp_c",       "degC"),
        ("uint8_t", "status_flags", ""),
    ],
    "reaction_wheels": [
        ("float",   "speed_rpm",    "RPM"),
        ("float",   "torque_nm",    "Nm"),
        ("float",   "momentum_nms", "Nms"),
        ("float",   "temp_c",       "degC"),
        ("uint8_t", "status_flags", ""),
    ],
    "star_trackers": [
        ("float",   "quat_q1", ""),
        ("float",   "quat_q2", ""),
        ("float",   "quat_q3", ""),
        ("float",   "quat_q4", ""),
        ("float",   "temp_c",  "degC"),
        ("uint8_t", "valid_flag", ""),
        ("uint8_t", "status_flags", ""),
    ],
    "transponders": [
        ("float",   "rssi_dbm",     "dBm"),
        ("float",   "link_margin_db", "dB"),
        ("uint32_t", "bitrate_bps", "bps"),
        ("float",   "temp_c",       "degC"),
        ("uint8_t", "mode",         ""),
        ("uint8_t", "status_flags", ""),
    ],
    "thrusters": [
        ("float",   "thrust_n",   "N"),
        ("float",   "isp_s",      "s"),
        ("float",   "temp_c",     "degC"),
        ("uint32_t", "burn_count", ""),
        ("uint8_t", "valve_state", ""),
        ("uint8_t", "status_flags", ""),
    ],
}

# Map SpaceCDF domain to FSW subsystem label
DOMAIN_TO_SUBSYS = {
    "power": "eps",
    "aocs": "aocs",
    "data": "obdh",
    "thermal": "tcs",
    "link": "ttc",
    "propulsion": "propulsion",
    "structure": "structure",
    "payload": "payload",
}


def _c_ident(s: str) -> str:
    """Sanitise a string into a valid C identifier suffix."""
    out = []
    for ch in s:
        if ch.isalnum():
            out.append(ch)
        else:
            out.append("_")
    # Ensure doesn't start with digit
    if out and out[0].isdigit():
        out.insert(0, "_")
    return "".join(out) or "x"


class FSWGenerator:
    """Generates flight software architecture from design state."""

    def generate(self, state: DesignState, requirements: MissionRequirements) -> dict[str, str]:
        """Generate FSW scaffolding files.

        Returns dict of filepath -> file content (as strings).
        """
        files: dict[str, str] = {}
        allocator = ParamIDAllocator()
        allocator.allocate_from_state(state)

        # Collect selected equipment per subsystem for TM packet generation
        selected_equipment = self._collect_selected_equipment(state)

        files["inc/param_db.h"] = self._gen_param_db(allocator)
        files["inc/apids.h"] = self._gen_apids(selected_equipment)
        files["inc/tm_packets.h"] = self._gen_tm_packets(allocator, selected_equipment)
        files["inc/mode_table.h"] = self._gen_mode_table(state)
        files["inc/fdir_rules.h"] = self._gen_fdir_rules(state)
        files["CMakeLists.txt"] = self._gen_cmake(requirements)

        # Generate app skeletons
        apps = ["mode_manager", "hk_service", "eps", "aocs", "tcs", "ttc",
                "payload", "fdir", "monitoring", "event_action"]
        for app in apps:
            files[f"src/{app}/{app}_app.h"] = self._gen_app_header(app)
            files[f"src/{app}/{app}_app.c"] = self._gen_app_source(app, state)

        files["src/main.c"] = self._gen_main(apps)

        files["docs/fsw_architecture.md"] = self._gen_architecture_doc(state, requirements)

        return files

    def _collect_selected_equipment(self, state: DesignState) -> dict[str, list[dict]]:
        """Group KB-selected equipment by FSW subsystem.

        Returns a dict keyed by subsystem (eps/aocs/...) where each value is
        a list of {id, name, category, domain, fields} entries.
        """
        # Try to locate KB components data by loading only what's needed; we
        # don't actually need KB files here — we infer the category from the
        # parameter's domain/name. But categories are the strongest signal.
        grouped: dict[str, list[dict]] = {}
        seen_ids: set[str] = set()
        for pid, p in sorted(state.parameters.items()):
            if p.source != ParameterSource.KB_COMPONENT:
                continue
            eq_id = p.equipment_id
            if not eq_id or eq_id in seen_ids:
                continue
            seen_ids.add(eq_id)
            subsys = DOMAIN_TO_SUBSYS.get(p.domain, "obdh")
            # Infer category from parameter id
            category = self._infer_category(p.domain, pid)
            fields = CATEGORY_TM_FIELDS.get(
                category, [("float", "value", ""), ("uint8_t", "status_flags", "")]
            )
            grouped.setdefault(subsys, []).append({
                "id": eq_id,
                "name": p.equipment_name or eq_id,
                "category": category,
                "domain": p.domain,
                "fields": fields,
            })
        return grouped

    @staticmethod
    def _infer_category(domain: str, param_id: str) -> str:
        """Infer KB category from the domain and parameter id."""
        lp = param_id.lower()
        if "battery" in lp or "bat_" in lp:
            return "batteries"
        if "sa_" in lp or "solar" in lp:
            return "solar_cells"
        if "wheel" in lp or "rw" in lp:
            return "reaction_wheels"
        if "star_tracker" in lp or "str_" in lp or "pointing" in lp:
            return "star_trackers"
        if domain == "link" or "xpdr" in lp or "transponder" in lp:
            return "transponders"
        if domain == "propulsion" or "thrust" in lp:
            return "thrusters"
        return ""

    def _gen_param_db(self, allocator: ParamIDAllocator) -> str:
        lines = [
            "/**",
            " * @file param_db.h",
            " * @brief Spacecraft Parameter Database — Auto-generated by SpaceCDF",
            " *",
            " * DO NOT EDIT MANUALLY. Regenerate from SpaceCDF design state.",
            " */",
            "",
            "#ifndef PARAM_DB_H",
            "#define PARAM_DB_H",
            "",
            "#include <stdint.h>",
            "",
            "typedef struct {",
            "    uint16_t id;",
            "    const char *name;",
            "    const char *unit;",
            "    float scale;",
            "    float low_limit;",
            "    float high_limit;",
            "} ParamDef_t;",
            "",
            f"#define PARAM_DB_COUNT {len(allocator.param_defs)}",
            "",
            "static const ParamDef_t PARAM_DB[PARAM_DB_COUNT] = {",
        ]
        for pdef in allocator.param_defs:
            name = pdef["name"].replace(".", "_")
            unit = pdef["units"]
            lines.append(
                f'    {{0x{pdef["id"]:04X}, "{name}", "{unit}", 100.0f, 0.0f, 0.0f}},'
            )
        lines.append("};")
        lines.append("")

        # Named constants for param IDs
        lines.append("/* Parameter ID constants */")
        for pdef in allocator.param_defs:
            cname = pdef["name"].replace(".", "_").upper()
            lines.append(f"#define PARAM_{cname} 0x{pdef['id']:04X}")
        lines.append("")
        lines.append("#endif /* PARAM_DB_H */")
        return "\n".join(lines)

    def _gen_tm_packets(
        self,
        allocator: ParamIDAllocator,
        selected_equipment: dict[str, list[dict]] | None = None,
    ) -> str:
        selected_equipment = selected_equipment or {}
        lines = [
            "/**",
            " * @file tm_packets.h",
            " * @brief Telemetry Packet Definitions — Auto-generated by SpaceCDF",
            " */",
            "",
            "#ifndef TM_PACKETS_H",
            "#define TM_PACKETS_H",
            "",
            "#include <stdint.h>",
            '#include "apids.h"',
            "",
        ]

        # 1) Per-subsystem housekeeping packets from the parameter DB
        subsys_params: dict[str, list] = {}
        for pdef in allocator.param_defs:
            subsys = pdef["subsystem"]
            subsys_params.setdefault(subsys, []).append(pdef)

        for subsys, params in sorted(subsys_params.items()):
            struct_name = f"HK_{subsys.upper()}_Packet_t"
            lines.append(f"/* SID: {subsys.upper()} Housekeeping (APID 0x{SUBSYSTEM_APID.get(subsys, 0x300):03X}) */")
            lines.append("typedef struct __attribute__((packed)) {")
            for p in params:
                field_name = p["name"].replace(".", "_").replace(f"{subsys}_", "")
                lines.append(f"    uint16_t {field_name};")
            lines.append(f"}} {struct_name};")
            lines.append("")

        # 2) Per-equipment TM packets from selected KB components
        if selected_equipment:
            lines.append("/* --- Per-equipment TM packets (KB-selected components) --- */")
            lines.append("")
            for subsys in sorted(selected_equipment.keys()):
                for comp in selected_equipment[subsys]:
                    safe_id = _c_ident(comp["id"])
                    struct_name = f"TM_{subsys.upper()}_{safe_id.upper()}_Packet_t"
                    lines.append(
                        f"/* Equipment: {comp['name']} (id={comp['id']}, "
                        f"category={comp['category']}) */"
                    )
                    lines.append("typedef struct __attribute__((packed)) {")
                    lines.append("    uint32_t timestamp_s;")
                    for ctype, fname, unit in comp["fields"]:
                        unit_tag = f" /* {unit} */" if unit else ""
                        lines.append(f"    {ctype} {fname};{unit_tag}")
                    lines.append(f"}} {struct_name};")
                    lines.append("")

        lines.append("#endif /* TM_PACKETS_H */")
        return "\n".join(lines)

    def _gen_apids(self, selected_equipment: dict[str, list[dict]]) -> str:
        lines = [
            "/**",
            " * @file apids.h",
            " * @brief CCSDS APID assignments — Auto-generated by SpaceCDF",
            " */",
            "",
            "#ifndef APIDS_H",
            "#define APIDS_H",
            "",
            "#include <stdint.h>",
            "",
            "/* Subsystem APID bases (CCSDS 11-bit, top 4 bits = subsystem) */",
        ]
        for subsys, apid in sorted(SUBSYSTEM_APID.items()):
            lines.append(f"#define APID_{subsys.upper()}_BASE 0x{apid:03X}")
        lines.append("")
        lines.append("/* Standard sub-APID offsets within a subsystem */")
        lines.append("#define APID_OFFSET_HK       0x00  /* Housekeeping */")
        lines.append("#define APID_OFFSET_EVENT    0x01  /* Event report */")
        lines.append("#define APID_OFFSET_DIAG     0x02  /* Diagnostic dump */")
        lines.append("#define APID_OFFSET_CMD_ACK  0x03  /* Command acknowledge */")
        lines.append("")

        # Per-equipment APID allocations: base + 0x10 + index
        if selected_equipment:
            lines.append("/* Per-equipment TM APIDs */")
            for subsys in sorted(selected_equipment.keys()):
                for idx, comp in enumerate(selected_equipment[subsys]):
                    safe_id = _c_ident(comp["id"]).upper()
                    apid = SUBSYSTEM_APID.get(subsys, 0x300) + 0x10 + idx
                    lines.append(
                        f"#define APID_{subsys.upper()}_{safe_id} 0x{apid:03X}"
                    )
            lines.append("")

        lines.append("#endif /* APIDS_H */")
        return "\n".join(lines)

    def _gen_mode_table(self, state: DesignState) -> str:
        lines = [
            "/**",
            " * @file mode_table.h",
            " * @brief Spacecraft Mode Definitions — Auto-generated by SpaceCDF",
            " */",
            "",
            "#ifndef MODE_TABLE_H",
            "#define MODE_TABLE_H",
            "",
            "typedef enum {",
            "    MODE_BOOT = 0,",
            "    MODE_SAFE = 1,",
            "    MODE_STANDBY = 2,",
            "    MODE_NOMINAL = 3,",
            "    MODE_COMMISSIONING = 4,",
            "    MODE_ORBIT_MAINTENANCE = 5,",
            "    MODE_DECOMMISSION = 6,",
            "    MODE_COUNT",
            "} SpacecraftMode_t;",
            "",
            "typedef struct {",
            "    SpacecraftMode_t mode;",
            "    const char *name;",
            "    uint8_t payload_active;",
            "    uint8_t aocs_mode;   /* 0=safe, 1=nominal, 2=slew */",
            "    uint8_t tx_active;",
            "    uint8_t heaters_active;",
            "} ModeConfig_t;",
            "",
            "static const ModeConfig_t MODE_TABLE[MODE_COUNT] = {",
            '    {MODE_BOOT,         "BOOT",         0, 0, 0, 1},',
            '    {MODE_SAFE,         "SAFE",         0, 0, 0, 1},',
            '    {MODE_STANDBY,      "STANDBY",      0, 1, 0, 1},',
            '    {MODE_NOMINAL,      "NOMINAL",      1, 1, 1, 1},',
            '    {MODE_COMMISSIONING,"COMMISSIONING", 0, 1, 1, 1},',
            '    {MODE_ORBIT_MAINTENANCE,"ORBIT_MAINT",0,2, 0, 1},',
            '    {MODE_DECOMMISSION, "DECOMMISSION", 0, 0, 0, 0},',
            "};",
            "",
            "#endif /* MODE_TABLE_H */",
        ]
        return "\n".join(lines)

    def _gen_fdir_rules(self, state: DesignState) -> str:
        lines = [
            "/**",
            " * @file fdir_rules.h",
            " * @brief FDIR Rule Table — Auto-generated by SpaceCDF",
            " */",
            "",
            "#ifndef FDIR_RULES_H",
            "#define FDIR_RULES_H",
            "",
            "#include <stdint.h>",
            "",
            "typedef enum {",
            "    FDIR_COND_LESS_THAN = 0,",
            "    FDIR_COND_GREATER_THAN = 1,",
            "} FdirCondition_t;",
            "",
            "typedef enum {",
            "    FDIR_ACT_LOAD_SHED_1 = 0x10,",
            "    FDIR_ACT_LOAD_SHED_2 = 0x11,",
            "    FDIR_ACT_LOAD_SHED_3 = 0x12,",
            "    FDIR_ACT_SAFE_MODE   = 0x20,",
            "    FDIR_ACT_AOCS_RESET  = 0x30,",
            "    FDIR_ACT_PAYLOAD_OFF = 0x41,",
            "} FdirAction_t;",
            "",
            "typedef struct {",
            "    uint16_t param_id;",
            "    float threshold;",
            "    FdirCondition_t condition;",
            "    uint8_t fdir_level;",
            "    FdirAction_t action;",
            '    const char *description;',
            "} FdirRule_t;",
            "",
            "#define FDIR_RULE_COUNT 5",
            "",
            "static const FdirRule_t FDIR_RULES[FDIR_RULE_COUNT] = {",
            '    {0x0101, 20.0f, FDIR_COND_LESS_THAN, 2, FDIR_ACT_LOAD_SHED_1, "Battery SOC low"},',
            '    {0x0101, 10.0f, FDIR_COND_LESS_THAN, 3, FDIR_ACT_SAFE_MODE,   "Battery SOC critical"},',
            '    {0x020C,  5.0f, FDIR_COND_GREATER_THAN, 2, FDIR_ACT_AOCS_RESET, "Attitude error high"},',
            '    {0x0407, 45.0f, FDIR_COND_GREATER_THAN, 2, FDIR_ACT_LOAD_SHED_1, "Battery temp high"},',
            '    {0x0407,-10.0f, FDIR_COND_LESS_THAN, 2, FDIR_ACT_LOAD_SHED_1, "Battery temp low"},',
            "};",
            "",
            "#endif /* FDIR_RULES_H */",
        ]
        return "\n".join(lines)

    def _gen_cmake(self, req: MissionRequirements) -> str:
        name = req.name.replace(" ", "_").replace("-", "_").lower()
        lines = [
            f"# CMakeLists.txt — {req.name} Flight Software",
            f"# Auto-generated by SpaceCDF",
            "cmake_minimum_required(VERSION 3.16)",
            f"project({name}_fsw C)",
            "",
            "set(CMAKE_C_STANDARD 11)",
            "",
            "# Developer must set CFS_SRC_ROOT to point at their cFS checkout.",
            'if(NOT DEFINED CFS_SRC_ROOT)',
            '    set(CFS_SRC_ROOT "/opt/cfs" CACHE PATH "Path to cFS source tree")',
            'endif()',
            "",
            "include_directories(",
            "    ${CMAKE_CURRENT_SOURCE_DIR}/inc",
            "    ${CFS_SRC_ROOT}/osal/src/os/inc",
            "    ${CFS_SRC_ROOT}/psp/fsw/inc",
            "    ${CFS_SRC_ROOT}/cfe/fsw/cfe-core/src/inc",
            "    ${CFS_SRC_ROOT}/cfe/fsw/inc",
            ")",
            "",
            "# Application libraries (one per subsystem app)",
        ]
        apps = ["mode_manager", "hk_service", "eps", "aocs", "tcs", "ttc",
                "payload", "fdir", "monitoring", "event_action"]
        for app in apps:
            lines.append(f"add_library({app} STATIC src/{app}/{app}_app.c)")
            lines.append(f"target_include_directories({app} PRIVATE src/{app})")
        lines.append("")
        lines.append(f"# Top-level executable — wires the scheduler")
        lines.append(f"add_executable({name}_fsw src/main.c)")
        lines.append(f"target_link_libraries({name}_fsw PRIVATE {' '.join(apps)})")
        lines.append("")
        return "\n".join(lines)

    def _gen_main(self, apps: list[str]) -> str:
        """Generate a simple 1 Hz scheduler that calls each app's HK() function."""
        includes = "\n".join(f'#include "{a}_app.h"' for a in apps)
        hk_calls = "\n".join(f"        {a}_HK();" for a in apps)
        init_calls = "\n".join(f"    {a}_Init();" for a in apps)
        return "\n".join([
            "/**",
            " * @file main.c",
            " * @brief SpaceCDF-generated FSW top-level scheduler.",
            " *",
            " * Initialises each application once, then runs a simple 1 Hz",
            " * cooperative scheduler that calls each app's HK() function.",
            " * Replace the sleep() call with a cFS/OSAL timer primitive in",
            " * the target environment.",
            " */",
            "",
            "#include <stdio.h>",
            "#include <stdint.h>",
            includes,
            "",
            "/* Portable 1 Hz delay: the real build should link against OSAL. */",
            "static void sched_sleep_1hz(void) {",
            "    /* TODO: OS_TaskDelay(1000); */",
            "}",
            "",
            "int main(void) {",
            init_calls,
            "",
            "    uint32_t tick = 0;",
            "    while (1) {",
            "        /* 1 Hz housekeeping cycle */",
            hk_calls,
            "        tick++;",
            "        sched_sleep_1hz();",
            "        if (tick == 0xFFFFFFFFu) break; /* guard — will never trigger */",
            "    }",
            "    return 0;",
            "}",
            "",
        ])

    def _gen_app_header(self, app_name: str) -> str:
        guard = f"{app_name.upper()}_APP_H"
        return "\n".join([
            f"/**",
            f" * @file {app_name}_app.h",
            f" * @brief {app_name.replace('_', ' ').title()} Application — Auto-generated by SpaceCDF",
            f" */",
            f"",
            f"#ifndef {guard}",
            f"#define {guard}",
            f"",
            f"#include <stdint.h>",
            f"#include \"param_db.h\"",
            f"",
            f"/* Application data */",
            f"typedef struct {{",
            f"    uint32_t run_count;",
            f"    uint8_t  enabled;",
            f"}} {app_name}_AppData_t;",
            f"",
            f"/* Public interface */",
            f"void {app_name}_Main(void);",
            f"int32_t {app_name}_Init(void);",
            f"void {app_name}_HK(void);",
            f"void {app_name}_ProcessCommand(uint16_t cmd_code, const uint8_t *data, uint16_t len);",
            f"",
            f"#endif /* {guard} */",
        ])

    def _gen_app_source(self, app_name: str, state: DesignState) -> str:
        lines = [
            f"/**",
            f" * @file {app_name}_app.c",
            f" * @brief {app_name.replace('_', ' ').title()} Application — Auto-generated by SpaceCDF",
            f" *",
            f" * This is a skeleton. Implement the TODO sections with mission-specific logic.",
            f" */",
            f"",
            f'#include "{app_name}_app.h"',
            f'#include "mode_table.h"',
            f'#include "fdir_rules.h"',
            f"",
            f"static {app_name}_AppData_t AppData;",
            f"",
            f"void {app_name}_Main(void)",
            f"{{",
            f"    /* Register with Executive Services */",
            f"    /* TODO: CFE_ES_RegisterApp(); */",
            f"",
            f"    {app_name}_Init();",
            f"",
            f"    /* Main loop */",
            f"    while (1) {{",
            f"        /* TODO: Wait for Software Bus message */",
            f"        /* CFE_SB_RcvMsg(&MsgPtr, AppData.CmdPipe, CFE_SB_PEND_FOREVER); */",
            f"        AppData.run_count++;",
            f"    }}",
            f"}}",
            f"",
            f"void {app_name}_HK(void)",
            f"{{",
            f"    /* 1 Hz housekeeping tick: gather telemetry, publish on SB. */",
            f"    if (!AppData.enabled) return;",
            f"    AppData.run_count++;",
            f"    /* TODO: populate HK packet and CFE_SB_SendMsg(). */",
            f"}}",
            f"",
            f"int32_t {app_name}_Init(void)",
            f"{{",
            f"    AppData.run_count = 0;",
            f"    AppData.enabled = 1;",
            f"",
            f"    /* TODO: Create Software Bus pipe */",
            f"    /* TODO: Subscribe to command Message IDs */",
            f"    /* TODO: Register tables */",
            f"",
            f"    return 0;",
            f"}}",
            f"",
            f"void {app_name}_ProcessCommand(uint16_t cmd_code, const uint8_t *data, uint16_t len)",
            f"{{",
            f"    switch (cmd_code) {{",
            f"        case 0x00: /* NOOP */",
            f"            break;",
            f"        case 0x01: /* Reset counters */",
            f"            AppData.run_count = 0;",
            f"            break;",
            f"        default:",
            f"            /* TODO: Implement {app_name}-specific commands */",
            f"            break;",
            f"    }}",
            f"}}",
        ]
        return "\n".join(lines)

    def _gen_architecture_doc(self, state: DesignState, req: MissionRequirements) -> str:
        lines = [
            f"# {req.name} — Flight Software Architecture",
            f"",
            f"**Generated by:** SpaceCDF AI Concurrent Design Facility",
            f"",
            f"## Overview",
            f"",
            f"The {req.name} flight software follows a cFS (core Flight System) architecture",
            f"with a Software Bus message-passing paradigm. Applications communicate exclusively",
            f"via CCSDS message packets, enabling independent development and testing.",
            f"",
            f"## Application Map",
            f"",
            f"| Application | PUS Service | Function |",
            f"|------------|-------------|----------|",
            f"| mode_manager | — | System mode FSM, mode transitions |",
            f"| hk_service | ST[03] | Housekeeping telemetry collection |",
            f"| eps | ST[08] | Power subsystem management |",
            f"| aocs | ST[08] | Attitude determination and control |",
            f"| tcs | ST[08] | Thermal control |",
            f"| ttc | ST[08] | Communication subsystem |",
            f"| payload | ST[08] | Payload operations |",
            f"| fdir | ST[19] | Fault detection, isolation, recovery |",
            f"| monitoring | ST[12] | Parameter limit monitoring |",
            f"| event_action | ST[05] | Event reporting |",
            f"",
            f"## Spacecraft Modes",
            f"",
            f"| Mode | Payload | AOCS | TX | Heaters |",
            f"|------|---------|------|----|---------|",
            f"| BOOT | Off | Safe | Off | On |",
            f"| SAFE | Off | Safe | Off | On |",
            f"| STANDBY | Off | Nominal | Off | On |",
            f"| NOMINAL | On | Nominal | On | On |",
            f"| COMMISSIONING | Off | Nominal | On | On |",
            f"",
            f"## Key Design Parameters",
            f"",
            f"- Parameter count: {len(state.parameters)}",
            f"- Spacecraft class: {req.spacecraft_class}",
            f"- Mission duration: {req.design_lifetime_years} years",
            f"",
        ]
        return "\n".join(lines)
