"""Reassemble segmented "report all" TM for tests (R4 G4).

TM(12,13) and TM(19,128) are segmented on the CCSDS grouping flags once the
record count outgrows a 256-octet packet (2026-08-21; see
``TMBuilder.pack_tm_segmented``). Each segment's data field is
``count(u16)`` + that segment's records. :func:`report_body` stitches the
segments of one (service, subtype) back into the single-packet body the
ground decoders expect, checking the flag sequence on the way (11 alone, or
01, 00..., 10) — the same rule as ``smo_mcs.server._reassemble_report``.
"""

from __future__ import annotations

import struct

from smo_common.protocol.ecss_packet import decommutate_packet

STANDALONE, FIRST, CONTINUATION, LAST = 0b11, 0b01, 0b00, 0b10


def report_segments(packets, service: int, subtype: int):
    """Decoded packets of one (service, subtype), in emission order."""
    out = []
    for raw in packets:
        pkt = decommutate_packet(raw)
        if pkt and pkt.secondary and (pkt.secondary.service,
                                      pkt.secondary.subtype) == (service, subtype):
            out.append(pkt)
    return out


def check_flag_sequence(flags: list[int]) -> None:
    """Assert a legal CCSDS grouping sequence for one report."""
    assert flags, "no segments"
    if len(flags) == 1:
        assert flags == [STANDALONE], f"single packet must be standalone, got {flags}"
        return
    assert flags[0] == FIRST, f"first segment flag {flags[0]:02b}, want 01"
    assert flags[-1] == LAST, f"last segment flag {flags[-1]:02b}, want 10"
    assert all(f == CONTINUATION for f in flags[1:-1]), f"bad middle flags {flags}"


def report_body(packets, service: int, subtype: int):
    """One ``count(u16) + records`` body rebuilt from every segment, or None."""
    segs = report_segments(packets, service, subtype)
    if not segs:
        return None
    check_flag_sequence([p.primary.sequence_flags for p in segs])
    total = 0
    records = b""
    for p in segs:
        data = p.data_field
        total += struct.unpack(">H", data[:2])[0]
        records += data[2:]
    return struct.pack(">H", total) + records
