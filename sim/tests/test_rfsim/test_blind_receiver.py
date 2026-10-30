"""Blind receiver (v2): decode with no prior knowledge of the signal.

The receiver is handed samples and a sample rate and nothing else. Every
test builds a realistic capture with ``blind.synth`` (the suite's own
framing, coding, modulator and recorder impairments), keeps the ground truth
to itself, and checks what the receiver worked out.

The live v1 receiver (pipeline/rx_chain.py) is untouched by v2; see
test_classic_untouched / test_rf_integration for it.
"""
from __future__ import annotations

import math
import os

import numpy as np
import pytest

from smo_rfsim.blind import BatchBlindDecoder, BlindReceiver
from smo_rfsim.blind import fast_viterbi, framing, frontend, sync
from smo_rfsim.blind.synth import synth_recording
from smo_rfsim.ccsds import convolutional, viterbi
from smo_rfsim.recording.iq_recorder import ImpairmentConfig


def _chirp(y, fs, rate_hz_s):
    t = np.arange(len(y)) / fs
    return (y * np.exp(1j * math.pi * rate_hz_s * t ** 2)).astype(np.complex64)


def _assert_identified(acq, truth, rate_tol=1e-4):
    assert acq.ok, acq.summary() + "\n" + "\n".join(
        f"{t.modulation} {t.symbol_rate_hz}: {t.verdict}" for t in acq.trials)
    d = acq.description
    fam = 7 if truth.modulation in (6, 7) else truth.modulation
    assert d.modulation == fam
    assert abs(d.symbol_rate_hz - truth.symbol_rate_hz) \
        < rate_tol * truth.symbol_rate_hz
    assert d.frame_length == truth.frame_length
    expected = {(True, True): "conv+rs", (True, False): "conv",
                (False, True): "rs", (False, False): "none"}
    assert d.coding == expected[(truth.conv, truth.rs)]
    assert d.scid == truth.scid
    assert abs(d.frame_air_time_s - truth.frame_air_time_s) \
        < 1e-3 * truth.frame_air_time_s


# ---------------------------------------------------------------------------
#  Building blocks
# ---------------------------------------------------------------------------

class TestFastViterbi:
    def test_matches_legacy_decoder_and_corrects_errors(self):
        rng = np.random.default_rng(3)
        data = rng.integers(0, 256, 300, dtype=np.uint8).tobytes()
        enc = convolutional.encode(data)
        assert fast_viterbi.decode_hard(enc, 300) == data
        assert fast_viterbi.decode_hard(enc, 300) == viterbi.decode(enc, 300)
        bits = np.unpackbits(np.frombuffer(enc, np.uint8))
        bits ^= (rng.random(len(bits)) < 0.03).astype(np.uint8)
        assert fast_viterbi.decode_hard(np.packbits(bits).tobytes(),
                                        300) == data

    def test_soft_decisions_beat_hard(self):
        """At Es/N0 ~ 0.5 dB soft decoding still succeeds where hard fails."""
        rng = np.random.default_rng(1)
        soft_ok = hard_ok = 0
        for _ in range(10):
            data = rng.integers(0, 256, 200, dtype=np.uint8).tobytes()
            b = np.unpackbits(np.frombuffer(convolutional.encode(data),
                                            np.uint8))
            y = (1 - 2.0 * b) + rng.normal(0, 0.65, len(b))
            soft_ok += fast_viterbi.decode_soft_bytes(y, 200) == data
            hard_ok += fast_viterbi.decode_hard(
                np.packbits((y < 0).astype(np.uint8)).tobytes(), 200) == data
        assert soft_ok >= 8
        assert soft_ok > hard_ok


class TestFraming:
    @pytest.mark.parametrize("coding", framing.CODINGS)
    def test_coded_length_inverts(self, coding):
        for fl in (223, 892, 1115, 1000, 64):
            c = framing.coded_length(fl, coding)
            assert framing.frame_length_for(c, coding) == fl

    def test_crc_matches_tm_framer(self):
        from smo_common.protocol.ecss_packet import crc16_ccitt
        data = bytes(range(200))
        assert framing.crc16(data) == crc16_ccitt(data)
        rc = framing.running_crc(data)
        assert rc[150] == crc16_ccitt(data[:150])


