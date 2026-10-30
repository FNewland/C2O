"""LinkConnection: one WebSocket, many logical streams (LINK_DESIGN §3, §3.8).

* one writer task with strict priority (CONTROL > TC > TM > STATE > PROXY >
  DUMP) that writes only while the transport write buffer is below 64 KiB,
  and seals every frame with the channel's tag (channel.py);
* one reader task that verifies the tag, decodes and dispatches each frame.
  A tag or decode failure (forged, replayed, reordered, malformed) closes the
  link; an exception in an application handler only drops that frame or
  closes that one stream (M2);
* PING every 10 s, link declared dead after 30 s of total silence;
* proxy streams (id >= 256) with 256 KiB credit windows, enforced on receive;
* queue entries may carry a deadline (TC time-to-live): an entry still queued
  past it is discarded, never sent, and reported through ``on_expired``.

The same class runs on both ends (aiohttp client or server WebSocket).
"""
from __future__ import annotations

import asyncio
import logging
import math
import time
from collections import deque
from typing import Any, Awaitable, Callable

import aiohttp
from aiohttp import WSMsgType

from . import protocol as P
from .channel import IntegrityError, SecureChannel
from .clock import ClockEstimator

logger = logging.getLogger("smo_link.mux")

WRITE_HIGH_WATER = 64 * 1024
PING_INTERVAL_S = 10.0
DEAD_AFTER_S = 30.0

FrameHandler = Callable[["LinkConnection", P.Frame], Awaitable[None] | None]
#: Largest reassembled proxy message (nested WebSocket message / body piece).
MAX_MESSAGE = 4 * 1024 * 1024

_buffer_size_warned = False


def _transport_buffer_size(ws: Any) -> int:
    """Bytes queued in the WebSocket transport (0 if it can't be read)."""
    global _buffer_size_warned
    try:
        tr = ws._writer.transport  # aiohttp internals: guarded
        return int(tr.get_write_buffer_size())
    except Exception as e:  # noqa: BLE001
        if not _buffer_size_warned:
            _buffer_size_warned = True
            logger.warning(P.kv("write_buffer_unreadable", error=type(e).__name__,
                                message="transport write-buffer size unavailable: "
                                        "link back-pressure falls back to drain() only"))
        return 0


class StreamClosed(Exception):
    pass


class StreamViolation(Exception):
    """The peer broke a per-stream rule (credit, size): close that stream only."""


