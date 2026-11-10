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


_TIME = re.compile(r"\b\d{1,2}:\d{2}\b")
_ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_ONE_IN = re.compile(r"\b1 in \d{1,3}(?:[ \u202f\u00a0]\d{3})*\b")
_RATIO = re.compile(r"\b\d+(?:\.\d+)?:\d+(?:\.\d+)?\b")
_PAREN_ID = re.compile(r"\(\s*\d+(?:[.,]\d+)*\s*\)")


def _masked_spans(text: str) -> list[tuple[int, int]]:
    """Spans whose numbers are never measured quantities: times, ISO dates, "1 in 10 000",
    ratios "1.3:1", parenthesised identifiers "(255,223)"."""
    spans = []
    for rx in (_TIME, _ISO_DATE, _ONE_IN, _RATIO, _PAREN_ID):
        spans += [m.span() for m in rx.finditer(text)]
    return spans


def _numbers_without_unit(text: str) -> list[str]:
    """Numbers that look like measured quantities but carry no unit (INCOSE R6).

    Not flagged (W2.06; word lists in ``number_skips`` of requirement_rules.yaml): a number
    followed by a unit or by a noun (a count: "40 scene pairs"); the first number of a range,
    a list or a tolerance ("449.75-450.25 MHz", "0 to 25 degC", "1.2, 9.6 and 38.4 kbps",
    "865 ±10 nm"); times, ISO dates, day-month dates and years; "1 in 10 000"; ratios;
    scientific notation; dimensions "100 x 100 x 340.5 mm"; compounds "30-day"; identifiers
    after a word such as "rev", "No.", "CCSDS", "Appendix", "services"; fractions below 1; and
    numbers in a dimensionless context (SNR, ratio, probability, factor, margin …)."""
    rules = _rules()
    unit_re = rules["unit_re"]
    skips = rules["cfg"].get("number_skips") or {}
    id_words = {w.lower() for w in skips.get("id_words") or []}
    dimless = [w.lower() for w in skips.get("dimensionless_words") or []]
    function_words = {w.lower() for w in skips.get("function_words") or []}
    months = {w.lower() for w in skips.get("months") or []}
    masked = _masked_spans(text)
    low = text.lower()
    out = []
    for m in _NUMBER.finditer(text):
        num = m.group(1)
        if any(a <= m.start() < b for a, b in masked):
            continue
        after = text[m.end():]
        before = text[:m.start()]
        if unit_re.match(after):
            continue
        # range, list or tolerance: another number follows ("-", "–", "to", "and", "or", ",", "±")
        if re.match(r"\s?(?:[-–]|to\b|and\b|or\b|et\b|à\b|,|±|\+/-)\s?[-+±]?\d", after):
            continue
        # scientific notation, dimensions, compounds and fractions written with "/"
        if re.match(r"[eE][-+]?\d", after) or re.match(r"\s?[x×]\s?\d", after) \
                or re.match(r"-[A-Za-zÀ-ÿ]|-\s", after) or re.match(r"/\d", after):
            continue
        prev = re.search(r"([A-Za-zÀ-ÿ§][\w.\-§]*)\s*$", before)
        prev_word = prev.group(1).lower() if prev else ""
        if prev_word.rstrip(".") in id_words or prev_word in id_words:
            continue
        if prev and prev.group(1)[:1].isupper() and prev.group(1).lower() not in ("at", "the", "in", "on"):
            # an identifier after a proper noun or acronym ("Landsat 8", "Appendix 3", "UN 38.3")
            if not re.search(r"(?i)\b(at least|at most|within|below|above|between|than|of)\s*$", before):
                continue
        nxt = re.match(r"\s?([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\-]*)", after)
        if nxt:
            word = nxt.group(1).lower()
            if word in months or prev_word in months:
                continue                       # "31 March", "1 April", "May 2027"
            if word not in function_words:
                continue                       # a count: the noun is what is counted
        elif prev_word in months:
            continue
        try:
            val = float(num.replace(",", ".").replace("+", ""))
        except ValueError:
            val = None
        if val is not None and 0 < abs(val) < 1:
            continue                           # a fraction or probability
        clause = low[max(0, low.rfind(",", 0, m.start()), low.rfind(";", 0, m.start())):m.start()]
        if any(re.search(r"(?<![\w-])" + re.escape(w) + r"(?![\w-])", clause) for w in dimless):
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
