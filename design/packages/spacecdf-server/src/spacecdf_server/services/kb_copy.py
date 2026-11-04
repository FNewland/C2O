"""SpaceCDF — the one place a KB part's facts are copied onto a design element (F4, D12).

Before Nov 2026 ``routers/elements._lookup_kb_component`` copied name, mass, power, cost,
TRL, manufacturer, part number and performance only, so the stack builder, the 3D view,
the thermal analysis and the exports had to re-read the KB for dimensions, form factor,
bus interfaces and operating temperatures. ``kb_element_fields`` returns every field the
element keeps from its part, including ``kb_spec`` (stored in ``design_elements.kb_spec_json``):

    kb_spec = {category, form_factor, interfaces[], operating_temp_c[min,max],
               survival_temp_c?, dimensions_mm?, frequency_band?, kb_id, kb_hash, copied_at}

``kb_hash`` is a digest of the part record: when the KB entry changes later, the element
is marked stale (rule 13, ``staleness``) until someone re-applies the part.

Other workers (electrical: bus interfaces → ports/buses; stack builder: dimensions and form
factor → placement) read ``element["kb_spec"]``; keep additions in this module.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

#: Top-level KB keys copied into ``kb_spec`` (when present on the part).
SPEC_KEYS: tuple[str, ...] = (
    "category", "form_factor", "interfaces", "operating_temp_c", "survival_temp_c",
    "dimensions_mm", "frequency_band", "deployment", "power_modes_w",
)


def kb_dir() -> Path:
    return Path(__file__).resolve().parents[3].parent / "spacecdf-kb" / "src" / "spacecdf_kb" / "data" / "components"


def find_kb_part(kb_id: str) -> dict | None:
    """The raw KB record with ``id`` (or ``name``) == ``kb_id``, read fresh from the YAML files."""
    import yaml
    d = kb_dir()
    if not kb_id or not d.exists():
        return None
    for f in sorted(d.glob("*.yaml")):
        try:
            with open(f, encoding="utf-8") as fp:
                data = yaml.safe_load(fp) or {}
        except Exception:  # noqa: BLE001 — a broken file must not hide the others
            continue
        for c in data.get("components", []) or []:
            if isinstance(c, dict) and (c.get("id") == kb_id or c.get("name") == kb_id):
                return c
    return None


def kb_hash(part: dict) -> str:
    """Stable 16-hex digest of a KB record (keys sorted; notes ignored)."""
    clean = {k: v for k, v in part.items() if k not in ("notes",)}
    raw = json.dumps(clean, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _dims(v: Any) -> list[float] | None:
    if isinstance(v, (list, tuple)) and len(v) == 3:
        try:
            return [float(x) for x in v]
        except (TypeError, ValueError):
            return None
    return None


def kb_element_fields(part: dict) -> dict[str, Any]:
    """Element fields taken from a KB part (None values are left out by the caller)."""
    perf = part.get("performance") if isinstance(part.get("performance"), dict) else None
    spec: dict[str, Any] = {k: part[k] for k in SPEC_KEYS if part.get(k) is not None}
    if "operating_temp_c" not in spec and perf and isinstance(perf.get("operating_temp_c"), (list, tuple)):
        spec["operating_temp_c"] = list(perf["operating_temp_c"])
    if "dimensions_mm" in spec:
        spec["dimensions_mm"] = _dims(spec["dimensions_mm"]) or spec["dimensions_mm"]
    spec.update({"kb_id": part.get("id"), "kb_hash": kb_hash(part),
                 "copied_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "stale": False})
    heritage = part.get("heritage_missions")
    return {
        "name": part.get("name"),
        "mass_kg": part.get("mass_kg"),
        "power_avg_w": part.get("power_w") or part.get("power_avg_w"),
        "power_peak_w": part.get("power_peak_w"),
        "cost_recurring_keur": part.get("cost_keur"),
        "trl": part.get("trl"),
        "manufacturer": part.get("manufacturer"),
        "part_number": part.get("part_number", part.get("id")),
        "performance": perf,
        "category": part.get("category"),
        "dimensions_mm": _dims(part.get("dimensions_mm")),
        "heritage_json": list(heritage) if isinstance(heritage, (list, tuple)) and heritage else None,
        "kb_spec": spec,
    }


def apply_to_element(element: dict, part: dict, *, overwrite: bool = False) -> list[str]:
    """Copy the part's fields onto ``element`` in place; returns the keys written.

    Without ``overwrite`` only empty fields are filled (create from a KB part), except
    ``kb_spec`` which always follows the part.
    """
    written = []
    for k, v in kb_element_fields(part).items():
        if v is None:
            continue
        if k == "kb_spec" or overwrite or element.get(k) is None:
            element[k] = v
            written.append(k)
    return written


def staleness(elements: Iterable[dict], lookup: Callable[[str], dict | None] | None = None) -> list[dict]:
    """Rule 13: elements whose KB part changed (or vanished) since it was copied.

    Returns one row per stale element: ``{element_id, name, kb_component_id, reason,
    copied_hash, current_hash, changed: [fields]}``. Elements without a stored hash (created
    before Nov 2026) are reported with reason ``never_copied`` so the user can re-apply once.
    """
    lookup = lookup or (lambda k: globals()["find_kb_part"](k))
    out = []
    for e in elements:
        kid = e.get("kb_component_id")
        if not kid or e.get("deleted_at"):
            continue
        spec = e.get("kb_spec") or {}
        part = lookup(str(kid))
        row = {"element_id": e.get("id"), "name": e.get("name"), "kb_component_id": kid,
               "copied_hash": spec.get("kb_hash"), "current_hash": None, "changed": []}
        if part is None:
            out.append({**row, "reason": "kb_part_missing"})
            continue
        cur = kb_hash(part)
        row["current_hash"] = cur
        if not spec.get("kb_hash"):
            out.append({**row, "reason": "never_copied"})
        elif spec.get("kb_hash") != cur:
            fresh = kb_element_fields(part)
            changed = [k for k in ("mass_kg", "power_avg_w", "power_peak_w", "trl", "cost_recurring_keur",
                                   "dimensions_mm") if fresh.get(k) is not None and fresh.get(k) != e.get(k)]
            changed += [f"kb_spec.{k}" for k in SPEC_KEYS
                        if (fresh["kb_spec"].get(k) != spec.get(k)) and (k in fresh["kb_spec"] or k in spec)]
            out.append({**row, "reason": "kb_changed", "changed": changed})
    return out
