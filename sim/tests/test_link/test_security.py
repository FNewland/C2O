"""Regression tests for the independent review of smo-link v1
(research/LINK_REVIEW.md, H1-H4, M1-M6, L*). Each test reproduces the
reviewed failure and asserts the fixed behaviour; the review's repro scripts
were t_tc_fin.py (H1), t_proxy.py (H3), t_e2e_bypass.py (M1), t_misc.py (M2,
M4, M6, L5) and t_slow.py (M4)."""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import math
import re
import struct
import time
from pathlib import Path

import aiohttp
import pytest
from aiohttp import web

from smo_link import protocol as P
from smo_link.agent import Agent
from smo_link.auth import AuthError, Verifier, make_header
from smo_link.channel import (IntegrityError, SecureChannel, check_link_url, mac_agent,
                              mac_gsg, new_nonce)
from smo_link.gateway import Gateway, GatewayConfig, TmClient, _dump_name_ok
from smo_link.mux import LinkConnection

from .harness import CONFIG_DIR, SECRET, SESSION, Stack, raw_agent, record, wait_for

pytestmark = pytest.mark.timeout(60)
REPO = Path(__file__).resolve().parents[2]
DEAD_URL = "ws://127.0.0.1:1/link"


@pytest.fixture
async def stack(tmp_path):
    s = await Stack(tmp_path).start()
    await wait_for(lambda: s.gw.bound() and s.sim.tm_clients and s.agent._tc_writer is not None,
                   msg="link bound")
    yield s
    await s.stop()


async def gw_only(tmp_path, **over) -> Stack:
    s = await Stack(tmp_path, **over).start(start_agent=False)
    return s


async def tc_client(port: int):
    return await asyncio.open_connection("127.0.0.1", port)


async def expect_rst(reader: asyncio.StreamReader, timeout: float = 2.0) -> float:
    """Wait for the peer's close and require it to be an RST (a FIN would
    read as b'' and leave an MCS-style writer believing the socket is fine).
    Returns the time it took."""
    t0 = time.monotonic()
    with pytest.raises(ConnectionResetError):
        data = await asyncio.wait_for(reader.read(10), timeout)
        raise AssertionError(f"expected RST, got FIN/data {data!r}")
    return time.monotonic() - t0


def tc_rec(i: int = 1) -> bytes:
    return record(i, 15)


# =========================================================================== H1

async def test_h1_supersede_resets_tc_clients_at_once(tmp_path):
    """t_tc_fin.py: agent A bound and silent, agent B supersedes. The TC
    client must be RESET at once (not FIN after ~5 s), and B binds at once."""
    s = await gw_only(tmp_path)
    try:
        async with aiohttp.ClientSession() as http:
            a = await raw_agent(s.gw, http, "A")          # A never reads again
            assert a.welcome["type"] == P.WELCOME
            r, w = await tc_client(s.gw.ports["tc"])
            await wait_for(lambda: s.gw.tc_clients, msg="tc client")
            s.gw.link.write_buffer_size = lambda: 10 ** 9      # A's queue holds the TC
            w.write(tc_rec(1))
            await w.drain()
            await wait_for(lambda: s.gw.counters["tc_packets"] == 1, msg="TC queued on A")
            t0 = time.monotonic()
            b_task = asyncio.ensure_future(raw_agent(s.gw, http, "B"))
            dt = await expect_rst(r, timeout=3)
            b = await asyncio.wait_for(b_task, 3)
            assert b.welcome["type"] == P.WELCOME
            assert time.monotonic() - t0 < 2.0, "B's WELCOME must not wait for A's close"
            assert dt < 2.0
            assert s.gw.counters["supersedes"] == 1
            assert s.gw.counters["tc_discarded"] == 1, "L2: TC queued on the old link reported"
            with pytest.raises((ConnectionResetError, BrokenPipeError)):
                w.write(tc_rec())
                await w.drain()
                await asyncio.sleep(0.05)
                w.write(tc_rec())
                await w.drain()
            await a.ws.close()
            await b.ws.close()
    finally:
        await s.stop()


async def test_l1_racing_binds_leave_no_orphan(tmp_path):
    """Two valid agents bind concurrently while a third is bound: exactly
    one ends up bound; every other one is told 4000 'superseded'."""
    s = await gw_only(tmp_path)
    try:
        async with aiohttp.ClientSession() as http:
            agents = [await raw_agent(s.gw, http, "A")]
            agents += await asyncio.gather(raw_agent(s.gw, http, "B"), raw_agent(s.gw, http, "C"))
            assert s.gw.counters["supersedes"] == 2 and s.gw.bound()
            bound = s.gw.link_info["instance"]
            for ra, inst in zip(agents, "ABC"):
                if inst == bound:
                    f = await ra.recv_frame(timeout=3)       # sealed PING/STATUS keep coming
                    assert f is not None and f.type in (P.CTRL, P.PING)
                else:
                    m = await ra.ws.receive(timeout=7)
                    while m.type == aiohttp.WSMsgType.BINARY:     # frames sent before the supersede
                        m = await ra.ws.receive(timeout=7)
                    assert m.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED)
                    assert ra.ws.close_code == P.WS_CLOSE_SUPERSEDED, inst
            for ra in agents:
                await ra.ws.close()
    finally:
        await s.stop()


