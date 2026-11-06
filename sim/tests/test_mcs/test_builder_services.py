"""The command builder's Service list covers every service the TC catalogue
uses. It was a fixed list without S2, so S2_* device commands (e.g. the
magnetometer in LEOP-007) were sent as TC(0,1) and rejected."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MCS_JS = ROOT / "packages/smo-mcs/src/smo_mcs/static/modern/mcs.js"
CMDS = ROOT / "configs/eosat1/commands"


def _catalogue_services() -> set[int]:
    out = set()
    for f in CMDS.glob("*.yaml"):
        doc = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        for c in doc.get("commands", []) if isinstance(doc, dict) else []:
            if isinstance(c, dict) and isinstance(c.get("service"), int):
                out.add(c["service"])
    return out


def test_service_list_is_derived_from_the_catalogue():
    src = MCS_JS.read_text(encoding="utf-8")
    body = src.split("function knownServices()")[1].split("\n}")[0]
    assert "S.tcCatalog" in body
    assert "[3, 5, 6, 8, 9, 11, 12, 15, 17, 19, 20].map" not in src


def test_base_services_cover_the_catalogue():
    src = MCS_JS.read_text(encoding="utf-8")
    line = next(l for l in src.splitlines() if l.startswith("const BASE_SERVICES"))
    base = {int(x) for x in line.split("[")[1].split("]")[0].split(",")}
    assert 2 in base
    missing = _catalogue_services() - base - {1}
    assert not missing, f"catalogue services not in BASE_SERVICES (still added at run time): {missing}"
