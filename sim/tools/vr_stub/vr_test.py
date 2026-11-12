#!/usr/bin/env python3
"""vr_test.py — check the EOSAT-1 VR interface (smo-vr/1, all three channels).

It connects like a headset would, reads what the server sends, and checks every
message against the interface (docs/VR_INTERFACE_ICD.md). Use it to find out
whether a problem is in the link or in your headset code.

    python3 vr_test.py check                          # channel 1 (state) on this laptop, TCP 8100
    python3 vr_test.py check --channel power          # channel 2 (power), TCP 8102
    python3 vr_test.py check --channel requests       # channel 3: hello + a harmless probe
    python3 vr_test.py check --host 192.168.1.20 --ws # the cyber-range machine, WebSocket
    python3 vr_test.py check --cloud --channel power  # wss://ops.c2o.live/vr/power
    python3 vr_test.py watch --channel power          # one readable line per frame
    python3 vr_test.py request deploy_antenna --team T07   # ask the flight director, follow the answer
    python3 vr_test.py file sample_vr_frames.ndjson   # check a sample or a recording, list its events
    python3 vr_test.py selftest                       # start vr_stub.py and check everything against it

What it checks (each check prints PASS, WARN or FAIL, then one RESULT line):
the hello and its schema; message rate and sequence numbers; that positions,
velocities and altitude look like low Earth orbit; that the quaternion is unit
length and agrees with the Sun and Earth directions (a wrong axis or a scalar-first
quaternion fails here); unit vectors; deployment states and fractions; known
values for the modes; the power block on channel 2; the request round trip on
channel 3.

The solar panels of the VR model are FIXED FLAPS: they swing out from the long
sides until level with the top deck and never rotate. The interface also carries a
panel rotation angle (deploy.sada_angle_deg, power.wings.sada_angle_deg,
hello.spacecraft.sada). These are marked DO NOT USE for the VR project: this tool
reports that they are present and otherwise ignores them. The flap angle it shows
is 90 degrees x deploy fraction (0 = folded down the side, 90 = level with the top deck).

Python 3.8 or newer, standard library only. Exit code 0 = no FAIL.
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import os
import socket
import ssl
import struct
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from urllib.parse import urlparse

SCHEMA = "smo-vr/1"
CHANNELS = ("state", "power", "requests")
PORTS = {"state": (8100, 8101, "/vr"), "power": (8102, 8103, "/vr"),
         "requests": (8104, 8105, "/vr/requests")}
CLOUD = {"state": "wss://ops.c2o.live/vr", "power": "wss://ops.c2o.live/vr/power",
         "requests": "wss://ops.c2o.live/vr/requests"}
REQUESTS = ("deploy_antenna", "deploy_wing_py", "deploy_wing_my", "deploy_both_wings")
EARTH_R_KM = 6371.0
DO_NOT_USE = ("deploy.sada_angle_deg", "power.wings.sada_angle_deg", "hello.spacecraft.sada")

ENUMS = {
    "attitude.aocs_mode": {"OFF", "SAFE_BOOT", "DETUMBLE", "COARSE_SUN", "NOMINAL", "FINE_POINT",
                           "SLEW", "DESAT", "ECLIPSE", "INERTIAL"},
    "attitude.pointing": {"NADIR", "INERTIAL", "TARGET_TRACK", "SUN"},
    "deploy.wing.state": {"STOWED", "DEPLOYING", "DEPLOYED"},
    "deploy.antenna.state": {"STOWED", "DEPLOYED", "JAMMED"},
    "deploy.antenna.sensor": {"UNKNOWN", "STOWED", "DEPLOYED", "JAMMED"},
    "mission.sc_mode": {"SAFE", "NOMINAL", "SCIENCE", "EMERGENCY"},
    "mission.phase": {"PRE_SEPARATION", "SEPARATION_TIMER", "INITIAL_POWER_ON", "BOOTLOADER_OPS",
                      "LEOP", "COMMISSIONING", "NOMINAL"},
}

USE_COLOUR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
COLOURS = {"PASS": "32", "WARN": "33", "FAIL": "31", "INFO": "36"}


def tag(level):
    word = f"{level:<4}"
    return f"\033[{COLOURS[level]}m{word}\033[0m" if USE_COLOUR else word


# ═════════════════════════════════════════════════════════════════════════
#  Vector and quaternion helpers
# ═════════════════════════════════════════════════════════════════════════

def norm(v):
    return math.sqrt(sum(x * x for x in v))


def is_vec(v, n=3):
    return isinstance(v, list) and len(v) == n and all(
        isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) for x in v)


def rotate(q, v):
    """v_eci = q (x) v_body (x) q*, q = [x, y, z, w] scalar last (ICD section 6)."""
    x, y, z, w = q
    # t = 2 * (q_vec x v); v' = v + w t + q_vec x t
    tx = 2 * (y * v[2] - z * v[1])
    ty = 2 * (z * v[0] - x * v[2])
    tz = 2 * (x * v[1] - y * v[0])
    return [v[0] + w * tx + (y * tz - z * ty),
            v[1] + w * ty + (z * tx - x * tz),
            v[2] + w * tz + (x * ty - y * tx)]


def angle_deg(a, b):
    na, nb = norm(a), norm(b)
    if na == 0 or nb == 0:
        return 180.0
    c = sum(x * y for x, y in zip(a, b)) / (na * nb)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def get(d, path, default=None):
    for part in path.split("."):
        if not isinstance(d, dict) or part not in d:
            return default
        d = d[part]
    return d


def num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def flap_deg(frac):
    """The VR model's flap hinge angle: 0 = folded down the long side, 90 = level with the top deck."""
    return 90.0 * max(0.0, min(1.0, float(frac or 0.0)))


