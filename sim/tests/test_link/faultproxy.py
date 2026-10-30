"""Asyncio TCP fault-injection proxy for the smo-link end-to-end tests.

Byte-transparent, so it carries plain TCP, HTTP and WebSocket alike. It sits
between the agent and the GSG ``/link`` port and can impose:

* a fixed one-way ``latency`` plus uniform ``jitter`` (+/-), applied to each
  direction independently and without reordering (TCP is a byte stream: a
  chunk is never delivered before the one read ahead of it);
* a ``bandwidth`` cap in bytes/s per direction (serialisation delay);
* ``cut()``: abort every live connection with RST (SO_LINGER 0) and, while
  cut, accept-and-reset new connects, so dialers fail fast;
* ``blackhole(True)``: keep connections open but silently drop every byte,
  the way a dead route looks to both ends;
* ``restore()``: clear cut and blackhole.

Settings can be changed while traffic flows; they apply to chunks read after
the change. ``stats`` counts connections and bytes per direction.
"""
from __future__ import annotations

import asyncio
import random
import socket
import struct
import time
from dataclasses import dataclass, field

READ_CHUNK = 65536
BW_CHUNK = 4096          # smaller reads when a bandwidth cap is on, for smooth pacing


def _abort(writer: asyncio.StreamWriter | None) -> None:
    """RST, not FIN: SO_LINGER 0 then abort the transport."""
    if writer is None:
        return
    try:
        sock = writer.get_extra_info("socket")
        if sock is not None:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
    except OSError:
        pass
    writer.transport.abort()


@dataclass
class ProxyStats:
    connections: int = 0
    refused: int = 0
    active: int = 0
    bytes_up: int = 0          # client -> target
    bytes_down: int = 0        # target -> client
    dropped_up: int = 0        # bytes discarded by blackhole/cut
    dropped_down: int = 0
    cuts: int = 0


@dataclass(eq=False)
class _Pair:
    client: asyncio.StreamWriter
    target: asyncio.StreamWriter
    tasks: list = field(default_factory=list)
    closed: bool = False


