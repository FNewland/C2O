# Blind Receiver (v2) — decoding a downlink with no prior knowledge

**Document ID:** EOSAT1-RF-BLIND-001
**Issue:** 1.0 — 2026-09-25
**Code:** `packages/smo-rfsim/src/smo_rfsim/blind/` · CLI `smo-rfsim-blind`
**Tests:** `tests/test_rfsim/test_blind_receiver.py` (30 tests)
**Sweep:** `docs/BLIND_RECEIVER_V2_SWEEP.md`, `tools/blind_sweep.py`

v1, the live ground-station receiver (`pipeline/rx_chain.py`), is **unchanged**.

---

## 1. Why a second receiver

v1 works on the live stream and is told the modulation and rate: the bridge
reads the spacecraft's active tier from telemetry and configures the
demodulator. If lock fails it searches one candidate at a time
(BPSK → QPSK → OQPSK → 8PSK). Each candidate gets a fixed dwell of 1.5–2.5 s,
and the search stops at the first sync marker.

v2 answers a different question: **given only a recording and its sample
rate, what was transmitted, and what did it say?** It works in batch on
chunks, so it can afford to be exhaustive. It pays for that with lag.

The design combines two approaches that are often treated as rivals:

| | Automatic modulation detection | Sync-marker verification |
|---|---|---|
| Question it answers | "What does this *look* like?" | "Is this *exactly* the right reading?" |
| Output | a ranked guess, with probabilities | yes / no, with near certainty |
| Cost | cheap, one pass | one full demodulation per guess |
| Fails on | low SNR, unusual signals | anything without a known marker |

v2 uses detection-style estimators to **rank** a short list of hypotheses.
The CCSDS attached sync marker (ASM, `1ACFFC1D`) **confirms** one of them. A
weak feature can only cost time, because every modulation family is still
tried at the best-supported symbol rates. It can never cost the signal.

## 2. The pipeline

```
 .cf32 + sample rate
   │
   ▼  frontend      remove DC → Welch PSD → flag CW lines → find band (centre, 99 % BW, SNR)
   │                → FFT cut to baseband → Doppler-rate fit (spectral registration) → dechirp
   │                → residual rate from the drift of an M-th power line (when there is one)
   ▼  estimators    |x|² line → Rs   (linear modulations)
   │                discriminator² line → Rs   (FSK, even low-index)
   │                x², x⁴, x⁸ lines → modulation order + carrier offset
   │                twin lines in x² (OQPSK) / x⁴ (π/4-DQPSK) → Rs and family
   │                envelope variance (noise-corrected) → constant envelope?
   │                → ranked (modulation, Rs) hypotheses
   ▼  demod         per hypothesis, feed-forward and vectorised:
   │                resample to 8 sps → RRC matched filter → Oerder–Meyr timing
   │                → M-th power frequency track → Viterbi–Viterbi phase
   │                → one SOFT bit stream per unresolved ambiguity
   │                  (rotation × spectral inversion × Gray/natural × OQPSK rail lead)
   ▼  sync          bit-level ASM correlation, both polarities → lattice test
   ▼  framing       ASM spacing → coded length → {conv+RS, conv, RS, none} → frame length
   │                decode (vectorised soft Viterbi, RS) → FECF check = CONFIRMED
   ▼  batch         growing acquisition window → chunked tracking → re-acquire on loss
                    → de-duplicate overlaps → ECSS packets
```

### 2.1 Estimators (the detection half)

* **Symbol rate.** A linearly modulated signal's power `|x(t)|²` repeats
  statistically every symbol. Its spectrum therefore carries a discrete line
  at Rs. v2 finds that line with parabolic interpolation and measures its
  local contrast. A global median is useless here, because a band-limited
  envelope spectrum is exactly zero over most of the band.
* **FSK has no envelope line.** Its envelope is constant, but its
  instantaneous frequency (the discriminator output) has a line at Rs. For a
  low-index FSK, almost all the power sits in a band narrower than Rs. The
  symbol transitions live in the weak skirts, so that line only appears on a
  cut several times wider than the 99 % bandwidth.
