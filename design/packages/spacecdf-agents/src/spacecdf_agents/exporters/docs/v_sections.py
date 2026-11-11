"""SpaceCDF — the sections of the review data package that carry the systems-engineering V
(wave 3, 3.X2): protocol deliverables, stakeholder register and MOEs, validation plan,
allocation ledger, negotiation records, open items and change proposals (with change control),
interface-control issues, reliability and FMEA, thermal model, assumption register, the
systems-engineering figures, and the payload definition (frames acquired on board next to the
delivered products).

Every section reads one export section (``StudyExport.as_dict()``); the owners fill them in
wave 3 (W0_SEAMS §9.5). Item keys are read as the table columns, with or without ``_json``
(``g``). A section still marked ``not_implemented`` becomes an open item with its owner; an
empty one says so. Nothing is invented.
"""
from __future__ import annotations

from typing import Any

# ─────────────────────────────────────────────────────────────── helpers


def g(obj: Any, *keys: str, default: Any = None) -> Any:
    if not isinstance(obj, dict):
        return default
    for k in keys:
        for kk in (k, k + "_json"):
            v = obj.get(kk)
            if v not in (None, "", [], {}):
                return v
    return default


def lst(v: Any) -> str:
    if v in (None, ""):
        return ""
    if isinstance(v, dict):
        return ", ".join(str(k) for k in v)
    if isinstance(v, (list, tuple)):
        return ", ".join(str(x.get("ref") or x.get("code") or x) if isinstance(x, dict) else str(x) for x in v)
    return str(v)


def num(v: Any) -> float | None:
    try:
        return None if v is None or v == "" else float(v)
    except (TypeError, ValueError):
        return None


def fmt(v: Any, nd: int = 3) -> str:
    x = num(v)
    if x is None:
        return ""
    s = f"{x:.{nd}f}".rstrip("0").rstrip(".")
    return s or "0"


def items(section: Any, key: str = "items") -> list[dict]:
    if not isinstance(section, dict) or section.get("status") == "not_implemented":
        return []
    return [x for x in (section.get(key) or []) if isinstance(x, dict)]


def _stub_or_empty(c, section: dict | None, what: str, default_owner: str) -> bool:
    """True (and an open item) when the section is a stub; also an open item when it is empty."""
    from .study_pack import is_stub, stub_owner
    if is_stub(section):
        c.pkg.p("Not yet available in the study model." if c.t.lang != "fr" else "Pas encore disponible dans le modèle de l’étude.")
        c.pkg.open(f"{what}: not yet in the study model", stub_owner(section) or default_owner)
        return True
    return False


def _fr(c) -> bool:
    return c.t.lang == "fr"


# ─────────────────────────────────────────────────────────────── index: protocol deliverables


def deliverables(c) -> None:
    """Protocol deliverables of the gate with their state and owner (SE-02, from the deliverables
    service of agent S; ``extras["deliverables"]``)."""
    t = c.t
    dl = c.extras.get("deliverables")
    c.pkg.h2("Systems-engineering deliverables of this review" if not _fr(c) else "Livrables d’ingénierie système de cette revue")
    if not isinstance(dl, dict) or dl.get("status") == "not_implemented" or not dl.get("items"):
        c.pkg.p("The deliverables service has not evaluated this gate yet." if not _fr(c)
                else "Le service des livrables n’a pas encore évalué ce jalon.")
        c.pkg.open("Protocol deliverables of the gate (status and owner)", (dl or {}).get("owner") and
                   f"{dl.get('owner')} {dl.get('work_package') or ''}".strip() or "S 3.S2", section=t("Package index"))
        return
    rows = []
    for d in dl["items"]:
        lab = d.get("label")
        rows.append([t.pick(lab) if isinstance(lab, dict) else (lab or d.get("id") or ""), d.get("kind") or "",
                     d.get("owner_seat") or "", d.get("state") or "", d.get("evidence") or d.get("fix") or ""])
    c.pkg.table([t("Item"), t("Kind"), t("Owner"), t("Status"), t("Evidence")], rows,
                caption=(f"Gate {str(dl.get('gate') or c.plan.gate).upper()}: ok = done, warn = partial, missing = not done"
                         if not _fr(c) else f"Jalon {str(dl.get('gate') or c.plan.gate).upper()} : ok = fait, warn = partiel, "
                                             "missing = non fait"))
    for d in dl["items"]:
        if d.get("state") == "missing":
            lab = d.get("label")
            c.pkg.open(f"Deliverable missing: {t.pick(lab) if isinstance(lab, dict) else lab or d.get('id')}",
                       d.get("owner_seat") or "", section=t("Package index"))


