"""Deliverables service of the systems-engineering protocol (SE-02, S part). Owner S (3.S2).

One evaluation that every reader shares, so the Phase panel, the gate ``start`` warnings, the
``<GATE>-SE-01`` criterion and the pack index cannot disagree::

    from spacecdf_server.services import se_deliverables
    ev = await se_deliverables.evaluate(study_id, "pdr")
    ev["deliverables"]   # [{id, kind, label{en,fr}, owner_seat, state: ok|warn|missing|info, evidence,
                         #   evidence_i18n{en,fr}, fix, draft, severity, refs}]
    ev["missing"]        # ids of deliverables not ok (severity warn or block): what ``start`` warns about
    ev["warnings"]       # [{id, label, state, evidence, owner_seat, severity}] ready for the gate history
    ev["summary"]        # {ok, warn, missing, info, total}

Each item of ``configs/se_protocol.yaml`` is judged from data the study already holds (no AI):

* ``product``  — the gate-profile product through an evidence rule (:data:`PRODUCT_RULES`), e.g.
  ``budgets`` at B means every allocation of the ledger is agreed by its owner seat;
* ``diagram``  — the diagram catalogue: drawn, empty, or with alarm gaps;
* ``trade``    — trade records by level (mission, system, architecture …) and gate, decided or open;
* ``document`` — a review-pack document, judged by the object query it carries;
* ``criteria`` — a gate exit criterion's status (guarded against recursion through ``*-SE-01``);
* ``object``   — a count query of :data:`OBJECT_QUERIES` (stakeholders, MOEs, validation …).

State: ``ok`` (evidence found), ``warn`` (partly there), ``missing`` (nothing yet), ``info`` (not
judged: a reading, a pointer). Evidence strings are in English and French.
"""
from __future__ import annotations

import contextvars
import logging
import re
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)

_IN_CRITERIA = contextvars.ContextVar("se_deliverables_in_criteria", default=False)
GATE_ORDER = ("mdr", "prr", "srr", "pdr", "cdr", "qr", "ar", "frr")
CATEGORY_LABEL = {"decision_authority": ("decision authority", "autorité de décision"),
                  "beneficiary": ("beneficiary", "bénéficiaire"), "affected_party": ("affected party", "partie affectée"),
                  "rights_holder": ("rights-holder", "titulaire de droits"), "non_human": ("non-human", "non humain")}


def E(en: str, fr: str) -> dict[str, str]:
    return {"en": en, "fr": fr}


class Ctx:
    """What the queries read, loaded once per evaluation and only when asked for."""

    def __init__(self, study_id: str, study: Any, gate: str):
        self.study_id, self.study, self.gate = study_id, study, gate
        self._c: dict[str, Any] = {}

    async def get(self, key: str, fn: Callable[[], Awaitable[Any]]) -> Any:
        if key not in self._c:
            try:
                self._c[key] = await fn()
            except Exception as exc:  # noqa: BLE001 — a failing source makes its items "missing", not a 500
                logger.warning("se_deliverables: %s unavailable for %s: %s", key, self.study_id, exc)
                self._c[key] = None
        return self._c[key]

    async def diagram_data(self):
        async def f():
            from . import diagrams as dg
            return await dg.load(self.study_id)
        return await self.get("diagram_data", f)

    async def requirements(self) -> list[dict]:
        async def f():
            from ..routers.requirements import _requirements, ensure_requirements_loaded
            try:
                await ensure_requirements_loaded()
            except Exception:  # noqa: BLE001
                pass
            return [dict(r) for r in _requirements.values() if r.get("study_id") == self.study_id
                    and r.get("status") != "retired"]
        return await self.get("requirements", f) or []

    async def moes(self) -> list[dict]:
        async def f():
            from ..routers.moes import list_moes
            return await list_moes(self.study_id)
        return await self.get("moes", f) or []

    async def activities(self) -> list[dict]:
        async def f():
            from ..routers.validation import list_activities
            return await list_activities(self.study_id)
        return await self.get("activities", f) or []

    async def need_validation(self) -> list[dict]:
        async def f():
            from ..routers.validation import list_need_validation
            return await list_need_validation(self.study_id)
        return await self.get("need_validation", f) or []

    async def assumptions(self) -> list[dict]:
        async def f():
            from ..routers.assumptions import list_assumptions
            return await list_assumptions(self.study_id)
        return await self.get("assumptions", f) or []

    async def ait_models(self) -> list[dict]:
        async def f():
            from . import ait
            return await ait.list_models(self.study_id)
        return await self.get("ait_models", f) or []

    async def table_rows(self, module: str, cls: str) -> list[Any] | None:
        """Rows of another agent's wave-3 table (allocation ledger, ICD issues), or None."""
        async def f():
            import importlib
            from sqlalchemy import select
            from ..db.engine import get_session_factory
            model = getattr(importlib.import_module(f"..db.{module}", __package__), cls)
            async with get_session_factory()() as s:
                return list((await s.execute(select(model).where(model.study_id == self.study_id))).scalars())
        return await self.get(f"rows:{module}.{cls}", f)


