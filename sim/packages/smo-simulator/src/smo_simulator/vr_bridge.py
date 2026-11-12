"""VR visualisation bridge — interface ``smo-vr/1``.

Streams the spacecraft's *visual* state (orbit position, attitude, sun and
Earth directions, solar-wing and antenna deployment) to external viewers —
first-year VR headset teams — and accepts an OPTIONAL status line back from
each viewer so the instructor console can show whether the headsets are
receiving data and are happy.

Two transports, one message format (docs/VR_INTERFACE_ICD.md is the ICD):

* TCP  (default port 8100): newline-delimited JSON, UTF-8. One JSON object
  per line in each direction. Best for Unity / Unreal / native clients.
* WebSocket (default port 8101, path ``/vr`` or ``/``): one JSON object per
  text message. Best for WebXR / three.js / A-Frame clients (browsers cannot
  open raw TCP sockets).

Server -> client: one ``hello`` on connect, then ``state`` messages at the
simulator tick rate (one per new tick, plus a 1 Hz keepalive while frozen),
capped at ``max_rate_hz``.

Client -> server (optional): ``status`` messages carrying a 16-bit
positive-logic ``status_word``; bits 0-3 all set means healthy.

Threading contract: ``build_vr_state`` reads LIVE model state and therefore
runs on the engine tick thread only (it is called from
``SimulationEngine._publish_snapshot``). The bridge itself runs on the
asyncio loop and only ever reads the published, immutable snapshot through
``engine.get_vr_state()``. The link summary travels the other way as a
freshly-built dict assigned to ``engine.vr_link`` (an atomic rebind).

This is a GROUND-SIDE visualisation of simulator truth. Nothing here is
spacecraft telemetry and nothing a headset sends can change the simulation.
"""
from __future__ import annotations

import asyncio
import json
import logging
import math
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import numpy as np

from smo_common import attitude as att

logger = logging.getLogger(__name__)

SCHEMA = "smo-vr/1"
DEFAULT_TCP_PORT = 8100
DEFAULT_WS_PORT = 8101
DEFAULT_MAX_RATE_HZ = 10.0
KEEPALIVE_S = 1.0          # resend the latest frame at least this often
SILENT_AFTER_S = 5.0       # a client that replied before and then stops
MAX_LINE_BYTES = 4096      # inbound line limit (a status line is ~150 B)
WRITE_TIMEOUT_S = 2.0      # a slow client is dropped, never waited for

# ── Status word (client -> server), positive logic: 0 means "nothing works" ──
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

# Health ranking, least to most severe. NO_REPLY is not a fault: the return
# line is optional, so a connected client that never talks back is simply
# "receiving, no feedback".
HEALTH_ORDER = ("OK", "NO_REPLY", "DEGRADED", "SILENT", "ERROR")

PHASE_NAMES = ("PRE_SEPARATION", "SEPARATION_TIMER", "INITIAL_POWER_ON",
               "BOOTLOADER_OPS", "LEOP", "COMMISSIONING", "NOMINAL")
SC_MODE_NAMES = {0: "SAFE", 1: "NOMINAL", 2: "SCIENCE", 3: "EMERGENCY"}
AOCS_MODE_NAMES = {0: "OFF", 1: "SAFE_BOOT", 2: "DETUMBLE", 3: "COARSE_SUN",
                   4: "NOMINAL", 5: "FINE_POINT", 6: "SLEW", 7: "DESAT",
                   8: "ECLIPSE", 9: "INERTIAL"}
POINTING_NAMES = {0: "INERTIAL", 1: "NADIR", 2: "TARGET_TRACK", 3: "SUN"}
ANTENNA_SENSOR_NAMES = {0: "UNKNOWN", 1: "STOWED", 2: "DEPLOYED",
                        3: "JAMMED"}

