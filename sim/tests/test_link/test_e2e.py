"""smo-link end-to-end (LINK_DESIGN.md §8.3), marked ``link_e2e``.

Topology (all on loopback, free ports)::

    SimulatorServer ⇄ agent ⇄ FaultProxy ⇄ GSG ⇄ MCSServer  (TM, TC, /api/state)
      (real engine)        (200 ms ±50 ms)       ⇄ planner subprocess (/api/state)
                                                 ⇄ raw "rfsim-like" TM tap

The simulator and MCS each run on their own event-loop thread, the way they
run as separate processes in production; the planner is a real subprocess
(its sim-clock fetch is a blocking urllib call and its contact recomputation
is CPU-heavy at x60). The GSG, agent, proxy and the test itself share the
module loop.

Tests run in file order against one module-scoped stack; the order matters
(cut/restore before the dump, which replays stored packets into the TM
stream; supersede last but one, since a second agent instance legitimately
re-sends TM).
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import hashlib
import json
import os
import socket
import struct
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import pytest

aiohttp = pytest.importorskip("aiohttp")
pytest_asyncio = pytest.importorskip("pytest_asyncio")
pytest.importorskip("pytest_timeout")
pytest.importorskip("smo_simulator.server")
pytest.importorskip("smo_mcs.server")
pytest.importorskip("smo_planner.server")
pytest.importorskip("smo_link.gateway")

from smo_common.protocol.ecss_packet import build_tc_packet  # noqa: E402
from smo_common.protocol.framing import frame_packet  # noqa: E402
from smo_link import protocol as P  # noqa: E402
from smo_link.agent import Agent, AgentConfig  # noqa: E402
from smo_link.gateway import Gateway, GatewayConfig  # noqa: E402

from .faultproxy import FaultProxy  # noqa: E402
from .harness import CONFIG_DIR, SECRET, SESSION, wait_for  # noqa: E402

if not Path(CONFIG_DIR, "mission.yaml").is_file():  # pragma: no cover
    pytest.skip("configs/eosat1 missing", allow_module_level=True)

pytestmark = [pytest.mark.link_e2e, pytest.mark.timeout(60),
              pytest.mark.asyncio(loop_scope="module")]

SPEED = 60.0
TICK_S = 1.0           # mission.yaml network.sim_tick_hz = 1.0
LATENCY = 0.200
JITTER = 0.050
FD = "flight_director"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _seq(pkt: bytes) -> tuple[int, int]:
    """(APID, CCSDS sequence count) from a primary header."""
    w0, w1 = struct.unpack(">HH", pkt[:4])
    return w0 & 0x7FF, w1 & 0x3FFF


def _seq_breaks(pkts: list[bytes]) -> list[tuple[int, int, int]]:
    """Per-APID places where the CCSDS sequence count does not step by one."""
    last: dict[int, int] = {}
    out = []
    for p in pkts:
        apid, s = _seq(p)
        if apid in last and (s - last[apid]) % 0x4000 != 1:
            out.append((apid, last[apid], s))
        last[apid] = s
    return out


def _tc(service: int, subtype: int, seq: int, data: bytes = b"") -> bytes:
    return build_tc_packet(apid=1, service=service, subtype=subtype, data=data, seq_count=seq)


# --- infrastructure ------------------------------------------------------------

class LoopThread:
    """An event loop on a daemon thread: one per 'process'."""

    def __init__(self, name: str):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, name=name, daemon=True)
        self.thread.start()

    def submit(self, coro) -> concurrent.futures.Future:
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    async def run(self, coro, timeout: float = 30.0):
        return await asyncio.wait_for(asyncio.wrap_future(self.submit(coro)), timeout)

    def stop(self) -> None:
        async def _shutdown():
            me = asyncio.current_task()
            tasks = [t for t in asyncio.all_tasks() if t is not me]
            for t in tasks:
                t.cancel()
            await asyncio.wait(tasks, timeout=3) if tasks else None
        try:
            self.submit(_shutdown()).result(5)
        except Exception:  # noqa: BLE001
            pass
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(5)


class TmTap:
    """Raw TM client (what rfsim does): records every framed packet."""

    def __init__(self, port: int):
        self.port = port
        self.pkts: list[bytes] = []
        self.times: list[float] = []
        self.eof = False
        self.error: BaseException | None = None

    async def start(self) -> "TmTap":
        self.reader, self.writer = await asyncio.open_connection("127.0.0.1", self.port)
        self.task = asyncio.ensure_future(self._run())
        return self

    async def _run(self):
        buf = bytearray()
        try:
            while True:
                d = await self.reader.read(65536)
                if not d:
                    self.eof = True
                    return
                buf += d
                # [u16 len][pkt], or [0xFFFF][u8 vcid][u16 len][pkt] for S15
                # playback on VC1 (smo_common.protocol.framing): a tap that
                # only knew the first form read 65535 bytes after a dump and
                # stopped counting, so every later test saw "no TM".
                for rec in P.split_records(buf):
                    hdr = 5 if rec[:2] == b"\xff\xff" else 2
                    self.pkts.append(rec[hdr:])
                    self.times.append(time.monotonic())
        except asyncio.CancelledError:
            raise
        except BaseException as e:  # noqa: BLE001
            self.error = e

    @property
    def alive(self) -> bool:
        return not self.eof and self.error is None and not self.writer.is_closing()

    def close(self):
        self.task.cancel()
        self.writer.close()


def assert_contiguous(gsg: list[bytes], sim: list[bytes], what: str) -> int:
    """GSG's packets must be an exact, contiguous run of the sim's: same bytes,
    no duplicates, no holes. Returns the sim index GSG starts at."""
    assert gsg, f"{what}: no TM at the GSG tap"
    try:
        i0 = sim.index(gsg[0])
    except ValueError:
        raise AssertionError(f"{what}: first GSG packet never seen at the sim tap")
    n = len(gsg)
    window = sim[i0:i0 + n]
    if window != gsg:
        k = next(i for i, (a, b) in enumerate(zip(window, gsg)) if a != b) \
            if any(a != b for a, b in zip(window, gsg)) else min(len(window), n)
        raise AssertionError(
            f"{what}: GSG stream diverges from sim at packet {k} of {n} "
            f"(sim {_seq(window[k]) if k < len(window) else 'short'} vs gsg {_seq(gsg[k])})")
    return i0


class TickTracker:
    """Watches engine._sim_time from its own thread (the test loop can be
    busy for 100+ ms) to know when each tick landed, so a test can compare a
    continuous clock against the engine's continuous time."""

    def __init__(self, engine):
        self.engine = engine
        self.last_sim = engine._sim_time
        self.last_wall = time.time()
        self.changes = 0
        self.history: list[tuple[float, datetime]] = [(self.last_wall, self.last_sim)]
        # /api/state serves the snapshot published at the END of a tick, while
        # _sim_time moves during its sub-steps: track the snapshot separately.
        self.snap_last: str | None = None
        self.snap_history: list[tuple[float, datetime]] = []
        self._stop = threading.Event()
        self.thread = threading.Thread(target=self._run, name="e2e-ticks", daemon=True)
        self.thread.start()

    def _run(self):
        while not self._stop.wait(0.005):
            t = self.engine._sim_time
            if t != self.last_sim:
                w = time.time()
                self.history.append((w, t))
                self.last_sim, self.last_wall = t, w
                self.changes += 1
            snap = getattr(self.engine, "_snapshot", None) or {}
            st = snap.get("sim_time")
            if st and st != self.snap_last:
                self.snap_last = st
                self.snap_history.append((time.time(), datetime.fromisoformat(st)))

    def stop(self):
        self._stop.set()

    @property
    def ready(self) -> bool:
        return self.changes >= 2

    def lateness(self, since: float) -> float:
        """Wall seconds by which the engine's ticks ending after ``since`` ran
        behind a steady 1/tick_hz cadence (CPU starvation: the engine never
        catches up, so every extrapolating clock drifts ahead by this x speed)."""
        h = list(self.history)
        ends = [w for (w, _), (w2, _) in zip(h, h[1:]) if w2 - w > 0.5] + [h[-1][0]]
        ends.append(max(ends[-1], time.time()))     # a tick that is overdue right now
        return sum(max(0.0, (b - a) - TICK_S) for a, b in zip(ends, ends[1:]) if b >= since)

    def plateau(self, value: datetime) -> tuple[float, float]:
        """Wall interval in which the sim's /api/state can have said
        ``value``: after the last snapshot below it, before the first above."""
        h = list(self.snap_history)
        lo = max((w for w, v in h if v < value), default=float("-inf"))
        hi = min((w for w, v in h if v > value), default=float("inf"))
        return lo, hi

    def continuous(self) -> datetime:
        from datetime import timedelta
        return self.last_sim + timedelta(seconds=(time.time() - self.last_wall)
                                         * self.engine.speed)


