#!/usr/bin/env python3
"""vr_stub.py — a stand-in for the simulator's VR stream (interface smo-vr/1).

Use this to build and test a VR headset client WITHOUT the full simulator.
It speaks exactly the protocol in docs/VR_INTERFACE_ICD.md: the same
``hello`` and ``state`` messages, on the same ports, and it listens for the
same optional ``status`` line. Code that works against this stub works
against the real simulator on demo day.

Python 3.8 or newer, standard library only: copy this one file anywhere.

    python3 vr_stub.py                        # real time, 1 frame/s (like the simulator)
    python3 vr_stub.py --speed 10 --rate 10   # faster story, smoother frames
    python3 vr_stub.py --story nominal        # skip LEOP: deployed and nadir-pointing
    python3 vr_stub.py --replay sample_vr_frames.ndjson --speed 5
    python3 vr_stub.py --chaos                # bad lines, stalls, duplicates: be robust!
    python3 vr_stub.py --write-sample .       # regenerate the sample files

Then connect to <this-machine>:8100 (TCP, one JSON object per line) or
ws://<this-machine>:8101/vr (WebSocket, one JSON object per message).

How the file is organised (read it top to bottom):

1. Protocol constants, ``build_hello`` and ``parse_client_message`` — copies
   of the simulator's (smo_simulator/vr_bridge.py). A test checks they stay
   identical.
2. A little vector and quaternion maths (no numpy).
3. The "world": a circular sun-synchronous orbit, the Sun, Earth rotation,
   eclipse and ground-station visibility.
4. ``Story`` — a scripted, compressed LEOP: tumbling after separation,
   detumble, antenna and wing deployment, nadir pointing, an imaging slew.
   ``Story.body(t, tick)`` gives the ``state`` message for story time t.
5. Flat files: ``write_sample`` writes sample_vr_frames.ndjson and .csv.
6. The servers: TCP, a minimal WebSocket server, the status-line monitor,
   replay and chaos mode.
7. ``main`` — the command line.

Frames (ICD section 6): ECI is Earth-centred inertial, km. The body frame is
+X along-track, +Y cross-track (the +Y wing and the solar-array drive axis),
+Z nadir (the imager faces Earth), -Z zenith. ``q_body_to_eci`` is
[x, y, z, w], scalar last, and rotates body vectors into ECI.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import csv
import hashlib
import json
import math
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone

# ═════════════════════════════════════════════════════════════════════════
#  1. Protocol (identical to smo_simulator/vr_bridge.py)
# ═════════════════════════════════════════════════════════════════════════

SCHEMA = "smo-vr/1"
DEFAULT_TCP_PORT = 8100
DEFAULT_WS_PORT = 8101
DEFAULT_MAX_RATE_HZ = 10.0
DEFAULT_POWER_TCP_PORT = 8102      # the same frames plus a "power" block (ICD §5a)
DEFAULT_POWER_WS_PORT = 8103
DEFAULT_REQUEST_TCP_PORT = 8104    # command requests (ICD §7a)
DEFAULT_REQUEST_WS_PORT = 8105
REQUESTS = {   # name -> what the flight director would be asked to send (spacecraft axes)
    "deploy_antenna": "Deploy the antenna",
    "deploy_wing_py": "Deploy solar wing -Y (the headset's +Y wing)",
    "deploy_wing_my": "Deploy solar wing +Y (the headset's -Y wing)",
    "deploy_both_wings": "Deploy both solar wings",
}
POWER_FIELDS = (
    "power: bus_voltage_v; generated_w, consumed_w, net_w (W); wings.wing_py/wing_my "
    "{current_a, power_w, deployed}, wings.sada_angle_deg; body_faces.px..mz {current_a, power_w} "
    "(smo-vr/1 body axes, wings excluded); strings.a/b {voltage_v, current_a, enabled}; battery "
    "{soc_pct, voltage_v, current_a (+ = charging), charging, temp_c}; load_shed_stage 0-3")
KEEPALIVE_S = 1.0          # resend the latest frame at least this often
SILENT_AFTER_S = 5.0       # a client that replied before and then stopped
MAX_LINE_BYTES = 4096      # longest status line we accept

# Status word (client -> server). Positive logic: a set bit = that works.
STATUS_BITS = {
    0: "RX_OK",         # receiving state frames
    1: "PARSE_OK",      # the last frame parsed without error
    2: "RENDERING",     # the scene is being drawn
    3: "DATA_FRESH",    # newest frame is < 2 s old (wall clock)
    4: "DEPLOY_SHOWN",  # optional: wing/antenna deployment is visualised
    5: "FRAMERATE_OK",  # optional: headset is holding its target frame rate
}
HEALTHY_MASK = 0x000F      # bits 0-3 must all be set for "OK"
CLIENT_STATES = ("OK", "WARN", "ERROR")

# The spacecraft description sent in `hello`, in smo-vr/1 body axes.
SPACECRAFT_GEOMETRY = {
    "name": "EOSAT-1",
    "bus_size_m": [0.100, 0.226, 0.366],
    "body_axes": {
        "+X": "along-track (velocity) in nominal nadir pointing",
        "+Y": "cross-track; +Y solar wing; solar-array-drive rotation axis",
        "+Z": "nadir (points at Earth in nominal attitude); imager boresight",
        "-Z": "zenith; zenith star camera and GPS antenna",
    },
    "solar_wings": {
        "mount_faces": ["+Y", "-Y"],
        "deployed_size_m": [0.418, 0.342],
        "note": "each wing = 2 folding 209x342 mm panels; hinged at the "
                "+/-Y face, folded flat against it when STOWED",
    },
    "sada": {
        "axis_body": "+Y",
        "cell_normal_body": "(cos a, 0, sin a) with a = "
                            "deploy.sada_angle_deg; when tracking, "
                            "a = atan2(sun_z, sun_x) in body axes",
    },
    "antenna": {
        "suggested_model": "4 tape-spring UHF elements ~0.5 m, on the -Z "
                           "(zenith) face corners, flush when STOWED",
        "note": "suggestion only; the simulator models deployment state, "
                "not element geometry",
    },
}


def build_hello(source, max_rate_hz, tcp_port=None, ws_port=None,
                channel="state"):
    """The ``hello`` message a server sends once, right after you connect."""
    hello = {
        "type": "hello",
        "schema": SCHEMA,
        "source": source,
        "max_rate_hz": max_rate_hz,
        "ports": {"tcp": tcp_port, "ws": ws_port},
        "frames": {
            "eci": "Earth-centred inertial (SGP4 TEME, treat as J2000 for "
                   "display); km; X to vernal equinox, Z to north pole",
            "body": "spacecraft body frame, see spacecraft.body_axes",
            "quaternion": "q_body_to_eci = [x, y, z, w], scalar LAST, "
                          "Hamilton; rotates body vectors into ECI (use as "
                          "the satellite's rotation in an ECI-aligned scene)",
            "ecef_from_eci": "rotate about ECI Z by earth.gmst_deg",
        },
        "status_bits": {str(k): v for k, v in STATUS_BITS.items()},
        "healthy_mask": HEALTHY_MASK,
        "spacecraft": SPACECRAFT_GEOMETRY,
    }
    if channel != "state":          # the state channel's hello stays exactly as issued
        hello["channel"] = channel
    if channel == "power":
        hello["power_fields"] = POWER_FIELDS
    return hello


def stub_power(body):
    """A plausible "power" block for a stub frame. The simulator's comes from its power
    model; these figures are scaled to match it in a nominal orbit (about 30 W from each
    deployed wing in sunlight, up to 15 W from a sunlit body face, about 20 W of load,
    a 33.4 V bus). The battery charge is a fixed figure here."""
    sun = body.get("sun") or {}
    lit = 0.0 if sun.get("in_eclipse") else float(sun.get("sun_fraction", 1.0))
    d = sun.get("dir_body") or [0.0, 0.0, 0.0]
    dep = body.get("deploy") or {}
    bus_v = 33.4
    faces = {}
    for name, axis, sign in (("px", 0, 1), ("mx", 0, -1), ("py", 1, 1), ("my", 1, -1),
                             ("pz", 2, 1), ("mz", 2, -1)):
        w = round(max(0.0, sign * d[axis]) * 15.5 * lit, 2)
        faces[name] = {"current_a": round(w / bus_v, 3), "power_w": w}
    wings = {}
    for wing in ("wing_py", "wing_my"):
        frac = float((dep.get(wing) or {}).get("fraction", 0.0))
        w = round(frac * 30.1 * lit, 2)
        wings[wing] = {"current_a": round(w / bus_v, 3), "power_w": w,
                       "deployed": (dep.get(wing) or {}).get("state") == "DEPLOYED"}
    wings["sada_angle_deg"] = dep.get("sada_angle_deg", 0.0)
    gen = round(sum(f["power_w"] for f in faces.values())
                + wings["wing_py"]["power_w"] + wings["wing_my"]["power_w"], 2)
    cons = 20.0
    net = round(gen - cons, 2)
    on = lit > 0
    return {
        "bus_voltage_v": bus_v, "generated_w": gen, "consumed_w": cons, "net_w": net,
        "wings": wings, "body_faces": faces,
        "strings": {"a": {"voltage_v": 32.4 if on else 0.0, "current_a": round(gen / 2 / 32.4, 3), "enabled": True},
                    "b": {"voltage_v": 32.4 if on else 0.0, "current_a": round(gen / 2 / 32.4, 3), "enabled": True}},
        "battery": {"soc_pct": 95.0, "voltage_v": 33.4, "current_a": round(net / 33.4, 3),
                    "charging": net / 33.4 > 0.05, "temp_c": 6.0},
        "load_shed_stage": 0,
    }


def parse_client_message(text):
    """Check one line a headset sent. Returns (message, None) or (None, why).

    This is the simulator's own validator, so if the stub accepts your
    status line, so will the simulator.
    """
    if isinstance(text, (bytes, bytearray)):
        try:
            text = text.decode("utf-8")
        except UnicodeDecodeError:
            return None, "not UTF-8"
    text = text.strip()
    if not text:
        return None, "empty line"
    try:
        msg = json.loads(text)
    except json.JSONDecodeError as e:
        return None, f"not JSON ({e.msg})"
    if not isinstance(msg, dict):
        return None, "not a JSON object"
    mtype = msg.get("type")
    if mtype != "status":
        return None, f"unknown type {mtype!r} (expected 'status')"
    word = msg.get("status_word")
    if isinstance(word, bool) or not isinstance(word, int):
        return None, "status_word must be an integer"
    if not 0 <= word <= 0xFFFF:
        return None, "status_word out of range 0..65535"
    out = {"type": "status", "status_word": word}
    state = msg.get("state")
    if state is not None:
        if not isinstance(state, str) or state.upper() not in CLIENT_STATES:
            return None, f"state must be one of {CLIENT_STATES}"
        out["state"] = state.upper()
    team = msg.get("team")
    if team is not None:
        out["team"] = str(team)[:32]
    txt = msg.get("text")
    if txt is not None:
        out["text"] = str(txt)[:200]
    fps = msg.get("fps")
    if isinstance(fps, (int, float)) and not isinstance(fps, bool) \
            and math.isfinite(fps):
        out["fps"] = round(float(fps), 1)
    seq_ack = msg.get("seq_ack")
    if isinstance(seq_ack, int) and not isinstance(seq_ack, bool):
        out["seq_ack"] = seq_ack
    return out, None


def decode_status_word(word):
    """Names of the bits set in a status word, e.g. ['RX_OK', 'PARSE_OK']."""
    return [name for bit, name in STATUS_BITS.items() if word & (1 << bit)]


def classify(msg):
    """Health of a client from its latest valid status message (ICD 7)."""
    if msg.get("state") == "ERROR":
        return "ERROR"
    if msg["status_word"] & HEALTHY_MASK == HEALTHY_MASK \
            and msg.get("state") in (None, "OK"):
        return "OK"
    return "DEGRADED"


# ═════════════════════════════════════════════════════════════════════════
#  2. Vector and quaternion maths (plain tuples, no numpy)
# ═════════════════════════════════════════════════════════════════════════
# A "DCM" here is a 3x3 matrix C (a tuple of three rows) that maps ECI
# vectors into body axes: v_body = C v_eci. Its rows are the body X, Y and Z
# axes written in ECI. The simulator uses the same convention.

def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def norm(a):
    return math.sqrt(dot(a, a))


def unit(a):
    n = norm(a)
    return tuple(x / n for x in a) if n > 0 else (0.0, 0.0, 0.0)


def mat_vec(C, v):
    return tuple(dot(row, v) for row in C)


def mat_mul(A, B):
    cols = list(zip(*B))
    return tuple(tuple(dot(row, col) for col in cols) for row in A)


def transpose(C):
    return tuple(zip(*C))


def axis_rotation(axis, angle):
    """DCM of a frame turned by `angle` (rad) about the unit vector `axis`.

    New-frame components of a fixed vector = axis_rotation(...) @ old ones.
    """
    k = unit(axis)
    c, s = math.cos(angle), math.sin(angle)
    kx, ky, kz = k
    return ((c + (1 - c) * kx * kx, (1 - c) * kx * ky + s * kz,
             (1 - c) * kx * kz - s * ky),
            ((1 - c) * ky * kx - s * kz, c + (1 - c) * ky * ky,
             (1 - c) * ky * kz + s * kx),
            ((1 - c) * kz * kx + s * ky, (1 - c) * kz * ky - s * kx,
             c + (1 - c) * kz * kz))


def quat_to_dcm(q):
    """ECI -> body DCM from q_body_to_eci = [x, y, z, w]."""
    x, y, z, w = q
    return ((1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w)),
            (2 * (x * y - z * w), 1 - 2 * (x * x + z * z), 2 * (y * z + x * w)),
            (2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y)))


def dcm_to_quat(C):
    """q_body_to_eci = [x, y, z, w] from an ECI -> body DCM.

    Same algorithm as the simulator, so both pick the same sign. Remember
    that q and -q are the same rotation: interpolate the short way round.
    """
    tr = C[0][0] + C[1][1] + C[2][2]
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        q = ((C[1][2] - C[2][1]) / s, (C[2][0] - C[0][2]) / s,
             (C[0][1] - C[1][0]) / s, 0.25 * s)
    elif C[0][0] > C[1][1] and C[0][0] > C[2][2]:
        s = math.sqrt(1.0 + C[0][0] - C[1][1] - C[2][2]) * 2
        q = (0.25 * s, (C[1][0] + C[0][1]) / s, (C[2][0] + C[0][2]) / s,
             (C[1][2] - C[2][1]) / s)
    elif C[1][1] > C[2][2]:
        s = math.sqrt(1.0 + C[1][1] - C[0][0] - C[2][2]) * 2
        q = ((C[1][0] + C[0][1]) / s, 0.25 * s, (C[2][1] + C[1][2]) / s,
             (C[2][0] - C[0][2]) / s)
    else:
        s = math.sqrt(1.0 + C[2][2] - C[0][0] - C[1][1]) * 2
        q = ((C[2][0] + C[0][2]) / s, (C[2][1] + C[1][2]) / s, 0.25 * s,
             (C[0][1] - C[1][0]) / s)
    n = math.sqrt(sum(x * x for x in q))
    return tuple(x / n for x in q)


def slerp(q0, q1, f):
    """Spherical interpolation from q0 (f = 0) to q1 (f = 1), short way."""
    d = sum(a * b for a, b in zip(q0, q1))
    if d < 0:                           # q and -q: take the short way
        q1, d = tuple(-x for x in q1), -d
    if d > 0.9995:                      # nearly equal: plain lerp is fine
        q = tuple(a + f * (b - a) for a, b in zip(q0, q1))
    else:
        th = math.acos(d)
        s0 = math.sin((1 - f) * th) / math.sin(th)
        s1 = math.sin(f * th) / math.sin(th)
        q = tuple(s0 * a + s1 * b for a, b in zip(q0, q1))
    n = math.sqrt(sum(x * x for x in q))
    return tuple(x / n for x in q)


def smoothstep(x):
    """0 -> 1 with zero slope at both ends (gentle starts and stops)."""
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def wrap180(a):
    """Angle in degrees wrapped to [-180, 180)."""
    return (a + 180.0) % 360.0 - 180.0


def rl(v, nd):
    """Round every component, as the simulator does on the wire."""
    return [round(float(x), nd) for x in v]


# ═════════════════════════════════════════════════════════════════════════
#  3. The world: orbit, Sun, Earth rotation, eclipse, ground stations
# ═════════════════════════════════════════════════════════════════════════
# Orbit elements from the EOSAT-1 TLE (configs/eosat1/orbit.yaml): mean
# motion 15.24 rev/day, inclination 97.39 deg, RAAN 120 deg, and argument of
# perigee + mean anomaly = 360 deg (on the equator, going north, at epoch).
# The stub flies a CIRCULAR orbit with the sun-synchronous node drift; the
# simulator uses SGP4. They agree to better than 50 km over the first orbit.

EPOCH = datetime(2026, 8, 20, 12, 0, 0, tzinfo=timezone.utc)
MU_KM3_S2 = 398600.4418
EARTH_RADIUS_KM = 6371.0               # the radius the simulator reports
EARTH_FLATTENING = 1.0 / 298.257223563
MEAN_MOTION = 15.24 * 2.0 * math.pi / 86400.0               # rad/s
SEMI_MAJOR_KM = (MU_KM3_S2 / MEAN_MOTION ** 2) ** (1.0 / 3.0)  # ~6871.9 km
INCLINATION = math.radians(97.39)
RAAN0 = math.radians(120.0)
ARG_LAT0 = 0.0
NODE_RATE = 2.0 * math.pi / (365.2422 * 86400.0)   # sun-synchronous, rad/s
PERIOD_S = 5670.0                      # one orbit (2 pi / n = 5669 s), rounded

# The five ground stations (name, lat deg, lon deg, alt km); 5 deg mask.
GROUND_STATIONS = (
    ("Iqaluit", 63.747, -68.518, 0.034),
    ("Troll", -72.012, 2.535, 1.275),
    ("Svalbard", 78.2297, 15.3975, 0.458),
    ("Inuvik", 68.3195, -133.5495, 0.102),
    ("O'Higgins", -63.3211, -57.9008, 0.032),
)
MIN_ELEVATION_DEG = 5.0


def orbit_eci(t):
    """Position (km) and velocity (km/s) in ECI, t seconds after EPOCH."""
    u = ARG_LAT0 + MEAN_MOTION * t         # argument of latitude
    raan = RAAN0 + NODE_RATE * t
    cu, su = math.cos(u), math.sin(u)
    co, so = math.cos(raan), math.sin(raan)
    ci, si = math.cos(INCLINATION), math.sin(INCLINATION)
    a, v = SEMI_MAJOR_KM, SEMI_MAJOR_KM * MEAN_MOTION
    pos = (a * (co * cu - so * su * ci), a * (so * cu + co * su * ci),
           a * su * si)
    vel = (v * (-co * su - so * cu * ci), v * (-so * su + co * cu * ci),
           v * cu * si)
    return pos, vel


def julian_date(utc):
    return 2440587.5 + utc.timestamp() / 86400.0


def gmst_deg(utc):
    """Earth rotation angle (deg): the simulator's own formula."""
    jd = julian_date(utc)
    T = (jd - 2451545.0) / 36525.0
    return (280.46061837 + 360.98564736629 * (jd - 2451545.0)
            + 0.000387933 * T * T - T * T * T / 38710000.0) % 360.0