# ── smo-vr/1 body frame vs the simulator body frame ──────────────────────
# The ICD (docs/VR_INTERFACE_ICD.md §6) fixes the smo-vr/1 body axes as
# +X along-track, +Y wing / SADA axis, +Z NADIR (imager), -Z zenith. Ruling Q4
# (2026-10-30) turned the SIMULATOR's body frame over: +Z = zenith, -Z = nadir
# (imager and radiator on -Z), +X along-track, +Y = +orbit normal. External
# student teams build against smo-vr/1, so the bridge does not change the
# interface: it re-expresses every body-frame quantity in the smo-vr/1 axes,
# which are the simulator's body axes turned 180 deg about X:
#     v_vr = VR_FROM_SIM_BODY @ v_sim
# The same physical spacecraft therefore renders exactly as before. Because
# that turn swaps +Y and -Y, the wing on the simulator's +Y face is the wing
# on the smo-vr/1 -Y face (so wing_py/wing_my are exchanged on the wire), and
# the SADA shaft angle about Y changes sign. Any move of the ICD itself to
# the new convention is a breaking change and would be smo-vr/2.
VR_FROM_SIM_BODY = np.diag([1.0, -1.0, -1.0])

# Static description sent once in `hello`. Body axes here are the smo-vr/1
# axes above (NOT the simulator's own). Bus dimensions follow the 6U
# envelope in subsystems/eps.yaml (100 x 226 x 366 mm: the 366x226 face is
# the X face, 366x100 the Y face, 226x100 the Z face). Wing and antenna
# geometry is a MODELLING SUGGESTION — the simulator models their areas and
# states, not their shapes.
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


# ─────────────────────────────────────────────────────────────────────────
#  Frame builder (tick thread)
# ─────────────────────────────────────────────────────────────────────────

def _unit(v) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else np.zeros(3)


def _rl(v, nd: int) -> list[float]:
    return [round(float(x), nd) for x in v]


def gmst_deg_at(utc) -> float:
    """Greenwich mean sidereal time (deg) — the propagator's own formula, so
    an Earth drawn with this rotation lines up with lat_deg/lon_deg."""
    from smo_common.orbit.propagator import _gmst
    jd = 2440587.5 + utc.timestamp() / 86400.0
    return math.degrees(_gmst(jd)) % 360.0


def _wing(deployed: bool, deploying: bool, timer_s: float,
          sweep_s: float) -> dict:
    if deployed:
        return {"state": "DEPLOYED", "fraction": 1.0}
    if deploying:
        sweep = max(float(sweep_s), 1e-6)
        frac = min(1.0, max(0.0, 1.0 - float(timer_s) / sweep))
        return {"state": "DEPLOYING", "fraction": round(frac, 3)}
    return {"state": "STOWED", "fraction": 0.0}


