# 135 — GMSK/GFSK ran at 1/8 of their modulation index

**Status:** Fixed

## Summary

Found while building the blind receiver (v2, `docs/BLIND_RECEIVER_V2.md`).
Every GMSK and GFSK waveform the suite produced advanced the carrier phase by
**π·h/sps per bit instead of π·h**. At the default 8 samples per symbol,
"GMSK" moved 11.25° per bit instead of 90°: an effective index of h = 1/16.

Consequences:

* The occupied bandwidth was about 0.2 × Rb instead of the textbook 1.04 × Rb
  (99 % power, BT = 0.5). The radio's spectrum display showed a sliver.
* The separation between the two symbols' phase trajectories was 1/8 of
  nominal — well over 10 dB of detection performance. The four GFSK
  captures in `sim_captures/` (9600 Bd, 10–30 dB) could not be decoded by
  any receiver, the blind one included.
* v1's CPM receiver only decides the *sign* of the phase change, and the
  simulated links run with large margins, so nothing in the live chain or
  the existing tests noticed.

## Root cause

`packages/smo-rfsim/src/smo_rfsim/dsp/modulator.py`, `_modulate_cpm()`:

```python
upsampled = np.zeros(len(nrz) * self.sps)
upsampled[::self.sps] = nrz                         # one impulse per bit
freq_shaped = np.convolve(upsampled, self._gaussian, mode='same')   # unit SUM
phase = np.cumsum(freq_shaped) * (math.pi * h / self.sps)
```

The Gaussian is normalised to unit sum. Its convolution with a *single
impulse* per bit therefore has area 1 sample, and `cumsum × π·h/sps` gives
π·h/sps per bit. The frequency pulse of GMSK is a rectangle one symbol long,
Gaussian-filtered. The fix holds each NRZ level for the full symbol
(`np.repeat(nrz, sps)`), so the area is `sps` and the phase step is π·h.

## Fix

* `_modulate_cpm()` uses a rectangular NRZ (`np.repeat`). Measured: GMSK 90.0°
  per bit at sps 4, 8 and 16; GFSK 180·h°; GMSK 99 % bandwidth 1.03 × Rb.
* The recorder's sidecar now records `gfsk_mod_index` and
  `cpm_phase_per_bit: "pi*h"`, so a capture made after the fix can be told
  apart from one made before it.
* **Re-baseline:** `tools/regenerate_captures.py` rebuilds a capture from its
  own sidecar. Regenerating with the *old* modulator reproduces the old files
  to within float rounding (correlation 1.0000, rms difference 2e-5). The
  four `sim_captures/` recordings were regenerated with the fix; results are
  in `docs/BLIND_RECEIVER_V2_SWEEP.md`.

## Regression tests

`tests/test_rfsim/test_modulation_roundtrip.py::TestCPMPhasePerBit`: phase
per bit for GMSK at three sps values and for GFSK at three indices, and the
GMSK occupied bandwidth.
