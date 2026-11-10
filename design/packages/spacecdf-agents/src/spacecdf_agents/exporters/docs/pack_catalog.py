"""SpaceCDF — what a review data pack holds at each gate (W4.02).

The products and their maturity per canonical gate (D draft, B baselined, U updated) come from
``configs/gate_profiles.yaml`` (``products``). That file stops at the CDR; the qualification,
acceptance and flight readiness reviews (QR, AR, FRR, ECSS-M-ST-10C Rev.1 §5.3) and a few
products the profile matrix does not list (SEMP, test reports, NCRs and waivers, as-built
configuration, licences, launch-provider acceptance, operations readiness, review record) are
added here. Cells for these are a C2O reading of ECSS-M-ST-10C / E-ST-10C Annex A and of
CubeSat review practice (to verify against the primary texts), exactly like the yaml ones.

A pack = the review data package (one document, sections chosen from the products present at
the gate) + the documents mapped to those products + an index of what is included and what is
still missing. The server (``routers/exports/packs.py``) produces the documents; this module is
pure data and has no I/O.

Producers (``Document.producer``):

* ``package``            the review data package itself (``study_pack.py``)
* ``docx:<type>``        ``POST /api/exports/docx/<type>`` (MRD, ConOps, TS, IRD, SEMP, VP, RMP)
* ``route:<family>``     an export family route with ``fmt=docx`` (launch ICD, thermal, test plan,
                         deorbit, RSSSA)
* ``vcd``, ``rtm``       the V&V control document and the requirement traceability matrix
* ``diagrams``           the diagram set (product and function trees, block, N2, power, RF...)
* ``xlsx:master_budget``, ``xlsx:bom``   the workbooks
* ``csv:<name>``         plain tables (requirements, risks, interfaces)
* ``hook:<module>``      a generator another work package owns. The module (under
                         ``spacecdf_server.services.docx``) lights up in the pack as soon as it
                         defines ``pack_docx(sx, *, gate, lang) -> bytes``; until then the index
                         lists the document as missing, with its owner and work package.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

#: every gate a pack can be made for, in life-cycle order
GATE_ORDER = ("mdr", "prr", "srr", "pdr", "cdr", "qr", "ar", "frr")
#: packs complete to PDR for the recording; later gates are skeletons fed by the collector
COMPLETE_TO = "pdr"

GATE_NAMES: dict[str, dict[str, str]] = {
    "mdr": {"en": "Mission Definition Review", "fr": "Revue de définition de la mission"},
    "prr": {"en": "Preliminary Requirements Review", "fr": "Revue des exigences préliminaires"},
    "srr": {"en": "System Requirements Review", "fr": "Revue des exigences système"},
    "pdr": {"en": "Preliminary Design Review", "fr": "Revue de conception préliminaire"},
    "cdr": {"en": "Critical Design Review", "fr": "Revue critique de conception"},
    "qr": {"en": "Qualification Review", "fr": "Revue de qualification"},
    "ar": {"en": "Acceptance Review", "fr": "Revue de recette"},
    "frr": {"en": "Flight Readiness Review", "fr": "Revue d’aptitude au vol"},
}
#: legacy and alternative gate ids accepted by the pack route
GATE_ALIASES = {"mcr": "mdr", "orr": "frr", "lrr": "frr"}

#: maturity of the profile products at the gates after CDR (C2O reading, to verify)
LATE_MATURITY: dict[str, dict[str, str]] = {
    "objectives": {"qr": "U", "ar": "U", "frr": "U"},
    "conops": {"frr": "U"},
    "trs": {"qr": "U"},
    "product_tree": {"qr": "U", "ar": "U"},
    "budgets": {"qr": "U", "ar": "U", "frr": "U"},
    "design_files": {"qr": "U", "ar": "U"},
    "interfaces": {"qr": "U", "ar": "U"},
    "aiv_plan": {"qr": "U", "ar": "U"},
    "vcd": {"qr": "U", "ar": "U", "frr": "U"},
    "trl_matrix": {"qr": "U"},
    "risk_register": {"qr": "U", "ar": "U", "frr": "U"},
    "cost_schedule": {"qr": "U", "ar": "U", "frr": "U"},
    "debris": {"ar": "U", "frr": "U"},
    "spectrum": {"frr": "U"},
    "cds_matrix": {"ar": "U", "frr": "U"},
    "tmtc_db": {"qr": "U", "ar": "U", "frr": "U"},
    "fdir_spec": {"qr": "U", "ar": "U"},
    "aocs_design": {"qr": "U"},
    "ops_products": {"ar": "U", "frr": "B"},
}

#: products the profile matrix does not list (C2O reading, to verify)
EXTRA_PRODUCTS: list[dict[str, Any]] = [
    {"id": "semp", "owner_seat": "team_leader",
     "label": {"en": "Systems engineering management plan", "fr": "Plan de management de l’ingénierie système"},
     "maturity": {"mdr": "D", "prr": "D", "srr": "B", "pdr": "U", "cdr": "U"}},
    {"id": "review_record", "owner_seat": "team_leader",
     "label": {"en": "Previous review record (RIDs, actions, decision)", "fr": "Compte rendu de la revue précédente (RID, actions, décision)"},
     "maturity": {"prr": "U", "srr": "U", "pdr": "U", "cdr": "U", "qr": "U", "ar": "U", "frr": "U"}},
    {"id": "licences", "owner_seat": "comms_engineer",
     "label": {"en": "Licences and filings (spectrum, remote sensing, registration)", "fr": "Licences et dépôts (spectre, télédétection, immatriculation)"},
     "maturity": {"pdr": "D", "cdr": "U", "qr": "U", "ar": "U", "frr": "B"}},
    {"id": "test_reports", "owner_seat": "systems_engineer",
     "label": {"en": "Test reports (development, qualification, acceptance)", "fr": "Rapports d’essai (développement, qualification, recette)"},
     "maturity": {"cdr": "D", "qr": "B", "ar": "B", "frr": "U"}},
    {"id": "ncr_waivers", "owner_seat": "systems_engineer",
     "label": {"en": "Non-conformances, deviations and waivers", "fr": "Non-conformités, dérogations et dispenses"},
     "maturity": {"qr": "B", "ar": "B", "frr": "U"}},
    {"id": "as_built", "owner_seat": "structures_engineer",
     "label": {"en": "As-built configuration and measured mass properties", "fr": "Configuration telle que construite et propriétés de masse mesurées"},
     "maturity": {"ar": "B", "frr": "U"}},
    {"id": "launch_acceptance", "owner_seat": "structures_engineer",
     "label": {"en": "Launch-provider interface and acceptance data", "fr": "Interface lanceur et données de recette du lanceur"},
     "maturity": {"pdr": "D", "cdr": "U", "ar": "U", "frr": "B"}},
    # wave 3 (3.X2): the objects of the systems-engineering V each pack carries as evidence
    {"id": "stakeholder_register", "owner_seat": "team_leader",
     "label": {"en": "Stakeholder register, needs and measures of effectiveness",
               "fr": "Registre des parties prenantes, besoins et mesures d’efficacité"},
     "maturity": {"mdr": "B", "prr": "U", "srr": "U", "pdr": "U", "cdr": "U"}},
    {"id": "validation_plan", "owner_seat": "systems_engineer",
     "label": {"en": "Validation plan and need validation", "fr": "Plan de validation et validation des besoins"},
     "maturity": {"mdr": "D", "prr": "B", "srr": "U", "pdr": "U", "cdr": "U", "qr": "U", "ar": "U", "frr": "U"}},
    {"id": "allocation_ledger", "owner_seat": "systems_engineer",
     "label": {"en": "Allocation ledger (budget shares signed by their owners)",
               "fr": "Registre des allocations (parts de bilan signées par leurs responsables)"},
     "maturity": {"prr": "D", "srr": "B", "pdr": "U", "cdr": "U"}},
    {"id": "negotiation_records", "owner_seat": "systems_engineer",
     "label": {"en": "Negotiation records between seats", "fr": "Comptes rendus de négociation entre postes"},
     "maturity": {"prr": "D", "srr": "U", "pdr": "U", "cdr": "U"}},
    {"id": "open_items_register", "owner_seat": "team_leader",
     "label": {"en": "Open items, conditional decisions and change proposals",
               "fr": "Points ouverts, décisions conditionnelles et propositions de modification"},
     "maturity": {"mdr": "D", "prr": "U", "srr": "U", "pdr": "U", "cdr": "U", "qr": "U", "ar": "U", "frr": "U"}},
    {"id": "assumption_register", "owner_seat": "systems_engineer",
     "label": {"en": "Assumption register", "fr": "Registre des hypothèses"},
     "maturity": {"mdr": "D", "prr": "U", "srr": "U", "pdr": "U", "cdr": "U"}},
    {"id": "icd_issues", "owner_seat": "systems_engineer",
     "label": {"en": "Interface control documents: issue and sign-off", "fr": "Documents de contrôle d’interface : édition et visa"},
     "maturity": {"srr": "D", "pdr": "B", "cdr": "U", "qr": "U"}},
    {"id": "reliability_fmea", "owner_seat": "systems_engineer",
     "label": {"en": "Reliability analysis and FMEA", "fr": "Analyse de fiabilité et AMDE"},
     "maturity": {"srr": "D", "pdr": "B", "cdr": "U", "qr": "U"}},
    {"id": "thermal_model", "owner_seat": "thermal_engineer",
     "label": {"en": "Thermal model (nodes, hot and cold cases, margins)",
               "fr": "Modèle thermique (nœuds, cas chaud et froid, marges)"},
     "maturity": {"pdr": "B", "cdr": "U", "qr": "U"}},
    {"id": "ops_readiness", "owner_seat": "mission_analyst",
     "label": {"en": "Operations readiness (procedures, rehearsals, ground segment validated)", "fr": "Aptitude opérationnelle (procédures, répétitions, segment sol validé)"},
     "maturity": {"ar": "D", "frr": "B"}},
]


@dataclass(frozen=True)
class Document:
    id: str
    file: str                      # path inside the zip
    title: dict[str, str]
    standard: str
    products: tuple[str, ...]
    producer: str
    owner: str = "X"               # agent / work package that writes the generator
    work_package: str = ""
    from_gate: str | None = None   # first gate the document is expected at (default: products decide)


DOCUMENTS: tuple[Document, ...] = (
    Document("mrd", "documents/MRD_mission_requirements.docx",
             {"en": "Mission requirements document (mission description, need, objectives)",
              "fr": "Document des exigences de mission (description, besoin, objectifs)"},
             "ECSS-E-ST-10C Annex B (MDD) / E-ST-10-06C", ("mission_statement", "objectives", "concept_report"),
             "docx:mrd"),
    Document("conops", "documents/ConOps.docx",
             {"en": "Concept of operations", "fr": "Concept d’opérations"},
             "ECSS-E-ST-70C / NASA SEH App. S", ("conops",), "docx:conops", "D", "W7.02"),
    Document("trades", "documents/Trade_off_report.docx",
             {"en": "Trade-off report", "fr": "Rapport de compromis"},
             "ECSS-E-ST-10C Annex K", ("trade_reports",), "hook:trades", "D", "W6"),
    Document("semp", "documents/SEMP.docx",
             {"en": "Systems engineering management plan", "fr": "Plan de management de l’ingénierie système"},
             "ECSS-E-ST-10C Annex D (SEP)", ("semp",), "docx:semp"),
    Document("ts", "documents/TS_technical_requirements.docx",
             {"en": "Technical requirements specification", "fr": "Spécification technique des besoins"},
             "ECSS-E-ST-10-06C Annex A", ("trs",), "docx:ts"),
    Document("requirements_csv", "data/requirements.csv",
             {"en": "Requirements table (all levels, CSV)", "fr": "Tableau des exigences (tous niveaux, CSV)"},
             "—", ("trs",), "csv:requirements"),
    Document("diagrams", "documents/Diagrams.docx",
             {"en": "Diagram set (context, stakeholder map, product and function trees, FFBD, N², V diagram, trade "
                    "matrices, budget flow-down, verification flow, block, power, data, RF)",
              "fr": "Jeu de diagrammes (contexte, carte des parties prenantes, arbres produit et fonctionnel, FFBD, N², "
                    "diagramme en V, matrices de compromis, déclinaison des bilans, flux de vérification, blocs, "
                    "puissance, données, RF)"},
             "ECSS-E-ST-10C Annex A figures", ("function_tree", "product_tree", "design_files"), "diagrams"),
    Document("ird", "documents/IRD_interfaces.docx",
             {"en": "Interface requirements document", "fr": "Document des exigences d’interface"},
             "ECSS-E-ST-10-24C", ("interfaces",), "docx:ird"),
    Document("icd_csv", "data/interfaces.csv",
             {"en": "Interface list (CSV)", "fr": "Liste des interfaces (CSV)"},
             "—", ("interfaces",), "csv:interfaces"),
    Document("master_budget", "budgets/master_budget.xlsx",
             {"en": "Master budget workbook (mass, power, data, link, pointing, margins, cost)",
              "fr": "Classeur des bilans (masse, puissance, données, liaison, pointage, marges, coût)"},
             "ECSS-E-HB-10-02A / margin policy", ("budgets",), "xlsx:master_budget"),
    Document("bom", "budgets/bill_of_materials.xlsx",
             {"en": "Equipment list and bill of materials", "fr": "Liste des équipements et nomenclature"},
             "—", ("product_tree", "cost_schedule"), "xlsx:bom"),
    Document("thermal", "documents/Thermal_report.docx",
             {"en": "Thermal design report", "fr": "Rapport de conception thermique"},
             "ECSS-E-ST-31C", ("design_files",), "route:thermal", from_gate="pdr"),
    Document("vp", "documents/VP_verification_plan.docx",
             {"en": "Verification plan", "fr": "Plan de vérification"},
             "ECSS-E-ST-10-02C Annex A", ("aiv_plan",), "docx:vp"),
    Document("test_plan", "documents/AIT_test_plan.docx",
             {"en": "AIT plan and test matrix", "fr": "Plan AIT et matrice des essais"},
             "ECSS-E-ST-10-03C", ("aiv_plan", "test_reports"), "route:test_plan", from_gate="pdr"),
    Document("ait", "documents/AIT_model_philosophy.docx",
             {"en": "Model philosophy and AIT programme", "fr": "Philosophie des modèles et programme AIT"},
             "ECSS-E-ST-10-03C", ("aiv_plan", "test_reports"), "hook:ait", "A", "W8a", from_gate="pdr"),
    Document("vcd", "documents/VCD_verification_control.docx",
             {"en": "Verification control document", "fr": "Document de contrôle de la vérification"},
             "ECSS-E-ST-10-02C Annex B", ("vcd",), "vcd"),
    Document("rtm", "data/rtm.csv",
             {"en": "Requirement traceability matrix (CSV)", "fr": "Matrice de traçabilité des exigences (CSV)"},
             "—", ("vcd",), "rtm"),
    Document("rmp", "documents/RMP_risk_management.docx",
             {"en": "Risk management plan with the risk register", "fr": "Plan de gestion des risques avec le registre"},
             "ECSS-M-ST-80C", ("risk_register",), "docx:rmp"),
    Document("risks_csv", "data/risk_register.csv",
             {"en": "Risk register (CSV)", "fr": "Registre des risques (CSV)"},
             "—", ("risk_register",), "csv:risks"),
    Document("schedule", "documents/Schedule_WBS.docx",
             {"en": "Schedule, WBS and long-lead items", "fr": "Calendrier, OT et articles à long délai"},
             "ECSS-M-ST-60C", ("cost_schedule",), "hook:schedule", "A", "W11a"),
    Document("deorbit", "documents/Debris_mitigation.docx",
             {"en": "Disposal and debris mitigation report", "fr": "Rapport d’élimination et d’atténuation des débris"},
             "ISO 24113 / ECSS-U-AS-10C / ISED debris rules", ("debris",), "route:deorbit", "L", "W5.02"),
    Document("licensing", "documents/Licensing_status.docx",
             {"en": "Spectrum and licensing documents (ISED, ITU, remote sensing)",
              "fr": "Documents de spectre et de licences (ISDE, UIT, télédétection)"},
             "ISED CPC-2-6-02 / RR App. 4 / RSSSA", ("spectrum", "licences"), "hook:licensing", "L", "W5.04"),
    Document("rsssa", "documents/RSSSA_application.docx",
             {"en": "Remote sensing operating licence application", "fr": "Demande de licence d’exploitation de télédétection"},
             "RSSSA guide", ("licences",), "route:rsssa", "L", "W5.04", from_gate="pdr"),
    Document("launch_icd", "documents/Launch_ICD.docx",
             {"en": "Launch interface control document and CDS compliance",
              "fr": "Document de contrôle d’interface lanceur et conformité CDS"},
             "CDS rev 14.1 / launch-provider ICD", ("cds_matrix", "launch_acceptance"), "route:launch_icd",
             from_gate="pdr"),
    Document("tmtc", "documents/TMTC_database.docx",
             {"en": "TM/TC database, FDIR and AOCS specification", "fr": "Base de données TM/TC, spécification FDIR et SCAO"},
             "ECSS-E-ST-70-41C / E-ST-10C", ("tmtc_db", "fdir_spec", "aocs_design"), "hook:tmtc", "H", "W3.06"),
    Document("review_report", "documents/Previous_review_report.docx",
             {"en": "Previous review report (criteria, RIDs, actions, decision)",
              "fr": "Rapport de la revue précédente (critères, RID, actions, décision)"},
             "ECSS-M-ST-10-01C", ("review_record",), "hook:review_report", "D", "W4.08"),
)

DOC_BY_ID = {d.id: d for d in DOCUMENTS}


def canonical_gate(gate_id: str) -> str | None:
    g = (gate_id or "").strip().lower()
    g = GATE_ALIASES.get(g, g)
    return g if g in GATE_ORDER else None


def _late_products(base: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for p in base:
        mat = dict(p.get("maturity") or {})
        mat.update(LATE_MATURITY.get(p["id"], {}))
        out.append({**p, "maturity": mat})
    known = {p["id"] for p in out}
    out += [dict(p) for p in EXTRA_PRODUCTS if p["id"] not in known]
    return out


def products_at(covers: list[str] | tuple[str, ...], profile_products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Products expected at a gate that covers the canonical gates ``covers``, each with its
    maturity (the most advanced stamp among the covered gates: B > U > D)."""
    rank = {"D": 1, "U": 2, "B": 3}
    out = []
    for p in _late_products(profile_products):
        mats = [(p.get("maturity") or {}).get(c) for c in covers]
        mats = [m for m in mats if m]
        if not mats:
            continue
        best = max(mats, key=lambda m: rank.get(m, 0))
        out.append({"id": p["id"], "label": p.get("label") or {}, "owner_seat": p.get("owner_seat"),
                    "maturity": best})
    return out