def sun_dir_eci(utc):
    """Unit vector towards the Sun in ECI (low-precision almanac)."""
    n = julian_date(utc) - 2451545.0
    L = (280.460 + 0.9856474 * n) % 360.0
    g = math.radians((357.528 + 0.9856003 * n) % 360.0)
    lam = math.radians(L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g))
    eps = math.radians(23.439 - 0.0000004 * n)
    return unit((math.cos(lam), math.sin(lam) * math.cos(eps),
                 math.sin(lam) * math.sin(eps)))


def in_shadow(pos, sun):
    """Cylindrical Earth shadow: behind the Earth and within one radius
    of the Earth-Sun line. (The simulator uses a cone with penumbra.)"""
    along = dot(pos, sun)
    if along >= 0:
        return False
    perp = tuple(p - along * s for p, s in zip(pos, sun))
    return norm(perp) < EARTH_RADIUS_KM


def eci_to_ecef(v, gmst):
    g = math.radians(gmst)
    c, s = math.cos(g), math.sin(g)
    return (c * v[0] + s * v[1], -s * v[0] + c * v[1], v[2])


def geodetic(pos_ecef):
    """(lat deg, lon deg, alt km) on the simulator's ellipsoid."""
    x, y, z = pos_ecef
    e2 = 2 * EARTH_FLATTENING - EARTH_FLATTENING ** 2
    p = math.hypot(x, y)
    lat = math.atan2(z, p * (1.0 - e2))
    for _ in range(5):
        n = EARTH_RADIUS_KM / math.sqrt(1.0 - e2 * math.sin(lat) ** 2)
        lat = math.atan2(z + e2 * n * math.sin(lat), p)
    n = EARTH_RADIUS_KM / math.sqrt(1.0 - e2 * math.sin(lat) ** 2)
    if abs(math.cos(lat)) > 0.01:
        alt = p / math.cos(lat) - n
    else:
        alt = z / math.sin(lat) - n * (1.0 - e2)
    return math.degrees(lat), math.degrees(math.atan2(y, x)), alt