R = tuple[str, dict[str, str], list[str]]      # state, evidence {en, fr}, refs


# ─── object queries ────────────────────────────────────────────────────────

def _need(study) -> Any:
    return getattr(study, "mission_need", None)


async def q_problem_statement(ctx: Ctx, spec: dict) -> R:
    ps = str(getattr(_need(ctx.study), "problem_statement", "") or "").strip()
    if not ps:
        return "missing", E("No problem statement yet.", "Pas encore d’énoncé du problème."), []
    words = len(ps.split())
    return ("ok" if words >= 8 else "warn",
            E(f"Problem statement written ({words} words).", f"Énoncé du problème rédigé ({words} mots)."), [])


async def q_stakeholder_register(ctx: Ctx, spec: dict) -> R:
    stk = list(getattr(_need(ctx.study), "stakeholders", None) or [])
    if not stk:
        return "missing", E("No stakeholder in the register.", "Aucune partie prenante au registre."), []
    cats: dict[str, int] = {}
    for s in stk:
        for c in s.categories or []:
            cats[c] = cats.get(c, 0) + 1
    uncl = [s.name for s in stk if not s.categories]
    no_auth = [s.name for s in stk if not str(s.authority or "").strip()]
    n_cat = len(cats)
    en = f"{len(stk)} stakeholders in {n_cat} categories"
    fr = f"{len(stk)} parties prenantes en {n_cat} catégories"
    if uncl or "decision_authority" not in cats:
        why_en = f"; {len(uncl)} not classified" if uncl else "; no decision authority named"
        why_fr = f"; {len(uncl)} non classées" if uncl else "; aucune autorité de décision nommée"
        return "warn", E(en + why_en + ".", fr + why_fr.replace("; ", " ; ") + "."), []
    if no_auth:
        return "warn", E(f"{en}; authority not stated for {len(no_auth)}.",
                         f"{fr} ; autorité non indiquée pour {len(no_auth)}."), []
    return "ok", E(en + ".", fr + "."), sorted(cats)


async def q_objectives_moes(ctx: Ctx, spec: dict) -> R:
    objs = [o for o in getattr(_need(ctx.study), "objectives", None) or []
            if str(getattr(o.priority, "value", o.priority)) == "primary"]
    if not objs:
        return "missing", E("No primary objective.", "Aucun objectif principal."), []
    moes = await ctx.moes()
    no_measure = [o.id for o in objs if not str(o.measurable_criterion or "").strip()]
    no_moe = [o.id for o in objs if not any(o.id in (m.get("objectives") or []) for m in moes)]
    ph = [m["code"] for m in moes if m.get("placeholder")]
    base_en = f"{len(objs)} primary objectives, {len(moes)} MOEs"
    base_fr = f"{len(objs)} objectifs principaux, {len(moes)} MOE"
    if not moes:
        return "missing", E(f"{len(objs)} primary objectives, no MOE yet.", f"{len(objs)} objectifs principaux, aucune MOE."), []
    if no_measure or no_moe:
        miss = sorted(set(no_measure + no_moe))
        return "warn", E(f"{base_en}; no measure for {', '.join(miss)}.",
                         f"{base_fr} ; pas de mesure pour {', '.join(miss)}."), miss
    if ph:
        return "warn", E(f"{base_en}; {', '.join(ph)} to co-define with the communities (not set by the team).",
                         f"{base_fr} ; {', '.join(ph)} à co-définir avec les communautés (pas fixées par l’équipe)."), ph
    return "ok", E(base_en + ".", base_fr + "."), []


async def q_alternatives(ctx: Ctx, spec: dict) -> R:
    need = _need(ctx.study)
    alts = list(getattr(need, "alternatives_considered", None) or [])
    if len(alts) < 2:
        return "missing", E(f"{len(alts)} alternative considered.", f"{len(alts)} solution envisagée."), []
    non_space = bool(getattr(need, "has_non_space_alternative", False))
    sel = getattr(need, "selected_alternative_id", None)
    en = f"{len(alts)} alternatives" + (", one without a new spacecraft" if non_space else ", all need a new spacecraft")
    fr = f"{len(alts)} solutions" + (", dont une sans nouveau véhicule" if non_space else ", toutes avec un nouveau véhicule")
    if not non_space or not sel:
        return "warn", E(en + ("" if sel else "; none selected") + ".", fr + ("" if sel else ", aucune retenue") + "."), []
    return "ok", E(en + "; one selected.", fr + " ; une retenue."), []


