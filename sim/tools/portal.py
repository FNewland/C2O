#!/usr/bin/env python3
"""portal.py: the C2O welcome page (port 8090).

https://c2o.live (the apex) shows this page: a short list of every C2O
screen, grouped by what the user is about to do (operate, design, analyse,
instruct), each with its address and a live status checked on the server,
plus a mission strip (simulator link, spacecraft mode, next pass) and the
signed-in account. It is a launcher, not a console: it reads, never commands.

Addresses
  * cloud (``SMO_PORTAL_DOMAIN=c2o.live``): ``https://<name>.c2o.live``;
  * local (no domain): ``http://<the host this page was opened on>:<port>``,
    the ports of ``sim/start.sh`` (MCS 9090, planner 9091, instructor 8080,
    tools 8092-8097, SpaceCDF 8000 or the 5173 dev server).

Status probes (server side, short timeouts, cached ``CACHE_S``; the page
renders at once and polls ``/api/status``). Where a probe goes:
  * ground services: ``127.0.0.1:<port>`` (in Docker the portal shares the
    GSG's network namespace, like the MCS; ``SMO_PORTAL_GROUND_HOST`` when
    start.sh binds the suite to one address);
  * instructor tools: ``SMO_PORTAL_SIM_HOST`` (default ``10.20.0.11``, the
    cloud simulator VM, when a domain is set; else ``127.0.0.1``);
  * per-service override: ``SMO_PORTAL_PROBE="design=spacecdf:8000,..."``;
  * local port override: ``SMO_PORTAL_PORTS="sim=18080,..."`` (start.sh
    passes the instructor console's real port).

Mission strip: the link from the GSG ``/link-status`` (or "simulator on this
machine" when the instructor port is the simulator itself); spacecraft mode
from the MCS ``/api/state`` (TM ``obdh.mode`` 0x0300 only, never the
simulator's truth); next pass from the MCS contact schedule. Signed-in
account: the IAP header ``X-Goog-Authenticated-User-Email``.

Usage::

    python tools/portal.py                       # port 8090, local links
    SMO_PORTAL_DOMAIN=c2o.live python tools/portal.py --host 0.0.0.0
"""
from __future__ import annotations

import argparse
import asyncio
import html
import json
import logging
import math
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parents[1]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
_COMMON_SRC = REPO / "packages" / "smo-common" / "src"
if _COMMON_SRC.is_dir() and str(_COMMON_SRC) not in sys.path:
    sys.path.insert(0, str(_COMMON_SRC))

try:
    import aiohttp
    from aiohttp import web
except ImportError:
    print("ERROR: aiohttp required. Install: pip install aiohttp")
    raise SystemExit(1)

#: A connect timeout means "not there"; a read timeout means "busy starting".
_CONNECT_TIMEOUT = getattr(aiohttp, "ConnectionTimeoutError", ())

DEFAULT_PORT = 8090
#: Probe results are shared by every viewer for this long (seconds).
CACHE_S = 5.0
#: Per-probe timeouts (seconds): a dead host must not hold the page's poll.
CONNECT_TIMEOUT_S = 1.0
TOTAL_TIMEOUT_S = 2.0
DEFAULT_SIM_HOST_CLOUD = "10.20.0.11"
IAP_USER_HEADER = "X-Goog-Authenticated-User-Email"
#: TM obdh.mode (0x0300) enumeration; same table as ui/state.js SC_MODES.
SC_MODES = ["NOMINAL", "SAFE", "EMERGENCY", "SCIENCE"]
#: MCS ages are SIM seconds; older than this the mode is shown as stale.
MODE_STALE_S = 60.0


def T(s: str) -> str:
    """Marks an English UI string for the tools catalog (the page translates
    it in the browser through data-i18n; the server always writes English)."""
    return s


# ── The screens ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class Service:
    key: str            # also the cloud host label: <key>.<domain>
    section: str        # operate | design | analyse | instructor
    name: str
    purpose: str
    ports: tuple[int, ...]   # local ports, first is preferred
    where: str = "ground"    # ground | sim (instructor tools on the sim VM)
    instructors_only: bool = False


