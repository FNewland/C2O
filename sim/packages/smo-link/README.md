# smo-link: space link for the SMO suite

`smo-link` lets the simulator run anywhere (a laptop behind NAT or a cloud
container) while MCS, planner, rfsim and the tools run on a ground host. The two
sides are joined by **one outbound WebSocket**. No other package changes.
The binding spec is `docs/web_2026-10/LINK_DESIGN.md`.

| Process | Side | Role |
|---|---|---|
| **agent** (`python -m smo_link.agent`) | space | Client of the sim's loopback TM 8002 / TC 8001 / HTTP 8080; dials the GSG |
| **GSG** (`python -m smo_link.gateway`) | ground | Impersonates the sim on the ground host (TM 8002, TC 8001, HTTP 8080) and accepts the agent on `/link` (9100) |

What crosses the link: TM (byte-identical, in order, resumable), TC (at most
once, never replayed, never older than its 5 s time-to-live), the sim's
`/api/state` at 1 Hz, S15 dump files, and an allowlist of instructor
HTTP/WebSocket routes proxied to the sim's port 8080.

Wire protocol **v2** (after the 2026-10-29 security review,
`docs/web_2026-10/LINK_REVIEW_RESPONSE.md`): both ends prove the session
secret to each other, and every frame carries a MAC. A v1 agent or GSG is
refused, so upgrade both ends together.

## Run

```bash
# once: issue a session id and secret (env-file lines)
python -m smo_link.token new > link.env        # SMO_LINK_SESSION=..., SMO_LINK_SECRET=...

# ground host
set -a; . ./link.env; set +a
SMO_DUMP_DIR=/srv/smo/dumps python -m smo_link.gateway
# then MCS / planner / rfsim exactly as today (they find "the sim" on 127.0.0.1)

# space host (simulator bound to loopback first)
SMO_BIND=127.0.0.1 python -m smo_simulator.server --config configs/eosat1/ --no-vr &
set -a; . ./link.env; set +a
SMO_LINK_URL=wss://link.example.ca/link python -m smo_link.agent
```

Console scripts when installed: `smo-link-agent`, `smo-link-gateway`,
`smo-link-token`. `python -m smo_link agent|gateway|token` also works.
Every environment variable has a CLI flag of the same meaning, and the flag
wins (for example `--sim-http-port`, `--link-port`, `--allowed-origins`).

## Environment

**Agent:** `SMO_LINK_URL` (required), `SMO_LINK_SESSION` (required),
`SMO_LINK_SECRET` or `SMO_LINK_SECRET_FILE`, `SMO_SIM_HOST` (127.0.0.1),
`SMO_SIM_TM_PORT` (8002), `SMO_SIM_TC_PORT` (8001), `SMO_SIM_HTTP_PORT` (8080),
`SMO_CONFIG_DIR` (configs/eosat1), `SMO_LINK_MODE` (`complete` | `timely`),
`SMO_LINK_STATE_DIR` (workspace/link; holds `dumps_acked.json`),
`SMO_LINK_ALLOW_INSECURE` (`1` permits plaintext `ws://` to a non-private
host; refused by default).

**GSG:** `SMO_GSG_BIND` (127.0.0.1), `SMO_GSG_HTTP_BIND` (default: the
`SMO_GSG_BIND` value), `SMO_GSG_TM_PORT` (8002),
`SMO_GSG_TC_PORT` (8001), `SMO_GSG_HTTP_PORT` (8080), `SMO_GSG_LINK_BIND`
(0.0.0.0), `SMO_GSG_LINK_PORT` (9100), `SMO_LINK_SESSION`, `SMO_LINK_SECRET`
or `SMO_LINK_SECRET_FILE`, `SMO_DUMP_DIR` (else mission `dump_dir`, else
workspace/dumps), `SMO_CONFIG_DIR`, `SMO_GSG_ALLOWED_ORIGINS` (comma list;
empty = same host only; their host names are also accepted as `Host`),
`SMO_GSG_ALLOWED_HOSTS` (extra `Host` names for the instructor proxy),
`SMO_LINK_TC_TTL_S` (5). Both accept `SMO_LOG_LEVEL`.

## GSG endpoints (ground host)

| Port | Path | Behaviour |
|---|---|---|
| 8002 | TCP | TM fan-out. Open from start; clients are never dropped (drop-oldest queue of 5000 packets / 8 MiB each) |
| 8001 | TCP | TC ingress. While the link is DOWN, or silent for 15 s (DEGRADED), clients are reset (RST) and new connects are reset at once, so the MCS reports `503 No TC connection`. Every close the GSG initiates is an RST, including on supersede and shutdown. A TC that waited more than `SMO_LINK_TC_TTL_S` in the link queue is discarded and reported (`code=tc-expired`) |
| 8080 | `/api/state` | Last STATE re-timed to now (`sim_time`, `met_s`, eclipse countdowns); **503** when older than 5 s |
| 8080 | `/healthz`, `/link-status` | Liveness (always 200) and JSON link state (UP / DEGRADED / DOWN, rtt, offset, counters) |
| 8080 | allowlisted routes | Proxied to the sim over the link (HTTP and WebSocket): the instructor console (`/`, `/classic`, `/modern`, `/static/**`, its `/api/...` reads, `POST /api/command` and `/api/breakpoint/{save,load}`), `/ws`, and the read-only dump/report views. **Everything else is 403**, including `/config*`, `/api/config*` and `POST /api/reports/{validate,generate}`. Request and response headers are allowlisted (no cookies or credentials cross; no `Set-Cookie` comes back) and a CSP plus `nosniff` are added |
| 9100 | `/link` | Agent WebSocket (upgrade header, then mutual challenge-response, then a MAC on every frame; one bound agent; a new one supersedes the old with close 4000). An unauthenticated connection has 10 s to finish the handshake |

