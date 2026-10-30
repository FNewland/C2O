"""Feature-based estimators — the "automatic modulation detection" half.

These never decide anything on their own. They turn a band-limited,
roughly-centred signal into a short, *ranked* list of hypotheses
(modulation, symbol rate, carrier offset) for the verifier to test against
the sync marker. The features are the classical cyclostationary ones:

* **Symbol rate** — a linearly modulated signal's envelope ``|x|^2`` is
  cyclostationary at the symbol rate, so its spectrum has a discrete line at
  ``Rs``. A continuous-phase (FSK/GMSK) signal has a constant envelope and
  no such line, but its *instantaneous frequency* does.
* **Modulation order** — raising M-PSK to the M-th power strips the data
  and leaves a pure tone at ``M * f_offset``. BPSK shows a line at M=2,
  QPSK only at M=4, 8PSK only at M=8. The smallest M that shows a line is
  the order, and the line's position is the carrier offset.
* **OQPSK** — its square has no line at ``2 f0`` (unlike BPSK) but a
  *pair* at ``2 f0 +/- Rs/2`` — the half-symbol stagger made visible.
* **Constant envelope** — the normalised envelope variance, corrected for
  the noise the band estimate predicts, separates CPM from filtered PSK.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Line:
    freq_hz: float
    strength: float           # peak / median of the searched spectrum


@dataclass
class Features:
    fs_hz: float
    n_samples: int
    envelope_lines: list = field(default_factory=list)      # |x|^2
    discriminator_lines: list = field(default_factory=list)  # inst. freq
    power_lines: dict = field(default_factory=dict)          # M -> Line
    oqpsk_twin: Line | None = None                           # sep = Rs
    pi4_twin: Line | None = None
    envelope_variance: float = 0.0     # noise-corrected, normalised
    snr_linear: float = 1.0


def _spectrum(v: np.ndarray, pad: int = 2) -> tuple[np.ndarray, np.ndarray]:
    n = len(v)
    nfft = 1 << int(math.ceil(math.log2(n * pad)))
    win = np.hanning(n)
    S = np.abs(np.fft.fft(v * win, nfft)) ** 2
    return S, np.fft.fftfreq(nfft, 1.0)   # frequency in cycles / sample


def _refine(S: np.ndarray, k: int) -> float:
    """Parabolic interpolation of a spectral peak (bins)."""
    n = len(S)
    a, b, c = S[(k - 1) % n], S[k], S[(k + 1) % n]
    den = a - 2 * b + c
    return k + (0.5 * (a - c) / den if den != 0 else 0.0)


def find_lines(v: np.ndarray, fs: float, fmin: float, fmax: float,
               n_lines: int = 3, two_sided: bool = False,
               exclude_dc_hz: float = 0.0,
               contrast_hz: float | None = None) -> list[Line]:
    """Strongest discrete spectral lines of ``v`` within [fmin, fmax] Hz.

    ``two_sided`` searches +/- the range (complex input); otherwise only the
    positive side. Strength is *local contrast*: the peak over the median of
    the spectrum within +/- ``contrast_hz`` of it (the peak's own lobe
    excluded). A global median is useless here — a band-limited signal's
    envelope spectrum is exactly zero over most of the band.
    """
    v = np.asarray(v)
    if np.isrealobj(v):
        v = v - np.mean(v)
    S, fr = _spectrum(v)
    nfft = len(S)
    f_hz = fr * fs
    af = np.abs(f_hz) if two_sided else f_hz
    mask = (af >= fmin) & (af <= fmax) & (np.abs(f_hz) >= exclude_dc_hz)
    if not np.any(mask):
        return []
    idx = np.nonzero(mask)[0]
    band = S[idx]
    order = np.argsort(band)[::-1]
    lines, taken = [], []
    lobe = max(3, int(round(nfft / len(v))) * 3)     # bins per main lobe
    if contrast_hz is None:
        contrast_hz = 0.1 * (fmax - fmin) + 1.0
    half = max(8 * lobe, int(contrast_hz / fs * nfft))
    for o in order[: 50 * n_lines]:
        k = int(idx[o])
        if any(abs(k - t) <= 2 * lobe for t in taken):
            continue
        taken.append(k)
        nb = np.concatenate([S[np.arange(k - half, k - 2 * lobe) % nfft],
                             S[np.arange(k + 2 * lobe + 1, k + half + 1)
                               % nfft]])
        ref = float(np.median(nb)) + 1e-30
        kk = _refine(S, k)
        f = (kk if kk < nfft / 2 else kk - nfft) * fs / nfft
        lines.append(Line(float(f), float(S[k] / ref)))
        if len(lines) >= n_lines:
            break
    lines.sort(key=lambda l: -l.strength)
    return lines


def instantaneous_frequency(x: np.ndarray, fs: float) -> np.ndarray:
    """Discriminator output in Hz (length len(x) - 1)."""
    return np.angle(x[1:] * np.conj(x[:-1])) * fs / (2 * math.pi)


def compute_features(x: np.ndarray, fs: float, bandwidth_hz: float,
                     snr_linear: float, max_samples: int = 1 << 20,
                     x_wide: np.ndarray | None = None) -> Features:
    """All features, from a centred band-limited signal sampled at ``fs``.

    ``x_wide`` is the same signal filtered several times wider than its
    99 % bandwidth. A low-index FSK keeps nearly all its power in a band
    much narrower than its symbol rate; the symbol transitions live in the
    weak skirts, so its rate line only shows on the wide version.
    """
    if len(x) > max_samples:
        x = x[:max_samples]
    x = x.astype(np.complex128)
    x = x / (np.sqrt(np.mean(np.abs(x) ** 2)) + 1e-30)
    feats = Features(fs_hz=fs, n_samples=len(x), snr_linear=snr_linear)
    nyq = fs / 2
    lo = 0.15 * bandwidth_hz
    hi = min(0.97 * nyq, 12 * bandwidth_hz)

    # Symbol-rate lines
    env = np.abs(x) ** 2
    feats.envelope_lines = find_lines(env, fs, lo, hi, n_lines=3)
    inst = instantaneous_frequency(x, fs)
    inst = inst - np.mean(inst)
    feats.discriminator_lines = find_lines(np.abs(np.diff(inst)), fs, lo, hi,
                                           n_lines=3)
    if x_wide is not None:
        xw = x_wide[:max_samples].astype(np.complex128)
        iw = instantaneous_frequency(xw, fs)
        wide = find_lines((iw - np.mean(iw)) ** 2, fs, lo, 0.45 * fs,
                          n_lines=2)
        feats.discriminator_lines = sorted(
            feats.discriminator_lines + wide, key=lambda l: -l.strength)[:4]

    # M-th power lines near DC (the signal is roughly centred, so the
    # residual offset is a small fraction of the bandwidth).
    # The band centroid is accurate to a few % of the bandwidth; searching
    # wider than that lets the M-th power's cyclic SIDE-lines (at M f0 +/- k
    # Rs) masquerade as the carrier line.
    span = max(0.05 * bandwidth_hz, 10 * fs / len(x))
    for m in (2, 4, 8):
        lines = find_lines(x ** m, fs, 0.0, min(m * span, 0.95 * nyq),
                           n_lines=1, two_sided=True,
                           contrast_hz=0.25 * bandwidth_hz)
        if lines:
            feats.power_lines[m] = lines[0]

    # OQPSK twin lines in x^2 (at 2f0 +/- Rs) and pi/4-DQPSK twin lines in
    # x^4 (at 4f0 +/- Rs/2): two lines of similar strength, symmetric about
    # the carrier line one power up (x^4 for OQPSK, x^8 for pi/4-DQPSK).
    for m, ref_m, attr, sep_per_rs in ((2, 4, "oqpsk_twin", 2.0),
                                       (4, 8, "pi4_twin", 1.0)):
        ref = feats.power_lines.get(ref_m)
        if ref is None:
            continue
        centre = ref.freq_hz * m / ref_m
        cand = find_lines(x ** m, fs, 0.0,
                          min(abs(centre) + 3 * bandwidth_hz, 0.95 * nyq),
                          n_lines=6, two_sided=True,
                          contrast_hz=0.3 * bandwidth_hz)
        best = None
        for i_a, a in enumerate(cand):
            for b in cand[i_a + 1:]:
                lo_l, hi_l = sorted((a, b), key=lambda l: l.freq_hz)
                sep = hi_l.freq_hz - lo_l.freq_hz
                mid = 0.5 * (hi_l.freq_hz + lo_l.freq_hz)
                ratio = (min(a.strength, b.strength)
                         / max(a.strength, b.strength))
                if (sep > 0.2 * bandwidth_hz and ratio > 0.25
                        and abs(mid - centre) < 0.01 * bandwidth_hz + 2 * fs
                        / feats.n_samples):
                    s_ = min(a.strength, b.strength)
                    if best is None or s_ > best.strength:
                        best = Line(sep / sep_per_rs, s_)
        setattr(feats, attr, best)

    # Envelope variance, corrected for noise. With unit total power split
    # into S signal + N noise (S/N = snr): E|x|^4 - 1 = S^2 k + 2SN + N^2.
    s = snr_linear / (1 + snr_linear)
    n = 1 - s
    m4 = float(np.mean(env ** 2))
    feats.envelope_variance = (m4 - 1 - 2 * s * n - n * n) / max(s * s, 1e-6)
    return feats


# ---------------------------------------------------------------------------
#  Hypothesis ranking
# ---------------------------------------------------------------------------

MOD_BPSK, MOD_QPSK, MOD_8PSK, MOD_OQPSK = 0, 1, 2, 3
MOD_PI4DQPSK, MOD_CPM = 5, 7


def presence(strength: float) -> float:
    """Map a line's local contrast to 0..1 (x20 -> 0, x200 and up -> 1)."""
    if strength <= 0:
        return 0.0
    return float(np.clip((math.log10(strength) - 1.3) / 1.0, 0.0, 1.0))


