"""Hashing, slugs, identifier/number/placeholder extraction shared by all modules."""
from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import Counter

from .mdparity import numbers as _numbers

_WS = re.compile(r"[ \t\r\n\f\v]+")


def normalise(text: str, en: bool = False) -> str:
    """Whitespace-normalised text. NBSP/NNBSP fold to space on the EN side only
    (on the FR side they are meaningful typography)."""
    t = unicodedata.normalize("NFC", text or "")
    if en:
        t = t.replace(" ", " ").replace(" ", " ")
    return _WS.sub(" ", t).strip()


def text_hash(text: str, en: bool = False) -> str:
    return hashlib.sha256(normalise(text, en).encode("utf-8")).hexdigest()[:16]


def slugify(s: str) -> str:
    s = re.sub(r"\{[:#][^}]*\}\s*$", "", s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"[`*_~\[\]()]", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "section"


# Mnemonic-like tokens (R2: identifiers stay English)
IDENT_RE = re.compile(r"(?<![\w-])[A-Z][A-Z0-9_]{2,}(?![\w])")


def identifiers(text: str, strong_only: bool = True) -> set[str]:
    """Strong identifiers contain a digit or underscore (AOCS_SET_MODE, RW3, S15, GNG1103).
    Pure capitals (AOCS, SAFE) may be legitimately rendered (SCAO), so they are weak."""
    toks = set(IDENT_RE.findall(text or ""))
    strong = {t for t in toks if re.search(r"[\d_]", t)}
    return strong if strong_only else toks - strong


def number_counter(text: str) -> Counter:
    t = re.sub(r"\{\{[^}]*\}\}|`[^`]*`|<[^>]*>|https?://\S+", " ", text or "")
    return _numbers(t)


PLACEHOLDER_RE = re.compile(r"\{\{\s*-?\s*([\w.$]+)\s*(?:,[^}]*)?\}\}")
NEST_RE = re.compile(r"\$t\(([^)]*)\)")
TAG_RE = re.compile(r"</?(?:\d+|[a-zA-Z][\w-]*)\s*/?>")


def placeholders(text: str) -> Counter:
    t = text or ""
    c = Counter("{{%s}}" % m for m in PLACEHOLDER_RE.findall(t))
    c.update("$t(%s)" % m for m in NEST_RE.findall(t))
    c.update(TAG_RE.findall(t))
    return c


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-zÀ-ÿ0-9]+(?:['’-][A-Za-zÀ-ÿ0-9]+)*", text or ""))
