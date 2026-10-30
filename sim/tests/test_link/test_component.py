"""smo-link component tests: fake sim sockets/HTTP + in-process GSG + agent."""
from __future__ import annotations

import asyncio
import gzip
import hashlib
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

import aiohttp
import pytest

from smo_link import protocol as P
from smo_link.confighash import STRICT_FILES, WARN_FILES

from .harness import CONFIG_DIR, Stack, record, wait_for

pytestmark = pytest.mark.timeout(60)

DEAD_URL = "ws://127.0.0.1:1/link"   # connection refused: the agent cannot rebind


@pytest.fixture
async def stack(tmp_path):
    s = await Stack(tmp_path).start()
    await wait_for(lambda: s.gw.bound() and s.sim.tm_clients and s.agent._tc_writer is not None,
                   msg="link bound")
    yield s
    await s.stop()


async def tm_reader(port: int, sink: bytearray):
    reader, writer = await asyncio.open_connection("127.0.0.1", port)

    async def run():
        try:
            while True:
                d = await reader.read(65536)
                if not d:
                    break
                sink.extend(d)
        except (ConnectionError, asyncio.CancelledError):
            pass
    return writer, asyncio.ensure_future(run())


async def cut_link(stack: Stack):
    link = stack.gw.link
    await link.close(1001, "test cut")
    await wait_for(lambda: stack.gw.link is not link, msg="unbound")
    await asyncio.sleep(0)


# --- TM ----------------------------------------------------------------------

async def test_tm_byte_equality_two_clients(stack):
    a, b = bytearray(), bytearray()
    wa, ta = await tm_reader(stack.gw.ports["tm"], a)
    wb, tb = await tm_reader(stack.gw.ports["tm"], b)
    await wait_for(lambda: len(stack.gw.tm_clients) == 2)
    recs = [record(i) for i in range(3000)] + [record(9999, 60000)]
    for i in range(0, len(recs), 100):
        await stack.sim.push_tm(recs[i:i + 100])
    expect = b"".join(recs)
    await wait_for(lambda: len(a) >= len(expect) and len(b) >= len(expect), msg="all TM")
    assert bytes(a) == expect and bytes(b) == expect
    for w, t in ((wa, ta), (wb, tb)):
        t.cancel()
        w.close()


async def test_tm_resume_no_duplicates_and_client_survives_down(stack):
    sink = bytearray()
    w, t = await tm_reader(stack.gw.ports["tm"], sink)
    await wait_for(lambda: stack.gw.tm_clients)
    sent = [record(i) for i in range(200)]
    await stack.sim.push_tm(sent)
    await wait_for(lambda: len(sink) == len(b"".join(sent)))
    # Cut the link, keep producing TM while DOWN.
    await cut_link(stack)
    more = [record(i) for i in range(200, 600)]
    await stack.sim.push_tm(more)
    await asyncio.sleep(0.2)
    assert not w.is_closing(), "TM client must stay connected while the link is DOWN"
    await wait_for(lambda: stack.gw.bound(), msg="rebound")
    expect = b"".join(sent + more)
    await wait_for(lambda: len(sink) >= len(expect), msg="resumed TM")
    await asyncio.sleep(0.2)
    assert bytes(sink) == expect
    assert stack.gw.counters["tm_lost_frames"] == 0
    t.cancel()
    w.close()


async def test_tm_replay_from_buffer_after_inflight_loss(stack):
    """Frames handed to the writer but lost with the socket are replayed."""
    sink = bytearray()
    w, t = await tm_reader(stack.gw.ports["tm"], sink)
    await wait_for(lambda: stack.gw.tm_clients)
    agent_link = stack.agent.link
    agent_link.write_buffer_size = lambda: 10**9    # writer stalls: frames stay queued
    recs = [record(i) for i in range(50)]
    await stack.sim.push_tm(recs)
    await wait_for(lambda: agent_link.queued_frames(P.P_TM) >= 1 or
                   stack.agent.tm_log.send_seq > 0, msg="tm queued")
    await asyncio.sleep(0.1)
    await cut_link(stack)
    await wait_for(lambda: stack.gw.bound(), msg="rebound")
    await wait_for(lambda: len(sink) >= len(b"".join(recs)), msg="replayed")
    await asyncio.sleep(0.1)
    assert bytes(sink) == b"".join(recs)
    t.cancel()
    w.close()


# --- TC ----------------------------------------------------------------------

