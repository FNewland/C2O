"""SpaceCDF — CubeSat Design Specification checks (rev 14.1), from ``configs/cds_rules.yaml``.

Deterministic checks of a CubeSat design against the CDS:

* mass per form factor (2.2.10, Table 1) — current best estimate and with margins;
* centre of gravity offset (2.2.11, Table 2) when every massive unit has a position;
* safety features: deployment switch (2.3.2), RBF (2.3.4/2.3.5), ≥ 3 RF inhibits
  (2.3.7) when a transmitter exists, ≥ 3 deployable inhibits (2.3.8) when a deployable
  exists, ≥ 3 propulsion inhibits (2.1.4) when propulsion exists;
* timers: deployables ≥ 30 min (2.4.4), RF ≥ 45 min (2.4.5) after deployment;
* protrusion ≤ 6.5 mm (2.2.3), outgassing TML ≤ 1 % / CVCM ≤ 0.1 % (2.1.7).

Evidence comes from (a) interfaces of canonical type ``electrical_signal`` with the
subtypes listed in ``recognition.links`` (the link proposer creates these: an
``inhibit`` link to a transmitter stands for ``properties.inhibit_count`` RF inhibits
and carries ``properties.delay_min``; a ``release`` link to a deployable likewise),
and (b) an
element declaration ``performance.cds`` — a C2O convention, e.g.
``{"rf_inhibits": 3, "rbf": true, "rf_delay_min": 45, "tml_percent": 0.4}``.
Missing evidence gives ``warn`` ("not declared"), a declared value that breaks the
rule gives ``fail``.
"""
from __future__ import annotations

from typing import Any

from . import rule_config as rc
from .margin_policy import evaluate_margins
from .rule_inputs import kb_component, leaves_with, live, perf, qty, space_hardware

CONFIG = "cds_rules"


def _iface_type(i: dict) -> str:
    return str(i.get("type") or i.get("interface_type") or "").lower()


def _iface_subtype(i: dict) -> str:
    props = i.get("properties") or {}
    return str(i.get("subtype") or props.get("subtype") or "").lower()


def _declared(elements: list[dict]) -> dict[str, Any]:
    """Merge every element's ``performance.cds`` declaration (max for counts, any for flags)."""
    out: dict[str, Any] = {}
    for e in live(elements):
        d = perf(e).get("cds")
        if not isinstance(d, dict):
            continue
        for k, v in d.items():
            if isinstance(v, bool):
                out[k] = out.get(k, False) or v
            elif isinstance(v, (int, float)):
                # counts and delays: the best declared value; limits (TML, protrusion): the worst.
                # Both are the maximum.
                out[k] = v if out.get(k) is None else max(out[k], v)
    return out


def _deployment(e: dict) -> str:
    kb = kb_component(e) or {}
    return str(perf(e).get("deployment") or (kb.get("performance") or {}).get("deployment")
               or kb.get("deployment") or "").lower()


def _has(elements: list[dict], keywords: list[str], domains: list[str], *, deployables: bool = False) -> list[dict]:
    """Space hardware matching a keyword (name or KB category) or a subsystem domain.

    For deployables the KB ``deployment`` field decides when it is known
    (``body_mounted`` is not a deployable; ``tape_spring``/``burn_wire``/``deployable_*`` is).
    """
    hits = []
    for e in space_hardware(elements):
        name = " " + (e.get("name") or "").lower()
        cat = str((kb_component(e) or {}).get("category") or "")
        if deployables:
            dep = _deployment(e)
            if dep:
                if dep != "body_mounted" and dep not in ("none", "fixed"):
                    hits.append(e)
                continue
        if (domains and e.get("subsystem_domain") in domains and e.get("element_type") == "component") or \
                any(k in name for k in keywords) or \
                any(k.strip() and k.strip() in cat for k in keywords):
            hits.append(e)
    return hits