SERVICES: tuple[Service, ...] = (
    Service("ops", "operate", T("Mission control"),
            T("Watch EOSAT-1 telemetry and send telecommands during a pass."), (9090,)),
    Service("plan", "operate", T("Mission planner"),
            T("Plan passes, imaging and downlinks, and build the command schedule."), (9091,)),
    Service("design", "design", T("SpaceCDF"),
            T("Design a CubeSat mission as a team: requirements, budgets and trades."),
            (8000, 5173)),
    Service("tm", "analyse", T("Delayed telemetry"),
            T("Decode and plot the housekeeping dumped during a pass."), (8092,)),
    Service("orbit", "analyse", T("Orbit tools"),
            T("Turn a TLE or state vector into the orbit-update telecommands."), (8093,)),
    Service("radio", "analyse", T("Radio view"),
            T("Follow the RF link: carrier, bit and frame lock, error rates."), (8094,)),
    Service("docs", "analyse", T("Documentation"),
            T("Mission manual, procedures and command reference."), (8095,)),
    Service("sim", "instructor", T("Instructor console"),
            T("Run the simulator: scenarios, failures, time and speed."), (8080,),
            instructors_only=True),
    Service("scenarios", "instructor", T("Scenario generator"),
            T("Write a new training scenario from failures and timings."), (8096,),
            where="sim", instructors_only=True),
    Service("adcs", "instructor", T("ADCS failure viewer"),
            T("Explore attitude-failure cases before running them in class."), (8097,),
            where="sim", instructors_only=True),
)

SECTIONS: tuple[tuple[str, str, str], ...] = (
    ("design", T("Design"), T("Build the mission")),
    ("operate", T("Operate"), T("Fly the spacecraft")),
    ("analyse", T("Analyse"), T("Review passes, prepare the next")),
    ("instructor", T("Instructor"), T("Instructors only")),
)


# ── Configuration ─────────────────────────────────────────────────────

