"""Space-link agent (space side): ``python -m smo_link.agent``.

A pure client of the simulator's loopback sockets (TM 8002, TC 8001, HTTP
8080). It reads sim TM promptly into a bounded log, writes TC from the link
to the sim (at most once, only whole records, never older than the TC TTL),
pushes STATE at 1 Hz, ships S15 dumps, serves allowlisted proxy streams
against the sim's HTTP/WS port, and keeps one outbound WebSocket to the GSG
alive with full-jitter backoff. It never exits on a link failure.

It refuses plaintext ``ws://`` to anything but a loopback/private address
unless ``SMO_LINK_ALLOW_INSECURE=1``, and it binds only after the GSG has
proved knowledge of the session secret (mutual challenge-response): a rogue
GSG never receives HELLO, and every later frame is tagged (channel.py).
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import random
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import aiohttp

from . import __version__
from . import protocol as P
from .auth import AuthError, load_secret, make_header
from .channel import (IntegrityError, SecureChannel, check_link_url, env_allow_insecure,
                      mac_agent, mac_gsg, new_nonce, parse_mac, parse_nonce, verify_mac)
from .confighash import compute as compute_config_hash
from .httpproxy import agent_serve_stream
from .mux import LinkConnection, Stream
from .replay import ReplayBuffer

logger = logging.getLogger("smo_link.agent")

STATE_PERIOD_S = 1.0
STATE_POLL_S = 0.5
DUMP_POLL_S = 2.0
SIM_RETRY_S = 1.0
HELLO_TIMEOUT_S = 15.0
HANDSHAKE_TIMEOUT_S = 10.0
TC_TTL_S = 5.0                  # used until the GSG's WELCOME says otherwise
DUMP_RETRY_CAP_S = 600.0
TM_QUEUE_LIMIT = 256 * 1024     # bytes of TM handed to the writer at once
DUMP_QUEUE_LIMIT = 128 * 1024
STATE_CHUNK = 32 * 1024


@dataclass
class AgentConfig:
    url: str
    session: str
    secret: bytes = field(repr=False)
    sim_host: str = "127.0.0.1"
    sim_tm_port: int = 8002
    sim_tc_port: int = 8001
    sim_http_port: int = 8080
    config_dir: str = "configs/eosat1"
    mode: str = "complete"          # complete | timely
    state_dir: str = "workspace/link"
    backoff_base: float = 0.5
    backoff_cap: float = 30.0
    backoff_reset_s: float = 60.0
    ping_interval: float = 10.0
    dead_after: float = 30.0
    queue_max_packets: int = 20_000
    queue_max_bytes: int = 8 * 1024 * 1024
    # >= dead_after + 10 s (L9): what a silently dead link swallowed in the
    # last 30 s is still there to resend after the reconnect.
    replay_age_s: float = 40.0
    replay_bytes: int = 16 * 1024 * 1024
    dump_poll_s: float = DUMP_POLL_S
    state_poll_s: float = STATE_POLL_S
    allow_insecure: bool = False    # SMO_LINK_ALLOW_INSECURE=1: ws:// to a public host


def backoff_delay(attempt: int, base: float = 0.5, cap: float = 30.0,
                  rng: random.Random | None = None) -> float:
    """Full-jitter exponential backoff: uniform(0, min(cap, base * 2**attempt))."""
    r = rng or random
    return r.uniform(0.0, min(cap, base * (2 ** min(attempt, 30))))


class Agent:
    def __init__(self, cfg: AgentConfig):
        if cfg.mode not in ("complete", "timely"):
            raise ValueError("mode must be 'complete' or 'timely'")
        check_link_url(cfg.url, cfg.allow_insecure or env_allow_insecure())
        if not isinstance(cfg.secret, (bytes, bytearray)) or len(cfg.secret) < 32:
            raise ValueError("link secret must be at least 32 bytes")
        self.cfg = cfg
        self.instance = secrets.token_hex(8)
        self.tm_log = ReplayBuffer(max_age_s=cfg.replay_age_s, max_bytes=cfg.replay_bytes,
                                   queue_max_packets=cfg.queue_max_packets,
                                   queue_max_bytes=cfg.queue_max_bytes)
        self._tm_event = asyncio.Event()
        self._tm_pending: list[bytes] = []
        self._tm_pending_bytes = 0
        self._tm_pending_t = 0.0
        self.link: LinkConnection | None = None
        self.bound = asyncio.Event()
        self.last_state: dict | None = None
        self._tc_writer: asyncio.StreamWriter | None = None
        self._state_seq = 0
        self._dump_seq = 0
        self._dump_waiters: dict[str, asyncio.Future] = {}
        self._dump_prev: dict[str, tuple] = {}
        self._dump_backoff: dict[str, tuple[float, float]] = {}   # name -> (next_try, delay)
        self.tc_ttl_s = TC_TTL_S
        self._welcome_offset = 0.0     # GSG wall - agent monotonic, from WELCOME
        self.acked: dict[str, str] = {}
        self._tasks: list[asyncio.Task] = []
        self._http: aiohttp.ClientSession | None = None
        self._proxy_http: aiohttp.ClientSession | None = None
        self._running = False
        self.config = compute_config_hash(cfg.config_dir)
        self.mission = self._mission_name()
        self.tick_hz = self._tick_hz()
        self.counters = {"tm_packets_in": 0, "tm_frames_out": 0, "tc_in": 0, "tc_to_sim": 0,
                         "tc_discarded": 0, "tc_expired": 0, "tc_malformed": 0,
                         "state_sent": 0, "dumps_shipped": 0, "dump_failures": 0,
                         "link_connects": 0, "link_failures": 0, "auth_failures": 0}
        self.status: dict = {}
        self._acked_path = Path(cfg.state_dir) / "dumps_acked.json"
        self._load_acked()

    # -- helpers ------------------------------------------------------------
    @property
    def sim_base(self) -> str:
        return f"http://{self.cfg.sim_host}:{self.cfg.sim_http_port}"

    def _mission_yaml(self) -> dict:
        try:
            import yaml
            return yaml.safe_load((Path(self.cfg.config_dir) / "mission.yaml")
                                  .read_text(encoding="utf-8")) or {}
        except Exception:  # noqa: BLE001
            return {}

    def _mission_name(self) -> str | None:
        return self._mission_yaml().get("name")

    def _tick_hz(self) -> float | None:
        net = self._mission_yaml().get("network") or {}
        try:
            return float(net.get("sim_tick_hz")) if net.get("sim_tick_hz") is not None else None
        except (TypeError, ValueError):
            return None

    def _load_acked(self) -> None:
        try:
            data = json.loads(self._acked_path.read_text(encoding="utf-8"))
            self.acked = dict(data.get("acked", {}))
        except (OSError, ValueError):
            self.acked = {}

    def _save_acked(self) -> None:
        try:
            self._acked_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._acked_path.with_name(self._acked_path.name + ".tmp")
            tmp.write_text(json.dumps({"acked": self.acked}, indent=1), encoding="utf-8")
            os.replace(tmp, self._acked_path)
        except OSError as e:
            logger.warning(P.kv("ack_persist_failed", error=type(e).__name__))

    # -- lifecycle ----------------------------------------------------------
    async def start(self) -> None:
        self._running = True
        self._http = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10, sock_connect=5))
        self._proxy_http = aiohttp.ClientSession(
            auto_decompress=False,
            timeout=aiohttp.ClientTimeout(total=None, sock_connect=10))
        logger.info(P.kv("agent_start", version=__version__, session=self.cfg.session,
                         url=self.cfg.url, mode=self.cfg.mode, mission=self.mission,
                         config_hash=self.config["hash"][:16], instance=self.instance))
        self._tasks = [asyncio.ensure_future(c) for c in (
            self._sim_tm_loop(), self._tm_flusher(), self._sim_tc_loop(),
            self._state_loop(), self._dump_loop(), self._link_loop())]

    async def stop(self) -> None:
        self._running = False
        if self.link is not None:
            await self.link.close(1001, "agent stopping")
        for t in self._tasks:
            t.cancel()
        for t in self._tasks:
            try:
                await t
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass
        if self._tc_writer is not None:
            self._tc_writer.close()
        for s in (self._http, self._proxy_http):
            if s is not None:
                await s.close()

    async def run_forever(self) -> None:
        await self.start()
        try:
            await asyncio.Event().wait()
        finally:
            await self.stop()

    # -- sim TM -------------------------------------------------------------
    async def _sim_tm_loop(self) -> None:
        while self._running:
            try:
                reader, writer = await asyncio.open_connection(self.cfg.sim_host, self.cfg.sim_tm_port)
            except OSError as e:
                logger.debug(P.kv("sim_tm_connect_failed", error=type(e).__name__))
                await asyncio.sleep(SIM_RETRY_S)
                continue
            logger.info(P.kv("sim_tm_connected", port=self.cfg.sim_tm_port))
            buf = bytearray()
            try:
                while True:
                    data = await reader.read(65536)
                    if not data:
                        break
                    buf += data
                    for rec in P.split_records(buf):
                        self._tm_add(rec)
            except (ConnectionError, P.ProtocolError) as e:
                logger.warning(P.kv("sim_tm_error", error=str(e)))
            finally:
                self._tm_flush()
                writer.close()
            logger.warning(P.kv("sim_tm_disconnected"))
            await asyncio.sleep(SIM_RETRY_S)

    def _tm_add(self, rec: bytes) -> None:
        self.counters["tm_packets_in"] += 1
        if not self._tm_pending:
            self._tm_pending_t = time.monotonic()
        if len(rec) > P.MAX_PAYLOAD:
            self._tm_flush()
            # Oversized record: split, later pieces flagged CONT.
            for off in range(0, len(rec), P.MAX_PAYLOAD):
                self.tm_log.append(rec[off:off + P.MAX_PAYLOAD], packets=1 if off == 0 else 0,
                                   flags=P.CONT if off else 0)
            self._tm_event.set()
            return
        if self._tm_pending_bytes + len(rec) > P.TM_COALESCE_BYTES:
            self._tm_flush()
        self._tm_pending.append(rec)
        self._tm_pending_bytes += len(rec)
        if self._tm_pending_bytes >= P.TM_COALESCE_BYTES:
            self._tm_flush()

    def _tm_flush(self) -> None:
        if not self._tm_pending:
            return
        self.tm_log.append(b"".join(self._tm_pending), packets=len(self._tm_pending))
        self._tm_pending = []
        self._tm_pending_bytes = 0
        self._tm_event.set()

    async def _tm_flusher(self) -> None:
        while self._running:
            await asyncio.sleep(P.TM_COALESCE_S / 2)
            if self._tm_pending and time.monotonic() - self._tm_pending_t >= P.TM_COALESCE_S:
                self._tm_flush()

    async def _tm_pump(self, link: LinkConnection) -> None:
        while not link.closed:
            if not self.tm_log.has_unsent():
                self._tm_event.clear()
                try:
                    await asyncio.wait_for(self._tm_event.wait(), 1.0)
                except asyncio.TimeoutError:
                    pass
                continue
            await link.wait_room(P.P_TM, TM_QUEUE_LIMIT)
            if link.closed:
                break
            e = self.tm_log.pop_unsent()
            if e is None:
                continue
            if e.flags & P.GAP:
                logger.warning(P.kv("tm_gap", seq=e.seq, dropped_frames=self.tm_log.dropped_frames,
                                    dropped_packets=self.tm_log.dropped_packets))
            link.enqueue(P.P_TM, P.encode(P.DATA, P.S_TM, e.seq, e.payload, e.flags))
            self.counters["tm_frames_out"] += 1

    # -- sim TC -------------------------------------------------------------
    async def _sim_tc_loop(self) -> None:
        while self._running:
            try:
                reader, writer = await asyncio.open_connection(self.cfg.sim_host, self.cfg.sim_tc_port)
            except OSError:
                await asyncio.sleep(SIM_RETRY_S)
                continue
            self._tc_writer = writer
            logger.info(P.kv("sim_tc_connected", port=self.cfg.sim_tc_port))
            try:
                while await reader.read(4096):
                    pass  # the sim never writes on TC
            except ConnectionError:
                pass
            finally:
                self._tc_writer = None
                writer.close()
            logger.warning(P.kv("sim_tc_disconnected"))
            await asyncio.sleep(SIM_RETRY_S)

    def _gsg_now(self, link: LinkConnection) -> float:
        """Current GSG wall time as estimated here. Anchored to the agent's
        monotonic clock, so a backward step of the agent's wall clock cannot
        make a stale TC look fresh (re-review N2)."""
        off = link.clock.mono_offset
        if off is None:
            off = self._welcome_offset
        return time.monotonic() + off

    def _on_tc(self, link: LinkConnection, f: P.Frame) -> None:
        """Write one TC to the sim: only whole records (L4), only if younger
        than the TC TTL end to end (M5). Never retried."""
        def refuse(counter: str, code: str, n: int, reason: str) -> None:
            self.counters[counter] += n
            logger.warning(P.kv("tc_discarded", code=code, reason=reason, count=n))
            link.enqueue(P.P_CONTROL, P.ctrl(P.NOTICE, code=code, count=n, reason=reason))

        try:
            stamp, payload = P.parse_tc_payload(f.payload)
            buf = bytearray(payload)
            records = P.split_records(buf)
            if buf or not records:
                raise P.ProtocolError("TC payload is not a whole number of records")
        except P.ProtocolError as e:
            refuse("tc_malformed", "tc-malformed", 1, str(e))
            return
        n = len(records)
        self.counters["tc_in"] += n
        age = self._gsg_now(link) - stamp
        if age > self.tc_ttl_s:
            refuse("tc_expired", "tc-expired", n, f"TC {age:.1f} s old (TTL {self.tc_ttl_s} s)")
            return
        w = self._tc_writer
        if w is None or w.is_closing():
            refuse("tc_discarded", "tc-discarded", n, "simulator TC socket not connected")
            return
        w.write(payload)  # byte-identical framed records; never retried
        self.counters["tc_to_sim"] += n

    # -- state --------------------------------------------------------------
    async def _state_loop(self) -> None:
        last_sent = 0.0
        last_key: tuple | None = None
        while self._running:
            await asyncio.sleep(self.cfg.state_poll_s)
            try:
                t0 = time.time()
                async with self._http.get(self.sim_base + "/api/state",
                                          timeout=aiohttp.ClientTimeout(total=2)) as r:
                    if r.status != 200:
                        continue
                    raw = await r.read()
                t1 = time.time()
                state = json.loads(raw)
            except (aiohttp.ClientError, asyncio.TimeoutError, OSError, ValueError):
                continue
            self.last_state = state
            key = (state.get("speed"),)
            link = self.link
            if link is None or link.closed or not self.bound.is_set():
                continue
            now = time.monotonic()
            if now - last_sent >= STATE_PERIOD_S or key != last_key:
                t_sample = (t0 + t1) / 2.0
                body = b'{"t_agent_wall":' + repr(t_sample).encode() + b',"state":' + raw + b"}"
                self._send_state(link, body)
                last_sent, last_key = now, key

    def _send_state(self, link: LinkConnection, body: bytes) -> None:
        for off in range(0, len(body), STATE_CHUNK):
            piece = body[off:off + STATE_CHUNK]
            fin = P.FIN if off + STATE_CHUNK >= len(body) else 0
            link.enqueue(P.P_STATE, P.encode(P.DATA, P.S_STATE, self._state_seq, piece, fin))
            self._state_seq = P.seq_add(self._state_seq, 1)
        self.counters["state_sent"] += 1

    # -- dumps --------------------------------------------------------------
    async def _dump_loop(self) -> None:
        while self._running:
            await asyncio.sleep(self.cfg.dump_poll_s)
            try:
                async with self._http.get(self.sim_base + "/api/dumps") as r:
                    if r.status != 200:
                        continue
                    listing = await r.json()
            except (aiohttp.ClientError, asyncio.TimeoutError, OSError, ValueError):
                continue
            seen = {}
            ready = []
            now = time.monotonic()
            for d in listing.get("dumps", []) if isinstance(listing, dict) else []:
                name = d.get("filename")
                if not name:
                    continue
                sig = (d.get("size_bytes"), d.get("mtime"))
                seen[name] = sig
                if self._dump_prev.get(name) == sig and name not in self.acked \
                        and self._dump_backoff.get(name, (0.0, 0.0))[0] <= now:
                    ready.append((name, d))
            self._dump_prev = seen
            for name, d in ready:
                link = self.link
                if link is None or link.closed or not self.bound.is_set():
                    break
                try:
                    await self._ship_dump(link, name, d)
                except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as e:
                    logger.warning(P.kv("dump_ship_failed", name=name, error=type(e).__name__))
                    break

    async def _ship_dump(self, link: LinkConnection, name: str, entry: dict) -> None:
        async with self._http.get(self.sim_base + "/api/dumps/file", params={"name": name},
                                  timeout=aiohttp.ClientTimeout(total=120)) as r:
            if r.status != 200:
                logger.warning(P.kv("dump_fetch_failed", name=name, status=r.status))
                return
            data = await r.read()
        if len(data) != entry.get("size_bytes"):
            return  # changed under us; next polls decide
        sha = hashlib.sha256(data).hexdigest()
        try:
            mtime = datetime.fromisoformat(str(entry.get("mtime"))).timestamp()
        except ValueError:
            mtime = time.time()
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self._dump_waiters[name] = fut
        try:
            link.enqueue(P.P_CONTROL, P.ctrl(P.DUMP_META, name=name, size=len(data),
                                             sha256=sha, mtime=mtime))
            reply = await asyncio.wait_for(fut, 30)
            if reply.get("type") == P.DUMP_READY:
                offset = int(reply.get("ack_offset") or 0)
                if not 0 <= offset <= len(data):
                    offset = 0
                logger.info(P.kv("dump_send", name=name, size=len(data), offset=offset))
                fut = loop.create_future()
                self._dump_waiters[name] = fut
                pos = offset
                while True:
                    await link.wait_room(P.P_DUMP, DUMP_QUEUE_LIMIT)
                    if link.closed:
                        return
                    piece = data[pos:pos + P.CHUNK]
                    last = pos + P.CHUNK >= len(data)
                    link.enqueue(P.P_DUMP, P.encode(P.DATA, P.S_DUMP, self._dump_seq, piece,
                                                    P.FIN if last else 0))
                    self._dump_seq = P.seq_add(self._dump_seq, 1)
                    pos += len(piece)
                    if last:
                        break
                reply = await asyncio.wait_for(fut, 120)
            if reply.get("type") == P.DUMP_ACK:
                if reply.get("ok"):
                    self.acked[name] = sha
                    self.counters["dumps_shipped"] += 1
                    self._save_acked()
                    logger.info(P.kv("dump_acked", name=name, size=len(data)))
                elif reply.get("reason") == "conflict":
                    self.acked[name] = "conflict"
                    self._save_acked()
                    logger.warning(P.kv("dump_conflict", name=name))
                else:
                    # GSG refused this transfer (io, disk-full, quota, ...): back
                    # off on this name only, so a full disk is not a retry storm.
                    self.counters["dump_failures"] += 1
                    _, prev = self._dump_backoff.get(name, (0.0, 0.0))
                    delay = min(DUMP_RETRY_CAP_S, max(2 * prev, 4 * self.cfg.dump_poll_s))
                    self._dump_backoff[name] = (time.monotonic() + delay, delay)
                    logger.warning(P.kv("dump_nack", name=name, reason=reply.get("reason"),
                                        retry_in_s=round(delay, 1)))
        finally:
            self._dump_waiters.pop(name, None)

    # -- link ---------------------------------------------------------------
    def _on_frame(self, link: LinkConnection, f: P.Frame) -> None:
        if f.type == P.DATA and f.stream == P.S_TC:
            self._on_tc(link, f)
        elif f.type == P.CTRL:
            try:
                m = P.loads_obj(f.payload)
            except P.ProtocolError:
                return
            t = m.get("type")
            if t in (P.DUMP_READY, P.DUMP_ACK):
                fut = self._dump_waiters.get(m.get("name"))
                if fut is not None and not fut.done():
                    fut.set_result(m)
            elif t == P.STATUS:
                self.status = m
            elif t == P.NOTICE:
                logger.warning(P.kv("gsg_notice", code=str(m.get("code"))[:64],
                                    count=m.get("count"),
                                    detail=str(m.get("message", ""))[:200]))

    async def _on_stream_open(self, s: Stream, msg: dict) -> None:
        await agent_serve_stream(s, msg, self._proxy_http, self.sim_base)

    def _hello(self) -> dict:
        st = self.last_state or {}
        return {"type": P.HELLO, "proto": P.PROTO, "session": self.cfg.session,
                "agent_version": __version__, "mission": self.mission,
                "config_hash": self.config["hash"], "config_files": self.config["files"],
                "sim": {"speed": st.get("speed"), "sim_time": st.get("sim_time"),
                        "tick_hz": self.tick_hz},
                "resume": {"instance": self.instance, "tm_next_seq": self.tm_log.send_seq},
                "mode": self.cfg.mode}

    async def _link_loop(self) -> None:
        attempt = 0
        while self._running:
            t_bound = None
            try:
                t_bound = await self._connect_once()
            except aiohttp.WSServerHandshakeError as e:
                self.counters["link_failures"] += 1
                level = logging.ERROR if e.status == 401 else logging.WARNING
                logger.log(level, P.kv("link_handshake_failed", status=e.status))
            except IntegrityError as e:
                self.counters["link_failures"] += 1
                self.counters["auth_failures"] += 1
                logger.error(P.kv("link_gsg_auth_failed", error=str(e),
                                  message="the GSG did not prove the session secret, "
                                          "or a frame failed its tag: nothing was sent"))
            except (aiohttp.ClientError, asyncio.TimeoutError, OSError, P.ProtocolError) as e:
                self.counters["link_failures"] += 1
                logger.warning(P.kv("link_connect_failed", error=type(e).__name__,
                                    detail=str(e)[:160]))
            except asyncio.CancelledError:
                raise
            except Exception as e:  # noqa: BLE001 - never exit on a link failure
                self.counters["link_failures"] += 1
                logger.exception(P.kv("link_error", error=type(e).__name__))
            if not self._running:
                break
            if t_bound is not None and time.monotonic() - t_bound >= self.cfg.backoff_reset_s:
                attempt = 0
            delay = backoff_delay(attempt, self.cfg.backoff_base, self.cfg.backoff_cap)
            attempt += 1
            logger.info(P.kv("link_retry", delay_s=round(delay, 2), attempt=attempt))
            await asyncio.sleep(delay)

    async def _handshake(self, ws: Any) -> SecureChannel | None:
        """Mutual challenge-response (channel.py): prove the secret to the
        GSG AND make it prove the secret back before anything else is sent."""
        msg = await ws.receive(timeout=HANDSHAKE_TIMEOUT_S)
        if msg.type != aiohttp.WSMsgType.BINARY:
            logger.warning(P.kv("link_no_challenge", msg_type=str(msg.type), code=ws.close_code))
            return None
        f = P.decode(msg.data)
        m = P.loads_obj(f.payload) if f.type == P.CTRL and f.stream == P.S_CONTROL else {}
        if m.get("type") != P.CHALLENGE or m.get("proto") != P.PROTO:
            raise P.ProtocolError(f"expected CHALLENGE proto {P.PROTO}")
        nonce_g = parse_nonce(m.get("nonce_g"))
        nonce_a = new_nonce()
        await ws.send_bytes(P.ctrl(P.AUTH, nonce_a=nonce_a.hex(), mac_a=mac_agent(
            self.cfg.secret, self.cfg.session, nonce_g, nonce_a).hex()))
        msg = await ws.receive(timeout=HANDSHAKE_TIMEOUT_S)
        if msg.type != aiohttp.WSMsgType.BINARY:
            logger.error(P.kv("link_auth_refused", msg_type=str(msg.type), code=ws.close_code))
            return None
        f = P.decode(msg.data)
        m = P.loads_obj(f.payload) if f.type == P.CTRL and f.stream == P.S_CONTROL else {}
        if m.get("type") != P.AUTH_OK:
            raise P.ProtocolError("expected AUTH_OK")
        verify_mac(mac_gsg(self.cfg.secret, self.cfg.session, nonce_a, nonce_g),
                   parse_mac(m.get("mac_g")))
        logger.info(P.kv("link_gsg_authenticated", gsg_id=str(m.get("gsg_id", ""))[:40]))
        return SecureChannel.for_agent(self.cfg.secret, nonce_a, nonce_g)

    async def _connect_once(self) -> float | None:
        """Dial, bind and run one link. Returns the bind time (monotonic) or None."""
        headers = {"Authorization": make_header(self.cfg.secret, self.cfg.session)}
        ws = await self._http.ws_connect(
            self.cfg.url, headers=headers, heartbeat=20, autoping=True, compress=0,
            max_msg_size=1 << 20, timeout=aiohttp.ClientWSTimeout(ws_receive=None, ws_close=10)
            if hasattr(aiohttp, "ClientWSTimeout") else 10.0)
        try:
            try:
                channel = await self._handshake(ws)
            except IntegrityError:
                await ws.close(code=P.WS_CLOSE_AUTH, message=b"gsg authentication failed")
                raise
            if channel is None:
                return None
            await ws.send_bytes(channel.seal(P.encode(P.CTRL, P.S_CONTROL, 0,
                                                      P.dumps(self._hello()))))
            msg = await ws.receive(timeout=HELLO_TIMEOUT_S)
            if msg.type != aiohttp.WSMsgType.BINARY:
                logger.warning(P.kv("link_no_welcome", msg_type=str(msg.type),
                                    code=ws.close_code))
                return None
            t_rx = time.monotonic()
            f = P.decode(channel.open(msg.data))
            reply = P.loads_obj(f.payload) if f.type == P.CTRL else {}
            if reply.get("type") == P.REJECT:
                logger.error(P.kv("link_rejected", code=reply.get("code"),
                                  files=",".join(reply.get("files", []))))
                return None
            if reply.get("type") != P.WELCOME:
                logger.warning(P.kv("link_unexpected_reply", type=reply.get("type")))
                return None
            try:
                ttl = float(reply.get("tc_ttl_s") or TC_TTL_S)
                self.tc_ttl_s = ttl if 0 < ttl <= 60 else TC_TTL_S
            except (TypeError, ValueError):
                self.tc_ttl_s = TC_TTL_S
            try:
                self._welcome_offset = float(reply.get("server_time")) - t_rx
            except (TypeError, ValueError):
                self._welcome_offset = 0.0
            link = LinkConnection(ws, "agent", self._on_frame, self._on_stream_open,
                                  ping_interval=self.cfg.ping_interval,
                                  dead_after=self.cfg.dead_after, channel=channel)
            resume = reply.get("resume_from_tm_seq")
            if self.cfg.mode == "timely":
                skipped = self.tm_log.skip_to_new()
                if skipped:
                    logger.warning(P.kv("tm_skipped_timely", frames=skipped))
            elif resume is not None:
                exact = self.tm_log.rewind(int(resume))
                if not exact:
                    logger.warning(P.kv("tm_resume_gap", requested=resume,
                                        oldest=self.tm_log.oldest_seq))
            self.link = link
            self.bound.set()
            self.counters["link_connects"] += 1
            t_bound = time.monotonic()
            logger.info(P.kv("link_up", session=self.cfg.session, resume_from=resume,
                             gsg_version=reply.get("gsg_version")))
            link.start()
            link.spawn(self._tm_pump(link))
            await link.wait_closed()
            logger.warning(P.kv("link_down", reason=link.close_reason,
                                tc_dropped=link.dropped_on_close.get(P.P_TC, 0)))
            return t_bound
        finally:
            self.bound.clear()
            if self.link is not None and self.link.ws is ws:
                self.link = None
            if not ws.closed:
                await ws.close()


# --- CLI --------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    e = os.environ.get
    p = argparse.ArgumentParser(prog="smo-link-agent",
                                description="SMO space-link agent (space side). "
                                            "Flags override the SMO_* environment.")
    p.add_argument("--url", default=e("SMO_LINK_URL"), help="GSG link URL ($SMO_LINK_URL)")
    p.add_argument("--session", default=e("SMO_LINK_SESSION"), help="session id ($SMO_LINK_SESSION)")
    p.add_argument("--secret", default=None,
                   help="hex secret; DISCOURAGED (visible in ps): use $SMO_LINK_SECRET or a file")
    p.add_argument("--secret-file", default=None, help="file holding the hex secret ($SMO_LINK_SECRET_FILE)")
    p.add_argument("--sim-host", default=e("SMO_SIM_HOST", "127.0.0.1"))
    p.add_argument("--sim-tm-port", type=int, default=int(e("SMO_SIM_TM_PORT", "8002")))
    p.add_argument("--sim-tc-port", type=int, default=int(e("SMO_SIM_TC_PORT", "8001")))
    p.add_argument("--sim-http-port", type=int, default=int(e("SMO_SIM_HTTP_PORT", "8080")))
    p.add_argument("--config-dir", default=e("SMO_CONFIG_DIR", "configs/eosat1"))
    p.add_argument("--mode", choices=["complete", "timely"], default=e("SMO_LINK_MODE", "complete"))
    p.add_argument("--state-dir", default=e("SMO_LINK_STATE_DIR", "workspace/link"))
    p.add_argument("--allow-insecure", action="store_true", default=env_allow_insecure(),
                   help="permit plaintext ws:// to a non-private host ($SMO_LINK_ALLOW_INSECURE=1)")
    p.add_argument("--log-level", default=e("SMO_LOG_LEVEL", "INFO"))
    return p


def config_from_args(args: argparse.Namespace) -> AgentConfig:
    if not args.url:
        raise SystemExit("smo-link-agent: SMO_LINK_URL (or --url) is required")
    if not args.session:
        raise SystemExit("smo-link-agent: SMO_LINK_SESSION (or --session) is required")
    if args.secret:
        logger.warning(P.kv("secret_on_command_line",
                            message="--secret is visible in ps and shell history; "
                                    "use SMO_LINK_SECRET_FILE"))
    try:
        secret = load_secret(args.secret, args.secret_file)
    except (AuthError, OSError) as e:
        raise SystemExit(f"smo-link-agent: {e}")
    try:
        check_link_url(args.url, args.allow_insecure)
    except ValueError as e:
        raise SystemExit(f"smo-link-agent: {e}")
    return AgentConfig(url=args.url, session=args.session, secret=secret,
                       sim_host=args.sim_host, sim_tm_port=args.sim_tm_port,
                       sim_tc_port=args.sim_tc_port, sim_http_port=args.sim_http_port,
                       config_dir=args.config_dir, mode=args.mode, state_dir=args.state_dir,
                       allow_insecure=args.allow_insecure)


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    P.setup_logging(args.log_level)
    cfg = config_from_args(args)
    try:
        asyncio.run(Agent(cfg).run_forever())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
