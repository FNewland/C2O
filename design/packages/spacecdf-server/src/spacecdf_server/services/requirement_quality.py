"""SpaceCDF — requirement quality checks (EARS pattern + pinned INCOSE rule subset).

Lexical, deterministic checks driven by ``configs/requirement_rules.yaml``:

* EARS pattern detection (Mavin et al., RE'09): ubiquitous, state-driven,
  event-driven, optional, unwanted behaviour, complex. English keywords follow
  EARS; the French keywords are a C2O adaptation.
* A pinned INCOSE GtWR subset (R1 modal verb, R2 passive voice, R6 units, R7 vague
  terms, R8 escape clauses, R9 open-ended clauses, R17 "/", R18 one "shall",
  R19 combinators, R20 purpose phrases, R24 pronouns, R26 absolutes, R33
  tolerances) plus the C2O "open item (TBD/TBC)" check.

These checks replace the AI "requirement writing" critique: the AI may still
*rephrase* a requirement (optional), but every text — typed by a student or
proposed by the AI — goes through ``check_text`` before it is shown as good.
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from . import rule_config as rc

CONFIG = "requirement_rules"

_EN_MODAL = re.compile(r"\bshall\b", re.I)
_FR_MODAL = re.compile(r"\bdoi(?:t|vent)\b", re.I)
_NUMBER = re.compile(r"(?<![\w.\-/])([-+]?\d+(?:[.,]\d+)?(?:\s?[x×]\s?10\^?-?\d+)?)")


def detect_language(text: str, hint: str | None = None) -> str:
    if _EN_MODAL.search(text):
        return "en"
    if _FR_MODAL.search(text):
        return "fr"
    return "fr" if (hint or "").lower().startswith("fr") else "en"


@lru_cache(maxsize=4)
def _compiled(_token: int) -> dict[str, Any]:
    cfg = rc.load(CONFIG)
    ears = [(p["id"], p["label"], re.compile(p["en"], re.I), re.compile(p["fr"], re.I))
            for p in cfg["ears"]["patterns"]]
    units = sorted(cfg.get("units", []), key=len, reverse=True)
    unit_re = re.compile(r"^\s?(" + "|".join(re.escape(u) for u in units) + r")(?![A-Za-zÀ-ÿ])")
    return {"cfg": cfg, "ears": ears, "unit_re": unit_re}


def _rules() -> dict[str, Any]:
    # Cache key tied to the rule_config cache: reload() there clears _raw, so tests
    # that swap configs call requirement_quality.reload() as well.
    return _compiled(0)


def reload() -> None:
    _compiled.cache_clear()


def _word_hits(text: str, words: list[str]) -> list[str]:
    hits = []
    low = text.lower()
    for w in words:
        wl = w.lower()
        if not wl:
            continue
        if re.match(r"^[\w\-’']+( [\w\-’']+)*$", wl):
            if re.search(r"(?<![\w\-])" + re.escape(wl) + r"(?![\w\-])", low):
                hits.append(w)
        elif wl in low:
            hits.append(w)
    return hits


def detect_ears(text: str, lang: str) -> dict[str, Any] | None:
    t = text.strip()
    for pid, label, en_re, fr_re in _rules()["ears"]:
        if (en_re if lang == "en" else fr_re).search(t):
            return {"id": pid, "label": label}
    return None


def _numbers_without_unit(text: str) -> list[str]:
    unit_re = _rules()["unit_re"]
    out = []
    for m in _NUMBER.finditer(text):
        num = m.group(1)
        after = text[m.end():]
        if unit_re.match(after):
            continue
        # ordinal-ish or list markers ("phase 2", "R18", "3 inhibits" counts are fine)
        nxt = re.match(r"\s?([A-Za-zÀ-ÿ]+)", after)
        if nxt and nxt.group(1).lower() in {
            "inhibits", "inhibit", "inhibitions", "independent", "indépendantes", "times", "fois", "axes",
            "axis", "redundant", "redondants", "units", "unités", "elements", "éléments", "of", "sur", "out", "parmi",
            "satellites", "spacecraft", "stations", "passes", "passages", "wheels", "roues", "switches",
            "interrupteurs", "sigma", "failures", "défaillances", "channels", "canaux", "modes"}:
            continue
        out.append(num)
    return out


def _has_bound(text: str, lang: str) -> bool:
    words = _rules()["cfg"]["bounds"].get(lang, [])
    return bool(_word_hits(text, words))


def check_text(text: str, language: str | None = None) -> dict[str, Any]:
    """Check one requirement text. Returns pattern, findings and a score.

    ``findings``: [{id, rule, severity, message:{en,fr}, term?, standard_ref, c2o_default}]
    ``status``: fail (any error) | warn (any warning) | pass.
    """
    cfg = _rules()["cfg"]
    text = (text or "").strip()
    lang = detect_language(text, language)
    findings: list[dict[str, Any]] = []

    def add(c: dict, term: str | None = None) -> None:
        ref = rc.ref_of(cfg, c)
        msg = {k: v.replace("{term}", term or "") for k, v in c["message"].items()}
        findings.append({"id": c["id"], "rule": c.get("rule", ""), "severity": c["severity"], "message": msg,
                         "term": term, "standard_ref": ref["standard_ref"], "c2o_default": ref["c2o_default"]})

    modal = _EN_MODAL if lang == "en" else _FR_MODAL
    n_modal = len(modal.findall(text))
    for c in cfg["checks"]:
        kind = c["kind"]
        if kind == "no_modal":
            if n_modal == 0:
                add(c)
        elif kind == "multi_modal":
            if n_modal > 1:
                add(c)
        elif kind == "words":
            for term in _word_hits(text, c["words"].get(lang, [])):
                add(c, term)
        elif kind == "regex":
            pat = c.get(f"pattern_{lang}") or c.get("pattern")
            if not pat:
                continue
            flags = 0 if c.get("case_sensitive") else re.I
            m = re.search(pat, text, flags)
            if m:
                add(c, m.group(0))
        elif kind == "number_without_unit":
            for num in _numbers_without_unit(text):
                add(c, num)
        elif kind == "number_without_bound":
            # only measured quantities (a number followed by a unit) need a bound
            unit_re = _rules()["unit_re"]
            measured = any(unit_re.match(text[m.end():]) for m in _NUMBER.finditer(text))
            if measured and not _has_bound(text, lang):
                add(c)

    ears = detect_ears(text, lang)
    errors = sum(1 for f in findings if f["severity"] == "error")
    warnings = sum(1 for f in findings if f["severity"] == "warning")
    status = "fail" if errors else ("warn" if warnings or ears is None else "pass")
    score = max(0, 100 - 25 * errors - 10 * warnings - 3 * (len(findings) - errors - warnings)
                - (10 if ears is None else 0))
    return {"text": text, "language": lang, "ears": ears, "findings": findings,
            "status": status, "score": score, "counts": {"error": errors, "warning": warnings,
                                                         "info": len(findings) - errors - warnings}}


def check_requirements(reqs: list[dict]) -> dict[str, Any]:
    """Check every requirement dict (``text`` field); returns rows and a summary."""
    rows = []
    for r in reqs:
        res = check_text(r.get("text", ""), r.get("language"))
        rows.append({"requirement_id": r.get("id"), "code": r.get("code", ""), **res})
    by_status = {"pass": 0, "warn": 0, "fail": 0}
    for row in rows:
        by_status[row["status"]] += 1
    rule_counts: dict[str, int] = {}
    for row in rows:
        for f in row["findings"]:
            rule_counts[f["id"]] = rule_counts.get(f["id"], 0) + 1
    ears_counts: dict[str, int] = {}
    for row in rows:
        k = row["ears"]["id"] if row["ears"] else "none"
        ears_counts[k] = ears_counts.get(k, 0) + 1
    return {"rows": rows, "summary": {"total": len(rows), **by_status, "by_rule": rule_counts,
                                      "by_ears_pattern": ears_counts}}


def rule_catalogue() -> list[dict[str, Any]]:
    """The checks as configured (for the UI legend and the docs)."""
    cfg = _rules()["cfg"]
    out = []
    for c in cfg["checks"]:
        ref = rc.ref_of(cfg, c)
        out.append({"id": c["id"], "rule": c.get("rule", ""), "severity": c["severity"], "kind": c["kind"],
                    "message": c["message"], "standard_ref": ref["standard_ref"], "c2o_default": ref["c2o_default"]})
    return out
