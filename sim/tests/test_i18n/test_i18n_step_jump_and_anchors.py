"""Author rulings Q35 and Q33 in the i18n checker.

Q35: « passer à l'étape N » is allowed in a French procedure when the card
declares a `**BRANCH:**` whose GO/NO-GO target is step N, and stays forbidden
otherwise (other steps, no BRANCH, other jump verbs).

Q33: explicit heading anchors `{#id}` are structural: identical in EN and FR.
"""
import textwrap

from tools.i18n import cli, mdparity
from tools.i18n.docs import branch_target_steps, forbidden_fr_wording

FORBID = [r"(?:passer|aller|revenir|sauter|reprendre)\s+(?:directement\s+)?"
          r"(?:à|a|aux?)\s+(?:l['’]\s*|la\s+)?[ée]tape\s+\d+"]

CARD = textwrap.dedent("""\
    # TST-001 : Essai

    **LABEL:** `STEP-2`

    **BRANCH:** `tcs.htr_battery == 0` -> GO `STEP-5` | NO-GO `STEP-3-WAIT` (timeout 70 s)
    """)


# ── unit level ──────────────────────────────────────────────────────────

def test_branch_target_steps_reads_go_and_nogo_labels():
    assert branch_target_steps(CARD) == {5, 3}
    assert branch_target_steps("no branch here") == set()
    assert branch_target_steps(
        "**BRANCH:** `a.b == 1` -> GO `STEP-END` | NO-GO `STEP-4V`") == {4}


def test_passer_allowed_when_branch_targets_that_step():
    for txt in ("Si oui, passer à l'étape 5.",
                "Sinon, passer à l’étape 3.",
                "passer directement à l'étape 5"):
        assert forbidden_fr_wording(txt, FORBID, CARD) is None, txt


def test_passer_forbidden_for_a_step_no_branch_targets():
    hit = forbidden_fr_wording("Puis passer à l'étape 4.", FORBID, CARD)
    assert hit and "4" in hit[0]


def test_passer_forbidden_without_any_branch():
    hit = forbidden_fr_wording("Passer à l'étape 5.", FORBID, "# carte sans BRANCH")
    assert hit


def test_other_jump_verbs_stay_forbidden_even_with_a_branch():
    for txt in ("Aller à l'étape 5.", "Revenir à l'étape 3.", "Sauter à l'étape 5."):
        assert forbidden_fr_wording(txt, FORBID, CARD), txt


def test_typographic_apostrophe_is_caught():
    assert forbidden_fr_wording("Aller à l’étape 2.", FORBID, CARD)


def test_a_later_unallowed_jump_is_still_reported():
    txt = "Passer à l'étape 5. Ensuite passer à l'étape 6."
    hit = forbidden_fr_wording(txt, FORBID, CARD)
    assert hit and hit[0].endswith("6")


# ── through the CLI gate ────────────────────────────────────────────────

EN = textwrap.dedent("""\
    # TST-001: Test

    ## Step 2

    **BRANCH:** `tcs.htr_battery == 0` -> GO `STEP-5` | NO-GO `STEP-3` (timeout 70 s)

    If the heater is off, proceed to Step {n}.
    """)


def _project(tmp_path, n, fr_body):
    en = EN.format(n=n)
    (tmp_path / "en").mkdir()
    (tmp_path / "fr").mkdir()
    (tmp_path / "en" / "c.md").write_text(en, encoding="utf-8")
    fr = en.replace("# TST-001: Test", "# TST-001 : Essai").replace(
        "## Step 2", "## Étape 2").replace(
        f"If the heater is off, proceed to Step {n}.", fr_body)
    (tmp_path / "fr" / "c.md").write_text(fr, encoding="utf-8")
    pat = FORBID[0].replace("\\", "\\\\")
    (tmp_path / "i18n.yaml").write_text(
        "docs:\n  - group: t\n    en: en/c.md\n    fr: fr/c.md\n"
        f"    forbid_fr:\n      - \"{pat}\"\n", encoding="utf-8")
    cfg = str(tmp_path / "i18n.yaml")
    cli.main(["--config", cfg, "accept", "--init"])
    return cfg


def test_gate_passes_a_declared_branch_narration(tmp_path):
    cfg = _project(tmp_path, 5, "Si le réchauffeur est coupé, passer à l'étape 5.")
    assert cli.main(["--config", cfg, "check"]) == 0


def test_gate_fails_an_undeclared_jump(tmp_path):
    cfg = _project(tmp_path, 7, "Si le réchauffeur est coupé, passer à l'étape 7.")
    assert cli.main(["--config", cfg, "check"]) == 1


# ── Q33: heading anchors are structural ─────────────────────────────────

def test_matching_heading_anchors_are_parity_clean():
    en = "# Power {#eps-power}\n\nText 5 W.\n\nSee [budget](#eps-budget-2).\n\n## Budget {#eps-budget-2}\n"
    fr = "# Puissance {#eps-power}\n\nTexte 5 W.\n\nVoir [bilan](#eps-budget-2).\n\n## Bilan {#eps-budget-2}\n"
    assert mdparity.compare(en, fr) == []


def test_differing_heading_anchor_is_a_parity_error():
    en = "# Power {#eps-power}\n\n## Budget {#eps-budget}\n"
    fr = "# Puissance {#eps-puissance}\n\n## Bilan {#eps-budget}\n"
    probs = mdparity.compare(en, fr)
    assert any("{#id}" in p for p in probs), probs


def test_missing_heading_anchor_in_fr_is_a_parity_error():
    en = "# Power {#eps-power}\n"
    fr = "# Puissance\n"
    assert mdparity.compare(en, fr)
    # ... also when the i18n tool compares one aligned section at a time
    assert mdparity.compare(en, fr, headings=False)


def test_digits_inside_anchor_ids_are_not_prose_numbers():
    en = "## Step 2 {#step-2-a5}\n"
    fr = "## Étape 2 {#step-2-a5}\n"
    assert mdparity.compare(en, fr) == []
