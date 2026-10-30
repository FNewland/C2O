"""smo-link unit tests: codec, auth, clock, replay, priority, deny-list, config hash."""
from __future__ import annotations

import asyncio
import random
import shutil
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from smo_link import protocol as P
from smo_link.auth import AuthError, NonceCache, Verifier, make_header, parse_secret
from smo_link.clock import ClockEstimator, SimClockAnchor, retime_state
from smo_link.confighash import MISSION_KEYS, STRICT_FILES, WARN_FILES, compare, compute
from smo_link.channel import SecureChannel
from smo_link.httpproxy import (deny_reason, filter_request_headers, filter_response_headers,
                                normalise_path, origin_allowed)
from smo_link.mux import LinkConnection
from smo_link.replay import ReplayBuffer
from smo_link.agent import backoff_delay

CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs" / "eosat1"


# --- frame codec -------------------------------------------------------------

def test_worked_example_from_spec():
    pkt = bytes.fromhex("0864C02A") + bytes(14)
    payload = len(pkt).to_bytes(2, "big") + pkt
    frame = P.encode(P.DATA, P.S_TM, 1000, payload)
    assert frame[:8] == bytes.fromhex("21000002000003E8")
    assert frame[8:10] == b"\x00\x12"


@pytest.mark.parametrize("ftype", sorted(P.TYPE_NAMES))
def test_codec_round_trip(ftype):
    for stream, seq, flags, size in [(0, 0, 0, 0), (2, 2**32 - 1, P.FIN | P.GAP, 100),
                                     (65535, 7, 0xFF, P.MAX_PAYLOAD)]:
        payload = bytes(random.getrandbits(8) for _ in range(size))
        f = P.decode(P.encode(ftype, stream, seq, payload, flags))
        assert f == P.Frame(ftype, flags, stream, seq, payload)


def test_codec_limits():
    with pytest.raises(ValueError):
        P.encode(P.DATA, 1, 0, bytes(P.MAX_PAYLOAD + 1))
    with pytest.raises(P.ProtocolError):
        P.decode(b"\x11\x00\x00")
    with pytest.raises(P.ProtocolError):
        P.decode(b"\x11" + bytes(7))  # version 1 (pre-v2 peers are refused)
    with pytest.raises(P.ProtocolError):
        P.decode(b"\x31" + bytes(7))  # version 3
    with pytest.raises(P.ProtocolError):
        P.decode(b"\x1f" + bytes(7))  # type 15
    with pytest.raises(P.ProtocolError):
        P.decode(bytes(P.MAX_FRAME + 1))


def test_codec_fuzz_never_crashes():
    rng = random.Random(1234)
    for _ in range(5000):
        blob = bytes(rng.getrandbits(8) for _ in range(rng.randint(0, 40)))
        try:
            f = P.decode(blob)
        except P.ProtocolError:
            continue
        assert P.encode(f.type, f.stream, f.seq, f.payload, f.flags) == blob


def test_split_records_and_seq_arith():
    buf = bytearray(b"\x00\x02ab\x00\x03cde\x00\x05xy")
    assert P.split_records(buf) == [b"\x00\x02ab", b"\x00\x03cde"]
    assert bytes(buf) == b"\x00\x05xy"
    with pytest.raises(P.ProtocolError):
        P.split_records(bytearray(b"\x00\x00"))
    assert P.seq_diff(1, 2**32 - 1) == 2
    assert P.seq_diff(2**32 - 1, 1) == -2
    assert P.seq_add(2**32 - 1, 2) == 1


def test_kv_logging_quotes():
    assert P.kv("x", a=1, b="two words") == 'event=x a=1 b="two words"'


# --- auth --------------------------------------------------------------------

SECRET = bytes(range(32))


def test_auth_good():
    v = Verifier(SECRET, "sess-1")
    assert v.verify(make_header(SECRET, "sess-1")) == "sess-1"


def test_auth_bad_signature_and_secret():
    v = Verifier(SECRET, "sess-1")
    hdr = make_header(SECRET, "sess-1")
    bad = hdr[:-1] + ("0" if hdr[-1] != "0" else "1")
    with pytest.raises(AuthError, match="signature"):
        v.verify(bad)
    with pytest.raises(AuthError, match="signature"):
        v.verify(make_header(b"x" * 32, "sess-1"))
    with pytest.raises(AuthError, match="session"):
        v.verify(make_header(SECRET, "other"))
    for junk in (None, "", "Bearer abc", "SMO-Link v=1, session=s"):
        with pytest.raises(AuthError):
            v.verify(junk)