# ═════════════════════════════════════════════════════════════════════════
#  Results: every check counts its passes and keeps its worst case
# ═════════════════════════════════════════════════════════════════════════

class Report:
    def __init__(self, title):
        self.title = title
        self.rows = {}          # name -> [level, detail, count_bad, count_all]
        self.order = []
        self.notes = []

    def add(self, name, ok, detail="", level_bad="FAIL"):
        if name not in self.rows:
            self.rows[name] = ["PASS", "", 0, 0]
            self.order.append(name)
        row = self.rows[name]
        row[3] += 1
        if not ok:
            row[2] += 1
            if row[0] == "PASS" or (row[0] == "WARN" and level_bad == "FAIL"):
                row[0] = level_bad
                row[1] = detail

    def set_detail(self, name, detail):
        if name in self.rows and self.rows[name][0] == "PASS":
            self.rows[name][1] = detail

    def info(self, text):
        if text not in self.notes:
            self.notes.append(text)

    def counts(self):
        f = sum(1 for r in self.rows.values() if r[0] == "FAIL")
        w = sum(1 for r in self.rows.values() if r[0] == "WARN")
        return f, w

    def print(self):
        print(self.title)
        for name in self.order:
            level, detail, bad, total = self.rows[name]
            extra = f" ({bad} of {total})" if bad and total > 1 else ""
            print(f"  {tag(level)}  {name}{extra}" + (f": {detail}" if detail else ""))
        for n in self.notes:
            print(f"  {tag('INFO')}  {n}")
        f, w = self.counts()
        verdict = "FAIL" if f else ("WARN" if w else "PASS")
        print(f"RESULT: {tag(verdict)} ({f} fail, {w} warn)\n")
        return verdict


# ═════════════════════════════════════════════════════════════════════════
#  Message checks (the interface, section by section)
# ═════════════════════════════════════════════════════════════════════════

def check_hello(rep, h, expect_channel=None):
    rep.add("hello is the first message", isinstance(h, dict) and h.get("type") == "hello",
            f"got {h.get('type') if isinstance(h, dict) else h!r}")
    if not isinstance(h, dict) or h.get("type") != "hello":
        return None
    schema = str(h.get("schema", ""))
    rep.add("schema is smo-vr/1", schema.split(".")[0] == SCHEMA, f"schema {schema!r}")
    channel = h.get("channel", "state")
    rep.add("hello names its channel", channel in CHANNELS, f"channel {channel!r}")
    if expect_channel:
        rep.add("connected to the channel asked for", channel == expect_channel,
                f"asked for {expect_channel}, server says {channel}")
    rep.set_detail("hello names its channel",
                   f"{channel}" + (" (no channel field: the original channel-1 hello)" if "channel" not in h else ""))
    rep.set_detail("schema is smo-vr/1", f"source {h.get('source', '?')}")
    if channel in ("state", "power"):
        rep.add("hello: max_rate_hz", num(h.get("max_rate_hz")) and h["max_rate_hz"] > 0,
                f"{h.get('max_rate_hz')!r}")
        rep.add("hello: spacecraft bus size", is_vec(get(h, "spacecraft.bus_size_m")),
                f"{get(h, 'spacecraft.bus_size_m')!r}", "WARN")
        if get(h, "spacecraft.sada") is not None:
            rep.info("hello.spacecraft.sada is present: DO NOT USE (the flaps are fixed)")
    if channel == "power":
        rep.add("hello: power_fields summary", isinstance(h.get("power_fields"), str), "", "WARN")
    if channel == "requests":
        offered = set(h.get("requests") or {})
        rep.add("hello lists the four requests", set(REQUESTS) <= offered,
                f"missing {sorted(set(REQUESTS) - offered)}")
    return channel


