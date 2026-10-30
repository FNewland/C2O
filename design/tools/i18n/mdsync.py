"""Markdown section segmentation, alignment and sidecar state.

A section is a heading line plus its body up to the next heading of any level;
text before the first heading is section 0 (the preamble, id "_preamble").
Section ids are the slugified heading-text path ("a/b/c"), "~N" for duplicates;
an explicit {#id} on the heading replaces its slug.

EN and FR are aligned by position (FR mirrors EN headings 1:1). The sidecar
records, in FR order, which EN section id each FR section mirrors and both
hashes at the last sync, so after EN headings are inserted/removed the FR
sections are realigned by id and the file is reported "structure changed".
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

from . import TOOL_VERSION
from .textutil import slugify, text_hash

_FENCE_RE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")
_HEAD_RE = re.compile(r"^(#{1,6})(?:[ \t]+(.*?))?[ \t]*$")
_EXPLICIT_ID = re.compile(r"\{#([\w:.-]+)[^}]*\}\s*$")


@dataclass
class Section:
    idx: int
    id: str
    level: int          # 0 = preamble
    title: str
    text: str           # exact source text (heading line + body)

    def hash(self, en: bool) -> str:
        return text_hash(self.text, en=en)


def segment(text: str) -> list[Section]:
    lines = text.splitlines(keepends=True)
    starts: list[tuple[int, int, str]] = []  # (line_no, level, title)
    fence = None
    i0 = 0
    if lines and lines[0].strip() == "---":   # YAML front matter belongs to the preamble
        for j in range(1, len(lines)):
            if lines[j].strip() in ("---", "..."):
                i0 = j + 1
                break
    for n in range(i0, len(lines)):
        ln = lines[n]
        m = _FENCE_RE.match(ln)
        if fence:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
                fence = None
            continue
        if m:
            fence = m.group(1)
            continue
        h = _HEAD_RE.match(ln.rstrip("\r\n"))
        if h:
            title = (h.group(2) or "")
            title = re.sub(r"[ \t]+#+[ \t]*$", "", title)
            starts.append((n, len(h.group(1)), title))
    secs: list[Section] = []
    bounds = [0] + [s[0] for s in starts] + [len(lines)]
    secs.append(Section(0, "_preamble", 0, "", "".join(lines[bounds[0]:bounds[1]])))
    stack: list[tuple[int, str]] = []
    seen: dict[str, int] = {}
    for k, (n, level, title) in enumerate(starts):
        while stack and stack[-1][0] >= level:
            stack.pop()
        m = _EXPLICIT_ID.search(title)
        slug = m.group(1) if m else slugify(title)
        path = "/".join([s for _, s in stack] + [slug])
        stack.append((level, slug))
        seen[path] = seen.get(path, 0) + 1
        sid = path if seen[path] == 1 else f"{path}~{seen[path]}"
        secs.append(Section(k + 1, sid, level, title, "".join(lines[bounds[k + 1]:bounds[k + 2]])))
    return secs


def levels(secs: list[Section]) -> list[int]:
    return [s.level for s in secs]


# ------------------------------------------------------------------ sidecar
def sidecar_path(fr_path: str) -> str:
    d, name = os.path.split(fr_path)
    return os.path.join(d, ".i18n", name + ".json")


def load_state(fr_path: str) -> dict | None:
    p = sidecar_path(fr_path)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_state(fr_path: str, state: dict) -> str:
    p = sidecar_path(fr_path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    state["tool_version"] = TOOL_VERSION
    with open(p, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return p


# ------------------------------------------------------------------ alignment
@dataclass
class Pair:
    en: Section | None
    fr: Section | None
    rec: dict | None
    status: str = ""


@dataclass
class Alignment:
    pairs: list[Pair]
    structure_changed: bool = False
    note: str = ""
    fr_exists: bool = True
    counts: dict = field(default_factory=dict)


def _status(p: Pair) -> str:
    if (p.en is not None and p.en.level == 0 and not p.en.text.strip()
            and (p.fr is None or not p.fr.text.strip())):
        return "ok"          # empty preamble on both sides: nothing to translate
    if p.en is not None and p.fr is None:
        return "missing"
    if p.en is None:
        return "orphan"
    if p.rec is None:
        return "untracked"
    en_changed = p.en.hash(en=True) != p.rec.get("en_hash")
    fr_changed = p.fr.hash(en=False) != p.rec.get("fr_hash")
    if en_changed and fr_changed:
        return "conflict"
    if en_changed:
        return "stale"
    if fr_changed:
        return "fr-edited"
    return "ok"


def align(en: list[Section], fr: list[Section] | None, state: dict | None) -> Alignment:
    if fr is None:
        pairs = [Pair(s, None, None) for s in en]
        a = Alignment(pairs, fr_exists=False, note="no FR file")
    else:
        recs = (state or {}).get("sections")
        en_by_id = {s.id: s for s in en}
        if recs is not None and len(recs) == len(fr):
            # FR[i] mirrors recs[i]["id"]; realign to current EN by id
            used: set[str] = set()
            fr_pairs: list[Pair] = []
            for sec, rec in zip(fr, recs):
                e = en_by_id.get(rec.get("id"))
                if e is None or e.id in used:
                    fr_pairs.append(Pair(None, sec, rec))
                else:
                    used.add(e.id)
                    fr_pairs.append(Pair(e, sec, rec))
            pairs = _merge_order(en, fr_pairs, used)
            changed = [r.get("id") for r in recs] != [s.id for s in en]
            a = Alignment(pairs, structure_changed=changed,
                          note="structure changed (realigned by id)" if changed else "")
        else:
            rec_by_id = {r.get("id"): r for r in (recs or [])}
            le, lf = levels(en), levels(fr)
            if le == lf:
                pairs = [Pair(e, f, rec_by_id.get(e.id)) for e, f in zip(en, fr)]
                changed = recs is not None and len(recs) != len(fr)
                a = Alignment(pairs, structure_changed=changed,
                              note="FR structure edited since last sync" if changed else "")
            else:
                k = 0
                while k < min(len(le), len(lf)) and le[k] == lf[k]:
                    k += 1
                pairs = [Pair(en[i], fr[i], rec_by_id.get(en[i].id)) for i in range(k)]
                pairs += [Pair(e, None, None) for e in en[k:]]
                pairs += [Pair(None, f, None) for f in fr[k:]]
                a = Alignment(pairs, structure_changed=True,
                              note=f"heading structure differs from heading #{k} "
                                   f"(EN {len(en) - 1} headings, FR {len(fr) - 1}); no usable sidecar")
    for p in a.pairs:
        p.status = _status(p)
        a.counts[p.status] = a.counts.get(p.status, 0) + 1
    return a


def _merge_order(en: list[Section], fr_pairs: list[Pair], used: set[str]) -> list[Pair]:
    """Order pairs by EN position; orphans follow the aligned FR section before them;
    EN sections with no FR counterpart are inserted as 'missing'."""
    after: dict[int, list[Pair]] = {}
    last = -1
    aligned: dict[int, Pair] = {}
    for p in fr_pairs:
        if p.en is None:
            after.setdefault(last, []).append(p)
        else:
            aligned[p.en.idx] = p
            last = p.en.idx
    out = list(after.get(-1, []))
    for s in en:
        out.append(aligned.get(s.idx) or Pair(s, None, None))
        out.extend(after.get(s.idx, []))
    return out


def assemble(al: Alignment, replacements: dict[str, str]) -> str:
    """Rebuild the FR file in EN order. replacements maps EN section id -> new FR text."""
    parts = []
    for p in al.pairs:
        if p.en is not None and p.en.id in replacements:
            parts.append(replacements[p.en.id])
        elif p.fr is not None:
            parts.append(p.fr.text)
    parts = [x for x in parts if x]
    for k in range(len(parts) - 1):
        if not parts[k].endswith("\n"):
            parts[k] += "\n"
    return "".join(parts)


def build_state(en_path_ref: str, al: Alignment, old: dict | None, update_ids: set[str] | None,
                en_commit: str | None = None) -> dict:
    """State for the FR file described by `al` (after any assemble+re-segment).
    update_ids: EN ids whose hashes are recorded as synced now (None = all aligned)."""
    secs = []
    for p in al.pairs:
        if p.fr is None:
            continue
        if p.en is not None and (update_ids is None or p.en.id in update_ids):
            secs.append({"id": p.en.id, "en_hash": p.en.hash(en=True), "fr_hash": p.fr.hash(en=False)})
        elif p.rec is not None:
            r = dict(p.rec)
            if p.en is not None:
                r["id"] = p.en.id
            secs.append(r)
        else:
            secs.append({"id": p.en.id if p.en else f"_orphan~{p.fr.idx}", "en_hash": None,
                         "fr_hash": None})
    st = {"tool_version": TOOL_VERSION, "en_path": en_path_ref, "sections": secs}
    if old:
        for k in ("waivers",):
            if k in old:
                st[k] = old[k]
        if old.get("en_commit") and not en_commit:
            st["en_commit"] = old["en_commit"]
    if en_commit:
        st["en_commit"] = en_commit
    return st


def trailing_ws(s: str) -> str:
    m = re.search(r"\s*$", s)
    return m.group(0) if m else ""


def fit_section(new_fr: str, en_sec: Section) -> str:
    """Give a translated section the same trailing blank lines as its EN section."""
    tail = trailing_ws(en_sec.text) or "\n"
    return new_fr.rstrip() + tail if new_fr.strip() else ""
