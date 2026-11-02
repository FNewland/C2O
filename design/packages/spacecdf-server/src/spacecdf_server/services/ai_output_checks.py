"""SpaceCDF — rule checks applied to every AI output before it is shown.

AI is only a drafting aid (docs/RULES_AND_AI.md). Whatever it writes goes through
the same deterministic checks as a student's own text:

* every requirement it proposes (the ``requirements`` JSON list, or any sentence
  containing "shall"/"doit" in prose) → ``requirement_quality.check_text``
  (EARS pattern + INCOSE subset); statements with an error-level finding are
  marked ``needs_revision``;
* prose (critique, narrative) → open items (TBD/TBC) and any embedded shall
  statements are flagged the same way.

The result carries ``rule_checks`` and ``validated: true`` so a UI can show the
draft *with* its findings, never as an unchecked answer.
"""
from __future__ import annotations

import re
from typing import Any

from .requirement_quality import check_text

_SENTENCE = re.compile(r"(?<=[.!?])\s+|\n+")
_MODAL = re.compile(r"\b(shall|doi(?:t|vent))\b", re.I)
_BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)]|\[[^\]]*\])\s*")


def extract_statements(text: str) -> list[str]:
    """Sentences / lines that state an obligation (contain shall / doit)."""
    out = []
    for part in _SENTENCE.split(text or ""):
        s = _BULLET.sub("", part).strip().strip("*").strip()
        if s and _MODAL.search(s) and len(s) < 600:
            out.append(s)
    return out


def check_ai_output(capability: str, result: dict[str, Any], language: str | None = None) -> dict[str, Any]:
    """Return ``result`` with ``rule_checks`` attached (never removes the content)."""
    checked: list[dict[str, Any]] = []
    reqs = result.get("requirements")
    if isinstance(reqs, list) and reqs:
        for i, r in enumerate(reqs):
            text = (r.get("text") or r.get("statement") or "") if isinstance(r, dict) else str(r)
            q = check_text(text, language)
            q["index"] = i
            q["needs_revision"] = q["counts"]["error"] > 0
            if isinstance(r, dict):
                r["quality"] = {"status": q["status"], "ears": q["ears"], "findings": q["findings"]}
            checked.append(q)
    else:
        for i, s in enumerate(extract_statements(result.get("content", ""))):
            q = check_text(s, language)
            q["index"] = i
            q["needs_revision"] = q["counts"]["error"] > 0
            checked.append(q)
    tbd = len(re.findall(r"\b(TBD|TBC|TBR)\b", result.get("content", "") or ""))
    result["rule_checks"] = {
        "capability": capability,
        "statements": checked,
        "summary": {"statements": len(checked),
                    "needs_revision": sum(1 for q in checked if q["needs_revision"]),
                    "pass": sum(1 for q in checked if q["status"] == "pass"),
                    "open_items": tbd},
        "note": {"en": "AI draft checked by SpaceCDF rules (EARS / INCOSE subset). Review before use.",
                 "fr": "Brouillon IA vérifié par les règles de SpaceCDF (EARS / sous-ensemble INCOSE). À relire avant usage."},
    }
    result["validated"] = True
    return result
