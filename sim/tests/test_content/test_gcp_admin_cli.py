"""deploy/gcp/c2o, the one admin command for the Google Cloud deployment.

Runs the real script with stub ``gcloud``, ``curl`` and ``ssh`` first on
PATH. The stubs log every call (argv as JSON lines) and answer with canned
JSON from a small state file, so nothing ever reaches Google. Checked:
status and its cost line, schedule validation and the resource-policy calls,
data clean (confirmation, the vm-bootstrap action and what it is sent),
users add/remove/import (dry run and apply), bare-name expansion, no password
or token on any command line, the missing-sign-in message, and the
``vm-bootstrap.sh clean`` action itself against a stub docker.

macOS ships bash 3.2: if a bash 3.2 binary is available (``$BASH32``, or
``/bin/bash`` on a Mac) the main paths also run under it; otherwise, and
always, the script is checked for constructs bash 3.2 does not have.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
GCP = REPO / "deploy" / "gcp"
C2O = GCP / "c2o"
BOOTSTRAP = GCP / "vm-bootstrap.sh"

pytestmark = pytest.mark.skipif(shutil.which("bash") is None or shutil.which("python3") is None,
                                reason="needs bash and python3")

TOKEN = "ya29.STUB-SECRET-TOKEN"

# ── stubs ────────────────────────────────────────────────────────────────

GCLOUD_STUB = r'''#!/usr/bin/env python3
import json, os, sys
d = os.environ["STUB_DIR"]
argv = sys.argv[1:]
st = json.load(open(os.path.join(d, "state.json")))
entry = {"argv": argv}
fmt = next((a.split("=", 1)[1] for a in argv if a.startswith("--format=")), "")
def opt(name):
    return next((a.split("=", 1)[1] for a in argv if a.startswith(name + "=")), None)
def save():
    json.dump(st, open(os.path.join(d, "state.json"), "w"))
def out(s="", rc=0):
    with open(os.path.join(d, "gcloud.log"), "a") as fh:
        fh.write(json.dumps(entry) + "\n")
    if s:
        sys.stdout.write(s if s.endswith("\n") else s + "\n")
    sys.exit(rc)
pos = [a for a in argv if not a.startswith("-")]
cmd = " ".join(pos[:3])
if pos[:3] == ["config", "get-value", "account"]:
    out("admin@c2o.live")
if pos[:2] == ["projects", "describe"]:
    out("123456789012" if "projectNumber" in fmt else pos[2])
if pos[:3] == ["auth", "application-default", "print-access-token"]:
    if not st.get("adc", True):
        sys.stderr.write("ERROR: (gcloud.auth.application-default.print-access-token) Could not automatically determine credentials.\n")
        out("", 1)
    out(os.environ["STUB_TOKEN"])
if pos[:3] == ["compute", "instances", "describe"]:
    vm = pos[3]
    if vm not in st["vms"]:
        out("", 1)
    if "resourcePolicies" in fmt:
        out(";".join(st.get("policies_on", {}).get(vm, [])))
    out(st["vms"][vm])
if pos[:3] == ["compute", "forwarding-rules", "describe"]:
    out(pos[3] if st.get("lb", True) else "", 0 if st.get("lb", True) else 1)
if pos[:3] == ["compute", "backend-services", "get-health"]:
    out("HEALTHY")
if pos[:3] == ["compute", "ssl-certificates", "list"]:
    out("c2o-cert\tACTIVE\nc2o-cert-tools-0a1b2c\tPROVISIONING")
if pos[:3] == ["compute", "resource-policies", "describe"]:
    if not st.get("policy"):
        out("", 1)
    if fmt == "value(name)":
        out(pos[3])
    if "description" in fmt:
        out(st["policy"]["description"])
    out("%s\t%s\tAmerica/Toronto" % (st["policy"]["start"], st["policy"]["stop"]))
if pos[:4] == ["compute", "resource-policies", "create", "instance-schedule"]:
    st["policy"] = {"description": opt("--description"), "start": opt("--vm-start-schedule"),
                    "stop": opt("--vm-stop-schedule")}
    save(); out()
if pos[:3] == ["compute", "resource-policies", "delete"]:
    st["policy"] = None; save(); out()
if pos[:3] == ["compute", "instances", "add-resource-policies"]:
    st.setdefault("policies_on", {})[pos[3]] = [opt("--resource-policies")]; save(); out()
if pos[:3] == ["compute", "instances", "remove-resource-policies"]:
    st.setdefault("policies_on", {})[pos[3]] = []; save(); out()
if pos[:3] == ["compute", "snapshots", "list"]:
    snaps = st.get("snapshots", [])
    if fmt == "value(storageBytes)":
        out("\n".join(str(s[2]) for s in snaps))
    if "storageBytes" in fmt:
        out("\n".join("%s\t%s\t%s\t%s" % (s[0], s[1], s[2], s[3]) for s in snaps))
    out("\n".join("%s\t%s\t%s" % (s[0], s[1], s[3]) for s in snaps))
if pos[:2] == ["compute", "ssh"]:
    command = opt("--command") or ""
    if "link-status" in command:
        out('{"state": "%s", "session": "s-1"}' % st.get("link", "UP"))
    data = sys.stdin.read()
    n = len([f for f in os.listdir(d) if f.startswith("ssh-stdin-")])
    open(os.path.join(d, "ssh-stdin-%d" % n), "w").write(data)
    entry["stdin_file"] = "ssh-stdin-%d" % n
    if " sizes" in command:
        out("role ground\nvol ground-archive 2097152\nvol ground-dumps 51200\n"
            "vol ground-workspace 300\nsub ground-workspace/logbook 120 7\n"
            "vol spacecdf-data 4096\ndisk 9437184 30832548")
    out("c2o-bootstrap: cleaned (stub)")
out()
'''

CURL_STUB = r'''#!/usr/bin/env python3
import json, os, re, sys, urllib.parse
d = os.environ["STUB_DIR"]
argv = sys.argv[1:]
st = json.load(open(os.path.join(d, "state.json")))
method, out, cfg, body, url = "GET", None, None, None, None
i = 0
while i < len(argv):
    a = argv[i]
    if a == "-X": method = argv[i + 1]; i += 1
    elif a == "-o": out = argv[i + 1]; i += 1
    elif a == "-K": cfg = argv[i + 1]; i += 1
    elif a in ("-w", "-H"): i += 1
    elif a == "--data-binary": body = argv[i + 1]; i += 1
    elif not a.startswith("-"): url = a
    i += 1
cfg_text = open(cfg).read() if cfg else ""
cfg_mode = oct(os.stat(cfg).st_mode & 0o777) if cfg else None
payload = json.load(open(body[1:])) if body else None
with open(os.path.join(d, "curl.log"), "a") as fh:
    fh.write(json.dumps({"argv": argv, "method": method, "url": url, "body": payload,
                         "auth": os.environ["STUB_TOKEN"] in cfg_text, "cfg_mode": cfg_mode}) + "\n")
p = urllib.parse.urlparse(url)
path = urllib.parse.unquote(p.path).split("/admin/directory/v1/", 1)[1]
q = urllib.parse.parse_qs(p.query)
users = st.setdefault("users", [])
groups = st.setdefault("groups", {})
def reply(code, obj=None):
    st["users"] = users; st["groups"] = groups
    json.dump(st, open(os.path.join(d, "state.json"), "w"))
    if out:
        open(out, "w").write(json.dumps(obj) if obj is not None else "")
    sys.stdout.write(str(code)); sys.exit(0)
if st.get("force_code"):
    reply(st["force_code"], {"error": {"message": "forced"}})
m = re.fullmatch(r"groups/([^/]+)/members(?:/(.+))?", path)
if m:
    g, who = m.group(1), m.group(2)
    mem = groups.setdefault(g, [])
    if method == "GET": reply(200, {"members": [{"email": e} for e in mem]})
    if method == "POST":
        if payload["email"] in mem: reply(409, {"error": {"message": "Member already exists."}})
        mem.append(payload["email"]); reply(200, {"email": payload["email"]})
    if method == "DELETE":
        if who not in mem: reply(404, {"error": {"message": "Resource Not Found"}})
        mem.remove(who); reply(204)
if path == "users" and method == "GET":
    reply(200, {"users": users})
if path == "users" and method == "POST":
    if any(u["primaryEmail"] == payload["primaryEmail"] for u in users):
        reply(409, {"error": {"message": "Entity already exists."}})
    users.append({"primaryEmail": payload["primaryEmail"],
                  "name": {"fullName": payload["name"]["givenName"] + " " + payload["name"]["familyName"]},
                  "isEnrolledIn2Sv": False, "suspended": False, "lastLoginTime": "1970-01-01T00:00:00.000Z"})
    reply(200, users[-1])
m = re.fullmatch(r"users/([^/]+)", path)
if m:
    e = m.group(1)
    u = [x for x in users if x["primaryEmail"] == e]
    if not u: reply(404, {"error": {"message": "Resource Not Found: userKey"}})
    if method == "GET": reply(200, u[0])
    if method == "DELETE": users.remove(u[0]); reply(204)
    if method in ("PATCH", "PUT"): u[0].update({k: v for k, v in payload.items() if k == "suspended"}); reply(200, u[0])
reply(400, {"error": {"message": "stub: unhandled %s %s" % (method, path)}})
'''

SSH_STUB = """#!/bin/sh
echo "ssh stub: c2o must reach the VMs through gcloud compute ssh only" >&2
echo "$*" >> "$STUB_DIR/ssh.log"
exit 99
"""

BASE_STATE = {
    "vms": {"c2o-ground-vm": "RUNNING", "c2o-sim-vm": "RUNNING"},
    "lb": True,
    "policy": None,
    "policies_on": {},
    "snapshots": [
        ["c2o-ground-vm-20261101-120000", "c2o-ground-vm", 2000000000, "2026-11-01T12:00:00.000-04:00"],
    ],
    "users": [
        {"primaryEmail": "admin@c2o.live", "name": {"fullName": "C2O Admin"}, "isAdmin": True,
         "isEnrolledIn2Sv": True, "suspended": False, "lastLoginTime": "2026-11-01T14:00:00.000Z"},
        {"primaryEmail": "jdoe@c2o.live", "name": {"fullName": "Jane Doe"},
         "isEnrolledIn2Sv": False, "suspended": False, "lastLoginTime": "1970-01-01T00:00:00.000Z"},
        {"primaryEmail": "prof@c2o.live", "name": {"fullName": "Pat Prof"},
         "isEnrolledIn2Sv": True, "suspended": False, "lastLoginTime": "2026-10-30T09:15:00.000Z"},
    ],
    "groups": {
        "c2o-students@c2o.live": ["jdoe@c2o.live"],
        "c2o-instructors@c2o.live": ["prof@c2o.live"],
    },
}


def _bash32() -> str | None:
    cand = os.environ.get("BASH32")
    if cand and Path(cand).exists():
        return cand
    for b in ("/bin/bash",):
        try:
            v = subprocess.run([b, "-c", "echo ${BASH_VERSINFO[0]}"], capture_output=True, text=True).stdout
        except OSError:
            continue
        if v.strip() == "3":
            return b
    return None


BASH32 = _bash32()


class Env:
    def __init__(self, tmp: Path, bash: str = "bash", **state):
        self.dir = tmp / "stubs"
        self.dir.mkdir()
        for name, body in (("gcloud", GCLOUD_STUB), ("curl", CURL_STUB), ("ssh", SSH_STUB)):
            p = self.dir / name
            p.write_text(body)
            p.chmod(0o755)
        st = json.loads(json.dumps(BASE_STATE))
        st.update(state)
        self.state_file.write_text(json.dumps(st))
        envtxt = (GCP / "c2o.env.example").read_text()
        self.envfile = tmp / "c2o.env"
        self.envfile.write_text(envtxt)
        self.tmp = tmp
        self.bash = bash
        self.cwd = tmp / "work"
        self.cwd.mkdir()

    @property
    def state_file(self) -> Path:
        return self.dir / "state.json"

    def state(self) -> dict:
        return json.loads(self.state_file.read_text())

    def set_env(self, line: str) -> None:
        self.envfile.write_text(self.envfile.read_text() + "\n" + line + "\n")

    def run(self, *args: str, stdin: str = "") -> subprocess.CompletedProcess:
        env = dict(os.environ)
        env.update(PATH=f"{self.dir}{os.pathsep}{env['PATH']}", STUB_DIR=str(self.dir),
                   STUB_TOKEN=TOKEN, C2O_ENV=str(self.envfile), TMPDIR=str(self.tmp))
        return subprocess.run([self.bash, str(C2O), *args], input=stdin, capture_output=True,
                              text=True, env=env, cwd=self.cwd, timeout=60)

    def log(self, name: str) -> list[dict]:
        f = self.dir / name
        if not f.exists():
            return []
        return [json.loads(ln) for ln in f.read_text().splitlines() if ln.strip()]

    def gcloud(self) -> list[list[str]]:
        return [e["argv"] for e in self.log("gcloud.log")]

    def gcalls(self, *prefix: str) -> list[list[str]]:
        return [a for a in self.gcloud() if [x for x in a if not x.startswith("-")][:len(prefix)] == list(prefix)]


@pytest.fixture
def env(tmp_path):
    return Env(tmp_path)


def _out(r: subprocess.CompletedProcess) -> str:
    return r.stdout + r.stderr


# ── help and portability ─────────────────────────────────────────────────

def test_help_needs_no_settings(tmp_path):
    e = Env(tmp_path)
    e.envfile.unlink()                       # help must work before c2o.env exists
    r = e.run("help")
    assert r.returncode == 0, _out(r)
    for head in ("Everyday", "Users", "Data", "Setup"):
        assert head in r.stdout
    assert "alias c2o='bash ~/C2O/deploy/gcp/c2o'" in r.stdout
    assert len(r.stdout.splitlines()) <= 34, "c2o help must fit on one screen"
    for sub in ("status", "up", "down", "schedule", "data", "users"):
        r = e.run(sub, "--help")
        assert r.returncode == 0 and "c2o " + sub in r.stdout, sub
    assert e.gcloud() == []


def test_unknown_command(env):
    r = env.run("frobnicate")
    assert r.returncode == 2 and "unknown command" in r.stderr


FORBIDDEN_BASH4 = [
    (r"declare\s+-A|local\s+-A|typeset\s+-A", "associative arrays"),
    (r"\bmapfile\b|\breadarray\b", "mapfile/readarray"),
    (r"\$\{[A-Za-z_][A-Za-z0-9_]*(,,|\^\^|,|\^)\}", "case-changing expansion"),
    (r"\bsed\s+(-[a-zA-Z]*\s+)*-i\b", "sed -i"),
    (r"\bdate\s+(-d|--date)\b", "GNU date -d"),
    (r"\bstat\s+(-c|--format)\b", "GNU stat -c"),
    (r"base64\s+-w", "base64 -w"),
    (r"readlink\s+-f", "readlink -f"),
    (r"\|&", "|& pipes"),
    (r";;&", ";;& case fall-through"),
    (r"\bcoproc\b", "coproc"),
    (r"local\s+-n|declare\s+-n", "namerefs"),
    (r"\$\{[A-Za-z_]+\[-1\]\}", "negative array index"),
    (r"\bpaste\s+-s[a-z]*\s*(\S+)?\s*\)", "paste -s without the - operand (macOS)"),
    (r"\{[A-Za-z_]+\}[<>]", "automatic fd allocation"),
    (r"\bshopt\s+-s\s+(globstar|lastpipe|inherit_errexit)", "bash 4 shopt"),
    # bash 3.2 bug: a failing `command X || fallback` still exits a set -e script.
    (r"\bcommand\s+(?!-v\b)[A-Za-z_][\w-]*[^\n]*\|\|", "`command X ||` (exits under bash 3.2 set -e)"),
]


@pytest.mark.parametrize("script", ["c2o", "common.sh", "start.sh", "stop.sh", "setup.sh",
                                    "teardown.sh", "rotate-link-secret.sh", "switch.sh",
                                    "voice-bootstrap.sh"])
def test_no_bash4_only_constructs(script):
    """macOS bash 3.2 (Franz's MacBook) runs c2o and the scripts it calls."""
    src = (GCP / script).read_text()
    code = "\n".join(ln for ln in src.splitlines() if not ln.lstrip().startswith("#"))
    # Python heredocs are not shell.
    code = re.sub(r"<<'PY'\n.*?\nPY\n", "\n", code, flags=re.S)
    for pat, what in FORBIDDEN_BASH4:
        m = re.search(pat, code)
        assert m is None, f"{script}: {what}: {m.group(0)!r}"


def test_empty_arrays_are_guarded_for_bash32():
    """`"${a[@]}"` on an empty array is an unbound-variable error under set -u in bash < 4.4."""
    src = C2O.read_text()
    for name in ("args", "pass"):
        for m in re.finditer(r'"\$\{' + name + r'\[@\]\}"', src):
            before = src[max(0, m.start() - 20):m.start()]
            assert "+" in before, f"unguarded \"${{{name}[@]}}\" near {src[m.start()-40:m.end()]!r}"


@pytest.mark.skipif(BASH32 is None, reason="no bash 3.2 binary (set $BASH32 to one)")
def test_runs_under_bash32(tmp_path):
    e = Env(tmp_path, bash=BASH32)
    assert subprocess.run([BASH32, "-n", str(C2O)]).returncode == 0
    r = e.run("help")
    assert r.returncode == 0, _out(r)
    r = e.run("status")
    assert r.returncode == 0, _out(r)
    assert "Total" in r.stdout
    r = e.run("schedule", "set", "Mon-Wed,Fri 08:45-12:15")
    assert r.returncode == 0, _out(r)
    assert e.state()["policy"]["start"] == "45 8 * * 1-3,5"
    r = e.run("schedule", "set", "Fri-Mon 08:00-09:00")
    assert r.returncode == 2
    r = e.run("users", "add", "newbie", "--name", "New Bie")
    assert r.returncode == 0, _out(r)
    r = e.run("data", "clean", "--dumps", stdin="y\n")
    assert r.returncode == 0, _out(r)
    r = e.run("down", "--all", stdin="n\n")
    assert r.returncode != 0
    r = e.run("down", "--all", "--yes")
    assert r.returncode == 0, _out(r)
    r = e.run("up", "--sim=laptop", "--no-wait")
    assert r.returncode == 0, _out(r)
    r = e.run("data", "list")
    assert r.returncode == 0 and "MCS telemetry archive" in r.stdout, _out(r)
    (e.cwd / "c.csv").write_text("email,first,last,role\nzed,Zed,Zulu,instructor\n")
    r = e.run("users", "import", "c.csv", "--apply", "--yes")
    assert r.returncode == 0 and "created zed@c2o.live" in r.stdout, _out(r)
    r = e.run("users", "list")
    assert r.returncode == 0 and "zed@c2o.live" in r.stdout, _out(r)
    r = e.run("schedule", "clear", "--yes")
    assert r.returncode == 0, _out(r)


# ── status ───────────────────────────────────────────────────────────────

def test_status_running(env):
    r = env.run("status")
    assert r.returncode == 0, _out(r)
    o = r.stdout
    assert re.search(r"c2o-ground-vm\s+RUNNING", o) and re.search(r"c2o-sim-vm\s+RUNNING", o)
    assert re.search(r"c2o-fr-https\s+present", o)
    for screen in ("welcome", "ops", "plan", "sim", "link", "tm", "design", "scenarios", "adcs"):
        assert re.search(rf"\n\s+{screen}\s+HEALTHY", o), screen
    assert "c2o-cert-tools-0a1b2c" in o and "PROVISIONING" in o
    assert "UP: a simulator is connected" in o
    assert "Automatic schedule" in o and "none" in o
    # 2 VMs (0.0738 + NAT 0.0014)/h + disks + LB + Armor + NAT IP + 2 GB of snapshots,
    # x 1.39: about CAD 6.64 a day.
    total = re.search(r"Total\s+CAD\s+([\d.]+)", o)
    assert total and 6.4 < float(total.group(1)) < 6.9, o
    assert "c2o down" in o and "saves CAD" in o


def test_status_everything_off(tmp_path):
    e = Env(tmp_path, vms={"c2o-ground-vm": "TERMINATED", "c2o-sim-vm": "TERMINATED"}, lb=False, snapshots=[])
    r = e.run("status")
    assert r.returncode == 0, _out(r)
    o = r.stdout
    assert "absent (site offline)" in o
    assert "DOWN (the ground VM is TERMINATED)" in o
    total = float(re.search(r"Total\s+CAD\s+([\d.]+)", o).group(1))
    assert 1.0 < total < 1.3, o       # disks + idle IP + Armor + NAT IP
    assert "floor" in o
    assert e.gcalls("compute", "ssh") == []          # no SSH to a stopped VM
    assert e.gcalls("compute", "backend-services", "get-health") == []


# ── up / down ────────────────────────────────────────────────────────────

def test_down_all_explains_and_asks(env):
    r = env.run("down", "--all", stdin="n\n")
    assert r.returncode != 0
    assert "unreachable" in r.stdout and "Not confirmed" in r.stderr
    assert env.gcalls("compute", "forwarding-rules", "delete") == []
    r = env.run("down", "--all", "--yes")
    assert r.returncode == 0, _out(r)
    deleted = env.gcalls("compute", "forwarding-rules", "delete")
    assert {a[3] for a in deleted} == {"c2o-fr-https", "c2o-fr-http"}
    assert env.gcalls("compute", "instances", "stop")


def test_up_hands_over_to_start_sh(env):
    r = env.run("up", "--sim=laptop", "--no-wait")
    assert r.returncode == 0, _out(r)
    assert any(a[3] == "c2o-ground-vm" for a in env.gcalls("compute", "instances", "start")) or \
        "already running" in r.stdout
    assert any(a[3] == "c2o-sim-vm" for a in env.gcalls("compute", "instances", "stop"))


# ── schedule ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("spec,msg", [
    ("Mon-Fri", "time window"),
    ("Mon-Fri 8-18", "time window"),
    ("Mon-Fri 18:00-08:00", "later the same day"),
    ("Mon-Fri 08:00-08:10", "15 minutes"),
    ("Mon-Fri 25:00-26:00", "not a time of day"),
    ("Fri-Mon 08:00-18:00", "backwards"),
    ("Mon-Funday 08:00-18:00", "unknown day"),
    ("Mon,,Tue 08:00-18:00", "empty day"),
])
def test_schedule_rejects_bad_input(env, spec, msg):
    r = env.run("schedule", "set", spec)
    assert r.returncode == 2, _out(r)
    assert msg in r.stderr and "Example" in r.stderr
    assert env.gcalls("compute", "resource-policies") == []


