""""Who is affected": the impact preview of a proposed change (wave 3, 3.L6; negotiation #3).

A proposed change is evaluated as a **dry run**: the study's analysis context is loaded once,
copied, the change is applied to the copy in memory, and the key numbers
(``services/key_numbers.numbers_from_context``) are computed before and after on the same code
path. Nothing is written to the database or to the element caches, so a preview can be opened,
discussed and dropped. The Δ of every key that moved is listed with the seat that owns it, and the
seats are grouped so each one sees what the change asks of it.

Change kinds (``body["change"]``, or the body itself):

* ``{"kind": "station", "action": "add", "name", "lat", "lon", "min_elevation_deg"?, "bands"?,
  "antenna_m"?}`` — a ground station added (the fourth-site ripple scene);
  ``{"kind": "station", "action": "remove", "name" | "element_id"}`` — one taken out;
* ``{"kind": "mode_share", "mode": <id | name | template key | kind>, "share_pct"}`` — a mode's share
  of the operational orbit; the difference is taken from (or given to) the nominal mode;
* ``{"kind": "mode_member", "mode", "element_id", "power_w"}`` — one unit's power in one mode;
* ``{"kind": "element", "element_id", "changes": {field: value}}`` — element fields (mass_kg,
  power_avg_w, quantity, performance keys); ``{"kind": "pending_change", "id"}`` reads a seat's
  pending change (``element_fields`` and ``element_param``) and previews it the same way;
* ``{"kind": "orbit", "altitude_km"?, "inclination_deg"?}`` — the mission orbit;
* ``{"kind": "allocation", "element_id", "resource": "mass" | "power", "value"}`` — a proposed
  allocation: the element's rolled-up value against it (margin), owner and Systems listed.

Several changes are previewed together with ``{"changes": [...]}`` (a change record's impact
specs, ``POST /changes/{id}/preview``). An element may be named by ``element`` (a unique name, a
name fragment, or a subsystem domain such as ``payload``) instead of ``element_id``.

``station`` changes also re-propose the downlink share from the union contact time (union ÷ 1440,
3.H3's rule) and apply its Δ to the energy balance (``ripple`` in the result), so the chain
(contacts → capacity → share → power → the Communications allocation) shows in one preview.
"""
from __future__ import annotations

import copy
import logging
from typing import Any

logger = logging.getLogger(__name__)

KINDS = ("station", "mode_share", "mode_member", "element", "pending_change", "orbit", "allocation")

#: relative / absolute thresholds under which a Δ is "no change"
_EPS_ABS = 1e-6

#: seats in the order the preview lists them
SEAT_ORDER = ("team_leader", "systems_engineer", "mission_analyst", "payload_lead", "power_engineer", "aocs_engineer",
              "comms_engineer", "thermal_engineer", "structures_engineer", "propulsion_engineer", "cost_engineer",
              "customer")


class PreviewError(ValueError):
    pass


def _num(v: Any) -> float | None:
    if isinstance(v, bool) or v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _copy_ctx(ctx):
    """A deep copy of the context (the study model and every list), so nothing leaks back."""
    c = copy.copy(ctx)
    for k in ("elements", "interfaces", "modes", "ground_stations", "link_cases", "requirements", "relations",
              "orbit", "power", "flat", "params", "latest_design", "thermal", "link"):
        setattr(c, k, copy.deepcopy(getattr(ctx, k)))
    st = ctx.study
    if st is not None:
        c.study = st.model_copy(deep=True) if hasattr(st, "model_copy") else copy.deepcopy(st)
    c.warnings = list(ctx.warnings)
    return c


# ───────────────────────────────────────────────────────────── appliers