class FrameChecker:
    """Checks state frames one by one and keeps what it needs across frames."""

    def __init__(self, rep, channel):
        self.rep = rep
        self.channel = channel
        self.last_seq = None
        self.gaps = self.repeats = self.backwards = 0
        self.unknown_top = set()
        self.n = 0
        self.worst = {"q": 0.0, "sun": 0.0, "earth": 0.0, "unit": 0.0, "alt": 0.0}

    KNOWN_TOP = {"type", "schema", "seq", "sim_time", "met_s", "tick", "speed", "orbit", "attitude",
                 "sun", "earth", "deploy", "mission", "power"}

    def frame(self, m):
        rep = self.rep
        self.n += 1
        rep.add("state: type and schema", m.get("type") == "state" and str(m.get("schema", "")).split(".")[0] == SCHEMA,
                f"type {m.get('type')!r} schema {m.get('schema')!r}")
        self.unknown_top |= set(m) - self.KNOWN_TOP

        seq = m.get("seq")
        rep.add("state: seq is an integer", isinstance(seq, int) and not isinstance(seq, bool), f"{seq!r}")
        if isinstance(seq, int) and self.last_seq is not None:
            if seq == self.last_seq:
                self.repeats += 1
            elif seq > self.last_seq + 1:
                self.gaps += 1
            elif seq < self.last_seq:
                self.backwards += 1
        if isinstance(seq, int):
            self.last_seq = seq

        t = m.get("sim_time")
        ok_t = isinstance(t, str)
        if ok_t:
            try:
                datetime.fromisoformat(t.replace("Z", "+00:00"))
            except ValueError:
                ok_t = False
        rep.add("state: sim_time is ISO-8601 UTC", ok_t, f"{t!r}")
        for k in ("met_s", "speed"):
            rep.add(f"state: {k} is a number", num(m.get(k)), f"{m.get(k)!r}")

        # Orbit
        pos, vel = get(m, "orbit.pos_eci_km"), get(m, "orbit.vel_eci_km_s")
        rep.add("orbit: position and velocity are 3-vectors", is_vec(pos) and is_vec(vel),
                f"pos {pos!r} vel {vel!r}")
        if is_vec(pos) and is_vec(vel):
            r, v = norm(pos), norm(vel)
            rep.add("orbit: low Earth orbit (200-2000 km, 6.5-8.5 km/s)",
                    EARTH_R_KM + 150 < r < EARTH_R_KM + 2000 and 6.5 < v < 8.5,
                    f"|pos| = {r:.1f} km, |vel| = {v:.3f} km/s")
            rep.set_detail("orbit: low Earth orbit (200-2000 km, 6.5-8.5 km/s)",
                           f"altitude about {r - EARTH_R_KM:.0f} km, {v:.2f} km/s")
            alt = get(m, "orbit.alt_km")
            if num(alt):
                d = abs(alt - (r - EARTH_R_KM))
                self.worst["alt"] = max(self.worst["alt"], d)
                rep.add("orbit: alt_km agrees with the position (within 40 km)", d < 40,
                        f"alt_km {alt:.1f} vs |pos| - R {r - EARTH_R_KM:.1f}", "WARN")
        for k in ("lat_deg", "lon_deg"):
            val = get(m, "orbit." + k)
            rep.add("orbit: latitude and longitude in range", num(val) and abs(val) <= (90 if k == "lat_deg" else 180),
                    f"{k} {val!r}", "WARN")

        # Attitude
        q = get(m, "attitude.q_body_to_eci")
        rep.add("attitude: quaternion is [x, y, z, w]", is_vec(q, 4), f"{q!r}")
        qok = is_vec(q, 4) and abs(norm(q) - 1) < 1e-3
        if is_vec(q, 4):
            self.worst["q"] = max(self.worst["q"], abs(norm(q) - 1))
            rep.add("attitude: quaternion has unit length", qok, f"|q| = {norm(q):.6f}")
        rep.add("attitude: body rate is a 3-vector", is_vec(get(m, "attitude.rate_body_deg_s")), "", "WARN")
        self.enum(m, "attitude.aocs_mode")
        self.enum(m, "attitude.pointing")

        # Sun and Earth, and their agreement with the quaternion: this is the check that catches a
        # swapped axis or a scalar-first quaternion.
        s_eci, s_body = get(m, "sun.dir_eci"), get(m, "sun.dir_body")
        e_body = get(m, "earth.dir_body")
        for name, vec in (("sun.dir_eci", s_eci), ("sun.dir_body", s_body), ("earth.dir_body", e_body)):
            ok = is_vec(vec) and abs(norm(vec) - 1) < 2e-3
            if is_vec(vec):
                self.worst["unit"] = max(self.worst["unit"], abs(norm(vec) - 1))
            rep.add("sun and earth: unit vectors", ok, f"{name} = {vec!r}")
        if qok and is_vec(s_eci) and is_vec(s_body):
            a = angle_deg(rotate(q, s_body), s_eci)
            self.worst["sun"] = max(self.worst["sun"], a)
            rep.add("quaternion turns sun.dir_body into sun.dir_eci (within 1 deg)", a < 1.0,
                    f"off by {a:.2f} deg")
        if qok and is_vec(e_body) and is_vec(pos):
            a = angle_deg(rotate(q, e_body), [-x for x in pos])
            self.worst["earth"] = max(self.worst["earth"], a)
            rep.add("quaternion turns earth.dir_body towards Earth's centre (within 1 deg)", a < 1.0,
                    f"off by {a:.2f} deg")
        rep.add("sun: in_eclipse is true/false and sun_fraction 0-1",
                isinstance(get(m, "sun.in_eclipse"), bool) and num(get(m, "sun.sun_fraction"))
                and 0 <= get(m, "sun.sun_fraction") <= 1,
                f"in_eclipse {get(m, 'sun.in_eclipse')!r} sun_fraction {get(m, 'sun.sun_fraction')!r}")
        rep.add("earth: gmst_deg and radius_km", num(get(m, "earth.gmst_deg")) and num(get(m, "earth.radius_km")),
                "", "WARN")

        # Deployment (the flaps)
        for wing in ("wing_py", "wing_my"):
            w = get(m, "deploy." + wing)
            st, fr = get(w, "state"), get(w, "fraction")
            ok = st in ENUMS["deploy.wing.state"] and num(fr) and 0 <= fr <= 1
            rep.add("deploy: flap state and fraction", ok, f"{wing} = {w!r}")
            if ok:
                agrees = (st != "STOWED" or fr == 0) and (st != "DEPLOYED" or fr == 1)
                rep.add("deploy: flap fraction agrees with its state", agrees,
                        f"{wing} {st} with fraction {fr}", "WARN")
        if get(m, "deploy.sada_angle_deg") is not None:
            rep.info("deploy.sada_angle_deg is present: DO NOT USE (the flaps are fixed); ignored here")
        self.enum(m, "deploy.antenna.state")
        self.enum(m, "deploy.antenna.sensor")
        rep.add("deploy: antenna.deployed is true/false", isinstance(get(m, "deploy.antenna.deployed"), bool),
                f"{get(m, 'deploy.antenna.deployed')!r}")

        # Mission
        self.enum(m, "mission.sc_mode")
        self.enum(m, "mission.phase")
        rep.add("mission: in_contact is true/false", isinstance(get(m, "mission.in_contact"), bool),
                f"{get(m, 'mission.in_contact')!r}", "WARN")

        # Channel 2
        p = m.get("power")
        if self.channel == "power":
            rep.add("power: every frame carries a power block", isinstance(p, dict), "missing")
        elif p is not None:
            rep.add("power block only on channel 2", False, "a power block on the state channel", "WARN")
        if isinstance(p, dict):
            self.power(p)

    def enum(self, m, path):
        val = get(m, path)
        rep_name = f"{path.split('.')[0]}: {path.split('.', 1)[1]} is a known value"
        self.rep.add(rep_name, val in ENUMS[path], f"{val!r}", "WARN")

    def power(self, p):
        rep = self.rep
        nums = ("bus_voltage_v", "generated_w", "consumed_w", "net_w")
        rep.add("power: bus voltage, generated, consumed, net are numbers",
                all(num(p.get(k)) for k in nums), f"{ {k: p.get(k) for k in nums} }")
        if all(num(p.get(k)) for k in nums):
            d = abs(p["net_w"] - (p["generated_w"] - p["consumed_w"]))
            rep.add("power: net_w = generated_w - consumed_w (within 0.5 W)", d <= 0.5, f"off by {d:.2f} W", "WARN")
        wings = p.get("wings") or {}
        for wing in ("wing_py", "wing_my"):
            w = wings.get(wing) or {}
            rep.add("power: each flap has current_a, power_w, deployed",
                    num(w.get("current_a")) and num(w.get("power_w")) and isinstance(w.get("deployed"), bool),
                    f"{wing} = {w!r}")
        if "sada_angle_deg" in wings:
            rep.info("power.wings.sada_angle_deg is present: DO NOT USE (the flaps are fixed); ignored here")
        faces = p.get("body_faces") or {}
        rep.add("power: six body faces px..mz", all(
            num((faces.get(f) or {}).get("power_w")) for f in ("px", "mx", "py", "my", "pz", "mz")),
            f"faces {sorted(faces)}")
        strings = p.get("strings") or {}
        rep.add("power: strings a and b", all(isinstance(strings.get(s), dict) for s in ("a", "b")),
                f"{sorted(strings)}", "WARN")
        b = p.get("battery") or {}
        rep.add("power: battery charge 0-100 %, voltage, current, temperature",
                num(b.get("soc_pct")) and 0 <= b["soc_pct"] <= 100 and num(b.get("voltage_v"))
                and num(b.get("current_a")) and num(b.get("temp_c")), f"{b!r}")
        rep.add("power: load_shed_stage 0-3", p.get("load_shed_stage") in (0, 1, 2, 3),
                f"{p.get('load_shed_stage')!r}", "WARN")

    def finish(self, seconds=None):
        rep = self.rep
        if self.n == 0:
            rep.add("state frames received", False, "none")
            return
        rate = f", {(self.n - 1) / seconds:.1f} per second" if seconds else ""
        rep.add("state frames received", True)
        rep.set_detail("state frames received", f"{self.n} frames{rate}")
        bits = []
        if self.gaps:
            bits.append(f"{self.gaps} gap(s) = missed frames")
        if self.repeats:
            bits.append(f"{self.repeats} repeat(s) = keepalives while paused")
        rep.add("state: seq never goes backwards", self.backwards == 0,
                f"{self.backwards} time(s): the server restarted, or a replay looped", "WARN")
        rep.set_detail("state: seq is an integer", "; ".join(bits) or "no gaps, no repeats")
        rep.set_detail("attitude: quaternion has unit length", f"worst |q| - 1 = {self.worst['q']:.1e}")
        rep.set_detail("quaternion turns sun.dir_body into sun.dir_eci (within 1 deg)",
                       f"worst {self.worst['sun']:.3f} deg")
        rep.set_detail("quaternion turns earth.dir_body towards Earth's centre (within 1 deg)",
                       f"worst {self.worst['earth']:.3f} deg")
        rep.set_detail("orbit: alt_km agrees with the position (within 40 km)",
                       f"worst {self.worst['alt']:.1f} km (the simulator uses the ellipsoid)")
        if self.unknown_top:
            rep.info(f"fields this tool does not know (ignore them in your client too): {sorted(self.unknown_top)}")


