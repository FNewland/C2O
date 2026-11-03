"""Cards power a unit's EPS line before commanding it, and check the
spacecraft before shedding (Franz's rulings P1 and P3, 2026-11-02).

The per-role walkthrough found two families of refused commands:

* P1 — `HEATER_*_ON` sent with the heater's EPS line dark (lines 5/6/8 were
  OFF after commissioning): refused S1.8 "EPS power line N is OFF", so in a
  contingency the team could not switch a heater on;
* P3 — load-shed cards that shed from the ground what on-board FDIR had
  already switched off (refused S1.8, the unit's mode frozen), and recovery
  steps that sent mode commands before re-powering the line.

These gates read the card TEXT (EN and FR) so a later edit cannot quietly
reintroduce either pattern:

1. every `**TC:**` that switches a heater ON, or puts a unit back into an
   operating mode, is preceded in the same step by `EPS_POWER_ON` of that
   unit's line (or, for the AOCS, a branch proving the line is ON);
2. every ground shed command in the load-shed cards is guarded by a BRANCH on
   that load's `eps.pl_*` line state.
"""
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
EN = REPO / "configs" / "eosat1" / "procedures"
FR = REPO / "configs" / "eosat1" / "i18n" / "fr" / "procedures"

RE_STEP = re.compile(r"^#{2,4} ")
RE_TC = re.compile(r"^\s*\*\*TC:\*\*\s*`([A-Z0-9_]+)\(?([^`)]*)\)?`")

#: command(args) -> EPS line index that must be powered first. Heaters: in
#: EVERY card (P1). Mode/PA restores: in the load-shed cards (P3), where the
#: line may have been opened on board; nominal cards run with the line on.
NEEDS_LINE_ALL = [
    (re.compile(r"^HEATER_BATTERY$"), r"on=1", 5),
    (re.compile(r"^HEATER_OBC$"), r"on=1", 6),
    (re.compile(r"^HEATER_THRUSTER$"), r"on=1", 8),
]
NEEDS_LINE_SHED = [
    (re.compile(r"^PAYLOAD_SET_MODE$"), r"mode=[1-9]", 3),
    (re.compile(r"^TTC_PA_ON$"), r"", 2),
]
#: the AOCS: EPS_POWER_ON(7) or a BRANCH establishing the line is ON.
AOCS_OK = re.compile(r"EPS_POWER_ON\(line_index=7\)|`eps\.pl_aocs_wheels == 1`")

#: Ground shed command -> the line-state BRANCH that must guard it.
SHED_GUARD = {
    "PAYLOAD_SET_MODE(mode=0)": "eps.pl_payload == 1",
    "FPA_COOLER(on=0)": "eps.pl_fpa_cooler == 1",
    "TTC_PA_OFF": "eps.pl_ttc_tx == 1",
    "EPS_POWER_OFF(line_index=7)": "eps.pl_aocs_wheels == 1",
}
#: The load-shed cards (CTG-001, CTG-005, CTG-023, EMG-001, EMG-002).
SHED_CARDS = ["contingency/undervoltage_loadshed.md",
              "contingency/eps_safe_mode.md",
              "contingency/progressive_load_shed.md",
              "emergency/emergency_safe_mode.md",
              "emergency/total_power_failure.md"]


def _cards(root):
    return sorted(p for p in root.rglob("*.md") if ".i18n" not in p.parts)


def _steps(text):
    """Yield (heading, [lines]) per step section."""
    head, buf = "(preamble)", []
    for ln in text.splitlines():
        if RE_STEP.match(ln):
            yield head, buf
            head, buf = ln, []
        else:
            buf.append(ln)
    yield head, buf


def _violations(path):
    out = []
    shed_card = path.name in {Path(c).name for c in SHED_CARDS}
    rules = NEEDS_LINE_ALL + (NEEDS_LINE_SHED if shed_card else [])
    for head, lines in _steps(path.read_text(encoding="utf-8")):
        for i, ln in enumerate(lines):
            m = RE_TC.match(ln)
            if not m:
                continue
            name, args = m.group(1), m.group(2)
            before = "\n".join(lines[:i])
            for rx, argrx, line_no in rules:
                if rx.match(name) and re.search(argrx, args):
                    if f"EPS_POWER_ON(line_index={line_no})" not in before:
                        out.append(f"{head.strip()} :: {name}({args}) "
                                   f"without EPS_POWER_ON(line_index={line_no}) first")
            if name == "AOCS_SET_MODE" and shed_card:
                if not AOCS_OK.search(before):
                    out.append(f"{head.strip()} :: AOCS_SET_MODE({args}) with "
                               f"the aocs_wheels line not established ON")
    return out


@pytest.mark.parametrize("root", [EN, FR], ids=["en", "fr"])
def test_every_heater_and_mode_restore_powers_its_line_first(root):
    bad = []
    for p in _cards(root):
        bad += [f"{p.relative_to(root)}: {v}" for v in _violations(p)]
    assert not bad, "commands sent to an unpowered line:\n" + "\n".join(bad)


@pytest.mark.parametrize("root", [EN, FR], ids=["en", "fr"])
@pytest.mark.parametrize("card", SHED_CARDS)
def test_ground_sheds_are_guarded_by_the_line_state(root, card):
    text = (root / card).read_text(encoding="utf-8")
    bad = []
    for head, lines in _steps(text):
        for i, ln in enumerate(lines):
            m = RE_TC.match(ln)
            if not m:
                continue
            for cmd, guard in SHED_GUARD.items():
                if ln.lstrip().startswith(f"**TC:** `{cmd}"):
                    if f"`{guard}`" not in "\n".join(lines[:i]):
                        bad.append(f"{head.strip()} :: {cmd} not guarded by "
                                   f"BRANCH `{guard}`")
    assert not bad, (f"{card}: sheds from the ground without checking the "
                     f"spacecraft first:\n" + "\n".join(bad))