def _find_mode(ctx, ref: Any):
    from ..routers.modes import _element_modes
    ms = _element_modes(ctx)
    r = str(ref or "")
    for m in ms:
        if m.id == r:
            return m
    for m in ms:
        if (m.name or "").lower() == r.lower():
            return m
    key = {m.id: (next((e for e in ctx.elements if e["id"] == m.id), {}).get("performance") or {}).get("template_key")
           for m in ms}
    for m in ms:
        if key.get(m.id) == r:
            return m
    hits = [m for m in ms if m.kind == r]
    if len(hits) == 1:
        return hits[0]
    raise PreviewError(f"unknown mode: {ref!r}")


def _set_share(ctx, mode, share: float, *, rebalance_kind: str = "nominal") -> dict:
    """Set ``mode``'s orbit fraction; the difference comes from the mode of ``rebalance_kind``."""
    from ..routers.modes import _element_modes
    old = float(mode.orbit_fraction or 0.0)
    share = max(0.0, min(1.0, share))
    d = share - old
    bg = next((m for m in _element_modes(ctx) if m.kind == rebalance_kind and m is not mode), None)
    mode.orbit_fraction = share
    if bg is not None and abs(d) > 0:
        bg.orbit_fraction = max(0.0, float(bg.orbit_fraction or 0.0) - d)
    for m in (mode, bg):
        if m is None:
            continue
        el = next((e for e in ctx.elements if e["id"] == m.id), None)
        if el is not None:
            el["performance"] = {**(el.get("performance") or {}), "orbit_fraction": m.orbit_fraction}
    return {"mode": mode.name, "from_pct": round(100 * old, 2), "to_pct": round(100 * share, 2),
            "rebalanced_with": bg.name if bg is not None else None}


def _station(ctx, ch: dict) -> dict:
    from .analysis_context import _select_stations
    action = (ch.get("action") or "add").lower()
    if action == "add":
        lat, lon = _num(ch.get("lat")), _num(ch.get("lon"))
        if lat is None or lon is None:
            raise PreviewError("a station needs lat and lon")
        name = str(ch.get("name") or "New station")
        perf = {"lat": lat, "lon": lon, "min_elevation_deg": _num(ch.get("min_elevation_deg")) or 10.0}
        for k in ("antenna_m", "alt_m", "g_over_t_db_k"):
            if _num(ch.get(k)) is not None:
                perf[k] = _num(ch.get(k))
        bands = ch.get("bands")
        if not bands:
            # the bands the study's other stations carry (a station of the same network)
            bands = next((s.get("bands") for s in ctx.ground_stations if s.get("bands")), None)
        if bands:
            perf["bands"] = list(bands)
        parent = next((e["id"] for e in ctx.elements if e.get("element_type") == "segment" and e.get("segment") == "ground"), None)
        ctx.elements.append({"id": "preview-station", "study_id": ctx.study_id, "name": name, "element_type": "system",
                             "segment": "ground", "subsystem_domain": "ground", "parent_id": parent, "performance": perf})
        ctx.ground_stations = _select_stations(ctx.elements, ctx.all_kb_stations)
        return {"added": name}
    if action == "remove":
        ref = str(ch.get("element_id") or ch.get("name") or "")
        key = ref.lower().replace("gs ", "").strip()
        hit = None
        for s in ctx.ground_stations:
            nm = str(s.get("name") or "").lower()
            if s.get("element_id") == ref or nm == ref.lower() or nm.replace("gs ", "").strip() == key:
                hit = s
                break
        if hit is None:
            raise PreviewError(f"no station {ref!r} in the study")
        ctx.elements = [e for e in ctx.elements if e["id"] != hit.get("element_id")]
        ctx.ground_stations = [s for s in ctx.ground_stations if s is not hit]
        return {"removed": hit.get("name")}
    raise PreviewError("station action must be add or remove")


