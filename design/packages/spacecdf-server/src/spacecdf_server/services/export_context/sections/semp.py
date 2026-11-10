"""Section ``semp``: the SEMP content the study does not hold elsewhere: organisation and seats,
lifecycle and gates, technical processes, tailoring, configuration management. Owner: X (3.X3).

The SEMP generator (``services/docx/semp.py``) reads this section and the others (requirements,
functions, trades, risks, AIT, schedule, allocations, validation, changes, ICDs …), so the plan
describes the study as it is: the seats the team uses and what each owns, the gate profile with
its state, the processes with the evidence the study already holds, the tailoring choices (gate
profile, margin hold, model philosophy) and the baselines and change rules.

Shapes (lists of plain dicts, labels as ``{en, fr}``)::

    organisation  [{seat, label, kind, owns_parameters[], owns_domains[], elements[], requirements}]
    lifecycle     [{gate, short, name, phase, state, passed_at, baseline, products_baselined[]}]
    processes     [{id, label, standard, how{en,fr}, evidence{key: count}}]
    tailoring     [{id, label, value, rationale}]
    configuration_management  {baselines[], change_classes[], change_rule{en,fr}, records}

No person's name is read (seats only).
"""
from __future__ import annotations

from typing import Any

#: lifecycle phase each gate closes (ECSS-M-ST-10C)
GATE_PHASE = {"mdr": "0", "prr": "A", "srr": "B", "pdr": "B", "cdr": "C", "qr": "D", "ar": "D", "frr": "D"}
#: the baseline each gate sets (ECSS-M-ST-40C reading, to verify against the primary text)
GATE_BASELINE = {
    "mdr": {"en": "mission baseline (need, objectives, concept)", "fr": "référence de mission (besoin, objectifs, concept)"},
    "prr": {"en": "preliminary requirements", "fr": "exigences préliminaires"},
    "srr": {"en": "functional baseline", "fr": "référence fonctionnelle"},
    "pdr": {"en": "allocated (design-to) baseline", "fr": "référence allouée (à concevoir)"},
    "cdr": {"en": "product (build-to) baseline", "fr": "référence produit (à fabriquer)"},
    "qr": {"en": "qualified design", "fr": "conception qualifiée"},
    "ar": {"en": "accepted flight model (as built)", "fr": "modèle de vol recetté (tel que construit)"},
    "frr": {"en": "flight configuration", "fr": "configuration de vol"},
}

