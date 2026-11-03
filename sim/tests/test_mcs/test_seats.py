"""Console seats (redesign WP10): registry, command authority bound on the
server, IAP JWT verification, the voice token from the seat, and the
anonymous ground-activity summary.

Verification table (redesign s6): an exclusive seat refuses a second holder;
handover is logged; two people with the same display name stay distinct; a
forged ``position=flight_director`` from an eps_tcs holder is refused; an
unknown position is denied; the log names the person; no email in the
activity summary.
"""
from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from smo_common.config.schemas import MCSDisplayConfig
from smo_common.web.iap_jwt import IapJwtError, IapVerifier, KeySet, verify_token
from smo_mcs.seats import SeatError, SeatRegistry
from smo_mcs.seats_http import (ITEM_KEYS, GroundActivity, SeatService, register_seat_routes,
                                summary_has_identity)
from tests.iap_test_keys import AUD_OPS, AUD_SIM, FakeIap

CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs" / "eosat1"
POSITIONS = ["flight_director", "eps_tcs", "aocs", "ttc", "payload_ops", "fdir_systems",
             "propulsion"]

ALICE = "alice@c2o.live"
BOB = "bob@c2o.live"
PROF = "prof@c2o.live"


class Clock:
    def __init__(self, t: float = 1_000_000.0):
        self.t = t

    def __call__(self) -> float:
        return self.t


# ════════════════════════════════════════════════════════════ registry ═══

def _reg():
    clk = Clock()
    reg = SeatRegistry(POSITIONS, clock=clk, sim_clock=lambda: clk.t + 5e8)
    for pid, name, ins in ((ALICE, "Alice", False), (BOB, "Bob", False), (PROF, "Prof", True)):
        reg.touch_person(pid, name, verified=True, instructor=ins)
    return reg, clk


def test_exclusive_seat_refuses_a_second_holder():
    reg, _ = _reg()
    reg.claim(ALICE, "eps_tcs")
    with pytest.raises(SeatError) as e:
        reg.claim(BOB, "eps_tcs")
    assert e.value.code == "held"
    assert reg.holder_of("eps_tcs") == ALICE


def test_one_person_holds_several_desks_and_switches_among_them():
    reg, _ = _reg()
    reg.claim(ALICE, "eps_tcs")
    reg.claim(ALICE, "propulsion")
    assert reg.command_positions(ALICE) == ["eps_tcs", "propulsion"]
    c = reg.connect(ALICE)
    reg.heartbeat(c.conn_id, ALICE, "propulsion")
    assert c.active_position == "propulsion"
    reg.heartbeat(c.conn_id, ALICE, "flight_director")     # not held: ignored
    assert c.active_position == "propulsion"


def test_same_display_name_different_people_stay_distinct():
    reg, _ = _reg()
    reg.touch_person("a1@c2o.live", "Sam", verified=True, instructor=False)
    reg.touch_person("a2@c2o.live", "Sam", verified=True, instructor=False)
    reg.claim("a1@c2o.live", "ttc")
    with pytest.raises(SeatError):
        reg.claim("a2@c2o.live", "ttc")
    assert reg.command_positions("a2@c2o.live") == []


def test_request_handover_is_logged_and_times_out_after_60_s():
    reg, clk = _reg()
    reg.claim(ALICE, "aocs")
    assert reg.request(BOB, "aocs")["status"] == "requested"
    assert [r.position for r in reg.requests_for(ALICE)] == ["aocs"]
    reg.answer(ALICE, "aocs", True)
    assert reg.holder_of("aocs") == BOB
    ev = [e for e in reg.events if e["action"] == "handover"][-1]
    assert ev["position"] == "aocs" and ev["person_id"] == BOB and ev["from_person"] == ALICE
    # a second request expires unanswered
    reg.request(ALICE, "aocs")
    clk.t += 61
    assert reg.requests_for(BOB) == []
    assert any(e["action"] == "request_expired" for e in reg.events)
    with pytest.raises(SeatError):
        reg.answer(BOB, "aocs", True)


