"""Voice loops: the MCS token service (smo_mcs/voice.py) and the /voice page.

Pins, per position: which loops (rooms) a token is minted for, canPublish
only on TALK loops (microphone only), the Instructor/SIM loop never sent to
a student, instructor seats refused to students, the IAP identity used and
local identities marked unverified, IAP required in the cloud, expiry <= 10
minutes and refreshed before it, JSON-only POST, no-store caching, 503 with
a reason when voice is not configured, and the vendored client wiring.
"""
from __future__ import annotations

import time
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

jwt = pytest.importorskip("jwt")
pytest.importorskip("livekit.api")

from smo_mcs import voice  # noqa: E402

SIM = Path(__file__).resolve().parents[2]
CONFIG = SIM / "configs" / "eosat1"
STATIC = SIM / "packages" / "smo-mcs" / "src" / "smo_mcs" / "static" / "modern"
KEY, SECRET = "APItest", "x" * 40
IAP = voice.IAP_USER_HEADER
CLOUD = {"LIVEKIT_URL": "wss://voice.c2o.live", "LIVEKIT_API_KEY": KEY, "LIVEKIT_API_SECRET": SECRET,
         "SMO_VOICE_REQUIRE_IAP": "1", "SMO_VOICE_INSTRUCTORS": "prof@c2o.live, Admin@C2O.live"}
STUDENTS = ["flight_director", "eps_tcs", "aocs", "ttc", "payload_ops", "fdir_systems", "propulsion"]


async def _client(env):
    app = web.Application()
    voice.register_voice_routes(app, CONFIG, env=env, static_dir=STATIC)
    c = TestClient(TestServer(app))
    await c.start_server()
    return c


def _claims(tok: str) -> dict:
    return jwt.decode(tok, SECRET, algorithms=["HS256"], options={"verify_aud": False})


async def _token(c, position, email=None, name=None):
    h = {IAP: f"accounts.google.com:{email}"} if email else {}
    body = {"position": position}
    if name is not None:
        body["name"] = name
    return await c.post("/api/voice/token", json=body, headers=h)


# ── rooms and rights per position ───────────────────────────────────────

@pytest.mark.parametrize("position", STUDENTS)
async def test_student_tokens_follow_the_loop_table(position):
    cfg = voice.load_voice_loops(CONFIG)
    c = await _client(CLOUD)
    try:
        r = await _token(c, position, email="jdoe@c2o.live")
        assert r.status == 200, await r.text()
        assert r.headers["Cache-Control"] == "no-store"
        d = await r.json()
        got = {lp["id"]: lp for lp in d["loops"]}
        want = {lp.id: lp.access_for(position) for lp in cfg.loops if lp.access_for(position) != "OFF"}
        assert set(got) == set(want)
        assert "instructor_sim" not in got, "students must never receive the instructor loop"
        for lid, lp in got.items():
            g = _claims(lp["token"])
            v = g["video"]
            assert v["room"] == f"c2o-{lid}" == lp["room"]
            assert v["roomJoin"] is True and v.get("canSubscribe", True) is True
            talk = want[lid] == "TALK"
            assert v.get("canPublish", False) is talk, lid
            assert v.get("canPublishSources", []) == (["microphone"] if talk else [])
            assert v.get("canPublishData", False) is False
            assert v.get("canUpdateOwnMetadata", False) is False
            assert g["sub"] == f"jdoe@c2o.live|{position}"
            assert g["name"] == "jdoe@c2o.live"
            assert g["attributes"] == {"position": position, "verified": "1", "role": "operator"}
        assert got["fd"]["access"] == "TALK", "FD loop: every position may talk"
        assert d["url"] == "wss://voice.c2o.live"
        assert d["identity"] == {"name": "jdoe@c2o.live", "verified": True, "instructor": False}
        assert d["recordings"] is False
    finally:
        await c.close()


async def test_own_subsystem_loop_is_talk_and_one_talk_at_start():
    c = await _client(CLOUD)
    try:
        own = {"eps_tcs": "eps_tcs", "aocs": "aocs_fd", "ttc": "ttc", "payload_ops": "payload",
               "fdir_systems": "fdir_systems", "propulsion": "propulsion", "flight_director": "fd"}
        for pos, loop in own.items():
            d = await (await _token(c, pos, email="a@c2o.live")).json()
            starts = {lp["id"]: lp["start"] for lp in d["loops"]}
            assert starts[loop] == "TALK", pos
            assert list(starts.values()).count("TALK") == 1, pos
            assert all(lp["start"] in ("OFF", "MON", "TALK") for lp in d["loops"])
    finally:
        await c.close()