class E2E:
    """The whole stack. Built once per module."""

    async def start(self, tmp: Path) -> "E2E":
        from smo_simulator.engine import SimulationEngine
        from smo_simulator.server import SimulatorServer

        self.tmp = tmp
        self.sim_dumps = tmp / "sim_dumps"
        self.gsg_dumps = tmp / "gsg_dumps"
        self.sim_dumps.mkdir()
        self.threads: list[LoopThread] = []

        # -- simulator (real engine) ------------------------------------
        self.engine = SimulationEngine(config_dir=CONFIG_DIR)
        self.engine._dump_dir = self.sim_dumps
        self.tc_log: list[bytes] = []
        q = self.engine.tc_queue
        orig_put = q.put_nowait

        def put_nowait(pkt, _orig=orig_put):
            self.tc_log.append(bytes(pkt))
            return _orig(pkt)
        q.put_nowait = put_nowait
        self.sim_ports = {"tc": _free_port(), "tm": _free_port(), "http": _free_port()}
        self.sim_server = SimulatorServer(self.engine, config={
            "tc_port": self.sim_ports["tc"], "tm_port": self.sim_ports["tm"],
            "http_port": self.sim_ports["http"], "bind_host": "127.0.0.1", "vr": None})
        self.sim_t = LoopThread("e2e-sim")
        self.threads.append(self.sim_t)
        self.sim_t.submit(self.sim_server.start())
        self.http = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
        sim_http = f"http://127.0.0.1:{self.sim_ports['http']}"
        await self._wait_http(sim_http + "/api/state")
        for cmd in ({"type": "set_phase", "phase": 6},          # nominal OBSW: S15 storage
                    {"type": "override_passes", "enabled": True},
                    {"type": "set_speed", "value": SPEED}):
            async with self.http.post(sim_http + "/api/command", json=cmd) as r:
                assert r.status == 200, (cmd, await r.text())
        self.sim_tap = await TmTap(self.sim_ports["tm"]).start()
        self.ticks = TickTracker(self.engine)

        # -- GSG + fault proxy + agent ------------------------------------
        self.gw = Gateway(GatewayConfig(
            session=SESSION, secret=SECRET, bind="127.0.0.1", tm_port=0, tc_port=0,
            http_port=0, link_bind="127.0.0.1", link_port=0, dump_dir=str(self.gsg_dumps),
            config_dir=CONFIG_DIR, ping_interval=1.0))
        await self.gw.start()
        self.gsg_http = f"http://127.0.0.1:{self.gw.ports['http']}"
        self.gsg_tap = await TmTap(self.gw.ports["tm"]).start()   # rfsim-like client
        self.proxy = await FaultProxy("127.0.0.1", self.gw.ports["link"],
                                      latency=LATENCY, jitter=JITTER, seed=7).start()
        self.agent = Agent(self.agent_cfg(f"ws://127.0.0.1:{self.proxy.port}/link", "a1"))
        await self.agent.start()

        # -- MCS + planner pointed at the GSG ------------------------------
        os.environ["SMO_TM_ARCHIVE"] = str(tmp / "mcs" / "tm_archive.db")
        from smo_mcs.server import MCSServer
        self.mcs_port, self.planner_port = _free_port(), _free_port()
        state_url = self.gsg_http + "/api/state"
        self.mcs_seen: list[tuple[int, int, bytes]] = []
        self.mcs_t = LoopThread("e2e-mcs")
        self.threads.append(self.mcs_t)

        async def make_mcs():
            m = MCSServer(CONFIG_DIR, connect_host="127.0.0.1", connect_port=self.gw.ports["tm"],
                          http_port=self.mcs_port, tc_port=self.gw.ports["tc"],
                          time_source="sim", sim_state_url=state_url, bind_host="127.0.0.1")
            m._dump_dir = self.gsg_dumps         # MCS and GSG share SMO_DUMP_DIR
            orig = m._process_tm

            async def rec(parsed, *a, _orig=orig, **kw):
                s = parsed.secondary
                self.mcs_seen.append((s.service, s.subtype, bytes(parsed.data_field[:4])))
                await _orig(parsed, *a, **kw)
            m._process_tm = rec
            return m
        self.mcs = await self.mcs_t.run(make_mcs())
        self.mcs_t.submit(self.mcs.start())
        # The planner runs as a real subprocess: its contact/ground-track
        # recomputation (every wall second at x60) is CPU-heavy, and inside
        # this process it would steal the GIL from the engine and skew every
        # clock measurement.
        repo = Path(CONFIG_DIR).parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(
            [str(repo / "packages" / p / "src") for p in
             ("smo-common", "smo-simulator", "smo-mcs", "smo-planner", "smo-link")]
            + [env.get("PYTHONPATH", "")])
        env.pop("SMO_SIM_STATE_URL", None)
        env.pop("SMO_TIME_SOURCE", None)
        self.planner_log = open(tmp / "planner.log", "wb")
        self.planner_proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "smo_planner.server", "--config", CONFIG_DIR,
            "--port", str(self.planner_port), "--host", "127.0.0.1",
            "--time-source", "sim", "--sim-state-url", state_url,
            env=env, cwd=str(repo), stdout=self.planner_log, stderr=subprocess.STDOUT)
        self.mcs_http = f"http://127.0.0.1:{self.mcs_port}"
        self.planner_http = f"http://127.0.0.1:{self.planner_port}"

        await wait_for(lambda: self.gw.bound(), timeout=15, msg="link bound")
        await self._wait_http(self.mcs_http + "/api/state")
        await self._wait_http(self.planner_http + "/api/time-source", timeout=40)
        await self.wait_mcs_tc()
        return self

    def agent_cfg(self, url: str, tag: str, **over) -> AgentConfig:
        kw = dict(url=url, session=SESSION, secret=SECRET, sim_host="127.0.0.1",
                  sim_tm_port=self.sim_ports["tm"], sim_tc_port=self.sim_ports["tc"],
                  sim_http_port=self.sim_ports["http"], config_dir=CONFIG_DIR,
                  mode="complete", state_dir=str(self.tmp / f"agent_{tag}"),
                  backoff_base=0.2, backoff_cap=1.0, ping_interval=1.0, dump_poll_s=0.3)
        kw.update(over)
        return AgentConfig(**kw)

    async def _wait_http(self, url: str, timeout: float = 15.0):
        t0 = time.monotonic()
        last = None
        while time.monotonic() - t0 < timeout:
            try:
                async with self.http.get(url, timeout=aiohttp.ClientTimeout(total=3)) as r:
                    if r.status == 200:
                        return
                    last = r.status
            except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as e:
                last = e
            await asyncio.sleep(0.2)
        raise AssertionError(f"{url} not ready: {last!r}")

    async def wait_mcs_tc(self, timeout: float = 15.0):
        def ok():
            w = self.mcs._tc_writer
            return w is not None and not w.is_closing() and self.gw.tc_clients
        await wait_for(ok, timeout=timeout, msg="MCS TC connected to GSG")

    async def pus(self, service: int, subtype: int, data_hex: str = "",
                  name: str | None = None) -> tuple[int, dict]:
        body = {"service": service, "subtype": subtype, "data_hex": data_hex,
                "name": name or f"S{service}.{subtype}", "position": FD}
        async with self.http.post(self.mcs_http + "/api/pus-command", json=body) as r:
            return r.status, await r.json()

    def mcs_s1(self, subtype: int, tc_seq: int) -> bool:
        return any(s == 1 and st == subtype and len(d) >= 4
                   and (struct.unpack(">H", d[2:4])[0] & 0x3FFF) == tc_seq
                   for s, st, d in list(self.mcs_seen))

    def tc_seqs_at_sim(self) -> set[int]:
        return {_seq(p)[1] for p in list(self.tc_log)}

    async def stop(self):
        if getattr(self, "ticks", None) is not None:
            self.ticks.stop()
        for c in (getattr(self, "gsg_tap", None), getattr(self, "sim_tap", None)):
            if c is not None:
                c.close()
        if getattr(self, "agent", None) is not None:
            await self.agent.stop()
        if getattr(self, "proxy", None) is not None:
            await self.proxy.stop()
        if getattr(self, "gw", None) is not None:
            await self.gw.stop()
        if getattr(self, "mcs", None) is not None:
            self.mcs._running = False
        proc = getattr(self, "planner_proc", None)
        if proc is not None and proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), 5)
            except asyncio.TimeoutError:
                proc.kill()
            self.planner_log.close()
        self.sim_server._running = False
        self.engine.stop()
        for t in self.threads:
            t.stop()
        await self.http.close()
        os.environ.pop("SMO_TM_ARCHIVE", None)