def test_declined_request_keeps_the_holder():
    reg, _ = _reg()
    reg.claim(ALICE, "ttc")
    reg.request(BOB, "ttc")
    reg.answer(ALICE, "ttc", False)
    assert reg.holder_of("ttc") == ALICE
    assert any(e["action"] == "request_declined" for e in reg.events)


def test_idle_after_3_min_reclaimable_after_5_min():
    reg, clk = _reg()
    c = reg.connect(ALICE)
    reg.claim(ALICE, "payload_ops")
    reg.tick()
    assert reg.seat_state("payload_ops") == "staffed"
    clk.t += 181
    assert reg.seat_state("payload_ops") == "idle"
    with pytest.raises(SeatError):
        reg.claim(BOB, "payload_ops")                    # idle is not yet reclaimable
    reg.tick()
    clk.t += 120
    assert reg.seat_state("payload_ops") == "reclaimable"
    reg.tick()
    assert [e["action"] for e in reg.events if e["position"] == "payload_ops"][-2:] == ["idle", "away"]
    reg.claim(BOB, "payload_ops")
    assert reg.holder_of("payload_ops") == BOB
    assert reg.events[-1]["action"] == "reclaim"
    # Alice's heartbeat brings presence back, but not the desk
    reg.heartbeat(c.conn_id, ALICE)
    assert reg.command_positions(ALICE) == []


def test_lock_blocks_self_service_but_not_the_instructor():
    reg, _ = _reg()
    reg.lock(PROF, True)
    with pytest.raises(SeatError) as e:
        reg.claim(ALICE, "eps_tcs")
    assert e.value.code == "locked"
    reg.assign(PROF, "eps_tcs", ALICE)
    assert reg.holder_of("eps_tcs") == ALICE
    with pytest.raises(SeatError):
        reg.release(ALICE, "eps_tcs")
    reg.lock(PROF, False)
    reg.release(ALICE, "eps_tcs")


def test_instructor_override_vacate_bench_and_rotate():
    reg, _ = _reg()
    reg.claim(ALICE, "flight_director")
    reg.claim(BOB, "eps_tcs")
    with pytest.raises(SeatError) as e:
        reg.assign(ALICE, "eps_tcs", ALICE)               # not an instructor
    assert e.value.code == "instructor"
    reg.assign(PROF, "eps_tcs", ALICE)                    # without asking
    assert reg.holder_of("eps_tcs") == ALICE and reg.command_positions(BOB) == []
    reg.assign(PROF, "ttc", BOB)
    moved = reg.rotate(PROF)
    assert reg.holder_of("eps_tcs") == ALICE              # flight_director -> eps_tcs
    assert reg.holder_of("aocs") == ALICE                 # eps_tcs -> aocs
    assert reg.holder_of("payload_ops") == BOB            # ttc -> payload_ops
    assert reg.holder_of("flight_director") is None and len(moved) == 3
    freed = reg.bench(PROF, ALICE)                        # "sick member"
    assert sorted(freed) == ["aocs", "eps_tcs"] and reg.command_positions(ALICE) == []
    reg.vacate(PROF, "payload_ops")
    assert reg.holder_of("payload_ops") is None
    actions = [e["action"] for e in reg.events]
    for a in ("assign", "rotate", "vacate"):
        assert a in actions


def test_pair_shadow_is_read_only_second_commands():
    reg, _ = _reg()
    reg.claim(ALICE, "aocs")
    with pytest.raises(SeatError):
        reg.pair(PROF, "aocs", BOB)                        # pair not ticked yet
    reg.set_pair_mode(PROF, "aocs", "shadow")
    reg.pair(PROF, "aocs", BOB)
    assert "aocs" in reg.view_positions(BOB) and reg.command_positions(BOB) == []
    reg.set_pair_mode(PROF, "aocs", "second")
    assert reg.command_positions(BOB) == ["aocs"]
    reg.set_pair_mode(PROF, "aocs", None)
    assert reg.command_positions(BOB) == [] and "aocs" not in reg.view_positions(BOB)