@pytest.mark.parametrize("spec,start,stop,text", [
    ("Mon-Fri 08:00-18:00", "0 8 * * 1-5", "0 18 * * 1-5", "Mon-Fri 08:00-18:00"),
    ("mon,wed,fri 13:00-17:30", "0 13 * * 1,3,5", "30 17 * * 1,3,5", "Mon,Wed,Fri 13:00-17:30"),
    ("Mon-Tue,Thu-Fri 8:45-12:15", "45 8 * * 1-2,4-5", "15 12 * * 1-2,4-5", "Mon-Tue,Thu-Fri 08:45-12:15"),
    ("Sat-Sun 10:00-14:00", "0 10 * * 0,6", "0 14 * * 0,6", "Sat-Sun 10:00-14:00"),
    ("daily 07:30-22:00", "30 7 * * *", "0 22 * * *", "Mon-Sun 07:30-22:00"),
    ("weekdays 09:00-17:00", "0 9 * * 1-5", "0 17 * * 1-5", "Mon-Fri 09:00-17:00"),
])
def test_schedule_set_creates_policy(env, spec, start, stop, text):
    r = env.run("schedule", "set", spec)
    assert r.returncode == 0, _out(r)
    create = env.gcalls("compute", "resource-policies", "create", "instance-schedule")
    assert len(create) == 1
    a = create[0]
    assert "c2o-schedule" in a and "--region=northamerica-northeast2" in a
    assert f"--vm-start-schedule={start}" in a and f"--vm-stop-schedule={stop}" in a
    assert "--timezone=America/Toronto" in a
    assert any(x.startswith("--description=") and text in x for x in a)
    attached = {c[3] for c in env.gcalls("compute", "instances", "add-resource-policies")}
    assert attached == {"c2o-ground-vm", "c2o-sim-vm"}          # SIM_MODE=cloud
    iam = env.gcalls("projects", "add-iam-policy-binding")
    assert any("--member=serviceAccount:service-123456789012@compute-system.iam.gserviceaccount.com" in c
               and "--role=roles/compute.instanceAdmin.v1" in c for c in iam)
    assert "load balancer is still billed" in r.stdout


