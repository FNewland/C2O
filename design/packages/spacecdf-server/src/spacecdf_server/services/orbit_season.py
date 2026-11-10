"""SpaceCDF — the orbit through the seasons: β angle, eclipse range, sun elevation at the daylight
node and the thermal design cases (wave 3, 3.H4; automation A6). Owner H.

A sun-synchronous orbit holds its node time against the *mean* sun, so the angle between the
orbit plane and the *true* sun (β) still changes over the year with the sun's declination and the
equation of time. This module propagates the orbit plane over a year (J2 secular node rate, the
same model as ``ground_scheduler``) and gives:

* ``β(t)`` and its range, and the eclipse duration per orbit from β (cylindrical shadow);
* the sun elevation at the sub-satellite point where the **daylight** pass crosses each latitude
  of interest, per month, with a flag where an optical payload cannot see the ground (below
  ``min_sun_elevation_deg``), e.g. freeze-up north of 60° N after mid-November;
* the thermal hot and cold β cases proposed to the Thermal seat: the β range widened by the
  β uncertainty (node drift, injection dispersion) and rounded, with the node-time window. A's
  thermal nodal model (``routers/thermal_model.py``) reads ``thermal_cases(study_id)``; it does
  not compute β itself (W0_SEAMS §9.2).

The year is the calendar year of the launch-date target, with the node time set on 1 January
(the convention of the mission-analysis baseline). Pure numbers in, pure dict out; ``season``
loads a study. Config: ``configs/mode_rules.yaml`` → ``orbit_season``.
"""
from __future__ import annotations

import math
from typing import Any

MU = 398600.4418            # km^3/s^2
RE = 6378.137               # km
J2 = 1.08262668e-3
DAYS_YEAR = 365.2421897

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
MONTHS_FR = ("janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc.")


def cfg() -> dict[str, Any]:
    from .mode_model import cfg as mode_cfg
    return dict(mode_cfg().get("orbit_season") or {})


def _v(node: Any, dflt: float) -> float:
    if isinstance(node, dict):
        node = node.get("value")
    try:
        return float(node) if node is not None else dflt
    except (TypeError, ValueError):
        return dflt


# ───────────────────────────────────────────────────────────── astronomy (low precision, < 0.01°)

def jd(y: int, mo: int, d: float, hr: float = 0.0) -> float:
    if mo <= 2:
        y -= 1
        mo += 12
    a = y // 100
    b = 2 - a + a // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (mo + 1)) + d + b - 1524.5 + hr / 24.0


def sun_eci(j: float) -> tuple[float, float, float]:
    """Unit vector to the sun in the equatorial frame (Astronomical Almanac low-precision formula)."""
    n = j - 2451545.0
    L = math.radians((280.460 + 0.9856474 * n) % 360)
    g = math.radians((357.528 + 0.9856003 * n) % 360)
    lam = L + math.radians(1.915) * math.sin(g) + math.radians(0.020) * math.sin(2 * g)
    eps = math.radians(23.439 - 4e-7 * n)
    return math.cos(lam), math.cos(eps) * math.sin(lam), math.sin(eps) * math.sin(lam)


def sso_inclination_deg(alt_km: float) -> float:
    a = RE + alt_km
    n = math.sqrt(MU / a ** 3)
    cosi = -2 * math.pi / (DAYS_YEAR * 86400) / (1.5 * n * J2 * (RE / a) ** 2)
    return math.degrees(math.acos(max(-1.0, min(1.0, cosi))))


def rates(alt_km: float, inc_deg: float) -> tuple[float, float, float]:
    """(mean motion, node rate, argument-of-latitude rate) in rad/s, J2 secular, circular."""
    a = RE + alt_km
    n = math.sqrt(MU / a ** 3)
    i = math.radians(inc_deg)
    k = 1.5 * J2 * (RE / a) ** 2
    raan_dot = -k * n * math.cos(i)
    argp_dot = 0.5 * k * n * (5 * math.cos(i) ** 2 - 1)
    m_dot = n * (1 + 0.5 * k * (3 * math.cos(i) ** 2 - 1))
    return n, raan_dot, m_dot + argp_dot


def _plane(alt_km: float, inc_deg: float, ltan_h: float, jd0: float, day: float) -> tuple[tuple, float]:
    """Orbit normal (unit) and RAAN (rad) ``day`` days after ``jd0``, node time held on ``jd0``."""
    _n, rd, _ud = rates(alt_km, inc_deg)
    s0 = sun_eci(jd0)
    raan = math.atan2(s0[1], s0[0]) + math.radians((ltan_h - 12.0) * 15.0) + rd * day * 86400.0
    i = math.radians(inc_deg)
    return (math.sin(i) * math.sin(raan), -math.sin(i) * math.cos(raan), math.cos(i)), raan


def beta_deg(alt_km: float, inc_deg: float, ltan_h: float, jd0: float, day: float) -> float:
    nrm, _ = _plane(alt_km, inc_deg, ltan_h, jd0, day)
    s = sun_eci(jd0 + day)
    return math.degrees(math.asin(max(-1.0, min(1.0, sum(a * b for a, b in zip(nrm, s))))))