def test_screens_views_and_board():
    reg, _ = _reg()
    reg.claim(ALICE, "eps_tcs")
    reg.claim(ALICE, "propulsion")
    s1 = reg.connect(ALICE)
    s2 = reg.connect(ALICE)
    assert (s1.label, s2.label) == ("screen 1", "screen 2")
    reg.set_view(s2.conn_id, "tile", ["eps_tcs", "propulsion"], ALICE)
    reg.set_view(s1.conn_id, "wall", [], PROF)             # instructor sets any screen
    with pytest.raises(SeatError):
        reg.set_view(s1.conn_id, "wall", [], BOB)          # nobody else
    b = reg.board(for_instructor=True)
    alice = next(p for p in b["people"] if p["id"] == ALICE)
    assert {s["view"]["kind"] for s in alice["screens"]} == {"tile", "wall"}
    vacant = [c["position"] for c in b["positions"] if c["state"] == "vacant"]
    assert "flight_director" in vacant and "eps_tcs" not in vacant
    assert "people" not in reg.board(for_instructor=False)


# ═══════════════════════════════════════════════════════════ IAP JWT ═══

def _verify(iap, tok, aud=(AUD_OPS,)):
    return verify_token(tok, KeySet.from_jwks(iap.jwks()), aud)


def test_jwt_valid_and_email_from_the_claim():
    iap = FakeIap()
    claims = _verify(iap, iap.token("Alice@C2O.live"))
    assert claims["email"] == "alice@c2o.live"
    assert _verify(iap, iap.token(ALICE, aud=AUD_SIM), (AUD_OPS, AUD_SIM))["email"] == ALICE


@pytest.mark.parametrize("kw,code", [
    ({"aud": "/projects/1/global/backendServices/9"}, "aud"),
    ({"iss": "https://evil.example"}, "iss"),
    ({"iat": -4000, "exp": -3000}, "expired"),        # iat/exp: seconds from now
    ({"iat": 600}, "iat"),
    ({"iat": -10, "exp": 7200}, "lifetime"),
    ({"kid": "other"}, "kid"),
    ({"alg": "HS256"}, "alg"),
])
def test_jwt_refusals(kw, code):
    iap = FakeIap()
    now = time.time()                                  # at run time, not collection
    kw = {k: (now + v if k in ("iat", "exp") else v) for k, v in kw.items()}
    with pytest.raises(IapJwtError) as e:
        _verify(iap, iap.token(ALICE, **kw))
    assert e.value.code == code


def test_jwt_forged_signature_and_garbage():
    iap, other = FakeIap(), FakeIap()                    # same kid, different key
    with pytest.raises(IapJwtError) as e:
        _verify(iap, other.token(ALICE))
    assert e.value.code == "signature"
    for junk in ("", "a.b", "x.y.z", "....", "eyJ.eyJ.sig"):
        with pytest.raises(IapJwtError):
            _verify(iap, junk)
    with pytest.raises(IapJwtError) as e:
        verify_token(iap.token(ALICE), KeySet.from_jwks(iap.jwks()), ())
    assert e.value.code == "audience-unset"


def test_verifier_refetches_keys_on_rotation():
    old, new = FakeIap("k-old"), FakeIap("k-new")
    docs = [old.jwks(), {"keys": [old.jwk(), new.jwk()]}]
    calls = []

    def fetch():
        calls.append(1)
        return docs[min(len(calls) - 1, 1)]

    v = IapVerifier([AUD_OPS], fetch=fetch)

    async def run():
        assert (await v.verify(old.token(ALICE)))["email"] == ALICE
        assert (await v.verify(new.token(BOB)))["email"] == BOB   # unknown kid -> refetch
    asyncio.run(run())
    assert len(calls) == 2


