"""SpaceCDF — Bill of Materials (BOM) Generator.

Generates a procurement-ready BOM from the element tree (primary) or
selected components (fallback). Includes component details, quantities,
pricing, lead times, export control, model level, and procurement status.

Groups by segment → subsystem → component (matching PBS structure).
Outputs JSON, CSV, or docx table.
"""
from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Any


# ─── Element-tree based BOM (primary) ───

def generate_bom_from_elements(
    elements: list[dict[str, Any]],
    study_name: str = "SpaceCDF Mission",
    form_factor: str = "3U",
    semp_answers: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate BOM from the element tree hierarchy.

    Elements should be the full flat list for a study.
    Groups components by segment → subsystem parent.
    """
    # Build parent lookup
    by_id: dict[str, dict] = {e["id"]: e for e in elements}

    # Classify elements
    segments: dict[str, dict] = {}
    subsystems: dict[str, dict] = {}
    components: list[dict] = []

    for el in elements:
        etype = el.get("element_type", "")
        if etype == "segment":
            segments[el["id"]] = el
        elif etype == "subsystem":
            subsystems[el["id"]] = el
        elif etype == "component":
            components.append(el)

    # Model philosophy from SEMP answers (if provided)
    model_philosophy: dict[str, str] = {}
    if semp_answers and "model_philosophy" in semp_answers:
        model_philosophy = semp_answers["model_philosophy"]  # {domain: "PFM"|"QM+FM"|...}

    # Build BOM lines grouped by subsystem
    groups: dict[str, list[dict]] = {}  # subsystem_name → lines
    total_mass = 0.0
    total_power = 0.0
    total_cost = 0.0
    lines: list[dict] = []
    line_num = 0

    for comp in components:
        line_num += 1
        parent = by_id.get(comp.get("parent_id", ""), {})
        _DOMAIN_LABELS = {
            "power": "EPS", "aocs": "AOCS", "ttc": "TTC", "obc": "OBC",
            "thermal": "Thermal", "structure": "Structure", "propulsion": "Propulsion",
            "payload": "Payload", "ground_rf": "Ground RF", "ground_ops": "Ground Ops",
        }
        subsys_name = parent.get("name") or _DOMAIN_LABELS.get(comp.get("subsystem_domain", ""), "Unassigned")
        domain = comp.get("subsystem_domain") or parent.get("subsystem_domain", "")
        segment = comp.get("segment", "space")

        mass = (comp.get("mass_kg") or 0) * (comp.get("quantity") or 1)
        power = (comp.get("power_avg_w") or 0) * (comp.get("quantity") or 1)
        cost = (comp.get("cost_recurring_keur") or 0) * (comp.get("quantity") or 1)

        # Determine model level from TRL and SEMP answers
        trl = comp.get("trl") or 0
        model_level = model_philosophy.get(domain, _default_model_level(trl))

        line = {
            "line": line_num,
            "item_id": comp.get("kb_component_id") or comp["id"][:12],
            "name": comp.get("name", ""),
            "subsystem": subsys_name,
            "subsystem_domain": domain,
            "segment": segment,
            "quantity": comp.get("quantity") or 1,
            "unit_mass_kg": comp.get("mass_kg") or 0,
            "total_mass_kg": round(mass, 4),
            "unit_power_w": comp.get("power_avg_w") or 0,
            "total_power_w": round(power, 2),
            "unit_cost_keur": comp.get("cost_recurring_keur") or 0,
            "total_cost_keur": round(cost, 1),
            "trl": trl,
            "manufacturer": comp.get("manufacturer") or "",
            "model_level": model_level,
            "procurement_status": _assess_procurement_status(comp),
            "export_control": _assess_export(comp),
            "lead_time_weeks": _estimate_lead_time(comp),
            "criticality": _assess_criticality(comp),
            "heritage": comp.get("heritage_missions") if isinstance(comp.get("heritage_missions"), list) else [],
            "maturity": _assess_maturity(comp),
        }
        lines.append(line)
        total_mass += mass
        total_power += power
        total_cost += cost

        if subsys_name not in groups:
            groups[subsys_name] = []
        groups[subsys_name].append(line)

    # Add standard hardware
    std_items = _standard_hardware(form_factor)
    for item in std_items:
        line_num += 1
        item_mass = item["mass_kg"] * item["qty"]
        item_cost = item["cost_keur"] * item["qty"]
        line = {
            "line": line_num,
            "item_id": item["id"],
            "name": item["name"],
            "subsystem": "Standard Hardware",
            "subsystem_domain": "integration",
            "segment": "space",
            "quantity": item["qty"],
            "unit_mass_kg": item["mass_kg"],
            "total_mass_kg": round(item_mass, 4),
            "unit_power_w": 0,
            "total_power_w": 0,
            "unit_cost_keur": item["cost_keur"],
            "total_cost_keur": round(item_cost, 1),
            "trl": 9,
            "manufacturer": "Various",
            "model_level": "FM",
            "procurement_status": "available",
            "export_control": "none",
            "lead_time_weeks": 4,
            "criticality": "standard",
            "heritage": [],
            "maturity": "specified",
        }
        lines.append(line)
        total_mass += item_mass
        total_cost += item_cost
        if "Standard Hardware" not in groups:
            groups["Standard Hardware"] = []
        groups["Standard Hardware"].append(line)

    # Summary
    max_lead = max((l["lead_time_weeks"] for l in lines), default=0)
    itar_items = [l for l in lines if l["export_control"] in ("ITAR", "EAR")]
    low_trl = [l for l in lines if l["trl"] < 7 and l["trl"] > 0]

    return {
        "title": f"Bill of Materials — {study_name}",
        "generated": datetime.now(timezone.utc).isoformat(),
        "form_factor": form_factor,
        "groups": {name: group_lines for name, group_lines in groups.items()},
        "lines": lines,
        "summary": {
            "total_lines": len(lines),
            "total_components": len(components),
            "total_standard_hw": len(std_items),
            "total_mass_kg": round(total_mass, 3),
            "total_power_w": round(total_power, 2),
            "total_cost_keur": round(total_cost, 1),
            "total_cost_eur": round(total_cost * 1000, 0),
            "subsystem_count": len(groups),
            "completeness_percent": _calc_completeness(subsystems, components),
            "critical_path_weeks": max_lead,
            "itar_items": len(itar_items),
            "low_trl_items": len(low_trl),
            "mean_trl": round(sum(l["trl"] for l in lines if l["trl"] > 0) / max(len([l for l in lines if l["trl"] > 0]), 1), 1),
        },
        "procurement_notes": _procurement_notes(lines, [], itar_items),
        "segment_totals": _segment_totals(lines),
    }


def bom_to_csv(bom: dict[str, Any]) -> str:
    """Convert BOM to CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Line", "Item ID", "Name", "Subsystem", "Segment", "Qty",
        "Unit Mass (kg)", "Total Mass (kg)", "Unit Power (W)", "Total Power (W)",
        "Unit Cost (kEUR)", "Total Cost (kEUR)", "TRL", "Manufacturer",
        "Model Level", "Procurement", "Export Control", "Lead Time (wk)", "Criticality",
    ])
    for line in bom.get("lines", []):
        writer.writerow([
            line["line"], line["item_id"], line["name"], line["subsystem"],
            line["segment"], line["quantity"],
            line["unit_mass_kg"], line["total_mass_kg"],
            line["unit_power_w"], line["total_power_w"],
            line["unit_cost_keur"], line["total_cost_keur"],
            line["trl"], line["manufacturer"],
            line["model_level"], line["procurement_status"],
            line["export_control"], line["lead_time_weeks"], line["criticality"],
        ])
    return output.getvalue()