def station_ecef(lat_deg, lon_deg, alt_km):
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    e2 = 2 * EARTH_FLATTENING - EARTH_FLATTENING ** 2
    n = EARTH_RADIUS_KM / math.sqrt(1 - e2 * math.sin(lat) ** 2)
    r = (n + alt_km) * math.cos(lat)
    return (r * math.cos(lon), r * math.sin(lon),
            (n * (1 - e2) + alt_km) * math.sin(lat))


_STATIONS = [(name, station_ecef(la, lo, al),
              (math.cos(math.radians(la)) * math.cos(math.radians(lo)),
               math.cos(math.radians(la)) * math.sin(math.radians(lo)),
               math.sin(math.radians(la))))
             for name, la, lo, al in GROUND_STATIONS]


def best_station(pos_ecef):
    """Name of the highest station above its 5 deg mask, or '' if none."""
    best, best_el = "", MIN_ELEVATION_DEG
    for name, gs, up in _STATIONS:
        rho = tuple(p - g for p, g in zip(pos_ecef, gs))
        el = math.degrees(math.asin(dot(rho, up) / norm(rho)))
        if el >= best_el:
            best, best_el = name, el
    return best


def nadir_dcm(pos, vel):
    """Nominal nadir pointing in smo-vr/1 axes: +Z to Earth's centre,
    +Y = -orbit normal, +X completes the triad (close to the velocity)."""
    z = unit(tuple(-p for p in pos))
    y = unit(tuple(-h for h in cross(pos, vel)))
    x = unit(cross(y, z))
    return (x, y, z)