async def test_h1_dead_link_resets_tc_before_ws_close(tmp_path):
    """A silently dead peer: TC clients are reset when the link is declared
    dead, BEFORE the (up to 5 s) WebSocket close handshake times out."""
    s = await gw_only(tmp_path, ping_interval=0.3, dead_after=1.0)
    try:
        async with aiohttp.ClientSession() as http:
            a = await raw_agent(s.gw, http, "A")          # sends nothing more
            conn = s.gw.link
            r, w = await tc_client(s.gw.ports["tc"])
            await wait_for(lambda: s.gw.tc_clients, msg="tc client")
            await expect_rst(r, timeout=4)
            assert not conn._done.is_set(), "RST must precede the WS close wait"
            assert not s.gw.bound()
            await a.ws.close()
    finally:
        await s.stop()


async def test_h1_stop_resets_tc_clients(tmp_path):
    s = await gw_only(tmp_path)
    async with aiohttp.ClientSession() as http:
        a = await raw_agent(s.gw, http, "A")
        r, w = await tc_client(s.gw.ports["tc"])
        await wait_for(lambda: s.gw.tc_clients, msg="tc client")
        stopper = asyncio.ensure_future(s.gw.stop())
        await expect_rst(r)
        await stopper
        await a.ws.close()
    await s.sim.stop()


async def test_h1_l3_bad_and_oversized_tc_length_reset(stack):
    for n in (0, P.MAX_TC_RECORD + 1, 65535):
        r, w = await tc_client(stack.gw.ports["tc"])
        await wait_for(lambda: stack.gw.tc_clients, msg="tc client")
        w.write(struct.pack(">H", n) + bytes(min(n, 70000)))
        await expect_rst(r)
    assert stack.gw.bound(), "a bad TC record must not touch the link"
    assert stack.sim.tc_received == bytearray()


# =========================================================================== H2

def test_h2_channel_tags_reject_forgery_replay_reorder_reflection():
    na, ng = new_nonce(), new_nonce()
    agent, gsg = SecureChannel.for_agent(SECRET, na, ng), SecureChannel.for_gsg(SECRET, na, ng)
    f1 = P.encode(P.DATA, P.S_TC, 0, b"\x00\x02ab")
    f2 = P.encode(P.DATA, P.S_TC, 1, b"\x00\x02cd")
    m1, m2 = gsg.seal(f1), gsg.seal(f2)
    assert len(m1) == len(f1) + 16
    assert agent.open(m1) == f1
    with pytest.raises(IntegrityError):            # replay of m1
        agent.open(m1)
    assert agent.open(m2) == f2
    m3 = gsg.seal(f1)
    for i in (0, 3, 9, len(m3) - 1):                # any flipped bit: header, payload, tag
        bad = bytearray(m3)
        bad[i] ^= 0x01
        with pytest.raises(IntegrityError):
            SecureChannel.for_agent(SECRET, na, ng).open(bytes(bad))
    # reorder: a fresh receiver given frame #1 before #0
    rx = SecureChannel.for_agent(SECRET, na, ng)
    with pytest.raises(IntegrityError):
        rx.open(m2)
    # reflection: the agent's own frame bounced back at it
    with pytest.raises(IntegrityError):
        SecureChannel.for_agent(SECRET, na, ng).open(
            SecureChannel.for_agent(SECRET, na, ng).seal(f1))
    # a different session's keys
    with pytest.raises(IntegrityError):
        SecureChannel.for_agent(SECRET, new_nonce(), ng).open(
            SecureChannel.for_gsg(SECRET, na, ng).seal(f1))
    # unsealed v1-style frame
    with pytest.raises(IntegrityError):
        SecureChannel.for_agent(SECRET, na, ng).open(f1[:20])
    assert mac_agent(SECRET, SESSION, ng, na) != mac_gsg(SECRET, SESSION, ng, na)


async def test_h2_forged_frame_from_the_path_closes_link_and_resets_tc(stack):
    """Anyone who can write on the WebSocket (plaintext LB->GSG hop, ws://)
    but lacks the key: an injected frame closes the link, TC clients RST."""
    r, w = await tc_client(stack.gw.ports["tc"])
    await wait_for(lambda: stack.gw.tc_clients, msg="tc client")
    conn = stack.gw.link
    stack.agent.cfg.url = DEAD_URL
    forged = P.encode(P.DATA, P.S_TM, 0, record(1)) + bytes(16)
    await stack.agent.link.ws.send_bytes(forged)
    await expect_rst(r, timeout=3)
    await wait_for(lambda: conn.closed, msg="link closed")
    assert conn.ws.close_code == P.WS_CLOSE_INTEGRITY or conn.close_reason == "integrity failure"


