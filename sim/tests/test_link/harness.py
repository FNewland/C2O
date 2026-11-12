"""In-process harness for smo-link component tests: a fake simulator (TM/TC
sockets + HTTP/WS on free ports), the GSG and the agent on loopback, and a
hand-driven v2 "raw agent" for adversarial tests.

The fake simulator's routes sit on the GSG's proxy allowlist (they are the
real instructor routes, with test bodies), plus the config editor routes,
which must never be reached."""
from __future__ import annotations

import asyncio
import gzip
import time
from pathlib import Path

import aiohttp
from aiohttp import WSMsgType, web

from smo_link import protocol as P
from smo_link.agent import Agent, AgentConfig
from smo_link.auth import make_header
from smo_link.channel import SecureChannel, mac_agent, new_nonce
from smo_link.confighash import compute
from smo_link.gateway import Gateway, GatewayConfig

CONFIG_DIR = str(Path(__file__).resolve().parents[2] / "configs" / "eosat1")
SECRET = bytes(range(32))
SESSION = "test-session"


def record(i: int, size: int | None = None) -> bytes:
    size = size or (10 + (i * 37) % 1040)
    body = bytes(((i + k) & 0xFF) for k in range(size))
    return len(body).to_bytes(2, "big") + body


class FakeSim:
    def __init__(self, dump_dir: Path):
        self.dump_dir = dump_dir
        self.tm_clients: list[asyncio.StreamWriter] = []
        self.tc_received = bytearray()
        self.tc_connections = 0
        self.config_hits = 0
        self.logbook_hits = 0
        self.seats_hits = 0
        self.last_headers: dict[str, str] = {}
        self.ws_inbound: list[str] = []
        self.state = {"tick": 1, "sim_time": "2026-08-20T12:00:00+00:00", "met_s": 1000.0,
                      "speed": 1.0, "in_contact": True, "time_to_eclipse_entry_s": 600.0,
                      "params": {"1": 0.5}}
        self.ports: dict[str, int] = {}

    async def start(self):
        self._tm = await asyncio.start_server(self._tm_handler, "127.0.0.1", 0)
        self._tc = await asyncio.start_server(self._tc_handler, "127.0.0.1", 0)
        app = web.Application()
        app.router.add_get("/api/state", self._state)
        app.router.add_get("/", self._index)
        app.router.add_get("/static/big.bin", self._big)
        app.router.add_get("/static/gz.txt", self._gz)
        app.router.add_get("/static/etag.txt", self._etag)
        app.router.add_post("/api/command", self._echo)
        app.router.add_get("/api/instructor/snapshot", self._headers)
        app.router.add_get("/api/vr", self._evil_headers)
        app.router.add_get("/config", self._config)
        app.router.add_get("/config/{tail:.*}", self._config)
        app.router.add_route("*", "/api/config/{tail:.*}", self._config)
        app.router.add_post("/api/reports/generate", self._config)
        app.router.add_get("/ws", self._ws)
        app.router.add_get("/vr", self._vr)
        app.router.add_get("/vr/power", self._vr)
        app.router.add_route("*", "/api/logbook{tail:.*}", self._logbook)
        app.router.add_route("*", "/api/seats{tail:.*}", self._seats)
        from smo_common.dump_store import register_dump_routes
        register_dump_routes(app, lambda: self.dump_dir, owner="fakesim")
        self._runner = web.AppRunner(app, access_log=None)
        await self._runner.setup()
        site = web.TCPSite(self._runner, "127.0.0.1", 0)
        await site.start()
        self.ports = {"tm": self._tm.sockets[0].getsockname()[1],
                      "tc": self._tc.sockets[0].getsockname()[1],
                      "http": site._server.sockets[0].getsockname()[1]}

    async def stop(self):
        for s in (self._tm, self._tc):
            s.close()
        for w in self.tm_clients:
            w.close()
        await self._runner.cleanup()

    # TM / TC
    async def _tm_handler(self, reader, writer):
        self.tm_clients.append(writer)
        try:
            while await reader.read(100):
                pass
        except ConnectionError:
            pass
        finally:
            if writer in self.tm_clients:
                self.tm_clients.remove(writer)

    async def push_tm(self, records: list[bytes]):
        data = b"".join(records)
        for w in list(self.tm_clients):
            w.write(data)
            await w.drain()

    async def _tc_handler(self, reader, writer):
        self.tc_connections += 1
        try:
            while True:
                d = await reader.read(4096)
                if not d:
                    break
                self.tc_received += d
        except ConnectionError:
            pass

    # HTTP
    async def _state(self, r):
        return web.json_response(self.state)

    async def _index(self, r):
        return web.Response(text="<html>instructor</html>", content_type="text/html",
                            headers={"Cache-Control": "no-cache"})

    async def _big(self, r):
        resp = web.StreamResponse()
        resp.content_type = "application/octet-stream"
        await resp.prepare(r)
        for i in range(64):
            await resp.write(bytes([i]) * 16384)
        await resp.write_eof()
        return resp

    GZ_PLAIN = b"hello gzip " * 5000

    async def _gz(self, r):
        return web.Response(body=gzip.compress(self.GZ_PLAIN), headers={
            "Content-Encoding": "gzip", "Content-Type": "text/plain"})

    async def _etag(self, r):
        if r.headers.get("If-None-Match") == '"v1"':
            return web.Response(status=304, headers={"ETag": '"v1"'})
        return web.Response(text="etag-body", headers={"ETag": '"v1"'})

    async def _echo(self, r):
        body = await r.read()
        return web.Response(body=body, headers={"X-Len": str(len(body))})

    async def _seats(self, r):
        self.seats_hits += 1            # must stay 0: the GSG answers it on the ground
        return web.json_response({"from": "space"})

    async def _logbook(self, r):
        self.logbook_hits += 1          # must stay 0: the GSG serves it locally
        return web.json_response({"from": "space"})

    async def _headers(self, r):
        self.last_headers = dict(r.headers)
        return web.json_response({"host": r.host, "origin": r.headers.get("Origin"),
                                  "conn": r.headers.get("Connection"),
                                  "x_hop": r.headers.get("X-Hop"),
                                  "path_qs": r.path_qs, "headers": dict(r.headers)})

    async def _evil_headers(self, r):
        """A hostile space side: tries to set cookies, redirect and relax CSP."""
        return web.Response(text="<script>alert(1)</script>", content_type="text/html", headers={
            "Set-Cookie": "stolen=1; Path=/", "Location": "https://evil.example/",
            "Access-Control-Allow-Origin": "*", "Content-Security-Policy": "default-src *",
            "X-Content-Type-Options": "sniff-please", "Refresh": "0; url=https://evil.example",
            "ETag": '"e1"'})

    async def _config(self, r):
        self.config_hits += 1
        return web.Response(text=f"CONFIG EDITOR {r.method} {r.path}")

    async def _vr(self, r):
        """The simulator's VR stream on its HTTP port: hello, one frame, echo status lines."""
        ws = web.WebSocketResponse()
        await ws.prepare(r)
        channel = "power" if r.path.endswith("/power") else "state"
        await ws.send_str('{"type":"hello","schema":"smo-vr/1"' +
                          (',"channel":"power"' if channel == "power" else "") + '}')
        await ws.send_str('{"type":"state","schema":"smo-vr/1","seq":1}')
        async for m in ws:
            if m.type == WSMsgType.TEXT:
                self.ws_inbound.append(m.data)
        return ws

    async def _ws(self, r):
        ws = web.WebSocketResponse()
        await ws.prepare(r)
        await ws.send_str('{"type":"state_update","state":{}}')
        async for m in ws:
            if m.type == WSMsgType.TEXT:
                self.ws_inbound.append(m.data)
                await ws.send_str("echo:" + m.data)
            elif m.type == WSMsgType.BINARY:
                await ws.send_bytes(m.data[::-1])
        return ws