def build_vr_state(engine) -> dict:
    """Build one ``state`` body from LIVE engine state. Tick thread only.

    The envelope fields (``type``, ``schema``, ``seq``) are added by the
    bridge at send time.
    """
    o = engine.orbit.state
    subs = getattr(engine, "subsystems", {}) or {}
    aocs = subs.get("aocs")
    eps = subs.get("eps")
    ttc = subs.get("ttc")

    pos = np.asarray(o.pos_eci, dtype=float)
    vel = np.asarray(o.vel_eci, dtype=float)
    sun_hat = _unit(o.sun_eci)
    nadir_hat = _unit(-pos)

    a = getattr(aocs, "_state", None)
    q = list(getattr(a, "q_true", None) or [0.0, 0.0, 0.0, 1.0])
    q = _unit(q) if np.linalg.norm(q) > 0 else np.array([0, 0, 0, 1.0])
    # attitude.quat_to_dcm is the ECI->body DCM (v_body = C v_eci); the same
    # scalar-last Hamilton quaternion, used as an ACTIVE rotation, takes body
    # vectors into ECI — i.e. it is the object's local-to-world rotation.
    # Re-express in the smo-vr/1 body axes (see VR_FROM_SIM_BODY).
    C = VR_FROM_SIM_BODY @ att.quat_to_dcm(q)
    q = att.dcm_to_quat(C)
    omega = VR_FROM_SIM_BODY @ np.degrees(np.asarray(
        getattr(a, "omega_true", None) or [0.0, 0.0, 0.0], dtype=float))
    aocs_mode = int(getattr(a, "mode", 0)) if a is not None else 0
    pointing = int(getattr(a, "pointing_frame", 1)) if a is not None else 1

    es = getattr(eps, "_state", None)
    sweep = float(getattr(eps, "_wing_deploy_time_s", 30.0) or 30.0)
    timer = float(getattr(es, "wing_deploy_timer", 0.0) or 0.0)
    # smo-vr/1 +Y is the simulator's -Y: the simulator's -Y wing is the
    # smo-vr/1 +Y wing, and the shaft angle about Y changes sign.
    wing_py = _wing(bool(getattr(es, "wing_my_deployed", False)),
                    bool(getattr(es, "wing_my_deploying", False)),
                    timer, sweep)
    wing_my = _wing(bool(getattr(es, "wing_py_deployed", False)),
                    bool(getattr(es, "wing_py_deploying", False)),
                    timer, sweep)
    sada = -float(getattr(es, "solar_array_drive_angle", 0.0) or 0.0)

    ts = getattr(ttc, "_state", None)
    ant_truth = bool(getattr(ts, "antenna_deployed", False))
    ant_sensor = int(getattr(ts, "antenna_deployment_sensor", 0) or 0)
    if ant_truth:
        ant_state = "DEPLOYED"
    elif ant_sensor == 3:
        ant_state = "JAMMED"
    else:
        ant_state = "STOWED"

    phase = int(getattr(engine, "_spacecraft_phase", 6))
    sim_time = o.utc if getattr(o, "utc", None) is not None \
        else engine.sim_time
    earth_r = float(getattr(getattr(engine, "_orbit_cfg", None),
                            "earth_radius_km", 6371.0) or 6371.0)

    return {
        "sim_time": sim_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "met_s": round(float(getattr(engine, "met_s", 0.0)), 3),
        "tick": int(getattr(engine, "_tick_count", 0)),
        "speed": float(getattr(engine, "speed", 1.0)),
        "orbit": {
            "pos_eci_km": _rl(pos, 3),
            "vel_eci_km_s": _rl(vel, 5),
            "lat_deg": round(float(o.lat_deg), 4),
            "lon_deg": round(float(o.lon_deg), 4),
            "alt_km": round(float(o.alt_km), 3),
        },
        "attitude": {
            "q_body_to_eci": _rl(q, 7),
            "rate_body_deg_s": _rl(omega, 4),
            "aocs_mode": AOCS_MODE_NAMES.get(aocs_mode, f"MODE_{aocs_mode}"),
            "pointing": POINTING_NAMES.get(pointing, f"FRAME_{pointing}"),
        },
        "sun": {
            "dir_eci": _rl(sun_hat, 6),
            "dir_body": _rl(C @ sun_hat, 6),
            "in_eclipse": bool(o.in_eclipse),
            "sun_fraction": round(float(getattr(
                o, "sun_fraction", 0.0 if o.in_eclipse else 1.0)), 3),
        },
        "earth": {
            "dir_body": _rl(C @ nadir_hat, 6),
            "gmst_deg": round(gmst_deg_at(sim_time), 4),
            "radius_km": earth_r,
        },
        "deploy": {
            "wing_py": wing_py,
            "wing_my": wing_my,
            "sada_angle_deg": round(sada, 2),
            "antenna": {
                "state": ant_state,
                "deployed": ant_truth,
                "sensor": ANTENNA_SENSOR_NAMES.get(ant_sensor, "UNKNOWN"),
            },
        },
        "mission": {
            "sc_mode": SC_MODE_NAMES.get(int(getattr(engine, "sc_mode", 0)),
                                         "UNKNOWN"),
            "phase": PHASE_NAMES[phase] if 0 <= phase < len(PHASE_NAMES)
            else f"PHASE_{phase}",
            "in_contact": bool(o.in_contact),
            "ground_station": getattr(o, "active_gs", None) or "",
        },
    }


# smo-vr/1 body faces from the simulator's: +X is shared, +Y and +Z swap sign
# (VR_FROM_SIM_BODY), so the VR "py" face is the simulator's "my" and so on.
VR_FACE_FROM_SIM = {"px": "px", "mx": "mx", "py": "my", "my": "py", "pz": "mz", "mz": "pz"}