def test_auth_skew():
    v = Verifier(SECRET, "s")
    now = 1_800_000_000
    assert v.verify(make_header(SECRET, "s", now=now - 119), now=now)
    with pytest.raises(AuthError, match="skew"):
        v.verify(make_header(SECRET, "s", now=now - 121), now=now)
    with pytest.raises(AuthError, match="skew"):
        v.verify(make_header(SECRET, "s", now=now + 121), now=now)


def test_auth_replay_and_nonce_expiry():
    v = Verifier(SECRET, "s", nonces=NonceCache(ttl=600))
    now = 1_800_000_000
    hdr = make_header(SECRET, "s", now=now, nonce="0123456789abcdef")
    v.verify(hdr, now=now)
    with pytest.raises(AuthError, match="replay"):
        v.verify(hdr, now=now + 1)
    # A re-signed request with the same nonce after the 10-minute window is fresh.
    hdr2 = make_header(SECRET, "s", now=now + 601, nonce="0123456789abcdef")
    assert v.verify(hdr2, now=now + 601) == "s"


def test_parse_secret():
    assert parse_secret("00" * 32) == bytes(32)
    with pytest.raises(AuthError):
        parse_secret("zz")
    with pytest.raises(AuthError):
        parse_secret("00" * 4)
    with pytest.raises(AuthError):
        parse_secret("00" * 16)          # L6: 16 bytes used to be accepted
    with pytest.raises(ValueError):
        Verifier(b"", "s")
    with pytest.raises(ValueError):
        Verifier(b"x" * 16, "s")


# --- clock -------------------------------------------------------------------

def test_clock_estimator_asymmetric_delay():
    """True offset 5 s; the min-delay sample of the last 8 bounds the error
    by half its asymmetry."""
    est = ClockEstimator()
    true_off = 5.0
    rng = random.Random(7)
    t = 1000.0
    for i in range(8):
        up = 0.05 + rng.random() * 0.4      # GSG -> agent
        down = 0.01 + rng.random() * 0.05   # agent -> GSG (asymmetric)
        if i == 5:
            up, down = 0.020, 0.010          # the best sample
        t1 = t
        t2 = t1 + up + true_off
        t3 = t2 + 0.001
        t4 = t3 - true_off + down
        est.add_sample(t1, t2, t3, t4)
        t += 10
    assert est.rtt == pytest.approx(0.030, abs=1e-6)
    assert abs(est.offset - true_off) <= 0.005 + 1e-9  # |up-down|/2
    # The window keeps only 8 samples: a much better old sample is forgotten.
    for _ in range(8):
        est.add_sample(t, t + 0.3 + true_off, t + 0.3 + true_off, t + 0.31)
        t += 10
    assert est.rtt == pytest.approx(0.31, abs=1e-6)


def test_retime_state_advances_time_fields_only():
    st = {"tick": 3, "sim_time": "2026-08-20T12:00:14+00:00", "met_s": 100.0, "speed": 10.0,
          "time_to_eclipse_entry_s": 30.0, "time_to_eclipse_exit_s": None, "params": {"1": 2}}
    # Agent clock is 2 s ahead of the GSG; sampled at agent 1002 -> GSG 1000; now 1001.5.
    out = retime_state(st, t_agent_wall=1002.0, offset=2.0, now_wall=1001.5)
    assert list(out) == list(st)
    assert out["sim_time"] == "2026-08-20T12:00:29+00:00"
    assert out["met_s"] == pytest.approx(115.0)
    assert out["time_to_eclipse_entry_s"] == pytest.approx(15.0)
    assert out["time_to_eclipse_exit_s"] is None
    assert out["params"] == st["params"] and out["tick"] == 3
    paused = retime_state(dict(st, speed=0.0), 1002.0, 2.0, 1100.0)
    assert paused["sim_time"] == st["sim_time"]
    datetime.fromisoformat(out["sim_time"])


