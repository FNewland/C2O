"""The decision catalogue is tied to the learner workbook and to the frontend.

configs/worksheets/decision_catalogue.yaml is hand-maintained; these tests
keep it honest: every decision names a real workbook part (in the generated
learner_workbook.yaml), is bilingual, uses the gate/seat/field/source
vocabularies, and every capture point it names exists in the SpaceCDF
frontend (and every decision the frontend records exists here).
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from spacecdf_server.logbook import decisions as dec
from spacecdf_server.logbook import prefill

DESIGN = Path(__file__).resolve().parents[2]
CAT = DESIGN / "configs" / "worksheets" / "decision_catalogue.yaml"
WB = DESIGN / "configs" / "worksheets" / "learner_workbook.yaml"
FRONTEND = DESIGN / "frontend" / "src"
NNBSP = " "


def _cat() -> dict:
    return yaml.safe_load(CAT.read_text(encoding="utf-8"))


def _parts() -> dict[str, set[str]]:
    wb = yaml.safe_load(WB.read_text(encoding="utf-8"))
    return {w["id"]: {q["id"] for q in w["questions"]} for w in wb["worksheets"]}


def _frontend_text() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in FRONTEND.rglob("*.ts*") if "node_modules" not in p.parts)


def test_hand_maintained_header():
    head = CAT.read_text(encoding="utf-8")[:600]
    assert "HAND-MAINTAINED" in head and "test_decision_catalogue.py" in head


def test_every_decision_names_a_real_workbook_part():
    parts = _parts()
    for d in _cat()["decisions"]:
        if d["part"] is None:
            # a CDR decision no workbook part asks for yet says so explicitly (phase 2)
            assert d.get("no_workbook_part") is True and d["id"].startswith("D-CDR-"), d["id"]
            continue
        wid, qid = d["part"].split("/")
        assert wid in parts, (d["id"], wid)
        assert qid in parts[wid], (d["id"], d["part"], sorted(parts[wid]))
        assert qid != "notes", f"{d['id']}: a decision belongs to a worksheet part, not the notes"


def test_ids_unique_and_well_formed():
    ids = [d["id"] for d in _cat()["decisions"]]
    assert len(ids) == len(set(ids))
    for d in _cat()["decisions"]:
        assert re.fullmatch(r"D-(\d\.\d|GATE|CDR)-[A-Z]+", d["id"]), d["id"]
        if d["id"].startswith(("D-GATE", "D-CDR")):
            continue
        assert d["part"].startswith(f"LW-{d['id'].split('-')[1]}/"), f"{d['id']} id says its worksheet: {d['part']}"


def test_bilingual_and_french_typography():
    cat = _cat()
    for d in cat["decisions"]:
        q = d["question"]
        assert q["en"].strip() and q["fr"].strip() and q["en"] != q["fr"], d["id"]
        assert q["en"].endswith("?"), d["id"]
        assert q["fr"].endswith(f"{NNBSP}?"), f"{d['id']}: narrow no-break space before '?' (STYLE_FR §0.7)"
        assert " :" not in q["fr"] and " ;" not in q["fr"], d["id"]
        if "hint" in d:
            assert d["hint"]["en"] and d["hint"]["fr"] and " ;" not in d["hint"]["fr"], d["id"]
    for g in cat["gates"]:
        assert g["label"]["en"] and g["label"]["fr"]
    for s in cat["seats"]:
        assert s["label"]["en"] and s["label"]["fr"]
    for k, v in cat["fields"].items():
        assert v["en"] and v["fr"], k
    for k, v in cat["sources"].items():
        assert v["label"]["en"] and v["label"]["fr"] and v["api"], k


def test_full_ecss_gate_profile():
    """Ruling 1 (REDESIGN_DECISIONS.md): MDR → PRR → SRR → PDR (→ CDR, phase 2); MCR is the old MDR name (ruling 3)."""
    gates = _cat()["gates"]
    assert [g["id"] for g in gates] == list(dec.GATE_ORDER) == ["mdr", "prr", "srr", "pdr", "cdr"]
    assert dec.due_by("cdr") == {"mdr", "prr", "srr", "pdr", "cdr"}
    assert "mcr" in gates[0]["ui_gates"]
    assert dec.gate_of_ui("mcr") == "mdr" and dec.gate_of_ui("SRR") == "srr" and dec.gate_of_ui("x") is None
    assert dec.due_by("srr") == {"mdr", "prr", "srr"}


def test_vocabularies():
    cat = _cat()
    seats = {s["id"] for s in cat["seats"]}
    gates = {g["id"] for g in cat["gates"]}
    assert set(cat["fields"]) == set(dec.FIELDS)
    for d in cat["decisions"]:
        assert d["seat"] in seats, d["id"]
        assert d["gate"] in gates, d["id"]
        assert set(d["fields"]) <= set(dec.FIELDS), d["id"]
        assert {"choice", "rationale"} <= set(d["fields"]), f"{d['id']}: every record asks for the choice and why"
        assert set(d["prefill"]) <= set(cat["sources"]), (d["id"], set(d["prefill"]) - set(cat["sources"]))
    # The ten seats (Franz's list) each own at least one decision, and every gate has some.
    assert len(seats) == 10
    assert {d["seat"] for d in cat["decisions"]} == seats
    assert {d["gate"] for d in cat["decisions"]} == gates


def test_server_sources_have_a_reader():
    server = {k for k, v in _cat()["sources"].items() if v.get("server")}
    assert server == set(prefill.SERVER_SOURCES)


def test_capture_points_exist_in_the_frontend_and_back():
    src = _frontend_text()
    # capture="decide:orbit-trade", or a literal in a map such as BUDGET_CAPTURE
    used_captures = set(re.findall(
        r"""['"]((?:wizard|decide|budget|interfaces|blocks|equipment|requirements|gate):[a-z-]+)['"]""", src))
    used_ids = set(re.findall(r"['\"](D-(?:\d\.\d|GATE)-[A-Z]+)['\"]", src))
    cat = _cat()
    named = {c for d in cat["decisions"] for c in d["capture"]}
    assert named <= used_captures, f"capture points named in the catalogue but not wired: {named - used_captures}"
    ids = {d["id"] for d in cat["decisions"]}
    assert used_ids <= ids, f"the frontend records decisions the catalogue does not have: {used_ids - ids}"
    for d in cat["decisions"]:
        if d["capture"]:
            assert d["id"] in used_ids, f"{d['id']} names capture points but the frontend never records it"