async def test_tc_at_most_once_across_reconnect(stack):
    r, w = await asyncio.open_connection("127.0.0.1", stack.gw.ports["tc"])
    tc_a = record(1, 15)
    w.write(tc_a)
    await w.drain()
    await wait_for(lambda: bytes(stack.sim.tc_received) == tc_a, msg="TC A at sim")
    # Stall the GSG writer, queue B and C, then lose the link.
    gl = stack.gw.link
    gl.write_buffer_size = lambda: 10**9
    tc_b, tc_c = record(2, 15), record(3, 15)
    w.write(tc_b + tc_c)
    await w.drain()
    await wait_for(lambda: stack.gw.counters["tc_packets"] == 3)
    await cut_link(stack)
    assert stack.gw.counters["tc_discarded"] >= 1
    await wait_for(lambda: stack.gw.bound(), msg="rebound")
    await asyncio.sleep(0.5)
    assert bytes(stack.sim.tc_received) == tc_a, "queued TC must never be replayed"
    # A new connection after reconnect works normally, exactly once.
    r2, w2 = await asyncio.open_connection("127.0.0.1", stack.gw.ports["tc"])
    tc_d = record(4, 20)
    w2.write(tc_d)
    await w2.drain()
    await wait_for(lambda: bytes(stack.sim.tc_received) == tc_a + tc_d, msg="TC D")
    w2.close()


async def test_tc_rst_when_link_down_mcs_style(stack):
    """A client that never reads its TC socket (like the MCS) must see the
    connection as closing after a link loss, so its next TC returns 503
    instead of vanishing into a FIN-closed socket."""
    agent = stack.agent
    r, w = await asyncio.open_connection("127.0.0.1", stack.gw.ports["tc"])
    await wait_for(lambda: stack.gw.tc_clients, msg="tc client registered")
    assert not w.is_closing()
    # Keep it DOWN: full-jitter backoff is uniform(0, cap), so a large cap
    # alone still lets the agent redial within milliseconds now and then.
    agent.cfg.url = DEAD_URL
    await cut_link(stack)
    await wait_for(lambda: w.is_closing(), timeout=3, msg="RST seen by never-reading client")
    with pytest.raises((ConnectionResetError, BrokenPipeError)):
        w.write(record(1, 15))
        await w.drain()
        await asyncio.sleep(0.05)
        w.write(record(1, 15))
        await w.drain()
    # New connects while DOWN are accepted then reset immediately.
    r2, w2 = await asyncio.open_connection("127.0.0.1", stack.gw.ports["tc"])
    with pytest.raises(ConnectionResetError):
        data = await asyncio.wait_for(r2.read(10), 2)
        assert data == b""  # a FIN would land here and fail the test
        raise AssertionError("expected RST, got FIN")
    await wait_for(lambda: w2.is_closing(), timeout=2)
    assert stack.gw.counters["tc_refused_connects"] >= 1
    assert stack.sim.tc_received == bytearray()


# --- STATE ---------------------------------------------------------------------

async def test_state_served_locally_and_stale_503(tmp_path):
    s = await Stack(tmp_path, stale_s=1.0).start()
    try:
        s.sim.state["speed"] = 10.0
        await wait_for(lambda: s.gw.anchor.state is not None, msg="state")
        async with aiohttp.ClientSession() as http:
            await asyncio.sleep(0.3)
            async with http.get(s.http + "/api/state") as r:
                assert r.status == 200
                st = await r.json()
        assert list(st) == list(s.sim.state)
        pushed = datetime.fromisoformat(s.sim.state["sim_time"])
        served = datetime.fromisoformat(st["sim_time"])
        assert 0 <= (served - pushed).total_seconds() <= 10.0 * 1.0
        assert st["met_s"] >= 1000.0 and st["params"] == {"1": 0.5}
        for a in s.agents:
            await a.stop()
        s.agents.clear()
        await asyncio.sleep(1.3)
        async with aiohttp.ClientSession() as http:
            async with http.get(s.http + "/api/state") as r:
                assert r.status == 503
            async with http.get(s.http + "/healthz") as r:
                assert r.status == 200
            async with http.get(s.http + "/link-status") as r:
                ls = await r.json()
                assert ls["state"] == "DOWN" and ls["session"] == "test-session"
                assert "secret" not in json.dumps(ls).lower()
    finally:
        await s.stop()


# --- dumps -----------------------------------------------------------------------

DUMP = "dump_sid01_20260820T120000Z.bin"


