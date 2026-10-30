#!/usr/bin/env python3
"""mdparity — structural parity check between an English Markdown text and its French translation.

Usage (stand-alone):  python3 -m tools.i18n.mdparity EN.md FR.md [--quiet]
Exit 0 = parity OK, 1 = problems (listed).

Checks (everything that must survive translation unchanged):
  * heading sequence: same count and same levels, same {#id}/{: attr} suffixes
  * fenced code blocks: byte-identical content (comments included — translate prose, not code)
  * display math ($$...$$, \\[...\\]) identical; inline $...$ multiset identical
    (\\text{...} contents are allowed to differ)
  * inline `code` spans multiset identical (mnemonics, parameter IDs, file names)
  * link / image targets multiset identical
  * Markdown attribute blocks {: ...} and HTML comments multiset identical
  * tables: same number of tables and same row/column shape
  * numbers: every number in EN appears in FR
    (decimal comma accepted: 3,5 == 3.5; NBSP/NNBSP thousands accepted)

compare(en_text, fr_text, headings=True) returns the list of problems; the i18n
tool calls it per aligned section with headings=False (alignment checks levels).
"""
from __future__ import annotations

import re
import sys
from collections import Counter

FENCE = re.compile(r'^(```|~~~)')


def split_blocks(text):
    lines = text.split('\n'); prose = []; fences = []; buf = None
    for l in lines:
        if FENCE.match(l.strip()):
            if buf is None:
                buf = [l]
            else:
                buf.append(l); fences.append('\n'.join(buf)); buf = None; prose.append('\x00FENCE\x00')
            continue
        if buf is not None:
            buf.append(l)
        else:
            prose.append(l)
    if buf is not None:
        fences.append('\n'.join(buf))
    return '\n'.join(prose), fences


def strip_text_cmd(m):
    return re.sub(r'\\(text|mathrm|textrm|mbox)\{[^{}]*\}', r'\\\1{}', m)


def norm_num(s, en=False):
    """Digits only: separators (. , space, NBSP, NNBSP) are locale formatting.
    3.5 == 3,5 ; 10,000 == 10 000 ; RS(255,223) == RS(255,223)."""
    return re.sub(r'[^0-9]', '', s).lstrip('0') or '0'

NUM_RE = re.compile(r'(?<![\w.,])\d{1,3}(?:,\d{3}){2,}(?:\.\d+)?|(?<![\w.,])\d{1,3}(?:[\u202f\u00a0 ]\d{3})+(?:[.,]\d+)?|(?<![\w])\d+(?:[.,]\d+)?')


def numbers(text):
    return Counter(norm_num(n) for n in NUM_RE.findall(text))



def _inline_math(prose):
    """Pandoc-like left-to-right pairing of single $...$ per line.
    Returns (list of math contents, prose with math blanked).
    A pair whose content starts with a digit and has no TeX syntax is currency ($30K), not maths."""
    out_lines, maths = [], []
    for line in prose.split('\n'):
        pos = [i for i, c in enumerate(line) if c == '$' and (i == 0 or line[i-1] != '\\')]
        spans, i = [], 0
        while i < len(pos) - 1:
            a, b = pos[i], pos[i+1]
            c = line[a+1:b]
            ok = bool(c) and not c[0].isspace() and not c[-1].isspace() and not (b + 1 < len(line) and line[b+1].isdigit())
            if ok and c[0].isdigit() and not re.search(r'[\\^_{}=]', c):
                ok = False
            if ok:
                spans.append((a, b)); i += 2
            else:
                i += 1
        for a, b in reversed(spans):
            maths.append(line[a+1:b]); line = line[:a] + ' ' + line[b+1:]
        out_lines.append(line)
    return maths, '\n'.join(out_lines)



PROSE_FENCE_INFO = {'', 'text', 'txt', 'plain', 'none'}
_ID_RE = re.compile(r'\b(?:[A-Z][A-Z0-9_]{2,}|0x[0-9A-Fa-f]+|[a-z_]+\.[a-z0-9_.]+)\b|\d+(?:[.,]\d+)?')


