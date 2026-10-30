# Web deployment: current state survey (SMO suite + SpaceCDF)

Survey date 2026-10-28. Read-only. All paths are relative to `/home/claude/work/smo` (SMO)
or `/home/claude/work/cdf` (CDF) unless stated. `file:line` citations refer to the working copies.

Target being prepared for:
(a) SMO: **simulator on a laptop/any host**; MCS, planner (+wall display), instructor console and RF pages
on a **cloud server**, reachable over the web by remote operators who talk on **voice loops**.
(b) SpaceCDF: users **join a running instance** or **start their own**.

---

## 0. Headline findings

1. **Every SMO inter-process link is "ground connects to simulator".** MCS, gateway, RF bridge and
   planner all open TCP/HTTP/WS connections *to* the simulator host
   (`smo-mcs/.../server.py:1604-1631`, `smo-gateway/.../gateway.py:35`, `smo-rfsim/.../bridge.py:135,246,644`,
   `smo-planner/.../server.py:585`). A simulator on a laptop behind NAT cannot be reached from a cloud
   server without a tunnel or a new sim-initiated (outbound) uplink. Nothing in the tree is
   sim-initiated.
2. **The cloud MCS needs four separate channels to the simulator**, not just TM/TC: TM TCP 8002,
   TC TCP 8001 (a second socket on the same host, `server.py:1604-1612`), and HTTP `GET /api/state`
   on 8080 every 1.5 s for clock sync and sim-mode ground truth (`server.py:2033-2077`). The planner also
   polls 8080 (`smo-planner/.../server.py:575-588`). In RF mode the bridge additionally needs the sim's
   WebSocket `ws://…:8080/ws` (`configs/eosat1/rfsim.yaml:135`).
3. **The instructor console and the read-write config editor live inside the simulator process** (port
   8080, `smo-simulator/.../instructor/app.py:66-158`). To run the instructor console in the cloud, either
   8080 has to be reverse-tunnelled from the laptop, or the instructor surface has to be split out of the
   simulator.
4. **`smo-gateway` does not relay TCs.** It connects upstream to the sim's TM port only
   (`deploy/smo-env.conf:42-43`) and writes TCs into that socket (`gateway.py:64-67`). The simulator's
   TM handler never reads inbound bytes (`smo-simulator/.../server.py:132-147`). The MCS ignores the
   gateway for TCs anyway: it sends them to `connect_host:8001`, i.e. to port 8001 *on the gateway host*
   (`smo-mcs/.../server.py:1608-1609`, `5519`). TCs only work when the gateway shares a host with the
   simulator, and then only by accident. There is no TLS, auth or reconnect (upstream loss ends the relay,
   `gateway.py:81-83`).
5. **The suite has no authentication anywhere** (documented, `docs/DEPLOYMENT.md:166-167`). Command
   authority is decided by the browser: the operator's position is a **self-declared** field in the request
   body or WS query string. The default is `flight_director` (allowed "all"), and **an unknown position name
   is allowed by default** (`smo-mcs/.../server.py:959, 986-989`).
6. **There is no voice loop, chat panel or second-key interlock in the code.** The only collaboration
   features are an append-only console log (REST, polled), GO/NO-GO polls (WS broadcast) and a handover log.
   The project's own errata already records that the ops book's §7.1 describes features that do not exist
   (`docs/i18n/ENGLISH_ERRATA.md:1557`).
7. **SpaceCDF is a single-process, single-tenant app.** Collaboration state (WS rooms, edit locks, live
   sessions) lives in module-level dicts (`routers/ws.py:48-67`, `services/session_manager.py:47-52`).
   Identity is a self-declared query parameter, and there is no auth. Redis is declared but unused. The
   compose file is a dev setup (`--reload`, hard-coded Postgres password, DB and Redis ports published). The
   production frontend (`frontend/dist`) is served by nothing. **One multi-user bug leaks API keys:** a user
   who sends `X-API-Key` replaces the process-wide Anthropic client, so later users' requests are billed to
   that key (`packages/spacecdf-ai/.../client.py:84-85, 96-97`).

---

## 1. SMO process topology

### 1.1 Processes launched by `start.sh`

