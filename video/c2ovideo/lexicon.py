"""Pronunciation lexicon: what the narrator says for identifiers and acronyms.

Captions keep the written form ("Send HK_REQUEST, SID 1"); only the text sent to
the speech engine is rewritten. Identifiers stay English in both languages
(Franz's bilingual ruling), so the French narrator says them the way a French
operator would read them aloud.

``video/lexicon/<lang>.yaml``::

    terms:              # whole-word replacements, case-sensitive
      LEOP: "lee op"
    spell: [AOCS, TTC]  # read letter by letter in that language
    rules:              # regexes applied after terms (Python re, \\1 groups)
      - ['([A-Z]{3})-(\\d)(\\d)(\\d)', '\\1 \\2 \\3 \\4']
"""

from __future__ import annotations

import re
from functools import lru_cache

import yaml

from .storyboard import ROOT

LETTERS = {
    "en": {c: c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
    "fr": {"A": "A", "B": "B", "C": "C", "D": "D", "E": "E", "F": "F", "G": "G", "H": "H", "I": "I",
           "J": "J", "K": "K", "L": "L", "M": "M", "N": "N", "O": "O", "P": "P", "Q": "Q", "R": "R",
           "S": "S", "T": "T", "U": "U", "V": "V", "W": "W", "X": "X", "Y": "Y", "Z": "Z"},
}
DIGITS = {
    "en": ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"],
    "fr": ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf"],
}


@lru_cache(maxsize=None)
def load(lang: str) -> dict:
    f = ROOT / "lexicon" / f"{lang}.yaml"
    data = yaml.safe_load(f.read_text(encoding="utf-8")) if f.exists() else {}
    return data or {}


def spell(token: str, lang: str) -> str:
    out = []
    for ch in token:
        if ch.isdigit():
            out.append(DIGITS[lang][int(ch)])
        elif ch.isalpha():
            # no full stops after French letters: the French voice drops an "E."
            # ("E. P. S." came out as "P S"); "E P S" is read as letters
            out.append(LETTERS[lang].get(ch.upper(), ch))
        else:
            out.append(" ")
    return " ".join(x for x in out if x.strip())


def spoken(text: str, lang: str) -> str:
    """Rewrite ``text`` for the speech engine."""
    lex = load(lang)
    s = text
    # snake_case identifiers: read the words ("bus_voltage" -> "bus voltage")
    s = re.sub(r"\b[A-Za-z0-9]+(?:_[A-Za-z0-9]+)+\b", lambda m: m.group(0).replace("_", " "), s)
    for pat, rep in lex.get("rules") or []:
        s = re.sub(pat, lambda m, rep=rep: _expand(m, rep, lang), s)
    for term, say in sorted((lex.get("terms") or {}).items(), key=lambda kv: -len(kv[0])):
        s = re.sub(rf"(?<![\w.]){re.escape(term)}(?![\w])", say, s)
    for tok in lex.get("spell") or []:
        s = re.sub(rf"(?<![\w.]){re.escape(tok)}(?![\w])", spell(tok, lang), s)
    # remaining all-capitals words of 4+ letters are words, not acronyms
    keep = set(lex.get("words") or [])
    s = re.sub(r"(?<![\w.])[A-Z]{4,}(?![\w])", lambda m: m.group(0) if m.group(0) in keep else m.group(0).lower(), s)
    return re.sub(r"\s+", " ", s).strip()


def _expand(m: re.Match, rep: str, lang: str) -> str:
    out = m.expand(rep)
    # {spell:XYZ} and {digits:123} helpers inside rule replacements
    out = re.sub(r"\{spell:([^}]*)\}", lambda x: spell(x.group(1), lang), out)
    out = re.sub(r"\{digits:([^}]*)\}", lambda x: " ".join(DIGITS[lang][int(d)] for d in x.group(1) if d.isdigit()), out)
    return out


def unknown_tokens(text: str, lang: str) -> list[str]:
    """Capitalised tokens still left after the lexicon (listed on the review sheet).

    A token the lexicon does not cover is read however the engine guesses, so
    the reviewer listens to these first.
    """
    words = set(load(lang).get("words") or [])
    left = re.findall(r"(?<![\w.])[A-Z][A-Z0-9]+(?![\w])", spoken(text, lang))
    return sorted({t for t in left if t not in words and not t.isdigit()})