# ═══════════════════════════════════════════ MCS: authority over HTTP ═══

def _server(tmp_path, monkeypatch, *, mode="iap", iap=None, env_extra=None):
    from smo_mcs import server as srv_mod
    real = srv_mod.load_positions(CONFIG_DIR)
    monkeypatch.setenv("SMO_TM_ARCHIVE", str(tmp_path / "archive.db"))
    with patch("smo_mcs.server.load_mcs_displays", return_value=MCSDisplayConfig()), \
         patch("smo_mcs.server.load_positions", return_value=real), \
         patch("smo_mcs.server.load_tc_catalog", return_value=[]):
        server = srv_mod.MCSServer(config_dir=str(tmp_path / "cfg"), connect_host="localhost",
                                   connect_port=9999, http_port=0)
    env = {"SMO_SEATS": mode, "SMO_INSTRUCTORS": PROF, **(env_extra or {})}
    verifier = IapVerifier([AUD_OPS, AUD_SIM], keys=KeySet.from_jwks(iap.jwks())) if iap else None
    server._seats = SeatService(list(real), sim_clock=time.time, env=env, mode=mode,
                                verifier=verifier)
    w = MagicMock()
    w.is_closing.return_value = False
    w.drain = AsyncMock()
    server._tc_writer = w
    return server


def _app(server):
    app = web.Application()
    register_seat_routes(app, server._seats)
    r = app.router
    r.add_post("/api/pus-command", server._handle_pus_command)
    r.add_get("/api/verification-log", server._handle_verification_log)
    r.add_post("/api/procedure/load", server._handle_proc_load)
    r.add_post("/api/procedure/start", server._handle_proc_start)
    r.add_post("/api/procedure/abort", server._handle_proc_abort)
    r.add_get("/api/procedure/status", server._handle_proc_status)
    r.add_post("/api/go-nogo/poll", server._handle_go_nogo_poll)
    r.add_post("/api/go-nogo/respond", server._handle_go_nogo_respond)
    r.add_post("/api/alarms/{alarm_id}/ack", server._handle_alarm_ack)
    r.add_post("/api/schedule/upload-s11", server._handle_s11_schedule_upload)
    return app


async def _client(app):
    c = TestClient(TestServer(app))
    await c.start_server()
    return c


@pytest.mark.asyncio
async def test_forged_position_refused_unknown_denied_log_names_the_person(tmp_path, monkeypatch):
    iap = FakeIap()
    server = _server(tmp_path, monkeypatch, iap=iap)
    c = await _client(_app(server))
    try:
        A = iap.headers(ALICE)
        r = await c.post("/api/seats/connect", json={"label": "left screen"}, headers=A)
        conn = (await r.json())["conn_id"]
        A = {**A, "X-SMO-Screen": conn}
        assert (await c.post("/api/seats/claim", json={"position": "eps_tcs"}, headers=A)).status == 200
        # forged FD position: refused, nothing written to the TC socket
        r = await c.post("/api/pus-command", headers=A, json={
            "service": 8, "subtype": 1, "data_hex": "10", "position": "flight_director"})
        assert r.status == 403
        j = await r.json()
        assert j["code"] == "not-holder" and j["status"] == "denied"
        # unknown position: denied
        r = await c.post("/api/pus-command", headers=A, json={
            "service": 8, "subtype": 1, "data_hex": "10", "position": "astronaut"})
        assert r.status == 403 and (await r.json())["code"] == "unknown-position"
        assert server._tc_writer.write.call_count == 0
        # own desk, from the registry (no position in the body at all)
        r = await c.post("/api/pus-command", headers=A, json={
            "service": 8, "subtype": 1, "data_hex": "10", "name": "EPS_X"})
        assert r.status == 200, await r.text()
        assert server._tc_writer.write.call_count == 1
        row = server._verification_log[0]
        assert row["position"] == "eps_tcs" and row["person"] == ALICE
        assert row["verified"] is True and row["screen"] == "left screen"
        arch = server._archive.query_commands()
        assert arch and arch[-1]["person"] == ALICE and arch[-1]["screen"] == "left screen"
        # an FD-only function from the eps desk is refused by its authority
        r = await c.post("/api/pus-command", headers=A, json={
            "service": 8, "subtype": 1, "data_hex": "00"})
        assert r.status == 403
        # S11.4 cannot smuggle a command the desk may not send
        r = await c.post("/api/pus-command", headers=A, json={
            "service": 11, "subtype": 4, "data_hex": "00001000" + "0801" + "00"})
        assert r.status == 403
    finally:
        await c.close()