def _element(ctx, element_id: str, changes: dict) -> dict:
    el = next((e for e in ctx.elements if e["id"] == element_id), None)
    if el is None:
        raise PreviewError(f"unknown element: {element_id}")
    cols = ("mass_kg", "power_avg_w", "power_peak_w", "quantity", "trl", "cost_recurring_keur", "name")
    applied = {}
    for k, v in (changes or {}).items():
        if k.startswith("_"):
            continue
        if k == "performance" and isinstance(v, dict):
            el["performance"] = {**(el.get("performance") or {}), **v}
        elif k in cols:
            el[k] = v
        else:
            el["performance"] = {**(el.get("performance") or {}), k: v}
        applied[k] = v
    # the mode matrix keeps its own per-mode values (Modes owns them): use ``mode_member`` for those
    return {"element": el.get("name"), "changes": applied}


async def _pending(ctx, pc_id: str) -> dict:
    from ..seats import store
    pc = await store.get_pending(pc_id)
    if not pc or pc.get("study_id") != ctx.study_id:
        raise PreviewError(f"unknown pending change: {pc_id}")
    new = dict(pc.get("new") or {})
    if pc.get("kind") == "element_fields":
        return {**_element(ctx, pc["element_id"], new), "pending_id": pc_id, "owner_seat": pc.get("owner_seat")}
    if pc.get("kind") == "element_param":
        name = new.pop("_name", None)
        if not name:
            raise PreviewError("pending change without a parameter name")
        return {**_element(ctx, pc["element_id"], {name: new.get("value")}), "pending_id": pc_id,
                "owner_seat": pc.get("owner_seat")}
    raise PreviewError(f"a {pc.get('kind')} change has no preview")


def _orbit(ctx, ch: dict) -> dict:
    from .analysis_context import _build_orbit
    st = ctx.study
    orb = getattr(getattr(st, "requirements", None), "orbit", None)
    if orb is None:
        raise PreviewError("the study has no orbit")
    before = {"altitude_km": orb.altitude_km, "inclination_deg": orb.inclination_deg}
    alt = _num(ch.get("altitude_km"))
    if alt is not None:
        orb.altitude_km = alt
        if _num(ch.get("inclination_deg")) is None and "sso" in str(getattr(orb, "orbit_type", "")).lower():
            try:
                from spacecdf_common.physics.orbit import sso_inclination_deg
                orb.inclination_deg = round(sso_inclination_deg(alt), 3)
            except Exception:  # noqa: BLE001
                pass
    if _num(ch.get("inclination_deg")) is not None:
        orb.inclination_deg = _num(ch.get("inclination_deg"))
    for k in ("orbit.altitude_km", "orbit.inclination_deg", "orbit.period_s", "orbit.eclipse_fraction",
              "orbit.sunlight_fraction"):
        ctx.flat.pop(k, None)
    ctx.latest_design = {k: v for k, v in ctx.latest_design.items() if not k.startswith("orbit.")}
    ctx.orbit = _build_orbit(ctx.flat, ctx.latest_design, st)
    return {"from": before, "to": {"altitude_km": orb.altitude_km, "inclination_deg": orb.inclination_deg}}


def _subtree(ctx, root_id: str) -> list[dict]:
    kids: dict[str, list[dict]] = {}
    for e in ctx.elements:
        kids.setdefault(e.get("parent_id") or "", []).append(e)
    out, stack = [], [next(e for e in ctx.elements if e["id"] == root_id)]
    while stack:
        e = stack.pop()
        out.append(e)
        stack.extend(kids.get(e["id"], []))
    return out


def allocation_status(ctx, element_id: str, resource: str, value: float) -> dict:
    """An element's rolled-up value (with maturity) against an allocation."""
    from .margin_policy import maturity_percent
    el = next((e for e in ctx.elements if e["id"] == element_id), None)
    if el is None:
        raise PreviewError(f"unknown element: {element_id}")
    res = "power" if resource == "power" else "mass"
    tot = 0.0
    for e in _subtree(ctx, element_id):
        if e.get("element_type") != "component":
            continue
        q = int(e.get("quantity") or 1)
        v = float(e.get("power_avg_w" if res == "power" else "mass_kg") or 0.0) * q
        tot += v * (1 + maturity_percent(e, resource=res) / 100)
    if res == "power":
        try:
            from .key_numbers import mode_shares   # the subsystem's orbit-average load where modes exist
            if (el.get("subsystem_domain") or "") in ("ttc", "comms", "communications"):
                c = mode_shares(ctx).get("comms_w")
                if c is not None:
                    tot = c
        except Exception:  # noqa: BLE001
            pass
    return {"element": el.get("name"), "element_id": element_id, "resource": res, "allocation": value,
            "current_with_maturity": round(tot, 3), "margin": round(value - tot, 3),
            "owner_seat": el.get("owner_position") or "systems_engineer", "within": tot <= value}


