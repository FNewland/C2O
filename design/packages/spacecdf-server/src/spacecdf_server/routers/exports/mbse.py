"""SpaceCDF export family: mbse.

ECSS-E-TM-10-25A style MBSE JSON export with functional/logical/physical architecture, allocations and traceability.
Routes (prefix /api/exports): POST /mbse/{study_id}

Moved verbatim from the single routers/exports.py in W0.1 (no behaviour change).
See design/docs/dev/W0_SEAMS.md for the module map and file ownership.
"""
from __future__ import annotations


from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ..studies import get_study_store
from . import _common

router = APIRouter()

def _derive_functional_architecture(study) -> list[dict]:
    """Derive functional architecture from study's functional decomposition or objectives."""
    func_decomp = getattr(study, "functional_decomposition", None)
    if func_decomp and func_decomp.functions:
        return [
            {
                "id": f.id,
                "name": f.name,
                "type": f.function_type.value if hasattr(f.function_type, "value") else str(f.function_type),
                "description": f.description,
                "parent_id": f.parent_function_id,
                "objective_ids": f.objective_ids,
                "derived_requirement_ids": f.derived_requirement_ids,
            }
            for f in func_decomp.functions
        ]
    # Fallback: generate generic functions from mission need objectives
    mission_need = getattr(study, "mission_need", None)
    objectives = getattr(mission_need, "objectives", []) if mission_need else []
    generic_functions = [
        {"id": "fn_acquire", "name": "Acquire data", "type": "observe",
         "description": "Collect mission data using payload instruments"},
        {"id": "fn_process", "name": "Process data", "type": "process",
         "description": "Onboard data processing and compression"},
        {"id": "fn_store", "name": "Store data", "type": "store",
         "description": "Buffer data between acquisition and downlink"},
        {"id": "fn_downlink", "name": "Downlink data", "type": "communicate",
         "description": "Transmit data to ground segment"},
        {"id": "fn_attitude", "name": "Maintain attitude", "type": "point",
         "description": "Attitude determination and control"},
        {"id": "fn_power", "name": "Generate power", "type": "power",
         "description": "Solar energy conversion, storage, and distribution"},
        {"id": "fn_thermal", "name": "Control thermal environment", "type": "protect",
         "description": "Maintain component temperatures within limits"},
        {"id": "fn_navigate", "name": "Navigate and manoeuvre", "type": "navigate",
         "description": "Orbit determination, station-keeping, collision avoidance"},
    ]
    # Link to objectives if present
    for i, obj in enumerate(objectives):
        obj_id = getattr(obj, "id", f"OBJ-{i+1}")
        if i < len(generic_functions):
            generic_functions[i]["objective_ids"] = [obj_id]
    return generic_functions


def _derive_logical_architecture(elements: list[dict], functions: list[dict]) -> list[dict]:
    """Map functions to systems/subsystems from element tree."""
    # Build domain → elements mapping
    domain_elements: dict[str, list[str]] = {}
    for e in elements:
        domain = e.get("subsystem_domain", "")
        if domain and e.get("segment") == "space":
            domain_elements.setdefault(domain, []).append(e.get("name", ""))

    function_to_domain = {
        "observe": ["payload"],
        "communicate": ["ttc"],
        "navigate": ["aocs", "propulsion"],
        "point": ["aocs"],
        "power": ["eps", "power"],
        "protect": ["thermal", "structure", "structures"],
        "process": ["obc", "obdh"],
        "store": ["obc", "obdh"],
        "propel": ["propulsion"],
        "support": ["structure", "structures"],
        "command": ["obc", "ttc"],
        "dispose": ["propulsion"],
    }

    mappings = []
    for func in functions:
        ftype = func.get("type", "")
        candidate_domains = function_to_domain.get(ftype, [])
        allocated_elements = []
        for d in candidate_domains:
            allocated_elements.extend(domain_elements.get(d, []))
        mappings.append({
            "function_id": func["id"],
            "function_name": func["name"],
            "allocated_domains": candidate_domains,
            "allocated_elements": allocated_elements,
        })
    return mappings