# ─────────────────────────────────────────────────────────────── stakeholders and MOEs


def stakeholder_rows(sx: dict) -> tuple[list[dict], list[dict], list[dict]]:
    """(stakeholders, needs, MOEs) from the stakeholders section, else the mission need."""
    st = sx.get("stakeholders") or {}
    sh = items(st)
    if not sh:
        sh = [s for s in (sx.get("need") or {}).get("stakeholders") or [] if isinstance(s, dict)]
    return sh, items(st, "needs"), items(st, "moes")


def is_placeholder(m: dict) -> bool:
    return bool(g(m, "placeholder", default=False)) or "placeholder" in str(g(m, "defined_by", default="")).lower()


def stakeholders(c) -> None:
    t, sx = c.t, c.sx
    fr = _fr(c)
    c.pkg.h1(("Stakeholders, needs and measures of effectiveness" if not fr else
              "Parties prenantes, besoins et mesures d’efficacité") + c.mat("stakeholder_register"))
    st = sx.get("stakeholders") or {}
    sh, needs, moes = stakeholder_rows(sx)
    if not sh:
        c.pkg.p("No stakeholder recorded." if not fr else "Aucune partie prenante enregistrée.")
        from .study_pack import stub_owner
        c.pkg.open("Stakeholder register (category, authority, engagement)", stub_owner(st) or "S 3.S3")
        return
    cats: dict[str, int] = {}
    for s in sh:
        k = str(g(s, "category", default="—")).replace("_", " ")
        cats[k] = cats.get(k, 0) + 1
    c.pkg.p((f"{len(sh)} stakeholders in {len(cats)} categories, {len(needs)} needs and {len(moes)} measures of effectiveness."
             if not fr else f"{len(sh)} parties prenantes en {len(cats)} catégories, {len(needs)} besoins et "
                            f"{len(moes)} mesures d’efficacité."))
    c.pkg.h2("Stakeholder register" if not fr else "Registre des parties prenantes")
    c.pkg.table([t("ID"), t("Name"), t("Category"), t("Role"), "Authority" if not fr else "Autorité",
                 "Engagement" if not fr else "Mode d’engagement", t("Needs")],
                [[g(s, "code", "id", default=""), g(s, "name", default=""), str(g(s, "category", default="")).replace("_", " "),
                  g(s, "role", default=""), g(s, "authority", default=""), g(s, "engagement", default=""), lst(g(s, "needs"))]
                 for s in sh])
    if any(not g(s, "category") for s in sh):
        c.pkg.open(f"{sum(1 for s in sh if not g(s, 'category'))} stakeholders have no category", "team_leader")
    if needs:
        c.pkg.h2("Stakeholder needs" if not fr else "Besoins des parties prenantes")
        c.pkg.table([t("ID"), "Need" if not fr else "Besoin", "Stakeholder" if not fr else "Partie prenante"],
                    [[g(n, "code", "id", default=""), g(n, "need", "text", "statement", default=""),
                      lst(g(n, "stakeholder", "stakeholders", default=""))] for n in needs])
    c.pkg.h2("Measures of effectiveness" if not fr else "Mesures d’efficacité")
    if moes:
        rows = []
        for m in moes:
            ph = is_placeholder(m)
            rows.append([g(m, "code", "id", default=""), g(m, "measure", "name", default=""), g(m, "threshold", default=""),
                         lst(g(m, "objectives")), lst(g(m, "needs")),
                         ("to co-define" if not fr else "à co-définir") if ph else g(m, "defined_by", default="")])
        c.pkg.table([t("ID"), t("Measure"), t("Threshold"), "Objectives" if not fr else "Objectifs", t("Needs"),
                     "Defined by" if not fr else "Défini par"], rows)
        ph = [str(g(m, "code", "id", default="")) for m in moes if is_placeholder(m)]
        if ph:
            c.pkg.callout((f"{', '.join(ph)}: to co-define with the communities; the values shown are engineering "
                           "proposals, not agreed measures." if not fr else
                           f"{', '.join(ph)} : à co-définir avec les communautés ; les valeurs indiquées sont des "
                           "propositions d’ingénierie, pas des mesures convenues."))
            c.pkg.open(f"Measures to co-define: {', '.join(ph)}", "team_leader")
    else:
        c.pkg.open("No measures of effectiveness recorded", "S 3.S3" if st.get("status") == "not_implemented" else "team_leader")
    nv = items(sx.get("validation") or {}, "need_validation")
    if nv:
        c.pkg.h2("How each need is validated" if not fr else "Validation de chaque besoin")
        c.pkg.table([t("Needs"), t("Method"), "Stage" if not fr else "Étape", t("Status")],
                    [[g(x, "need_code", "need", default=""), g(x, "method", "criterion", default=""), g(x, "stage", default=""),
                      g(x, "status", default="")] for x in nv])