class TestFrontEnd:
    def test_band_and_cw_line(self):
        imp = ImpairmentConfig(carrier_offset_hz=-40_000,
                               doppler_model="none", envelope_model="flat",
                               snr_db=12, cw_interferers=((60_000, 0.0),),
                               phase_noise_model="none")
        y, fs, truth = synth_recording("LOW", n_frames=2, impairments=imp)
        b = frontend.find_band(frontend.remove_dc(y), fs)
        assert b.found
        assert abs(b.center_hz - (-40_000)) < 300
        assert 0.9 * truth.symbol_rate_hz < b.bandwidth_hz \
            < 1.6 * truth.symbol_rate_hz
        assert any(abs(f - 60_000) < 200 for f in b.cw_lines_hz)

    def test_drift_estimate(self):
        y, fs, _ = synth_recording("LOW", n_frames=4, snr_db=8)
        y = _chirp(y, fs, 800.0)
        rx = BlindReceiver()
        x = frontend.remove_dc(y)
        b = frontend.find_band(x, fs)
        from smo_rfsim.blind.receiver import WIDE_KEEP
        xw, fs_w, _ = rx._extract(x, fs, b, WIDE_KEEP)
        coef = frontend.estimate_drift(xw, fs_w, b.bandwidth_hz)
        slope = np.polyval(np.polyder(coef), len(y) / fs / 2)
        assert abs(slope - 800.0) < 60.0


class TestSync:
    def test_lattice_from_hits(self):
        soft = np.random.default_rng(0).normal(size=40_000)
        pat = sync.ASM_PM * 5
        for p in (1000, 9000, 17000, 33000):       # 25000 missing
            soft[p:p + 32] = pat
        res = sync.analyse(soft)
        assert res.period_bits == 8000
        assert res.n_aligned == 4

    def test_no_marker_in_noise(self):
        soft = np.random.default_rng(1).normal(size=200_000)
        res = sync.analyse(soft)
        assert res.n_aligned <= 1


# ---------------------------------------------------------------------------
#  Acquisition — the flown ladder and beyond
# ---------------------------------------------------------------------------

CASES = {
    "LOW (BPSK 16k conv+RS)": ("LOW", {}),
    "HIGH (QPSK 64 kBd RS)": ("HIGH", {"n_frames": 8}),
    "OQPSK": ("LOW", {"modulation": 3}),
    "8PSK": ("LOW", {"modulation": 2}),
    "pi/4-DQPSK": ("LOW", {"modulation": 5}),
    "GMSK (h=0.5)": ("LOW", {"modulation": 6}),
    "GFSK h=0.35": ("LOW", {"modulation": 7, "gfsk_h": 0.35}),
    "FSK h=1 (tones)": ("LOW", {"modulation": 7, "gfsk_h": 1.0}),
    "QPSK uncoded": ("LOW", {"modulation": 1, "conv": False, "rs": False}),
    "BPSK 9600 conv only": ("LOW", {"info_rate_bps": 9600, "rs": False,
                                    "frame_length": 223}),
}


@pytest.mark.parametrize("name", list(CASES))
def test_acquire_identifies_signal(name):
    tier, kw = CASES[name]
    y, fs, truth = synth_recording(tier, **{"n_frames": 4, "snr_db": 12,
                                            **kw})
    acq = BlindReceiver().acquire(y, fs)
    _assert_identified(acq, truth)
    assert sum(f.ok for f in acq.frames) >= min(3, truth.n_frames - 1)


def test_estimators_put_truth_first_for_the_flown_tiers():
    for tier in ("LOW", "HIGH"):
        y, fs, truth = synth_recording(tier, n_frames=4, snr_db=12)
        acq = BlindReceiver().acquire(y, fs)
        assert acq.ok
        assert len(acq.trials) == 1, [t.modulation for t in acq.trials]


def test_low_snr_soft_decoding():
    """1 dB in-band SNR on the LOW rung — soft Viterbi carries it."""
    y, fs, truth = synth_recording("LOW", n_frames=4, snr_db=1.0)
    acq = BlindReceiver().acquire(y, fs)
    _assert_identified(acq, truth)


@pytest.mark.parametrize("mod", [0, 3])
def test_doppler_ramp(mod):
    """800 Hz/s — about the worst an S-band LEO pass produces near TCA."""
    y, fs, truth = synth_recording("LOW", n_frames=4, snr_db=8,
                                   modulation=mod)
    acq = BlindReceiver().acquire(_chirp(y, fs, 800.0), fs)
    _assert_identified(acq, truth)


def test_inband_cw_interferer_and_clock_error():
    imp = ImpairmentConfig(carrier_offset_hz=-35_000, doppler_model="none",
                           envelope_model="flat", snr_db=10,
                           cw_interferers=((-33_000, -6.0),),
                           sample_clock_ppm=50, phase_noise_model="powerlaw")
    y, fs, truth = synth_recording("LOW", n_frames=4, impairments=imp)
    acq = BlindReceiver().acquire(y, fs)
    assert acq.ok and acq.description.modulation == 0
    assert acq.description.frame_length == truth.frame_length


