# Recorded RF captures

The baseband recordings (`*.cf32`, complex float32 IQ, 60 MB each) are **not stored in git**. Download them from the
[**captures-2026-10** release](https://github.com/FNewland/C2O/releases/tag/captures-2026-10) and place them in this folder. Their `*.json` and `*.sigmf-meta` descriptions stay here.

| File | Description |
|---|---|
| `EOSAT1-SIM_0_20260705T191709Z_401.4150MHz.cf32` | Simulator downlink recorded 2026-07-05 at 401.415 MHz |
| `eosat1_best.cf32`, `eosat1_tuned2.cf32`, `eosat1_tuned_bison.cf32` | Tuned blind-receiver test captures |

To recreate them instead: `python3 tools/regenerate_captures.py`.
