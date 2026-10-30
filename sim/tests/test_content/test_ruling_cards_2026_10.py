"""The three cards added by the amended rulings of 2026-10-30.

* NOM-014 End-of-Life Disposal (ruling Q3 as amended: a perigee-lowering burn
  sized for re-entry within 5 years at solar minimum, then passivation);
* CTG-029 Gyro Failure Recovery and CTG-030 Telecommand Rejection and
  Verification Failure (ruling Q22 as amended: the ops book's temporary
  CTG-B01 / CTG-B02 become real simulator cards).

Every telecommand a card names must exist in ``tc_catalog.yaml`` with the
service, subtype, func_id and argument names the card writes; every
``name (0xID)`` parameter reference must exist in ``parameters.yaml`` under that
name; every event and every procedure the card points to must exist; and the
French card must command exactly what the English card commands.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO / "configs" / "eosat1"
PROC_DIR = CONFIG / "procedures"
FR_PROC_DIR = CONFIG / "i18n" / "fr" / "procedures"

_src = REPO / "packages" / "smo-common" / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from smo_common.procedures import markdown_steps  # noqa: E402

NEW_CARDS = {
    "NOM-014": ("nominal/eol_disposal.md", "nominal"),
    "CTG-029": ("contingency/gyro_failure.md", "contingency"),
    "CTG-030": ("contingency/tc_rejection.md", "contingency"),
}


def _catalog() -> dict[str, dict]:
    data = yaml.safe_load((CONFIG / "commands" / "tc_catalog.yaml").read_text("utf-8"))
    out: dict[str, dict] = {}
    for cmd in data["commands"]:
        out[cmd["name"].upper()] = cmd
        for alias in cmd.get("aliases", []) or []:
            out.setdefault(str(alias).upper(), cmd)
    return out


CATALOG = _catalog()
PARAMS = {int(p["id"]): p["name"] for p in yaml.safe_load(
    (CONFIG / "telemetry" / "parameters.yaml").read_text("utf-8"))["parameters"]}
EVENTS = {int(e["id"]): e["name"] for e in yaml.safe_load(
    (CONFIG / "events" / "event_catalog.yaml").read_text("utf-8"))["events"]}
INDEX = {e["id"]: e for e in yaml.safe_load(
    (PROC_DIR / "procedure_index.yaml").read_text("utf-8"))["procedures"]}

RE_TC = re.compile(r"\*\*TC:\*\*\s*`([A-Z][A-Z0-9_]+)(?:\(([^)]*)\))?`([^\n]*)")
RE_FUNC = re.compile(r"func_id\s*=?\s*(\d+)")
RE_SVC = re.compile(r"Service\s+(\d+),\s*Subtype\s+(\d+)")
RE_PARAM = re.compile(r"`([a-z]{2,8}\.[a-z][a-z0-9_]*)`\s*\(\s*(0x[0-9A-Fa-f]{4})\s*\)")
RE_EVENT = re.compile(r"\b([A-Z][A-Z0-9_]{3,})\s*\(\s*(0x[0-9A-Fa-f]{4})\s*\)"
                      r"|event\s+(0x[0-9A-Fa-f]{4})\s+([A-Z][A-Z0-9_]{3,})")
RE_PROC = re.compile(r"\b((?:LEOP|COM|NOM|CTG|EMG)-\d{3})\b")


def _text(rel: str, fr: bool = False) -> str:
    return ((FR_PROC_DIR if fr else PROC_DIR) / rel).read_text("utf-8")


@pytest.mark.parametrize("card_id", sorted(NEW_CARDS))
def test_card_is_indexed_with_its_file_and_category(card_id):
    rel, category = NEW_CARDS[card_id]
    entry = INDEX.get(card_id)
    assert entry is not None, f"{card_id} missing from procedure_index.yaml"
    assert entry["file"] == rel
    assert entry["category"] == category
    assert (PROC_DIR / rel).is_file()
    assert (FR_PROC_DIR / rel).is_file(), f"{card_id} has no French card"
    assert _text(rel).startswith(f"# {card_id}")


@pytest.mark.parametrize("card_id", sorted(NEW_CARDS))
@pytest.mark.parametrize("fr", [False, True], ids=["en", "fr"])
def test_every_telecommand_exists_with_its_routing_and_arguments(card_id, fr):
    text = _text(NEW_CARDS[card_id][0], fr)
    found = RE_TC.findall(text)
    assert found, f"{card_id} names no telecommand"
    for name, args, tail in found:
        cmd = CATALOG.get(name)
        assert cmd is not None, f"{card_id}: {name} is not in tc_catalog.yaml"
        svc = RE_SVC.search(tail)
        if svc:
            assert (int(svc.group(1)), int(svc.group(2))) == (
                cmd["service"], cmd["subtype"]), f"{card_id}: {name} routing"
        func = RE_FUNC.search(tail)
        if func:
            assert int(func.group(1)) == cmd.get("func_id"), \
                f"{card_id}: {name} func_id {func.group(1)} != {cmd.get('func_id')}"
        fields = {f["name"] for f in cmd.get("fields", []) or []}
        for arg in filter(None, (a.strip() for a in (args or "").split(","))):
            key = arg.split("=", 1)[0].strip()
            assert key in fields, f"{card_id}: {name} has no argument {key!r}"


@pytest.mark.parametrize("card_id", sorted(NEW_CARDS))
@pytest.mark.parametrize("fr", [False, True], ids=["en", "fr"])
def test_every_parameter_reference_exists_under_its_name(card_id, fr):
    text = _text(NEW_CARDS[card_id][0], fr)
    refs = RE_PARAM.findall(text)
    assert refs, f"{card_id} references no telemetry"
    for name, pid in refs:
        assert int(pid, 16) in PARAMS, f"{card_id}: {pid} not in parameters.yaml"
        assert PARAMS[int(pid, 16)] == name, \
            f"{card_id}: {pid} is {PARAMS[int(pid, 16)]}, card says {name}"


@pytest.mark.parametrize("card_id", sorted(NEW_CARDS))
def test_every_event_and_procedure_reference_exists(card_id):
    text = _text(NEW_CARDS[card_id][0])
    for m in RE_EVENT.finditer(text):
        name, eid = (m.group(1), m.group(2)) if m.group(1) else (m.group(4), m.group(3))
        if name in CATALOG:            # "PROP_SET_BURN (0x...)" is not an event
            continue
        if int(eid, 16) in EVENTS:
            assert EVENTS[int(eid, 16)] == name, f"{card_id}: event {eid}"
    for pid in set(RE_PROC.findall(text)) - {card_id}:
        assert pid in INDEX, f"{card_id} points to {pid}, which is not indexed"


@pytest.mark.parametrize("card_id", sorted(NEW_CARDS))
def test_french_card_commands_exactly_what_the_english_card_commands(card_id):
    rel = NEW_CARDS[card_id][0]

    def cmds(fr):
        steps = markdown_steps(_text(rel, fr), CATALOG)[0]
        return [(s.get("service"), s.get("subtype"), s.get("mnemonic"))
                for s in steps if s.get("type") == "command"]

    assert cmds(False) == cmds(True)


def test_disposal_card_matches_the_prop_budget():
    """The burn the card flies is the burn prop.yaml budgets."""
    text = _text("nominal/eol_disposal.md")
    prop = (CONFIG / "subsystems" / "prop.yaml").read_text("utf-8")
    assert "34.3 m/s" in text and "34.3" in prop
    assert "390 km" in text and "390 km" in prop
    six = re.findall(r"PROP_SET_BURN\(dv_m_s=([0-9.]+), direction=1", text)
    assert six and float(six[0]) * 6 == pytest.approx(34.3, abs=0.05)
