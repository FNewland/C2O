"""Live procedure checklists for the ops workbook (logbook "Workbook" tab).

Franz (2026-11-02): "make the checklists part of the log books". When an
operator opens or runs a procedure in the MCS, its confirm-each-step sheet
becomes a live checklist in their logbook. The checklist is built from the
PROCEDURE CARD (``configs/<mission>/procedures/**.md``), because the card is
what is executed; the printed workbook sheet (``WB-5.x-…`` in
``ops_week3.yaml``) is kept beside each step as the printed reference, and
every place where the two disagree is listed (``mismatches``).

Card model (``parse_card``): every ``### Step N — Title`` (``### Étape N``
in the French twin) is a step; any other ``###`` section that carries
``**TC:**`` / ``**Verify:**`` / ``**GO/NO-GO:**`` / ``**Action:**`` lines is a
step too (recovery orbits, recovery actions). Each ``**Verify:**`` becomes a
check: the quoted parameter, its id, the comparison and the expected value
when the line states one, so the tick can capture the observed value.

Prerequisites (``parse_prereqs``): every ``- [ ]`` item of the card's
``## Prerequisites`` (``## Prérequis``) section, keyed ``p1``, ``p2``… in
document order, its indented continuation lines folded in. They are ticked
like steps (``check.part = "pre"``), on the card in the MCS and in the
Workbook tab, and come first in the exported run.

Runner mapping (``runner_map``): for a card the MCS can run (``runnable:
{kind: markdown}``), the runner's atomic steps are the card's TC / Verify /
GO/NO-GO lines in document order (``smo_common.procedures.markdown_steps``).
The map gives, for each runner step index, the checklist step it belongs to,
so "runner step 7 PASSED" ticks card step 3. A card run from a planner
activity type (``runnable: {kind: activity_type}``) executes the activity's
own command sequence, so its map is data: ``mcs/runner_step_map.yaml`` (one
card step key per runner step, plus ``notes`` where the activity does a
step differently from the card; they ride with the runner's tick).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

__all__ = ["parse_card", "parse_check", "parse_prereqs", "runner_map", "build_checklist",
           "compare_sheet", "ChecklistProvider", "sheet_for_procedure"]

_STEP_HEAD = re.compile(
    r"^###\s+(?:Step|[ÉE]tape)\s+([0-9]+[A-Za-z]?)\b\s*(?:-{2,3}|—|–|:|-)?\s*(.*?)\s*$")
_H3 = re.compile(r"^###\s+(.+?)\s*$")
_H2 = re.compile(r"^##\s+(.+?)\s*$")
_H1 = re.compile(r"^#\s+(.+?)\s*$")
_TAG = re.compile(
    r"^\s*(?:[-*]\s+)?\*\*(?P<tag>TC|Verify|(?:Jalon\s+)?GO/NO-?GO(?:\s+Gate)?[^*:]*|Note|Action|BRANCH|LABEL)"
    r"\s*:?\*\*\s*:?\s*(?P<rest>.*)$")
_ANY_BOLD_TAG = re.compile(r"^\s*\*\*[^*]+:\*\*")
_ANCHOR = re.compile(r"\s*\{#[A-Za-z0-9_][\w.:-]*(?:\s[^}]*)?\}\s*$")

_PARAM = r"[a-z][a-z0-9_]+(?:\.[a-z0-9_]+)+"
#: `param` [(0xHHHH)] OP VALUE  — the card's verification grammar.
_CHECK = re.compile(
    r"\|?`(?P<param>" + _PARAM + r")`\|?\s*(?:\((?P<pid>0x[0-9A-Fa-f]{4})\))?\s*"
    r"(?P<op>==|!=|<=|>=|≤|≥|≠|=|<|>|in\s+range|in)?\s*"
    r"(?P<value>\{[^}]*\}|\[[^\]]*\]|`[^`]*`(?:\s*\(0x[0-9A-Fa-f]{4}\))?|[-+−]?\d[\d.,]*(?:e[-+]?\d+)?\s*[%A-Za-z°/µ]*|[A-Z][A-Z_]+)?")
#: the runner's own predicate form inside one backtick span
_PRED = re.compile(r"`(?P<param>" + _PARAM + r")\s*(?P<op>==|!=|>=|<=|>|<)\s*(?P<value>[^`\s]+)`")
_HEX = re.compile(r"\b0x[0-9A-Fa-f]{4}\b")
_CMD = re.compile(r"\b([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+)\b")
_NUM = re.compile(r"[-+−]?\d+(?:[.,]\d+)?(?:e[-+]?\d+)?")
_OPS = {"=": "==", "==": "==", "!=": "!=", "≠": "!=", "<": "<", ">": ">",
        "<=": "<=", ">=": ">=", "≤": "<=", "≥": ">="}
#: Upper-case words that are not telecommands (statuses, mode names).
_NOT_CMD = {"GO_NOGO", "NO_GO", "SAFE_BOOT", "COARSE_SUN", "FINE_POINT", "TRACKING_READY",
            "BOOT_COMPLETE", "BOOT_FAILURE", "NOT_OK"}


def _num(s: str) -> float | None:
    m = _NUM.search(s or "")
    if not m:
        return None
    try:
        return float(m.group(0).replace("−", "-").replace(",", "."))
    except ValueError:
        return None


def parse_check(text: str) -> dict:
    """One ``**Verify:**`` line -> ``{text, param?, pid?, op?, value?, lo?, hi?,
    set?}``. ``op`` is ``== != < > <= >= in``; ``value`` is the expected value as
    written; ``lo``/``hi`` a numeric range, ``set`` a list of allowed values."""
    out: dict[str, Any] = {"text": text.strip()}
    m = _PRED.search(text)
    if m:
        out.update(param=m.group("param"), op=_OPS.get(m.group("op"), m.group("op")),
                   value=m.group("value"))
        n = _num(m.group("value"))
        if n is not None:
            out["num"] = n
        return out
    m = _CHECK.search(text)
    if not m:
        h = _HEX.search(text)
        if h:
            out["pid"] = h.group(0)
        return out
    out["param"] = m.group("param")
    if m.group("pid"):
        out["pid"] = m.group("pid")
    else:
        h = re.match(r"\s*\(?\s*(0x[0-9A-Fa-f]{4})", text[m.end("param") + 1:])
        if h:
            out["pid"] = h.group(1)
    op, value = (m.group("op") or "").strip(), (m.group("value") or "").strip()
    if not op:
        return out
    if op.startswith("in"):
        if value.startswith("{"):
            out.update(op="in", value=value,
                       set=[v.strip() for v in value.strip("{}").split(",") if v.strip()])
        elif value.startswith("["):
            parts = [_num(p) for p in value.strip("[]").split(",")]
            if len(parts) == 2 and None not in parts:
                out.update(op="in", value=value, lo=parts[0], hi=parts[1])
        return out
    if not value:
        return out
    out["op"] = _OPS.get(op, op)
    if value.startswith("`"):
        # compared with another parameter: `eps.power_gen` > `eps.power_cons`
        out["value"] = out["ref_param"] = value[1:].split("`")[0]
    else:
        out["value"] = value
        n = _num(value)
        if n is not None and not re.match(r"^[A-Z_]+$", value):
            out["num"] = n
    return out


def _clean_title(s: str) -> str:
    s = _ANCHOR.sub("", s or "")
    return re.sub(r"\s+", " ", s).strip(" -—–:")


def parse_card(md: str) -> dict:
    """``{title, steps: [{key, n, title, tcs, checks, gonogo, notes, actions,
    line}]}`` from a procedure card. Steps keep document order; ``key`` is
    ``s<N>`` for a numbered step, ``h<i>`` for another titled section."""
    lines = (md or "").splitlines()
    title = ""
    steps: list[dict] = []
    cur: dict | None = None
    last: tuple[str, int] | None = None     # (list name, index) for continuation lines
    h_count = 0
    for i, raw in enumerate(lines):
        line = raw.rstrip()
        if not title:
            m = _H1.match(line)
            if m:
                title = _clean_title(m.group(1))
                continue
        m = _STEP_HEAD.match(line)
        if m or _H3.match(line):
            if m:
                n, t = m.group(1), _clean_title(m.group(2))
                key = f"s{n.lower()}"
            else:
                h_count += 1
                n, t, key = "", _clean_title(_H3.match(line).group(1)), f"h{h_count}"
            cur = {"key": key, "n": n, "title": t, "tcs": [], "checks": [], "gonogo": "",
                   "notes": [], "actions": [], "line": i + 1}
            steps.append(cur)
            last = None
            continue
        if _H2.match(line) or _H1.match(line):
            cur, last = None, None
            continue
        if cur is None:
            continue
        stripped = line.strip()
        if not stripped:
            last = None if last and last[0] != "gonogo" else last
            continue
        t = _TAG.match(line)
        if t:
            tag, rest = t.group("tag"), t.group("rest").strip()
            if tag == "TC":
                cmd = re.match(r"`([^`]+)`", rest)
                cur["tcs"].append({"text": rest, "cmd": cmd.group(1) if cmd else ""})
                last = ("tcs", len(cur["tcs"]) - 1)
            elif tag == "Verify":
                cur["checks"].append(parse_check(rest))
                last = ("checks", len(cur["checks"]) - 1)
            elif "GO/NO" in tag:
                cur["gonogo"] = (cur["gonogo"] + " " + rest).strip() if cur["gonogo"] else rest
                last = ("gonogo", 0)
            elif tag == "Note":
                cur["notes"].append(rest)
                last = ("notes", len(cur["notes"]) - 1)
            elif tag == "Action":
                cur["actions"].append(rest)
                last = ("actions", len(cur["actions"]) - 1)
            else:
                last = None
            continue
        if _ANY_BOLD_TAG.match(line):
            # **Decision:** after a GO/NO-GO gate belongs to the gate
            if last and last[0] == "gonogo":
                cur["gonogo"] += " " + re.sub(r"\*\*", "", stripped)
            else:
                last = None
            continue
        if last:
            name, idx = last
            extra = re.sub(r"^[-*]\s+", "• ", stripped)
            if name == "gonogo":
                cur["gonogo"] += ("\n" if extra.startswith("•") else " ") + extra
            elif name == "checks":
                c = cur["checks"][idx]
                c["text"] += " " + extra
            elif name == "tcs":
                cur["tcs"][idx]["text"] += " " + extra
            else:
                cur[name][idx] += " " + extra
    # a titled section with nothing to do or check is reference text, not a step
    steps = [s for s in steps if s["n"] or s["tcs"] or s["checks"] or s["gonogo"] or s["actions"]]
    return {"title": title, "steps": steps}


_PREREQ_HEAD = re.compile(r"^##\s+(?:Prerequisites|Pr[ée]requis|Conditions\s+pr[ée]alables)\b", re.I)
#: a checkbox item at the start of a line (indented items are continuation)
_PREREQ_ITEM = re.compile(r"^[-*]\s+\[[ xX]\]\s+(.*\S)\s*$")


def parse_prereqs(md: str) -> list[dict]:
    """``[{key: "p1", text, line}]``: the ``- [ ]`` items of the card's
    Prerequisites section, in order, with indented continuation lines
    folded in. The MCS card view and the documentation viewer number the
    same items the same way (``procard.js``)."""
    out: list[dict] = []
    inside = False
    for i, raw in enumerate((md or "").splitlines()):
        line = raw.rstrip()
        if _H2.match(line) or _H1.match(line) or _H3.match(line):
            inside = bool(_PREREQ_HEAD.match(line))
            continue
        if not inside:
            continue
        m = _PREREQ_ITEM.match(line)
        if m:
            out.append({"key": f"p{len(out) + 1}", "text": m.group(1), "line": i + 1})
        elif out and line[:1] in (" ", "\t") and line.strip() and not re.match(r"^\s*[-*]\s", line):
            out[-1]["text"] += " " + line.strip()
        elif not line.strip():
            continue
        elif out:
            # any other line ends the item list's continuation
            out[-1].setdefault("_closed", True)
    for p in out:
        p.pop("_closed", None)
    return out


def runner_map(md: str, catalog: dict | None = None) -> list[str | None]:
    """For each step the MCS runner extracts from *md* (``from_markdown``),
    the checklist step key it belongs to (``None``: outside any step).

    The runner's extraction is line-local, so running it per section and
    concatenating gives the same step list as running it on the whole card
    (pinned by a test); the section a step came from is its checklist step.
    """
    from smo_common.procedures import markdown_steps
    lines = (md or "").splitlines(keepends=True)
    keys = {s["line"]: s["key"] for s in parse_card(md)["steps"]}
    out: list[str | None] = []
    seg: list[str] = []
    seg_key: str | None = None

    def flush():
        if seg:
            steps, _ = markdown_steps("".join(seg), catalog)
            out.extend([seg_key] * len(steps))

    h3 = 0
    for i, line in enumerate(lines):
        if _STEP_HEAD.match(line.rstrip()) or _H3.match(line.rstrip()) \
                or _H2.match(line.rstrip()) or _H1.match(line.rstrip()):
            flush()
            seg = []
            seg_key = keys.get(i + 1)
            h3 += 1
        seg.append(line)
    flush()
    return out


# ── the printed workbook sheet ─────────────────────────────────────────

def _tokens(text: str) -> dict[str, set[str]]:
    t = text or ""
    cmds = {c for c in _CMD.findall(t) if c not in _NOT_CMD and len(c) > 4}
    return {"cmd": cmds,
            "param": set(re.findall(r"\b(" + _PARAM + r")\b", t)),
            "pid": {h.lower() for h in _HEX.findall(t)}}


_STOP = {"verify", "confirm", "check", "station", "should", "which", "their", "there", "after",
         "before", "every", "within", "where", "while", "until", "spacecraft", "procedure"}


def _words(text: str) -> set[str]:
    """Content words (5+ letters, a crude stem) for matching prose to prose."""
    return {w[:7] for w in re.findall(r"[a-z]{5,}", (text or "").lower()) if w not in _STOP}


def _step_text(s: dict) -> str:
    parts = [s["title"]] + [x["text"] for x in s["tcs"]] + [c["text"] for c in s["checks"]] \
        + [s["gonogo"]] + s["actions"] + s["notes"]
    return "\n".join(p for p in parts if p)


def compare_sheet(card: dict, sheet: dict | None, lang: str = "en") -> dict:
    """Line the printed sheet's confirm-each-step rows up with the card.

    Returns ``{rows: {step key: [row refs]}, mismatches: [{kind, row?, step?,
    detail}]}``. A row matches the card step that shares most commands,
    parameter names and parameter ids with it (ties go to the first tied step
    after the one the previous row matched, else to the earliest).
    Reported: a different number of steps; a printed row whose command or
    parameter is nowhere on the card; a card step no printed row covers; a
    printed row matched out of order.
    """
    out: dict[str, Any] = {"rows": {}, "mismatches": []}
    if not sheet:
        return out
    rows = [q for q in sheet.get("questions") or [] if q.get("step")]
    if not rows:
        out["mismatches"].append({"kind": "no_steps",
                                  "detail": "the printed sheet has no confirm-each-step rows"})
        return out

    def txt(v):
        return (v.get(lang) or v.get("en") or "") if isinstance(v, dict) else str(v or "")

    steps = card["steps"]
    card_tok = [_tokens(_step_text(s)) for s in steps]
    all_card = {k: set().union(*(t[k] for t in card_tok)) if card_tok else set()
                for k in ("cmd", "param", "pid")}
    if len(rows) != len(steps):
        out["mismatches"].append({
            "kind": "count", "n_sheet": len(rows), "n_card": len(steps), "detail": f"printed sheet has {len(rows)} steps, card has {len(steps)}"})
    covered: set[str] = set()
    last_idx = -1
    for q in rows:
        en = txt(q.get("text")) + " " + txt(q.get("hint"))
        tok = _tokens((q.get("text") or {}).get("en", "") + " " + (q.get("hint") or {}).get("en", ""))
        best, best_score = None, 0
        scores = [3 * len(tok["cmd"] & ct["cmd"]) + 2 * len(tok["pid"] & ct["pid"])
                  + len(tok["param"] & ct["param"]) for ct in card_tok]
        top = max(scores, default=0)
        if top > 0:
            # Ties (HK_REQUEST is on half the steps of a card) go to the first
            # tied step after the previous row's, then to the earliest one.
            tied = [i for i, s in enumerate(scores) if s == top]
            best = next((i for i in tied if i > last_idx), tied[0])
            best_score = top
        ref = {"q": q.get("id"), "n": q.get("step"), "text": txt(q.get("text")),
               "hint": txt(q.get("hint"))}
        if best is None:
            # prose on both sides: the step that shares the most content words
            words = _words((q.get("text") or {}).get("en", ""))
            for i, s in enumerate(steps):
                score = len(words & _words(s["title"] + " " + " ".join(s["actions"])))
                if score >= 2 and score > best_score:
                    best, best_score = i, score
        if best is None:
            out["mismatches"].append({"kind": "row_unmatched", "row": q.get("step"),
                                      "text": txt(q.get("text")),
                                      "detail": f"printed row {q.get('step')} has no counterpart on the card: {en.strip()[:160]}"})
            continue
        key = steps[best]["key"]
        covered.add(key)
        out["rows"].setdefault(key, []).append(ref)
        if best < last_idx:
            out["mismatches"].append({"kind": "order", "row": q.get("step"), "step": steps[best]["n"] or key,
                                      "detail": f"printed row {q.get('step')} matches card step {steps[best]['n'] or key}, out of the card's order"})
        last_idx = max(last_idx, best)
        missing_cmd = sorted(tok["cmd"] - all_card["cmd"])
        missing_par = sorted((tok["param"] - all_card["param"]))
        if missing_cmd:
            out["mismatches"].append({"kind": "command", "row": q.get("step"), "names": missing_cmd,
                                      "detail": f"printed row {q.get('step')} names {', '.join(missing_cmd)}, which the card does not send"})
        if missing_par:
            out["mismatches"].append({"kind": "parameter", "row": q.get("step"), "names": missing_par,
                                      "detail": f"printed row {q.get('step')} checks {', '.join(missing_par)}, which the card does not check"})
    for s in steps:
        if s["key"] not in covered:
            out["mismatches"].append({"kind": "step_unprinted", "step": s["n"] or s["key"],
                                      "key": s["key"], "title": s["title"],
                                      "detail": f"card step {s['n'] or s['key']} ({s['title']}) is not on the printed sheet"})
    return out


def sheet_for_procedure(sheets: list[dict], proc_id: str) -> dict | None:
    """The printed confirm-each-step sheet for a procedure (has step rows)."""
    cands = [w for w in sheets if proc_id in ((w.get("applies") or {}).get("procedures") or [])]
    for w in cands:
        if any(q.get("step") for q in w.get("questions") or []):
            return w
    return cands[0] if cands and not cands[0].get("form") and \
        "confirm" in str((cands[0].get("title") or {}).get("en", "")).lower() else None


def _loc(v: Any, lang: str) -> str:
    if isinstance(v, dict):
        return str(v.get(lang) or v.get("en") or "")
    return "" if v is None else str(v)


def _plain(s: str) -> str:
    """Card markup as reading text: no code ticks or bold markers."""
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s or "")
    s = re.sub(r"\s+-{2,3}\s+", " — ", s)
    return re.sub(r"[ \t]+", " ", s.replace("`", "")).strip()


def build_checklist(proc_id: str, card_md: str, *, card_md_fr: str | None = None,
                    sheet: dict | None = None, name: str = "", file: str = "",
                    runnable: bool = False, catalog: dict | None = None,
                    lang: str = "en", step_map: list | None = None,
                    runner_notes: dict | None = None) -> dict:
    """The checklist the logbook renders for *proc_id* (see module doc).

    ``step_map``: the runner map of an activity-type card (from
    ``runner_step_map.yaml``) instead of one derived from the card's TC
    lines; ``runner_notes``: ``{step key: text}`` already in *lang*."""
    lang = "fr" if lang == "fr" else "en"
    en = parse_card(card_md)
    fr = parse_card(card_md_fr) if card_md_fr else None
    fr_by_key = {s["key"]: s for s in (fr["steps"] if fr else [])}
    cmp = compare_sheet(en, sheet, lang)
    steps = []
    for s in en["steps"]:
        loc = fr_by_key.get(s["key"]) if lang == "fr" else None
        # the French twin must have the same checks, or its text is not used
        if loc and (len(loc["checks"]) != len(s["checks"]) or len(loc["tcs"]) != len(s["tcs"])):
            loc = None
        src = loc or s
        checks = []
        for c_en, c_loc in zip(s["checks"], src["checks"]):
            c = dict(c_en)            # parsed from the English card: the executed one
            c["text"] = _plain(c_loc["text"])
            checks.append(c)
        steps.append({
            "key": s["key"], "n": s["n"], "title": _plain(src["title"] or s["title"]),
            "tcs": [t["cmd"] or _plain(t["text"]) for t in s["tcs"]],
            "checks": checks,
            # the English card decides that a step is a GO/NO-GO gate
            "gonogo": "\n".join(_plain(x) for x in (src["gonogo"] or s["gonogo"]).split("\n")).strip(),
            "actions": [_plain(a) for a in src["actions"]],
            "ref": cmp["rows"].get(s["key"], []),
        })
    titles = {st["key"]: st["title"] for st in steps}
    for m in cmp["mismatches"]:
        if m.get("kind") == "step_unprinted" and m.get("key") in titles:
            m["title"] = titles[m["key"]]
    pre_en = parse_prereqs(card_md)
    pre_fr = parse_prereqs(card_md_fr) if (card_md_fr and lang == "fr") else []
    if len(pre_fr) != len(pre_en):
        pre_fr = []                   # the twin must list the same items
    prereqs = []
    for i, p in enumerate(pre_en):
        c = parse_check(p["text"])
        item = {"key": p["key"], "n": f"P{i + 1}",
                "text": _plain(pre_fr[i]["text"] if pre_fr else p["text"])}
        if c.get("param"):
            c["text"] = item["text"]
            item["checks"] = [c]
        prereqs.append(item)
    sheet_id = sheet["id"] if sheet else f"PROC-{proc_id}"
    extra = []
    if sheet:
        for q in sheet.get("questions") or []:
            if q.get("step"):
                continue
            item = {"id": q.get("id"), "kind": q.get("kind") or "text", "text": _loc(q.get("text"), lang)}
            if q.get("hint"):
                item["hint"] = _loc(q["hint"], lang)
            extra.append(item)
    out = {
        "procedure": proc_id,
        "name": name or en["title"],
        "title": (fr["title"] if (fr and lang == "fr" and fr["title"]) else en["title"]),
        "card": file,
        "lang": lang,
        "sheet_id": sheet_id,
        "sheet_title": _loc(sheet.get("title"), lang) if sheet else "",
        "runnable": bool(runnable),
        "steps": steps,
        "prereqs": prereqs,
        "extra": extra,
        "mismatches": cmp["mismatches"],
    }
    if runnable:
        out["runner_map"] = (list(step_map) if step_map is not None
                             else runner_map(card_md, catalog))
        keys = {st["key"] for st in steps}
        notes = {k: str(v) for k, v in (runner_notes or {}).items() if k in keys and v}
        if notes:
            out["runner_notes"] = notes
    return out


class ChecklistProvider:
    """``provider(proc_id, lang) -> checklist | None`` for the logbook routes.

    ``index``: procedure_index.yaml entries; ``proc_dir``: the cards;
    ``fr_dir``: the French cards (``i18n/fr/procedures``); ``sheets``: a
    callable returning the worksheet catalogue's raw sheets; ``catalog``: the
    TC catalogue (mnemonic -> {service, subtype, func_id}) for the runner map;
    ``step_maps``: ``runner_step_map.yaml``'s ``procedures`` (a dict or a
    callable returning one) for the activity-type cards.
    Cards are re-read when they change on disk (cheap: mtime check).
    """

    def __init__(self, index: list[dict] | Callable[[], list[dict]], proc_dir: Path,
                 fr_dir: Path | None = None, sheets: Callable[[], list[dict]] | None = None,
                 catalog: Callable[[], dict] | dict | None = None,
                 step_maps: Callable[[], dict] | dict | None = None):
        self._step_maps = step_maps
        self._index = index
        self.proc_dir = Path(proc_dir)
        self.fr_dir = Path(fr_dir) if fr_dir else None
        self._sheets = sheets or (lambda: [])
        self._catalog = catalog
        self._cache: dict[tuple, tuple] = {}

    def index(self) -> list[dict]:
        return self._index() if callable(self._index) else self._index

    def entry(self, proc_id: str) -> dict | None:
        return next((e for e in self.index() if e.get("id") == proc_id), None)

    def _read(self, base: Path | None, rel: str) -> tuple[str | None, int]:
        if not base or not rel:
            return None, 0
        p = (base / rel).resolve()
        if not str(p).startswith(str(base.resolve())) or not p.is_file():
            return None, 0
        return p.read_text(encoding="utf-8"), p.stat().st_mtime_ns

    def __call__(self, proc_id: str, lang: str = "en") -> dict | None:
        e = self.entry(proc_id)
        if not e or not e.get("file"):
            return None
        md, m1 = self._read(self.proc_dir, e["file"])
        if md is None:
            return None
        fr, m2 = self._read(self.fr_dir, e["file"]) if lang == "fr" else (None, 0)
        sheets = self._sheets() or []
        key = (proc_id, lang, m1, m2, id(sheets), len(sheets))
        hit = self._cache.get(key)
        if hit:
            return hit[0]
        link = e.get("runnable") if isinstance(e.get("runnable"), dict) else {}
        runnable = link.get("kind") == "markdown"
        step_map, notes = None, None
        if link.get("kind") == "activity_type":
            sm = self.step_map(proc_id)
            if sm and sm.get("activity_type") == link.get("ref") and isinstance(sm.get("steps"), list):
                runnable, step_map = True, sm["steps"]
                notes = {k: _loc(v, lang) for k, v in (sm.get("notes") or {}).items()}
        cat = self._catalog() if callable(self._catalog) else (self._catalog or {})
        out = build_checklist(proc_id, md, card_md_fr=fr, sheet=sheet_for_procedure(sheets, proc_id),
                              name=str(e.get("name") or ""), file=e["file"],
                              runnable=runnable, catalog=cat, lang=lang,
                              step_map=step_map, runner_notes=notes)
        if not out["steps"]:
            out = None                # a retired / prose-only card: no checklist
        if len(self._cache) > 256:
            self._cache.clear()
        self._cache[key] = (out,)
        return out

    def step_map(self, proc_id: str) -> dict | None:
        """The ``runner_step_map.yaml`` entry of an activity-type card."""
        maps = self._step_maps() if callable(self._step_maps) else (self._step_maps or {})
        m = (maps or {}).get(proc_id)
        return m if isinstance(m, dict) else None

    def report(self) -> list[dict]:
        """Every printed confirm-each-step sheet against its card (EN)."""
        rows = []
        for w in self._sheets() or []:
            procs = (w.get("applies") or {}).get("procedures") or []
            if not any(q.get("step") for q in w.get("questions") or []):
                continue
            for pid in procs:
                cl = self(pid, "en")
                rows.append({"sheet": w["id"], "procedure": pid,
                             "card": cl["card"] if cl else None,
                             "mismatches": cl["mismatches"] if cl else
                             [{"kind": "no_card", "detail": "no procedure card"}]})
        return rows


def _main(argv=None) -> int:          # pragma: no cover - a report for people
    """``python3 -m smo_common.logbook.checklist [config_dir]``: list where
    the printed confirm-each-step sheets and the procedure cards disagree."""
    import sys

    import yaml

    from .worksheets import WorksheetCatalog
    args = list(sys.argv[1:] if argv is None else argv)
    cfg = Path(args[0]) if args else Path("configs/eosat1")
    index = (yaml.safe_load((cfg / "procedures" / "procedure_index.yaml").read_text()) or {}).get("procedures", [])
    cat = WorksheetCatalog(cfg / "worksheets")
    sm_path = cfg / "mcs" / "runner_step_map.yaml"
    maps = ((yaml.safe_load(sm_path.read_text(encoding="utf-8")) or {}).get("procedures") or {}) \
        if sm_path.is_file() else {}
    prov = ChecklistProvider(index, cfg / "procedures", cfg / "i18n" / "fr" / "procedures", cat.sheets,
                             step_maps=maps)
    for r in prov.report():
        print(f"{r['sheet']}  <->  {r['procedure']}  ({r['card']})")
        for m in r["mismatches"] or [{"detail": "lines up"}]:
            print(f"    - {m['detail']}")
    return 0


if __name__ == "__main__":            # pragma: no cover
    raise SystemExit(_main())