def fence_ok(en_f, fr_f):
    """Code fences must be byte-identical, except plain-text fences (no language, or text/txt/plain):
    those carry teaching prose (function trees, requirement lists, ASCII diagrams) and may be translated
    provided the fence line, line count and every identifier/number survive."""
    if en_f == fr_f:
        return True
    el, fl = en_f.split('\n'), fr_f.split('\n')
    info = el[0].strip().lstrip('`~').strip().lower()
    if info not in PROSE_FENCE_INFO or el[0] != fl[0] or len(el) != len(fl):
        return False
    norm = lambda t: Counter(re.sub(r'[^0-9A-Za-z_.x]', '', m).replace(',', '.') for m in _ID_RE.findall(t))
    return norm(en_f) == norm(fr_f)


def analyse(text, en=False):
    prose, fences = split_blocks(text)
    r = {}
    r['fences'] = fences
    heads = []
    for l in prose.split('\n'):
        m = re.match(r'^(#{1,6})\s+(.*)$', l)
        if m:
            suffix = re.findall(r'\{[:#][^}]*\}\s*$', m.group(2))
            heads.append((len(m.group(1)), suffix[0] if suffix else ''))
    r['headings'] = heads
    dm = re.findall(r'\$\$.*?\$\$|\\\[.*?\\\]', prose, re.S)
    r['display_math'] = Counter(strip_text_cmd(x) for x in dm)
    p2 = re.sub(r'\$\$.*?\$\$|\\\[.*?\\\]', ' ', prose, flags=re.S)
    im, p2m = _inline_math(p2)
    r['inline_math'] = Counter(strip_text_cmd(x) for x in im)
    r['code'] = Counter(re.findall(r'`([^`\n]+)`', p2))
    r['links'] = Counter(re.findall(r'\]\(([^)\s]+)', p2))
    r['attrs'] = Counter(re.findall(r'\{:[^}]*\}', p2))
    r['comments'] = Counter(re.findall(r'<!--.*?-->', p2, re.S))
    tables = []; cur = None
    for l in prose.split('\n'):
        if l.strip().startswith('|'):
            cols = len(re.findall(r'(?<!\\)\|', l.strip())) - 1
            if cur is None:
                cur = []
            cur.append(cols)
        elif cur is not None:
            tables.append(tuple(cur)); cur = None
    if cur is not None:
        tables.append(tuple(cur))
    r['tables'] = tables
    p3 = re.sub(r'`[^`\n]+`|\]\([^)]*\)|<!--.*?-->|\{[:#][^}]*\}', ' ', p2m, flags=re.S)
    r['numbers'] = numbers(p3)
    return r


def diff_counter(name, a, b, out, limit=8):
    if a != b:
        miss = list((a - b).elements())[:limit]; extra = list((b - a).elements())[:limit]
        out.append(f"{name}: missing in FR {miss!r}  extra in FR {extra!r}")


def compare(en: str, fr: str, headings: bool = True) -> list[str]:
    A, B = analyse(en, True), analyse(fr)
    out: list[str] = []
    if headings:
        ea = [h[0] for h in A['headings']]; fa = [h[0] for h in B['headings']]
        if ea != fa:
            out.append(f"headings: EN {len(ea)} vs FR {len(fa)} (levels differ)")
            for i, (x, y) in enumerate(zip(ea, fa)):
                if x != y:
                    out.append(f"  first level mismatch at heading #{i+1}: EN h{x} FR h{y}"); break
    if [h[1] for h in A['headings']] != [h[1] for h in B['headings']]:
        out.append("headings: {#id}/{: attr} suffixes differ")
    if len(A['fences']) != len(B['fences']) or not all(fence_ok(x, y) for x, y in zip(A['fences'], B['fences'])):
        n = sum(1 for x, y in zip(A['fences'], B['fences']) if not fence_ok(x, y))
        out.append(f"code fences: EN {len(A['fences'])} FR {len(B['fences'])}, {n} differ in content")
    for k in ('display_math', 'inline_math', 'code', 'links', 'attrs', 'comments'):
        diff_counter(k, A[k], B[k], out)
    if A['tables'] != B['tables']:
        out.append(f"tables: EN {len(A['tables'])} FR {len(B['tables'])} (shape differs)")
    diff_counter('numbers', A['numbers'], B['numbers'], out)
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    args = [a for a in argv if not a.startswith('--')]
    en, fr = (open(p, encoding='utf-8').read() for p in args[:2])
    out = compare(en, fr)
    if out:
        print(f"PARITY FAIL {args[1]}"); print('\n'.join('  ' + o for o in out)); return 1
    if '--quiet' not in argv:
        print(f"PARITY OK {args[1]}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
