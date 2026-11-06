#!/usr/bin/env python3
"""Record one orbit of EOSAT-1's energy balance for the energy explainer.

Runs sim/tools/power_budget.py's own `run_profile` (the production EPS and TCS
models, EOL arrays, the real pass and TX timeline) and records generation,
load, state of charge and eclipse every 30 s through the second orbit.

    sim/.venv/bin/python video/explainers/data/gen_energy_orbit.py > video/explainers/data/energy_orbit.json
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "sim" / "tools"))
import power_budget as pb  # noqa: E402

rec = []
_make = pb._make_models


def _recording(cfg, eol):
    eps, tcs = _make(cfg, eol)
    tick = eps.tick
    t = {"t": 0.0}

    def wrapped(dt, st, params):
        tick(dt, st, params)
        s = eps._state
        rec.append((t["t"], s.power_gen_w, s.power_cons_w, s.bat_soc_pct, bool(st.in_eclipse),
                    float(getattr(st, "solar_beta_deg", 0.0))))
        t["t"] += dt
    eps.tick = wrapped
    return eps, tcs


pb._make_models = _recording
cfg = pb.load_configs(REPO / "sim" / "configs" / "eosat1")
_, epoch = pb.build_propagator(cfg["orbit"])
cstats = pb.contact_stats(cfg["orbit"], cfg["simulation"], epoch)
res = pb.run_profile(cfg, "nominal", epoch, 2, eol=True, cstats=cstats)
period = pb.orbit_period_s(cfg["orbit"])
orbit2 = [r for r in rec if period <= r[0] < 2 * period]
samples = [{"t": round(r[0] - period), "gen": round(r[1], 2), "load": round(r[2], 2),
            "soc": round(r[3], 2), "ecl": r[4]} for i, r in enumerate(orbit2) if i % 3 == 0]
gen = sum(r[1] for r in orbit2) / len(orbit2)
load = sum(r[2] for r in orbit2) / len(orbit2)
json.dump({"source": "sim/tools/power_budget.py run_profile('nominal', EOL), orbit 2",
           "period_s": round(period, 1), "beta_deg": round(orbit2[0][5], 1),
           "eclipse_s": sum(30 for s in samples if s["ecl"]),
           "gen_avg_w": round(gen, 1), "load_avg_w": round(load, 1),
           "margin_wh_per_orbit": round((gen - load) * period / 3600, 1),
           "peak_gen_w": round(max(r[1] for r in orbit2), 1),
           "samples": samples}, sys.stdout, indent=0)
