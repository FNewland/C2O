#!/usr/bin/env python3
"""
Orbit Tools: TLE and State Vector to Telecommand (TC) Converter

Converts orbital elements (TLEs or Cartesian state vectors) to TC command
sequences for uploading orbit state to spacecraft. Supports CLI and web interface.

Spacecraft Parameter IDs (SET_PARAM S20.1):
  - 0x0231: GPS ECEF X position (meters)
  - 0x0232: GPS ECEF Y position (meters)
  - 0x0233: GPS ECEF Z position (meters)
  - 0x0234: GPS ECEF X velocity (m/s)
  - 0x0235: GPS ECEF Y velocity (m/s)
  - 0x0236: GPS ECEF Z velocity (m/s)
"""

import argparse
import json
import sys
from pathlib import Path
import asyncio
import struct
import math
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Tuple, List, Dict, Optional

try:
    from sgp4.api import Satrec, jday
except ImportError:
    import sys
    print("ERROR: sgp4 library required: pip install sgp4", file=sys.stderr)
    sys.exit(1)

# smo_common from the checkout when the suite is not pip-installed.
_COMMON_SRC = Path(__file__).resolve().parents[1] / "packages" / "smo-common" / "src"
if _COMMON_SRC.is_dir() and str(_COMMON_SRC) not in sys.path:
    sys.path.insert(0, str(_COMMON_SRC))

try:
    import aiohttp
    from aiohttp import web
    # Shared HTTP policy + design-system / language runtime for tool pages.
    from smo_common.web.http import setup_tool_app, tool_html_response
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import tool_frame          # shared page frame (TOOL_HEAD + title bar)
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


# Constants
_DEG = math.pi / 180.0
_RAD = 180.0 / math.pi
_EARTH_RADIUS_KM = 6371.0
_EARTH_FLATTENING = 1.0 / 298.257223563
_AU = 1.495978707e8  # km per AU
_MU_EARTH = 398600.4418  # km^3/s^2


# Telecommand Structure
TC_SERVICE_ID = 20
TC_SUBTYPE_ID = 1
PARAM_IDS = {
    'x_pos': 0x0231,
    'y_pos': 0x0232,
    'z_pos': 0x0233,
    'x_vel': 0x0234,
    'y_vel': 0x0235,
    'z_vel': 0x0236,
}


class OrbitAnalyzer:
    """Compute orbital elements from state vectors."""

    @staticmethod
    def compute_orbital_elements(pos_km: np.ndarray, vel_km_s: np.ndarray,
                                 mu: float = _MU_EARTH) -> Dict[str, float]:
        """
        Compute classical orbital elements from Cartesian state.

        Args:
            pos_km: ECI position [km]
            vel_km_s: ECI velocity [km/s]
            mu: Gravitational parameter [km^3/s^2]

        Returns:
            Dictionary with a, e, i, RAAN, AOP, TA, period
        """
        r = np.linalg.norm(pos_km)
        v = np.linalg.norm(vel_km_s)

        # Semi-major axis
        a = 1.0 / (2.0/r - v*v/mu)

        # Angular momentum
        h = np.cross(pos_km, vel_km_s)
        h_mag = np.linalg.norm(h)

        # Eccentricity
        ecc_vec = ((v*v - mu/r) * pos_km - np.dot(pos_km, vel_km_s) * vel_km_s) / mu
        e = np.linalg.norm(ecc_vec)

        # Inclination
        i = math.acos(np.clip(h[2] / h_mag, -1.0, 1.0))

        # RAAN (Omega)
        n_vec = np.array([-h[1], h[0], 0.0])
        n_mag = np.linalg.norm(n_vec)
        if n_mag > 1e-9:
            raan = math.atan2(n_vec[0], -n_vec[1])
        else:
            raan = 0.0

        # Argument of perigee (omega)
        if n_mag > 1e-9:
            aop = math.atan2(ecc_vec[2], np.dot(n_vec, ecc_vec)) - math.pi/2
        else:
            aop = 0.0

        # True anomaly
        if e > 1e-9:
            ta = math.atan2(np.dot(np.cross(ecc_vec, pos_km), h)/h_mag,
                           np.dot(ecc_vec, pos_km))
        else:
            ta = math.atan2(pos_km[1], pos_km[0])

        # Orbital period
        if a > 0:
            period = 2.0 * math.pi * math.sqrt(a**3 / mu)
        else:
            period = 0.0

        # Altitude at this point
        alt = r - _EARTH_RADIUS_KM

        return {
            'a_km': a,
            'e': e,
            'i_deg': i * _RAD,
            'raan_deg': (raan * _RAD) % 360.0,
            'aop_deg': (aop * _RAD) % 360.0,
            'ta_deg': (ta * _RAD) % 360.0,
            'period_s': period,
            'period_min': period / 60.0,
            'altitude_km': alt,
            'velocity_km_s': v,
        }


class EciEcefConverter:
    """Convert between ECI and ECEF frames."""

    @staticmethod
    def gmst(jd_ut1: float) -> float:
        """Greenwich Mean Sidereal Time in radians."""
        T = (jd_ut1 - 2451545.0) / 36525.0
        gmst_deg = (280.46061837 + 360.98564736629 * (jd_ut1 - 2451545.0)
                    + 0.000387933 * T * T - T * T * T / 38710000.0) % 360.0
        return gmst_deg * _DEG

    @staticmethod
    def eci_to_ecef(r_eci: np.ndarray, gmst: float) -> np.ndarray:
        """
        Convert ECI position/velocity to ECEF using GMST rotation.

        Args:
            r_eci: 3-element vector (position or velocity)
            gmst: Greenwich Mean Sidereal Time in radians

        Returns:
            ECEF vector
        """
        c, s = math.cos(gmst), math.sin(gmst)
        return np.array([
            c * r_eci[0] + s * r_eci[1],
            -s * r_eci[0] + c * r_eci[1],
            r_eci[2]
        ])

    @staticmethod
    def ecef_to_eci(r_ecef: np.ndarray, gmst: float) -> np.ndarray:
        """Convert ECEF position/velocity to ECI."""
        c, s = math.cos(gmst), math.sin(gmst)
        return np.array([
            c * r_ecef[0] - s * r_ecef[1],
            s * r_ecef[0] + c * r_ecef[1],
            r_ecef[2]
        ])


class TelecommandEncoder:
    """Encode orbital state into SET_PARAM telecommand bytes."""

    @staticmethod
    def float32_to_bytes(value: float) -> bytes:
        """Convert Python float to IEEE 754 float32 big-endian bytes."""
        return struct.pack('>f', value)

    @staticmethod
    def param_to_hex_cmd(param_id: int, value: float) -> str:
        """
        Generate a single SET_PARAM command.

        Service 20, Subtype 1: SET_PARAM
        Data format: param_id (2 bytes BE) + value (4 bytes IEEE754 BE)

        Args:
            param_id: Parameter ID (0x0231-0x0236)
            value: Float value

        Returns:
            Hex string without 0x prefix (ready for MCS input)
        """
        # Service and subtype bytes
        service = bytes([TC_SERVICE_ID])
        subtype = bytes([TC_SUBTYPE_ID])

        # Param ID (2 bytes, big-endian)
        param_bytes = struct.pack('>H', param_id)

        # Value (4 bytes, IEEE754, big-endian)
        value_bytes = TelecommandEncoder.float32_to_bytes(value)

        # Full command: service + subtype + param_id + value
        cmd = service + subtype + param_bytes + value_bytes

        return cmd.hex().upper()

    @staticmethod
    def state_to_commands(pos_ecef_m: np.ndarray, vel_ecef_ms: np.ndarray,
                         param_order: List[str] = None) -> Dict[str, str]:
        """
        Convert ECEF state vector to SET_PARAM hex commands.

        Args:
            pos_ecef_m: ECEF position [m] [x, y, z]
            vel_ecef_ms: ECEF velocity [m/s] [vx, vy, vz]
            param_order: Order of parameters (default: x, y, z, vx, vy, vz)

        Returns:
            Dictionary mapping parameter names to hex command strings
        """
        if param_order is None:
            param_order = ['x_pos', 'y_pos', 'z_pos', 'x_vel', 'y_vel', 'z_vel']

        state = {
            'x_pos': pos_ecef_m[0],
            'y_pos': pos_ecef_m[1],
            'z_pos': pos_ecef_m[2],
            'x_vel': vel_ecef_ms[0],
            'y_vel': vel_ecef_ms[1],
            'z_vel': vel_ecef_ms[2],
        }

        commands = {}
        for param_name in param_order:
            value = state[param_name]
            param_id = PARAM_IDS[param_name]
            cmd = TelecommandEncoder.param_to_hex_cmd(param_id, value)
            commands[param_name] = cmd

        return commands


