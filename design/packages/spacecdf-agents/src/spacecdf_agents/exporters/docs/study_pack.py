"""SpaceCDF — the review data package of a gate, built from what the team entered (W4.01/W4.02).

Input: ``StudyExport.as_dict()`` from ``spacecdf_server.services.export_context.collect`` (the
whole study, collected once), the ``PackPlan`` of the gate (``pack_catalog.plan_pack``) and a
few extras the server adds (the gate checklist, the status of each pack document, the
parametric cross-check). Nothing here runs the parametric design loop: every figure is the
team's (roll-up of the selected equipment, the requirements store, the risk register, the modes
and their energy balance, the analysis runs...). The loop's totals appear only in the
"parametric cross-check" column of the budget summary when the server passes them.

The package is built once as a list of blocks and rendered twice: to Word (the SpaceCDF course
style of ``theme.py``) and to Markdown (the plain-text twin in the zip). A section whose data
does not exist yet says so and adds an entry to the open-items list; nothing is invented and no
"[HUMAN INPUT REQUIRED]" placeholder is ever written.

Headings, column headers and fixed sentences are bilingual (``lang`` = en | fr); the study's
own text stays as the team wrote it.
"""
from __future__ import annotations

import io
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .pack_catalog import DOCUMENTS, GATE_ORDER, PackPlan

# ─────────────────────────────────────────────────────────────── language

_FR: dict[str, str] = {
    "Review data package": "Dossier de données de revue",
    "Purpose and scope": "Objet et domaine d’application",
    "Package index": "Index du dossier",
    "Products expected at this review": "Produits attendus à cette revue",
    "Documents in this pack": "Documents de ce dossier",
    "Mission statement and need": "Énoncé de mission et besoin",
    "Stakeholders": "Parties prenantes",
    "Objectives and measures": "Objectifs et mesures",
    "Success criteria": "Critères de succès",
    "Concept and alternatives": "Concept et solutions de rechange",
    "Trade-offs and decisions": "Compromis et décisions",
    "Concept of operations": "Concept d’opérations",
    "Mission analysis": "Analyse de mission",
    "Requirements": "Exigences",
    "Function tree": "Arbre fonctionnel",
    "Product tree and equipment list": "Arbre produit et liste des équipements",
    "Technical budgets": "Bilans techniques",
    "Mass budget": "Bilan de masse",
    "Power budget": "Bilan de puissance",
    "Data budget": "Bilan de données",
    "Link budget": "Bilan de liaison",
    "Pointing budget": "Bilan de pointage",
    "Margin ladder": "Échelle des marges",
    "Design definition and justification": "Définition et justification de la conception",
    "Interfaces": "Interfaces",
    "Verification and AIV": "Vérification et AIV",
    "Technology readiness": "Maturité technologique",
    "Risk register": "Registre des risques",
    "Cost and schedule": "Coût et calendrier",
    "Debris mitigation and disposal": "Atténuation des débris et élimination",
    "Spectrum and licensing": "Spectre et licences",
    "CubeSat Design Specification compliance": "Conformité à la spécification CubeSat (CDS)",
    "TM/TC database": "Base de données TM/TC",
    "FDIR specification": "Spécification FDIR",
    "AOCS modes and control": "Modes et commande SCAO",
    "Operations products": "Produits d’exploitation",
    "Test results": "Résultats d’essai",
    "Non-conformances and waivers": "Non-conformités et dispenses",
    "As-built configuration": "Configuration telle que construite",
    "Launch-provider interface": "Interface lanceur",
    "Operations readiness": "Aptitude opérationnelle",
    "Previous reviews": "Revues précédentes",
    "Gate checklist": "Liste de contrôle du jalon",
    "Open items": "Points ouverts",
    "Product": "Produit", "Maturity": "Maturité", "Owner": "Responsable", "Where": "Où",
    "Document": "Document", "File": "Fichier", "Standard": "Norme", "Status": "État", "Note": "Remarque",
    "included": "inclus", "missing": "manquant", "partial": "partiel",
    "Code": "Code", "Level": "Niveau", "Type": "Type", "Requirement": "Exigence", "Threshold": "Seuil",
    "Method": "Méthode", "Phase": "Phase", "Parent": "Parent", "Allocated to": "Alloué à",
    "Name": "Nom", "Role": "Rôle", "Needs": "Besoins", "Priority": "Priorité", "Measure": "Mesure",
    "Decision": "Décision", "Rationale": "Justification",
    "Subsystem": "Sous-système", "Qty": "Qté", "Mass (kg)": "Masse (kg)", "Power (W)": "Puissance (W)",
    "TRL": "NMT", "Cat.": "Cat.", "KB id": "Id BC",
    "Item": "Élément", "Value": "Valeur", "Source": "Source", "Parametric cross-check": "Contrôle paramétrique",
    "Mode": "Mode", "Kind": "Type", "Share of orbit": "Part de l’orbite", "Pointing": "Pointage",
    "Power CBE (W)": "Puissance MEA (W)", "With margins (W)": "Avec marges (W)", "Energy per orbit (Wh)": "Énergie par orbite (Wh)",
    "DoD (%)": "DdD (%)", "Gate": "Jalon", "System margin": "Marge système", "With system margin (kg)": "Avec marge système (kg)",
    "Station": "Station", "Latitude": "Latitude", "Longitude": "Longitude", "Bands": "Bandes",
    "Analysis": "Analyse", "Run": "Exécution", "Result": "Résultat",
    "ID": "ID", "Risk": "Risque", "Category": "Catégorie", "L": "P", "C": "G", "Score": "Note",
    "Mitigation": "Atténuation", "Criterion": "Critère", "Evidence": "Preuve",
    "Count": "Nombre", "Kind of row": "Type de ligne", "Key": "Clé", "Description": "Description",
    "Recurring (k€)": "Récurrent (k€)", "Non-recurring (k€)": "Non récurrent (k€)",
    "Open item": "Point ouvert", "Owner / work package": "Responsable / lot de travail",
    "From": "De", "To": "À", "Interface": "Interface",
}


@dataclass
class Tr:
    lang: str = "en"

    def __call__(self, text: str) -> str:
        return _FR.get(text, text) if self.lang == "fr" else text

    def pick(self, d: Any) -> str:
        if isinstance(d, dict):
            return str(d.get(self.lang) or d.get("en") or next(iter(d.values()), ""))
        return "" if d is None else str(d)


# ─────────────────────────────────────────────────────────────── block model

@dataclass
class Block:
    kind: str                    # h1 h2 p bullets table callout
    text: str = ""
    items: list[str] = field(default_factory=list)
    headers: list[str] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)
    caption: str = ""


@dataclass
class Package:
    title: str
    subtitle: str
    study_name: str
    gate_short: str
    document_code: str
    date: str
    lang: str
    blocks: list[Block] = field(default_factory=list)
    open_items: list[dict[str, str]] = field(default_factory=list)
    sections: list[str] = field(default_factory=list)   # h1 titles, in order

    def h1(self, text: str) -> None:
        n = len(self.sections) + 1
        self.sections.append(text)
        self.blocks.append(Block("h1", f"{n}. {text}"))

    def h2(self, text: str) -> None:
        self.blocks.append(Block("h2", text))

    def p(self, text: str) -> None:
        if text:
            self.blocks.append(Block("p", str(text)))

    def bullets(self, items: list[str]) -> None:
        items = [str(i) for i in items if i]
        if items:
            self.blocks.append(Block("bullets", items=items))

    def table(self, headers: list[str], rows: list[list[Any]], caption: str = "") -> None:
        self.blocks.append(Block("table", headers=headers, rows=[[_cell(c) for c in r] for r in rows], caption=caption))

    def callout(self, text: str) -> None:
        self.blocks.append(Block("callout", text))

    def open(self, text: str, owner: str = "", section: str = "") -> None:
        self.open_items.append({"text": text, "owner": owner, "section": section or (self.sections[-1] if self.sections else "")})


def _cell(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float):
        if v == int(v) and abs(v) < 1e9:
            return str(int(v))
        if abs(v) < 1e-3:
            return f"{v:.3g}"
        return f"{v:.6g}" if abs(v) >= 100 else f"{round(v, 4):g}"
    if isinstance(v, (list, tuple)):
        return ", ".join(_cell(x) for x in v)
    return str(v)


def _num(v: Any) -> float | None:
    try:
        return None if v is None or v == "" else float(v)
    except (TypeError, ValueError):
        return None


def _fmt(v: Any, nd: int = 2) -> str:
    x = _num(v)
    return "" if x is None else f"{x:.{nd}f}"


# ─────────────────────────────────────────────────────────────── derived views of the study