def test_schedule_replace_show_clear(env):
    assert env.run("schedule", "set", "Mon-Fri 08:00-18:00").returncode == 0
    r = env.run("schedule", "show")
    assert "Mon-Fri 08:00-18:00" in r.stdout and "c2o-ground-vm" in r.stdout and "0 8 * * 1-5" in r.stdout
    r = env.run("schedule", "set", "Tue 09:00-12:00")
    assert r.returncode == 0, _out(r)
    names = [" ".join(a[:3]) for a in env.gcloud()]
    # The old policy is detached from both VMs and deleted before the new one is created.
    i_del = names.index("compute resource-policies delete")
    i_new = max(i for i, n in enumerate(names) if n == "compute resource-policies create")
    assert i_del < i_new
    assert len(env.gcalls("compute", "instances", "remove-resource-policies")) == 2
    assert env.state()["policy"]["start"] == "0 9 * * 2"
    r = env.run("schedule", "clear", stdin="n\n")
    assert r.returncode != 0 and env.state()["policy"]
    r = env.run("schedule", "clear", "--yes")
    assert r.returncode == 0, _out(r)
    assert env.state()["policy"] is None
    assert env.state()["policies_on"] == {"c2o-ground-vm": [], "c2o-sim-vm": []}


def test_schedule_laptop_mode_ground_only(env):
    env.set_env("SIM_MODE=laptop")
    r = env.run("schedule", "set", "Mon-Fri 08:00-18:00")
    assert r.returncode == 0, _out(r)
    assert {c[3] for c in env.gcalls("compute", "instances", "add-resource-policies")} == {"c2o-ground-vm"}