| # | Process | Launch (start.sh) | Listens | Bind |
|---|---|---|---|---|
| 1 | `smo-simulator` | `:230` | TC **8001**/tcp, TM **8002**/tcp, HTTP+WS **8080** (`$SMO_SIM_HTTP_PORT`), VR **8100**/tcp NDJSON + **8101**/ws | `$SMO_BIND` (127.0.0.1 default, 0.0.0.0 with `--public`, `start.sh:98-103`) |
| 2 | `smo-rfsim` bridge (only `--rf`) | `:266-277` | MCS-TM **8012**, MCS-TC **8011** (`mcs_bind` from rfsim.yaml, default 0.0.0.0), radio web **8094** (always 0.0.0.0, `bridge.py:966` passes no host), ZMQ PUB **5555** (`tcp://*`, `pipeline/channel_stage.py:86-90`) | see column |
| 3 | `smo-mcs` | `:288` (RF) / `:291` (direct) | HTTP+WS **9090** | `$SMO_BIND` |
| 4 | `smo-planner` | `:299` | HTTP **9091** (`/`, `/wide`) | `$SMO_BIND` |
| 5 | `tools/delayed_tm_viewer.py` | `:306` | **8092** | 127.0.0.1 / 0.0.0.0 with `--public` |
| 6 | `tools/orbit_tools.py` | `:312` | **8093** | always 0.0.0.0 (`tools/orbit_tools.py:850`) |
| 7 | `tools/doc_viewer.py` | `:338` | **8095** | always 0.0.0.0 (`tools/doc_viewer.py:373`) |
| 8 | `tools/scenario_generator.py` | `:343` | **8096** | localhost / 0.0.0.0 with `--public` |
| 9 | `tools/adcs_sim_viewer.py` | `:349` | **8097** | 127.0.0.1 / 0.0.0.0 with `--public` |

`deploy/start-all.sh` launches the same set (`:144-236`) plus the optional gateway on **10025** (`:158-168`).

### 1.2 Inter-process links

Framing for all TM/TC sockets: **2-byte big-endian length prefix + raw CCSDS/ECSS PUS packet**
(`smo-common/.../protocol/framing.py:13-34`). There is no CLTU/TF framing except inside the RF bridge.
The sockets carry no handshake, no auth and no TLS.

| Link | Dir | Transport | Client → Server | Data | Host/port control |
|---|---|---|---|---|---|
| L1 TM downlink | sim→MCS | TCP, len-prefixed PUS TM | MCS → sim:8002 | All TM, fanned out to every TM client; per-client `drain` timeout 2 s, sequential (`smo-simulator/.../server.py:149-170`) | MCS `--connect host:port` (`smo-mcs/.../server.py:5490`), deploy `MCS_TM_HOST/PORT`. **Sim ports hard-coded 8001/8002** (`smo-simulator/.../server.py:275`); `mission.yaml network.tc_port/tm_port` (`configs/eosat1/mission.yaml:50-51`) and `SIMULATOR_TC_PORT` (`deploy/smo-env.conf:21`) are read by nobody |
| L2 TC uplink | MCS→sim | TCP, len-prefixed PUS TC | MCS → **same host as `--connect`** : `--tc-port` (default 8001) (`smo-mcs/.../server.py:1604-1612, 5519`) | TCs from `/api/pus-command`, procedures, S11 uploads, TM-dump buttons, all serialized by `_tc_send_lock`; sim pushes into `engine.tc_queue` (`smo-simulator/.../server.py:114-130`) | `--tc-port`. TC host cannot be set apart from the TM host |
| L3 Sim clock + ground-truth poll | MCS→sim | HTTP GET JSON, every 1.5 s, 2 s timeout | MCS → `SMO_SIM_STATE_URL` (default `http://<connect_host>:$SMO_SIM_HTTP_PORT/api/state`) (`smo-mcs/.../server.py:216-223, 2033-2077`) | `sim_time`, `speed`, `hk_enabled`, health, orbit elset (post-burn), illumination (sim mode only) | `--sim-state-url` > `SMO_SIM_STATE_URL` > `mission.yaml sim_state_url` > default. start.sh exports it (`:226`). **deploy/start-mcs.sh does not set it**, so with a gateway the default resolves to the *gateway* host:8080 |
| L4 Planner sim poll | planner→sim | HTTP GET via **blocking `urllib`**, 1.5 s timeout, at most ~1/s, inside async handlers (`smo-planner/.../server.py:575-588, 752`, 15 `_get_now()` call sites) | planner → `sim_state_url` (default `http://<connect_host>:8080/api/state`, **8080 hard-coded**, `:130`) | sim_time/speed, elset, illumination | `--connect-host`, `--sim-state-url`, `SMO_SIM_STATE_URL`, `planner.yaml time.sim_state_url`. **deploy/start-planner.sh passes none** (`:57-60`) |
| L5 MCS→planner | MCS→planner | HTTP | MCS → `SMO_PLANNER_URL` (default `http://<connect_host>:9091`, `smo-mcs/.../server.py:600-602`) | `/api/contacts` server-side proxy (`:5006, 5338`) | `SMO_PLANNER_URL` (deploy sets from `PLANNER_REACHABLE_HOST`, `deploy/start-all.sh:174-176`; start.sh does not set it) |
| L6 Planner→MCS | planner→MCS | HTTP POST | planner → `SMO_MCS_URL` (default `http://localhost:9090`, `smo-planner/.../server.py:264`) | Activity upload: `/api/procedure/load` (immediate) or `/api/schedule/upload-s11` (`:1308-1322`) | `SMO_MCS_URL` |
| L7 Browser→planner direct | browser→planner | **Cross-origin** fetch from the MCS page | MCS page → `client_config.planner_url` (`smo-mcs/.../static/modern/mcs.js:574-578, 1849-1856`; classic `static/index.html:8264`) | `/api/time-source`, `/api/schedule` (burn plan) | Same `planner_url` as L5, so it must also resolve from the **browser's** point of view. **No CORS headers anywhere in SMO** (grep finds none), so it fails even when reachable. The code treats this as a "designed absent state" |
| L8 Wall display→MCS/rfsim | browser→MCS, rfsim | Cross-origin fetch | `/wide` → `services.mcs_url`/`rfsim_url` (`smo-planner/.../static/modern/wide.js:184-200`) | MCS `/api/state.derived`, rfsim pass roll-ups | `planner.yaml` services (`smo-planner/.../planner_config.py:151`). Same CORS problem |
| L9 RF bridge sim side | bridge→sim | TCP TM (8002), TCP TC (8001), **WS `ws://127.0.0.1:8080/ws`** (instructor state stream for link feedback) | bridge → sim (`bridge.py:135, 246, 633-660`) | TM in, TC out, sim state feedback | `configs/eosat1/rfsim.yaml:131-135` (all 127.0.0.1) |
| L10 RF bridge MCS side | MCS→bridge | TCP len-prefixed (after RF/frame impairments) | MCS → bridge:8012 (TM), :8011 (TC) | as L1/L2 | `start.sh:288` `--connect …:8012 --tc-port 8011`; `rfsim.yaml:137-139` |
| L11 IQ samples | bridge→SDR tools | ZMQ PUB | external SUB → :5555 | baseband samples | `rfsim.yaml:143` |
| L12 VR feed | sim→headsets | TCP NDJSON 8100 / WS 8101 `/vr` | headset → sim | `hello`+`state` ~1 Hz (≤10 Hz); clients may send `status` lines ≤4096 B (`docs/VR_INTERFACE_ICD.md:29-56, 162`) | `--vr-port/--vr-ws-port`, `SMO_VR*`, `mission.yaml network.vr_*` (`smo-simulator/.../server.py:234-262`) |
| L13 Gateway (deploy only) | sim↔gateway↔N MCS | TCP len-prefixed | gateway → sim:8002 upstream; MCS → gateway:10025 | TM fan-out works; **TC path broken** (see §2) | `deploy/smo-env.conf:34-43` |
| L14 Delayed-TM store | sim→(MCS, viewer) | **Shared filesystem** | — | S15 dumps `dump_sid*.bin` written by the sim (`smo-simulator/.../engine.py:3469`), read by MCS `/dumps` and viewer 8092 | `SMO_DUMP_DIR` > `mission.yaml dump_dir` > `workspace/dumps` (`docs/DEPLOYMENT.md:226-233`; `start.sh:81-82`). The viewer also has an HTTP `--api` mode (`DEPLOYMENT.md:276-285`) |

