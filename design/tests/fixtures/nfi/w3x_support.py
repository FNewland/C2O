"""Test support for agent X's wave-3 work (3.X1–3.X3).

Until the wave-3 merge this module held stand-in collectors that built the other agents' export
sections from the v2 baseline files, and wrote the v2 function tree straight into the store. Since
the merge every section is real (its owner's collector) and the function tree comes from R's bulk
import in the seed, so the stand-ins are gone and the tests read the study as the tool builds it.
"""
from __future__ import annotations


def counts_by_stage(reqs: list[dict]) -> dict[str, int]:
    """Requirements per closing stage, counted as the V counts them (store rows, without SN-*,
    OBJ-* and generated IR-* rows)."""
    out: dict[str, int] = {}
    for r in reqs:
        if r.get("generated_interface") or r.get("level") == "stakeholder" or str(r.get("code") or "").startswith(("OBJ-", "SN-", "IR-")):
            continue
        st = str(r.get("verification_phase") or "").upper()
        if st:
            out[st] = out.get(st, 0) + 1
    return out


__all__ = ["counts_by_stage"]