# ─────────────────────────────────────────────────────────────── validation plan


def validation(c) -> None:
    t, sx = c.t, c.sx
    fr = _fr(c)
    c.pkg.h1(("Validation plan" if not fr else "Plan de validation") + c.mat("validation_plan"))
    sec = sx.get("validation") or {}
    if _stub_or_empty(c, sec, "Validation plan (V1 …) and need validation", "S 3.S5"):
        return
    acts = items(sec)
    if not acts:
        c.pkg.p("No validation activity recorded." if not fr else "Aucune activité de validation enregistrée.")
        c.pkg.open("Validation activities (V1 …): none recorded", "systems_engineer")
        return
    c.pkg.table([t("ID"), t("Name"), "When" if not fr else "Quand", "Performed by" if not fr else "Réalisé par", t("Method"),
                 "Exit" if not fr else "Sortie", t("Status")],
                [[g(a, "code", "id", default=""), g(a, "title", "name", default=""), g(a, "stage", "when", default=""),
                  g(a, "performer", "who", default=""), g(a, "method", default=""), g(a, "acceptance", "exit", default=""),
                  g(a, "status", default="")] for a in acts])
    cov = sec.get("coverage") if isinstance(sec.get("coverage"), dict) else {}
    if cov:
        c.pkg.p("; ".join(f"{k}: {v}" for k, v in cov.items() if not isinstance(v, (dict, list))))
    gate = c.plan.covers[-1].upper()
    due = [a for a in acts if gate in str(g(a, "stage", "when", default="")).upper() and g(a, "status", default="") not in
           ("done", "passed")]
    for a in due:
        c.pkg.open(f"Validation {g(a, 'code', 'id', default='')} planned at {gate} is not done", "systems_engineer")


# ─────────────────────────────────────────────────────────────── allocation ledger

BUDGET_LABEL = {"mass": ("Mass", "Masse"), "power_avg": ("Orbit-average power", "Puissance moyenne orbitale"),
                "power_peak": ("Peak power", "Puissance crête"), "power_mode": ("Power per mode", "Puissance par mode"),
                "data": ("Downlink data", "Données descendantes"), "pointing": ("Pointing", "Pointage"),
                "registration": ("Registration", "Recalage"), "timing": ("Timing", "Datation")}


def ledger_sums(lines: list[dict]) -> dict[str, float]:
    out: dict[str, float] = {}
    for x in lines:
        if str(g(x, "line_kind", default="allocation")) == "reserve" or str(g(x, "element_code", default="")).upper() == "SYS":
            continue
        bt = str(g(x, "budget_type", default=""))
        v = num(g(x, "value"))
        if v is not None:
            out[bt] = round(out.get(bt, 0.0) + v, 6)
    return out


def allocations(c) -> None:
    t, sx = c.t, c.sx
    fr = _fr(c)
    c.pkg.h1(("Allocation ledger" if not fr else "Registre des allocations") + c.mat("allocation_ledger"))
    sec = sx.get("allocations") or {}
    if _stub_or_empty(c, sec, "Allocation ledger (budget shares agreed by their owners)", "A 3.A2"):
        return
    lines = items(sec)
    if not lines:
        c.pkg.p("No allocation recorded." if not fr else "Aucune allocation enregistrée.")
        c.pkg.open("Allocation ledger is empty: propose the allocations (Budget)", "systems_engineer")
        return
    sums = ledger_sums(lines)
    closure = sec.get("closure") if isinstance(sec.get("closure"), dict) else {}
    for bt in [b for b in BUDGET_LABEL if any(str(g(x, "budget_type", default="")) == b for x in lines)]:
        mine = [x for x in lines if str(g(x, "budget_type", default="")) == bt]
        unit = next((g(x, "unit") for x in mine if g(x, "unit")), "")
        c.pkg.h2(BUDGET_LABEL[bt][1 if fr else 0] + (f" ({unit})" if unit else ""))
        c.pkg.table(["Element" if not fr else "Élément", "Kind" if not fr else "Nature", "Allocation", "CBE" if not fr else "MEA",
                     "With maturity" if not fr else "Avec maturité", t("Requirement"), t("Owner"), t("Status")],
                    [[g(x, "element_code", default="") or lst((g(x, "data") or {}).get("contributor")) or "",
                      g(x, "line_kind", default="allocation"), fmt(g(x, "value")), fmt(g(x, "cbe")), fmt(g(x, "margined")),
                      g(x, "requirement_code", default=""), g(x, "owner_seat", default=""), g(x, "status", default="")]
                     for x in mine],
                    caption=(f"Sum of the allocations: {fmt(sums.get(bt))} {unit}" if not fr
                             else f"Somme des allocations : {fmt(sums.get(bt))} {unit}"))
        cl = closure.get(bt) if isinstance(closure.get(bt), dict) else {}
        if cl:
            c.pkg.p("; ".join(f"{k}: {fmt(v) if num(v) is not None else v}" for k, v in cl.items()
                              if not isinstance(v, (dict, list)) and v is not None))
    disputed = [x for x in lines if g(x, "status") == "disputed"]
    proposed = [x for x in lines if g(x, "status") == "proposed"]
    if disputed:
        c.pkg.open(f"{len(disputed)} allocation lines are disputed", "systems_engineer")
    if proposed:
        c.pkg.open(f"{len(proposed)} allocation lines are proposed and not yet agreed by their owner", "systems_engineer")