def bom_to_svg_table(bom: dict[str, Any]) -> str:
    """Generate an SVG table visualization of the BOM summary by subsystem."""
    groups = bom.get("groups", {})
    summary = bom.get("summary", {})

    row_h = 28
    header_h = 35
    pad = 12
    col_widths = [180, 60, 80, 80, 80, 50]  # name, items, mass, power, cost, TRL
    total_w = sum(col_widths) + pad * 2
    num_rows = len(groups) + 1  # +1 for totals
    total_h = header_h + row_h * num_rows + pad * 2 + 30  # +30 for title

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" style="font-family:Inter,sans-serif;font-size:11px;">']
    svg.append(f'<rect width="{total_w}" height="{total_h}" fill="#0f172a" rx="6"/>')

    # Title
    svg.append(f'<text x="{total_w/2}" y="22" text-anchor="middle" fill="#d1d5db" font-size="13" font-weight="600">{bom.get("title", "BOM")}</text>')

    y0 = 35
    # Header
    headers = ["Subsystem", "Items", "Mass (kg)", "Power (W)", "Cost (kEUR)", "TRL"]
    x = pad
    for i, h in enumerate(headers):
        svg.append(f'<text x="{x + 4}" y="{y0 + 18}" fill="#9ca3af" font-size="9" font-weight="600">{h}</text>')
        x += col_widths[i]
    svg.append(f'<line x1="{pad}" y1="{y0 + header_h - 5}" x2="{total_w - pad}" y2="{y0 + header_h - 5}" stroke="#374151" stroke-width="1"/>')

    # Rows
    y = y0 + header_h
    for name, group_lines in groups.items():
        g_mass = sum(l["total_mass_kg"] for l in group_lines)
        g_power = sum(l["total_power_w"] for l in group_lines)
        g_cost = sum(l["total_cost_keur"] for l in group_lines)
        g_trl = round(sum(l["trl"] for l in group_lines if l["trl"] > 0) / max(len([l for l in group_lines if l["trl"] > 0]), 1), 0)
        # Alternating row bg
        if list(groups.keys()).index(name) % 2 == 0:
            svg.append(f'<rect x="{pad}" y="{y}" width="{total_w - pad*2}" height="{row_h}" fill="rgba(255,255,255,0.02)" rx="2"/>')
        x = pad
        vals = [name[:22], str(len(group_lines)), f"{g_mass:.2f}", f"{g_power:.1f}", f"{g_cost:.0f}", f"{g_trl:.0f}"]
        for i, v in enumerate(vals):
            svg.append(f'<text x="{x + 4}" y="{y + 18}" fill="#d1d5db">{v}</text>')
            x += col_widths[i]
        y += row_h

    # Totals row
    svg.append(f'<line x1="{pad}" y1="{y}" x2="{total_w - pad}" y2="{y}" stroke="#374151" stroke-width="1"/>')
    x = pad
    tot_vals = ["TOTAL", str(summary.get("total_lines", 0)),
                f"{summary.get('total_mass_kg', 0):.2f}",
                f"{summary.get('total_power_w', 0):.1f}",
                f"{summary.get('total_cost_keur', 0):.0f}",
                f"{summary.get('mean_trl', 0):.0f}"]
    for i, v in enumerate(tot_vals):
        svg.append(f'<text x="{x + 4}" y="{y + 18}" fill="#10b981" font-weight="600">{v}</text>')
        x += col_widths[i]

    svg.append('</svg>')
    return '\n'.join(svg)


