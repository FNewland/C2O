"""SpaceCDF — review-gate checks computed from the model (replaces manual/AI review prep).

Two things, both deterministic:

1. **Criteria of ``configs/gate_exit_criteria.yaml`` that are ``manual`` or ``hybrid``**
   get a ``computed`` block when the model can answer them (e.g. SRR-EC-08 TRL from
   the KB parts). The YAML status is left as it is; the reviewer still signs off,
   but sees the computed evidence. (PDR-EC-02 interfaces belongs to the interface
   readiness service.)
2. **Artefact checks per gate** following ECSS-M-ST-10C Rev.1 review objectives
   (SRR during phase B, 4.4.3.4.3; PDR end of phase B, 4.4.3.4.4: product tree,
   specification tree and verification plan released), plus the rule engines:
   requirement quality, verification methods, margin policy, CDS checks, FMECA.
   Which engine feeds which gate, and the pass thresholds, are C2O defaults.
"""
from __future__ import annotations

from typing import Any

from . import rule_config as rc
from .cds_checks import evaluate_cds
from .fmeca_library import build_skeleton
from .margin_policy import evaluate_margins
from .requirement_quality import check_requirements
from .rule_inputs import children_map, kb_component, space_hardware
from .verification_defaults import suggest_all

_CFG = {"sources": {
    "ecss_m_10": {"kind": "standard", "short": "ECSS-M-ST-10C Rev.1",
                  "title": "ECSS-M-ST-10C Rev.1 Project planning and implementation", "verified": True},
    "ecss_10_02": {"kind": "standard", "short": "ECSS-E-ST-10-02C Rev.1", "title": "ECSS-E-ST-10-02C Rev.1 Verification",
                   "verified": True},
    "c2o_default": {"kind": "c2o_default", "title": "C2O default", "verified": False},
}}

#: Requirement-quality pass threshold for SRR/PDR (share of requirements with no error). C2O default.
QUALITY_PASS_SHARE = {"SRR": 0.8, "PDR": 1.0, "CDR": 1.0}
#: Minimum TRL of selected parts at SRR (gate_exit_criteria SRR-EC-08 evidence text).
SRR_MIN_TRL = 4

GATE_CHECKS: dict[str, tuple[str, ...]] = {
    # Phase 0 has no product tree yet (gate_profiles.yaml products: first draft at PRR).
    "MDR": (),
    "PRR": ("GC-PRODUCT-TREE", "GC-MARGINS"),
    "SRR": ("GC-SPEC-TREE", "GC-REQ-QUALITY", "GC-VER-METHODS", "GC-MARGINS"),
    "PDR": ("GC-PRODUCT-TREE", "GC-SPEC-TREE", "GC-REQ-QUALITY", "GC-VER-METHODS", "GC-VER-RISK",
            "GC-MARGINS", "GC-CDS", "GC-STACK", "GC-FMECA"),
    # CDR: the PDR artefacts again (now at the CDR margin step); the CDR products themselves
    # (TM/TC database, FDIR, AOCS modes, operations) are exit criteria CDR-EC-03 … 09.
    "CDR": ("GC-PRODUCT-TREE", "GC-SPEC-TREE", "GC-REQ-QUALITY", "GC-VER-METHODS", "GC-VER-RISK",
            "GC-MARGINS", "GC-CDS", "GC-STACK", "GC-FMECA"),
}


def _ref(source: str, clause: str | None = None) -> dict[str, Any]:
    return rc.ref_of(_CFG, {"source": source, "clause": clause})


def _trl_of(e: dict) -> int | None:
    if e.get("trl") is not None:
        return int(e["trl"])
    kb = kb_component(e) or {}
    return int(kb["trl"]) if kb.get("trl") is not None else None


def computed_for_criterion(cid: str, ctx: dict[str, Any]) -> dict[str, Any] | None:
    """Computed evidence for a manual/hybrid gate criterion, or None."""
    if cid == "SRR-EC-08":
        comps = [e for e in space_hardware(ctx["elements"]) if e.get("element_type") == "component"]
        rated = [(e, _trl_of(e)) for e in comps]
        known = [(e, t) for e, t in rated if t is not None]
        if not known:
            return {"status": "not_evaluated", "detail": {"en": "No component has a TRL yet.",
                                                          "fr": "Aucun composant n’a encore de TRL."},
                    **_ref("c2o_default")}
        low = [e.get("name", "") for e, t in known if t < SRR_MIN_TRL]
        return {"status": "fail" if low else "pass",
                "detail": {"en": f"{len(known)}/{len(comps)} components rated; below TRL {SRR_MIN_TRL}: "
                                 + (", ".join(low[:6]) if low else "none") + ".",
                           "fr": f"{len(known)}/{len(comps)} composants évalués ; sous le TRL {SRR_MIN_TRL} : "
                                 + (", ".join(low[:6]) if low else "aucun") + "."},
                "standard_ref": "gate_exit_criteria.yaml SRR-EC-08 (C2O default threshold)", "c2o_default": True}
    return None


