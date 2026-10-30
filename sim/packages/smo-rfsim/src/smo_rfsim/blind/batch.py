"""Batch (lagged) blind decoding of a whole recording.

The receiver works on chunks of a recording rather than on a live stream,
so it can afford to be exhaustive: every hypothesis, every ambiguity branch,
soft-decision Viterbi — at the price of a delay. The pieces:

1. **Acquire.** Start with a short window; if a signal is present but not
   yet provable (a slow rate may not have delivered two frames yet), double
   the window; if nothing is there at all (before AOS), slide on.
2. **Track.** With a signal description in hand, decode fixed chunks. The
   chunk length is derived from the *discovered* frame air time — at least
   four frames per chunk, overlapping by one and a half frames so a frame
   straddling a boundary is always whole in one of them. Nothing here is a
   fixed timeout against the RF chain.
3. **Re-acquire** when two chunks in a row show no sync marker at all — LOS,
   or the spacecraft switching rate tier mid-pass.
4. **Reassemble** frames in time order and extract ECSS packets.

The lag reported for each frame is how long after its last bit went over
the air it would have come out of this receiver: waiting for the chunk to
fill, plus the processing time of that chunk.
"""
from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass, field

import numpy as np

from ..ccsds.tm_frame import TMFrameParser
from .receiver import BlindReceiver, SignalDescription


@dataclass
class Segment:
    """A stretch of the recording decoded under one signal description."""
    start_s: float
    end_s: float
    description: dict
    acquisition_window_s: float
    acquisition_trials: list
    acquisition_seconds: float


@dataclass
class FrameRecord:
    time_s: float
    ok: bool
    segment: int
    lag_s: float
    mc_count: int | None = None
    vcid: int | None = None
    data: bytes = b""


@dataclass
class BatchReport:
    source: str
    sample_rate_hz: float
    duration_s: float
    segments: list = field(default_factory=list)
    frames: list = field(default_factory=list)
    packets: list = field(default_factory=list)
    chunks: list = field(default_factory=list)
    acquisition_attempts: list = field(default_factory=list)
    processing_seconds: float = 0.0

    @property
    def frames_ok(self) -> int:
        return sum(1 for f in self.frames if f.ok)

    @property
    def frames_bad(self) -> int:
        return sum(1 for f in self.frames if not f.ok)

    def lag_stats(self) -> dict:
        lags = [f.lag_s for f in self.frames if f.ok]
        if not lags:
            return {}
        return {"min_s": round(min(lags), 3), "mean_s":
                round(float(np.mean(lags)), 3), "max_s": round(max(lags), 3)}

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "sample_rate_hz": self.sample_rate_hz,
            "duration_s": round(self.duration_s, 3),
            "processing_seconds": round(self.processing_seconds, 2),
            "realtime_factor": round(self.processing_seconds
                                     / max(self.duration_s, 1e-9), 3),
            "segments": [s.__dict__ for s in self.segments],
            "frames_ok": self.frames_ok,
            "frames_bad": self.frames_bad,
            "packets": len(self.packets),
            "lag": self.lag_stats(),
            "frames": [{"time_s": round(f.time_s, 4), "ok": f.ok,
                        "segment": f.segment, "lag_s": round(f.lag_s, 3),
                        "vcid": f.vcid, "mc_count": f.mc_count}
                       for f in self.frames],
            "chunks": self.chunks,
            "acquisition_attempts": self.acquisition_attempts,
        }

    def summary(self) -> str:
        lines = [f"{self.source}: {self.duration_s:.1f} s at "
                 f"{self.sample_rate_hz / 1e3:.1f} kS/s, processed in "
                 f"{self.processing_seconds:.1f} s "
                 f"({self.processing_seconds / max(self.duration_s, 1e-9):.2f}"
                 f"x real time)"]
        if not self.segments:
            lines.append("  no signal acquired")
        for i, s in enumerate(self.segments):
            d = s.description
            lines.append(
                f"  segment {i}: {s.start_s:.1f}-{s.end_s:.1f} s  "
                f"{d['modulation_name']} {d['symbol_rate_hz']:.1f} Bd, "
                f"{d['coding']}, {d['frame_length']} B frames every "
                f"{d['frame_air_time_s']:.3f} s, SCID {d['scid']}, "
                f"carrier {d['center_hz']:+.0f} Hz, {d['snr_db']:.1f} dB "
                f"(acquired from a {s.acquisition_window_s:.1f} s window in "
                f"{s.acquisition_seconds:.1f} s)")
        lines.append(f"  frames: {self.frames_ok} good, {self.frames_bad} "
                     f"bad; packets: {len(self.packets)}")
        if self.lag_stats():
            ls = self.lag_stats()
            lines.append(f"  lag after last bit on air: min {ls['min_s']} s, "
                         f"mean {ls['mean_s']} s, max {ls['max_s']} s")
        return "\n".join(lines)