#: the technical processes of ISO/IEC/IEEE 15288 the study runs, how SpaceCDF supports each, and
#: which section counts are the evidence
PROCESSES: list[dict[str, Any]] = [
    {"id": "stakeholder_needs", "standard": "ISO/IEC/IEEE 15288 §6.4.2",
     "label": {"en": "Stakeholder needs and requirements definition", "fr": "Définition des besoins et exigences des parties prenantes"},
     "how": {"en": "Stakeholder register by category with authority and engagement; needs (SN-…) and measures of effectiveness "
                   "with thresholds; placeholders are co-defined with the people concerned, not set by the engineering team.",
             "fr": "Registre des parties prenantes par catégorie, avec autorité et mode d’engagement ; besoins (SN-…) et "
                   "mesures d’efficacité avec seuils ; les valeurs provisoires sont co-définies avec les personnes concernées, "
                   "pas fixées par l’équipe d’ingénierie."},
     "evidence": ("stakeholders.items", "stakeholders.needs", "stakeholders.moes")},
    {"id": "requirements", "standard": "ISO/IEC/IEEE 15288 §6.4.3; ECSS-E-ST-10-06C",
     "label": {"en": "System requirements definition", "fr": "Définition des exigences système"},
     "how": {"en": "Requirements by level (mission, segment, system, subsystem, interface) with a parent, an objective, a "
                   "function, an allocation, a verification method, level, model, event and an acceptance criterion; SMART "
                   "checks run on every edit.",
             "fr": "Exigences par niveau (mission, segment, système, sous-système, interface) avec une mère, un objectif, une "
                   "fonction, une allocation, une méthode, un niveau, un modèle, un événement de vérification et un critère "
                   "d’acceptation ; les contrôles SMART s’exécutent à chaque modification."},
     "evidence": ("requirements.items",)},
    {"id": "architecture", "standard": "ISO/IEC/IEEE 15288 §6.4.4; ECSS-E-ST-10C",
     "label": {"en": "Architecture definition (functional and physical)", "fr": "Définition de l’architecture (fonctionnelle et physique)"},
     "how": {"en": "Function tree decomposed to leaves, each leaf allocated to one product; functional exchanges and the N² "
                   "charts; product tree with the selected equipment; system-level trades on absolute scales with ±20 % "
                   "weight sensitivity.",
             "fr": "Arbre fonctionnel décomposé jusqu’aux feuilles, chaque feuille allouée à un produit ; échanges fonctionnels "
                   "et diagrammes N² ; arbre produit avec les équipements choisis ; compromis système sur échelles absolues "
                   "avec sensibilité des poids à ±20 %."},
     "evidence": ("functions.items", "elements.items", "trades.items")},
    {"id": "interfaces", "standard": "ECSS-E-ST-10-24C",
     "label": {"en": "Interface management", "fr": "Gestion des interfaces"},
     "how": {"en": "Interfaces between elements with type and direction; interface requirements generated from the links; "
                   "each ICD carries an issue and the sign-off of both owning seats.",
             "fr": "Interfaces entre éléments avec type et sens ; exigences d’interface générées à partir des liaisons ; chaque "
                   "ICD porte une édition et le visa des deux postes responsables."},
     "evidence": ("elements.interfaces", "icds.items")},
    {"id": "budgets", "standard": "ECSS-E-ST-10C Annex I; ECSS-E-HB-10-02A",
     "label": {"en": "Technical budgets and margins", "fr": "Bilans techniques et marges"},
     "how": {"en": "Roll-up of the selected equipment with maturity margins and the system margin of the gate; allocations "
                   "per element in a ledger each owner agrees to; the Systems reserve on its own line.",
             "fr": "Cumul des équipements choisis avec marges de maturité et marge système du jalon ; allocations par élément "
                   "dans un registre que chaque responsable approuve ; la réserve Système sur sa propre ligne."},
     "evidence": ("allocations.items",)},
    {"id": "verification", "standard": "ISO/IEC/IEEE 15288 §6.4.9; ECSS-E-ST-10-02C",
     "label": {"en": "Verification", "fr": "Vérification"},
     "how": {"en": "One verification item per requirement with method, level, model, event and stage; analyses close "
                   "analysis items automatically; the VCD tracks close-out.",
             "fr": "Un élément de vérification par exigence avec méthode, niveau, modèle, événement et étape ; les analyses "
                   "clôturent automatiquement les éléments par analyse ; le DCV suit la clôture."},
     "evidence": ("verification.items",)},
    {"id": "validation", "standard": "ISO/IEC/IEEE 15288 §6.4.11",
     "label": {"en": "Validation", "fr": "Validation"},
     "how": {"en": "Validation activities V1 … with the stakeholders who perform them; each need has its validation method "
                   "and stage.",
             "fr": "Activités de validation V1 … avec les parties prenantes qui les réalisent ; chaque besoin a sa méthode et "
                   "son étape de validation."},
     "evidence": ("validation.items", "validation.need_validation")},
    {"id": "risk", "standard": "ECSS-M-ST-80C",
     "label": {"en": "Risk management", "fr": "Gestion des risques"},
     "how": {"en": "5 × 5 likelihood × consequence register with an owner seat, mitigation and residual score; reviewed at "
                   "every gate.",
             "fr": "Registre 5 × 5 probabilité × gravité avec poste responsable, atténuation et note résiduelle ; revu à chaque "
                   "jalon."},
     "evidence": ("risks.items",)},
    {"id": "decisions", "standard": "ISO/IEC/IEEE 15288 §6.3.3",
     "label": {"en": "Decision management and negotiation", "fr": "Gestion des décisions et négociation"},
     "how": {"en": "Trade decisions with conditions and fallbacks; open-item register; negotiation records signed by every "
                   "seat concerned, with the trigger that reopens them.",
             "fr": "Décisions de compromis avec conditions et solutions de repli ; registre des points ouverts ; comptes rendus "
                   "de négociation visés par chaque poste concerné, avec le déclencheur qui les rouvre."},
     "evidence": ("open_items.items", "negotiations.items")},
    {"id": "configuration", "standard": "ECSS-M-ST-40C",
     "label": {"en": "Configuration management", "fr": "Gestion de configuration"},
     "how": {"en": "A baseline is frozen at each passed gate; changes after it go through a change proposal with an impact "
                   "preview, the agreement of the affected seats and a board decision.",
             "fr": "Une référence est figée à chaque jalon franchi ; les modifications ultérieures passent par une proposition "
                   "de modification avec aperçu d’impact, l’accord des postes concernés et une décision du comité."},
     "evidence": ("changes.items", "change_control.items")},
    {"id": "assumptions", "standard": "ISO/IEC/IEEE 15288 §6.3.4",
     "label": {"en": "Assumptions and open items", "fr": "Hypothèses et points ouverts"},
     "how": {"en": "Every assumption has an owner, the evidence that would replace it and the gate it is due.",
             "fr": "Chaque hypothèse a un responsable, la preuve qui la remplacera et le jalon où elle est due."},
     "evidence": ("assumptions.items",)},
]