class Stream:
    """A proxy stream (id >= 256) with credit-based flow control."""

    def __init__(self, conn: "LinkConnection", sid: int, window: int = P.PROXY_WINDOW):
        self.conn = conn
        self.id = sid
        self.window = window
        self._send_credit = window
        self._credit_event = asyncio.Event()
        self._inbox: asyncio.Queue = asyncio.Queue()
        self._consumed = 0
        #: bytes the peer may still send before it needs more credit from us
        self._rx_budget = window
        self._seq = 0
        self.open_msg: asyncio.Future = asyncio.get_running_loop().create_future()
        self.closed = False
        self.close_info: dict | None = None

    # -- outbound -----------------------------------------------------------
    def send_open(self, msg: dict) -> None:
        self.conn.enqueue(P.P_PROXY, P.encode(P.OPEN, self.id, 0, P.dumps(msg)))

    async def send_data(self, data: bytes, flags: int = 0, fin: bool = False) -> None:
        """Send ``data`` in CHUNK pieces under credit. FIN goes on the last."""
        view = memoryview(data)
        if not len(view):
            await self._send_chunk(b"", flags | (P.FIN if fin else 0))
            return
        for off in range(0, len(view), P.CHUNK):
            piece = bytes(view[off:off + P.CHUNK])
            last = off + P.CHUNK >= len(view)
            await self._send_chunk(piece, flags | (P.FIN if (fin and last) else 0))

    async def _send_chunk(self, piece: bytes, flags: int) -> None:
        while self._send_credit < len(piece):
            if self.closed or self.conn.closed:
                raise StreamClosed(self.id)
            self._credit_event.clear()
            await self._credit_event.wait()
        if self.closed or self.conn.closed:
            raise StreamClosed(self.id)
        self._send_credit -= len(piece)
        self.conn.enqueue(P.P_PROXY, P.encode(P.DATA, self.id, self._seq, piece, flags))
        self._seq = P.seq_add(self._seq, 1)

    def send_close(self, code: int = 0, reason: str = "") -> None:
        if not self.closed:
            self.conn.enqueue(P.P_PROXY, P.encode(P.CLOSE, self.id, 0,
                                                  P.dumps({"code": code, "reason": reason})))
        self._local_close()

    # -- inbound ------------------------------------------------------------
    def _on_frame(self, f: P.Frame) -> None:
        if f.type == P.DATA:
            if self.closed:
                return
            self._rx_budget -= len(f.payload)
            if self._rx_budget < 0:
                raise StreamViolation(f"stream {self.id}: peer exceeded its credit window")
            self._inbox.put_nowait((f.flags, f.payload))
        elif f.type == P.OPEN:
            try:
                msg = P.loads(f.payload)
            except P.ProtocolError:
                msg = {}
            if not self.open_msg.done():
                self.open_msg.set_result(msg)
            else:
                self._inbox.put_nowait(("open", msg))
        elif f.type == P.WINDOW:
            inc = P.parse_window(f.payload)
            if self._send_credit + inc > 4 * self.window:
                raise StreamViolation(f"stream {self.id}: credit beyond the window")
            self._send_credit += inc
            self._credit_event.set()
        elif f.type == P.CLOSE:
            try:
                self.close_info = P.loads(f.payload) if f.payload else {}
            except P.ProtocolError:
                self.close_info = {}
            self._local_close()

    def _local_close(self) -> None:
        if self.closed:
            return
        self.closed = True
        self._inbox.put_nowait(None)
        self._credit_event.set()
        if not self.open_msg.done():
            self.open_msg.set_exception(StreamClosed(self.id))
            self.open_msg.exception()  # mark retrieved
        self.conn._streams.pop(self.id, None)

    async def recv(self) -> tuple[int, bytes] | None:
        """Next ``(flags, payload)`` DATA chunk, or None once closed."""
        item = await self._inbox.get()
        if item is None:
            self._inbox.put_nowait(None)  # sticky
            return None
        if item[0] == "open":
            return await self.recv()
        flags, payload = item
        self._consumed += len(payload)
        if self._consumed >= self.window // 2 and not self.closed:
            self.conn.enqueue(P.P_PROXY, P.encode(P.WINDOW, self.id, 0,
                                                  P.window_payload(self._consumed)))
            self._rx_budget += self._consumed
            self._consumed = 0
        return flags, payload

    async def recv_message(self, max_size: int = MAX_MESSAGE) -> tuple[int, bytes] | None:
        """Reassemble chunks up to FIN: ``(flags_of_first, body)`` or None.
        A message larger than ``max_size`` closes the stream (1009)."""
        parts: list[bytes] = []
        size = 0
        first_flags = None
        while True:
            item = await self.recv()
            if item is None:
                return None
            flags, payload = item
            if first_flags is None:
                first_flags = flags
            size += len(payload)
            if size > max_size:
                logger.warning(P.kv("stream_message_too_large", link=self.conn.name,
                                    stream=self.id, limit=max_size))
                self.send_close(1009, "message too large")
                return None
            parts.append(payload)
            if flags & P.FIN:
                return first_flags, b"".join(parts)