class FaultProxy:
    def __init__(self, target_host: str, target_port: int, *, listen_host: str = "127.0.0.1",
                 listen_port: int = 0, latency: float = 0.0, jitter: float = 0.0,
                 bandwidth: float | None = None, seed: int | None = None):
        self.target_host = target_host
        self.target_port = target_port
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.latency = latency
        self.jitter = jitter
        self.bandwidth = bandwidth
        self._rng = random.Random(seed)
        self._cut = False
        self._blackhole = False
        self._pairs: set[_Pair] = set()
        self._server: asyncio.AbstractServer | None = None
        self.stats = ProxyStats()
        self.port = 0

    # -- control ------------------------------------------------------------
    async def start(self) -> "FaultProxy":
        self._server = await asyncio.start_server(self._accept, self.listen_host, self.listen_port)
        self.port = self._server.sockets[0].getsockname()[1]
        return self

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
        for p in list(self._pairs):
            self._close_pair(p, abort=True)
        if self._server is not None:
            try:
                await asyncio.wait_for(self._server.wait_closed(), 2)
            except asyncio.TimeoutError:
                pass

    def set(self, *, latency: float | None = None, jitter: float | None = None,
            bandwidth: float | None | str = "keep") -> None:
        if latency is not None:
            self.latency = latency
        if jitter is not None:
            self.jitter = jitter
        if bandwidth != "keep":
            self.bandwidth = bandwidth  # type: ignore[assignment]

    def cut(self) -> int:
        """Reset every live connection and refuse new ones until restore()."""
        self._cut = True
        self.stats.cuts += 1
        n = 0
        for p in list(self._pairs):
            self._close_pair(p, abort=True)
            n += 1
        return n

    def blackhole(self, on: bool = True) -> None:
        self._blackhole = on

    def restore(self) -> None:
        self._cut = False
        self._blackhole = False

    @property
    def is_cut(self) -> bool:
        return self._cut

    @property
    def active(self) -> int:
        return len(self._pairs)

    # -- data path ----------------------------------------------------------
    async def _accept(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        if self._cut:
            self.stats.refused += 1
            _abort(writer)
            return
        try:
            t_reader, t_writer = await asyncio.open_connection(self.target_host, self.target_port)
        except OSError:
            self.stats.refused += 1
            _abort(writer)
            return
        if self._cut:  # cut while we were dialling
            _abort(writer)
            _abort(t_writer)
            return
        self.stats.connections += 1
        pair = _Pair(writer, t_writer)
        self._pairs.add(pair)
        self.stats.active = len(self._pairs)
        pair.tasks = [asyncio.ensure_future(self._pipe(pair, reader, t_writer, "up")),
                      asyncio.ensure_future(self._pipe(pair, t_reader, writer, "down"))]

    def _close_pair(self, pair: _Pair, abort: bool) -> None:
        if pair.closed:
            return
        pair.closed = True
        self._pairs.discard(pair)
        self.stats.active = len(self._pairs)
        for w in (pair.client, pair.target):
            if abort:
                _abort(w)
            else:
                try:
                    w.close()
                except Exception:  # noqa: BLE001
                    pass
        cur = asyncio.current_task()
        for t in pair.tasks:
            if t is not cur:
                t.cancel()

    def _delay(self) -> float:
        j = self._rng.uniform(-self.jitter, self.jitter) if self.jitter else 0.0
        return max(0.0, self.latency + j)

    async def _pipe(self, pair: _Pair, src: asyncio.StreamReader, dst: asyncio.StreamWriter,
                    direction: str) -> None:
        q: asyncio.Queue = asyncio.Queue()
        sender = asyncio.ensure_future(self._sender(pair, q, dst))
        pair.tasks.append(sender)
        last_deliver = 0.0
        tx_end = 0.0
        try:
            while not pair.closed:
                data = await src.read(BW_CHUNK if self.bandwidth else READ_CHUNK)
                if not data:
                    break
                if self._blackhole or self._cut:
                    if direction == "up":
                        self.stats.dropped_up += len(data)
                    else:
                        self.stats.dropped_down += len(data)
                    continue
                now = time.monotonic()
                if self.bandwidth:
                    tx_end = max(now, tx_end) + len(data) / float(self.bandwidth)
                    base = tx_end
                else:
                    base = now
                deliver = max(base + self._delay(), last_deliver)
                last_deliver = deliver
                q.put_nowait((deliver, data, direction))
        except (ConnectionError, OSError):
            # The peer reset us: pass the reset on rather than a clean FIN.
            self._close_pair(pair, abort=True)
            return
        except asyncio.CancelledError:
            return
        q.put_nowait(None)  # EOF marker: sender half-closes after draining

    async def _sender(self, pair: _Pair, q: asyncio.Queue, dst: asyncio.StreamWriter) -> None:
        try:
            while True:
                item = await q.get()
                if item is None:
                    if dst.can_write_eof():
                        dst.write_eof()
                    else:
                        self._close_pair(pair, abort=False)
                    # Both directions at EOF -> close the pair.
                    if all(t.done() for t in pair.tasks[:2]):
                        self._close_pair(pair, abort=False)
                    return
                deliver, data, direction = item
                wait = deliver - time.monotonic()
                if wait > 0:
                    await asyncio.sleep(wait)
                if pair.closed:
                    return
                if self._blackhole or self._cut:
                    if direction == "up":
                        self.stats.dropped_up += len(data)
                    else:
                        self.stats.dropped_down += len(data)
                    continue
                dst.write(data)
                await dst.drain()
                if direction == "up":
                    self.stats.bytes_up += len(data)
                else:
                    self.stats.bytes_down += len(data)
        except (ConnectionError, OSError):
            self._close_pair(pair, abort=True)
        except asyncio.CancelledError:
            pass