def test_anchor_stale_after_5s():
    a = SimClockAnchor()
    assert a.retimed(0.0) is None
    a.update(100.0, {"sim_time": "2026-01-01T00:00:00+00:00", "speed": 1.0}, rx_mono=50.0)
    assert a.retimed(0.0, now_wall=101.0, now_mono=54.9) is not None
    assert a.retimed(0.0, now_wall=101.0, now_mono=55.1) is None


# --- replay buffer -------------------------------------------------------------

def test_replay_keeps_age_or_bytes_whichever_more():
    rb = ReplayBuffer(max_age_s=10, max_bytes=1000, queue_max_packets=10**6,
                      queue_max_bytes=10**9)
    for i in range(50):
        rb.append(bytes(100), now=float(i) * 0.1)
    while rb.pop_unsent(now=5.0):
        pass
    rb.expire(now=5.0)          # all < 10 s old: all kept although 5000 B > 1000 B
    assert len(rb) == 50
    rb.expire(now=100.0)        # all old: keep the newest 1000 B
    assert rb.replay_bytes == 1000 and len(rb) == 10
    assert rb.oldest_seq == 40


def test_replay_queue_bound_drops_oldest_with_gap():
    rb = ReplayBuffer(queue_max_packets=5, queue_max_bytes=10**9)
    for i in range(8):
        rb.append(bytes([i]), packets=1, now=0.0)
    assert rb.unsent_packets == 5 and rb.dropped_frames == 3
    e = rb.pop_unsent()
    assert e.seq == 3 and e.flags & P.GAP and e.payload == b"\x03"
    assert not rb.pop_unsent().flags & P.GAP


def test_replay_rewind_and_skip():
    rb = ReplayBuffer()
    for i in range(10):
        rb.append(bytes([i]))
    for _ in range(10):
        rb.pop_unsent()
    assert rb.rewind(7) is True
    assert [rb.pop_unsent().seq for _ in range(3)] == [7, 8, 9]
    assert rb.pop_unsent() is None
    rb2 = ReplayBuffer(queue_max_packets=3)
    for i in range(6):
        rb2.append(b"x")
    assert rb2.rewind(0) is False          # gone: resend from oldest with GAP
    e = rb2.pop_unsent()
    assert e.seq == 3 and e.flags & P.GAP
    rb2.append(b"y")
    assert rb2.skip_to_new() == 3
    assert not rb2.has_unsent()


def test_replay_hard_ceiling():
    rb = ReplayBuffer(max_age_s=1e9, max_bytes=10, hard_max_bytes=1000,
                      queue_max_bytes=10**9)
    for _ in range(100):
        rb.append(bytes(100), now=0.0)
        rb.pop_unsent()
    assert rb.replay_bytes <= 1000


# --- priority writer -----------------------------------------------------------

class FakeWS:
    def __init__(self):
        self.sent: list[bytes] = []
        self.closed = False
        self.close_code = None

    async def send_bytes(self, data):
        self.sent.append(data)

    async def close(self, code=1000, message=b""):
        self.closed = True

    def __aiter__(self):
        return self

    async def __anext__(self):
        await asyncio.sleep(3600)
        raise StopAsyncIteration


def _chan() -> SecureChannel:
    return SecureChannel(b"k" * 32, b"k" * 32, b"tx", b"rx")


def _unseal(msgs):
    return [m[:-16] for m in msgs]


async def test_priority_writer_ordering():
    ws = FakeWS()
    conn = LinkConnection(ws, "t", lambda c, f: None, ping_interval=3600, channel=_chan())
    order = [P.P_DUMP, P.P_PROXY, P.P_STATE, P.P_TM, P.P_TC, P.P_CONTROL, P.P_TM, P.P_DUMP]
    for i, prio in enumerate(order):
        conn.enqueue(prio, P.encode(P.DATA, 10 + prio, i))
    conn._tasks = [asyncio.ensure_future(conn._writer())]
    for _ in range(50):
        await asyncio.sleep(0)
    got = [P.decode(b).stream - 10 for b in _unseal(ws.sent)]
    assert got == sorted(order)
    # TM (prio 3) frames keep FIFO order among themselves
    tm_seqs = [P.decode(b).seq for b in _unseal(ws.sent) if P.decode(b).stream == 10 + P.P_TM]
    assert tm_seqs == [3, 6]
    await conn.close()