def test_no_false_acquisition():
    fs = 250_000.0
    rng = np.random.default_rng(7)
    noise = (rng.normal(size=int(2 * fs)) + 1j * rng.normal(
        size=int(2 * fs))).astype(np.complex64)
    assert not BlindReceiver().acquire(noise, fs).ok
    # A clean BPSK carrier of random data — a perfectly good signal with no
    # CCSDS framing in it — must not be "confirmed" either.
    from smo_rfsim.dsp.modulator import Modulator
    from smo_rfsim.recording.iq_recorder import fft_resample
    data = rng.integers(0, 256, 8000, dtype=np.uint8).tobytes()
    base = Modulator(0, sps=8).modulate(data)
    y = fft_resample(base, int(len(base) / 8 / 16000 * fs))
    y = y + 0.1 * (rng.normal(size=len(y)) + 1j * rng.normal(size=len(y)))
    acq = BlindReceiver().acquire(y.astype(np.complex64), fs)
    assert not acq.ok


# ---------------------------------------------------------------------------
#  Batch decoding of a pass
# ---------------------------------------------------------------------------

def test_batch_rate_switch_mid_pass():
    """AOS in noise, LOW, the spacecraft steps to HIGH, LOS in noise.
    Every packet out, two segments, and the switch found where it happened.
    """
    fs = 250_000.0
    rng = np.random.default_rng(5)
    y1, _, t1 = synth_recording("LOW", n_frames=6, snr_db=10,
                                sample_rate_hz=fs, seed=1)
    y2, _, t2 = synth_recording("HIGH", n_frames=40, snr_db=12,
                                sample_rate_hz=fs, seed=2,
                                carrier_offset_hz=24_000)
    p = np.mean(np.abs(y1) ** 2)

    def noise(sec):
        n = int(sec * fs)
        return (np.sqrt(p / 20) * (rng.normal(size=n) + 1j * rng.normal(
            size=n))).astype(np.complex64)
    y = np.concatenate([noise(3), y1,
                        y2 * np.sqrt(p / np.mean(np.abs(y2) ** 2)), noise(2)])
    rep = BatchBlindDecoder().run(y.astype(np.complex64), fs, "switch")
    assert [s.description["modulation_name"] for s in rep.segments] == \
        ["BPSK", "QPSK"]
    want = set(t1.packets) | set(t2.packets)
    assert set(rep.packets) == want
    switch_at = 3 + len(y1) / fs
    assert abs(rep.segments[1].start_s - switch_at) < 1.0
    # Chunk length follows the discovered frame air time (>= 4 frames).
    low_air = rep.segments[0].description["frame_air_time_s"]
    first = rep.chunks[0]
    assert first["end_s"] - first["start_s"] >= min(
        4 * low_air, y.size / fs - first["start_s"]) - 1e-3
    assert rep.lag_stats()["max_s"] > 0


def test_batch_safe_rate_long_frames():
    """SAFE: 1 kBd, a frame every 20.4 s. The acquisition window has to
    grow until markers repeat; chunking follows the 20 s frame, not a
    fixed timeout."""
    y, fs, truth = synth_recording("SAFE", n_frames=5, snr_db=6,
                                   sample_rate_hz=25_000.0)
    y = _chirp(y, fs, 40.0)
    rep = BatchBlindDecoder().run(y, fs, "safe")
    assert len(rep.segments) == 1
    d = rep.segments[0].description
    assert d["symbol_rate_hz"] == pytest.approx(1000.0, rel=1e-4)
    assert d["frame_air_time_s"] == pytest.approx(truth.frame_air_time_s,
                                                  rel=1e-3)
    assert rep.segments[0].acquisition_window_s > truth.frame_air_time_s
    assert set(rep.packets) == set(truth.packets)


def test_cli_roundtrip(tmp_path):
    from smo_rfsim.blind import cli
    assert cli.main(["synth", "--tier", "HIGH", "--frames", "30",
                     "--snr-db", "12", "--doppler-rate", "300",
                     "--out", str(tmp_path), "--name", "hi"]) == 0
    out = tmp_path / "rep.json"
    assert cli.main(["decode", str(tmp_path / "hi.cf32"), "--json",
                     str(out)]) == 0
    import json
    rep = json.loads(out.read_text())
    assert rep["segments"][0]["description"]["modulation_name"] == "QPSK"
    assert rep["frames_ok"] >= 29