def empty() -> dict:
    return {"organisation": [], "lifecycle": [], "processes": [], "tailoring": [], "configuration_management": {}}


def _count(sections: dict[str, dict], path: str) -> int | None:
    sec, _, key = path.partition(".")
    s = sections.get(sec)
    if not isinstance(s, dict) or s.get("status") == "not_implemented":
        return None
    v = s.get(key)
    return len(v) if isinstance(v, list) else None


async def _organisation(ctx) -> list[dict]:
    from ....seats import config as seat_cfg
    used: list[str] = []
    try:
        from ....seats import store
        from ....seats.service import used_seats
        state = store.peek_team(ctx.study_id) or await store.get_team(ctx.study_id)
        used = list(used_seats(state) or [])
    except Exception:  # noqa: BLE001 — fall back to every seat of the configuration
        used = []
    seats = [s for s in seat_cfg.seats() if not used or s["id"] in used]
    reqs = (ctx.sections.get("requirements") or {}).get("items") or []
    out = []
    for s in seats:
        if s.get("kind") == "instructor":
            continue
        owns = s.get("owns") or {}
        els = sorted({e.get("name") for e in ctx.elements if e.get("owner_position") == s["id"]
                      and e.get("element_type") in ("segment", "system", "subsystem") and e.get("name")})
        out.append({"seat": s["id"], "label": dict(s.get("label") or {"en": s["id"], "fr": s["id"]}), "kind": s.get("kind") or "",
                    "owns_parameters": [f"{x}.*" for x in (owns.get("prefixes") or [])] if isinstance(owns, dict) else [],
                    "owns_domains": list(owns.get("element_domains") or []) if isinstance(owns, dict) else [],
                    "elements": els,
                    "requirements": sum(1 for r in reqs if (r.get("responsible_position") or r.get("owner_seat")) == s["id"])})
    return out


async def _lifecycle(ctx) -> list[dict]:
    gates = ctx.sections.get("gates") or {}
    rows = gates.get("gates") or []
    if not rows and ctx.study is not None:
        try:
            from ....routers.gates import study_profile
            rows = [{"id": g["id"], "short": g.get("short"), "name": g.get("name"), "covers": g.get("covers")}
                    for g in study_profile(ctx.study).get("gates") or []]
        except Exception:  # noqa: BLE001
            rows = []
    try:
        from spacecdf_agents.exporters.docs.pack_catalog import _late_products
        from ...gate_profiles import load as gp_load
        prods = _late_products(list(gp_load().get("products") or []))
    except Exception:  # noqa: BLE001
        prods = []
    out = []
    for g in rows:
        covers = [c for c in (g.get("covers") or [g.get("id")]) if c]
        last = covers[-1] if covers else g.get("id")
        base = [p.get("label") or {"en": p["id"], "fr": p["id"]} for p in prods
                if any((p.get("maturity") or {}).get(c) == "B" for c in covers)]
        out.append({"gate": g.get("id"), "short": g.get("short") or str(g.get("id") or "").upper(), "name": g.get("name"),
                    "phase": GATE_PHASE.get(str(last), ""), "state": g.get("state") or "", "passed_at": g.get("passed_at"),
                    "baseline": GATE_BASELINE.get(str(last), {"en": "", "fr": ""}), "products_baselined": base})
    return out


