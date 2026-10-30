"""Blind front end: find the signal in a wideband capture and cut it out.

Nothing here knows what was transmitted. From the raw I/Q and the sample
rate alone it:

1. removes receiver DC,
2. estimates the PSD (Welch) and flags narrowband CW lines — spurs,
   birdies, interferers — which would otherwise masquerade as carriers in
   the M-th power tests downstream,
3. finds the occupied band (the strongest contiguous region above the noise
   floor) and measures its centre, 99 % bandwidth and in-band SNR,
4. extracts that band to complex baseband at a chosen output rate with a
   single FFT (shift + brick-wall + resample in one step), notching any CW
   lines that fall inside it.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


@dataclass
class BandEstimate:
    """Where the signal sits in the capture."""
    found: bool
    center_hz: float = 0.0          # offset from the capture's DC
    bandwidth_hz: float = 0.0       # 99 % occupied bandwidth
    snr_db: float = -99.0           # in-band SNR (signal / noise in bandwidth)
    noise_psd: float = 0.0          # per-Hz noise floor (linear, capture units)
    cw_lines_hz: list = field(default_factory=list)
    resolution_hz: float = 0.0


def remove_dc(x: np.ndarray) -> np.ndarray:
    return (x - np.mean(x)).astype(np.complex64)


def welch_psd(x: np.ndarray, fs: float, nfft: int = 4096,
              max_segments: int = 512) -> tuple[np.ndarray, np.ndarray]:
    """Averaged, Hann-windowed periodogram; returns fftshifted (f, psd/Hz)."""
    n = len(x)
    nfft = int(min(nfft, 1 << int(math.floor(math.log2(max(n, 16))))))
    hop = nfft // 2
    n_seg = max(1, (n - nfft) // hop + 1)
    if n_seg > max_segments:            # spread the segments over the capture
        starts = np.linspace(0, n - nfft, max_segments).astype(int)
    else:
        starts = np.arange(n_seg) * hop
    win = np.hanning(nfft).astype(np.float32)
    acc = np.zeros(nfft)
    for s in starts:
        seg = x[s:s + nfft]
        if len(seg) < nfft:
            continue
        acc += np.abs(np.fft.fft(seg * win)) ** 2
    acc /= max(1, len(starts)) * fs * np.sum(win ** 2)
    f = np.fft.fftshift(np.fft.fftfreq(nfft, 1.0 / fs))
    return f, np.fft.fftshift(acc)


def _running_median(v: np.ndarray, w: int) -> np.ndarray:
    w = max(3, w | 1)
    pad = w // 2
    vp = np.pad(v, pad, mode="edge")
    windows = np.lib.stride_tricks.sliding_window_view(vp, w)
    return np.median(windows, axis=1)


def _moving_average(v: np.ndarray, w: int) -> np.ndarray:
    if w <= 1:
        return v
    k = np.ones(w) / w
    return np.convolve(np.pad(v, w // 2, mode="edge"), k, mode="valid")[:len(v)]


def find_band(x: np.ndarray, fs: float, nfft: int = 4096,
              line_threshold_db: float = 10.0,
              detect_threshold_db: float = 3.0) -> BandEstimate:
    """Locate the strongest occupied band in a capture."""
    f, psd = welch_psd(x, fs, nfft)
    nb = len(psd)
    df = fs / nb
    # 1. Narrowband lines: far above a local median, and only a few bins wide.
    #    A suppressed-carrier PSK/FSK spectrum has no such lines; spurs and
    #    CW interferers do.
    local = _running_median(psd, 31)
    hot = psd > local * 10 ** (line_threshold_db / 10)
    lines, cleaned = [], psd.copy()
    i = 0
    while i < nb:
        if hot[i]:
            j = i
            while j + 1 < nb and hot[j + 1]:
                j += 1
            if j - i + 1 <= 4:
                k = i + int(np.argmax(psd[i:j + 1]))
                lines.append(float(f[k]))
                lo, hi = max(0, i - 2), min(nb, j + 3)
                cleaned[lo:hi] = local[lo:hi]
            i = j + 1
        else:
            i += 1

    floor = float(np.median(cleaned))
    smooth = _moving_average(cleaned, max(3, nb // 1024))
    above = smooth > floor * 10 ** (detect_threshold_db / 10)
    # 2. Contiguous regions above the floor; keep the one with most excess power.
    best, best_pow = None, 0.0
    i = 0
    while i < nb:
        if above[i]:
            j = i
            while j + 1 < nb and above[j + 1]:
                j += 1
            p = float(np.sum(np.clip(cleaned[i:j + 1] - floor, 0, None)))
            if p > best_pow and (j - i + 1) >= 2:
                best, best_pow = (i, j), p
            i = j + 1
        else:
            i += 1
    if best is None:
        return BandEstimate(found=False, noise_psd=floor, cw_lines_hz=lines,
                            resolution_hz=df)
    i, j = best
    # Widen generously, then take the 0.5 %..99.5 % excess-power quantiles.
    w = j - i + 1
    lo, hi = max(0, i - w // 2), min(nb, j + w // 2 + 1)
    excess = np.clip(cleaned[lo:hi] - floor, 0, None)
    c = np.cumsum(excess)
    total = c[-1]
    if total <= 0:
        return BandEstimate(found=False, noise_psd=floor, cw_lines_hz=lines,
                            resolution_hz=df)
    q_lo = lo + int(np.searchsorted(c, 0.005 * total))
    q_hi = lo + int(np.searchsorted(c, 0.995 * total))
    bw = max(df, (q_hi - q_lo + 1) * df)
    center = float(np.sum(f[lo:hi] * excess) / total)
    snr = total * df / (floor * bw)
    return BandEstimate(found=True, center_hz=center, bandwidth_hz=bw,
                        snr_db=10 * math.log10(max(snr, 1e-12)),
                        noise_psd=floor / 1.0, cw_lines_hz=lines,
                        resolution_hz=df)


def extract_band(x: np.ndarray, fs: float, center_hz: float,
                 keep_bw_hz: float, fs_out: float,
                 notch_hz: tuple = (), notch_width_hz: float = 0.0,
                 ) -> tuple[np.ndarray, float, float]:
    """Mix ``center_hz`` to DC, brick-wall to ``keep_bw_hz``, resample.

    Done in one FFT: the output spectrum is a window of the input spectrum,
    so the bin spacing is preserved exactly and the true output rate is
    returned alongside (it differs from ``fs_out`` by < 1 bin). The centre
    is quantised to the bin grid; the true shift applied is also returned.
    Returns ``(y, fs_out_actual, center_applied_hz)``.
    """
    n = len(x)
    X = np.fft.fft(x)
    df = fs / n
    n_out = max(16, int(round(n * fs_out / fs)))
    shift = int(round(center_hz / df))
    half_keep = int(min(keep_bw_hz / 2 / df, n_out // 2 - 1, n // 2 - 1))
    Y = np.zeros(n_out, dtype=np.complex128)
    k = np.arange(-half_keep, half_keep + 1)
    src = (k + shift) % n
    Y[k % n_out] = X[src]
    for fn in notch_hz:
        # Notch lines that ended up inside the kept band.
        rel = fn - shift * df
        if abs(rel) <= half_keep * df:
            wb = max(2, int(notch_width_hz / df))
            kk = int(round(rel / df))
            idx = np.arange(kk - wb, kk + wb + 1)
            idx = idx[np.abs(idx) <= half_keep]
            Y[idx % n_out] = 0
    y = np.fft.ifft(Y) * (n_out / n)
    return y.astype(np.complex64), n_out * df, shift * df


def lowpass(x: np.ndarray, fs: float, bw_hz: float) -> np.ndarray:
    """Brick-wall to +/- bw/2 (FFT), same rate."""
    n = len(x)
    X = np.fft.fft(x)
    f = np.fft.fftfreq(n, 1.0 / fs)
    X[np.abs(f) > bw_hz / 2] = 0
    return np.fft.ifft(X).astype(np.complex64)


def estimate_drift(x: np.ndarray, fs: float, bandwidth_hz: float,
                   n_windows: int = 32) -> np.ndarray:
    """Fit the band centre's motion over the capture (Doppler rate).

    Each short window's spectrum is registered against the average
    spectrum by cross-correlation (iterated, re-aligning the average each
    time). Registration uses the whole spectral shape, so flat in-band
    noise cannot bias it — a plain centroid is dragged toward the middle of
    whatever window it is computed over and under-reads the rate by 20 %+
    at moderate SNR. The track is least-squares fitted with a line
    (quadratic for captures long enough to curve). Returns polynomial
    coefficients in Hz vs seconds (``np.polyval``), or a single mean offset
    if no significant drift is seen.
    """
    n = len(x)
    wl = max(1024, n // n_windows)
    if n < 4 * wl:
        return np.array([0.0])
    nw = n // wl
    f = np.fft.fftshift(np.fft.fftfreq(wl, 1.0 / fs))
    df = fs / wl
    # Signal region, and a noise-only ring just outside it but still inside
    # the receiver's cut (+/- 2 bandwidths): outside the cut the spectrum is
    # exactly zero and would read as the floor.
    sel = np.abs(f) <= 1.4 * bandwidth_hz
    noise_sel = (np.abs(f) > 1.5 * bandwidth_hz) & (np.abs(f) < 1.95
                                                     * bandwidth_hz)
    win = np.hanning(wl)
    k_s = max(1, int(bandwidth_hz / 50 / df))
    rows, t = [], []
    for i in range(nw):
        seg = x[i * wl:(i + 1) * wl]
        P = np.fft.fftshift(np.abs(np.fft.fft(seg * win)) ** 2)
        floor = np.median(P[noise_sel]) if np.any(noise_sel) else \
            np.median(P)
        e = np.convolve(P[sel] - floor, np.ones(k_s) / k_s, mode="same")
        rows.append(np.clip(e, 0, None))
        t.append((i + 0.5) * wl / fs)
    rows, t = np.array(rows), np.array(t)
    # Windows without the signal (before AOS, after LOS, a PA switched off)
    # carry no information about its frequency — and registering noise
    # against the reference gives an arbitrary shift. Use only windows
    # holding a fair share of the signal energy, weighted by it.
    energy = rows.sum(axis=1)
    keep = energy > 0.25 * np.median(energy[energy > 0]) if np.any(
        energy > 0) else np.zeros(len(energy), bool)
    if np.sum(keep) < 4:
        return np.array([0.0])
    rows, t, energy = rows[keep], t[keep], energy[keep]
    nw = len(rows)
    fsel = f[sel]
    m = len(fsel)
    nfft = 1 << int(math.ceil(math.log2(2 * m)))
    shifts = np.zeros(nw)
    ref = rows.mean(axis=0)
    for _ in range(3):
        R = np.conj(np.fft.fft(ref, nfft))
        for i in range(nw):
            xc = np.real(np.fft.ifft(np.fft.fft(rows[i], nfft) * R))
            k = int(np.argmax(xc))
            a, b, c = xc[(k - 1) % nfft], xc[k], xc[(k + 1) % nfft]
            den = a - 2 * b + c
            kf = k + (0.5 * (a - c) / den if den != 0 else 0.0)
            if kf > nfft / 2:
                kf -= nfft
            shifts[i] = kf * df
        aligned = [np.interp(fsel, fsel - sh, r, left=0, right=0)
                   for r, sh in zip(rows, shifts)]
        ref = np.mean(aligned, axis=0)
    base = float(np.sum(fsel * ref) / (np.sum(ref) + 1e-30))
    c = shifts - np.mean(shifts) + base
    span_s = t[-1] - t[0]
    max_deg = 1 if span_s <= 4.0 or nw < 12 else (2 if span_s <= 20.0 else 3)
    w = np.sqrt(energy / energy.max())
    coef = _robust_polyfit(t, c, w, max_deg)
    resid = c - np.polyval(coef, t)
    span = abs(np.polyval(coef, t[-1]) - np.polyval(coef, t[0]))
    if span < 3 * (np.std(resid) + 1e-9) / math.sqrt(nw) or span < df:
        return np.array([float(np.mean(c))])
    return coef


def _robust_polyfit(t, c, w, max_deg):
    """Weighted polynomial fit with outlier rejection and a BIC choice of
    degree: a higher-order term is kept only if it earns its place, since
    a spurious cubic extrapolates wildly at the ends of a chunk."""
    best = None
    for deg in range(1, max_deg + 1):
        m = np.ones(len(t), bool)
        for _ in range(3):
            if np.sum(m) <= deg + 2:
                break
            co = np.polyfit(t[m], c[m], deg, w=w[m])
            r = c - np.polyval(co, t)
            mad = np.median(np.abs(r[m])) + 1e-9
            m_new = np.abs(r) < 4 * 1.4826 * mad
            if np.array_equal(m_new, m):
                break
            m = m_new
        r = (c - np.polyval(co, t))[m]
        n = int(np.sum(m))
        bic = n * math.log(np.mean(r ** 2) + 1e-12) + (deg + 1) * \
            math.log(max(n, 2))
        if best is None or bic < best[0] - 2.0:
            best = (bic, co)
    return best[1]


def remove_drift(x: np.ndarray, fs: float, coef: np.ndarray) -> np.ndarray:
    """Mix out the time-varying frequency described by ``coef``."""
    if len(coef) == 0 or (len(coef) == 1 and float(coef[0]) == 0.0):
        return x
    t = np.arange(len(x)) / fs
    integ = np.polyint(coef)
    phase = 2 * math.pi * np.polyval(integ, t)
    return (x * np.exp(-1j * phase)).astype(np.complex64)


def refine_drift_mth_power(x: np.ndarray, fs: float, bandwidth_hz: float,
                           n_sub: int = 8, min_strength: float = 30.0):
    """Residual Doppler rate from the drift of an M-th power line.

    For M in (2, 4, 8), find the M-th power line near DC in ``n_sub``
    sub-windows; if it is clearly present in most of them, least-squares
    fit its frequency against time and return that residual track (Hz vs
    s, divided by M) as polynomial coefficients. Returns None for signals
    with no M-th power line (FSK/GMSK) or no measurable drift.
    """
    n = len(x)
    wl = n // n_sub
    if wl < 256:
        return None
    x = x / (np.sqrt(np.mean(np.abs(x) ** 2)) + 1e-30)
    best = None
    for m in (2, 4, 8):
        nfft = 1 << int(math.ceil(math.log2(wl * 4)))
        f = np.fft.fftfreq(nfft, 1.0 / fs)
        # Narrow: the carrier line only. Wider and a cyclic side-line
        # (pi/4-DQPSK: 4f0 +/- Rs/2) is taken for it.
        near = np.abs(f) <= m * 0.03 * bandwidth_hz
        idx = np.nonzero(near)[0]
        t, fr, st = [], [], []
        win = np.hanning(wl)
        for i in range(n_sub):
            seg = x[i * wl:(i + 1) * wl] ** m
            S = np.abs(np.fft.fft(seg * win, nfft)) ** 2
            k = int(idx[np.argmax(S[idx])])
            a, b, c = S[(k - 1) % nfft], S[k], S[(k + 1) % nfft]
            den = a - 2 * b + c
            kf = k + (0.5 * (a - c) / den if den != 0 else 0.0)
            ff = (kf if kf < nfft / 2 else kf - nfft) * fs / nfft
            t.append((i + 0.5) * wl / fs)
            fr.append(ff / m)
            st.append(b / (np.median(S[idx]) + 1e-30))
        st = np.array(st)
        good = st > min_strength
        if np.sum(good) < max(4, n_sub // 2):
            continue
        score = float(np.median(st[good]))
        if best is None or score > best[0]:
            tt, ff = np.array(t)[good], np.array(fr)[good]
            coef = np.polyfit(tt, ff, 1)
            best = (score, coef)
    if best is None:
        return None
    coef = best[1]
    if abs(coef[0]) * (n / fs) < fs / n * 2:     # no drift worth removing
        return np.array([float(coef[1] + coef[0] * n / fs / 2)])
    return coef