# ═════════════════════════════════════════════════════════════════════════
#  Connections: TCP lines, or WebSocket text messages (ws:// and wss://)
# ═════════════════════════════════════════════════════════════════════════

class Conn:
    def __init__(self, sock, ws):
        self.sock, self.ws, self.buf = sock, ws, b""
        self.label = ""

    @classmethod
    def open(cls, target, timeout=10.0):
        u = urlparse(target if "://" in target else "tcp://" + target)
        if u.scheme == "tcp":
            s = socket.create_connection((u.hostname, u.port), timeout=timeout)
            c = cls(s, False)
        elif u.scheme in ("ws", "wss"):
            port = u.port or (443 if u.scheme == "wss" else 80)
            s = socket.create_connection((u.hostname, port), timeout=timeout)
            if u.scheme == "wss":
                s = ssl.create_default_context().wrap_socket(s, server_hostname=u.hostname)
            key = base64.b64encode(os.urandom(16)).decode()
            path = (u.path or "/") + (("?" + u.query) if u.query else "")
            s.sendall((f"GET {path} HTTP/1.1\r\nHost: {u.hostname}:{port}\r\nUpgrade: websocket\r\n"
                       f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n"
                       f"User-Agent: vr_test\r\n\r\n").encode())
            c = cls(s, True)
            head = c._read_until(b"\r\n\r\n", timeout)
            status = head.split(b"\r\n", 1)[0].decode("latin-1")
            if " 101" not in status:
                low = head.lower()
                if b"x-goog-iap" in low or b"accounts.google.com" in low:
                    raise ConnectionError("the address asks for a Google sign-in, so the cloud VR routes are "
                                          "not open yet (instructor: rerun deploy/gcp/setup.sh)")
                if b" 404" in status.encode() or " 502" in status or " 503" in status:
                    raise ConnectionError(f"{status.strip()}: the simulator behind this address is not running "
                                          f"(is the class on? c2o up)")
                raise ConnectionError(f"WebSocket upgrade refused: {status.strip()}")
        else:
            raise ValueError(f"unknown address {target!r}: use host:port, tcp://, ws:// or wss://")
        c.label = target
        return c

    def _fill(self, timeout):
        self.sock.settimeout(timeout)
        data = self.sock.recv(65536)
        if not data:
            raise ConnectionError("the server closed the connection")
        self.buf += data

    def _read_until(self, marker, timeout):
        end = time.monotonic() + timeout
        while marker not in self.buf:
            self._fill(max(0.05, end - time.monotonic()))
        i = self.buf.index(marker) + len(marker)
        out, self.buf = self.buf[:i], self.buf[i:]
        return out

    def _read_n(self, n, timeout):
        end = time.monotonic() + timeout
        while len(self.buf) < n:
            self._fill(max(0.05, end - time.monotonic()))
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def recv(self, timeout):
        """The next message as text, or None after `timeout` seconds of silence."""
        try:
            if not self.ws:
                return self._read_until(b"\n", timeout).decode("utf-8", "replace").rstrip("\r\n")
            parts = []
            while True:
                b0, b1 = self._read_n(2, timeout)
                op, ln = b0 & 0x0F, b1 & 0x7F
                if ln == 126:
                    ln = struct.unpack("!H", self._read_n(2, timeout))[0]
                elif ln == 127:
                    ln = struct.unpack("!Q", self._read_n(8, timeout))[0]
                mask = self._read_n(4, timeout) if b1 & 0x80 else None
                data = self._read_n(ln, timeout)
                if mask:
                    data = bytes(x ^ mask[i % 4] for i, x in enumerate(data))
                if op == 0x8:
                    raise ConnectionError("the server closed the WebSocket")
                if op == 0x9:
                    self._send_frame(0xA, data)
                    continue
                if op in (0x1, 0x0, 0x2):
                    parts.append(data)
                    if b0 & 0x80:
                        return b"".join(parts).decode("utf-8", "replace")
        except socket.timeout:
            return None

    def _send_frame(self, op, payload):
        mask = os.urandom(4)
        n = len(payload)
        head = bytes([0x80 | op])
        if n < 126:
            head += bytes([0x80 | n])
        elif n < 65536:
            head += bytes([0x80 | 126]) + struct.pack("!H", n)
        else:
            head += bytes([0x80 | 127]) + struct.pack("!Q", n)
        self.sock.sendall(head + mask + bytes(x ^ mask[i % 4] for i, x in enumerate(payload)))

    def send(self, text):
        if self.ws:
            self._send_frame(0x1, text.encode("utf-8"))
        else:
            self.sock.sendall((text + "\n").encode("utf-8"))

    def close(self):
        try:
            if self.ws:
                self._send_frame(0x8, b"")
            self.sock.close()
        except OSError:
            pass