async def q_need_validation(ctx: Ctx, spec: dict) -> R:
    needs = [n.id for n in getattr(_need(ctx.study), "stakeholder_needs", None) or []]
    nv = {n["need_code"] for n in await ctx.need_validation()}
    if not needs:
        return "missing", E("No stakeholder need (SN) recorded.", "Aucun besoin (SN) consigné."), []
    missing = [n for n in needs if n not in nv]
    if len(missing) == len(needs):
        return "missing", E(f"None of the {len(needs)} needs has a validation plan.",
                            f"Aucun des {len(needs)} besoins n’a de plan de validation."), missing
    if missing:
        return "warn", E(f"{len(needs) - len(missing)}/{len(needs)} needs have a validation plan; missing {', '.join(missing)}.",
                         f"{len(needs) - len(missing)}/{len(needs)} besoins ont un plan de validation ; manquent {', '.join(missing)}."), missing
    return "ok", E(f"All {len(needs)} needs have a validation plan.", f"Les {len(needs)} besoins ont un plan de validation."), []


async def q_validation_at_stage(ctx: Ctx, spec: dict) -> R:
    stage = str(spec.get("stage") or ctx.gate).upper()
    acts = [a for a in await ctx.activities() if stage in (a.get("stages") or [a.get("stage")])]
    if not acts:
        return "missing", E(f"No validation activity at {stage}.", f"Aucune activité de validation en {stage}."), []
    eng = [a["code"] for a in acts if a.get("engineers_only")]
    codes = [a["code"] for a in acts]
    done = [a["code"] for a in acts if a.get("status") == "done"]
    en = f"{', '.join(codes)} at {stage}" + (f" ({len(done)} done)" if done else " (planned)")
    fr = f"{', '.join(codes)} en {stage}" + (f" ({len(done)} réalisées)" if done else " (planifiées)")
    if eng and len(eng) == len(acts):
        return "warn", E(en + "; performed by the engineering team only.", fr + " ; menées par l’équipe d’ingénierie seule."), codes
    return "ok", E(en + ".", fr + "."), codes


async def q_validation_coverage(ctx: Ctx, spec: dict) -> R:
    from ..routers.validation import coverage
    cov = await coverage(ctx.study_id)
    if not cov["activities"]:
        return "missing", E("No validation activity yet.", "Aucune activité de validation."), []
    if cov["ok"]:
        return "ok", E(f"Every primary objective ({', '.join(cov['primary'])}) has a validation activity with a stakeholder.",
                       f"Chaque objectif principal ({', '.join(cov['primary'])}) a une activité de validation avec une partie prenante."), cov["primary"]
    un = cov["uncovered_primary"]
    return "warn", E(f"No stakeholder-performed validation for {', '.join(un) or 'the primary objectives'}.",
                     f"Pas de validation menée par une partie prenante pour {', '.join(un) or 'les objectifs principaux'}."), un


async def q_validation_in_orbit(ctx: Ctx, spec: dict) -> R:
    acts = [a for a in await ctx.activities() if set(a.get("stages") or []) & {"CRR", "IOV", "PHASE_E"}]
    if not acts:
        return "missing", E("No in-orbit validation activity.", "Aucune activité de validation en orbite."), []
    codes = [a["code"] for a in acts]
    return "ok", E(f"In-orbit validation planned: {', '.join(codes)}.", f"Validation en orbite planifiée : {', '.join(codes)}."), codes


def _level(r: dict) -> str:
    return str(r.get("level") or r.get("tool_level") or "").lower()


async def q_requirements_at_level(ctx: Ctx, spec: dict) -> R:
    lv, mn = str(spec.get("level") or "mission"), int(spec.get("min") or 1)
    rows = [r for r in await ctx.requirements() if _level(r) == lv and not str(r.get("code") or "").startswith("OBJ-")]
    n = len(rows)
    if n < mn:
        return "missing", E(f"{n} {lv} requirements.", f"{n} exigences de niveau {lv}."), []
    return "ok", E(f"{n} {lv} requirements.", f"{n} exigences de niveau {lv}."), []


def _has_method(r: dict) -> bool:
    return bool(r.get("verification_method") or r.get("verification_methods"))


