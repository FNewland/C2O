# Space link: design and wire protocol (smo-link v2)

*2026-10-29. This is the build contract for the server–client link between the spacecraft side (simulator, later a ground station or flatsat) and the cloud ground segment.*
*Revision 2 (same day): protocol v2 after the independent security review (`LINK_REVIEW_RESPONSE.md`): mutual challenge-response, a MAC on every frame, TC time-to-live, route and header allowlists for the proxy, loopback-by-default publishing. v1 peers are refused.*
*Inputs:*
- `docs/web_2026-10/ARCHITECTURE.md` rev 2
- `research/LINK_INTERFACES.md` (the code contract, file:line)
- `research/LINK_RESEARCH.md` (prior art, GCP limits, SLE)

The last two are copied into this folder.

## 1. Goal and non-goals

**Goal.** Run the simulator anywhere: a laptop behind NAT, or a cloud container. Run MCS, planner, RF sim and the tools on a ground host. Connect the two with one outbound WebSocket. MCS, planner, rfsim, the tools and the simulator itself need **no code change**.

**Non-goals for v1:**
- the portal, IAP, rosters, voice and practice mode;
- a real ground station or HIL provider (the interface leaves room for them);
- remote VR (headsets stay local to the simulator).

## 2. Components

```
 space host (laptop or cloud container)                    ground host (cloud VM)
┌─────────────────────────────────────────┐             ┌────────────────────────────────────────────────┐
│ smo-simulator  TC :8001  TM :8002        │             │ GSG  (python -m smo_link.gateway)               │
│                HTTP/WS :8080 (loopback)  │             │  TM  listener 127.0.0.1:8002  ──► MCS, rfsim    │
│        ▲ TCP/HTTP on loopback            │   WSS       │  TC  listener 127.0.0.1:8001  ◄── MCS, rfsim    │
│ space-link agent (python -m smo_link.    │ ──────────► │  HTTP 127.0.0.1:8080: /api/state (local, from   │
│   agent): reads TM, writes TC, polls     │  outbound   │      STATE), /healthz, /link-status, everything │
│   /api/state, ships dumps, serves proxy  │  only       │      else proxied to the sim over the link      │
│   streams to the sim's 8080              │             │  LINK listener 0.0.0.0:9100  /link (agent only) │
└─────────────────────────────────────────┘             │  dumps → $SMO_DUMP_DIR (atomic)                 │
                                                          └────────────────────────────────────────────────┘
```

The new package is **`packages/smo-link`** (`src/smo_link/`). It depends only on the stdlib, aiohttp and smo-common.

| Module | Contents |
|---|---|
| `protocol.py` | frame codec, constants, control-message schemas |
| `mux.py` | `LinkConnection`: priority writer, stream table, credit windows, heartbeat, stats |
| `auth.py` | HMAC upgrade-header sign/verify (fail-fast filter), nonce cache |
| `channel.py` | v2 mutual challenge-response, per-direction key derivation, per-frame tags, `ws://` policy |
| `clock.py` | NTP-style offset estimator, `SimClockAnchor` |
| `confighash.py` | bind-set hashing (§6) |
| `replay.py` | bounded TM replay buffer (seq, bytes, age) |
| `agent.py` | space side: sim connectors, TM reader, TC writer, STATE poller, dump shipper, HTTP/WS proxy target, reconnect loop |
| `gateway.py` | ground side: link server, TM fan-out server, TC server, local HTTP (state, health, proxy), dump receiver, link status |
| `httpproxy.py` | HTTP request/response and nested WebSocket over link streams; route and header allowlists |
| `__main__`/CLI | `python -m smo_link.agent …`, `python -m smo_link.gateway …`, `python -m smo_link.token …` (issue a session secret or token for testing) |

## 3. Wire protocol

**One WebSocket** carries everything. The agent dials `wss://<host>/link`. It refuses plaintext `ws://` unless the host is a loopback, RFC 1918 or IPv6 ULA address literal (or `localhost`), or `SMO_LINK_ALLOW_INSECURE=1` is set, which it logs as a loud `INSECURE_TRANSPORT` warning (the compose `local-demo` profile sets it for `ws://gsg:9100`). Every WebSocket *binary* message is exactly one frame. Text messages are invalid.

