#!/usr/bin/env python3
"""gen_failure_strings.py — the failure catalogue's English text, as YAML.

The instructor console's inject form is generated from each subsystem model's
``FAILURE_SPECS`` (smo_simulator/failure_catalog.py): failure labels, effect
text, parameter labels and enum value labels. They are English Python strings,
and the repo's French mechanism is the YAML overlay (tools/i18n: kind:id:field
keys in configs/eosat1/i18n/fr/db.yaml, looked up in the browser with tdb()).
This tool writes those strings to configs/eosat1/i18n/en/failure_catalog.yaml
so `python3 -m tools.i18n extract` picks them up like any other config prose
(rules fail / failsub / failparam / failval in i18n.yaml).

The output is GENERATED: never edit it by hand. A test fails when it is stale.

Usage:
    python3 tools/gen_failure_strings.py            # rewrite the file
    python3 tools/gen_failure_strings.py --check    # exit 1 if it is stale
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for _pkg in ("smo-common", "smo-simulator"):
    _src = REPO / "packages" / _pkg / "src"
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

OUTPUT = REPO / "configs" / "eosat1" / "i18n" / "en" / "failure_catalog.yaml"

HEADER = """# GENERATED FILE — DO NOT EDIT BY HAND.
# Written by tools/gen_failure_strings.py from the models' FAILURE_SPECS
# (smo_simulator/failure_catalog.py). It only carries the English text of the
# instructor inject form for the French overlay (tools/i18n rules fail,
# failsub, failparam, failval -> configs/eosat1/i18n/fr/db.yaml). The
# simulator does not read it.
"""


def _q(v) -> str:
    return json.dumps(str(v), ensure_ascii=False)


def build() -> str:
    from smo_simulator import failure_catalog as fc
    doc = fc.to_dict()
    out = [HEADER.rstrip("\n"), "subsystems:"]
    for sub in doc["subsystems"]:
        out.append(f"  - name: {sub['name']}")
        out.append(f"    label: {_q(sub['label'])}")
        out.append("    failures:")
        for f in sub["failures"]:
            out.append(f"      - name: {f['name']}")
            out.append(f"        label: {_q(f['label'])}")
            if f.get("effect"):
                out.append(f"        effect: {_q(f['effect'])}")
            if f.get("notes"):
                out.append(f"        notes: {_q(f['notes'])}")
            params = ([f["magnitude"]] if f.get("magnitude") else []) + list(f.get("params") or [])
            if not params:
                continue
            out.append("        params:")
            for p in params:
                out.append(f"          - name: {p['name']}")
                out.append(f"            label: {_q(p.get('label') or p['name'])}")
                if p.get("description"):
                    out.append(f"            description: {_q(p['description'])}")
                vals = [(v, lab) for v, lab in zip(p.get("values") or [], p.get("value_labels") or [])
                        if str(lab).upper() != str(v).upper()]
                if vals:
                    out.append("            values:")
                    for v, lab in vals:
                        out.append(f"              - {{value: {_q(v)}, label: {_q(lab)}}}")
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if the committed file is stale")
    ap.add_argument("--output", type=Path, default=OUTPUT)
    a = ap.parse_args(argv)
    text = build()
    if a.check:
        if not a.output.exists() or a.output.read_text(encoding="utf-8") != text:
            print(f"{a.output} is stale: run python3 tools/gen_failure_strings.py")
            return 1
        return 0
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(text, encoding="utf-8")
    print(f"wrote {a.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