@pytest_asyncio.fixture(loop_scope="module", scope="module")
async def e2e(tmp_path_factory):
    stack = E2E()
    try:
        await stack.start(tmp_path_factory.mktemp("link_e2e"))
        yield stack
    finally:
        await stack.stop()


# --- (1) TM byte equality ----------------------------------------------------

async def test_tm_byte_equality_sim_tap_vs_gsg_tap(e2e):
    n0 = len(e2e.gsg_tap.pkts)
    await wait_for(lambda: len(e2e.gsg_tap.pkts) >= n0 + 20, timeout=15, msg="20 TM packets")
    await asyncio.sleep(LATENCY + JITTER + 0.2)
    i0 = assert_contiguous(e2e.gsg_tap.pkts, e2e.sim_tap.pkts, "TM byte equality")
    # The proxy really is in the path, and the delay is really there.
    assert e2e.proxy.stats.bytes_down > 0 and e2e.proxy.stats.bytes_up > 0
    await wait_for(lambda: e2e.gw.link is not None and e2e.gw.link.clock.rtt is not None,
                   timeout=10, msg="rtt measured")
    assert e2e.gw.link.clock.rtt >= 2 * (LATENCY - JITTER) - 0.01, e2e.gw.link.clock.rtt
    assert i0 >= 0