def test_every_decision_worksheet_is_covered():
    """Each design worksheet that asks for decisions (1.2 … 5.2) has at least one in the catalogue."""
    covered = {d["part"].split("/")[0] for d in _cat()["decisions"] if d["part"]}
    expected = {"LW-1.2", "LW-1.3", "LW-1.4", "LW-2.1", "LW-2.2", "LW-2.3", "LW-2.4", "LW-3.1", "LW-3.2",
                "LW-3.3", "LW-3.4", "LW-4.1", "LW-4.2", "LW-4.3", "LW-4.4", "LW-5.1", "LW-5.2"}
    assert expected <= covered, expected - covered


def test_localised_order_follows_the_workbook():
    out = dec.localised("fr", [], None, lookup=None)
    nums = [tuple(int(x) for x in d["worksheet"].split("-")[1].split(".")) for d in out["decisions"] if d["worksheet"]]
    assert nums == sorted(nums)
    # decisions with no workbook part come last
    tail = [d["id"] for d in out["decisions"] if not d["worksheet"]]
    assert tail and [d["id"] for d in out["decisions"]][-len(tail):] == tail
    assert out["gates"][0]["label"].startswith("MDR") and all(d["status"] == "open" for d in out["decisions"])
    assert sum(c["total"] for c in out["counts"].values()) == len(out["decisions"])
