"""Synthetic recordings for exercising the blind receiver.

Produces a realistic SDR-style capture of an EO-Sat-1 downlink — real CCSDS
TM frames carrying real ECSS packets, coded exactly as ``SpacecraftTX`` codes
them (RS(255,223) blocks, optional conv(7,1/2), ASM), modulated by the
suite's own ``Modulator`` and then passed through every impairment stage of
``BasebandRecorder`` (Doppler S-curve, carrier offset, phase noise, IQ
imbalance, CW interferers, AWGN, 8-bit quantisation...).

The ground truth is returned alongside the samples so a test can score the
blind receiver, but it is **never** given to the receiver.
"""
from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from ..ccsds.asm import attach_asm
from ..ccsds.convolutional import encode as conv_encode
from ..ccsds.reed_solomon import encode as rs_encode
from ..ccsds.tm_frame import TMFrameBuilder
from ..dsp.modulator import Modulator, BITS_PER_SYMBOL, MOD_NAMES
from ..recording.iq_recorder import (BasebandRecorder, ImpairmentConfig,
                                     RecorderConfig, fft_resample,
                                     _normalize_power)

#: The EO-Sat-1 S-band ladder (configs/eosat1/subsystems/ttc.yaml), plus the
#: UHF beacon. Channel bit rate, modulation index, coding.
EOSAT1_TIERS = {
    "SAFE":   dict(bps=1000,   modulation=0, conv=True,  rs=True),
    "LOW":    dict(bps=16000,  modulation=0, conv=True,  rs=True),
    "HIGH":   dict(bps=128000, modulation=1, conv=False, rs=True),
    "BEACON": dict(bps=1000,   modulation=0, conv=True,  rs=True),
}


@dataclass
class SynthTruth:
    """What was actually transmitted — for scoring only."""
    modulation: int
    modulation_name: str
    symbol_rate_hz: float
    info_rate_bps: float
    conv: bool
    rs: bool
    frame_length: int
    coded_frame_bytes: int
    frame_air_time_s: float
    scid: int
    carrier_offset_hz: float
    packets: list = field(default_factory=list)
    n_frames: int = 0


def ecss_packet(apid: int, seq: int, payload: bytes) -> bytes:
    """Minimal ECSS/CCSDS space packet (TM, no secondary header)."""
    word0 = (0 << 13) | (0 << 12) | (0 << 11) | (apid & 0x7FF)
    word1 = (0b11 << 14) | (seq & 0x3FFF)
    return struct.pack(">HHH", word0, word1, len(payload) - 1) + payload