class LinkConnection:
    def __init__(self, ws: Any, name: str, on_frame: FrameHandler,
                 on_stream_open: Callable[[Stream, dict], Awaitable[None]] | None = None,
                 ping_interval: float = PING_INTERVAL_S, dead_after: float = DEAD_AFTER_S,
                 high_water: int = WRITE_HIGH_WATER, *, channel: SecureChannel,
                 on_close: Callable[["LinkConnection"], None] | None = None,
                 on_expired: Callable[["LinkConnection", int, int], None] | None = None):
        if channel is None:
            raise ValueError("a LinkConnection needs the authenticated SecureChannel")
        self.ws = ws
        self.name = name
        self.channel = channel
        self._on_frame = on_frame
        self._on_stream_open = on_stream_open
        self._on_close = on_close
        self._on_expired = on_expired
        self.ping_interval = ping_interval
        self.dead_after = dead_after
        self.high_water = high_water
        self._queues: dict[int, deque] = {p: deque() for p in P.PRIORITIES}
        self._qbytes: dict[int, int] = {p: 0 for p in P.PRIORITIES}
        self._has_data = asyncio.Event()
        self._room = asyncio.Event()
        self._streams: dict[int, Stream] = {}
        self._next_stream = P.PROXY_FIRST
        self._tasks: list[asyncio.Task] = []
        self._stream_tasks: set[asyncio.Task] = set()
        self.clock = ClockEstimator()
        self.closed = False
        self.close_reason = ""
        self._done = asyncio.Event()
        now = time.monotonic()
        self.last_rx = now
        self.connected_at = now
        self.tx_frames = self.rx_frames = self.tx_bytes = self.rx_bytes = 0
        self.dropped_on_close: dict[int, int] = {}
        self.expired: dict[int, int] = {p: 0 for p in P.PRIORITIES}
        self.handler_errors = 0
        self.write_buffer_size = lambda: _transport_buffer_size(self.ws)
        self._last_ping = 0.0
        self._ws_close_task: asyncio.Task | None = None

    # -- lifecycle ----------------------------------------------------------
    def start(self) -> None:
        self._tasks = [asyncio.ensure_future(self._writer()),
                       asyncio.ensure_future(self._reader()),
                       asyncio.ensure_future(self._pinger())]

    async def wait_closed(self) -> None:
        await self._done.wait()

    def abort(self, code: int = 1000, reason: str = "") -> asyncio.Task | None:
        """Synchronously mark the link closed, drop every queued frame, and run
        ``on_close`` (the GSG unbinds and resets its TC clients there) BEFORE
        anything awaits the WebSocket closing handshake, which can take up to
        5 s on a silent peer (H1). Returns the task finishing the WS close."""
        if self.closed:
            return self._ws_close_task
        self.closed = True
        self.close_reason = reason or str(code)
        self.dropped_on_close = {p: len(q) for p, q in self._queues.items() if q}
        for q in self._queues.values():
            q.clear()
        for p in P.PRIORITIES:
            self._qbytes[p] = 0
        self._has_data.set()
        self._room.set()
        for s in list(self._streams.values()):
            s._local_close()
        for t in list(self._stream_tasks):
            t.cancel()
        cur = asyncio.current_task()
        for t in self._tasks:
            if t is not cur:
                t.cancel()
        if self._on_close is not None:
            try:
                self._on_close(self)
            except Exception:  # noqa: BLE001
                logger.exception(P.kv("on_close_failed", link=self.name))
        self._ws_close_task = asyncio.ensure_future(self._finish_ws_close(code, reason))
        return self._ws_close_task

    async def _finish_ws_close(self, code: int, reason: str) -> None:
        try:
            await asyncio.wait_for(self.ws.close(code=code, message=reason.encode()[:120]), 5)
        except Exception:  # noqa: BLE001
            pass
        finally:
            self._done.set()

    async def close(self, code: int = 1000, reason: str = "") -> None:
        task = self.abort(code, reason)
        if task is not None and task is not asyncio.current_task():
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError:
                if not task.done():
                    raise

    def spawn(self, coro: Awaitable) -> asyncio.Task:
        """Run a per-connection task, cancelled when the link closes."""
        t = asyncio.ensure_future(coro)
        self._stream_tasks.add(t)
        t.add_done_callback(self._stream_tasks.discard)
        return t

    # -- writer -------------------------------------------------------------
    def enqueue(self, prio: int, frame: bytes, deadline: float | None = None) -> bool:
        """Queue ``frame``. With ``deadline`` (``time.monotonic()`` value) the
        frame is discarded instead of sent if it is still queued after it."""
        if self.closed:
            return False
        self._queues[prio].append((frame, deadline))
        self._qbytes[prio] += len(frame)
        self._has_data.set()
        return True

    def queued_bytes(self, prio: int) -> int:
        return self._qbytes[prio]

    def queued_frames(self, prio: int) -> int:
        return len(self._queues[prio])

    async def wait_room(self, prio: int, limit: int) -> None:
        """Block until fewer than ``limit`` bytes are queued at ``prio``."""
        while not self.closed and self._qbytes[prio] >= limit:
            self._room.clear()
            await self._room.wait()

    def _pop(self) -> bytes | None:
        now = None
        for p in P.PRIORITIES:
            q = self._queues[p]
            expired = 0
            while q:
                frame, deadline = q.popleft()
                self._qbytes[p] -= len(frame)
                self._room.set()
                if deadline is not None:
                    now = time.monotonic() if now is None else now
                    if now > deadline:
                        expired += 1
                        continue
                if expired:
                    self._report_expired(p, expired)
                return frame
            if expired:
                self._report_expired(p, expired)
        return None

    def _report_expired(self, prio: int, n: int) -> None:
        self.expired[prio] += n
        if self._on_expired is not None:
            try:
                self._on_expired(self, prio, n)
            except Exception:  # noqa: BLE001
                logger.exception(P.kv("on_expired_failed", link=self.name))

    async def _writer(self) -> None:
        try:
            while not self.closed:
                # Wait for transport room BEFORE choosing the frame, so the
                # highest priority wins and a TC deadline is checked at the
                # moment it would really be sent.
                while self.write_buffer_size() >= self.high_water and not self.closed:
                    await asyncio.sleep(0.005)
                if self.closed:
                    break
                frame = self._pop()
                if frame is None:
                    self._has_data.clear()
                    await self._has_data.wait()
                    continue
                await self.ws.send_bytes(self.channel.seal(frame))
                self.tx_frames += 1
                self.tx_bytes += len(frame)
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            logger.info(P.kv("link_write_failed", link=self.name, error=type(e).__name__))
            asyncio.ensure_future(self.close(1011, "write failed"))

    # -- reader -------------------------------------------------------------
    async def _reader(self) -> None:
        reason = "closed"
        try:
            async for msg in self.ws:
                if msg.type == WSMsgType.BINARY:
                    try:
                        f = P.decode(self.channel.open(msg.data))
                    except IntegrityError as e:
                        # Forged, replayed, reordered or truncated: never act on
                        # it and never trust anything after it.
                        logger.error(P.kv("frame_rejected", link=self.name, error=str(e)))
                        reason = "integrity failure"
                        await self.close(P.WS_CLOSE_INTEGRITY, reason)
                        return
                    except P.ProtocolError as e:
                        logger.warning(P.kv("bad_frame", link=self.name, error=str(e)))
                        reason = "protocol error"
                        await self.close(P.WS_CLOSE_PROTOCOL, reason)
                        return
                    self.last_rx = time.monotonic()
                    self.rx_frames += 1
                    self.rx_bytes += len(msg.data)
                    await self._dispatch_safe(f)
                elif msg.type == WSMsgType.TEXT:
                    logger.warning(P.kv("text_message_rejected", link=self.name))
                    reason = "text message"
                    await self.close(P.WS_CLOSE_PROTOCOL, reason)
                    return
                elif msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSING, WSMsgType.CLOSED,
                                  WSMsgType.ERROR):
                    break
            code = getattr(self.ws, "close_code", None)
            reason = f"peer closed ({code})"
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            reason = f"read error {type(e).__name__}"
        await self.close(1000, reason)

    async def _dispatch_safe(self, f: P.Frame) -> None:
        """Run one frame's handler. An application error drops that frame
        (or closes that proxy stream); it never closes the link (M2)."""
        try:
            await self._dispatch(f)
        except asyncio.CancelledError:
            raise
        except StreamViolation as e:
            self.handler_errors += 1
            logger.warning(P.kv("stream_violation", link=self.name, stream=f.stream, error=str(e)))
            s = self._streams.get(f.stream)
            if s is not None:
                s.send_close(1008, "flow-control violation")
        except Exception as e:  # noqa: BLE001
            self.handler_errors += 1
            logger.warning(P.kv("frame_handler_error", link=self.name, frame=f.describe(),
                                error=type(e).__name__, detail=str(e)[:160]))
            if f.stream >= P.PROXY_FIRST:
                s = self._streams.get(f.stream)
                if s is not None:
                    s.send_close(1011, "handler error")

    async def _dispatch(self, f: P.Frame) -> None:
        if f.type == P.PING:
            t2 = time.time()
            try:
                t1 = P.loads_obj(f.payload).get("t1")
                if not isinstance(t1, (int, float)) or isinstance(t1, bool):
                    return
            except P.ProtocolError:
                return
            self.enqueue(P.P_CONTROL, P.encode(
                P.PONG, P.S_CONTROL, 0, P.dumps({"t1": t1, "t2": t2, "t3": time.time()})))
            return
        if f.type == P.PONG:
            t4 = time.time()
            try:
                m = P.loads_obj(f.payload)
                ts = [float(m["t1"]), float(m["t2"]), float(m["t3"])]
                if all(math.isfinite(x) for x in ts):
                    self.clock.add_sample(ts[0], ts[1], ts[2], t4)
            except (P.ProtocolError, KeyError, TypeError, ValueError):
                pass
            return
        if f.stream >= P.PROXY_FIRST:
            s = self._streams.get(f.stream)
            if s is None:
                if f.type == P.OPEN and self._on_stream_open is not None:
                    s = Stream(self, f.stream)
                    self._streams[f.stream] = s
                    try:
                        msg = P.loads_obj(f.payload)
                    except P.ProtocolError:
                        msg = {}
                    s.open_msg.set_result(msg)
                    self.spawn(self._run_stream(s, msg))
                elif f.type not in (P.CLOSE, P.WINDOW):
                    # Unknown stream: tell the peer it's gone.
                    self.enqueue(P.P_PROXY, P.encode(P.CLOSE, f.stream, 0,
                                                     P.dumps({"code": 1011, "reason": "no such stream"})))
                return
            s._on_frame(f)
            return
        res = self._on_frame(self, f)
        if asyncio.iscoroutine(res):
            await res

    async def _run_stream(self, s: Stream, msg: dict) -> None:
        try:
            await self._on_stream_open(s, msg)
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            logger.warning(P.kv("stream_handler_error", link=self.name, stream=s.id,
                                error=type(e).__name__))
        finally:
            if not s.closed:
                s.send_close(0, "done")

    # -- streams ------------------------------------------------------------
    def open_stream(self) -> Stream:
        for _ in range(P.PROXY_LAST - P.PROXY_FIRST + 1):
            sid = self._next_stream
            self._next_stream = sid + 1 if sid < P.PROXY_LAST else P.PROXY_FIRST
            if sid not in self._streams:
                s = Stream(self, sid)
                self._streams[sid] = s
                return s
        raise RuntimeError("no free proxy stream ids")

    @property
    def stream_count(self) -> int:
        return len(self._streams)

    # -- liveness -----------------------------------------------------------
    def send_ping(self) -> None:
        self._last_ping = time.monotonic()
        self.enqueue(P.P_CONTROL, P.encode(P.PING, P.S_CONTROL, 0, P.dumps({"t1": time.time()})))

    def silence(self) -> float:
        return time.monotonic() - self.last_rx

    async def _pinger(self) -> None:
        self.send_ping()
        while not self.closed:
            await asyncio.sleep(min(self.ping_interval, 1.0))
            if self.silence() > self.dead_after:
                logger.warning(P.kv("link_dead", link=self.name, silence_s=round(self.silence(), 1)))
                await self.close(P.WS_CLOSE_DEAD, "dead")
                return
            if time.monotonic() - self._last_ping >= self.ping_interval:
                self.send_ping()

    def stats(self) -> dict:
        return {"tx_frames": self.tx_frames, "rx_frames": self.rx_frames,
                "tx_bytes": self.tx_bytes, "rx_bytes": self.rx_bytes,
                "streams": len(self._streams),
                "queued": {p: len(q) for p, q in self._queues.items()},
                "expired": {p: n for p, n in self.expired.items() if n},
                "handler_errors": self.handler_errors,
                "tx_counter": self.channel.tx_counter, "rx_counter": self.channel.rx_counter}


def client_timeout() -> aiohttp.ClientTimeout:
    return aiohttp.ClientTimeout(total=None, sock_connect=10)