# ─────────────────────────────────────────────────────────────── negotiation records


def negotiations(c) -> None:
    t, sx = c.t, c.sx
    fr = _fr(c)
    c.pkg.h1(("Negotiation records" if not fr else "Comptes rendus de négociation") + c.mat("negotiation_records"))
    sec = sx.get("negotiations") or {}
    if _stub_or_empty(c, sec, "Negotiation records between seats", "H 3.H6"):
        return
    recs = items(sec)
    if not recs:
        c.pkg.p("No negotiation recorded." if not fr else "Aucune négociation enregistrée.")
        return
    rows = []
    for n in recs:
        seats = g(n, "seats", default=[]) or []
        signed = g(n, "signoffs", default={}) or {}
        rows.append([g(n, "code", "id", default=""), (g(n, "issue_fr") if fr else None) or g(n, "issue", default=""),
                     lst(seats), f"{len(signed)}/{len(seats)}", "; ".join(f"{k} = {v}" for k, v in (g(n, "agreed", default={}) or {}).items()),
                     g(n, "reopen_trigger", default=""), g(n, "status", default="")])
    c.pkg.table([t("ID"), "Issue" if not fr else "Question", "Seats" if not fr else "Postes", "Signed" if not fr else "Visas",
                 "Agreed values" if not fr else "Valeurs convenues", "Reopen if" if not fr else "Rouvrir si", t("Status")], rows)
    for n in recs:
        opts = g(n, "options", default=[]) or []
        if opts:
            c.pkg.h2(f"{g(n, 'code', 'id', default='')}: " + ("options" if not fr else "options"))
            c.pkg.table(["Option", "Effects" if not fr else "Effets"],
                        [[o.get("label") or o.get("id") or "", "; ".join(f"{k} = {v}" for k, v in (o.get("effects") or {}).items())]
                         for o in opts if isinstance(o, dict)])
    for n in recs:
        if g(n, "status") != "agreed":
            c.pkg.open(f"Negotiation {g(n, 'code', 'id', default='')} not agreed ({g(n, 'status', default='')})",
                       lst(g(n, "seats", default=[])))


# ─────────────────────────────────────────────────────────────── open items and changes