# ─── Legacy flat-component BOM (fallback) ───

def generate_bom(
    selected_components: dict[str, dict[str, Any]],
    form_factor: str = "3U",
    mission_duration_years: float = 3.0,
) -> dict[str, Any]:
    """Generate a BOM from selected components (legacy flat format)."""
    lines: list[dict[str, Any]] = []
    total_mass_kg = 0.0
    total_cost_keur = 0.0
    categories_covered: list[str] = []
    categories_missing: list[str] = []

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

    max_lead_time = max((l["lead_time_weeks"] for l in lines), default=0)
    itar_items = [l for l in lines if l["export_control"] in ("ITAR", "EAR")]

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


# ─── Helpers ───

def _default_model_level(trl: int) -> str:
    """Default model approach based on TRL per ECSS conventions."""
    if trl >= 9:
        return "PFM"      # Protoflight — flight-proven COTS
    elif trl >= 7:
        return "QM+FM"    # Qualification + Flight
    elif trl >= 5:
        return "EM+QM+FM" # Engineering + Qualification + Flight
    else:
        return "BB+EM+QM+FM"  # Breadboard + Engineering + Qual + Flight


def _assess_procurement_status(comp: dict) -> str:
    """Assess procurement status from component metadata."""
    if comp.get("kb_component_id"):
        return "catalogue"  # In KB = available from vendor
    elif comp.get("manufacturer"):
        return "identified"  # Custom but vendor known
    else:
        return "tbd"  # Needs selection


def _assess_criticality(comp: dict) -> str:
    """Assess component criticality."""
    redundancy = comp.get("redundancy_type")
    if redundancy and redundancy != "none":
        return "redundant"
    # Single-string items in critical subsystems
    domain = comp.get("subsystem_domain", "")
    if domain in ("obc", "power", "ttc"):
        return "single-point"
    return "standard"


def _assess_maturity(comp: dict) -> str:
    """Quick maturity assessment for BOM line items."""
    if comp.get("kb_component_id") and comp.get("mass_kg") and comp.get("manufacturer"):
        return "specified"
    elif comp.get("kb_component_id"):
        return "selected"
    elif comp.get("mass_kg"):
        return "estimated"
    return "parametric"