* **Modulation order.** Raising M-PSK to the M-th power strips the data and
  leaves a tone at M·f₀. BPSK shows a tone at M=2, QPSK only at M=4, and
  8PSK only at M=8. The smallest M with a line gives the order. The search
  is limited to ±5 % of the bandwidth. Any wider and the cyclic *side*-lines
  (at M·f₀ ± k·Rs) masquerade as the carrier.
* **OQPSK.** Its square has no line at 2f₀ (BPSK does). It has a *pair* at
  2f₀ ± Rs, symmetric about the x⁴ carrier line: the half-symbol stagger made
  visible. π/4-DQPSK shows the analogous pair in x⁴ at 4f₀ ± Rs/2.

### 2.2 Verification (the decisive half)

A 32-bit ASM tolerating 3 bit errors appears in random bits about once per
780 000 positions. One hit therefore proves little, especially after 32
ambiguity variants of an 8PSK hypothesis. v2 accepts a hypothesis only on
one of these:

1. **A lattice**: three or more markers at one fixed spacing, **and** a
   coding scheme that makes a frame's FECF (CRC-16) check. That is the
   normal path.
2. **A single marker whose frame closes**: RS(255,223) decodes (random data
   essentially never does) and the CRC checks. A CRC-only closure must be
   corroborated by another marker exactly one frame later. Scanning a few
   thousand candidate lengths against a 16-bit CRC finds a false match a few
   per cent of the time. An early build confirmed a false 8PSK this way,
   which is why this guard exists.

### 2.3 Framing discovered, not configured

The ASM spacing gives the *coded* frame size C. Each CCSDS concatenation
maps C to exactly one transfer-frame length:

| Coding | Coded bytes for a 1115-byte frame |
|---|---|
| none | 1115 |
| RS(255,223) | 1115 + 5·32 = 1275 |
| conv(7,½) | 2·1115 + 2 = 2232 |
| conv(7,½) + RS | 2·1275 + 2 = 2552 |

v2 decodes a frame under each option and keeps the one whose FECF checks.
The SCID then comes out of the frame header. The EOSAT-1 ladder is
recovered exactly:

| Tier | Recovered | Frame air time |
|---|---|---|
| SAFE | BPSK 1000 Bd, conv+RS, 1115 B | 20.449 s |
| LOW | BPSK 16 000 Bd, conv+RS, 1115 B | 1.278 s |
| HIGH | QPSK 64 000 Bd, RS, 1115 B | 0.080 s |

## 3. Batch operation and lag

* **Acquisition** starts on a 4 s window. If a band is present but nothing
  is provable, the window doubles (up to 96 s). If there is no band at all
  (before AOS), the window slides on. SAFE needs a 32 s window, because the
  markers have to repeat and a SAFE frame lasts 20.4 s.
* **Tracking** chunks are `max(2 s, 4 × frame air time)` long and overlap by
  1.5 frames. They are **derived from the discovered frame air time, never a
  fixed timeout against the RF chain** (the rule from the July test-harness
  fix). Carrier, Doppler rate, timing and the phase-ambiguity branch are
  re-estimated in every chunk, because they drift.
* **Re-acquisition** happens after two chunks with no good frame. It starts
  from the end of the last good frame, so a mid-pass rate switch
  (LOW → HIGH) is caught where it happened, not where it was noticed.
* **Lag** per frame = (end of its chunk − end of the frame on air) + chunk
  processing time. The table below shows lag and speed on a laptop-class
  CPU:

| Scenario | Result | Lag after last bit | Speed |
|---|---|---|---|
| LOW, 20 frames, 6 dB, 500 Hz/s Doppler | 162/162 packets | 0.7–5.3 s | 0.5× real time |
| HIGH, 150 frames, 10 dB, 500 Hz/s | 1236/1236 | 0.9–6.6 s | 0.6× |
| SAFE, 5 frames, 6 dB, 40 Hz/s | 39/39 | 3–46 s | 0.2× |
| AOS → LOW → HIGH → LOS | 550/550, 2 segments | 1.3–6.7 s | ~2× |

