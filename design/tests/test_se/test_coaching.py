"""3.S4: coaching cards, deterministic and bilingual; linter (sources, banned superlatives) and the
paraphrase check against the systems-engineering skill (where a local copy exists)."""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

GATES = ("mdr", "prr", "srr", "pdr")
ROOT = Path(__file__).resolve().parents[2]


def _seats() -> list[str]:
    return [s["id"] for s in yaml.safe_load((ROOT / "configs" / "seats.yaml").read_text(encoding="utf-8"))["seats"]]


@pytest.mark.parametrize("register", ["learning", "plain", "practitioner"])
def test_every_seat_has_a_card_per_phase_in_en_and_fr(register):
    from spacecdf_server.services import se_protocol as sp
    seats = _seats()
    assert len(seats) >= 11
    for g in GATES:
        c = sp.coaching([g], register=register)
        assert set(c["seats"]) == set(seats), g
        for seat, cards in c["seats"].items():
            assert cards, (g, seat)
            for card in cards:
                assert card["body"]["en"].strip() and card["body"]["fr"].strip(), (g, seat)
                assert card["title"]["fr"] and card["source"] and card["source_label"]
        assert all(x["body"]["en"] and x["body"]["fr"] for x in c["phase"])


def test_registers_differ_and_learning_puts_why_before_what():
    from spacecdf_server.services import se_protocol as sp
    data = sp.load()
    raw = data["phases"]["pdr"]["coaching"]["seats"]["comms_engineer"]
    get = {r: sp.coaching(["pdr"], register=r, seat="comms_engineer")["seats"]["comms_engineer"][0]["body"]["en"]
           for r in sp.REGISTERS}
    assert get["plain"] == raw["why"]["en"] and get["practitioner"] == raw["focus"]["en"]
    assert get["learning"].index(raw["why"]["en"]) < get["learning"].index(raw["focus"]["en"])
    assert sp.coaching(["pdr"], register="nonsense")["register"] == "learning"


def test_linter_every_card_cites_a_source_and_uses_no_banned_superlative():
    from spacecdf_server.services import se_protocol as sp
    data = sp.load()
    cards = sp.all_cards(data)
    assert cards
    for c in cards:
        assert c["source"] in data["sources"], c["id"]
        for lang in ("en", "fr"):
            text = f"{c['title'][lang]} {c['body'][lang]}".lower()
            for w in sp.BANNED_WORDS:
                assert not re.search(rf"(?<![\w-]){re.escape(w)}(?![\w-])", text), (c["id"], lang, w)
            if lang == "fr":
                assert "'" not in text, (c["id"], "use the typographic apostrophe")


def test_pointer_cards_and_the_data_governance_draft():
    from spacecdf_server.services import se_protocol as sp
    ptr = {p["id"]: p for p in sp.coaching(["pdr"])["pointers"]}
    assert {"PTR-COST-01", "PTR-REVIEW-01", "PTR-CYBER-01", "PTR-DATAGOV-01"} <= set(ptr)
    gov = ptr["PTR-DATAGOV-01"]
    assert gov["approval"] == "pi_pending" and gov["legal_confidence"] == "uncertain"
    assert "uncertain" in gov["body"]["en"] and "incertaine" in gov["body"]["fr"]
    assert "cannot replace the relationship" in gov["body"]["en"]
    # seat filter keeps the pointers meant for the seat
    cost = sp.coaching(["mdr"], seat="cost_engineer")["pointers"]
    assert [p["id"] for p in cost] == ["PTR-COST-01"]


def test_paraphrase_check_finds_no_copied_run_of_twelve_words():
    from tools import se_paraphrase_check as pc
    skill = Path(pc.DEFAULT_SKILL)
    if not (skill / "SKILL.md").is_file():
        pytest.skip("no local copy of the systems-engineering skill")
    data = yaml.safe_load((ROOT / "configs" / "se_protocol.yaml").read_text(encoding="utf-8"))
    assert pc.check(data, skill, 12) == []
    # the check itself works: a copied sentence is found
    probe = {"x": {"en": "Before doing any substantive work on a lifecycle phase or engineering task, execute the following"}}
    assert pc.check(probe, skill, 12)


async def test_phase_endpoint_serves_cards_by_register_and_seat(client):
    from tests.fixtures.nfi import seed_nfi
    s = await seed_nfi(client, "S0")
    r = (await client.get(f"/api/studies/{s.study_id}/phase?register=plain&seat=payload_lead")).json()
    co = r["coaching"]
    assert co["register"] == "plain" and list(co["seats"]) == ["payload_lead"]
    assert [p["id"] for p in co["pointers"]] == ["PTR-DATAGOV-01"]
