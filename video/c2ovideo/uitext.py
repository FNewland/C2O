"""Translate English UI strings to the French the tool actually shows.

Storyboards name buttons and tabs in English (``{role: button, name: "Create
New Mission"}``). For the French take the runner looks the string up in the
tool's own catalogue, so a storyboard never repeats a translation and a
catalogue change is picked up on the next render.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from .storyboard import REPO

SIM = REPO / "sim"
CATALOGS = {
    "spacecdf": [REPO / "design/frontend/src/i18n/locales"],
    "mcs": [SIM / "packages/smo-mcs/src/smo_mcs/static/modern/i18n/fr.json",
            SIM / "packages/smo-common/src/smo_common/ui/i18n/fr.json"],
    "planner": [SIM / "packages/smo-planner/src/smo_planner/static/modern/i18n/fr.json",
                SIM / "packages/smo-common/src/smo_common/ui/i18n/fr.json"],
    "instructor": [SIM / "packages/smo-simulator/src/smo_simulator/instructor/static/modern/i18n/fr.json",
                   SIM / "packages/smo-common/src/smo_common/ui/i18n/fr.json"],
    "tools": [SIM / "packages/smo-common/src/smo_common/ui/i18n/tools/fr.json",
              SIM / "packages/smo-common/src/smo_common/ui/i18n/fr.json"],
    "docs": [SIM / "packages/smo-common/src/smo_common/ui/i18n/tools/fr.json",
             SIM / "packages/smo-common/src/smo_common/ui/i18n/fr.json"],
    "portal": [SIM / "packages/smo-common/src/smo_common/ui/i18n/tools/fr.json",
               SIM / "packages/smo-common/src/smo_common/ui/i18n/fr.json"],
}


class MissingTranslation(KeyError):
    pass


@lru_cache(maxsize=None)
def catalog(app: str) -> dict:
    out: dict = {}
    for src in CATALOGS.get(app, []):
        files = sorted(src.glob("fr*.json")) if src.is_dir() else [src]
        for f in files:
            if f.exists():
                for k, v in json.loads(f.read_text(encoding="utf-8")).items():
                    out.setdefault(k, v)
    return out


def ui(app: str, text, lang: str) -> str:
    """The on-screen string for ``text`` in ``lang``.

    ``text`` may be a plain English string (looked up), or ``{en, fr}`` given
    explicitly when the catalogue key differs from what is displayed.
    """
    if isinstance(text, dict):
        return text.get(lang) or text["en"]
    if lang == "en":
        return text
    cat = catalog(app)
    if text in cat:
        return cat[text]
    # interpolated catalogue keys: "Stakeholder {{n}}: role" matches "Stakeholder 2: role"
    for key, val in _patterns(app):
        m = key.fullmatch(text)
        if m:
            return re.sub(r"\{\{\s*(\w+)\s*\}\}", lambda x: m.group(x.group(1)), val)
    raise MissingTranslation(f"{app}: no French for {text!r} in the catalogue; give {{en, fr}} in the storyboard")


@lru_cache(maxsize=None)
def _patterns(app: str) -> list:
    out = []
    for k, v in catalog(app).items():
        if "{{" in k and isinstance(v, str):
            parts = re.split(r"(\{\{\s*\w+\s*\}\})", k)
            rx = "".join(f"(?P<{re.sub(r'[^\w]', '', p)}>.+?)" if p.startswith("{{") else re.escape(p) for p in parts)
            literal = len(re.sub(r"\{\{\s*\w+\s*\}\}", "", k).strip(" :·—-()"))
            if literal < 4:             # "{{name}}" alone would match any string
                continue
            try:
                out.append((len(re.sub(r"\{\{\s*\w+\s*\}\}", "", k)), re.compile(rx), v))
            except re.error:
                pass
    # most literal text first, so "Stakeholder {{n}}: role" wins over "{{a}}: {{b}}"
    return [(rx, v) for _, rx, v in sorted(out, key=lambda x: -x[0])]