@pytest.mark.asyncio
async def test_identity_required_and_verified(tmp_path, monkeypatch):
    iap = FakeIap()
    server = _server(tmp_path, monkeypatch, iap=iap)
    c = await _client(_app(server))
    try:
        body = {"service": 17, "subtype": 1, "data_hex": ""}
        # no IAP at all
        assert (await c.post("/api/pus-command", json=body)).status == 401
        # plain header only (IAP bypassed): refused, the header is not trusted
        r = await c.post("/api/pus-command", json=body,
                         headers={"X-Goog-Authenticated-User-Email": f"accounts.google.com:{PROF}"})
        assert r.status == 401
        # header and assertion disagree
        h = {**iap.headers(ALICE), "X-Goog-Authenticated-User-Email": f"accounts.google.com:{PROF}"}
        assert (await c.post("/api/pus-command", json=body, headers=h)).status == 401
        # another signer
        assert (await c.post("/api/pus-command", json=body,
                             headers=FakeIap().headers(ALICE))).status == 401
        # signed in, verified, but no desk
        r = await c.post("/api/pus-command", json=body, headers=iap.headers(ALICE))
        assert r.status == 403 and (await r.json())["code"] == "no-desk"
    finally:
        await c.close()


@pytest.mark.asyncio
async def test_instructor_actions_are_server_side(tmp_path, monkeypatch):
    iap = FakeIap()
    server = _server(tmp_path, monkeypatch, iap=iap)
    c = await _client(_app(server))
    try:
        A, B, P = iap.headers(ALICE), iap.headers(BOB), iap.headers(PROF, aud=AUD_SIM)
        await c.post("/api/seats/connect", json={}, headers=A)
        await c.post("/api/seats/connect", json={}, headers=B)
        assert (await c.get("/api/seats/board", headers=A)).status == 403
        assert (await c.post("/api/seats/rotate", json={}, headers=A)).status == 403
        assert (await c.post("/api/seats/assign", json={"position": "ttc", "person": BOB},
                             headers=A)).status == 403
        # the instructor (reached through the sim host's audience) assigns
        r = await c.post("/api/seats/assign", json={"position": "ttc", "person": BOB}, headers=P)
        assert r.status == 200, await r.text()
        b = await (await c.get("/api/seats/board", headers=P)).json()
        assert next(x for x in b["positions"] if x["position"] == "ttc")["holder"]["id"] == BOB
        assert {p["id"] for p in b["people"]} >= {ALICE, BOB}
        # participants see names on the desks but no screens, ids or bench
        pb = await (await c.get("/api/seats", headers=A)).json()
        assert "people" not in pb["board"]
        ttc = next(x for x in pb["board"]["positions"] if x["position"] == "ttc")
        assert ttc["holder"]["name"] == BOB and "id" not in ttc["holder"]
        # lock: self-claim refused
        await c.post("/api/seats/lock", json={"on": True}, headers=P)
        r = await c.post("/api/seats/claim", json={"position": "aocs"}, headers=A)
        assert r.status == 423
        ev = await (await c.get("/api/seats/events?format=csv", headers=P)).text()
        assert "assign,ttc," in ev and "lock" in ev
    finally:
        await c.close()


