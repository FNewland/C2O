"""Legacy functional-decomposition JSON -> FunctionRow / FunctionAllocationRow (SCDF-160 §1.1).

``study.functional_decomposition.functions[]`` (``spacecdf_common.models.functions.Function``)
carries ``allocated_to`` as a *domain string* ("power", "link", ...). This
service turns every legacy function into a persisted SA-layer ``FunctionRow``
and its allocation into a ``FunctionAllocationRow`` pointing at the study's
subsystem element whose ``subsystem_domain`` matches
``element_projection.DOMAIN_SUBSYSTEM_MAP[allocated_to]`` (or ``allocated_to``
itself when it is already a subsystem domain or an element id).

Idempotent: the legacy id is stored in ``external_ids_json['legacy']`` and a
re-run updates the existing rows instead of duplicating them.
"""
from __future__ import annotations

import logging
from typing import Any

from ..db import function_repo
from .element_projection import DOMAIN_SUBSYSTEM_MAP

logger = logging.getLogger(__name__)

LEGACY_KEY = "legacy"


def _find_target_element(allocated_to: str, study_id: str, elements_by_id: dict[str, dict]) -> str | None:
    """Resolve a legacy ``allocated_to`` value to an element id in this study."""
    if not allocated_to:
        return None
    # 1. It is already an element id
    el = elements_by_id.get(allocated_to)
    if el and not el.get("deleted_at") and el.get("study_id", study_id) == study_id:
        return allocated_to
    # 2. Agent domain -> subsystem domain (or already a subsystem domain)
    target_domain = DOMAIN_SUBSYSTEM_MAP.get(allocated_to, allocated_to)
    candidates = [
        e for e in elements_by_id.values()
        if e.get("element_type") == "subsystem"
        and e.get("subsystem_domain") == target_domain
        and not e.get("deleted_at")
        and e.get("study_id", study_id) == study_id
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda e: (e.get("created_at") or "", e.get("id") or ""))
    return candidates[0]["id"]


def _function_payload(study_id: str, f: dict) -> dict:
    return {
        "study_id": study_id,
        "name": f.get("name") or f.get("id") or "Unnamed function",
        "description": f.get("description") or "",
        "layer": "SA",
        "function_type": (
            f["function_type"].value if hasattr(f.get("function_type"), "value") else f.get("function_type")
        ),
        "level": int(f.get("level") or 0),
        "is_leaf": bool(f.get("is_leaf", False)),
        "position_responsible": f.get("position_responsible") or None,
        "external_ids": {LEGACY_KEY: f.get("id")},
    }


async def migrate_study_functions(
    study_id: str,
    functions: list[dict[str, Any]],
    elements_by_id: dict[str, dict],
) -> dict[str, int]:
    """Import legacy functions into rows. Returns counts.

    ``functions`` are ``Function.model_dump()`` dicts (or equivalent).
    ``elements_by_id`` is the element cache (``routers.elements._elements``)
    or any ``{id: element_dict}`` mapping.
    """
    counts = {
        "functions_created": 0, "functions_updated": 0, "parents_linked": 0,
        "allocations": 0, "unallocated": 0, "skipped": 0,
    }
    functions = [f for f in functions if f.get("id")]
    if not functions:
        return counts

    # Existing rows keyed by legacy id
    existing = await function_repo.load_all_functions(study_id)
    by_legacy: dict[str, dict] = {}
    for row in existing.values():
        legacy = (row.get("external_ids") or {}).get(LEGACY_KEY)
        if legacy:
            by_legacy[legacy] = row

    # Pass 1: upsert functions (parents resolved in pass 2)
    legacy_to_row_id: dict[str, str] = {}
    for f in functions:
        legacy_id = f["id"]
        payload = _function_payload(study_id, f)
        try:
            if legacy_id in by_legacy:
                row = by_legacy[legacy_id]
                row = await function_repo.update_function(row["id"], payload)
                counts["functions_updated"] += 1
            else:
                row = await function_repo.create_function(payload)
                counts["functions_created"] += 1
        except Exception:
            logger.exception("migrate_study_functions: failed on legacy function %s", legacy_id)
            counts["skipped"] += 1
            continue
        legacy_to_row_id[legacy_id] = row["id"]

    # Pass 2: parents
    for f in functions:
        parent_legacy = f.get("parent_function_id")
        row_id = legacy_to_row_id.get(f["id"])
        if not row_id:
            continue
        parent_row_id = legacy_to_row_id.get(parent_legacy) if parent_legacy else None
        if parent_legacy and not parent_row_id:
            logger.warning("Legacy parent %s of %s not found; leaving root", parent_legacy, f["id"])
        current = by_legacy.get(f["id"], {}).get("parent_id")
        if current != parent_row_id:
            await function_repo.update_function(row_id, {"parent_id": parent_row_id})
        if parent_row_id:
            counts["parents_linked"] += 1

    # Pass 3: allocations (unique per function+layer, so upsert is idempotent)
    for f in functions:
        row_id = legacy_to_row_id.get(f["id"])
        if not row_id:
            continue
        allocated_to = f.get("allocated_to") or ""
        element_id = _find_target_element(allocated_to, study_id, elements_by_id)
        if element_id:
            await function_repo.allocate_function(study_id, row_id, element_id, layer="SA")
            counts["allocations"] += 1
        else:
            if allocated_to:
                logger.info("No subsystem element for allocated_to=%r (function %s)", allocated_to, f["id"])
            await function_repo.unallocate_function(row_id, layer="SA")
            counts["unallocated"] += 1

    logger.info("migrate_study_functions(%s): %s", study_id, counts)
    return counts


async def get_functions(study_id: str, legacy_functions: list[dict] | None = None) -> list[dict]:
    """Rows are the truth; fall back to the legacy JSON list when no rows exist.

    Intended for ``lifecycle.py`` call sites that currently read
    ``study.functional_decomposition.functions``.
    """
    rows = await function_repo.list_functions_by_study(study_id)
    if rows:
        return rows
    return list(legacy_functions or [])