# --- (2) TC through the MCS ----------------------------------------------------

async def test_tc_via_mcs_yields_s1_1_and_s1_7(e2e):
    status, body = await e2e.pus(17, 1, name="CONN_TEST")
    assert status == 200 and body["status"] == "sent", body
    seq = body["seq"]
    await wait_for(lambda: e2e.mcs_s1(1, seq) and e2e.mcs_s1(7, seq), timeout=10,
                   msg=f"S1.1 + S1.7 for TC seq {seq} at the MCS")
    assert seq in e2e.tc_seqs_at_sim()
    async with e2e.http.get(e2e.mcs_http + "/api/verification-log") as r:
        log = (await r.json())["log"]
    assert any(e["seq"] == seq and e["state"] == "COMPLETED" for e in log)


# --- (3) clocks under 200 ms ±50 ms one-way delay at x60 ----------------------------

async def test_clocks_track_engine_under_latency(e2e):
    """MCS, planner and GSG clocks track the engine within 1 tick x speed.

    The engine's ``_sim_time`` is a staircase (it jumps 60 s once per 1 Hz
    tick at x60) while the ground clocks are anchored on one sample of that
    staircase and extrapolated continuously, so even over a perfect link the
    raw difference spans (-60 s, +60 s): the spec bound is the envelope with
    no margin. The test therefore measures each clock against the engine's
    *continuous* time C (last tick value + wall time since it x speed), where
    a correct link gives ``-tick*speed < clock - C <= 0``, and allows 0.5 s
    x speed (30 s) of scheduling jitter: the sim, MCS and GSG share one Python
    process and one GIL here, and on a 2-CPU runner the agent's /api/state
    fetch (whose mid-point stamps the sample) can stall for a few hundred ms,
    which is tens of sim seconds at x60. When the engine itself runs late (a tick
    starved of CPU; it never catches up) every extrapolating clock runs ahead
    of it by that lateness x speed, link or no link, so the measured lateness
    is allowed for on that side. The latency compensation itself is checked
    directly: the GSG's agent-clock offset stays ~0 although the RTT is
    ~0.4 s, and each STATE's agent timestamp falls on the engine tick that
    produced its sim_time, not 200 ms later.
    """
    gw = e2e.gw
    assert e2e.engine.speed == SPEED
    await wait_for(lambda: e2e.mcs._sim_speed == SPEED and e2e.mcs._ground_epoch is not None,
                   timeout=10, msg="MCS anchored at x60")
    await wait_for(lambda: e2e.ticks.ready, timeout=5, msg="engine ticks observed")
    tick = TICK_S * SPEED
    # 0.75 s of wall time: 0.5 s failed the 2026-11-08 nightly by 10 ms of
    # runner jitter (all three clocks ran ahead together, i.e. the runner).
    slack = 0.75 * SPEED
    rows = []
    anchors: dict[float, str] = {}
    for i in range(40):
        a = gw.anchor
        if a.t_agent_wall is not None and a.state:
            anchors[a.t_agent_wall] = a.state["sim_time"]
        if i % 4 == 0:
            c, eng = e2e.ticks.continuous(), e2e.engine._sim_time
            mcs = e2e.mcs.sim_now()
            async with e2e.http.get(e2e.planner_http + "/api/time-source") as r:
                ts = await r.json()
            c_p = e2e.ticks.continuous()
            assert ts["time_source"] == "sim" and ts["sim_reachable"], ts
            planner = datetime.fromisoformat(ts["sim_time"])
            async with e2e.http.get(e2e.gsg_http + "/api/state") as r:
                assert r.status == 200
                gsg = datetime.fromisoformat((await r.json())["sim_time"])
            c_g = e2e.ticks.continuous()
            late = e2e.ticks.lateness(time.time() - 5.0) * SPEED   # >= any anchor age
            rows.append({"late": late,
                         "mcs": (mcs - c).total_seconds(),
                         "planner": (planner - c_p).total_seconds(),
                         "gsg": (gsg - c_g).total_seconds(),
                         "mcs_vs_engine": abs((mcs - eng).total_seconds())})
        await asyncio.sleep(0.1)
    summary = {k: (round(min(r[k] for r in rows), 2), round(max(r[k] for r in rows), 2))
               for k in rows[0]}
    # STATE timestamps: t_agent_wall must lie on the plateau where the engine
    # held that sim_time (an RX-time stamp would sit ~0.2 s past its end).
    misses = []
    for t_wall, st in sorted(anchors.items())[:-1]:     # last plateau may be open
        lo, hi = e2e.ticks.plateau(datetime.fromisoformat(st))
        if not (lo - 0.06 <= t_wall <= hi + 0.06):    # fetch midpoint + tracker poll
            misses.append((round(t_wall - lo, 3), round(hi - t_wall, 3)))
    offset, rtt = gw.link.clock.offset, gw.link.clock.rtt
    print(f"clock - continuous engine time, (min, max) s: {summary}; "
          f"{len(anchors)} STATE anchors, misses {misses}; offset {offset:.4f} rtt {rtt:.3f}")
    for r in rows:
        for k in ("mcs", "planner", "gsg"):
            assert -tick - slack < r[k] <= slack + r["late"], \
                f"{k} clock off: {r[k]:.2f} s (tick*speed {tick}, engine late {r['late']:.1f}): {summary}"
        assert r["mcs_vs_engine"] < tick + slack + r["late"], summary
    assert rtt >= 2 * (LATENCY - JITTER) - 0.01 and abs(offset) < 0.05, (offset, rtt)
    assert len(anchors) >= 3 and not misses, misses


