"""SpaceCDF — Bill of Materials (BOM) Generator.

Generates a procurement-ready BOM from selected components across all
subsystems. Includes component details, quantities, pricing, lead times,
export control status, and harness/structural hardware estimates.

Part of Stage 2: CubeSat full lifecycle capability.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def generate_bom(
    selected_components: dict[str, dict[str, Any]],
    form_factor: str = "3U",
    mission_duration_years: float = 3.0,
) -> dict[str, Any]:
    """Generate a Bill of Materials from selected components.

    Args:
        selected_components: {category: component_dict} — one selected
            component per KB category.
        form_factor: CubeSat form factor for structural hardware estimate.
        mission_duration_years: For spares estimation.

    Returns:
        Structured BOM with line items, totals, and procurement summary.
    """
    lines: list[dict[str, Any]] = []
    total_mass_kg = 0.0
    total_cost_keur = 0.0
    categories_covered: list[str] = []
    categories_missing: list[str] = []

    # Expected categories for a complete CubeSat
    expected_categories = [
        "batteries", "eps_boards", "solar_panels", "obcs",
        "reaction_wheels", "star_trackers", "sun_sensors", "magnetorquers",
        "transponders", "antennas", "thrusters", "cubesat_structures",
        "gps_receivers",
    ]

    for category in expected_categories:
        comp = selected_components.get(category)
        if comp is None:
            categories_missing.append(category)
            continue

        categories_covered.append(category)
        mass = comp.get("mass_kg", 0)
        cost = comp.get("cost_keur", 0)

        # Quantity — some items need multiples
        qty = _default_quantity(category, form_factor)
        line_mass = mass * qty
        line_cost = cost * qty

        lines.append({
            "line": len(lines) + 1,
            "category": category,
            "component_id": comp.get("id", ""),
            "name": comp.get("name", ""),
            "manufacturer": comp.get("manufacturer", ""),
            "quantity": qty,
            "unit_mass_kg": mass,
            "total_mass_kg": round(line_mass, 4),
            "unit_cost_keur": cost,
            "total_cost_keur": round(line_cost, 1),
            "trl": comp.get("trl", 0),
            "lead_time_weeks": _estimate_lead_time(comp),
            "export_control": _assess_export(comp),
            "interfaces": comp.get("interfaces", []),
            "heritage": comp.get("heritage_missions", []),
        })
        total_mass_kg += line_mass
        total_cost_keur += line_cost

    # Add standard hardware not in component DB
    standard_items = _standard_hardware(form_factor)
    for item in standard_items:
        lines.append({
            "line": len(lines) + 1,
            "category": item["category"],
            "component_id": item["id"],
            "name": item["name"],
            "manufacturer": "Various",
            "quantity": item["qty"],
            "unit_mass_kg": item["mass_kg"],
            "total_mass_kg": round(item["mass_kg"] * item["qty"], 4),
            "unit_cost_keur": item["cost_keur"],
            "total_cost_keur": round(item["cost_keur"] * item["qty"], 1),
            "trl": 9,
            "lead_time_weeks": 4,
            "export_control": "none",
            "interfaces": [],
            "heritage": [],
        })
        total_mass_kg += item["mass_kg"] * item["qty"]
        total_cost_keur += item["cost_keur"] * item["qty"]

    # Procurement summary
    max_lead_time = max((l["lead_time_weeks"] for l in lines), default=0)
    itar_items = [l for l in lines if l["export_control"] == "ITAR"]

    return {
        "title": f"SpaceCDF Bill of Materials — {form_factor} CubeSat",
        "generated": datetime.now(timezone.utc).isoformat(),
        "form_factor": form_factor,
        "lines": lines,
        "summary": {
            "total_lines": len(lines),
            "total_mass_kg": round(total_mass_kg, 3),
            "total_cost_keur": round(total_cost_keur, 1),
            "total_cost_eur": round(total_cost_keur * 1000, 0),
            "categories_covered": len(categories_covered),
            "categories_missing": categories_missing,
            "completeness_percent": round(len(categories_covered) / len(expected_categories) * 100, 0),
            "critical_path_weeks": max_lead_time,
            "itar_items": len(itar_items),
            "mean_trl": round(sum(l["trl"] for l in lines) / max(len(lines), 1), 1),
        },
        "procurement_notes": _procurement_notes(lines, categories_missing, itar_items),
    }


def _default_quantity(category: str, form_factor: str) -> int:
    """Default quantity per category based on CubeSat design practices."""
    multiples = {
        "sun_sensors": 6,          # 6x for full sphere coverage
        "magnetorquers": 3,        # 3-axis
        "solar_panels": {"1U": 5, "3U": 2, "6U": 2}.get(form_factor, 2),
        "antennas": 1,
        "deployment_switches": 4,
    }
    return multiples.get(category, 1)


def _estimate_lead_time(comp: dict) -> int:
    """Estimate procurement lead time in weeks."""
    trl = comp.get("trl", 5)
    if trl >= 9:
        return 8   # Flight-proven COTS — typically 8-12 weeks
    elif trl >= 7:
        return 16  # Qualified but less available
    else:
        return 26  # May need custom build/qualification


def _assess_export(comp: dict) -> str:
    """Simple export control assessment."""
    manufacturer = comp.get("manufacturer", "").lower()
    # US-origin items may be subject to ITAR/EAR
    us_manufacturers = {"mma design", "pumpkin", "blue canyon", "busek", "phase four", "novatel"}
    if any(m in manufacturer for m in us_manufacturers):
        return "EAR"  # Export Administration Regulations (likely)
    return "none"


def _standard_hardware(form_factor: str) -> list[dict]:
    """Standard hardware items not in the component database."""
    items = [
        {"id": "hw-harness", "name": "Internal harness assembly", "category": "harness",
         "mass_kg": 0.1 if form_factor in ("1U", "3U") else 0.25, "cost_keur": 2, "qty": 1},
        {"id": "hw-fasteners", "name": "Fastener kit (M3 screws, standoffs, spacers)", "category": "fasteners",
         "mass_kg": 0.05, "cost_keur": 0.5, "qty": 1},
        {"id": "hw-thermal", "name": "Thermal hardware (MLI, tape, thermistors)", "category": "thermal_hardware",
         "mass_kg": 0.05, "cost_keur": 1, "qty": 1},
        {"id": "hw-sep-switch", "name": "Deployment switches (microswitches)", "category": "mechanisms",
         "mass_kg": 0.01, "cost_keur": 0.5, "qty": 4},
        {"id": "hw-rbe-flags", "name": "Remove Before Flight flags & pins", "category": "ground_support",
         "mass_kg": 0.01, "cost_keur": 0.1, "qty": 4},
    ]
    return items


def _procurement_notes(lines: list, missing: list, itar: list) -> list[str]:
    """Generate procurement notes and warnings."""
    notes = []
    if missing:
        notes.append(f"WARNING: {len(missing)} categories not yet selected: {', '.join(missing)}")
    if itar:
        notes.append(f"EXPORT CONTROL: {len(itar)} item(s) may be subject to US EAR — verify before international procurement")

    max_lt = max((l["lead_time_weeks"] for l in lines), default=0)
    if max_lt > 12:
        notes.append(f"SCHEDULE: Critical path component has {max_lt}-week lead time — order immediately")

    low_trl = [l for l in lines if l["trl"] < 7]
    if low_trl:
        names = [l["name"] for l in low_trl]
        notes.append(f"TRL RISK: {len(low_trl)} component(s) below TRL 7: {', '.join(names)} — qualification needed")

    notes.append("All prices are estimates. Request formal quotations from vendors before commitment.")
    notes.append("Lead times are typical — confirm with vendor for current availability.")
    return notes