def coded_frame_bytes(frame_length: int, rs: bool, conv: bool) -> int:
    n = frame_length
    if rs:
        n += 32 * ((frame_length + 222) // 223)
    if conv:
        n = 2 * n + 2
    return n


def build_wire_bytes(n_frames: int, frame_length: int = 1115, scid: int = 1,
                     rs: bool = True, conv: bool = True,
                     seed: int = 0) -> tuple[bytes, list[bytes]]:
    """Coded, ASM-attached byte stream of ``n_frames`` TM frames."""
    rng = np.random.default_rng(seed)
    builder = TMFrameBuilder(scid=scid, frame_length=frame_length,
                             fecf_present=True)
    frames, packets, seq = [], [], 0
    while len(frames) < n_frames:
        size = int(rng.integers(20, 240))
        pkt = ecss_packet(0x10 + (seq % 5), seq, rng.integers(
            0, 256, size, dtype=np.uint8).tobytes())
        packets.append(pkt)
        seq += 1
        frames.extend(builder.add_packet(pkt, vcid=0))
    out = bytearray()
    for fr in frames[:n_frames]:
        raw = fr.header.pack() + fr.data
        if fr.fecf is not None:
            raw += struct.pack(">H", fr.fecf)
        if rs:
            coded = bytearray()
            for i in range(0, len(raw), 223):
                coded.extend(rs_encode(raw[i:i + 223]))
            raw = bytes(coded)
        if conv:
            raw = conv_encode(raw)
        out += attach_asm(raw)
    # Only packets wholly inside the transmitted frames count as truth.
    carried = sum(len(f.data) for f in frames[:n_frames])
    kept, used = [], 0
    for p in packets:
        if used + len(p) <= carried:
            kept.append(p)
        used += len(p)
    return bytes(out), kept


class _WireRecorder(BasebandRecorder):
    """BasebandRecorder whose clean baseband is a given wire byte stream."""

    def __init__(self, config: RecorderConfig, wire: bytes,
                 gfsk_h: float = 0.5):
        super().__init__(config)
        self._wire = wire
        self._gfsk_h = gfsk_h

    def _modulate(self) -> np.ndarray:
        cfg = self.cfg
        mod = Modulator(modulation=cfg.mod_index(), sps=cfg.sps_internal,
                        rolloff=cfg.rolloff, gmsk_bt=cfg.gmsk_bt,
                        gfsk_mod_index=self._gfsk_h)
        base = mod.modulate(self._wire)
        n_out = int(round(len(base) / cfg.sps_internal / cfg.symbol_rate_hz
                          * cfg.sample_rate_hz))
        y = fft_resample(base, n_out)
        return _normalize_power(y)


def synth_recording(tier: Optional[str] = "LOW", *, modulation: int = None,
                    info_rate_bps: float = None, conv: bool = None,
                    rs: bool = None, n_frames: int = 6,
                    frame_length: int = 1115, scid: int = 1,
                    sample_rate_hz: float = 250_000.0,
                    snr_db: float = 15.0, carrier_offset_hz: float = 21_000.0,
                    doppler_peak_hz: float = 0.0, lead_in_s: float = 0.3,
                    gfsk_h: float = 0.5, rolloff: float = 0.35,
                    impairments: ImpairmentConfig = None,
                    seed: int = 0) -> tuple[np.ndarray, float, SynthTruth]:
    """Return ``(samples, sample_rate_hz, truth)``.

    ``tier`` picks an EO-Sat-1 rung; any explicit keyword overrides it, so a
    test can also build signals the ladder never flies (8PSK, GFSK, ...).
    """
    t = dict(EOSAT1_TIERS.get(tier or "", EOSAT1_TIERS["LOW"]))
    if modulation is not None:
        t["modulation"] = modulation
    if info_rate_bps is not None:
        t["bps"] = info_rate_bps
    if conv is not None:
        t["conv"] = conv
    if rs is not None:
        t["rs"] = rs
    mod = t["modulation"]
    bps_sym = BITS_PER_SYMBOL.get(mod, 1)
    # The suite's ladder quotes the CHANNEL bit rate (coordinator.py: LOW is
    # 16 kbps BPSK = 16 kBd, a coded frame every 1.28 s), so the code rate
    # does not enter the symbol rate.
    symbol_rate = t["bps"] / bps_sym

    wire, packets = build_wire_bytes(n_frames, frame_length, scid,
                                     t["rs"], t["conv"], seed)
    # Carrier-only lead-in/out (idle bits would carry no ASM) so the capture
    # starts mid-stream, as a real one does.
    rng = np.random.default_rng(seed + 99)
    pad = rng.integers(0, 256, max(1, int(lead_in_s * symbol_rate * bps_sym
                                          / 8)), dtype=np.uint8).tobytes()
    wire_all = pad + wire + pad

    imp = impairments or ImpairmentConfig(
        carrier_offset_hz=carrier_offset_hz,
        doppler_model="leo_scurve" if doppler_peak_hz else "none",
        doppler_peak_hz=doppler_peak_hz, envelope_model="flat",
        phase_noise_model="powerlaw", snr_db=snr_db,
        iq_gain_imbalance_db=0.3, iq_phase_imbalance_deg=1.5,
        dc_offset=0.01, quantization_bits=8)
    if impairments is None:
        imp.snr_db = snr_db
    duration = len(wire_all) * 8 / bps_sym / symbol_rate
    cfg = RecorderConfig(modulation=mod, symbol_rate_hz=symbol_rate,
                         rolloff=rolloff, sps_internal=8,
                         sample_rate_hz=sample_rate_hz, duration_s=duration,
                         random_seed=seed, impairments=imp)
    rec = _WireRecorder(cfg, wire_all, gfsk_h=gfsk_h)
    y = rec.generate()

    coded = coded_frame_bytes(frame_length, t["rs"], t["conv"])
    truth = SynthTruth(
        modulation=mod, modulation_name=MOD_NAMES.get(mod, str(mod)),
        symbol_rate_hz=symbol_rate, info_rate_bps=t["bps"], conv=t["conv"],
        rs=t["rs"], frame_length=frame_length, coded_frame_bytes=coded,
        frame_air_time_s=(coded + 4) * 8 / bps_sym / symbol_rate, scid=scid,
        carrier_offset_hz=imp.carrier_offset_hz, packets=packets,
        n_frames=n_frames)
    return y, sample_rate_hz, truth