def _tailoring(ctx) -> list[dict]:
    out: list[dict] = []
    gates = ctx.sections.get("gates") or {}
    prof = gates.get("profile") or {}
    if prof:
        out.append({"id": "gate_profile", "label": {"en": "Gate profile", "fr": "Profil de jalons"},
                    "value": prof.get("label") or prof.get("id") or "",
                    "rationale": prof.get("description") or {"en": "", "fr": ""}})
    mp = getattr(ctx.study, "margin_policy", None) if ctx.study is not None else None
    hold = (mp or {}).get("study_override") if isinstance(mp, dict) else getattr(mp, "study_override", None)
    if hold:
        h = hold if isinstance(hold, dict) else dict(hold)
        out.append({"id": "margin_hold", "label": {"en": "System margin hold", "fr": "Maintien de la marge système"},
                    "value": f"{h.get('percent')} % through {str(h.get('through_gate') or '').upper()} "
                             f"({', '.join(h.get('resources') or [])})",
                    "rationale": {"en": str(h.get("rationale") or ""), "fr": str(h.get("rationale") or "")}})
    ru = ctx.sections.get("rollup") or {}
    m = ru.get("mass") or {}
    if m.get("ladder_percent") is not None:
        out.append({"id": "margin_ladder", "label": {"en": "Margin ladder of the gate", "fr": "Échelle des marges du jalon"},
                    "value": f"{m.get('ladder_percent')} % (ladder) / {m.get('system_margin_percent')} % (applied, "
                             f"{m.get('system_margin_source') or 'ladder'})",
                    "rationale": {"en": "configs/margin_policy.yaml (ECSS-E-HB-10-02A)", "fr": "configs/margin_policy.yaml (ECSS-E-HB-10-02A)"}})
    ait = ctx.sections.get("ait") or {}
    if isinstance(ait, dict) and ait.get("philosophy") and ait.get("status") != "not_implemented":
        out.append({"id": "model_philosophy", "label": {"en": "Model philosophy", "fr": "Philosophie des modèles"},
                    "value": str(ait.get("philosophy")),
                    "rationale": {"en": ", ".join(str(x.get("code") or x.get("name") or "") for x in ait.get("models") or []),
                                  "fr": ", ".join(str(x.get("code") or x.get("name") or "") for x in ait.get("models") or [])}})
    out.append({"id": "independence", "label": {"en": "Product assurance independence", "fr": "Indépendance de l’assurance produit"},
                "value": "instructor and observer seats",
                "rationale": {"en": "ECSS gives product assurance independent authority; in a course the instructor and "
                                    "observer seats review read-only and witness the tests.",
                              "fr": "L’ECSS donne à l’assurance produit une autorité indépendante ; dans un cours, les postes "
                                    "instructeur et observateur relisent en lecture seule et assistent aux essais."}})
    return out


def _configuration(ctx) -> dict:
    gates = ctx.sections.get("gates") or {}
    records = gates.get("records") or {}
    baselines = []
    for gid, rec in records.items():
        if not isinstance(rec, dict):
            continue
        if rec.get("passed_at") or rec.get("baseline") or rec.get("state") == "passed":
            baselines.append({"gate": gid, "passed_at": rec.get("passed_at"),
                              "baseline": GATE_BASELINE.get(str(gid).lower(), {"en": "", "fr": ""})})
    return {"baselines": baselines,
            "change_classes": [{"id": "I", "label": {"en": "Class I: affects a baselined requirement, an interface, mass, "
                                                         "power, cost or schedule; decided by the board",
                                                   "fr": "Classe I : touche une exigence de référence, une interface, la masse, "
                                                         "la puissance, le coût ou le calendrier ; décidée par le comité"}},
                               {"id": "II", "label": {"en": "Class II: any other change; agreed by the affected seats",
                                                    "fr": "Classe II : toute autre modification ; approuvée par les postes concernés"}}],
            "change_rule": {"en": "After a gate is passed, its baseline changes only through a change proposal (impact preview, "
                                  "agreement of the affected seats, decision, baseline update).",
                            "fr": "Après le franchissement d’un jalon, sa référence ne change que par une proposition de "
                                  "modification (aperçu d’impact, accord des postes concernés, décision, mise à jour de la "
                                  "référence)."},
            "records": len(records)}


async def collect(ctx) -> dict:
    sections = ctx.sections
    processes = []
    for p in PROCESSES:
        ev = {k: _count(sections, k) for k in p["evidence"]}
        processes.append({"id": p["id"], "label": p["label"], "standard": p["standard"], "how": p["how"], "evidence": ev})
    return {"organisation": await _organisation(ctx), "lifecycle": await _lifecycle(ctx), "processes": processes,
            "tailoring": _tailoring(ctx), "configuration_management": _configuration(ctx)}