def open_items_and_changes(c) -> None:
    t, sx = c.t, c.sx
    fr = _fr(c)
    c.pkg.h1(("Open items, decisions and change proposals" if not fr else
              "Points ouverts, décisions et propositions de modification") + c.mat("open_items_register"))
    oi = sx.get("open_items") or {}
    gate = c.plan.covers[-1]
    c.pkg.h2("Open-item register" if not fr else "Registre des points ouverts")
    if not _stub_or_empty(c, oi, "Open-item register (RIDs, actions, conditional and PI decisions)", "D 3.D4"):
        rows = items(oi)
        if rows:
            c.pkg.table([t("ID"), t("Kind"), t("Description"), t("Owner"), "Blocks" if not fr else "Bloque", "Due" if not fr else "Échéance",
                         "Condition / fallback" if not fr else "Condition / repli", t("Status")],
                        [[g(x, "code", "id", default=""), g(x, "kind", default=""), g(x, "title", "description", default=""),
                          g(x, "owner_seat", default=""), str(g(x, "blocks_gate", default="")).upper(), g(x, "due", default=""),
                          " / ".join(v for v in (g(x, "condition", default=""), g(x, "fallback", default="")) if v),
                          g(x, "status", default="")] for x in rows])
            for x in rows:
                if str(g(x, "blocks_gate", default="")).lower() == gate and g(x, "status", default="open") != "closed":
                    c.pkg.open(f"{g(x, 'code', 'id', default='')} blocks the {gate.upper()}: {g(x, 'title', default='')}"[:240],
                               g(x, "owner_seat", default=""))
        else:
            c.pkg.p("No open item recorded." if not fr else "Aucun point ouvert enregistré.")
    ch = sx.get("changes") or {}
    c.pkg.h2("Change proposals" if not fr else "Propositions de modification")
    if not _stub_or_empty(c, ch, "Change proposals (ECP, CR)", "L 3.L4"):
        rows = items(ch)
        if rows:
            c.pkg.table([t("ID"), t("Name"), "Class" if not fr else "Classe", "Affects" if not fr else "Affecte",
                         "Impact", "Trade" if not fr else "Compromis", t("Gate"), t("Status")],
                        [[g(x, "code", "id", default=""), g(x, "title", default=""), g(x, "change_class", default=""),
                          lst(g(x, "affected_codes")), "; ".join(f"{k} {v}" for k, v in (g(x, "impact", default={}) or {}).items()),
                          g(x, "source_trade", default=""), str(g(x, "decision_gate", default="")).upper(), g(x, "status", default="")]
                         for x in rows])
            for x in rows:
                if g(x, "status", default="proposed") == "proposed":
                    c.pkg.open(f"Change proposal {g(x, 'code', 'id', default='')} awaits a decision", "team_leader")
        else:
            c.pkg.p("No change proposal recorded." if not fr else "Aucune proposition de modification enregistrée.")
    cc = sx.get("change_control") or {}
    rows = items(cc)
    if rows:
        c.pkg.h2("Change control: agreements and decisions" if not fr else "Maîtrise des modifications : accords et décisions")
        c.pkg.table(["Change" if not fr else "Modification", t("Kind"), "Seat" if not fr else "Poste", t("Decision"),
                     "Baseline" if not fr else "Référence", t("Note")],
                    [[g(x, "change_code", "change_id", default=""), g(x, "kind", default=""), g(x, "seat", default=""),
                      g(x, "decision", default=""), g(x, "baseline_ref", default=""), g(x, "note", default="")] for x in rows])
    elif cc.get("status") == "not_implemented":
        from .study_pack import stub_owner
        c.pkg.open("Change-control flow (affected seats' agreement, board decision, baseline update)",
                   stub_owner(cc) or "D 3.D7")


# ─────────────────────────────────────────────────────────────── ICD issues


def icds(c) -> None:
    t, sx = c.t, c.sx
    fr = _fr(c)
    c.pkg.h1(("Interface control documents: issue and sign-off" if not fr else
              "Documents de contrôle d’interface : édition et visa") + c.mat("icd_issues"))
    sec = sx.get("icds") or {}
    if _stub_or_empty(c, sec, "ICD issue control (issue, revision, state, sign-off by both seats)", "R 3.R6"):
        return
    rows = items(sec)
    if not rows:
        c.pkg.p("No interface control document recorded." if not fr else "Aucun document de contrôle d’interface enregistré.")
        c.pkg.open("ICDs: none issued", "systems_engineer")
        return
    c.pkg.table(["ICD", t("Name"), "Issue" if not fr else "Édition", "Rev.", t("Status"), "Provider" if not fr else "Fournisseur",
                 "Consumer" if not fr else "Utilisateur", "Signed by" if not fr else "Visé par"],
                [[g(x, "icd_ref", default=""), g(x, "title", default=""), g(x, "issue", default=""), g(x, "revision", default=0),
                  g(x, "state", default=""), g(x, "provider_seat", default=""), g(x, "consumer_seat", default=""),
                  lst(g(x, "signoffs", default={}))] for x in rows])
    gate = c.plan.covers[-1]
    if gate in ("pdr", "cdr"):
        low = [x for x in rows if str(g(x, "state", default="draft")) in ("draft", "")]
        if low:
            c.pkg.open(f"{len(low)} ICDs are still drafts (Issue A expected at {gate.upper()})", "systems_engineer")
    unsigned = [x for x in rows if len(g(x, "signoffs", default={}) or {}) < 2]
    if unsigned:
        c.pkg.open(f"{len(unsigned)} ICDs lack the sign-off of both owning seats", "systems_engineer")


# ─────────────────────────────────────────────────────────────── reliability and FMEA


