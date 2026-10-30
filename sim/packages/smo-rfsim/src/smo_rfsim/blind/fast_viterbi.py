"""Vectorised soft-decision Viterbi decoder for the CCSDS K=7 r=1/2 code.

Same code as ``ccsds/convolutional.py`` (G1=0x79, G2=0x5B, encoder flushed
with K-1 zero bits), but the add-compare-select runs over all 64 states at
once in numpy instead of in nested Python loops. On a 1115-byte frame that is
roughly 50-100x faster than ``ccsds/viterbi.py``, which is what makes batch
decoding of a whole LOW- or SAFE-rate pass practical.

It also accepts *soft* input: one real number per coded bit, positive for a
received ``0`` and negative for a received ``1`` (the natural output of a
BPSK matched filter, or a max-log LLR). Soft decisions are worth about 2 dB
over hard ones — hard decisions are still accepted (``decode_hard``).
"""
from __future__ import annotations

import numpy as np

from ..ccsds.convolutional import G1, G2, K

NUM_STATES = 1 << (K - 1)          # 64


def _parity(v: int) -> int:
    return bin(v).count("1") & 1


# For every NEXT state n there are two predecessor registers
#   reg = n | (msb << 6),  msb in {0, 1}
# whose previous state is reg >> 1 and whose input bit is n & 1.
_PRED = np.zeros((2, NUM_STATES), dtype=np.int64)
_EXP1 = np.zeros((2, NUM_STATES), dtype=np.float64)   # +1 for bit 0, -1 for 1
_EXP2 = np.zeros((2, NUM_STATES), dtype=np.float64)
for _n in range(NUM_STATES):
    for _msb in range(2):
        _reg = _n | (_msb << 6)
        _PRED[_msb, _n] = _reg >> 1
        _EXP1[_msb, _n] = 1.0 - 2.0 * _parity(_reg & G1)
        _EXP2[_msb, _n] = 1.0 - 2.0 * _parity(_reg & G2)


def decode_soft(soft: np.ndarray, n_data_bits: int | None = None,
                terminated: bool = True) -> np.ndarray:
    """Decode a soft coded-bit stream; returns decoded *bits* (uint8).

    ``soft`` holds one value per coded bit (G1, G2 interleaved), positive
    meaning "0". ``n_data_bits`` trims the K-1 flush bits (and any padding).
    ``terminated`` starts the traceback from state 0, as the encoder is
    flushed; set False when decoding a window cut out of a longer stream.
    """
    soft = np.asarray(soft, dtype=np.float64)
    n_steps = len(soft) // 2
    if n_steps == 0:
        return np.zeros(0, dtype=np.uint8)
    r1 = soft[0:2 * n_steps:2]
    r2 = soft[1:2 * n_steps:2]

    pm = np.full(NUM_STATES, -1e18)
    pm[0] = 0.0                                   # encoder starts in state 0
    decisions = np.zeros((n_steps, NUM_STATES), dtype=np.uint8)
    pred0, pred1 = _PRED[0], _PRED[1]
    e10, e11, e20, e21 = _EXP1[0], _EXP1[1], _EXP2[0], _EXP2[1]
    for t in range(n_steps):
        a, b = r1[t], r2[t]
        m0 = pm[pred0] + a * e10 + b * e20
        m1 = pm[pred1] + a * e11 + b * e21
        choose1 = m1 > m0
        decisions[t] = choose1
        pm = np.where(choose1, m1, m0)
        pm -= pm.max()                             # keep metrics bounded

    state = 0 if terminated else int(np.argmax(pm))
    bits = np.zeros(n_steps, dtype=np.uint8)
    for t in range(n_steps - 1, -1, -1):
        bits[t] = state & 1
        msb = decisions[t, state]
        state = int(_PRED[msb, state])
    if n_data_bits is not None:
        bits = bits[:n_data_bits]
    return bits


def decode_hard(encoded: bytes, original_length: int | None = None) -> bytes:
    """Drop-in equivalent of ``ccsds.viterbi.decode`` (hard decisions)."""
    bits = np.unpackbits(np.frombuffer(encoded, dtype=np.uint8))
    soft = 1.0 - 2.0 * bits.astype(np.float64)
    n_data = None if original_length is None else original_length * 8
    out = decode_soft(soft, n_data)
    out = out[: (len(out) // 8) * 8]
    return bytes(np.packbits(out))


def decode_soft_bytes(soft: np.ndarray, original_length: int) -> bytes:
    """Soft decode to exactly ``original_length`` bytes."""
    bits = decode_soft(soft, original_length * 8)
    if len(bits) < original_length * 8:
        bits = np.concatenate([bits, np.zeros(original_length * 8 - len(bits),
                                              dtype=np.uint8)])
    return bytes(np.packbits(bits))
