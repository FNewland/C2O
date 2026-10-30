"""BlindReceiver — estimators propose, the sync marker disposes.

``acquire()`` takes raw I/Q plus the sample rate and nothing else, and
returns a ``SignalDescription``: modulation, symbol rate, carrier offset,
which ambiguity branch the demodulator is on, coding, frame length and
spacecraft ID — together with a log of every hypothesis it tried and why.

``decode()`` then uses a description to pull frames out of further chunks
of the same pass (re-estimating carrier, timing and phase ambiguity per
chunk, since those drift, but not the signal's identity).
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field, asdict

import numpy as np

from . import estimators as est
from .demod import demodulate, mod_name
from .framing import FramingResult, decode_frame, fecf_ok, infer_framing
from .frontend import BandEstimate, estimate_drift, extract_band, \
    find_band, lowpass, refine_drift_mth_power, remove_dc, remove_drift
from .sync import analyse


@dataclass
class SignalDescription:
    modulation: int
    modulation_name: str
    symbol_rate_hz: float
    bits_per_symbol: int
    center_hz: float
    bandwidth_hz: float
    snr_db: float
    variant: str
    coding: str
    frame_length: int
    coded_frame_bytes: int
    fecf: bool
    period_bits: int
    frame_air_time_s: float
    scid: int | None = None
    evidence: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Trial:
    modulation: str
    symbol_rate_hz: float
    estimator_score: float
    best_variant: str
    asm_hits: int
    asm_on_lattice: int
    period_bits: int | None
    verdict: str
    seconds: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DecodedFrame:
    time_s: float                  # ASM start, seconds from input start
    data: bytes
    ok: bool

    @property
    def header(self) -> dict:
        if len(self.data) < 6:
            return {}
        w0, w1 = int.from_bytes(self.data[0:2], "big"), self.data[2]
        return {"scid": (w0 >> 4) & 0x3FF, "vcid": (w0 >> 1) & 0x7,
                "mc_count": w1}


@dataclass
class Acquisition:
    ok: bool
    band: BandEstimate | None
    reason: str = ""
    description: SignalDescription | None = None
    trials: list = field(default_factory=list)
    hypotheses: list = field(default_factory=list)
    features: dict = field(default_factory=dict)
    frames: list = field(default_factory=list)
    seconds: float = 0.0

    def summary(self) -> str:
        if not self.ok:
            return f"no acquisition: {self.reason}"
        d = self.description
        return (f"{d.modulation_name} at {d.symbol_rate_hz:.1f} Bd, "
                f"carrier {d.center_hz:+.1f} Hz, {d.coding} coding, "
                f"{d.frame_length}-byte frames every {d.frame_air_time_s:.3f}"
                f" s, SCID {d.scid}  [{d.evidence}]")


def _rolloff_from(bw: float, rs: float) -> float:
    return float(np.clip(bw / rs - 1.0, 0.25, 0.5))


#: The "wide" cut, in multiples of the measured 99 % bandwidth. Wide enough
#: for the symbol-rate skirts of a low-index FSK and for Doppler smear; not
#: so wide that it takes in the receiver's IQ image or a neighbouring
#: signal, whose beats with an FSK's discrete tones throw strong false
#: symbol-rate lines (seen at 8x on an h = 1 FSK with IQ imbalance).
WIDE_KEEP = 4.0


class BlindReceiver:
    """Blind acquisition and decoding of a CCSDS-framed downlink."""

    def __init__(self, max_hypotheses: int = 10, asm_max_errors: int = 3,
                 feature_seconds: float = 2.0):
        self.max_hypotheses = max_hypotheses
        self.asm_max_errors = asm_max_errors
        self.feature_seconds = feature_seconds

    # -- helpers ----------------------------------------------------------

    @staticmethod
    def _working_rate(fs: float, bw: float) -> float:
        # Wide enough for the symbol-rate lines of a low-index FSK, whose
        # 99 % bandwidth can be well under its symbol rate.
        return float(min(fs, max(16 * bw, 2000.0)))

    def _extract(self, x, fs, band: BandEstimate, keep_factor=1.6,
                 notch=True):
        fs_w = self._working_rate(fs, band.bandwidth_hz)
        keep = min(fs_w, keep_factor * band.bandwidth_hz)
        return extract_band(x, fs, band.center_hz, keep, fs_w,
                            tuple(band.cw_lines_hz) if notch else (),
                            2 * band.resolution_hz)

    @staticmethod
    def _inband_lines(band: BandEstimate) -> list:
        return [f for f in band.cw_lines_hz
                if abs(f - band.center_hz) < 4 * band.bandwidth_hz]

    def _prepared(self, x, fs, band: BandEstimate):
        """Wide cuts of the band, with and without in-band line notches.

        A narrowband line inside the band is usually an interferer, and
        notching it saves a PSK hypothesis. But an FSK with an integer
        modulation index carries real spectral lines at its tones, and
        notching those destroys it. So both versions are kept: linear
        hypotheses get the notched one, continuous-phase ones the raw one.
        """
        xw_n, fs_w, centre = self._extract(x, fs, band, WIDE_KEEP,
                                           notch=True)
        if self._inband_lines(band):
            xw_r, _, _ = self._extract(x, fs, band, WIDE_KEEP, notch=False)
        else:
            xw_r = xw_n
        # Doppler rate: the band centroid's motion, removed up front so the
        # M-th power lines and twin lines stay sharp over the analysis
        # window. (A ground station would use predicted Doppler here; blind,
        # the signal is its own predictor.)
        drift = estimate_drift(xw_n, fs_w, band.bandwidth_hz)
        self.last_drift = drift
        if len(drift) > 1:
            same = xw_r is xw_n
            xw_n = remove_drift(xw_n, fs_w, drift)
            xw_r = xw_n if same else remove_drift(xw_r, fs_w, drift)
            # A band smeared by Doppler over the window reads wider than it
            # is; measure it again now that it holds still.
            b2 = find_band(xw_n, fs_w)
            if b2.found and b2.bandwidth_hz < band.bandwidth_hz:
                # (Bandwidth only: this cut is band-limited, so its noise
                # floor — and any SNR measured on it — is not trustworthy.)
                band.bandwidth_hz = b2.bandwidth_hz
                # ...and re-centre on it: the drift fit's constant term is
                # the least certain part of it, and a residual offset of a
                # sizeable fraction of the symbol rate costs matched-filter
                # and timing performance before the carrier loop sees it.
                if abs(b2.center_hz) > 0:
                    coef = drift.copy()
                    coef[-1] += b2.center_hz
                    shift = np.array([b2.center_hz])
                    xw_n = remove_drift(xw_n, fs_w, shift)
                    xw_r = xw_n if same else remove_drift(xw_r, fs_w, shift)
                    self.last_drift = coef
            # Second stage: the spectral-registration fit is good to ~1 %,
            # which still smears an M-th power line over tens of Hz across
            # a 2 s analysis window (OQPSK's weak twin lines vanish). Where
            # the signal has an M-th power line, measure its drift directly
            # and remove the residual.
            resid = refine_drift_mth_power(
                lowpass(xw_n, fs_w, 1.6 * band.bandwidth_hz), fs_w,
                band.bandwidth_hz)
            if resid is not None:
                xw_n = remove_drift(xw_n, fs_w, resid)
                xw_r = xw_n if same else remove_drift(xw_r, fs_w, resid)
        return xw_n, xw_r, fs_w, centre

    def _signal_for(self, mod, rs, prepared, bw):
        xw_n, xw_r, fs_w, _ = prepared
        xw = xw_r if mod == est.MOD_CPM else xw_n
        return self._for_rate(xw, lowpass(xw, fs_w, 1.6 * bw), fs_w, bw, rs)

    @staticmethod
    def _for_rate(xw, xb, fs_w, bw, rs):
        """The narrow cut suits a signal whose bandwidth exceeds its rate
        (every filtered PSK); a hypothesis with Rs well above the measured
        bandwidth (low-index FSK) needs its transitions kept."""
        if 1.3 * rs <= 1.6 * bw:
            return xb
        return lowpass(xw, fs_w, min(fs_w, 1.3 * rs))

    # -- acquisition --------------------------------------------------------

    def acquire(self, x: np.ndarray, fs: float) -> Acquisition:
        t0 = time.monotonic()
        x = remove_dc(np.asarray(x, dtype=np.complex64))
        band = find_band(x, fs)
        if not band.found:
            return Acquisition(False, band, "no signal above the noise floor",
                               seconds=time.monotonic() - t0)
        prep = self._prepared(x, fs, band)
        xw_n, xw_r, fs_w, centre = prep
        xb = lowpass(xw_n, fs_w, 1.6 * band.bandwidth_hz)
        band.center_hz = centre
        n_feat = int(min(len(xb), self.feature_seconds * fs_w, 1 << 20))
        f0 = _strongest_span(xb, n_feat)
        fsl = slice(f0, f0 + n_feat)
        snr_lin = 10 ** (band.snr_db / 10)
        feats = est.compute_features(xb[fsl], fs_w, band.bandwidth_hz,
                                     snr_lin, x_wide=xw_n[fsl])
        if xw_r is not xw_n:
            raw = est.compute_features(
                lowpass(xw_r, fs_w, 1.6 * band.bandwidth_hz)[fsl], fs_w,
                band.bandwidth_hz, snr_lin, x_wide=xw_r[fsl])
            feats.envelope_variance = min(feats.envelope_variance,
                                          raw.envelope_variance)
            feats.discriminator_lines = sorted(
                feats.discriminator_lines + raw.discriminator_lines,
                key=lambda l: -l.strength)[:4]
        hyps = est.rank_hypotheses(feats, band.bandwidth_hz,
                                   self.max_hypotheses)
        acq = Acquisition(False, band, hypotheses=[
            {"modulation": mod_name(h.modulation),
             "symbol_rate_hz": round(h.symbol_rate_hz, 2),
             "score": round(h.score, 3), "why": h.reason} for h in hyps],
            features=_features_dict(feats))
        rolloff_guess = None
        for h in hyps:
            ts = time.monotonic()
            rolloff_guess = _rolloff_from(band.bandwidth_hz, h.symbol_rate_hz)
            dm = demodulate(self._signal_for(h.modulation, h.symbol_rate_hz,
                                             prep, band.bandwidth_hz),
                            fs_w, h.modulation, h.symbol_rate_hz,
                            rolloff_guess)
            best = None
            for v in dm.variants:
                sy = analyse(v.soft, self.asm_max_errors)
                if best is None or sy.score() > best[1].score():
                    best = (v, sy)
            verdict, framing = "no sync marker", None
            if best is not None and best[1].n_hits:
                v, sy = best
                soft = v.soft * sy.sign
                framing = infer_framing(soft, sy)
                if framing is not None:
                    verdict = f"CONFIRMED: {framing.evidence}"
                elif sy.n_aligned >= 3:
                    verdict = (f"sync lattice confirmed ({sy.n_aligned} "
                               f"markers) but framing/coding not identified")
                else:
                    verdict = (f"{sy.n_hits} isolated marker hit(s) — "
                               f"not enough to confirm")
            acq.trials.append(Trial(
                mod_name(h.modulation), round(h.symbol_rate_hz, 3),
                round(h.score, 3), best[0].label if best else "-",
                best[1].n_hits if best else 0,
                best[1].n_aligned if best else 0,
                best[1].period_bits if best else None, verdict,
                round(time.monotonic() - ts, 3)))
            if framing is not None:
                v, sy = best
                bps = dm.bits_per_symbol
                desc = SignalDescription(
                    modulation=h.modulation,
                    modulation_name=mod_name(h.modulation),
                    symbol_rate_hz=h.symbol_rate_hz, bits_per_symbol=bps,
                    center_hz=band.center_hz + dm.freq_offset_hz,
                    bandwidth_hz=band.bandwidth_hz, snr_db=band.snr_db,
                    variant=v.label, coding=framing.coding,
                    frame_length=framing.frame_length,
                    coded_frame_bytes=framing.coded_bytes,
                    fecf=framing.fecf, period_bits=framing.period_bits,
                    frame_air_time_s=framing.period_bits / bps
                    / h.symbol_rate_hz,
                    scid=framing.header().get("scid"),
                    evidence=framing.evidence)
                acq.ok, acq.description = True, desc
                acq.frames = self._frames_from(v.soft * sy.sign, sy, desc,
                                               dm, framing)
                break
        if not acq.ok:
            acq.reason = (f"{len(acq.trials)} hypotheses tried, none "
                          f"produced a verifiable frame")
        acq.seconds = time.monotonic() - t0
        return acq

    # -- decoding -----------------------------------------------------------

    def _frames_from(self, soft, sy, desc: SignalDescription, dm,
                     framing: FramingResult | None = None) -> list:
        out = []
        bps, rs = desc.bits_per_symbol, desc.symbol_rate_hz
        # Lattice hits first; any other hit only if it is not inside a
        # frame the lattice already accounts for (a false correlation there
        # would otherwise displace a real marker).
        anchors = sorted(set(int(p) for p in sy.aligned))
        others = sorted(set(int(p) for p, s in zip(sy.positions, sy.signs)
                            if s == sy.sign)) if len(sy.positions) else []
        kept = list(anchors)
        for p in others:
            if all(abs(p - q) >= desc.period_bits * 0.9 for q in kept):
                kept.append(p)
        kept.sort()
        for p in kept:
            fr = decode_frame(soft, p, desc.coding, desc.frame_length)
            if fr is None:
                if p + desc.period_bits <= len(soft):
                    out.append(DecodedFrame(dm.symbol_time0_s + p / bps / rs,
                                            b"", False))
                continue
            ok = fecf_ok(fr) if desc.fecf else True
            out.append(DecodedFrame(dm.symbol_time0_s + p / bps / rs, fr, ok))
        return out

    def decode(self, x: np.ndarray, fs: float,
               desc: SignalDescription) -> tuple[list, dict]:
        """Decode a chunk with a known signal description."""
        x = remove_dc(np.asarray(x, dtype=np.complex64))
        band = find_band(x, fs)
        info = {"band_found": band.found}
        # Follow the band where it is in THIS chunk: over a long chunk
        # (SAFE rate: 80 s) Doppler moves it by several bandwidths, and the
        # smeared width is what the drift estimator must be allowed to see.
        if band.found and band.bandwidth_hz < 50 * desc.bandwidth_hz:
            centre = band.center_hz
            bw = max(desc.bandwidth_hz, band.bandwidth_hz)
        else:
            centre, bw = desc.center_hz, desc.bandwidth_hz
        use = BandEstimate(True, centre, bw, desc.snr_db,
                           band.noise_psd,
                           band.cw_lines_hz if band.found else [],
                           band.resolution_hz)
        prep = self._prepared(x, fs, use)
        fs_w, centre = prep[2], prep[3]
        xb = self._signal_for(desc.modulation, desc.symbol_rate_hz, prep,
                              desc.bandwidth_hz)
        dm = demodulate(xb, fs_w, desc.modulation, desc.symbol_rate_hz,
                        _rolloff_from(desc.bandwidth_hz,
                                      desc.symbol_rate_hz))
        best = None
        for v in dm.variants:
            sy = analyse(v.soft, self.asm_max_errors)
            if best is None or sy.score() > best[1].score():
                best = (v, sy)
        info.update(center_hz=centre + dm.freq_offset_hz,
                    evm_snr_db=round(dm.evm_snr_db, 2))
        if best is None or best[1].n_hits == 0:
            info["asm_hits"] = 0
            return [], info
        v, sy = best
        info.update(asm_hits=sy.n_hits, variant=v.label)
        return self._frames_from(v.soft * sy.sign, sy, desc, dm), info


def _strongest_span(x: np.ndarray, n: int) -> int:
    """Start index of the length-``n`` span holding the most energy — the
    features are measured where the signal actually is (a window may open
    before AOS or run past LOS)."""
    if len(x) <= n:
        return 0
    blk = max(1, n // 16)
    nb = len(x) // blk
    e = (np.abs(x[:nb * blk]) ** 2).reshape(nb, blk).sum(axis=1)
    w = n // blk
    if nb <= w:
        return 0
    c = np.convolve(e, np.ones(w), mode="valid")
    return int(np.argmax(c)) * blk


def _features_dict(f: est.Features) -> dict:
    def ln(l):
        return None if l is None else {"hz": round(l.freq_hz, 2),
                                       "strength": round(l.strength, 1)}
    return {
        "envelope_lines": [ln(l) for l in f.envelope_lines],
        "discriminator_lines": [ln(l) for l in f.discriminator_lines],
        "power_lines": {str(m): ln(l) for m, l in f.power_lines.items()},
        "oqpsk_twin_rate": ln(f.oqpsk_twin),
        "pi4_twin_rate": ln(f.pi4_twin),
        "envelope_variance": round(f.envelope_variance, 4),
    }
