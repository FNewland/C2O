"""The C2O welcome page (sim/tools/portal.py) and its wiring.

Pins:
  - the page renders in EN and FR from the shared frame and design system,
    and every screen string has a French entry in the tools catalog;
  - links: https://<name>.<domain> in the cloud, http://<request host>:<port>
    locally (start.sh ports), with the env overrides start.sh and compose use;
  - /api/status: server-side probes (mocked here), cached, link state from
    the GSG /link-status, spacecraft mode from TM only (never the
    simulator's sc_mode truth), next pass from the MCS contact schedule;
  - the IAP account header is shown (escaped) and absent locally; /healthz;
  - compose, start.sh and the GCP scripts all carry the portal, and the
    apex of the domain routes to it.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest
import yaml
from aiohttp.test_utils import TestClient, TestServer

SIM = Path(__file__).resolve().parents[2]
ROOT = SIM.parent
TOOLS = SIM / "tools"
CATALOG = SIM / "packages/smo-common/src/smo_common/ui/i18n/tools/fr.json"
GCP = ROOT / "deploy" / "gcp"


def _load():
    spec = importlib.util.spec_from_file_location("_tp_portal", TOOLS / "portal.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


pt = _load()


class FakeProber(pt.Prober):
    """Answers from a table {(port, path): (state, status, body)}; anything
    else is "down". Counts calls so caching can be checked."""

    def __init__(self, cfg, table):
        super().__init__(cfg)
        self.table = table
        self.calls = 0

    async def http(self, host, port, path):
        self.calls += 1
        return self.table.get((port, path), ("down", None, None))


def _up(body=None, status=200):
    return ("up", status, body)


async def _client(app):
    c = TestClient(TestServer(app))
    await c.start_server()
    return c


# ── configuration and links ────────────────────────────────────────────

def test_local_links_use_the_request_host_and_start_sh_ports():
    cfg = pt.Config.from_env({})
    by = {s.key: s for s in pt.SERVICES}
    assert cfg.link(by["ops"], "10.0.0.5") == "http://10.0.0.5:9090/"
    assert cfg.link(by["plan"], None) == "http://localhost:9091/"
    assert cfg.link(by["sim"], "lab-pc") == "http://lab-pc:8080/"
    assert cfg.link(by["tm"], "h") == "http://h:8092/"
    assert cfg.link(by["adcs"], "h") == "http://h:8097/"
    assert cfg.link(by["design"], "h") == "http://h:8000/"
    assert cfg.link(by["ops"], "::1") == "http://[::1]:9090/"
    assert cfg.sim_host == "127.0.0.1"
    # every start.sh tool port is on the page
    assert {p for s in pt.SERVICES for p in s.ports} >= {
        9090, 9091, 8080, 8092, 8093, 8094, 8095, 8096, 8097, 8000, 5173}


def test_cloud_links_are_subdomains():
    cfg = pt.Config.from_env({"SMO_PORTAL_DOMAIN": "c2o.live"})
    assert {s.key: cfg.link(s, "c2o.live") for s in pt.SERVICES} == {
        k: f"https://{k}.c2o.live/" for k in
        ("ops", "plan", "design", "tm", "orbit", "radio", "docs", "sim", "scenarios", "adcs")}
    assert cfg.sim_host == "10.20.0.11"               # the cloud sim VM
    by = {s.key: s for s in pt.SERVICES}
    assert cfg.targets(by["scenarios"]) == [("10.20.0.11", 8096)]
    assert cfg.targets(by["ops"]) == [("127.0.0.1", 9090)]


def test_cloud_host_labels_match_the_gcp_tool_list():
    """Every link host must be one the load balancer routes (common.sh)."""
    if not (GCP / "common.sh").exists():
        pytest.skip("deploy/gcp not in this checkout")
    src = (GCP / "common.sh").read_text()
    tools = re.search(r'TOOLS="\n(.*?)\n"', src, re.DOTALL).group(1)
    labels = {ln.split()[1] for ln in tools.splitlines() if ln.strip()}
    assert {s.key for s in pt.SERVICES} == labels | {"ops", "plan", "sim"}


def test_env_overrides():
    cfg = pt.Config.from_env({
        "SMO_PORTAL_DOMAIN": "@DOMAIN@",                  # unrendered template
        "SMO_PORTAL_PORTS": "sim=18080, design=8000/5173, bad=x",
        "SMO_PORTAL_PROBE": "design=spacecdf:8000,scenarios=scenario-gen:8096",
        "SMO_PORTAL_GROUND_HOST": "10.1.2.3",
    })
    by = {s.key: s for s in pt.SERVICES}
    assert cfg.domain == ""
    assert cfg.link(by["sim"], "h") == "http://h:18080/"
    assert cfg.targets(by["sim"]) == [("10.1.2.3", 18080)]
    assert cfg.targets(by["design"]) == [("spacecdf", 8000)]
    assert cfg.targets(by["scenarios"]) == [("scenario-gen", 8096)]
    assert cfg.targets(by["adcs"]) == [("127.0.0.1", 8097)]
    assert pt.display_address("https://ops.c2o.live/") == "ops.c2o.live"


def test_iap_user():
    h = {pt.IAP_USER_HEADER: "accounts.google.com:franz@c2o.live"}
    assert pt.iap_user(h) == "franz@c2o.live"
    assert pt.iap_user({}) is None
    assert pt.iap_user({pt.IAP_USER_HEADER: "  "}) is None


# ── page ───────────────────────────────────────────────────────────────

async def test_page_renders_en_and_fr_with_local_links():
    cfg = pt.Config()
    app = pt.create_app(cfg, FakeProber(cfg, {}))
    c = await _client(app)
    try:
        r = await c.get("/")
        t = await r.text()
        assert r.status == 200 and '<html lang="en">' in t
        assert "/static/shared/tool-page.js" in t and "design-system.css" in t
        assert 'href="http://127.0.0.1:9090/"' in t
        assert ">127.0.0.1:9090<" not in t          # no address line (review §1)
        assert "start.sh" not in t
        for s in pt.SERVICES:
            assert f'id="row-{s.key}"' in t and s.name in t
        for _, title, _ in pt.SECTIONS:
            assert title in t
        assert "Signed in as" not in t                 # no IAP locally
        assert "c2o.live" not in t
        r = await c.get("/?lang=fr")
        assert '<html lang="fr">' in await r.text()
        # the page never waits for probes: status cells start as "Checking"
        # status slots start empty: nothing to read until the first probe
        assert t.count('class="pt-state"') >= len(pt.SERVICES)
    finally:
        await c.close()


async def test_page_in_the_cloud_shows_the_iap_account_escaped(monkeypatch):
    monkeypatch.setenv("SMO_INSTRUCTORS", "franz@c2o.live")
    cfg = pt.Config.from_env({"SMO_PORTAL_DOMAIN": "c2o.live"})
    app = pt.create_app(cfg, FakeProber(cfg, {}))
    c = await _client(app)
    try:
        t = await (await c.get("/", headers={
            pt.IAP_USER_HEADER: "accounts.google.com:franz@c2o.live"})).text()
        assert "Signed in as" in t and "<b>franz@c2o.live</b>" in t
        assert 'href="https://ops.c2o.live/"' in t and 'href="https://adcs.c2o.live/"' in t
        assert "gcp-iap-mode=CLEAR_LOGIN_COOKIE" in t
        assert "localhost" not in t and ":9090" not in t
        t = await (await c.get("/", headers={
            pt.IAP_USER_HEADER: "accounts.google.com:<script>x</script>"})).text()
        assert "<script>x</script>" not in t and "&lt;script&gt;" in t
    finally:
        await c.close()


async def test_instructor_section_only_for_instructors(monkeypatch):
    """SCREEN_REVIEW #17: behind IAP a student sees neither the instructor
    tiles nor their status in the feed; an account in SMO_INSTRUCTORS sees
    both; with no list configured nobody does (closed by default). Laptop
    mode (no domain, no IAP header) keeps everything."""
    monkeypatch.setenv("SMO_INSTRUCTORS", "prof@c2o.live")
    cfg = pt.Config.from_env({"SMO_PORTAL_DOMAIN": "c2o.live"})
    c = await _client(pt.create_app(cfg, FakeProber(cfg, _cloud_table())))
    stu = {pt.IAP_USER_HEADER: "accounts.google.com:student@c2o.live"}
    prof = {pt.IAP_USER_HEADER: "accounts.google.com:Prof@c2o.live"}
    try:
        t = await (await c.get("/", headers=stu)).text()
        assert 'id="row-sim"' not in t and 'id="row-adcs"' not in t
        # a student sees a greyed Instructor card, but no instructor tool names
        assert 'id="row-ops"' in t and "is-locked" in t
        assert all(s.name not in t for s in pt.SERVICES if s.instructors_only)
        d = await (await c.get("/api/status", headers=stu)).json()
        assert not {"sim", "scenarios", "adcs"} & set(d["services"])
        assert all("port" not in v for v in d["services"].values())
        t = await (await c.get("/", headers=prof)).text()
        assert 'id="row-sim"' in t and 'id="row-adcs"' in t
        d = await (await c.get("/api/status", headers=prof)).json()
        assert {"sim", "scenarios", "adcs"} <= set(d["services"])
        monkeypatch.delenv("SMO_INSTRUCTORS")
        t = await (await c.get("/", headers=prof)).text()
        assert 'id="row-sim"' not in t
        t = await (await c.get("/")).text()          # IAP bypassed: still closed
        assert 'id="row-sim"' not in t
    finally:
        await c.close()
    cfg = pt.Config()
    c = await _client(pt.create_app(cfg, FakeProber(cfg, {})))
    try:
        t = await (await c.get("/")).text()
        assert 'id="row-sim"' in t
    finally:
        await c.close()


async def test_healthz():
    cfg = pt.Config()
    c = await _client(pt.create_app(cfg, FakeProber(cfg, {})))
    try:
        r = await c.get("/healthz")
        assert r.status == 200 and (await r.json()) == {"ok": True}
    finally:
        await c.close()


def test_every_screen_string_has_french():
    fr = json.loads(CATALOG.read_text(encoding="utf-8"))
    want = {s.name for s in pt.SERVICES} | {s.purpose for s in pt.SERVICES}
    want |= {t for _, a, b in pt.SECTIONS for t in (a, b)}
    missing = sorted(k for k in want if not fr.get(k))
    assert not missing, missing


# ── status ─────────────────────────────────────────────────────────────

MCS_STATE = {"params": {"0x0300": 1}, "last_frame_age_s": 3.0, "stale": False,
             "sc_mode": "nominal"}
SCHEDULE = {"next_passes": [], "current_contact_status":
            {"in_contact": False, "ground_station": "Svalbard", "time_to_aos": 754.0}}


def _cloud_table(link_state="UP"):
    return {
        (9090, "/"): _up(), (9090, "/api/state"): _up(MCS_STATE),
        (9090, "/api/displays/contact-schedule"): _up(SCHEDULE),
        (9091, "/"): _up(),
        (8080, "/"): _up(), (8080, "/link-status"): _up({"state": link_state, "rtt": 0.04}),
        (8092, "/"): _up(), (8095, "/"): _up(),
        (8093, "/"): ("starting", 503, None),
    }


async def test_status_reports_each_screen_link_mode_and_pass(monkeypatch):
    monkeypatch.setenv("SMO_INSTRUCTORS", "prof@c2o.live")
    cfg = pt.Config.from_env({"SMO_PORTAL_DOMAIN": "c2o.live"})
    prober = FakeProber(cfg, _cloud_table())
    c = await _client(pt.create_app(cfg, prober))
    try:
        r = await c.get("/api/status", headers={
            pt.IAP_USER_HEADER: "accounts.google.com:prof@c2o.live"})
        assert r.headers["Cache-Control"] == "no-store"
        d = await r.json()
        st = {k: v["state"] for k, v in d["services"].items()}
        assert st == {"ops": "up", "plan": "up", "design": "down", "tm": "up",
                      "orbit": "starting", "radio": "down", "docs": "up", "sim": "up",
                      "scenarios": "down", "adcs": "down"}
        assert d["link"]["state"] == "UP"
        assert d["mode"] == {"mode": "SAFE", "source": "TM obdh.mode 0x0300",
                             "age_s": 3.0, "stale": False}
        assert d["pass"] == {"in_contact": False, "station": "Svalbard", "seconds": 754.0}
        assert "checked_at" not in d          # no wall clock beside sim time
        n = prober.calls
        await c.get("/api/status")                       # cached: no new probes
        assert prober.calls == n
    finally:
        await c.close()


async def test_instructor_console_waits_for_a_simulator():
    cfg = pt.Config.from_env({"SMO_PORTAL_DOMAIN": "c2o.live"})
    snap = await FakeProber(cfg, _cloud_table("DOWN")).snapshot()
    assert snap["link"]["state"] == "DOWN"
    assert snap["services"]["sim"]["state"] == "starting"
    assert snap["services"]["sim"]["reason"] == "no-simulator"


async def test_local_simulator_without_a_gateway_is_direct():
    cfg = pt.Config()
    table = {(8080, "/"): _up(), (8080, "/link-status"): _up(None, 404),
             (8080, "/api/state"): _up({"sim_time": 1})}
    snap = await FakeProber(cfg, table).snapshot()
    assert snap["link"]["state"] == "DIRECT"
    assert snap["mode"] is None and snap["pass"] is None      # MCS down
    snap = await FakeProber(cfg, {}).snapshot()
    assert snap["link"]["state"] == "UNREACHABLE"


async def test_design_probe_falls_back_to_the_dev_port():
    cfg = pt.Config()
    snap = await FakeProber(cfg, {(5173, "/"): _up()}).snapshot()
    assert snap["services"]["design"] == {"state": "up", "port": 5173}


def test_mode_comes_from_telemetry_only():
    # The simulator's own mode (sc_mode, truth) must never reach this page.
    assert pt.mode_from_state({"sc_mode": "safe"})["mode"] is None
    assert pt.mode_from_state({"obdh": {"mode": 0}})["mode"] == "NOMINAL"
    m = pt.mode_from_state({"params": {"0x0300": 3}, "last_frame_age_s": 400.0})
    assert m["mode"] == "SCIENCE" and m["stale"] is True
    assert pt.mode_from_state({"params": {"0x0300": 9}})["mode"] == "MODE_9"


def test_pass_from_schedule():
    assert pt.pass_from_schedule({}) is None
    assert pt.pass_from_schedule({"current_contact_status": {
        "in_contact": True, "ground_station": "Inuvik", "time_to_los": 300}}) == {
        "in_contact": True, "station": "Inuvik", "seconds": 300.0}
    assert pt.pass_from_schedule({"current_contact_status": {
        "in_contact": False, "ground_station": "", "time_to_aos": None}})["seconds"] is None


async def test_real_probe_classifies_refused_as_down():
    cfg = pt.Config()
    p = pt.Prober(cfg)
    try:
        state, status, body = await p.http("127.0.0.1", 1, "/")
        assert (state, status, body) == ("down", None, None)
    finally:
        await p.close()


# ── wiring: compose, start.sh, GCP ─────────────────────────────────────

def test_compose_runs_the_portal_in_the_ground_namespace():
    d = yaml.safe_load((SIM / "docker" / "compose.yaml").read_text(encoding="utf-8"))
    svc = d["services"]["portal"]
    assert set(svc["profiles"]) == {"ground", "local-demo"}
    assert svc["network_mode"] == "service:gsg"
    assert "tools/portal.py" in svc["command"] and "8090" in svc["command"]
    assert "${SMO_PUBLISH_ADDR:-127.0.0.1}:8090:8090" in d["services"]["gsg"]["ports"]
    assert "8090" in svc["healthcheck"]["test"][-1]


def test_start_sh_starts_the_portal_and_prints_it_first():
    src = (SIM / "start.sh").read_text()
    assert re.search(r'python "\$SCRIPT_DIR/tools/portal.py" --port 8090 --host "\$SMO_BIND"', src)
    banner = src[src.index('echo "  SMO Suite Running"'):]
    lines = [ln for ln in banner.splitlines() if "http://$ACCESS_HOST" in ln]
    assert "Welcome page" in lines[0] and ":8090" in lines[0]
    # the simulator's fallback console port must not take the portal's
    assert not re.search(r"for LINK_P in [^;]*\b8090\b", src)


def test_gcp_routes_the_apex_to_the_portal():
    if not GCP.exists():
        pytest.skip("deploy/gcp not in this checkout")
    common = (GCP / "common.sh").read_text()
    setup = (GCP / "setup.sh").read_text()
    assert 'BE_PORTAL="$PREFIX-be-portal"' in common and 'HC_PORTAL="$PREFIX-hc-portal"' in common
    assert "portal:8090" in setup
    assert 'hc "$HC_PORTAL" 8090 /healthz' in setup
    assert 'be "$BE_PORTAL" portal' in setup
    assert 'iap_grant "$BE_PORTAL" "$STUDENTS_GROUP"' in setup
    assert 'iap_grant "$BE_PORTAL" "$INSTRUCTORS_GROUP"' in setup
    assert re.search(r"tcp:8090", setup)
    assert "pathMatcher: portal" in setup and '$(bs "$BE_PORTAL")' in setup
    td = (GCP / "teardown.sh").read_text()
    assert "$BE_PORTAL" in td and "$HC_PORTAL" in td and "$FW_PORTAL_SIM" in td
    env = (GCP / "env" / "ground.env.example").read_text()
    assert "SMO_PORTAL_DOMAIN=@DOMAIN@" in env
    assert "Welcome page" in (GCP / "start.sh").read_text()
