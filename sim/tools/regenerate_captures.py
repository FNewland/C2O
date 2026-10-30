#!/usr/bin/env python3
"""Regenerate simulated I/Q captures from their own sidecars.

Every ``BasebandRecorder`` capture records its full configuration (signal,
seed and every impairment) in the ``.json`` sidecar, so a capture can be
rebuilt bit-for-bit with the current code. Use it to re-baseline the
recordings after a change to the modulator or the recorder — first done
for defect #135 (GMSK/GFSK ran at h/8).

    python tools/regenerate_captures.py sim_captures/*.json [--out DIR]

Without ``--out`` the capture is rewritten in place (same basename).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "packages", "smo-rfsim", "src"))

from smo_rfsim.recording.iq_recorder import (  # noqa: E402
    BasebandRecorder, ImpairmentConfig, RecorderConfig)


def config_from_sidecar(path: str) -> RecorderConfig:
    with open(path, encoding="utf-8") as f:
        side = json.load(f)
    sim = side["simulation"]
    imp = dict(sim.get("impairments", {}))
    imp["cw_interferers"] = tuple(tuple(c) for c in
                                  imp.get("cw_interferers", ()))
    known = ImpairmentConfig.__dataclass_fields__
    imp = ImpairmentConfig(**{k: v for k, v in imp.items() if k in known})
    return RecorderConfig(
        modulation=sim.get("modulation_index", sim.get("modulation")),
        symbol_rate_hz=sim["symbol_rate_hz"],
        rolloff=sim.get("rolloff", 0.35),
        gmsk_bt=sim.get("gmsk_bt", 0.5),
        gfsk_mod_index=sim.get("gfsk_mod_index", 0.5),
        sps_internal=sim.get("sps_internal", 8),
        sample_rate_hz=side["sample_rate_hz"],
        duration_s=side["recorded_seconds"],
        data_source=sim.get("data_source", "ccsds"),
        frame_length=sim.get("frame_length", 223),
        random_seed=sim.get("random_seed", 0),
        satellite=side.get("satellite", "EOSAT1-SIM"),
        norad=side.get("norad", 0),
        nominal_downlink_hz=side.get("nominal_downlink_hz", 401_415_000.0),
        mode_label=side.get("mode", ""),
        impairments=imp)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("sidecars", nargs="+")
    p.add_argument("--out", help="output folder (default: in place)")
    a = p.parse_args()
    for sc in a.sidecars:
        cfg = config_from_sidecar(sc)
        out = a.out or os.path.dirname(os.path.abspath(sc))
        base = os.path.splitext(os.path.basename(sc))[0]
        man = BasebandRecorder(cfg).record(out, base)
        print(f"{base}: {man['n_samples']} samples -> {man['cf32']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
