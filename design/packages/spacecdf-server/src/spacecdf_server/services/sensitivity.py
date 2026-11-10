"""SpaceCDF — sensitivity on the real services (wave 3, 3.H5; negotiation support #4). Owner H.

The negotiations of the Northern Fire and Ice mission (N1 science volume vs downlink, N3 imaging
duty vs power, N4 altitude vs resolution and disposal) need "what does the margin do if this value
moves" on the study's own models, not on the parametric design loop. Two views:

* ``data(study_id, parameter)``: the daily data-budget margin (``services/data_budget.compute``,
  the same function as the Data budget page) against

  - ``science_target``: the science delivered per day (MB/day after compression);
  - ``compression_ratio``: the lossless ratio on the planned product set;
  - ``rate_tier``: the downlink rate (every tier of TM/TC → rate tiers), with the largest science
    volume that still closes with the required margin at that rate;
  - ``imaging_share``: the imaging share of the orbit, with the product set scaled to the number of
    acquisitions, the orbit-average power and the depth of discharge (``mode_model.energy_balance``).

* ``altitude(study_id)``: a sweep of the circular sun-synchronous altitude: GSD and swath (they scale
  with the altitude from the payload's stated or optical values), union contact minutes with the
  study's stations, decay with and without the drag device (``physics/disposal``, L's mass and area
  basis), eclipse (``orbit_season``) and link margin (the design case scaled by the slant range),
  with the regulatory lines (600 km apogee without propulsion, 5-year disposal).

Contacts are computed once per view; every point is a pure ``compute`` call. Pure read.
"""
from __future__ import annotations

import math
from typing import Any

PARAMETERS = ("science_target", "compression_ratio", "rate_tier", "imaging_share")
DEFAULT_MARGIN = 10.0          # % of capacity held back (the negotiation question "with 10 % margin")


def _num(v: Any) -> float | None:
    if isinstance(v, bool) or v is None:
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


# ───────────────────────────────────────────────────────────── data budget sweeps

class _Budget:
    """The study's data-budget inputs, contacts computed once; ``run`` is one ``compute`` call."""

    def __init__(self, ctx, rows: list[dict], *, degraded: bool = False):
        from . import cdr_model as cm
        from . import data_budget as dbs
        from . import ground_closure as gc
        from .ground_scheduler import contact_statistics
        from .mode_model import cfg as mode_cfg
        self.ctx, self.rows = ctx, rows
        self.warnings: list[str] = []
        self.net = gc.network(ctx, self.warnings)
        self.modes = [dbs._mode_dict(m) for m in dbs.study_modes(ctx.elements)]
        self.stats = contact_statistics(self.net["orbit"], self.net["included"], days=30.0, step_s=10.0,
                                        ltan_h=self.net["ltan_h"], epoch=self.net["epoch"]) if self.net["included"] else None
        self.tiers = [{"name": t.get("name"), "bps": t.get("bps")} for t in cm.live_data(rows, "rate_tiers")]
        self.stations = [{"id": g.id, "name": g.name, "lon": g.longitude_deg, "control": g.id in self.net["control"]}
                         for g in self.net["included"]]
        self.rate = float(self.net["link"].downlink_bps or 0.0)
        self.period = float(ctx.orbit.get("period_s") or 5700.0)
        self.fallback_hk = float(mode_cfg()["data"]["housekeeping_bps"]["value"])
        self.degraded: list[dict] = []
        if degraded and len(self.net["included"]) > 1:
            for gs in self.net["included"]:
                rest = [g for g in self.net["included"] if g.id != gs.id]
                s2 = contact_statistics(self.net["orbit"], rest, days=30.0, step_s=10.0, ltan_h=self.net["ltan_h"],
                                        epoch=self.net["epoch"])
                self.degraded.append({"station": gs.name, "station_id": gs.id, "union_min_per_day": s2.union["min_per_day"],
                                      "windows_per_day": s2.union["windows_per_day"], "longest_gap_h": s2.union["longest_gap_h"],
                                      "stats": s2})
            self.degraded.sort(key=lambda x: x["union_min_per_day"])

    def run(self, scenario: dict | None = None, *, modes: list[dict] | None = None, rate: float | None = None,
            rows: list[dict] | None = None, contacts=None, stations: list[dict] | None = None) -> dict:
        from . import data_budget as dbs
        deg = [{k: v for k, v in d.items() if k != "stats"} for d in self.degraded[:1]] if contacts is None else None
        return dbs.compute(rows if rows is not None else self.rows, modes if modes is not None else self.modes,
                           contacts=contacts if contacts is not None else self.stats, link_rate_bps=rate or self.rate,
                           period_s=self.period, stations=stations if stations is not None else self.stations,
                           tiers=self.tiers, scenario=scenario, degraded=deg, fallback_hk_bps=self.fallback_hk)