def eclipse_fraction(alt_km: float, beta: float) -> float:
    """Share of the orbit in the Earth's (cylindrical) shadow at this β; 0 above β*."""
    a = RE + alt_km
    b_star = math.degrees(math.asin(RE / a))
    if abs(beta) >= b_star:
        return 0.0
    x = math.sqrt(alt_km ** 2 + 2 * RE * alt_km) / (a * math.cos(math.radians(beta)))
    return math.degrees(math.acos(max(-1.0, min(1.0, x)))) / 180.0


def nodal_period_s(alt_km: float, inc_deg: float) -> float:
    return 2 * math.pi / rates(alt_km, inc_deg)[2]


def daylight_sun_elevation(alt_km: float, inc_deg: float, ltan_h: float, jd0: float, day: float,
                           lat_deg: float) -> float | None:
    """Sun elevation (deg) at the sub-satellite point where the daylight pass crosses ``lat_deg``
    (geocentric, spherical Earth). ``None`` when the orbit does not reach that latitude."""
    i = math.radians(inc_deg)
    s_lat = math.sin(math.radians(lat_deg)) / math.sin(i)
    if abs(s_lat) > 1:
        return None
    _nrm, raan = _plane(alt_km, inc_deg, ltan_h, jd0, day)
    s = sun_eci(jd0 + day)
    best = None
    u1 = math.asin(s_lat)
    for u in (u1, math.pi - u1):          # ascending and descending crossings of the latitude
        cO, sO, cu, su, ci, si = math.cos(raan), math.sin(raan), math.cos(u), math.sin(u), math.cos(i), math.sin(i)
        r = (cO * cu - sO * su * ci, sO * cu + cO * su * ci, su * si)
        el = math.degrees(math.asin(max(-1.0, min(1.0, sum(a * b for a, b in zip(r, s))))))
        best = el if best is None or el > best else best
    return best


# ───────────────────────────────────────────────────────────── the season of one orbit