class Stack:
    """FakeSim + GSG + agent."""

    def __init__(self, tmp: Path, mode: str = "complete", stale_s: float = 5.0,
                 agent_config_dir: str = CONFIG_DIR, agent_secret: bytes = SECRET,
                 **gw_over):
        self.tmp = tmp
        self.sim = FakeSim(tmp / "sim_dumps")
        (tmp / "sim_dumps").mkdir(parents=True, exist_ok=True)
        self.mode = mode
        self.stale_s = stale_s
        self.agent_config_dir = agent_config_dir
        self.agent_secret = agent_secret
        self.gw_over = gw_over
        self.agents: list[Agent] = []

    async def start(self, start_agent: bool = True):
        await self.sim.start()
        kw = dict(session=SESSION, secret=SECRET, bind="127.0.0.1", tm_port=0, tc_port=0,
                  http_port=0, link_bind="127.0.0.1", link_port=0,
                  dump_dir=str(self.tmp / "gsg_dumps"), config_dir=CONFIG_DIR,
                  status_interval=0.5, state_stale_s=self.stale_s, dump_min_free=0)
        kw.update(self.gw_over)
        self.gw = Gateway(GatewayConfig(**kw))
        await self.gw.start()
        if start_agent:
            self.agent = await self.add_agent()
        return self

    def agent_cfg(self, **over) -> AgentConfig:
        kw = dict(url=f"ws://127.0.0.1:{self.gw.ports['link']}/link", session=SESSION,
                  secret=self.agent_secret, sim_host="127.0.0.1",
                  sim_tm_port=self.sim.ports["tm"], sim_tc_port=self.sim.ports["tc"],
                  sim_http_port=self.sim.ports["http"], config_dir=self.agent_config_dir,
                  mode=self.mode, state_dir=str(self.tmp / f"agent_state{len(self.agents)}"),
                  backoff_base=0.05, backoff_cap=0.3, dump_poll_s=0.2, state_poll_s=0.05)
        kw.update(over)
        return AgentConfig(**kw)

    async def add_agent(self, **over) -> Agent:
        a = Agent(self.agent_cfg(**over))
        await a.start()
        self.agents.append(a)
        return a

    async def stop(self):
        for a in self.agents:
            await a.stop()
        await self.gw.stop()
        await self.sim.stop()

    @property
    def http(self) -> str:
        return f"http://127.0.0.1:{self.gw.ports['http']}"