def _derive_physical_architecture(elements: list[dict]) -> list[dict]:
    """Return element tree with parent/child relationships."""
    element_map = {e.get("id"): e for e in elements if e.get("id")}
    tree = []
    for e in elements:
        children = [
            c.get("name", "") for c in elements
            if c.get("parent_element_id") == e.get("id")
        ]
        tree.append({
            "id": e.get("id", ""),
            "name": e.get("name", ""),
            "element_type": e.get("element_type", ""),
            "segment": e.get("segment", ""),
            "subsystem_domain": e.get("subsystem_domain", ""),
            "parent_id": e.get("parent_element_id", ""),
            "parent_name": element_map.get(e.get("parent_element_id", ""), {}).get("name", ""),
            "children": children,
            "mass_kg": e.get("mass_kg"),
            "power_avg_w": e.get("power_avg_w"),
            "quantity": e.get("quantity", 1),
        })
    return tree


def _derive_allocation_matrix(requirements: list[dict], elements: list[dict]) -> list[dict]:
    """Build requirements-to-elements allocation matrix from element_id FK."""
    element_map = {e.get("id"): e.get("name", "") for e in elements if e.get("id")}
    allocations = []
    for r in requirements:
        element_id = r.get("element_id", "")
        allocations.append({
            "requirement_code": r.get("code", r.get("id", "")),
            "requirement_text": r.get("text", ""),
            "level": r.get("level", ""),
            "element_id": element_id,
            "element_name": element_map.get(element_id, "unallocated"),
            "verification_method": r.get("verification_method", ""),
        })
    return allocations


def _derive_traceability(study, requirements: list[dict], elements: list[dict]) -> list[dict]:
    """Build objective -> requirement -> element -> verification chain."""
    mission_need = getattr(study, "mission_need", None)
    objectives = getattr(mission_need, "objectives", []) if mission_need else []

    element_map = {e.get("id"): e.get("name", "") for e in elements if e.get("id")}
    chains = []

    for obj in objectives:
        obj_id = getattr(obj, "id", "")
        obj_text = getattr(obj, "text", "")
        # Find requirements that trace to this objective (by parent or tag)
        linked_reqs = [
            r for r in requirements
            if r.get("parent_objective_id") == obj_id
            or obj_id in r.get("objective_ids", [])
            or obj_text.lower()[:20] in r.get("text", "").lower()
        ]
        if not linked_reqs:
            # Fallback: all system-level requirements
            linked_reqs = [r for r in requirements if r.get("level") in ("mission", "system")]

        for r in linked_reqs:
            element_id = r.get("element_id", "")
            chains.append({
                "objective_id": obj_id,
                "objective_text": obj_text,
                "requirement_code": r.get("code", r.get("id", "")),
                "requirement_text": r.get("text", ""),
                "element_id": element_id,
                "element_name": element_map.get(element_id, "unallocated"),
                "verification_method": r.get("verification_method", ""),
            })

    return chains