async def q_requirements_verifiable(ctx: Ctx, spec: dict) -> R:
    lv = spec.get("level")
    rows = [r for r in await ctx.requirements() if (not lv or _level(r) == lv)
            and not str(r.get("code") or "").startswith(("OBJ-", "SN-"))]
    if not rows:
        return "missing", E(f"No {lv or ''} requirement yet.".replace("  ", " "),
                            f"Aucune exigence {('de niveau ' + lv) if lv else ''} pour l’instant.".replace("  ", " ")), []
    no_m = [r.get("code") for r in rows if not _has_method(r)]
    if no_m:
        return "warn", E(f"{len(rows) - len(no_m)}/{len(rows)} have a verification method; e.g. {', '.join(map(str, no_m[:3]))}.",
                         f"{len(rows) - len(no_m)}/{len(rows)} ont une méthode de vérification ; p. ex. {', '.join(map(str, no_m[:3]))}."), [str(c) for c in no_m[:10]]
    return "ok", E(f"{len(rows)} requirements, each with a verification method.",
                   f"{len(rows)} exigences, chacune avec une méthode de vérification."), []


def level_of(state: dict) -> str:
    """The trade level enum from the stored level (D's enum, or the v2 free text)."""
    raw = str(state.get("level") or "").strip().lower()
    if raw in ("mission", "system", "architecture", "subsystem", "equipment"):
        return raw
    if "architecture" in raw:
        return "architecture"
    if raw.startswith("subsystem") or ":" in raw:
        return "subsystem"
    if raw.startswith("mission"):
        return "mission"
    if raw.startswith("system"):
        return "system"
    if raw.startswith("equipment") or raw.startswith("unit"):
        return "equipment"
    return "subsystem" if raw else ""


def trades_of(study: Any) -> list[dict]:
    from . import trades as tr
    out = []
    for tid, rec in tr.normalise_records(getattr(study, "trade_records", None) or {}).items():
        st = dict((rec or {}).get("state") or {})
        st.setdefault("id", tid)
        out.append({"id": st.get("id") or tid, "title": st.get("title") or "", "level": level_of(st),
                    "gate": str(st.get("gate") or "").lower(), "decided": st.get("status") == "decided"
                    or bool((st.get("decision") or {}).get("selected"))})
    return out


async def q_trades_decided(ctx: Ctx, spec: dict) -> R:
    levels = set(spec.get("levels") or ["mission", "system", "architecture"])
    ts = [t for t in trades_of(ctx.study) if t["level"] in levels]
    dec = [t["id"] for t in ts if t["decided"]]
    mn = int(spec.get("min") or 1)
    if len(dec) >= mn:
        return "ok", E(f"{len(dec)} decided: {', '.join(dec)}.", f"{len(dec)} décidés : {', '.join(dec)}."), dec
    if ts:
        return "warn", E(f"{len(ts)} trades, {len(dec)} decided.", f"{len(ts)} compromis, {len(dec)} décidés."), [t["id"] for t in ts]
    return "missing", E("No trade recorded at mission, system or architecture level.",
                        "Aucun compromis consigné au niveau mission, système ou architecture."), []


async def q_section_ready(ctx: Ctx, spec: dict) -> R:
    import importlib
    from .export_context import CollectContext
    name = str(spec.get("section"))
    mod = importlib.import_module(f".export_context.sections.{name}", __package__)
    res = await mod.collect(CollectContext(study_id=ctx.study_id, study=ctx.study, gate=ctx.gate))
    if (res or {}).get("status") == "not_implemented":
        return "warn", E("The generator for this document is not available yet in this version.",
                         "Le générateur de ce document n’est pas encore disponible dans cette version."), []
    return "ok", E("The document can be generated from the study.", "Le document peut être produit à partir de l’étude."), []


async def q_ait_models(ctx: Ctx, spec: dict) -> R:
    ms = await ctx.ait_models()
    mn = int(spec.get("min") or 1)
    if len(ms) < mn:
        return "missing", E("No model philosophy yet.", "Pas encore de philosophie des modèles."), []
    codes = [m["code"] for m in ms]
    return "ok", E(f"{len(ms)} models: {', '.join(codes)}.", f"{len(ms)} modèles : {', '.join(codes)}."), codes


async def q_assumptions_register(ctx: Ctx, spec: dict) -> R:
    a = await ctx.assumptions()
    op = [x for x in a if x["status"] == "open"]
    return "info", E(f"{len(a)} assumptions in the register, {len(op)} open.",
                     f"{len(a)} hypothèses au registre, {len(op)} ouvertes."), [x["code"] for x in op]


async def q_budget_assumptions(ctx: Ctx, spec: dict) -> R:
    a = [x for x in await ctx.assumptions() if x["status"] == "open"
         and any(f.get("kind") == "budget" for f in x.get("affects") or [])]
    if not a:
        return "ok", E("No budget line rests on an open assumption.", "Aucune ligne de bilan ne repose sur une hypothèse ouverte."), []
    lines = sorted({f["ref"] for x in a for f in x["affects"] if f.get("kind") == "budget"})
    return "warn", E(f"{len(a)} open assumptions under {len(lines)} budget lines.",
                     f"{len(a)} hypothèses ouvertes sous {len(lines)} lignes de bilan."), [x["code"] for x in a]