@dataclass
class View:
    """Lookups over the StudyExport shared by the sections."""
    sx: dict[str, Any]
    elements: list[dict] = field(default_factory=list)
    by_id: dict[str, dict] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.elements = [e for e in (self.sx.get("elements") or {}).get("items") or [] if e.get("id")]
        self.by_id = {e["id"]: e for e in self.elements}

    def ancestors(self, e: dict) -> list[dict]:
        out, cur, n = [], e, 0
        while cur.get("parent_id") in self.by_id and n < 50:
            cur = self.by_id[cur["parent_id"]]
            out.append(cur)
            n += 1
        return out

    def segment_of(self, e: dict) -> str | None:
        if e.get("segment"):
            return e["segment"]
        for a in self.ancestors(e):
            if a.get("segment"):
                return a["segment"]
        return None

    def subsystem_of(self, e: dict) -> str:
        for a in self.ancestors(e):
            if a.get("element_type") == "subsystem":
                return a.get("name") or ""
        return e.get("subsystem_domain") or ""

    def equipment(self) -> list[dict]:
        """Components of the space segment, in tree order (the equipment list)."""
        return [e for e in self.elements if e.get("element_type") == "component"
                and (self.segment_of(e) or "space") == "space"]

    def stations(self) -> list[dict]:
        return [e for e in self.elements if self.segment_of(e) == "ground"
                and isinstance(e.get("performance"), dict)
                and (e["performance"].get("lat") is not None or e["performance"].get("latitude") is not None)]

    def name(self, eid: Any) -> str:
        return (self.by_id.get(eid) or {}).get("name") or ""

    def requirements(self) -> list[dict]:
        return list((self.sx.get("requirements") or {}).get("items") or [])

    def user_requirements(self) -> list[dict]:
        return [r for r in self.requirements() if not r.get("generated_interface")]

    def req_code(self) -> dict[str, str]:
        return {r.get("id"): (r.get("code") or r.get("id") or "") for r in self.requirements()}

    def definition(self) -> dict:
        return (self.sx.get("mission") or {}).get("definition") or {}


def threshold_text(r: dict) -> str:
    op, val = r.get("threshold_op"), r.get("threshold_value")
    if val is None or val == "":
        return ""
    unit = r.get("unit") or r.get("threshold_unit") or ""
    return " ".join(str(x) for x in (op or "", _cell(val) if not isinstance(val, str) else val, unit) if x != "").strip()


def requirement_rows(view: View, reqs: list[dict]) -> list[list[Any]]:
    codes = view.req_code()
    out = []
    for r in reqs:
        parent = r.get("parent_id") or r.get("derived_from_requirement_id")
        out.append([r.get("code") or r.get("id"), r.get("level") or "", r.get("req_type") or "",
                    r.get("text") or "", threshold_text(r), r.get("verification_method") or "",
                    r.get("verification_phase") or "", codes.get(parent, parent or ""),
                    view.name(r.get("element_id"))])
    return out


REQ_HEADERS = ["Code", "Level", "Type", "Requirement", "Threshold", "Method", "Phase", "Parent", "Allocated to"]


def is_stub(section: dict | None) -> bool:
    return isinstance(section, dict) and section.get("status") == "not_implemented"


def stub_owner(section: dict | None) -> str:
    if not isinstance(section, dict):
        return ""
    return " / ".join(x for x in (section.get("owner"), section.get("work_package")) if x)


# ─────────────────────────────────────────────────────────────── sections

SectionFn = Callable[["Ctx"], None]


@dataclass
class Ctx:
    pkg: Package
    view: View
    plan: PackPlan
    t: Tr
    extras: dict[str, Any]

    @property
    def sx(self) -> dict[str, Any]:
        return self.view.sx

    def mat(self, product: str) -> str:
        m = self.plan.maturity(product)
        return f" [{m}]" if m else ""


def _scope(c: Ctx) -> None:
    t, sx, plan = c.t, c.sx, c.plan
    c.pkg.h1(t("Purpose and scope"))
    name = sx.get("study_name") or (sx.get("mission") or {}).get("name") or ""
    gates = sx.get("gates") or {}
    prof = gates.get("profile") or {}
    if t.lang == "fr":
        c.pkg.p(f"Ce dossier rassemble les données de l’étude « {name} » pour la {t.pick(plan.name).lower()} "
                f"({plan.short}). Chaque chiffre provient de ce que l’équipe a saisi dans SpaceCDF : arbre produit "
                f"et équipements choisis, exigences, registre des risques, modes et bilan énergétique, analyses.")
    else:
        c.pkg.p(f"This package gathers the data of the study \u201c{name}\u201d for the {t.pick(plan.name)} "
                f"({plan.short}). Every figure comes from what the team entered in SpaceCDF: the product tree and "
                f"the selected equipment, the requirements, the risk register, the modes and their energy balance, "
                f"and the analysis runs.")
    rows = [["Gate profile" if t.lang != "fr" else "Profil de jalons", t.pick(prof.get("label")) or (prof.get("id") or "")],
            ["Review" if t.lang != "fr" else "Revue", f"{plan.short} \u2014 {t.pick(plan.name)}"],
            ["Canonical gates covered" if t.lang != "fr" else "Jalons canoniques couverts",
             ", ".join(g.upper() for g in plan.covers)],
            ["Margin-ladder step" if t.lang != "fr" else "Échelon de l’échelle des marges", plan.margin_gate.upper()],
            ["Current gate of the study" if t.lang != "fr" else "Jalon courant de l’étude",
             str(gates.get("current_gate") or "").upper()],
            ["Mission phase" if t.lang != "fr" else "Phase de mission", str((sx.get("mission") or {}).get("phase") or "")]]
    c.pkg.table([t("Item"), t("Value")], rows)
    if not plan.complete:
        c.pkg.callout("This review comes after the PDR. Its pack is a skeleton: every section is filled from the "
                      "study where data exists, and the open items list what the later work packages add."
                      if t.lang != "fr" else
                      "Cette revue suit la PDR. Son dossier est un squelette : chaque section est remplie à partir de "
                      "l’étude lorsque les données existent, et les points ouverts listent ce qu’ajoutent les lots suivants.")


def _index(c: Ctx) -> None:
    t, plan = c.t, c.plan
    c.pkg.h1(t("Package index"))
    c.pkg.h2(t("Products expected at this review"))
    c.pkg.table([t("Product"), t("Maturity"), t("Owner")],
                [[t.pick(p["label"]), p["maturity"], p.get("owner_seat") or ""] for p in plan.products],
                caption="D draft, B baselined, U updated (configs/gate_profiles.yaml; QR/AR/FRR and extra products: pack catalogue)"
                if t.lang != "fr" else "D ébauche, B référencé, U mis à jour")
    c.pkg.h2(t("Documents in this pack"))
    status = c.extras.get("documents") or {}
    rows = []
    for d in plan.documents:
        st = status.get(d.id) or {}
        rows.append([t.pick(d.title), d.file if st.get("status") == "included" else "", d.standard,
                     t(st.get("status") or "missing"), st.get("note") or ""])
    c.pkg.table([t("Document"), t("File"), t("Standard"), t("Status"), t("Note")], rows)
    for d in plan.documents:
        st = status.get(d.id) or {}
        if st.get("status") != "included":
            c.pkg.open(f"{t.pick(d.title)}: {st.get('note') or 'not produced'}",
                       owner=f"{d.owner} {d.work_package}".strip(), section=t("Package index"))


def _mission_statement(c: Ctx) -> None:
    t, need = c.t, c.sx.get("need") or {}
    c.pkg.h1(t("Mission statement and need") + (c.mat("mission_statement") or c.mat("objectives")))
    if not need:
        c.pkg.p("No mission need recorded." if t.lang != "fr" else "Aucun besoin de mission enregistré.")
        c.pkg.open("Mission need (problem statement, objectives) not entered", "team_leader")
        return
    c.pkg.p(need.get("problem_statement") or "")
    c.pkg.p(need.get("operational_context") or "")
    sh = need.get("stakeholders") or []
    if sh:
        c.pkg.h2(t("Stakeholders"))
        c.pkg.table([t("Name"), t("Role"), t("Needs"), t("Priority")],
                    [[s.get("name"), s.get("role"), "; ".join(s.get("needs") or []), s.get("priority") or ""] for s in sh])
    objs = need.get("objectives") or []
    c.pkg.h2(t("Objectives and measures") + c.mat("objectives"))
    if objs:
        c.pkg.table(["ID", "Objective" if t.lang != "fr" else "Objectif", t("Priority"), t("Measure"), t("Status")],
                    [[o.get("id"), o.get("text"), o.get("priority"), o.get("measurable_criterion") or "", o.get("status") or ""]
                     for o in objs])
    else:
        c.pkg.open("No objectives recorded", "team_leader")
    sc = need.get("success_criteria") or []
    c.pkg.h2(t("Success criteria"))
    if sc:
        c.pkg.bullets([s if isinstance(s, str) else (s.get("text") or s.get("criterion") or str(s)) for s in sc])
    else:
        c.pkg.p("No success criteria recorded." if t.lang != "fr" else "Aucun critère de succès enregistré.")
        c.pkg.open("Success criteria not recorded (mission need editor, W1.06)", "D W1.06")


