"""The interface object as the API serves it (Nov 2026 contract).

One place that turns any stored or incoming interface dict into the
canonical shape::

    {id, study_id, name, type, interface_type, subtype, direction,
     from_element_id, to_element_id, properties, exchange_item_ids_json,
     origin: "user" | "import" | "rule:<rule_id>",
     status: "suggested" | "accepted" | "rejected",
     rationale: {en, fr} | None, standard_ref: str | None,
     criticality, diagram_label, version, deleted_at}

``type`` and ``interface_type`` always carry the same canonical value
(``interface_type`` is the stored column and stays for older readers).
"""
from __future__ import annotations

from typing import Any

from spacecdf_common.models.interface_types import (
    INTERFACE_STATUSES,
    canonical_interface_type,
)

ORIGINS_FIXED = ("user", "import")


def canonical_status(raw: Any) -> str:
    """``defined``/``identified``/``agreed``/``verified`` (older values) count as accepted."""
    s = str(raw or "").strip().lower()
    return s if s in INTERFACE_STATUSES else "accepted"


def valid_origin(raw: Any) -> bool:
    return isinstance(raw, str) and (raw in ORIGINS_FIXED or (raw.startswith("rule:") and len(raw) > 5))


def normalise_rationale(raw: Any) -> dict[str, str] | None:
    if not raw:
        return None
    if isinstance(raw, str):
        return {"en": raw, "fr": raw}
    if isinstance(raw, dict):
        en = raw.get("en") or ""
        fr = raw.get("fr") or en
        return {"en": en or fr, "fr": fr} if (en or fr) else None
    return None


def normalise_interface(d: dict) -> dict:
    """Bring a stored/legacy interface dict to the canonical API shape (in place, returned)."""
    raw_type = d.get("interface_type") or d.get("type")
    canon = canonical_interface_type(raw_type) or "data"
    d["interface_type"] = canon
    d["type"] = canon
    if "rationale_json" in d and "rationale" not in d:
        d["rationale"] = d.pop("rationale_json")
    else:
        d.pop("rationale_json", None)
    d["rationale"] = normalise_rationale(d.get("rationale"))
    d.setdefault("standard_ref", None)
    d.setdefault("subtype", None)
    if not isinstance(d.get("properties"), dict):
        d["properties"] = {}
    origin = d.get("origin")
    d["origin"] = origin if valid_origin(origin) else "user"
    d["status"] = canonical_status(d.get("status"))
    d.setdefault("direction", "bidirectional")
    d.setdefault("criticality", "standard")
    d.setdefault("diagram_label", "")
    return d


def rule_id_of(iface: dict) -> str | None:
    o = iface.get("origin") or ""
    return o[5:] if o.startswith("rule:") else None


def is_active(iface: dict) -> bool:
    """Counts in analyses, budgets, exports and readiness (suggested links do; rejected do not)."""
    return not iface.get("deleted_at") and iface.get("status") != "rejected"