def load_cf32(path: str) -> np.ndarray:
    """Memory-map an interleaved float32 I/Q file (GNU Radio / RTL-SDR)."""
    return np.memmap(path, dtype=np.complex64, mode="r")


def sample_rate_from_sidecar(path: str) -> float | None:
    """Only the SAMPLE RATE is taken from metadata — it is a property of
    the recorder, not of the signal. Nothing about the signal is read."""
    base = os.path.splitext(path)[0]
    for ext, key in ((".sigmf-meta", None), (".json", "sample_rate_hz")):
        p = base + ext
        if not os.path.exists(p):
            continue
        try:
            with open(p, encoding="utf-8") as f:
                meta = json.load(f)
        except (OSError, ValueError):
            continue
        if key is None:
            v = meta.get("global", {}).get("core:sample_rate")
        else:
            v = meta.get(key)
        if v:
            return float(v)
    return None


class BatchBlindDecoder:
    """Chunked, lagged blind decoding of a recording."""

    def __init__(self, receiver: BlindReceiver | None = None,
                 acquire_window_s: float = 4.0,
                 max_acquire_window_s: float = 96.0,
                 min_chunk_s: float = 2.0, frames_per_chunk: float = 4.0,
                 overlap_frames: float = 1.5, lost_after_chunks: int = 2,
                 progress=None):
        self.rx = receiver or BlindReceiver()
        self.acquire_window_s = acquire_window_s
        self.max_acquire_window_s = max_acquire_window_s
        self.min_chunk_s = min_chunk_s
        self.frames_per_chunk = frames_per_chunk
        self.overlap_frames = overlap_frames
        self.lost_after_chunks = lost_after_chunks
        self.progress = progress or (lambda msg: None)

    def run(self, samples: np.ndarray, fs: float,
            source: str = "<array>") -> BatchReport:
        t_wall = time.monotonic()
        n = len(samples)
        dur = n / fs
        rep = BatchReport(source, fs, dur)
        frames_raw: list[tuple] = []   # (time, DecodedFrame, seg, lag, air)
        self._misses = 0
        last_good = 0.0
        t = 0.0
        desc: SignalDescription | None = None
        seg_idx = -1
        while t < dur - 1e-3:
            if desc is None:
                desc, t_acq, acq_frames, t = self._acquire(samples, fs, t, rep)
                if desc is None:
                    break
                seg_idx += 1
                s = rep.segments[-1]
                air = desc.frame_air_time_s
                for fr in acq_frames:
                    frames_raw.append((t_acq + fr.time_s, fr, seg_idx,
                                       s.acquisition_window_s - fr.time_s
                                       - air + s.acquisition_seconds, air))
                good = [t_acq + fr.time_s + air for fr in acq_frames
                        if fr.ok]
                last_good = max(good) if good else t_acq
                # Carry on from the end of the acquisition window, backed
                # off by the overlap so a frame cut by its edge is re-read.
                t = max(t_acq, s.end_s - (self.overlap_frames * air + 0.05))
                if s.end_s >= dur - 1e-3:
                    break
                continue
            # --- tracking ---------------------------------------------------
            air = desc.frame_air_time_s
            L = max(self.min_chunk_s, self.frames_per_chunk * air)
            ov = self.overlap_frames * air + 0.05
            a, b = int(t * fs), min(n, int((t + L) * fs))
            if b - a < int(1.5 * air * fs):
                break
            tc = time.monotonic()
            frames, info = self.rx.decode(np.asarray(samples[a:b]), fs, desc)
            proc = time.monotonic() - tc
            t_end = b / fs
            n_ok = 0
            for fr in frames:
                ft = t + fr.time_s
                lag = t_end - (ft + air) + proc
                frames_raw.append((ft, fr, seg_idx, lag, air))
                n_ok += fr.ok
            info.update(start_s=round(t, 3), end_s=round(t_end, 3),
                        frames=len(frames), frames_ok=n_ok,
                        processing_s=round(proc, 3))
            rep.chunks.append(info)
            self.progress(f"  {t:7.1f}-{t_end:7.1f} s: {n_ok}/{len(frames)} "
                          f"frames ({proc:.1f} s)")
            if n_ok == 0:
                self._misses += 1
            else:
                self._misses = 0
                last_good = max(last_good, max(t + fr.time_s + air
                                               for fr in frames if fr.ok))
                if "center_hz" in info:
                    desc.center_hz = info["center_hz"]
            rep.segments[-1].end_s = max(last_good, rep.segments[-1].start_s)
            if self._misses >= self.lost_after_chunks:
                # Pick up again right after the last frame that decoded —
                # the signal changed (rate switch) or went away (LOS) there,
                # not where we happened to notice.
                t = max(last_good, rep.segments[-1].start_s + 1e-3) \
                    if last_good > 0 else t
                self.progress(f"  sync lost after {t:.1f} s — re-acquiring")
                self._misses = 0
                desc = None
                continue
            if b >= n:
                # Ran out of recording while sync was already slipping: look
                # once more from the last good frame — the tail may hold a
                # different signal (a rate switch late in the pass).
                if self._misses and last_good < dur - 1.0:
                    t, desc, self._misses = last_good, None, 0
                    continue
                break
            t = t + L - ov
        rep.frames = self._dedupe(frames_raw)
        rep.packets = self._packets(rep)
        rep.processing_seconds = time.monotonic() - t_wall
        return rep

    # -- acquisition with a growing / sliding window ---------------------------

    def _acquire(self, samples, fs, t, rep):
        dur = len(samples) / fs
        W = self.acquire_window_s
        while t < dur - 1e-3:
            a, b = int(t * fs), min(len(samples), int((t + W) * fs))
            acq = self.rx.acquire(np.asarray(samples[a:b]), fs)
            rep.acquisition_attempts.append({
                "start_s": round(t, 3), "window_s": round((b - a) / fs, 3),
                "ok": acq.ok, "reason": acq.reason if not acq.ok else
                acq.summary(), "seconds": round(acq.seconds, 2)})
            self.progress(f"acquire {t:.1f}+{(b - a) / fs:.1f} s: "
                          f"{acq.summary()}")
            if acq.ok:
                d = acq.description
                rep.segments.append(Segment(
                    t, b / fs, d.to_dict(), (b - a) / fs,
                    [tr.to_dict() for tr in acq.trials], acq.seconds))
                return d, t, acq.frames, t
            if b >= len(samples):
                # The window has grown to the end of the recording without
                # success. Before giving up, start again further in with a
                # short window: a pass that is hard at AOS (weak, or a
                # Doppler curve no low-order fit follows over the whole
                # capture) is often easy a few seconds later.
                step = self.acquire_window_s
                if t + step + step / 2 < dur and W > step:
                    t, W = t + step, step
                    continue
                return None, t, [], dur      # recording exhausted
            if acq.band is None or not acq.band.found:
                t += W                      # nothing there (yet): slide on
                W = self.acquire_window_s
            elif 2 * W <= self.max_acquire_window_s:
                W *= 2                      # something there: look longer
            else:
                t += W / 2
                W = self.acquire_window_s
        return None, t, [], dur

    # -- reassembly --------------------------------------------------------

    @staticmethod
    def _dedupe(frames_raw) -> list:
        frames_raw.sort(key=lambda r: (r[0], not r[1].ok))
        out: list[FrameRecord] = []
        for ft, fr, seg, lag, air in frames_raw:
            # The same frame seen in two overlapping chunks: keep the good
            # copy, and the earliest lag at which a good copy existed.
            dup = None
            for rec in out[-4:]:
                if abs(rec.time_s - ft) < 0.25 * air:
                    dup = rec
                    break
            if dup is not None:
                if fr.ok and not dup.ok:
                    h = fr.header
                    dup.ok, dup.data, dup.lag_s = True, fr.data, lag
                    dup.mc_count, dup.vcid = h.get("mc_count"), h.get("vcid")
                elif fr.ok and dup.ok:
                    dup.lag_s = min(dup.lag_s, lag)
                continue
            h = fr.header if fr.data else {}
            out.append(FrameRecord(ft, fr.ok, seg, lag, h.get("mc_count"),
                                   h.get("vcid"), fr.data))
        return out

    @staticmethod
    def _packets(rep: BatchReport) -> list:
        packets = []
        parsers: dict = {}
        for f in rep.frames:
            if not f.ok or not f.data:
                continue
            d = rep.segments[f.segment].description
            key = (f.segment,)
            if key not in parsers:
                parsers[key] = TMFrameParser(frame_length=d["frame_length"],
                                             fecf_present=d["fecf"])
            p = parsers[key]
            parsed = p.parse_frame(f.data)
            if parsed is not None and not parsed.is_idle:
                packets.extend(p.extract_packets(parsed))
        return packets

