"""Blind framing: coded frame length -> coding scheme -> frame length.

Given the soft bit stream and the ASM positions, work out how the frames
are coded without being told:

* With a lattice, the ASM spacing fixes the *coded* frame size ``C``. Each
  coding option (conv+RS, conv, RS, none — the concatenations CCSDS 131.0
  allows and ``SpacecraftTX`` uses) maps ``C`` to exactly one transfer-frame
  length; decode a frame under each and keep the one whose FECF checks.
* With a single ASM, the length is unknown too: decode a long window after
  the marker and scan for the length at which the RS codewords and the CRC
  all close. RS(255,223) essentially never decodes random data, so an RS
  success is strong evidence on its own.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field

import numpy as np

from reedsolo import ReedSolomonError

from ..ccsds.reed_solomon import _codec as _rs_codec
from .fast_viterbi import decode_soft

CODINGS = ("conv+rs", "conv", "rs", "none")

_CRC_TABLE = []
for _b in range(256):
    _c = _b << 8
    for _ in range(8):
        _c = ((_c << 1) ^ 0x1021) if _c & 0x8000 else (_c << 1)
    _CRC_TABLE.append(_c & 0xFFFF)


def crc16(data: bytes) -> int:
    """CRC-16/CCITT-FALSE, identical to the FECF the TM framer appends."""
    crc = 0xFFFF
    for byte in data:
        crc = ((crc << 8) & 0xFFFF) ^ _CRC_TABLE[((crc >> 8) ^ byte) & 0xFF]
    return crc


def running_crc(data: bytes) -> np.ndarray:
    """CRC of every prefix: out[i] = crc16(data[:i])."""
    out = np.empty(len(data) + 1, dtype=np.int64)
    crc = 0xFFFF
    out[0] = crc
    for i, byte in enumerate(data):
        crc = ((crc << 8) & 0xFFFF) ^ _CRC_TABLE[((crc >> 8) ^ byte) & 0xFF]
        out[i + 1] = crc
    return out


def rs_decode(codeword: bytes) -> bytes | None:
    """RS(255,223) decode, quietly. Blind search decodes many wrong guesses
    on purpose, so a failure here is routine, not worth a log line (the
    suite's ``ccsds.reed_solomon.decode`` warns on every one)."""
    if len(codeword) < 33:
        return None
    try:
        return bytes(_rs_codec.decode(codeword)[0])
    except ReedSolomonError:
        return None


def rs_coded_length(fl: int) -> int:
    return fl + 32 * ((fl + 222) // 223)


def coded_length(fl: int, coding: str) -> int:
    n = rs_coded_length(fl) if "rs" in coding else fl
    return 2 * n + 2 if coding.startswith("conv") else n


def frame_length_for(coded: int, coding: str) -> int | None:
    """Invert ``coded_length`` (None if no frame length fits)."""
    inner = coded
    if coding.startswith("conv"):
        if (coded - 2) % 2:
            return None
        inner = (coded - 2) // 2
    if "rs" not in coding:
        return inner if inner >= 8 else None
    n_blocks = (inner + 254) // 255
    for nb in (n_blocks, n_blocks - 1, n_blocks + 1):
        if nb <= 0:
            continue
        fl = inner - 32 * nb
        if fl > 0 and rs_coded_length(fl) == inner:
            return fl
    return None


def _hard_bytes(soft: np.ndarray) -> bytes:
    bits = (np.asarray(soft) < 0).astype(np.uint8)
    bits = bits[: (len(bits) // 8) * 8]
    return bytes(np.packbits(bits))


def _rs_unwrap(data: bytes, fl: int) -> bytes | None:
    out = bytearray()
    pos, left = 0, fl
    while left > 0:
        k = min(223, left)
        block = data[pos:pos + k + 32]
        if len(block) < k + 32:
            return None
        dec = rs_decode(bytes(block))
        if dec is None:
            return None
        out.extend(dec)
        pos += k + 32
        left -= k
    return bytes(out)


def decode_frame(soft: np.ndarray, start_bit: int, coding: str,
                 fl: int) -> bytes | None:
    """Decode the frame whose ASM starts at ``start_bit``; None on failure."""
    s = start_bit + 32
    C = coded_length(fl, coding)
    seg = soft[s:s + C * 8]
    if len(seg) < C * 8:
        return None
    if coding.startswith("conv"):
        inner = rs_coded_length(fl) if "rs" in coding else fl
        bits = decode_soft(seg[: (inner * 8 + 6) * 2], inner * 8)
        data = bytes(np.packbits(bits))
    else:
        data = _hard_bytes(seg)
    if "rs" in coding:
        return _rs_unwrap(data, fl)
    return data


def fecf_ok(frame: bytes) -> bool:
    return len(frame) >= 8 and crc16(frame[:-2]) == struct.unpack(
        ">H", frame[-2:])[0]


def plausible_header(frame: bytes) -> bool:
    """TM transfer frame version number must be 0 ('00')."""
    return len(frame) >= 6 and (frame[0] >> 6) == 0


@dataclass
class FramingResult:
    coding: str
    frame_length: int
    coded_bytes: int
    fecf: bool
    period_bits: int
    evidence: str
    frames: list = field(default_factory=list)   # (start_bit, bytes, ok)

    @property
    def n_ok(self) -> int:
        return sum(1 for f in self.frames if f[2])

    def header(self) -> dict:
        for _, fr, ok in self.frames:
            if ok and fr and len(fr) >= 6:
                w0 = struct.unpack(">H", fr[:2])[0]
                return {"version": w0 >> 14, "scid": (w0 >> 4) & 0x3FF,
                        "vcid": (w0 >> 1) & 0x7}
        return {}


def _try_known_period(soft, hits, period_bits, max_frames=3,
                      max_extended=48):
    C = period_bits // 8 - 4
    if period_bits % 8 or C < 8:
        return None
    for coding in CODINGS:
        fl = frame_length_for(C, coding)
        if fl is None:
            continue
        frames = []
        for h in hits[:max_frames]:
            fr = decode_frame(soft, h, coding, fl)
            if fr is None:
                frames.append((h, fr, False))
                continue
            frames.append((h, fr, fecf_ok(fr)))
        n_ok = sum(1 for f in frames if f[2])
        if n_ok:
            return FramingResult(coding, fl, C, True, period_bits,
                                 f"FECF valid on {n_ok}/{len(frames)} "
                                 f"frames", frames)
        # RS decoded but no FECF: accept as a frame without an FECF.
        rs_ok = [f for f in frames if f[1] is not None]
        if "rs" in coding and rs_ok and all(plausible_header(f[1])
                                            for f in rs_ok):
            return FramingResult(coding, fl, C, False, period_bits,
                                 "RS codewords valid, no FECF",
                                 [(h, fr, fr is not None)
                                  for h, fr, _ in frames])
    # Marginal link, no FEC: the markers repeat (the lattice is proof enough
    # that this is the signal) but the first few frames all carry a bit
    # error. Keep looking along the lattice for ONE frame that checks.
    if len(hits) > max_frames:
        for coding in CODINGS:
            fl = frame_length_for(C, coding)
            if fl is None:
                continue
            for i, h in enumerate(hits[max_frames:max_extended], max_frames):
                fr = decode_frame(soft, h, coding, fl)
                if fr is not None and fecf_ok(fr):
                    return FramingResult(
                        coding, fl, C, True, period_bits,
                        f"FECF valid on frame {i + 1} of the lattice "
                        f"(marginal link)", [(h, fr, True)])
    return None


def _scan_single(soft, hit, other_hits=(), max_frame=4096):
    """One ASM, unknown length: find (coding, length) that closes.

    An RS success is accepted on its own (random data essentially never
    decodes). A CRC-only closure is not: scanning a few thousand candidate
    lengths against a 16-bit CRC finds a false match a few % of the time,
    so it must be corroborated by another ASM exactly one frame later.
    """
    others = np.asarray(list(other_hits), dtype=np.int64)
    s = hit + 32
    avail = len(soft) - s
    for coding in CODINGS:
        if coding.startswith("conv"):
            n_coded_bits = min(avail, (2 * (max_frame + 16 * 32) + 2) * 8)
            n_steps = n_coded_bits // 2
            if n_steps < 64:
                continue
            bits = decode_soft(soft[s:s + 2 * n_steps], terminated=False)
            data = bytes(np.packbits(bits[: (len(bits) // 8) * 8]))
        else:
            data = _hard_bytes(soft[s:s + min(avail, (max_frame + 600) * 8)])
        if "rs" in coding:
            # Full 255-byte codewords first, then a shortened final block.
            full, out = 0, bytearray()
            while (full + 1) * 255 <= len(data):
                dec = rs_decode(data[full * 255:(full + 1) * 255])
                if dec is None:
                    break
                out.extend(dec)
                full += 1
            base = full * 255
            for r in range(0, 223):
                if r == 0:
                    if full == 0:
                        continue
                    frame = bytes(out)
                else:
                    blk = data[base:base + r + 32]
                    if len(blk) < r + 32:
                        break
                    dec = rs_decode(blk)
                    if dec is None:
                        continue
                    frame = bytes(out) + dec
                if fecf_ok(frame) and plausible_header(frame):
                    fl = len(frame)
                    C = coded_length(fl, coding)
                    return FramingResult(coding, fl, C, True, (C + 4) * 8,
                                         "single ASM: RS + FECF closed",
                                         [(hit, frame, True)])
        else:
            crcs = running_crc(data)
            arr = np.frombuffer(data, dtype=np.uint8).astype(np.int64)
            if len(arr) < 16:
                continue
            tail = (arr[:-1] << 8) | arr[1:]          # value at [i, i+1]
            L = np.arange(16, len(data) + 1)
            match = crcs[L - 2] == tail[L - 2]
            for fl in L[match]:
                frame = data[:fl]
                if plausible_header(frame):
                    C = coded_length(int(fl), coding)
                    nxt = hit + (C + 4) * 8
                    if not np.any(np.abs(others - nxt) <= 1):
                        continue
                    return FramingResult(coding, int(fl), C, True,
                                         (C + 4) * 8,
                                         "single ASM: FECF closed",
                                         [(hit, frame, True)])
    return None


def infer_framing(soft: np.ndarray, sync) -> FramingResult | None:
    """``soft`` must already be polarity-corrected (multiply by sync.sign)."""
    if sync.period_bits:
        res = _try_known_period(soft, sync.aligned, sync.period_bits)
        if res:
            return res
    for h in sync.aligned[:2] or list(sync.positions[:2]):
        res = _scan_single(soft, int(h), sync.positions)
        if res:
            return res
    return None