def test_schedule_warns_when_lb_is_down(tmp_path):
    e = Env(tmp_path, lb=False)
    r = e.run("schedule", "set", "Mon-Fri 08:00-18:00")
    assert r.returncode == 0 and "site stays offline" in r.stderr


# ── data ─────────────────────────────────────────────────────────────────

def _ssh_cleans(env):
    out = []
    for e in env.log("gcloud.log"):
        a = e["argv"]
        cmd = next((x for x in a if x.startswith("--command=")), "")
        if a[:2] == ["compute", "ssh"] and " clean " in cmd:
            stdin = (env.dir / e["stdin_file"]).read_text()
            out.append((a[2], re.search(r"sudo bash \"\$t\" (clean[^;]*);", cmd).group(1), stdin))
    return out


def test_data_clean_asks_and_does_nothing_without_yes(env):
    r = env.run("data", "clean", "--all", stdin="n\n")
    assert r.returncode != 0
    assert "MCS telemetry archive" in r.stdout and "Kept: saved scenarios" in r.stdout
    assert _ssh_cleans(env) == []


def test_data_clean_all_runs_bootstrap_clean(env):
    r = env.run("data", "clean", "--all", stdin="y\n")
    assert r.returncode == 0, _out(r)
    calls = _ssh_cleans(env)
    assert [(vm, c) for vm, c, _ in calls] == [
        ("c2o-ground-vm", "clean telemetry dumps reports"),
        ("c2o-sim-vm", "clean dumps"),
    ]
    # The VM runs the local vm-bootstrap.sh (sent over stdin), not its own possibly older copy.
    assert all(stdin == BOOTSTRAP.read_text() for _, _, stdin in calls)
    assert all("designs" not in c for _, c, _ in calls)
    assert env.gcalls("compute", "disks", "snapshot") == []