def documents_for(product_ids: set[str], covers: list[str] | tuple[str, ...]) -> list[Document]:
    last = max((GATE_ORDER.index(c) for c in covers if c in GATE_ORDER), default=0)
    out = []
    for d in DOCUMENTS:
        if not product_ids.intersection(d.products):
            continue
        if d.from_gate and GATE_ORDER.index(d.from_gate) > last:
            continue
        out.append(d)
    return out


@dataclass
class PackPlan:
    gate: str                       # the id asked for (profile gate id or canonical)
    covers: list[str]               # canonical gates this pack covers
    short: str                      # label shown on the cover (MDR, MCR, PRR+SRR, FRR...)
    name: dict[str, str]
    profile_id: str | None
    margin_gate: str                # margin-ladder step for the budgets (mdr..cdr)
    products: list[dict[str, Any]] = field(default_factory=list)
    documents: list[Document] = field(default_factory=list)
    complete: bool = True           # False: skeleton (gates after PDR)

    def has(self, product_id: str) -> bool:
        return any(p["id"] == product_id for p in self.products)

    def maturity(self, product_id: str) -> str | None:
        return next((p["maturity"] for p in self.products if p["id"] == product_id), None)

    def as_dict(self) -> dict[str, Any]:
        return {"gate": self.gate, "covers": self.covers, "short": self.short, "name": self.name,
                "profile_id": self.profile_id, "margin_gate": self.margin_gate, "complete": self.complete,
                "products": self.products, "documents": [d.id for d in self.documents]}


