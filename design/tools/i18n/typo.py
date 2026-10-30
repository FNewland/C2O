"""French (France) typography fixer.

Inserts U+202F (narrow no-break space) before ; ! ? and inside « », and U+00A0
before :, replacing any plain or wrong space already there. Never touches:
YAML front matter, fenced code, inline code, display/inline math, URLs and link
targets, HTML comments and tags, Markdown attribute blocks, link reference
definitions, {{placeholders}}, and the English procedure annotation keys the
SMO parser reads (**TC:**, **Verify:** …, STYLE_FR §13).
"""
from __future__ import annotations

import re

NNBSP = " "
NBSP = " "

_PROTECT_INLINE = [
    r"<!--.*?-->",                                   # HTML comments
    r"`+[^`\n]*?`+",                                 # inline code
    r"\$\$.*?\$\$",                                  # display math
    r"\\\[.*?\\\]", r"\\\(.*?\\\)",                  # LaTeX display / inline
    r"(?<![\\$])\$(?!\s)[^$\n]+?(?<!\s)\$(?!\d)",     # inline $math$
    r"\]\([^)\n]*\)",                                # link / image targets
    r"<[A-Za-z/!][^>\n]*>",                          # HTML tags, autolinks
    r"\b(?:https?|ftp|mailto|file):[^\s)>\]]+",      # bare URLs
    r"\bwww\.[^\s)>\]]+",
    r"\{[:#][^}\n]*\}",                              # attribute blocks
    r"\{\{[^}\n]*\}\}",                              # i18next placeholders
    r"\*\*(?:TC|Verify|LABEL|BRANCH|GO/NO-GO|Action|Note):\*\*",  # SMO parser keys
    r"\$t\([^)\n]*\)",
    r"&[a-zA-Z]+;|&#\d+;",                           # HTML entities
]
_PROTECT_RE = re.compile("|".join(f"(?:{p})" for p in _PROTECT_INLINE), re.S)
_FENCE_RE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")
_REFDEF_RE = re.compile(r"^\s{0,3}\[[^\]]+\]:\s")
_SP = "[   \t]"

_RULES = [
    # « guillemets »
    (re.compile(r"«" + _SP + r"*"), "«" + NNBSP),
    (re.compile(_SP + r"*»"), NNBSP + "»"),
    # ; ! ?  (only when followed by space/end/closing punctuation, not "?!"-runs' second char)
    (re.compile(r"(?<=[^\s:;!?(\[«\-|])" + _SP + r"?([;!?]+)(?=[\s»)\]*_\"'’]|$)"), NNBSP + r"\1"),
    # :  (not ::, not 12:30, not URL schemes — those are protected)
    (re.compile(r"(?<=[^\s:;!?(\[«\-|])" + _SP + r"?:(?=[\s»)\]*_]|$)"), NBSP + ":"),
]


def _fix_inline(text: str) -> str:
    stash: list[str] = []

    def keep(m):
        stash.append(m.group(0))
        return f"{len(stash) - 1}"

    t = _PROTECT_RE.sub(keep, text)
    for rx, rep in _RULES:
        t = rx.sub(rep, t)
    return re.sub(r"(\d+)", lambda m: stash[int(m.group(1))], t)


def fix(text: str, markdown: bool = True) -> str:
    """Return text with French spacing applied outside protected regions."""
    if not markdown:
        return _fix_inline(text)
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    buf: list[str] = []
    fence = None
    i = 0
    # front matter
    if lines and lines[0].strip() == "---":
        j = 1
        while j < len(lines) and lines[j].strip() not in ("---", "..."):
            j += 1
        if j < len(lines):
            out.extend(lines[: j + 1])
            i = j + 1

    def flush():
        if buf:
            out.append(_fix_inline("".join(buf)))
            buf.clear()

    for line in lines[i:]:
        m = _FENCE_RE.match(line)
        if fence:
            out.append(line)
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not line.strip()[len(m.group(1)):].strip():
                fence = None
            continue
        if m:
            flush()
            fence = m.group(1)
            out.append(line)
            continue
        if _REFDEF_RE.match(line):
            flush()
            out.append(line)
            continue
        buf.append(line)
    flush()
    return "".join(out)


def fix_file(path, write: bool = False) -> tuple[int, str]:
    with open(path, encoding="utf-8") as f:
        src = f.read()
    md = not str(path).endswith((".json", ".txt"))
    new = fix(src, markdown=md)
    changed = sum(1 for a, b in zip(src.splitlines(), new.splitlines()) if a != b)
    if write and new != src:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new)
    return changed, new