def _concept(c: Ctx) -> None:
    t, need = c.t, c.sx.get("need") or {}
    c.pkg.h1(t("Concept and alternatives") + c.mat("concept_report"))
    alts = need.get("alternatives_considered") or []
    if alts:
        c.pkg.table([t("Name"), t("Type"), "Pros" if t.lang != "fr" else "Avantages",
                     "Cons" if t.lang != "fr" else "Inconvénients", t("Decision")],
                    [[a.get("name"), a.get("type") or "", "; ".join(a.get("pros") or []), "; ".join(a.get("cons") or []),
                      a.get("decision") or ""] for a in alts])
        if not any(a.get("pros") or a.get("cons") for a in alts):
            c.pkg.open("Alternatives have no pros and cons recorded", "systems_engineer")
    else:
        c.pkg.open("No alternatives recorded", "systems_engineer")
    sel = next((a for a in alts if a.get("id") == need.get("selected_alternative_id")), None)
    if sel:
        c.pkg.p(("Selected concept: " if t.lang != "fr" else "Concept retenu : ") + str(sel.get("name")))
    c.pkg.p(need.get("selection_rationale") or "")


def _trades(c: Ctx) -> None:
    t, sx = c.t, c.sx
    c.pkg.h1(t("Trade-offs and decisions") + c.mat("trade_reports"))
    items = (sx.get("trades") or {}).get("items") or []
    if items:
        rows = []
        for it in items:
            st = it.get("state") if isinstance(it.get("state"), dict) else {}
            rows.append([it.get("id"), it.get("title") or st.get("title") or "", it.get("decision") or st.get("decision") or "",
                         it.get("status") or st.get("status") or ""])
        c.pkg.table([t("ID"), t("Name"), t("Decision"), t("Status")], rows)
    else:
        c.pkg.p("No trade study recorded in the study." if t.lang != "fr" else "Aucune étude de compromis enregistrée.")
        c.pkg.open("Trade studies T-01... are not recorded (multiple trades, W6)", "D W6")
    decs = (sx.get("decisions") or {}).get("items") or []
    if decs:
        c.pkg.h2("Decision records" if t.lang != "fr" else "Registre des décisions")
        c.pkg.table([t("ID"), t("Decision"), t("Rationale"), t("Status")],
                    [[d.get("id"), d.get("title") or d.get("decision") or "", d.get("rationale") or "", d.get("status") or ""]
                     for d in decs])


def _conops(c: Ctx) -> None:
    t, sx, view = c.t, c.sx, c.view
    c.pkg.h1(t("Concept of operations") + c.mat("conops"))
    c.pkg.p((sx.get("need") or {}).get("conops_summary") or "")
    modes = (sx.get("modes") or {}).get("modes") or []
    if modes:
        c.pkg.table([t("Mode"), t("Kind"), t("Pointing"), t("Share of orbit"), "Sunlit only" if t.lang != "fr" else "Éclairé seulement"],
                    [[m.get("name"), m.get("kind"), m.get("pointing"), _fmt(m.get("orbit_fraction"), 2),
                      bool(m.get("sunlit_only"))] for m in modes],
                    caption=f"{len(modes)} modes, {len((sx.get('modes') or {}).get('transitions') or [])} transitions")
    else:
        c.pkg.open("No mode set recorded (Modes tab)", "H")
    st = view.stations()
    if st:
        c.pkg.h2("Ground segment" if t.lang != "fr" else "Segment sol")
        c.pkg.table([t("Station"), t("Latitude"), t("Longitude"), t("Bands"), "Antenna (m)" if t.lang != "fr" else "Antenne (m)",
                     "Min. elevation (deg)" if t.lang != "fr" else "Élévation min. (deg)"],
                    [[s.get("name"), (s.get("performance") or {}).get("lat"), (s.get("performance") or {}).get("lon"),
                      (s.get("performance") or {}).get("bands") or [], (s.get("performance") or {}).get("antenna_m"),
                      (s.get("performance") or {}).get("min_elevation_deg")] for s in st])
    contacts = sx.get("contacts") or {}
    if is_stub(contacts) or not contacts.get("stations"):
        c.pkg.open("Contact table per station and union (min/day, passes, longest gap)", stub_owner(contacts) or "H W4.05")
    else:
        _contacts_table(c, contacts)


def _contacts_table(c: Ctx, contacts: dict) -> None:
    t = c.t
    rows = []
    for s in contacts.get("stations") or []:
        rows.append([s.get("name"), s.get("min_per_day") or s.get("contact_min_per_day"), s.get("passes_per_day"),
                     s.get("mean_pass_min"), s.get("max_pass_min")])
    u = contacts.get("union") or {}
    if u:
        rows.append(["union" if t.lang != "fr" else "union", u.get("min_per_day"), u.get("passes_per_day"),
                     u.get("mean_pass_min"), u.get("max_pass_min")])
    c.pkg.table([t("Station"), "min/day" if t.lang != "fr" else "min/jour", "passes/day" if t.lang != "fr" else "passages/jour",
                 "mean pass (min)" if t.lang != "fr" else "passage moyen (min)", "max pass (min)" if t.lang != "fr" else "passage max (min)"], rows)
    if u.get("longest_gap_h") is not None:
        c.pkg.p(("Longest gap without contact: " if t.lang != "fr" else "Plus longue interruption sans contact : ")
                + f"{_fmt(u.get('longest_gap_h'), 1)} h")


def _mission_analysis(c: Ctx) -> None:
    t, view, sx = c.t, c.view, c.sx
    c.pkg.h1(t("Mission analysis") + c.mat("mission_analysis"))
    d = view.definition()
    o = (sx.get("mission") or {}).get("orbit") or {}
    rows = [["Orbit type" if t.lang != "fr" else "Type d’orbite", o.get("orbit_type")],
            ["Altitude (km)", o.get("altitude_km")],
            ["Inclination (deg)" if t.lang != "fr" else "Inclinaison (deg)", o.get("inclination_deg")],
            ["Local time of ascending node" if t.lang != "fr" else "Heure locale du nœud ascendant", o.get("ltan")],
            ["Period (min)" if t.lang != "fr" else "Période (min)", o.get("period_min")],
            ["Eclipse (min / fraction)" if t.lang != "fr" else "Éclipse (min / fraction)",
             f"{_fmt(o.get('eclipse_duration_min'), 1)} / {_fmt(o.get('eclipse_fraction'), 3)}"],
            ["Orbits per day" if t.lang != "fr" else "Orbites par jour", o.get("orbits_per_day")],
            ["Mission duration (y)" if t.lang != "fr" else "Durée de mission (a)", o.get("mission_duration_years")],
            ["Design lifetime (y)" if t.lang != "fr" else "Durée de vie de conception (a)", d.get("design_lifetime_years")],
            ["Launch date target" if t.lang != "fr" else "Date de lancement visée", d.get("launch_date_target")],
            ["Deorbit required" if t.lang != "fr" else "Désorbitation requise", o.get("deorbit_required")]]
    c.pkg.table([t("Item"), t("Value")], [r for r in rows if r[1] not in (None, "")])
    cons = d.get("constraints") or {}
    if cons:
        c.pkg.h2("Mission constraints" if t.lang != "fr" else "Contraintes de mission")
        c.pkg.table([t("Item"), t("Value")], [[k, v] for k, v in cons.items()])
    pls = d.get("payloads") or []
    if pls:
        c.pkg.h2("Payload complement" if t.lang != "fr" else "Charges utiles")
        c.pkg.table([t("Name"), t("Type"), t("Mass (kg)"), t("Power (W)"), "Peak (W)" if t.lang != "fr" else "Crête (W)",
                     "Data per day (GB)" if t.lang != "fr" else "Données par jour (Go)", t("Description")],
                    [[p.get("name"), p.get("type"), p.get("mass_kg"), p.get("power_w"), p.get("power_peak_w"),
                      p.get("data_volume_per_day_gb"), p.get("description") or ""] for p in pls])
    _analysis_runs(c, ("mission_simulation", "ground_segment"))


_RESULT_SKIP = ("_id", "run_id")


def _scalar_summary(summary: dict) -> list[list[Any]]:
    rows = []
    for k in sorted(summary or {}):
        v = summary[k]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or k.endswith(_RESULT_SKIP):
            continue
        rows.append([k, float(v)])
    return rows