def compute(*, altitude_km: float, inclination_deg: float | None, ltan_h: float, year: int,
            latitudes: list[float] | None = None, step_days: float = 1.0, c: dict | None = None) -> dict[str, Any]:
    """β, eclipse, sun elevation and thermal cases over the calendar ``year`` (see module doc)."""
    c = c if c is not None else cfg()
    inc = float(inclination_deg) if inclination_deg else sso_inclination_deg(altitude_km)
    jd0 = jd(year, 1, 1)
    T = nodal_period_s(altitude_km, inc)
    days = [k * step_days for k in range(int(365.0 / step_days) + 1)]
    series = []
    for d in days:
        b = beta_deg(altitude_km, inc, ltan_h, jd0, d)
        f = eclipse_fraction(altitude_km, b)
        series.append({"day": round(d, 2), "beta_deg": round(b, 2), "eclipse_fraction": round(f, 4),
                       "eclipse_min": round(f * T / 60.0, 2)})
    betas = [s["beta_deg"] for s in series]
    abs_b = [abs(b) for b in betas]
    fr = [s["eclipse_fraction"] for s in series]
    i_min, i_max = abs_b.index(min(abs_b)), abs_b.index(max(abs_b))
    ecl = [s["eclipse_min"] for s in series]

    # sun elevation at the daylight crossing, mid-month and the second half of November
    lats = latitudes or [float(x) for x in (c.get("latitudes_deg") or [48, 52, 56, 60, 64, 68])]
    min_el = _v(c.get("min_sun_elevation_deg"), 10.0)
    sample = sorted([(m, 15.0) for m in range(1, 13)] + [(11, 25.0)])
    sun_rows = []
    for mo, dd in sample:
        d = jd(year, mo, dd) - jd0
        vals = {f"{lat:g}": (round(v, 1) if v is not None else None)
                for lat in lats for v in [daylight_sun_elevation(altitude_km, inc, ltan_h, jd0, d, lat)]}
        sun_rows.append({"month": mo, "day_of_month": dd, "label": {"en": f"{dd:g} {MONTHS[mo - 1]}", "fr": f"{dd:g} {MONTHS_FR[mo - 1]}"},
                         "elevation_deg": vals})
    flags = []
    for r in sun_rows:
        low = [lat for lat in lats if r["elevation_deg"][f"{lat:g}"] is not None and r["elevation_deg"][f"{lat:g}"] < min_el]
        if low:
            flags.append({"month": r["month"], "day_of_month": r["day_of_month"], "latitudes_deg": low,
                          "north_of_deg": min(low), "min_sun_elevation_deg": min_el,
                          "text": {"en": f"{r['label']['en']}: the daylight pass sees the ground at less than {min_el:g}° sun elevation "
                                         f"north of {min(low):g}° N: not observable in the optical",
                                   "fr": f"{r['label']['fr']} : le passage de jour voit le sol sous moins de {min_el:g}° d’élévation solaire "
                                         f"au nord de {min(low):g}° N : non observable dans le visible"}})
    fz_lat = _v(c.get("freeze_up_latitude_deg"), 60.0)
    freeze = [f for f in flags if (f["month"] == 11 and f["day_of_month"] > 15 or f["month"] == 12)
              and any(lat >= fz_lat for lat in f["latitudes_deg"])]

    # thermal design cases proposed to the Thermal seat
    margin = _v(c.get("beta_margin_deg"), 2.5)
    win = c.get("node_window_h") or {}
    early, late = _v(win.get("early"), -1.0), _v(win.get("late"), 3.0)
    ltdn = (ltan_h + 12.0) % 24.0

    def hhmm(h: float) -> str:
        h %= 24.0
        return f"{int(h):02d}:{int(round((h - int(h)) * 60)) % 60:02d}"
    b_lo, b_hi = min(abs_b), max(abs_b)
    cold_b, hot_b = round(max(0.0, b_lo - margin)), round(b_hi + margin)
    f_cold, f_hot = eclipse_fraction(altitude_km, cold_b), eclipse_fraction(altitude_km, hot_b)
    cases = {
        "source": "orbit_season", "beta_margin_deg": margin,
        "node_window": {"early": hhmm(ltdn + early), "late": hhmm(ltdn + late), "nominal": hhmm(ltdn), "kind": "LTDN"},
        "hot": {"beta_deg": hot_b, "node": hhmm(ltdn + late), "eclipse_fraction": round(f_hot, 4), "eclipse_min": round(f_hot * T / 60, 1),
                "modes": {"en": "imaging + downlink in sunlight", "fr": "imagerie + liaison descendante au soleil"},
                "rationale": {"en": f"highest β over the year ({b_hi:.1f}°) + {margin:g}° (node drift, injection dispersion): the shortest eclipse",
                              "fr": f"β le plus élevé de l’année ({b_hi:.1f}°) + {margin:g}° (dérive du nœud, dispersion d’injection) : l’éclipse la plus courte"}},
        "cold": {"beta_deg": cold_b, "node": hhmm(ltdn + early), "eclipse_fraction": round(f_cold, 4), "eclipse_min": round(f_cold * T / 60, 1),
                 "modes": {"en": "Safe in eclipse", "fr": "Survie (Safe) en éclipse"},
                 "rationale": {"en": f"lowest β over the year ({b_lo:.1f}°) − {margin:g}°: the longest eclipse",
                               "fr": f"β le plus faible de l’année ({b_lo:.1f}°) − {margin:g}° : l’éclipse la plus longue"}},
    }
    weekly = series[:: max(1, int(round(7 / step_days)))]
    return {
        "inputs": {"altitude_km": altitude_km, "inclination_deg": round(inc, 3), "ltan_h": ltan_h, "ltdn_h": round(ltdn, 3),
                   "year": year, "node_set_on": f"{year}-01-01", "nodal_period_min": round(T / 60.0, 2),
                   "model": "J2 secular node rate, circular; low-precision sun; cylindrical shadow"},
        "beta": {"min_deg": round(min(betas), 2), "max_deg": round(max(betas), 2), "abs_min_deg": round(b_lo, 2),
                 "abs_max_deg": round(b_hi, 2), "day_of_min": series[i_min]["day"], "day_of_max": series[i_max]["day"]},
        "eclipse": {"min_min": round(min(ecl), 2), "max_min": round(max(ecl), 2), "fraction_min": round(min(fr), 4),
                    "fraction_max": round(max(fr), 4), "eclipse_free_days": sum(1 for x in fr if x == 0.0) * step_days},
        "series": weekly,
        "sun_elevation": {"latitudes_deg": lats, "min_sun_elevation_deg": min_el, "rows": sun_rows, "flags": flags,
                          "freeze_up_not_observable": bool(freeze), "freeze_up_flags": freeze},
        "thermal_cases": cases,
    }


async def season(study_id: str) -> dict[str, Any]:
    """``compute`` for a stored study: altitude, inclination and node time of the orbit, the year
    of the launch-date target."""
    from .analysis_context import build_context
    from .ground_closure import orbit_inputs
    ctx = await build_context(study_id)
    orbit, ltan_h, epoch = orbit_inputs(ctx)
    warnings = []
    if ltan_h is None:
        ltan_h = 22.5
        warnings.append("no node time on the orbit: 22:30 LTAN (10:30 LTDN) assumed")
    res = compute(altitude_km=orbit.altitude_km, inclination_deg=orbit.inclination_deg, ltan_h=ltan_h, year=int(epoch[0]))
    res["study_id"] = study_id
    res["warnings"] = warnings
    return res


async def thermal_cases(study_id: str) -> dict[str, Any]:
    """The hot and cold β cases for the Thermal seat (read by A's thermal nodal model)."""
    s = await season(study_id)
    return {**s["thermal_cases"], "eclipse": s["eclipse"], "beta": s["beta"], "inputs": s["inputs"]}


__all__ = ["compute", "season", "thermal_cases", "beta_deg", "eclipse_fraction", "daylight_sun_elevation"]