def target_for(args, channel):
    if getattr(args, "url", None):
        return args.url
    if args.cloud:
        return CLOUD[channel]
    tcp, ws, path = PORTS[channel]
    if args.ws:
        return f"ws://{args.host}:{args.port or ws}{path}"
    return f"tcp://{args.host}:{args.port or tcp}"


def parse(text):
    try:
        m = json.loads(text)
        return m if isinstance(m, dict) else None
    except (TypeError, ValueError):
        return None


# ═════════════════════════════════════════════════════════════════════════
#  Commands
# ═════════════════════════════════════════════════════════════════════════

def run_check(target, channel, frames=10, timeout=15.0, team=None, status_word=0x000B, quiet=False):
    """Connect, check the hello and `frames` messages. Returns the verdict."""
    rep = Report(f"vr_test check: channel {channel} at {target}")
    try:
        c = Conn.open(target, timeout)
    except (OSError, ValueError, ConnectionError) as e:
        hint = "" if "sign-in" in str(e) or "not running" in str(e) else \
            ". Is the server running, the address right, the port open?"
        rep.add("connect", False, f"{e}{hint}")
        return rep.print() if not quiet else rep
    rep.add("connect", True)
    rep.set_detail("connect", "TCP, one JSON object per line" if not c.ws else "WebSocket, one JSON object per message")
    try:
        first = c.recv(timeout)
        if first is None:
            rep.add("hello is the first message", False, f"nothing within {timeout:.0f} s")
            return rep.print() if not quiet else rep
        hello = parse(first)
        rep.add("every message is a JSON object", hello is not None, f"first line {first[:80]!r}")
        got = check_hello(rep, hello or {}, channel)
        if got == "requests":
            probe_requests(rep, c, timeout)
        elif got in ("state", "power"):
            fc = FrameChecker(rep, got)
            t0 = time.monotonic()
            first_t = None
            while fc.n < frames and time.monotonic() - t0 < timeout + frames * 2:
                line = c.recv(timeout)
                if line is None:
                    rep.add("frames keep coming", False, f"silence for {timeout:.0f} s")
                    break
                m = parse(line)
                rep.add("every message is a JSON object", m is not None, f"bad line {line[:80]!r}", "WARN")
                if m is None:
                    continue
                if m.get("type") != "state":
                    rep.info(f"message type {m.get('type')!r} ignored (clients ignore types they do not know)")
                    continue
                if first_t is None:
                    first_t = time.monotonic()
                fc.frame(m)
                if team:
                    c.send(json.dumps({"type": "status", "team": team, "status_word": status_word,
                                       "state": "OK", "seq_ack": m.get("seq"), "text": "vr_test link check"}))
            fc.finish((time.monotonic() - first_t) if first_t and fc.n > 1 else None)
            if team:
                rep.info(f"sent a status line per frame as team {team!r} (status_word {status_word}); "
                         f"the instructor console shows it")
    except (OSError, ConnectionError) as e:
        rep.add("connection stays up", False, str(e))
    finally:
        c.close()
    return rep.print() if not quiet else rep