### 3.1 Frame layout (big-endian)

```
| ver:4 type:4 | flags | stream u16 | seq u32 | payload (0 .. 65 528 B) | tag (16 B) |
  \_____________ 8-byte header _____________/                            only after the handshake
```

| Byte(s) | Field | Notes |
|---|---|---|
| 0 | `ver:4 \| type:4` | version **2** (a v1 frame is a protocol error) |
| 1 | `flags` | bit0 FIN (last chunk of a message or body), bit1 GAP (frames were dropped before this one), bit2 RESUMED, bit3 TEXT (nested WebSocket text message), bit4 CONT (TM frame starts inside an oversized record) |
| 2–3 | `stream` u16 | |
| 4–7 | `seq` u32 | per-stream, per-direction, wraps |
| end − 16 … end | `tag` | first 16 bytes of `HMAC-SHA256(K_dir, dir_label ‖ counter u64 ‖ header ‖ payload)` (§3.3). Present on every frame except the three handshake frames |

The maximum frame size is **64 KiB** including the header, plus the 16-byte tag; bulk data is chunked at 16 KiB.

**Types:**

| Code | Name | Payload |
|---|---|---|
| 0x1 | DATA | raw bytes for the stream |
| 0x2 | OPEN | JSON (proxy streams: request head) |
| 0x3 | CLOSE | JSON `{code, reason}` |
| 0x4 | WINDOW | u32 credit increment |
| 0x5 | CTRL | JSON object on stream 0 (NaN/Infinity and non-objects are refused) |
| 0x6 | PING | JSON `{t1}` |
| 0x7 | PONG | JSON `{t1, t2, t3}` |

Worked example: one 18-byte TM packet (with its 2-byte length prefix) on stream 2, seq 1000:
`21 00 00 02 00 00 03 E8 | 00 12 | 08 64 C0 2A … | <16-byte tag>`

### 3.2 Streams

| Id | Name | Dir | Payload / semantics |
|---|---|---|---|
| 0 | CONTROL | both | Handshake: `CHALLENGE`, `AUTH`, `AUTH_OK` (untagged). Then CTRL JSON: `HELLO`, `WELCOME`, `REJECT`, `NOTICE`, `STATUS`, `DUMP_META`, `DUMP_READY`, `DUMP_ACK` |
| 1 | TC | G→A | One record per frame: an 8-byte **stamp** (u64 µs, GSG wall clock when the GSG accepted it) followed by one existing `framing.frame_packet` record, byte-identical. **At most once.** Never replayed and never queued across a link loss; anything queued at loss is discarded and reported in a NOTICE. Time-to-live §3.8 |
| 2 | TM | A→G | Existing framed records, byte-identical, in simulator order. Coalescing: flush every ≤20 ms or 32 KiB |
| 3 | STATE | A→G | JSON `{t_agent_wall, state: <exact /api/state body>}` at 1 Hz, and immediately after a speed or pause change is detected. The body carries no instructor state and no identity; its one instructor-originated field is `session_label`, free text the instructor publishes for the consoles on purpose (`set_session_label`, ≤ 80 characters; never the scenario name; see LOGBOOK_SPEC §9) |
| 4 | DUMP | A→G | Dump transfer (§3.6) |
| ≥256 | PROXY | opened by G | One HTTP exchange or one nested WebSocket each (§3.7) |

### 3.3 Handshake and binding (SLE-style BIND/START)

The secret is a per-session key of at least 32 bytes (`SMO_LINK_SECRET`, hex; shorter keys are refused). It is issued by `python -m smo_link.token new` and later by the portal. All MAC comparisons are constant time (`hmac.compare_digest`).

1. **Upgrade request (fail-fast filter).** The agent sends an HTTP GET to `/link` with `Authorization: SMO-Link v=2, session=<id>, ts=<unix>, nonce=<16 hex>, sig=<64 hex HMAC-SHA256(secret, "v2\nGET\n/link\n<session>\n<ts>\n<nonce>")>`.
   - The GSG answers **401** (never 500) if the header is malformed (non-ASCII, wrong field syntax), the signature is bad, `ts` is more than 120 s from its clock, or the nonce has been seen within 10 minutes. Auth-failure log lines are rate-limited (10 per minute plus a summary).
   - This check costs one HMAC and keeps no state for strangers. It is **not** the session's authentication: a header captured on the path could be replayed to a GSG whose nonce cache was emptied by a restart, which is why step 2 exists.