@router.post("/mbse/{study_id}")
async def export_mbse(study_id: str) -> JSONResponse:
    """Generate an ECSS-E-TM-10-25A-style MBSE JSON export.

    Research-credibility artefact: SysML-like model with blocks, parameters,
    requirements, traceability links, and applicable ECSS standards.
    Suitable for import into Cameo / Capella via a downstream converter and
    for archival in version control (diff-friendly JSON).
    """
    studies = get_study_store()
    study = studies.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")

    state, requirements, _ = await _common._run_design_for_study(study_id)

    # Auto-generate requirements from the mission baseline when the study
    # hasn't been augmented with explicit ones.
    from spacecdf_common.models.requirements import generate_requirements
    req_objects = generate_requirements(requirements.model_dump())

    # Pull applicable ECSS from the originating template when present
    applicable_ecss: list[str] = []
    notes = getattr(study, "notes", "") or ""
    if "Seeded from template:" in notes:
        tmpl_id = notes.split("Seeded from template:")[1].strip().split()[0]
        try:
            from ...services.template_library import get_template
            tmpl = get_template(tmpl_id)
            if tmpl:
                applicable_ecss = list(tmpl.applicable_ecss)
        except Exception:
            pass

    from spacecdf_agents.exporters.mbse import generate_mbse_export

    phase = study.phase.value if hasattr(study.phase, "value") else str(study.phase)
    export = generate_mbse_export(
        study_id=study.id,
        study_name=study.name,
        phase=phase,
        parameters=state.parameters,
        requirements=req_objects,
        applicable_standards=applicable_ecss,
        notes=notes,
    )

    # ── MBSE Enrichments: functional / logical / physical arch, allocations, traceability ──
    elements: list[dict] = []
    interfaces: list[dict] = []
    req_dicts: list[dict] = []
    try:
        from ..elements import _elements, _interfaces
        elements = [e for e in _elements.values()
                    if e.get("study_id") == study_id and not e.get("deleted_at")]
        interfaces = [
            i for i in _interfaces.values()
            if not i.get("deleted_at") and i.get("status") != "rejected" and (
                i.get("study_id") == study_id
                or i.get("source_element_id") in {e.get("id") for e in elements}
                or i.get("target_element_id") in {e.get("id") for e in elements}
            )
        ]
    except Exception:
        pass
    try:
        from ..requirements import _requirements
        req_dicts = [r for r in _requirements.values()
                     if r.get("study_id") == study_id and r.get("status") != "retired"]
    except Exception:
        pass

    functional_architecture = _derive_functional_architecture(study)
    logical_architecture = _derive_logical_architecture(elements, functional_architecture)
    physical_architecture = _derive_physical_architecture(elements)

    # Interface definitions from the interface store
    interface_definitions = []
    element_map = {e.get("id"): e.get("name", "") for e in elements if e.get("id")}
    for iface in interfaces:
        interface_definitions.append({
            "id": iface.get("id", ""),
            "source_element_id": iface.get("source_element_id", ""),
            "source_name": element_map.get(iface.get("source_element_id", ""),
                                           iface.get("source_name", "")),
            "target_element_id": iface.get("target_element_id", ""),
            "target_name": element_map.get(iface.get("target_element_id", ""),
                                           iface.get("target_name", "")),
            "interface_type": iface.get("interface_type", iface.get("type", "")),
            "properties": iface.get("properties", {}),
            "direction": iface.get("direction", "bidirectional"),
        })

    # Also include subsystem-level interfaces from study's InterfaceMatrix
    interface_matrix = getattr(study, "interface_matrix", None)
    if interface_matrix:
        for si in getattr(interface_matrix, "subsystem_interfaces", []):
            interface_definitions.append({
                "id": f"{si.subsystem_a}_{si.subsystem_b}",
                "source_name": si.subsystem_a,
                "target_name": si.subsystem_b,
                "interface_type": [it.value if hasattr(it, "value") else str(it)
                                   for it in getattr(si, "interface_types", [])],
                "status": si.status.value if hasattr(si.status, "value") else str(si.status),
                "criticality": getattr(si, "criticality", "standard"),
                "description": getattr(si, "description", ""),
            })

    allocation_matrix = _derive_allocation_matrix(req_dicts, elements)
    traceability = _derive_traceability(study, req_dicts, elements)

    export["functional_architecture"] = functional_architecture
    export["logical_architecture"] = logical_architecture
    export["physical_architecture"] = physical_architecture
    export["interface_definitions"] = interface_definitions
    export["allocation_matrix"] = allocation_matrix
    export["traceability"] = traceability

    return JSONResponse(content=export)
