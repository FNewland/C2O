#!/usr/bin/env python3
"""Performance sweep of the blind receiver (v2).

Two parts:

* ``captures`` — run the batch decoder over every ``*.cf32`` in a folder
  (``sim_captures/`` by default: the recorded passes), using only the sample
  rate, then score against the sidecar's ``simulation`` block.
* ``matrix`` — synthetic passes over modulation x SNR x Doppler rate x seed,
  scoring identification (modulation, rate, coding, frame length), frames
  recovered, hypotheses tried and time. Writes CSV + JSON (+ PNG if
  matplotlib is present).

    python tools/blind_sweep.py captures --dir sim_captures --out docs/sweeps
    python tools/blind_sweep.py matrix --out docs/sweeps [--quick] [-j 2]
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "packages", "smo-rfsim", "src"))
sys.path.insert(0, os.path.join(HERE, "..", "packages", "smo-common", "src"))

from smo_rfsim.blind import BatchBlindDecoder, BlindReceiver  # noqa: E402
from smo_rfsim.blind.batch import load_cf32, sample_rate_from_sidecar  # noqa
from smo_rfsim.blind.synth import synth_recording  # noqa: E402

# (label, tier, overrides) — the flown ladder first, then the families the
# radio supports but the ladder does not fly.
FAMILIES = [
    ("BPSK conv+RS (LOW)", "LOW", {}),
    ("QPSK RS (HIGH)", "HIGH", {"n_frames": 10}),
    ("OQPSK conv+RS", "LOW", {"modulation": 3}),
    ("8PSK conv+RS", "LOW", {"modulation": 2}),
    ("pi/4-DQPSK conv+RS", "LOW", {"modulation": 5}),
    ("GMSK conv+RS", "LOW", {"modulation": 6}),
    ("GFSK h=1 conv+RS", "LOW", {"modulation": 7, "gfsk_h": 1.0}),
    ("QPSK uncoded", "LOW", {"modulation": 1, "conv": False, "rs": False}),
]


def _chirp(y, fs, rate):
    if not rate:
        return y
    t = np.arange(len(y)) / fs
    return (y * np.exp(1j * math.pi * rate * t ** 2)).astype(np.complex64)


def run_case(args):
    label, tier, kw, snr, rate, seed = args
    y, fs, tr = synth_recording(tier, **{"n_frames": 4, "snr_db": snr,
                                         "seed": seed, **kw})
    y = _chirp(y, fs, rate)
    t0 = time.monotonic()
    acq = BlindReceiver().acquire(y, fs)
    dt = time.monotonic() - t0
    fam = 7 if tr.modulation in (6, 7) else tr.modulation
    ok_id = bool(acq.ok and acq.description.modulation == fam and abs(
        acq.description.symbol_rate_hz - tr.symbol_rate_hz)
        < 1e-4 * tr.symbol_rate_hz
        and acq.description.frame_length == tr.frame_length)
    frames_ok = sum(f.ok for f in acq.frames) if acq.ok else 0
    return {"family": label, "snr_db": snr, "doppler_hz_s": rate,
            "seed": seed, "acquired": acq.ok, "identified": ok_id,
            "frames_ok": frames_ok, "frames_sent": tr.n_frames,
            "trials": len(acq.trials), "seconds": round(dt, 2),
            "decoded_as": acq.description.modulation_name if acq.ok else ""}


def cmd_matrix(a):
    snrs = [0, 2, 4, 6, 8, 10, 12, 16] if not a.quick else [2, 6, 12]
    rates = [0.0, 800.0]
    seeds = range(a.seeds)
    jobs = [(l, t, k, s, r, sd) for l, t, k in FAMILIES for s in snrs
            for r in rates for sd in seeds]
    print(f"{len(jobs)} cases on {a.jobs} worker(s)")
    rows = []
    t0 = time.monotonic()
    with ProcessPoolExecutor(a.jobs) as ex:
        for i, r in enumerate(ex.map(run_case, jobs, chunksize=1)):
            rows.append(r)
            if (i + 1) % 20 == 0:
                print(f"  {i + 1}/{len(jobs)}  {time.monotonic() - t0:.0f} s",
                      flush=True)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "matrix.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    summary = summarise(rows)
    with open(os.path.join(a.out, "matrix_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print_summary(summary)
    plot(summary, os.path.join(a.out, "matrix_success_vs_snr.png"))


def summarise(rows):
    out = {}
    for r in rows:
        k = (r["family"], r["doppler_hz_s"])
        d = out.setdefault(f"{k[0]} @ {k[1]:.0f} Hz/s", {})
        s = d.setdefault(str(r["snr_db"]), {"n": 0, "id": 0, "fr_ok": 0,
                                            "fr": 0, "trials": 0, "t": 0.0})
        s["n"] += 1
        s["id"] += r["identified"]
        s["fr_ok"] += r["frames_ok"]
        s["fr"] += r["frames_sent"]
        s["trials"] += r["trials"]
        s["t"] += r["seconds"]
    return out


def print_summary(summary):
    for key, by_snr in summary.items():
        cells = []
        for snr in sorted(by_snr, key=float):
            s = by_snr[snr]
            cells.append(f"{snr:>3}dB {s['id']}/{s['n']} "
                         f"({100 * s['fr_ok'] / max(s['fr'], 1):3.0f}%)")
        print(f"{key:36s} " + "  ".join(cells))


def plot(summary, path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for ax, rate in zip(axes, ("0", "800")):
        for key, by_snr in summary.items():
            if not key.endswith(f"@ {rate} Hz/s"):
                continue
            snrs = sorted(by_snr, key=float)
            ax.plot([float(s) for s in snrs],
                    [100 * by_snr[s]["fr_ok"] / max(by_snr[s]["fr"], 1)
                     for s in snrs], marker="o", label=key.split(" @")[0])
        ax.set_title(f"Doppler ramp {rate} Hz/s")
        ax.set_xlabel("in-band SNR (dB)")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("frames recovered blind (%)")
    axes[1].legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=130)


def cmd_captures(a):
    rows = []
    for path in sorted(glob.glob(os.path.join(a.dir, "*.cf32"))):
        fs = sample_rate_from_sidecar(path)
        x = load_cf32(path)
        rep = BatchBlindDecoder().run(x, fs, os.path.basename(path))
        side = {}
        try:
            with open(os.path.splitext(path)[0] + ".json") as f:
                side = json.load(f).get("simulation", {})
        except (OSError, ValueError):
            pass
        imp = side.get("impairments", {})
        seg = rep.segments[0].description if rep.segments else {}
        row = {"file": os.path.basename(path),
               "truth": f"{side.get('modulation')} "
                        f"{side.get('symbol_rate_hz')} Bd",
               "snr_db": imp.get("snr_db"),
               "doppler": f"{imp.get('doppler_model')} "
                          f"{imp.get('doppler_peak_hz')}",
               "decoded": (f"{seg.get('modulation_name')} "
                           f"{seg.get('symbol_rate_hz', 0):.1f} Bd "
                           f"{seg.get('coding')} {seg.get('frame_length')} B")
               if seg else "not acquired",
               "frames_ok": rep.frames_ok, "frames_bad": rep.frames_bad,
               "packets": len(rep.packets),
               "seconds": round(rep.processing_seconds, 1)}
        rows.append(row)
        print(json.dumps(row), flush=True)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, f"captures_{a.tag}.json"), "w") as f:
        json.dump(rows, f, indent=2)


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("matrix")
    m.add_argument("--out", default="docs/sweeps")
    m.add_argument("--quick", action="store_true")
    m.add_argument("--seeds", type=int, default=2)
    m.add_argument("-j", "--jobs", type=int, default=os.cpu_count() or 1)
    m.set_defaults(func=cmd_matrix)
    c = sub.add_parser("captures")
    c.add_argument("--dir", default="sim_captures")
    c.add_argument("--out", default="docs/sweeps")
    c.add_argument("--tag", default="run")
    c.set_defaults(func=cmd_captures)
    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