@pytest.mark.asyncio
async def test_procedure_runner_runs_as_the_loaders_desk(tmp_path, monkeypatch):
    """Walkthrough M2: the procedure panel used to send as
    "procedure_runner" with no authority check."""
    iap = FakeIap()
    server = _server(tmp_path, monkeypatch, iap=iap)
    c = await _client(_app(server))
    try:
        A, B = iap.headers(ALICE), iap.headers(BOB)
        for h, pos in ((A, "eps_tcs"), (B, "aocs")):
            await c.post("/api/seats/connect", json={}, headers=h)
            await c.post("/api/seats/claim", json={"position": pos}, headers=h)
        steps = [{"service": 8, "subtype": 1, "data_hex": "00", "description": "AOCS func 0"}]
        r = await c.post("/api/procedure/load", headers=A, json={"name": "t", "steps": steps})
        assert r.status == 200, await r.text()
        assert (await r.json())["position"] == "eps_tcs"
        # Bob (aocs) may not drive Alice's procedure
        assert (await c.post("/api/procedure/start", headers=B)).status == 403
        r = await c.post("/api/procedure/start", headers=A)
        assert r.status == 200
        for _ in range(50):
            st = await (await c.get("/api/procedure/status")).json()
            if st["state"] in ("FAILED", "COMPLETED"):
                break
            await asyncio.sleep(0.05)
        assert st["state"] == "FAILED"                  # eps may not send AOCS func 0
        assert server._tc_writer.write.call_count == 0
        server._feed_procedure_activity()
        items = server._seats.activity_summary()["items"]
        step = [i for i in items if i["kind"] == "g_step"][0]
        assert step["position"] == "eps_tcs" and step["result"] == "FAILED"
    finally:
        await c.close()


@pytest.mark.asyncio
async def test_gonogo_vote_only_for_a_held_desk(tmp_path, monkeypatch):
    iap = FakeIap()
    server = _server(tmp_path, monkeypatch, iap=iap)
    c = await _client(_app(server))
    try:
        A, F = iap.headers(ALICE), iap.headers(BOB)
        for h, pos in ((A, "eps_tcs"), (F, "flight_director")):
            await c.post("/api/seats/connect", json={}, headers=h)
            await c.post("/api/seats/claim", json={"position": pos}, headers=h)
        r = await c.post("/api/go-nogo/poll", headers=A,
                         json={"position": "flight_director", "label": "burn"})
        assert r.status == 403
        assert (await c.post("/api/go-nogo/poll", headers=F, json={"label": "burn"})).status == 200
        r = await c.post("/api/go-nogo/respond", headers=A,
                         json={"position": "ttc", "response": "GO"})
        assert r.status == 403
        r = await c.post("/api/go-nogo/respond", headers=A, json={"response": "NOGO"})
        assert r.status == 200 and (await r.json())["position"] == "eps_tcs"
        kinds = [(i["kind"], i["position"]) for i in server._seats.activity_summary()["items"]]
        assert ("g_poll", "flight_director") in kinds and ("g_vote", "eps_tcs") in kinds
    finally:
        await c.close()


@pytest.mark.asyncio
async def test_seats_off_keeps_laptop_mode_but_denies_unknown(tmp_path, monkeypatch):
    server = _server(tmp_path, monkeypatch, mode="off")
    c = await _client(_app(server))
    try:
        r = await c.post("/api/pus-command", json={
            "service": 8, "subtype": 1, "data_hex": "10", "position": "eps_tcs"})
        assert r.status == 200
        row = server._verification_log[0]
        assert row["position"] == "eps_tcs" and row["verified"] is False
        r = await c.post("/api/pus-command", json={
            "service": 8, "subtype": 1, "data_hex": "10", "position": "nobody"})
        assert r.status == 403
        assert (await c.post("/api/seats/claim", json={"position": "ttc"})).status == 409
    finally:
        await c.close()