def probe_requests(rep, c, timeout):
    """A harmless round trip on channel 3: an unknown request must come back rejected, and
    creates nothing for the flight director."""
    c.send(json.dumps({"type": "request", "request": "vr_test_probe", "team": "vr_test"}))
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        line = c.recv(max(0.1, end - time.monotonic()))
        if line is None:
            break
        m = parse(line)
        if m and m.get("type") == "request_rejected":
            rep.add("requests: the server answers (probe rejected as expected)", True)
            rep.set_detail("requests: the server answers (probe rejected as expected)",
                           f"reason: {m.get('reason', '')[:90]}")
            return
    rep.add("requests: the server answers (probe rejected as expected)", False,
            f"no request_rejected within {timeout:.0f} s")


def cmd_check(args):
    channels = CHANNELS if args.channel == "all" else (args.channel,)
    verdicts = [run_check(target_for(args, ch), ch, args.frames, args.timeout, args.team) for ch in channels]
    return 1 if "FAIL" in verdicts else 0


def cmd_watch(args):
    target = target_for(args, args.channel)
    c = Conn.open(target, args.timeout)
    print(f"watching {target} (Ctrl+C to stop). Flap angle = 90 x fraction; sada_angle_deg is not shown (DO NOT USE).")
    try:
        while True:
            line = c.recv(args.timeout)
            if line is None:
                print(f"  ... nothing for {args.timeout:.0f} s")
                continue
            m = parse(line)
            if not m:
                print(f"  bad line: {line[:80]!r}")
                continue
            if m.get("type") == "hello":
                print(f"hello: {m.get('source')} channel {m.get('channel', 'state')} schema {m.get('schema')}")
                continue
            if m.get("type") != "state":
                print(f"  {m}")
                continue
            q, pos, eb = get(m, "attitude.q_body_to_eci"), get(m, "orbit.pos_eci_km"), [0, 0, 1]
            nadir = angle_deg(rotate(q, eb), [-x for x in pos]) if is_vec(q, 4) and is_vec(pos) else float("nan")
            wp, wm = get(m, "deploy.wing_py") or {}, get(m, "deploy.wing_my") or {}
            out = (f"{m.get('seq', '?'):>6} {str(m.get('sim_time', ''))[11:19]} "
                   f"alt {get(m, 'orbit.alt_km', 0):6.1f} km  {get(m, 'attitude.aocs_mode', '?'):<10} "
                   f"imager {nadir:5.1f} deg off nadir  "
                   f"{'ECLIPSE' if get(m, 'sun.in_eclipse') else 'sun    '}  "
                   f"flaps +Y {flap_deg(wp.get('fraction')):3.0f} -Y {flap_deg(wm.get('fraction')):3.0f} deg  "
                   f"antenna {get(m, 'deploy.antenna.state', '?')}")
            p = m.get("power")
            if isinstance(p, dict):
                w = p.get("wings") or {}
                out += (f"  | gen {p.get('generated_w', 0):5.1f} W  use {p.get('consumed_w', 0):5.1f} W  "
                        f"flaps {get(w, 'wing_py.power_w', 0):4.1f}/{get(w, 'wing_my.power_w', 0):4.1f} W  "
                        f"battery {get(p, 'battery.soc_pct', 0):4.1f} %")
            print(out)
    except KeyboardInterrupt:
        print()
    finally:
        c.close()
    return 0


