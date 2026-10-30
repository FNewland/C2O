"""Language switch for the textbook figures (English default, French on demand).

    FIG_LANG=fr python3 fig_gsd.py     # writes fig_gsd_fr.png beside fig_gsd.png
    python3 make_all.py --lang fr      # every figure, French
    python3 make_all.py --lang all     # English then French

How it works: `oer_style.apply_style()` calls `install()`. In French mode every
matplotlib Text (titles, labels, ticks, legends, annotations, table cells) is
passed through `tr()` as it is set, so the generators keep their English source
strings and need no per-string edits. `tr()` looks the exact English string up
in `i18n_fr_strings.py` (per-figure table first, then the shared one) and, for
bare numeric tick labels, applies the French decimal comma and thousands
grouping. A string with letters and no translation is kept in English and
reported on stderr ("FR-MISSING"), so a changed figure cannot silently ship
half-translated.

In English mode nothing is patched: the English PNGs are byte-identical to the
output before this module existed.

FIG_HARVEST=<dir> (English mode) writes <dir>/<figure>.json with every string
the figure sets — the source list for the translation tables.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

LANG = os.environ.get("FIG_LANG", "en").strip().lower() or "en"
FR = LANG == "fr"
SUFFIX = "_fr" if FR else ""
HARVEST = os.environ.get("FIG_HARVEST")

NBSP = " "
NNBSP = " "

_installed = False
_seen: list[str] = []
_missing: list[str] = []


def figure_name() -> str:
    f = sys.argv[0] if sys.argv and sys.argv[0] else ""
    return Path(f).stem if f.endswith(".py") else "unknown"


def _tables():
    from i18n_fr_strings import COMMON, PER_FIGURE
    return PER_FIGURE.get(figure_name(), {}), COMMON


_NUM = re.compile(r"^([−+\-]?)(\d+)(?:\.(\d+))?$")
_MATHNUM = re.compile(r"^\$\\mathdefault\{([−\-]?\d+)\.(\d+)\}\$$")


def french_number(s: str) -> str | None:
    """'0.5' -> '0,5', '27500' -> '27 500' (NNBSP), '-1.5' -> '−1,5'. None if not a number."""
    m = _NUM.match(s)
    if m:
        sign, ip, fp = m.groups()
        sign = "−" if sign in ("-", "−") else sign
        if len(ip) >= 5:
            ip = f"{int(ip):,}".replace(",", NNBSP)
        return sign + ip + ("," + fp if fp else "")
    m = _MATHNUM.match(s)
    if m:
        return f"$\\mathdefault{{{m.group(1)}{{,}}{m.group(2)}}}$"
    return None


# Unit symbols (and a few short tokens) that are the same in French: a string made only
# of numbers, these, symbols and acronyms needs no table entry (decimal comma applied).
_UNITS = ("dBi dBW dBHz dBm dB km cm mm µm nm m kg g kW W V K °C % s h min mN N GHz MHz kHz Hz "
          "kbit/s Mbit/s bit/s Go Mo ko k€ M€ € kEUR krad mbar A sin cos max min log m/s km/s kg/m W/m m/A").split()
_UNIT_RE = "|".join(re.escape(u) for u in sorted(_UNITS, key=len, reverse=True))
_NBSP_UNIT = re.compile(r"(?<=\d) (?=(?:" + _UNIT_RE + r"|cycles?|jours?|ans?|mois|sem\.|semaines?|"
                        r"orbites?|tirages|passages?|roues?|quarts?|h/j)(?![A-Za-zÀ-ÿ]))")
_THOUS = re.compile(r"(?<![\d,.])(\d{1,3}) (\d{3})(?![\d,])")


def _math_comma(m: str) -> str:
    """Decimal comma inside mathtext ('0.98' -> '0{,}98'); figures are for reading (STYLE_FR §4.1)."""
    return re.sub(r"(?<=\d)\.(?=\d)", "{,}", m)


def _outside_math(s: str, fn) -> str:
    parts = re.split(r"(\$[^$]*\$)", s)
    return "".join(_math_comma(p) if p.startswith("$") and p.endswith("$") and len(p) > 1 else fn(p)
                   for p in parts)


def _typo(seg: str) -> str:
    seg = seg.replace("kEUR", "k€")
    seg = re.sub(r"\bGB\b", "Go", seg)
    seg = re.sub(r"\bMB\b", "Mo", seg)
    seg = _THOUS.sub(lambda m: m.group(1) + NNBSP + m.group(2), seg)
    seg = _NBSP_UNIT.sub(NBSP, seg)
    seg = re.sub(r" ([;!?])", NNBSP + r"\1", seg)
    seg = re.sub(r" :(?=\s|$)", NBSP + ":", seg)
    seg = seg.replace("« ", "«" + NNBSP).replace(" »", NNBSP + "»")
    return seg


def _needs_words(s: str) -> bool:
    plain = re.sub(r"\$[^$]*\$", "", s)
    for tok in re.findall(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ/]+", plain):
        if any(c.islower() for c in tok) and tok not in _UNITS:
            return True
    return False


def tr(s: str) -> str:
    """Translate one rendered string (French mode)."""
    return tr_scaled(s)[0]


def tr_scaled(s: str) -> tuple[str, float]:
    """(French text, font-size factor). A table value may be a plain string or
    (string, factor) when the French needs a slightly smaller font to fit a box."""
    if not s or not FR:
        return s, 1.0
    per, common = _tables()
    for table in (per, common):
        if s in table:
            v = table[s]
            text, scale = (v, 1.0) if isinstance(v, str) else v
            return _outside_math(text, _typo), scale
    return _tr_auto(s), 1.0


def _tr_auto(s: str) -> str:
    n = french_number(s)
    if n is not None:
        return n
    if _needs_words(s):
        if s not in _missing:
            _missing.append(s)
        return s
    # numbers, units, symbols and acronyms only: French number format
    def _num(seg):
        seg = re.sub(r"(?<![\w.])-(?=\d)", "−", seg)
        seg = re.sub(r"(?<=\d)\.(?=\d)", ",", seg)
        return _typo(seg)
    return _outside_math(s, _num)


def install() -> None:
    """Patch matplotlib Text in French / harvest mode. No-op in plain English mode."""
    global _installed
    if _installed or not (FR or HARVEST):
        return
    _installed = True
    from matplotlib.text import Text

    orig = Text.set_text

    def set_text(self, s):
        orig(self, s)
        txt = self._text
        if HARVEST and txt and txt not in _seen:
            _seen.append(txt)
        if FR:
            self._text, self._fr_scale = tr_scaled(txt)

    Text.set_text = set_text

    if FR:
        # font-size factor from the table, applied once at first layout (after the
        # generator's own fontsize= kwargs have been set)
        orig_layout = Text._get_layout

        def _get_layout(self, renderer):
            sc = getattr(self, "_fr_scale", 1.0)
            if sc != 1.0 and not getattr(self, "_fr_scaled", False):
                self._fr_scaled = True
                self.set_fontsize(self.get_fontsize() * sc)
            return orig_layout(self, renderer)

        Text._get_layout = _get_layout

    import atexit
    atexit.register(_report)


def _report() -> None:
    if HARVEST:
        d = Path(HARVEST)
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{figure_name()}.json").write_text(
            json.dumps(_seen, ensure_ascii=False, indent=1), encoding="utf-8")
    if FR and _missing:
        for s in _missing:
            print(f"FR-MISSING {figure_name()}: {s!r}", file=sys.stderr)