### 1.3 ASCII diagram (start.sh, `--rf` shown dashed)

```
                       ┌──────────────────────── Browsers ─────────────────────────┐
                       │ MCS page        Planner / /wide      Instructor   Radio    │
                       │ WS /ws?position= REST polling 1-10 s  WS /ws       WS /ws   │
                       └──┬──────────┬───────────┬────────────────┬───────────┬─────┘
                  HTTP+WS │ cross-   │ HTTP      │ cross-origin   │ HTTP+WS   │ HTTP+WS
                          │ origin L7│           │ L8             │           │
                    ┌─────▼────┐     └──►┌───────▼─────┐          │      ┌────▼──────┐
                    │ smo-mcs  │◄──L6────│ smo-planner │          │      │ rfsim web │
                    │  :9090   │──L5────►│   :9091     │          │      │  :8094    │
                    │ SQLite   │         └──────┬──────┘          │      └────┬──────┘
                    │ archive  │                │L4 HTTP /api/state│           │
                    └┬───┬───┬─┘                │ (blocking)       │      ┌────┴──────────┐
         L1 TM 8002  │   │L2 │L3 HTTP /api/state│                  │      │ smo-rfsim     │
     (or 8012 via RF)│   │TC │ every 1.5 s      │                  │ ┌ ─ ┤ bridge        │
                     │   │   │                  │                  │      │ 8011/8012     │
                     │   │   │                  │                  │ │    │ ZMQ :5555 ──► SDR
                     ▼   ▼   ▼                  ▼                  ▼      └─┬───┬────┬────┘
                  ┌─────────────────────────────────────────────────────┐ │ L9 TM/TC  WS :8080/ws
                  │ smo-simulator   TC:8001  TM:8002  HTTP/WS:8080       │◄┘ (sim side)
                  │  engine + instructor console + /config (READ-WRITE)  │
                  │  + /dumps + /reports + breakpoints                   │
                  │  VR bridge TCP:8100 WS:8101 ───────────────────────────► headsets (L12)
                  └──────────┬──────────────────────────────────────────┘
                             │ writes  workspace/dumps/*.bin  (L14, shared FS)
                             ▼
                 MCS /dumps, delayed_tm_viewer :8092 read the same directory
```

### 1.4 Things that assume localhost or one shared filesystem

