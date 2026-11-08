"""The console's built-in displays reference only parameters an operator can receive.

The payload page showed SNR (0x0616) and image quality (0x060D) as key
parameters and in its schematic, but both are instructor truth: the boxes read
"no data" forever (2026-11-08).
"""
import re
from pathlib import Path

import yaml

SIM = Path(__file__).resolve().parents[2]
STATIC = SIM / "packages/smo-mcs/src/smo_mcs/static/modern"


def _instructor_only() -> set[str]:
    params = yaml.safe_load((SIM / "configs/eosat1/telemetry/parameters.yaml").read_text())["parameters"]
    return {f"0x{p['id']:04X}" for p in params if p.get("visibility") == "instructor"}


def test_subsystem_pages_and_schematics_use_operator_parameters():
    hidden = _instructor_only()
    js = (STATIC / "mcs.js").read_text()
    start = js.index('  eps: { title: "Electrical power"')
    block = js[start:js.index("  obd: { title", start) + 1500]
    refs = set(re.findall(r'"(0x[0-9A-F]{4})"', block))
    svg = (STATIC / "schematics.svg").read_text()
    refs |= set(re.findall(r'data-param="(0x[0-9A-F]{4})"', svg))
    bad = sorted(refs & hidden)
    assert not bad, f"instructor-only parameters on the operator console: {bad}"