def build_vr_power(engine) -> dict:
    """The ``power`` block of the power channel (ICD §5a). Tick thread only.

    Simulation truth from the power model, in the smo-vr/1 body axes. Power on a
    face or wing is its current times the bus voltage (the model's own split).
    """
    eps = (getattr(engine, "subsystems", {}) or {}).get("eps")
    s = getattr(eps, "_state", None)
    if s is None:
        return {}
    bus_v = float(getattr(s, "bus_voltage", 0.0) or 0.0)
    panels = dict(getattr(s, "sa_panel_currents", {}) or {})
    wings = dict(getattr(s, "sa_wing_currents", {}) or {})

    def amps_watts(i: float) -> dict:
        return {"current_a": round(i, 3), "power_w": round(i * bus_v, 2)}

    faces = {}
    for vr_face, sim_face in VR_FACE_FROM_SIM.items():
        body_i = float(panels.get(sim_face, 0.0) or 0.0) - float(wings.get(sim_face, 0.0) or 0.0)
        faces[vr_face] = amps_watts(max(0.0, body_i))
    wing_py_i = float(wings.get("my", 0.0) or 0.0)      # smo-vr/1 +Y wing = simulator -Y wing
    wing_my_i = float(wings.get("py", 0.0) or 0.0)
    gen = float(getattr(s, "power_gen_w", 0.0) or 0.0)
    cons = float(getattr(s, "power_cons_w", 0.0) or 0.0)
    bat_i = float(getattr(s, "bat_current", 0.0) or 0.0)
    return {
        "bus_voltage_v": round(bus_v, 3),
        "generated_w": round(gen, 2),
        "consumed_w": round(cons, 2),
        "net_w": round(gen - cons, 2),
        "wings": {
            "wing_py": dict(amps_watts(wing_py_i), deployed=bool(getattr(s, "wing_my_deployed", False))),
            "wing_my": dict(amps_watts(wing_my_i), deployed=bool(getattr(s, "wing_py_deployed", False))),
            "sada_angle_deg": round(-float(getattr(s, "solar_array_drive_angle", 0.0) or 0.0), 2),
        },
        "body_faces": faces,
        "strings": {
            "a": {"voltage_v": round(float(getattr(s, "sa_a_voltage", 0.0) or 0.0), 3),
                  "current_a": round(float(getattr(s, "sa_a_current", 0.0) or 0.0), 3),
                  "enabled": bool(getattr(s, "sa_a_enabled", True))},
            "b": {"voltage_v": round(float(getattr(s, "sa_b_voltage", 0.0) or 0.0), 3),
                  "current_a": round(float(getattr(s, "sa_b_current", 0.0) or 0.0), 3),
                  "enabled": bool(getattr(s, "sa_b_enabled", True))},
        },
        "battery": {
            "soc_pct": round(float(getattr(s, "bat_soc_pct", 0.0) or 0.0), 2),
            "voltage_v": round(float(getattr(s, "bat_voltage", 0.0) or 0.0), 3),
            "current_a": round(bat_i, 3),
            "charging": bat_i > 0.05,
            "temp_c": round(float(getattr(s, "bat_temp", 0.0) or 0.0), 2),
        },
        "load_shed_stage": int(getattr(s, "load_shed_stage", 0) or 0),
    }


POWER_FIELDS = (
    "power: bus_voltage_v; generated_w, consumed_w, net_w (W); wings.wing_py/wing_my "
    "{current_a, power_w, deployed}, wings.sada_angle_deg; body_faces.px..mz {current_a, power_w} "
    "(smo-vr/1 body axes, wings excluded); strings.a/b {voltage_v, current_a, enabled}; battery "
    "{soc_pct, voltage_v, current_a (+ = charging), charging, temp_c}; load_shed_stage 0-3")


def build_hello(source: str, max_rate_hz: float,
                tcp_port: int | None = None,
                ws_port: int | None = None,
                channel: str = "state") -> dict:
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


# ─────────────────────────────────────────────────────────────────────────
#  Return line (client -> server)
# ─────────────────────────────────────────────────────────────────────────

def parse_client_message(text: str) -> tuple[Optional[dict], Optional[str]]:
    """Validate one inbound line. Returns (message, None) or (None, error)."""
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
    out: dict[str, Any] = {"type": "status", "status_word": word}
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


def decode_status_word(word: int) -> list[str]:
    return [name for bit, name in STATUS_BITS.items() if word & (1 << bit)]