def test_data_clean_snapshot_first(env):
    r = env.run("data", "clean", "--telemetry", "--snapshot", "--yes")
    assert r.returncode == 0, _out(r)
    names = [" ".join(a[:3]) for a in env.gcloud()]
    snap = names.index("compute disks snapshot")
    ssh_clean = max(i for i, e in enumerate(env.log("gcloud.log"))
                    if e["argv"][:2] == ["compute", "ssh"] and " clean " in " ".join(e["argv"]))
    assert snap < ssh_clean
    s = env.gcalls("compute", "disks", "snapshot")[0]
    assert s[3] == "c2o-ground-vm" and "--labels=app=c2o" in s
    assert [c for _, c, _ in _ssh_cleans(env)] == ["clean telemetry"]     # telemetry: ground only


def test_data_clean_designs_needs_typed_confirmation(env):
    r = env.run("data", "clean", "--designs", "--yes", stdin="yes\n")
    assert r.returncode != 0 and _ssh_cleans(env) == []
    r = env.run("data", "clean", "--designs", "--yes", stdin="delete-designs\n")
    assert r.returncode == 0, _out(r)
    assert [c for _, c, _ in _ssh_cleans(env)] == ["clean designs"]


def test_data_clean_logbooks_on_both_vms_not_in_all(env):
    """Logbooks (LOGBOOK_SPEC §7): their own switch, never part of --all."""
    r = env.run("data", "clean", "--logbooks", stdin="y\n")
    assert r.returncode == 0, _out(r)
    assert "participant logbook" in r.stdout
    assert [(vm, c) for vm, c, _ in _ssh_cleans(env)] == [
        ("c2o-ground-vm", "clean logbooks"), ("c2o-sim-vm", "clean logbooks")]


def test_data_clean_dumps_and_logbooks_sim_gets_both(env):
    r = env.run("data", "clean", "--dumps", "--logbooks", "--yes")
    assert r.returncode == 0, _out(r)
    assert [(vm, c) for vm, c, _ in _ssh_cleans(env)] == [
        ("c2o-ground-vm", "clean dumps logbooks"), ("c2o-sim-vm", "clean dumps logbooks")]


def test_data_clean_needs_running_vm(tmp_path):
    e = Env(tmp_path, vms={"c2o-ground-vm": "TERMINATED", "c2o-sim-vm": "TERMINATED"})
    r = e.run("data", "clean", "--all", "--yes")
    assert r.returncode != 0 and "c2o up" in r.stderr and _ssh_cleans(e) == []


def test_data_clean_requires_a_choice(env):
    r = env.run("data", "clean")
    assert r.returncode != 0 and "--telemetry" in r.stderr


def test_data_list(env):
    r = env.run("data", "list")
    assert r.returncode == 0, _out(r)
    o = r.stdout
    assert re.search(r"MCS telemetry archive\s+2\.0 GB\s+--telemetry", o)
    assert re.search(r"SpaceCDF designs\s+4 MB\s+--designs only", o)
    assert re.search(r"of which participant logbooks\s+120 KB\s+--logbooks", o)
    assert "Disk: 9.0 GB used of 29.4 GB" in o
    assert "c2o-ground-vm-20261101-120000" in o