A real-time factor below 1 means batch decoding keeps up with the pass. The
lag is simply the chunk: at SAFE rate you must wait for whole 20 s frames,
whatever the receiver.

## 4. Where it breaks down, and why

These are the limits that make good discussion material:

* **No sync marker, no confirmation.** v2 identifies a signal's family, rate
  and carrier without one. Without a marker it cannot *prove* the reading.
  For non-cooperative signals, detection is the whole answer.
* **8PSK needs about 10 dB** in-band before the 8th-power phase estimate and
  the decoder hold. That is the physics, and the reason the ladder stops at
  QPSK.
* **HIGH is RS-only.** Uncoded QPSK at 6 dB gives about a 2 % bit error
  rate, far beyond what RS(255,223) can correct. No receiver decodes that.
  With 35 dB of margin, the flown link never gets close.
* **Uncoded, noncoherent FSK is the weakest case.** The regenerated
  `sim_captures/` GFSK passes carry no FEC. At 12 dB, about 1 frame in 5
  survives; at 18 dB and above, over 90 % do. See the sweep document.

## 5. Finding: GMSK/GFSK ran at 1/8 of their modulation index (defect #135, fixed)

Testing v2 exposed a bug in the existing `dsp/modulator.py` CPM path.
`_modulate_cpm` upsampled the NRZ as one impulse per bit and convolved it
with a Gaussian normalised to unit *sum*. Each bit therefore contributed a
frequency area of 1 sample instead of `sps`, and the phase advanced `π·h/sps`
per bit rather than `π·h`: **11.25° per bit for GMSK instead of 90°**. The
signals were about 1/8 of their proper bandwidth and far harder to detect.
None of the four GFSK captures in `sim_captures/` could be decoded by any
receiver.

**Fixed 2026-09-25.** The NRZ level is held for the full symbol before
Gaussian filtering. GMSK now advances 90° per bit and occupies 1.03 × Rb
(99 %). A companion defect, #136, was also fixed: the configured
`gfsk_mod_index` / `gmsk_bt` never reached the transmitter. The captures were
regenerated from their own sidecars with `tools/regenerate_captures.py`. The
before/after results are in `docs/BLIND_RECEIVER_V2_SWEEP.md`.

## 6. Using it

```bash
# make a test pass (truth goes in the .json; the decoder never reads it)
smo-rfsim-blind synth --tier LOW --frames 20 --snr-db 7 --doppler-rate 400 \
    --out sim_captures/blind --name low_pass

# decode it blind; --score compares with the truth AFTER decoding
smo-rfsim-blind decode sim_captures/blind/low_pass.cf32 --score \
    --json report.json --packets out/
```

```python
from smo_rfsim.blind import BlindReceiver, BatchBlindDecoder, load_cf32
acq = BlindReceiver().acquire(samples, fs)       # one window
print(acq.summary()); print(acq.trials)          # every hypothesis and verdict
rep = BatchBlindDecoder().run(load_cf32(path), fs, path)   # a whole pass
```

The only metadata read is the **sample rate**, from `--fs` or the
recorder's sidecar. It is a property of the recorder, not of the signal.

## 7. Suggested student exercises

1. Run `decode -v` on a LOW pass and read the hypothesis table. Then make an
   OQPSK pass (`--modulation OQPSK`) and explain why QPSK ranks second, not
   first.
2. Lower `--snr-db` in 1 dB steps on LOW and on HIGH. Explain why LOW
   survives far lower (conv(7,½) with soft decisions versus RS alone).
3. Make a SAFE pass and explain the acquisition window and the lag. What
   would a real station do instead? (Predicted Doppler plus a known
   schedule.)
4. Change the ASM tolerance (`BlindReceiver(asm_max_errors=…)`). Measure
   false hits in noise and the success rate at low SNR. Relate the result
   to the lattice rule in §2.2.