def _pairs(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in (text or "").split(","):
        k, sep, v = item.strip().partition("=")
        if sep and k.strip() and v.strip():
            out[k.strip()] = v.strip()
    return out


@dataclass
class Config:
    domain: str = ""                     # "" = local links
    sim_host: str = "127.0.0.1"          # where the instructor tools run
    ground_host: str = "127.0.0.1"       # where the ground services run
    ports: dict[str, tuple[int, ...]] = field(default_factory=dict)
    probe: dict[str, str] = field(default_factory=dict)   # key -> host:port

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> Config:
        env = dict(os.environ if env is None else env)
        domain = env.get("SMO_PORTAL_DOMAIN", "").strip().strip(".").lower()
        if domain.startswith("@"):        # an unrendered template value
            domain = ""
        sim_host = env.get("SMO_PORTAL_SIM_HOST", "").strip() or (
            DEFAULT_SIM_HOST_CLOUD if domain else "127.0.0.1")
        ports: dict[str, tuple[int, ...]] = {}
        for k, v in _pairs(env.get("SMO_PORTAL_PORTS", "")).items():
            try:
                ports[k] = tuple(int(p) for p in v.split("/") if p)
            except ValueError:
                logger.warning("SMO_PORTAL_PORTS: ignoring %s=%s", k, v)
        ground_host = env.get("SMO_PORTAL_GROUND_HOST", "").strip() or "127.0.0.1"
        return cls(domain=domain, sim_host=sim_host, ground_host=ground_host, ports=ports,
                   probe=_pairs(env.get("SMO_PORTAL_PROBE", "")))

    def local_ports(self, svc: Service) -> tuple[int, ...]:
        return self.ports.get(svc.key) or svc.ports

    def targets(self, svc: Service) -> list[tuple[str, int]]:
        """host:port pairs to probe, in order of preference."""
        if svc.key in self.probe:
            host, _, port = self.probe[svc.key].rpartition(":")
            try:
                return [(host or "127.0.0.1", int(port))]
            except ValueError:
                pass
        host = self.sim_host if svc.where == "sim" else self.ground_host
        return [(host, p) for p in self.local_ports(svc)]

    def link(self, svc: Service, request_host: str | None, port: int | None = None) -> str:
        if self.domain:
            return f"https://{svc.key}.{self.domain}/"
        host = request_host or "localhost"
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"                     # IPv6 literal
        return f"http://{host}:{port or self.local_ports(svc)[0]}/"


def display_address(url: str) -> str:
    """``https://ops.c2o.live/`` -> ``ops.c2o.live``."""
    return url.split("://", 1)[-1].rstrip("/")


def iap_user(headers) -> str | None:
    """The IAP-asserted account, without the ``accounts.google.com:`` prefix.
    Only the load balancer sets this header; locally it is absent."""
    raw = (headers.get(IAP_USER_HEADER) or "").strip()
    if not raw:
        return None
    user = raw.split(":", 1)[1] if ":" in raw else raw
    return user[:254] or None


# ── Probes ────────────────────────────────────────────────────────────

class Prober:
    """All probes for one status snapshot, shared by every viewer for CACHE_S."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._cache: tuple[float, dict] | None = None
        self._lock = asyncio.Lock()
        self._session: aiohttp.ClientSession | None = None

    def cached(self) -> dict | None:
        if self._cache and time.monotonic() - self._cache[0] < CACHE_S:
            return self._cache[1]
        return None

    async def snapshot(self) -> dict:
        hit = self.cached()
        if hit is not None:
            return hit
        async with self._lock:
            hit = self.cached()
            if hit is not None:
                return hit
            snap = await self._collect()
            self._cache = (time.monotonic(), snap)
            return snap

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    def _sess(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=TOTAL_TIMEOUT_S,
                                              sock_connect=CONNECT_TIMEOUT_S),
                headers={"User-Agent": "c2o-portal"})
        return self._session

    async def http(self, host: str, port: int, path: str) -> tuple[str, int | None, object]:
        """-> ("up"|"starting"|"down", status, parsed JSON or None)."""
        url = f"http://{host}:{port}{path}"
        try:
            async with self._sess().get(url, allow_redirects=False) as r:
                body = None
                if "json" in (r.headers.get("Content-Type") or ""):
                    try:
                        body = await r.json(content_type=None)
                    except (ValueError, aiohttp.ClientError):
                        body = None
                return ("starting" if r.status >= 500 else "up"), r.status, body
        except _CONNECT_TIMEOUT:
            return "down", None, None        # nothing answers at that address
        except TimeoutError:
            return "starting", None, None    # connected, but no answer yet
        except (aiohttp.ClientError, OSError):
            return "down", None, None

    async def _service(self, svc: Service) -> dict:
        best = None
        for host, port in self.cfg.targets(svc):
            state, _, _ = await self.http(host, port, "/")
            if state == "up":
                return {"state": "up", "port": port}
            if best is None or (state == "starting" and best["state"] == "down"):
                best = {"state": state, "port": port}
        return best or {"state": "down", "port": None}

    async def _collect(self) -> dict:
        svc_results = await asyncio.gather(*(self._service(s) for s in SERVICES))
        services = {s.key: r for s, r in zip(SERVICES, svc_results)}
        link, mode, nxt = await asyncio.gather(self._link(), self._mode(), self._pass())
        # The instructor console goes through the GSG: with no simulator on
        # the link it cannot open, whatever its port says.
        if link.get("state") == "DOWN" and services["sim"]["state"] != "down":
            services["sim"] = {**services["sim"], "state": "starting",
                               "reason": "no-simulator"}
        return {
            "checked_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "services": services, "link": link, "mode": mode, "pass": nxt,
        }

    def _first(self, key: str) -> tuple[str, int]:
        svc = next(s for s in SERVICES if s.key == key)
        return self.cfg.targets(svc)[0]

    async def _link(self) -> dict:
        host, port = self._first("sim")
        state, _, body = await self.http(host, port, "/link-status")
        if state == "up" and isinstance(body, dict) and "state" in body:
            s = str(body.get("state", "")).upper()
            return {"state": s if s in ("UP", "DEGRADED", "DOWN") else "DOWN",
                    "rtt_s": body.get("rtt") if isinstance(body.get("rtt"), (int, float)) else None}
        if state == "up":
            # 404 from a simulator (start.sh "all" profile): no space link,
            # the simulator itself is on this port.
            st2, _, _ = await self.http(host, port, "/api/state")
            if st2 == "up":
                return {"state": "DIRECT"}
        return {"state": "UNREACHABLE"}

    async def _mode(self) -> dict | None:
        host, port = self._first("ops")
        state, _, st = await self.http(host, port, "/api/state")
        if state != "up" or not isinstance(st, dict):
            return None
        return mode_from_state(st)

    async def _pass(self) -> dict | None:
        host, port = self._first("ops")
        state, _, d = await self.http(host, port, "/api/displays/contact-schedule")
        if state != "up" or not isinstance(d, dict):
            return None
        return pass_from_schedule(d)


def _finite(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def mode_from_state(st: dict) -> dict:
    """Spacecraft mode from GROUND telemetry only (ui/state.js modeState,
    without the training-truth fallback): TM 0x0300, else obdh.mode."""
    params = st.get("params") if isinstance(st.get("params"), dict) else {}
    code, source = None, None
    if _finite(params.get("0x0300")):
        code, source = int(params["0x0300"]), "TM obdh.mode 0x0300"
    elif isinstance(st.get("obdh"), dict) and _finite(st["obdh"].get("mode")):
        code, source = int(st["obdh"]["mode"]), "TM obdh.mode"
    if code is None:
        return {"mode": None, "source": None, "age_s": None, "stale": False}
    mode = SC_MODES[code] if 0 <= code < len(SC_MODES) else f"MODE_{code}"
    age = st.get("last_frame_age_s")
    age = float(age) if _finite(age) else None
    stale = bool(st.get("stale")) or (age is not None and age > MODE_STALE_S)
    return {"mode": mode, "source": source, "age_s": age, "stale": stale}


def pass_from_schedule(d: dict) -> dict | None:
    cur = d.get("current_contact_status")
    if not isinstance(cur, dict):
        return None
    station = str(cur.get("ground_station") or "")[:60]
    if cur.get("in_contact"):
        t = cur.get("time_to_los")
        return {"in_contact": True, "station": station,
                "seconds": float(t) if _finite(t) else None}
    t = cur.get("time_to_aos")
    if not _finite(t):
        return {"in_contact": False, "station": "", "seconds": None}
    return {"in_contact": False, "station": station, "seconds": float(t)}


# ── Page ──────────────────────────────────────────────────────────────

PAGE_CSS = """
/* ── portal (tools/portal.py) ── tokens only ───────────────────────── */
.pt-main{ max-width:1320px; padding:var(--sp-5) var(--sp-5) var(--sp-6); }
.pt-intro{ color:var(--tx2); max-width:68ch; margin-bottom:var(--sp-5); }
.pt-intro b{ color:var(--tx); font-weight:600; }

/* Mission strip: one line of readouts under the title bar, hairlines only. */
.pt-band{ background:var(--s1); border-bottom:1px solid var(--line); }
.pt-strip{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); max-width:1320px; }
.pt-cell{ padding:var(--sp-3) var(--sp-5); min-width:0; border-right:1px solid var(--line); }
.pt-cell:last-child{ border-right:0; }
.pt-cell dt{ font-size:var(--fs-label); color:var(--tx3); margin-bottom:2px; }
.pt-cell dd{ display:flex; align-items:baseline; flex-wrap:wrap; gap:var(--sp-2);
  font-size:var(--fs-value); line-height:var(--lh-value,1.2); color:var(--val); min-height:20px; }