def run_request(target, name, team, text="", wait=120.0, timeout=10.0, quiet=False):
    """Send one request on channel 3 and follow it to SENT, DECLINED or EXPIRED."""
    say = (lambda *a: None) if quiet else print
    c = Conn.open(target, timeout)
    try:
        hello = parse(c.recv(timeout) or "")
        if not hello or hello.get("channel") != "requests":
            say(f"FAIL: {target} is not the request channel (hello {hello!r:.120})")
            return None
        c.send(json.dumps({"type": "request", "request": name, "team": team, "text": text}))
        say(f"sent {name} as team {team!r}; waiting up to {wait:.0f} s for the flight director (Ctrl+C withdraws)")
        end, rid = time.monotonic() + wait, None
        try:
            while time.monotonic() < end:
                m = parse(c.recv(max(0.1, end - time.monotonic())) or "")
                if not m:
                    continue
                kind = m.get("type")
                if kind == "request_rejected":
                    say(f"REJECTED: {m.get('reason')}")
                    return "REJECTED"
                if kind == "request_ack":
                    rid = m.get("id")
                    say(f"{rid}: {m.get('state')}" + (" (you already had this request open)" if m.get("duplicate") else ""))
                elif kind == "request_update" and m.get("id") == rid:
                    extra = (f", command sequence {m.get('tc_seq')}" if m.get("tc_seq") is not None else "") + \
                            (f", note: {m.get('note')}" if m.get("note") else "")
                    say(f"{rid}: {m.get('state')}{extra}")
                    if m.get("state") in ("SENT", "DECLINED", "EXPIRED", "WITHDRAWN"):
                        if m.get("state") == "SENT":
                            say("Now watch channel 1 or 2: the deploy fields show whether it actually deployed.")
                        return m.get("state")
        except KeyboardInterrupt:
            if rid:
                c.send(json.dumps({"type": "withdraw", "id": rid}))
                say(f"withdrew {rid}")
            return "WITHDRAWN"
        say(f"no decision within {wait:.0f} s (the request stays open for 15 minutes on the server)")
        return "WAITING"
    finally:
        c.close()


def cmd_request(args):
    if args.name not in REQUESTS:
        print(f"unknown request {args.name!r}: one of {', '.join(REQUESTS)}")
        return 2
    state = run_request(target_for(args, "requests"), args.name, args.team, args.text, args.wait, args.timeout)
    return 0 if state in ("SENT", "DECLINED") else 1


def check_file(path, quiet=False):
    """Check a .ndjson file (a sample or a recording) and list the events in it."""
    rep = Report(f"vr_test file: {path}")
    events, prev, fc, channel = [], {}, None, None
    with open(path, encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f if ln.strip()]
    rep.add("file has lines", bool(lines), "empty")
    kinds = {}
    for i, line in enumerate(lines):
        m = parse(line)
        rep.add("every line is a JSON object", m is not None, f"line {i + 1}: {line[:60]!r}")
        if m is None:
            continue
        if "message" in m and "from" in m:          # a channel-3 transcript line: {t_s, from, message}
            m = m["message"] if isinstance(m["message"], dict) else {}
            check_request_message(rep, m)
        kinds[m.get("type")] = kinds.get(m.get("type"), 0) + 1
        if m.get("type") == "hello":
            channel = check_hello(rep, m)
            continue
        if m.get("type") in ("request", "request_ack", "request_update", "request_rejected", "withdraw", "list"):
            channel = channel or "requests"
            continue
        if m.get("type") != "state":
            continue
        if fc is None:
            fc = FrameChecker(rep, channel or ("power" if "power" in m else "state"))
        fc.frame(m)
        t = m.get("met_s")
        now = {"aocs_mode": get(m, "attitude.aocs_mode"), "eclipse": get(m, "sun.in_eclipse"),
               "+Y flap": get(m, "deploy.wing_py.state"), "-Y flap": get(m, "deploy.wing_my.state"),
               "antenna": get(m, "deploy.antenna.state"), "phase": get(m, "mission.phase"),
               "contact": get(m, "mission.in_contact")}
        for k, v in now.items():
            if k in prev and prev[k] != v:
                events.append((t, k, prev[k], v))
        prev = now
    if fc:
        fc.finish()
    verdict = rep if quiet else rep.print()
    if not quiet:
        print("Message types: " + ", ".join(f"{k} x{v}" for k, v in kinds.items()))
        if events:
            print("Events (mission elapsed time, s):")
            for t, k, a, b in events:
                print(f"  {t:8.0f}  {k}: {a} -> {b}")
    return verdict


def check_request_message(rep, m):
    """One channel-3 message, either direction (ICD section 7a)."""
    kind = m.get("type")
    known = ("hello", "request", "request_ack", "request_update", "request_rejected", "withdraw", "list", "status")
    rep.add("requests: message types are known", kind in known, f"{kind!r}", "WARN")
    if kind == "request":
        rep.add("requests: a request names what it asks for", isinstance(m.get("request"), str), f"{m!r:.100}")
    if kind in ("request_ack", "request_update"):
        rep.add("requests: acks and updates carry an id and a state",
                isinstance(m.get("id"), str) and m.get("state") in
                ("PENDING", "SENT", "DECLINED", "EXPIRED", "WITHDRAWN"), f"{m!r:.100}")
    if kind == "request_rejected":
        rep.add("requests: a rejection says why", isinstance(m.get("reason"), str), f"{m!r:.100}")