| Artefact / assumption | Writer → reader | Evidence |
|---|---|---|
| `configs/eosat1/` read by **every** process at start-up (HK structures, parameters, positions, displays, TLE, staleness). MCS decodes HK with `hk_structures.yaml`, so a config mismatch between sim and cloud MCS **silently mis-decodes TM** | all | `smo-mcs/.../server.py:240-246` (decode only from TM via hk_structures); `start.sh:230-299` all `--config configs/eosat1/` |
| Config editor writes `configs/` + shadow git `workspace/config-history/` on the **sim host only**. MCS/planner read-only views read their *own* copy | sim → (none) | `instructor/app.py:114-136`, `confedit/api.py:240-259`, `DEPLOYMENT.md:302` |
| Delayed-TM dumps | sim → MCS/viewer | `DEPLOYMENT.md:226-233, 351-363` (shape C) |
| TM archive SQLite `configs/../data/tm_archive.db` (`SMO_TM_ARCHIVE` relocates; network FS warned) | MCS only | `smo-mcs/.../server.py:500-517` |
| Custom procedures written into `configs/eosat1/procedures/custom/` | MCS host | `smo-mcs/.../server.py:4277-4291` |
| Scenario YAML written by 8096 into `configs/eosat1/scenarios/`, read by sim | tool host → sim | `tools/scenario_generator.py:1036-1043`; `DEPLOYMENT.md:304` |
| Breakpoints `workspace/breakpoints/*.json` | sim | `smo-simulator/.../breakpoints.py:152` |
| Reports `workspace/reports/` | whichever host generates | `smo-common/.../reporting/generate.py:196` |
| `rfsim.yaml` sim endpoints all `127.0.0.1` | bridge | `configs/eosat1/rfsim.yaml:131-135` |
| Defaults `localhost`: MCS TM `localhost:8002`, planner `connect_host=localhost`, `SMO_MCS_URL=http://localhost:9090`, `SMO_RFSIM_URL=http://localhost:8094` | various | `smo-mcs/.../server.py:5490`; `smo-planner/.../server.py:264, 1761`; `smo-common/.../reporting/render_html.py:730` |
| Planner and scenario state in memory only (schedule, debriefs) | — | `DEPLOYMENT.md:305`; no planner writes found |
| Logs to stdout only | — | `DEPLOYMENT.md:310` |

---

## 2. smo-gateway (deploy-only relay)

- **Code:** 3 files, about 240 lines (`packages/smo-gateway/src/smo_gateway/`). `gateway.py` is the only one used. `upstream.py` and
  `downstream.py` are unused helper classes.
- **What it does:** opens **one** upstream TCP connection (`gateway.py:35-36`), listens on
  `0.0.0.0:10025` (`:40-41`), fans every upstream frame out to all downstream clients (`:76-102`), and
  forwards any frame a downstream client sends to the same upstream socket (`:59-67`).
- **Protocol:** the same 2-byte length-prefixed PUS packets (framing.py). Transparent: no TC arbitration,
  no client identity, no authority, no buffering or replay for late joiners, no TLS, no auth.
- **How deploy/ uses it:** `USE_GATEWAY="yes"` (`deploy/smo-env.conf:34`). Upstream defaults to the
  **simulator TM port 8002** (`:42-43`, `deploy/start-gateway.sh:175-176`). MCS gets `--connect
  GATEWAY_HOST:10025` (`deploy/start-all.sh:168`, `deploy/start-mcs.sh:44-46`) and no `--tc-port`.
- **Defects found:**
  1. **TC relay is non-functional.** Gateway TCs go into the sim's TM socket, whose handler only sleeps and
     checks `is_closing` and never reads (`smo-simulator/.../server.py:132-147`).
  2. The MCS does not send TCs through the gateway anyway: TC goes to `GATEWAY_HOST:8001`
     (`smo-mcs/.../server.py:1608`). That reaches the sim only if the gateway is co-located with it.
  3. Upstream loss ends `_relay_tm_downstream` permanently, and `start()` does not reconnect (`gateway.py:81-83`).
  4. The sim-state poll (L3) default follows `connect_host`, so with a gateway it points at
     `GATEWAY_HOST:8080`, where nothing is listening. In sim mode the MCS clock then free-runs on the last anchor.