# ───────────────────────────────────────────────────────────── preview

def _delta(a: Any, b: Any) -> Any:
    na, nb = _num(a), _num(b)
    if na is not None and nb is not None:
        return round(nb - na, 4)
    return None


def _changed(a: Any, b: Any) -> bool:
    na, nb = _num(a), _num(b)
    if na is not None and nb is not None:
        return abs(nb - na) > max(_EPS_ABS, 1e-4 * max(abs(na), abs(nb)))
    return a != b


def _resolve_element(ctx, ch: dict) -> str:
    """An element id from ``element_id``, else from ``element`` (a unique name, or a subsystem
    domain such as ``payload``)."""
    eid = str(ch.get("element_id") or "")
    if eid:
        return eid
    ref = str(ch.get("element") or "")
    if not ref:
        raise PreviewError("give element_id or element")
    hits = [e for e in ctx.elements if (e.get("name") or "").lower() == ref.lower()]
    if not hits:
        hits = [e for e in ctx.elements if e.get("element_type") == "subsystem" and (e.get("subsystem_domain") or "") == ref]
    if not hits:
        hits = [e for e in ctx.elements if ref.lower() in (e.get("name") or "").lower()]
    if len(hits) != 1:
        raise PreviewError(f"element {ref!r} is unknown or ambiguous")
    return hits[0]["id"]


async def _apply(after, ch: dict, extra_lines: list[dict]) -> dict:
    kind = str(ch.get("kind") or "")
    if kind not in KINDS:
        raise PreviewError(f"kind must be one of {', '.join(KINDS)}")
    if kind == "station":
        return _station(after, ch)
    if kind == "mode_share":
        share = _num(ch.get("share_pct"))
        if share is None:
            raise PreviewError("mode_share needs share_pct")
        return _set_share(after, _find_mode(after, ch.get("mode")), share / 100.0,
                          rebalance_kind=str(ch.get("rebalance") or "nominal"))
    if kind == "mode_member":
        m = _find_mode(after, ch.get("mode"))
        pw = _num(ch.get("power_w"))
        eid = _resolve_element(after, ch)
        row = next((r for r in m.members if r.get("element_id") == eid), None)
        if row is None or pw is None:
            raise PreviewError("mode_member needs a unit of the mode and power_w")
        out = {"mode": m.name, "element_id": eid, "from_w": row.get("power_w"), "to_w": pw}
        row["power_w"] = pw
        row["state"] = "nominal" if pw > 0 else "off"
        return out
    if kind == "element":
        return _element(after, _resolve_element(after, ch), ch.get("changes") or {})
    if kind == "pending_change":
        return await _pending(after, str(ch.get("id") or ""))
    if kind == "orbit":
        return _orbit(after, ch)
    # allocation
    val = _num(ch.get("value"))
    if val is None:
        raise PreviewError("allocation needs a value")
    a = allocation_status(after, _resolve_element(after, ch), str(ch.get("resource") or "mass"), val)
    unit = "kg" if a["resource"] == "mass" else "W"
    extra_lines.append({"key": f"allocation.{a['resource']}", "label": a["element"], "before": ch.get("from"),
                        "after": a["allocation"], "delta": _delta(ch.get("from"), a["allocation"]), "unit": unit,
                        "source": "allocation", "owner_seat": a["owner_seat"],
                        "note": {"current_with_maturity": a["current_with_maturity"], "margin": a["margin"],
                                 "within": a["within"]}})
    extra_lines.append({"key": f"allocation.{a['resource']}.margin", "label": a["element"], "before": None,
                        "after": a["margin"], "delta": None, "unit": unit, "source": "allocation",
                        "owner_seat": "systems_engineer"})
    return a