class TleToStateConverter:
    """Convert TLE to state vector at specified epoch."""

    @staticmethod
    def propagate(tle_line1: str, tle_line2: str, epoch_utc: datetime) -> Tuple[np.ndarray, np.ndarray]:
        """
        Propagate TLE to specified epoch.

        Args:
            tle_line1: TLE line 1
            tle_line2: TLE line 2
            epoch_utc: UTC datetime to propagate to

        Returns:
            (pos_km, vel_km_s) in ECI frame
        """
        sat = Satrec.twoline2rv(tle_line1, tle_line2)

        jd, fr = jday(epoch_utc.year, epoch_utc.month, epoch_utc.day,
                      epoch_utc.hour, epoch_utc.minute,
                      epoch_utc.second + epoch_utc.microsecond * 1e-6)

        e, r, v = sat.sgp4(jd, fr)

        if e != 0:
            raise ValueError(f"SGP4 propagation error: {e}")

        return np.array(r), np.array(v)  # km and km/s


class OrbitSummary:
    """Generate human-readable orbit summary."""

    @staticmethod
    def format_summary(elements: Dict[str, float], utc: datetime) -> str:
        """Format orbital elements as readable text."""
        lines = [
            "=== ORBIT SUMMARY ===",
            f"Epoch: {utc.isoformat()} UTC",
            "",
            "CLASSICAL ELEMENTS:",
            f"  Semi-major axis:  {elements['a_km']:.2f} km",
            f"  Eccentricity:     {elements['e']:.6f}",
            f"  Inclination:      {elements['i_deg']:.4f}°",
            f"  RAAN:             {elements['raan_deg']:.4f}°",
            f"  Argument of Peri: {elements['aop_deg']:.4f}°",
            f"  True Anomaly:     {elements['ta_deg']:.4f}°",
            "",
            "DERIVED:",
            f"  Altitude:         {elements['altitude_km']:.2f} km",
            f"  Velocity:         {elements['velocity_km_s']:.4f} km/s",
            f"  Orbital Period:   {elements['period_min']:.2f} min ({elements['period_s']:.0f} s)",
            f"  Perigee:          {elements['a_km'] * (1 - elements['e']) - _EARTH_RADIUS_KM:.2f} km",
            f"  Apogee:           {elements['a_km'] * (1 + elements['e']) - _EARTH_RADIUS_KM:.2f} km",
        ]
        return "\n".join(lines)


def _state_dict(pos_m: np.ndarray, vel_ms: np.ndarray) -> Dict[str, float]:
    return {k: float(v) for k, v in zip(
        ('x_pos', 'y_pos', 'z_pos', 'x_vel', 'y_vel', 'z_vel'),
        list(pos_m) + list(vel_ms))}


_BASEMAP = (Path(__file__).resolve().parents[1] / "packages" / "smo-planner" / "src"
            / "smo_planner" / "static" / "modern" / "wide-basemap.js")


# Ground track and station passes (the picture the web page leads with)

_WGS84_A_KM = 6378.137
_WGS84_E2 = _EARTH_FLATTENING * (2.0 - _EARTH_FLATTENING)
_OMEGA_EARTH = 7.2921150e-5          # rad/s
TRACK_ORBITS = 3                     # ground track drawn for this many orbits
PASS_HORIZON_H = 24                  # pass list horizon
_STEP_S = 30.0                       # sampling step for track and passes

_ORBIT_YAML = Path(__file__).resolve().parents[1] / "configs" / "eosat1" / "orbit.yaml"


def mission_orbit() -> Dict:
    """EOSAT-1 elements and the canonical ground stations from orbit.yaml.

    Empty lists/strings when the file or PyYAML is missing (the tool still
    works on a pasted TLE; it just has no stations to draw)."""
    out = {"tle1": "", "tle2": "", "stations": []}
    try:
        import yaml
        d = yaml.safe_load(_ORBIT_YAML.read_text(encoding="utf-8")) or {}
    except Exception:
        return out
    out["tle1"] = str(d.get("tle_line1", "")).strip()
    out["tle2"] = str(d.get("tle_line2", "")).strip()
    for s in d.get("ground_stations") or []:
        try:
            out["stations"].append({
                "name": str(s["name"]), "lat": float(s["lat_deg"]),
                "lon": float(s["lon_deg"]), "alt_km": float(s.get("alt_km", 0.0)),
                "min_el": float(s.get("min_elevation_deg", 5.0))})
        except (KeyError, TypeError, ValueError):
            continue
    return out


def _gmst_at(epoch_utc: datetime, t_s: np.ndarray) -> np.ndarray:
    jd, fr = jday(epoch_utc.year, epoch_utc.month, epoch_utc.day, epoch_utc.hour,
                  epoch_utc.minute, epoch_utc.second + epoch_utc.microsecond * 1e-6)
    jd_all = jd + fr + t_s / 86400.0
    T = (jd_all - 2451545.0) / 36525.0
    g = (280.46061837 + 360.98564736629 * (jd_all - 2451545.0)
         + 0.000387933 * T * T - T * T * T / 38710000.0) % 360.0
    return g * _DEG


def _eci_to_ecef_many(r_eci: np.ndarray, gmst: np.ndarray) -> np.ndarray:
    c, s = np.cos(gmst), np.sin(gmst)
    return np.column_stack([c * r_eci[:, 0] + s * r_eci[:, 1],
                            -s * r_eci[:, 0] + c * r_eci[:, 1], r_eci[:, 2]])