async def q_functions(ctx: Ctx, spec: dict) -> R:
    d = await ctx.diagram_data()
    n = len(getattr(d, "functions", None) or []) if d else 0
    if not n:
        n = len(getattr(getattr(ctx.study, "functional_decomposition", None), "functions", None) or [])
    if n < int(spec.get("min") or 1):
        return "missing", E("No function yet.", "Aucune fonction pour l’instant."), []
    alloc = len(getattr(d, "allocations", None) or []) if d else 0
    return "ok", E(f"{n} functions, {alloc} allocations.", f"{n} fonctions, {alloc} allocations."), []


async def q_risks(ctx: Ctx, spec: dict) -> R:
    rs = list(getattr(ctx.study, "risk_register", None) or [])
    if len(rs) < int(spec.get("min") or 1):
        return "missing", E("No risk registered.", "Aucun risque enregistré."), []
    res = sum(1 for r in rs if (r.get("residual_likelihood") if isinstance(r, dict) else None))
    return "ok", E(f"{len(rs)} risks ({res} with residual risk).", f"{len(rs)} risques ({res} avec risque résiduel)."), []


async def q_conops(ctx: Ctx, spec: dict) -> R:
    d = await ctx.diagram_data()
    modes = len(getattr(d, "modes", None) or []) if d else 0
    phases = len(getattr(getattr(ctx.study, "conops", None), "phases", None) or [])
    if not modes and not phases:
        return "missing", E("No mode or mission phase yet.", "Aucun mode ni phase de mission."), []
    return "ok", E(f"{phases} mission phases, {modes} modes.", f"{phases} phases de mission, {modes} modes."), []


async def q_mission_analysis(ctx: Ctx, spec: dict) -> R:
    orbit = getattr(getattr(ctx.study, "requirements", None), "orbit", None)
    alt = getattr(orbit, "altitude_km", None)
    if not alt:
        return "missing", E("No orbit defined.", "Aucune orbite définie."), []
    ot = str(getattr(getattr(orbit, "orbit_type", None), "value", getattr(orbit, "orbit_type", "")) or "").upper()
    return "ok", E(f"{ot} orbit at {alt:g} km.", f"Orbite {ot} à {alt:g} km."), []


async def q_product_tree(ctx: Ctx, spec: dict) -> R:
    d = await ctx.diagram_data()
    els = [e for e in (getattr(d, "elements", None) or []) if e.get("element_type") not in ("mode",)] if d else []
    if not els:
        return "missing", E("No element in the product tree.", "Aucun élément dans l’arbre produit."), []
    return "ok", E(f"{len(els)} elements.", f"{len(els)} éléments."), []


async def q_interfaces(ctx: Ctx, spec: dict) -> R:
    rows = await ctx.table_rows("models_icd", "IcdIssueRow")
    if rows:
        ok = [r for r in rows if str(getattr(r, "state", "")).lower() in ("issue_a", "baselined", "issue_b")]
        both = [r for r in ok if len(getattr(r, "signoffs_json", None) or {}) >= 2]
        st = "ok" if len(both) == len(rows) else "warn"
        return st, E(f"{len(rows)} ICDs under issue control, {len(ok)} at issue A or later, {len(both)} signed by both owners.",
                     f"{len(rows)} ICD sous contrôle d’édition, {len(ok)} à l’édition A ou plus, {len(both)} signés par les deux responsables."), []
    d = await ctx.diagram_data()
    n = len(getattr(d, "interfaces", None) or []) if d else 0
    if not n:
        return "missing", E("No interface defined.", "Aucune interface définie."), []
    return "warn", E(f"{n} interfaces defined; no ICD under issue control yet.",
                     f"{n} interfaces définies ; aucun ICD sous contrôle d’édition."), []


async def q_allocations_agreed(ctx: Ctx, spec: dict) -> R:
    rows = await ctx.table_rows("models_alloc", "AllocationLedgerRow")
    if not rows:
        return "missing", E("No allocation in the ledger yet.", "Aucune allocation dans le registre pour l’instant."), []
    agreed = [r for r in rows if str(getattr(r, "status", "")) == "agreed"]
    disp = [r for r in rows if str(getattr(r, "status", "")) == "disputed"]
    if len(agreed) == len(rows):
        return "ok", E(f"{len(rows)} allocations, all agreed by their owners.",
                       f"{len(rows)} allocations, toutes approuvées par leurs responsables."), []
    return "warn", E(f"{len(agreed)}/{len(rows)} allocations agreed, {len(disp)} disputed.",
                     f"{len(agreed)}/{len(rows)} allocations approuvées, {len(disp)} contestées."), []


