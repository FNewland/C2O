"""smo-link v2 wire protocol: frame codec, constants, control messages.

Every WebSocket *binary* message is exactly one frame (LINK_DESIGN §3.1)::

    byte 0      ver:4 | type:4      (version 2)
    byte 1      flags               bit0 FIN, bit1 GAP, bit2 RESUMED, bit3 TEXT, bit4 CONT
    bytes 2-3   stream  u16 BE
    bytes 4-7   seq     u32 BE      per-stream, per-direction, wraps
    payload     0 .. MAX_FRAME-8 bytes
    tag         16 bytes            truncated HMAC-SHA256 (channel.py); every
                                    frame after the mutual handshake carries it

The three handshake frames (CHALLENGE, AUTH, AUTH_OK) are the only frames
without a tag. Text WebSocket messages are invalid on the link.
"""
from __future__ import annotations

import json
import logging
import struct
from typing import Any, NamedTuple

VERSION = 2
HEADER = struct.Struct(">BBHI")
HEADER_SIZE = HEADER.size  # 8

#: Maximum frame size including the 8-byte header (the 16-byte tag comes on top).
MAX_FRAME = 64 * 1024
MAX_PAYLOAD = MAX_FRAME - HEADER_SIZE
#: Bulk data (proxy bodies, dumps) is chunked at this size.
CHUNK = 16 * 1024
#: TM coalescing: flush when this many bytes are pending ...
TM_COALESCE_BYTES = 32 * 1024
#: ... or after this many seconds.
TM_COALESCE_S = 0.020

# Frame types
DATA = 0x1
OPEN = 0x2
CLOSE = 0x3
WINDOW = 0x4
CTRL = 0x5
PING = 0x6
PONG = 0x7
TYPE_NAMES = {DATA: "DATA", OPEN: "OPEN", CLOSE: "CLOSE", WINDOW: "WINDOW",
              CTRL: "CTRL", PING: "PING", PONG: "PONG"}

# Flags
FIN = 0x01
GAP = 0x02
RESUMED = 0x04
TEXT = 0x08      # nested WebSocket: text message
CONT = 0x10      # TM: frame starts in the middle of a record (oversized record)

# Streams
S_CONTROL = 0
S_TC = 1
S_TM = 2
S_STATE = 3
S_DUMP = 4
PROXY_FIRST = 256
PROXY_LAST = 0xFFFF

# Writer priorities (1 = highest), LINK_DESIGN §3.8
P_CONTROL = 1
P_TC = 2
P_TM = 3
P_STATE = 4
P_PROXY = 5
P_DUMP = 6
PRIORITIES = (P_CONTROL, P_TC, P_TM, P_STATE, P_PROXY, P_DUMP)

#: Proxy stream credit window (bytes).
PROXY_WINDOW = 256 * 1024

# Control message types (CTRL JSON "type")
CHALLENGE = "CHALLENGE"     # GSG -> agent, unauthenticated: {nonce_g, gsg_id}
AUTH = "AUTH"               # agent -> GSG, unauthenticated: {nonce_a, mac_a}
AUTH_OK = "AUTH_OK"         # GSG -> agent, unauthenticated: {mac_g}
HELLO = "HELLO"
WELCOME = "WELCOME"
REJECT = "REJECT"
NOTICE = "NOTICE"
STATUS = "STATUS"
DUMP_META = "DUMP_META"
DUMP_READY = "DUMP_READY"
DUMP_ACK = "DUMP_ACK"

# WebSocket close codes
WS_CLOSE_SUPERSEDED = 4000
WS_CLOSE_PROTOCOL = 4002
WS_CLOSE_DEAD = 4008
WS_CLOSE_AUTH = 4401        # mutual authentication failed
WS_CLOSE_INTEGRITY = 4403   # a frame failed its MAC (forged, replayed, reordered)
WS_CLOSE_CONFIG = 4409

PROTO = 2

#: Stream 1 (TC) DATA payload = 8-byte GSG wall-clock stamp (u64 microseconds,
#: taken when the GSG accepted the record) + exactly one framed record.
TC_STAMP = struct.Struct(">Q")
MAX_TC_RECORD = MAX_PAYLOAD - TC_STAMP.size - 2
SEQ_MOD = 1 << 32


class ProtocolError(ValueError):
    """A frame could not be decoded."""


class Frame(NamedTuple):
    type: int
    flags: int
    stream: int
    seq: int
    payload: bytes

    def describe(self) -> str:
        """Loggable summary: never includes payload bytes."""
        return (f"type={TYPE_NAMES.get(self.type, self.type)} stream={self.stream} "
                f"seq={self.seq} flags=0x{self.flags:02x} size={len(self.payload)}")


