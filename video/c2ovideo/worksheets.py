"""Course worksheets and decisions, so videos can point into the workbook.

Ties in a storyboard are ids from the two workbooks and the decision catalogue:

* ``LW-1.4`` or ``LW-1.4/B``      learner workbook (SpaceCDF), part B
* ``WB-5.4-N001`` or ``…/q3``     operations workbook (simulator), question q3
* ``D-1.2-SUPPLIERS``             a decision record in the SpaceCDF logbook

Titles come from the worksheet YAML in both languages, so the end card and
the H5P "your workbook" panel never repeat a translation.
"""

from __future__ import annotations

from functools import lru_cache

import yaml

from .storyboard import REPO, tr

LEARNER = REPO / "design/configs/worksheets/learner_workbook.yaml"
OPS = REPO / "sim/configs/eosat1/worksheets/ops_week3.yaml"
DECISIONS = REPO / "design/configs/worksheets/decision_catalogue.yaml"

GRADED_NEVER = {"WB-5.4-Q"}       # the graded gate quiz: videos never mirror it


class TieError(KeyError):
    pass


@lru_cache(maxsize=1)
def index() -> dict:
    out: dict = {}
    for src, tool in ((LEARNER, "spacecdf"), (OPS, "mcs")):
        if not src.exists():
            continue
        for w in yaml.safe_load(src.read_text(encoding="utf-8")).get("worksheets", []):
            out[w["id"]] = {"kind": "worksheet", "tool": tool, "title": w.get("title", {}),
                            "questions": {q["id"]: q for q in w.get("questions", [])}}
    if DECISIONS.exists():
        for d in yaml.safe_load(DECISIONS.read_text(encoding="utf-8")).get("decisions", []):
            out[d["id"]] = {"kind": "decision", "tool": "spacecdf", "title": d.get("question", {}),
                            "part": d.get("part"), "questions": {}}
    return out


def resolve(tie: str) -> dict:
    base, _, sub = tie.partition("/")
    if base in GRADED_NEVER:
        raise TieError(f"{tie}: the graded quiz is never tied to a video")
    w = index().get(base)
    if not w:
        raise TieError(f"unknown worksheet or decision id {tie!r}")
    q = None
    if sub:
        q = w["questions"].get(sub)
        if q is None:
            raise TieError(f"{tie}: no part/question {sub!r} in {base}")
    return {"id": tie, "base": base, "sub": sub, "worksheet": w, "question": q}


def label(tie: str, lang: str) -> str:
    r = resolve(tie)
    w = r["worksheet"]
    title = tr(w["title"], lang) or ""
    if r["question"]:
        qt = tr(r["question"].get("text") or {}, lang) or ""
        return f"{title} — {qt}" if qt and not qt.startswith(title) else (qt or title)
    if w["kind"] == "decision":
        pre = "Decision record: " if lang == "en" else "Fiche de décision : "
        return pre + title
    return title


def end_card_ties(sb, lang: str) -> list[tuple[str, str]]:
    ties = []
    for t in (sb.ties.get("worksheets") or []) + (sb.ties.get("decisions") or []):
        ties.append((t, label(t, lang)))
    return ties[:6]