def largest_science(b: dict, margin_pct: float) -> float | None:
    """Largest science delivered per day (MB/day) that keeps ``margin_pct`` of the capacity free in
    the baseline case: (capacity × (1 − m) − real-time HK − stored HK) × CFDP efficiency."""
    c1 = next((c for c in b.get("cases") or [] if c["id"] == "C1"), None) or b.get("closure") or {}
    cap = _num(c1.get("capacity_mb"))
    if not cap:
        return None
    cfdp = float((b.get("science") or {}).get("cfdp_efficiency") or 1.0)
    return round(max(0.0, (cap * (1 - margin_pct / 100.0) - float(c1.get("rt_hk_mb") or 0) -
                           float(c1.get("stored_hk_mb") or 0)) * cfdp), 2)


def _point(x: float, b: dict, margin: float, **extra: Any) -> dict:
    cl = b.get("closure") or {}
    mg = _num(cl.get("margin_pct"))
    return {"x": round(x, 4), "capacity_mb": cl.get("capacity_mb"), "demand_mb": cl.get("demand_mb"),
            "science_mb": cl.get("science_mb"), "margin_pct": mg,
            "status": "not_evaluated" if mg is None else "pass" if mg >= margin else "warn" if mg >= 0 else "fail", **extra}


def _imaging_rows(rows: list[dict], factor: float) -> list[dict]:
    """The CDR rows with the payload product set scaled by ``factor`` (more acquisitions)."""
    out = []
    for r in rows:
        if r.get("kind") == "payload_products" and r.get("status") != "rejected":
            d = dict(r.get("data") or {})
            d["products"] = [{**p, "per_day": (_num(p.get("per_day")) or 0) * factor} for p in d.get("products") or []]
            if _num(d.get("science_mb_per_day")) is not None:
                d["science_mb_per_day"] = float(d["science_mb_per_day"]) * factor
            r = {**r, "data": d}
        out.append(r)
    return out