def encode(ftype: int, stream: int, seq: int = 0, payload: bytes = b"",
           flags: int = 0) -> bytes:
    """Encode one frame. Raises ``ValueError`` if it would exceed MAX_FRAME."""
    if ftype not in TYPE_NAMES:
        raise ValueError(f"unknown frame type {ftype}")
    if not 0 <= stream <= 0xFFFF:
        raise ValueError(f"stream out of range: {stream}")
    if len(payload) > MAX_PAYLOAD:
        raise ValueError(f"frame too large: {len(payload) + HEADER_SIZE} > {MAX_FRAME}")
    return HEADER.pack((VERSION << 4) | ftype, flags & 0xFF, stream,
                       seq % SEQ_MOD) + bytes(payload)


def decode(data: bytes) -> Frame:
    """Decode one frame; raises :class:`ProtocolError` on anything invalid."""
    if len(data) < HEADER_SIZE:
        raise ProtocolError(f"short frame ({len(data)} bytes)")
    if len(data) > MAX_FRAME:
        raise ProtocolError(f"oversized frame ({len(data)} bytes)")
    b0, flags, stream, seq = HEADER.unpack_from(data)
    ver, ftype = b0 >> 4, b0 & 0x0F
    if ver != VERSION:
        raise ProtocolError(f"unsupported version {ver}")
    if ftype not in TYPE_NAMES:
        raise ProtocolError(f"unknown frame type {ftype}")
    return Frame(ftype, flags, stream, seq, bytes(data[HEADER_SIZE:]))


# --- JSON helpers -----------------------------------------------------------

def dumps(obj: Any) -> bytes:
    return json.dumps(obj, separators=(",", ":"), allow_nan=False).encode()


def _no_constant(name: str) -> Any:
    raise ValueError(f"non-finite number {name} is not valid JSON")


def loads(payload: bytes) -> Any:
    """Strict JSON: NaN / Infinity are refused (they could not be echoed back
    by :func:`dumps` and used to crash the PING handler)."""
    try:
        return json.loads(payload.decode("utf-8"), parse_constant=_no_constant)
    except (UnicodeDecodeError, ValueError, RecursionError) as e:
        raise ProtocolError(f"bad JSON payload: {e}") from e


def loads_obj(payload: bytes) -> dict:
    """:func:`loads` that also requires a JSON object."""
    m = loads(payload)
    if not isinstance(m, dict):
        raise ProtocolError("JSON payload is not an object")
    return m


def tc_payload(record: bytes, stamp: float) -> bytes:
    return TC_STAMP.pack(int(stamp * 1e6)) + record


def parse_tc_payload(payload: bytes) -> tuple[float, bytes]:
    if len(payload) < TC_STAMP.size:
        raise ProtocolError("TC payload shorter than its stamp")
    return TC_STAMP.unpack_from(payload)[0] / 1e6, payload[TC_STAMP.size:]


def ctrl(msg_type: str, **fields: Any) -> bytes:
    """Encode a CTRL frame on stream 0."""
    body = {"type": msg_type}
    body.update(fields)
    return encode(CTRL, S_CONTROL, 0, dumps(body))


def window_payload(increment: int) -> bytes:
    return struct.pack(">I", increment)


def parse_window(payload: bytes) -> int:
    if len(payload) != 4:
        raise ProtocolError("WINDOW payload must be 4 bytes")
    return struct.unpack(">I", payload)[0]


# --- serial-number arithmetic (RFC 1982 style) ------------------------------

def seq_add(seq: int, n: int) -> int:
    return (seq + n) % SEQ_MOD


def seq_diff(a: int, b: int) -> int:
    """Signed distance a - b in serial-number space."""
    d = (a - b) % SEQ_MOD
    return d - SEQ_MOD if d >= SEQ_MOD // 2 else d


# --- record helpers (2-byte BE length + packet, smo_common framing) ----------

def split_records(buf: bytearray) -> list[bytes]:
    """Pop every complete ``[u16 len][packet]`` record from ``buf``.

    Raises :class:`ProtocolError` on a zero length (the existing readers treat
    that as end of connection, so it must never be forwarded).
    """
    out: list[bytes] = []
    pos = 0
    n = len(buf)
    while n - pos >= 2:
        length = (buf[pos] << 8) | buf[pos + 1]
        if length == 0:
            raise ProtocolError("zero-length record")
        end = pos + 2 + length
        if end > n:
            break
        out.append(bytes(buf[pos:end]))
        pos = end
    if pos:
        del buf[:pos]
    return out


# --- structured logging -----------------------------------------------------

def _fmt(v: Any) -> str:
    s = str(v)
    if s == "" or any(c in s for c in ' "=\n'):
        s = '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    return s


def kv(event: str, **fields: Any) -> str:
    """Render a structured ``event=x k=v`` log line."""
    parts = [f"event={event}"]
    parts.extend(f"{k}={_fmt(v)}" for k, v in fields.items())
    return " ".join(parts)


def setup_logging(level: str = "INFO") -> None:
    import sys
    logging.basicConfig(
        level=getattr(logging, str(level).upper(), logging.INFO),
        stream=sys.stdout,
        format="ts=%(asctime)s level=%(levelname)s logger=%(name)s %(message)s",
    )