def cmd_file(args):
    verdicts = [check_file(p) for p in args.paths]
    return 1 if "FAIL" in verdicts else 0


def free_ports(n):
    socks = []
    for _ in range(n):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        socks.append(s)
    ports = [s.getsockname()[1] for s in socks]
    for s in socks:
        s.close()
    return ports


def cmd_selftest(args):
    """Start vr_stub.py on free ports and check every channel, both transports, a request round trip
    and the sample files. Proves the kit works on this machine before you test your headset."""
    here = os.path.dirname(os.path.abspath(__file__))
    stub = os.path.join(here, "vr_stub.py")
    if not os.path.exists(stub):
        print(f"vr_stub.py not found next to this file ({here})")
        return 2
    p = free_ports(6)
    logdir = tempfile.mkdtemp(prefix="vr_test_")
    cmd = [sys.executable, stub, "--host", "127.0.0.1", "--port", str(p[0]), "--ws-port", str(p[1]),
           "--power-port", str(p[2]), "--power-ws-port", str(p[3]), "--request-port", str(p[4]),
           "--request-ws-port", str(p[5]), "--speed", "20", "--rate", "5", "--story", "once",
           "--decide-after", "1", "--log-dir", logdir]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    summary = []
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            try:
                socket.create_connection(("127.0.0.1", p[5]), timeout=0.5).close()
                break
            except OSError:
                time.sleep(0.2)
        plan = [("state", f"tcp://127.0.0.1:{p[0]}"), ("state", f"ws://127.0.0.1:{p[1]}/vr"),
                ("power", f"tcp://127.0.0.1:{p[2]}"), ("power", f"ws://127.0.0.1:{p[3]}/vr"),
                ("requests", f"tcp://127.0.0.1:{p[4]}"), ("requests", f"ws://127.0.0.1:{p[5]}/vr/requests")]
        for ch, url in plan:
            v = run_check(url, ch, frames=args.frames, timeout=10, team="selftest")
            summary.append((f"check {ch} over {url.split(':')[0]}", v))
        st = run_request(f"ws://127.0.0.1:{p[5]}/vr/requests", "deploy_antenna", "selftest",
                         "selftest", wait=15, quiet=True)
        summary.append(("request deploy_antenna -> SENT", "PASS" if st == "SENT" else "FAIL"))
        print(f"vr_test request: deploy_antenna -> {st}\n")
        for name in ("sample_vr_frames.ndjson", "sample_vr_power.ndjson", "sample_vr_requests.ndjson"):
            path = os.path.join(here, name)
            if os.path.exists(path):
                rep = check_file(path, quiet=True)
                v = rep.print()
                summary.append((f"file {name}", v))
    finally:
        proc.terminate()
        try:
            proc.wait(5)
        except subprocess.TimeoutExpired:
            proc.kill()
    print("SELFTEST")
    for name, v in summary:
        print(f"  {tag(v)}  {name}")
    bad = [n for n, v in summary if v == "FAIL"]
    print(f"RESULT: {tag('FAIL' if bad else 'PASS')}")
    return 1 if bad else 0


def build_parser():
    ap = argparse.ArgumentParser(description="Check the EOSAT-1 VR interface (smo-vr/1): a live server, "
                                             "a channel-3 request, or a recorded file.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def where(p, channels=("state", "power", "requests")):
        p.add_argument("--channel", choices=channels, default=channels[0],
                       help="which channel (default %(default)s)")
        p.add_argument("--host", default="127.0.0.1", help="server address (default this machine)")
        p.add_argument("--port", type=int, help="override the channel's usual port")
        p.add_argument("--ws", action="store_true", help="use the WebSocket port instead of TCP")
        p.add_argument("--cloud", action="store_true", help="use wss://ops.c2o.live (no sign-in)")
        p.add_argument("--url", help="a full address: tcp://host:port, ws://host:port/vr or wss://...")
        p.add_argument("--timeout", type=float, default=15.0, help="seconds of silence before giving up")

    p = sub.add_parser("check", help="connect and check the hello and some frames")
    where(p, ("state", "power", "requests", "all"))
    p.add_argument("--frames", type=int, default=10, help="frames to check (default %(default)s)")
    p.add_argument("--team", help="also send a status line per frame under this team name")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("watch", help="print one readable line per frame")
    where(p, ("state", "power"))
    p.set_defaults(func=cmd_watch)

    p = sub.add_parser("request", help="ask the flight director for a deployment and follow the answer")
    p.add_argument("name", help="one of " + ", ".join(REQUESTS))
    p.add_argument("--team", required=True, help="your team name, shown to the flight director")
    p.add_argument("--text", default="", help="why you are asking (shown to the flight director)")
    p.add_argument("--wait", type=float, default=120.0, help="seconds to wait for a decision")
    where(p, ("requests",))
    p.set_defaults(func=cmd_request)

    p = sub.add_parser("file", help="check .ndjson files (samples or recordings) and list their events")
    p.add_argument("paths", nargs="+")
    p.set_defaults(func=cmd_file)

    p = sub.add_parser("selftest", help="start vr_stub.py and check all three channels against it")
    p.add_argument("--frames", type=int, default=8)
    p.set_defaults(func=cmd_selftest)
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