def reliability(c) -> None:
    t, sx = c.t, c.sx
    fr = _fr(c)
    c.pkg.h1(("Reliability analysis and FMEA" if not fr else "Analyse de fiabilité et AMDE") + c.mat("reliability_fmea"))
    sec = sx.get("reliability") or {}
    if _stub_or_empty(c, sec, "Reliability analysis and FMEA", "A 3.A5"):
        return
    res = sec.get("result") if isinstance(sec.get("result"), dict) else {}
    if res:
        c.pkg.table([t("Item"), t("Value")], [[k, fmt(v, 4) if num(v) is not None else v] for k, v in res.items()
                                              if not isinstance(v, (dict, list))])
    blocks = items(sec, "blocks")
    if blocks:
        c.pkg.h2("Reliability block diagram" if not fr else "Diagramme de fiabilité")
        c.pkg.table([t("Name"), t("Subsystem"), "Arrangement" if not fr else "Agencement", "FIT", t("Source"),
                     "Reliability" if not fr else "Fiabilité"],
                    [[g(b, "name", default=""), g(b, "subsystem", default=""), g(b, "arrangement", default=""),
                      fmt(g(b, "failure_rate_fit"), 1), g(b, "rate_source", default=""), fmt(g(b, "reliability"), 4)] for b in blocks])
    fm = items(sec, "fmea")
    c.pkg.h2("FMEA worksheet" if not fr else "Feuille AMDE")
    if fm:
        c.pkg.table([t("ID"), t("Subsystem"), t("Item"), "Failure mode" if not fr else "Mode de défaillance",
                     "System effect" if not fr else "Effet système", "S", "P", "Crit.", "FDIR", t("Mitigation")],
                    [[g(x, "code", default=""), g(x, "subsystem", default=""), g(x, "item", default=""), g(x, "failure_mode", default=""),
                      g(x, "system_effect", default=""), g(x, "severity", default=""), g(x, "probability", default=""),
                      g(x, "criticality", default=""), g(x, "fdir_ref", default=""), g(x, "mitigation", default="")] for x in fm])
        spf = [x for x in fm if g(x, "single_point", default=False)]
        if spf:
            c.pkg.open(f"{len(spf)} single-point failures in the FMEA", "systems_engineer")
    else:
        c.pkg.open("FMEA worksheet is empty", "systems_engineer")
    if not res:
        c.pkg.open("Reliability analysis not run", "systems_engineer")


# ─────────────────────────────────────────────────────────────── thermal model


def thermal_model(c) -> None:
    t, sx = c.t, c.sx
    fr = _fr(c)
    c.pkg.h1(("Thermal model" if not fr else "Modèle thermique") + c.mat("thermal_model"))
    sec = sx.get("thermal_model") or {}
    if _stub_or_empty(c, sec, "Thermal nodal model (nodes, hot and cold cases, margins)", "A 3.A6"):
        return
    nodes = items(sec, "nodes")
    cases = items(sec, "cases")
    if nodes:
        c.pkg.table([t("ID"), t("Name"), "Op. min (°C)" if not fr else "Fonct. min (°C)", "Op. max (°C)" if not fr else "Fonct. max (°C)",
                     "Heater (W)" if not fr else "Réchauffeur (W)", t("Source")],
                    [[g(n, "code", default=""), g(n, "name", default=""), fmt(g(n, "op_min_c"), 1), fmt(g(n, "op_max_c"), 1),
                      fmt(g(n, "heater_w"), 2), g(n, "limits_source", default="")] for n in nodes],
                    caption=(f"{len(nodes)} nodes, {len(items(sec, 'couplings'))} couplings" if not fr
                             else f"{len(nodes)} nœuds, {len(items(sec, 'couplings'))} couplages"))
    else:
        c.pkg.open("Thermal model has no nodes", "thermal_engineer")
    if cases:
        rows = []
        for k in cases:
            res = g(k, "results", default={}) or {}
            worst = min((num((v or {}).get("margin_design_c")) for v in res.values() if isinstance(v, dict)
                         and num((v or {}).get("margin_design_c")) is not None), default=None)
            rows.append([g(k, "code", default=""), g(k, "kind", default=""), fmt(g(k, "beta_deg"), 1), fmt(g(k, "eclipse_min"), 1),
                         g(k, "mode_key", default=""), fmt(worst, 1), g(k, "status", default="")])
            if worst is not None and worst < 0:
                c.pkg.open(f"Thermal case {g(k, 'code', default='')}: negative design margin ({fmt(worst, 1)} °C)", "thermal_engineer")
        c.pkg.table(["Case" if not fr else "Cas", t("Kind"), "β (deg)", "Eclipse (min)" if not fr else "Éclipse (min)", t("Mode"),
                     "Worst design margin (°C)" if not fr else "Marge de conception la plus faible (°C)", t("Status")], rows)
    else:
        c.pkg.open("Thermal model: no hot or cold case solved", "thermal_engineer")


# ─────────────────────────────────────────────────────────────── debris assessment and cost