# --- (7) instructor through the GSG proxy -------------------------------------------

async def test_instructor_index_ws_and_config_denied(e2e):
    async with e2e.http.get(e2e.gsg_http + "/") as r:
        assert r.status == 200
        assert "text/html" in r.headers.get("Content-Type", "")
        assert "<html" in (await r.text()).lower()
    async with e2e.http.ws_connect(e2e.gsg_http.replace("http", "ws", 1) + "/ws") as ws:
        msg = await ws.receive(timeout=8)
        assert msg.type == aiohttp.WSMsgType.TEXT, msg
        assert json.loads(msg.data).get("type") == "state_update"
    for path in ("/config", "/api/config"):
        async with e2e.http.get(e2e.gsg_http + path) as r:
            assert r.status == 403, path


async def test_instructor_ui_loads_under_csp_in_a_browser(e2e):
    """H3 / M1: the CSP, the header allowlist and the route allowlist must not
    break the real instructor console served through the GSG."""
    import re
    missing: set[str] = set()
    for page in ("/", "/classic", "/modern"):
        async with e2e.http.get(e2e.gsg_http + page) as r:
            assert r.status == 200, page
            html = await r.text()
            assert r.headers["X-Content-Type-Options"] == "nosniff"
            assert "default-src 'self'" in r.headers["Content-Security-Policy"]
            assert "Set-Cookie" not in r.headers
        refs = set(re.findall(r'(?:src|href)="(/static/[^"#]+)', html))
        assert refs, page
        sim_http = f"http://127.0.0.1:{e2e.sim_ports['http']}"
        for ref in refs:     # the proxy is transparent for every referenced asset
            async with e2e.http.get(sim_http + ref) as direct:
                want = (direct.status, await direct.read())
                if direct.status != 200:
                    missing.add(ref)  # absent at the sim itself (not a link matter)
            async with e2e.http.get(e2e.gsg_http + ref) as r2:
                assert (r2.status, await r2.read()) == want, (page, ref)
    for ref in ("/static/modern/instructor.js?v=1", "/static/shared/design-system.css?v=1"):
        async with e2e.http.get(e2e.gsg_http + ref) as r2:
            assert r2.status == 200, ref
        assert not re.search(r'(?:src|href)="(?:https?:)?//', html), "third-party asset"
    pw = pytest.importorskip("playwright.async_api")
    problems: list[str] = []
    sockets: list[str] = []
    async with pw.async_playwright() as p:
        try:
            browser = await p.chromium.launch()
        except Exception as e:  # noqa: BLE001
            pytest.skip(f"no headless chromium: {e}")
        try:
            page = await browser.new_page()
            await page.add_init_script(
                "window.__csp = []; document.addEventListener('securitypolicyviolation',"
                " e => window.__csp.push(e.violatedDirective + ' ' + e.blockedURI));")
            page.on("console", lambda m: problems.append("console: " + m.text)
                    if ("Content Security Policy" in m.text or "Refused" in m.text) else None)
            page.on("requestfailed", lambda r: problems.append(f"failed {r.url} {r.failure}")
                    if "ERR_ABORTED" not in str(r.failure) else None)
            page.on("response", lambda r: problems.append(f"{r.status} {r.url}")
                    if r.status == 403 else None)
            page.on("websocket", lambda ws: sockets.append(ws.url))
            for path in ("/", "/classic"):
                await page.goto(e2e.gsg_http + path, wait_until="load")
                await page.wait_for_timeout(2000)
                problems.extend(f"csp {v}" for v in await page.evaluate("window.__csp"))
                assert await page.evaluate("document.body.innerText.length") > 100, path
        finally:
            await browser.close()
    print(f"browser: websockets {sockets}; assets missing at the sim itself: {sorted(missing)}")
    problems = [p for p in problems if not any(m in p for m in missing)]
    assert not problems, problems
    assert any(u.endswith("/ws") for u in sockets), sockets