def _calc_completeness(subsystems: dict, components: list) -> float:
    """Calculate BOM completeness as % of subsystems with at least one component."""
    if not subsystems:
        return 0
    covered = set()
    for comp in components:
        pid = comp.get("parent_id")
        if pid and pid in subsystems:
            covered.add(pid)
    return round(len(covered) / max(len(subsystems), 1) * 100, 0)


def _segment_totals(lines: list[dict]) -> dict[str, dict]:
    """Compute mass/power/cost totals per segment."""
    totals: dict[str, dict] = {}
    for line in lines:
        seg = line.get("segment", "space")
        if seg not in totals:
            totals[seg] = {"mass_kg": 0, "power_w": 0, "cost_keur": 0, "items": 0}
        totals[seg]["mass_kg"] += line["total_mass_kg"]
        totals[seg]["power_w"] += line.get("total_power_w", 0)
        totals[seg]["cost_keur"] += line["total_cost_keur"]
        totals[seg]["items"] += 1
    # Round
    for seg in totals:
        totals[seg]["mass_kg"] = round(totals[seg]["mass_kg"], 3)
        totals[seg]["power_w"] = round(totals[seg]["power_w"], 2)
        totals[seg]["cost_keur"] = round(totals[seg]["cost_keur"], 1)
    return totals


def _default_quantity(category: str, form_factor: str) -> int:
    multiples: dict[str, Any] = {
        "sun_sensors": 6,
        "magnetorquers": 3,
        "solar_panels": {"1U": 5, "3U": 2, "6U": 2}.get(form_factor, 2),
        "antennas": 1,
        "deployment_switches": 4,
    }
    return multiples.get(category, 1)


def _estimate_lead_time(comp: dict) -> int:
    trl = comp.get("trl", 5)
    if trl >= 9:
        return 8
    elif trl >= 7:
        return 16
    else:
        return 26


def _assess_export(comp: dict) -> str:
    manufacturer = (comp.get("manufacturer") or "").lower()
    us_manufacturers = {"mma design", "pumpkin", "blue canyon", "busek", "phase four", "novatel"}
    if any(m in manufacturer for m in us_manufacturers):
        return "EAR"
    return "none"


def _standard_hardware(form_factor: str) -> list[dict]:
    return [
        {"id": "hw-harness", "name": "Internal harness assembly", "category": "harness",
         "mass_kg": 0.1 if form_factor in ("1U", "3U") else 0.25, "cost_keur": 2, "qty": 1},
        {"id": "hw-fasteners", "name": "Fastener kit (M3 screws, standoffs, spacers)", "category": "fasteners",
         "mass_kg": 0.05, "cost_keur": 0.5, "qty": 1},
        {"id": "hw-thermal", "name": "Thermal hardware (MLI, tape, thermistors)", "category": "thermal_hardware",
         "mass_kg": 0.05, "cost_keur": 1, "qty": 1},
        {"id": "hw-sep-switch", "name": "Deployment switches (microswitches)", "category": "mechanisms",
         "mass_kg": 0.01, "cost_keur": 0.5, "qty": 4},
        {"id": "hw-rbf-flags", "name": "Remove Before Flight flags & pins", "category": "ground_support",
         "mass_kg": 0.01, "cost_keur": 0.1, "qty": 4},
    ]


def _procurement_notes(lines: list, missing: list, itar: list) -> list[str]:
    notes = []
    if missing:
        notes.append(f"WARNING: {len(missing)} categories not yet selected: {', '.join(missing)}")
    if itar:
        notes.append(f"EXPORT CONTROL: {len(itar)} item(s) may be subject to US EAR — verify before international procurement")
    max_lt = max((l["lead_time_weeks"] for l in lines), default=0)
    if max_lt > 12:
        notes.append(f"SCHEDULE: Critical path component has {max_lt}-week lead time — order immediately")
    low_trl = [l for l in lines if l.get("trl", 9) < 7 and l.get("trl", 0) > 0]
    if low_trl:
        names = [l["name"] for l in low_trl]
        notes.append(f"TRL RISK: {len(low_trl)} component(s) below TRL 7: {', '.join(names)} — qualification needed")
    notes.append("All prices are estimates. Request formal quotations from vendors before commitment.")
    notes.append("Lead times are typical — confirm with vendor for current availability.")
    return notes