2. **Mutual challenge-response** (inside the WebSocket, untagged CTRL frames on stream 0):
   ```
   GSG   → agent  CHALLENGE {proto:2, nonce_g: 32 B hex, gsg_id}
   agent → GSG    AUTH      {nonce_a: 32 B hex,
                             mac_a: HMAC-SHA256(secret, "smo-link/v2/agent" ‖ session ‖ nonce_g ‖ nonce_a)}
   GSG   → agent  AUTH_OK   {mac_g: HMAC-SHA256(secret, "smo-link/v2/gsg"   ‖ session ‖ nonce_a ‖ nonce_g)}
   ```
   `session` is length-prefixed (u16) and the nonces are raw 32-byte values, so the input is unambiguous; the two labels differ, so neither MAC can be reflected as the other.
   - The GSG verifies `mac_a` or closes with **4401**. The agent verifies `mac_g` or aborts. A GSG that does not know the secret (spoofed DNS, a student network) therefore never receives HELLO, a TC or a proxied response.
   - Both ends contribute a fresh nonce, so no login can be replayed (this closes review M6). The GSG must finish steps 1–2 within **10 s** of the TCP accept, or the connection is aborted (§7).
3. **Keys.** `K_a2g = HMAC-SHA256(secret, "smo-link/v2/k_a2g" ‖ nonce_a ‖ nonce_g)`, `K_g2a` likewise with `"smo-link/v2/k_g2a"`.
4. **Every later frame is tagged** (HELLO, WELCOME and REJECT included): `tag = HMAC-SHA256(K_dir, dir_label ‖ counter ‖ header ‖ payload)[:16]`, where `dir_label` is `a2g` or `g2a` and `counter` is a u64 that starts at 0 per direction and counts frames. The counter is **implicit**: both ends count, nothing is sent. A frame whose tag fails (forged, replayed, dropped, reordered, truncated, or a v1 frame) closes the link at once with **4403**; the GSG then unbinds and resets its TC clients. Only the writer task seals and only the reader task opens, so the counters cannot diverge.
5. **HELLO** (agent → GSG, stream 0):
   ```
   {proto:1, session, agent_version, mission, config_hash, config_files:{path:sha256},
    sim:{speed, sim_time, tick_hz}, resume:{instance, tm_next_seq} | null,
    mode:"complete"|"timely"}
   ```
6. **The GSG decides:**
   - It sends `REJECT {code:"config-mismatch", files:[...]}` (then closes 4409) if any **strict** bind-set file differs (§6). If only **warn**-set files differ, it accepts and posts a NOTICE.
   - If a session is already bound, the new valid HELLO **supersedes** it. The old session is **unbound synchronously** first: it is marked DOWN, the TCs still queued on it are counted and reported, and every TC client is **reset (RST)**. Only then does the old WebSocket's close (4000 "superseded") run, in the background, and the new session binds at once. There is no `await` between the supersede and the new bind, so two racing HELLOs cannot leave an orphan. The MCS sees its TC socket reset and reconnects to the new session by itself.
7. **WELCOME** (GSG → agent):
   ```
   {proto:2, gsg_version, accepted:true, resume_from_tm_seq: n | null, server_time, tc_ttl_s}
   ```
   - In `complete` mode the agent replays TM from `resume_from_tm_seq` out of its replay buffer. If that seq is no longer buffered, it sends from the oldest buffered frame and sets **GAP**, and the GSG logs a NOTICE "N packets lost".
   - In `timely` mode the agent sends only new TM.
8. **STATUS** (GSG → agent, every 5 s): the GSG's view (UP/DEGRADED, RTT, clients). This is informational only.

