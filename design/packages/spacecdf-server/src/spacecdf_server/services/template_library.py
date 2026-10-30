"""SpaceCDF — Template library service.

Loads MissionTemplate YAMLs from configs/templates/ at startup and caches them
in-memory. Exposes a synchronous lookup API for the templates router.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import ValidationError

from spacecdf_common.models.template import MissionTemplate

logger = logging.getLogger(__name__)


def _templates_dir() -> Path:
    """Locate configs/templates relative to the repo root.

    Walks up from this file until it finds a `configs/templates` directory.
    """
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        candidate = parent / "configs" / "templates"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("configs/templates directory not found")


@lru_cache(maxsize=1)
def _load_all() -> dict[str, MissionTemplate]:
    """Scan the templates dir once and return {id: MissionTemplate}."""
    out: dict[str, MissionTemplate] = {}
    try:
        tdir = _templates_dir()
    except FileNotFoundError:
        logger.warning("Template library: configs/templates not found; no templates loaded")
        return out

    for yml in sorted(tdir.glob("*.yaml")):
        try:
            data = yaml.safe_load(yml.read_text())
            tmpl = MissionTemplate(**data)
        except (ValidationError, yaml.YAMLError, OSError) as exc:
            logger.warning("Template %s failed to load: %s", yml.name, exc)
            continue
        if tmpl.id in out:
            logger.warning("Duplicate template id %s in %s; keeping first", tmpl.id, yml.name)
            continue
        out[tmpl.id] = tmpl

    logger.info("Template library: loaded %d templates from %s", len(out), tdir)
    return out


def list_templates() -> list[MissionTemplate]:
    """Return all templates, sorted by id."""
    return sorted(_load_all().values(), key=lambda t: t.id)


def get_template(template_id: str) -> MissionTemplate | None:
    """Lookup a single template by id."""
    return _load_all().get(template_id)


def reload_templates() -> int:
    """Force re-read of YAMLs (useful for dev / tests). Returns count."""
    _load_all.cache_clear()
    return len(_load_all())