@dataclass
class Hypothesis:
    modulation: int
    symbol_rate_hz: float
    score: float
    reason: str

    def key(self) -> tuple:
        return (self.modulation, round(self.symbol_rate_hz, 1))


def _rate_candidates(feats: Features, bandwidth_hz: float) -> list[tuple]:
    """(rate, strength, source) — merged across features, harmonics removed,
    strongest first."""
    raw = []
    for l in feats.envelope_lines:
        raw.append((abs(l.freq_hz), l.strength, "envelope"))
    for l in feats.discriminator_lines:
        raw.append((abs(l.freq_hz), l.strength, "discriminator"))
    if feats.oqpsk_twin:
        raw.append((feats.oqpsk_twin.freq_hz, feats.oqpsk_twin.strength,
                    "oqpsk-twin"))
    if feats.pi4_twin:
        raw.append((feats.pi4_twin.freq_hz, feats.pi4_twin.strength,
                    "pi4-twin"))
    raw = [r for r in raw if r[0] > 0]
    raw.sort(key=lambda r: -r[1])
    merged = []
    for r in raw:
        hit = next((m for m in merged if abs(r[0] - m[0]) < 0.005 * m[0]),
                   None)
        if hit is None:
            merged.append(list(r))
        elif r[2] not in hit[2]:
            hit[2] += "+" + r[2]
    # Drop harmonics: a rate at 2x/3x/4x a present candidate is that
    # candidate's harmonic, not a rate of its own.
    out = []
    for r in merged:
        # Only the envelope/discriminator lines have harmonics; a rate
        # inferred from twin lines never suppresses one measured directly.
        fundamental = any(
            abs(r[0] / m[0] - n) < 0.005 * n
            for m in merged if m is not r and m[1] > 0.3 * r[1]
            and ("envelope" in m[2] or "discriminator" in m[2])
            for n in (2, 3, 4))
        if not fundamental:
            out.append(tuple(r))
    return out[:4]


