"""SMO Common — server-side UI-language helpers (EN/FR, i18n packet S0).

The language is a property of each BROWSER (``?lang=`` > localStorage >
server default > ``en``, resolved client-side by ``ui/i18n.js``). The
servers only contribute:

* a **default** for browsers that have not chosen: ``SMO_LANG`` env >
  ``mission.yaml: ui_lang`` > ``"en"`` (:func:`server_default_lang`), handed
  to the page as ``<html data-default-lang="fr">`` when the modern index is
  served (:func:`inject_default_lang`; English pages are served unchanged);
* the **localised Markdown** for display endpoints that take an additive
  ``?lang=`` (:func:`resolve_lang`, :func:`localized_md_path`).

API traffic stays English and ID-based. Nothing here may be used on an
execution path: the procedure RUNNER always reads the English procedure.
No aiohttp import — ``request_or_query`` is duck-typed.
"""
from __future__ import annotations

import logging
import os
import re
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)

SUPPORTED_LANGS: tuple[str, ...] = ("en", "fr")
DEFAULT_LANG = "en"
# Markdown trees that have a translated twin under <config>/i18n/<lang>/.
LOCALIZED_TREES: tuple[str, ...] = ("procedures", "manual")


def normalize_lang(value) -> str | None:
    """``"fr-CA"`` -> ``"fr"``; unsupported or empty -> ``None``."""
    if value is None:
        return None
    primary = re.split(r"[-_]", str(value).strip().lower(), maxsplit=1)[0]
    return primary if primary in SUPPORTED_LANGS else None


def resolve_lang(request_or_query=None, default: str | None = DEFAULT_LANG) -> str:
    """The ``lang`` query parameter if supported, else ``default`` (else en).

    Accepts an aiohttp request (anything with ``.query``), a mapping, or a
    raw query string (``"lang=fr&x=1"`` / ``"?lang=fr"``).
    """
    raw = None
    src = request_or_query
    # .query first: an aiohttp Request is ITSELF a MutableMapping (per-request
    # storage), so a Mapping check alone would read the wrong dict.
    if src is not None and not isinstance(src, (str, bytes, dict)) \
            and hasattr(src, "query"):
        src = src.query
    if isinstance(src, bytes):
        src = src.decode("utf-8", "replace")
    if isinstance(src, str):
        vals = parse_qs(src.lstrip("?")).get("lang")
        raw = vals[0] if vals else None
    elif isinstance(src, Mapping):
        raw = src.get("lang")
    return normalize_lang(raw) or normalize_lang(default) or DEFAULT_LANG


def server_default_lang(cli: str | None = None, mission_lang: str | None = None) -> str:
    """House precedence (mirrors SMO_UI): CLI > ``SMO_LANG`` env >
    ``mission.yaml: ui_lang`` > ``"en"``. Unknown values warn and fall back."""
    for source, value in (("cli", cli), ("SMO_LANG", os.environ.get("SMO_LANG")),
                          ("mission.yaml ui_lang", mission_lang)):
        if value is None or str(value).strip() == "":
            continue
        lang = normalize_lang(value)
        if lang:
            return lang
        logger.warning("Unsupported UI language %r from %s — using %s",
                       value, source, DEFAULT_LANG)
        return DEFAULT_LANG
    return DEFAULT_LANG


def mission_ui_lang(config_dir) -> str | None:
    """``ui_lang`` from mission.yaml, or None (absent/unreadable config)."""
    try:
        from smo_common.config.loader import load_mission_config
        return load_mission_config(Path(config_dir)).ui_lang
    except Exception:  # noqa: BLE001 — a default must never block start-up
        return None


_HTML_TAG = re.compile(r"<html\b", re.IGNORECASE)


def inject_default_lang(html: str, lang: str | None) -> str:
    """Add ``data-default-lang`` to the ``<html>`` tag. English (or an
    unsupported value) returns ``html`` UNCHANGED, byte for byte."""
    lang = normalize_lang(lang)
    if not lang or lang == DEFAULT_LANG or "data-default-lang" in html:
        return html
    return _HTML_TAG.sub(f'<html data-default-lang="{lang}"', html, count=1)


def localized_md_path(en_path, lang: str | None, config_dir=None) -> Path:
    """Map an English Markdown path to its translation, if it exists.

    ``<cfg>/procedures/X.md`` -> ``<cfg>/i18n/<lang>/procedures/X.md`` and
    ``<cfg>/manual/X.md`` -> ``<cfg>/i18n/<lang>/manual/X.md``. Falls back to
    ``en_path`` for English, an unsupported language, a path outside those
    trees, or a missing translation. The translations live OUTSIDE
    ``procedures/`` on purpose: the MCS loads ``procedures/**/*.md``
    recursively.
    """
    en = Path(en_path)
    lang = normalize_lang(lang)
    if not lang or lang == DEFAULT_LANG:
        return en
    parts = en.parts
    root = Path(config_dir).resolve() if config_dir is not None else None
    for i in range(len(parts) - 1, -1, -1):
        if parts[i] not in LOCALIZED_TREES:
            continue
        cfg = Path(*parts[:i]) if i else Path(".")
        if root is not None and cfg.resolve() != root:
            continue
        candidate = cfg / "i18n" / lang / Path(*parts[i:])
        try:
            if candidate.is_file() and candidate.resolve().is_relative_to(
                    (cfg / "i18n" / lang).resolve()):
                return candidate
        except OSError:
            pass
        return en
    return en