def _analysis_runs(c: Ctx, which: tuple[str, ...]) -> None:
    t = c.t
    runs = (c.sx.get("analyses") or {}).get("last_runs") or {}
    for a in which:
        run = runs.get(a)
        title = {"mission_simulation": "Mission simulation", "ground_segment": "Ground-segment analysis",
                 "physics": "Physics (mass properties, disturbance torques)", "fmeca": "FMECA",
                 "vv": "V&V analysis"}.get(a, a)
        if not run:
            c.pkg.open(f"{title}: not run", "systems_engineer")
            continue
        c.pkg.h2(f"{title} ({t('Run')} {str(run.get('finished_at') or run.get('started_at') or '')[:19]})")
        summary = run.get("summary") or {}
        stations = summary.get("stations") if isinstance(summary.get("stations"), list) else []
        all_excluded = bool(stations) and all(s.get("status") == "excluded" for s in stations)
        rows = _scalar_summary(summary)
        if rows and not all_excluded:
            c.pkg.table([t("Result"), t("Value")], rows)
        elif all_excluded:
            c.pkg.p("Every station was excluded by this run, so its link and data-return results are not quoted; "
                    "the contact geometry below is." if t.lang != "fr" else
                    "Toutes les stations ont été exclues par cette exécution : ses résultats de liaison et de retour "
                    "de données ne sont pas cités ; la géométrie des contacts ci-dessous l’est.")
        if stations:
            c.pkg.table([t("Station"), "contacts/day" if t.lang != "fr" else "contacts/jour",
                         "min/day" if t.lang != "fr" else "min/jour", t("Status")],
                        [[s.get("name"), s.get("contacts_per_day"), s.get("contact_min_per_day"), s.get("status")]
                         for s in stations])
            excluded = [s for s in stations if s.get("status") == "excluded"]
            if excluded:
                c.pkg.open(f"The ground-segment analysis excluded {len(excluded)} of {len(stations)} stations "
                           f"(band mismatch with the analysis assumptions); its data-return figures are not usable",
                           "H W4.05")
        if run.get("status") not in (None, "done", "ok", "complete", "completed", "succeeded"):
            c.pkg.open(f"{title}: last run status {run.get('status')}", "systems_engineer")


def _requirements(c: Ctx) -> None:
    t, view = c.t, c.view
    c.pkg.h1(t("Requirements") + c.mat("trs"))
    counts = (c.sx.get("requirements") or {}).get("counts") or {}
    user = view.user_requirements()
    gen = [r for r in view.requirements() if r.get("generated_interface")]
    by_level = counts.get("by_level") or {}
    c.pkg.p((f"{len(user)} requirements entered by the team"
             + (f" and {len(gen)} interface requirements generated from the links (in the IRD)" if gen else "")
             + ". By level: " + ", ".join(f"{k} {v}" for k, v in by_level.items()) + ".")
            if t.lang != "fr" else
            (f"{len(user)} exigences saisies par l’équipe"
             + (f" et {len(gen)} exigences d’interface générées à partir des liaisons (dans le DEI)" if gen else "")
             + ". Par niveau : " + ", ".join(f"{k} {v}" for k, v in by_level.items()) + "."))
    by_type: dict[str, int] = {}
    for r in user:
        by_type[r.get("req_type") or "—"] = by_type.get(r.get("req_type") or "—", 0) + 1
    if by_type:
        c.pkg.table([t("Type"), t("Count")], [[k, v] for k, v in sorted(by_type.items())])
    if user:
        c.pkg.table([t(h) for h in REQ_HEADERS], requirement_rows(view, user),
                    caption=("Every requirement the team entered, by level then code (no truncation)"
                             if t.lang != "fr" else "Toutes les exigences saisies par l’équipe, par niveau puis code"))
        no_th = [r for r in user if r.get("req_type") == "performance" and r.get("threshold_value") in (None, "")]
        if no_th:
            c.pkg.open(f"{len(no_th)} performance requirements have no threshold", "systems_engineer")
        no_alloc = [r for r in user if not r.get("element_id")]
        if no_alloc:
            c.pkg.open(f"{len(no_alloc)} requirements are not allocated to an element", "R W2.09")
    else:
        c.pkg.open("No requirements entered", "systems_engineer")


def _functions(c: Ctx) -> None:
    t = c.t
    c.pkg.h1(t("Function tree") + c.mat("function_tree"))
    fns = (c.sx.get("functions") or {}).get("items") or []
    if fns:
        c.pkg.table([t("Code"), t("Name"), t("Allocated to")],
                    [[f.get("code") or "", ("\u2003" * int(f.get("depth") or 0)) + str(f.get("name") or ""),
                      ", ".join(f.get("allocated_to") or [])] for f in fns])
    else:
        c.pkg.p("No function tree recorded (Functions tab)." if t.lang != "fr" else "Aucun arbre fonctionnel enregistré.")
        c.pkg.open("Function tree not recorded (Functions tab)", "systems_engineer")


def _product_tree(c: Ctx) -> None:
    t, view = c.t, c.view
    c.pkg.h1(t("Product tree and equipment list") + c.mat("product_tree"))
    tree = [e for e in view.elements if e.get("element_type") != "component"]
    if tree:
        c.pkg.table([t("Name"), t("Type"), "Segment", t("Owner")],
                    [[("\u2003" * int(e.get("depth") or 0)) + str(e.get("name") or ""), e.get("element_type"),
                      view.segment_of(e) or "", e.get("owner_position") or ""] for e in _tree_order(view, tree)],
                    caption="Product tree (segments, systems, subsystems, stations)" if t.lang != "fr" else "Arbre produit")
    eq = view.equipment()
    units = {u.get("element_id"): u for u in ((c.sx.get("rollup") or {}).get("mass") or {}).get("units") or []}
    c.pkg.h2("Equipment list" if t.lang != "fr" else "Liste des équipements")
    if eq:
        c.pkg.table([t("Subsystem"), t("Name"), t("Qty"), t("Mass (kg)"), t("Power (W)"), t("TRL"), t("Cat."), t("KB id")],
                    [[view.subsystem_of(e), e.get("name"), e.get("quantity") or 1, e.get("mass_kg"), e.get("power_avg_w"),
                      e.get("trl"), (units.get(e["id"]) or {}).get("category") or (e.get("performance") or {}).get("maturity_category") or "",
                      e.get("kb_component_id") or "custom"] for e in sorted(eq, key=lambda x: (view.subsystem_of(x), str(x.get("name"))))],
                    caption=(f"{len(eq)} equipment lines (space segment components)" if t.lang != "fr"
                             else f"{len(eq)} lignes d’équipement (composants du segment spatial)"))
    else:
        c.pkg.open("No equipment selected", "systems_engineer")


def _tree_order(view: View, els: list[dict]) -> list[dict]:
    ids = {e["id"] for e in els}
    kids: dict[Any, list[dict]] = {}
    for e in els:
        kids.setdefault(e.get("parent_id") if e.get("parent_id") in ids else None, []).append(e)
    out: list[dict] = []

    def walk(p, n):
        for e in sorted(kids.get(p, []), key=lambda x: str(x.get("name") or "")):
            out.append(e)
            if n < 50:
                walk(e["id"], n + 1)
    walk(None, 0)
    return out


def mass_by_subsystem(view: View, rollup: dict) -> list[dict]:
    units = (rollup.get("mass") or {}).get("units") or []
    agg: dict[str, dict] = {}
    for u in units:
        el = view.by_id.get(u.get("element_id")) or {}
        sub = view.subsystem_of(el) if el else ""
        a = agg.setdefault(sub or "—", {"subsystem": sub or "—", "cbe": 0.0, "with_margin": 0.0, "lines": 0})
        a["cbe"] += float(u.get("cbe") or 0)
        a["with_margin"] += float(u.get("with_margin") or 0)
        a["lines"] += 1
    return sorted(agg.values(), key=lambda a: -a["cbe"])