async def test_writer_respects_high_water():
    ws = FakeWS()
    conn = LinkConnection(ws, "t", lambda c, f: None, ping_interval=3600, channel=_chan())
    level = {"v": 100_000}
    conn.write_buffer_size = lambda: level["v"]
    conn.enqueue(P.P_TM, P.encode(P.DATA, 2, 0))
    conn._tasks = [asyncio.ensure_future(conn._writer())]
    await asyncio.sleep(0.05)
    assert ws.sent == []
    level["v"] = 0
    await asyncio.sleep(0.05)
    assert len(ws.sent) == 1
    await conn.close()


def test_backoff_full_jitter_bounds():
    rng = random.Random(3)
    for attempt in range(12):
        d = backoff_delay(attempt, 0.5, 30.0, rng)
        assert 0 <= d <= min(30.0, 0.5 * 2 ** attempt)


# --- proxy allowlist (M1) and headers (H3) ---------------------------------------

@pytest.mark.parametrize("method,path", [
    # the config editor and its API, however spelled
    ("GET", "/config"), ("GET", "/config/"), ("GET", "/config/x"), ("GET", "/CONFIG"),
    ("GET", "//config"), ("GET", "/static/../config"), ("GET", "/%63onfig"),
    ("GET", "/static/%2e%2e/config"), ("GET", "/static/%252e%252e/config"),
    ("GET", "/api/config/files"), ("PUT", "/api/config/file"), ("GET", "/api/config"),
    ("POST", "/api/config/baselines/x/apply"), ("POST", "/api/reports/generate"),
    ("POST", "/api/reports/generate/"), ("POST", "/api/reports/validate"),
    ("GET", "/../etc/passwd"), ("GET", "/a/../../x"),
    ("GET", "/static/..%5c..%5cx"), ("GET", "/x%00y"),
    # review M1 bypasses: fragment, encoded '#', TAB, params, double encoding
    ("GET", "/config#x"), ("GET", "/config%23x"), ("GET", "/config\t"), ("GET", "/config;x"),
    ("GET", "/%2563onfig"), ("PUT", "/api/conf\tig/file"), ("PUT", "/api/conf%09ig/file"),
    ("GET", "/api/config%2Ffile"), ("GET", "/api/%63onfig/file"), ("GET", "/static/.hidden"),
    # wrong method on an allowed path, lower-case methods, unknown routes
    ("DELETE", "/api/command"), ("PUT", "/api/command"), ("get", "/"), ("POST", "/"),
    ("GET", "/api/state"), ("GET", "/anything"), ("GET", "/ws"), ("GET", "/static/"),
])
def test_allowlist_blocks(method, path):
    assert deny_reason(method, path) is not None


@pytest.mark.parametrize("method,path", [
    ("GET", "/"), ("GET", "/modern"), ("GET", "/classic"), ("HEAD", "/"),
    ("GET", "/static/modern/instructor.js"), ("GET", "/static/shared/design-system.css?v=1"),
    ("GET", "/static/modern/i18n/fr.json"), ("GET", "/static/a/../b.js"),
    ("GET", "/api/instructor/snapshot"), ("GET", "/api/failure-catalog"),
    ("GET", "/api/reports/templates"), ("GET", "/api/reports/templates/pass_summary"),
    ("POST", "/api/command"), ("POST", "/api/breakpoint/save"), ("POST", "/api/breakpoint/load"),
    ("GET", "/api/dumps"), ("GET", "/api/dumps/"), ("GET", "/api/dumps/file?name=x"),
    ("GET", "/api/dumps/dump_sid01_20260820T120000Z.bin/summary"), ("GET", "/dumps"),
    ("GET", "/reports"), ("GET", "/api/reports/file?name=r.html"), ("POST", "//api//command#x"),
])
def test_allowlist_allows(method, path):
    assert deny_reason(method, path) is None, path


def test_allowlist_websocket_only_ws():
    assert deny_reason("GET", "/ws", websocket=True) is None
    assert deny_reason("GET", "/", websocket=True) is not None
    assert deny_reason("GET", "/config", websocket=True) is not None


def test_normalise_path():
    assert normalise_path("/a/./b//c/") == "/a/b/c/"
    assert normalise_path("/a/../b") == "/b"
    assert normalise_path("/..") is None
    assert normalise_path("relative") is None
    assert normalise_path("/config#x") == "/config"
    assert normalise_path("/a;p=1/b;q") == "/a/b"
    assert normalise_path("/%2563") is None           # double encoding refused
    assert normalise_path("/a\tb") is None
    assert normalise_path("/caf%C3%A9") is None       # non-ASCII refused