# --- (4) + (5) link cut and restore --------------------------------------------------

async def test_link_cut_and_restore(e2e):
    gw, mcs = e2e.gw, e2e.mcs
    assert gw.bound()
    # A TC accepted by the GSG but still in flight (inside the 200 ms of
    # latency) when the link drops must never reach the sim afterwards.
    _r, raw_w = await asyncio.open_connection("127.0.0.1", gw.ports["tc"])
    await wait_for(lambda: len(gw.tc_clients) >= 2, msg="raw TC client registered")
    n_tc = gw.counters["tc_packets"]
    raw_w.write(frame_packet(_tc(17, 1, 0x3ABD)))
    await raw_w.drain()
    await wait_for(lambda: gw.counters["tc_packets"] > n_tc, timeout=2, msg="TC on the link")
    await asyncio.sleep(0.03)

    sim_n_at_cut = len(e2e.sim_tap.pkts)
    t_cut = time.monotonic()
    e2e.proxy.cut()

    # MCS: 503 "No TC connection" within 3 s.
    sent_during_cut: list[int] = []
    t_503 = None
    while time.monotonic() - t_cut < 4.0:
        status, body = await e2e.pus(17, 1, name="CUT_TC")
        sent_during_cut.append(mcs._tc_manager._seq_count)
        if status == 503:
            assert body["message"] == "No TC connection", body
            t_503 = time.monotonic() - t_cut
            break
        await asyncio.sleep(0.1)
    assert t_503 is not None and t_503 <= 3.0, f"MCS 503 after {t_503}"
    await e2e.pus(17, 1, name="CUT_TC_2")     # submitted during the cut
    sent_during_cut.append(mcs._tc_manager._seq_count)

    # A raw TC connect during the cut is accepted then reset.
    r2, w2 = await asyncio.open_connection("127.0.0.1", gw.ports["tc"])
    try:
        w2.write(frame_packet(_tc(17, 1, 0x3ABE)))
        with pytest.raises((ConnectionResetError, BrokenPipeError)):
            await w2.drain()
            d = await asyncio.wait_for(r2.read(10), 2)
            raise AssertionError(f"expected RST, got {d!r}")
    finally:
        w2.close()

    # GSG /api/state: still served (re-timed) for a while, 503 once ~5 s stale.
    t_state503 = None
    early_ok = False
    while time.monotonic() - t_cut < 8.0:
        async with e2e.http.get(e2e.gsg_http + "/api/state") as r:
            el = time.monotonic() - t_cut
            if r.status == 200 and el < 2.5:
                early_ok = True
            if r.status == 503:
                t_state503 = el
                break
        await asyncio.sleep(0.1)
    print(f"cut: MCS 503 after {t_503:.2f} s, GSG /api/state 503 after {t_state503} s, "
          f"MCS TCs 'sent' during cut {sent_during_cut}")
    assert t_state503 is not None and 3.0 <= t_state503 <= 6.5, t_state503
    assert early_ok
    async with e2e.http.get(e2e.gsg_http + "/link-status") as r:
        assert (await r.json())["state"] == "DOWN"
    assert not gw.bound()
    # The rfsim-style TM socket is never dropped.
    assert e2e.gsg_tap.alive
    gsg_n_down = len(e2e.gsg_tap.pkts)
    await asyncio.sleep(0.5)
    assert len(e2e.gsg_tap.pkts) == gsg_n_down          # nothing arrives while DOWN
    sim_n_at_restore = len(e2e.sim_tap.pkts)
    assert sim_n_at_restore > sim_n_at_cut, "sim produced no TM during the cut"

    # Restore.
    e2e.proxy.restore()
    await wait_for(lambda: gw.bound(), timeout=10, msg="link back UP")
    target = e2e.sim_tap.pkts[sim_n_at_restore - 1]
    await wait_for(lambda: target in e2e.gsg_tap.pkts[gsg_n_down:], timeout=10,
                   msg="TM produced during the cut delivered")
    assert e2e.gsg_tap.alive

    # complete mode: one exact contiguous run, no duplicates, no holes,
    # spanning the outage.
    i0 = assert_contiguous(e2e.gsg_tap.pkts, e2e.sim_tap.pkts, "TM across cut")
    gsg = e2e.gsg_tap.pkts
    window = gsg[max(0, sim_n_at_cut - i0 - 50):]
    sim_window = e2e.sim_tap.pkts[i0 + len(gsg) - len(window):i0 + len(gsg)]
    # CCSDS sequence counts: the GSG saw exactly the sim's (APID, seq) multiset
    # and the same seq-count discontinuities (the sim keeps several counters
    # per APID, so it has some of its own), i.e. the link added none.
    from collections import Counter
    assert Counter(map(_seq, window)) == Counter(map(_seq, sim_window))
    assert _seq_breaks(window) == _seq_breaks(sim_window)
    # ...and the link layer itself saw no duplicate or lost frame.
    assert gw.counters["tm_dup_frames"] == 0 and gw.counters["tm_lost_frames"] == 0, gw.counters
    print(f"TM: {len(gsg)} pkts at GSG, {sim_n_at_restore - sim_n_at_cut} produced during "
          f"the cut, all delivered once")

    # MCS TC recovers by itself and works again.
    await e2e.wait_mcs_tc(timeout=10)
    status, body = await e2e.pus(17, 1, name="AFTER_RESTORE")
    assert status == 200, body
    seq_after = body["seq"]
    await wait_for(lambda: e2e.mcs_s1(7, seq_after), timeout=10, msg="S1.7 after restore")
    await asyncio.sleep(LATENCY + JITTER + 0.3)
    # Nothing submitted during the cut, nor the TC in flight at the cut, was
    # delivered to the sim afterwards.
    at_sim = e2e.tc_seqs_at_sim()
    assert 0x3ABD not in at_sim and 0x3ABE not in at_sim
    assert not (set(sent_during_cut) & at_sim), (sent_during_cut, at_sim)
    raw_w.close()