def _budgets(c: Ctx) -> None:
    t, sx, view = c.t, c.sx, c.view
    c.pkg.h1(t("Technical budgets") + c.mat("budgets"))
    ru = sx.get("rollup") or {}
    m, pw = ru.get("mass") or {}, ru.get("power") or {}
    cross = c.extras.get("crosscheck") or {}
    c.pkg.h2(t("Mass budget"))
    c.pkg.table([t("Subsystem"), "CBE (kg)" if t.lang != "fr" else "MEA (kg)", "With maturity margin (kg)" if t.lang != "fr" else "Avec marge de maturité (kg)"],
                [[a["subsystem"], round(a["cbe"], 3), round(a["with_margin"], 3)] for a in mass_by_subsystem(view, ru)])
    lim = _num(m.get("limit_kg"))
    rows = [["Current best estimate (kg)" if t.lang != "fr" else "Meilleure estimation actuelle (kg)", m.get("cbe_kg"), cross.get("mass_nominal_kg")],
            ["With maturity margins (kg)" if t.lang != "fr" else "Avec marges de maturité (kg)", m.get("with_maturity_kg"), ""],
            [f"With system margin {_fmt(m.get('system_margin_percent'), 0)} % at {str(ru.get('gate') or '').upper()} (kg)"
             if t.lang != "fr" else f"Avec marge système {_fmt(m.get('system_margin_percent'), 0)} % à {str(ru.get('gate') or '').upper()} (kg)",
             m.get("with_system_margin_kg"), cross.get("mass_with_margin_kg")],
            ["Harness (kg)" if t.lang != "fr" else "Harnais (kg)", m.get("harness_kg"), ""],
            ["Total dry incl. harness (kg)" if t.lang != "fr" else "Masse sèche totale avec harnais (kg)", m.get("total_dry_kg"), ""],
            [f"Limit (kg, {m.get('limit_source') or ''})" if t.lang != "fr" else f"Limite (kg, {m.get('limit_source') or ''})", m.get("limit_kg"), ""]]
    if lim and _num(m.get("with_system_margin_kg")):
        rows.append(["Margin to limit (kg)" if t.lang != "fr" else "Marge par rapport à la limite (kg)",
                     round(lim - float(m["with_system_margin_kg"]), 3), ""])
    c.pkg.table([t("Item"), t("Value"), t("Parametric cross-check")], rows,
                caption=("Roll-up of the selected equipment (leaf units x quantity); the cross-check column is the "
                         "parametric design loop, for comparison only" if t.lang != "fr" else
                         "Cumul des équipements choisis ; la colonne de contrôle provient de la boucle paramétrique"))
    c.pkg.h2(t("Margin ladder"))
    lad = m.get("ladder") or {}
    if lad:
        c.pkg.table([t("Gate"), t("With system margin (kg)")], [[g.upper(), v] for g, v in lad.items()])
    c.pkg.h2(t("Power budget"))
    prow = [["Sum of ON powers (W)" if t.lang != "fr" else "Somme des puissances en marche (W)", pw.get("sum_on_power_w"), cross.get("power_w")],
            ["Orbit average, nominal mix (W)" if t.lang != "fr" else "Moyenne orbitale, mélange nominal (W)", pw.get("orbit_average_w"), ""],
            ["Orbit average with system margin (W)" if t.lang != "fr" else "Moyenne orbitale avec marge système (W)", pw.get("orbit_average_with_margin_w"), ""]]
    c.pkg.table([t("Item"), t("Value"), t("Parametric cross-check")], prow, caption=pw.get("orbit_average_source") or "")
    energy = (sx.get("modes") or {}).get("energy") or {}
    emodes = energy.get("modes") or []
    shares = {m.get("id"): m.get("orbit_fraction") for m in (sx.get("modes") or {}).get("modes") or []}
    if emodes:
        c.pkg.table([t("Mode"), t("Share of orbit"), t("Power CBE (W)"), t("With margins (W)"), t("Energy per orbit (Wh)"),
                     t("DoD (%)"), t("Status")],
                    [[e.get("name"), _fmt(shares.get(e.get("mode_id")), 2), e.get("power_cbe_w"), e.get("power_total_w"),
                      e.get("energy_load_wh"), e.get("dod_percent"), e.get("status")] for e in emodes],
                    caption="Energy balance per mode (Modes tab)" if t.lang != "fr" else "Bilan énergétique par mode")
        op = energy.get("operational_orbit") or {}
        if op:
            c.pkg.p((f"Operational orbit: generated {_fmt(op.get('generated_wh'))} Wh, needed {_fmt(op.get('needed_wh'))} Wh, "
                     f"balance {_fmt(op.get('balance_wh'))} Wh, depth of discharge {_fmt(op.get('dod_percent'), 1)} % ({op.get('status')}).")
                    if t.lang != "fr" else
                    (f"Orbite opérationnelle : produite {_fmt(op.get('generated_wh'))} Wh, nécessaire {_fmt(op.get('needed_wh'))} Wh, "
                     f"bilan {_fmt(op.get('balance_wh'))} Wh, profondeur de décharge {_fmt(op.get('dod_percent'), 1)} % ({op.get('status')})."))
    else:
        c.pkg.open("Power by mode not available (no modes or no energy balance)", "H")
    _data_budget(c)
    _link_budget(c)
    _pointing(c)


def _data_budget(c: Ctx) -> None:
    t, sx, view = c.t, c.sx, c.view
    c.pkg.h2(t("Data budget"))
    pls = view.definition().get("payloads") or []
    gen = sum(float(p.get("data_volume_per_day_gb") or 0) for p in pls)
    if pls:
        c.pkg.p((f"Payload data generated per day (payload definition): {gen * 1000:.0f} MB."
                 if t.lang != "fr" else f"Données de charge utile produites par jour (définition) : {gen * 1000:.0f} Mo."))
    db = sx.get("data_budget") or {}
    if is_stub(db) or not (db.get("daily") or db.get("cases")):
        c.pkg.open("Daily data budget against the downlink (generated, stored, downlinked, margin)", stub_owner(db) or "H W3.02")
    else:
        daily = db.get("daily") or {}
        if daily:
            c.pkg.table([t("Item"), t("Value")], [[k, v] for k, v in daily.items() if not isinstance(v, (dict, list))])
        for case in db.get("cases") or []:
            if isinstance(case, dict):
                c.pkg.p(", ".join(f"{k} {_cell(v)}" for k, v in case.items() if not isinstance(v, (dict, list))))
    hk = ((sx.get("cdr") or {}).get("budget") or {})
    if hk:
        rows = [[k, v] for k, v in hk.items() if isinstance(v, (int, float, str)) and not isinstance(v, bool)]
        if rows:
            c.pkg.table([t("Item"), t("Value")], rows, caption="Housekeeping downlink budget (CDR model)" if t.lang != "fr"
                        else "Bilan de télémesure de servitude (modèle CDR)")


def _link_budget(c: Ctx) -> None:
    t, sx, view = c.t, c.sx, c.view
    c.pkg.h2(t("Link budget"))
    cons = view.definition().get("constraints") or {}
    links = sx.get("links") or {}
    dc = {k: v for k, v in (links.get("design_case") or {}).items() if v not in (None, "", [])}
    rows = []
    for k in ("downlink_band_mhz", "uplink_band_mhz"):
        if cons.get(k):
            rows.append([k, cons[k]])
    rows += [[k, v] for k, v in dc.items()]
    ttc = ((sx.get("cdr") or {}).get("rows") or {}).get("ttc") or []
    for r in ttc[:1]:
        rows += [[f"ttc.{k}", v] for k, v in (r.get("data") or {}).items() if not isinstance(v, (dict, list))]
    radios = [e for e in view.equipment() if (e.get("subsystem_domain") or "") in ("communications", "ttc", "comms")]
    rows += [["radio equipment" if t.lang != "fr" else "équipement radio", e.get("name")] for e in radios]
    if rows:
        c.pkg.table([t("Item"), t("Value")], rows)
    items = links.get("items") or []
    if items:
        c.pkg.table(["Case" if t.lang != "fr" else "Cas", t("Station"), "Direction", "Rate" if t.lang != "fr" else "Débit",
                     "Margin (dB)" if t.lang != "fr" else "Marge (dB)"],
                    [[i.get("name") or i.get("id"), i.get("station") or "", i.get("direction") or "",
                      i.get("rate_bps") or i.get("rate") or "", i.get("margin_db")] for i in items])
    else:
        c.pkg.open("Named link-budget cases (per station, rate tier, direction) are not stored", "D W4.04")
    if not dc:
        c.pkg.open("The link design case (requirements.link) is empty: apply a link budget to the design", "comms_engineer")


def _pointing(c: Ctx) -> None:
    t, sx, view = c.t, c.sx, c.view
    c.pkg.h2(t("Pointing budget"))
    rows = [[f"{p.get('name')}: pointing accuracy (deg)" if t.lang != "fr" else f"{p.get('name')} : précision de pointage (deg)",
             p.get("pointing_accuracy_deg")] for p in view.definition().get("payloads") or [] if p.get("pointing_accuracy_deg") is not None]
    phys = ((sx.get("analyses") or {}).get("last_runs") or {}).get("physics") or {}
    for k, v in sorted((phys.get("summary") or {}).items()):
        if k.startswith("aocs_") and isinstance(v, (int, float)) and not isinstance(v, bool):
            rows.append([k, float(v)])
    if rows:
        c.pkg.table([t("Item"), t("Value")], rows)
    else:
        c.pkg.open("Pointing budget: no payload pointing requirement and no physics run", "aocs_engineer")


def _design(c: Ctx) -> None:
    t, view = c.t, c.view
    c.pkg.h1(t("Design definition and justification") + c.mat("design_files"))
    subs = [e for e in view.elements if e.get("element_type") == "subsystem" and (view.segment_of(e) or "space") == "space"]
    eq = view.equipment()
    for s in sorted(subs, key=lambda x: str(x.get("name"))):
        comps = [e for e in eq if s in view.ancestors(e)]
        c.pkg.h2(str(s.get("name")))
        if s.get("description"):
            c.pkg.p(s["description"])
        perf = s.get("performance") or {}
        if isinstance(perf, dict) and perf:
            c.pkg.p("; ".join(f"{k}: {_cell(v)}" for k, v in perf.items() if not isinstance(v, (dict,))))
        if comps:
            c.pkg.bullets([f"{e.get('name')} (x{e.get('quantity') or 1}, {_cell(e.get('mass_kg'))} kg, {_cell(e.get('power_avg_w'))} W, "
                           f"TRL {e.get('trl') or '?'})" + (f": {e.get('description')}" if e.get("description") else "")
                           for e in comps])
        else:
            c.pkg.open(f"Subsystem {s.get('name')}: no equipment selected", s.get("owner_position") or "systems_engineer")
    _analysis_runs(c, ("physics", "fmeca"))