.pt-cell .src{ font-size:var(--fs-label); color:var(--tx3); }
.pt-cell .v{ font-family:var(--mono); font-weight:500; }
.pt-cell .v.is-stale{ color:var(--tx3); font-style:italic; font-weight:400; }
.pt-cell .ok{ color:var(--ok); }
.pt-cell .is-caution{ color:var(--warn); }
.pt-cell .quiet{ color:var(--tx2); }
.pt-cell svg{ width:11px; height:11px; align-self:center; flex:0 0 auto; }

/* The launcher: section label on the left, its screens on the right. */
.pt-sec{ display:grid; grid-template-columns:11rem minmax(0,1fr); column-gap:var(--sp-5);
  border-top:1px solid var(--line-2); padding-top:var(--sp-3); margin-bottom:var(--sp-5); }
.pt-sec>header{ padding-top:var(--sp-2); }
.pt-sec h2{ font-size:var(--fs-body); font-weight:600; color:var(--tx); }
.pt-sec header p{ font-size:var(--fs-label); color:var(--tx3); margin-top:2px; }
.pt-list{ list-style:none; }
.pt-row{ display:grid; grid-template-columns:12rem minmax(0,1fr) 11.5rem 8.5rem;
  column-gap:var(--sp-4); align-items:center; min-height:48px; padding:var(--sp-2) var(--sp-3);
  border-bottom:1px solid var(--line); color:inherit; text-decoration:none;
  border-radius:var(--radius-sm); transition:background-color var(--motion,140ms); }