def evaluate_cds(
    elements: list[dict],
    interfaces: list[dict] | None = None,
    params: dict[str, Any] | None = None,
    form_factor: str | None = None,
) -> dict[str, Any]:
    cfg = rc.load(CONFIG)
    params = params or {}
    elements = live(elements)
    ifaces = [i for i in (interfaces or []) if not i.get("deleted_at") and i.get("status") != "rejected"]
    checks: list[dict] = []

    if not form_factor or form_factor not in cfg["cubesat_form_factors"]:
        return {"applicable": False, "form_factor": form_factor, "checks": [], "summary": rc.summarise([]),
                "reason": {"en": "Not a CubeSat form factor (set a CubeSat structure from the KB or structure.form_factor_u).",
                           "fr": "Pas un facteur de forme CubeSat (choisir une structure CubeSat de la base ou structure.form_factor_u)."}}

    # ------------------------------------------------------------------ mass (Table 1)
    mnode = cfg["max_mass_kg"]
    limit = float(mnode["values"].get(form_factor, 0)) or None
    mref = rc.ref_of(cfg, mnode)
    margins = evaluate_margins(elements, params)
    cbe = margins["mass"]["cbe_kg"]
    with_m = margins["mass"]["total_wet_kg"]
    if not cbe:
        checks.append(rc.check_item("CDS-MASS", {"en": "Mass within the CDS limit", "fr": "Masse dans la limite du CDS"},
                                    "not_evaluated", {"en": "No unit masses yet.", "fr": "Pas encore de masses d’unités."},
                                    mref, limit=limit, unit="kg"))
    else:
        status = "fail" if cbe > limit else ("warn" if with_m > limit else "pass")
        checks.append(rc.check_item(
            "CDS-MASS", {"en": "Mass within the CDS limit", "fr": "Masse dans la limite du CDS"}, status,
            {"en": f"{form_factor}: estimate {rc.fmt(cbe, 2)} kg, with margins {rc.fmt(with_m, 2)} kg, "
                   f"typical limit {rc.fmt(limit, 2)} kg (the dispenser may differ, 2.2.10.2).",
             "fr": f"{form_factor} : estimation {rc.fmt_fr(cbe, 2)} kg, avec marges {rc.fmt_fr(with_m, 2)} kg, "
                   f"limite typique {rc.fmt_fr(limit, 2)} kg (le déployeur peut différer, 2.2.10.2)."},
            mref, value=round(cbe, 3), value_with_margins=round(with_m, 3), limit=limit, unit="kg"))

    # ------------------------------------------------------------------ CoG (Table 2)
    cnode, enode = cfg["cog_limits_cm"], cfg["envelope_mm"]
    lim_cm = cnode["values"].get(form_factor)
    env_m = [x / 1000 for x in enode["values"].get(form_factor, [0, 0, 0])]
    massive = leaves_with(elements, "mass_kg")
    placed = [e for e in massive if isinstance(e.get("position_json"), list) and len(e["position_json"]) == 3]
    cref = rc.ref_of(cfg, cnode)
    if not massive or len(placed) < len(massive):
        checks.append(rc.check_item(
            "CDS-COG", {"en": "Centre of gravity within the CDS box", "fr": "Centre de gravité dans la boîte du CDS"},
            "not_evaluated",
            {"en": f"{len(placed)}/{len(massive)} massive units have a position; place them all to check the CoG.",
             "fr": f"{len(placed)}/{len(massive)} unités massives ont une position ; les placer toutes pour vérifier le CdG."},
            cref, counts={"placed": len(placed), "total": len(massive)}))
    else:
        mtot = sum(float(e["mass_kg"]) * qty(e) for e in placed)
        cog = [sum(float(e["mass_kg"]) * qty(e) * float(e["position_json"][k]) for e in placed) / mtot for k in range(3)]
        off_cm = [abs(cog[k] - env_m[k] / 2) * 100 for k in range(3)]
        ok = all(off_cm[k] <= lim_cm[k] for k in range(3))
        txt = ", ".join(f"{'XYZ'[k]} {off_cm[k]:.1f}/{lim_cm[k]:g}" for k in range(3))
        checks.append(rc.check_item(
            "CDS-COG", {"en": "Centre of gravity within the CDS box", "fr": "Centre de gravité dans la boîte du CDS"},
            "pass" if ok else "fail",
            {"en": f"Offset from the geometric centre (cm, actual/limit): {txt}.",
             "fr": f"Écart au centre géométrique (cm, réel/limite) : {txt.replace('.', ',')}."},
            cref, value=[round(x, 2) for x in off_cm], limit=lim_cm, unit="cm"))

    # ------------------------------------------------------------------ safety features
    rec = cfg["recognition"]
    declared = _declared(elements)
    safety = cfg["safety"]
    sig = [i for i in ifaces if _iface_type(i) == rec.get("interface_type", "electrical_signal")]
    count_prop = rec.get("count_property", "inhibit_count")
    delay_prop = rec.get("delay_property", "delay_min")

    transmitters = _has(elements, rec["transmitter_keywords"], rec.get("transmitter_domains", []))
    deployables = _has(elements, rec["deployable_keywords"], [], deployables=True)
    propulsion = _has(elements, rec["propulsion_keywords"], rec.get("propulsion_domains", []))
    idx = {e["id"]: e for e in elements}

    def with_ancestors(units: list[dict]) -> set[str]:
        """The units and every element above them: a subsystem-level link to the TT&C
        subsystem covers the transceiver inside it."""
        out: set[str] = set()
        for u in units:
            cur, n = u, 0
            while cur is not None and n < 50:
                out.add(cur["id"])
                cur = idx.get(cur.get("parent_id") or "")
                n += 1
        return out

    targets = {"transmitter": with_ancestors(transmitters), "deployable": with_ancestors(deployables),
               "propulsion": with_ancestors(propulsion)}

    def links(kind: str) -> list[dict]:
        spec = rec["links"].get(kind) or {}
        subs = set(spec.get("subtypes", []))
        tgt = spec.get("target")
        return [i for i in sig if _iface_subtype(i) in subs
                and (tgt is None or i.get("to_element_id") in targets.get(tgt, set()))]

    def counted(kind: str) -> int:
        """Inhibits a set of links stands for: each link counts ``inhibit_count`` (default 1).
        Per target unit the counts add up; the design is as good as its worst unit."""
        per_target: dict[str, int] = {}
        for i in links(kind):
            n = (i.get("properties") or {}).get(count_prop)
            n = int(n) if isinstance(n, (int, float)) and not isinstance(n, bool) else 1
            key = i.get("to_element_id") or ""
            per_target[key] = per_target.get(key, 0) + n
        return min(per_target.values()) if per_target else 0

    def link_delay(kind: str) -> float | None:
        vals = [float(d) for i in links(kind)
                for d in [(i.get("properties") or {}).get(delay_prop)]
                if isinstance(d, (int, float)) and not isinstance(d, bool)]
        return min(vals) if vals else None

    def count_check(cid: str, label: dict, kind: str, decl_key: str, node: dict, applies: bool,
                    why: dict) -> None:
        ref = rc.ref_of(cfg, node)
        need = int(node["value"])
        if not applies:
            checks.append(rc.check_item(cid, label, "pass", why, ref, value=0, limit=need, applicable=False))
            return
        n = max(counted(kind), int(declared.get(decl_key) or 0))
        if n == 0 and decl_key not in declared:
            checks.append(rc.check_item(
                cid, label, "warn",
                {"en": f"Not declared: accept the proposed electrical-signal link or set performance.cds.{decl_key} (≥ {need}).",
                 "fr": f"Non déclaré : accepter la liaison de signal électrique proposée ou renseigner performance.cds.{decl_key} (≥ {need})."},
                ref, value=0, limit=need))
        else:
            checks.append(rc.check_item(
                cid, label, "pass" if n >= need else "fail",
                {"en": f"{n} found, {need} required.", "fr": f"{n} trouvé(s), {need} requis."},
                ref, value=n, limit=need))

    count_check("CDS-SW", {"en": "Deployment switch", "fr": "Interrupteur de déploiement"}, "deployment_switch",
                "deployment_switches", safety["min_deployment_switches"], True, {"en": "", "fr": ""})
    rbf_ref = rc.ref_of(cfg, safety["rbf_required"])
    rbf = bool(links("rbf")) or bool(declared.get("rbf"))
    checks.append(rc.check_item(
        "CDS-RBF", {"en": "Remove-before-flight pin", "fr": "Goupille RBF (Remove Before Flight)"},
        "pass" if rbf else "warn",
        {"en": "RBF present." if rbf else "Not declared: an RBF that cuts all power is required.",
         "fr": "Goupille présente." if rbf else "Non déclarée : une goupille coupant toute l’alimentation est requise."},
        rbf_ref))
    count_check("CDS-RF-INH", {"en": "RF inhibits (≥ 3)", "fr": "Inhibitions RF (≥ 3)"}, "rf_inhibit", "rf_inhibits",
                safety["min_rf_inhibits"], bool(transmitters),
                {"en": "No transmitter in the design.", "fr": "Aucun émetteur dans la conception."})
    count_check("CDS-DEP-INH", {"en": "Deployable inhibits (≥ 3)", "fr": "Inhibitions des déployables (≥ 3)"},
                "deployable_inhibit", "deployable_inhibits", safety["min_deployable_inhibits"], bool(deployables),
                {"en": "No deployable in the design.", "fr": "Aucun élément déployable dans la conception."})
    count_check("CDS-PROP-INH", {"en": "Propulsion inhibits (≥ 3)", "fr": "Inhibitions de la propulsion (≥ 3)"},
                "propulsion_inhibit", "propulsion_inhibits", safety["min_propulsion_inhibits"], bool(propulsion),
                {"en": "No propulsion in the design.", "fr": "Aucune propulsion dans la conception."})

    # ------------------------------------------------------------------ timers
    def min_check(cid: str, label: dict, key: str, kind: str, node: dict, applies: bool) -> None:
        ref = rc.ref_of(cfg, node)
        need = float(node["value"])
        if not applies:
            return
        vals = [v for v in (declared.get(key), link_delay(kind)) if v is not None]
        if not vals:
            checks.append(rc.check_item(cid, label, "warn",
                                        {"en": f"Not declared (performance.cds.{key} ≥ {need:g} min).",
                                         "fr": f"Non déclaré (performance.cds.{key} ≥ {need:g} min)."},
                                        ref, limit=need, unit="min"))
        else:
            v = float(min(vals))   # the shortest stated delay is the one that matters
            checks.append(rc.check_item(cid, label, "pass" if v >= need else "fail",
                                        {"en": f"{v:g} min after deployment, {need:g} min required.",
                                         "fr": f"{v:g} min après le déploiement, {need:g} min requises."},
                                        ref, value=v, limit=need, unit="min"))

    min_check("CDS-DEP-T", {"en": "Deployables wait after separation", "fr": "Attente des déployables après séparation"},
              "deploy_delay_min", "deployable_inhibit", safety["min_deploy_delay_min"], bool(deployables))
    min_check("CDS-RF-T", {"en": "No RF transmission before the delay", "fr": "Aucune émission RF avant le délai"},
              "rf_delay_min", "rf_inhibit", safety["min_rf_delay_min"], bool(transmitters))

    # ------------------------------------------------------------------ limits declared per element
    def max_check(cid: str, label: dict, key: str, node: dict, unit: str) -> None:
        ref = rc.ref_of(cfg, node)
        lim = float(node["value"])
        vals = []
        for e in elements:
            d = perf(e).get("cds") or {}
            v = d.get(key) if isinstance(d, dict) else None
            if v is None:
                v = perf(e).get(key)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                vals.append((e, float(v)))
        if not vals:
            checks.append(rc.check_item(cid, label, "not_evaluated",
                                        {"en": f"No element declares {key}.", "fr": f"Aucun élément ne déclare {key}."},
                                        ref, limit=lim, unit=unit))
            return
        bad = [(e, v) for e, v in vals if v > lim]
        checks.append(rc.check_item(
            cid, label, "fail" if bad else "pass",
            {"en": (f"{len(bad)} element(s) above {lim:g} {unit}: " + ", ".join(e.get('name', '') for e, _ in bad[:5]))
                   if bad else f"{len(vals)} element(s) declared, all ≤ {lim:g} {unit}.",
             "fr": (f"{len(bad)} élément(s) au-delà de {lim:g} {unit} : " + ", ".join(e.get('name', '') for e, _ in bad[:5]))
                   if bad else f"{len(vals)} élément(s) déclaré(s), tous ≤ {lim:g} {unit}."},
            ref, value=max(v for _, v in vals), limit=lim, unit=unit,
            element_ids=[e["id"] for e, _ in bad]))

    max_check("CDS-PROTR", {"en": "Protrusion from the rail plane", "fr": "Dépassement du plan des rails"},
              "max_protrusion_mm", cfg["mechanical"]["max_protrusion_mm"], "mm")
    max_check("CDS-TML", {"en": "Outgassing: total mass loss", "fr": "Dégazage : perte de masse totale"},
              "tml_percent", cfg["materials"]["max_tml_percent"], "%")
    max_check("CDS-CVCM", {"en": "Outgassing: collected volatile condensable material",
                           "fr": "Dégazage : matières condensables volatiles recueillies"},
              "cvcm_percent", cfg["materials"]["max_cvcm_percent"], "%")

    # the approved stack layout (services/stack_builder.py): column height, envelope, protrusion,
    # collisions, keep-out, star tracker, PC/104 pinout — CoG stays CDS-COG above
    from .stack_builder import cds_stack_checks
    checks.extend(cds_stack_checks(elements, form_factor))

    return {"applicable": True, "form_factor": form_factor, "checks": checks, "summary": rc.summarise(checks),
            "evidence": {"transmitters": [e["id"] for e in transmitters], "deployables": [e["id"] for e in deployables],
                         "propulsion": [e["id"] for e in propulsion], "declared": declared}}