def _interfaces(c: Ctx) -> None:
    t, view = c.t, c.view
    c.pkg.h1(t("Interfaces") + c.mat("interfaces"))
    ifs = (c.sx.get("elements") or {}).get("interfaces") or []
    by_type: dict[str, int] = {}
    for i in ifs:
        k = str(i.get("interface_type") or i.get("type") or "—")
        by_type[k] = by_type.get(k, 0) + 1
    if ifs:
        c.pkg.table([t("Type"), t("Count")], [[k, v] for k, v in sorted(by_type.items())],
                    caption=f"{len(ifs)} interfaces; the full list is in the IRD and data/interfaces.csv" if t.lang != "fr"
                    else f"{len(ifs)} interfaces ; la liste complète est dans le DEI et data/interfaces.csv")
    else:
        c.pkg.open("No interfaces recorded", "systems_engineer")
    ir = [r for r in view.requirements() if r.get("level") == "interface" or r.get("generated_interface")]
    if ir:
        c.pkg.table([t(h) for h in REQ_HEADERS], requirement_rows(view, ir),
                    caption="Interface requirements" if t.lang != "fr" else "Exigences d’interface")


def _verification(c: Ctx) -> None:
    t, sx, view = c.t, c.sx, c.view
    c.pkg.h1(t("Verification and AIV") + c.mat("aiv_plan"))
    items = (sx.get("verification") or {}).get("items") or []
    if items:
        def agg(key):
            out: dict[str, int] = {}
            for v in items:
                out[str(v.get(key) or "—")] = out.get(str(v.get(key) or "—"), 0) + 1
            return out
        rows = [["method" if t.lang != "fr" else "méthode", k, n] for k, n in sorted(agg("method").items())]
        rows += [["level" if t.lang != "fr" else "niveau", k, n] for k, n in sorted(agg("level").items())]
        rows += [["stage" if t.lang != "fr" else "étape", k, n] for k, n in sorted(agg("phase").items())]
        rows += [["status" if t.lang != "fr" else "état", k, n] for k, n in sorted(agg("status").items())]
        c.pkg.table([t("Item"), t("Value"), t("Count")], rows,
                    caption=f"{len(items)} verification items (the VCD lists each one)" if t.lang != "fr"
                    else f"{len(items)} éléments de vérification (le DCV les liste)")
    else:
        c.pkg.open("No verification items (run the V&V analysis)", "systems_engineer")
    ait = sx.get("ait") or {}
    c.pkg.h2("Model philosophy and test programme" if t.lang != "fr" else "Philosophie des modèles et programme d’essais")
    if is_stub(ait) or not (ait.get("models") or ait.get("tests")):
        pa = [r for r in view.user_requirements() if "model" in str(r.get("text") or "").lower()
              and str(r.get("code") or "").upper().startswith(("PA", "SYS-PA", "PRG"))]
        if pa:
            c.pkg.bullets([f"{r.get('code')}: {r.get('text')}" for r in pa])
        c.pkg.open("Model philosophy and AIT programme (models, test matrix, facilities)", stub_owner(ait) or "A W8a")
    else:
        if ait.get("models"):
            c.pkg.table([t("Name"), t("Description")], [[m.get("name") or m.get("id"), m.get("purpose") or m.get("description") or ""]
                                                       for m in ait["models"]])
        if ait.get("tests"):
            c.pkg.table([t("ID"), t("Name"), t("Status")], [[x.get("id"), x.get("name") or x.get("type"), x.get("status")] for x in ait["tests"]])


def _trl(c: Ctx) -> None:
    t, view = c.t, c.view
    c.pkg.h1(t("Technology readiness") + c.mat("trl_matrix"))
    eq = view.equipment()
    units = {u.get("element_id"): u for u in ((c.sx.get("rollup") or {}).get("mass") or {}).get("units") or []}
    rows = [[e.get("name"), view.subsystem_of(e), e.get("trl"), (units.get(e["id"]) or {}).get("category") or
             (e.get("performance") or {}).get("maturity_category") or ""] for e in sorted(eq, key=lambda x: (_num(x.get("trl")) or 0, str(x.get("name"))))]
    if rows:
        c.pkg.table([t("Name"), t("Subsystem"), t("TRL"), t("Cat.")], rows,
                    caption="Maturity category: A/B off the shelf, C modified, D new (margin policy)" if t.lang != "fr"
                    else "Catégorie de maturité : A/B sur étagère, C modifié, D nouveau")
        low = [e for e in eq if (_num(e.get("trl")) or 0) < 6]
        if low:
            c.pkg.open(f"{len(low)} equipment items below TRL 6: " + ", ".join(str(e.get("name")) for e in low), "systems_engineer")
    else:
        c.pkg.open("No equipment, so no TRL table", "systems_engineer")


def _risks(c: Ctx) -> None:
    t = c.t
    c.pkg.h1(t("Risk register") + c.mat("risk_register"))
    items = (c.sx.get("risks") or {}).get("items") or []
    if items:
        c.pkg.table([t("ID"), t("Risk"), t("Category"), t("L"), t("C"), t("Score"), t("Owner"), t("Status"), t("Mitigation")],
                    [[r.get("id"), r.get("description") or r.get("title") or "", r.get("category") or "", r.get("likelihood"),
                      r.get("consequence"), r.get("score"), r.get("owner") or "", r.get("status") or "", r.get("mitigation") or ""]
                     for r in items],
                    caption=(f"{len(items)} risks, highest likelihood x consequence first" if t.lang != "fr"
                             else f"{len(items)} risques, du plus élevé au plus faible"))
        red = [r for r in items if (r.get("score") or 0) >= 16 and (r.get("status") or "open") != "closed"]
        if red:
            c.pkg.open(f"{len(red)} risks scored 16 or more remain open: " + ", ".join(str(r.get("id")) for r in red), "team_leader")
    else:
        c.pkg.open("Risk register is empty", "team_leader")


def _cost_schedule(c: Ctx) -> None:
    t, view, sx = c.t, c.view, c.sx
    c.pkg.h1(t("Cost and schedule") + c.mat("cost_schedule"))
    eq = view.equipment()
    agg: dict[str, list[float]] = {}
    for e in eq:
        a = agg.setdefault(view.subsystem_of(e), [0.0, 0.0])
        a[0] += float(e.get("cost_recurring_keur") or 0) * int(e.get("quantity") or 1)   # per-unit cost x quantity
        a[1] += float(e.get("cost_nre_keur") or 0)
    if agg:
        rows = [[k, round(v[0], 1), round(v[1], 1)] for k, v in sorted(agg.items())]
        rows.append(["Total", round(sum(v[0] for v in agg.values()), 1), round(sum(v[1] for v in agg.values()), 1)])
        c.pkg.table([t("Subsystem"), t("Recurring (k€)"), t("Non-recurring (k€)")], rows,
                    caption="Equipment cost as entered on the elements (flight hardware)" if t.lang != "fr"
                    else "Coût des équipements saisi sur les éléments (matériel de vol)")
    tc = view.definition().get("target_cost_meur")
    if tc:
        c.pkg.p(("Cost target: " if t.lang != "fr" else "Objectif de coût : ") + f"{tc} M€")
    sch = sx.get("schedule") or {}
    if is_stub(sch) or not (sch.get("milestones") or sch.get("work_packages")):
        ld = view.definition().get("launch_date_target")
        if ld:
            c.pkg.p(("Launch date target: " if t.lang != "fr" else "Date de lancement visée : ") + str(ld))
        c.pkg.open("Schedule, milestones, WBS and long-lead items", stub_owner(sch) or "A W11a")
    else:
        c.pkg.table([t("Name"), "Date", t("Status")], [[m.get("name") or m.get("id"), m.get("date") or m.get("due") or "", m.get("status") or ""]
                                                       for m in sch.get("milestones") or []])


def _debris(c: Ctx) -> None:
    t, view = c.t, c.view
    c.pkg.h1(t("Debris mitigation and disposal") + c.mat("debris"))
    cons = view.definition().get("constraints") or {}
    rows = [[k, v] for k, v in cons.items() if any(s in k for s in ("disposal", "collision", "apogee", "casualty"))]
    o = view.definition().get("orbit") or {}
    rows.insert(0, ["Altitude (km)", o.get("altitude_km")])
    if o.get("deorbit_required") is not None:
        rows.append(["deorbit_required", o.get("deorbit_required")])
    if view.definition().get("disposal_method"):
        rows.append(["disposal_method", view.definition().get("disposal_method")])
    c.pkg.table([t("Item"), t("Value")], rows)
    dev = [e for e in view.equipment() if str(e.get("kb_component_id") or "").startswith("deorb")
           or "sail" in str(e.get("name") or "").lower() or "deorbit" in str(e.get("name") or "").lower()]
    if dev:
        c.pkg.bullets([f"{e.get('name')} ({view.subsystem_of(e)}, {_cell(e.get('mass_kg'))} kg)" for e in dev])
    else:
        c.pkg.open("No disposal device in the design", "propulsion_engineer")
    c.pkg.p("The lifetime and compliance figures are in the disposal and debris mitigation report of this pack."
            if t.lang != "fr" else "La durée de vie orbitale et la conformité figurent dans le rapport d’élimination de ce dossier.")


