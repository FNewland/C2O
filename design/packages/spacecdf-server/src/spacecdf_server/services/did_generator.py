"""SpaceCDF — ECSS DID (Document Item Description) Generator.

Generates document templates for all major ECSS deliverables.
Each document is populated from the live design state, requirements,
ConOps, and functional decomposition.

References:
  - ECSS-E-ST-10C Annex A — MRD
  - ECSS-E-ST-10-06C — Technical Specification
  - ECSS-E-ST-10-02C — VP / VCD (existing in compliance_generator)
  - ECSS-E-ST-10-24C — IRD
  - ECSS-M-ST-80C — RMP
  - NASA SEH Appendix J — SEMP
  - NASA SEH Appendix S — ConOps
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def generate_mrd(
    *,
    study_name: str,
    mission_need: dict[str, Any],
    requirements: list[dict[str, Any]],
    phase_id: str = "phase_a",
) -> dict[str, Any]:
    """Mission Requirements Document — ECSS-E-ST-10C Annex A."""
    mn = mission_need or {}
    objectives = mn.get("objectives", [])
    stakeholders = mn.get("stakeholders", [])

    # Group requirements by domain
    by_domain: dict[str, list[dict]] = {}
    for r in requirements:
        d = r.get("domain", "systems")
        by_domain.setdefault(d, []).append(r)

    return {
        "document": "Mission Requirements Document (MRD)",
        "standard": "ECSS-E-ST-10C Annex A",
        "study_name": study_name,
        "phase": phase_id,
        "generated": datetime.now(timezone.utc).isoformat(),
        "sections": [
            {
                "number": "1", "title": "Introduction",
                "subsections": [
                    {"number": "1.1", "title": "Purpose", "content": f"This document defines the mission-level requirements for the {study_name} mission."},
                    {"number": "1.2", "title": "Scope", "content": "Covers all mission-level requirements derived from stakeholder needs and mission objectives."},
                    {"number": "1.3", "title": "Applicable Documents", "content": "ECSS-E-ST-10C Rev.1, ECSS-M-ST-10C Rev.1"},
                    {"number": "1.4", "title": "Reference Documents", "content": ""},
                ],
            },
            {
                "number": "2", "title": "Mission Overview",
                "subsections": [
                    {"number": "2.1", "title": "Problem Statement", "content": mn.get("problem_statement", "TBD")},
                    {"number": "2.2", "title": "Mission Objectives",
                     "content": "\n".join(f"- [{o.get('priority', 'primary').upper()}] {o.get('text', '')}" for o in objectives) or "TBD"},
                    {"number": "2.3", "title": "Stakeholders",
                     "content": "\n".join(f"- {s.get('name', '')}: {s.get('role', '')}" for s in stakeholders) or "TBD"},
                    {"number": "2.4", "title": "Mission Success Criteria",
                     "content": "\n".join(f"- {o.get('measurable_criterion', 'TBD')}" for o in objectives if o.get("measurable_criterion")) or "TBD"},
                ],
            },
            {
                "number": "3", "title": "Mission Requirements",
                "subsections": [
                    {"number": f"3.{i+1}", "title": f"{domain.replace('_', ' ').title()} Requirements",
                     "content": "\n".join(f"- [{r.get('id', '')}] {r.get('text', '')}" for r in reqs)}
                    for i, (domain, reqs) in enumerate(by_domain.items())
                ],
            },
            {
                "number": "4", "title": "Constraints",
                "subsections": [
                    {"number": "4.1", "title": "Programmatic Constraints", "content": "TBD — budget, schedule, launch date"},
                    {"number": "4.2", "title": "Technical Constraints", "content": "TBD — orbit, mass, interfaces"},
                    {"number": "4.3", "title": "Regulatory Constraints", "content": "Space debris mitigation per ECSS-U-AS-10C Rev.2, ITU frequency coordination"},
                ],
            },
            {
                "number": "5", "title": "Verification Approach",
                "subsections": [
                    {"number": "5.1", "title": "Verification Methods", "content": "Analysis, Test, Review, Inspection per ECSS-E-ST-10-02C"},
                    {"number": "5.2", "title": "Verification Matrix", "content": "See Verification Plan (VP) document"},
                ],
            },
        ],
        "total_requirements": len(requirements),
        "requirements_by_domain": {d: len(r) for d, r in by_domain.items()},
    }


def generate_technical_specification(
    *,
    study_name: str,
    requirements: list[dict[str, Any]],
    design_params: dict[str, Any],
    phase_id: str = "phase_a",
) -> dict[str, Any]:
    """Technical Specification — ECSS-E-ST-10-06C."""
    return {
        "document": "Technical Specification (TS)",
        "standard": "ECSS-E-ST-10-06C",
        "study_name": study_name,
        "phase": phase_id,
        "generated": datetime.now(timezone.utc).isoformat(),
        "sections": [
            {
                "number": "1", "title": "Introduction",
                "subsections": [
                    {"number": "1.1", "title": "Purpose", "content": f"Technical specification for {study_name}."},
                    {"number": "1.2", "title": "Scope", "content": "System-level technical requirements and design constraints."},
                ],
            },
            {
                "number": "2", "title": "System Description",
                "subsections": [
                    {"number": "2.1", "title": "System Architecture", "content": "See ConOps document for mission architecture."},
                    {"number": "2.2", "title": "Functional Description", "content": "See Functional Decomposition."},
                ],
            },
            {
                "number": "3", "title": "Technical Requirements",
                "subsections": [
                    {"number": "3.1", "title": "Performance Requirements",
                     "content": "\n".join(f"- [{r.get('id','')}] {r.get('text','')}" for r in requirements if r.get('category') == 'performance') or "See MRD"},
                    {"number": "3.2", "title": "Interface Requirements", "content": "See IRD"},
                    {"number": "3.3", "title": "Environmental Requirements", "content": "Per ECSS-E-ST-10-04C"},
                    {"number": "3.4", "title": "Design Constraints", "content": "TBD"},
                ],
            },
            {
                "number": "4", "title": "Design Budgets",
                "subsections": [
                    {"number": "4.1", "title": "Mass Budget",
                     "content": f"Dry mass: {design_params.get('systems.dry_mass_kg', 'TBD')} kg, Margin: {design_params.get('systems.mass_margin_percent', 'TBD')}%"},
                    {"number": "4.2", "title": "Power Budget",
                     "content": f"Total power: {design_params.get('systems.total_power_w', 'TBD')} W"},
                    {"number": "4.3", "title": "Link Budget", "content": "See link budget analysis"},
                    {"number": "4.4", "title": "Delta-V Budget", "content": f"Total dV: {design_params.get('propulsion.total_dv_ms', 'TBD')} m/s"},
                ],
            },
        ],
        "total_requirements": len(requirements),
    }


def generate_ird(
    *,
    study_name: str,
    interfaces: list[dict[str, Any]],
    phase_id: str = "phase_b",
) -> dict[str, Any]:
    """Interface Requirements Document — ECSS-E-ST-10-24C."""
    return {
        "document": "Interface Requirements Document (IRD)",
        "standard": "ECSS-E-ST-10-24C",
        "study_name": study_name,
        "phase": phase_id,
        "generated": datetime.now(timezone.utc).isoformat(),
        "sections": [
            {
                "number": "1", "title": "Introduction",
                "subsections": [
                    {"number": "1.1", "title": "Purpose", "content": f"Defines all internal and external interfaces for {study_name}."},
                    {"number": "1.2", "title": "Interface Categories", "content": "Mechanical, Electrical, Thermal, Data, RF, Optical"},
                ],
            },
            {
                "number": "2", "title": "Internal Interfaces (Subsystem-to-Subsystem)",
                "subsections": [
                    {"number": f"2.{i+1}", "title": f"{ifc.get('subsystems', ['?','?'])[0]} ↔ {ifc.get('subsystems', ['?','?'])[1]}",
                     "content": f"Types: {', '.join(ifc.get('types', []))}. {ifc.get('description', '')}"}
                    for i, ifc in enumerate(interfaces[:20])
                ] if interfaces else [{"number": "2.1", "title": "TBD", "content": "Interface matrix not yet populated"}],
            },
            {
                "number": "3", "title": "External Interfaces",
                "subsections": [
                    {"number": "3.1", "title": "Launch Vehicle Interface", "content": "Per launch adapter ICD. Mechanical, electrical separation connector."},
                    {"number": "3.2", "title": "Ground Segment Interface", "content": "RF link (TM/TC), data products interface."},
                ],
            },
            {
                "number": "4", "title": "Interface Conflicts & Resolution",
                "subsections": [
                    {"number": "4.1", "title": "Identified Conflicts",
                     "content": "\n".join(f"- {ifc.get('conflict_title', '')}" for ifc in interfaces if ifc.get('has_conflict')) or "No conflicts identified"},
                ],
            },
        ],
        "total_interfaces": len(interfaces),
    }


def generate_semp(
    *,
    study_name: str,
    phase_id: str = "phase_a",
) -> dict[str, Any]:
    """Systems Engineering Management Plan — NASA SEH Appendix J / ECSS-M-ST-10C."""
    return {
        "document": "Systems Engineering Management Plan (SEMP)",
        "standard": "NASA SEH Appendix J / ECSS-M-ST-10C",
        "study_name": study_name,
        "phase": phase_id,
        "generated": datetime.now(timezone.utc).isoformat(),
        "sections": [
            {"number": "1", "title": "Introduction", "subsections": [
                {"number": "1.1", "title": "Purpose", "content": f"Defines the SE approach for {study_name}."},
                {"number": "1.2", "title": "Scope", "content": "Covers all 17 SE processes per NPR 7123.1."},
            ]},
            {"number": "2", "title": "SE Process Application", "subsections": [
                {"number": "2.1", "title": "System Design (Processes 1-4)", "content": "Stakeholder expectations, requirements definition, logical decomposition, design solution."},
                {"number": "2.2", "title": "Product Realisation (Processes 5-9)", "content": "Implementation, integration, verification, validation, transition."},
                {"number": "2.3", "title": "Technical Management (Processes 10-17)", "content": "Planning, requirements management, interface management, risk, CM, data, assessment, decision analysis."},
            ]},
            {"number": "3", "title": "Organisation & Roles", "subsections": [
                {"number": "3.1", "title": "Concurrent Design Team", "content": "Systems Engineer, Power, AOCS, Thermal, Comms, Propulsion, Structures, Payload, Cost, Mission Analyst."},
            ]},
            {"number": "4", "title": "Reviews & Milestones", "subsections": [
                {"number": "4.1", "title": "Review Schedule", "content": "MCR → SRR → PDR → CDR → TRR → FRR per ECSS-M-ST-10C / NASA life cycle."},
                {"number": "4.2", "title": "Exit Criteria", "content": "Per SpaceCDF gate review framework."},
            ]},
            {"number": "5", "title": "Risk Management", "subsections": [
                {"number": "5.1", "title": "Risk Process", "content": "Per ECSS-M-ST-80C / NPR 8000.4."},
            ]},
            {"number": "6", "title": "Technical Performance Measures", "subsections": [
                {"number": "6.1", "title": "TPMs", "content": "Mass margin, power margin, pointing accuracy, link margin, cost margin."},
            ]},
        ],
    }


def generate_rmp(
    *,
    study_name: str,
    risks: list[dict[str, Any]] | None = None,
    phase_id: str = "phase_a",
) -> dict[str, Any]:
    """Risk Management Plan — ECSS-M-ST-80C."""
    risk_items = risks or []
    return {
        "document": "Risk Management Plan (RMP)",
        "standard": "ECSS-M-ST-80C",
        "study_name": study_name,
        "phase": phase_id,
        "generated": datetime.now(timezone.utc).isoformat(),
        "sections": [
            {"number": "1", "title": "Introduction", "subsections": [
                {"number": "1.1", "title": "Purpose", "content": f"Risk management approach for {study_name}."},
            ]},
            {"number": "2", "title": "Risk Process", "subsections": [
                {"number": "2.1", "title": "Identification", "content": "Risk identification via design analysis, trade studies, heritage review."},
                {"number": "2.2", "title": "Assessment", "content": "5×5 likelihood × consequence matrix per ECSS-M-ST-80C."},
                {"number": "2.3", "title": "Mitigation", "content": "Accept / Mitigate / Transfer / Avoid."},
                {"number": "2.4", "title": "Monitoring", "content": "Risk review at each design review gate."},
            ]},
            {"number": "3", "title": "Risk Register", "subsections": [
                {"number": f"3.{i+1}", "title": r.get("title", f"Risk {i+1}"),
                 "content": f"Likelihood: {r.get('likelihood', 'TBD')}, Consequence: {r.get('consequence', 'TBD')}. {r.get('description', '')}"}
                for i, r in enumerate(risk_items)
            ] if risk_items else [
                {"number": "3.1", "title": "TBD", "content": "Risk register to be populated during Phase A."},
            ]},
        ],
        "total_risks": len(risk_items),
    }


def generate_conops_document(
    *,
    study_name: str,
    mission_need: dict[str, Any],
    conops: dict[str, Any] | None = None,
    phase_id: str = "phase_a",
) -> dict[str, Any]:
    """Concept of Operations Document — NASA SEH Appendix S."""
    mn = mission_need or {}
    ops = conops or {}
    phases = ops.get("phases", [])
    modes = ops.get("modes", [])

    return {
        "document": "Concept of Operations (ConOps)",
        "standard": "NASA SEH Appendix S",
        "study_name": study_name,
        "phase": phase_id,
        "generated": datetime.now(timezone.utc).isoformat(),
        "sections": [
            {"number": "1", "title": "Introduction", "subsections": [
                {"number": "1.1", "title": "Purpose", "content": f"Describes how {study_name} will be operated to meet mission objectives."},
                {"number": "1.2", "title": "Mission Overview", "content": mn.get("problem_statement", "TBD")},
            ]},
            {"number": "2", "title": "Mission Architecture", "subsections": [
                {"number": "2.1", "title": "Space Segment", "content": "Spacecraft + payload."},
                {"number": "2.2", "title": "Ground Segment", "content": "Ground station(s) + MCC + data processing."},
                {"number": "2.3", "title": "User Segment", "content": "Data products and services to end users."},
            ]},
            {"number": "3", "title": "Mission Phases", "subsections": [
                {"number": f"3.{i+1}", "title": p.get("name", f"Phase {i+1}"),
                 "content": f"Duration: {p.get('duration_days', 'TBD')} days. {p.get('description', '')}"}
                for i, p in enumerate(phases)
            ] if phases else [
                {"number": "3.1", "title": "LEOP", "content": "TBD"},
                {"number": "3.2", "title": "Commissioning", "content": "TBD"},
                {"number": "3.3", "title": "Nominal Operations", "content": "TBD"},
                {"number": "3.4", "title": "Disposal", "content": "TBD"},
            ]},
            {"number": "4", "title": "Operational Modes", "subsections": [
                {"number": f"4.{i+1}", "title": m.get("name", f"Mode {i+1}"),
                 "content": f"{m.get('description', '')}. Active subsystems: {', '.join(m.get('subsystems_active', []))}. Pointing: {m.get('pointing', 'TBD')}. Data flow: {m.get('dataflow', 'TBD')}."}
                for i, m in enumerate(modes)
            ] if modes else [
                {"number": "4.1", "title": "TBD", "content": "Operational modes to be defined."},
            ]},
            {"number": "5", "title": "Data Flow", "subsections": [
                {"number": "5.1", "title": "Data Pipeline", "content": "Instrument → Onboard Storage → Downlink → Ground Processing → Archive → User."},
            ]},
        ],
        "total_phases": len(phases),
        "total_modes": len(modes),
    }


def generate_test_plan(
    *,
    study_name: str,
    requirements: list[dict[str, Any]],
    phase_id: str = "phase_c",
) -> dict[str, Any]:
    """Test Plan — ECSS-E-ST-10-03C."""
    test_reqs = [r for r in requirements if r.get("verification_method") == "test"]
    return {
        "document": "Test Plan",
        "standard": "ECSS-E-ST-10-03C",
        "study_name": study_name,
        "phase": phase_id,
        "generated": datetime.now(timezone.utc).isoformat(),
        "sections": [
            {"number": "1", "title": "Introduction", "subsections": [
                {"number": "1.1", "title": "Purpose", "content": f"Test plan for {study_name} verification."},
                {"number": "1.2", "title": "Test Philosophy", "content": "Proto-flight approach for CubeSats; model philosophy for larger missions."},
            ]},
            {"number": "2", "title": "Environmental Testing", "subsections": [
                {"number": "2.1", "title": "Vibration", "content": "Sine, random, shock per launch vehicle ICD."},
                {"number": "2.2", "title": "Thermal Vacuum", "content": "Qualification range ±10°C beyond operating. 4 cycles minimum."},
                {"number": "2.3", "title": "EMC", "content": "Per ECSS-E-ST-20-07C. Radiated emissions, susceptibility, conducted."},
            ]},
            {"number": "3", "title": "Functional Testing", "subsections": [
                {"number": "3.1", "title": "Subsystem Tests", "content": "Individual subsystem functional verification before integration."},
                {"number": "3.2", "title": "System-Level Tests", "content": "End-to-end data chain, mode transitions, FDIR."},
            ]},
            {"number": "4", "title": "Test Requirements Matrix", "subsections": [
                {"number": f"4.{i+1}", "title": f"{r.get('id', '')}",
                 "content": f"{r.get('text', '')} — Test method: TBD"}
                for i, r in enumerate(test_reqs[:20])
            ] if test_reqs else [
                {"number": "4.1", "title": "TBD", "content": "Test requirements to be derived from VP."},
            ]},
        ],
        "test_requirement_count": len(test_reqs),
    }


# Map of all available DID types
DID_TYPES = {
    "mrd": ("Mission Requirements Document", generate_mrd),
    "ts": ("Technical Specification", generate_technical_specification),
    "ird": ("Interface Requirements Document", generate_ird),
    "semp": ("SE Management Plan", generate_semp),
    "rmp": ("Risk Management Plan", generate_rmp),
    "conops": ("Concept of Operations", generate_conops_document),
    "test_plan": ("Test Plan", generate_test_plan),
}


def list_available_dids() -> list[dict[str, str]]:
    """List all available DID types."""
    return [{"id": k, "name": v[0]} for k, v in DID_TYPES.items()]
