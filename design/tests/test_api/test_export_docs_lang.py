"""i18n packet C2: French ECSS review templates (templates/fr/*.md.j2).

``POST /api/exports/docs/{id}?lang=fr`` renders the French Markdown; without
``lang`` (or ``lang=en``) the English templates are used unchanged.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from spacecdf_agents.exporters.docs import generator as gen

REVIEWS = ("srr", "pdr", "cdr")
JINJA = re.compile(r"\{\{.*?\}\}|\{%.*?%\}", re.S)

EN_HEADINGS = {
    "srr": "System Requirements Review (SRR)",
    "pdr": "Preliminary Design Review (PDR)",
    "cdr": "Critical Design Review (CDR)",
}
FR_HEADINGS = {
    "srr": "Revue des exigences système (SRR)",
    "pdr": "Revue de définition préliminaire (PDR)",
    "cdr": "Revue de définition critique (CDR)",
}


@pytest.mark.parametrize("review", REVIEWS)
def test_fr_template_exists_with_identical_jinja(review):
    en = (gen.TEMPLATE_DIR / f"{review}.md.j2").read_text(encoding="utf-8")
    fr_path = Path(gen.TEMPLATE_DIR) / "fr" / f"{review}.md.j2"
    assert fr_path.is_file()
    fr = fr_path.read_text(encoding="utf-8")
    # Only prose is translated: every Jinja tag is byte-identical and in order.
    assert JINJA.findall(fr) == JINJA.findall(en)
    assert len(fr.splitlines()) == len(en.splitlines())


def test_template_search_path_prefers_fr_and_keeps_english_fallback():
    assert gen.template_search_path(None) == [str(gen.TEMPLATE_DIR)]
    assert gen.template_search_path("en") == [str(gen.TEMPLATE_DIR)]
    fr = gen.template_search_path("fr")
    assert fr[0].endswith("fr") and fr[-1] == str(gen.TEMPLATE_DIR)


async def test_export_docs_markdown_lang_fr_and_default(client, study_obj, monkeypatch):
    from spacecdf_server.routers.exports import _common as exports_common

    # Run the real design loop once per review is slow; cache one run. Since W0.1 every export
    # family calls the loop through routers/exports/_common, so that is where it is patched.
    real = exports_common._run_design_for_study
    cache: dict = {}

    async def cached(study_id):
        if study_id not in cache:
            cache[study_id] = await real(study_id)
        return cache[study_id]

    monkeypatch.setattr(exports_common, "_run_design_for_study", cached)

    for review in REVIEWS:
        base = f"/api/exports/docs/{study_obj.id}?review={review}&fmt=markdown"
        r_en = await client.post(base)
        assert r_en.status_code == 200, r_en.text
        md_en = r_en.json()["document_markdown"]
        assert EN_HEADINGS[review] in md_en
        assert "## 3. " in md_en and "Mass Budget" in md_en
        assert "Bilan de masse" not in md_en

        r_fr = await client.post(base + "&lang=fr")
        assert r_fr.status_code == 200, r_fr.text
        md_fr = r_fr.json()["document_markdown"]
        assert FR_HEADINGS[review] in md_fr
        assert "Bilan de masse" in md_fr and "Bilan de puissance" in md_fr
        assert "Mass Budget" not in md_fr and "HUMAN INPUT REQUIRED" not in md_fr

        r_en2 = await client.post(base + "&lang=en")
        assert r_en2.status_code == 200, r_en2.text
        md_en2 = r_en2.json()["document_markdown"]
        assert EN_HEADINGS[review] in md_en2 and "Bilan de masse" not in md_en2
