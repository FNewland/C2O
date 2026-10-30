"""``smo-rfsim-blind`` — blind decoding of an I/Q recording.

    smo-rfsim-blind decode CAPTURE.cf32 [--fs HZ] [--json OUT] [--packets DIR]
    smo-rfsim-blind synth  --tier LOW --out DIR [--snr-db 10] [--frames 20]
                           [--doppler-rate 500] [--modulation QPSK] ...

``decode`` reads only the samples and the sample rate (from ``--fs``, or the
recorder's ``.sigmf-meta`` / ``.json`` sidecar). It never reads the
sidecar's description of the signal; with ``--score`` it does so *after*
decoding, to mark its own work.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

from ..dsp.modulator import MOD_NAMES
from .batch import BatchBlindDecoder, load_cf32, sample_rate_from_sidecar
from .receiver import BlindReceiver

_MOD_BY_NAME = {v.upper(): k for k, v in MOD_NAMES.items()}
_MOD_BY_NAME.update({"PI4DQPSK": 5, "FSK": 7})


def _score(path: str, rep) -> list[str]:
    base = os.path.splitext(path)[0]
    out = []
    try:
        with open(base + ".json", encoding="utf-8") as f:
            sim = json.load(f).get("simulation", {})
    except (OSError, ValueError):
        return ["(no sidecar to score against)"]
    if not rep.segments:
        return ["score: nothing acquired"]
    d = rep.segments[0].description
    tm = sim.get("modulation")
    tr = sim.get("symbol_rate_hz")
    out.append(f"score: modulation truth={tm} decoded={d['modulation_name']}")
    if tr:
        out.append(f"score: symbol rate truth={tr} decoded="
                   f"{d['symbol_rate_hz']:.2f} "
                   f"({(d['symbol_rate_hz'] - tr) / tr * 1e6:+.0f} ppm)")
    return out


def cmd_decode(a) -> int:
    fs = a.fs or sample_rate_from_sidecar(a.capture)
    if not fs:
        print("sample rate unknown: pass --fs (no sidecar found)",
              file=sys.stderr)
        return 2
    x = load_cf32(a.capture)
    if a.max_seconds:
        x = x[: int(a.max_seconds * fs)]
    dec = BatchBlindDecoder(BlindReceiver(max_hypotheses=a.max_hypotheses),
                            acquire_window_s=a.acquire_s,
                            max_acquire_window_s=a.max_acquire_s,
                            min_chunk_s=a.chunk_s,
                            progress=(print if a.verbose else None))
    rep = dec.run(x, fs, os.path.basename(a.capture))
    print(rep.summary())
    for seg in rep.segments:
        print("  hypotheses tried (in estimator order):")
        for t in seg.acquisition_trials:
            print(f"    {t['modulation']:>14s} {t['symbol_rate_hz']:>11.2f} Bd"
                  f"  score {t['estimator_score']:5.2f}  -> {t['verdict']}")
    if a.score:
        for line in _score(a.capture, rep):
            print(line)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(rep.to_dict(), f, indent=2, default=str)
        print(f"report: {a.json}")
    if a.packets:
        os.makedirs(a.packets, exist_ok=True)
        path = os.path.join(a.packets, "packets.bin")
        with open(path, "wb") as f:
            for p in rep.packets:
                f.write(p)
        print(f"{len(rep.packets)} packets: {path}")
    return 0 if rep.segments else 1


def cmd_synth(a) -> int:
    from ..recording.iq_recorder import write_cf32
    from .synth import synth_recording
    mod = None
    if a.modulation:
        mod = _MOD_BY_NAME.get(a.modulation.upper().replace("/", ""))
        if mod is None:
            print(f"unknown modulation {a.modulation}", file=sys.stderr)
            return 2
    y, fs, truth = synth_recording(
        a.tier, modulation=mod, n_frames=a.frames, snr_db=a.snr_db,
        sample_rate_hz=a.fs, carrier_offset_hz=a.offset_hz, seed=a.seed,
        info_rate_bps=a.bps, gfsk_h=a.gfsk_h)
    if a.doppler_rate:
        t = np.arange(len(y)) / fs
        y = (y * np.exp(1j * math.pi * a.doppler_rate * t ** 2)).astype(
            np.complex64)
    os.makedirs(a.out, exist_ok=True)
    name = a.name or f"blind_{a.tier or 'custom'}_{truth.modulation_name}"
    name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    cf = os.path.join(a.out, name + ".cf32")
    write_cf32(cf, y)
    side = {"sample_rate_hz": fs, "source": "smo-rfsim-blind synth",
            "simulation": {"modulation": truth.modulation_name,
                           "symbol_rate_hz": truth.symbol_rate_hz,
                           "conv": truth.conv, "rs": truth.rs,
                           "frame_length": truth.frame_length,
                           "carrier_offset_hz": truth.carrier_offset_hz,
                           "doppler_rate_hz_per_s": a.doppler_rate,
                           "snr_db": a.snr_db, "packets": len(truth.packets),
                           "frames": truth.n_frames}}
    with open(os.path.join(a.out, name + ".json"), "w",
              encoding="utf-8") as f:
        json.dump(side, f, indent=2)
    print(f"wrote {cf} ({len(y) / fs:.1f} s, {truth.modulation_name} "
          f"{truth.symbol_rate_hz:.0f} Bd, {truth.n_frames} frames)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="smo-rfsim-blind",
        description="Blind (no prior knowledge) decoding of CCSDS "
                    "downlink recordings.")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("decode", help="decode a .cf32 recording")
    d.add_argument("capture")
    d.add_argument("--fs", type=float, help="sample rate (Hz)")
    d.add_argument("--json", help="write the full report here")
    d.add_argument("--packets", help="directory for recovered packets")
    d.add_argument("--chunk-s", type=float, default=2.0,
                   help="minimum chunk length; the real one is derived from "
                        "the discovered frame air time")
    d.add_argument("--acquire-s", type=float, default=4.0)
    d.add_argument("--max-acquire-s", type=float, default=96.0)
    d.add_argument("--max-hypotheses", type=int, default=10)
    d.add_argument("--max-seconds", type=float)
    d.add_argument("--score", action="store_true",
                   help="after decoding, compare with the sidecar's truth")
    d.add_argument("-v", "--verbose", action="store_true")
    d.set_defaults(func=cmd_decode)

    s = sub.add_parser("synth", help="write a synthetic test recording")
    s.add_argument("--tier", default="LOW",
                   help="EO-Sat-1 rung: SAFE, LOW, HIGH (default LOW)")
    s.add_argument("--modulation", help="override: BPSK, QPSK, OQPSK, 8PSK,"
                                        " PI4DQPSK, GFSK")
    s.add_argument("--bps", type=float, help="override channel bit rate")
    s.add_argument("--frames", type=int, default=12)
    s.add_argument("--snr-db", type=float, default=10.0)
    s.add_argument("--fs", type=float, default=250_000.0)
    s.add_argument("--offset-hz", type=float, default=21_000.0)
    s.add_argument("--doppler-rate", type=float, default=0.0,
                   help="linear Doppler ramp, Hz/s")
    s.add_argument("--gfsk-h", type=float, default=0.5)
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--out", default="sim_captures/blind")
    s.add_argument("--name")
    s.set_defaults(func=cmd_synth)
    return p


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    raise SystemExit(main())