@dataclass
class VRClient:
    cid: int
    transport: str
    peer: str
    connected_at: float = field(default_factory=time.monotonic)
    frames_sent: int = 0
    rx_count: int = 0
    rx_errors: int = 0
    last_error: str = ""
    last_rx: Optional[float] = None
    team: str = ""
    status_word: Optional[int] = None
    state: Optional[str] = None
    text: str = ""
    fps: Optional[float] = None
    seq_ack: Optional[int] = None
    health: str = "NO_REPLY"

    def evaluate(self, now: float) -> str:
        if self.last_rx is None:
            return "NO_REPLY"
        if now - self.last_rx > SILENT_AFTER_S:
            return "SILENT"
        if self.state == "ERROR":
            return "ERROR"
        if (self.status_word or 0) & HEALTHY_MASK == HEALTHY_MASK \
                and self.state in (None, "OK"):
            return "OK"
        return "DEGRADED"


class VRLinkMonitor:
    """Book-keeping for connected viewers and their optional status line."""

    def __init__(self, tcp_port: int | None = None,
                 ws_port: int | None = None):
        self.channel = "state"
        self.tcp_port = tcp_port
        self.ws_port = ws_port
        self._clients: dict[int, VRClient] = {}
        self._next_id = 1
        self.current_seq = 0

    def register(self, transport: str, peer: str) -> VRClient:
        c = VRClient(cid=self._next_id, transport=transport, peer=peer)
        self._next_id += 1
        self._clients[c.cid] = c
        logger.info("VR client %d connected (%s %s)", c.cid, transport, peer)
        return c

    def unregister(self, client: VRClient) -> None:
        if self._clients.pop(client.cid, None) is not None:
            logger.info("VR client %d (%s) disconnected after %d frames",
                        client.cid, client.team or client.peer,
                        client.frames_sent)

    def on_text(self, client: VRClient, text) -> Optional[str]:
        """Handle one inbound line/message. Returns an error string or None."""
        msg, err = parse_client_message(text)
        if err is not None:
            client.rx_errors += 1
            client.last_error = err
            logger.debug("VR client %d bad message: %s", client.cid, err)
            return err
        client.rx_count += 1
        client.last_rx = time.monotonic()
        client.status_word = msg["status_word"]
        client.state = msg.get("state")
        client.team = msg.get("team", client.team)
        client.text = msg.get("text", "")
        client.fps = msg.get("fps", client.fps)
        client.seq_ack = msg.get("seq_ack", client.seq_ack)
        self.refresh()
        return None

    def refresh(self) -> None:
        now = time.monotonic()
        for c in self._clients.values():
            h = c.evaluate(now)
            if h != c.health:
                log = logger.warning if h in ("SILENT", "ERROR",
                                              "DEGRADED") else logger.info
                log("VR client %d (%s): %s -> %s  word=%s %s", c.cid,
                    c.team or c.peer, c.health, h,
                    f"0x{c.status_word:04X}" if c.status_word is not None
                    else "-", c.text)
                c.health = h

    @property
    def clients(self) -> list[VRClient]:
        return list(self._clients.values())

    def summary(self) -> dict:
        self.refresh()
        now = time.monotonic()
        rows = []
        for c in self._clients.values():
            rows.append({
                "id": c.cid,
                "channel": self.channel,
                "team": c.team,
                "transport": c.transport,
                "peer": c.peer,
                "health": c.health,
                "status_word": c.status_word,
                "status_word_hex": (f"0x{c.status_word:04X}"
                                    if c.status_word is not None else None),
                "status_bits": (decode_status_word(c.status_word)
                                if c.status_word is not None else []),
                "state": c.state,
                "text": c.text,
                "fps": c.fps,
                "frames_sent": c.frames_sent,
                "lag_frames": (self.current_seq - c.seq_ack
                               if c.seq_ack is not None else None),
                "rx_count": c.rx_count,
                "rx_errors": c.rx_errors,
                "last_error": c.last_error,
                "last_rx_age_s": (round(now - c.last_rx, 1)
                                  if c.last_rx is not None else None),
                "connected_s": round(now - c.connected_at, 1),
            })
        if rows:
            overall = max((r["health"] for r in rows),
                          key=HEALTH_ORDER.index)
        else:
            overall = "NO_CLIENTS"
        return {
            "enabled": True,
            "schema": SCHEMA,
            "tcp_port": self.tcp_port,
            "ws_port": self.ws_port,
            "n_clients": len(rows),
            "overall": overall,
            "clients": rows,
        }