def test_data_prune_keeps_newest(tmp_path):
    snaps = [
        ["g-4", "c2o-ground-vm", 1, "2026-11-04T00:00:00"],
        ["g-3", "c2o-ground-vm", 1, "2026-11-03T00:00:00"],
        ["s-2", "c2o-sim-vm", 1, "2026-11-02T00:00:00"],
        ["g-2", "c2o-ground-vm", 1, "2026-11-02T00:00:00"],
        ["g-1", "c2o-ground-vm", 1, "2026-11-01T00:00:00"],
    ]
    e = Env(tmp_path, snapshots=snaps)
    r = e.run("data", "prune", "--keep", "2", "--yes")
    assert r.returncode == 0, _out(r)
    d = e.gcalls("compute", "snapshots", "delete")
    assert len(d) == 1 and set(d[0][3:5]) == {"g-2", "g-1"} and "--quiet" in d[0]
    assert e.run("data", "prune", "--keep", "x").returncode != 0


# ── users ────────────────────────────────────────────────────────────────

def _all_argv(env) -> str:
    return json.dumps([e["argv"] for e in env.log("gcloud.log") + env.log("curl.log")])


def test_users_add_student(env):
    r = env.run("users", "add", "NewStudent", "--name", "Ada Lovelace")
    assert r.returncode == 0, _out(r)
    curl = env.log("curl.log")
    create = [c for c in curl if c["method"] == "POST" and c["url"].endswith("/users")]
    assert len(create) == 1
    body = create[0]["body"]
    assert body["primaryEmail"] == "newstudent@c2o.live"           # bare name, lower-cased
    assert body["name"] == {"givenName": "Ada", "familyName": "Lovelace"}
    assert body["changePasswordAtNextLogin"] is True
    pw = body["password"]
    assert len(pw) >= 12
    assert r.stdout.count(pw) == 1                                   # printed exactly once
    # Neither the password nor the access token is ever on a command line.
    argv = _all_argv(env)
    assert pw not in argv and TOKEN not in argv
    assert all(c["auth"] and c["cfg_mode"] == "0o600" for c in curl)
    member = [c for c in curl if c["method"] == "POST" and "/members" in c["url"]]
    assert "c2o-students@c2o.live" in member[0]["url"] and member[0]["body"]["email"] == "newstudent@c2o.live"
    # The temporary files are gone.
    assert not [p for p in env.tmp.glob("c2o.*") if p.is_dir()]


def test_users_add_instructor_and_bad_input(env):
    r = env.run("users", "add", "ta1@c2o.live", "--name", "Tom Assistant", "--role", "instructor")
    assert r.returncode == 0, _out(r)
    assert "c2o-instructors@c2o.live" in env.state()["groups"] and \
        "ta1@c2o.live" in env.state()["groups"]["c2o-instructors@c2o.live"]
    for args, msg in ((("x@gmail.com", "--name", "A B"), "not an @c2o.live"),
                      (("bob",), "full name"),
                      (("bob", "--name", "Bob B", "--role", "dean"), "student or instructor"),
                      (("b ob", "--name", "Bob B"), "valid account")):
        r = env.run("users", "add", *args)
        assert r.returncode != 0 and msg in r.stderr, (args, _out(r))


def test_users_add_existing(env):
    r = env.run("users", "add", "jdoe", "--name", "Jane Doe")
    assert r.returncode != 0 and "already exists" in r.stderr


def test_users_list_and_seats(env):
    r = env.run("users", "list")
    assert r.returncode == 0, _out(r)
    o = r.stdout
    assert re.search(r"jdoe@c2o\.live\s+Jane Doe\s+student\s+no\s+no\s+never", o)
    assert re.search(r"prof@c2o\.live\s+Pat Prof\s+instructor\s+yes\s+no\s+2026-10-30 09:15", o)
    assert re.search(r"admin@c2o\.live\s+C2O Admin\s+admin", o)
    assert "3 account(s) of 50" in o
    r = env.run("users", "seats")
    assert "3 of 50 accounts used" in r.stdout and "47 free" in r.stdout


def test_users_remove(env):
    r = env.run("users", "remove", "jdoe", stdin="n\n")
    assert r.returncode != 0 and "PERMANENT" in r.stdout
    assert not [c for c in env.log("curl.log") if c["method"] == "DELETE"]
    r = env.run("users", "remove", "JDoe", "--yes")
    assert r.returncode == 0, _out(r)
    d = [c for c in env.log("curl.log") if c["method"] == "DELETE"]
    assert len(d) == 1 and d[0]["url"].endswith("/users/jdoe@c2o.live")
    r = env.run("users", "remove", "admin", "--yes")
    assert r.returncode != 0 and "administrator" in r.stderr


def test_users_suspend_reset_role(env):
    r = env.run("users", "suspend", "jdoe")
    assert r.returncode == 0, _out(r)
    assert env.state()["users"][1]["suspended"] is True
    assert env.run("users", "unsuspend", "jdoe").returncode == 0
    assert env.state()["users"][1]["suspended"] is False
    r = env.run("users", "reset", "jdoe")
    assert r.returncode == 0, _out(r)
    patch = [c for c in env.log("curl.log") if c["method"] == "PATCH"][-1]
    pw = patch["body"]["password"]
    assert patch["body"]["changePasswordAtNextLogin"] is True
    assert r.stdout.count(pw) == 1 and pw not in _all_argv(env)
    r = env.run("users", "role", "jdoe", "instructor")
    assert r.returncode == 0, _out(r)
    g = env.state()["groups"]
    assert "jdoe@c2o.live" in g["c2o-instructors@c2o.live"] and "jdoe@c2o.live" not in g["c2o-students@c2o.live"]


CLASS_CSV = """email,first,last,role
alice,Alice,Archer,student
bob@c2o.live,Bob,Baker,
jdoe,Jane,Doe,instructor
carol@gmail.com,Carol,Cook,student
dave,Dave,,student
alice,Alice,Again,student
erin,Erin,Eng,ta
"""