def debris_assessment(c) -> None:
    t, sx = c.t, c.sx
    fr = _fr(c)
    sec = sx.get("debris") or {}
    c.pkg.h2("Debris assessment" if not fr else "Évaluation des débris")
    if sec.get("status") == "not_implemented":
        from .study_pack import stub_owner
        c.pkg.open("Debris assessment (lifetime, casualty risk, collision probability) in the tool", stub_owner(sec) or "L 3.L8")
        return
    a = sec.get("assessment") if isinstance(sec.get("assessment"), dict) else None
    if not a:
        c.pkg.open("Debris assessment not run", "mission_analyst")
        return
    c.pkg.table([t("Item"), t("Value")],
                [["Orbital lifetime with the device (y)" if not fr else "Durée de vie orbitale avec le dispositif (a)", fmt(a.get("lifetime_y"), 2)],
                 ["Without the device (y)" if not fr else "Sans le dispositif (a)", fmt(a.get("lifetime_without_device_y"), 2)],
                 ["Casualty risk" if not fr else "Risque de victimes", a.get("casualty_risk")],
                 ["Collision probability" if not fr else "Probabilité de collision", a.get("collision_probability")],
                 [t("Status"), a.get("status") or ""],
                 ["Accepted at" if not fr else "Acceptée à", str(a.get("accepted_gate") or "").upper()],
                 ["Accepted by" if not fr else "Acceptée par", a.get("accepted_by") or ""]])
    if a.get("status") != "accepted":
        c.pkg.open("Debris assessment not accepted", "mission_analyst")


def cost_items(c) -> None:
    t, sx = c.t, c.sx
    fr = _fr(c)
    sec = sx.get("cost") or {}
    c.pkg.h2("Cost estimate (labour, tests, reserve)" if not fr else "Estimation des coûts (main-d’œuvre, essais, réserve)")
    if sec.get("status") == "not_implemented":
        from .study_pack import stub_owner
        c.pkg.open("Cost pricing: labour, test campaigns and reserve (launch provided)", stub_owner(sec) or "A 3.A7")
        return
    rows = items(sec)
    if not rows:
        c.pkg.open("Cost items not priced", "team_leader")
        return
    c.pkg.table([t("Category"), t("Name"), t("Qty"), "Unit" if not fr else "Unité", "Unit cost (k€)" if not fr else "Coût unitaire (k€)",
                 "Total (k€)", t("Source")],
                [[g(x, "category", default=""), (g(x, "name_fr") if fr else None) or g(x, "name", default=""), fmt(g(x, "quantity"), 2),
                  g(x, "unit", default=""), fmt(g(x, "unit_cost_keur"), 2), fmt(g(x, "total_keur"), 1), g(x, "source", default="")]
                 for x in rows],
                caption=(f"Total {fmt(sec.get('total_keur'), 1)} k€" if sec.get("total_keur") is not None else ""))


# ─────────────────────────────────────────────────────────────── assumptions


def assumptions(c) -> None:
    t, sx = c.t, c.sx
    fr = _fr(c)
    c.pkg.h1(("Appendix: assumption register" if not fr else "Annexe : registre des hypothèses") + c.mat("assumption_register"))
    sec = sx.get("assumptions") or {}
    if _stub_or_empty(c, sec, "Assumption register", "S 3.S6"):
        return
    rows = items(sec)
    if not rows:
        c.pkg.p("No assumption recorded." if not fr else "Aucune hypothèse enregistrée.")
        return
    c.pkg.table([t("ID"), "Assumption" if not fr else "Hypothèse", "Affects" if not fr else "Affecte",
                 "Replace with" if not fr else "À remplacer par", t("Owner"), "Due" if not fr else "Échéance", t("Status")],
                [[g(x, "code", default=""), g(x, "statement", default=""), lst(g(x, "affects")), g(x, "replace_with", default=""),
                  g(x, "owner_seat", default=""), str(g(x, "due_gate", default="")).upper(), g(x, "status", default="")] for x in rows])
    gate = c.plan.covers[-1]
    due = [x for x in rows if str(g(x, "due_gate", default="")).lower() == gate and g(x, "status", default="open") == "open"]
    if due:
        c.pkg.open(f"{len(due)} assumptions due at {gate.upper()} are still open", "systems_engineer")


# ─────────────────────────────────────────────────────────────── SE figures


