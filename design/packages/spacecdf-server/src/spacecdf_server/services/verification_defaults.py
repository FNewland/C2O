"""SpaceCDF — default verification method per requirement (ECSS-E-ST-10-02C).

ECSS-E-ST-10-02C Rev.1 defines four verification methods: Test (incl.
demonstration), Analysis (incl. similarity), Review of design and Inspection
(4.2.2, 5.2.2.2–5.2.2.5). It also requires a risk assessment for requirements
verified only by analysis or review of design (5.2.2.1).

Which method suits which requirement *type* is a C2O default, configured in
``configs/requirement_rules.yaml`` (section ``verification``): a requirement is
classified by its threshold parameter (``mass.*`` → budget → Analysis) and by
keywords in its text, first match wins. The designer's own choice always wins:
``suggest`` reports the default next to the current method and ``apply`` only
fills empty methods.
"""
from __future__ import annotations

import re
from typing import Any

from . import rule_config as rc

CONFIG = "requirement_rules"
_ALIASES = {"D": "T"}   # demonstration is part of Test in ECSS-E-ST-10-02C


def classify(req: dict[str, Any]) -> dict[str, Any]:
    cfg = rc.load(CONFIG)["verification"]
    text = (req.get("text") or "").lower()
    path = (req.get("threshold_param_path") or "").lower()
    # The threshold parameter is the stronger evidence, so it is tried first for every type.
    for t in cfg["types"]:
        if path and any(path.startswith(p) for p in t.get("param_prefixes", [])):
            return {**t, "matched": path}
    for t in cfg["types"]:
        for kw in t.get("keywords", []):
            # word-start match: "ITU" must not match "attitude"; "licen" matches "licence"
            if re.search(r"(?<!\w)" + re.escape(kw.lower()), text):
                return {**t, "matched": kw}
    return {"id": "unclassified", **cfg["fallback"], "matched": None}


def suggest(req: dict[str, Any]) -> dict[str, Any]:
    full = rc.load(CONFIG)
    cfg = full["verification"]
    t = classify(req)
    method = t["method"]
    current = (req.get("verification_method") or "").strip().upper() or None
    current_n = _ALIASES.get(current, current) if current else None
    risk_methods = set(cfg.get("risk_assessment_methods", []))
    effective = current_n or method
    method_ref = rc.ref_of(full, {"source": cfg.get("source"), "clause": "4.2.2"})
    mapping_ref = rc.ref_of(full, t)
    return {
        "requirement_id": req.get("id"), "code": req.get("code", ""),
        "type": t["id"], "type_label": t.get("label"), "matched": t.get("matched"),
        "default_method": method, "default_label": cfg["methods"][method],
        "current_method": current, "differs": bool(current_n and current_n != method),
        "needs_risk_assessment": effective in risk_methods,
        "risk_note": ({"en": "Verified only by analysis or review of design: a risk assessment is required (ECSS-E-ST-10-02C 5.2.2.1).",
                       "fr": "Vérifiée uniquement par analyse ou revue de conception : une évaluation des risques est requise (ECSS-E-ST-10-02C 5.2.2.1)."}
                      if effective in risk_methods else None),
        "method_standard_ref": method_ref["standard_ref"],
        "mapping_standard_ref": mapping_ref["standard_ref"], "mapping_c2o_default": mapping_ref["c2o_default"],
    }


def suggest_all(reqs: list[dict]) -> dict[str, Any]:
    rows = [suggest(r) for r in reqs if r.get("status") != "retired"]
    return {"rows": rows, "summary": {
        "total": len(rows),
        "missing_method": sum(1 for r in rows if not r["current_method"]),
        "differs_from_default": sum(1 for r in rows if r["differs"]),
        "needs_risk_assessment": sum(1 for r in rows if r["needs_risk_assessment"]),
        "by_default_method": {m: sum(1 for r in rows if r["default_method"] == m) for m in ("T", "A", "R", "I")},
    }}
