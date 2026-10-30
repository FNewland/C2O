"""Blind receiver (v2) — decode a CCSDS downlink with no prior knowledge.

The live receiver (``pipeline/rx_chain.py``, v1) is told the modulation and
rate by the simulator and only falls back to a sequential search when it
loses lock. v2 is told nothing but the sample rate. It works on recordings
in batch, with a lag, which buys it the freedom to be exhaustive:

    frontend    find the band, notch CW lines, cut it out, remove Doppler rate
    estimators  cyclostationary features -> ranked (modulation, rate) list
    demod       feed-forward demodulators, one soft stream per ambiguity
    sync        CCSDS ASM search + lattice test (the verifier)
    framing     coded length -> coding scheme -> frame length, by FECF/RS
    receiver    BlindReceiver.acquire() / .decode()
    batch       chunked, lagged decoding of a whole pass
    synth       realistic test recordings with ground truth
    cli         ``smo-rfsim-blind decode|synth``

See docs/BLIND_RECEIVER_V2.md.
"""
from .batch import BatchBlindDecoder, BatchReport, load_cf32
from .receiver import Acquisition, BlindReceiver, SignalDescription

__all__ = ["BlindReceiver", "BatchBlindDecoder", "BatchReport",
           "SignalDescription", "Acquisition", "load_cf32"]