def _dump_bytes(n=40000) -> bytes:
    return b"".join(len(p).to_bytes(4, "big") + p for p in (bytes([i % 256]) * 100 for i in range(n // 104)))


async def test_dump_shipped_atomically_with_mtime(stack):
    data = _dump_bytes(60000)
    src = stack.sim.dump_dir / DUMP
    src.write_bytes(data[:1000])          # partial: must not ship until stable
    await asyncio.sleep(0.25)
    src.write_bytes(data)
    os.utime(src, (1_790_000_000, 1_790_000_000))
    dst = Path(stack.gw.cfg.dump_dir) / DUMP
    await wait_for(lambda: dst.exists(), msg="dump at GSG")
    assert dst.read_bytes() == data
    assert int(dst.stat().st_mtime) == 1_790_000_000
    assert not list(Path(stack.gw.cfg.dump_dir).glob(".part-*"))
    await wait_for(lambda: DUMP in stack.agent.acked)
    acked = json.loads((Path(stack.agent.cfg.state_dir) / "dumps_acked.json").read_text())
    assert acked["acked"][DUMP] == hashlib.sha256(data).hexdigest()
    assert stack.gw.counters["dumps_received"] == 1


async def test_dump_resume_from_part_and_bad_part_recovers(stack, tmp_path):
    data = _dump_bytes(100000)
    sha = hashlib.sha256(data).hexdigest()
    gdir = Path(stack.gw.cfg.dump_dir)
    half = 49920
    (gdir / f".part-{DUMP}").write_bytes(data[:half])
    (gdir / f".part-{DUMP}.json").write_text(json.dumps({"sha256": sha, "size": len(data), "mtime": 1}))
    received = {"n": 0}
    orig = stack.gw._on_dump_data

    async def counting(conn, f):
        received["n"] += len(f.payload)
        await orig(conn, f)
    stack.gw._on_dump_data = counting
    (stack.sim.dump_dir / DUMP).write_bytes(data)
    await wait_for(lambda: (gdir / DUMP).exists(), msg="resumed dump")
    assert (gdir / DUMP).read_bytes() == data
    assert received["n"] == len(data) - half, "resume must start at ack_offset"

    # A corrupt .part with matching meta fails the hash, is discarded, and the
    # retry from 0 succeeds.
    name2 = "dump_sid02_20260820T120001Z.bin"
    data2 = _dump_bytes(30000)
    sha2 = hashlib.sha256(data2).hexdigest()
    (gdir / f".part-{name2}").write_bytes(b"\xff" * 1000)
    (gdir / f".part-{name2}.json").write_text(json.dumps({"sha256": sha2, "size": len(data2), "mtime": 1}))
    (stack.sim.dump_dir / name2).write_bytes(data2)
    await wait_for(lambda: (gdir / name2).exists(), msg="dump after bad part")
    assert (gdir / name2).read_bytes() == data2
    assert not list(gdir.glob(".part-*"))


async def test_dump_existing_same_hash_acked_without_rewrite(stack):
    data = _dump_bytes(5000)
    gdir = Path(stack.gw.cfg.dump_dir)
    (gdir / DUMP).write_bytes(data)
    os.utime(gdir / DUMP, (1000, 1000))
    (stack.sim.dump_dir / DUMP).write_bytes(data)
    await wait_for(lambda: DUMP in stack.agent.acked, msg="ack")
    assert int((gdir / DUMP).stat().st_mtime) == 1000
    assert stack.gw.counters["dumps_received"] == 0


# --- proxy -------------------------------------------------------------------------

async def test_proxy_http(stack):
    async with aiohttp.ClientSession(auto_decompress=False) as http:
        async with http.get(stack.http + "/") as r:
            assert r.status == 200 and "instructor" in await r.text()
            assert r.headers["Cache-Control"] == "no-cache"
        async with http.get(stack.http + "/static/big.bin") as r:
            body = await r.read()
            assert body == b"".join(bytes([i]) * 16384 for i in range(64))
        async with http.get(stack.http + "/static/gz.txt", headers={"Accept-Encoding": "gzip"}) as r:
            assert r.headers["Content-Encoding"] == "gzip"
            raw = await r.read()
            assert gzip.decompress(raw) == stack.sim.GZ_PLAIN
        async with http.get(stack.http + "/static/etag.txt", headers={"If-None-Match": '"v1"'}) as r:
            assert r.status == 304 and r.headers["ETag"] == '"v1"'
        payload = os.urandom(700_000)    # > 256 KiB window: credits must flow
        async with http.post(stack.http + "/api/command", data=payload) as r:
            assert r.status == 200 and await r.read() == payload
        async with http.get(stack.http + "/api/instructor/snapshot", headers={
                "Connection": "X-Hop", "X-Hop": "1",
                "Origin": stack.http}) as r:
            h = await r.json()
            assert h["host"] == f"127.0.0.1:{stack.sim.ports['http']}"
            assert h["origin"] == f"http://127.0.0.1:{stack.sim.ports['http']}"
            assert h["x_hop"] is None
        for method, path in (("GET", "/config"), ("GET", "/static/../config"),
                             ("GET", "/api/config/files"), ("PUT", "/api/config/file"),
                             ("POST", "/api/reports/generate")):
            async with http.request(method, stack.http + path) as r:
                assert r.status == 403, path
        async with http.post(stack.http + "/api/command", data=b"x",
                             headers={"Origin": "http://evil.example"}) as r:
            assert r.status == 403
        async with http.get(stack.http + "/api/dumps") as r:
            assert r.status == 200 and (await r.json())["owner"] == "fakesim"
    assert stack.sim.config_hits == 0


async def test_proxy_websocket(stack):
    async with aiohttp.ClientSession() as http:
        async with http.ws_connect(stack.http.replace("http", "ws") + "/ws") as ws:
            first = await ws.receive(timeout=5)
            assert json.loads(first.data)["type"] == "state_update"
            await ws.send_str('{"type":"freeze"}')
            m = await ws.receive(timeout=5)
            assert m.data == 'echo:{"type":"freeze"}'
            big = os.urandom(100_000)
            await ws.send_bytes(big)
            m = await ws.receive(timeout=5)
            assert m.type == aiohttp.WSMsgType.BINARY and m.data == big[::-1]
        with pytest.raises(aiohttp.WSServerHandshakeError) as ei:
            async with http.ws_connect(stack.http.replace("http", "ws") + "/ws",
                                       origin="http://evil.example"):
                pass
        assert ei.value.status == 403
    assert stack.sim.ws_inbound == ['{"type":"freeze"}']


async def test_proxy_503_when_link_down(stack):
    stack.agent.cfg.url = DEAD_URL          # stay DOWN (see test above)
    await cut_link(stack)
    async with aiohttp.ClientSession() as http:
        async with http.get(stack.http + "/") as r:
            assert r.status == 503
        async with http.get(stack.http + "/config") as r:
            assert r.status == 403


# --- binding -----------------------------------------------------------------------

async def test_supersede(stack):
    first = stack.agent
    first_link = first.link
    second = await stack.add_agent()
    await wait_for(lambda: first_link.closed, msg="first superseded")
    assert stack.gw.counters["supersedes"] >= 1
    assert first_link.ws.close_code == P.WS_CLOSE_SUPERSEDED
    await first.stop()
    stack.agents.remove(first)
    await wait_for(lambda: stack.gw.bound() and second.link is not None, msg="second bound")
    sink = bytearray()
    w, t = await tm_reader(stack.gw.ports["tm"], sink)
    await wait_for(lambda: stack.gw.tm_clients)
    await stack.sim.push_tm([record(1)])
    await wait_for(lambda: bytes(sink) == record(1))
    t.cancel()
    w.close()


def _copy_config(dst: Path) -> Path:
    for rel in STRICT_FILES + WARN_FILES:
        (dst / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(CONFIG_DIR) / rel, dst / rel)
    return dst


async def test_config_mismatch_reject(tmp_path):
    cfg = _copy_config(tmp_path / "cfg")
    p = cfg / "telemetry/hk_structures.yaml"
    p.write_text(p.read_text(encoding="utf-8") + "\n# drift\n", encoding="utf-8")
    s = await Stack(tmp_path, agent_config_dir=str(cfg)).start()
    try:
        await wait_for(lambda: s.gw.counters["config_rejects"] >= 2, msg="rejects")
        assert not s.gw.bound() and s.agent.link is None
        # TC connects are refused while unbound.
        r, w = await asyncio.open_connection("127.0.0.1", s.gw.ports["tc"])
        with pytest.raises(ConnectionResetError):
            await asyncio.wait_for(r.read(10), 2)
            raise AssertionError("expected RST")
    finally:
        await s.stop()


async def test_config_warn_binds(tmp_path):
    cfg = _copy_config(tmp_path / "cfg")
    (cfg / "subsystems/eps.yaml").write_text("drift: true\n", encoding="utf-8")
    s = await Stack(tmp_path, agent_config_dir=str(cfg)).start()
    try:
        await wait_for(lambda: s.gw.bound(), msg="bound despite warn diff")
        assert s.gw.counters["config_rejects"] == 0
    finally:
        await s.stop()


async def test_bad_secret_401(tmp_path):
    s = await Stack(tmp_path, agent_secret=b"\x01" * 32).start()
    try:
        await wait_for(lambda: s.gw.counters["auth_failures"] >= 2, msg="401s")
        assert not s.gw.bound()
        async with aiohttp.ClientSession() as http:
            async with http.get(f"http://127.0.0.1:{s.gw.ports['link']}/link") as r:
                assert r.status == 401
    finally:
        await s.stop()