def merge_summaries(by_channel: dict) -> dict:
    """One instructor view of every channel: the ``state`` summary's fields, all clients
    (each row names its channel), and the power channel's ports."""
    summaries = [v for v in by_channel.values() if v]
    if not summaries:
        return {"enabled": False}
    base = dict(by_channel.get("state") or summaries[0])
    rows = [r for v in summaries for r in v.get("clients", [])]
    base["clients"] = rows
    base["n_clients"] = len(rows)
    base["overall"] = (max((r["health"] for r in rows), key=HEALTH_ORDER.index)
                       if rows else "NO_CLIENTS")
    pw = by_channel.get("power")
    if pw:
        base["power_tcp_port"], base["power_ws_port"] = pw.get("tcp_port"), pw.get("ws_port")
    return base


# ─────────────────────────────────────────────────────────────────────────
#  The bridge (asyncio side)
# ─────────────────────────────────────────────────────────────────────────

def _dumps(obj: dict) -> str:
    return json.dumps(obj, separators=(",", ":"))


class VRBridge:
    """Serve ``smo-vr/1`` over TCP (NDJSON) and WebSocket.

    ``get_state`` returns the latest published state body (or None before the
    first tick); ``on_summary`` receives the link summary whenever it may
    have changed.
    """

    def __init__(self, get_state: Callable[[], Optional[dict]], *,
                 host: str = "0.0.0.0",
                 tcp_port: int | None = DEFAULT_TCP_PORT,
                 ws_port: int | None = DEFAULT_WS_PORT,
                 max_rate_hz: float = DEFAULT_MAX_RATE_HZ,
                 source: str = "smo-simulator",
                 on_summary: Optional[Callable[[dict], None]] = None,
                 channel: str = "state"):
        self._get_state = get_state
        self.channel = channel
        self._host = host
        self.tcp_port = tcp_port
        self.ws_port = ws_port
        self.max_rate_hz = max(0.5, float(max_rate_hz))
        self._source = source
        self._on_summary = on_summary
        self.monitor = VRLinkMonitor(tcp_port, ws_port)
        self.monitor.channel = channel
        if channel != "state":                 # ids stay unique across channels
            self.monitor._next_id = 1001
        self._writers: dict[int, Any] = {}   # cid -> send coroutine fn
        self._seq = 0
        self._last_line: Optional[str] = None
        self._running = False
        self._tcp_server = None
        self._ws_runner = None
        self._task: Optional[asyncio.Task] = None

    # -- lifecycle ----------------------------------------------------------

    async def start(self) -> None:
        self._running = True
        if self.tcp_port is not None:
            self._tcp_server = await asyncio.start_server(
                self._handle_tcp, self._host, self.tcp_port,
                limit=MAX_LINE_BYTES)
            if self.tcp_port == 0:
                self.tcp_port = self._tcp_server.sockets[0].getsockname()[1]
        if self.ws_port is not None:
            from aiohttp import web
            app = web.Application()
            app.router.add_get("/", self._handle_ws)
            app.router.add_get("/vr", self._handle_ws)
            self._ws_runner = web.AppRunner(app)
            await self._ws_runner.setup()
            site = web.TCPSite(self._ws_runner, self._host, self.ws_port)
            await site.start()
            if self.ws_port == 0:
                self.ws_port = site._server.sockets[0].getsockname()[1]
        self.monitor.tcp_port, self.monitor.ws_port = self.tcp_port, self.ws_port
        self._publish_summary()
        self._task = asyncio.ensure_future(self._broadcast_loop())
        logger.info("VR bridge (%s, %s channel) on %s — TCP:%s WS:%s max %.1f Hz",
                    SCHEMA, self.channel, self._host, self.tcp_port, self.ws_port,
                    self.max_rate_hz)

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
        if self._tcp_server:
            self._tcp_server.close()
        if self._ws_runner:
            await self._ws_runner.cleanup()

    async def serve_forever(self) -> None:
        await self.start()
        while self._running:
            await asyncio.sleep(3600)

    # -- outbound -----------------------------------------------------------

    def _hello_line(self) -> str:
        return _dumps(build_hello(self._source, self.max_rate_hz,
                                  self.tcp_port, self.ws_port, self.channel))

    def _next_frame_line(self, body: dict) -> str:
        self._seq += 1
        self.monitor.current_seq = self._seq
        msg = {"type": "state", "schema": SCHEMA, "seq": self._seq}
        msg.update(body)
        return _dumps(msg)

    async def _broadcast_loop(self) -> None:
        period = 1.0 / self.max_rate_hz
        last_key = None
        last_sent = 0.0
        last_summary = 0.0
        while self._running:
            await asyncio.sleep(period)
            now = time.monotonic()
            try:
                body = self._get_state()
            except Exception as e:  # noqa: BLE001
                logger.debug("VR state unavailable: %s", e)
                body = None
            if body is not None:
                key = (body.get("tick"), body.get("sim_time"))
                if key != last_key or now - last_sent >= KEEPALIVE_S:
                    last_key, last_sent = key, now
                    self._last_line = self._next_frame_line(body)
                    await self._send_all(self._last_line)
            if now - last_summary >= 1.0:
                last_summary = now
                self._publish_summary()

    async def _send_all(self, line: str) -> None:
        dead = []
        for client in self.monitor.clients:
            send = self._writers.get(client.cid)
            if send is None:
                continue
            try:
                await asyncio.wait_for(send(line), timeout=WRITE_TIMEOUT_S)
                client.frames_sent += 1
            except Exception:  # noqa: BLE001 — slow or gone: drop it
                dead.append(client)
        for c in dead:
            self._writers.pop(c.cid, None)
            self.monitor.unregister(c)
        if dead:
            self._publish_summary()

    def _publish_summary(self) -> None:
        if self._on_summary is None:
            return
        try:
            self._on_summary(self.monitor.summary())
        except Exception as e:  # noqa: BLE001
            logger.debug("VR summary publish failed: %s", e)

    # -- TCP ----------------------------------------------------------------

    async def _handle_tcp(self, reader: asyncio.StreamReader,
                          writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        client = self.monitor.register("tcp", f"{peer[0]}:{peer[1]}"
                                       if peer else "?")

        async def send(line: str) -> None:
            writer.write((line + "\n").encode("utf-8"))
            await writer.drain()

        try:
            await send(self._hello_line())
            if self._last_line:
                await send(self._last_line)
                client.frames_sent += 1
            self._writers[client.cid] = send
            self._publish_summary()
            while self._running:
                try:
                    raw = await reader.readline()
                except (asyncio.LimitOverrunError, ValueError):
                    client.rx_errors += 1
                    client.last_error = f"line longer than {MAX_LINE_BYTES} B"
                    # StreamReader.readline has already discarded the
                    # oversize data; carry on with the next line.
                    continue
                if not raw:
                    break
                if raw.strip():
                    self.monitor.on_text(client, raw)
                    self._publish_summary()
        except (ConnectionError, asyncio.IncompleteReadError):
            pass
        except Exception as e:  # noqa: BLE001
            logger.debug("VR TCP client error: %s", e)
        finally:
            self._writers.pop(client.cid, None)
            self.monitor.unregister(client)
            self._publish_summary()
            try:
                writer.close()
            except Exception:  # noqa: BLE001
                pass

    # -- WebSocket ----------------------------------------------------------

    async def handle_ws(self, request):
        """The WebSocket stream; also mounted on the simulator's HTTP port (``/vr``,
        ``/vr/power``) so the space link can carry it to the cloud."""
        return await self._handle_ws(request)

    async def _handle_ws(self, request):
        from aiohttp import web, WSMsgType
        ws = web.WebSocketResponse(heartbeat=10.0,
                                   max_msg_size=MAX_LINE_BYTES)
        await ws.prepare(request)
        # through the space link the socket peer is the link agent: prefer the forwarded address
        peer = (request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
                or str(request.remote or "?"))
        client = self.monitor.register("ws", peer)

        async def send(line: str) -> None:
            await ws.send_str(line)

        try:
            await send(self._hello_line())
            if self._last_line:
                await send(self._last_line)
                client.frames_sent += 1
            self._writers[client.cid] = send
            self._publish_summary()
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    self.monitor.on_text(client, msg.data)
                    self._publish_summary()
                elif msg.type == WSMsgType.BINARY:
                    self.monitor.on_text(client, msg.data)
                elif msg.type in (WSMsgType.ERROR, WSMsgType.CLOSE):
                    break
        except Exception as e:  # noqa: BLE001
            logger.debug("VR WS client error: %s", e)
        finally:
            self._writers.pop(client.cid, None)
            self.monitor.unregister(client)
            self._publish_summary()
        return ws