def _spectrum(c: Ctx) -> None:
    t, sx, view = c.t, c.sx, c.view
    c.pkg.h1(t("Spectrum and licensing") + c.mat("spectrum"))
    cons = view.definition().get("constraints") or {}
    rows = [[k, v] for k, v in cons.items() if "band" in k or "mhz" in k]
    rows += [["ground station bands" if t.lang != "fr" else "bandes des stations sol",
              f"{s.get('name')}: {_cell((s.get('performance') or {}).get('bands') or [])}"] for s in view.stations()]
    if rows:
        c.pkg.table([t("Item"), t("Value")], rows)
    lic = sx.get("licensing") or {}
    if is_stub(lic) or not (lic.get("filings") or lic.get("assignments")):
        c.pkg.open("Frequency assignments and licence filings (ISED space and earth stations, ITU, RSSSA)",
                   stub_owner(lic) or "L W5")
    else:
        if lic.get("assignments"):
            c.pkg.table([t("Name"), "Frequency (MHz)" if t.lang != "fr" else "Fréquence (MHz)", "Direction", t("Note")],
                        [[a.get("name") or a.get("id"), a.get("frequency_mhz") or a.get("centre_mhz"), a.get("direction") or "",
                          a.get("emission") or a.get("note") or ""] for a in lic["assignments"]])
        if lic.get("filings"):
            c.pkg.table([t("Document"), t("Status"), "Date"], [[f.get("kind") or f.get("name"), f.get("status"),
                                                                f.get("submitted_at") or f.get("date") or ""] for f in lic["filings"]])


def _cds(c: Ctx) -> None:
    t, sx = c.t, c.sx
    c.pkg.h1(t("CubeSat Design Specification compliance") + c.mat("cds_matrix"))
    ru = sx.get("rollup") or {}
    m = ru.get("mass") or {}
    phys = (((sx.get("analyses") or {}).get("last_runs") or {}).get("physics") or {}).get("summary") or {}
    rows = [["Form factor" if t.lang != "fr" else "Format", f"{ru.get('form_factor') or '?'} ({ru.get('form_factor_source')})"],
            ["Mass with system margin vs limit (kg)" if t.lang != "fr" else "Masse avec marge système / limite (kg)",
             f"{_cell(m.get('with_system_margin_kg'))} / {_cell(m.get('limit_kg'))} ({m.get('limit_source') or ''})"]]
    for k in ("mp_total_mass_kg", "mp_com_x_m", "mp_com_y_m", "mp_com_z_m"):
        if phys.get(k) is not None:
            rows.append([k, round(float(phys[k]), 4)])
    c.pkg.table([t("Item"), t("Value")], rows)
    c.pkg.p("The CDS checklist and the deployer interface are in the launch ICD of this pack."
            if t.lang != "fr" else "La liste CDS et l’interface du distributeur figurent dans l’ICD lanceur de ce dossier.")


def _cdr_group(c: Ctx, group: str, title: str, product: str, kinds: tuple[str, ...]) -> None:
    t, cdr = c.t, c.sx.get("cdr") or {}
    c.pkg.h1(t(title) + c.mat(product))
    rows_by_kind = cdr.get("rows") or {}
    any_rows = False
    for k in kinds:
        rows = rows_by_kind.get(k) or []
        if not rows:
            continue
        any_rows = True
        c.pkg.h2(f"{k} ({len(rows)})")
        c.pkg.table([t("Key"), t("Name"), t("Description"), t("Status")],
                    [[r.get("key"), (r.get("data") or {}).get("name") or (r.get("data") or {}).get("label") or "",
                      (r.get("data") or {}).get("description") or (r.get("data") or {}).get("text") or "", r.get("status") or ""]
                     for r in rows])
    if not any_rows:
        c.pkg.open(f"{t(title)}: no rows in the CDR model (propose and accept the {group} rows)", "H")
    if group == "tmtc":
        checks = [x for x in cdr.get("checks") or [] if str(x.get("severity") or x.get("level") or "").lower() in ("error", "fail")]
        if checks:
            c.pkg.open(f"CDR model checks: {len(checks)} errors", "H")


def _tmtc(c: Ctx) -> None:
    _cdr_group(c, "tmtc", "TM/TC database", "tmtc_db", ("settings", "apids", "services", "hk", "commands", "events", "rate_tiers", "ttc"))


def _fdir(c: Ctx) -> None:
    _cdr_group(c, "fdir", "FDIR specification", "fdir_spec", ("monitors", "event_actions", "load_shed", "safe_mode", "fdir_levels"))


def _aocs(c: Ctx) -> None:
    _cdr_group(c, "aocs", "AOCS modes and control", "aocs_design", ("aocs_modes", "aocs_transitions", "aocs_control"))


def _ops(c: Ctx) -> None:
    _cdr_group(c, "ops", "Operations products", "ops_products", ("positions", "gonogo", "flight_rules"))


def _test_results(c: Ctx) -> None:
    t, sx = c.t, c.sx
    c.pkg.h1(t("Test results") + c.mat("test_reports"))
    items = (sx.get("verification") or {}).get("items") or []
    closed = [v for v in items if v.get("status") in ("passed", "waived")]
    c.pkg.p((f"Verification close-out: {len(closed)} of {len(items)} items passed or waived."
             if t.lang != "fr" else f"Clôture de la vérification : {len(closed)} éléments sur {len(items)} réussis ou dispensés."))
    with_ev = [v for v in items if v.get("evidence_ref")]
    if with_ev:
        c.pkg.table(["Item", t("Status"), t("Evidence")], [[v.get("requirement_id"), v.get("status"), v.get("evidence_ref")] for v in with_ev])
    ait = sx.get("ait") or {}
    if is_stub(ait) or not ait.get("tests"):
        c.pkg.open("Test campaign records and test reports", stub_owner(ait) or "A W8a/W8b")
    if len(closed) < len(items):
        c.pkg.open(f"{len(items) - len(closed)} verification items are not closed", "systems_engineer")


def _ncr(c: Ctx) -> None:
    t, sx = c.t, c.sx
    c.pkg.h1(t("Non-conformances and waivers") + c.mat("ncr_waivers"))
    w = [v for v in (sx.get("verification") or {}).get("items") or [] if v.get("status") == "waived"]
    if w:
        c.pkg.table(["Item", t("Note")], [[v.get("requirement_id"), v.get("notes") or ""] for v in w])
    else:
        c.pkg.p("No waived verification item." if t.lang != "fr" else "Aucun élément de vérification dispensé.")
    c.pkg.open("Non-conformance reports (no NCR model yet)", "A W8")


def _as_built(c: Ctx) -> None:
    t, sx = c.t, c.sx
    c.pkg.h1(t("As-built configuration") + c.mat("as_built"))
    m = (sx.get("rollup") or {}).get("mass") or {}
    c.pkg.p((f"Design mass (roll-up): {_cell(m.get('cbe_kg'))} kg CBE. Measured mass properties are not recorded."
             if t.lang != "fr" else f"Masse de conception (cumul) : {_cell(m.get('cbe_kg'))} kg MEA. Les propriétés de masse mesurées ne sont pas enregistrées."))
    c.pkg.open("As-built configuration and measured mass properties (no as-built model yet)", "A W8")


def _launch(c: Ctx) -> None:
    t, view = c.t, c.view
    c.pkg.h1(t("Launch-provider interface") + c.mat("launch_acceptance"))
    ls = [e for e in view.elements if view.segment_of(e) == "launch" and e.get("element_type") != "segment"]
    rows = [["launch_vehicle", view.definition().get("launch_vehicle") or ""],
            ["launch_date_target", view.definition().get("launch_date_target") or ""]]
    rows += [[e.get("name"), e.get("description") or ""] for e in ls]
    c.pkg.table([t("Item"), t("Value")], rows)
    if not view.definition().get("launch_vehicle") and not ls:
        c.pkg.open("Launch vehicle and deployer not selected", "structures_engineer")


def _ops_readiness(c: Ctx) -> None:
    t, cdr = c.t, c.sx.get("cdr") or {}
    c.pkg.h1(t("Operations readiness") + c.mat("ops_readiness"))
    counts = cdr.get("counts") or {}
    c.pkg.table([t("Kind of row"), t("Count")], [[k, counts.get(k, 0)] for k in ("positions", "gonogo", "flight_rules")])
    c.pkg.open("Operations procedures, rehearsals and ground segment validation (no procedure model yet)", "D W8")