def test_users_import_dry_run_then_apply(env):
    csv = env.cwd / "class.csv"
    csv.write_text(CLASS_CSV)
    r = env.run("users", "import", "class.csv")
    assert r.returncode == 0, _out(r)
    o = r.stdout
    assert "create   alice@c2o.live" in o and "create   bob@c2o.live  (Bob Baker, student)" in o
    assert "create   erin@c2o.live  (Erin Eng, instructor)" in o
    assert "role     jdoe@c2o.live  -> instructor" in o
    assert "not an @c2o.live address" in o and "first and last name" in o and "listed twice" in o
    assert "3 to create, 1 role change(s), 0 already fine, 3 skipped; seats: 3 used + 3 new of 50" in o
    assert "Dry run" in o
    assert not [c for c in env.log("curl.log") if c["method"] != "GET"]

    r = env.run("users", "import", "class.csv", "--apply", "--yes", "--out", "pw.csv")
    assert r.returncode == 0, _out(r)
    created = [c["body"] for c in env.log("curl.log") if c["method"] == "POST" and c["url"].endswith("/users")]
    assert [b["primaryEmail"] for b in created] == ["alice@c2o.live", "bob@c2o.live", "erin@c2o.live"]
    pwfile = env.cwd / "pw.csv"
    assert stat.S_IMODE(pwfile.stat().st_mode) == 0o600
    lines = pwfile.read_text().splitlines()
    assert lines[0] == "email,password" and len(lines) == 4
    argv = _all_argv(env)
    for b in created:
        assert b["password"] not in argv and r.stdout.count(b["password"]) == 1
    g = env.state()["groups"]
    assert "erin@c2o.live" in g["c2o-instructors@c2o.live"]
    assert "jdoe@c2o.live" in g["c2o-instructors@c2o.live"]
    assert "jdoe@c2o.live" not in g["c2o-students@c2o.live"]
    # Running it again creates nothing.
    r = env.run("users", "import", "class.csv")
    assert "0 to create, 0 role change(s), 4 already fine" in r.stdout


def test_users_import_warns_over_cap(env):
    env.set_env("USER_CAP=4")
    (env.cwd / "c.csv").write_text("a1,A,One\na2,A,Two\n")
    r = env.run("users", "import", "c.csv")
    assert "exceeds the 4-account cap" in r.stderr


def test_users_missing_sign_in(tmp_path):
    e = Env(tmp_path, adc=False)
    r = e.run("users", "list")
    assert r.returncode != 0 and "c2o users login" in r.stderr
    assert e.log("curl.log") == []


@pytest.mark.parametrize("code,body", [(401, "x"), (403, "insufficient")])
def test_users_expired_or_unscoped_token(tmp_path, code, body):
    e = Env(tmp_path, force_code=code)
    if body == "insufficient":
        # The stub answers {"error": {"message": "forced"}}; give it a scope error instead.
        st = e.state(); st["force_code"] = 403; e.state_file.write_text(json.dumps(st))
        stub = (e.dir / "curl").read_text().replace(
            '"forced"', '"Request had insufficient authentication scopes."')
        (e.dir / "curl").write_text(stub)
    r = e.run("users", "seats")
    assert r.returncode != 0 and "c2o users login" in r.stderr, _out(r)


def test_users_login_uses_admin_scopes(env):
    r = env.run("users", "login")
    assert r.returncode == 0, _out(r)
    login = env.gcalls("auth", "application-default", "login")[0]
    scopes = next(a for a in login if a.startswith("--scopes=")).split("=", 1)[1].split(",")
    assert set(scopes) == {
        "https://www.googleapis.com/auth/admin.directory.user",
        "https://www.googleapis.com/auth/admin.directory.group.member",
        "https://www.googleapis.com/auth/cloud-platform",
    }
    q = env.gcalls("auth", "application-default", "set-quota-project")[0]
    assert "c2o-live-prod" in q


def test_setup_enables_admin_api_and_schedule_agent():
    src = (GCP / "setup.sh").read_text()
    assert "admin.googleapis.com" in src
    assert "compute-system.iam.gserviceaccount.com" in src and "roles/compute.instanceAdmin.v1" in src


# ── vm-bootstrap.sh clean (on the VM) against stub docker + metadata ────

DOCKER_STUB = r'''#!/usr/bin/env python3
import json, os, sys
d = os.environ["STUB_DIR"]
a = sys.argv[1:]
open(os.path.join(d, "docker.log"), "a").write(json.dumps(a) + "\n")
if a[:2] == ["volume", "inspect"]:
    v = a[-1]
    if v.endswith("missing-vol"):
        sys.exit(1)
    if "-f" in a:
        print(os.path.join(d, "vols", v))
    sys.exit(0)
if a[:2] == ["volume", "ls"]:
    print("\n".join(["smo_ground-archive", "smo_ground-dumps", "smo_space-workspace", "other_x"])); sys.exit(0)
if a[:1] == ["inspect"]:
    print("sha256:builtimage"); sys.exit(0)
if a[:1] == ["compose"] and "ps" in a and "-q" in a:
    print("cid-" + a[-1]); sys.exit(0)
sys.exit(0)
'''

META_CURL_STUB = r'''#!/bin/sh
for a in "$@"; do url="$a"; done
case "$url" in
  */instance/attributes/c2o-role) printf '%s' "$STUB_ROLE" ;;
  */project/project-id) printf 'c2o-live-prod' ;;
  */instance/network-interfaces/0/ip) printf '10.20.0.10' ;;
  */instance/attributes/*) exit 22 ;;
  *) exit 22 ;;
esac
'''


def _bootstrap(tmp: Path, role: str, *args: str):
    d = tmp / "bs"
    (d / "vols").mkdir(parents=True)
    for n, body in (("docker", DOCKER_STUB), ("curl", META_CURL_STUB)):
        (d / n).write_text(body)
        (d / n).chmod(0o755)
    app = tmp / "app"
    (app / "sim" / "docker").mkdir(parents=True)
    (app / "sim" / "docker" / "config-hash.sh").write_text("echo cafe\n")
    env = dict(os.environ, PATH=f"{d}{os.pathsep}{os.environ['PATH']}", STUB_DIR=str(d),
               STUB_ROLE=role, C2O_APP_DIR=str(app))
    r = subprocess.run(["bash", str(BOOTSTRAP), *args], capture_output=True, text=True, env=env, timeout=60)
    calls = [json.loads(ln) for ln in (d / "docker.log").read_text().splitlines()] \
        if (d / "docker.log").exists() else []
    return r, calls


def _compose_verb(call):
    if call[:1] != ["compose"]:
        return None
    rest = call[call.index("docker/compose.yaml") + 1:]
    rest = [x for i, x in enumerate(rest) if x != "--profile" and (i == 0 or rest[i - 1] != "--profile")]
    return rest