# ═════════════════════════════════════════════════════════════════════════
#  4. The story: a compressed LEOP in one orbit (ICD section 9)
# ═════════════════════════════════════════════════════════════════════════

# Attitude just after separation (an arbitrary "the deployer left us here")
# and the tumble rate in body axes, deg/s (|w| ~ 2.7 deg/s).
Q_SEPARATION = (0.3017553, -0.2011702, 0.5029255, 0.7845637)
TUMBLE_RATE_DEG_S = (2.0, -1.5, 1.0)
DETUMBLE_START_S = 300.0
DETUMBLE_TAU_S = 150.0              # the tumble rate decays e-fold in 150 s
ACQUIRE_START_S, ACQUIRE_END_S = 900.0, 1200.0   # tumble -> nadir pointing
ANTENNA_DEPLOY_S = 600.0
WING_PY_START_S, WING_MY_START_S = 1300.0, 1400.0
WING_SWEEP_S = 30.0
SADA_START_S, SADA_END_S = 1440.0, 1620.0       # drive starts tracking
IMAGING_ROLL_DEG = 25.0
SLEW_OUT_S, HOLD_S, SLEW_BACK_S, SLEW_DONE_S = 4300.0, 4400.0, 4700.0, 4800.0

STORIES = ("leop", "once", "nominal")