**Why tag every frame.** In v1 only the upgrade was authenticated. Anyone who could write on the TCP path (the plaintext LB → GSG hop inside the VPC, or any `ws://` deployment) could inject `DATA stream=1` frames, which are TCs to the simulator, or OPEN frames that drive the instructor API. A spoofed GSG got full TC and proxy control of the sim. With v2 the tag proves who wrote each frame and that the frame is the next one in order. This holds **end to end, across the plaintext LB → GSG hop as well**.

**What v2 does not give: confidentiality.** Frames are MACed, not encrypted. Between the agent and the load balancer TLS (`wss://`) protects them. Between the LB and the GSG, inside the VPC, anyone who can capture traffic there can read TM, TC, proxied pages and dumps, though they cannot change or inject any of them. The same is true on any `ws://` deployment. Encrypting frames inside the link (or TLS to the GSG) is future work if that hop is ever shared.

### 3.4 Liveness and reconnection
- **PING every 10 s** from both sides. If nothing at all is received for 30 s, the link is dead: close and reconnect. aiohttp `heartbeat=20` is also on, as a backstop.
- **Agent reconnect:** full-jitter exponential backoff, base 0.5 s, cap 30 s, reset after 60 s connected. The agent never exits on a link failure.
- **Link states** published by the GSG:

  | State | Condition | TC |
  |---|---|---|
  | UP | bound, last frame < 15 s ago | accepted |
  | DEGRADED | 15–30 s silence, or RTT > 1 s | **refused when caused by silence**: TC clients are reset, new connects reset (§3.8) |
  | DOWN | otherwise | refused (RST) |

### 3.5 Clock
- Each PING/PONG yields one NTP sample. The estimator keeps the **minimum-delay sample of the last 8**, giving `offset` (agent wall − GSG wall) and `rtt`.
- **STATE re-timing at the GSG:**
  ```
  age_s = gsg_now − (t_agent_wall − offset)
  served sim_time = state.sim_time + age_s × state.speed   (0 if paused)
  ```
  `met_s` is advanced the same way. All other fields are served unchanged.
- **Staleness:** `/api/state` returns **503** when the last STATE is older than **5 s** of GSG wall time. MCS and planner already handle 503 by keeping their anchor, then falling back to their own propagator at 4.5 s.

### 3.6 Dumps
- **Agent:**
  - Polls the simulator's `GET /api/dumps` every 2 s.
  - A file is shipped once its size is stable across two polls and it is not already acknowledged. Acknowledged names are kept in `$SMO_LINK_STATE_DIR/dumps_acked.json`.
  - It sends `DUMP_META {name, size, sha256, mtime}` as CTRL, then DATA on stream 4 in 16 KiB chunks with FIN on the last chunk. Dumps run at the **lowest priority**.
  - On reconnect it restarts the file from offset `ack_offset` if the GSG reports one, otherwise from 0.
- **GSG:**
  - Accepts only names that fully match `dump_sid<n>_<yyyymmdd>T<hhmmss>Z.bin` (ASCII, no trailing newline).
  - Refuses a dump larger than **64 MiB** (`too-large`; real dumps are ≈ 2 MB), one that would leave less than **256 MiB** free on the dump disk (`disk-full`), or one that would take the `.part-*` files over **256 MiB** in total (`quota`).
  - Writes `.part-<name>` in `$SMO_DUMP_DIR` while hashing incrementally, verifies sha256, then `os.replace` to `<name>` and sets mtime. Hashing an existing file runs off the event loop.
  - Replies `DUMP_ACK {name, ok}`; a refusal or an I/O error (`io`) also sends a NOTICE. Either way only that transfer fails, never the link. The agent backs off on that name (doubling, up to 10 min), so a full disk cannot turn into a reconnect storm.
  - A name that already exists with the same hash is acked without rewriting it.

### 3.7 Proxied HTTP and WebSocket (stream ≥ 256)

**Opening.** The GSG opens a stream with OPEN:
```
{kind:"http"|"ws", method, path, query, headers:[[k, v], …], protocols?:[…]}
```
`path` is the **canonical** path that passed the allowlist below, re-encoded. `headers` are only the allowlisted request headers. `Host` is set by the agent to the sim's address, and `Origin` is checked at the GSG and then rewritten to the sim's own origin.