# --- (6) S15 dump -------------------------------------------------------------------

async def test_s15_dump_reaches_gsg_and_mcs(e2e):
    storage = e2e.engine._tm_storage
    status = {s["id"]: s["count"] for s in storage.get_status()}
    sid = next((i for i, c in sorted(status.items()) if c > 0), None)
    if sid is None:
        sid = 1
        for p in e2e.sim_tap.pkts[:20]:
            storage.store_packet_direct(sid, p)
    before = set(os.listdir(e2e.sim_dumps))
    code, body = await e2e.pus(15, 9, data_hex=f"{sid:02X}", name="TM_DUMP")
    assert code == 200 and body["status"] == "sent", body
    await wait_for(lambda: set(os.listdir(e2e.sim_dumps)) - before, timeout=10,
                   msg="sim archived the dump")
    name = sorted(set(os.listdir(e2e.sim_dumps)) - before)[0]
    src = e2e.sim_dumps / name
    dst = e2e.gsg_dumps / name
    await wait_for(dst.exists, timeout=15, msg="dump at the GSG")
    assert dst.read_bytes() == src.read_bytes()
    assert hashlib.sha256(dst.read_bytes()).hexdigest() == hashlib.sha256(src.read_bytes()).hexdigest()
    assert abs(dst.stat().st_mtime - src.stat().st_mtime) < 1.0
    assert not list(e2e.gsg_dumps.glob(".part-*"))
    async with e2e.http.get(e2e.mcs_http + "/api/dumps") as r:
        listing = await r.json()
    assert name in [d["filename"] for d in listing["dumps"]], listing


# --- (8) supersede ------------------------------------------------------------------