class Story:
    """The scripted world. ``body(t, tick)`` is the ``state`` message body
    (without type/schema/seq) at story time t seconds after separation.

    * ``leop``    — the compressed LEOP, repeated every orbit (the clock
                    jumps back to the start each time, as the ICD warns).
    * ``once``    — the same LEOP once; afterwards everything stays
                    deployed and nadir-pointing while the orbit continues.
    * ``nominal`` — skip LEOP: deployed, nadir-pointing, Sun-tracking.
    """

    def __init__(self, name="leop", speed=1.0):
        if name not in STORIES:
            raise ValueError(f"story must be one of {STORIES}")
        self.name = name
        self.speed = float(speed)

    # -- what happens when ------------------------------------------------

    def _story_time(self, t):
        if self.name == "leop":
            return t % PERIOD_S
        return t

    def _events(self, t):
        """Modes, phase and deployments at story time t (a plain timeline).
        The `nominal` story behaves as if LEOP finished long ago."""
        if self.name == "nominal":
            t = max(t, 1e9)
        imaging = HOLD_S <= t < SLEW_BACK_S and self.name != "nominal"
        slewing = (SLEW_OUT_S <= t < HOLD_S or SLEW_BACK_S <= t < SLEW_DONE_S) \
            and self.name != "nominal"
        if t < DETUMBLE_START_S:
            aocs = "OFF"
        elif t < ACQUIRE_START_S:
            aocs = "DETUMBLE"
        elif slewing:
            aocs = "SLEW"
        else:
            aocs = "NOMINAL"
        if t < 240:
            phase = "SEPARATION_TIMER"
        elif t < DETUMBLE_START_S:
            phase = "INITIAL_POWER_ON"
        elif t < ANTENNA_DEPLOY_S:
            phase = "BOOTLOADER_OPS"
        elif t < 1500:
            phase = "LEOP"
        elif t < 2700:
            phase = "COMMISSIONING"
        else:
            phase = "NOMINAL"
        sc_mode = "SAFE" if t < 2700 else ("SCIENCE" if imaging else "NOMINAL")
        return {
            "aocs_mode": aocs,
            "pointing": "TARGET_TRACK" if imaging else "NADIR",
            "phase": phase,
            "sc_mode": sc_mode,
            "antenna": t >= ANTENNA_DEPLOY_S,
            "wing_py": self._wing(t - WING_PY_START_S),
            "wing_my": self._wing(t - WING_MY_START_S),
        }

    @staticmethod
    def _wing(dt):
        if dt < 0:
            return {"state": "STOWED", "fraction": 0.0}
        if dt < WING_SWEEP_S:
            return {"state": "DEPLOYING", "fraction": round(dt / WING_SWEEP_S, 3)}
        return {"state": "DEPLOYED", "fraction": 1.0}

    # -- attitude ---------------------------------------------------------

    @staticmethod
    def _tumble_dcm(t):
        """Free tumble about a body-fixed axis, slowing down from 300 s."""
        rate = math.radians(norm(TUMBLE_RATE_DEG_S))
        if t <= DETUMBLE_START_S:
            angle = rate * t
        else:
            k = 1.0 - math.exp(-(t - DETUMBLE_START_S) / DETUMBLE_TAU_S)
            angle = rate * (DETUMBLE_START_S + DETUMBLE_TAU_S * k)
        return mat_mul(axis_rotation(TUMBLE_RATE_DEG_S, angle),
                       quat_to_dcm(Q_SEPARATION))

    def attitude_dcm(self, t):
        """ECI -> body DCM at story time t."""
        pos, vel = orbit_eci(t)
        nadir = nadir_dcm(pos, vel)
        if self.name == "nominal" or t >= ACQUIRE_END_S:
            if self.name != "nominal" and SLEW_OUT_S <= t < SLEW_DONE_S:
                # Imaging: roll about +X (along-track) to look off to the side.
                if t < HOLD_S:
                    f = smoothstep((t - SLEW_OUT_S) / (HOLD_S - SLEW_OUT_S))
                elif t < SLEW_BACK_S:
                    f = 1.0
                else:
                    f = 1.0 - smoothstep((t - SLEW_BACK_S)
                                         / (SLEW_DONE_S - SLEW_BACK_S))
                roll = math.radians(IMAGING_ROLL_DEG) * f
                return mat_mul(axis_rotation((1.0, 0.0, 0.0), roll), nadir)
            return nadir
        tumble = self._tumble_dcm(t)
        if t < ACQUIRE_START_S:
            return tumble
        # Acquisition: blend smoothly from the slowed tumble to nadir.
        f = smoothstep((t - ACQUIRE_START_S) / (ACQUIRE_END_S - ACQUIRE_START_S))
        return quat_to_dcm(slerp(dcm_to_quat(tumble), dcm_to_quat(nadir), f))

    def body_rate_deg_s(self, t, h=0.01):
        """Body angular rate by differencing the attitude over +/- h s.
        For a DCM C, dC/dt = -[w x] C, so C(t+h) C(t-h)^T ~ I - 2h [w x]."""
        M = mat_mul(self.attitude_dcm(t + h), transpose(self.attitude_dcm(t - h)))
        k = math.degrees(1.0) / (4.0 * h)
        return ((M[1][2] - M[2][1]) * k, (M[2][0] - M[0][2]) * k,
                (M[0][1] - M[1][0]) * k)

    # -- the frame --------------------------------------------------------

    def body(self, t, tick):
        """The ``state`` message body at story time t (seconds)."""
        t = self._story_time(float(t))
        utc = EPOCH + timedelta(seconds=t)
        ev = self._events(t)
        pos, vel = orbit_eci(t)
        gmst = gmst_deg(utc)
        lat, lon, alt = geodetic(eci_to_ecef(pos, gmst))
        C = self.attitude_dcm(t)
        sun = sun_dir_eci(utc)
        sun_body = mat_vec(C, sun)
        eclipse = in_shadow(pos, sun)
        station = best_station(eci_to_ecef(pos, gmst))

        # Solar-array drive: parked at 0 until it starts tracking the Sun.
        tracked = math.degrees(math.atan2(sun_body[2], sun_body[0]))
        if self.name == "nominal" or t >= SADA_END_S:
            sada = tracked
        elif t < SADA_START_S:
            sada = 0.0
        else:
            f = smoothstep((t - SADA_START_S) / (SADA_END_S - SADA_START_S))
            sada = wrap180(f * wrap180(tracked))

        return {
            "sim_time": utc.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "met_s": round(t, 3),
            "tick": int(tick),
            "speed": self.speed,
            "orbit": {
                "pos_eci_km": rl(pos, 3),
                "vel_eci_km_s": rl(vel, 5),
                "lat_deg": round(lat, 4),
                "lon_deg": round(lon, 4),
                "alt_km": round(alt, 3),
            },
            "attitude": {
                "q_body_to_eci": rl(dcm_to_quat(C), 7),
                "rate_body_deg_s": rl(self.body_rate_deg_s(t), 4),
                "aocs_mode": ev["aocs_mode"],
                "pointing": ev["pointing"],
            },
            "sun": {
                "dir_eci": rl(sun, 6),
                "dir_body": rl(sun_body, 6),
                "in_eclipse": eclipse,
                "sun_fraction": 0.0 if eclipse else 1.0,
            },
            "earth": {
                "dir_body": rl(mat_vec(C, unit(tuple(-p for p in pos))), 6),
                "gmst_deg": round(gmst, 4),
                "radius_km": EARTH_RADIUS_KM,
            },
            "deploy": {
                "wing_py": ev["wing_py"],
                "wing_my": ev["wing_my"],
                "sada_angle_deg": round(sada, 2),
                "antenna": {
                    "state": "DEPLOYED" if ev["antenna"] else "STOWED",
                    "deployed": ev["antenna"],
                    "sensor": "DEPLOYED" if ev["antenna"] else "STOWED",
                },
            },
            "mission": {
                "sc_mode": ev["sc_mode"],
                "phase": ev["phase"],
                "in_contact": bool(station),
                "ground_station": station,
            },
        }


# ═════════════════════════════════════════════════════════════════════════
#  5. Messages on the wire and flat files
# ═════════════════════════════════════════════════════════════════════════

def dumps(obj):
    """Compact JSON, exactly as the simulator writes it."""
    return json.dumps(obj, separators=(",", ":"))


def state_message(seq, body):
    """Wrap a body in the ``state`` envelope (type, schema, seq first)."""
    msg = {"type": "state", "schema": SCHEMA, "seq": seq}
    msg.update(body)
    return msg


def flatten(frame, prefix=""):
    """One frame as a flat {column: value} dict for the CSV file: nested
    names joined with '_', vectors as _x/_y/_z(/_w), booleans as 0/1."""
    out = {}
    for key, value in frame.items():
        if not prefix and key in ("type", "schema"):
            continue
        name = prefix + key
        if isinstance(value, dict):
            out.update(flatten(value, name + "_"))
        elif isinstance(value, list):
            for axis, x in zip("xyzw", value):
                out[f"{name}_{axis}"] = x
        elif isinstance(value, bool):
            out[name] = int(value)
        else:
            out[name] = value
    return out


