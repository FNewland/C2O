"""Which mission documents a student or operator may read.

One rule for every student- and operator-facing server that lists the
Markdown under ``configs/eosat1`` (the documentation viewer, the MCS MAN
and PRC pages), so a document hidden on one cannot be read on another
(SCREEN_REVIEW #7):

* a document whose header block carries ``**Manual-Scope:** system`` is
  training-system documentation (installation guides, software
  architecture, the RF simulation layer, the development change log): it
  is not part of the operations manual and is not served;
* ``mcs/role_analysis/`` holds design analyses of the positions, not
  operator material;
* a retired procedure card ("(RETIRED)" or "(retired" in its title) is not
  listed beside the live ones (its file stays readable for old links).

The documents stay on disk and in the instructor's copy of the repository.
"""
from __future__ import annotations

import re
from pathlib import Path

__all__ = ["SYSTEM_SCOPE_MARK", "HIDDEN_PREFIXES", "doc_title",
           "is_system_doc", "is_retired", "is_student_doc"]

SYSTEM_SCOPE_MARK = "**Manual-Scope:** system"
#: configs-relative prefixes never served to students or operators
HIDDEN_PREFIXES = ("mcs/role_analysis/", "i18n/")
_HEAD_BYTES = 1200
_ANCHOR = re.compile(r"\s*\{#[A-Za-z0-9_][\w.:-]*(?:\s[^}]*)?\}\s*$")


def _head(path: Path) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read(_HEAD_BYTES)
    except OSError:
        return ""


def doc_title(path: Path) -> str:
    """The document's first ``#`` heading without its ``{#id}`` anchor;
    the file stem in sentence case when there is none."""
    for line in _head(path).splitlines():
        m = re.match(r"^#\s+(.*)", line.strip())
        if m:
            return _ANCHOR.sub("", m.group(1)).strip()
    stem = re.sub(r"^\d+[_-]", "", path.stem).replace("_", " ")
    return stem[:1].upper() + stem[1:]


def is_system_doc(path: Path) -> bool:
    return SYSTEM_SCOPE_MARK in _head(path)


def is_retired(path: Path) -> bool:
    title = doc_title(path)
    return "(RETIRED" in title.upper()


def is_student_doc(path: Path, rel: str) -> bool:
    """True when the document at ``path`` (``rel`` relative to the config
    root) may be listed on a student- or operator-facing page."""
    rp = rel.replace("\\", "/").lstrip("/")
    if any(rp.startswith(p) for p in HIDDEN_PREFIXES):
        return False
    return not is_system_doc(path) and not is_retired(path)