async def data(study_id: str, parameter: str = "science_target", *, margin_pct: float = DEFAULT_MARGIN,
               values: list[float] | None = None) -> dict[str, Any]:
    """Margin of the daily data budget against one parameter (see the module doc)."""
    from ..db import cdr_repo
    from .analysis_context import build_context
    if parameter not in PARAMETERS:
        raise ValueError(f"parameter must be one of {', '.join(PARAMETERS)}")
    ctx = await build_context(study_id)
    rows = await cdr_repo.list_rows(study_id)
    B = _Budget(ctx, rows)
    base = B.run()
    sci = base.get("science") or {}
    out: dict[str, Any] = {"study_id": study_id, "parameter": parameter, "margin_required_percent": margin_pct,
                           "baseline": _point(0.0, base, margin_pct) | {"x": None}, "warnings": B.warnings + base.get("warnings", []),
                           "rate_bps": B.rate, "status": "ok" if base.get("capacity", {}).get("union_min_per_day") else "no_contact_plan"}
    target = _num(sci.get("target_mb_per_day")) or _num(sci.get("delivered_mb_per_day")) or 0.0
    cr0 = _num(sci.get("compression_ratio")) or 1.0
    pts: list[dict] = []
    if parameter == "science_target":
        xs = values or [round(x, 1) for x in (5, 7.5, 9, 10, 12.5, 13, 15, 17.5, 19.9, 20, 22.5, 25)]
        for x in sorted(set(xs)):
            pts.append(_point(x, B.run({"science_mb_per_day": x, "basis": "target"}), margin_pct))
        out["baseline"]["x"] = target
        out["unit"] = "MB/day"
        out["largest_with_margin_mb_per_day"] = largest_science(base, margin_pct)
        out["label"] = {"en": "Science delivered per day (after compression)", "fr": "Science livrée par jour (après compression)"}
    elif parameter == "compression_ratio":
        xs = values or [1.0, 1.1, 1.2, 1.28, 1.3, 1.4, 1.5, 1.75, 2.0, 2.5, 3.0]
        for x in sorted(set(xs)):
            b = B.run({"compression_ratio": x, "basis": "products"})
            s = b.get("science") or {}
            pts.append(_point(x, b, margin_pct, delivered_mb=s.get("delivered_mb_per_day"),
                              meets_target=(s.get("delivered_mb_per_day") or 0) >= target - 1e-9 if target else None))
        out["baseline"] = _point(cr0, B.run({"compression_ratio": cr0, "basis": "products"}), margin_pct)
        out["unit"] = ":1"
        out["needed_for_target"] = sci.get("compression_needed")
        out["raw_mb_per_day"] = sci.get("raw_mb_per_day")
        out["label"] = {"en": "Lossless compression ratio on the planned product set", "fr": "Taux de compression sans perte sur les produits prévus"}
    elif parameter == "rate_tier":
        tiers = sorted({float(t["bps"]) for t in B.tiers if _num(t.get("bps"))} | ({B.rate} if B.rate else set()))
        if values:
            tiers = sorted(set(float(v) for v in values))
        names = {float(t["bps"]): t.get("name") for t in B.tiers if _num(t.get("bps"))}
        for r in tiers:
            b = B.run(rate=r)
            c1 = next((c for c in b.get("cases") or [] if c["id"] == "C1"), None) or {}
            mg = _num(c1.get("margin_pct"))
            pts.append({"x": r, "tier": names.get(r), "capacity_mb": c1.get("capacity_mb"), "demand_mb": c1.get("demand_mb"),
                        "margin_pct": mg, "largest_with_margin_mb_per_day": largest_science(b, margin_pct),
                        "status": "not_evaluated" if mg is None else "pass" if mg >= margin_pct else "warn" if mg >= 0 else "fail"})
        out["baseline"]["x"] = B.rate
        out["unit"] = "bit/s"
        out["label"] = {"en": "Downlink rate tier", "fr": "Palier de débit descendant"}
    else:                                   # imaging_share
        from . import mode_model as mm
        img = next((m for m in B.modes if m.get("kind") == "imaging"), None)
        nom = next((m for m in B.modes if m.get("kind") == "nominal"), None)
        if img is None or nom is None:
            out["status"] = "no_imaging_mode"
            out["points"] = []
            return out
        f0 = float(img.get("orbit_fraction") or 0.0)
        xs = values or [0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.12, 0.15]
        xs = sorted(set([round(x, 4) for x in xs] + ([round(f0, 4)] if f0 else [])))
        energy = _energy_inputs(ctx)
        for x in xs:
            factor = x / f0 if f0 else 1.0
            modes = [{**m, "orbit_fraction": (x if m is img else max(0.0, float(nom.get("orbit_fraction") or 0) - (x - f0))
                                              if m is nom else m.get("orbit_fraction"))} for m in B.modes]
            b = B.run(modes=modes, rows=_imaging_rows(rows, factor))
            p = _point(x, b, margin_pct)
            if energy:
                em = [_with_fraction(m, x if m.id == img["id"] else
                                     max(0.0, float(nom.get("orbit_fraction") or 0) - (x - f0)) if m.id == nom["id"] else None)
                      for m in energy["modes"]]
                eb = mm.energy_balance(em, ctx.elements, period_s=B.period, eclipse_fraction=ctx.orbit.get("eclipse_fraction"),
                                       sa_power_eol_w=energy["sa"], battery_wh=energy["bat"],
                                       system_margin_percent=energy["sys"], max_dod_percent=ctx.power.get("battery_dod_percent"))
                ops = eb.get("operational_orbit") or {}
                p.update({"orbit_average_cbe_w": ops.get("orbit_average_cbe_w"), "orbit_average_load_w": ops.get("orbit_average_load_w"),
                          "energy_balance_wh": ops.get("balance_wh"), "dod_percent": ops.get("dod_percent"),
                          "power_status": ops.get("status")})
            pts.append(p)
        out["baseline"]["x"] = f0
        out["unit"] = "share of orbit"
        out["label"] = {"en": "Imaging share of the orbit (products scale with the acquisitions)",
                        "fr": "Part de l’orbite en imagerie (les produits suivent le nombre d’acquisitions)"}
    out["points"] = pts
    return out