**Route allowlist (GSG and agent).** Only these requests are proxied; everything else gets **403**:
- `GET`/`HEAD`: `/`, `/classic`, `/modern`, `/static/**` (no dot-files), `/api/instructor/snapshot`, `/api/instructor/{views,timeline,fault-menu,history,debrief}` (the instructor console's truth, divergence, timeline and debrief feeds), `/api/vr`, `/api/scenarios`, `/api/scenario/debrief`, `/api/failures`, `/api/failure-catalog`, `/api/breakpoints`, and the **read-only** dump and report views `/dumps`, `/api/dumps`, `/api/dumps/`, `/api/dumps/{file,summary}`, `/api/dumps/<name>`, `/api/dumps/<name>/summary`, `/reports`, `/api/reports`, `/api/reports/`, `/api/reports/templates`, `/api/reports/templates/<id>`, `/api/reports/file`;
- `POST`: `/api/command`, `/api/breakpoint/save`, `/api/breakpoint/load` (the instructor commands);
- WebSocket upgrade: `/ws` only (instructor console and rfsim).

The list is derived from `smo_simulator/instructor/app.py` and the libraries it mounts. Not on it, and so unreachable: the config editor (`/config`, `/api/config/*`), `POST /api/reports/{validate,generate}` (reports are made on the ground), and anything added to the sim later until someone lists it.

The match is case-sensitive and runs on the **fully normalised** path: fragment and query stripped, `;params` stripped from every segment, percent-decoded once (anything still holding `%`, a backslash, NUL, a control character, a space or non-ASCII is refused), `//` collapsed, and `.`/`..` resolved (escaping the root is refused). The GSG forwards exactly that canonical path. The agent, the side next to the simulator, checks it again on the path it receives AND on the final upstream URL it builds (`yarl.URL.build(..., encoded=True)`), and refuses anything that differs.

**Headers (allowlists in both directions).**
- Request headers forwarded: `Accept`, `Accept-Encoding`, `Accept-Language`, `Content-Type`, `If-None-Match`, `If-Modified-Since`, `If-Match`, `If-Unmodified-Since`, `If-Range`, `Range`, `Cache-Control`, `Pragma`, `User-Agent`, `X-Requested-With` (plus `Origin`, rewritten, and the WebSocket subprotocol list). Never `Cookie`, `Authorization`, `X-Goog-IAP-*`, `Proxy-*`, `Forwarded` or `X-Forwarded-*`: the space side may be a student laptop, and must not see the instructor's edge credentials.
- Response headers relayed: `Content-Type`, `Content-Length`, `Content-Encoding`, `Cache-Control`, `ETag`, `Last-Modified`, `Content-Disposition`, plus `Content-Range` and `Accept-Ranges` because `Range` is allowed. Never `Set-Cookie`, `Location`, `Refresh`, CORS or security-policy headers chosen by the space side.
- The GSG adds to every proxied response: `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: same-origin`, `Cross-Origin-Resource-Policy: same-origin` and
  `Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; media-src 'self'; connect-src 'self' ws://<host> wss://<host>; worker-src 'none'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'self'`.
  This blocks third-party script, connect, form and frame targets. `'unsafe-inline'` is needed by the classic console's inline handlers. The e2e test loads both consoles in headless Chromium through the GSG and requires zero CSP violations.
- **Residual risk.** A hostile agent can still serve its own same-origin HTML and JS on the instructor origin, because it *is* the origin. The CSP stops that script from talking to any other origin, but it can still navigate the tab. That is why the instructor proxy must be served on its own host (`instructor.<domain>`, as in `deploy/gcp/README.md`), never on the MCS's origin.

**Host check (DNS rebinding).** The proxy and `/link-status` answer only Host names that are IP literals, `localhost`, the hosts of `SMO_GSG_ALLOWED_ORIGINS`, or `SMO_GSG_ALLOWED_HOSTS`.

**HTTP exchange:**
1. The request body follows as DATA with FIN.
2. The agent performs the request against `http://127.0.0.1:$SMO_SIM_HTTP_PORT` with `auto_decompress=False` and `timeout total=None`.
3. The agent replies with OPEN `{status, headers}`, then the body as DATA chunks with FIN.

**WebSocket.** Each message is one DATA frame. Flag bit3 set means a text message. CLOSE ends it.

**Flow control.** Credit windows of 256 KiB per proxy stream (WINDOW frames), so a large download can't starve TM. The window is **enforced on receive**: DATA beyond the credit granted closes that stream (1008), and a reassembled nested-WebSocket message over 4 MiB closes that stream (1009). Neither closes the link.

**Error isolation.** An exception in any frame handler (dump, proxy, state, control) drops that frame, or closes that one proxy stream, and is logged as `frame_handler_error`. Only a protocol or authentication violation (tag failure, undecodable frame, text message) closes the link.

**Served locally by the GSG (never proxied):**
- `/api/state` (§3.5)
- `/healthz` (always 200 while the process is up)
- `/link-status` (JSON: state, rtt, offset, session, last_state_age, counters)

### 3.8 Scheduling and back-pressure
- **One writer task per side, strict priority:**

  | Priority | Traffic |
  |---|---|
  | 1 | CONTROL / PING / PONG |
  | 2 | TC |
  | 3 | TM |
  | 4 | STATE |
  | 5 | PROXY |
  | 6 | DUMP |

- The writer only writes while the transport's write buffer is below **64 KiB** (`ws._writer.transport.get_write_buffer_size()`, guarded by a fallback).
- **Agent TM buffering:** the sim TM socket is always read promptly (constraint: the simulator drops readers slower than 2 s). Frames go into a bounded queue (default 20 000 frames or 8 MiB) and the replay buffer (10 s or 2 MiB, whichever holds more).
  - `timely` mode: on overflow, drop the oldest and set GAP.
  - `complete` mode: drop the oldest too, but only once over the bound, and report GAP. The sim socket is never blocked.
- **Agent replay buffer:** at least `dead_after` + 10 s (40 s) or 16 MiB, so that what a silently dead link swallowed is still there to resend.
- **GSG TM fan-out:** each local client has a queue bounded at 5 000 packets **and 8 MiB**.
  - On overflow, drop the oldest for that client and log it. Never disconnect it: the MCS reconnects in a tight loop and rfsim never reconnects.
  - TM clients stay connected while the link is DOWN, and the listener is open from process start.
- **GSG TC while the link is DOWN, or DEGRADED by silence (≥ 15 s with nothing received):**
  - Existing TC client sockets are closed abortively (SO_LINGER 0, i.e. RST), within 0.25 s.
  - New TC connections are accepted and immediately RST.
  - A TC that arrives in that state is discarded, counted and logged (`code=tc-discarded`), and its client is reset.
  - The MCS then reports `503 No TC connection`, exactly as "simulator down" today.
  - When the link comes back, new connections are accepted normally.
- **Every close of a TC client that the GSG initiates is an RST**, never a FIN: link down, dead link, supersede, degraded, bad record length (0 or > 65 518 B), and GSG shutdown. A FIN leaves the MCS's writer believing the socket is fine, so its next TC is silently lost (review H1). On a link loss or supersede the session is **unbound and its TC clients reset synchronously, before** the WebSocket closing handshake is awaited (which can take 5 s on a silent peer).
- **TC time-to-live** (`SMO_LINK_TC_TTL_S`, default **5 s**, sent to the agent in WELCOME):
  - At the GSG, a TC still in the link queue when the writer would send it, and older than the TTL, is discarded, never sent. It is logged as `event=notice code=tc-expired`, counted (`tc_expired`) and reported to the agent in a NOTICE. The deadline is checked after the writer has transport room, at the moment of sending.
  - At the agent, a TC whose stamp (§3.2) is older than the TTL is discarded, counted and NOTICEd to the GSG. Its age is measured in GSG time, using the PING/PONG clock offset (or, before the first sample, WELCOME's `server_time`). This bounds the whole delay, including the kernel buffers of a silently dead path.
  - The agent writes a TC to the simulator only if the payload is a whole number of valid records (review L4); otherwise it is refused (`tc-malformed`).

## 4. Configuration (environment first, CLI flags mirror it)

**Agent:**

| Variable | Default / meaning |
|---|---|
| `SMO_LINK_URL` | e.g. `wss://link.team-a.ops.example.ca/link` |
| `SMO_LINK_SESSION` | session id |
| `SMO_LINK_SECRET` | hex secret, or `SMO_LINK_SECRET_FILE` |
| `SMO_SIM_HOST` | 127.0.0.1 |
| `SMO_SIM_TM_PORT` | 8002 |
| `SMO_SIM_TC_PORT` | 8001 |
| `SMO_SIM_HTTP_PORT` | 8080 |
| `SMO_CONFIG_DIR` | configs/eosat1 |
| `SMO_LINK_MODE` | `complete` or `timely` |
| `SMO_LINK_STATE_DIR` | `workspace/link` |
| `SMO_LINK_ALLOW_INSECURE` | `1` permits plaintext `ws://` to a non-private host (loud warning). Default: refused |

**GSG:**

| Variable | Default / meaning |
|---|---|
| `SMO_GSG_BIND` | 127.0.0.1 (TM, TC, and HTTP unless `SMO_GSG_HTTP_BIND`) |
| `SMO_GSG_HTTP_BIND` | defaults to `SMO_GSG_BIND`; compose sets 0.0.0.0 inside the container so the port can be published |
| `SMO_GSG_TM_PORT` | 8002 |
| `SMO_GSG_TC_PORT` | 8001 |
| `SMO_GSG_HTTP_PORT` | 8080 |
| `SMO_GSG_LINK_BIND` | 0.0.0.0 |
| `SMO_GSG_LINK_PORT` | 9100 |
| `SMO_LINK_SESSION` | session id |
| `SMO_LINK_SECRET` | hex secret, or `SMO_LINK_SECRET_FILE` |
| `SMO_DUMP_DIR` | dump directory |
| `SMO_CONFIG_DIR` | configs/eosat1 |
| `SMO_GSG_ALLOWED_ORIGINS` | comma list for proxied browser requests; empty means same host only. Their host names are also accepted as `Host` |
| `SMO_GSG_ALLOWED_HOSTS` | extra `Host` names the instructor proxy answers (IP literals and `localhost` always) |
| `SMO_LINK_TC_TTL_S` | 5: the TC time-to-live (§3.8) |

**Log format.** Logs are structured key=value lines on stdout. No secrets are ever logged. `--secret` on the command line works but logs a warning (it is visible in `ps`); use `SMO_LINK_SECRET_FILE`.

## 5. Launch profiles

- **`start.sh` gains `SMO_PROFILE=all|space|ground`** (default `all` keeps today's behaviour byte for byte).
  - `space`: simulator, then agent (after the sim's `/api/state` answers).
  - `ground`: GSG first, then a wait on TM port 8002, then MCS, planner, rfsim (only after the GSG TM port is open), viewer, orbit tools and doc viewer. The scenario generator and ADCS viewer belong to `space`.
- **Docker:** one image (`docker/Dockerfile`, python:3.13-slim, installs all `packages/*`). `docker/compose.yaml` has these profiles:
  - `space` (sim + agent);
  - `ground` (gsg + mcs + planner + tools, optional rfsim);
  - `local-demo` (both on one host over the compose network: `ws://gsg:9100/link`). This is also the **cloud-simulator provider**.
- **Healthchecks:** sim `/api/state`; GSG `/healthz`.
- `smo-gateway` and `deploy/` are marked **deprecated** in docs, with `smo-link` as the replacement. Removal comes in a later pass, since the Mac mount can't delete files.

## 6. Config bind set (from LINK_INTERFACES §5)

- **Strict (reject on mismatch):**
  - HK structures, telemetry parameters, TC catalogue, event catalogue, memory map;
  - S12 and S19 monitoring definitions;
  - `subsystems/ttc.yaml` and `orbit.yaml`;
  - the identity subset of `mission.yaml`: name, APIDs, PUS version, time epoch, boot mode.
- **Warn only:** ground stations, EPS, payload and propulsion configs, fault propagation.

Files are hashed with line endings normalised, sha256 per file plus an overall hash. The exact file list lives in `confighash.py` with a test that every listed path exists.

## 7. Security baseline (v2)

**Link endpoint:**
- HMAC upgrade header as a fail-fast filter, then mutual challenge-response, per-direction keys and a 16-byte MAC on every frame (§3.3).
- One bound agent per session.
- **Pre-auth limits:** a connection must complete the upgrade AND the challenge-response within **10 s** of the TCP accept, or it is aborted (no more half-open requests held forever). At most **64** unauthenticated connections at once, **16** per source address, and **120** new connections per source address per minute; beyond that, new connections are aborted on accept. Behind the GCP LB the source is a Google front end, so these are a backstop; Cloud Armor limits per client.
- 401s, 4401s, 4403s and 4409s are logged; auth-failure lines are rate-limited.
- In GCP, `/link` sits behind its own backend service **with IAP off**, a **3600 s backend timeout**, and firewall rules limited to Google's load-balancer ranges. Every other path stays behind IAP (WP-0).

**GSG local ports:**
- TM, TC and HTTP bind **127.0.0.1** by default; in compose TM/TC stay on loopback inside the ground namespace.
- **Docker publishes** MCS 9090, planner 9091, the instructor proxy 8080 and the link 9100 on `${SMO_PUBLISH_ADDR:-127.0.0.1}`. On GCP that is the VM's internal IP, with the VPC firewall admitting only the LB ranges and IAP (`deploy/gcp/README.md`).
- Browsers reach the instructor proxy only through the authenticated edge (WP-0), on its own host name.
- The proxy applies the route and header allowlists, the Host check and an Origin check (§3.7).

**Transport:**
- TLS is terminated at the load balancer. The LB → GSG hop inside the VPC is plaintext, but frames are MACed end to end, so it can read and cannot forge (§3.3: confidentiality only to the LB). The agent refuses `ws://` to a non-private host unless explicitly overridden.

**TC:**
- Never replayed. A stale TC queue is discarded on link loss. A TC older than its TTL is never forwarded, by the GSG or by the agent. TC is refused while the link is DEGRADED by silence. Every GSG-initiated TC close is an RST.

## 8. Tests (all must run in CI without root)

1. **Unit:**
   - frame codec round-trip and fuzz;
   - HMAC verify (good, bad, skewed, replayed);
   - clock estimator under asymmetric delay;
   - replay buffer bounds;
   - priority writer ordering;
   - proxy route allowlist and path normalisation; header allowlists;
   - config hash stability under CRLF.
2. **Component** (in-process, fake sim sockets): TM byte equality, TC at-most-once across reconnect, dump atomicity and resume, proxy HTTP with streaming and gzip passthrough, proxy WebSocket.
3. **End-to-end** (`tests/test_link/test_e2e.py`, marked `link_e2e`, about 60 s):
   - **Topology:** a real `SimulatorServer` on free ports, the agent, an asyncio **fault proxy** between agent and GSG (latency, jitter, cut the connection), the GSG on free ports, a real `MCSServer` pointed at the GSG, and `PlannerServer`.
   - **Assertions:**
     - TM byte equality from the sim tap to the GSG tap;
     - a TC through the MCS API produces S1.1 and S1.7;
     - with 200 ms one-way delay at ×60, the MCS clock is within one tick × speed of the engine;
     - link cut: MCS gets `503 No TC connection` within 3 s, GSG `/api/state` returns 503 after 5 s, and the rfsim-style TM client socket stays open;
     - reconnect: TM resumes with no duplicates (`complete` mode), and a TC queued during the cut is not delivered;
     - an S15 dump arrives byte-identical, and MCS `/api/dumps` lists it;
     - the instructor page and `/ws` work through the GSG proxy, and `/config` returns 403.
4. **Security regression** (`tests/test_link/test_security.py`): one or more tests per review finding (`LINK_REVIEW_RESPONSE.md`), each reproducing the reviewed failure (a forged, replayed or injected frame; a rogue GSG; a replayed header after a restart; supersede and dead-link TC resets; header and route bypasses; handler errors; credit, dump and fan-out bounds; half-open floods; TC TTL and DEGRADED). The e2e suite also loads both instructor consoles in headless Chromium through the GSG and requires zero CSP violations and zero allowlist 403s. It skips if Playwright is not installed.
5. **Regression:** the full suite shows no new failures against the current baseline.