def figures(c) -> None:
    """The systems-engineering figures this review expects (diagram catalogue for the gate), with
    their gaps; the figures themselves are in Diagrams.docx and the SEMP."""
    t = c.t
    fr = _fr(c)
    cat = c.extras.get("diagrams") or []
    c.pkg.h1("Systems-engineering figures" if not fr else "Figures d’ingénierie système")
    if not cat:
        c.pkg.p("The diagram catalogue was not evaluated for this pack." if not fr
                else "Le catalogue des diagrammes n’a pas été évalué pour ce dossier.")
        return
    gate = c.plan.covers
    rows = []
    for e in cat:
        mats = [x["maturity"] for x in e.get("gates") or [] if x.get("gate") in gate]
        title = e.get("title")
        title = (title.get("t") if isinstance(title, dict) else title) or e.get("kind")
        rows.append([title, ", ".join(mats), e.get("gaps", 0), "; ".join(
            _gap_text(x) for x in e.get("top_gaps") or [])[:200],
            len(e.get("instances") or []) or 1])
    c.pkg.table(["Figure", t("Maturity"), "Gaps" if not fr else "Lacunes", "What the model lacks" if not fr else "Ce qui manque au modèle",
                 "Figures" if not fr else "Figures"], rows,
                caption=("Drawn from the design model in documents/Diagrams.docx (D draft, B baselined, U updated)" if not fr
                         else "Tirées du modèle de conception dans documents/Diagrams.docx (D ébauche, B référencé, U mis à jour)"))
    for e in cat:
        if e.get("empty") or e.get("gap_alarm"):
            title = e.get("title")
            title = (title.get("t") if isinstance(title, dict) else title) or e.get("kind")
            if e.get("empty"):
                c.pkg.open(f"Figure {title}: the model lacks data for it", "systems_engineer")
            else:
                # the figure is drawn; what it shows is an alarm of the design (3.F1 dry run: "lacks
                # data" was printed for a risk matrix of 37 risks with 3 critical ones open)
                gaps = "; ".join(_gap_text(x) for x in (e.get("top_gaps") or [])[:2])
                c.pkg.open(f"Figure {title}: {gaps or 'alarms in the design shown'}", "systems_engineer")


def _gap_text(g) -> str:
    """One gap of the diagram catalogue as plain text (``{"t": "{{n}} …", "p": {"n": 3}}``)."""
    if not isinstance(g, dict):
        return str(g)
    out = str(g.get("t") or "")
    for k, v in (g.get("p") or {}).items():
        out = out.replace("{{" + k + "}}", str(v))
    return out


# ─────────────────────────────────────────────────────────────── payload definition


def payload_data_lines(sx: dict, lang: str = "en") -> list[list[str]]:
    """Frames acquired on board (the payload definition) next to the products delivered (the data
    budget's product set): never one "generated" figure (wave-2b leftover)."""
    fr = lang == "fr"
    pls = ((sx.get("mission") or {}).get("definition") or {}).get("payloads") or []
    frames_gb = sum(float(p.get("data_volume_per_day_gb") or 0) for p in pls)
    sci = ((sx.get("data_budget") or {}).get("science") or {}) if isinstance((sx.get("data_budget") or {}).get("science"), dict) else {}
    rows = []
    if pls:
        rows.append(["Frames acquired on board per day (payload definition, before ROI selection)" if not fr else
                     "Images acquises à bord par jour (définition de la charge utile, avant sélection des ROI)",
                     f"{frames_gb:.2f} GB/day" if not fr else f"{frames_gb:.2f} Go/jour".replace(".", ",")])
    if sci.get("raw_mb_per_day") is not None:
        prods = ", ".join(f"{fmt(p.get('per_day'), 0)} × {p.get('name')}" for p in sci.get("products") or [] if isinstance(p, dict))
        rows.append([("Products selected per day, raw" if not fr else "Produits retenus par jour, bruts") + (f" ({prods})" if prods else ""),
                     f"{fmt(sci.get('raw_mb_per_day'), 1)} MB/day" if not fr else f"{fmt(sci.get('raw_mb_per_day'), 1)} Mo/jour"])
    if sci.get("delivered_mb_per_day") is not None or sci.get("target_mb_per_day") is not None:
        v = sci.get("delivered_mb_per_day") if sci.get("delivered_mb_per_day") is not None else sci.get("target_mb_per_day")
        rows.append([("Products delivered per day after compression" if not fr else "Produits livrés par jour après compression")
                     + (f" (≥ {fmt(sci.get('compression_needed'), 2)}:1 needed)" if sci.get("compression_needed") and not fr else
                        f" (≥ {fmt(sci.get('compression_needed'), 2)}:1 nécessaire)" if sci.get("compression_needed") else ""),
                     f"{fmt(v, 1)} MB/day" if not fr else f"{fmt(v, 1)} Mo/jour"])
    return rows


__all__ = ["deliverables", "stakeholders", "validation", "allocations", "negotiations", "open_items_and_changes", "icds",
           "reliability", "thermal_model", "debris_assessment", "cost_items", "assumptions", "figures", "payload_data_lines",
           "ledger_sums", "stakeholder_rows", "is_placeholder", "g", "items"]
