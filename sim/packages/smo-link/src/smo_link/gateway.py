"""Ground-station gateway (GSG, ground side): ``python -m smo_link.gateway``.

Impersonates the simulator on the ground host so MCS, planner, rfsim and the
tools run unchanged:

* TM listener (default 127.0.0.1:8002): open from process start; clients are
  never disconnected (per-client drop-oldest queue: 5000 packets / 8 MiB).
* TC listener (default 127.0.0.1:8001): accepts TC only while the link is UP
  and has been heard from in the last 15 s. Otherwise existing clients are
  reset (SO_LINGER 0, RST) and new connects are accepted and reset at once,
  so the MCS reports ``503 No TC connection``. EVERY close of a TC client that
  the GSG initiates is abortive (H1). A TC that waited longer than
  ``SMO_LINK_TC_TTL_S`` (5 s) in the link queue is discarded, never sent.
* HTTP (default 127.0.0.1:8080): ``/api/state`` served locally from STATE
  (re-timed, 503 when older than 5 s), ``/healthz``, ``/link-status``, and an
  allowlist of instructor routes proxied to the sim's 8080 over the link.
* Link listener (default 0.0.0.0:9100) ``/link``: one agent, authenticated by
  the upgrade header (fail fast), then a mutual challenge-response, then a
  tag on every frame (channel.py). Pre-auth connections are capped and must
  finish the handshake within 10 s.
* Dumps written atomically into ``$SMO_DUMP_DIR`` (size / quota / free-space
  limits; an I/O error fails that transfer only).
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import math
import os
import re
import secrets
import shutil
import socket
import struct
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aiohttp import WSMsgType, web

from . import __version__
from . import protocol as P
from .auth import AuthError, Verifier, load_secret
from .channel import (IntegrityError, SecureChannel, mac_agent, mac_gsg, new_nonce,
                      parse_mac, parse_nonce, verify_mac)
from .clock import STATE_STALE_S, SimClockAnchor
from .confighash import compare as compare_config, compute as compute_config_hash
from .httpproxy import gsg_proxy, host_allowed, hosts_from_origins
from .mux import LinkConnection

logger = logging.getLogger("smo_link.gateway")

TM_CLIENT_QUEUE = 5000
TM_CLIENT_MAX_BYTES = 8 * 1024 * 1024
STATUS_INTERVAL_S = 5.0
HELLO_TIMEOUT_S = 15.0
TC_TTL_S = 5.0
TC_SILENCE_S = 15.0
PREAUTH_TIMEOUT_S = 10.0
DUMP_MAX_BYTES = 64 * 1024 * 1024
DUMP_MAX_INFLIGHT = 256 * 1024 * 1024
DUMP_MIN_FREE = 256 * 1024 * 1024

#: Strict, ASCII-only, whole-string dump name (L5). It is also checked against
#: smo_common's DUMP_NAME_RE so the MCS can list what the GSG stores.
_DUMP_NAME_RE = re.compile(r"dump_sid[0-9]{1,6}_[0-9]{8}T[0-9]{6}Z\.bin", re.ASCII)


def _dump_name_ok(name: Any) -> bool:
    if not isinstance(name, str) or not _DUMP_NAME_RE.fullmatch(name):
        return False
    try:
        from smo_common.dump_store import DUMP_NAME_RE
    except Exception:  # noqa: BLE001
        return True
    return bool(DUMP_NAME_RE.fullmatch(name))


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _sha256_prefix(path: Path, n: int) -> "hashlib._Hash":
    h = hashlib.sha256()
    with path.open("rb") as fh:
        left = n
        while left > 0:
            block = fh.read(min(1 << 20, left))
            if not block:
                break
            h.update(block)
            left -= len(block)
    return h


def rst_close(writer: asyncio.StreamWriter) -> None:
    """Abortive close: SO_LINGER 0 then abort, so the peer sees RST, not FIN."""
    try:
        sock = writer.get_extra_info("socket")
        if sock is not None:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
    except OSError:
        pass
    writer.transport.abort()


@dataclass
class GatewayConfig:
    session: str
    secret: bytes = field(repr=False)
    bind: str = "127.0.0.1"
    tm_port: int = 8002
    tc_port: int = 8001
    http_port: int = 8080
    http_bind: str | None = None          # default: ``bind``
    link_bind: str = "0.0.0.0"
    link_port: int = 9100
    dump_dir: str = "workspace/dumps"
    config_dir: str = "configs/eosat1"
    allowed_origins: list[str] = field(default_factory=list)
    allowed_hosts: list[str] = field(default_factory=list)
    tm_client_queue: int = TM_CLIENT_QUEUE
    tm_client_max_bytes: int = TM_CLIENT_MAX_BYTES
    status_interval: float = STATUS_INTERVAL_S
    ping_interval: float = 10.0
    dead_after: float = 30.0
    state_stale_s: float = STATE_STALE_S
    tc_ttl_s: float = TC_TTL_S
    tc_silence_s: float = TC_SILENCE_S
    preauth_timeout: float = PREAUTH_TIMEOUT_S
    max_preauth: int = 64
    max_preauth_per_ip: int = 16
    attempts_per_ip_per_min: int = 120
    auth_log_per_min: int = 10
    dump_max_bytes: int = DUMP_MAX_BYTES
    dump_max_inflight: int = DUMP_MAX_INFLIGHT
    dump_min_free: int = DUMP_MIN_FREE
    gsg_id: str = field(default_factory=lambda: "gsg-" + secrets.token_hex(4))


# --- link-port protection (M4) ------------------------------------------------

class _GuardedProtocol(asyncio.Protocol):
    """Delegates to aiohttp's RequestHandler; tells the guard when a
    connection opens and closes."""

    def __init__(self, inner: asyncio.Protocol, guard: "PreAuthGuard"):
        self._inner = inner
        self._guard = guard
        self._transport: asyncio.BaseTransport | None = None

    def connection_made(self, transport):  # type: ignore[override]
        self._transport = transport
        self._inner.connection_made(transport)
        self._guard.admit(transport)

    def data_received(self, data):  # type: ignore[override]
        self._inner.data_received(data)

    def eof_received(self):  # type: ignore[override]
        return self._inner.eof_received()

    def pause_writing(self):  # type: ignore[override]
        self._inner.pause_writing()

    def resume_writing(self):  # type: ignore[override]
        self._inner.resume_writing()

    def connection_lost(self, exc):  # type: ignore[override]
        self._guard.release(self._transport)
        self._inner.connection_lost(exc)


class PreAuthGuard:
    """Caps unauthenticated connections on the link port: at most
    ``max_total`` at once, ``max_per_ip`` per source address, and
    ``rate_per_min`` new connections per source address per minute. A
    connection that has not completed the mutual handshake within
    ``timeout`` seconds (header read, upgrade, challenge-response) is aborted.
    Behind the GCP load balancer the source is a Google front end, so these
    are a backstop; Cloud Armor rate-limits per client (deploy/gcp/README.md)."""

    def __init__(self, timeout: float, max_total: int, max_per_ip: int, rate_per_min: int):
        self.timeout = timeout
        self.max_total = max_total
        self.max_per_ip = max_per_ip
        self.rate_per_min = rate_per_min
        self._pending: dict[Any, tuple[str, asyncio.TimerHandle]] = {}
        self._per_ip: dict[str, int] = {}
        self._attempts: dict[str, deque] = {}
        self.rejected = 0
        self.timeouts = 0
        self.evicted = 0

    def factory(self, inner_factory):
        return lambda: _GuardedProtocol(inner_factory(), self)

    @staticmethod
    def _ip(transport) -> str:
        peer = transport.get_extra_info("peername")
        return str(peer[0]) if isinstance(peer, (tuple, list)) and peer else "?"

    def admit(self, transport) -> None:
        ip = self._ip(transport)
        now = time.monotonic()
        att = self._attempts.setdefault(ip, deque())
        while att and now - att[0] > 60.0:
            att.popleft()
        att.append(now)
        if len(self._attempts) > 10_000:          # bound memory under a spray
            for k in [k for k, v in self._attempts.items() if not v or now - v[-1] > 60.0]:
                self._attempts.pop(k, None)
        if self._per_ip.get(ip, 0) >= self.max_per_ip or len(att) > self.rate_per_min:
            self.rejected += 1
            transport.abort()
            return
        if len(self._pending) >= self.max_total:
            # Re-review N1: evict the oldest unauthenticated connection rather
            # than refusing the newcomer, so a filler cannot lock the agent out.
            oldest = next(iter(self._pending))
            self._forget(oldest)
            self.evicted += 1
            oldest.abort()
        handle = asyncio.get_running_loop().call_later(self.timeout, self._expire, transport)
        self._pending[transport] = (ip, handle)
        self._per_ip[ip] = self._per_ip.get(ip, 0) + 1

    def _forget(self, transport) -> bool:
        entry = self._pending.pop(transport, None)
        if entry is None:
            return False
        ip, handle = entry
        handle.cancel()
        n = self._per_ip.get(ip, 1) - 1
        if n > 0:
            self._per_ip[ip] = n
        else:
            self._per_ip.pop(ip, None)
        return True

    def _expire(self, transport) -> None:
        if self._forget(transport):
            self.timeouts += 1
            transport.abort()

    def mark_authenticated(self, transport) -> None:
        self._forget(transport)

    def release(self, transport) -> None:
        self._forget(transport)

    @property
    def pending(self) -> int:
        return len(self._pending)


class RateLimitedLog:
    """At most ``per_window`` lines per ``window`` seconds, then a summary."""

    def __init__(self, log: logging.Logger, per_window: int, window: float = 60.0):
        self.log = log
        self.per_window = per_window
        self.window = window
        self._start = 0.0
        self._count = 0
        self.suppressed = 0

    def warning(self, event: str, **fields: Any) -> None:
        now = time.monotonic()
        if now - self._start >= self.window:
            if self.suppressed:
                self.log.warning(P.kv(event + "_suppressed", count=self.suppressed,
                                      window_s=self.window))
            self._start, self._count, self.suppressed = now, 0, 0
        if self._count < self.per_window:
            self._count += 1
            self.log.warning(P.kv(event, **fields))
        else:
            self.suppressed += 1


# --- TM fan-out -----------------------------------------------------------------

class TmClient:
    """One local TM consumer: bounded drop-oldest queue (packets AND bytes)
    plus a writer task."""

    def __init__(self, writer: asyncio.StreamWriter, maxlen: int, peer: str,
                 max_bytes: int = TM_CLIENT_MAX_BYTES):
        self.writer = writer
        self.peer = peer
        self.q: deque[bytes] = deque()
        self.qbytes = 0
        self.maxlen = maxlen
        self.max_bytes = max_bytes
        self.event = asyncio.Event()
        self.dropped = 0
        self.sent = 0
        self.task: asyncio.Task | None = None

    def push(self, rec: bytes) -> None:
        self.q.append(rec)
        self.qbytes += len(rec)
        while len(self.q) > self.maxlen or (self.qbytes > self.max_bytes and len(self.q) > 1):
            self.qbytes -= len(self.q.popleft())
            self.dropped += 1
            if self.dropped == 1 or self.dropped % 1000 == 0:
                logger.warning(P.kv("tm_client_drop", peer=self.peer, dropped=self.dropped))
        self.event.set()

    async def run(self) -> None:
        while True:
            await self.event.wait()
            self.event.clear()
            while self.q:
                n = len(self.q)
                batch = b"".join(self.q.popleft() for _ in range(n))
                self.qbytes -= len(batch)
                self.writer.write(batch)
                self.sent += n
                await self.writer.drain()


class Gateway:
    def __init__(self, cfg: GatewayConfig):
        self.cfg = cfg
        self.verifier = Verifier(cfg.secret, cfg.session)
        self.config = compute_config_hash(cfg.config_dir)
        self.dump_dir = Path(cfg.dump_dir)
        self.anchor = SimClockAnchor(cfg.state_stale_s)
        self.link: LinkConnection | None = None
        self.link_info: dict = {}
        self.tm_clients: set[TmClient] = set()
        self.tc_clients: set[asyncio.StreamWriter] = set()
        self.guard = PreAuthGuard(cfg.preauth_timeout, cfg.max_preauth, cfg.max_preauth_per_ip,
                                  cfg.attempts_per_ip_per_min)
        self._auth_log = RateLimitedLog(logger, cfg.auth_log_per_min)
        self._allowed_hosts = list(cfg.allowed_hosts) + hosts_from_origins(cfg.allowed_origins)
        self._tc_seq = 0
        self._tm_instance: str | None = None
        self._tm_expected: int | None = None
        self._tm_buf = bytearray()
        self._tm_resync = True
        self._state_buf = bytearray()
        self._dump_rx: dict | None = None
        self._servers: list[Any] = []
        self._runners: list[web.AppRunner] = []
        self._tasks: set[asyncio.Task] = set()
        self.ports: dict[str, int] = {}
        self.counters = {k: 0 for k in (
            "tm_frames", "tm_packets", "tm_dup_frames", "tm_lost_frames", "tc_packets",
            "tc_refused_connects", "tc_reset_clients", "tc_discarded", "tc_expired",
            "tc_rejected_records", "state_rx", "dumps_received", "dump_failures",
            "auth_failures", "handshake_failures", "config_rejects", "supersedes", "binds")}

    # -- lifecycle ----------------------------------------------------------
    async def start(self) -> None:
        self.dump_dir.mkdir(parents=True, exist_ok=True)
        tm = await asyncio.start_server(self._handle_tm, self.cfg.bind, self.cfg.tm_port)
        tc = await asyncio.start_server(self._handle_tc, self.cfg.bind, self.cfg.tc_port)
        self._servers = [tm, tc]
        self.ports["tm"] = tm.sockets[0].getsockname()[1]
        self.ports["tc"] = tc.sockets[0].getsockname()[1]

        local = web.Application(client_max_size=8 * 1024 * 1024)
        local.router.add_get("/api/state", self._h_state)
        local.router.add_get("/healthz", self._h_health)
        local.router.add_get("/link-status", self._h_link_status)
        local.router.add_route("*", "/{tail:.*}", self._h_proxy)
        runner = web.AppRunner(local, access_log=None, handle_signals=False)
        await runner.setup()
        site = web.TCPSite(runner, self.cfg.http_bind or self.cfg.bind, self.cfg.http_port)
        await site.start()
        self._runners.append(runner)
        self.ports["http"] = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]

        link_app = web.Application(client_max_size=64 * 1024)
        link_app.router.add_get("/link", self._h_link)
        link_app.router.add_get("/healthz", self._h_health)
        link_runner = web.AppRunner(link_app, access_log=None, handle_signals=False)
        await link_runner.setup()
        loop = asyncio.get_running_loop()
        link_srv = await loop.create_server(self.guard.factory(link_runner.server),
                                            self.cfg.link_bind, self.cfg.link_port,
                                            reuse_address=True, backlog=128)
        self._runners.append(link_runner)
        self._servers.append(link_srv)
        self.ports["link"] = link_srv.sockets[0].getsockname()[1]
        self._spawn(self._status_loop())
        self._spawn(self._tc_watchdog())
        logger.info(P.kv("gsg_start", version=__version__, proto=P.PROTO, session=self.cfg.session,
                         gsg_id=self.cfg.gsg_id, bind=self.cfg.bind, tm=self.ports["tm"],
                         tc=self.ports["tc"], http_bind=self.cfg.http_bind or self.cfg.bind,
                         http=self.ports["http"], link_bind=self.cfg.link_bind,
                         link=self.ports["link"], dump_dir=self.dump_dir,
                         tc_ttl_s=self.cfg.tc_ttl_s, config_hash=self.config["hash"][:16]))

    async def stop(self) -> None:
        for s in self._servers:
            s.close()
        link = self.link
        if link is not None:
            link.abort(1001, "gsg stopping")       # unbinds + RSTs TC clients first
        self._reset_tc_clients("gsg stopping")
        for t in list(self._tasks):
            t.cancel()
        for c in list(self.tm_clients):
            if c.task is not None:
                c.task.cancel()
            c.writer.close()
        if link is not None:
            await link.close(1001, "gsg stopping")
        for r in self._runners:
            await r.cleanup()
        self._close_dump_rx()

    async def run_forever(self) -> None:
        await self.start()
        try:
            await asyncio.Event().wait()
        finally:
            await self.stop()

    def _spawn(self, coro) -> asyncio.Task:
        t = asyncio.ensure_future(coro)
        self._tasks.add(t)
        t.add_done_callback(self._tasks.discard)
        return t

    # -- state --------------------------------------------------------------
    def bound(self) -> bool:
        return self.link is not None and not self.link.closed

    def tc_open(self) -> bool:
        """TC flows only while bound AND the agent was heard recently: a
        DEGRADED (silent >= tc_silence_s) link is DOWN for TC (M5)."""
        link = self.link
        return link is not None and not link.closed and link.silence() < self.cfg.tc_silence_s

    def link_state(self) -> str:
        link = self.link
        if link is None or link.closed:
            return "DOWN"
        silence = link.silence()
        rtt = link.clock.rtt
        if silence < self.cfg.tc_silence_s and (rtt is None or rtt <= 1.0):
            return "UP"
        if silence < self.cfg.dead_after:
            return "DEGRADED"
        return "DOWN"

    def status(self) -> dict:
        link = self.link
        age = self.anchor.age_since_rx()
        return {
            "state": self.link_state(), "session": self.cfg.session, "proto": P.PROTO,
            "gsg_version": __version__, "gsg_id": self.cfg.gsg_id,
            "tc_open": self.tc_open(),
            "rtt": link.clock.rtt if link else None,
            "offset": link.clock.offset if link else None,
            "last_state_age": round(age, 3) if age is not None else None,
            "agent": self.link_info if link else None,
            "clients": {"tm": len(self.tm_clients), "tc": len(self.tc_clients)},
            "tm_client_drops": sum(c.dropped for c in self.tm_clients),
            "counters": dict(self.counters),
            "preauth": {"pending": self.guard.pending, "rejected": self.guard.rejected,
                        "evicted": self.guard.evicted,
                        "timeouts": self.guard.timeouts},
            "link": link.stats() if link else None,
            "config_hash": self.config["hash"],
        }

    async def _status_loop(self) -> None:
        while True:
            await asyncio.sleep(self.cfg.status_interval)
            link = self.link
            if link is not None and not link.closed:
                st = self.status()
                link.enqueue(P.P_CONTROL, P.ctrl(P.STATUS, state=st["state"], rtt=st["rtt"],
                                                 clients=st["clients"]))

    async def _tc_watchdog(self) -> None:
        while True:
            await asyncio.sleep(0.25)
            if self.tc_clients and not self.tc_open():
                self._reset_tc_clients("link degraded" if self.bound() else "link down")

    # -- local TM -----------------------------------------------------------
    async def _handle_tm(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = str(writer.get_extra_info("peername"))
        try:
            writer.transport.set_write_buffer_limits(high=256 * 1024)
        except Exception:  # noqa: BLE001
            pass
        client = TmClient(writer, self.cfg.tm_client_queue, peer, self.cfg.tm_client_max_bytes)
        self.tm_clients.add(client)
        logger.info(P.kv("tm_client_connected", peer=peer, clients=len(self.tm_clients)))
        task = asyncio.ensure_future(client.run())
        client.task = task

        def _done(t: asyncio.Task, client: TmClient = client) -> None:   # L8
            if t.cancelled():
                return
            exc = t.exception()
            if exc is not None:
                logger.info(P.kv("tm_client_write_failed", peer=client.peer,
                                 error=type(exc).__name__))
                self.tm_clients.discard(client)
                client.writer.transport.abort()
        task.add_done_callback(_done)
        try:
            while True:  # bytes sent to the TM port are ignored, like the sim
                if not await reader.read(4096):
                    break
        except (ConnectionError, OSError):
            pass
        finally:
            task.cancel()
            self.tm_clients.discard(client)
            writer.close()
            logger.info(P.kv("tm_client_disconnected", peer=peer, dropped=client.dropped))

    def _on_tm(self, f: P.Frame) -> None:
        self.counters["tm_frames"] += 1
        if self._tm_expected is not None:
            d = P.seq_diff(f.seq, self._tm_expected)
            if d < 0:
                self.counters["tm_dup_frames"] += 1
                return
            if d > 0:
                self.counters["tm_lost_frames"] += d
                logger.warning(P.kv("tm_frames_lost", count=d, expected=self._tm_expected,
                                    got=f.seq))
                self._tm_resync = True
        if f.flags & P.GAP:
            logger.warning(P.kv("tm_gap_flag", seq=f.seq))
            self._tm_resync = True
        self._tm_expected = P.seq_add(f.seq, 1)
        if self._tm_resync:
            self._tm_buf.clear()
            if f.flags & P.CONT:
                return
            self._tm_resync = False
        self._tm_buf += f.payload
        if len(self._tm_buf) > 2 * P.MAX_FRAME + 65537:
            logger.error(P.kv("tm_corrupt", error="partial record too large"))
            self._tm_buf.clear()
            self._tm_resync = True
            return
        try:
            records = P.split_records(self._tm_buf)
        except P.ProtocolError as e:
            logger.error(P.kv("tm_corrupt", error=str(e)))
            self._tm_buf.clear()
            self._tm_resync = True
            return
        self.counters["tm_packets"] += len(records)
        for c in self.tm_clients:
            for rec in records:
                c.push(rec)

    # -- local TC -----------------------------------------------------------
    async def _handle_tc(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = str(writer.get_extra_info("peername"))
        if not self.tc_open():
            self.counters["tc_refused_connects"] += 1
            logger.info(P.kv("tc_connect_reset", peer=peer,
                             reason="link degraded" if self.bound() else "link down"))
            rst_close(writer)
            return
        self.tc_clients.add(writer)
        logger.info(P.kv("tc_client_connected", peer=peer))
        abort = True            # every close the GSG initiates is an RST (H1)
        try:
            while True:
                hdr = await reader.readexactly(2)
                n = struct.unpack(">H", hdr)[0]
                if n == 0 or n > P.MAX_TC_RECORD:
                    self.counters["tc_rejected_records"] += 1
                    logger.warning(P.kv("tc_bad_length", peer=peer, length=n,
                                        max=P.MAX_TC_RECORD))
                    break
                rec = hdr + await reader.readexactly(n)
                link = self.link
                if link is None or not self.tc_open():
                    self.counters["tc_discarded"] += 1
                    logger.warning(P.kv("notice", code="tc-discarded", count=1, peer=peer,
                                        reason="link degraded" if self.bound() else "link down"))
                    break
                link.enqueue(P.P_TC, P.encode(P.DATA, P.S_TC, self._tc_seq,
                                              P.tc_payload(rec, time.time())),
                             deadline=time.monotonic() + self.cfg.tc_ttl_s)
                self._tc_seq = P.seq_add(self._tc_seq, 1)
                self.counters["tc_packets"] += 1
        except asyncio.IncompleteReadError:
            abort = False      # the client closed (or we already reset it)
        except (ConnectionError, OSError):
            pass
        finally:
            self.tc_clients.discard(writer)
            if abort:
                rst_close(writer)
            elif not writer.is_closing():
                writer.close()

    def _reset_tc_clients(self, reason: str = "link down") -> None:
        n = len(self.tc_clients)
        for w in list(self.tc_clients):
            rst_close(w)
        self.tc_clients.clear()
        if n:
            self.counters["tc_reset_clients"] += n
            logger.warning(P.kv("tc_clients_reset", count=n, reason=reason))

    def _on_expired(self, conn: LinkConnection, prio: int, n: int) -> None:
        if prio != P.P_TC:
            return
        self.counters["tc_expired"] += n
        logger.warning(P.kv("notice", code="tc-expired", count=n, ttl_s=self.cfg.tc_ttl_s,
                            message="TC waited longer than its TTL in the link queue; "
                                    "discarded, never sent"))
        conn.enqueue(P.P_CONTROL, P.ctrl(P.NOTICE, code="tc-expired", count=n,
                                         message=f"{n} TC discarded at the GSG (TTL "
                                                 f"{self.cfg.tc_ttl_s} s)"))

    # -- HTTP ---------------------------------------------------------------
    async def _h_health(self, request: web.Request) -> web.Response:
        return web.json_response({"ok": True, "state": self.link_state()})

    async def _h_link_status(self, request: web.Request) -> web.Response:
        if not host_allowed(request.headers.get("Host"), self._allowed_hosts):
            return web.json_response({"error": "forbidden", "reason": "host not allowed"},
                                     status=403)
        return web.json_response(self.status())

    async def _h_state(self, request: web.Request) -> web.Response:
        offset = self.link.clock.offset if self.link is not None else self._last_offset
        state = self.anchor.retimed(offset)
        if state is None:
            age = self.anchor.age_since_rx()
            return web.json_response(
                {"error": "no fresh simulator state over the space link",
                 "link": self.link_state(),
                 "last_state_age": round(age, 3) if age is not None else None}, status=503)
        return web.json_response(state)

    _last_offset = 0.0

    async def _h_proxy(self, request: web.Request) -> web.StreamResponse:
        return await gsg_proxy(request, self.link, self.cfg.allowed_origins, self._allowed_hosts)

    # -- link ---------------------------------------------------------------
    def _auth_reject(self, peer: str | None, reason: str) -> web.Response:
        self.counters["auth_failures"] += 1
        self._auth_log.warning("link_auth_rejected", peer=peer, reason=reason)
        resp = web.json_response({"error": "unauthorized"}, status=401)
        resp.force_close()          # re-review N1: free the pre-auth slot now
        return resp

    async def _handshake(self, ws: web.WebSocketResponse, peer: str | None
                         ) -> SecureChannel | None:
        """Mutual challenge-response (channel.py). Returns the channel, or
        None after closing the socket."""
        nonce_g = new_nonce()
        try:
            await ws.send_bytes(P.ctrl(P.CHALLENGE, proto=P.PROTO, nonce_g=nonce_g.hex(),
                                       gsg_id=self.cfg.gsg_id))
            msg = await ws.receive(timeout=self.cfg.preauth_timeout)
            if msg.type != WSMsgType.BINARY:
                raise P.ProtocolError("expected binary AUTH")
            f = P.decode(msg.data)
            m = P.loads_obj(f.payload) if f.type == P.CTRL and f.stream == P.S_CONTROL else {}
            if m.get("type") != P.AUTH:
                raise P.ProtocolError("expected AUTH")
            nonce_a = parse_nonce(m.get("nonce_a"))
            mac_a = parse_mac(m.get("mac_a"))
            if nonce_a == nonce_g:
                raise IntegrityError("reflected nonce")
            verify_mac(mac_agent(self.cfg.secret, self.cfg.session, nonce_g, nonce_a), mac_a)
        except IntegrityError as e:
            self.counters["auth_failures"] += 1
            self._auth_log.warning("link_mutual_auth_failed", peer=peer, reason=str(e))
            await ws.close(code=P.WS_CLOSE_AUTH, message=b"authentication failed")
            return None
        except (asyncio.TimeoutError, P.ProtocolError, ConnectionError) as e:
            self.counters["handshake_failures"] += 1
            self._auth_log.warning("link_handshake_failed", peer=peer,
                                   error=str(e) or type(e).__name__)
            await ws.close(code=P.WS_CLOSE_PROTOCOL, message=b"bad handshake")
            return None
        await ws.send_bytes(P.ctrl(P.AUTH_OK, mac_g=mac_gsg(self.cfg.secret, self.cfg.session,
                                                             nonce_a, nonce_g).hex()))
        return SecureChannel.for_gsg(self.cfg.secret, nonce_a, nonce_g)

    async def _h_link(self, request: web.Request) -> web.StreamResponse:
        peer = request.remote
        try:
            self.verifier.verify(request.headers.get("Authorization"), "GET", "/link")
        except AuthError as e:
            self.guard.release(request.transport)
            return self._auth_reject(peer, str(e))
        except Exception as e:  # noqa: BLE001 - a malformed credential is a 401, never a 500
            self.guard.release(request.transport)
            return self._auth_reject(peer, f"malformed credential ({type(e).__name__})")
        ws = web.WebSocketResponse(heartbeat=20, compress=False, autoping=True,
                                   max_msg_size=2 * P.MAX_FRAME)
        await ws.prepare(request)
        channel = await self._handshake(ws, peer)
        if channel is None:
            return ws
        self.guard.mark_authenticated(request.transport)
        try:
            msg = await ws.receive(timeout=HELLO_TIMEOUT_S)
            if msg.type != WSMsgType.BINARY:
                raise P.ProtocolError("expected binary HELLO")
            f = P.decode(channel.open(msg.data))
            hello = P.loads_obj(f.payload) if f.type == P.CTRL else {}
            if hello.get("type") != P.HELLO or hello.get("proto") != P.PROTO:
                raise P.ProtocolError(f"expected HELLO proto {P.PROTO}")
            if hello.get("session") != self.cfg.session:
                raise P.ProtocolError("session mismatch")
        except (asyncio.TimeoutError, P.ProtocolError, IntegrityError) as e:
            logger.warning(P.kv("link_hello_failed", peer=peer, error=str(e) or type(e).__name__))
            await ws.close(code=P.WS_CLOSE_PROTOCOL, message=b"bad hello")
            return ws

        strict, warn = compare_config(self.config["files"], hello.get("config_files"))
        if strict:
            self.counters["config_rejects"] += 1
            logger.error(P.kv("link_config_mismatch", peer=peer, files=",".join(strict)))
            await ws.send_bytes(channel.seal(P.ctrl(P.REJECT, code="config-mismatch",
                                                    files=strict)))
            await ws.close(code=P.WS_CLOSE_CONFIG, message=b"config mismatch")
            return ws

        # ---- bind: no await between here and conn.start() (L1) ----
        old = self.link
        if old is not None:
            if not old.closed:
                self.counters["supersedes"] += 1
                logger.warning(P.kv("link_superseded", peer=peer))
            # Synchronous: unbinds, counts the old queue's TCs, RSTs every TC
            # client, THEN finishes the old WebSocket close in the background.
            old.abort(P.WS_CLOSE_SUPERSEDED, "superseded")
            if self.link is old:
                self._unbind(old)

        resume = hello.get("resume") if isinstance(hello.get("resume"), dict) else {}
        instance = resume.get("instance")
        if instance and instance == self._tm_instance:
            # Same agent process: continue where we are (agent seqs start at
            # 0, so an instance that never delivered TM resumes from 0).
            resume_from = self._tm_expected if self._tm_expected is not None else 0
        else:
            resume_from = None
            if self._tm_instance is None and isinstance(resume.get("tm_next_seq"), int) \
                    and resume["tm_next_seq"] > 0:
                logger.warning(P.kv("notice", code="tm-continuity-unknown",
                                    agent_tm_next_seq=resume["tm_next_seq"],
                                    message="GSG restarted under a running agent: TM in flight "
                                            "to the previous GSG process may be lost"))
            self._tm_instance = instance
            self._tm_expected = None
            self._tm_resync = True
        self._state_buf.clear()
        self._close_dump_rx()

        conn = LinkConnection(ws, "gsg", self._on_frame, None,
                              ping_interval=self.cfg.ping_interval, dead_after=self.cfg.dead_after,
                              channel=channel, on_close=self._on_link_close,
                              on_expired=self._on_expired)
        self.link = conn
        self.counters["binds"] += 1
        self.link_info = {"peer": peer, "agent_version": hello.get("agent_version"),
                          "mission": hello.get("mission"), "mode": hello.get("mode"),
                          "instance": instance, "config_hash": hello.get("config_hash"),
                          "sim": hello.get("sim"), "bound_at": time.time()}
        conn.enqueue(P.P_CONTROL, P.ctrl(P.WELCOME, proto=P.PROTO, gsg_version=__version__,
                                         accepted=True, resume_from_tm_seq=resume_from,
                                         server_time=time.time(), tc_ttl_s=self.cfg.tc_ttl_s))
        if warn:
            logger.warning(P.kv("link_config_warn", files=",".join(warn)))
            conn.enqueue(P.P_CONTROL, P.ctrl(P.NOTICE, code="config-warn", files=warn,
                                             message="warn-set config files differ"))
        logger.info(P.kv("link_up", peer=peer, session=self.cfg.session, mode=hello.get("mode"),
                         resume_from=resume_from, agent_version=hello.get("agent_version")))
        conn.start()
        try:
            await conn.wait_closed()
        finally:
            if self.link is conn:
                self._unbind(conn)
            logger.info(P.kv("link_closed", reason=conn.close_reason))
        return ws

    def _on_link_close(self, conn: LinkConnection) -> None:
        """Runs synchronously inside LinkConnection.abort(), before the
        WebSocket close handshake is awaited."""
        if self.link is conn:
            self._unbind(conn)

    def _unbind(self, conn: LinkConnection) -> None:
        self.link = None
        self._last_offset = conn.clock.offset
        tc_dropped = conn.dropped_on_close.get(P.P_TC, 0)
        if tc_dropped:
            self.counters["tc_discarded"] += tc_dropped
            logger.warning(P.kv("notice", code="tc-discarded", count=tc_dropped,
                                reason=conn.close_reason,
                                message="queued TC discarded on link loss (never replayed)"))
        logger.warning(P.kv("link_down", reason=conn.close_reason))
        self._reset_tc_clients(conn.close_reason or "link down")
        self._close_dump_rx()

    async def _on_frame(self, conn: LinkConnection, f: P.Frame) -> None:
        if conn is not self.link:
            return
        if f.type == P.DATA:
            if f.stream == P.S_TM:
                self._on_tm(f)
            elif f.stream == P.S_STATE:
                self._on_state(f)
            elif f.stream == P.S_DUMP:
                await self._on_dump_data(conn, f)
        elif f.type == P.CTRL:
            try:
                m = P.loads_obj(f.payload)
            except P.ProtocolError as e:
                logger.warning(P.kv("ctrl_bad", error=str(e)[:120]))
                return
            t = m.get("type")
            if t == P.DUMP_META:
                await self._on_dump_meta(conn, m)
            elif t == P.NOTICE:
                logger.warning(P.kv("agent_notice", code=str(m.get("code"))[:64],
                                    count=m.get("count"),
                                    detail=str(m.get("reason", m.get("message", "")))[:200]))

    def _on_state(self, f: P.Frame) -> None:
        self._state_buf += f.payload
        if len(self._state_buf) > 8 * 1024 * 1024:
            self._state_buf.clear()
            return
        if not f.flags & P.FIN:
            return
        body = bytes(self._state_buf)
        self._state_buf.clear()
        try:
            m = P.loads_obj(body)
            t = float(m["t_agent_wall"])
            if not math.isfinite(t) or not isinstance(m["state"], dict):
                raise ValueError("bad STATE")
            self.anchor.update(t, m["state"])
            self.counters["state_rx"] += 1
        except (P.ProtocolError, ValueError, KeyError, TypeError) as e:
            logger.warning(P.kv("state_bad", error=type(e).__name__))

    # -- dumps --------------------------------------------------------------
    def _close_dump_rx(self) -> None:
        rx, self._dump_rx = self._dump_rx, None
        if rx is not None:
            try:
                rx["fh"].close()
            except OSError:
                pass

    def _dump_nack(self, conn: LinkConnection, name: Any, reason: str, detail: str = "") -> None:
        self.counters["dump_failures"] += 1
        logger.error(P.kv("dump_rejected", name=str(name)[:80], reason=reason, detail=detail))
        conn.enqueue(P.P_CONTROL, P.ctrl(P.DUMP_ACK, name=name if isinstance(name, str) else None,
                                         ok=False, reason=reason))
        conn.enqueue(P.P_CONTROL, P.ctrl(P.NOTICE, code="dump-failed", reason=reason,
                                         message=f"dump transfer refused: {reason}"))

    def _inflight_bytes(self, exclude: Path) -> int:
        total = 0
        try:
            for p in self.dump_dir.glob(".part-*"):
                if p != exclude and not p.name.endswith(".json"):
                    try:
                        total += p.stat().st_size
                    except OSError:
                        pass
        except OSError:
            pass
        return total

    async def _on_dump_meta(self, conn: LinkConnection, m: dict) -> None:
        name = m.get("name")
        try:
            size = int(m.get("size"))
            sha = str(m.get("sha256"))
            mtime = float(m.get("mtime"))
            if not math.isfinite(mtime):
                raise ValueError
        except (TypeError, ValueError):
            size, sha, mtime = -1, "", 0.0
        if not _dump_name_ok(name) or size < 0 or not re.fullmatch(r"[0-9a-f]{64}", sha):
            conn.enqueue(P.P_CONTROL, P.ctrl(P.DUMP_ACK, name=name if isinstance(name, str)
                                             else None, ok=False, reason="invalid"))
            return
        if size > self.cfg.dump_max_bytes:
            self._dump_nack(conn, name, "too-large", f"size={size} max={self.cfg.dump_max_bytes}")
            return
        self._close_dump_rx()
        final = self.dump_dir / name
        part = self.dump_dir / f".part-{name}"
        meta = self.dump_dir / f".part-{name}.json"
        try:
            if final.exists():
                same = await asyncio.to_thread(_sha256_file, final) == sha
                if not same:
                    logger.error(P.kv("dump_conflict", name=name))
                conn.enqueue(P.P_CONTROL, P.ctrl(P.DUMP_ACK, name=name, ok=same,
                                                 reason=None if same else "conflict"))
                return
            offset = 0
            try:
                prev = json.loads(meta.read_text(encoding="utf-8"))
                if prev.get("sha256") == sha and prev.get("size") == size and part.is_file():
                    offset = part.stat().st_size
                    if offset > size:
                        offset = 0
            except (OSError, ValueError, AttributeError):
                pass
            need = size - offset
            free = shutil.disk_usage(self.dump_dir).free
            if free - need < self.cfg.dump_min_free:
                self._dump_nack(conn, name, "disk-full", f"free={free} need={need}")
                return
            if self._inflight_bytes(part) + size > self.cfg.dump_max_inflight:
                self._dump_nack(conn, name, "quota", f"max_inflight={self.cfg.dump_max_inflight}")
                return
            h = await asyncio.to_thread(_sha256_prefix, part, offset) if offset else hashlib.sha256()
            if offset == 0:
                meta.write_text(json.dumps({"sha256": sha, "size": size, "mtime": mtime}),
                                encoding="utf-8")
            fh = part.open("r+b" if offset else "wb")
            try:
                fh.seek(offset)
                fh.truncate()
            except OSError:
                fh.close()
                raise
        except OSError as e:
            self._dump_nack(conn, name, "io", type(e).__name__)
            return
        self._dump_rx = {"name": name, "size": size, "sha256": sha, "mtime": mtime, "h": h,
                         "fh": fh, "part": part, "meta": meta, "pos": offset}
        logger.info(P.kv("dump_rx_start", name=name, size=size, ack_offset=offset))
        conn.enqueue(P.P_CONTROL, P.ctrl(P.DUMP_READY, name=name, ack_offset=offset))

    async def _on_dump_data(self, conn: LinkConnection, f: P.Frame) -> None:
        rx = self._dump_rx
        if rx is None:
            return
        if rx["pos"] + len(f.payload) > rx["size"]:
            self._dump_fail(conn, rx, "oversize")
            return
        try:
            rx["fh"].write(f.payload)
            rx["h"].update(f.payload)
            rx["pos"] += len(f.payload)
            if not f.flags & P.FIN:
                return
            fh = rx["fh"]
            fh.flush()
            os.fsync(fh.fileno())
            fh.close()
            self._dump_rx = None
            name, part, final = rx["name"], rx["part"], self.dump_dir / rx["name"]
            if rx["pos"] != rx["size"] or rx["h"].hexdigest() != rx["sha256"]:
                self._dump_fail(conn, rx, "hash-mismatch")
                return
            os.replace(part, final)
            os.utime(final, (rx["mtime"], rx["mtime"]))
        except OSError as e:
            self._dump_fail(conn, rx, "io", type(e).__name__)
            return
        try:
            rx["meta"].unlink()
        except OSError:
            pass
        self.counters["dumps_received"] += 1
        logger.info(P.kv("dump_stored", name=name, size=rx["size"]))
        conn.enqueue(P.P_CONTROL, P.ctrl(P.DUMP_ACK, name=name, ok=True, sha256=rx["sha256"]))

    def _dump_fail(self, conn: LinkConnection, rx: dict, reason: str, detail: str = "") -> None:
        try:
            rx["fh"].close()
        except OSError:
            pass
        if self._dump_rx is rx:
            self._dump_rx = None
        for p in (rx["part"], rx["meta"]):
            try:
                p.unlink()
            except OSError:
                pass
        self._dump_nack(conn, rx["name"], reason, detail)


# --- CLI --------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    e = os.environ.get
    p = argparse.ArgumentParser(prog="smo-link-gateway",
                                description="SMO ground-station gateway (GSG). "
                                            "Flags override the SMO_* environment.")
    p.add_argument("--bind", default=e("SMO_GSG_BIND", "127.0.0.1"),
                   help="TM/TC listeners (and HTTP unless --http-bind)")
    p.add_argument("--http-bind", default=e("SMO_GSG_HTTP_BIND") or None)
    p.add_argument("--tm-port", type=int, default=int(e("SMO_GSG_TM_PORT", "8002")))
    p.add_argument("--tc-port", type=int, default=int(e("SMO_GSG_TC_PORT", "8001")))
    p.add_argument("--http-port", type=int, default=int(e("SMO_GSG_HTTP_PORT", "8080")))
    p.add_argument("--link-bind", default=e("SMO_GSG_LINK_BIND", "0.0.0.0"))
    p.add_argument("--link-port", type=int, default=int(e("SMO_GSG_LINK_PORT", "9100")))
    p.add_argument("--session", default=e("SMO_LINK_SESSION"))
    p.add_argument("--secret", default=None,
                   help="hex secret; DISCOURAGED (visible in ps): use $SMO_LINK_SECRET or a file")
    p.add_argument("--secret-file", default=None)
    p.add_argument("--dump-dir", default=None, help="default: $SMO_DUMP_DIR, mission dump_dir, workspace/dumps")
    p.add_argument("--config-dir", default=e("SMO_CONFIG_DIR", "configs/eosat1"))
    p.add_argument("--allowed-origins", default=e("SMO_GSG_ALLOWED_ORIGINS", ""),
                   help="comma list; empty = same host only")
    p.add_argument("--allowed-hosts", default=e("SMO_GSG_ALLOWED_HOSTS", ""),
                   help="comma list of extra Host names the instructor proxy answers "
                        "(IP literals and localhost always; plus the allowed origins' hosts)")
    p.add_argument("--tc-ttl", type=float, default=float(e("SMO_LINK_TC_TTL_S", str(TC_TTL_S))),
                   help="seconds a TC may wait in the link queue before it is discarded")
    p.add_argument("--log-level", default=e("SMO_LOG_LEVEL", "INFO"))
    return p


def _resolve_dump_dir(explicit: str | None) -> str:
    try:
        from smo_common.dump_store import resolve_dump_dir
        return str(resolve_dump_dir(None, explicit))
    except Exception:  # noqa: BLE001
        return explicit or os.environ.get("SMO_DUMP_DIR") or "workspace/dumps"


def _csv(s: str) -> list[str]:
    return [o.strip() for o in (s or "").split(",") if o.strip()]


def config_from_args(args: argparse.Namespace) -> GatewayConfig:
    if not args.session:
        raise SystemExit("smo-link-gateway: SMO_LINK_SESSION (or --session) is required")
    if args.secret:
        logger.warning(P.kv("secret_on_command_line",
                            message="--secret is visible in ps and shell history; "
                                    "use SMO_LINK_SECRET_FILE"))
    try:
        secret = load_secret(args.secret, args.secret_file)
    except (AuthError, OSError) as e:
        raise SystemExit(f"smo-link-gateway: {e}")
    if not (0 < args.tc_ttl <= 60):
        raise SystemExit("smo-link-gateway: SMO_LINK_TC_TTL_S must be in (0, 60]")
    return GatewayConfig(
        session=args.session, secret=secret, bind=args.bind, http_bind=args.http_bind,
        tm_port=args.tm_port, tc_port=args.tc_port, http_port=args.http_port,
        link_bind=args.link_bind, link_port=args.link_port,
        dump_dir=_resolve_dump_dir(args.dump_dir), config_dir=args.config_dir,
        allowed_origins=_csv(args.allowed_origins), allowed_hosts=_csv(args.allowed_hosts),
        tc_ttl_s=args.tc_ttl)


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    P.setup_logging(args.log_level)
    cfg = config_from_args(args)
    try:
        asyncio.run(Gateway(cfg).run_forever())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