def _check(cid: str, gate: str, ctx: dict[str, Any], cache: dict[str, Any]) -> dict[str, Any]:
    els, reqs = ctx["elements"], ctx["requirements"]
    if cid == "GC-PRODUCT-TREE":
        hw = space_hardware(els)
        kids = children_map(hw)
        systems = [e for e in hw if e.get("element_type") == "system"]
        subs = [e for e in hw if e.get("element_type") == "subsystem"]
        with_comp = [s for s in subs if any(c.get("element_type") == "component" for c in kids.get(s["id"], []))]
        need_comp = gate in ("PDR", "CDR")
        # levels (services/product_tree.py): no subsystem or unit directly under a segment
        from .product_tree import misplaced
        hw_ids = {e["id"] for e in hw}
        wrong = [e for e in misplaced(els) if e["id"] in hw_ids]
        ok = bool(systems) and bool(subs) and not wrong and (len(with_comp) == len(subs) if need_comp else True)
        wtxt_en = f" {len(wrong)} at the wrong level (e.g. {wrong[0].get('name')}: a subsystem needs a spacecraft above it)." if wrong else ""
        wtxt_fr = f" {len(wrong)} au mauvais niveau (p. ex. {wrong[0].get('name')} : un sous-système a besoin d’un satellite au-dessus)." if wrong else ""
        return rc.check_item(cid, {"en": "Product tree", "fr": "Arbre produit"}, "pass" if ok else "fail",
                             {"en": f"{len(systems)} system(s), {len(subs)} subsystem(s), {len(with_comp)} with components.{wtxt_en}",
                              "fr": f"{len(systems)} système(s), {len(subs)} sous-système(s), dont {len(with_comp)} avec composants.{wtxt_fr}"},
                             _ref("ecss_m_10", "4.4.3.4.4" if gate == "PDR" else ("4.4.3.4.5 (to verify)" if gate == "CDR" else None)),
                             counts={"systems": len(systems), "subsystems": len(subs), "with_components": len(with_comp),
                                     "misplaced": len(wrong)})
    if cid == "GC-SPEC-TREE":
        levels = {r.get("level") for r in reqs}
        below = [r for r in reqs if r.get("level") in ("subsystem",)]
        orphans = [r for r in below if not (r.get("parent_id") or r.get("derived_from_requirement_id"))]
        has_sys = "system" in levels
        need_sub = gate in ("PDR", "CDR")
        ok = has_sys and (bool(below) if need_sub else True) and not orphans
        return rc.check_item(cid, {"en": "Specification tree", "fr": "Arbre de spécifications"}, "pass" if ok else "fail",
                             {"en": f"Levels {sorted(x for x in levels if x)}; {len(orphans)} subsystem requirement(s) without a parent.",
                              "fr": f"Niveaux {sorted(x for x in levels if x)} ; {len(orphans)} exigence(s) de sous-système sans parent."},
                             _ref("ecss_m_10", "4.4.3.4.4"), counts={"orphans": len(orphans), "requirements": len(reqs)})
    if cid == "GC-REQ-QUALITY":
        q = cache.setdefault("quality", check_requirements(reqs))
        total = q["summary"]["total"]
        clean = total - q["summary"]["fail"]
        share = clean / total if total else 0.0
        need = QUALITY_PASS_SHARE.get(gate, 0.8)
        status = "not_evaluated" if not total else ("pass" if share >= need else "fail")
        return rc.check_item(cid, {"en": "Requirement quality (EARS / INCOSE)", "fr": "Qualité des exigences (EARS / INCOSE)"},
                             status,
                             {"en": f"{clean}/{total} requirements without a rewrite-level finding (need {need:.0%}).",
                              "fr": f"{clean}/{total} exigences sans constat bloquant (seuil {need:.0%})."},
                             _ref("c2o_default", "threshold"), value=round(share, 3), limit=need)
    if cid in ("GC-VER-METHODS", "GC-VER-RISK"):
        v = cache.setdefault("verification", suggest_all(reqs))
        total = v["summary"]["total"]
        if cid == "GC-VER-METHODS":
            missing = v["summary"]["missing_method"]
            return rc.check_item(cid, {"en": "Verification method for every requirement",
                                       "fr": "Méthode de vérification pour chaque exigence"},
                                 "not_evaluated" if not total else ("pass" if not missing else "fail"),
                                 {"en": f"{total - missing}/{total} requirements have a method (defaults available for the rest).",
                                  "fr": f"{total - missing}/{total} exigences ont une méthode (valeurs par défaut disponibles pour les autres)."},
                                 _ref("ecss_10_02", "5.2.8.2 (VCD)"), counts={"missing": missing, "total": total})
        n = v["summary"]["needs_risk_assessment"]
        return rc.check_item(cid, {"en": "Risk assessment for A/R-only verification",
                                   "fr": "Évaluation des risques pour les vérifications par A ou R seulement"},
                             "pass" if not n else "warn",
                             {"en": f"{n} requirement(s) verified only by analysis or review of design need a risk assessment.",
                              "fr": f"{n} exigence(s) vérifiée(s) uniquement par analyse ou revue de conception exigent une évaluation des risques."},
                             _ref("ecss_10_02", "5.2.2.1"), count=n)
    if cid == "GC-MARGINS":
        m = cache.setdefault("margins", evaluate_margins(els, ctx["params"], mass_limit_kg=ctx.get("mass_limit_kg"),
                                                         gate=ctx.get("margin_gate") or gate.lower()))
        s = m["summary"]
        status = "fail" if s["fail"] else ("not_evaluated" if s["pass"] == 0 else ("warn" if s["warn"] else "pass"))
        return rc.check_item(cid, {"en": "Budgets close with the margin policy", "fr": "Bilans bouclés avec la politique de marges"},
                             status, {"en": f"{s['pass']} pass, {s['warn']} caution, {s['fail']} fail, {s['not_evaluated']} not evaluated.",
                                      "fr": f"{s['pass']} conformes, {s['warn']} à surveiller, {s['fail']} non conformes, {s['not_evaluated']} non évalués."},
                             rc.ref_of(rc.load("margin_policy"), {"source": "esa_margin_1_3"}), counts=s,
                             system_margin=m.get("system_margin"))
    if cid == "GC-CDS":
        c = cache.setdefault("cds", evaluate_cds(els, ctx["interfaces"], ctx["params"], ctx.get("form_factor")))
        if not c["applicable"]:
            return rc.check_item(cid, {"en": "CubeSat Design Specification", "fr": "Spécification CubeSat (CDS)"},
                                 "pass", c["reason"], rc.ref_of(rc.load("cds_rules"), {"source": "cds_14_1"}), applicable=False)
        s = c["summary"]
        status = "fail" if s["fail"] else ("warn" if s["warn"] else "pass")
        return rc.check_item(cid, {"en": "CubeSat Design Specification", "fr": "Spécification CubeSat (CDS)"}, status,
                             {"en": f"{s['pass']} pass, {s['warn']} not declared, {s['fail']} fail.",
                              "fr": f"{s['pass']} conformes, {s['warn']} non déclarés, {s['fail']} non conformes."},
                             rc.ref_of(rc.load("cds_rules"), {"source": "cds_14_1"}), counts=s)
    if cid == "GC-STACK":
        from .stack_builder import stack_gate_check
        return stack_gate_check(els, ctx.get("form_factor"))
    if cid == "GC-FMECA":
        f = cache.setdefault("fmeca", build_skeleton(els, ctx["interfaces"]))
        sp = f["summary"]["single_points"]
        return rc.check_item(cid, {"en": "FMECA: single-point failures", "fr": "AMDEC : points de défaillance uniques"},
                             "not_evaluated" if not f["rows"] else ("warn" if sp else "pass"),
                             {"en": f"{f['summary']['modes']} failure modes, {sp} single point(s), max RPN {f['summary']['max_rpn']}.",
                              "fr": f"{f['summary']['modes']} modes de défaillance, {sp} point(s) unique(s), RPN max {f['summary']['max_rpn']}."},
                             rc.ref_of(rc.load("failure_modes"), {"source": "c2o_default"}), counts=f["summary"])
    raise KeyError(cid)


def evaluate_gate_checks(gate: str, ctx: dict[str, Any], criteria: list[dict] | None = None) -> dict[str, Any]:
    """``ctx``: elements, interfaces, requirements, params, form_factor, mass_limit_kg
    (optional margin_gate: the margin-ladder step; default the gate itself)."""
    g = gate.upper()
    g = {"MCR": "MDR"}.get(g, g)   # MCR = the old name of MDR (ruling 3)
    cache: dict[str, Any] = {}
    checks = [_check(cid, g, ctx, cache) for cid in GATE_CHECKS.get(g, ())]
    computed = []
    for c in criteria or []:
        if c.get("status") in ("manual", "not_evaluated") or c.get("id") in ("SRR-EC-08",):
            comp = computed_for_criterion(c.get("id", ""), ctx)
            if comp:
                computed.append({"id": c["id"], **comp})
    return {"gate": g, "checks": checks, "computed_criteria": computed, "summary": rc.summarise(checks)}