@pytest.mark.asyncio
async def test_local_mode_typed_names_are_unverified(tmp_path, monkeypatch):
    server = _server(tmp_path, monkeypatch, mode="local")
    c = await _client(_app(server))
    try:
        r = await c.post("/api/seats/connect", json={})
        assert (await r.json())["me"]["needs_name"] is True
        r = await c.post("/api/seats/connect", json={"name": "Ava"})
        j = await r.json()
        assert j["me"]["name"] == "Ava" and j["me"]["verified"] is False
        await c.post("/api/seats/claim", json={"position": "ttc"})
        r = await c.post("/api/pus-command", json={"service": 17, "subtype": 1, "data_hex": ""})
        assert r.status == 200
        row = server._verification_log[0]
        assert row["person"] == "Ava" and row["verified"] is False and row["position"] == "ttc"
    finally:
        await c.close()


# ═════════════════════════════════════════════════════════════ voice ═══

@pytest.mark.asyncio
async def test_voice_token_follows_the_seat(tmp_path, monkeypatch):
    pytest.importorskip("livekit.api")
    from smo_mcs.voice import register_voice_routes
    iap = FakeIap()
    server = _server(tmp_path, monkeypatch, iap=iap)
    app = _app(server)
    register_voice_routes(app, CONFIG_DIR, env={"SMO_VOICE": "dev"}, seats=server._seats)
    c = await _client(app)
    try:
        A = iap.headers(ALICE)
        await c.post("/api/seats/connect", json={}, headers=A)
        await c.post("/api/seats/claim", json={"position": "ttc"}, headers=A)
        cfg = await (await c.get("/api/voice/config", headers=A)).json()
        assert cfg["positions"] == ["ttc"] and cfg["identity"]["verified"] is True
        r = await c.post("/api/voice/token", headers=A, json={"position": "flight_director"})
        assert r.status == 403 and (await r.json())["code"] == "not-holder"
        r = await c.post("/api/voice/token", headers=A, json={"position": "ttc"})
        assert r.status == 200
        tok = await r.json()
        assert tok["position"] == "ttc" and tok["identity"]["name"] == ALICE
        assert (await c.post("/api/voice/token", headers=A,
                             json={"position": "instructor"})).status == 403
        # talk edges reach the anonymous feed under the seat's position
        await c.post("/api/seats/talk", headers=A, json={"loop": "fd", "on": True})
        await c.post("/api/seats/talk", headers=A, json={"loop": "fd", "on": False})
        talk = [i for i in server._seats.activity_summary()["items"] if i["kind"] == "talk"]
        assert talk and talk[0]["position"] == "ttc" and talk[0]["loop"] == "fd"
        r = await c.post("/api/seats/talk", headers=A,
                         json={"loop": "fd", "on": True, "position": "aocs"})
        assert r.status == 403
    finally:
        await c.close()


# ══════════════════════════════════════════════ anonymous activity ═══