.pt-list li:last-child .pt-row{ border-bottom:0; }
.pt-row:hover{ background:var(--s2); }
.pt-row:focus-visible{ outline-offset:-2px; }
.pt-name{ font-size:var(--fs-value); font-weight:600; color:var(--val); }
.pt-row:hover .pt-name{ text-decoration:underline; text-decoration-thickness:1px;
  text-underline-offset:3px; }
.pt-purpose{ color:var(--tx2); }
.pt-addr{ font-family:var(--mono); font-size:var(--fs-label); color:var(--tx3);
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.pt-state{ justify-self:end; text-align:right; }
.pt-up{ display:inline-flex; align-items:center; gap:6px; font-size:var(--fs-label); color:var(--tx2); }
.pt-up .g{ color:var(--ok); display:inline-flex; }
.pt-up svg{ width:10px; height:10px; }
.pt-state .why{ display:block; font-size:var(--fs-label); color:var(--tx3); margin-top:2px; }
.pt-row.is-down .pt-name{ color:var(--tx2); font-weight:500; }
.pt-row.is-down .pt-purpose{ color:var(--tx3); }

.pt-foot{ font-size:var(--fs-label); color:var(--tx3); max-width:80ch; }
.pt-foot .num{ color:var(--tx2); }
.pt-user{ font-size:var(--fs-label); color:var(--tx2); white-space:nowrap; }
.pt-user b{ font-weight:500; color:var(--tx); font-family:var(--mono); }
.pt-user a{ margin-left:var(--sp-3); }

@media (max-width:1100px){
  .pt-row{ grid-template-columns:11rem minmax(0,1fr) 9.5rem; }
  .pt-addr{ grid-column:2; grid-row:2; }
  .pt-state{ grid-column:3; grid-row:1 / span 2; }
}
@media (max-width:720px){
  .pt-main{ padding:var(--sp-4) var(--sp-4) var(--sp-5); }
  .pt-strip{ grid-template-columns:1fr; }
  .pt-cell{ border-right:0; border-bottom:1px solid var(--line); padding:var(--sp-2) var(--sp-4);
    display:flex; justify-content:space-between; gap:var(--sp-3); align-items:baseline; }
  .pt-cell:last-child{ border-bottom:0; }
  .pt-cell dt{ margin:0; flex:0 0 auto; }
  .pt-cell dd{ justify-content:flex-end; text-align:right; }
  .pt-sec{ grid-template-columns:1fr; }
  .pt-sec>header{ display:flex; align-items:baseline; gap:var(--sp-3); padding:0 0 var(--sp-1); }
  .pt-sec header p{ margin:0; }
  .pt-row{ grid-template-columns:minmax(0,1fr) auto; row-gap:2px; padding:var(--sp-2) 0; }
  .pt-name{ grid-column:1; grid-row:1; }
  .pt-state{ grid-column:2; grid-row:1; }
  .pt-purpose{ grid-column:1 / -1; grid-row:2; }
  .pt-addr{ grid-column:1 / -1; grid-row:3; }
  .pt-up{ display:inline-flex; align-items:center; gap:6px; font-size:var(--fs-label); color:var(--tx2); }
.pt-up .g{ color:var(--ok); display:inline-flex; }
.pt-up svg{ width:10px; height:10px; }
.pt-state .why{ display:none; }
  .pt-user{ white-space:normal; }
}
"""

#: Theme: ?theme= > stored c2o.theme > the OS setting (light/dark).
_PREFERS = """<script>
(function(){try{var m=window.matchMedia&&matchMedia("(prefers-color-scheme: light)").matches;
document.documentElement.setAttribute("data-default-theme",m?"light":"dark");}catch(e){}})();
</script>"""


#: Strings from SERVICES/SECTIONS are marked with T() above; written through
#: this name, their data-i18n spans are not read as catalog keys themselves.
_DYN_I18N = "data-i18n"


def _status_cell(svc: Service) -> str:
    return (f'<span class="pt-state" id="st-{svc.key}" data-key="{svc.key}">'
            '<span class="ds-chip is-nodata"><span data-i18n>Checking…</span></span></span>')


def _row(svc: Service, url: str) -> str:
    # No address line: the row is the link, and a port number or host name
    # is developer information (SCREEN_REVIEW §1).
    e = html.escape
    return (f'<li><a class="pt-row" id="row-{svc.key}" href="{e(url)}">'
            f'<span class="pt-name" {_DYN_I18N}>{e(svc.name)}</span>'
            f'<span class="pt-purpose" {_DYN_I18N}>{e(svc.purpose)}</span>'
            f'{_status_cell(svc)}</a></li>')


def visible_services(instructor: bool) -> tuple[Service, ...]:
    """The screens this viewer may see: instructor tools only for an
    instructor (SCREEN_REVIEW #17); a student does not learn they exist."""
    return tuple(s for s in SERVICES if instructor or not s.instructors_only)


def build_page(cfg: Config, *, request_host: str | None, user: str | None,
               lang: str = "en", instructor: bool = True) -> str:
    import tool_frame
    e = html.escape
    sections = []
    shown = visible_services(instructor)
    for key, title, sub in SECTIONS:
        rows = "".join(_row(s, cfg.link(s, request_host)) for s in shown if s.section == key)
        if not rows:
            continue
        sections.append(
            f'<section class="pt-sec" aria-labelledby="h-{key}">'
            f'<header><h2 id="h-{key}" {_DYN_I18N}>{e(title)}</h2>'
            f'<p {_DYN_I18N}>{e(sub)}</p></header>'
            f'<ul class="pt-list">{rows}</ul></section>')
    if user:
        who = (f'<span class="pt-user"><span data-i18n>Signed in as</span> <b>{e(user)}</b>'
               '<a href="/?gcp-iap-mode=CLEAR_LOGIN_COOKIE" data-i18n>Sign out</a></span>')
    else:
        who = ""
    bar = tool_frame.bar('<span data-i18n>Welcome to C2O</span>',
                         meta_html='<span data-i18n>EOSAT-1 mission operations training</span>',
                         logbook="portal")
    # The account sits in the bar's status slot (server-rendered, not live).
    bar = bar.replace('aria-live="polite"></span>', f'aria-live="polite">{who}</span>', 1)
    strip = (
        '<section class="pt-band" aria-labelledby="h-mission"><h2 class="ds-sr" id="h-mission" data-i18n>Mission status</h2>'
        '<dl class="pt-strip">'
        '<div class="pt-cell"><dt data-i18n>Simulator link</dt>'
        '<dd id="m-link"><span class="quiet" data-i18n>Checking…</span></dd></div>'
        '<div class="pt-cell"><dt data-i18n>Spacecraft mode</dt>'
        '<dd id="m-mode"><span class="quiet" data-i18n>Checking…</span></dd></div>'
        '<div class="pt-cell"><dt data-i18n>Next pass</dt>'
        '<dd id="m-pass"><span class="quiet" data-i18n>Checking…</span></dd></div>'
        '</dl></section>')
    where = (f'<span data-i18n>Each screen has its own address under</span> '
             f'<b class="num">{e(cfg.domain)}</b><span data-i18n>; sign in once with your C2O account.</span>'
             if cfg.domain else '')
    boot = json.dumps({"domain": cfg.domain}).replace("</", "<\\/")
    return f"""<!DOCTYPE html>
<html lang="{e(lang)}"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>C2O</title>
{_PREFERS}
{tool_frame.head(extra_css=PAGE_CSS)}
</head><body>
<a class="ds-skip" href="#content" data-i18n>Skip to content</a>
{bar}
{strip}
<main id="content" class="pt-main">
<p class="pt-intro"><span data-i18n>Choose the screen for what you are about to do. The status beside each one is checked on the server every few seconds.</span> {where}</p>
{"".join(sections)}
<p class="pt-foot" id="foot"><span data-i18n>Status not checked yet.</span></p>
</main>
<script id="pt-boot" type="application/json">{boot}</script>
{tool_frame.SCRIPT}
{PAGE_JS}
</body></html>"""


PAGE_JS = """<script type="module">
import { glyph, esc } from "/static/shared/components.js";
import I18n from "/static/shared/i18n.js";
const T = (s, v) => I18n.tText(s, v);
const $ = (id) => document.getElementById(id);
let last = null, failed = false;

function dur(s) {
  if (s === null || s === undefined || !isFinite(s)) return "";
  s = Math.max(0, Math.round(s));
  if (s < 60) return T("{{n}} s", { n: s });
  const m = Math.round(s / 60);
  if (m < 60) return T("{{n}} min", { n: m });
  return T("{{h}} h {{m}} min", { h: Math.floor(m / 60), m: m % 60 });
}
function chip(kind, label, g) {
  return `<span class="ds-chip ${kind}">${g ? glyph(g) : ""}<span>${esc(label)}</span></span>`;
}
function serviceCell(key, r) {
  if (!r) return chip("is-nodata", T("Checking…"));
  // Calm when nominal: "available" is quiet text; only exceptions get a chip.
  if (r.state === "up") return `<span class="pt-up"><span class="g">${glyph("ack")}</span>${esc(T("Available"))}</span>`;
  if (r.state === "starting") {
    const why = r.reason === "no-simulator" ? T("No simulator connected") : T("Not answering yet");
    return chip("is-stale", r.reason === "no-simulator" ? T("Waiting") : T("Starting"), "stale") +
      `<span class="why">${esc(why)}</span>`;
  }
  return chip("off", T("Not running"), "off");
}
function linkCell(l) {
  const s = (l || {}).state;
  if (s === "UP") return `<span class="ok">${glyph("ack")}</span><span>${esc(T("Connected"))}</span>`;
  if (s === "DEGRADED") return `<span class="is-caution">${glyph("warn-up")}</span><span class="is-caution">${esc(T("Degraded"))}</span><span class="src">${esc(T("telemetry may lag"))}</span>`;
  if (s === "DIRECT") return `<span class="ok">${glyph("ack")}</span><span>${esc(T("Simulator on this computer"))}</span>`;
  if (s === "DOWN") return `${glyph("off")}<span class="quiet">${esc(T("No simulator connected"))}</span>`;
  return `${glyph("off")}<span class="quiet">${esc(T("Gateway not reachable"))}</span>`;
}
function modeCell(m) {
  if (!m) return `<span class="ds-chip is-nodata"><span>${esc(T("no data"))}</span></span><span class="src">${esc(T("mission control not running"))}</span>`;
  if (!m.mode) return `<span class="ds-chip is-nodata"><span>${esc(T("no data"))}</span></span><span class="src">${esc(T("not downlinked yet"))}</span>`;
  const bad = m.mode === "SAFE" || m.mode === "EMERGENCY";
  if (m.stale) {
    const age = m.age_s === null || m.age_s === undefined ? "" : `<span class="ds-age">${esc(dur(m.age_s))}</span>`;
    return `<span class="v is-stale">${esc(m.mode)}</span>${age}<span class="src">${esc(T("last telemetry"))}</span>`;
  }
  const g = bad ? `<span class="is-caution">${glyph("warn-up")}</span>` : "";
  const age = m.age_s === null || m.age_s === undefined ? "" : ", " + esc(dur(m.age_s));
  return `${g}<span class="v${bad ? " is-caution" : ""}">${esc(m.mode)}</span><span class="src">${esc(T("telemetry"))}${age}</span>`;
}
function passCell(p) {
  if (!p) return `<span class="ds-chip is-nodata"><span>${esc(T("no data"))}</span></span><span class="src">${esc(T("mission control not running"))}</span>`;
  if (p.in_contact) return `<span class="v">${esc(p.station || "")}</span><span>${esc(T("in contact, LOS in {{t}}", { t: dur(p.seconds) }))}</span>`;
  if (p.seconds === null || p.seconds === undefined) return `<span class="quiet">${esc(T("No pass scheduled"))}</span>`;
  return `<span class="v">${esc(p.station || "")}</span><span>${esc(T("AOS in {{t}}", { t: dur(p.seconds) }))}</span>`;
}
function paint() {
  const d = last || {};
  const sv = d.services || {};
  document.querySelectorAll(".pt-state[data-key]").forEach((el) => {
    const r = sv[el.dataset.key];
    el.innerHTML = last ? serviceCell(el.dataset.key, r) : serviceCell(el.dataset.key, null);
    const row = el.closest(".pt-row");
    if (row) row.classList.toggle("is-down", !!r && r.state === "down");
  });
  if (last) {
    $("m-link").innerHTML = linkCell(d.link);
    $("m-mode").innerHTML = modeCell(d.mode);
    $("m-pass").innerHTML = passCell(d.pass);
    // No wall-clock stamp beside sim-time readouts (SCREEN_REVIEW §1).
    $("foot").textContent = failed
      ? T("This page lost contact with its server; the status shown may be out of date.")
      : T("Status refreshed every few seconds.");
  }
  // A local SpaceCDF may answer on the dev port instead of 8000.
  const boot = JSON.parse(($("pt-boot") || {}).textContent || "{}");
  if (!boot.domain && sv.design && sv.design.port) {
    const a = $("row-design");
    if (a) {
      const u = new URL(a.href); u.port = String(sv.design.port);
      a.href = u.toString();
    }
  }
}
async function poll() {
  try {
    const r = await fetch("/api/status", { cache: "no-store" });
    if (!r.ok) throw new Error(String(r.status));
    last = await r.json(); failed = false;
  } catch (e) { failed = true; }
  paint();
}
let timer = null;
function schedule() {
  clearInterval(timer);
  if (document.visibilityState === "visible") timer = setInterval(poll, 10000);
}
document.addEventListener("visibilitychange", () => { if (document.visibilityState === "visible") poll(); schedule(); });
window.addEventListener("smo:i18nready", paint);
window.addEventListener("smo:langchange", paint);
poll(); schedule();
</script>"""


# ── App ───────────────────────────────────────────────────────────────

def status_for(snap: dict, *, instructor: bool, local: bool) -> dict:
    """The status feed as one viewer may see it. A student never receives
    the instructor tools' entries (the feed, not only the page, SCREEN_REVIEW
    #17), and nobody receives port numbers or the server's wall-clock stamp,
    except the local SpaceCDF port the page needs to find a dev server."""
    keep = {s.key for s in visible_services(instructor)}
    services = {}
    for k, v in (snap.get("services") or {}).items():
        if k not in keep:
            continue
        v = {kk: vv for kk, vv in v.items() if kk != "port"}
        if k == "design" and local and (snap["services"][k] or {}).get("port"):
            v["port"] = snap["services"][k]["port"]
        services[k] = v
    out = {k: v for k, v in snap.items() if k not in ("services", "checked_at")}
    out["services"] = services
    return out


def _request_host(request) -> str | None:
    return request.url.host or None


def create_app(cfg: Config | None = None, prober: Prober | None = None) -> web.Application:
    from smo_common.web.http import setup_tool_app, tool_html_response
    cfg = cfg or Config.from_env()
    app = setup_tool_app(web.Application())
    prober = prober or Prober(cfg)
    # Participant logbook (LOGBOOK_SPEC.md): the welcome page has the button
    # too, so a participant can download before leaving.
    from smo_common.logbook import register_logbook_routes
    register_logbook_routes(app, tool="portal")

    def _instructor(request) -> bool:
        from smo_common.web.identity import is_instructor
        return is_instructor(request.headers, behind_iap=bool(cfg.domain))

    async def index(request):
        lang = (request.query.get("lang") or "en").strip().lower()[:2]
        page = build_page(cfg, request_host=_request_host(request),
                          user=iap_user(request.headers), lang="fr" if lang == "fr" else "en",
                          instructor=_instructor(request))
        return tool_html_response(page, app)

    async def status(request):
        return web.json_response(status_for(await prober.snapshot(),
                                             instructor=_instructor(request),
                                             local=not cfg.domain),
                                 headers={"Cache-Control": "no-store"})

    async def healthz(request):
        return web.json_response({"ok": True})

    async def _close(_app):
        await prober.close()

    app.router.add_get("/", index)
    app.router.add_get("/api/status", status)
    app.router.add_get("/healthz", healthz)
    app.on_cleanup.append(_close)
    return app


def main():
    ap = argparse.ArgumentParser(description="C2O welcome page")
    ap.add_argument("--port", type=int, default=int(os.environ.get("SMO_PORTAL_PORT", DEFAULT_PORT)))
    ap.add_argument("--host", default=os.environ.get("SMO_BIND", "127.0.0.1"))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [portal] %(message)s")
    cfg = Config.from_env()
    logger.info("Welcome page on %s:%d (%s links)", args.host, args.port,
                cfg.domain or "local")
    web.run_app(create_app(cfg), host=args.host, port=args.port, print=None)


if __name__ == "__main__":
    main()