def _with_fraction(m, f: float | None):
    from dataclasses import replace
    return replace(m, orbit_fraction=f) if f is not None else m


def _energy_inputs(ctx) -> dict | None:
    try:
        from ..routers.gates import study_margin_gate
        from ..routers.modes import _element_modes, _power_sources
        from .margin_policy import system_margin_percent
        sa, _s1, bat, _s2 = _power_sources(ctx)
        return {"modes": _element_modes(ctx), "sa": sa, "bat": bat,
                "sys": system_margin_percent(study_margin_gate(ctx.study), "power")}
    except Exception:  # noqa: BLE001
        return None


# ───────────────────────────────────────────────────────────── altitude sweep

def slant_range_km(alt_km: float, el_deg: float) -> float:
    re_ = 6371.0
    s = math.sin(math.radians(el_deg))
    return -re_ * s + math.sqrt((re_ * s) ** 2 + (re_ + alt_km) ** 2 - re_ ** 2)


async def altitude(study_id: str, *, altitudes: list[float] | None = None, min_elevation_deg: float = 10.0) -> dict[str, Any]:
    """The altitude sweep (see the module doc). Regulatory lines: 600 km apogee without propulsion
    (ISED), 5 years from the end of operations with the device (weak and nominal solar cycle)."""
    from spacecdf_common.physics.disposal import decay_lifetime_years, start_altitude_for, year_of
    from . import ground_closure as gc
    from . import licensing as lic
    from . import orbit_season as osn
    from . import rollup
    from .analysis_context import build_context
    from .ground_scheduler import OrbitParams, contact_statistics, sso_inclination_deg
    ctx = await build_context(study_id)
    warnings: list[str] = []
    net = gc.network(ctx, warnings)
    orbit, ltan_h, epoch = net["orbit"], net["ltan_h"], net["epoch"]
    h0 = float(orbit.altitude_km)
    study = ctx.study
    ru = (await rollup.compute(study_id)).as_dict()
    try:
        rec, _v = await lic.load_record(study_id)
    except Exception:  # noqa: BLE001
        rec = None
    disp = lic.disposal_analysis(study, ctx.elements, ru, rec)
    mass = float(disp.get("mass_kg") or 4.0)
    a_sail = _num(disp.get("area_deployed_effective_m2"))
    a_bus = float(disp.get("area_stowed_m2") or 0.03)
    start = float(disp.get("start_year") or year_of(getattr(getattr(study, "requirements", None), "launch_date_target", None)))
    pay = lic._payload_info(study, ctx.elements, h0)
    gsd0, sw0 = _num(pay.get("gsd_m")), _num(pay.get("swath_km"))
    link = getattr(getattr(study, "requirements", None), "link", None)
    m0 = _num(getattr(link, "margin_db", None)) if link is not None else None
    s0 = slant_range_km(h0, min_elevation_deg)
    hs = altitudes or [450, 475, 500, 525, 550, 575, 590, 600, 625, 650, 675, 700]
    hs = sorted(set([float(h) for h in hs] + [h0]))
    pts = []
    for h in hs:
        inc = sso_inclination_deg(h)
        st = contact_statistics(OrbitParams(altitude_km=h, inclination_deg=inc), net["included"], days=30.0, step_s=10.0,
                                ltan_h=ltan_h, epoch=epoch) if net["included"] else None
        ss = osn.compute(altitude_km=h, inclination_deg=inc, ltan_h=ltan_h if ltan_h is not None else 22.5,
                         year=int(epoch[0]), step_days=7.0)
        life = {}
        if a_sail:
            for sc in ("nominal", "weak"):
                life[f"with_device_{sc}_y"] = round(decay_lifetime_years(h, start, mass, a_sail, sc, max_years=30.0), 1)
        for sc in ("strong", "weak"):
            life[f"without_device_{sc}_y"] = round(decay_lifetime_years(h, start, mass, a_bus, sc, max_years=30.0), 1)
        pts.append({"altitude_km": h, "inclination_deg": round(inc, 3),
                    "gsd_m": round(gsd0 * h / h0, 1) if gsd0 else None, "swath_km": round(sw0 * h / h0, 1) if sw0 else None,
                    "union_min_per_day": round(st.union["min_per_day"], 1) if st else None,
                    "longest_gap_h": round(st.union["longest_gap_h"], 2) if st else None,
                    "eclipse_max_min": ss["eclipse"]["max_min"], "eclipse_min_min": ss["eclipse"]["min_min"],
                    "beta_min_deg": ss["beta"]["min_deg"], "beta_max_deg": ss["beta"]["max_deg"],
                    "link_margin_db": round(m0 + 20 * math.log10(s0 / slant_range_km(h, min_elevation_deg)), 2) if m0 is not None else None,
                    "apogee_ok": h <= 600.0, **life,
                    "disposal_ok": (life.get("with_device_weak_y", life.get("without_device_weak_y", 99)) <= 5.0)})
    lines = {"apogee_without_propulsion_km": 600.0, "disposal_years": 5.0}
    if a_sail:
        lines["max_start_altitude_5y_weak_km"] = start_altitude_for(5.0, start, mass, a_sail, "weak")
        lines["max_start_altitude_5y_nominal_km"] = start_altitude_for(5.0, start, mass, a_sail, "nominal")
    lines["max_start_altitude_5y_without_device_strong_km"] = start_altitude_for(5.0, start, mass, a_bus, "strong", lo_km=300.0)
    return {"study_id": study_id, "baseline_altitude_km": h0, "points": pts, "lines": lines,
            "basis": {"mass_kg": mass, "mass_basis": disp.get("mass_basis"), "device_area_m2": a_sail, "bus_area_m2": a_bus,
                      "start_year": start, "gsd_m": gsd0, "swath_km": sw0, "gsd_source": pay.get("gsd_source"),
                      "design_link_margin_db": m0, "min_elevation_deg": min_elevation_deg,
                      "stations": [g.name for g in net["included"]]},
            "warnings": warnings}