def test_bootstrap_clean_telemetry_ground(tmp_path):
    r, calls = _bootstrap(tmp_path, "ground", "clean", "telemetry")
    assert r.returncode == 0, r.stderr
    verbs = [_compose_verb(c) for c in calls if c[:1] == ["compose"]]
    assert ["stop", "mcs"] in verbs                 # only the MCS mounts the archive
    assert verbs[-1] == ["up", "-d"]                # restarted, without --build
    run = [c for c in calls if c[:1] == ["run"]]
    assert len(run) == 1
    c = run[0]
    assert "--rm" in c and "--network" in c and "none" in c and "--entrypoint" in c
    assert "smo_ground-archive:/v" in c and "sha256:builtimage" in c     # the image already on the VM
    assert not any(x in ("pull", "build", "--build") for call in calls for x in call)


def test_bootstrap_clean_ground_dumps_reports_stop_everything(tmp_path):
    r, calls = _bootstrap(tmp_path, "ground", "clean", "dumps", "reports")
    assert r.returncode == 0, r.stderr
    verbs = [_compose_verb(c) for c in calls if c[:1] == ["compose"]]
    assert ["stop"] in verbs, "the GSG's network namespace is shared: stop all"
    vols = [x for c in calls if c[:1] == ["run"] for x in c if x.endswith(":/v")]
    assert vols == ["smo_ground-dumps:/v", "smo_ground-workspace:/v"]
    reports = [c for c in calls if c[:1] == ["run"] and "smo_ground-workspace:/v" in c][0]
    assert "C2O_PATHS=reports pass_rollups*" in reports


def test_bootstrap_clean_sim_and_never_scenarios(tmp_path):
    r, calls = _bootstrap(tmp_path, "sim", "clean", "telemetry", "dumps", "reports")
    assert r.returncode == 0, r.stderr
    vols = [x for c in calls if c[:1] == ["run"] for x in c if x.endswith(":/v")]
    assert vols == ["smo_space-dumps:/v"]
    assert "nothing of that kind on the sim VM" in r.stderr
    assert not any("space-workspace" in x for c in calls for x in c if c[:1] == ["run"])


def test_bootstrap_clean_logbooks(tmp_path):
    r, calls = _bootstrap(tmp_path / "g", "ground", "clean", "logbooks")
    assert r.returncode == 0, r.stderr
    run = [c for c in calls if c[:1] == ["run"]]
    assert len(run) == 1 and "smo_ground-workspace:/v" in run[0]
    assert "C2O_PATHS=logbook" in run[0]
    assert ["stop"] in [_compose_verb(c) for c in calls if c[:1] == ["compose"]]
    r, calls = _bootstrap(tmp_path / "s", "sim", "clean", "logbooks")
    assert r.returncode == 0, r.stderr
    run = [c for c in calls if c[:1] == ["run"]]
    assert len(run) == 1 and "smo_space-workspace:/v" in run[0] and "C2O_PATHS=logbook" in run[0]


def test_bootstrap_clean_rejects_unknown(tmp_path):
    r, calls = _bootstrap(tmp_path, "ground", "clean", "scenarios")
    assert r.returncode != 0 and "unknown recording" in r.stderr
    assert not [c for c in calls if c[:1] in (["run"], ["compose"])]


def test_bootstrap_clean_snippet_deletes_files_keeps_dirs(tmp_path):
    """Run the in-container snippet for real, on a fake volume."""
    _, calls = _bootstrap(tmp_path, "ground", "clean", "reports")
    c = [c for c in calls if c[:1] == ["run"]][0]
    snippet = c[c.index("-c") + 1].replace("/v", str(tmp_path / "vol"))
    paths = next(x for x in c if x.startswith("C2O_PATHS=")).split("=", 1)[1]
    v = tmp_path / "vol"
    (v / "reports" / "2026").mkdir(parents=True)
    (v / "reports" / "2026" / "pass1.html").write_text("x")
    (v / "pass_rollups.jsonl").write_text("x")
    (v / "dumps").mkdir()
    (v / "keep.json").write_text("x")
    r = subprocess.run(["sh", "-c", snippet], env=dict(os.environ, C2O_PATHS=paths))
    assert r.returncode == 0
    assert (v / "reports" / "2026").is_dir() and not (v / "reports" / "2026" / "pass1.html").exists()
    assert not (v / "pass_rollups.jsonl").exists()
    assert (v / "keep.json").exists() and (v / "dumps").is_dir()


def test_bootstrap_sizes(tmp_path):
    r, _ = _bootstrap(tmp_path, "ground", "sizes")
    assert r.returncode == 0, r.stderr
    lines = r.stdout.splitlines()
    assert lines[0] == "role ground"
    assert [ln.split()[1] for ln in lines if ln.startswith("vol ")] == \
        ["ground-archive", "ground-dumps", "space-workspace"]
    assert any(ln.startswith("disk ") for ln in lines)


# ── c2o update (both VMs: pull, rebuild, restart) ──────────────────────────
def _ssh_updates(env):
    out = []
    for e in env.log("gcloud.log"):
        a = e["argv"]
        cmd = next((x for x in a if x.startswith("--command=")), "")
        if a[:2] == ["compute", "ssh"] and 'sudo bash "$t" update' in cmd:
            out.append((a[2], (env.dir / e["stdin_file"]).read_text()))
    return out


def test_update_runs_bootstrap_update_on_both_vms(env):
    r = env.run("update")
    assert r.returncode == 0, _out(r)
    calls = _ssh_updates(env)
    assert [vm for vm, _ in calls] == ["c2o-ground-vm", "c2o-sim-vm"]
    assert all(stdin == BOOTSTRAP.read_text() for _, stdin in calls)
    r = env.run("update", "ground")
    assert r.returncode == 0, _out(r)
    assert [vm for vm, _ in _ssh_updates(env)][-1] == "c2o-ground-vm"
    assert env.run("update", "nonsense").returncode != 0


def test_bootstrap_on_a_laptop_says_what_to_run(tmp_path):
    # not root / not Linux and no C2O_APP_DIR: stop before any bash-4-only line
    stub = tmp_path / "uname"
    stub.write_text("#!/bin/sh\necho Darwin\n")
    stub.chmod(0o755)
    env = {k: v for k, v in os.environ.items() if k != "C2O_APP_DIR"}
    env["PATH"] = f"{tmp_path}:{env['PATH']}"
    r = subprocess.run(["bash", str(BOOTSTRAP), "update"], capture_output=True, text=True, env=env, timeout=30)
    assert r.returncode == 2 and "c2o update" in r.stderr
