"""Blind demodulators — one per modulation family, all feed-forward.

Each takes a band-limited, roughly centred signal and a hypothesis
(modulation, symbol rate) and returns *soft* bit streams for every
ambiguity the receiver cannot resolve on its own: the carrier-phase
rotations of an M-PSK constellation, spectral inversion (I/Q swap in the
receiver), Gray versus natural labelling and — for OQPSK — which rail
leads. The sync marker decides between them downstream.

Everything is block-wise and vectorised (no per-sample Python loops), so a
whole recording can be pushed through in batch:

* **timing** — Oerder & Meyr: the phase of the symbol-rate line of
  ``|y|^2`` in each block gives the sampling instant; unwrapped across
  blocks it tracks clock drift and sample-rate error.
* **carrier** — M-th power: a coarse offset from the global line, a
  windowed track of it for Doppler rate, then Viterbi & Viterbi block
  phase estimation for the rest.
* **CPM (FSK/GMSK)** — discriminator, integrate-and-dump; frequency offset
  and Doppler appear as a slowly varying bias and are simply subtracted.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterator

import numpy as np

from ..dsp.modulator import (BITS_PER_SYMBOL, MOD_NAMES, _rrc_taps,
                             constellation_map, pi4_phase_changes)
from .estimators import MOD_BPSK, MOD_QPSK, MOD_8PSK, MOD_OQPSK, \
    MOD_PI4DQPSK, MOD_CPM
from .frontend import extract_band

SPS = 8                 # working samples per symbol


@dataclass
class Variant:
    """One way of reading the demodulated symbols as bits."""
    label: str
    soft: np.ndarray            # one value per bit, > 0 means "0"


@dataclass
class DemodOutput:
    modulation: int
    symbol_rate_hz: float
    bits_per_symbol: int
    n_symbols: int
    symbol_time0_s: float = 0.0        # time of symbol 0 within the input
    evm_snr_db: float = 0.0            # decision-directed SNR estimate
    freq_offset_hz: float = 0.0        # residual carrier offset removed
    symbols: np.ndarray | None = None  # for display/diagnostics
    variants: list = field(default_factory=list)


# ---------------------------------------------------------------------------
#  Shared helpers
# ---------------------------------------------------------------------------

def _fft_conv(x: np.ndarray, h: np.ndarray) -> np.ndarray:
    """'same'-mode linear convolution via FFT."""
    n = len(x) + len(h) - 1
    nfft = 1 << int(math.ceil(math.log2(n)))
    y = np.fft.ifft(np.fft.fft(x, nfft) * np.fft.fft(h, nfft))[:n]
    start = (len(h) - 1) // 2
    return y[start:start + len(x)]


def _interp(y: np.ndarray, pos: np.ndarray) -> np.ndarray:
    """Cubic (Catmull-Rom) interpolation of ``y`` at fractional indices."""
    i = np.floor(pos).astype(np.int64)
    t = pos - i
    n = len(y)
    i0 = np.clip(i - 1, 0, n - 1)
    i1 = np.clip(i, 0, n - 1)
    i2 = np.clip(i + 1, 0, n - 1)
    i3 = np.clip(i + 2, 0, n - 1)
    p0, p1, p2, p3 = y[i0], y[i1], y[i2], y[i3]
    return (p1 + 0.5 * t * (p2 - p0 + t * (2 * p0 - 5 * p1 + 4 * p2 - p3
                                           + t * (3 * (p1 - p2) + p3 - p0))))


def _timing_positions(power: np.ndarray, sps: int,
                      block_symbols: int = 256,
                      offset_frac: float = 0.0) -> np.ndarray:
    """Oerder & Meyr timing: fractional sample index of every symbol.

    ``power`` is a non-negative waveform with a line at the symbol rate
    (``|y|^2``, or a squared rail, or a squared discriminator).
    """
    n_sym = len(power) // sps - 1
    if n_sym < 4:
        return np.zeros(0)
    nb = max(1, n_sym // block_symbols)
    L = nb * block_symbols * sps
    L = min(L, len(power))
    rot = np.exp(-2j * math.pi * np.arange(L) / sps)
    usable = (L // (block_symbols * sps)) * block_symbols * sps
    if usable == 0:
        usable = L
        nb = 1
        blk = L
    else:
        nb = usable // (block_symbols * sps)
        blk = block_symbols * sps
    X = (power[:usable] * rot[:usable]).reshape(nb, blk).sum(axis=1)
    # The maximum-energy instant sits at -arg(X)/2pi of a symbol.
    tau = np.unwrap(-np.angle(X)) / (2 * math.pi)            # symbols
    if nb >= 3:
        k = np.ones(3) / 3
        tau = np.convolve(np.pad(tau, 1, mode="edge"), k, mode="valid")
    centres = (np.arange(nb) + 0.5) * (blk / sps)
    ks = np.arange(n_sym, dtype=np.float64)
    tau_k = np.interp(ks, centres, tau) + offset_frac
    pos = (ks + tau_k) * sps
    return pos[(pos >= 1) & (pos < len(power) - 3)]


def _mth_power_const(ref: np.ndarray, m: int) -> complex:
    c = np.mean(ref ** m)
    return c / abs(c) if abs(c) > 1e-9 else 1.0 + 0j


def _track_frequency(s: np.ndarray, m: int, window: int = 2048,
                     const: complex = 1.0) -> tuple[np.ndarray, float]:
    """Remove the carrier frequency (and its drift) from symbol samples.

    The M-th power line is measured in overlapping windows. Tracking starts
    from the window with the strongest line and walks outwards, each window
    searching only near its neighbour's estimate — so a Doppler ramp of
    many kHz across the chunk is followed without letting a noise peak
    anywhere in the spectrum capture a weak window. Returns (derotated,
    mean offset in cycles/symbol).
    """
    n = len(s)
    if n < 2 * window:
        window = max(64, n // 2)
    hop = window // 2
    starts = list(range(0, max(1, n - window + 1), hop))
    nfw = window * 8
    win = np.hanning(window)
    spectra = np.empty((len(starts), nfw))
    for i, st in enumerate(starts):
        seg = s[st:st + window]
        if len(seg) < window:
            seg = np.pad(seg, (0, window - len(seg)))
        spectra[i] = np.abs(np.fft.fft(seg ** m / const * win, nfw))
    peaks = spectra.max(axis=1) / (np.median(spectra, axis=1) + 1e-30)
    k0 = int(np.argmax(peaks))
    est_bin = np.zeros(len(starts))

    def refine(row, kk):
        a, b, c = row[(kk - 1) % nfw], row[kk % nfw], row[(kk + 1) % nfw]
        den = a - 2 * b + c
        return kk + (0.5 * (a - c) / den if den != 0 else 0.0)

    est_bin[k0] = refine(spectra[k0], int(np.argmax(spectra[k0])))
    # Max drift per hop we follow: 1/64 of the symbol rate (at M-th power).
    lim = max(4, nfw // 64)
    for order in (range(k0 + 1, len(starts)), range(k0 - 1, -1, -1)):
        prev = k0
        for i in order:
            centre = int(round(est_bin[prev]))
            cand = np.arange(centre - lim, centre + lim + 1)
            kk = int(cand[np.argmax(spectra[i][cand % nfw])])
            est_bin[i] = refine(spectra[i], kk)
            prev = i
    # unwrap the circular bin index, convert to cycles/symbol
    est = np.unwrap(est_bin * 2 * math.pi / nfw) * nfw / (2 * math.pi)
    freqs = np.where(est > nfw / 2, est - nfw, est) / nfw / m
    if len(freqs) >= 5:
        pad = np.pad(freqs, 2, mode="edge")
        freqs = np.median(np.lib.stride_tricks.sliding_window_view(pad, 5),
                          axis=1)
    centres = np.array(starts) + window / 2
    f_track = np.interp(np.arange(n), centres, freqs)
    phase = 2 * math.pi * np.cumsum(f_track)
    return s * np.exp(-1j * phase), float(np.mean(f_track))


def _vv_phase(s: np.ndarray, m: int, const: complex,
              block: int = 32) -> np.ndarray:
    """Viterbi & Viterbi block phase recovery (M-fold ambiguity remains)."""
    n = len(s)
    nb = max(1, n // block)
    usable = nb * block
    z = (s[:usable] ** m / const).reshape(nb, block).sum(axis=1)
    if n > usable:
        z = np.append(z, np.sum(s[usable:] ** m / const))
        centres = np.append((np.arange(nb) + 0.5) * block,
                            usable + (n - usable) / 2)
    else:
        centres = (np.arange(nb) + 0.5) * block
    ph = np.unwrap(np.angle(z)) / m
    theta = np.interp(np.arange(n), centres, ph)
    return s * np.exp(-1j * theta)


def soft_bits(symbols: np.ndarray, ref: np.ndarray, bps: int,
              noise_var: float) -> np.ndarray:
    """Max-log LLRs for an arbitrary labelled constellation (>0 means 0)."""
    d2 = np.abs(symbols[:, None] - ref[None, :]) ** 2     # (n, M)
    labels = np.arange(len(ref))
    out = np.empty((len(symbols), bps))
    for b in range(bps):
        bit = (labels >> (bps - 1 - b)) & 1
        d0 = d2[:, bit == 0].min(axis=1)
        d1 = d2[:, bit == 1].min(axis=1)
        out[:, b] = (d1 - d0) / max(noise_var, 1e-6)
    return out.reshape(-1)


def _evm_snr(s: np.ndarray, ref: np.ndarray) -> tuple[float, float]:
    """Decision-directed SNR (dB) and noise variance after normalising."""
    d = np.abs(s[:, None] - ref[None, :])
    nearest = ref[np.argmin(d, axis=1)]
    err = np.mean(np.abs(s - nearest) ** 2) + 1e-12
    return 10 * math.log10(1.0 / err), float(err)


def _normalise(s: np.ndarray) -> np.ndarray:
    return s / (np.sqrt(np.mean(np.abs(s) ** 2)) + 1e-30)


def _resample(xb: np.ndarray, fs_w: float, rs: float,
              sps: int = SPS) -> tuple[np.ndarray, float]:
    """Resample the band to exactly ``sps`` samples per symbol."""
    fs2 = sps * rs
    keep = min(fs_w, fs2) * 0.999
    y, fs2_actual, _ = extract_band(xb, fs_w, 0.0, keep, fs2)
    return y, fs2_actual


# ---------------------------------------------------------------------------
#  Linear modulations
# ---------------------------------------------------------------------------

def _rotations(mod: int) -> list[float]:
    """Carrier-phase rotations left ambiguous by an M-th power loop.

    For BPSK the only one (pi) is a full bit inversion, which the sync
    correlator already detects from the sign of its peak. For QPSK a pi
    rotation is an inversion only under Gray labelling, so all four are
    tried."""
    if mod == MOD_BPSK:
        return [0.0]
    if mod in (MOD_QPSK, MOD_OQPSK):
        return [k * math.pi / 2 for k in range(4)]
    if mod == MOD_8PSK:
        return [k * math.pi / 4 for k in range(8)]
    return [0.0]


def demod_linear(xb: np.ndarray, fs_w: float, mod: int, rs: float,
                 rolloff: float = 0.35) -> DemodOutput:
    y, fs2 = _resample(xb, fs_w, rs)
    sps_eff = fs2 / rs                     # ~SPS (bin-quantised)
    y = _fft_conv(y, _rrc_taps(SPS, rolloff).astype(np.complex128))
    y = _normalise(y)
    bps = BITS_PER_SYMBOL[mod]

    if mod == MOD_OQPSK:
        return _demod_oqpsk(y, rs, sps_eff, bps)

    pos = _timing_positions(np.abs(y) ** 2, SPS)
    if len(pos) < 16:
        return DemodOutput(mod, rs, bps, 0)
    s = _interp(y, pos)

    if mod == MOD_PI4DQPSK:
        # De-rotate the pi/4 per-symbol step: the result is QPSK-like, so a
        # 4th-power line gives the frequency. Differential detection needs
        # no absolute phase.
        k = np.arange(len(s))
        s4 = s * np.exp(-1j * math.pi / 4 * k)
        _, f_off = _track_frequency(s4, 4)
        s = s * np.exp(-2j * math.pi * f_off * k)
        s = _normalise(s)
        out = DemodOutput(mod, rs, bps, len(s), pos[0] / fs2,
                          freq_offset_hz=f_off * rs, symbols=s)
        prods = s[1:] * np.conj(s[:-1])
        for conj in (False, True):
            d = np.angle(np.conj(prods) if conj else prods)
            for gray in (True, False):
                table = np.asarray(pi4_phase_changes(gray))
                # soft value per dibit bit: distance to nearest table entry
                # with bit=0 minus with bit=1 (wrapped)
                diff = np.abs(np.angle(np.exp(1j * (d[:, None]
                                                    - table[None, :]))))
                lab = np.arange(4)
                soft = np.empty((len(d), 2))
                for b in range(2):
                    bit = (lab >> (1 - b)) & 1
                    soft[:, b] = (diff[:, bit == 1].min(axis=1)
                                  - diff[:, bit == 0].min(axis=1))
                out.variants.append(Variant(
                    f"{'conj ' if conj else ''}{'gray' if gray else 'nat'}",
                    soft.reshape(-1)))
        return out

    m = {MOD_BPSK: 2, MOD_QPSK: 4, MOD_8PSK: 8}[mod]
    ref_gray = constellation_map(mod, True)
    const = _mth_power_const(ref_gray, m)
    s, f_off = _track_frequency(s, m, const=const)
    s = _vv_phase(s, m, const)
    s = _normalise(s)
    snr_db, nv = _evm_snr(s, ref_gray)
    out = DemodOutput(mod, rs, bps, len(s), pos[0] / fs2, snr_db,
                      f_off * rs, symbols=s)
    labellings = [("gray", True)] if mod == MOD_BPSK else \
        [("gray", True), ("nat", False)]
    conjs = (False,) if mod == MOD_BPSK else (False, True)
    for conj in conjs:
        base = np.conj(s) if conj else s
        for rot in _rotations(mod):
            r = base * np.exp(1j * rot)
            for lname, gray in labellings:
                ref = constellation_map(mod, gray)
                out.variants.append(Variant(
                    f"{'conj ' if conj else ''}rot{math.degrees(rot):.0f} "
                    f"{lname}", soft_bits(r, ref, bps, nv)))
    return out


def _demod_oqpsk(y: np.ndarray, rs: float, sps_eff: float,
                 bps: int) -> DemodOutput:
    """OQPSK: carrier from the oversampled 4th power, then treat each rail
    as BPSK sampled half a symbol apart. Which rail leads, and the
    rotation, are left to the sync marker."""
    fs2 = sps_eff * rs
    ref = constellation_map(MOD_OQPSK, True)
    const = _mth_power_const(ref, 4)
    # Frequency + phase on the oversampled waveform (x^4 line of OQPSK).
    yd, f_off = _track_frequency(y, 4, window=2048 * SPS, const=const)
    yd = _vv_phase(yd, 4, const, block=32 * SPS)
    half = SPS // 2
    out = DemodOutput(MOD_OQPSK, rs, bps, 0, 0.0,
                      freq_offset_hz=f_off * fs2)
    for rot in _rotations(MOD_OQPSK):
        yr = yd * np.exp(1j * rot)
        # With the M-th power constant removed the constellation sits at
        # 45 deg, i.e. the I and Q rails ARE the axes: each rail is a real
        # BPSK-like PAM whose own squared line gives the timing.
        ya = yr
        pos = _timing_positions(ya.real ** 2, SPS)
        if len(pos) < 16:
            continue
        for lead in (0, 1):          # which rail is on time
            p_i = pos + lead * half
            p_q = pos + (1 - lead) * half
            ok = p_q < len(ya) - 3
            p_i, p_q = p_i[ok], p_q[ok]
            s = (_interp(ya.real, p_i) + 1j * _interp(ya.imag, p_q))
            s = _normalise(s)
            snr_db, nv = _evm_snr(s, ref)
            if out.symbols is None or snr_db > out.evm_snr_db:
                out.symbols, out.evm_snr_db = s, snr_db
                out.n_symbols = len(s)
                out.symbol_time0_s = p_i[0] / fs2
            for conj in (False, True):
                base = np.conj(s) if conj else s
                for gray in (True, False):
                    out.variants.append(Variant(
                        f"{'conj ' if conj else ''}rot{math.degrees(rot):.0f}"
                        f" lead{'IQ'[lead]} {'gray' if gray else 'nat'}",
                        soft_bits(base, constellation_map(MOD_OQPSK, gray),
                                  bps, nv)))
    return out


# ---------------------------------------------------------------------------
#  Continuous-phase (FSK / GFSK / GMSK)
# ---------------------------------------------------------------------------

def demod_cpm(xb: np.ndarray, fs_w: float, rs: float) -> DemodOutput:
    y, fs2 = _resample(xb, fs_w, rs)
    f = np.angle(y[1:] * np.conj(y[:-1]))                  # rad / sample
    # Carrier offset and Doppler appear as a slowly varying bias.
    w = 64 * SPS
    if len(f) > 2 * w:
        bias = np.convolve(np.pad(f, w // 2, mode="edge"),
                           np.ones(w) / w, mode="valid")[:len(f)]
    else:
        bias = np.full(len(f), np.mean(f))
    f0 = float(np.mean(bias))
    f = f - bias
    c = np.convolve(f, np.ones(SPS), mode="same")           # integrate
    pos = _timing_positions(c ** 2, SPS)
    out = DemodOutput(MOD_CPM, rs, 1, 0, freq_offset_hz=f0 * fs2
                      / (2 * math.pi))
    if len(pos) < 16:
        return out
    d = _interp(c, pos)
    scale = np.mean(np.abs(d)) + 1e-12
    d = d / scale
    err = np.mean((np.abs(d) - 1) ** 2) + 1e-9
    out.n_symbols = len(d)
    out.symbol_time0_s = pos[0] / fs2
    out.evm_snr_db = 10 * math.log10(1 / err)
    out.symbols = d.astype(np.complex128)
    # Modulator NRZ: bit 1 -> positive frequency. Soft value > 0 means "0".
    out.variants.append(Variant("fm", -d / err))
    return out


def demodulate(xb: np.ndarray, fs_w: float, mod: int, rs: float,
               rolloff: float = 0.35) -> DemodOutput:
    if mod == MOD_CPM:
        return demod_cpm(xb, fs_w, rs)
    return demod_linear(xb, fs_w, mod, rs, rolloff)


def mod_name(mod: int) -> str:
    return "FSK/GFSK/GMSK" if mod == MOD_CPM else MOD_NAMES.get(mod, str(mod))