def plan_pack(gate_id: str, *, profile: dict[str, Any] | None, profile_products: list[dict[str, Any]]) -> PackPlan:
    """The pack for ``gate_id``: a gate of the study's profile (``cr``, ``prr`` covering PRR+SRR,
    the NASA skin's ``mdr`` = MCR...), a canonical gate, a legacy id (``mcr``) or a gate after CDR
    (``qr``, ``ar``, ``frr``). Raises ``KeyError`` for an unknown id."""
    gid = (gate_id or "").strip().lower()
    pgate = None
    for g in (profile or {}).get("gates") or []:
        if g.get("id") == gid:
            pgate = g
            break
    if pgate is not None:
        covers = [c for c in pgate.get("covers") or [gid] if c in GATE_ORDER]
        short = pgate.get("short") or gid.upper()
        name = dict(pgate.get("name") or GATE_NAMES.get(covers[-1], {}))
        name = {k: (v[:1].upper() + v[1:]) if isinstance(v, str) else v for k, v in name.items()}
    else:
        canon = canonical_gate(gid)
        if canon is None:
            raise KeyError(gid)
        covers = [canon]
        short = canon.upper()
        name = dict(GATE_NAMES[canon])
        gid = canon
    margin_gate = next((c for c in reversed(covers) if c in ("mdr", "prr", "srr", "pdr", "cdr")), "cdr")
    products = products_at(covers, profile_products)
    docs = documents_for({p["id"] for p in products}, covers)
    complete = max(GATE_ORDER.index(c) for c in covers) <= GATE_ORDER.index(COMPLETE_TO)
    return PackPlan(gate=gid, covers=covers, short=short, name=name,
                    profile_id=(profile or {}).get("id"), margin_gate=margin_gate,
                    products=products, documents=docs, complete=complete)


def available_gates(profile: dict[str, Any] | None) -> list[dict[str, Any]]:
    """The packs a study can ask for: its profile's gates, then QR, AR and FRR."""
    out = []
    seen: set[str] = set()
    for g in (profile or {}).get("gates") or []:
        covers = [c for c in g.get("covers") or [] if c in GATE_ORDER]
        seen.update(covers)
        out.append({"id": g["id"], "short": g.get("short") or g["id"].upper(), "name": g.get("name"),
                    "covers": covers,
                    "complete": max((GATE_ORDER.index(c) for c in covers), default=0) <= GATE_ORDER.index(COMPLETE_TO)})
    for c in GATE_ORDER:
        if c not in seen and GATE_ORDER.index(c) > GATE_ORDER.index("pdr"):
            out.append({"id": c, "short": c.upper(), "name": GATE_NAMES[c], "covers": [c], "complete": False})
    return out
