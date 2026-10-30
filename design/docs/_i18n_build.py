"""Shared helpers for the French PDF builds (docs/oer/build_oer.py --lang fr,
docs/build_course_books.py --lang fr).

Anchor mapping: French headings slugify to French ids, but every in-book link
(index, TOC, cross-references) targets the ENGLISH slug. The French book is
structurally 1:1 with the English one (parity-checked by i18n/mdparity.py), so
the build renders both and gives the n-th French heading the id of the n-th
English heading.
"""
from __future__ import annotations

import re

_HEAD_RE = re.compile(r'<h([1-6])\b([^>]*?)\sid="([^"]*)"')


def heading_ids(html_text: str) -> list[str]:
    return [m.group(3) for m in _HEAD_RE.finditer(html_text)]


def remap_heading_ids(fr_html: str, en_ids: list[str], label: str = "") -> str:
    fr_ids = heading_ids(fr_html)
    if len(fr_ids) != len(en_ids):
        raise SystemExit(
            f"{label}: heading count differs (FR {len(fr_ids)} vs EN {len(en_ids)}); "
            "run i18n/mdparity.py on the sources — anchor mapping needs a 1:1 structure")
    it = iter(en_ids)
    return _HEAD_RE.sub(lambda m: f'<h{m.group(1)}{m.group(2)} id="{next(it)}"', fr_html)


def broken_links(html_text: str) -> list[str]:
    ids = set(re.findall(r'\sid="([^"]*)"', html_text))
    hrefs = re.findall(r'href="#([^"]*)"', html_text)
    return [h for h in hrefs if h not in ids]