@pytest.mark.parametrize("seat", ["instructor", "sim"])
async def test_instructor_seats(seat):
    c = await _client(CLOUD)
    try:
        r = await _token(c, seat, email="jdoe@c2o.live")
        assert r.status == 403
        r = await _token(c, seat, email="admin@c2o.live")       # case-insensitive allow-list
        assert r.status == 200, await r.text()
        d = await r.json()
        got = {lp["id"]: lp for lp in d["loops"]}
        assert got["instructor_sim"]["access"] == "TALK"
        assert _claims(got["instructor_sim"]["token"])["video"]["canPublish"] is True
        assert _claims(got["fd"]["token"])["attributes"]["role"] == "instructor"
        assert d["identity"]["instructor"] is True
        # an instructor taking a STUDENT seat still never gets the instructor loop
        d2 = await (await _token(c, "eps_tcs", email="prof@c2o.live")).json()
        assert "instructor_sim" not in {lp["id"] for lp in d2["loops"]}
    finally:
        await c.close()


# ── identity ────────────────────────────────────────────────────────────

async def test_cloud_requires_the_iap_identity():
    c = await _client(CLOUD)
    try:
        r = await _token(c, "eps_tcs", name="Mallory")
        assert r.status == 401
        r = await c.get("/api/voice/config")
        assert r.status == 401
    finally:
        await c.close()


async def test_local_identity_is_typed_and_unverified():
    c = await _client({"SMO_VOICE": "dev"})
    try:
        r = await _token(c, "eps_tcs")
        assert r.status == 400 and (await r.json())["code"] == "name"
        r = await _token(c, "eps_tcs", name="  Ana\u0007   Lopez  " + "x" * 60)
        assert r.status == 200
        d = await r.json()
        assert d["identity"]["verified"] is False
        name = d["identity"]["name"]
        assert "\u0007" not in name and "  " not in name and len(name) <= 40 and name.startswith("Ana Lopez")
        g = _claims_dev(d["loops"][0]["token"])
        assert g["attributes"]["verified"] == "0" and g["sub"].startswith("local:ana lopez")
        assert d["url"].startswith("ws://") and d["url"].endswith(":7880")
        # dev mode: the local user may take instructor seats (SMO_VOICE_LOCAL_INSTRUCTOR=0 stops it)
        assert (await _token(c, "instructor", name="Prof")).status == 200
    finally:
        await c.close()
    c = await _client({"SMO_VOICE": "dev", "SMO_VOICE_LOCAL_INSTRUCTOR": "0"})
    try:
        assert (await _token(c, "instructor", name="Prof")).status == 403
    finally:
        await c.close()


def _claims_dev(tok):
    return jwt.decode(tok, voice.DEV_API_SECRET, algorithms=["HS256"], options={"verify_aud": False})


async def test_config_endpoint():
    c = await _client(CLOUD)
    try:
        d = await (await c.get("/api/voice/config", headers={IAP: "accounts.google.com:jdoe@c2o.live"})).json()
        assert d["available"] is True and d["needs_name"] is False
        assert d["positions"] == STUDENTS
        assert set(d["position_labels"]) == set(STUDENTS) | {"instructor", "sim"}
        assert d["position_labels"]["instructor"] == {"en": "Instructor", "fr": "Instructeur"}
        d = await (await c.get("/api/voice/config", headers={IAP: "prof@c2o.live"})).json()
        assert d["positions"] == STUDENTS + ["instructor", "sim"]
    finally:
        await c.close()


# ── expiry ──────────────────────────────────────────────────────────────

async def test_tokens_expire_within_ten_minutes_and_are_refreshed_before():
    for ttl_env, ttl in ((None, 600), ("120", 120), ("3600", 600), ("5", 60), ("junk", 600)):
        env = dict(CLOUD)
        if ttl_env is not None:
            env["SMO_VOICE_TOKEN_TTL_S"] = ttl_env
        c = await _client(env)
        try:
            t0 = int(time.time())
            d = await (await _token(c, "ttc", email="a@c2o.live")).json()
            assert d["ttl_s"] == ttl
            assert d["refresh_in_s"] < ttl
            for lp in d["loops"]:
                exp = _claims(lp["token"])["exp"]
                assert t0 + ttl - 2 <= exp <= t0 + ttl + 2
                assert exp - t0 <= 600 + 2
        finally:
            await c.close()


# ── request hygiene and failure modes ───────────────────────────────────