# ───────────────────────────────────────────────────────────── option effects for negotiations (3.H6)

def _case(b: dict, prefix: str) -> dict | None:
    return next((c for c in b.get("cases") or [] if str(c.get("id", "")).startswith(prefix)), None)


def _margins(b: dict) -> dict[str, Any]:
    c1, c4, c5 = _case(b, "C1"), _case(b, "C4"), _case(b, "C5")
    return {"capacity_mb_per_day": (c1 or {}).get("capacity_mb"), "demand_mb_per_day": (c1 or {}).get("demand_mb"),
            "margin_c1_pct": (c1 or {}).get("margin_pct"),
            "margin_worst_site_out_pct": (c4 or {}).get("margin_pct"), "worst_site": ((c4 or {}).get("label") or {}).get("en"),
            "margin_fallback_rate_pct": (c5 or {}).get("margin_pct")}


async def science_options(study_id: str, values: list[float], *, margin_pct: float = DEFAULT_MARGIN) -> dict[str, Any]:
    """N1: the daily margins (baseline, worst single site out, fallback rate) for science targets."""
    from ..db import cdr_repo
    from .analysis_context import build_context
    ctx = await build_context(study_id)
    B = _Budget(ctx, await cdr_repo.list_rows(study_id), degraded=True)
    base = B.run()
    rows = [{"science_mb_per_day": v, **_margins(B.run({"science_mb_per_day": v, "basis": "target"}))} for v in values]
    fall = [float(t["bps"]) for t in B.tiers if _num(t.get("bps")) and 4800 <= float(t["bps"]) < B.rate]
    return {"options": rows, "largest_with_margin_mb_per_day": largest_science(base, margin_pct),
            "largest_with_margin_at_fallback_mb_per_day": largest_science(B.run(rate=max(fall)), margin_pct) if fall else None,
            "fallback_rate_bps": max(fall) if fall else None, "rate_bps": B.rate,
            "baseline_target_mb_per_day": (base.get("science") or {}).get("target_mb_per_day"),
            "compression_ratio": (base.get("science") or {}).get("compression_ratio"),
            "compression_needed": (base.get("science") or {}).get("compression_needed")}


