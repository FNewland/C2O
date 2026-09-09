"""Shared mutation-broadcast helper for the SCDF-160 arcadia routers.

``routers/elements.py`` announces mutations by pushing ``{"type": ...}``
messages to the study WebSocket via ``ws._broadcast_study``. The arcadia
routers (functions / exchange items / relations) do the same through this
helper so the wire format stays uniform:

    {"type": "function_created", "target_kind": "function",
     "target_id": "fn-…", "study_id": "…", "payload": {...}}

``ChangeKind`` (spacecdf_common.models.change_event) is a closed ``str``
enum and is owned by the spine/parameters work, so no new kinds are added
here; the entity type travels in ``target_kind`` instead.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def broadcast_mutation(
    study_id: str | None,
    event_type: str,
    target_kind: str,
    target_id: str,
    payload: Any = None,
) -> None:
    """Fire-and-forget broadcast; never raises into the request."""
    if not study_id:
        return
    try:
        from .ws import _broadcast_study
        await _broadcast_study(study_id, {
            "type": event_type,
            "target_kind": target_kind,
            "target_id": target_id,
            "study_id": study_id,
            "payload": payload,
        })
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Broadcast %s failed: %s", event_type, exc)
