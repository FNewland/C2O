"""Prefill a decision record from the study's current state.

Used when a student records a decision from the logbook's open-decision list
(no capture point in front of them). Each catalogue ``prefill`` source with
``server: true`` has a reader here; ``server: false`` sources (orbit trade
results, Pugh matrix, gate checklist…) exist only in the browser at the
capture point, which sends its own prefill.

Reads the server's in-memory study, element, interface and requirement
caches (the same ones the REST routes read); it never writes. Every reader is
best-effort: a missing study or element gives an empty fragment, never an
error, because a record can always be written by hand.

Labels are in the participant's language; values keep their units.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Catalogue sources this module can read from the study (``server: true`` in
# decision_catalogue.yaml; a test keeps the two in step).
SERVER_SOURCES = frozenset({
    "mission_need", "mission_trade", "study_requirements", "architecture", "selected_orbit", "constellation",
    "selected_equipment", "interfaces", "budget_mass", "budget_power", "budget_data", "budget_cost",
    "requirements", "conops",
})

_L = {
    "mission_type": {"en": "Mission type", "fr": "Type de mission"},
    "orbit": {"en": "Orbit", "fr": "Orbite"},
    "altitude": {"en": "Altitude", "fr": "Altitude"},
    "inclination": {"en": "Inclination", "fr": "Inclinaison"},
    "lifetime": {"en": "Design lifetime", "fr": "Durée de vie nominale"},
    "target_mass": {"en": "Target mass", "fr": "Masse cible"},
    "target_cost": {"en": "Target cost", "fr": "Coût cible"},
    "payload_mass": {"en": "Payload mass", "fr": "Masse de la charge utile"},
    "payload_power": {"en": "Payload power", "fr": "Puissance de la charge utile"},
    "payload_rate": {"en": "Payload data rate", "fr": "Débit de la charge utile"},
    "pointing": {"en": "Pointing accuracy", "fr": "Précision de pointage"},
    "context": {"en": "Operational context", "fr": "Contexte opérationnel"},
    "segments": {"en": "Segments", "fr": "Segments"},
    "spacecraft": {"en": "Spacecraft", "fr": "Véhicules spatiaux"},
    "components": {"en": "Components selected", "fr": "Composants retenus"},
    "ifaces_accepted": {"en": "Interfaces accepted", "fr": "Interfaces acceptées"},
    "ifaces_suggested": {"en": "Interfaces still suggested", "fr": "Interfaces encore proposées"},
    "ifaces_rejected": {"en": "Interfaces rejected", "fr": "Interfaces rejetées"},
    "nominal": {"en": "{b}: nominal", "fr": "{b} : nominal"},
    "with_margin": {"en": "{b}: with maturity margin", "fr": "{b} : avec marge de maturité"},
    "allocation": {"en": "{b}: allocation", "fr": "{b} : allocation"},
    "margin": {"en": "{b}: margin to allocation", "fr": "{b} : marge par rapport à l’allocation"},
    "margin_line": {"en": "{b} margin to allocation {m} % ({status})", "fr": "Marge {b} par rapport à l’allocation {m} % ({status})"},
    "margin_none": {"en": "{b}: no allocation set, so no margin to allocation yet", "fr": "{b} : aucune allocation définie, donc pas encore de marge"},
    "reqs": {"en": "Requirements ({lvl})", "fr": "Exigences ({lvl})"},
    "reqs_method": {"en": "Requirements with a verification method", "fr": "Exigences avec méthode de vérification"},
    "modes": {"en": "Operational modes", "fr": "Modes opérationnels"},
    "walker": {"en": "Constellation pattern", "fr": "Configuration de constellation"},
    "problem": {"en": "Problem statement", "fr": "Énoncé du problème"},
}
_BUDGET = {
    "mass": {"en": "Mass", "fr": "Masse"}, "power": {"en": "Power", "fr": "Puissance"},
    "data": {"en": "Data", "fr": "Données"}, "cost": {"en": "Cost", "fr": "Coût"},
}
_STATUS = {
    "green": {"en": "above 20 %", "fr": "au-dessus de 20 %"},
    "amber": {"en": "0 to 20 %", "fr": "entre 0 et 20 %"},
    "red": {"en": "negative", "fr": "négative"},
}


def _t(key: str, lang: str, table: dict = _L, **kw: Any) -> str:
    entry = table.get(key) or {}
    text = entry.get(lang) or entry.get("en") or key
    if lang == "fr":
        text = text.replace(" :", " :").replace(" %", " %")
    return text.format(**kw) if kw else text


def _ev(label: str, value: Any, unit: str | None = None) -> dict:
    out = {"label": label, "value": value}
    if unit:
        out["unit"] = unit
    return out


def _study(study_id: str | None):
    if not study_id:
        return None
    try:
        from ..routers.studies import get_study_store
        return get_study_store().get(study_id)
    except Exception as e:  # noqa: BLE001 - best effort
        logger.debug("prefill: no study store: %s", e)
        return None


def _elements(study_id: str | None) -> list[dict]:
    if not study_id:
        return []
    try:
        from ..routers.elements import _elements as els
    except Exception:  # noqa: BLE001
        return []
    return [e for e in els.values() if e.get("study_id") == study_id and not e.get("deleted_at")]


def _root(elements: list[dict]) -> dict | None:
    roots = [e for e in elements if not e.get("parent_id")]
    return roots[0] if roots else None


def _enum(v: Any) -> Any:
    return getattr(v, "value", v)


# ─── Readers: each returns a fragment {options?, evidence?, choice?, rationale?, margin_impact?} ──

def _mission_need(study, decision_id: str, lang: str) -> dict:
    if study is None:
        return {}
    mn = study.mission_need
    out: dict[str, Any] = {}
    if decision_id == "D-1.4-PROBLEM" and mn.problem_statement:
        out["choice"] = mn.problem_statement
        if mn.operational_context:
            out["evidence"] = [_ev(_t("context", lang), mn.operational_context)]
    elif decision_id == "D-1.4-STAKEHOLDERS" and mn.stakeholders:
        out["options"] = [{"name": s.name, "summary": "; ".join(s.needs or []),
                           "values": {"role": _enum(s.role), "priority": s.priority}}
                          for s in mn.stakeholders if s.name]
    elif decision_id == "D-1.4-OBJECTIVES" and mn.objectives:
        out["options"] = [{"name": o.text, "summary": o.measurable_criterion or "",
                           "values": {"priority": _enum(o.priority)},
                           "chosen": _enum(o.priority) == "primary"}
                          for o in mn.objectives if o.text]
    elif decision_id == "D-1.4-SPACE" and mn.alternatives_considered:
        out["options"] = [{"name": a.name, "summary": a.description[:200] if a.description else "",
                           "score": round(float(a.feasibility_score or 0), 3),
                           "chosen": _enum(a.decision) == "selected" or a.id == mn.selected_alternative_id}
                          for a in mn.alternatives_considered if a.name]
        chosen = [o["name"] for o in out["options"] if o.get("chosen")]
        if chosen:
            out["choice"] = chosen[0]
        if mn.selection_rationale:
            out["rationale"] = mn.selection_rationale
    elif mn.problem_statement:
        out["evidence"] = [_ev(_t("problem", lang), mn.problem_statement[:200])]
    return out


def _study_requirements(study, lang: str) -> dict:
    if study is None:
        return {}
    r = study.requirements
    ev = [_ev(_t("mission_type", lang), str(_enum(r.mission_type)).replace("_", " ")),
          _ev(_t("orbit", lang), str(_enum(r.orbit.orbit_type)).upper()),
          _ev(_t("altitude", lang), r.orbit.altitude_km, "km"),
          _ev(_t("inclination", lang), r.orbit.inclination_deg, "°"),
          _ev(_t("lifetime", lang), r.design_lifetime_years, "yr" if lang == "en" else "ans")]
    if r.target_mass_kg:
        ev.append(_ev(_t("target_mass", lang), r.target_mass_kg, "kg"))
    if r.target_cost_meur:
        ev.append(_ev(_t("target_cost", lang), r.target_cost_meur, "M€"))
    if r.payloads:
        p = r.payloads[0]
        ev += [_ev(_t("payload_mass", lang), p.mass_kg, "kg"), _ev(_t("payload_power", lang), p.power_w, "W"),
               _ev(_t("payload_rate", lang), p.data_rate_mbps, "Mbit/s"),
               _ev(_t("pointing", lang), p.pointing_accuracy_deg, "°")]
    return {"evidence": ev}


def _architecture(elements: list[dict], lang: str) -> dict:
    segs = [e for e in elements if e.get("element_type") == "segment"]
    craft = [e for e in elements if e.get("element_type") == "system" and e.get("segment") == "space"]
    ev = []
    if segs:
        ev.append(_ev(_t("segments", lang), ", ".join(e["name"] for e in segs)))
    if craft:
        ev.append(_ev(_t("spacecraft", lang), sum(int(e.get("quantity") or 1) for e in craft)))
    return {"evidence": ev} if ev else {}


def _selected_orbit(elements: list[dict], lang: str) -> dict:
    for e in elements:
        perf = e.get("performance") or {}
        if perf.get("orbit_altitude_km"):
            ev = [_ev(_t("altitude", lang), perf["orbit_altitude_km"], "km")]
            if perf.get("orbit_inclination_deg") is not None:
                ev.append(_ev(_t("inclination", lang), perf["orbit_inclination_deg"], "°"))
            kind = str(perf.get("orbit_type") or "").upper()
            choice = f"{kind} {perf['orbit_altitude_km']} km".strip()
            if perf.get("orbit_inclination_deg") is not None:
                choice += f", {perf['orbit_inclination_deg']}°"
            return {"evidence": ev, "choice": choice}
    return {}


def _constellation(elements: list[dict], lang: str) -> dict:
    for e in elements:
        perf = e.get("performance") or {}
        if perf.get("constellation") or perf.get("walker_notation"):
            what = perf.get("walker_notation") or f"{perf.get('orbital_planes')} × {perf.get('sats_per_plane')}"
            return {"evidence": [_ev(_t("walker", lang), what), _ev(_t("spacecraft", lang), e.get("quantity") or 1)],
                    "choice": str(what)}
    return {}


def _selected_equipment(elements: list[dict], lang: str) -> dict:
    comps = [e for e in elements if e.get("element_type") == "component"]
    if not comps:
        return {}
    opts = []
    for c in comps[:MAX_OPTS]:
        vals: dict[str, Any] = {}
        if c.get("subsystem_domain"):
            vals["domain"] = c["subsystem_domain"]
        if c.get("mass_kg") is not None:
            vals["kg"] = c["mass_kg"]
        if c.get("power_avg_w") is not None:
            vals["W"] = c["power_avg_w"]
        if c.get("cost_recurring_keur") is not None:
            vals["kEUR"] = c["cost_recurring_keur"]
        if c.get("trl") is not None:
            vals["TRL"] = c["trl"]
        opts.append({"name": c["name"], "summary": c.get("manufacturer") or "", "values": vals, "chosen": True})
    return {"options": opts, "evidence": [_ev(_t("components", lang), len(comps))]}


MAX_OPTS = 20


def _interfaces(study_id: str | None, lang: str) -> dict:
    if not study_id:
        return {}
    try:
        from ..routers.elements import _interfaces as ifs
    except Exception:  # noqa: BLE001
        return {}
    here = [i for i in ifs.values() if i.get("study_id") == study_id and not i.get("deleted_at")]
    if not here:
        return {}
    by = {"accepted": 0, "suggested": 0, "rejected": 0}
    for i in here:
        st = i.get("status") or "accepted"
        by[st if st in by else "accepted"] += 1
    return {"evidence": [_ev(_t("ifaces_accepted", lang), by["accepted"]),
                         _ev(_t("ifaces_suggested", lang), by["suggested"]),
                         _ev(_t("ifaces_rejected", lang), by["rejected"])]}


async def _budget(elements: list[dict], kind: str, lang: str) -> dict:
    root = _root(elements)
    if root is None:
        return {}
    try:
        from ..routers.elements import compute_budget
        b = await compute_budget(root["id"], kind)
    except Exception as e:  # noqa: BLE001
        logger.debug("prefill: budget %s: %s", kind, e)
        return {}
    name = _t(kind, lang, _BUDGET)
    unit = {"mass": "kg", "power": "W", "data": "Mbit/s", "cost": "kEUR"}[kind]
    ev = [_ev(_t("nominal", lang, b=name), b.get("sum_nominal"), unit),
          _ev(_t("with_margin", lang, b=name), b.get("sum_with_margin"), unit)]
    if b.get("allocation") is not None:
        ev.append(_ev(_t("allocation", lang, b=name), b["allocation"], unit))
    if b.get("margin_pct") is not None:
        ev.append(_ev(_t("margin", lang, b=name), b["margin_pct"], "%"))
        m = str(b["margin_pct"]).replace(".", ",") if lang == "fr" else b["margin_pct"]
        impact = _t("margin_line", lang, b=name.lower(), m=m,
                    status=_t(b.get("status") or "red", lang, _STATUS))
    else:
        impact = _t("margin_none", lang, b=name)
    return {"evidence": ev, "margin_impact": impact}


def _requirements(study_id: str | None, lang: str) -> dict:
    if not study_id:
        return {}
    try:
        from ..routers.requirements import _requirements as reqs
    except Exception:  # noqa: BLE001
        return {}
    mine = [r for r in reqs.values() if r.get("study_id") == study_id and r.get("status") != "retired"]
    if not mine:
        return {}
    levels: dict[str, int] = {}
    for r in mine:
        levels[r.get("level") or "?"] = levels.get(r.get("level") or "?", 0) + 1
    ev = [_ev(_t("reqs", lang, lvl=k), v) for k, v in sorted(levels.items())]
    ev.append(_ev(_t("reqs_method", lang), sum(1 for r in mine if r.get("verification_method"))))
    return {"evidence": ev}


def _conops(study, lang: str) -> dict:
    if study is None or not study.conops.modes:
        return {}
    opts = [{"name": m.name or str(_enum(m.mode_type)),
             "values": {"W": m.power_w, "%": m.duty_cycle_percent}} for m in study.conops.modes[:MAX_OPTS]]
    return {"options": opts, "evidence": [_ev(_t("modes", lang), len(opts))]}


def _merge(into: dict, frag: dict) -> None:
    for k, v in frag.items():
        if not v:
            continue
        if k in ("options", "evidence"):
            if k == "options" and into.get("options"):
                continue                 # the first source's options win
            into.setdefault(k, []).extend(v)
        elif k == "margin_impact" and into.get(k):
            into[k] = f"{into[k]}\n{v}"
        else:
            into.setdefault(k, v)


async def prefill(decision: dict, study_id: str | None, lang: str) -> dict:
    """The fragment of a record SpaceCDF can fill for ``decision`` (a catalogue entry)."""
    study = _study(study_id)
    elements = _elements(study_id)
    out: dict[str, Any] = {}
    used = []
    for src in decision.get("prefill") or []:
        frag: dict = {}
        if src == "mission_need":
            frag = _mission_need(study, decision["id"], lang)
        elif src in ("mission_trade",):
            frag = _mission_need(study, decision["id"], lang) if decision["id"] == "D-1.4-SPACE" else {}
        elif src == "study_requirements":
            frag = _study_requirements(study, lang)
        elif src == "architecture":
            frag = _architecture(elements, lang)
        elif src == "selected_orbit":
            frag = _selected_orbit(elements, lang)
        elif src == "constellation":
            frag = _constellation(elements, lang)
        elif src == "selected_equipment":
            frag = _selected_equipment(elements, lang)
        elif src == "interfaces":
            frag = _interfaces(study_id, lang)
        elif src.startswith("budget_"):
            frag = await _budget(elements, src.split("_", 1)[1], lang)
        elif src == "requirements":
            frag = _requirements(study_id, lang)
        elif src == "conops":
            frag = _conops(study, lang)
        if frag:
            used.append(src)
            _merge(out, frag)
    # Evidence from several sources may repeat a label: keep the first.
    seen = set()
    ev = []
    for e in out.get("evidence") or []:
        if e["label"] in seen:
            continue
        seen.add(e["label"])
        ev.append(e)
    if ev:
        out["evidence"] = ev[:30]
    out["sources"] = used
    return out