async def preview(study_id: str, body: dict[str, Any], *, ctx=None, rows: list[dict] | None = None) -> dict[str, Any]:
    """The impact preview of one proposed change, or of several applied together
    (``{"changes": [...]}``; see the module doc). Pure: never writes."""
    from .analysis_context import build_context
    from .key_numbers import DAY_MIN, numbers_from_context
    if isinstance(body.get("changes"), list) and body["changes"]:
        changes = [dict(c) for c in body["changes"] if isinstance(c, dict)]
    else:
        changes = [dict(body.get("change") or body)]
    for ch in changes:
        if str(ch.get("kind") or "") not in KINDS:
            raise PreviewError(f"kind must be one of {', '.join(KINDS)}")
    kinds = {str(c["kind"]) for c in changes}
    if ctx is None:
        ctx = await build_context(study_id)
    if rows is None:
        try:
            from ..db import cdr_repo
            rows = await cdr_repo.list_rows(study_id)
        except Exception:  # noqa: BLE001
            rows = []
    data = bool(kinds & {"station", "orbit", "mode_share", "mode_member"})
    disposal = bool(kinds & {"orbit", "element", "pending_change"})
    before_ctx = _copy_ctx(ctx)
    after = _copy_ctx(ctx)
    extra_lines: list[dict] = []
    applied = [await _apply(after, ch, extra_lines) for ch in changes]
    kn0 = await numbers_from_context(before_ctx, rows, data=data, disposal=disposal)
    ripple = None
    if "station" in kinds:
        # the ripple: the downlink share follows the union contact time (3.H3's rule), Δ applied
        p0 = (kn0.get("modes.downlink_share_proposed_pct") or {}).get("value")
        kn_tmp = await numbers_from_context(after, rows, data=True, disposal=False)
        p1 = (kn_tmp.get("modes.downlink_share_proposed_pct") or {}).get("value")
        if p0 is not None and p1 is not None:
            try:
                dl = _find_mode(after, "downlink")
                ripple = _set_share(after, dl, float(dl.orbit_fraction or 0.0) + (p1 - p0) / 100.0)
                ripple["rule"] = f"union contact ÷ {DAY_MIN:.0f} min/day"
            except PreviewError:
                ripple = None
    kn1 = await numbers_from_context(after, rows, data=data, disposal=disposal)
    lines: list[dict] = []
    for key in sorted(set(kn0) | set(kn1)):
        a, b = kn0.get(key) or {}, kn1.get(key) or {}
        va, vb = a.get("value"), b.get("value")
        if va is None and vb is None:
            continue
        if not _changed(va, vb):
            continue
        lines.append({"key": key, "before": va, "after": vb, "delta": _delta(va, vb), "unit": (b or a).get("unit"),
                      "source": (b or a).get("source"), "owner_seat": (b or a).get("owner_seat")})
    lines += extra_lines
    seats: dict[str, list[str]] = {}
    for ln in lines:
        seats.setdefault(ln["owner_seat"] or "systems_engineer", []).append(ln["key"])
    ordered = sorted(seats, key=lambda s: SEAT_ORDER.index(s) if s in SEAT_ORDER else 99)
    return {"study_id": study_id, "kind": changes[0]["kind"] if len(changes) == 1 else "composite",
            "change": changes[0] if len(changes) == 1 else None, "changes": changes,
            "applied": applied[0] if len(applied) == 1 else applied, "ripple": ripple, "dry_run": True,
            "lines": lines, "seats": [{"seat": s, "keys": seats[s]} for s in ordered],
            "before": kn0, "after": kn1}


__all__ = ["KINDS", "PreviewError", "allocation_status", "preview"]