Dumps land in `SMO_DUMP_DIR` as `.part-<name>`, are checked against sha256,
then renamed atomically and given the sim's mtime. Interrupted transfers resume.

## Security notes

- **Authentication.** The secret is at least 32 bytes (`smo_link.token new`).
  1. The upgrade carries `Authorization: SMO-Link v=2, session, ts, nonce, sig`, an HMAC-SHA256 over the session secret. The GSG answers **401** for a malformed header, a bad signature, a timestamp more than 120 s off, or a replayed nonce (10 min cache). This is only a cheap filter.
  2. Inside the WebSocket the GSG sends a 32-byte challenge, the agent answers with its own nonce and an HMAC, and the GSG proves the secret back. A GSG without the secret gets nothing: no HELLO, no TC, no proxy traffic. A captured header is useless without the secret.
  3. Every later frame carries a 16-byte HMAC-SHA256 tag under per-direction keys derived from both nonces, with an implicit frame counter. A forged, replayed, dropped or reordered frame closes the link (4403), and the GSG resets its TC clients.
- **Confidentiality** comes only from TLS (`wss://`) up to the load balancer. The LB→GSG hop inside the VPC can read frames but cannot forge them. The agent refuses `ws://` unless the host is a loopback/RFC 1918/ULA literal, or `SMO_LINK_ALLOW_INSECURE=1` is set (logged loudly).
- Keep the secret in a file (`SMO_LINK_SECRET_FILE`, mode 600). `--secret` on the command line works but logs a warning. Secrets are never logged.
- If the strict config bind set (`confighash.py`: HK structures, parameters,
  TC and event catalogues, memory map, S12/S19, `ttc.yaml`, `orbit.yaml`, the
  identity subset of `mission.yaml`) differs, the GSG sends REJECT and closes
  with 4409. Warn-set differences bind with a NOTICE.
- TM, TC and HTTP bind 127.0.0.1 by default. Docker publishes the ground
  ports on `${SMO_PUBLISH_ADDR:-127.0.0.1}`; on GCP set the VM's internal IP
  and keep the firewall to the LB ranges and IAP. Expose `/link` only through
  the TLS-terminating load balancer (`wss://`). Browsers should reach the
  proxied console only through the authenticated edge, on its own host name.
  The proxy checks `Host` (DNS rebinding) and `Origin` before rewriting it.
- The link port caps unauthenticated connections (64 total, 16 per address,
  120 new per address per minute) and aborts any that has not finished the
  handshake 10 s after connecting. Auth-failure logs are rate-limited.
