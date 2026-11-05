"""Course videos on the welcome page (sim/tools/video_library.py).

Pins:
  - /videos lists the published catalogue in the page language; instructor-only
    videos stay hidden from students; the H5P download is for instructors;
  - /videos/<slug> plays the unpacked H5P package with h5p-standalone and
    hands the player the question ids that map answers to worksheets;
  - narration review and its notes: instructors and SMO_VIDEO_REVIEWERS only;
  - /media/videos serves the files (symlinks inside the package included);
  - unknown or malformed slugs are 404; the logbook accepts the ``video`` context;
  - the page strings have French entries in the tools catalogue.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest
from aiohttp.test_utils import TestClient, TestServer

SIM = Path(__file__).resolve().parents[2]
TOOLS = SIM / "tools"
CATALOG = SIM / "packages/smo-common/src/smo_common/ui/i18n/tools/fr.json"
COMMON = SIM / "packages/smo-common/src/smo_common/ui/i18n/fr.json"
IAP = "X-Goog-Authenticated-User-Email"


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
pt = _load("_tv_portal", TOOLS / "portal.py")
vl = _load("video_library", TOOLS / "video_library.py")


class Prober(pt.Prober):
    async def http(self, host, port, path):
        return ("down", None, None)


def _entry(slug, audience="all"):
    lang = lambda l: {"mp4": f"{slug}.{l}.mp4", "vtt": f"{slug}.{l}.vtt", "chapters": f"{slug}.{l}.chapters.vtt",
                      "poster": f"{slug}.{l}.poster.jpg", "transcript": f"{slug}.{l}.transcript.md",
                      "h5p": f"{slug}.{l}.h5p", "duration": 140.0, "questions": 1,
                      "chapter_list": [{"start": 3.2, "title": "Intro" if l == "en" else "Intro FR"}],
                      "question_list": [{"step": "s1", "subContentId": "11111111-2222-5333-8444-555555555555",
                                         "text": "Q?", "worksheet": "LW-1.4/B", "worksheet_label": "Part B"}]}
    return {"id": slug.upper(), "slug": slug, "week": 2, "audience": audience,
            "title": {"en": f"Title {slug}", "fr": f"Titre {slug}"}, "summary": {"en": "S", "fr": "R"},
            "ties": [{"id": "LW-1.4/B", "tool": "spacecdf", "label": {"en": "Part B", "fr": "Partie B"}}],
            "langs": {"en": lang("en"), "fr": lang("fr")}, "licence": "CC0-1.0"}


@pytest.fixture
def videos(tmp_path, monkeypatch):
    d = tmp_path / "videos"
    v = d / "v-test-01"
    (v / "h5p" / "fr" / "content" / "videos").mkdir(parents=True)
    (v / "v-test-01.fr.mp4").write_bytes(b"\0\0\0\x18ftypmp42")
    (v / "h5p" / "fr" / "content" / "videos" / "v-test-01.fr.mp4").symlink_to(Path("../../../../v-test-01.fr.mp4"))
    (d / "catalog.json").write_text(json.dumps({"videos": [_entry("v-test-01"), _entry("v-ta-01", "instructors")]}))
    monkeypatch.setenv("SMO_VIDEO_DIR", str(d))
    monkeypatch.setenv("SMO_VIDEO_REVIEW_DIR", str(tmp_path / "review"))
    monkeypatch.setenv("SMO_INSTRUCTORS", "prof@c2o.live")
    monkeypatch.setenv("SMO_VIDEO_REVIEWERS", "relectrice@c2o.live")
    return d


async def _client(domain="c2o.live"):
    cfg = pt.Config.from_env({"SMO_PORTAL_DOMAIN": domain} if domain else {})
    c = TestClient(TestServer(pt.create_app(cfg, Prober(cfg))))
    await c.start_server()
    return c


def _who(email):
    return {IAP: f"accounts.google.com:{email}"}


def _boot(page: str) -> dict:
    m = re.search(r'<script id="vl-boot" type="application/json">(.*?)</script>', page, re.S)
    return json.loads(m.group(1))


async def test_library_by_audience_and_language(videos):
    c = await _client()
    try:
        t = await (await c.get("/videos?lang=fr", headers=_who("student@c2o.live"))).text()
        b = _boot(t)
        assert [v["slug"] for v in b["videos"]] == ["v-test-01"]
        assert b["instructor"] is False and b["reviewer"] is False
        assert '<html lang="fr">' in t and "Course videos" in t
        b = _boot(await (await c.get("/videos", headers=_who("prof@c2o.live"))).text())
        assert {v["slug"] for v in b["videos"]} == {"v-test-01", "v-ta-01"} and b["instructor"] and b["reviewer"]
        b = _boot(await (await c.get("/videos", headers=_who("relectrice@c2o.live"))).text())
        assert b["reviewer"] is True and b["instructor"] is False
        # the welcome page links to the library
        assert 'href="/videos"' in await (await c.get("/", headers=_who("student@c2o.live"))).text()
    finally:
        await c.close()


async def test_player_and_media(videos):
    c = await _client()
    try:
        r = await c.get("/videos/v-test-01?lang=fr", headers=_who("student@c2o.live"))
        t = await r.text()
        assert r.status == 200 and "/vendor/h5p/main.bundle.js" in t and "Titre v-test-01" in t
        b = _boot(t)
        assert b["lang"] == "fr" and b["questions"][0]["worksheet"] == "LW-1.4/B"
        assert (await c.get("/videos/v-ta-01", headers=_who("student@c2o.live"))).status == 404
        assert (await c.get("/videos/no-such", headers=_who("student@c2o.live"))).status == 404
        assert (await c.get("/videos/..%2Fetc", headers=_who("student@c2o.live"))).status == 404
        r = await c.get("/media/videos/v-test-01/h5p/fr/content/videos/v-test-01.fr.mp4")
        assert r.status == 200 and (await r.read()).startswith(b"\0\0\0\x18ftyp")
        assert (await c.get("/vendor/h5p/main.bundle.js")).status == 200
    finally:
        await c.close()


async def test_review_notes_for_reviewers_only(videos):
    c = await _client()
    try:
        stu, rev = _who("student@c2o.live"), _who("relectrice@c2o.live")
        assert (await c.get("/videos/v-test-01/review", headers=stu)).status == 403
        assert (await c.post("/api/videos/v-test-01/review", json={"step": "s1", "text": "x"}, headers=stu)).status == 403
        assert (await c.get("/videos/v-test-01/review", headers=rev)).status == 200
        r = await c.post("/api/videos/v-test-01/review", headers=rev,
                         json={"step": "s1", "lang": "fr", "text": "« Markdown » mal prononcé"})
        d = await r.json()
        assert r.status == 200 and d["notes"][-1]["by"] == "relectrice@c2o.live" and d["notes"][-1]["lang"] == "fr"
        assert (await c.post("/api/videos/v-test-01/review", headers=rev, json={"step": "../x", "text": "y"})).status == 400
        d = await (await c.get("/api/videos/v-test-01/review", headers=_who("prof@c2o.live"))).json()
        assert len(d["notes"]) == 1
        # notes live outside the served folder
        assert (await c.get("/media/videos/../review/v-test-01.json")).status in (403, 404)
    finally:
        await c.close()


def test_logbook_accepts_the_video_context():
    from smo_common.logbook.store import CONTEXT_KEYS
    assert "video" in CONTEXT_KEYS


def test_page_strings_have_french():
    src = (TOOLS / "video_library.py").read_text(encoding="utf-8")
    keys = set(re.findall(r'data-i18n>([^<]+)<', src)) | set(re.findall(r'\bT\("([^"]+)"', src))
    fr = json.loads(CATALOG.read_text(encoding="utf-8"))
    fr.update(json.loads(COMMON.read_text(encoding="utf-8")))     # the tools catalogue falls back on it
    missing = sorted(k for k in keys if k not in fr)
    assert not missing, missing