def _ops_power(ctx, fractions: dict[str, float]) -> dict | None:
    """Operational-orbit power with some mode shares replaced (nominal takes the balance)."""
    from . import mode_model as mm
    e = _energy_inputs(ctx)
    if not e:
        return None
    ms = e["modes"]
    nom = next((m for m in ms if m.kind == "nominal"), None)
    new = []
    for m in ms:
        f = fractions.get(m.id)
        new.append(_with_fraction(m, f))
    if nom is not None and nom.id not in fractions:
        others = sum(float(m.orbit_fraction or 0) for m in new if mm.in_operational_mix(m) and m.id != nom.id)
        new = [_with_fraction(m, max(0.0, 1.0 - others)) if m.id == nom.id else m for m in new]
    eb = mm.energy_balance(new, ctx.elements, period_s=ctx.orbit.get("period_s") or 5700.0,
                           eclipse_fraction=ctx.orbit.get("eclipse_fraction"), sa_power_eol_w=e["sa"], battery_wh=e["bat"],
                           system_margin_percent=e["sys"], max_dod_percent=ctx.power.get("battery_dod_percent"))
    return eb.get("operational_orbit")


async def station_options(study_id: str) -> dict[str, Any]:
    """The fourth-station ripple: the network with and without the station whose loss costs the
    most contact, with the union, the capacity, the daily margin, the proposed downlink share and
    the orbit-average power at that share."""
    from ..db import cdr_repo
    from .analysis_context import build_context
    ctx = await build_context(study_id)
    B = _Budget(ctx, await cdr_repo.list_rows(study_id), degraded=True)
    if not B.stats:
        return {"options": [], "station": None}
    dl = next((m for m in B.modes if m.get("kind") == "downlink"), None)
    out = []
    worst = B.degraded[0] if B.degraded else None
    variants = ([("without", worst["station"], worst["stats"], [s for s in B.stations if s["id"] != worst["station_id"]])]
                if worst else []) + [("with", None, B.stats, B.stations)]
    for key, st_name, stats, sts in variants:
        b = B.run(contacts=stats, stations=sts)
        union = float(stats.union["min_per_day"])
        share = union / 1440.0
        ops = _ops_power(ctx, {dl["id"]: share}) if dl else None
        out.append({"key": key, "stations": [s["name"] for s in sts], "left_out": st_name,
                    "union_min_per_day": round(union, 1), "longest_gap_h": round(float(stats.union["longest_gap_h"]), 2),
                    "downlink_share": round(share, 4), **_margins(b),
                    "orbit_average_cbe_w": (ops or {}).get("orbit_average_cbe_w"),
                    "orbit_average_load_w": (ops or {}).get("orbit_average_load_w")})
    return {"options": out, "station": worst["station"] if worst else None}


async def imaging_options(study_id: str, shares: list[float]) -> dict[str, Any]:
    """N3: imaging share options with the orbit-average power, the depth of discharge and the data margin."""
    res = await data(study_id, "imaging_share", values=shares)
    return {"options": res.get("points") or [], "baseline_share": res["baseline"].get("x"), "status": res.get("status")}


__all__ = ["PARAMETERS", "data", "altitude", "largest_science", "science_options", "station_options", "imaging_options"]
