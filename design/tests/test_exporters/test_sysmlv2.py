"""SCDF-160 Phase 2d — SysML v2 textual export smoke test."""
from __future__ import annotations

import re

import pytest

from tests.test_repositories.conftest import db_factory, study  # noqa: F401
from tests.test_exporters.test_capella import _seed, clean_stores  # noqa: F401


def test_identifier_escaping():
    from spacecdf_agents.exporters.sysmlv2 import sysml_identifier
    assert sysml_identifier("Flight Software") == "Flight_Software"
    assert sysml_identifier("28V bus") == "'28V bus'"
    assert sysml_identifier("part") == "'part'"
    assert sysml_identifier("it's") == "it_s"
    assert sysml_identifier("28V it's") == "'28V it\\'s'"
    assert sysml_identifier("", "x") == "x"


def test_validator_catches_unbalanced():
    from spacecdf_agents.exporters.sysmlv2 import validate_sysml
    assert validate_sysml("package P { part a; }") == []
    assert validate_sysml("package P { part a; ") != []
    assert validate_sysml("package P { doc /* } */ }") == []
    assert validate_sysml("part a;") != []


async def test_export_smoke(db_factory, study, clean_stores):  # noqa: F811
    from spacecdf_agents.exporters.sysmlv2 import export_study_sysml, validate_sysml
    from spacecdf_server.routers.requirements import _requirements

    await _seed(study)
    _requirements["SR-1"]["element_id"] = "eps"
    text = await export_study_sysml(study)
    assert validate_sysml(text) == []
    assert re.search(r"^package \S+ \{", text, re.M)
    for kw in ("part def Subsystem;", "part def Component;", "part def Software;",
               "part Spacecraft : System {", "part EPS : Subsystem {", "part PCDU : Component",
               "attribute mass_kg = 4.5;  // unit: kg", "attribute power_avg_w = 30.0;  // unit: W",
               "action def Fn_Generate_power;", "action Generate_power : Fn_Generate_power {",
               "action Distribute_power : Fn_Distribute_power;",
               "allocate Generate_power to EPS;", "allocate Distribute_power to PCDU;",
               "connection '28V bus' connect PCDU to OBDH;", "connection TM_TC connect OBDH to EPS;",
               "requirement def Req_SR_001;", "requirement SR_001 : Req_SR_001 {",
               "doc /* The EPS shall deliver 30 W average. */", "subject subj : Subsystem;",
               "satisfy SR_001 by EPS;"):
        assert kw in text, kw
    # nesting: PCDU inside EPS inside Spacecraft
    assert text.index("part Spacecraft") < text.index("part EPS") < text.index("part PCDU") < text.index("part OBDH")
    # deterministic
    assert text == await export_study_sysml(study)