async def test_rejects_bad_requests():
    c = await _client(CLOUD)
    try:
        h = {IAP: "a@c2o.live"}
        r = await c.post("/api/voice/token", data="position=eps_tcs", headers={
            **h, "Content-Type": "application/x-www-form-urlencoded"})
        assert r.status == 415, "a cross-site form post must not mint a token"
        r = await c.post("/api/voice/token", data="{nope", headers={**h, "Content-Type": "application/json"})
        assert r.status == 400
        r = await _token(c, "astronaut", email="a@c2o.live")
        assert r.status == 400 and (await r.json())["code"] == "position"
        r = await c.get("/api/voice/token")
        assert r.status == 405
    finally:
        await c.close()


@pytest.mark.parametrize("env,code", [
    ({}, "not-configured"),
    ({"LIVEKIT_API_KEY": KEY, "LIVEKIT_API_SECRET": SECRET}, "not-configured"),       # no URL
    ({"LIVEKIT_URL": "wss://v", "LIVEKIT_API_KEY": KEY, "LIVEKIT_API_SECRET": "short"}, "weak-secret"),
])
async def test_not_configured_is_a_clear_503(env, code):
    c = await _client(env)
    try:
        r = await c.post("/api/voice/token", json={"position": "eps_tcs", "name": "A"})
        assert r.status == 503 and (await r.json())["code"] == code
        d = await (await c.get("/api/voice/config?name=A")).json()
        assert d["available"] is False and d["reason"] == code
    finally:
        await c.close()


async def test_a_broken_loop_file_disables_only_voice(tmp_path):
    import shutil
    cfg = tmp_path / "cfg"
    shutil.copytree(CONFIG / "mcs", cfg / "mcs")
    (cfg / "voice").mkdir()
    (cfg / "voice" / "voice_loops.yaml").write_text("loops: []\n")
    app = web.Application()
    voice.register_voice_routes(app, cfg, env=CLOUD, static_dir=STATIC)
    c = TestClient(TestServer(app))
    await c.start_server()
    try:
        r = await _token(c, "eps_tcs", email="a@c2o.live")
        assert r.status == 503 and (await r.json())["code"] == "bad-config"
    finally:
        await c.close()


def test_recording_is_a_documented_stub():
    with pytest.raises(NotImplementedError):
        voice.start_recording()
    assert voice.load_voice_loops(CONFIG).recordings is False


# ── the page ────────────────────────────────────────────────────────────

async def test_voice_page_is_served_with_the_vendored_client():
    c = await _client(CLOUD)
    try:
        r = await c.get("/voice")
        assert r.status == 200 and r.headers["Cache-Control"] == "no-cache"
        html = await r.text()
        assert '/static/vendor/js/livekit/livekit-client.umd.js' in html
        assert '/static/modern/voice.js' in html
        import re
        srcs = re.findall(r'<script[^>]+src="([^"]+)"', html)
        assert srcs and not any(s.startswith(("http:", "https:", "//")) for s in srcs), "no CDN"
    finally:
        await c.close()


def test_vendored_livekit_client_is_pinned_and_licensed():
    d = SIM / "vendor" / "js" / "livekit"
    js = (d / "livekit-client.umd.js").read_text()
    assert '"2.23.0"' in js and "LivekitClient" in js[:400]
    assert "Apache License" in (d / "LICENSE").read_text()
    notice = (d / "NOTICE.txt").read_text()
    assert "livekit-client 2.23.0" in notice and "Apache" in notice
    import hashlib
    assert hashlib.sha256((d / "livekit-client.umd.js").read_bytes()).hexdigest() in notice


def test_mcs_registers_the_voice_routes_and_header_button():
    src = (SIM / "packages/smo-mcs/src/smo_mcs/server.py").read_text()
    assert "register_voice_routes(app, self.config_dir" in src
    idx = (STATIC / "index.html").read_text()
    assert 'id="voice-btn"' in idx and "/static/modern/voice-dock.js" in idx
    dock = (STATIC / "voice-dock.js").read_text()
    assert 'frame.allow = "microphone; autoplay"' in dock and 'frame.src = "/voice"' in dock


def test_panel_keeps_audio_behind_a_user_gesture_and_echo_cancellation_on():
    js = (STATIC / "voice.js").read_text()
    assert "echoCancellation: true" in js and "noiseSuppression: true" in js
    assert "autojoin" not in js, "audio must start only from the Join click"
    assert 'localStorage.getItem("mcs.position")' in js
    assert "await track.mute();" in js, "the microphone is published closed"
