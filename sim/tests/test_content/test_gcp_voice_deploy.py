"""Voice loops deployment (deploy/gcp + sim/docker): the LiveKit VM, its
startup script, the ground VM's voice.env, c2o up/down/status/schedule and
the laptop compose service must agree with each other and with the MCS.

Runs the real scripts against stubs (no Google call is ever made):
  * voice-bootstrap.sh renders livekit.yaml / caddy.json / compose.yaml from
    stubbed metadata + Secret Manager; with $LIVEKIT_SERVER_BIN set (a
    livekit-server binary, e.g. built from source) the rendered livekit.yaml
    is also LOADED by the real server, which must start;
  * vm-bootstrap.sh refresh writes sim/docker/voice.env (mode 600) on the
    ground VM, and an empty one when there is no key pair;
  * c2o status / schedule with the voice VM present (the stubs of
    test_gcp_admin_cli.py, extended with the voice VM).
"""
from __future__ import annotations

import base64
import json
import os
import re
import shutil
import socket
import stat
import subprocess
import time
from pathlib import Path

import pytest
import yaml

from tests.test_content.test_gcp_admin_cli import Env, _out

REPO = Path(__file__).resolve().parents[3]
SIM = REPO / "sim"
GCP = REPO / "deploy" / "gcp"
VOICE_BS = GCP / "voice-bootstrap.sh"
VM_BS = GCP / "vm-bootstrap.sh"

pytestmark = pytest.mark.skipif(shutil.which("bash") is None or shutil.which("python3") is None,
                                reason="needs bash and python3")

KEY, SECRET = "APIabcdef123456", "s" * 20 + "-_" + "t" * 21          # 43 url-safe chars
#: LiveKit's documented single-VM firewall list (docs.livekit.io, "Deploy to
#: a VM" + "Firewall configuration", checked 2026-11-02).
LIVEKIT_PORTS = {"tcp:80", "tcp:443", "tcp:7881", "udp:3478", "udp:50000-60000"}


def _sh(path: Path) -> str:
    return path.read_text()


# ── stubs for the VM-side scripts ────────────────────────────────────────

META_CURL = r'''#!/usr/bin/env python3
import json, os, sys
d = os.environ["STUB_DIR"]
url, out = None, None
a = sys.argv[1:]
i = 0
while i < len(a):
    if a[i] == "-o": out = a[i + 1]; i += 1
    elif a[i] in ("-w", "-H"): i += 1
    elif not a[i].startswith("-"): url = a[i]
    i += 1
open(os.path.join(d, "curl.log"), "a").write(json.dumps(a) + "\n")
md = json.load(open(os.path.join(d, "meta.json")))
if "metadata.google.internal" in url:
    key = url.split("/computeMetadata/v1/", 1)[1]
    if key == "instance/service-accounts/default/token":
        print(json.dumps({"access_token": "ya29.stub"})); sys.exit(0)
    if key in md:
        sys.stdout.write(md[key]); sys.exit(0)
    sys.exit(22)
if "secretmanager.googleapis.com" in url:
    name = url.split("/secrets/", 1)[1].split("/", 1)[0]
    sec = json.load(open(os.path.join(d, "secrets.json")))
    code = 200 if name in sec else 404
    body = {"payload": {"data": sec[name]}} if code == 200 else {"error": {"code": 404}}
    if out:
        open(out, "w").write(json.dumps(body))
    sys.stdout.write(str(code)); sys.exit(0)
sys.exit(7)
'''

DOCKER = r'''#!/bin/sh
echo "$*" >> "$STUB_DIR/docker.log"
exit 0
'''


