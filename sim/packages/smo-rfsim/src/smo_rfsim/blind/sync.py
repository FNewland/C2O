"""The verifier: find the CCSDS sync marker, and prove it repeats.

A 32-bit ASM tolerating 3 bit errors turns up in random bits about once per
780 000 positions, so one hit proves little. The same marker recurring at a
fixed spacing, however, is essentially impossible by chance: three hits on
one lattice is the acceptance bar, or a single hit whose frame then decodes
with a valid checksum (see ``framing``).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..ccsds.asm import ASM_BYTES

ASM_BITS = np.unpackbits(np.frombuffer(ASM_BYTES, dtype=np.uint8))
ASM_PM = (1.0 - 2.0 * ASM_BITS.astype(np.float64))      # bit 0 -> +1
ASM_LEN_BITS = 32


@dataclass
class SyncResult:
    positions: np.ndarray                  # bit index of each hit
    signs: np.ndarray                      # +1 normal, -1 inverted stream
    sign: int = 1                          # dominant polarity
    period_bits: int | None = None         # ASM-to-ASM spacing
    aligned: list = field(default_factory=list)   # hits on the lattice

    @property
    def n_hits(self) -> int:
        return int(len(self.positions))

    @property
    def n_aligned(self) -> int:
        return len(self.aligned)

    def score(self) -> tuple:
        return (self.n_aligned, self.n_hits)


def correlate(soft: np.ndarray, max_errors: int = 3) -> tuple[np.ndarray,
                                                              np.ndarray]:
    """Bit-level ASM search on hard decisions (both polarities)."""
    if len(soft) < ASM_LEN_BITS:
        return np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64)
    h = np.where(np.asarray(soft) >= 0, 1.0, -1.0)
    c = np.correlate(h, ASM_PM, mode="valid")
    thr = ASM_LEN_BITS - 2 * max_errors
    idx = np.nonzero(np.abs(c) >= thr - 1e-9)[0]
    return idx.astype(np.int64), np.sign(c[idx]).astype(np.int64)


def analyse(soft: np.ndarray, max_errors: int = 3,
            min_period_bits: int = 256) -> SyncResult:
    pos, sg = correlate(soft, max_errors)
    res = SyncResult(pos, sg)
    if len(pos) == 0:
        return res
    res.sign = 1 if np.sum(sg > 0) >= np.sum(sg < 0) else -1
    p = pos[sg == res.sign]
    if len(p) == 0:
        return res
    res.aligned = [int(p[0])]
    if len(p) < 2:
        return res
    # Candidate periods from pairwise spacings of the first hits.
    head = p[:60]
    diffs = (head[None, :] - head[:, None]).ravel()
    diffs = np.unique(diffs[diffs >= min_period_bits])
    best = (1, None, [int(p[0])])
    for d in diffs[:400]:
        # Hits whose offset from some anchor is a multiple of d (+/-1 bit).
        for anchor in head[:8]:
            r = (p - anchor) % d
            on = (r <= 1) | (r >= d - 1)
            n = int(np.sum(on))
            if n > best[0] or (n == best[0] and best[1] is not None
                               and d < best[1] and n >= 2):
                best = (n, int(d), [int(v) for v in p[on]])
    if best[1] is not None:
        res.period_bits = best[1]
        res.aligned = best[2]
    return res