def test_request_header_allowlist_strips_credentials():
    hdrs = [("Cookie", "GCP_IAP_AUTH_TOKEN_abc=SECRET"), ("Authorization", "Bearer XYZ"),
            ("X-Goog-IAP-JWT-Assertion", "eyJ"), ("X-Forwarded-For", "6.6.6.6"),
            ("Forwarded", "for=1.2.3.4"), ("Proxy-Authorization", "x"), ("Host", "h"),
            ("Connection", "keep-alive, X-Secret-Hop"), ("X-Secret-Hop", "1"),
            ("Accept", "text/html"), ("If-None-Match", '"a"'), ("Content-Type", "x/y"),
            ("User-Agent", "ua"), ("Bad\r\nName", "v"), ("Accept-Language", "fr\r\nX: y")]
    assert filter_request_headers(hdrs) == [("Accept", "text/html"), ("If-None-Match", '"a"'),
                                            ("Content-Type", "x/y"), ("User-Agent", "ua")]


def test_response_header_allowlist_strips_set_cookie():
    hdrs = [("Set-Cookie", "x=1"), ("Location", "https://evil"), ("Content-Type", "text/html"),
            ("ETag", '"a"'), ("Access-Control-Allow-Origin", "*"),
            ("Content-Security-Policy", "default-src *"), ("Transfer-Encoding", "chunked"),
            ("Cache-Control", "no-cache")]
    assert filter_response_headers(hdrs) == [("Content-Type", "text/html"), ("ETag", '"a"'),
                                             ("Cache-Control", "no-cache")]


def test_origin_check():
    assert origin_allowed(None, "h:1", [])
    assert origin_allowed("http://h:1", "h:1", [])
    assert not origin_allowed("http://evil:1", "h:1", [])
    assert not origin_allowed("null", "h:1", [])
    assert origin_allowed("https://instr.example.ca", "127.0.0.1:8080", ["https://instr.example.ca"])
    assert not origin_allowed("http://127.0.0.1:8080", "127.0.0.1:8080", ["https://instr.example.ca"])


# --- config hash -----------------------------------------------------------------

def test_bind_set_paths_exist():
    for rel in STRICT_FILES + WARN_FILES:
        assert (CONFIG_DIR / rel).is_file(), rel
    import yaml
    mission = yaml.safe_load((CONFIG_DIR / "mission.yaml").read_text(encoding="utf-8"))
    for k in MISSION_KEYS:
        assert k in mission, k


def _copy_bind_set(dst: Path):
    for rel in STRICT_FILES + WARN_FILES:
        (dst / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(CONFIG_DIR / rel, dst / rel)


def test_config_hash_crlf_stable(tmp_path):
    _copy_bind_set(tmp_path)
    base = compute(CONFIG_DIR)
    assert compute(tmp_path) == base
    for rel in STRICT_FILES + WARN_FILES:
        p = tmp_path / rel
        p.write_bytes(p.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    assert compute(tmp_path) == base


def test_config_hash_strict_vs_warn(tmp_path):
    _copy_bind_set(tmp_path)
    base = compute(CONFIG_DIR)
    # Deployment keys in mission.yaml are outside the identity subset.
    m = tmp_path / "mission.yaml"
    m.write_text(m.read_text(encoding="utf-8") + "\ndump_dir: /elsewhere\n", encoding="utf-8")
    assert compute(tmp_path)["hash"] == base["hash"]
    (tmp_path / "subsystems/eps.yaml").write_text("changed: 1\n", encoding="utf-8")
    other = compute(tmp_path)
    assert other["hash"] == base["hash"]
    assert compare(base["files"], other["files"]) == ([], ["subsystems/eps.yaml"])
    p = tmp_path / "telemetry/hk_structures.yaml"
    p.write_text(p.read_text(encoding="utf-8") + "\n# edit\n", encoding="utf-8")
    other = compute(tmp_path)
    assert other["hash"] != base["hash"]
    assert compare(base["files"], other["files"])[0] == ["telemetry/hk_structures.yaml"]
    (tmp_path / "orbit.yaml").unlink()
    assert compute(tmp_path)["files"]["orbit.yaml"] == "missing"
