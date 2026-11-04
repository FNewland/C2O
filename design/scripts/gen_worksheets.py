#!/usr/bin/env python3
"""Generate the in-tool worksheets from the course workbook (LOGBOOK_SPEC.md §4).

    python3 scripts/gen_worksheets.py            # (re)write configs/worksheets/learner_workbook.yaml
    python3 scripts/gen_worksheets.py --check    # exit 1 if the committed file is stale

Sources (never hand-copied, so the logbook's worksheet text cannot drift from
the printed workbook):

    docs/course/learner_workbook_expanded.md       English
    docs/course/fr/learner_workbook_expanded.md    its French twin (same heading structure)
    configs/worksheets/worksheet_map.yaml          hand-maintained: phase and where SpaceCDF
                                                   offers each worksheet (steps, tabs, levels, gates)
    configs/worksheets/where_map.yaml              hand-maintained: per question, where in SpaceCDF it
                                                   is answered (target ids), textbook sections and
                                                   external links (Nov 2026 worksheet/screen audit)

Parsing rules:
    "# Worksheet N.M: Title"          one worksheet, id LW-N.M (LW = learner workbook; the
                                      ops week-3 workbook uses WB-…, so the ids never clash)
    "## Part X: …"                    one question, id X
    "## Notes & Reflections"          question "notes";  "## Decision Justification" → "justification"
    other "## …"                      one question, id = slug of the English heading
    "## …" whose "### …" children     one question per child (5.3 "Simulation Debrief")
      all end in "?" or ":"
    "## Quick Reference…", "## Key Equations…", "## Worked Example…" are reading, not questions.
Each question carries its heading, the first prose paragraph(s) as the prompt, and the bold
sub-prompts / numbered sub-questions as points. Fill-in lines, tables and hints are left out.
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent          # design/
SRC_EN = ROOT / "docs" / "course" / "learner_workbook_expanded.md"
SRC_FR = ROOT / "docs" / "course" / "fr" / "learner_workbook_expanded.md"
MAP = ROOT / "configs" / "worksheets" / "worksheet_map.yaml"
WHERE = ROOT / "configs" / "worksheets" / "where_map.yaml"
OUT = ROOT / "configs" / "worksheets" / "learner_workbook.yaml"

HEADER = """\
# GENERATED FILE — DO NOT EDIT BY HAND.
# Source: docs/course/learner_workbook_expanded.md (+ docs/course/fr/…) and
# configs/worksheets/worksheet_map.yaml and where_map.yaml. Regenerate with:
#     python3 scripts/gen_worksheets.py
# tests/test_logbook/test_worksheets_generated.py fails when this file is stale.
"""

WS_RE = {"en": re.compile(r"^# Worksheet (\d+\.\d+)\s*:\s*(.+)$"),
         "fr": re.compile(r"^# Fiche (\d+\.\d+)\s*:\s*(.+)$")}
PART_RE = {"en": re.compile(r"^Part ([A-Z])\s*:\s*(.+)$"),
           "fr": re.compile(r"^Partie ([A-Z])\s*:\s*(.+)$")}
READING_RE = {"en": re.compile(r"^(Quick Reference|Key Equations|Worked Example)", re.I),
              "fr": re.compile(r"^(Aide-mémoire|Rappel des équations|Exemple résolu)", re.I)}
FILL_RE = re.compile(r"^[\s_|:.\-]*$")
SPECIAL_IDS = {"Notes & Reflections": "notes", "Decision Justification": "justification"}
PROMPT_MAX = 700
POINTS_MAX = 10


# ─── Markdown → blocks ────────────────────────────────────────────────────

def _strip_code(lines: list[str]) -> list[str]:
    out, fence = [], False
    for ln in lines:
        if ln.lstrip().startswith("```"):
            fence = not fence
            out.append("")
            continue
        out.append("" if fence else ln)
    return out


def _clean(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\s*_{3,}.*$", "", text)          # "Label: ______" → "Label:"
    text = text.replace(" -- ", " – ").replace("--", "–")
    return re.sub(r"\s+", " ", text).strip()


def _heading_text(text: str) -> str:
    return _clean(text)


def parse(path: Path, lang: str) -> list[dict]:
    """Worksheets with their sections: [{num, title, sections: [{level, title, body}]}]."""
    lines = _strip_code(path.read_text(encoding="utf-8").splitlines())
    sheets: list[dict] = []
    cur = None
    sec = None
    for ln in lines:
        if ln.startswith("# "):
            m = WS_RE[lang].match(ln)
            if m:
                cur = {"num": m.group(1), "title": _heading_text(m.group(2)), "sections": []}
                sheets.append(cur)
            else:
                cur = None
            sec = None
            continue
        if cur is None:
            continue
        m = re.match(r"^(#{2,3}) (.+)$", ln)
        if m:
            sec = {"level": len(m.group(1)), "title": _heading_text(m.group(2)), "body": []}
            cur["sections"].append(sec)
            continue
        if sec is not None:
            sec["body"].append(ln)
    return sheets


def _paragraphs(body: list[str]) -> list[list[str]]:
    paras, cur = [], []
    for ln in body:
        if ln.strip():
            cur.append(ln)
        elif cur:
            paras.append(cur)
            cur = []
    if cur:
        paras.append(cur)
    return paras


def _is_prose(para: list[str]) -> bool:
    first = para[0].lstrip()
    if first.startswith(("|", "---", "![", "<", "$$", "- ", "* ")) or re.match(r"^\d+\.\s", first):
        return False
    if all(FILL_RE.match(ln) for ln in para):
        return False
    text = " ".join(para).strip()
    if re.match(r"^\*?\*?(Hint|Indice|Astuce)\b", text.lstrip("*_ "), re.I):
        return False
    if text.startswith("**"):                          # "**Conflict 1:** …": a point
        return False
    if text.startswith("*") and text.endswith("*"):    # italic aside ("Use this space…")
        return False
    return bool(_clean(text))


def prompt_and_points(body: list[str]) -> tuple[str, list[str]]:
    prompt_parts: list[str] = []
    started_other = False
    for para in _paragraphs(body):
        if _is_prose(para) and not started_other:
            prompt_parts.append(_clean(" ".join(para)))
            if len(prompt_parts) == 2:
                break
        else:
            started_other = True
    prompt = " ".join(prompt_parts)
    if len(prompt) > PROMPT_MAX:
        cut = prompt[:PROMPT_MAX].rsplit(" ", 1)[0]
        prompt = cut.rstrip(",;:") + " …"
    points: list[str] = []
    for ln in body:
        s = ln.strip()
        m = re.match(r"^\*\*(.+?)\*\*.*$", s)
        n = re.match(r"^\d+\.\s+(.+)$", s)
        txt = _clean(s) if m else _clean(n.group(1)) if n else ""
        if txt and not FILL_RE.match(txt) and txt not in points:
            points.append(txt)
        if len(points) >= POINTS_MAX:
            break
    return prompt, points


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:40].rstrip("-") or "q"


def questions(sheet: dict, lang: str) -> list[dict]:
    """[{id, heading, prompt, points}] in document order."""
    out: list[dict] = []
    secs = sheet["sections"]
    i = 0
    while i < len(secs):
        sec = secs[i]
        if sec["level"] != 2:
            i += 1
            continue
        kids = []
        j = i + 1
        while j < len(secs) and secs[j]["level"] == 3:
            kids.append(secs[j])
            j += 1
        if READING_RE[lang].match(sec["title"]):
            i = j
            continue
        m = PART_RE[lang].match(sec["title"])
        if kids and all(k["title"].rstrip().endswith(("?", ":")) for k in kids):
            prompt, _ = prompt_and_points(sec["body"])
            for k in kids:
                p, pts = prompt_and_points(k["body"])
                out.append({"key": ("sub", sec["title"], k["title"]), "heading": k["title"].rstrip(" :"),
                            "group": sec["title"], "prompt": p or prompt, "points": pts})
        else:
            body = sec["body"] + [ln for k in kids for ln in ["", *k["body"]]]
            p, pts = prompt_and_points(body)
            out.append({"key": ("part", m.group(1)) if m else ("sec", sec["title"]),
                        "heading": sec["title"], "prompt": p, "points": pts})
        i = j
    return out


# ─── Build ────────────────────────────────────────────────────────────────

def _bi(en: str, fr: str) -> dict:
    return {"en": en, "fr": fr}


def build() -> dict:
    en_sheets = parse(SRC_EN, "en")
    fr_sheets = parse(SRC_FR, "fr")
    fr_by_num = {s["num"]: s for s in fr_sheets}
    wmap = yaml.safe_load(MAP.read_text(encoding="utf-8")) or {}
    defaults = wmap.get("defaults") or {}
    per = wmap.get("worksheets") or {}
    where = yaml.safe_load(WHERE.read_text(encoding="utf-8")) if WHERE.exists() else {}
    where_parts = (where or {}).get("parts") or {}
    targets = set((where or {}).get("targets") or {})
    link_ids = set((where or {}).get("links") or {})
    problems: list[str] = []

    sheets_out = []
    for s in en_sheets:
        wid = f"LW-{s['num']}"
        fr = fr_by_num.get(s["num"])
        if fr is None:
            problems.append(f"{wid}: no French twin (Fiche {s['num']})")
            continue
        qe, qf = questions(s, "en"), questions(fr, "fr")
        if len(qe) != len(qf):
            problems.append(f"{wid}: {len(qe)} English questions but {len(qf)} French")
            continue
        m = per.get(wid) or {}
        applies = {
            "tools": list(m.get("tools") or defaults.get("tools") or ["design"]),
            "steps": list(m.get("steps") or []),
            "tabs": list(m.get("tabs") or []),
            "levels": list(m.get("levels") or []),
            "gates": list(m.get("gates") or []),
        }
        qs = []
        seen: set[str] = set()
        for a, b in zip(qe, qf):
            if a["key"][0] == "part":
                qid = a["key"][1]
            elif a["key"][0] == "sec":
                qid = SPECIAL_IDS.get(a["heading"], _slug(a["heading"]))
            else:
                qid = _slug(a["heading"])
            base, n = qid, 2
            while qid in seen:
                qid = f"{base}-{n}"
                n += 1
            seen.add(qid)
            q = {"id": qid, "text": _bi(a["heading"], b["heading"]), "kind": "text"}
            if a["prompt"] or b["prompt"]:
                q["prompt"] = _bi(a["prompt"], b["prompt"] or a["prompt"])
            if a["points"] and len(a["points"]) == len(b["points"]):
                q["points"] = [_bi(x, y) for x, y in zip(a["points"], b["points"])]
            elif a["points"]:
                q["points"] = [_bi(x, x) for x in a["points"]]
                problems.append(f"{wid}/{qid}: {len(a['points'])} EN points but {len(b['points'])} FR; FR shows English")
            wp = where_parts.get(f"{wid}/{qid}")
            if wp is None:
                problems.append(f"{wid}/{qid}: not in where_map.yaml (audit)")
            else:
                for key, known in (("where", targets), ("links", link_ids)):
                    ids = list(wp.get(key) or [])
                    bad = [x for x in ids if x not in known]
                    if bad:
                        problems.append(f"{wid}/{qid}: unknown {key} id(s) {bad}")
                    if ids:
                        q[key] = ids
                if wp.get("book"):
                    q["book"] = [str(x) for x in wp["book"]]
            qs.append(q)
        sheets_out.append({
            "id": wid,
            "number": s["num"],
            "title": _bi(s["title"], fr["title"]),
            "phase": m.get("phase") or defaults.get("phase") or "exercise",
            "applies": applies,
            "questions": qs,
        })
    known_parts = {f"{w['id']}/{q['id']}" for w in sheets_out for q in w["questions"]}
    stale = sorted(set(where_parts) - known_parts)
    if stale:
        problems.append(f"where_map.yaml names questions that do not exist: {', '.join(stale)}")
    unknown = sorted(set(per) - {w["id"] for w in sheets_out})
    if unknown:
        problems.append(f"worksheet_map.yaml names worksheets that do not exist: {', '.join(unknown)}")
    return {
        "source": "design/docs/course/learner_workbook_expanded.md",
        "source_fr": "design/docs/course/fr/learner_workbook_expanded.md",
        "map": "design/configs/worksheets/worksheet_map.yaml",
        "where_map": "design/configs/worksheets/where_map.yaml",
        "worksheets": sheets_out,
        "_problems": problems,
    }


def render(data: dict) -> str:
    data = {k: v for k, v in data.items() if not k.startswith("_")}
    body = yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=100, default_flow_style=None)
    return HEADER + body


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if the committed YAML is stale")
    args = ap.parse_args(argv)
    data = build()
    for p in data["_problems"]:
        print(f"warning: {p}", file=sys.stderr)
    text = render(data)
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != text:
            diff = difflib.unified_diff(current.splitlines(), text.splitlines(),
                                        "committed", "regenerated", lineterm="", n=1)
            print("\n".join(list(diff)[:60]))
            print(f"\n{OUT.relative_to(ROOT)} is stale: run python3 scripts/gen_worksheets.py", file=sys.stderr)
            return 1
        print(f"{OUT.relative_to(ROOT)} is current ({len(data['worksheets'])} worksheets)")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    n_q = sum(len(w["questions"]) for w in data["worksheets"])
    print(f"wrote {OUT.relative_to(ROOT)}: {len(data['worksheets'])} worksheets, {n_q} questions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