- **Docker/compose:** none in SMO (no `Dockerfile`, `docker-compose*`, or systemd units found).
- **`docs/DEPLOYMENT.md`** (401 lines) covers three shapes: A single machine, B server + browsers ("the
  classroom. Use this one."), and C distributed services (`:26-34`). It also has the port table (`:40-110`), the firewall list
  (`:139-167`, *"No authentication anywhere … never on the open internet"*), `--public` (`:171-195`), the dump
  store (§4), the artefact locations table (§5), shape C caveats (`:351-363`), the classroom recipe (§7) and
  troubleshooting (§8). **There is no cloud, NAT-traversal, reverse-proxy, TLS or auth design.** No SMO doc
  mentions nginx, Caddy, Traefik or TLS in a deployment sense. `docs/architecture.md:51` lists the gateway as "for
  multi-site deployments".

---

## 3. Browser ↔ server

### 3.1 Transports per UI

| UI | Server | Transport | Evidence |
|---|---|---|---|
| MCS (modern + classic) | 9090 | **WebSocket `/ws?position=<pos>`**: full `state` JSON pushed at 1 Hz to every client (`server.py:2620-2649`), plus **one `tm` message per received TM packet** (`:2017-2031`), plus `alarm`, `alarm_cleared` and `go_nogo_*` messages. REST for everything else (62 root-relative `/api/` refs in `static/modern/mcs.js`); a couple of `setInterval` polls; console log fetched by REST (`mcs.js:1803`). WS URL built from `location.host` with `wss:` when https (`mcs.js:526-528`) | |
| Planner `/`, `/wide` | 9091 | **REST polling only**: 1 s clock, 10 s contacts/timeline (`static/modern/planner.js:258, 1385, 1396`; `wide.js:1209-1210`). No WS route (`server.py:475-522`) | |
| Instructor | 8080 (sim) | **WebSocket `/ws`**: `state_update` 1 Hz (`smo-simulator/.../server.py:172-187`), **accepts instructor commands over the same WS** (`instructor/app.py:267-297`), plus REST `/api/command` (`:75`) | |
| Radio (rfsim) | 8094 | WebSocket `/ws` + REST status. POST control routes exist but return 503 unless `--radio-control` (`radio/web_ui.py:62-67, 216-218`; `bridge.py:929-932`) | |
| Tools 8092-8097 | each | Plain HTTP pages + POST APIs | |

- **Same-origin assumptions:** all UIs use root-relative `/api/...` and `/static/...` paths, so they work behind
  a reverse proxy only **per host or subdomain**, not under a path prefix such as `/mcs/`. Exception: cross-service calls
  (L7, L8) use absolute configured URLs and therefore need CORS or a single-origin proxy.
- **CORS:** none in SMO (no `Access-Control` anywhere in `packages/` or `tools/`).
- **WS Origin checks:** none (aiohttp default), so the WebSockets are open to cross-site WebSocket hijacking.
- **Auth/session:** none. The position, language, theme and "guided" mode live in `localStorage`
  (`mcs.js:544, 4418-4430, 4946-4948`).

### 3.2 Multi-user behaviour in the MCS

- **N browsers can connect at once:** `_ws_clients` is a list of `(ws, position)` (`server.py:140, 3161-3209`).
  Each gets the same full state. Positions are **not exclusive**: two people can both be FD.
- **Command authority:** `/api/pus-command` takes `position` from the **JSON body**, defaulting to
  `flight_director` (`server.py:2959`). `_check_position_access` returns **allowed** when positions are not
  loaded or **the position is unknown** (`:984-989`). `flight_director` has `allowed_commands: "all"`
  (`configs/eosat1/mcs/positions.yaml:2-6`). Other TC paths have **no position check at all**:
  `/api/schedule/upload-s11` (`server.py:3611-`), `/api/tm-dump` (`:5032-`, logs position `"tm_dump"`),
  and the procedure runner (`:3382` checks only inside procedures).
- **No command lock or arbitration:** there is one global FIFO (`_cmd_queue`, `_tc_send_lock`, `:595-596,
  1592-1602`), **one shared `ProcedureRunner`** for all browsers (`:469`) with no owner, and global alarm acks.
- **GO/NO-GO:** `POST /api/go-nogo/poll` checks `position != "flight_director"` against a self-declared
  string (`:5187-5216`). Responses come over WS and are broadcast (`:3182-3203`).
- **Handover log, console log:** REST POST, stored in memory (handover, `:4133-4149`) or in SQLite (console
  log, `:4731-4771`, kinds `tc|ack|shelve|procedure|gonogo|mark|note`). Console-log entries are **not pushed**
  to other clients; they are fetched on demand.
- **"Blind TC" two-press arm** is a client-side UI state only (`mcs.js:1947`, "armed — second press enables
  (voice FD GO first)").

### 3.3 Voice loops, chat, second key

**Not implemented.** Grep for voice, WebRTC, getUserMedia, RTCPeer, chat, second-key, two-person and
push-to-talk across `packages/**/*.{py,js,html}` finds only UI strings telling operators to "confirm … by voice"
(`mcs.js:1852, 1865, 1947`) and propulsion "arm interlocks" (a spacecraft bitmask, not a ground two-key).
`docs/i18n/ENGLISH_ERRATA.md:1557` records the book contradiction: Ch. 6 says "There is no voice-loop chat …
There is no second-key interlock in the MCS", while §7.1 describes both. Voice-loop discipline is
treated as pedagogy (`docs/design_2026-08/POSITION_NEEDS.md:31`; callouts stay English per
`docs/i18n/PLAN.md:13`).

### 3.4 Spacecraft-agnostic constraint (applies to any new web layer)

`docs/design_2026-08/UI_DELIVERY_NOTES.md:60-80`: ground tools must work identically against a real
spacecraft. Sim-only data needs a provenance label and appears only in sim mode. The SPEED control belongs to the
instructor, and the MCS shows only a `TRAINING · SIM xN` chip. The MCS L3 back-channel is the main remaining sim
dependency, and it is guarded to sim mode (`server.py:2045-2046, 2094-2095`). **Implication:** voice loops and
presence must be ground-segment features (MCS or a separate service) and must not be routed through the simulator.

---

## 4. Time: sim vs onboard vs wall, and what network latency does

**Clocks.**
- *Sim time* is owned by the engine.
- *MCS ground clock* `sim_now()` is an open-loop anchor and extrapolation, `epoch + (wall − anchor_wall) × speed + offset`,
  re-anchored from L3 every 1.5 s (`smo-mcs/.../server.py:1085-1111, 2033-2077`). REAL mode is wall UTC.
- *Onboard time* is the OBC CUC from TM 0x0309 plus a fine field (`:1218-1233`).
- The planner keeps its own anchor from L4 (`smo-planner/.../server.py:591-640, 737-752`).
- Procedure step timeouts deliberately use `time.monotonic()` wall time (`procedure_runner.py:64-67, 563`).

**Effects of putting MCS/planner across a WAN from the sim (100 ms RTT, jitter):**

| Mechanism | Behaviour | Impact |
|---|---|---|
| L3 re-anchor ignores request latency: `sim_time` is stamped at server send, and the anchor wall time is taken at client receipt (`server.py:2058-2063`) | MCS clock lags sim by about one-way latency × speed, with jitter noise per poll | ×1: ~50 ms, negligible. ×60: ~3 s. ×100: ~5 s. Jump tolerance is `max(cfg, 4.5 s × speed)` (`:2186-2188`), so jitter will not trigger false "discontinuity" resets |
| L3 timeout 2 s, keep last anchor on failure (`:2049, 2076-2077`) | Packet loss leads to a free-running clock | Pause or speed changes are missed until the next good poll (≤1.5 s plus RTT) |
| Planner L4 is **blocking urllib in async handlers** (`smo-planner/.../server.py:584-585`, called from `_get_now()` ≤1/s) | Each refresh stalls the planner event loop for one RTT; unreachable sim → up to 1.5 s stall per second | With a WAN, all planner HTTP requests (including the wall display) see latency spikes. Must become async before going remote |
| TM receipt stamped with `sim_now()` (`server.py:1672-1681`, "RECEIVE TIMESTAMP, in SIM TIME") | Ages include the network latency | Staleness thresholds are tens of sim seconds (`configs/eosat1/mcs/staleness.yaml`), so no impact at 100 ms |
| S11 time-tag conversion `_utc_to_obc_cuc_seconds = last_0x0309 + (target − sim_now)` (`server.py:3578-3601`) | Uses the **last cached** OBC value with no correction for its age (cache entry has `last_update_ts`, unused here, `:1226-1233`) | The tag error equals HK age plus latency, multiplied by speed. This is a pre-existing bias that the WAN makes worse. Worth fixing before relying on S11 remotely |
| TC verification: `tc_manager._pending_verifications` has **no timeout** (`tc_manager.py:23, 150-170`) | Latency does not cause false timeouts | — |
| Procedure `verify`/`wait` deadlines use wall-clock monotonic time (`procedure_runner.py:556-578`) | +RTT per step. At high speed, sim progress per wall second grows, so the risk is the opposite (conditions met quickly) | Negligible at 100 ms |
| Contact windows: MCS uses its own TLE propagator and `sim_now()`; the planner uses its own anchor; the sim gates the link with its own geometry and clock | AOS/LOS display is offset from the sim's actual link by the clock lag above | ×1 negligible. At high speed, MCS shows AOS seconds late |
| MCS WS fan-out is **awaited inline in the TM receive path** (`server.py:2017-2031`) and in the state loop, with no per-client timeout | One slow remote browser back-pressures TM ingest for everyone | Needs per-client queues or timeouts before the internet |
| Sim TM fan-out drains each client sequentially with a 2 s timeout (`smo-simulator/.../server.py:156-164`) | A slow WAN TM client delays the others' TM by up to 2 s per packet | Put one relay near the sim, not N MCS across the WAN |
| Ground-time override `POST /api/ground-time {offset_s|epoch|speed}` (`server.py:2654-2676`) | Any browser can shift the shared MCS clock | Must become instructor-only |

---

## 5. SpaceCDF

### 5.1 Deployment model today

- **Backend:** FastAPI app `spacecdf_server.app:app` (`packages/spacecdf-server/.../app.py:117-168`), about 40 k lines.
  It runs as one uvicorn process. Native path: `uvicorn … --reload --port 8000` plus `npm run dev` (Vite 5173, proxying `/api` and `/ws`
  to `localhost:8000`, `frontend/vite.config.ts`; `install.sh:267-295`; `README.md:56-64`).
- **Production frontend:** `frontend/dist` exists, but **nothing serves it**. `StaticFiles` is imported but
  unused (`app.py:13`), and the Dockerfile does not build the frontend.
- **docker-compose.yml:** `postgres:16-alpine` (password `spacecdf_dev`, **5432 published**, `:7-9`),
  `redis:7-alpine` (**6379 published**, `:16`), and `server` (bind-mounted `./packages`, `--reload`, `:31-32`). It is a dev configuration.
  The Dockerfile `CMD` runs uvicorn on 0.0.0.0:8000 without `--reload` (`Dockerfile:56`), but **does not pip-install
  `spacecdf-ai`** (copied at `:38-39`, not in the install list at `:42-46`), so AI is always off in Docker.
- **DB:** `DATABASE_URL`, default `sqlite+aiosqlite:///./spacecdf.db` (**cwd-relative**), with WAL pragmas
  (`db/engine.py:23, 30-63`). Postgres via asyncpg in compose. Schema is created with `create_all` plus an additive migrator
  (`app.py:25-44`). Alembic is a dependency but no migrations were seen. Writes go through a background write queue
  (`db/write_queue.py`). There are in-memory write-through caches for elements, requirements and studies, loaded once at start-up
  (`app.py:66-85`), so **a second process would not see the first process's writes**.
- **Redis:** declared (`pyproject.toml`, compose `REDIS_URL`), but **no code references it** (grep finds no use in `packages/*/src`).
- **Other files:** analysis series are written to `$SPACECDF_DATA_DIR` (default `./data`, `services/analysis_results.py:120-139`).
  Some user artefacts live **only in browser `localStorage`**: risk register and Pugh matrix
  (`frontend/src/App.tsx:322-323`, `workbench/VVPanel.tsx:466`, `workbench/DecisionPanel.tsx:467`). They are not shared
  between collaborators and not server-side.
- **CORS:** `allow_origins=["http://localhost:5173","http://localhost:3000"]`, credentials true (`app.py:125-131`).
- **Docs:** `docs/INSTALLATION_GUIDE.md` §8.1-8.4 covers compose, Postgres ("for multi-user production
  deployments") and "Remote access via Tailscale", which points at `docs/REMOTE_ACCESS.md`. **That file does not exist**
  (not in `docs/`).

### 5.2 Collaboration and "instances"

There are two collaboration concepts, both keyed by IDs in URLs. These are the natural "connect to a running instance" handles.

- **Design session** (`/api/sessions`, WS `/ws/session/{session_id}?position_id(s)=…&display_name=…`):
  position-scoped parameter edits with ownership patterns from the positions YAML, plus convergence. Sessions are
  held in `SessionManager._sessions` in memory and persisted through the write queue; they can be listed (merging memory
  and DB) and resumed (`routers/sessions.py:29-60, 202`; `services/session_manager.py:44-60`).
  `_connections[session_id][position_id] = ws` (`routers/ws.py:48, 167-170`), so **two users claiming the same position
  overwrite each other's socket**.
- **Study workbench** (WS `/ws/study/{study_id}?name=…`, `routers/ws.py:400-432`): presence, a contributors list,
  **element edit locks** with a 30 s heartbeat expiry (`:51-107`). The room is keyed by display name, so two users named
  "Anonymous" (the default, `:404`) collide.
- **Identity:** self-declared `display_name`/`name`/`position_id`. No auth and no ownership on studies (`StudyRow` has
  no owner column; `SessionRow.owner_label` is a free string, `db/models.py:18-36`). `DELETE /api/studies/{id}`
  is open (`routers/studies.py:192`).
- **What an instance is:** one uvicorn process, one DB (SQLite file or Postgres), `configs/`
  (genai.yaml, ECSS gate files, templates), `./data/`, an optional `ANTHROPIC_API_KEY`, the frontend (dev server or a static
  build that would need a host), and optionally about 500 MB of ECSS PDFs in the repo root (`INSTALLATION_GUIDE.md:523-527`).

### 5.3 AI / LLM

- `configs/genai.yaml`: `enabled: false` master switch, provider anthropic, model names, capability toggles,
  budget (`session_token_limit: 100000`, `rate_limit_rpm: 30`). The key comes from `api_key_env: ANTHROPIC_API_KEY`
  (`packages/spacecdf-ai/.../config.py:36-44`).
- Per-request override: `X-API-Key` header (`routers/ai.py:7, 91-136`). **Bug (multi-tenant blocker):**
  `_get_client`/`_get_async_client` replace the shared cached client whenever a per-request key is passed
  (`client.py:84-85, 96-97`). Subsequent requests **without** a header then reuse that user's key, so keys leak across users.
  The frontend does not appear to send `X-API-Key` today (no match in `frontend/src`).
- Usage tracking is per session id inside the single process (`client.py:73`). There is no per-user quota.

### 5.4 Hosted multi-tenant vs per-user spawned: gap list (from the code above)

| Need | Multi-tenant hosted | Per-user spawned instance |
|---|---|---|
| Identity/auth | Must add (none today), then map users to studies/sessions and owners on rows | Can be gated at the proxy (one user per container); still need a shareable "join" link for collaborators |
| Horizontal scale | Blocked by in-process WS rooms, locks and caches (`ws.py:48-67`, `app.py:66-85`). Needs a single worker or a Redis pub/sub + DB-backed cache rewrite | Natural: one process per container |
| DB | Postgres, tenant scoping on every query (no tenant/owner columns today) | SQLite per container is fine. `./spacecdf.db` is cwd-relative, so pin it to a volume |
| AI key | Fix the client cache bug, then add per-user keys/quotas | Inject a per-container env key or BYO key |
| Frontend | Serve `dist` (not wired) and fix `useSessionSocket.ts:139`, which rewrites the WS host to **`:8000`** (breaks behind 443/TLS). `useCollaboration.ts:76-77` is already same-origin | Same frontend fixes |
| Browser-only data | Move risk register and Pugh matrix server-side to share them | Same |

---

## 6. Security exposure if put on the internet today

**SMO (all unauthenticated, no TLS):**
- **Raw TM/TC sockets 8001/8002 (and 8011/8012, 10025):** anyone can inject arbitrary PUS TCs or read the full TM stream
  (`smo-simulator/.../server.py:114-147`). `DEPLOYMENT.md:161-164` says never to expose them.
- **MCS 9090:** `/api/pus-command` (any TC; send an unknown or FD position to bypass checks, `server.py:2959-2967, 986-989`),
  `/api/schedule/upload-s11` (time-tagged TCs, no position check), `/api/tm-dump`, `/api/procedure/{load,start,
  override-command,abort,...}`, `/api/procedure/save` (writes a YAML file into `configs/…/procedures/custom/`, name
  sanitised, `:4277-4291`), `/api/ground-time` (shift the shared clock), alarm ack, go/no-go, handover, console log.
  WS has no Origin check. `/api/procedures/{path}` and `/api/manual/{path}` guard traversal with a `startswith`
  prefix check (`:4178-4179, 4241-4242`), which is weaker than `is_relative_to` (a sibling directory with the same prefix passes).
- **Simulator 8080 (instructor):** `/api/command` and WS `/ws` allow freeze, set_speed, failure inject/clear, set_phase,
  set_battery_soc, start/stop scenario, save/load breakpoint (`smo-simulator/.../engine.py:3904-4052`;
  allowlisted but unauthenticated). `/api/instructor/snapshot` exposes full ground truth (`instructor/app.py:477`).
  **`/config` is a read-write config editor**: `PUT /api/config/file`, revert, baselines apply
  (`smo-common/.../confedit/api.py:250-258`). Its path containment is sound (`confedit/editor.py:80-84`).
- **Planner 9091:** `DELETE /api/schedule` (clear all), POST/PUT activities, upload to MCS (forwards to L6, so it
  issues commands) (`smo-planner/.../server.py:486-501, 1295-1322`).
- **Scenario generator 8096:** writes YAML into `configs/eosat1/scenarios/` (slugged filename); `name` is interpolated
  unescaped into YAML (`tools/scenario_generator.py:260`), a YAML injection risk.
- **Radio 8094:** read-only unless `--radio-control`. **ZMQ 5555** is bound on `*` whenever configured.
- **VR 8100/8101:** read-only feed; accepts 4 KB status lines.
- **Dump API:** filename validation is described as load-bearing (`DEPLOYMENT.md:262-266`).
- **Debug endpoints:** none found beyond the instructor snapshot.
- **Always-0.0.0.0 tools:** orbit tools 8093 and doc viewer 8095 bind publicly even in LOCAL mode.

**SpaceCDF:**
- All REST and WS endpoints are open, including study delete, imports (`POST …/import/capella|reqif`, uploads up to 200 MB,
  `routers/exchange.py:184-211`) and exports.
- `/docs` (OpenAPI) is exposed.
- **AI endpoints spend the server's `ANTHROPIC_API_KEY`** for any caller, and the key-leak bug in §5.3 applies.
- Compose publishes Postgres (default password) and Redis (no password) on the host.
- `--reload` with source mounted.
- CORS is localhost-only with credentials (harmless now, but it will need changing).

---

## 7. Implications for the target architecture (facts only, no design)

- The sim-to-cloud hop must carry **TM, TC, the HTTP `/api/state` back-channel, and the instructor HTTP/WS (8080)**, plus
  optionally VR 8101 and the sim WS for rfsim. All of these are today **inbound to the sim**.
- The MCS and planner on the cloud need a **byte-identical `configs/eosat1/`** with the sim (the HK decode depends on
  it). The config editor and scenario generator write on the sim side only.
- The dump store is written on the sim host. The cloud MCS `/dumps` will be empty unless the store is relayed or
  synced, or the viewer `--api` mode points at the sim.
- Browser cross-service calls (L7, L8) need either a single-origin proxy with path or subdomain routing plus a
  corrected `planner_url`/`mcs_url`, or CORS headers.
- No existing presence, identity or voice primitives exist to build on. The MCS WS already broadcasts per-position
  messages (`go_nogo_*`) and is the natural signalling channel candidate. Positions come from
  `configs/eosat1/mcs/positions.yaml`.