def _b64(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


def _stubs(tmp: Path, meta: dict, secrets: dict) -> dict:
    d = tmp / "stubs"
    d.mkdir()
    for n, body in (("curl", META_CURL), ("docker", DOCKER), ("logger", "#!/bin/sh\nexit 0\n")):
        (d / n).write_text(body)
        (d / n).chmod(0o755)
    (d / "meta.json").write_text(json.dumps(meta))
    (d / "secrets.json").write_text(json.dumps({k: _b64(v) for k, v in secrets.items()}))
    return dict(os.environ, PATH=f"{d}{os.pathsep}{os.environ['PATH']}", STUB_DIR=str(d))


VOICE_META = {
    "instance/attributes/c2o-voice-host": "voice.c2o.live",
    "instance/attributes/c2o-voice-turn-host": "voice-turn.c2o.live",
    "instance/attributes/c2o-voice-secret": "c2o-livekit-keys",
    "instance/attributes/c2o-acme-email": "franz@example.org",
    "project/project-id": "c2o-live-prod",
    "instance/network-interfaces/0/access-configs/0/external-ip": "203.0.113.10",
}


def _voice_bootstrap(tmp: Path, action: str = "refresh", meta=None, secrets=None):
    env = _stubs(tmp, VOICE_META if meta is None else meta,
                 {"c2o-livekit-keys": f"LIVEKIT_API_KEY={KEY}\nLIVEKIT_API_SECRET={SECRET}\n"}
                 if secrets is None else secrets)
    out = tmp / "voice"
    env["C2O_VOICE_DIR"] = str(out)
    r = subprocess.run(["bash", str(VOICE_BS), action], capture_output=True, text=True, env=env, timeout=60)
    return r, out


def test_voice_bootstrap_renders_livekit_caddy_and_compose(tmp_path):
    r, out = _voice_bootstrap(tmp_path)
    assert r.returncode == 0, r.stderr
    lk = out / "livekit.yaml"
    assert stat.S_IMODE(lk.stat().st_mode) == 0o600, "livekit.yaml holds the API secret"
    cfg = yaml.safe_load(lk.read_text())
    assert cfg["keys"] == {KEY: SECRET}
    assert cfg["bind_addresses"] == ["127.0.0.1"], "signalling only through Caddy"
    assert cfg["rtc"]["tcp_port"] == 7881
    assert (cfg["rtc"]["port_range_start"], cfg["rtc"]["port_range_end"]) == (50000, 60000)
    assert cfg["rtc"]["node_ip"] == "203.0.113.10"
    t = cfg["turn"]
    assert t["enabled"] and t["domain"] == "voice-turn.c2o.live" and t["udp_port"] == 3478
    assert t["external_tls"] is True and t["proxy_protocol"] is True and t["tls_port"] == 5349
    caddy = json.loads((out / "caddy.json").read_text())
    assert set(caddy["apps"]["tls"]["certificates"]["automate"]) == {"voice.c2o.live", "voice-turn.c2o.live"}
    issuers = caddy["apps"]["tls"]["automation"]["policies"][0]["issuers"]
    assert issuers[0]["email"] == "franz@example.org"
    srv = caddy["apps"]["layer4"]["servers"]["main"]
    assert srv["listen"] == [":443"]
    routes = {rt["match"][0]["tls"]["sni"][0]: rt["handle"] for rt in srv["routes"]}
    assert routes["voice-turn.c2o.live"][1]["upstreams"][0]["dial"] == ["127.0.0.1:5349"]
    assert routes["voice-turn.c2o.live"][1]["proxy_protocol"] == "v2"
    assert routes["voice.c2o.live"][1]["upstreams"][0]["dial"] == ["127.0.0.1:7880"]
    comp = yaml.safe_load((out / "compose.yaml").read_text())
    for svc in ("livekit", "caddy"):
        s = comp["services"][svc]
        assert s["network_mode"] == "host"
        assert re.search(r":v[\d.]+@sha256:[0-9a-f]{64}$", s["image"]), f"{svc} image not pinned: {s['image']}"
    docker = (tmp_path / "stubs" / "docker.log").read_text()
    assert "compose -f compose.yaml up -d" in docker
    assert SECRET not in r.stderr + r.stdout, "the secret must never be printed"


def test_voice_bootstrap_rejects_a_malformed_key_pair(tmp_path):
    r, out = _voice_bootstrap(tmp_path, secrets={"c2o-livekit-keys": "LIVEKIT_API_KEY=x\nLIVEKIT_API_SECRET=short\n"})
    assert r.returncode != 0
    assert not (out / "livekit.yaml").exists()


def test_voice_bootstrap_needs_the_external_ip(tmp_path):
    meta = dict(VOICE_META)
    del meta["instance/network-interfaces/0/access-configs/0/external-ip"]
    r, _ = _voice_bootstrap(tmp_path, meta=meta)
    assert r.returncode != 0 and "external IP" in r.stderr


def _free(port: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


@pytest.mark.skipif(not os.environ.get("LIVEKIT_SERVER_BIN"),
                    reason="set LIVEKIT_SERVER_BIN to a livekit-server binary to load the rendered config")
def test_rendered_livekit_yaml_is_loaded_by_the_real_server(tmp_path):
    if not (_free(7880) and _free(7881) and _free(5349)):
        pytest.skip("ports 7880/7881/5349 busy (a LiveKit dev server running?)")
    r, out = _voice_bootstrap(tmp_path)
    assert r.returncode == 0, r.stderr
    cfg = (out / "livekit.yaml").read_text().replace("203.0.113.10", "127.0.0.1")
    (out / "livekit.yaml").write_text(cfg)
    p = subprocess.Popen([os.environ["LIVEKIT_SERVER_BIN"], "--config", str(out / "livekit.yaml")],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        deadline, log = time.time() + 20, ""
        import urllib.request
        while time.time() < deadline:
            try:
                if urllib.request.urlopen("http://127.0.0.1:7880/", timeout=1).read() == b"OK":
                    break
            except OSError:
                time.sleep(0.3)
        else:
            p.terminate()
            log = p.communicate(timeout=10)[0]
            pytest.fail(f"livekit-server did not start with the rendered config:\n{log[-3000:]}")
    finally:
        p.terminate()
        try:
            log = p.communicate(timeout=10)[0]
        except subprocess.TimeoutExpired:
            p.kill()
            log = ""
    assert "turn" in log.lower() and "voice-turn.c2o.live" in log or "starting LiveKit server" in log


# ── the ground VM: voice.env ─────────────────────────────────────────────

GROUND_META = {
    "instance/attributes/c2o-role": "ground",
    "instance/attributes/c2o-domain": "c2o.live",
    "instance/attributes/c2o-ground-ip": "10.20.0.10",
    "instance/attributes/c2o-voice-secret": "c2o-livekit-keys",
    "instance/attributes/c2o-voice-host": "voice.c2o.live",
    "instance/attributes/c2o-voice-instructors": "admin@c2o.live prof@c2o.live",
    "project/project-id": "c2o-live-prod",
    "instance/network-interfaces/0/ip": "10.20.0.10",
}
LINK = "SMO_LINK_SESSION=s-0123456789abcdef\nSMO_LINK_SECRET=" + "ab" * 32 + "\n"


def _ground_refresh(tmp: Path, secrets: dict):
    app = tmp / "app"
    (app / "sim" / "docker").mkdir(parents=True)
    (app / "sim" / "docker" / "config-hash.sh").write_text("echo cafe\n")
    (app / "deploy" / "gcp" / "env").mkdir(parents=True)
    shutil.copy(GCP / "env" / "ground.env.example", app / "deploy" / "gcp" / "env" / "ground.env.example")
    env = _stubs(tmp, GROUND_META, secrets)
    env["C2O_APP_DIR"] = str(app)
    r = subprocess.run(["bash", str(VM_BS), "refresh"], capture_output=True, text=True, env=env, timeout=60)
    return r, app / "sim" / "docker" / "voice.env"


def test_ground_vm_writes_voice_env_from_the_secret(tmp_path):
    r, f = _ground_refresh(tmp_path, {"c2o-link-session": LINK,
                                      "c2o-livekit-keys": f"LIVEKIT_API_KEY={KEY}\nLIVEKIT_API_SECRET={SECRET}\n"})
    assert r.returncode == 0, r.stderr
    assert stat.S_IMODE(f.stat().st_mode) == 0o600
    kv = dict(ln.split("=", 1) for ln in f.read_text().splitlines() if "=" in ln and not ln.startswith("#"))
    assert kv["LIVEKIT_URL"] == "wss://voice.c2o.live"
    assert kv["LIVEKIT_API_KEY"] == KEY and kv["LIVEKIT_API_SECRET"] == SECRET
    assert kv["SMO_VOICE_REQUIRE_IAP"] == "1"
    assert kv["SMO_VOICE_INSTRUCTORS"].split() == ["admin@c2o.live", "prof@c2o.live"]
    assert SECRET not in r.stderr


def test_ground_vm_without_voice_keys_writes_an_empty_voice_env(tmp_path):
    r, f = _ground_refresh(tmp_path, {"c2o-link-session": LINK})
    assert r.returncode == 0, r.stderr
    assert f.exists() and f.read_text() == ""
    assert "voice loops off" in r.stderr


# ── setup / start / stop / teardown agree ────────────────────────────────

def test_firewall_opens_exactly_livekits_documented_ports():
    common = _sh(GCP / "common.sh")
    m = re.search(r'^VOICE_PORTS="([^"]+)"', common, re.M)
    assert m and set(m.group(1).split(",")) == LIVEKIT_PORTS
    setup = _sh(GCP / "setup.sh")
    assert 'fw "$FW_VOICE" "$VOICE_PORTS" "$TAG_VOICE" --source-ranges=0.0.0.0/0' in setup
    assert '"$TAG_GROUND,$TAG_SIM,$TAG_VOICE"' in setup, "IAP SSH must reach the voice VM"


def test_setup_creates_the_voice_vm_with_a_static_ip_and_prints_its_dns():
    setup = _sh(GCP / "setup.sh")
    assert 'gcloud compute addresses create "$ADDR_VOICE" --region="$REGION"' in setup
    create = setup[setup.index('gcloud compute instances create "$VM_VOICE"'):]
    create = create[:create.index("--labels=app=c2o,role=voice")]
    for flag in ('--address="$voice_ip"', '--machine-type="$VOICE_MACHINE_TYPE"', '--tags="$TAG_VOICE"',
                 'startup-script="$GCP_DIR/voice-bootstrap.sh"', '--service-account="$SA_VOICE_EMAIL"'):
        assert flag in create
    assert "--no-address" not in create
    # the two A records, to the voice IP (not the LB)
    assert '"voice" "$voice_ip" "voice-turn" "$voice_ip"' in setup
    common = _sh(GCP / "common.sh")
    assert 'HOST_VOICE="voice.$DOMAIN"' in common and 'HOST_VOICE_TURN="voice-turn.$DOMAIN"' in common


def test_setup_generates_the_key_pair_without_exposing_it():
    setup = _sh(GCP / "setup.sh")
    block = setup[setup.index('log "Secret $SECRET_VOICE'):setup.index("# ── 4. VMs")]
    assert "| gcloud secrets versions add \"$SECRET_VOICE\" --data-file=-" in block
    assert "token_urlsafe(32)" in block       # >= 32 chars: LiveKit's minimum
    for sa in ('"$SA_VOICE_EMAIL"', '"$SA_GROUND_EMAIL"'):
        assert sa in block
    assert "secretmanager.secretAccessor" in block
    # the ground VM learns where the voice server is and who is instructor
    assert "c2o-voice-secret=$SECRET_VOICE,c2o-voice-host=$HOST_VOICE,c2o-voice-instructors=$voice_instr" in setup


def test_start_stop_teardown_cover_the_voice_vm():
    assert 'start_vm "$VM_VOICE"' in _sh(GCP / "start.sh")
    assert 'stop_vm "$VM_VOICE"' in _sh(GCP / "stop.sh")
    td = _sh(GCP / "teardown.sh")
    for name in ('"$VM_VOICE"', '"$ADDR_VOICE"', '"$FW_VOICE"', '"$SECRET_VOICE"', '"$SA_VOICE_EMAIL"'):
        assert name in td, f"teardown.sh leaves {name} behind"


def test_readme_documents_voice_loops():
    rd = _sh(GCP / "README.md")
    assert "\n## Voice loops\n" in rd
    for needle in ("voice-turn", "c2o-voice-ip", "VOICE_INSTRUCTORS", "--profile voice", "SMO_VOICE=dev",
                   "UDP 50000-60000", "TCP 7881", "UDP 3478", "recordings", "voice-bootstrap.sh"):
        assert needle in rd, needle


# ── c2o: status, costs and schedule with the voice VM ────────────────────

def test_status_shows_the_voice_vm_and_its_cost(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    base = Env(tmp_path / "a").run("status")
    e = Env(tmp_path / "b", vms={"c2o-ground-vm": "RUNNING", "c2o-sim-vm": "RUNNING",
                                 "c2o-voice-vm": "RUNNING"})
    r = e.run("status")
    assert r.returncode == 0, _out(r)
    assert re.search(r"c2o-voice-vm\s+RUNNING", r.stdout)
    assert "Voice loops server" in r.stdout and "https://voice.c2o.live" in r.stdout
    assert "Voice VM static IP (in use)" in r.stdout
    t0 = float(re.search(r"Total\s+CAD\s+([\d.]+)", base.stdout).group(1))
    t1 = float(re.search(r"Total\s+CAD\s+([\d.]+)", r.stdout).group(1))
    want = (0.0184 * 24 + 0.005 * 24 + 10 * 0.11 / 30.4) * 1.39      # VM + IP + 10 GB disk
    assert abs((t1 - t0) - want) < 0.03, (t0, t1, want)


def test_status_voice_vm_stopped_costs_its_reserved_ip(tmp_path):
    e = Env(tmp_path, vms={"c2o-ground-vm": "TERMINATED", "c2o-sim-vm": "TERMINATED",
                           "c2o-voice-vm": "TERMINATED"}, lb=False, snapshots=[])
    r = e.run("status")
    assert r.returncode == 0, _out(r)
    assert "DOWN (the voice VM is TERMINATED" in r.stdout
    assert "reserved, VM stopped" in r.stdout
    assert e.gcalls("compute", "ssh") == []


def test_schedule_takes_the_voice_vm_along(tmp_path):
    e = Env(tmp_path, vms={"c2o-ground-vm": "RUNNING", "c2o-sim-vm": "RUNNING", "c2o-voice-vm": "RUNNING"})
    r = e.run("schedule", "set", "Mon-Fri 08:00-18:00")
    assert r.returncode == 0, _out(r)
    attached = {a[3] for a in e.gcalls("compute", "instances", "add-resource-policies")}
    assert attached == {"c2o-ground-vm", "c2o-sim-vm", "c2o-voice-vm"}


def test_down_and_up_include_the_voice_vm(tmp_path):
    e = Env(tmp_path, vms={"c2o-ground-vm": "RUNNING", "c2o-sim-vm": "RUNNING", "c2o-voice-vm": "RUNNING"})
    r = e.run("down")
    assert r.returncode == 0, _out(r)
    assert "c2o-voice-vm" in {a[3] for a in e.gcalls("compute", "instances", "stop")}
    (tmp_path / "up").mkdir()
    e2 = Env(tmp_path / "up", vms={"c2o-ground-vm": "TERMINATED", "c2o-sim-vm": "TERMINATED",
                                    "c2o-voice-vm": "TERMINATED"})
    r = e2.run("up", "--sim=laptop", "--no-wait")
    assert r.returncode == 0, _out(r)
    assert "c2o-voice-vm" in {a[3] for a in e2.gcalls("compute", "instances", "start")}
    assert "https://ops.c2o.live/voice" in r.stdout


# ── laptop compose + the image ───────────────────────────────────────────

def test_compose_livekit_dev_service_is_loopback_and_matches_the_mcs_dev_key():
    comp = yaml.safe_load((SIM / "docker" / "compose.yaml").read_text())
    lk = comp["services"]["livekit"]
    assert lk["profiles"] == ["voice"]
    assert all(p.startswith("127.0.0.1:") for p in lk["ports"]), lk["ports"]
    assert {"127.0.0.1:7880:7880", "127.0.0.1:7881:7881", "127.0.0.1:7882:7882/udp"} == set(lk["ports"])
    cmd = lk["command"]
    assert "--dev" in cmd and cmd[cmd.index("--node-ip") + 1] == "127.0.0.1"
    from smo_mcs import voice
    assert cmd[cmd.index("--keys") + 1] == f"{voice.DEV_API_KEY}: {voice.DEV_API_SECRET}"
    assert len(voice.DEV_API_SECRET) >= 32
    # the same pinned server image as the cloud VM
    vb = _sh(VOICE_BS)
    assert f'LIVEKIT_IMAGE="{lk["image"]}"' in vb
    mcs = comp["services"]["mcs"]
    assert {"path": "./voice.env", "required": False} in mcs["env_file"]
    assert {"path": "./ground.env", "required": False} in mcs["env_file"]


def test_image_installs_the_pinned_token_library():
    assert '-e "packages/smo-mcs[voice]"' in (SIM / "docker" / "Dockerfile").read_text()
    py = (SIM / "packages" / "smo-mcs" / "pyproject.toml").read_text()
    assert re.search(r'voice = \["livekit-api==\d+\.\d+\.\d+"\]', py)


@pytest.mark.skipif(shutil.which("shellcheck") is None, reason="shellcheck not installed")
def test_deploy_scripts_are_shellcheck_clean():
    scripts = ["c2o", "common.sh", "setup.sh", "start.sh", "stop.sh", "teardown.sh",
               "vm-bootstrap.sh", "voice-bootstrap.sh", "rotate-link-secret.sh", "switch.sh"]
    r = subprocess.run(["shellcheck", "-x", "-S", "warning", *scripts], cwd=GCP,
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr
