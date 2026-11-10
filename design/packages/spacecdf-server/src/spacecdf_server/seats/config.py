"""Seat definitions and team-size presets (configs/seats.yaml).

Pure functions over the YAML: which seats exist, which seats a study uses, and which seat
owns an element (and so its parameters).
"""
from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import yaml

EDITING_KINDS = ("lead", "systems", "domain")
GATE_SEATS = ("team_leader",)          # + the instructor: gate review actions, gate profile


def _file() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "configs" / "seats.yaml"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("configs/seats.yaml not found")


@functools.lru_cache(maxsize=1)
def load() -> dict[str, Any]:
    data = yaml.safe_load(_file().read_text(encoding="utf-8")) or {}
    errs = validate(data)
    if errs:
        raise ValueError("configs/seats.yaml: " + "; ".join(errs))
    return data


def validate(data: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    ids = [s.get("id") for s in data.get("seats") or []]
    if len(ids) != len(set(ids)):
        errs.append("duplicate seat ids")
    for s in data.get("seats") or []:
        lab = s.get("label") or {}
        if not lab.get("en") or not lab.get("fr"):
            errs.append(f"{s.get('id')}: label needs en and fr")
        if s.get("kind") not in (*EDITING_KINDS, "customer", "observer", "instructor"):
            errs.append(f"{s.get('id')}: bad kind {s.get('kind')!r}")
        if s.get("fallback") and s["fallback"] not in ids:
            errs.append(f"{s.get('id')}: unknown fallback {s['fallback']}")
    for p in data.get("presets") or []:
        for g in p.get("groups") or []:
            for sid in g:
                if sid not in ids:
                    errs.append(f"preset {p.get('id')}: unknown seat {sid}")
    return errs


def seats() -> list[dict[str, Any]]:
    return list(load().get("seats") or [])


def seat(seat_id: str) -> dict[str, Any] | None:
    return next((s for s in seats() if s["id"] == seat_id), None)


def seat_ids() -> list[str]:
    return [s["id"] for s in seats()]


def label(seat_id: str) -> dict[str, str]:
    s = seat(seat_id)
    return dict((s or {}).get("label") or {"en": seat_id, "fr": seat_id})


def kind(seat_id: str) -> str:
    return (seat(seat_id) or {}).get("kind", "")


def is_exclusive(seat_id: str) -> bool:
    return bool((seat(seat_id) or {}).get("exclusive", True))


def timing() -> dict[str, float]:
    t = load().get("timing") or {}
    return {"idle_after_s": float(t.get("idle_after_s", 180)),
            "reclaimable_after_s": float(t.get("reclaimable_after_s", 300)),
            "handover_timeout_s": float(t.get("handover_timeout_s", 60))}


def layout_fields() -> set[str]:
    return set(load().get("layout_fields") or [])


def presets() -> list[dict[str, Any]]:
    return list(load().get("presets") or [])


def preset_ids() -> list[str]:
    return [str(p["id"]) for p in presets()]


def preset_for_size(team_size: int | str | None) -> str | None:
    """4 → "4", 5-6 → "6", 7+ → "9"; None/0 → no seats (solo study)."""
    if team_size in (None, "", 0, "0", "solo"):
        return None
    if str(team_size) in preset_ids():
        return str(team_size)
    n = int(team_size)
    if n <= 4:
        return "4"
    if n <= 6:
        return "6"
    return "9"


def groups_for(preset_id: str, optional: list[str] | None = None) -> list[list[str]]:
    """The seat groups of a preset, with the enabled optional seats added."""
    p = next((p for p in presets() if str(p["id"]) == str(preset_id)), None)
    if p is None:
        raise ValueError(f"unknown seat preset {preset_id!r}")
    groups = [list(g) for g in p.get("groups") or []]
    for sid in optional or []:
        s = seat(sid)
        if not s or not s.get("optional"):
            continue
        if any(sid in g for g in groups):
            continue
        if str(preset_id) == "9":
            groups.append([sid])
        else:
            fb = s.get("fallback")
            target = next((g for g in groups if fb in g), None)
            (target if target is not None else groups[-1]).append(sid)
    return groups


def study_seats(groups: list[list[str]]) -> list[str]:
    """Seats used by a study: the preset's seats + Customer, Observer (always available)."""
    out = [sid for g in groups for sid in g]
    return out + [sid for sid in ("customer", "observer") if sid not in out]


# ─── ownership ──────────────────────────────────────────────────────────────

def _domain_index() -> dict[str, str]:
    idx: dict[str, str] = {}
    for s in seats():
        for d in ((s.get("owns") or {}).get("element_domains") or []):
            idx.setdefault(str(d).lower(), s["id"])
    return idx


def _prefix_index() -> dict[str, str]:
    idx: dict[str, str] = {}
    for s in seats():
        for p in ((s.get("owns") or {}).get("prefixes") or []):
            idx.setdefault(str(p).lower(), s["id"])
    return idx


def seat_for_domain(domain: str | None) -> str | None:
    if not domain:
        return None
    return _domain_index().get(str(domain).lower())


def seat_for_param_key(key: str) -> str | None:
    """``power.battery_capacity_wh`` → power_engineer (by prefix)."""
    prefix = (key or "").split(".", 1)[0].lower()
    return _prefix_index().get(prefix)


def owner_prefix(seat_id: str) -> str:
    s = seat(seat_id) or {}
    pre = (s.get("owns") or {}).get("prefixes") or [seat_id]
    return str(pre[0])


#: Words that mark a disposal (deorbit) device: a drag sail, a deorbit / drag device, a
#: disposal timer. The KB files these under ``structure``; the PI decision (Nov 2026) gives them
#: to the Propulsion seat (the disposal function).
_DISPOSAL_WORDS = ("drag sail", "deorbit", "de-orbit", "drag device", "disposal")


def is_disposal_device(element: dict[str, Any]) -> bool:
    """A drag sail or another deorbit device (by KB id, class, domain or name)."""
    kb = str(element.get("kb_component_id") or "").lower()
    perf = element.get("performance") if isinstance(element.get("performance"), dict) else {}
    cls = str(perf.get("component_class") or perf.get("class") or "").lower()
    dom = str(element.get("subsystem_domain") or "").lower()
    name = str(element.get("name") or "").lower()
    return (kb.startswith(("deorb-", "deorbit")) or cls in ("deorbit_device", "drag_sail", "deorbit_timer")
            or dom in ("disposal", "deorbit") or any(w in name for w in _DISPOSAL_WORDS))


def element_owner_seat(element: dict[str, Any], elements: dict[str, dict[str, Any]]) -> str | None:
    """The seat that owns an element: its subsystem_domain, else the nearest ancestor's;
    a mission root → Team leader, a segment/system without a domain → Systems. A disposal device
    (drag sail, deorbit device) and its subtree belong to Propulsion (PI decision, Nov 2026)."""
    seen: set[str] = set()
    probe: dict[str, Any] | None = element
    while probe is not None and probe.get("id") not in seen:
        seen.add(probe.get("id", ""))
        if (probe.get("element_type") or "").lower() in ("component", "subsystem", "assembly", "equipment") \
                and is_disposal_device(probe):
            return "propulsion_engineer"
        pid = probe.get("parent_id")
        probe = elements.get(pid) if pid else None
    seen = set()
    el: dict[str, Any] | None = element
    while el is not None and el.get("id") not in seen:
        seen.add(el.get("id", ""))
        sid = seat_for_domain(el.get("subsystem_domain"))
        if sid:
            return sid
        et = (el.get("element_type") or "").lower()
        for s in seats():
            if et and et in ((s.get("owns") or {}).get("element_types") or []):
                return s["id"]
        pid = el.get("parent_id")
        el = elements.get(pid) if pid else None
    return None


def resolve_in_study(seat_id: str | None, used: list[str]) -> str | None:
    """A seat the study does not use hands its ownership to its fallback (then Systems)."""
    hops = 0
    while seat_id and seat_id not in used and hops < 5:
        seat_id = (seat(seat_id) or {}).get("fallback") or ("systems_engineer" if seat_id != "systems_engineer" else None)
        hops += 1
    return seat_id if seat_id in used else None


def public() -> dict[str, Any]:
    """The seat catalogue for the frontend."""
    return {
        "seats": [{k: s.get(k) for k in ("id", "label", "kind", "exclusive", "optional", "fallback",
                                         "sees_first", "tabs", "kb_position")}
                  | {"prefixes": list((s.get("owns") or {}).get("prefixes") or [])}
                  for s in seats()],
        "presets": [{"id": str(p["id"]), "label": p.get("label"), "groups": p.get("groups")} for p in presets()],
        "timing": timing(),
    }