async def test_h2_replayed_frame_closes_link(tmp_path):
    s = await gw_only(tmp_path)
    try:
        async with aiohttp.ClientSession() as http:
            a = await raw_agent(s.gw, http, "A")
            conn = s.gw.link
            msg = await a.send(P.encode(P.CTRL, 0, 0, P.dumps({"type": "NOTICE", "code": "x"})))
            await asyncio.sleep(0.1)
            assert not conn.closed
            await a.ws.send_bytes(msg)                      # the same sealed bytes again
            await wait_for(lambda: conn.closed, msg="replay rejected")
            assert conn.close_reason == "integrity failure"
            await a.ws.close()
    finally:
        await s.stop()


async def test_h2_injected_tc_towards_agent_never_reaches_sim(stack):
    """A TC frame injected on the path towards the agent (it would go
    straight to the simulator's TC port in v1) is rejected by the agent."""
    link = stack.agent.link
    stack.agent.cfg.url = DEAD_URL
    gl = stack.gw.link
    tc = P.tc_payload(tc_rec(), time.time())
    await gl.ws.send_bytes(P.encode(P.DATA, P.S_TC, 0, tc) + bytes(16))
    await wait_for(lambda: link.closed, msg="agent closed the link")
    assert link.close_reason == "integrity failure"
    await asyncio.sleep(0.2)
    assert stack.sim.tc_received == bytearray()


async def test_h2_valid_header_but_no_secret_cannot_bind(tmp_path):
    """M6 / H2: a captured header passes the fail-fast check of a GSG with an
    empty nonce cache (restart), but without the secret the mutual
    challenge-response fails, so nothing binds."""
    header = make_header(SECRET, SESSION)
    s = await gw_only(tmp_path)
    try:
        async with aiohttp.ClientSession() as http:
            a = await raw_agent(s.gw, http, "A", header=header)    # the real agent
            await a.ws.close()
            await wait_for(lambda: not s.gw.bound(), msg="unbound")
        await s.gw.stop()
        s.gw = Gateway(GatewayConfig(session=SESSION, secret=SECRET, bind="127.0.0.1",
                                     tm_port=0, tc_port=0, http_port=0, link_bind="127.0.0.1",
                                     link_port=0, dump_dir=str(tmp_path / "d2"),
                                     config_dir=CONFIG_DIR))
        await s.gw.start()                                         # "restarted" GSG
        Verifier(SECRET, SESSION).verify(header)                   # header alone still passes
        async with aiohttp.ClientSession() as http:
            ra = await raw_agent(s.gw, http, "attacker", header=header,
                                 mac_secret=b"\x77" * 32, hello=False)
            assert ra.channel is None
            assert ra.ws.close_code == P.WS_CLOSE_AUTH
        assert not s.gw.bound() and s.gw.counters["auth_failures"] == 1
        assert s.gw.counters["binds"] == 0
    finally:
        await s.stop()