def _geodetic(r_ecef: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(lat deg, lon deg, alt km), WGS-84, a few fixed-point iterations."""
    x, y, z = r_ecef[:, 0], r_ecef[:, 1], r_ecef[:, 2]
    p = np.hypot(x, y)
    lat = np.arctan2(z, p * (1 - _WGS84_E2))
    for _ in range(4):
        n = _WGS84_A_KM / np.sqrt(1 - _WGS84_E2 * np.sin(lat) ** 2)
        alt = p / np.cos(lat) - n
        lat = np.arctan2(z, p * (1 - _WGS84_E2 * n / (n + alt)))
    n = _WGS84_A_KM / np.sqrt(1 - _WGS84_E2 * np.sin(lat) ** 2)
    alt = p / np.cos(lat) - n
    return lat * _RAD, np.arctan2(y, x) * _RAD, alt


def _station_ecef(st: Dict) -> Tuple[np.ndarray, np.ndarray]:
    la, lo = st["lat"] * _DEG, st["lon"] * _DEG
    n = _WGS84_A_KM / math.sqrt(1 - _WGS84_E2 * math.sin(la) ** 2)
    h = st.get("alt_km", 0.0)
    r = np.array([(n + h) * math.cos(la) * math.cos(lo),
                  (n + h) * math.cos(la) * math.sin(lo),
                  (n * (1 - _WGS84_E2) + h) * math.sin(la)])
    up = np.array([math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)])
    return r, up


def _passes(epoch_utc: datetime, t_s: np.ndarray, r_ecef: np.ndarray,
            stations: List[Dict]) -> List[Dict]:
    """AOS/LOS (linear interpolation on the elevation curve) and max elevation."""
    out = []
    for st in stations:
        rs, up = _station_ecef(st)
        rho = r_ecef - rs
        el = np.degrees(np.arcsin(np.clip((rho @ up) / np.linalg.norm(rho, axis=1), -1, 1)))
        above = el >= st["min_el"]
        i = 0
        n = len(t_s)
        while i < n:
            if not above[i]:
                i += 1
                continue
            j = i
            while j + 1 < n and above[j + 1]:
                j += 1

            def cross(a, b):
                if a < 0 or b >= n:
                    return t_s[max(0, min(n - 1, a if a >= 0 else b))]
                ea, eb = el[a] - st["min_el"], el[b] - st["min_el"]
                return t_s[a] + (t_s[b] - t_s[a]) * (ea / (ea - eb) if ea != eb else 0.5)
            aos = cross(i - 1, i) if i > 0 else t_s[0]
            los = cross(j, j + 1) if j + 1 < n else t_s[-1]
            k = i + int(np.argmax(el[i:j + 1]))
            out.append({"station": st["name"],
                        "aos": (epoch_utc + timedelta(seconds=float(aos))).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "los": (epoch_utc + timedelta(seconds=float(los))).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "aos_s": round(float(aos), 1), "los_s": round(float(los), 1),
                        "max_el": round(float(el[k]), 1),
                        "truncated": bool(i == 0 or j + 1 >= n)})
            i = j + 1
    out.sort(key=lambda p: p["aos_s"])
    return out


def _two_body_eci(r0: np.ndarray, v0: np.ndarray, t_s: np.ndarray) -> np.ndarray:
    """Two-body (no J2, no drag) RK4 positions at t_s (monotonic, from 0)."""
    def acc(r):
        return -_MU_EARTH * r / np.linalg.norm(r) ** 3
    out = np.empty((len(t_s), 3))
    r, v, t = r0.astype(float).copy(), v0.astype(float).copy(), 0.0
    h_max = 10.0
    for k, tk in enumerate(t_s):
        while t < tk - 1e-9:
            h = min(h_max, tk - t)
            k1v, k1r = acc(r), v
            k2v, k2r = acc(r + 0.5 * h * k1r), v + 0.5 * h * k1v
            k3v, k3r = acc(r + 0.5 * h * k2r), v + 0.5 * h * k2v
            k4v, k4r = acc(r + h * k3r), v + h * k3v
            r = r + h / 6 * (k1r + 2 * k2r + 2 * k3r + k4r)
            v = v + h / 6 * (k1v + 2 * k2v + 2 * k3v + k4v)
            t += h
        out[k] = r
    return out


def _eclipse_flags(epoch_utc: datetime, t_s: np.ndarray, r_eci: np.ndarray) -> List[bool]:
    """Umbra flag per sample, from the same shadow model and sun ephemeris the
    simulator and planner use (track rows: [t_min, lat, lon, alt_km, ecl])."""
    from smo_common.orbit.eclipse import shadow_state
    from smo_common.orbit.propagator import _sun_eci
    jd, fr = jday(epoch_utc.year, epoch_utc.month, epoch_utc.day, epoch_utc.hour,
                  epoch_utc.minute, epoch_utc.second + epoch_utc.microsecond * 1e-6)
    out = []
    for k in range(len(t_s)):
        r = r_eci[k]
        if not np.all(np.isfinite(r)):
            out.append(False)
            continue
        out.append(bool(shadow_state(r, _sun_eci(jd + fr + float(t_s[k]) / 86400.0)).in_eclipse))
    return out


def orbit_geometry(epoch_utc: datetime, *, tle: Tuple[str, str] | None = None,
                   sv_ecef_km: Tuple[np.ndarray, np.ndarray] | None = None,
                   period_s: float = 5670.0, stations: List[Dict] | None = None) -> Dict:
    """Ground track (TRACK_ORBITS orbits) and station passes (PASS_HORIZON_H).

    ``tle`` propagates with SGP4; ``sv_ecef_km`` (position km, velocity km/s,
    ECEF at the epoch) with a two-body model, said so in ``model``."""
    stations = mission_orbit()["stations"] if stations is None else stations
    horizon = PASS_HORIZON_H * 3600.0
    t_s = np.arange(0.0, horizon + _STEP_S, _STEP_S)
    if tle is not None:
        sat = Satrec.twoline2rv(tle[0], tle[1])
        jd, fr = jday(epoch_utc.year, epoch_utc.month, epoch_utc.day, epoch_utc.hour,
                      epoch_utc.minute, epoch_utc.second + epoch_utc.microsecond * 1e-6)
        frs = fr + t_s / 86400.0
        err, r, _v = sat.sgp4_array(np.full_like(frs, jd), frs)
        r_eci = np.asarray(r)
        bad = np.asarray(err) != 0
        if bad.any():
            r_eci[bad] = np.nan
        model = "SGP4"
    else:
        r0e, v0e = sv_ecef_km
        g0 = _gmst_at(epoch_utc, np.array([0.0]))[0]
        r0 = EciEcefConverter.ecef_to_eci(r0e, g0)
        v0 = EciEcefConverter.ecef_to_eci(v0e, g0) + np.cross([0, 0, _OMEGA_EARTH], r0)
        r_eci = _two_body_eci(r0, v0, t_s)
        model = "two-body"
    r_ecef = _eci_to_ecef_many(r_eci, _gmst_at(epoch_utc, t_s))
    lat, lon, alt = _geodetic(r_ecef)
    n_track = int(min(len(t_s), math.ceil(TRACK_ORBITS * max(period_s, 600.0) / _STEP_S) + 1))
    # Spacecraft eclipse along the track: the suite's one shadow model
    # (smo_common.orbit.eclipse.shadow_state, umbra) with the propagator's sun.
    ecl = _eclipse_flags(epoch_utc, t_s[:n_track], r_eci[:n_track])
    track = [[round(float(t_s[k]) / 60.0, 2), round(float(lat[k]), 3), round(float(lon[k]), 3),
              round(float(alt[k]), 1), int(ecl[k])]
             for k in range(n_track) if np.isfinite(lat[k])]
    ok = np.isfinite(lat)
    return {
        "model": model, "step_s": _STEP_S, "horizon_h": PASS_HORIZON_H,
        "orbits": TRACK_ORBITS, "track": track,
        "stations": stations,
        "passes": _passes(epoch_utc, t_s[ok], r_ecef[ok], stations) if ok.any() else [],
        "epoch": epoch_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


# CLI Interface

def cli_tle_mode(args) -> None:
    """Handle --tle command line mode."""
    tle1 = args.tle[0]
    tle2 = args.tle[1]

    try:
        epoch_utc = datetime.fromisoformat(args.epoch)
    except ValueError:
        raise ValueError(f"Invalid epoch format. Use ISO format: 2024-01-15T12:30:00")

    if epoch_utc.tzinfo is None:
        epoch_utc = epoch_utc.replace(tzinfo=timezone.utc)

    print(f"\n[TLE to TC Command Converter]")
    print(f"Epoch: {epoch_utc.isoformat()}")

    # Propagate TLE
    try:
        pos_eci_km, vel_eci_km_s = TleToStateConverter.propagate(tle1, tle2, epoch_utc)
        print(f"TLE propagated successfully")
    except Exception as e:
        print(f"ERROR: Failed to propagate TLE: {e}")
        return

    # Convert ECI to ECEF
    jd = epoch_utc.toordinal() + 1721425.5  # Julian date approximation
    jd_frac = (epoch_utc.hour + epoch_utc.minute/60.0 + epoch_utc.second/3600.0) / 24.0
    gmst = EciEcefConverter.gmst(jd + jd_frac)

    pos_ecef_km = EciEcefConverter.eci_to_ecef(pos_eci_km, gmst)
    vel_ecef_km_s = EciEcefConverter.eci_to_ecef(vel_eci_km_s, gmst)

    # Convert to meters and m/s
    pos_ecef_m = pos_ecef_km * 1000.0
    vel_ecef_ms = vel_ecef_km_s * 1000.0

    # Generate commands
    commands = TelecommandEncoder.state_to_commands(pos_ecef_m, vel_ecef_ms)

    # Compute orbital elements for summary
    elements = OrbitAnalyzer.compute_orbital_elements(pos_eci_km, vel_eci_km_s)
    summary = OrbitSummary.format_summary(elements, epoch_utc)

    # Output
    print(summary)
    print("\n=== TELECOMMAND SEQUENCES ===")
    param_names = ['x_pos', 'y_pos', 'z_pos', 'x_vel', 'y_vel', 'z_vel']
    param_labels = ['X Position', 'Y Position', 'Z Position', 'X Velocity', 'Y Velocity', 'Z Velocity']
    param_units = ['(m)', '(m)', '(m)', '(m/s)', '(m/s)', '(m/s)']

    for name, label, unit in zip(param_names, param_labels, param_units):
        value = {
            'x_pos': pos_ecef_m[0],
            'y_pos': pos_ecef_m[1],
            'z_pos': pos_ecef_m[2],
            'x_vel': vel_ecef_ms[0],
            'y_vel': vel_ecef_ms[1],
            'z_vel': vel_ecef_ms[2],
        }[name]
        cmd = commands[name]
        print(f"{label} {unit}: {value:.3f}")
        print(f"  CMD: {cmd}")

    print("\n[Commands ready to paste into MCS command input]")


def cli_sv_mode(args) -> None:
    """Handle --sv command line mode."""
    try:
        x, y, z, vx, vy, vz = map(float, args.sv)
    except ValueError:
        raise ValueError("State vector must be 6 floats: x y z vx vy vz")

    pos_ecef_m = np.array([x, y, z])
    vel_ecef_ms = np.array([vx, vy, vz])

    # Try to compute epoch from args
    epoch_utc = datetime.now(timezone.utc)
    if hasattr(args, 'epoch') and args.epoch:
        try:
            epoch_utc = datetime.fromisoformat(args.epoch)
            if epoch_utc.tzinfo is None:
                epoch_utc = epoch_utc.replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    print(f"\n[State Vector to TC Command Converter]")
    print(f"Epoch: {epoch_utc.isoformat()}")

    # Generate commands
    commands = TelecommandEncoder.state_to_commands(pos_ecef_m, vel_ecef_ms)

    # Compute orbital elements for summary
    pos_eci_km = pos_ecef_m / 1000.0
    vel_eci_km_s = vel_ecef_ms / 1000.0
    elements = OrbitAnalyzer.compute_orbital_elements(pos_eci_km, vel_eci_km_s)
    summary = OrbitSummary.format_summary(elements, epoch_utc)

    print(summary)
    print("\n=== TELECOMMAND SEQUENCES ===")
    param_names = ['x_pos', 'y_pos', 'z_pos', 'x_vel', 'y_vel', 'z_vel']
    param_labels = ['X Position', 'Y Position', 'Z Position', 'X Velocity', 'Y Velocity', 'Z Velocity']
    param_units = ['(m)', '(m)', '(m)', '(m/s)', '(m/s)', '(m/s)']

    values = [x, y, z, vx, vy, vz]
    for name, label, unit, value in zip(param_names, param_labels, param_units, values):
        cmd = commands[name]
        print(f"{label} {unit}: {value:.3f}")
        print(f"  CMD: {cmd}")

    print("\n[Commands ready to paste into MCS command input]")


# Web Server Interface

if HAS_AIOHTTP:
    HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title data-i18n>Orbit tools</title>
__FRAME_HEAD__
<style>
/* Orbit tools. Picture first: the ground track and the passes it implies,
   then the elements, then the telecommands one disclosure deeper. */
.ot-in{ display:grid; grid-template-columns:minmax(0,1fr) 220px auto; gap:var(--sp-3) var(--sp-4);
  align-items:start; padding:var(--sp-3) var(--sp-4) var(--sp-4); }
.ot-in[hidden]{ display:none; }
.ot-in .ds-field>label{ white-space:nowrap; }
.ot-in .ds-input.tle{ font-size:var(--fs-label); letter-spacing:0; }
.ot-in .act{ display:flex; flex-direction:column; gap:var(--sp-2); padding-top:20px; }
.ot-sv{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:var(--sp-3) var(--sp-3); }
.ot-tabs{ padding:0 var(--sp-4); }
.ot-grid{ display:grid; grid-template-columns:minmax(0,1fr) 360px; gap:var(--sp-4); margin-top:var(--sp-4); }
.ot-map{ position:relative; padding:var(--sp-2) var(--sp-3) var(--sp-3); }
.ot-map svg{ display:block; width:100%; }
.ot-legend{ display:flex; flex-wrap:wrap; gap:var(--sp-1) var(--sp-4); padding:0 var(--sp-4) var(--sp-3);
  font-size:var(--fs-label); color:var(--tx3); }
.ot-legend span{ display:inline-flex; align-items:center; gap:6px; }
.ot-legend svg{ width:22px; height:10px; overflow:visible; }
.land{ fill:var(--s2); stroke:var(--line-2); stroke-width:.75; }
.sea{ fill:var(--bg); }
.trk1{ stroke:var(--fill); stroke-width:1.5; fill:none; stroke-linejoin:round; }
.trk2{ stroke:var(--tx3); stroke-width:1; fill:none; stroke-dasharray:3 3; }
.trkc{ stroke:var(--val); stroke-width:3; fill:none; stroke-linecap:round; }
.vis{ stroke:var(--tx3); stroke-width:1; fill:none; stroke-dasharray:2 3; }
.stn{ fill:var(--tx2); }
.stn-l{ fill:var(--tx2) !important; font-family:var(--sans) !important; }
.ep{ fill:var(--val); stroke:var(--bg); stroke-width:2; }
.ep-l{ fill:var(--val) !important; }
.ot-passes td{ white-space:nowrap; }
.ot-passes .elbar{ display:inline-block; vertical-align:middle; width:48px; height:6px; background:var(--s3);
  position:relative; margin-right:6px; border-radius:1px; }
.ot-passes .elbar i{ position:absolute; left:0; top:0; bottom:0; background:var(--fill); border-radius:1px; }
.ot-passes tr.next td{ color:var(--val); }
.ot-passes tr.next td:first-child{ box-shadow:inset 2px 0 0 var(--accent); }
.ot-passes{ display:flex; flex-direction:column; }
.ot-passes .ds-panel-b{ padding:0; flex:1 1 0; min-height:240px; overflow:auto; position:relative; }
.ot-tl{ padding:var(--sp-2) var(--sp-4) var(--sp-3); }
.ot-tl .bar{ fill:var(--fill); }
.ot-tl .bar:hover{ fill:var(--val); }
.ot-tl .lane{ stroke:var(--line); }
.ot-tl .lab{ fill:var(--tx2) !important; font-family:var(--sans) !important; font-size:13px !important; }
.ot-el{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); }
.ot-el>div{ padding:var(--sp-2) var(--sp-4) var(--sp-3); border-right:1px solid var(--line); border-bottom:1px solid var(--line);
  display:flex; flex-direction:column; gap:2px; }
.ot-el .k{ font-size:var(--fs-label); color:var(--tx3); }
.ot-tc td.hex{ font-family:var(--mono); font-size:var(--fs-label); color:var(--tx2); word-break:break-all; white-space:normal; }
.ot-msg{ margin:0 var(--sp-4) var(--sp-3); }
.ot-note{ font-size:var(--fs-label); color:var(--tx3); }
.ot-sec{ margin-top:var(--sp-4); }
@media (max-width:1100px){ .ot-grid{ grid-template-columns:minmax(0,1fr); } }
@media (max-width:720px){
  .ot-in{ grid-template-columns:minmax(0,1fr); }
  .ot-in .act{ padding-top:0; flex-direction:row; }
  .ot-sv{ grid-template-columns:repeat(2,minmax(0,1fr)); }
  .ot-el{ grid-template-columns:repeat(2,minmax(0,1fr)); }
  .ot-passes .elbar{ display:none; }
  .ot-passes .ds-table th,.ot-passes .ds-table td{ padding-left:8px; padding-right:8px; }
  .ot-passes .ds-panel-b{ flex:none; max-height:360px; }
}
</style>
</head>
<body>
<a class="ds-skip" href="#main" data-i18n>Skip to content</a>
__FRAME_BAR__
<main id="main" class="tf-main">

<section class="ds-panel" aria-labelledby="in-h">
  <h2 class="ds-sr" id="in-h" data-i18n>Orbit input</h2>
  <div class="ot-tabs" id="mode-tabs"></div>
  <form class="ot-in" id="form-tle" data-mode="tle" novalidate>
    <div class="ds-stack" style="gap:var(--sp-3)">
      <div class="ds-field" id="f-tle1">
        <label for="tle1" data-i18n>TLE line 1</label>
        <input class="ds-input tle" id="tle1" type="text" spellcheck="false" autocomplete="off" maxlength="80">
      </div>
      <div class="ds-field" id="f-tle2">
        <label for="tle2" data-i18n>TLE line 2</label>
        <input class="ds-input tle" id="tle2" type="text" spellcheck="false" autocomplete="off" maxlength="80">
      </div>
    </div>
    <div class="ds-stack" style="gap:var(--sp-3)">
      <div class="ds-field" id="f-tle_epoch">
        <label for="tle_epoch" data-i18n>Epoch (UTC)</label>
        <input class="ds-input" id="tle_epoch" type="text" spellcheck="false" placeholder="2026-11-02T12:00:00">
      </div>
      <button type="button" class="ds-btn ghost sm" id="load-eosat" data-i18n>Use EOSAT-1 elements</button>
    </div>
    <div class="act">
      <button type="submit" class="ds-btn primary" id="go-tle" data-i18n>Convert TLE</button>
    </div>
  </form>
  <form class="ot-in" id="form-sv" data-mode="sv" hidden novalidate>
    <div class="ot-sv">
      <div class="ds-field"><label for="sv_x" data-i18n>Position X (ECEF)</label><span class="ds-input-wrap"><input class="ds-input" id="sv_x" inputmode="decimal" placeholder="6878000"><span class="u">m</span></span></div>
      <div class="ds-field"><label for="sv_y" data-i18n>Position Y (ECEF)</label><span class="ds-input-wrap"><input class="ds-input" id="sv_y" inputmode="decimal" placeholder="0"><span class="u">m</span></span></div>
      <div class="ds-field"><label for="sv_z" data-i18n>Position Z (ECEF)</label><span class="ds-input-wrap"><input class="ds-input" id="sv_z" inputmode="decimal" placeholder="0"><span class="u">m</span></span></div>
      <div class="ds-field"><label for="sv_vx" data-i18n>Velocity X (ECEF)</label><span class="ds-input-wrap"><input class="ds-input" id="sv_vx" inputmode="decimal" placeholder="0"><span class="u">m/s</span></span></div>
      <div class="ds-field"><label for="sv_vy" data-i18n>Velocity Y (ECEF)</label><span class="ds-input-wrap"><input class="ds-input" id="sv_vy" inputmode="decimal" placeholder="-1000"><span class="u">m/s</span></span></div>
      <div class="ds-field"><label for="sv_vz" data-i18n>Velocity Z (ECEF)</label><span class="ds-input-wrap"><input class="ds-input" id="sv_vz" inputmode="decimal" placeholder="7550"><span class="u">m/s</span></span></div>
    </div>
    <div class="ds-field" id="f-sv_epoch">
      <label for="sv_epoch" data-i18n>Epoch (UTC)</label>
      <input class="ds-input" id="sv_epoch" type="text" spellcheck="false" placeholder="2026-11-02T12:00:00">
      <span class="hint" data-i18n>Propagated two-body: no J2, no drag.</span>
    </div>
    <div class="act">
      <button type="submit" class="ds-btn primary" id="go-sv" data-i18n>Convert state vector</button>
    </div>
  </form>
  <div class="ot-msg" id="msg" role="alert"></div>
</section>

<div class="ot-grid">
  <section class="ds-panel" aria-labelledby="map-h">
    <div class="ds-panel-h"><span id="map-h" data-i18n>Ground track</span><span class="r" id="map-meta"></span></div>
    <div class="ot-map" id="map"></div>
    <div class="ot-legend" id="map-legend"></div>
  </section>
  <section class="ds-panel ot-passes" aria-labelledby="pass-h">
    <div class="ds-panel-h"><span id="pass-h" data-i18n>Passes</span><span class="r" id="pass-meta"></span></div>
    <div class="ds-panel-b" id="passes" tabindex="0" aria-labelledby="pass-h"></div>
  </section>
</div>

<section class="ds-panel ot-sec" aria-labelledby="tl-h">
  <div class="ds-panel-h"><span id="tl-h" data-i18n>Contact timeline</span><span class="r" id="tl-meta"></span></div>
  <div class="ot-tl" id="timeline"></div>
</section>

<section class="ds-panel ot-sec" aria-labelledby="el-h">
  <div class="ds-panel-h"><span id="el-h" data-i18n>Orbit at epoch</span><span class="r" id="el-meta"></span></div>
  <div class="ot-el" id="elements"></div>
  <div id="tcs"></div>
</section>
</main>
__FRAME_SCRIPT__
<script type="module">
import { renderValue, renderNoData, renderTabs, mountTabs, renderBanner, renderButton,
         setDisabled, setEnabled, glyph, esc } from "/static/shared/components.js";
import I18n from "/static/shared/i18n.js";
const T = (s, v) => I18n.tText(s, v);
const $ = (id) => document.getElementById(id);
const BOOT = __BOOT_JSON__;
let LAND = null;
let mode = "tle", last = null, lastSrc = "", busy = false;
// Logbook context (tool_frame mounts the panel): which input is in use.
window.c2oLogbookContext = () => ({ page: mode });

/* ── input validation (TLE format: 69 columns, modulo-10 checksum) ── */
function tleChecksum(line) {
  let s = 0;
  for (const c of line.slice(0, 68)) { if (c >= "0" && c <= "9") s += +c; else if (c === "-") s += 1; }
  return s % 10;
}
function checkTle(line, n) {
  if (!line) return T("Enter TLE line {{n}}.", { n });
  if (!line.startsWith(n + " ")) return T('Line {{n}} must start with "{{n}} ".', { n });
  if (line.length !== 69) return T("69 characters expected, {{got}} entered.", { got: line.length });
  const want = tleChecksum(line), got = line[68];
  if (String(want) !== got) return T("Checksum fails: column 69 should be {{want}}.", { want });
  return "";
}
function parseEpoch(s) {
  if (!s) return null;
  const d = new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(s) ? s : s + "Z");
  return isNaN(d) ? null : d;
}
function setField(id, err) {
  const f = $("f-" + id), inp = $(id);
  if (!f) return;
  f.classList.toggle("is-invalid", !!err);
  let e = f.querySelector(".err");
  if (err) {
    if (!e) { e = document.createElement("span"); e.className = "err"; e.id = id + "-err"; f.appendChild(e); }
    e.innerHTML = glyph("alarm-up") + esc(err);
    inp.setAttribute("aria-invalid", "true"); inp.setAttribute("aria-describedby", id + "-err");
  } else {
    if (e) e.remove();
    inp.removeAttribute("aria-invalid"); inp.removeAttribute("aria-describedby");
  }
}
function tleEpoch(l1) {           // TLE epoch from line 1 columns 19-32 (YYDDD.DDDDDDDD)
  const m = /^1 .{16}(\d{2})(\d{3}\.\d+)/.exec(l1 || "");
  if (!m) return null;
  const yy = +m[1], y = yy < 57 ? 2000 + yy : 1900 + yy;
  return new Date(Date.UTC(y, 0, 1) + (parseFloat(m[2]) - 1) * 86400000);
}
function validateTle(show) {
  const e1 = checkTle($("tle1").value.trim(), 1), e2 = checkTle($("tle2").value.trim(), 2);
  const ep = parseEpoch($("tle_epoch").value.trim());
  const e3 = ep ? "" : T("Use ISO 8601, for example 2026-11-02T12:00:00.");
  if (show) { setField("tle1", e1); setField("tle2", e2); setField("tle_epoch", e3); }
  const reason = e1 ? T("TLE line 1: {{e}}", { e: e1 }) : e2 ? T("TLE line 2: {{e}}", { e: e2 })
    : e3 ? T("Epoch: {{e}}", { e: e3 }) : "";
  if (busy) return !reason;
  if (reason) setDisabled($("go-tle"), reason); else setEnabled($("go-tle"));
  return !reason;
}
const SV = ["sv_x", "sv_y", "sv_z", "sv_vx", "sv_vy", "sv_vz"];
function validateSv() {
  const bad = SV.filter((k) => !Number.isFinite(parseFloat($(k).value)));
  const ep = parseEpoch($("sv_epoch").value.trim());
  const reason = bad.length ? T("Enter all six state vector components ({{n}} missing).", { n: bad.length })
    : !ep ? T("Epoch: {{e}}", { e: T("Use ISO 8601, for example 2026-11-02T12:00:00.") }) : "";
  if (!busy) { if (reason) setDisabled($("go-sv"), reason); else setEnabled($("go-sv")); }
  return !reason;
}

/* ── running state on the button that was pressed ── */
function setBusy(btn, on) {
  busy = on;
  if (on) {
    btn.dataset.label = btn.textContent;
    btn.classList.add("is-active");
    btn.innerHTML = `<span class="ds-run" aria-hidden="true"></span>${esc(T("Computing…"))}`;
    btn.setAttribute("aria-busy", "true");
  } else {
    btn.classList.remove("is-active");
    btn.textContent = btn.dataset.label || btn.textContent;
    btn.removeAttribute("aria-busy");
  }
}

async function run(kind) {
  const btn = $(kind === "tle" ? "go-tle" : "go-sv");
  if (btn.getAttribute("aria-disabled") === "true" || busy) return;
  const body = kind === "tle"
    ? { tle1: $("tle1").value.trim(), tle2: $("tle2").value.trim(), epoch: $("tle_epoch").value.trim() }
    : Object.assign({ epoch: $("sv_epoch").value.trim() },
        Object.fromEntries(SV.map((k) => [k.slice(3), parseFloat($(k).value)])));
  setBusy(btn, true);
  $("msg").innerHTML = "";
  try {
    const r = await fetch(kind === "tle" ? "api/tle" : "api/sv", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const j = await r.json().catch(() => ({ error: T("Server error {{status}}", { status: r.status }) }));
    if (!r.ok || j.error) throw new Error(j.error || T("Server error {{status}}", { status: r.status }));
    last = j; lastSrc = kind;
    renderAll();
  } catch (e) {
    $("msg").innerHTML = renderBanner("alarm", T("Could not convert: {{msg}}", { msg: e.message }));
  } finally {
    setBusy(btn, false);
    kind === "tle" ? validateTle(false) : validateSv();
  }
}

/* ── formatting ── */
const pad = (n) => String(n).padStart(2, "0");
const hhmm = (d) => `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`;
const mmss = (s) => `${Math.floor(s / 60)}:${pad(Math.round(s % 60))}`;
const fmtNum = (x, d) => Number(x).toLocaleString(I18n.getLang() === "fr" ? "fr-FR" : "en-GB",
  { minimumFractionDigits: d, maximumFractionDigits: d });

/* ── ground track ── */
function proj(W, H) { return (lon, lat) => [((lon + 180) / 360) * W, ((90 - lat) / 180) * H]; }
function pathOf(pts, P) {          // split where the track wraps the antimeridian
  let d = "", prev = null;
  for (const [lon, lat] of pts) {
    const [x, y] = P(lon, lat);
    d += (prev === null || Math.abs(lon - prev) > 180 ? "M" : "L") + x.toFixed(1) + " " + y.toFixed(1);
    prev = lon;
  }
  return d;
}
function visCircle(st, altKm) {     // station visibility edge at its mask, for the mean altitude
  const Re = 6371, el = st.min_el * Math.PI / 180;
  const lam = Math.acos((Re / (Re + altKm)) * Math.cos(el)) - el;
  const la = st.lat * Math.PI / 180, lo = st.lon * Math.PI / 180, out = [];
  for (let k = 0; k <= 96; k++) {
    const az = (k / 96) * 2 * Math.PI;
    const lat2 = Math.asin(Math.sin(la) * Math.cos(lam) + Math.cos(la) * Math.sin(lam) * Math.cos(az));
    const lon2 = lo + Math.atan2(Math.sin(az) * Math.sin(lam) * Math.cos(la), Math.cos(lam) - Math.sin(la) * Math.sin(lat2));
    out.push([((lon2 * 180 / Math.PI + 540) % 360) - 180, lat2 * 180 / Math.PI]);
  }
  return out;
}
/* The ground track is the shared pictorial module (shared/ui-viz/groundtrack.js,
 * served at /static/shared/viz/): the same map as the planner, with the
 * spacecraft eclipse along the track, station visibility at each mask and
 * the next AOS in a fixed strip. "Now" is the conversion epoch. If the
 * module cannot load, the inline SVG below draws the plain track. */
let gtView = null;
function gtModel() {
  const stations = ((last && last.stations) || BOOT.stations || []).map((s) =>
    ({ name: s.name, lat: s.lat, lon: s.lon, maskDeg: s.min_el }));
  if (!last) return { stations };
  const ep = new Date(last.epoch).getTime();
  const tr = (last.track || []).map((p) => ({ t: ep + p[0] * 60000, lat: p[1], lon: p[2], alt_km: p[3], in_eclipse: !!p[4] }));
  return {
    nowMs: ep, track: tr, stations,
    position: tr.length ? { lat: tr[0].lat, lon: tr[0].lon, altKm: tr[0].alt_km, src: T("epoch") } : null,
    contacts: (last.passes || []).map((ps) => ({ station: ps.station, aos: ep + ps.aos_s * 1000, los: ep + ps.los_s * 1000, maxEl: ps.max_el })),
    eclipseSource: "ground_propagator",
  };
}
function drawMap() {
  if (gtView) { gtView.update(gtModel()); return; }
  const host = $("map");
  const W = Math.max(280, host.clientWidth - 24), H = Math.round(W / 2);
  const P = proj(W, H);
  let s = `<svg class="tf-plot" viewBox="0 0 ${W} ${H + 20}" width="${W}" height="${H + 20}" role="img" aria-labelledby="map-h map-desc">`;
  s += `<desc id="map-desc">${esc(mapDesc())}</desc>`;
  s += `<rect class="sea" x="0" y="0" width="${W}" height="${H}"/>`;
  if (LAND) for (const ring of LAND) {
    let d = "";
    for (let i = 0; i < ring.length; i += 2) { const [x, y] = P(ring[i], ring[i + 1]); d += (i ? "L" : "M") + x.toFixed(1) + " " + y.toFixed(1); }
    s += `<path class="land" d="${d}Z"/>`;
  }
  for (let lon = -150; lon <= 150; lon += 30) { const [x] = P(lon, 0); s += `<line class="grid" x1="${x}" y1="0" x2="${x}" y2="${H}"/>`; }
  for (let lat = -60; lat <= 60; lat += 30) { const [, y] = P(0, lat); s += `<line class="grid" x1="0" y1="${y}" x2="${W}" y2="${y}"/>`; }
  s += `<rect class="ax" x="0" y="0" width="${W}" height="${H}"/>`;
  const lonStep = W < 520 ? 120 : 60, latStep = H < 240 ? 60 : 30;
  for (let lon = -180; lon <= 180; lon += lonStep) {
    const [x] = P(lon, 0);
    s += `<text x="${x}" y="${H + 14}" text-anchor="${lon === -180 ? "start" : lon === 180 ? "end" : "middle"}">${Math.abs(lon)}°${lon < 0 ? "W" : lon > 0 ? "E" : ""}</text>`;
  }
  for (let lat = -60; lat <= 60; lat += latStep) { const [, y] = P(-180, lat); s += `<text x="4" y="${y - 3}">${Math.abs(lat)}°${lat < 0 ? "S" : lat > 0 ? "N" : ""}</text>`; }
  const stations = (last && last.stations) || BOOT.stations || [];
  const meanAlt = last && last.track && last.track.length
    ? last.track.reduce((a, p) => a + p[3], 0) / last.track.length : 513;
  for (const st of stations) s += `<path class="vis" d="${pathOf(visCircle(st, meanAlt), P)}"/>`;
  if (last && last.track && last.track.length) {
    const per = (last.elements && last.elements.period_min) || 94.5;
    const o1 = last.track.filter((p) => p[0] <= per), o2 = last.track.filter((p) => p[0] >= per);
    s += `<path class="trk2" d="${pathOf(o2.map((p) => [p[2], p[1]]), P)}"/>`;
    s += `<path class="trk1" d="${pathOf(o1.map((p) => [p[2], p[1]]), P)}"/>`;
    const inC = (tmin) => (last.passes || []).some((ps) => tmin * 60 >= ps.aos_s && tmin * 60 <= ps.los_s);
    let run = [];
    const flush = () => { if (run.length > 1) s += `<path class="trkc" d="${pathOf(run, P)}"/>`; run = []; };
    for (const p of last.track) { if (inC(p[0])) run.push([p[2], p[1]]); else flush(); }
    flush();
    const [ex, ey] = P(last.track[0][2], last.track[0][1]);
    s += `<circle class="ep" cx="${ex}" cy="${ey}" r="5"/><text class="ep-l" x="${ex + 8}" y="${ey + 4}">${esc(T("epoch"))}</text>`;
  }
  for (const st of stations) {
    const [x, y] = P(st.lon, st.lat);
    s += `<path class="stn" d="M${x} ${y - 6}L${x + 5} ${y + 3}L${x - 5} ${y + 3}Z"/>`;
    const right = x < W - 90;
    s += `<text class="stn-l" x="${right ? x + 8 : x - 8}" y="${y + 4}" text-anchor="${right ? "start" : "end"}">${esc(st.name)}</text>`;
  }
  s += `</svg>`;
  host.innerHTML = s;
}
function mapDesc() {
  if (!last) return T("Map of the ground stations; no orbit converted yet.");
  return T("Ground track for {{n}} orbits from {{epoch}}, {{p}} passes in the next {{h}} h.",
    { n: last.orbits, epoch: last.epoch, p: (last.passes || []).length, h: last.horizon_h });
}
function legend() {
  if (gtView) { $("map-legend").innerHTML = ""; return; }
  const sw = (cls, kind) => kind === "tri"
    ? `<svg viewBox="0 0 22 10" aria-hidden="true"><path class="stn" d="M11 0L16 9L6 9Z"/></svg>`
    : `<svg viewBox="0 0 22 10" aria-hidden="true"><line class="${cls}" x1="1" y1="5" x2="21" y2="5"/></svg>`;
  $("map-legend").innerHTML =
    `<span>${sw("trk1")}${esc(T("First orbit"))}</span>` +
    `<span>${sw("trk2")}${esc(T("Next orbits"))}</span>` +
    `<span>${sw("trkc")}${esc(T("In contact"))}</span>` +
    `<span>${sw("", "tri")}${esc(T("Ground station"))}</span>` +
    `<span>${sw("vis")}${esc(T("Visibility edge at the elevation mask"))}</span>`;
}

/* ── passes: list + 24 h contact timeline ── */
function drawPasses() {
  const host = $("passes");
  if (!last) { host.innerHTML = `<p class="tf-empty">${esc(T("Convert an orbit to list its passes."))}</p>`; $("pass-meta").textContent = ""; return; }
  const ps = last.passes || [];
  const mask = (last.stations[0] || {}).min_el ?? 5;
  $("pass-meta").textContent = T("next {{h}} h · mask {{m}}°", { h: last.horizon_h, m: mask });
  if (!ps.length) { host.innerHTML = `<p class="tf-empty">${esc(T("No pass above the elevation mask in the next {{h}} h.", { h: last.horizon_h }))}</p>`; return; }
  const ep = new Date(last.epoch);
  // The next five; the rest behind "more" (review §5: a 47-row list).
  const shown = allPasses ? ps : ps.slice(0, 5);
  host.innerHTML = `<table class="ds-table"><thead><tr><th>${esc(T("Station"))}</th><th>${esc(T("AOS (UTC)"))}</th>` +
    `<th class="n">${esc(T("Duration"))}</th><th>${esc(T("Max elevation"))}</th></tr></thead><tbody>` +
    shown.map((p, i) => {
      const a = new Date(ep.getTime() + p.aos_s * 1000);
      const day = a.getUTCDate() !== ep.getUTCDate() ? ` <small>+1 d</small>` : "";
      return `<tr class="${i === 0 ? "next" : ""}"><td>${esc(p.station)}</td>` +
        `<td class="num">${hhmm(a)}${day}</td><td class="n">${mmss(p.los_s - p.aos_s)}</td>` +
        `<td class="num"><span class="elbar" aria-hidden="true"><i style="width:${(p.max_el / 90 * 100).toFixed(0)}%"></i></span>${fmtNum(p.max_el, 1)}°</td></tr>`;
    }).join("") + `</tbody></table>` +
    (ps.length > shown.length
      ? `<p><button type="button" class="ds-btn ghost sm" id="passes-more">${esc(T("Show all {{n}} passes", { n: ps.length }))}</button></p>` : "");
  const more = $("passes-more");
  if (more) more.addEventListener("click", () => { allPasses = true; drawPasses(); });
}
let allPasses = false;
function drawTimeline() {
  const host = $("timeline");
  const stations = (last && last.stations) || BOOT.stations || [];
  const W = Math.max(300, host.clientWidth - 32), L = W < 500 ? 76 : 104, laneH = 26, top = 4;
  const H = top + stations.length * laneH + 22, span = ((last && last.horizon_h) || 24) * 3600;
  const X = (t) => L + (t / span) * (W - L - 8);
  let s = `<svg class="tf-plot" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-labelledby="tl-h tl-desc">` +
    `<desc id="tl-desc">${esc(T("One lane per ground station over the next {{h}} h; each bar is a pass, its height the maximum elevation.", { h: (last && last.horizon_h) || 24 }))}</desc>`;
  const ep = last ? new Date(last.epoch) : new Date();
  const step = W < 600 ? 6 : 3;
  for (let h = 0; h <= span / 3600; h += step) {
    const x = X(h * 3600), d = new Date(ep.getTime() + h * 3600000);
    s += `<line class="grid" x1="${x}" y1="${top}" x2="${x}" y2="${H - 18}"/>` +
         `<text x="${x}" y="${H - 4}" text-anchor="${h === 0 ? "start" : "middle"}">${hhmm(d)}</text>`;
  }
  stations.forEach((st, i) => {
    const y = top + i * laneH;
    s += `<line class="lane" x1="${L}" y1="${y + laneH}" x2="${W - 8}" y2="${y + laneH}"/>` +
         `<text class="lab" x="0" y="${y + laneH - 8}">${esc(st.name)}</text>`;
    for (const p of (last && last.passes || []).filter((q) => q.station === st.name)) {
      const h = 4 + (laneH - 8) * Math.min(1, p.max_el / 90);
      const a = new Date(ep.getTime() + p.aos_s * 1000), b = new Date(ep.getTime() + p.los_s * 1000);
      s += `<rect class="bar" x="${X(p.aos_s).toFixed(1)}" y="${(y + laneH - 2 - h).toFixed(1)}" width="${Math.max(2, X(p.los_s) - X(p.aos_s)).toFixed(1)}" height="${h.toFixed(1)}">` +
           `<title>${esc(`${st.name} ${hhmm(a)}–${hhmm(b)} UTC · ${T("max elevation")} ${fmtNum(p.max_el, 1)}°`)}</title></rect>`;
    }
  });
  s += `<line class="ax" x1="${L}" y1="${H - 18}" x2="${W - 8}" y2="${H - 18}"/></svg>`;
  host.innerHTML = s;
  $("tl-meta").textContent = last ? T("UTC from epoch · bar height = maximum elevation") : "";
}

/* ── elements + telecommands ── */
const PARAM = {
  x_pos: ["0x0231", () => T("Position X"), "m"], y_pos: ["0x0232", () => T("Position Y"), "m"], z_pos: ["0x0233", () => T("Position Z"), "m"],
  x_vel: ["0x0234", () => T("Velocity X"), "m/s"], y_vel: ["0x0235", () => T("Velocity Y"), "m/s"], z_vel: ["0x0236", () => T("Velocity Z"), "m/s"],
};
function drawElements() {
  const host = $("elements");
  if (!last) { host.innerHTML = ""; $("tcs").innerHTML = ""; $("el-meta").textContent = ""; return; }
  const e = last.elements, Re = 6371;
  const cell = (k, v, u, d) => `<div><span class="k">${esc(k)}</span>${renderValue(v, { units: u, digits: d })}</div>`;
  host.innerHTML = [
    cell(T("Semi-major axis"), e.a_km, "km", 1), cell(T("Eccentricity"), e.e, "", 5),
    cell(T("Inclination"), e.i_deg, "°", 3), cell(T("RAAN"), e.raan_deg, "°", 3),
    cell(T("Argument of perigee"), e.aop_deg, "°", 2), cell(T("True anomaly"), e.ta_deg, "°", 2),
    cell(T("Period"), e.period_min, "min", 2), cell(T("Altitude"), e.altitude_km, "km", 1),
    cell(T("Perigee altitude"), e.a_km * (1 - e.e) - Re, "km", 1), cell(T("Apogee altitude"), e.a_km * (1 + e.e) - Re, "km", 1),
  ].join("");
  $("el-meta").textContent = `${last.epoch} · ${lastSrc === "tle" ? "SGP4" : T("two-body")}`;
  const st = last.state_ecef || {};
  const rows = Object.entries(last.commands || {}).map(([k, hex]) => {
    const [pid, nameFn, u] = PARAM[k] || [k, () => k, ""];
    const name = nameFn();
    const val = st[k];
    return `<tr><td class="num">${pid}</td><td>${esc(name)}</td>` +
      `<td class="n">${val === undefined ? renderNoData() : renderValue(val, { units: u, digits: u === "m" ? 1 : 3 })}</td>` +
      `<td class="hex">${esc(hex)}</td><td>${renderButton({ label: T("Copy"), kind: "ghost", size: "sm", attrs: `data-copy="${esc(hex)}"` })}</td></tr>`;
  }).join("");
  const n = Object.keys(last.commands || {}).length;
  $("tcs").innerHTML = `<details class="ds-disclosure" id="tc-d"${$("tc-d") && $("tc-d").open ? " open" : ""}>` +
    `<summary>${esc(T("Telecommands: {{n}} × TC(20,1) set parameter", { n }))}<span class="r">${esc(T("ECEF state at epoch"))}</span></summary>` +
    `<div class="bd ot-tc" style="padding-left:var(--sp-4)"><table class="ds-table"><thead><tr><th>${esc(T("Parameter"))}</th><th>${esc(T("Name"))}</th>` +
    `<th class="n">${esc(T("Value"))}</th><th>${esc(T("Command (hex)"))}</th><th><span class="ds-sr">${esc(T("Copy"))}</span></th></tr></thead><tbody>${rows}</tbody></table>` +
    `<div class="ds-row" style="margin-top:var(--sp-2)">${renderButton({ label: T("Copy all commands"), size: "sm", attrs: `data-copy-all="1"` })}</div></div></details>`;
}

function drawMeta() {
  const tle1 = $("tle1").value.trim();
  const te = tleEpoch(tle1), ep = parseEpoch($("tle_epoch").value.trim());
  let meta = last ? T("{{n}} orbits from epoch", { n: last.orbits }) + " · " + (lastSrc === "tle" ? "SGP4" : T("two-body")) : "";
  if (last && lastSrc === "tle" && te && ep) {
    const days = Math.abs(ep - te) / 86400000;
    if (days > 14) meta += " · " + T("{{d}} days from the TLE epoch: accuracy degrades", { d: Math.round(days) });
  }
  $("map-meta").textContent = meta;
  document.getElementById("tf-meta").textContent = last
    ? `${T("Epoch")} ${last.epoch}` : T("EOSAT-1 · TLE or state vector to TC(20,1)");
}

function renderAll() { drawMeta(); drawMap(); legend(); drawPasses(); drawTimeline(); drawElements(); }

/* ── wiring ── */
function drawTabs() {
  $("mode-tabs").innerHTML = renderTabs([{ id: "tle", label: T("Two-line elements") }, { id: "sv", label: T("State vector") }],
    mode, { label: T("Input"), panel: "form-" + mode });
  mountTabs($("mode-tabs"), (id) => { mode = id; $("form-tle").hidden = id !== "tle"; $("form-sv").hidden = id !== "sv"; drawTabs(); });
}
$("form-tle").addEventListener("submit", (ev) => { ev.preventDefault(); validateTle(true); run("tle"); });
$("form-sv").addEventListener("submit", (ev) => { ev.preventDefault(); validateSv(); run("sv"); });
for (const id of ["tle1", "tle2", "tle_epoch"]) {
  $(id).addEventListener("input", () => validateTle(!!$("f-" + id).querySelector(".err")));
  $(id).addEventListener("blur", () => validateTle(true));
}
for (const id of [...SV, "sv_epoch"]) $(id).addEventListener("input", validateSv);
$("load-eosat").addEventListener("click", () => { $("tle1").value = BOOT.tle1; $("tle2").value = BOOT.tle2; validateTle(true); });
document.addEventListener("click", async (ev) => {
  const b = ev.target.closest("[data-copy],[data-copy-all]");
  if (!b) return;
  const text = b.dataset.copy || Object.values(last.commands || {}).join("\n");
  try { await navigator.clipboard.writeText(text); b.textContent = T("Copied"); setTimeout(() => drawElements(), 1200); } catch (e) { /* no clipboard */ }
});
// The default epoch is the MISSION clock (sim time in training), the one
// mission control and the planner show, not this browser's wall clock.
async function missionNow() {
  try {
    const r = await fetch("/api/now", { cache: "no-store" });
    if (r.ok) { const j = await r.json(); if (j.utc) return new Date(j.utc); }
  } catch (e) { /* server too old or offline */ }
  return new Date();
}
const now = await missionNow(); now.setUTCSeconds(0, 0);
const iso = now.toISOString().slice(0, 16) + ":00";
$("tle_epoch").value = iso; $("sv_epoch").value = iso;
$("tle1").value = BOOT.tle1; $("tle2").value = BOOT.tle2;
if (!BOOT.tle1) $("load-eosat").hidden = true;
drawTabs(); validateTle(false); validateSv(); renderAll();
new ResizeObserver(() => { drawMap(); drawTimeline(); }).observe($("map"));
import("/static/shared/viz/groundtrack.js").then((GT) => {
  $("map").innerHTML = "";
  gtView = GT.mount($("map"), { t: T });
  legend(); drawMap();
}).catch(() => {
  import("/static/orbit/wide-basemap.js").then((m) => { LAND = m.LAND; drawMap(); }).catch(() => { /* graticule only */ });
});
const rerender = () => { drawTabs(); renderAll(); validateTle(!!document.querySelector(".is-invalid")); validateSv(); };
window.addEventListener("smo:i18nready", rerender);
window.addEventListener("smo:langchange", rerender);
if (BOOT.tle1) run("tle");
</script>
</body>
</html>
"""

    async def handle_now(request):
        """GET /api/now — the mission clock this page should start from.

        Mission control and the planner run on SIMULATION time in training
        (SMO_TIME_SOURCE=sim, the start.sh and compose default); this tool
        used the browser's wall clock, so its epoch, passes and "Next AOS"
        disagreed with theirs (SCREEN_REVIEW §5). Sim time comes from the
        same state endpoint the MCS polls (SMO_SIM_STATE_URL); wall clock
        when the source is "real" or the simulator cannot be reached."""
        import os
        import urllib.request
        source = (os.environ.get("SMO_TIME_SOURCE") or "sim").strip().lower()
        url = (os.environ.get("SMO_SIM_STATE_URL") or "").strip()
        if source == "sim" and url:
            def _fetch():
                with urllib.request.urlopen(url, timeout=1.5) as r:
                    return json.loads(r.read().decode())
            try:
                st = await asyncio.get_running_loop().run_in_executor(None, _fetch)
                t = str(st.get("sim_time") or "")
                if t:
                    when = datetime.fromisoformat(t.replace("Z", "+00:00"))
                    if when.tzinfo is None:
                        when = when.replace(tzinfo=timezone.utc)
                    return web.json_response({
                        "utc": when.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "source": "sim"})
            except Exception:  # noqa: BLE001 — fall back to the wall clock
                pass
        return web.json_response({
            "utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": "sim-unreachable" if source == "sim" and url else "wall"})

    async def handle_index(request):
        """Serve the web interface."""
        m = mission_orbit()
        boot = json.dumps({"tle1": m["tle1"], "tle2": m["tle2"], "stations": m["stations"]})
        page = (HTML_TEMPLATE
                .replace("__FRAME_HEAD__", tool_frame.head())
                .replace("__FRAME_BAR__", tool_frame.bar('<span data-i18n>Orbit tools</span>',
                                                        logbook="orbit"))
                .replace("__FRAME_SCRIPT__", tool_frame.SCRIPT)
                .replace("__BOOT_JSON__", boot.replace("</", "<\\/")))
        return tool_html_response(page, request.app)

    async def handle_basemap(request):
        """Natural Earth 110 m land rings, shared with the planner wall view
        (one copy of the data in the repo). 404 -> the map draws a graticule only."""
        if _BASEMAP.is_file():
            return web.FileResponse(_BASEMAP, headers={"Cache-Control": "public, max-age=86400"})
        raise web.HTTPNotFound()

    async def handle_tle_api(request):
        """API endpoint for TLE conversion."""
        try:
            data = await request.json()
            tle1 = data.get('tle1', '').strip()
            tle2 = data.get('tle2', '').strip()
            epoch_str = data.get('epoch', datetime.now(timezone.utc).isoformat())

            if not tle1 or not tle2:
                return web.json_response({'error': 'Missing TLE lines'}, status=400)

            try:
                epoch_utc = datetime.fromisoformat(epoch_str.replace('Z', '+00:00'))
            except ValueError:
                return web.json_response({'error': f'Invalid epoch format: {epoch_str}'}, status=400)

            if epoch_utc.tzinfo is None:
                epoch_utc = epoch_utc.replace(tzinfo=timezone.utc)

            # Propagate TLE
            try:
                pos_eci_km, vel_eci_km_s = TleToStateConverter.propagate(tle1, tle2, epoch_utc)
            except Exception as e:
                return web.json_response({'error': f'TLE propagation failed: {str(e)}'}, status=400)

            # Convert ECI to ECEF
            jd = epoch_utc.toordinal() + 1721425.5
            jd_frac = (epoch_utc.hour + epoch_utc.minute/60.0 + epoch_utc.second/3600.0) / 24.0
            gmst = EciEcefConverter.gmst(jd + jd_frac)

            pos_ecef_km = EciEcefConverter.eci_to_ecef(pos_eci_km, gmst)
            vel_ecef_km_s = EciEcefConverter.eci_to_ecef(vel_eci_km_s, gmst)

            pos_ecef_m = pos_ecef_km * 1000.0
            vel_ecef_ms = vel_ecef_km_s * 1000.0

            # Generate commands
            commands = TelecommandEncoder.state_to_commands(pos_ecef_m, vel_ecef_ms)

            # Compute orbital elements
            elements = OrbitAnalyzer.compute_orbital_elements(pos_eci_km, vel_eci_km_s)
            summary = OrbitSummary.format_summary(elements, epoch_utc)

            return web.json_response({
                'summary': summary,
                'commands': commands,
                'elements': elements,
                'state_ecef': _state_dict(pos_ecef_m, vel_ecef_ms),
                **orbit_geometry(epoch_utc, tle=(tle1, tle2),
                                 period_s=elements['period_s']),
            })

        except Exception as e:
            return web.json_response({'error': f'Internal error: {str(e)}'}, status=500)

    async def handle_sv_api(request):
        """API endpoint for state vector conversion."""
        try:
            data = await request.json()
            x = float(data.get('x', 0))
            y = float(data.get('y', 0))
            z = float(data.get('z', 0))
            vx = float(data.get('vx', 0))
            vy = float(data.get('vy', 0))
            vz = float(data.get('vz', 0))
            epoch_str = data.get('epoch', datetime.now(timezone.utc).isoformat())

            try:
                epoch_utc = datetime.fromisoformat(epoch_str.replace('Z', '+00:00'))
            except ValueError:
                return web.json_response({'error': f'Invalid epoch format: {epoch_str}'}, status=400)

            if epoch_utc.tzinfo is None:
                epoch_utc = epoch_utc.replace(tzinfo=timezone.utc)

            pos_ecef_m = np.array([x, y, z])
            vel_ecef_ms = np.array([vx, vy, vz])

            # Generate commands
            commands = TelecommandEncoder.state_to_commands(pos_ecef_m, vel_ecef_ms)

            # Compute orbital elements
            pos_eci_km = pos_ecef_m / 1000.0
            vel_eci_km_s = vel_ecef_ms / 1000.0
            elements = OrbitAnalyzer.compute_orbital_elements(pos_eci_km, vel_eci_km_s)
            summary = OrbitSummary.format_summary(elements, epoch_utc)

            if not np.isfinite(elements.get('period_s', float('nan'))) or elements['a_km'] <= 0:
                return web.json_response(
                    {'error': 'State vector is not a closed orbit (check the units: metres and m/s)'},
                    status=400)
            return web.json_response({
                'summary': summary,
                'commands': commands,
                'elements': elements,
                'state_ecef': _state_dict(pos_ecef_m, vel_ecef_ms),
                **orbit_geometry(epoch_utc, sv_ecef_km=(pos_eci_km, vel_eci_km_s),
                                 period_s=elements['period_s']),
            })

        except Exception as e:
            return web.json_response({'error': f'Internal error: {str(e)}'}, status=500)

    async def start_web_server(port: int = 8093) -> None:
        """Start the aiohttp web server."""
        # Shared HTTP policy + design system / language runtime (R3 A8, §8).
        app = setup_tool_app(web.Application())
        # Participant logbook (LOGBOOK_SPEC.md): private, /api/logbook here.
        from smo_common.logbook import register_logbook_routes
        register_logbook_routes(app, tool="orbit", worksheets_dir=(
            Path(__file__).resolve().parents[1] / "configs" / "eosat1" / "worksheets"))
        app.router.add_get('/', handle_index)
        app.router.add_get('/api/now', handle_now)
        app.router.add_post('/api/tle', handle_tle_api)
        app.router.add_post('/api/sv', handle_sv_api)
        app.router.add_get('/static/orbit/wide-basemap.js', handle_basemap)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()

        print(f"\nWeb server started at http://localhost:{port}")
        print("Press Ctrl+C to stop\n")

        # Keep server running
        try:
            await asyncio.sleep(3600 * 24)  # Run for 24 hours max
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            await runner.cleanup()


def main():
    parser = argparse.ArgumentParser(
        description='Orbit Tools: TLE and State Vector to Telecommand Converter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert TLE at a specific epoch
  %(prog)s --tle "1 25544U..." "2 25544 51.64..." --epoch 2024-01-15T12:30:00

  # Convert state vector to commands
  %(prog)s --sv 6378000 0 0 0 7600 0

  # Start web interface
  %(prog)s --serve
        """
    )

    # Use mutually exclusive groups instead of subparsers
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument('--tle', nargs=2, metavar=('LINE1', 'LINE2'),
                       help='TLE line 1 and line 2')
    group.add_argument('--sv', nargs=6, type=float, metavar=('X', 'Y', 'Z', 'VX', 'VY', 'VZ'),
                       help='State vector: x y z vx vy vz (in meters and m/s)')
    group.add_argument('--serve', action='store_true',
                       help='Start web interface')

    parser.add_argument('--epoch', default=None,
                        help='Epoch (ISO format: 2024-01-15T12:30:00). Default: current time')
    parser.add_argument('--port', type=int, default=8093,
                        help='Port for web server (default 8093)')

    args = parser.parse_args()

    if args.tle:
        tle_args = argparse.Namespace(tle=args.tle, epoch=args.epoch)
        cli_tle_mode(tle_args)
    elif args.sv:
        sv_args = argparse.Namespace(sv=args.sv, epoch=args.epoch)
        cli_sv_mode(sv_args)
    elif args.serve:
        if not HAS_AIOHTTP:
            print("ERROR: aiohttp required for --serve mode")
            print("Install with: pip install aiohttp")
            return

        import asyncio
        asyncio.run(start_web_server(args.port))


if __name__ == '__main__':
    main()
