"""SMO Common — TCP Length-Prefixed Framing.

All TM/TC traffic over TCP uses a 2-byte big-endian length prefix
followed by the raw ECSS/CCSDS packet bytes.

Virtual channel tag (2026-11, alarm-lifecycle)
-----------------------------------------------
The TCP stream stands in for the TM transfer-frame layer, and on a real
downlink the frame header's VCID is what tells the ground a *stored*
(played-back) packet from a *real-time* one: EO-Sat-1 puts real-time TM on
VC0 and S15 packet-store playback on VC1 (configs/eosat1/rfsim.yaml,
manual §11.4.2). A dumped packet is otherwise byte-identical to the
real-time packet it once was, so without that tag the MCS processed a dump
of the alarm store as if the spacecraft were re-living every old
excursion, alarm and value right now.

The tag is an escape in the length word, so a real-time (VC0) record is
unchanged on the wire for every length it could already carry::

    VC0 record:  [u16 len   ][packet]                     len 1..0xFFFE
    VCn record:  [u16 0xFFFF][u8 vcid][u16 len][packet]   n = 1..7

(0xFFFF was a legal 65535-byte record before; no EO-Sat-1 packet comes
within 60 KiB of it.) A reader that understands the tag returns a
:class:`VcPacket` (a ``bytes`` subclass carrying ``.vcid``) for a VCn record
and plain ``bytes`` for VC0, so every relay that does
``frame_packet(read_framed_packet(...))`` — the gateway, the rfsim bridge —
preserves the channel without knowing about it.
Upgrade the simulator, link, rfsim and MCS together: an old reader would
mis-size a VCn record.
"""
import asyncio
import struct
import logging
from typing import Optional

logger = logging.getLogger(__name__)

FRAME_HEADER_SIZE = 2  # 2-byte big-endian length prefix
#: Length word that introduces a virtual-channel tagged record.
VC_ESCAPE = 0xFFFF
#: Largest packet a record can carry (0xFFFF is the VC escape).
MAX_PACKET_SIZE = 0xFFFE
_VC_HDR = struct.Struct('>BH')   # vcid, length — after the escape word

#: Real-time telemetry (also the default for anything untagged).
VC_REALTIME = 0
#: S15 packet-store playback (delayed / stored TM).
VC_PLAYBACK = 1


class VcPacket(bytes):
    """Packet bytes plus the virtual channel they travelled on."""

    vcid: int = VC_REALTIME

    def __new__(cls, data: bytes, vcid: int = VC_REALTIME):
        obj = super().__new__(cls, data)
        obj.vcid = int(vcid)
        return obj

    def __reduce__(self):  # keep the tag through pickling/copying
        return (VcPacket, (bytes(self), self.vcid))


def tag_vc(packet: bytes, vcid: int) -> bytes:
    """Return *packet* tagged with *vcid* (plain bytes for VC0)."""
    vcid = int(vcid)
    if not 0 <= vcid <= 7:
        raise ValueError(f"VCID out of range: {vcid}")
    if vcid == VC_REALTIME:
        return bytes(packet)
    return VcPacket(packet, vcid)


def vcid_of(packet) -> int:
    """The virtual channel *packet* travelled on (0 when untagged)."""
    return int(getattr(packet, "vcid", VC_REALTIME) or VC_REALTIME)


def is_playback(packet) -> bool:
    """True for stored TM played back from an S15 packet store (VC1)."""
    return vcid_of(packet) == VC_PLAYBACK


def frame_packet(packet: bytes, vcid: Optional[int] = None) -> bytes:
    """Wrap a packet with its length prefix (and VC tag when not VC0).

    *vcid* defaults to the tag the packet already carries, so a relay
    forwards a played-back packet on the channel it arrived on.
    """
    vc = vcid_of(packet) if vcid is None else int(vcid)
    length = len(packet)
    if length > MAX_PACKET_SIZE:
        raise ValueError(f"Packet too large: {length} > {MAX_PACKET_SIZE}")
    if vc == VC_REALTIME:
        return struct.pack('>H', length) + bytes(packet)
    if not 0 < vc <= 7:
        raise ValueError(f"VCID out of range: {vc}")
    return struct.pack('>H', VC_ESCAPE) + _VC_HDR.pack(vc, length) + bytes(packet)


async def read_framed_packet(reader: asyncio.StreamReader) -> Optional[bytes]:
    """Read a single length-prefixed packet from an asyncio stream.

    Returns a :class:`VcPacket` for a VC-tagged (playback) record.
    """
    try:
        header = await reader.readexactly(FRAME_HEADER_SIZE)
        length = struct.unpack('>H', header)[0]
        vc = VC_REALTIME
        if length == VC_ESCAPE:
            vc, length = _VC_HDR.unpack(await reader.readexactly(_VC_HDR.size))
            if not 0 <= vc <= 7:
                logger.warning("Invalid VCID in tagged frame: %d", vc)
                return None
        if length == 0 or length > MAX_PACKET_SIZE:
            logger.warning("Invalid frame length: %d", length)
            return None
        data = await reader.readexactly(length)
        return tag_vc(data, vc) if vc else data
    except asyncio.IncompleteReadError:
        return None
    except Exception as e:
        logger.debug("Frame read error: %s", e)
        return None


def deframe_sync(buffer: bytearray) -> list[bytes]:
    """
    Extract complete framed packets from a byte buffer (synchronous).
    Returns list of extracted packets and modifies buffer in-place.
    VC-tagged records come back as :class:`VcPacket`.
    """
    packets = []
    while len(buffer) >= FRAME_HEADER_SIZE:
        length = struct.unpack('>H', buffer[:FRAME_HEADER_SIZE])[0]
        hdr = FRAME_HEADER_SIZE
        vc = VC_REALTIME
        if length == VC_ESCAPE:
            if len(buffer) < hdr + _VC_HDR.size:
                break  # incomplete tag header
            vc, length = _VC_HDR.unpack(buffer[hdr:hdr + _VC_HDR.size])
            hdr += _VC_HDR.size
            if not 0 <= vc <= 7:
                buffer.pop(0)
                continue
        if length == 0 or length > MAX_PACKET_SIZE:
            # Invalid frame — skip 1 byte and try to resync
            buffer.pop(0)
            continue
        total = hdr + length
        if len(buffer) < total:
            break  # incomplete packet, wait for more data
        pkt = bytes(buffer[hdr:total])
        del buffer[:total]
        packets.append(tag_vc(pkt, vc) if vc else pkt)
    return packets