async def test_h2_rogue_gsg_gets_no_hello_and_no_traffic(tmp_path):
    """A GSG that does not know the secret (spoofed DNS, student network)
    accepts any header and fakes AUTH_OK: the agent aborts before HELLO."""
    seen: list = []

    async def rogue(request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        await ws.send_bytes(P.ctrl(P.CHALLENGE, proto=P.PROTO, nonce_g=new_nonce().hex(),
                                   gsg_id="rogue"))
        async for m in ws:
            seen.append(m.data)
            await ws.send_bytes(P.ctrl(P.AUTH_OK, mac_g="00" * 32))
        return ws

    app = web.Application()
    app.router.add_get("/link", rogue)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    s = await Stack(tmp_path).start(start_agent=False)
    try:
        agent = await s.add_agent(url=f"ws://127.0.0.1:{port}/link")
        await wait_for(lambda: agent.counters["auth_failures"] >= 2, msg="agent refused rogue")
        assert agent.link is None and agent.counters["link_connects"] == 0
        for raw in seen:   # only AUTH frames ever went out: no HELLO, no data
            assert P.loads(P.decode(raw).payload)["type"] == P.AUTH
    finally:
        await s.stop()
        await runner.cleanup()


@pytest.mark.parametrize("url,ok", [
    ("wss://link.example.ca/link", True), ("ws://127.0.0.1:9100/link", True),
    ("ws://localhost:9100/link", True), ("ws://10.20.0.5:9100/link", True),
    ("ws://172.16.3.4/link", True), ("ws://192.168.1.10/link", True),
    ("ws://[::1]:9100/link", True), ("ws://[fd12::1]/link", True),
    ("ws://link.example.ca/link", False), ("ws://8.8.8.8/link", False),
    ("ws://172.32.0.1/link", False), ("ws://gsg:9100/link", False),
    ("http://127.0.0.1/link", False), ("ftp://x/link", False),
])
def test_h2_agent_refuses_plaintext_to_public_hosts(url, ok, caplog):
    if ok:
        check_link_url(url)
    else:
        with pytest.raises(ValueError):
            check_link_url(url)
    if not ok and url.startswith("ws://"):
        with caplog.at_level(logging.WARNING):
            check_link_url(url, allow_insecure=True)
        assert "INSECURE_TRANSPORT" in caplog.text


def test_h2_agent_constructor_enforces_transport(tmp_path):
    s = Stack(tmp_path)
    s.sim.ports = {"tm": 1, "tc": 1, "http": 1}

    class _G:
        ports = {"link": 1}
    s.gw = _G()
    with pytest.raises(ValueError, match="plaintext"):
        Agent(s.agent_cfg(url="ws://link.example.ca/link"))
    Agent(s.agent_cfg(url="ws://link.example.ca/link", allow_insecure=True))


# =========================================================================== H3

async def test_h3_credentials_never_cross_and_space_cannot_set_cookies(stack):
    async with aiohttp.ClientSession() as http:
        async with http.get(stack.http + "/api/instructor/snapshot", headers={
                "Cookie": "GCP_IAP_AUTH_TOKEN_abc=SECRET", "Authorization": "Bearer XYZ",
                "X-Goog-IAP-JWT-Assertion": "eyJhbGc", "X-Forwarded-For": "6.6.6.6",
                "Forwarded": "for=6.6.6.6", "Proxy-Authorization": "Basic x",
                "Accept-Language": "fr"}) as r:
            assert r.status == 200
        got = {k.lower() for k in stack.sim.last_headers}
        for h in ("cookie", "authorization", "x-goog-iap-jwt-assertion", "x-forwarded-for",
                  "x-forwarded-host", "x-forwarded-proto", "forwarded", "proxy-authorization"):
            assert h not in got, h
        assert stack.sim.last_headers.get("Accept-Language") == "fr"
        async with http.get(stack.http + "/api/vr") as r:
            assert r.status == 200
            for h in ("Set-Cookie", "Location", "Access-Control-Allow-Origin", "Refresh"):
                assert h not in r.headers, h
            assert r.headers["ETag"] == '"e1"'
            assert r.headers["X-Content-Type-Options"] == "nosniff"
            csp = r.headers["Content-Security-Policy"]
            assert "default-src 'self'" in csp and "default-src *" not in csp
            assert "connect-src 'self'" in csp and "frame-ancestors 'self'" in csp
            assert not r.cookies


# =========================================================================== M1

async def raw_http(port: int, line: bytes, extra: bytes = b"") -> bytes:
    r, w = await asyncio.open_connection("127.0.0.1", port)
    w.write(line + b"\r\nHost: 127.0.0.1:%d\r\n" % port + extra
            + b"Content-Length: 2\r\nConnection: close\r\n\r\n{}")
    await w.drain()
    data = await asyncio.wait_for(r.read(4096), 10)
    w.close()
    return data.split(b"\r\n", 1)[0]


async def test_m1_fragment_and_encoding_bypasses_refused(stack):
    """t_e2e_bypass.py: GET /config#x used to reach the sim's writable editor."""
    port = stack.gw.ports["http"]
    for line in (b"GET /config#x HTTP/1.1", b"GET /config%23x HTTP/1.1",
                 b"GET /%63onfig HTTP/1.1", b"GET /config;x HTTP/1.1",
                 b"GET /static/%2e%2e/config HTTP/1.1", b"GET //config HTTP/1.1",
                 b"PUT /api/conf%09ig/file HTTP/1.1", b"PUT /api/config/file HTTP/1.1",
                 b"POST /api/config/revert HTTP/1.1", b"POST /api/reports/generate HTTP/1.1",
                 b"GET /api/config%2Ffiles HTTP/1.1"):
        status = await raw_http(port, line)
        assert b" 403 " in status or b" 400 " in status, (line, status)
    assert stack.sim.config_hits == 0


async def test_m1_agent_reenforces_allowlist(stack):
    """Defence in depth: a proxy stream opened straight onto the link (as a
    compromised or buggy GSG could) for a config route is refused by the agent."""
    for msg in ({"kind": "http", "method": "GET", "path": "/config", "query": "", "headers": []},
                {"kind": "http", "method": "GET", "path": "/static/../config", "query": "",
                 "headers": []},
                {"kind": "http", "method": "PUT", "path": "/api/config/file", "query": "",
                 "headers": []},
                {"kind": "http", "method": "GET", "path": "/", "query": "a#b", "headers": []},
                {"kind": "ws", "method": "GET", "path": "/config", "query": "", "headers": []}):
        st = stack.gw.link.open_stream()
        st.send_open(msg)
        await st.send_data(b"", fin=True)
        head = await asyncio.wait_for(st.open_msg, 5)
        assert head["status"] == 403, (msg, head)
        st.send_close(0, "done")
    assert stack.sim.config_hits == 0


async def test_l11_host_header_allowlist(stack):
    async with aiohttp.ClientSession() as http:
        for path in ("/", "/link-status"):
            async with http.get(stack.http + path, headers={"Host": "evil.example:8080"}) as r:
                assert r.status == 403, path
            async with http.get(stack.http + path, headers={"Host": "localhost:8080"}) as r:
                assert r.status == 200, path


# =========================================================================== M2

async def test_m2_dump_io_error_fails_transfer_not_link(stack):
    """t_misc.py: an unwritable .part used to kill the link (and flap it
    forever as the agent reshipped). Now: DUMP_ACK ok=false reason=io, NOTICE,
    the link stays, the agent backs off on that name."""
    name = "dump_sid01_20260101T000000Z.bin"
    gdir = Path(stack.gw.cfg.dump_dir)
    (gdir / f".part-{name}").mkdir()
    link = stack.gw.link
    (stack.sim.dump_dir / name).write_bytes(b"x" * 1000)
    await wait_for(lambda: stack.agent.counters["dump_failures"] >= 1, msg="nack")
    assert stack.gw.link is link and not link.closed
    assert stack.gw.counters["dump_failures"] >= 1
    assert name in stack.agent._dump_backoff
    t_first = time.monotonic()
    await wait_for(lambda: stack.agent.counters["dump_failures"] >= 2, msg="second try")
    assert time.monotonic() - t_first >= 0.7, "backed off, no retry storm"
    await wait_for(lambda: stack.agent.counters["dump_failures"] >= 3, msg="third try")
    assert stack.agent._dump_backoff[name][1] >= 1.6, "the backoff grows"
    assert stack.gw.link is link and not link.closed


async def test_m2_bad_ping_and_ctrl_do_not_kill_link(stack):
    link = stack.gw.link
    al = stack.agent.link
    al.enqueue(P.P_CONTROL, P.encode(P.PING, 0, 0, b'{"t1": NaN}'))
    al.enqueue(P.P_CONTROL, P.encode(P.PONG, 0, 0, b'{"t1": 1, "t2": "x", "t3": []}'))
    al.enqueue(P.P_CONTROL, P.encode(P.CTRL, 0, 0, b'[1, 2, 3]'))
    al.enqueue(P.P_CONTROL, P.encode(P.CTRL, 0, 0, b'"DUMP_META"'))
    al.enqueue(P.P_CONTROL, P.ctrl(P.DUMP_META, name="../../etc/passwd", size=1,
                                   sha256="0" * 64, mtime=0))
    al.enqueue(P.P_CONTROL, P.ctrl(P.DUMP_META, name="dump_sid01_20260101T000000Z.bin\n",
                                   size=1, sha256="0" * 64, mtime=0))
    al.enqueue(P.P_STATE, P.encode(P.DATA, P.S_STATE, 0, b'{"t_agent_wall": NaN, "state": {}}',
                                   P.FIN))
    await asyncio.sleep(0.5)
    assert stack.gw.link is link and not link.closed and stack.agent.link is al
    assert not list(Path(stack.gw.cfg.dump_dir).glob("*passwd*"))


def test_m2_strict_json():
    with pytest.raises(P.ProtocolError):
        P.loads(b'{"t1": NaN}')
    with pytest.raises(P.ProtocolError):
        P.loads(b'{"t1": Infinity}')
    with pytest.raises(P.ProtocolError):
        P.loads_obj(b"[1]")


# =========================================================================== M3

class _WS:
    def __init__(self):
        self.sent = []
        self.closed = False
        self.close_code = None

    async def send_bytes(self, d):
        self.sent.append(d)

    async def close(self, code=1000, message=b""):
        self.closed = True

    def __aiter__(self):
        return self

    async def __anext__(self):
        await asyncio.sleep(3600)
        raise StopAsyncIteration


def _conn() -> LinkConnection:
    return LinkConnection(_WS(), "t", lambda c, f: None, ping_interval=3600,
                          channel=SecureChannel(b"k" * 32, b"k" * 32, b"a", b"b"))


async def test_m3_credit_enforced_on_receive_closes_stream_only():
    conn = _conn()
    st = conn.open_stream()
    chunk = bytes(P.CHUNK)
    for i in range(P.PROXY_WINDOW // P.CHUNK):
        await conn._dispatch_safe(P.Frame(P.DATA, 0, st.id, i, chunk))
    assert not st.closed
    await conn._dispatch_safe(P.Frame(P.DATA, 0, st.id, 99, b"x"))   # one byte over
    assert st.closed and not conn.closed
    sent = [P.decode(m) for m, _ in conn._queues[P.P_PROXY]]
    assert any(f.type == P.CLOSE and P.loads(f.payload)["code"] == 1008 for f in sent)
    await conn.close()


async def test_m3_reassembly_capped():
    conn = _conn()
    st = conn.open_stream()
    task = asyncio.ensure_future(st.recv_message(max_size=40_000))
    for i in range(4):
        await conn._dispatch_safe(P.Frame(P.DATA, 0, st.id, i, bytes(P.CHUNK)))
        await asyncio.sleep(0)
    assert await asyncio.wait_for(task, 2) is None and st.closed
    await conn.close()


async def test_m3_tm_fanout_bounded_by_bytes():
    class W:
        def write(self, d):
            pass

        async def drain(self):
            await asyncio.sleep(3600)
    c = TmClient(W(), maxlen=5000, peer="p", max_bytes=8 * 1024 * 1024)
    rec = bytes(65537)
    for _ in range(1000):                                # ~65 MB offered
        c.push(rec)
    assert c.qbytes <= 8 * 1024 * 1024 and c.dropped >= 1000 - 8 * 1024 * 1024 // len(rec)
    assert c.qbytes == sum(map(len, c.q))


@pytest.mark.parametrize("over,reason", [
    ({"dump_max_bytes": 10_000}, "too-large"),
    ({"dump_min_free": 1 << 62}, "disk-full"),
    ({"dump_max_inflight": 10_000}, "quota"),
])
async def test_m3_dump_limits(tmp_path, over, reason, caplog):
    s = await Stack(tmp_path, **over).start()
    try:
        await wait_for(lambda: s.gw.bound(), msg="bound")
        name = "dump_sid01_20260820T120000Z.bin"
        with caplog.at_level(logging.WARNING):
            (s.sim.dump_dir / name).write_bytes(b"y" * 40_000)
            await wait_for(lambda: s.agent.counters["dump_failures"] >= 1, msg="nack")
        assert f"reason={reason}" in caplog.text
        assert not (Path(s.gw.cfg.dump_dir) / name).exists()
        assert s.gw.bound()
    finally:
        await s.stop()


# =========================================================================== M4

async def test_m4_preauth_header_timeout_and_cap(tmp_path):
    """t_slow.py: half-open requests used to be held forever."""
    s = await gw_only(tmp_path, preauth_timeout=1.0, max_preauth=4, max_preauth_per_ip=10)
    try:
        port = s.gw.ports["link"]
        conns = []
        for _ in range(4):
            r, w = await asyncio.open_connection("127.0.0.1", port)
            w.write(b"GET /link HTTP/1.1\r\nHost: x\r\n")
            await w.drain()
            conns.append((r, w))
        await asyncio.sleep(0.1)
        # Over the cap: the newcomer is admitted and the OLDEST pending
        # connection is evicted (re-review N1), so fillers cannot lock out
        # the agent.
        r5, w5 = await asyncio.open_connection("127.0.0.1", port)
        r1, _w1 = conns.pop(0)
        try:
            assert await asyncio.wait_for(r1.read(10), 1) == b""
        except ConnectionResetError:
            pass
        conns.append((r5, w5))
        t0 = time.monotonic()
        for r, w in conns:
            try:
                d = await asyncio.wait_for(r.read(100), 3)
                assert d == b""
            except ConnectionResetError:
                pass
        assert time.monotonic() - t0 < 2.5
        assert s.gw.guard.timeouts == 4 and s.gw.guard.evicted == 1
        assert s.gw.guard.pending == 0
        # Still serves a legitimate agent afterwards, and an authenticated
        # link outlives the pre-auth deadline.
        agent = await s.add_agent()
        await wait_for(lambda: s.gw.bound(), msg="bound")
        await asyncio.sleep(1.5)
        assert s.gw.bound() and agent.counters["link_connects"] == 1
    finally:
        await s.stop()


async def test_m4_malformed_auth_is_401_and_logs_are_rate_limited(tmp_path, caplog):
    s = await gw_only(tmp_path, auth_log_per_min=3)
    try:
        port = s.gw.ports["link"]

        async def status(auth: bytes) -> bytes:
            r, w = await asyncio.open_connection("127.0.0.1", port)
            w.write(b"GET /link HTTP/1.1\r\nHost: x\r\nUpgrade: websocket\r\n"
                    b"Connection: Upgrade\r\nSec-WebSocket-Version: 13\r\n"
                    b"Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nAuthorization: "
                    + auth + b"\r\n\r\n")
            await w.drain()
            d = await asyncio.wait_for(r.read(200), 5)
            w.close()
            return d.split(b"\r\n", 1)[0]
        with caplog.at_level(logging.WARNING, logger="smo_link.gateway"):
            assert b" 401 " in await status(
                b"SMO-Link v=2, session=test-session, ts=1, nonce=0123456789abcdef, sig=\xe9")
            assert b" 401 " in await status(
                b"SMO-Link v=2, session=test-session, ts=1, nonce=0123456789abcdef, sig=00")
            assert b" 401 " in await status(b"SMO-Link v=1, session=\xff\xfe")
            for _ in range(15):
                assert b" 401 " in await status(b"garbage")
        assert s.gw.counters["auth_failures"] == 18
        assert caplog.text.count("event=link_auth_rejected ") == 3
        with pytest.raises(AuthError):
            Verifier(SECRET, SESSION).verify(
                "SMO-Link v=2, session=test-session, ts=1, nonce=0123456789abcdef, sig=\xe9" * 1)
    finally:
        await s.stop()


# =========================================================================== M5

async def test_m5_tc_ttl_in_gsg_queue(tmp_path, caplog):
    s = await Stack(tmp_path, tc_ttl_s=0.3).start()
    try:
        await wait_for(lambda: s.gw.bound() and s.agent._tc_writer is not None, msg="bound")
        gl = s.gw.link
        gl.write_buffer_size = lambda: 10 ** 9              # stall the GSG writer
        r, w = await tc_client(s.gw.ports["tc"])
        with caplog.at_level(logging.WARNING):
            w.write(tc_rec(1))
            await w.drain()
            await wait_for(lambda: s.gw.counters["tc_packets"] == 1, msg="queued")
            await asyncio.sleep(0.5)
            gl.write_buffer_size = lambda: 0
            await wait_for(lambda: s.gw.counters["tc_expired"] == 1, msg="expired")
            await asyncio.sleep(0.3)
        assert s.sim.tc_received == bytearray(), "a TC past its TTL must never be sent"
        assert "code=tc-expired" in caplog.text
        w.write(tc_rec(2))                                  # fresh TC still flows
        await w.drain()
        await wait_for(lambda: bytes(s.sim.tc_received) == tc_rec(2), msg="fresh TC")
    finally:
        await s.stop()


async def test_m5_degraded_link_is_down_for_tc(tmp_path):
    s = await Stack(tmp_path, tc_silence_s=1.0).start()
    try:
        await wait_for(lambda: s.gw.bound() and s.agent._tc_writer is not None, msg="bound")
        r, w = await tc_client(s.gw.ports["tc"])
        await wait_for(lambda: s.gw.tc_clients, msg="tc client")
        al = s.agent.link
        al.write_buffer_size = lambda: 10 ** 9              # agent goes silent
        await expect_rst(r, timeout=3)
        assert s.gw.bound() and s.gw.link_state() == "DEGRADED"
        r2, w2 = await tc_client(s.gw.ports["tc"])
        await expect_rst(r2)
        al.write_buffer_size = lambda: 0
        await wait_for(lambda: s.gw.tc_open(), msg="UP again")
        r3, w3 = await tc_client(s.gw.ports["tc"])
        w3.write(tc_rec(3))
        await w3.drain()
        await wait_for(lambda: bytes(s.sim.tc_received) == tc_rec(3), msg="TC after recovery")
    finally:
        await s.stop()


async def test_m5_agent_drops_stale_tc_and_l4_malformed(stack, caplog):
    gl = stack.gw.link
    with caplog.at_level(logging.WARNING):
        gl.enqueue(P.P_TC, P.encode(P.DATA, P.S_TC, 900, P.tc_payload(tc_rec(), time.time() - 30)))
        gl.enqueue(P.P_TC, P.encode(P.DATA, P.S_TC, 901,
                                    P.tc_payload(tc_rec()[:-3], time.time())))        # partial
        gl.enqueue(P.P_TC, P.encode(P.DATA, P.S_TC, 902,
                                    P.tc_payload(tc_rec() + b"\x00", time.time())))   # trailing
        await wait_for(lambda: stack.agent.counters["tc_expired"] == 1
                       and stack.agent.counters["tc_malformed"] == 2, msg="agent refused")
        await wait_for(lambda: "code=tc-expired" in caplog.text
                       and "event=agent_notice" in caplog.text, msg="NOTICE at the GSG")
    assert stack.sim.tc_received == bytearray()
    assert stack.gw.link is gl and not gl.closed


# =========================================================================== H4

def test_h4_compose_publishes_on_loopback_by_default():
    text = (REPO / "docker" / "compose.yaml").read_text(encoding="utf-8")
    import yaml
    doc = yaml.safe_load(text)
    for name, svc in doc["services"].items():
        for p in svc.get("ports", []) or []:
            p = str(p)
            host = p[:p.index("}") + 1] if p.startswith("${") else p.split(":")[0]
            assert host in ("127.0.0.1", "${SMO_PUBLISH_ADDR:-127.0.0.1}"), (name, p)
    assert "0.0.0.0}" not in text
    env = doc["services"]["gsg"]["environment"]
    assert env["SMO_GSG_BIND"] == "127.0.0.1", "GSG TM/TC must be loopback in the namespace"


# =========================================================================== L*

def test_l5_dump_name_strict():
    assert _dump_name_ok("dump_sid01_20260101T000000Z.bin")
    for bad in ("dump_sid01_20260101T000000Z.bin\n", "dump_sid٠1_20260101T000000Z.bin",
                "../dump_sid01_20260101T000000Z.bin", None, 5):
        assert not _dump_name_ok(bad), bad


async def test_m2_handler_exception_in_reader_drops_frame_not_link():
    """The isolation layer itself: an exception raised by an application
    handler for one frame leaves the link up and the next frame is handled."""
    from aiohttp import WSMessage, WSMsgType
    na, ng = new_nonce(), new_nonce()
    tx, rx = SecureChannel.for_gsg(SECRET, na, ng), SecureChannel.for_agent(SECRET, na, ng)
    msgs = [tx.seal(P.ctrl(P.NOTICE, code=c)) for c in ("boom", "ok")]

    class WS(_WS):
        def __init__(self):
            super().__init__()
            self._it = iter(msgs)

        async def __anext__(self):
            try:
                return WSMessage(WSMsgType.BINARY, next(self._it), None)
            except StopIteration:
                await asyncio.sleep(3600)
                raise StopAsyncIteration
    seen = []

    def on_frame(c, f):
        code = P.loads(f.payload)["code"]
        seen.append(code)
        if code == "boom":
            raise RuntimeError("handler bug")
    conn = LinkConnection(WS(), "t", on_frame, ping_interval=3600, channel=rx)
    conn.start()
    await wait_for(lambda: len(seen) == 2, msg="both frames handled")
    assert not conn.closed and conn.handler_errors == 1
    await conn.close()


# =========================================================================== re-review N1/N2

async def test_n1_401_frees_slot_and_cap_evicts_oldest(tmp_path):
    """N1: a completed 401 used to hold its pre-auth slot for the timeout;
    a full table used to refuse the real agent."""
    s = await gw_only(tmp_path, preauth_timeout=10.0, max_preauth=4, max_preauth_per_ip=100)
    try:
        port = s.gw.ports["link"]
        for _ in range(6):
            r, w = await asyncio.open_connection("127.0.0.1", port)
            w.write(b"GET /link HTTP/1.1\r\nHost: x\r\nConnection: keep-alive\r\n\r\n")
            await w.drain()
            data = await asyncio.wait_for(r.read(), 3)       # server closes after 401
            assert b" 401 " in data.split(b"\r\n", 1)[0]
            w.close()
        await asyncio.sleep(0.05)
        assert s.gw.guard.pending == 0
        fillers = []
        for _ in range(4):
            r, w = await asyncio.open_connection("127.0.0.1", port)
            fillers.append((r, w))
        await asyncio.sleep(0.05)
        assert s.gw.guard.pending == 4
        await s.add_agent()
        await wait_for(lambda: s.gw.bound(), timeout=5, msg="agent bound past fillers")
        assert s.gw.guard.evicted >= 1
        for _r, w in fillers:
            w.close()
    finally:
        await s.stop()


def test_n2_tc_age_survives_agent_wall_clock_step(monkeypatch):
    """N2: a backward step of the agent wall clock must not make a stale TC
    look fresh; the GSG time estimate is anchored to the monotonic clock."""
    from smo_link import agent as A
    from smo_link.clock import ClockEstimator
    est = ClockEstimator()
    now = time.time()
    est.add_sample(now, now + 0.01, now + 0.01, now + 0.02)   # in sync, 20 ms RTT
    fake = type("L", (), {"clock": est})()
    ag = A.Agent.__new__(A.Agent)
    ag._welcome_offset = 0.0
    before = A.Agent._gsg_now(ag, fake)
    real_time = time.time
    monkeypatch.setattr(A.time, "time", lambda: real_time() - 30.0)   # wall steps back 30 s
    after = A.Agent._gsg_now(ag, fake)
    assert abs(after - before) < 1.0


# ================================================================== logbook

@pytest.mark.parametrize("method,path", [
    ("GET", "/api/logbook"), ("DELETE", "/api/logbook"), ("POST", "/api/logbook/entries"),
    ("PATCH", "/api/logbook/entries/x"), ("DELETE", "/api/logbook/entries/x"),
    ("GET", "/api/logbook/export?format=md"), ("GET", "/api/logbook/worksheets"),
    ("GET", "/api/logbook/"), ("GET", "/static/../api/logbook"),
])
def test_logbook_is_never_on_the_link_allowlist(method, path):
    """LOGBOOK_SPEC §1: the person id and the logbook text never cross the
    space link. Neither the GSG nor the agent may forward /api/logbook."""
    from smo_link.httpproxy import deny_reason
    assert deny_reason(method, path) is not None


async def test_gsg_serves_the_logbook_itself(stack, tmp_path, monkeypatch):
    """The instructor console reached through the GSG keeps its logbook on the
    ground: the GSG answers /api/logbook from its own store (the ground
    workspace), with the Host check, and the simulator never sees it."""
    monkeypatch.setenv("SMO_LOGBOOK_DIR", str(tmp_path / "lb"))
    # the fixture's GSG was built before the env var: rebuild its store
    from smo_common.logbook import LogbookStore
    from smo_common.logbook.aiohttp_routes import STORE_KEY
    store = stack.gw._runners[0].app[STORE_KEY]
    store.dir = LogbookStore().dir
    H = {"Host": "localhost:8080",
         "X-Goog-Authenticated-User-Email": "accounts.google.com:fd@example.org"}
    async with aiohttp.ClientSession() as http:
        async with http.post(stack.http + "/api/logbook/entries", headers=H,
                             json={"kind": "decision", "text": "inject EPS fault at T+5"}) as r:
            assert r.status == 201, await r.text()
            e = await r.json()
            assert e["tool"] == "instructor"
        async with http.get(stack.http + "/api/logbook", headers=H) as r:
            j = await r.json()
            assert j["count"] == 1 and j["person"]["id_label"] == "fd@example.org"
        async with http.get(stack.http + "/api/logbook",
                            headers={**H, "Host": "evil.example:8080"}) as r:
            assert r.status == 403
    assert stack.sim.logbook_hits == 0
    assert (tmp_path / "lb").is_dir()