OBJECT_QUERIES: dict[str, Callable[[Ctx, dict], Awaitable[R]]] = {
    "problem_statement": q_problem_statement, "stakeholder_register": q_stakeholder_register,
    "objectives_moes": q_objectives_moes, "alternatives": q_alternatives, "need_validation": q_need_validation,
    "validation_at_stage": q_validation_at_stage, "validation_coverage": q_validation_coverage,
    "validation_in_orbit": q_validation_in_orbit, "requirements_at_level": q_requirements_at_level,
    "requirements_verifiable": q_requirements_verifiable, "trades_decided": q_trades_decided,
    "section_ready": q_section_ready, "ait_models": q_ait_models, "assumptions_register": q_assumptions_register,
    "budget_assumptions": q_budget_assumptions, "functions": q_functions, "risks": q_risks, "conops": q_conops,
    "mission_analysis": q_mission_analysis, "product_tree": q_product_tree, "interfaces": q_interfaces,
    "allocations_agreed": q_allocations_agreed,
}

#: product (gate_profiles.yaml) -> the object query that evidences it (maturity B for budgets
#: means the ledger is agreed; D accepts a draft)
PRODUCT_RULES: dict[str, tuple[str, dict]] = {
    "mission_statement": ("problem_statement", {}), "objectives": ("objectives_moes", {}),
    "concept_report": ("alternatives", {}), "trade_reports": ("trades_decided", {"levels": ["mission", "system", "architecture"]}),
    "conops": ("conops", {}), "mission_analysis": ("mission_analysis", {}),
    "trs": ("requirements_at_level", {"level": "mission", "min": 1}), "function_tree": ("functions", {}),
    "product_tree": ("product_tree", {}), "budgets": ("allocations_agreed", {}), "interfaces": ("interfaces", {}),
    "aiv_plan": ("ait_models", {}), "vcd": ("requirements_verifiable", {}), "risk_register": ("risks", {}),
}


# ─── item evaluation ───────────────────────────────────────────────────────

async def _product(ctx: Ctx, it: dict) -> R:
    rule = PRODUCT_RULES.get(it.get("ref"))
    if rule is None:
        return "info", E("No automatic evidence rule: the review board judges this product.",
                         "Pas de règle de preuve automatique : le comité de revue juge ce produit."), []
    q, params = rule
    state, ev, refs = await OBJECT_QUERIES[q](ctx, {**params, **{k: v for k, v in it.items() if k in ("min",)}})
    if it.get("ref") == "budgets" and it.get("maturity") == "D" and state == "warn":
        state = "ok"
    return state, ev, refs


async def _diagram(ctx: Ctx, it: dict) -> R:
    from . import diagrams as dg
    kind = it.get("ref")
    if kind not in dg.KINDS:
        return "missing", E("This diagram is not available yet in this version.",
                            "Ce diagramme n’est pas encore disponible dans cette version."), []
    if dg.KINDS[kind].get("fn") is None:
        return "info", E("Shown on its own tab.", "Affiché dans son propre onglet."), []
    data = await ctx.diagram_data()
    if data is None:
        return "missing", E("The study model could not be read.", "Le modèle de l’étude n’a pas pu être lu."), []
    m = dg.build(kind, data)
    if m.get("empty"):
        return "missing", E("Nothing to draw yet.", "Rien à tracer pour l’instant."), []
    alarms = [g for g in m.get("gaps") or [] if g.get("severity") == "alarm"]
    comp = m.get("completeness")
    pct = f" ({round(100 * comp)} % complete)" if isinstance(comp, (int, float)) else ""
    pct_fr = f" (complet à {round(100 * comp)} %)" if isinstance(comp, (int, float)) else ""
    if alarms:
        return "warn", E(f"Drawn with {len(alarms)} gaps to fix{pct}.", f"Tracé avec {len(alarms)} lacunes à corriger{pct_fr}."), []
    return "ok", E(f"Drawn from the model{pct}.", f"Tracé à partir du modèle{pct_fr}."), []