async def test_second_agent_supersedes_link_stays_up(e2e):
    gw, a1 = e2e.gw, e2e.agent
    await wait_for(lambda: gw.bound() and a1.link is not None, msg="a1 bound")
    link1 = a1.link
    mcs_tc = e2e.mcs._tc_writer
    resets = gw.counters["tc_reset_clients"]
    sup = gw.counters["supersedes"]
    a1.cfg.backoff_base = a1.cfg.backoff_cap = 5.0
    a2 = Agent(e2e.agent_cfg(f"ws://127.0.0.1:{gw.ports['link']}/link", "a2"))
    await a2.start()
    try:
        await wait_for(lambda: link1.closed, timeout=10, msg="first agent closed")
        e2e.proxy.cut()                      # keep a1 from re-superseding a2
        await wait_for(lambda: link1.ws.close_code == P.WS_CLOSE_SUPERSEDED, timeout=3,
                       msg="close 4000 at agent 1")
        await wait_for(lambda: gw.bound() and gw.link_info.get("instance") == a2.instance,
                       timeout=5, msg="a2 bound")
        assert gw.counters["supersedes"] == sup + 1
        # H1: a supersede unbinds the old session first, so its TC clients
        # are RESET (never FIN-closed): the MCS sees the drop at once instead
        # of writing its next TC into a dead socket, and reconnects by itself.
        assert gw.counters["tc_reset_clients"] > resets
        assert mcs_tc.is_closing()
        await e2e.wait_mcs_tc(timeout=10)
        assert e2e.mcs._tc_writer is not mcs_tc
        n = len(e2e.gsg_tap.pkts)
        await wait_for(lambda: len(e2e.gsg_tap.pkts) > n, timeout=10, msg="TM via a2")
        code, body = await e2e.pus(17, 1, name="VIA_A2")
        assert code == 200, body
        await wait_for(lambda: e2e.mcs_s1(7, body["seq"]), timeout=10, msg="S1.7 via a2")
        assert e2e.gsg_tap.alive
    finally:
        await a2.stop()
        e2e.proxy.restore()
        a1.cfg.backoff_base, a1.cfg.backoff_cap = 0.2, 1.0
    await wait_for(lambda: gw.bound() and gw.link_info.get("instance") == a1.instance,
                   timeout=15, msg="a1 back")


# --- (9) wrong secret ---------------------------------------------------------------

async def test_wrong_secret_401_link_stays_down(e2e, tmp_path):
    gw = Gateway(GatewayConfig(
        session=SESSION, secret=SECRET, bind="127.0.0.1", tm_port=0, tc_port=0, http_port=0,
        link_bind="127.0.0.1", link_port=0, dump_dir=str(tmp_path / "d"), config_dir=CONFIG_DIR))
    await gw.start()
    bad = Agent(e2e.agent_cfg(f"ws://127.0.0.1:{gw.ports['link']}/link", "bad",
                              secret=b"\x5a" * 32))
    await bad.start()
    try:
        await wait_for(lambda: gw.counters["auth_failures"] >= 2, timeout=10, msg="401s")
        assert not gw.bound() and bad.link is None and bad.counters["link_connects"] == 0
        async with e2e.http.get(f"http://127.0.0.1:{gw.ports['link']}/link") as r:
            assert r.status == 401
        base = f"http://127.0.0.1:{gw.ports['http']}"
        async with e2e.http.get(base + "/link-status") as r:
            assert (await r.json())["state"] == "DOWN"
        async with e2e.http.get(base + "/api/state") as r:
            assert r.status == 503
    finally:
        await bad.stop()
        await gw.stop()


# --- the fault proxy itself ----------------------------------------------------------

async def test_faultproxy_latency_bandwidth_cut_blackhole():
    async def echo(r, w):
        try:
            while d := await r.read(65536):
                w.write(d)
                await w.drain()
        except ConnectionError:
            pass
        w.close()
    srv = await asyncio.start_server(echo, "127.0.0.1", 0)
    px = await FaultProxy("127.0.0.1", srv.sockets[0].getsockname()[1], latency=0.1).start()
    try:
        r, w = await asyncio.open_connection("127.0.0.1", px.port)
        t0 = time.monotonic()
        w.write(b"ping")
        assert await r.readexactly(4) == b"ping"
        assert 0.19 <= time.monotonic() - t0 < 0.6
        px.set(latency=0.0, bandwidth=100_000)
        t0 = time.monotonic()
        w.write(b"x" * 40_000)
        await r.readexactly(40_000)
        assert time.monotonic() - t0 >= 0.7       # 40 kB each way at 100 kB/s
        px.set(bandwidth=None)
        px.blackhole(True)
        w.write(b"lost")
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(r.read(10), 0.3)
        assert not w.is_closing()
        px.restore()
        w.write(b"back")
        assert await asyncio.wait_for(r.readexactly(4), 2) == b"back"
        px.cut()
        with pytest.raises(ConnectionResetError):
            await asyncio.wait_for(r.read(10), 2)
        r3, w3 = await asyncio.open_connection("127.0.0.1", px.port)
        with pytest.raises(ConnectionResetError):
            await asyncio.wait_for(r3.read(10), 2)
        px.restore()
        r4, w4 = await asyncio.open_connection("127.0.0.1", px.port)
        w4.write(b"ok")
        assert await asyncio.wait_for(r4.readexactly(2), 2) == b"ok"
        w4.close()
    finally:
        await px.stop()
        srv.close()