- TC is never queued across a link loss: anything pending is discarded and
  reported (`event=notice code=tc-discarded`). No TC older than
  `SMO_LINK_TC_TTL_S` reaches the simulator (the GSG checks its queue and the
  agent checks the GSG's stamp), and the agent writes only whole records.
- Dumps: at most 64 MiB each and 256 MiB of partial files in total, and never
  below 256 MiB free disk. A refused or failed dump fails that transfer only;
  the agent backs off on that name.

## Troubleshooting

| Symptom | Check |
|---|---|
| Agent logs `link_handshake_failed status=401` | Session id or secret differ between the two sides, or a clock is more than 120 s off (run NTP), or one side still runs protocol v1 |
| Agent logs `link_gsg_auth_failed` | The GSG did not prove the secret: wrong secret on the ground, or not your GSG at all (check `SMO_LINK_URL` and DNS) |
| Agent exits with `refusing plaintext ws://` | Use `wss://`, a private IP literal, or set `SMO_LINK_ALLOW_INSECURE=1` deliberately |
| GSG logs `frame_rejected` / close 4403 | A frame failed its MAC: something on the path altered or injected traffic (or a bug). The link reconnects by itself |
| `code=tc-expired` in logs | A TC waited longer than `SMO_LINK_TC_TTL_S`: the link was stalled; the TC was not executed |
| Agent logs `link_rejected code=config-mismatch files=...` | The named config files differ; deploy the same `configs/` on both hosts |
| GSG `/api/state` gives 503 | Link is DOWN or the agent cannot reach the sim's `/api/state` (see `/link-status` `last_state_age`) |
| MCS says `No TC connection` | Expected while the link is DOWN; it reconnects by itself once UP |
| rfsim gets no TM | Start rfsim **after** the GSG TM port is open (it never reconnects) |
| `tm_frames_lost` / `tm_gap` in logs | The agent's TM buffer overflowed during a long outage; raise the bounds or use `complete` mode |
| Instructor page 403 on POST | `Origin` not allowed: set `SMO_GSG_ALLOWED_ORIGINS` to the public console origin |
| Instructor proxy 403 `host not allowed` | Browsing by a host name the GSG does not know: add it to `SMO_GSG_ALLOWED_ORIGINS` (or `SMO_GSG_ALLOWED_HOSTS`) |
| Instructor proxy 403 `route not on the space-link allowlist` | That sim route is not proxied on purpose (config editor, report generation). A new instructor route must be added to `httpproxy.py` |

Logs are `key=value` lines on stdout (`event=link_up`, `event=link_down`, ...).

## Tests

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/smo-rfsim/src:packages/smo-link/src \
  python -m pytest -p no:cacheprovider -q tests/test_link --timeout=180
# only the end-to-end stack (real sim, agent, fault proxy, GSG, MCS, planner; ~30 s):
#   ... -m link_e2e        skip it:  ... -m "not link_e2e"
```

`tests/test_link/test_e2e.py` runs the real `SimulatorServer` ⇄ agent ⇄
`faultproxy.py` (200 ms ±50 ms one-way, cut/restore, blackhole, bandwidth
cap) ⇄ GSG ⇄ real `MCSServer` + planner (subprocess), all on free loopback ports,
and checks TM byte equality, TC → S1.1/S1.7, clock tracking at ×60, link cut
(MCS 503, GSG `/api/state` 503, TM clients kept), resume with no duplicate or
missing TM, at-most-once TC, S15 dump delivery, the instructor proxy
(including both consoles in headless Chromium with zero CSP violations, when
Playwright is installed), supersede and a wrong secret.
`tests/test_link/test_security.py` has the regression tests for every
finding of the security review: forged, replayed and injected frames, a rogue
GSG, a replayed header after a restart, RST on supersede, dead link and
shutdown, route and header bypasses, handler-error isolation, credit, dump
and fan-out bounds, half-open floods, TC TTL and DEGRADED.

## Two-terminal demo

`start.sh` runs either half of the split: `SMO_PROFILE=ground` (GSG + MCS +
planner + ground tools) and `SMO_PROFILE=space` (simulator + agent). It
installs smo-link itself the first time.

**Credentials.** On its first run the ground profile creates
`workspace/link/session.env` (mode 600, git-ignored) holding a new session id
and secret, and both profiles read that file when `SMO_LINK_SESSION` /
`SMO_LINK_SECRET` are not set. The simulator side needs the **same** file:
copy it to `workspace/link/` in the checkout there. Delete it to issue new
credentials (then copy it again). `python -m smo_link.token new` still prints
a fresh pair if you prefer environment variables or a secrets manager.

**One machine** (to try it out — verified 2026-10-29):

```bash
# terminal 1
SMO_PROFILE=ground ./start.sh --same-host
# terminal 2
SMO_PROFILE=space ./start.sh --same-host
```

`--same-host` moves the ground side's stand-in simulator ports to
18001/18002/18080 (the real simulator keeps 8001/8002/8080) and points the
agent at `ws://127.0.0.1:9100/link`. Open the MCS at <http://localhost:9090>,
the planner at <http://localhost:9091>, the simulator's own instructor
console at <http://localhost:8080> and the same console *through the link* at
<http://localhost:18080>.

**Two hosts** (simulator laptop → ground server):

```bash
# ground server (first run creates workspace/link/session.env)
SMO_PROFILE=ground ./start.sh
# copy workspace/link/session.env to the laptop's checkout, then on the laptop:
SMO_LINK_URL=wss://<ground-host>/link SMO_PROFILE=space ./start.sh
```

The agent accepts plaintext `ws://` only to a loopback or private-network
**IP address** (e.g. `ws://192.168.1.20:9100/link` on a home LAN); anything
else must be `wss://` through the TLS load balancer (`deploy/gcp/README.md`).

Check it from the ground side (ports as with `--same-host`; drop the leading
`1` from 18080 on a two-host setup):

```bash
curl -s localhost:18080/link-status                 # "state": "UP"
curl -s localhost:9090/api/state | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["stale"], d["param_count"])'
                                                    # False, >0 — but only during a ground-station pass
curl -s -X POST localhost:9090/api/pus-command -H 'Content-Type: application/json' \
     -d '{"service":17,"subtype":1,"position":"flight_director"}'
curl -s localhost:9090/api/verification-log         # COMPLETED if sent during a pass
curl -s -o /dev/null -w '%{http_code}\n' localhost:18080/          # 200: instructor page via the link
curl -s -o /dev/null -w '%{http_code}\n' localhost:18080/config    # 403: never proxied
```

Telemetry flows only while EO-Sat-1 is over a ground station, exactly as with
everything on one host; speed the simulator up from the instructor console to
reach a pass. Ctrl+C in each terminal stops it. Until the agent binds, the
ground side shows the link DOWN and the MCS logs repeated TC reconnects
(expected).