async def _trade(ctx: Ctx, it: dict) -> R:
    levels, gates, mn = set(it.get("levels") or []), set(it.get("gates") or []), int(it.get("min") or 1)
    all_t = trades_of(ctx.study)
    ts = [t for t in all_t if t["level"] in levels and t["gate"] in gates]
    lab = "/".join(sorted(g.upper() for g in gates))
    if not ts:
        others = {}
        for t in all_t:
            others[t["level"] or "?"] = others.get(t["level"] or "?", 0) + 1
        o_en = ", ".join(f"{n} {k}-level" for k, n in sorted(others.items())) or "none at any level"
        o_fr = ", ".join(f"{n} de niveau {k}" for k, n in sorted(others.items())) or "aucun à aucun niveau"
        return "missing", E(f"0 {'/'.join(sorted(levels))}-level trades at {lab}; {o_en}.",
                            f"0 compromis de niveau {'/'.join(sorted(levels))} en {lab} ; {o_fr}."), []
    open_ = [t["id"] for t in ts if not t["decided"]]
    dec = [t["id"] for t in ts if t["decided"]]
    if open_:
        return "warn", E(f"{', '.join(dec) + ' decided; ' if dec else ''}{', '.join(open_)} undecided.",
                         f"{', '.join(dec) + ' décidés ; ' if dec else ''}{', '.join(open_)} non décidés.".replace(" ;", " ;")), [t["id"] for t in ts]
    if len(dec) < mn:
        return "warn", E(f"{len(dec)} of {mn} trades decided: {', '.join(dec)}.",
                         f"{len(dec)} compromis sur {mn} décidés : {', '.join(dec)}."), dec
    return "ok", E(f"Decided: {', '.join(dec)}.", f"Décidés : {', '.join(dec)}."), dec


async def _criteria(ctx: Ctx, it: dict) -> R:
    if _IN_CRITERIA.get():
        return "info", E("Evaluated by the gate checklist.", "Évalué par la liste du jalon."), []
    tok = _IN_CRITERIA.set(True)
    try:
        from ..routers.gates import evaluate_study_gate
        ev = await evaluate_study_gate(ctx.study_id, ctx.gate)
        c = next((c for c in ev.get("criteria") or [] if c.get("id") == it.get("ref")), None)
    finally:
        _IN_CRITERIA.reset(tok)
    if c is None:
        return "info", E("Criterion not in this gate's checklist.", "Critère absent de la liste de ce jalon."), []
    st = {"pass": "ok", "fail": "missing"}.get(c.get("status"), "warn")
    found = str(c.get("evidence_found") or c.get("status"))
    return st, E(found, found), [str(it.get("ref"))]


async def _document(ctx: Ctx, it: dict) -> R:
    chk = dict(it.get("check") or {})
    return await OBJECT_QUERIES[chk.pop("query")](ctx, chk)


async def _gate_passed(ctx: Ctx, it: dict) -> R:
    ref = it.get("ref")
    states = getattr(ctx.study, "gate_states", None) or {}
    try:
        from ..routers.gates import study_profile
        gates = study_profile(ctx.study).get("gates") or []
    except Exception:  # noqa: BLE001
        gates = []
    pg = next((g for g in gates if ref in (g.get("covers") or [])), None)
    if pg is not None and ctx.gate == pg["id"]:
        return "ok", E("Held in this review.", "Tenu dans cette revue."), []
    gid = pg["id"] if pg else ref
    if (states.get(gid) or {}).get("state") == "passed":
        return "ok", E(f"{str(pg.get('short') if pg else ref).upper()} passed.", f"{str(pg.get('short') if pg else ref).upper()} passée."), [gid]
    return "missing", E(f"{str(pg.get('short') if pg else ref).upper()} not passed yet.",
                        f"{str(pg.get('short') if pg else ref).upper()} pas encore passée."), [gid]


async def _reading(ctx: Ctx, it: dict, sources: dict) -> R:
    src = sources.get(it.get("ref"), it.get("ref"))
    return "info", E(str(src), str(src)), []


async def _assumptions_due(ctx: Ctx, it: dict) -> tuple[str, dict, list[str], list[dict]]:
    from ..routers.assumptions import due_by
    a = [x for x in await ctx.assumptions() if x["status"] == "open" and due_by(x, ctx.gate)]
    if not a:
        return "ok", E("No open assumption is due by this gate.", "Aucune hypothèse ouverte n’est à lever pour ce jalon."), [], []
    items = [{"code": x["code"], "statement": x["statement"], "owner_seat": x["owner_seat"],
              "due_gate": x["due_gate"], "replace_with": x["replace_with"]} for x in a]
    return "warn", E(f"{len(a)} open assumptions are due by {ctx.gate.upper()}.",
                     f"{len(a)} hypothèses ouvertes sont à lever pour la {ctx.gate.upper()}."), [x["code"] for x in a], items


def _out(it: dict, state: str, ev: dict, refs: list[str], lang: str, extra: dict | None = None) -> dict[str, Any]:
    o = {"id": it["id"], "kind": it.get("kind"), "label": dict(it.get("label") or {}), "state": state,
         "evidence": ev.get(lang) or ev.get("en", ""), "evidence_i18n": ev, "refs": refs,
         "severity": it.get("severity", "warn"), "owner_seat": it.get("owner_seat"), "fix": it.get("fix"),
         "draft": it.get("draft")}
    for k in ("ref", "maturity", "levels", "gates", "query", "stage", "where"):
        if it.get(k) is not None:
            o[k] = it[k]
    if extra:
        o.update(extra)
    return o