def rank_hypotheses(feats: Features, bandwidth_hz: float,
                    max_hypotheses: int = 12) -> list[Hypothesis]:
    """Turn features into an ordered list of (modulation, rate) guesses.

    Every modulation the verifier supports stays in the list — the features
    only decide the ORDER. A weak feature therefore costs time, never a
    missed signal.
    """
    rates = _rate_candidates(feats, bandwidth_hz)
    if not rates:
        # No cyclic line at all: fall back to the bandwidth rule of thumb.
        rates = [(bandwidth_hz / 1.35, 1.0, "bandwidth")]
    P = {m: presence(feats.power_lines[m].strength)
         if m in feats.power_lines else 0.0 for m in (2, 4, 8)}
    twin = presence(feats.oqpsk_twin.strength) if feats.oqpsk_twin else 0.0
    pi4 = presence(feats.pi4_twin.strength) if feats.pi4_twin else 0.0
    ev = feats.envelope_variance
    const_env = float(np.clip((0.15 - ev) / 0.1, 0.0, 1.0))

    mod_score = {
        MOD_BPSK: P[2],
        MOD_QPSK: P[4] * (1 - P[2]),
        MOD_OQPSK: twin * (1 - P[2]),
        MOD_8PSK: P[8] * (1 - P[4]),
        MOD_PI4DQPSK: pi4 * (1 - P[4]),
        MOD_CPM: const_env,
    }
    # A constant envelope vetoes the linear modulations (integer-h FSK
    # does throw an x^2 line, but it never has a PSK's envelope ripple).
    for m in (MOD_BPSK, MOD_QPSK, MOD_OQPSK, MOD_8PSK, MOD_PI4DQPSK):
        mod_score[m] *= (1 - 0.8 * const_env)
    detail = (f"M2={P[2]:.2f} M4={P[4]:.2f} M8={P[8]:.2f} twin={twin:.2f} "
              f"pi4={pi4:.2f} env_var={ev:.3f}")
    hyps = []
    for rank, (rate, rstrength, src) in enumerate(rates):
        rate_score = presence(rstrength) - 0.15 * rank
        for mod, ms in mod_score.items():
            fam = 0.0
            if "oqpsk-twin" in src and mod == MOD_OQPSK:
                fam = 0.5
            if "pi4-twin" in src and mod == MOD_PI4DQPSK:
                fam = 0.5
            hyps.append(Hypothesis(mod, rate, ms + 0.5 * rate_score + fam,
                                   f"rate {rate:.1f} Hz from {src} "
                                   f"(x{rstrength:.0f}); {detail}"))
    hyps.sort(key=lambda h: -h.score)
    seen, out = set(), []
    for h in hyps:
        if h.key() in seen:
            continue
        seen.add(h.key())
        out.append(h)
    out = out[:max_hypotheses]
    # Every family must get a go at each of the two best-supported rates,
    # even if its features scored poorly — a misleading feature may cost
    # time, never the signal. (Integer-index FSK, for one, throws strong
    # twin lines that look like OQPSK at half its rate.)
    for top_rate, _, _ in rates[:2]:
        def at(h, r=top_rate):
            return abs(h.symbol_rate_hz - r) <= 1e-6 * r
        have = {h.modulation for h in out if at(h)}
        for h in hyps:
            if at(h) and h.modulation not in have:
                have.add(h.modulation)
                out.append(h)
    out.sort(key=lambda h: -h.score)
    return out