@pytest.mark.asyncio
async def test_activity_summary_carries_no_identity(tmp_path, monkeypatch):
    iap = FakeIap()
    server = _server(tmp_path, monkeypatch, iap=iap)
    c = await _client(_app(server))
    secrets_ = [ALICE, BOB, PROF, "alice", "bob", "Left screen", "screen 1"]
    try:
        A, B, P = iap.headers(ALICE), iap.headers(BOB), iap.headers(PROF)
        ra = await (await c.post("/api/seats/connect", json={"label": "Left screen"},
                                 headers=A)).json()
        await c.post("/api/seats/connect", json={}, headers=B)
        await c.post("/api/seats/claim", json={"position": "eps_tcs"}, headers=A)
        await c.post("/api/seats/claim", json={"position": "flight_director"}, headers=B)
        await c.post("/api/seats/request", json={"position": "flight_director"}, headers=A)
        await c.post("/api/seats/answer", json={"position": "flight_director", "accept": False},
                     headers=B)
        server._alarm_journal.appendleft({"id": 7, "subsystem": "eps", "severity": 3,
                                          "name": "eps.bat_soc", "parameter": "0x0101",
                                          "acknowledged": False, "timestamp": time.time()})
        server._acknowledge_alarm = AsyncMock(return_value={"id": 7, "subsystem": "eps",
                                                            "severity": 3, "name": "eps.bat_soc",
                                                            "parameter": "0x0101"})
        assert (await c.post("/api/alarms/7/ack", json={}, headers=A)).status == 200
        await c.post("/api/go-nogo/poll", json={"label": "pass 3"}, headers=B)
        await c.post("/api/go-nogo/respond", json={"response": "GO"}, headers=A)
        await c.post("/api/seats/talk", json={"loop": "fd", "on": True}, headers=A)
        await c.post("/api/seats/talk", json={"loop": "fd", "on": False}, headers=A)
        server._seats.tick()
        assert (await c.get("/api/seats/activity", headers=A)).status == 403
        r = await c.get("/api/seats/activity", headers=P)
        assert r.status == 200
        summ = await r.json()
        kinds = {i["kind"] for i in summ["items"]}
        assert {"g_ack", "g_poll", "g_vote", "talk", "seat"} <= kinds
        ack = next(i for i in summ["items"] if i["kind"] == "g_ack")
        assert ack["position"] == "eps_tcs" and ack["alarm_id"] == 7
        states = {p["id"]: p["state"] for p in summ["positions"]}
        assert states["eps_tcs"] == "staffed" and states["ttc"] == "vacant"
        for it in summ["items"]:
            assert set(it) <= ITEM_KEYS, it
        assert summary_has_identity(summ, secrets_ + [ra["conn_id"]]) == []
        assert set(summ) == {"schema", "seq", "now_sim", "positions", "talking", "items"}
        since = summ["seq"]
        again = await (await c.get(f"/api/seats/activity?since={since}", headers=P)).json()
        assert again["items"] == []
    finally:
        await c.close()


def test_activity_add_drops_unknown_keys():
    act = GroundActivity(time.time)
    it = act.add("alarm", "g_ack", "ttc", person_id=ALICE, name="Alice", email=ALICE,
                 screen="screen 1", alarm_id=3)
    assert set(it) <= ITEM_KEYS and ALICE not in json.dumps(it)


# ═══════════════════════════════ laptop: instructor app forwards to MCS ═══

@pytest.mark.asyncio
async def test_instructor_app_forwards_seats_to_the_local_mcs(monkeypatch):
    """One-host laptop run: the simulator's instructor app answers
    /api/seats* from the MCS on the same host (behind the GSG this route is
    never reached: the GSG answers it on the ground)."""
    seen = []

    async def fake(request):
        seen.append((request.method, request.path_qs, dict(request.headers)))
        return web.json_response({"from": "mcs"})
    mcs = web.Application()
    mcs.router.add_route("*", "/api/seats{tail:.*}", fake)
    ms = TestServer(mcs)
    await ms.start_server()
    from smo_simulator.instructor.app import create_instructor_app
    monkeypatch.setenv("SMO_INSTRUCTOR_SEATS_URL", str(ms.make_url("")).rstrip("/"))
    c = TestClient(TestServer(create_instructor_app(MagicMock(), ui_mode="modern")))
    await c.start_server()
    try:
        r = await c.get("/api/seats/activity?since=3",
                        headers={"Authorization": "Bearer x", "X-SMO-Screen": "abcdefgh12"})
        assert r.status == 200 and (await r.json())["from"] == "mcs"
        assert seen[0][1] == "/api/seats/activity?since=3"
        assert "Authorization" not in seen[0][2] and seen[0][2]["X-SMO-Screen"] == "abcdefgh12"
        await ms.close()
        r = await c.get("/api/seats/board")
        assert r.status == 502
    finally:
        await c.close()
    monkeypatch.setenv("SMO_INSTRUCTOR_SEATS_URL", "off")
    app = create_instructor_app(MagicMock(), ui_mode="modern")
    assert not any(getattr(r.resource, "canonical", "").startswith("/api/seats")
                   for r in app.router.routes())