async def wait_for(pred, timeout: float = 10.0, interval: float = 0.02, msg: str = ""):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        if pred():
            return
        await asyncio.sleep(interval)
    raise AssertionError(f"timeout waiting for {msg or pred}")


# --- hand-driven v2 agent ----------------------------------------------------------

class RawAgent:
    """Speaks the v2 handshake by hand, then exposes the sealed channel so a
    test can send well-formed, forged or replayed frames."""

    def __init__(self, ws, channel: SecureChannel | None, welcome: dict | None):
        self.ws = ws
        self.channel = channel
        self.welcome = welcome
        self.sent: list[bytes] = []

    async def send(self, frame: bytes) -> bytes:
        msg = self.channel.seal(frame)
        self.sent.append(msg)
        await self.ws.send_bytes(msg)
        return msg

    async def recv_frame(self, timeout: float = 5.0) -> P.Frame | None:
        m = await self.ws.receive(timeout=timeout)
        if m.type != WSMsgType.BINARY:
            return None
        return P.decode(self.channel.open(m.data))


async def raw_agent(gw: Gateway, http: aiohttp.ClientSession, instance: str = "raw",
                    secret: bytes = SECRET, header: str | None = None,
                    mac_secret: bytes | None = None, hello: bool = True) -> RawAgent:
    url = f"http://127.0.0.1:{gw.ports['link']}/link"
    ws = await http.ws_connect(url, headers={"Authorization": header or make_header(secret, SESSION)},
                               autoping=True, heartbeat=None)
    m = await ws.receive(timeout=5)
    chal = P.loads(P.decode(m.data).payload)
    assert chal["type"] == P.CHALLENGE, chal
    nonce_g = bytes.fromhex(chal["nonce_g"])
    nonce_a = new_nonce()
    mac = mac_agent(mac_secret or secret, SESSION, nonce_g, nonce_a)
    await ws.send_bytes(P.ctrl(P.AUTH, nonce_a=nonce_a.hex(), mac_a=mac.hex()))
    m = await ws.receive(timeout=5)
    if m.type != WSMsgType.BINARY:
        return RawAgent(ws, None, None)
    ok = P.loads(P.decode(m.data).payload)
    assert ok["type"] == P.AUTH_OK, ok
    ch = SecureChannel.for_agent(secret, nonce_a, nonce_g)
    ra = RawAgent(ws, ch, None)
    if hello:
        conf = compute(CONFIG_DIR)
        await ra.send(P.encode(P.CTRL, 0, 0, P.dumps({
            "type": "HELLO", "proto": P.PROTO, "session": SESSION, "config_files": conf["files"],
            "resume": {"instance": instance}, "mode": "complete"})))
        f = await ra.recv_frame()
        ra.welcome = P.loads(f.payload) if f is not None else None   # None: superseded at once
    return ra
