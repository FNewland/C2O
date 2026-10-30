"""Markdown doc pairs: status, check, accept/init, backport."""
from __future__ import annotations

import difflib
import os
import re
from dataclasses import dataclass

from . import gitutil, mdparity
from .config import Config, DocPair
from .mdsync import Alignment, align, build_state, levels, load_state, save_state, segment
from .textutil import identifiers, word_count

ATTENTION = ("stale", "missing", "conflict", "orphan", "untracked", "fr-edited")


def read(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return f.read()


@dataclass
class DocState:
    pair: DocPair
    en_text: str
    fr_text: str | None
    state: dict | None
    al: Alignment

    @property
    def file_status(self) -> str:
        if self.fr_text is None:
            return "missing"
        bad = [k for k in ATTENTION if self.al.counts.get(k)]
        if not bad and not self.al.structure_changed:
            return "ok"
        return "structure changed" if self.al.structure_changed else bad[0]


def analyse(pair: DocPair) -> DocState:
    en = read(pair.en) or ""
    fr = read(pair.fr)
    st = load_state(pair.fr)
    al = align(segment(en), segment(fr) if fr is not None else None, st)
    return DocState(pair, en, fr, st, al)


def section_problems(en_sec, fr_sec) -> list[str]:
    out = mdparity.compare(en_sec.text, fr_sec.text, headings=False)
    miss = identifiers(_strip_code(en_sec.text)) - identifiers(_strip_code(fr_sec.text))
    if miss:
        out.append(f"identifiers: missing in FR {sorted(miss)[:8]!r}")
    return out


def _strip_code(t: str) -> str:   # code is compared byte-exact by mdparity already
    return re.sub(r"```.*?```|~~~.*?~~~|`[^`\n]+`", " ", t, flags=re.S)


def check_doc(cfg: Config, ds: DocState, strict: bool) -> tuple[list[str], list[str]]:
    errs, warns = [], []
    name = cfg.rel(ds.pair.fr)
    if ds.fr_text is None:
        warns.append(f"{cfg.rel(ds.pair.en)}: no FR file ({len(ds.al.pairs)} sections to translate)")
        return (warns, []) if strict else ([], warns)
    if ds.al.structure_changed:
        warns.append(f"{name}: {ds.al.note}")
    waivers = set((ds.state or {}).get("waivers") or [])
    for p in ds.al.pairs:
        sid = p.en.id if p.en else (p.rec or {}).get("id", f"fr#{p.fr.idx}")
        if p.status in ("ok", "fr-edited", "untracked", "stale", "conflict"):
            for prob in section_problems(p.en, p.fr):
                msg = f"{name} [{sid}] {prob}"
                if p.status in ("stale", "conflict") or ds.pair.legacy or f"{sid}: {prob}" in waivers:
                    warns.append(msg)
                else:
                    errs.append(msg)
            for rx in ds.pair.forbid_fr:
                m = re.search(rx, p.fr.text, flags=re.I)
                if m:
                    errs.append(f"{name} [{sid}] forbidden FR wording {m.group(0)!r} (pattern {rx!r})")
    for k in ATTENTION:
        n = ds.al.counts.get(k)
        if n:
            hint = {"untracked": " (run: i18n accept --init)", "fr-edited": " (review, then i18n accept / backport)",
                    "stale": " (i18n translate --stale)", "missing": " (i18n translate --stale)"}.get(k, "")
            warns.append(f"{name}: {n} section(s) {k}{hint}")
    if strict:
        errs += warns
        warns = []
    return errs, warns


def accept(cfg: Config, ds: DocState, init: bool = False, waive: bool = False,
           section: str | None = None) -> str:
    if ds.fr_text is None:
        return "skip (no FR file)"
    if init and ds.state is not None:
        return "skip (already tracked)"
    if not section and ds.al.structure_changed:
        # Whole-file accept after headings were renamed/moved in BOTH languages: if EN and FR
        # mirror each other structurally, re-pair them by position and drop stale ids.
        en_secs, fr_secs = segment(ds.en_text), segment(ds.fr_text)
        if levels(en_secs) == levels(fr_secs):
            ds.al = align(en_secs, fr_secs, None)
    aligned = [p for p in ds.al.pairs if p.en is not None and p.fr is not None]
    if section:
        ids = {p.en.id for p in aligned if p.en.id == section}
        if not ids:
            return f"skip (no aligned section {section!r})"
    else:
        ids = {p.en.id for p in aligned}
    st = build_state(cfg.ref(ds.pair.en), ds.al, ds.state, ids, gitutil.head(ds.pair.en))
    if waive:
        w = set(st.get("waivers") or [])
        for p in aligned:
            if p.en.id in ids:
                w.update(f"{p.en.id}: {prob}" for prob in section_problems(p.en, p.fr))
        st["waivers"] = sorted(w)
    save_state(ds.pair.fr, st)
    unaligned = len(ds.al.pairs) - len(aligned)
    return f"accepted {len(ids)} section(s)" + (f", {unaligned} unaligned left as missing/orphan" if unaligned else "")


def old_en_section(ds: DocState, sec_id: str, want_hash: str | None) -> str | None:
    """English text of a section as it was at the last sync (from git), if recoverable."""
    if not want_hash:
        return None
    revs = [r for r in ((ds.state or {}).get("en_commit"), "HEAD") if r]
    for rev in revs:
        txt = gitutil.show(rev, ds.pair.en)
        if txt is None:
            continue
        for s in segment(txt):
            if s.id == sec_id and s.hash(en=True) == want_hash:
                return s.text
        for s in segment(txt):   # heading renamed: match by hash alone
            if s.hash(en=True) == want_hash:
                return s.text
    return None


def backport(cfg: Config, ds: DocState) -> list[str]:
    out = []
    edited = [p for p in ds.al.pairs if p.status in ("fr-edited", "conflict")]
    if not edited:
        return out
    old_fr = gitutil.show("HEAD", ds.pair.fr)
    old_secs = segment(old_fr) if old_fr else []
    for p in edited:
        prev = next((s.text for s in old_secs if p.rec and s.hash(en=False) == p.rec.get("fr_hash")), None)
        out.append(f"=== {cfg.rel(ds.pair.fr)} [{p.en.id}] ({p.status})")
        if prev is not None:
            out += [l.rstrip("\n") for l in difflib.unified_diff(
                prev.splitlines(True), p.fr.text.splitlines(True), "fr@sync", "fr@now", n=1)]
        else:
            out.append("(synced FR not recoverable from git; current FR shown)")
            out += ["+ " + l for l in p.fr.text.rstrip().splitlines()]
        out.append("--- EN (current):")
        out += ["  " + l for l in p.en.text.rstrip().splitlines()]
    return out


def words(ds: DocState) -> int:
    return word_count(ds.en_text)