async def evaluate(study_id: str, gate: str | None = None, *, study: Any = None, lang: str = "en",
                   covers: list[str] | None = None) -> dict[str, Any]:
    """Every entry, deliverable and analysis item of the protocol for ``gate`` (a profile gate id,
    default: the study's current gate) with its state and evidence. The same result feeds
    ``/phase``, the gate ``start`` warnings (D), the ``<GATE>-SE-01`` criterion (R) and the pack
    index (X)."""
    from . import se_protocol as sp
    from . import gate_profiles as gp
    if study is None:
        from ..routers.studies import get_study_store
        study = get_study_store().get(study_id)
    data = sp.load()
    pg = sp.profile_gate(study, gate)
    gid = (gp.legacy_gate_id(pg.get("id")) or pg.get("id")) if pg else (gate or "mdr")
    covers = covers or [c for c in (pg.get("covers") if pg else [gid]) if c in sp.CANONICAL]
    ctx = Ctx(study_id, study, gid)
    sources = dict(data.get("sources") or {})
    entry, deliv, analysis = [], [], []
    seen: set[str] = set()
    for c in covers:
        blk = (data.get("phases") or {}).get(c) or {}
        for it in blk.get("entry") or []:
            if it["id"] in seen:
                continue
            seen.add(it["id"])
            k = it.get("kind")
            if k == "gate_passed":
                st, ev, refs = await _gate_passed(ctx, it)
            elif k == "reading":
                st, ev, refs = await _reading(ctx, it, sources)
            elif k == "criteria":
                st, ev, refs = await _criteria(ctx, it)
            else:
                st, ev, refs = await OBJECT_QUERIES[it["query"]](ctx, it)
            entry.append(_out(it, st, ev, refs, lang))
        for it in blk.get("deliverables") or []:
            if it["id"] in seen:
                continue
            seen.add(it["id"])
            fn = {"product": _product, "diagram": _diagram, "trade": _trade, "criteria": _criteria,
                  "document": _document}.get(it.get("kind"))
            try:
                st, ev, refs = await (fn(ctx, it) if fn else OBJECT_QUERIES[it["query"]](ctx, it))
            except Exception as exc:  # noqa: BLE001 — one broken item must not hide the others
                logger.exception("deliverable %s failed for %s", it.get("id"), study_id)
                st, ev, refs = "missing", E(f"Could not be evaluated: {str(exc)[:120]}",
                                            f"Évaluation impossible : {str(exc)[:120]}"), []
            deliv.append(_out(it, st, ev, refs, lang))
        for it in blk.get("analysis") or []:
            if it["id"] in seen:
                continue
            seen.add(it["id"])
            if it.get("kind") == "assumptions_due":
                st, ev, refs, items = await _assumptions_due(ctx, it)
                analysis.append(_out(it, st, ev, refs, lang, {"items": items}))
            else:
                st, ev, refs = await OBJECT_QUERIES[it["query"]](ctx, it)
                analysis.append(_out(it, st, ev, refs, lang))
    allx = entry + deliv + analysis
    summary = {s: sum(1 for x in deliv if x["state"] == s) for s in ("ok", "warn", "missing", "info")}
    summary["total"] = len(deliv)
    gaps = [x for x in deliv + entry if x["state"] in ("warn", "missing") and x["severity"] != "info"]
    warnings = [{"id": x["id"], "label": x["label"], "state": x["state"], "evidence": x["evidence"],
                 "owner_seat": x.get("owner_seat"), "severity": x["severity"], "kind": x["kind"]} for x in gaps]
    warnings += [{"id": x["id"], "label": x["label"], "state": x["state"], "evidence": x["evidence"],
                  "owner_seat": None, "severity": x["severity"], "kind": "analysis"}
                 for x in analysis if x["state"] == "warn" and x["severity"] != "info"]
    return {"study_id": study_id, "gate": gid, "covers": covers, "entry": entry, "deliverables": deliv,
            "analysis": analysis, "summary": summary,
            "missing": [x["id"] for x in deliv if x["state"] in ("warn", "missing") and x["severity"] != "info"],
            "blocking": [x["id"] for x in gaps if x["severity"] == "block"],
            "out_of_order": [x["id"] for x in entry if x["kind"] == "gate_passed" and x["state"] == "missing"],
            "warnings": warnings, "ok": not any(x["state"] in ("warn", "missing") for x in deliv if x["severity"] != "info"),
            "_n": len(allx)}


__all__ = ["OBJECT_QUERIES", "PRODUCT_RULES", "evaluate", "level_of", "trades_of"]