def _previous_reviews(c: Ctx) -> None:
    t, gates = c.t, c.sx.get("gates") or {}
    c.pkg.h1(t("Previous reviews") + c.mat("review_record"))
    rows = []
    for g in gates.get("gates") or []:
        s = g.get("summary") or {}
        rows.append([g.get("short") or g.get("id"), g.get("state"), f"{s.get('must_pass_met', 0)}/{s.get('must_pass', 0)}",
                     f"{s.get('pass', 0)} / {s.get('fail', 0)} / {s.get('not_evaluated', 0)}", str(g.get("passed_at") or "")[:19]])
    if rows:
        c.pkg.table([t("Gate"), t("Status"), "Must-pass met" if t.lang != "fr" else "Obligatoires satisfaits",
                     "pass / fail / not evaluated" if t.lang != "fr" else "réussi / échec / non évalué",
                     "Passed at" if t.lang != "fr" else "Franchi le"], rows)
    rids = gates.get("rids") or gates.get("actions") or []
    if rids:
        c.pkg.table([t("ID"), t("Gate"), t("Description"), t("Owner"), t("Status")],
                    [[r.get("id"), r.get("gate"), r.get("description"), r.get("owner"), r.get("status")] for r in rids])
    else:
        c.pkg.open("RID and action log of the previous review", "D W4.08")


def _checklist(c: Ctx) -> None:
    t = c.t
    c.pkg.h1(t("Gate checklist"))
    chk = c.extras.get("checklist") or {}
    crit = chk.get("criteria") or []
    if not crit:
        c.pkg.p("No exit criteria are defined for this review yet." if t.lang != "fr"
                else "Aucun critère de sortie n’est encore défini pour cette revue.")
        if c.plan.gate in ("qr", "ar", "frr"):
            c.pkg.open(f"{c.plan.short} exit criteria (gate profile and criteria file)", "X W4.09")
        return
    rows = [[x.get("id"), x.get("title") or x.get("label") or x.get("description") or x.get("text") or "",
             x.get("status") or x.get("verdict") or "", "yes" if x.get("must_pass") else "",
             x.get("evidence_found") or x.get("evidence") or ""] for x in crit]
    c.pkg.table([t("ID"), t("Criterion"), t("Status"), "Must pass" if t.lang != "fr" else "Obligatoire", t("Evidence")], rows)
    fails = [x for x in crit if x.get("must_pass") and (x.get("status") or x.get("verdict")) not in ("pass",)]
    for x in fails:
        c.pkg.open(f"Must-pass criterion {x.get('id')}: {x.get('title') or x.get('label') or ''} ({x.get('status')})",
                   x.get("owner_seat") or "")


def _open_items(c: Ctx) -> None:
    t, sx = c.t, c.sx
    for name, err in (sx.get("errors") or {}).items():
        c.pkg.open(f"Collector section {name} failed: {err}", "X")
    c.pkg.h1(t("Open items"))
    if c.pkg.open_items:
        c.pkg.table(["#", t("Open item"), t("Owner / work package"), "Section"],
                    [[i + 1, o["text"], o.get("owner") or "", o.get("section") or ""] for i, o in enumerate(c.pkg.open_items)])
    else:
        c.pkg.p("None." if t.lang != "fr" else "Aucun.")


#: section function per product (order = order in the package); ``None`` products are always present
SECTION_PLAN: tuple[tuple[str | None, SectionFn], ...] = (
    (None, _scope),
    (None, _index),
    ("mission_statement|objectives", _mission_statement),
    ("concept_report", _concept),
    ("trade_reports", _trades),
    ("conops", _conops),
    ("mission_analysis", _mission_analysis),
    ("trs", _requirements),
    ("function_tree", _functions),
    ("product_tree", _product_tree),
    ("budgets", _budgets),
    ("design_files", _design),
    ("interfaces", _interfaces),
    ("aiv_plan", _verification),
    ("trl_matrix", _trl),
    ("risk_register", _risks),
    ("cost_schedule", _cost_schedule),
    ("debris", _debris),
    ("spectrum", _spectrum),
    ("cds_matrix", _cds),
    ("tmtc_db", _tmtc),
    ("fdir_spec", _fdir),
    ("aocs_design", _aocs),
    ("ops_products", _ops),
    ("test_reports", _test_results),
    ("ncr_waivers", _ncr),
    ("as_built", _as_built),
    ("launch_acceptance", _launch),
    ("ops_readiness", _ops_readiness),
    ("review_record", _previous_reviews),
    (None, _checklist),
)


def build_package(sx: dict[str, Any], plan: PackPlan, *, lang: str = "en", extras: dict[str, Any] | None = None,
                  date: str | None = None) -> Package:
    """The review data package of ``plan`` for the study ``sx`` (``StudyExport.as_dict()``)."""
    t = Tr("fr" if str(lang or "").lower().startswith("fr") else "en")
    extras = dict(extras or {})
    name = sx.get("study_name") or (sx.get("mission") or {}).get("name") or ""
    date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    pkg = Package(title=f"{t.pick(plan.name)} ({plan.short})", subtitle=t("Review data package"),
                  study_name=name, gate_short=plan.short,
                  document_code=f"SCDF-{plan.short.replace('+', '').replace('/', '')}-RDP", date=date, lang=t.lang)
    ctx = Ctx(pkg=pkg, view=View(sx), plan=plan, t=t, extras=extras)
    # the index is rendered before the open items exist: render everything, then put the open-items
    # section last (it reads the list the other sections filled)
    for product, fn in SECTION_PLAN:
        if product is None or any(plan.has(p) for p in product.split("|")):
            fn(ctx)
    _open_items(ctx)
    return pkg


# ─────────────────────────────────────────────────────────────── renderers

def render_markdown(pkg: Package) -> str:
    out = [f"# {pkg.title} \u2014 {pkg.study_name}", "", f"*{pkg.subtitle}* \u00b7 {pkg.document_code} \u00b7 {pkg.date}", ""]
    for b in pkg.blocks:
        if b.kind == "h1":
            out += [f"## {b.text}", ""]
        elif b.kind == "h2":
            out += [f"### {b.text}", ""]
        elif b.kind == "p":
            out += [b.text, ""]
        elif b.kind == "callout":
            out += [f"> {b.text}", ""]
        elif b.kind == "bullets":
            out += [f"- {i}" for i in b.items] + [""]
        elif b.kind == "table":
            esc = lambda s: str(s).replace("|", "\\|").replace("\n", " ")  # noqa: E731
            out.append("| " + " | ".join(esc(h) for h in b.headers) + " |")
            out.append("|" + "|".join("---" for _ in b.headers) + "|")
            for r in b.rows:
                out.append("| " + " | ".join(esc(x) for x in r) + " |")
            if b.caption:
                out += ["", f"*{b.caption}*"]
            out.append("")
    return "\n".join(out).rstrip() + "\n"


def render_docx(pkg: Package, output: Path | io.BytesIO | None = None) -> bytes:
    from . import theme
    theme.reset_counters()
    doc = theme.new_document()
    theme.add_cover_page(doc, title=f"{pkg.gate_short} \u2014 {pkg.study_name}", subtitle=f"{pkg.title}: {pkg.subtitle}",
                         document_code=pkg.document_code, study_name=pkg.study_name, issue="1.0", date=pkg.date,
                         classification="Internal", cohort="SpaceCDF",
                         publisher="C2O \u2014 from Concept to Orbit \u00b7 du Concept \u00e0 l\u2019Orbite")
    theme.add_page_furniture(doc, running_title=f"SpaceCDF \u2014 {pkg.gate_short} \u2014 {pkg.study_name}",
                             document_code=pkg.document_code, footer_left=f"{pkg.document_code} \u00b7 {pkg.study_name}",
                             footer_right="C2O \u00b7 SpaceCDF")
    theme.add_doc_info_table(doc, document_code=pkg.document_code, title=pkg.title, study_name=pkg.study_name,
                             issue="1.0", date=pkg.date, prepared_by="SpaceCDF (from the study data)",
                             applies_to=pkg.study_name)
    theme.add_toc(doc)
    for b in pkg.blocks:
        if b.kind == "h1":
            doc.add_heading(b.text, level=1)
        elif b.kind == "h2":
            doc.add_heading(b.text, level=2)
        elif b.kind == "p":
            doc.add_paragraph(b.text)
        elif b.kind == "callout":
            theme.add_callout(doc, b.text)
        elif b.kind == "bullets":
            for i in b.items:
                doc.add_paragraph(i, style="List Bullet")
        elif b.kind == "table":
            if b.caption:
                theme.add_table_caption(doc, b.caption)
            theme.styled_table(doc, headers=b.headers, rows=b.rows)
    buf = io.BytesIO()
    doc.save(buf)
    data = buf.getvalue()
    if isinstance(output, Path):
        output.write_bytes(data)
    elif output is not None:
        output.write(data)
    return data


def all_document_ids() -> list[str]:
    return [d.id for d in DOCUMENTS]


__all__ = ["Package", "Block", "View", "build_package", "render_docx", "render_markdown", "requirement_rows",
           "threshold_text", "mass_by_subsystem", "REQ_HEADERS", "GATE_ORDER", "all_document_ids"]
