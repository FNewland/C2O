"""Study context serialization for AI prompts.

Converts SpaceCDF design state into structured text that Claude can
reason over effectively.  Three granularities:

- build_study_context(): Full study — element tree + all budgets + requirements
- build_agent_context(): Single-agent scope — one subsystem's parameters
- build_review_context(): CDR-quality review — everything plus interfaces & ConOps
"""
from __future__ import annotations

from typing import Any


def build_study_context(
    study: dict[str, Any],
    elements: list[dict] | None = None,
    budgets: dict[str, Any] | None = None,
    requirements: list[dict] | None = None,
    max_elements: int = 200,
) -> str:
    """Serialize full study state into AI-readable context.

    Args:
        study: Study metadata (name, mission_need, orbit, payloads, etc.)
        elements: Element tree nodes [{id, name, type, parent_id, properties}]
        budgets: Budget summaries {mass: {...}, power: {...}, ...}
        requirements: Requirement list [{id, text, level, parent_id, verification}]
        max_elements: Truncate element tree to this many nodes
    """
    sections: list[str] = []

    # Mission identity
    name = study.get("name", "Unnamed Study")
    sections.append(f"# Mission: {name}")

    # Mission need
    mn = study.get("mission_need", {})
    if mn:
        if mn.get("problem_statement"):
            sections.append(f"\n## Problem Statement\n{mn['problem_statement']}")
        if mn.get("objectives"):
            sections.append("\n## Objectives")
            for obj in mn["objectives"]:
                pri = obj.get("priority", "?")
                text = obj.get("text", "?")
                sections.append(f"- [{pri}] {text}")

    # Orbit
    orbit = study.get("orbit") or study.get("requirements", {}).get("orbit", {})
    if orbit:
        sections.append("\n## Orbit")
        sections.append(f"- Type: {orbit.get('orbit_type', '?')}")
        sections.append(f"- Altitude: {orbit.get('altitude_km', '?')} km")
        sections.append(f"- Inclination: {orbit.get('inclination_deg', '?')} deg")
        if orbit.get("raan_deg"):
            sections.append(f"- RAAN: {orbit['raan_deg']} deg")

    # Payloads
    payloads = study.get("payloads") or study.get("requirements", {}).get("payloads", [])
    if payloads:
        sections.append("\n## Payloads")
        for pl in payloads:
            sections.append(
                f"- {pl.get('name', '?')}: {pl.get('mass_kg', '?')} kg, "
                f"{pl.get('power_w', '?')} W, {pl.get('data_rate_mbps', '?')} Mbps"
            )

    # Element tree
    if elements:
        sections.append(f"\n## Design Elements ({len(elements)} nodes)")
        for el in elements[:max_elements]:
            indent = "  " * el.get("depth", 0)
            etype = el.get("type", "?")
            ename = el.get("name", "?")
            props = el.get("properties", {})
            mass = props.get("mass_kg", "")
            power = props.get("power_w", "")
            extras = ""
            if mass:
                extras += f" [{mass} kg"
                if power:
                    extras += f", {power} W"
                extras += "]"
            sections.append(f"{indent}- {ename} ({etype}){extras}")
        if len(elements) > max_elements:
            sections.append(f"  ... ({len(elements) - max_elements} more elements truncated)")

    # Budgets
    if budgets:
        sections.append("\n## Engineering Budgets")
        for bname, bdata in budgets.items():
            if isinstance(bdata, dict):
                sections.append(f"\n### {bname.replace('_', ' ').title()}")
                for key, val in bdata.items():
                    if isinstance(val, (int, float, str)):
                        sections.append(f"- {key}: {val}")

    # Requirements
    if requirements:
        sections.append(f"\n## Requirements ({len(requirements)})")
        for req in requirements[:50]:
            level = req.get("level", "?")
            text = req.get("text", "?")
            ver = req.get("verification_method", "")
            ver_str = f" [{ver}]" if ver else ""
            sections.append(f"- [{level}] {text}{ver_str}")
        if len(requirements) > 50:
            sections.append(f"  ... ({len(requirements) - 50} more requirements)")

    return "\n".join(sections)


def build_agent_context(
    agent_name: str,
    parameters: dict[str, Any],
    related_budgets: dict[str, Any] | None = None,
) -> str:
    """Serialize single-agent context for focused AI assistance.

    Args:
        agent_name: Name of the design agent (e.g. "power", "aocs")
        parameters: Agent's input/output parameters
        related_budgets: Budget data relevant to this agent
    """
    sections = [f"# Agent: {agent_name}"]

    sections.append("\n## Parameters")
    for key, val in sorted(parameters.items()):
        sections.append(f"- {key}: {val}")

    if related_budgets:
        sections.append("\n## Related Budgets")
        for bname, bdata in related_budgets.items():
            sections.append(f"\n### {bname}")
            if isinstance(bdata, dict):
                for k, v in bdata.items():
                    sections.append(f"- {k}: {v}")

    return "\n".join(sections)


def build_review_context(
    study: dict[str, Any],
    elements: list[dict] | None = None,
    budgets: dict[str, Any] | None = None,
    requirements: list[dict] | None = None,
    interfaces: list[dict] | None = None,
    conops: dict[str, Any] | None = None,
    conflicts: list[dict] | None = None,
    max_elements: int = 200,
) -> str:
    """Serialize complete design state for CDR-quality review.

    This is the most comprehensive context — used for consistency checking
    and full design reviews.  Includes interfaces and ConOps on top of
    the standard study context.
    """
    # Start with full study context
    base = build_study_context(study, elements, budgets, requirements, max_elements)
    sections = [base]

    # Interfaces
    if interfaces:
        sections.append(f"\n## Interfaces ({len(interfaces)})")
        for ifc in interfaces[:30]:
            src = ifc.get("source_name", ifc.get("source_id", "?"))
            tgt = ifc.get("target_name", ifc.get("target_id", "?"))
            itype = ifc.get("type", "?")
            sections.append(f"- {src} -> {tgt} [{itype}]")

    # ConOps modes
    if conops:
        modes = conops.get("modes", [])
        if modes:
            sections.append(f"\n## Operational Modes ({len(modes)})")
            for mode in modes:
                mname = mode.get("name", "?")
                power = mode.get("power_w", "?")
                data = mode.get("data_rate_mbps", "?")
                sections.append(f"- {mname}: {power} W, {data} Mbps")

    # Known conflicts
    if conflicts:
        sections.append(f"\n## Known Conflicts ({len(conflicts)})")
        for c in conflicts:
            sev = c.get("severity", "?")
            desc = c.get("description", "?")
            sections.append(f"- [{sev}] {desc}")

    return "\n".join(sections)