def write_sample(directory, step=5.0, story="once"):
    """Write sample_vr_frames.ndjson and sample_vr_frames.csv: one orbit of
    the story at `step`-second intervals. Returns the two paths."""
    st = Story(story)
    frames = []
    n = int(math.ceil(PERIOD_S / step))
    for i in range(n):
        t = i * step
        frames.append(state_message(i + 1, st.body(t, int(t))))
    os.makedirs(directory, exist_ok=True)
    nd = os.path.join(directory, "sample_vr_frames.ndjson")
    cs = os.path.join(directory, "sample_vr_frames.csv")
    hello = build_hello("vr-stub", DEFAULT_MAX_RATE_HZ, DEFAULT_TCP_PORT,
                        DEFAULT_WS_PORT)
    with open(nd, "w", encoding="utf-8", newline="\n") as f:
        f.write(dumps(hello) + "\n")
        for fr in frames:
            f.write(dumps(fr) + "\n")
    rows = [flatten(fr) for fr in frames]
    with open(cs, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return nd, cs


def write_issue2_samples(directory, step=5.0, story="once"):
    """Sample files for the issue-2 channels: sample_vr_power.ndjson/.csv (the same orbit
    as sample_vr_frames, each frame with its "power" block, as channel 2 sends it) and
    sample_vr_requests.ndjson (a channel-3 conversation: one line per message, wrapped as
    {"t_s": seconds, "from": "headset" | "server", "message": {...}}). Returns the paths."""
    st = Story(story)
    frames = []
    for i in range(int(math.ceil(PERIOD_S / step))):
        t = i * step
        body = st.body(t, int(t))
        frames.append(state_message(i + 1, dict(body, power=stub_power(body))))
    os.makedirs(directory, exist_ok=True)
    nd = os.path.join(directory, "sample_vr_power.ndjson")
    cs = os.path.join(directory, "sample_vr_power.csv")
    hello = build_hello("vr-stub", DEFAULT_MAX_RATE_HZ, DEFAULT_POWER_TCP_PORT,
                        DEFAULT_POWER_WS_PORT, "power")
    with open(nd, "w", encoding="utf-8", newline="\n") as f:
        f.write(dumps(hello) + "\n")
        for fr in frames:
            f.write(dumps(fr) + "\n")
    rows = [flatten(fr) for fr in frames]
    with open(cs, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    rq_hello = {"type": "hello", "schema": SCHEMA, "source": "vr-stub", "channel": "requests",
                "ports": {"tcp": DEFAULT_REQUEST_TCP_PORT, "ws": DEFAULT_REQUEST_WS_PORT},
                "requests": dict(REQUESTS)}
    talk = [
        (0.0, "server", rq_hello),
        (2.0, "headset", {"type": "request", "request": "deploy_antenna", "team": "T07",
                          "text": "we want to see the dipole unfold"}),
        (2.0, "server", {"type": "request_ack", "schema": SCHEMA, "id": "R1",
                         "request": "deploy_antenna", "state": "PENDING"}),
        (3.0, "headset", {"type": "request", "request": "deploy_antenna", "team": "T07"}),
        (3.0, "server", {"type": "request_rejected", "request": "deploy_antenna",
                         "reason": "one request every 2 s"}),
        (6.0, "headset", {"type": "request", "request": "deploy_antenna", "team": "T07"}),
        (6.0, "server", {"type": "request_ack", "schema": SCHEMA, "id": "R1",
                         "request": "deploy_antenna", "state": "PENDING", "duplicate": True}),
        (9.0, "headset", {"type": "request", "request": "open_the_pod_bay_doors", "team": "T07"}),
        (9.0, "server", {"type": "request_rejected", "request": "open_the_pod_bay_doors",
                         "reason": "unknown request; one of " + ", ".join(REQUESTS)}),
        (48.0, "server", {"type": "request_update", "schema": SCHEMA, "id": "R1",
                          "request": "deploy_antenna", "team": "T07", "state": "SENT",
                          "note": "", "tc_seq": 214}),
        (60.0, "headset", {"type": "request", "request": "deploy_both_wings", "team": "T07",
                           "text": "flaps out please"}),
        (60.0, "server", {"type": "request_ack", "schema": SCHEMA, "id": "R2",
                          "request": "deploy_both_wings", "state": "PENDING"}),
        (95.0, "server", {"type": "request_update", "schema": SCHEMA, "id": "R2",
                          "request": "deploy_both_wings", "team": "T07", "state": "DECLINED",
                          "note": "not in contact; ask again in the next pass", "tc_seq": None}),
    ]
    rq = os.path.join(directory, "sample_vr_requests.ndjson")
    with open(rq, "w", encoding="utf-8", newline="\n") as f:
        for t, who, msg in talk:
            f.write(dumps({"t_s": t, "from": who, "message": msg}) + "\n")
    return nd, cs, rq


# ═════════════════════════════════════════════════════════════════════════
#  6. Servers
# ═════════════════════════════════════════════════════════════════════════

class StoryFeed:
    """Frames from the story, with story time = speed x wall time."""

    def __init__(self, story):
        self.story = story
        self.t0 = time.monotonic()

    def current(self):
        t = self.story.speed * (time.monotonic() - self.t0)
        return self.story.body(t, int(t))


class ReplayFeed:
    """Frames from a recorded .ndjson file (e.g. sample_vr_frames.ndjson or
    a recording from vr_client_example.py), paced by their met_s and
    looping at the end."""

    def __init__(self, path, speed=1.0):
        self.frames = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    m = json.loads(line)
                except ValueError:
                    continue
                if isinstance(m, dict) and m.get("type") == "state":
                    for k in ("type", "schema", "seq"):
                        m.pop(k, None)
                    self.frames.append(m)
        if not self.frames:
            raise SystemExit(f"{path}: no 'state' lines to replay")
        self.speed = float(speed)
        self.t0 = time.monotonic()
        first = float(self.frames[0].get("met_s", 0.0))
        self.offsets = [float(fr.get("met_s", 0.0)) - first for fr in self.frames]
        self.length = self.offsets[-1] + (self.offsets[1] if len(self.offsets) > 1
                                          else 1.0)

    def current(self):
        t = (self.speed * (time.monotonic() - self.t0)) % max(self.length, 1e-6)
        i = 0
        while i + 1 < len(self.offsets) and self.offsets[i + 1] <= t:
            i += 1
        return self.frames[i]


class StatusLog:
    """Prints each headset's health when it changes and logs every line a
    headset sends to vr_logs/vr_replies_<time>.jsonl."""

    def __init__(self, log_dir="vr_logs"):
        os.makedirs(log_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = os.path.join(log_dir, f"vr_replies_{stamp}.jsonl")
        self._f = open(self.path, "a", encoding="utf-8")
        self._last = {}

    def on_line(self, peer, transport, raw, current_seq):
        msg, err = parse_client_message(raw)
        text = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw
        self._f.write(dumps({"wall": datetime.now().isoformat(timespec="seconds"),
                             "peer": peer, "transport": transport,
                             "raw": text.strip(), "error": err, "msg": msg}) + "\n")
        self._f.flush()
        if err:
            print(f"  [{peer}] ignored a bad line: {err}")
            return
        who = msg.get("team") or peer
        health = classify(msg)
        if self._last.get(who) != health:
            self._last[who] = health
            lag = (f", {current_seq - msg['seq_ack']} frames behind"
                   if "seq_ack" in msg else "")
            print(f"  [{who}] {health}: status_word=0x{msg['status_word']:04X} "
                  f"{' '.join(decode_status_word(msg['status_word']))}"
                  f"{lag} {msg.get('text', '')}")

    def silent_check(self, who_last_rx):
        now = time.monotonic()
        for who, t in who_last_rx.items():
            if now - t > SILENT_AFTER_S and self._last.get(who) != "SILENT":
                self._last[who] = "SILENT"
                print(f"  [{who}] SILENT: no status line for {SILENT_AFTER_S:.0f} s")


WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


class StubServer:
    """Serves frames to every connected client over TCP and WebSocket."""

    def __init__(self, feed, host, tcp_port, ws_port, rate_hz, chaos=False,
                 status_log=None, channel="state"):
        self.feed = feed
        self.channel = channel
        self.host = host
        self.tcp_port, self.ws_port = tcp_port, ws_port
        self.rate_hz = max(0.5, min(float(rate_hz), DEFAULT_MAX_RATE_HZ))
        self.chaos = random.Random(1) if chaos else None
        self.log = status_log
        self.senders = {}          # peer -> async send(line)
        self.last_rx = {}          # peer -> monotonic time of last good line
        self.seq = 0
        self.last_line = None

    # -- outbound ---------------------------------------------------------

    def hello_line(self):
        return dumps(build_hello("vr-stub", self.rate_hz, self.tcp_port,
                                 self.ws_port, self.channel))

    def frame_body(self):
        body = self.feed.current()
        if self.channel == "power":
            body = dict(body, power=stub_power(body))
        return body

    async def send_all(self, line):
        for peer, send in list(self.senders.items()):
            try:
                await asyncio.wait_for(send(line), timeout=2.0)
            except Exception:       # slow or gone: drop it, it can reconnect
                self.senders.pop(peer, None)
                print(f"- {peer} dropped")

    async def broadcast(self):
        """Send one frame per tick of the frame clock, plus chaos if asked."""
        period = 1.0 / self.rate_hz
        while True:
            await asyncio.sleep(period)
            self.seq += 1
            line = dumps(state_message(self.seq, self.frame_body()))
            if self.chaos:
                line = await self.misbehave(line)
                if line is None:
                    continue
            self.last_line = line
            await self.send_all(line)
            if self.log:
                self.log.silent_check(self.last_rx)

    async def misbehave(self, line):
        """--chaos: everything a real network and a real simulator can do."""
        r = self.chaos.random()
        if r < 0.04:
            print("  chaos: garbage line")
            await self.send_all('{"type":"state","seq":')
        elif r < 0.08:
            print("  chaos: repeated the previous frame")
            if self.last_line:
                await self.send_all(self.last_line)
        elif r < 0.11:
            print("  chaos: skipped a frame (seq gap)")
            return None
        elif r < 0.13:
            print("  chaos: 3 s stall")
            await asyncio.sleep(3.0)
        elif r < 0.16:
            print("  chaos: unknown message type")
            await self.send_all(dumps({"type": "notice", "schema": SCHEMA,
                                       "text": "ignore me"}))
        elif r < 0.20:
            msg = json.loads(line)
            msg["x_future_field"] = {"note": "ignore fields you do not know"}
            return dumps(msg)
        return line

    async def greet(self, peer, send):
        await send(self.hello_line())
        if self.last_line:
            await send(self.last_line)
        self.senders[peer] = send
        print(f"+ {peer} connected ({len(self.senders)} client(s))")

    def on_text(self, peer, transport, raw):
        if self.log:
            msg, err = parse_client_message(raw)
            if err is None:
                self.last_rx[msg.get("team") or peer] = time.monotonic()
            self.log.on_line(peer, transport, raw, self.seq)

    # -- TCP: one JSON object per line ------------------------------------

    async def handle_tcp(self, reader, writer):
        addr = writer.get_extra_info("peername")
        peer = f"tcp {addr[0]}:{addr[1]}" if addr else "tcp ?"

        async def send(line):
            writer.write((line + "\n").encode("utf-8"))
            await writer.drain()

        try:
            await self.greet(peer, send)
            while True:
                try:
                    raw = await reader.readline()
                except (asyncio.LimitOverrunError, ValueError):
                    print(f"  [{peer}] line longer than {MAX_LINE_BYTES} B ignored")
                    continue
                if not raw:
                    break
                if raw.strip():
                    self.on_text(peer, "tcp", raw)
        except (ConnectionError, asyncio.IncompleteReadError):
            pass
        finally:
            if self.senders.pop(peer, None) is not None:
                print(f"- {peer} disconnected")
            writer.close()

    # -- WebSocket: a minimal RFC 6455 server (text frames only) ----------

    async def handle_ws(self, reader, writer):
        addr = writer.get_extra_info("peername")
        peer = f"ws {addr[0]}:{addr[1]}" if addr else "ws ?"
        try:
            request = await reader.readuntil(b"\r\n\r\n")
        except (asyncio.IncompleteReadError, asyncio.LimitOverrunError):
            writer.close()
            return
        lines = request.decode("latin-1").split("\r\n")
        path = lines[0].split(" ")[1] if len(lines[0].split(" ")) > 1 else ""
        headers = {}
        for h in lines[1:]:
            if ":" in h:
                k, v = h.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        key = headers.get("sec-websocket-key")
        if path.split("?")[0] not in ("/", "/vr", "/vr/power", "/vr/requests") or not key:
            writer.write(b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n")
            await writer.drain()
            writer.close()
            return
        accept = base64.b64encode(hashlib.sha1(
            (key + WS_GUID).encode()).digest()).decode()
        writer.write(("HTTP/1.1 101 Switching Protocols\r\n"
                      "Upgrade: websocket\r\nConnection: Upgrade\r\n"
                      f"Sec-WebSocket-Accept: {accept}\r\n\r\n").encode())
        await writer.drain()

        async def send_frame(opcode, payload):
            n = len(payload)
            if n < 126:
                head = bytes([0x80 | opcode, n])
            elif n < 65536:
                head = bytes([0x80 | opcode, 126]) + n.to_bytes(2, "big")
            else:
                head = bytes([0x80 | opcode, 127]) + n.to_bytes(8, "big")
            writer.write(head + payload)
            await writer.drain()

        async def send(line):
            await send_frame(0x1, line.encode("utf-8"))

        try:
            await self.greet(peer, send)
            message = b""
            while True:
                b0, b1 = await reader.readexactly(2)
                opcode, n = b0 & 0x0F, b1 & 0x7F
                if n == 126:
                    n = int.from_bytes(await reader.readexactly(2), "big")
                elif n == 127:
                    n = int.from_bytes(await reader.readexactly(8), "big")
                mask = await reader.readexactly(4) if b1 & 0x80 else b"\0\0\0\0"
                if n > MAX_LINE_BYTES:
                    print(f"  [{peer}] message longer than {MAX_LINE_BYTES} B")
                    break
                data = bytes(c ^ mask[i % 4] for i, c in
                             enumerate(await reader.readexactly(n)))
                if opcode == 0x8:                       # close
                    await send_frame(0x8, data[:2])
                    break
                if opcode == 0x9:                       # ping -> pong
                    await send_frame(0xA, data)
                    continue
                if opcode in (0x0, 0x1, 0x2):           # (continued) data
                    message += data
                    if b0 & 0x80:                       # final fragment
                        self.on_text(peer, "ws", message)
                        message = b""
        except (ConnectionError, asyncio.IncompleteReadError):
            pass
        finally:
            if self.senders.pop(peer, None) is not None:
                print(f"- {peer} disconnected")
            writer.close()

    # -- run --------------------------------------------------------------

    async def run(self):
        servers = []
        if self.tcp_port is not None:
            s = await asyncio.start_server(self.handle_tcp, self.host,
                                           self.tcp_port, limit=MAX_LINE_BYTES)
            self.tcp_port = s.sockets[0].getsockname()[1]
            servers.append(s)
        if self.ws_port is not None:
            s = await asyncio.start_server(self.handle_ws, self.host,
                                           self.ws_port)
            self.ws_port = s.sockets[0].getsockname()[1]
            servers.append(s)
        print(f"vr_stub ({SCHEMA}, {self.channel} channel) on {self.host}: TCP {self.tcp_port}, "
              f"WebSocket ws://<this-machine>:{self.ws_port}/vr, "
              f"{self.rate_hz:g} frame(s)/s.")
        if self.log and self.channel == "state":
            print(f"Status lines are logged to {self.log.path}")
        await self.broadcast()


class RequestStub(StubServer):
    """The command-request channel (ICD §7a) without an MCS: every request is
    acknowledged as PENDING, then "decided" after --decide-after seconds (SENT, or
    DECLINED with --decline), as a flight director would."""

    def __init__(self, host, tcp_port, ws_port, decide_after=5.0, decline=False):
        super().__init__(None, host, tcp_port, ws_port, 1.0, channel="requests")
        self.decide_after = decide_after
        self.decline = decline
        self.next_id = 1
        self.pending = {}            # id -> (peer, request, team)

    def hello_line(self):
        return dumps({"type": "hello", "schema": SCHEMA, "source": "vr-stub",
                      "channel": "requests", "ports": {"tcp": self.tcp_port, "ws": self.ws_port},
                      "requests": dict(REQUESTS),
                      "usage": 'send {"type":"request","request":"deploy_antenna","team":"T07",'
                               '"text":"why"}; the flight director decides; you get request_ack, '
                               "then request_update"})

    async def greet(self, peer, send):
        await send(self.hello_line())
        self.senders[peer] = send
        print(f"+ {peer} connected to the request channel")

    async def reply(self, peer, obj):
        send = self.senders.get(peer)
        if send:
            try:
                await send(dumps(obj))
            except Exception:
                self.senders.pop(peer, None)

    def on_text(self, peer, transport, raw):
        asyncio.ensure_future(self.handle_request(peer, raw))

    async def handle_request(self, peer, raw):
        try:
            msg = json.loads(raw)
            assert isinstance(msg, dict)
        except Exception:
            await self.reply(peer, {"type": "request_rejected", "reason": "line is not a JSON object"})
            return
        if msg.get("type") == "status":
            return
        if msg.get("type") != "request":
            await self.reply(peer, {"type": "request_rejected",
                                    "reason": "type must be request, withdraw, list or status"})
            return
        name = str(msg.get("request", "")).strip().lower()
        if name not in REQUESTS:
            await self.reply(peer, {"type": "request_rejected", "request": name,
                                    "reason": "unknown request; one of " + ", ".join(REQUESTS)})
            return
        pid = f"R{self.next_id}"
        self.next_id += 1
        team = str(msg.get("team") or "")[:32]
        print(f"  {peer} {team}: {name} -> {pid} PENDING")
        await self.reply(peer, {"type": "request_ack", "schema": SCHEMA, "id": pid,
                                "request": name, "state": "PENDING"})
        await asyncio.sleep(self.decide_after)
        state = "DECLINED" if self.decline else "SENT"
        print(f"  {pid} {state}")
        await self.reply(peer, {"type": "request_update", "schema": SCHEMA, "id": pid,
                                "request": name, "team": team, "state": state,
                                "note": "stub flight director" if self.decline else "",
                                "tc_seq": None if self.decline else 1000 + int(pid[1:])})

    async def broadcast(self):
        while True:
            await asyncio.sleep(3600)


# ═════════════════════════════════════════════════════════════════════════
#  7. Command line
# ═════════════════════════════════════════════════════════════════════════

def build_parser():
    p = argparse.ArgumentParser(
        description="smo-vr/1 test server: the simulator's VR stream "
                    "without the simulator.")
    p.add_argument("--host", default="0.0.0.0",
                   help="address to listen on (default: all interfaces, so "
                        "a headset on the same Wi-Fi can connect)")
    p.add_argument("--port", type=int, default=DEFAULT_TCP_PORT,
                   help="TCP port (default %(default)s)")
    p.add_argument("--ws-port", type=int, default=DEFAULT_WS_PORT,
                   help="WebSocket port (default %(default)s)")
    p.add_argument("--no-ws", action="store_true", help="TCP only")
    p.add_argument("--power-port", type=int, default=DEFAULT_POWER_TCP_PORT,
                   help="power channel TCP port (default %(default)s)")
    p.add_argument("--power-ws-port", type=int, default=DEFAULT_POWER_WS_PORT,
                   help="power channel WebSocket port (default %(default)s)")
    p.add_argument("--request-port", type=int, default=DEFAULT_REQUEST_TCP_PORT,
                   help="command-request TCP port (default %(default)s)")
    p.add_argument("--request-ws-port", type=int, default=DEFAULT_REQUEST_WS_PORT,
                   help="command-request WebSocket port (default %(default)s)")
    p.add_argument("--state-only", action="store_true",
                   help="serve only the state channel (8100/8101), as issue 1 did")
    p.add_argument("--decide-after", type=float, default=5.0,
                   help="seconds before the stub 'flight director' answers a request")
    p.add_argument("--decline", action="store_true",
                   help="the stub flight director declines every request")
    p.add_argument("--speed", type=float, default=1.0,
                   help="story seconds per wall-clock second (default 1)")
    p.add_argument("--rate", type=float, default=1.0,
                   help="frames per second, at most 10 (default 1, like "
                        "the simulator at x1)")
    p.add_argument("--story", choices=STORIES, default="leop",
                   help="leop: the compressed LEOP, repeated every orbit; "
                        "once: LEOP once, then nominal; nominal: skip LEOP")
    p.add_argument("--replay", metavar="FILE.ndjson",
                   help="replay a recorded file instead of the story")
    p.add_argument("--chaos", action="store_true",
                   help="misbehave on purpose: garbage lines, repeats, seq "
                        "gaps, stalls, unknown types and fields")
    p.add_argument("--log-dir", default="vr_logs",
                   help="where status lines are logged (default %(default)s)")
    p.add_argument("--write-sample", metavar="DIR",
                   help="write the sample files (frames, power, requests) into DIR and exit")
    p.add_argument("--sample-step", type=float, default=5.0,
                   help="seconds between sample frames (default 5)")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.write_sample:
        nd, cs = write_sample(args.write_sample, args.sample_step)
        print(f"wrote {nd}\nwrote {cs}")
        for path in write_issue2_samples(args.write_sample, args.sample_step):
            print(f"wrote {path}")
        return 0
    if args.replay:
        feed = ReplayFeed(args.replay, args.speed)
    else:
        feed = StoryFeed(Story(args.story, args.speed))
    server = StubServer(feed, args.host, args.port,
                        None if args.no_ws else args.ws_port, args.rate,
                        chaos=args.chaos, status_log=StatusLog(args.log_dir))
    servers = [server]
    if not args.state_only:
        servers.append(StubServer(feed, args.host, args.power_port,
                                  None if args.no_ws else args.power_ws_port, args.rate,
                                  chaos=args.chaos, channel="power"))
        servers.append(RequestStub(args.host, args.request_port,
                                   None if args.no_ws else args.request_ws_port,
                                   args.decide_after, args.decline))

    async def run_all():
        await asyncio.gather(*(s.run() for s in servers))
    print("Ctrl+C to stop.")
    try:
        asyncio.run(run_all())
    except KeyboardInterrupt:
        print("\nstopped")
    except OSError as e:
        print(f"cannot listen: {e}. Is another stub or the simulator already "
              f"using port {args.port}/{args.ws_port}? Try --port/--ws-port.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
