"""VR command requests (docs/VR_INTERFACE_ICD.md §7a): headsets PROPOSE, the Flight Director decides.

A headset team may ask for one of a few deployments (antenna, a solar wing, both wings).
Nothing is ever sent to the spacecraft from here: a request becomes a *proposal* on the
Flight Director's console (the VR requests tab of the log drawer). The Flight Director
sends it through the console's normal commanding (authority, arm-through, verification,
command history) or declines it, and the team is told the outcome on its connection.

Transports, all speaking the same newline/one-message-per-frame JSON as smo-vr/1:

* TCP 8104 (NDJSON) and WebSocket 8105 on the MCS host (cyber range, ``--public``);
* ``/vr/requests`` on the MCS HTTP port, which is what the cloud exposes as
  wss://ops.c2o.live/vr/requests (no sign-in, like the rest of /vr).

Requests are named in smo-vr/1 axes, as the state stream names the wings: smo-vr/1 +Y is
the spacecraft's -Y (VR_INTERFACE_ICD §6), so ``deploy_wing_py`` proposes EPS_DEPLOY_WING
with wing=1. The proposal shows the Flight Director the spacecraft's own name for it.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

logger = logging.getLogger(__name__)

SCHEMA = "smo-vr/1"
DEFAULT_TCP_PORT = 8104
DEFAULT_WS_PORT = 8105
MAX_LINE_BYTES = 4096
WRITE_TIMEOUT_S = 2.0
MIN_GAP_S = 2.0            # one request per connection every 2 s
MAX_PENDING_PER_CLIENT = 3
EXPIRE_S = 15 * 60         # a proposal nobody decided in 15 min (wall clock) lapses
KEEP_DECIDED = 30          # decided proposals kept for the console and for re-connects

# name -> (catalogue command, args, English and French labels in spacecraft axes)
REQUESTS: dict[str, dict] = {
    "deploy_antenna": {"command": "TTC_DEPLOY_ANTENNA", "args": {},
                       "label": {"en": "Deploy the antenna", "fr": "Déployer l'antenne"}},
    "deploy_wing_py": {"command": "EPS_DEPLOY_WING", "args": {"wing": 1},
                       "label": {"en": "Deploy solar wing -Y (the headset's +Y wing)",
                                 "fr": "Déployer l'aile solaire -Y (l'aile +Y du casque)"}},
    "deploy_wing_my": {"command": "EPS_DEPLOY_WING", "args": {"wing": 0},
                       "label": {"en": "Deploy solar wing +Y (the headset's -Y wing)",
                                 "fr": "Déployer l'aile solaire +Y (l'aile -Y du casque)"}},
    "deploy_both_wings": {"command": "EPS_DEPLOY_WING", "args": {"wing": 2},
                          "label": {"en": "Deploy both solar wings",
                                    "fr": "Déployer les deux ailes solaires"}},
}
STATES = ("PENDING", "SENT", "DECLINED", "EXPIRED", "WITHDRAWN")


def _dumps(obj: dict) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


def _clean(s: Any, n: int) -> str:
    return "".join(ch for ch in str(s or "") if ch.isprintable())[:n].strip()


def hello(tcp_port: int | None = None, ws_port: int | None = None) -> dict:
    return {
        "type": "hello", "schema": SCHEMA, "source": "smo-mcs", "channel": "requests",
        "ports": {"tcp": tcp_port, "ws": ws_port},
        "requests": {k: v["label"]["en"] for k, v in REQUESTS.items()},
        "usage": 'send {"type":"request","request":"deploy_antenna","team":"T07","text":"why"}; '
                 "the flight director decides; you get request_ack, then request_update",
    }


@dataclass
class Proposal:
    id: str
    request: str
    team: str
    text: str
    peer: str
    transport: str
    client: int
    created: float                      # wall clock (time.time)
    state: str = "PENDING"
    decided_by: str = ""
    decided_at: Optional[float] = None
    note: str = ""
    tc_seq: Optional[int] = None

    def public(self) -> dict:
        spec = REQUESTS[self.request]
        return {"id": self.id, "request": self.request, "team": self.team, "text": self.text,
                "peer": self.peer, "transport": self.transport, "state": self.state,
                "command": spec["command"], "args": spec["args"], "label": spec["label"],
                "created": self.created, "decided_by": self.decided_by,
                "decided_at": self.decided_at, "note": self.note, "tc_seq": self.tc_seq}

    def update_msg(self) -> dict:
        return {"type": "request_update", "schema": SCHEMA, "id": self.id, "request": self.request,
                "team": self.team, "state": self.state, "note": self.note, "tc_seq": self.tc_seq}


@dataclass
class _Client:
    cid: int
    transport: str
    peer: str
    send: Callable[[str], Awaitable[None]]
    last_request: float = 0.0
    team: str = ""
    ids: list = field(default_factory=list)


class VRRequestDesk:
    """Holds proposals and talks to the headsets. ``on_change(proposals)`` tells the MCS to
    refresh every console; ``log(text)`` writes the console/mission log."""

    def __init__(self, *, host: str = "0.0.0.0", tcp_port: int | None = DEFAULT_TCP_PORT,
                 ws_port: int | None = DEFAULT_WS_PORT,
                 on_change: Optional[Callable[[list], Any]] = None,
                 log: Optional[Callable[[str], None]] = None,
                 clock: Callable[[], float] = time.time):
        self._host = host
        self.tcp_port = tcp_port
        self.ws_port = ws_port
        self._on_change = on_change
        self._log = log
        self._clock = clock
        self._clients: dict[int, _Client] = {}
        self._next_cid = 1
        self._next_id = 1
        self._proposals: dict[str, Proposal] = {}
        self._tcp_server = None
        self._ws_runner = None
        self._expiry_task: Optional[asyncio.Task] = None

    # -- lifecycle -----------------------------------------------------------

    async def start(self) -> None:
        """Open the cyber-range ports (either may be None). A clash is logged, not fatal."""
        if self.tcp_port is not None:
            try:
                self._tcp_server = await asyncio.start_server(
                    self._handle_tcp, self._host, self.tcp_port, limit=MAX_LINE_BYTES)
                if self.tcp_port == 0:
                    self.tcp_port = self._tcp_server.sockets[0].getsockname()[1]
            except OSError as e:
                logger.error("VR requests TCP port %s not opened (%s)", self.tcp_port, e)
                self.tcp_port = None
        if self.ws_port is not None:
            from aiohttp import web
            app = web.Application()
            app.router.add_get("/", self.handle_ws)
            app.router.add_get("/vr/requests", self.handle_ws)
            self._ws_runner = web.AppRunner(app)
            await self._ws_runner.setup()
            try:
                site = web.TCPSite(self._ws_runner, self._host, self.ws_port)
                await site.start()
                if self.ws_port == 0:
                    self.ws_port = site._server.sockets[0].getsockname()[1]
            except OSError as e:
                logger.error("VR requests WebSocket port %s not opened (%s)", self.ws_port, e)
                self.ws_port = None
        self._expiry_task = asyncio.ensure_future(self._expiry_loop())
        logger.info("VR request desk — TCP:%s WS:%s (and /vr/requests on the MCS port)",
                    self.tcp_port, self.ws_port)

    async def stop(self) -> None:
        if self._expiry_task:
            self._expiry_task.cancel()
        if self._tcp_server:
            self._tcp_server.close()
        if self._ws_runner:
            await self._ws_runner.cleanup()

    # -- the console side ----------------------------------------------------

    def proposals(self) -> list[dict]:
        """Pending first (oldest first), then the recently decided (newest first)."""
        ps = list(self._proposals.values())
        pending = sorted((p for p in ps if p.state == "PENDING"), key=lambda p: p.created)
        done = sorted((p for p in ps if p.state != "PENDING"),
                      key=lambda p: p.decided_at or p.created, reverse=True)
        return [p.public() for p in pending + done]

    def summary(self) -> dict:
        return {"connected": len(self._clients),
                "pending": sum(p.state == "PENDING" for p in self._proposals.values()),
                "tcp_port": self.tcp_port, "ws_port": self.ws_port}

    async def decide(self, pid: str, decision: str, *, position: str, note: str = "",
                     tc_seq: Optional[int] = None) -> dict:
        """``decision``: ``sent`` (the console has just sent the command) or ``declined``."""
        p = self._proposals.get(pid)
        if p is None:
            raise KeyError(pid)
        if p.state != "PENDING":
            raise ValueError(f"{pid} is already {p.state}")
        decision = str(decision).lower()
        if decision not in ("sent", "declined"):
            raise ValueError("decision must be 'sent' or 'declined'")
        p.state = "SENT" if decision == "sent" else "DECLINED"
        p.decided_by, p.decided_at = position, self._clock()
        p.note = _clean(note, 200)
        p.tc_seq = int(tc_seq) if tc_seq is not None else None
        self._say(f"VR request {p.id} from {p.team or p.peer} ({REQUESTS[p.request]['command']}) "
                  f"{p.state.lower()} by {position}" + (f": {p.note}" if p.note else ""))
        await self._tell(p)
        self._trim()
        await self._changed()
        return p.public()

    # -- the headset side ----------------------------------------------------

    async def on_text(self, client: _Client, raw) -> None:
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8", "replace")
        try:
            msg = json.loads(raw)
            if not isinstance(msg, dict):
                raise ValueError("not a JSON object")
        except Exception:  # noqa: BLE001
            await self._send(client, {"type": "request_rejected", "reason": "line is not a JSON object"})
            return
        kind = msg.get("type")
        if kind == "status":           # the smo-vr/1 status line is welcome here too; nothing to do
            client.team = _clean(msg.get("team"), 32) or client.team
            return
        if kind == "list":
            mine = [self._proposals[i].update_msg() for i in client.ids if i in self._proposals]
            await self._send(client, {"type": "request_list", "requests": mine})
            return
        if kind == "withdraw":
            p = self._proposals.get(str(msg.get("id", "")))
            if p is None or p.client != client.cid or p.state != "PENDING":
                await self._send(client, {"type": "request_rejected", "id": msg.get("id"),
                                          "reason": "no pending request of yours with that id"})
                return
            p.state, p.decided_at = "WITHDRAWN", self._clock()
            self._say(f"VR request {p.id} withdrawn by {p.team or p.peer}")
            await self._tell(p)
            await self._changed()
            return
        if kind != "request":
            await self._send(client, {"type": "request_rejected",
                                      "reason": "type must be request, withdraw, list or status"})
            return
        name = str(msg.get("request", "")).strip().lower()
        team = _clean(msg.get("team"), 32) or client.team
        if name not in REQUESTS:
            await self._send(client, {"type": "request_rejected", "request": name,
                                      "reason": "unknown request; one of " + ", ".join(REQUESTS)})
            return
        now = self._clock()
        if now - client.last_request < MIN_GAP_S:
            await self._send(client, {"type": "request_rejected", "request": name,
                                      "reason": f"one request every {MIN_GAP_S:g} s"})
            return
        client.last_request = now
        client.team = team or client.team
        for p in self._proposals.values():          # the same ask again: point at the open one
            if p.state == "PENDING" and p.request == name and (p.team or p.peer) == (team or client.peer):
                if p.id not in client.ids:
                    client.ids.append(p.id)
                await self._send(client, {"type": "request_ack", "schema": SCHEMA, "id": p.id,
                                          "request": name, "state": "PENDING", "duplicate": True})
                return
        mine = sum(1 for p in self._proposals.values() if p.client == client.cid and p.state == "PENDING")
        if mine >= MAX_PENDING_PER_CLIENT:
            await self._send(client, {"type": "request_rejected", "request": name,
                                      "reason": f"at most {MAX_PENDING_PER_CLIENT} pending requests"})
            return
        pid = f"R{self._next_id}"
        self._next_id += 1
        p = Proposal(id=pid, request=name, team=team, text=_clean(msg.get("text"), 200),
                     peer=client.peer, transport=client.transport, client=client.cid, created=now)
        self._proposals[pid] = p
        client.ids.append(pid)
        self._say(f"VR request {pid} from {team or client.peer}: {REQUESTS[name]['label']['en']}"
                  + (f" — {p.text}" if p.text else ""))
        await self._send(client, {"type": "request_ack", "schema": SCHEMA, "id": pid,
                                  "request": name, "state": "PENDING"})
        await self._changed()

    # -- transports ----------------------------------------------------------

    def _register(self, transport: str, peer: str, send) -> _Client:
        c = _Client(cid=self._next_cid, transport=transport, peer=peer, send=send)
        self._next_cid += 1
        self._clients[c.cid] = c
        return c

    async def _handle_tcp(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")

        async def send(line: str) -> None:
            writer.write((line + "\n").encode("utf-8"))
            await writer.drain()

        c = self._register("tcp", f"{peer[0]}:{peer[1]}" if peer else "?", send)
        try:
            await send(_dumps(hello(self.tcp_port, self.ws_port)))
            while True:
                try:
                    raw = await reader.readline()
                except (asyncio.LimitOverrunError, ValueError):
                    await self._send(c, {"type": "request_rejected",
                                         "reason": f"line longer than {MAX_LINE_BYTES} B"})
                    continue
                if not raw:
                    break
                if raw.strip():
                    await self.on_text(c, raw)
        except (ConnectionError, asyncio.IncompleteReadError):
            pass
        except Exception as e:  # noqa: BLE001
            logger.debug("VR request TCP client error: %s", e)
        finally:
            self._clients.pop(c.cid, None)
            await self._changed()
            try:
                writer.close()
            except Exception:  # noqa: BLE001
                pass

    async def handle_ws(self, request):
        from aiohttp import WSMsgType, web
        ws = web.WebSocketResponse(heartbeat=10.0, max_msg_size=MAX_LINE_BYTES)
        await ws.prepare(request)
        peer = (request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
                or str(request.remote or "?"))

        async def send(line: str) -> None:
            await ws.send_str(line)

        c = self._register("ws", peer, send)
        try:
            await send(_dumps(hello(self.tcp_port, self.ws_port)))
            await self._changed()
            async for msg in ws:
                if msg.type in (WSMsgType.TEXT, WSMsgType.BINARY):
                    await self.on_text(c, msg.data)
                elif msg.type in (WSMsgType.ERROR, WSMsgType.CLOSE):
                    break
        except Exception as e:  # noqa: BLE001
            logger.debug("VR request WS client error: %s", e)
        finally:
            self._clients.pop(c.cid, None)
            await self._changed()
        return ws

    # -- internals -----------------------------------------------------------

    async def _send(self, client: _Client, obj: dict) -> None:
        try:
            await asyncio.wait_for(client.send(_dumps(obj)), timeout=WRITE_TIMEOUT_S)
        except Exception:  # noqa: BLE001 — a slow or gone client is dropped
            self._clients.pop(client.cid, None)

    async def _tell(self, p: Proposal) -> None:
        """The outcome goes to every connection that asked for it (also after a reconnect,
        when the team asked again or sent ``list``)."""
        for c in list(self._clients.values()):
            if p.id in c.ids or c.cid == p.client:
                await self._send(c, p.update_msg())

    async def _changed(self) -> None:
        if self._on_change is None:
            return
        try:
            r = self._on_change(self.proposals())
            if asyncio.iscoroutine(r):
                await r
        except Exception as e:  # noqa: BLE001
            logger.debug("VR request broadcast failed: %s", e)

    def _say(self, text: str) -> None:
        if self._log:
            try:
                self._log(text)
            except Exception:  # noqa: BLE001
                pass

    def _trim(self) -> None:
        done = sorted((p for p in self._proposals.values() if p.state != "PENDING"),
                      key=lambda p: p.decided_at or p.created)
        for p in done[:-KEEP_DECIDED] if len(done) > KEEP_DECIDED else []:
            self._proposals.pop(p.id, None)

    async def expire(self) -> int:
        now, n = self._clock(), 0
        for p in self._proposals.values():
            if p.state == "PENDING" and now - p.created > EXPIRE_S:
                p.state, p.decided_at, p.note = "EXPIRED", now, "not decided in time"
                n += 1
                self._say(f"VR request {p.id} expired")
                await self._tell(p)
        if n:
            self._trim()
            await self._changed()
        return n

    async def _expiry_loop(self) -> None:
        while True:
            await asyncio.sleep(30)
            try:
                await self.expire()
            except Exception as e:  # noqa: BLE001
                logger.debug("VR request expiry failed: %s", e)
