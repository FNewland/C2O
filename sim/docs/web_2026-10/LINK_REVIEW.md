# smo-link v1 — independent security and robustness review

2026-10-29. Read-only review of `packages/smo-link/src/smo_link/*.py` against `docs/web_2026-10/LINK_DESIGN.md` and `LINK_INTERFACES.md`. No repository file was edited.

Confirmation scripts are in `/tmp/claude-0/-home-claude/1321a170-74b6-5d07-9a93-b12889d176dd/scratchpad/review/`. Each one starts a real `Gateway` on free ports and either a hand-driven fake agent or a real `Agent` with a mock simulator. Findings marked **[CONFIRMED]** were reproduced. The others come from reading the code.

**Threat model.** The space host may be a student laptop, so whoever holds `SMO_LINK_SECRET` is less trusted than the ground. TC is safety-critical. The owner's requirement is that login and protection be "beyond doubt".

---

## Severity summary

| # | Sev | Finding |
|---|---|---|
| H1 | HIGH | TC sockets are closed with **FIN, not RST**, on the discard path, during a supersede and on GSG stop. The MCS's next TC is lost without any error **[CONFIRMED]** |
| H2 | HIGH | Only the HTTP upgrade is authenticated. There is no mutual auth and no per-frame integrity. `ws://` to any host is accepted. The LB→GSG hop is plaintext. TC frames can be injected by anyone on that path |
| H3 | HIGH | The proxy forwards ground `Cookie`, `Authorization` and IAP JWT headers to the space side. It also relays `Set-Cookie` and arbitrary HTML/JS from the space side to ground browsers **[CONFIRMED]** |
| H4 | HIGH | `docker/compose.yaml` publishes MCS 9090, planner 9091, the GSG proxy on 8080 and the link on 9100 on **0.0.0.0 by default**. None of these has its own auth, so an unauthenticated TC uplink is exposed whenever the host is reachable |
| M1 | MED | Deny-list bypass: `GET /config#x` reaches the simulator's writable config editor page **[CONFIRMED]**. Write routes are safe today only because of an HTTP-parser detail |
| M2 | MED | Any exception in a GSG frame handler tears down the link. With a disk error, the dump retry turns this into a link-flap loop and a TC outage **[CONFIRMED]** |
| M3 | MED | A malicious or buggy agent can exhaust GSG memory and disk (credit not enforced on receive, unbounded message reassembly, TM fan-out up to about 330 MB per client, unbounded dumps) |
| M4 | MED | The link port (0.0.0.0) has no header timeout and no connection cap: 300 half-open connections were held for more than 90 s **[CONFIRMED]**. 401 log lines are unbounded. A non-ASCII `sig` gives a 500 with a traceback **[CONFIRMED]** |
| M5 | MED | TCs are accepted and queued while the link is silent (up to 30 s), then delivered late with no TTL. The MCS shows SENT |
| M6 | MED | A captured `Authorization` header can be replayed after a GSG restart, because the nonce cache is in memory only **[CONFIRMED]** |
| L1–L12 | LOW | See §3 |

---

## 1. HIGH

### H1. TC client closed with FIN instead of RST: silent TC loss [CONFIRMED]
- **Where:**
  - `gateway.py:338-342` (TC arrives while `self.link` is None or closed: `break`);
  - `:349-351` (`finally: writer.close()` sends a FIN);
  - `:334-336` (bad length: FIN);
  - `:198-199` (`stop()` uses `w.close()`).
- **Why it matters.** LINK_INTERFACES §1.6 measured that after a FIN the MCS's `is_closing()` stays False and the next TC "succeeds" into a dead socket. This is constraint 3 of the contract.
- **Windows where it happens:**
  - **Supersede** (`:427-428`): `self.link = None`, then `await old.close()`. When the old peer has gone silent (the normal reconnect-after-network-change case), `ws.close` waits up to 5 s (`mux.py:222`).
  - **Dead link:** the same 5 s inside `LinkConnection.close()`. During it `self.link` still points at the closed connection, so `_unbind` (which sends the RST) has not run.
  - **GSG restart or redeploy.**
- **Repro** (`t_tc_fin.py`). Agent A is bound. An MCS-style TC client connects. Agent B (valid credentials) supersedes while A is silent. A TC is sent, and the GSG logs `tc_discarded`. The client then shows `is_closing() == False`, and the **second TC write+drain succeeds** and is lost. B's WELCOME arrived only after about 5 s, and every TC in that window is lost this way.
- **Fix:**
  - Use `rst_close(writer)` on every GSG-initiated TC close: the discard path, bad length and `stop()`.
  - On supersede, either keep TCs flowing (assign the new connection before awaiting `old.close()`, and close the old one in a background task), or RST the TC clients.
  - Do not keep a closed link in `self.link`: call `_unbind` from `LinkConnection.close()` through a callback, before the `ws.close` wait.

### H2. Auth covers the upgrade only, not the channel; no mutual auth
- **Where:** `auth.py:68-76` (the signature covers `v1/GET/link/session/ts/nonce` only); `mux.py` (frames carry no MAC); `agent.py:497` (any `ws://` URL is accepted); LINK_DESIGN §7 ("No TLS inside the VPC").
- **Scenarios:**
  - **Injection on the path.** Anyone between the LB and the GSG (plaintext inside the VPC), or anyone on the network in `ws://` deployments (compose `local-demo`, `ws://gsg:9100`, or a student who sets `ws://`), can inject `DATA stream=1` frames. Those are TCs that go straight to the simulator's TC port, and later to a real ground station. They can also inject OPEN frames that drive the instructor API on the space side.
  - **Rogue GSG.** The agent never authenticates the GSG. A spoofed GSG (DNS on a student network with `ws://`) gets full TC and proxy control of the sim.
  - **Safety.** The HMAC proves who opened the socket, not who wrote a TC. That does not meet "beyond doubt".
- **Fix (keep it stdlib):**
  1. Challenge-response with mutual auth.
     - The GSG sends `server_nonce` (in the 401 `WWW-Authenticate`, or as the first frame).
     - The agent sends `HMAC(K, "agent"‖session‖cn‖sn)`, and the GSG proves `HMAC(K, "gsg"‖…)` in WELCOME.
     - Derive `K_s = HKDF(K, cn‖sn)`.
  2. **MAC every TC frame** (and ideally every frame), with `K_s` over `header‖payload`, a monotonic per-direction counter and a GSG timestamp. The agent drops anything that fails before it writes to the sim.
  3. The agent refuses `ws://` unless the host is loopback or the operator sets `--insecure-transport`. Pin the TLS CA if possible.

### H3. Ground credentials go to the space side; space content goes to ground browsers [CONFIRMED]
- **Where:** `httpproxy.py:132` (only hop-by-hop headers and `Host` are stripped); `:167-168` (response headers relayed verbatim apart from hop-by-hop).
- **Repro** (`t_proxy.py`). The fake agent received this OPEN:
  `[['Cookie','GCP_IAP_AUTH_TOKEN_abc=SECRET'],['Authorization','Bearer XYZ'],['X-Goog-IAP-JWT-Assertion','eyJhbGc'],['X-Forwarded-For','6.6.6.6'],…]`.
  The agent's `Set-Cookie: x=1` was relayed to the client.
- **Impact:**
  - The space operator (possibly a student) gets the instructor's edge credentials: the IAP session cookie or JWT, if IAP forwards them, which needs checking, plus any portal cookies.
  - A malicious agent can also serve HTML or JS on the IAP-protected instructor origin. This is stored XSS in the instructor's browser, with the same-site cookies that reach the MCS.
  - Client-supplied `X-Forwarded-For` is passed through, so logs can be spoofed.
- **Fix:**
  - **Request headers:** forward an allowlist only: `Accept`, `Accept-Encoding`, `Accept-Language`, `Content-Type`, `If-None-Match`, `If-Modified-Since`, `Cache-Control`, `Range`. Drop `Cookie`, `Authorization`, `X-Goog-*`, `X-Forwarded-*` and `Forwarded` from the client.
  - **Response headers:** allowlist `Content-Type`, `Content-Encoding`, `Content-Length`, `ETag`, `Last-Modified`, `Cache-Control`, `Content-Disposition`. Drop `Set-Cookie`.
  - Add `Content-Security-Policy: sandbox`, or serve the proxy on its own registrable domain, cookie-isolated from the MCS and portal.

### H4. Compose publishes unauthenticated ground services on 0.0.0.0 by default
- **Where:** `docker/compose.yaml:150-154` uses `${SMO_PUBLISH_ADDR:-0.0.0.0}` for 9090 (MCS, which can send TCs), 9091, 8080 (the instructor proxy: failure injection, speed, breakpoints) and 9100. The `local-demo` profile, meant for laptops, uses the same `gsg` service.
- **Spec conflict:** LINK_DESIGN §7 says "TM, TC and HTTP bind 127.0.0.1 by default". Protection depends entirely on "a VM with no external IP behind IAP". On a laptop on campus Wi-Fi, or a VM with a public IP, anyone can command the spacecraft through the MCS. Docker-published ports also bypass ufw.
- **Inside the container:** GSG TM/TC bind 0.0.0.0 (`:139`), so any container on the compose network, and the host through the container IP, can reach TC 8001 directly. TC 8001 has no auth (inherited from the sim).
- **Fix:**
  - Default `SMO_PUBLISH_ADDR` to `127.0.0.1` and require an explicit opt-in for the LB deployment.
  - Put ground services on an `internal: true` network.
  - Keep `network_mode: service:gsg` but bind GSG TM/TC to 127.0.0.1, which works because they share the namespace.

---

## 2. MEDIUM

### M1. Deny-list checks a different string than the one the simulator routes on [CONFIRMED]
- **Where:**
  - `httpproxy.py:46-83` normalises `request.raw_path`, which keeps a `#fragment`, and `:138` forwards it.
  - `agent_serve_stream` (`:280`) builds `sim_base + path`. yarl then **strips the fragment and removes embedded TAB/CR/LF** (WHATWG behaviour).
- **Repro** (`t_e2e_bypass.py`, real GSG + real Agent + mock sim). `GET /config#x` gives **200 from the sim's `/config`** handler, the editor page rendered with `READONLY=false`. `GET /config` correctly gives 403.
  - `PUT /api/conf<TAB>ig/file` would become `/api/config/file` after yarl. Today it is rejected with 400 by both the C and the pure-Python aiohttp parsers (tested with `AIOHTTP_NO_EXTENSIONS=1`), so config **writes are not reachable**. That protection rests on a parser detail.
- **Fix:**
  - Build the upstream URL with `URL.build(path=…, query_string=…, encoded=True)` from `request.rel_url` (no fragment).
  - Re-run the deny check on `URL(final).path` in the agent just before the request.
  - Better still, replace the deny-list with an **allowlist** of the routes in LINK_INTERFACES §3.1 (`/`, `/classic`, `/modern`, `/ws`, `/api/instructor/snapshot`, `/api/vr`, `/api/command`, `/api/scenarios`, …, `/static/…`, read-only `/api/dumps*` and `/api/reports*`).

### M2. Exceptions in handlers kill the link; disk errors cause a flap loop [CONFIRMED]
- **Where:** `mux.py:356-358` calls `on_frame` without a try. `_reader` (`:315-317`) turns any exception into `close()`, and the GSG then resets TC.
- **Repro** (`t_misc.py`):
  - **Dump failure.** `DUMP_META` with an unwritable `.part` (stand-in for ENOSPC or EACCES) gives `link_down reason="read error IsADirectoryError"`. The agent reships the unacked dump about 2 s after every reconnect, so a full disk means a permanent link flap and a TC outage.
  - **Bad PING.** `PING {"t1": NaN}` gives `read error ValueError`, because `dumps(allow_nan=False)` fails in `_dispatch`.
  - **Bad CTRL.** CTRL JSON that is not an object raises `AttributeError` at `gateway.py:503`.
- **Fix:**
  - Wrap `_dispatch` per frame: log and drop the frame (or the stream), and never close the link for an application error.
  - In the dump path, catch `OSError` and reply `DUMP_ACK ok=false reason=io`, with agent-side backoff per name.
  - Parse JSON with `parse_constant` that rejects NaN and Infinity.
  - Type-check that CTRL messages are dicts.

### M3. A malicious or buggy agent can exhaust GSG memory and disk
The agent holds the secret, and the GSG shares its host with the MCS.
- **Stream inbox ignores credit.** `Stream._inbox` (`mux.py:56, 99`) is an unbounded `asyncio.Queue`. Received DATA is never checked against the advertised window, so a peer that ignores credit grows the GSG's memory without limit. Track received bytes and close the stream with a protocol error if they exceed the window.
- **Unbounded reassembly.** `recv_message` (`mux.py:146-159`) concatenates DATA chunks until FIN with no cap. Cap it at `WS_MAX_MSG`.
- **TM fan-out bound counts records, not bytes.** `TmClient` (`gateway.py:111-118`) allows 5000 records of up to 65 537 B each, about 330 MB per TM client. Add a byte cap of a few MB.
- **Dumps unbounded.** `size` is taken from the agent (`:530`) with no maximum and no total quota or free-space check. Name collisions are refused, but new names are unlimited. Cap at about 64 MB per dump (the real maximum is about 1.9 MB), enforce a directory quota, and check `shutil.disk_usage`.
- **DUMP_META hashing blocks the event loop** (`:540`, `_sha256_file` on the event loop). Fine at 2 MB; with larger files, move it to a thread.

### M4. Link port (0.0.0.0) DoS and log flooding [CONFIRMED]
- **Half-open connections.** aiohttp has no request-header timeout. In `t_slow.py`, 300 connections that sent only a partial request line were all still open after 90 s. Enough of them exhaust file descriptors, and the legitimate agent can't reconnect, so the link stays DOWN.
  - The GCP LB absorbs this, but the default bind is 0.0.0.0 and compose publishes 9100.
  - **Fix:** a front proxy, or a `handler_args`/`TCPSite(backlog…)` connection cap, a per-IP limit and a header-read deadline. A small asyncio pre-reader with a 5 s header timeout is enough.
- **Log flooding.** Each 401 logs one WARNING (`gateway.py:392`), so an unauthenticated peer can produce unlimited log volume (with Cloud Logging cost). Rate-limit, and log a summary every N seconds.
- **Non-ASCII signature.** `sig=\xe9` makes `hmac.compare_digest` raise `TypeError` (`auth.py:157`). The response is **500 with a stack trace** and is not counted in `auth_failures`. Validate `sig` with `^[0-9a-f]{64}$` before comparing (no auth bypass is involved).

### M5. Stale TC delivery
- **What happens.** While the WebSocket is silently dead (up to `dead_after` = 30 s), `_handle_tc` keeps enqueuing TCs and the writer pushes them into the kernel send buffer.
  - If the TCP path recovers inside that window, they are delivered late. The agent writes them to the sim with no age check (`agent.py:295-306`).
  - Otherwise they are dropped at close and only counted (`_unbind`). The MCS meanwhile shows SENT.
- **Why it matters.** A TC that executes 25 s after the operator gave up on it is a classic ops hazard.
- **Fix:**
  - Stamp each TC frame with the GSG send time (inside the MAC, see H2). The agent drops TCs older than a TTL (for example 5 s, or a value set per session), corrected by the clock offset, and NOTICEs the drop.
  - The GSG treats `silence > 2 × ping_interval` (DEGRADED) as "refuse TC": it RSTs clients and refuses connects.

### M6. Credential replay after a GSG restart [CONFIRMED]
- **Where:** `NonceCache` is in-memory (`auth.py:107`).
- **Repro.** A header accepted by one `Verifier` is accepted again by a fresh one (`t_misc.py`). Anyone who saw a header in the last 120 s (plaintext LB→GSG, a debug proxy) can replay it after a GSG restart or redeploy. That person then supersedes the real agent: they receive operators' TCs and proxied requests with cookies (H3), and they inject TM, STATE and dumps until the real agent supersedes them back.
- **Fix:** a server challenge (H2.1) removes this whole class. Otherwise, persist the nonce cache, or refuse `ts < gsg_start_time`.

---

## 3. LOW

| # | Where | Issue → fix |
|---|---|---|
| L1 | `gateway.py:420-428` | **Concurrent supersede race:** two valid HELLOs during `await old.close()` leave an orphan connection that stays open and "bound" from the agent's view while its frames are ignored. Serialise binds with an `asyncio.Lock`. |
| L2 | `gateway.py:428`, `467-471` | TCs queued on a **superseded** connection are dropped with no counter and no NOTICE, because `_unbind` is skipped. Count and log `old.dropped_on_close[P_TC]`. |
| L3 | `gateway.py:334,343` | A TC record with `n > 65526` makes `P.encode` raise `ValueError`, which is not caught: the task errors and the client gets a FIN. Cap at `MAX_PAYLOAD-2` and RST. |
| L4 | `agent.py:305` | The agent writes the GSG payload to the sim **without validating framing** (`split_records` is used only for counting). One bad frame would desynchronise the sim TC stream, so following bytes are parsed as commands. Write only if the payload parses into whole records and the TC seq is the expected one. |
| L5 | `gateway.py:51-57` | `DUMP_NAME_RE` uses `$`, which accepts a trailing `\n` (confirmed). Use `re.fullmatch` and `\d` with `re.ASCII`. |
| L6 | `auth.py:47`, `Verifier` | A 16-byte secret is accepted (the spec says 32). `Verifier(secret=b"")` is accepted programmatically. Require ≥ 32 bytes in `Verifier.__init__`. |
| L7 | `agent.py:559`, `gateway.py:629` | `--secret` on the command line is visible in `ps` and in shell history. Drop the flag, or warn. |
| L8 | `gateway.py:120-129,273` | A `TmClient.run` task that dies on a reset is never awaited ("exception never retrieved"). The client stays registered until the reader sees EOF. Add a done-callback that removes and closes it. |
| L9 | `replay.py`, `agent.py:67` | The replay window (10 s or 2 MiB) is shorter than the dead-link detection (about 30 s). "complete" mode loses (and correctly GAP-flags) up to about 20 s at high rate. Size the replay at ≥ `dead_after` + 10 s, or 16 MiB. |
| L10 | `gateway.py:430-440` | After a **GSG restart**, frames lost in flight are not reported: the instance is unknown, so `resume_from=None` and `_tm_expected=None`. Persist `(instance, expected)`, or have the agent always send `tm_next_seq` and let the GSG flag a GAP. |
| L11 | `httpproxy.py:98-112`, `gateway.py:366` | `Origin == Host` is not proof against DNS rebinding. Also check `Host` against an allowlist. `/link-status` (peer IP, config hash, session) is served unauthenticated on 8080. |
| L12 | `mux.py:273-274` | Busy-wait at 5 ms while the write buffer is high. Acceptable; prefer awaiting `drain()`. The `_transport_buffer_size` fallback of 0 silently disables back-pressure if aiohttp internals change: log once when it fails. |

**Design note (performance, not security).** Each instructor tab's `/ws` is proxied transparently, which costs about 11 kB/s of link bandwidth per tab at PROXY priority. LINK_INTERFACES §3.2 recommends synthesising `state_update` locally from STATE.

---

## 4. Checked and solid

- **Auth ordering:** verification happens **before** the WebSocket upgrade (`gateway.py:389-393`), so an unauthenticated peer can't reach HELLO, TC, proxy or bind.
  - The signature is checked first, with `hmac.compare_digest`.
  - A nonce is recorded only after a valid signature, so the cache can't be filled without the secret.
  - The cache is bounded at 100 k with TTL eviction.
  - Session and nonce are regex-checked, and the session id is bound in both the signature and HELLO.
- **Supersede:** impossible without the secret (except through M6 replay).
- **Fail closed:** the GSG and agent exit when the secret or session is missing or malformed (`config_from_args`). The token goes only in the `Authorization` header and is never logged. `GatewayConfig.secret` has `repr=False`.
- **Deny-list core:**
  - percent-decodes twice and handles `..` escape, `//`, `%2F`, backslash, NUL and case;
  - the agent re-checks it (defence in depth);
  - there are no method-override semantics in aiohttp.
  - Every confedit write route sits under `/api/config/`, and the WS `/ws` command set has no config writes.
- **Proxy hygiene:**
  - hop-by-hop headers and `Connection`-listed tokens are stripped;
  - the agent drops `Content-Length` and `Transfer-Encoding` and lets aiohttp re-frame, so there is no request smuggling;
  - the upstream authority is fixed (`sim_base + path`, and the path must start with `/`), so there is no SSRF;
  - request body cap 8 MiB, WS message cap 4 MiB;
  - credit-based sending, and the GSG returns credit only as the client drains.
- **Codec:** strict version, type and size checks. Text messages are rejected. Unknown streams get a CLOSE. Sequence numbers use RFC 1982 arithmetic.
- **TC:**
  - never replayed, and the queue is cleared on close (`mux.py:208-210`);
  - one global seq;
  - arrival order across local clients is preserved per record;
  - the agent ignores TC data on any stream other than 1, and the GSG ignores stream 1 from the agent;
  - RST with SO_LINGER 0 when DOWN, for new and existing clients.
- **TM:**
  - per-client writer tasks with drop-oldest, so one slow client can't block another, and clients are never disconnected;
  - duplicate and loss detection by seq;
  - resync on GAP or CONT;
  - frames always carry whole records except the oversized-record CONT path;
  - instance-scoped resume;
  - the agent reads the sim socket promptly.
- **Clock:**
  - the sign conventions are correct (offset = agent − GSG; age = now − (t_agent − offset));
  - negative age is clamped;
  - paused or zero speed means no advance;
  - staleness is measured on GSG monotonic receipt time, with 503 after 5 s.
- **Dumps:** names are validated by regex (no traversal possible), written to a `.part-` file, then fsync, size and sha256 check, `os.replace` and `utime`. An existing name with the same hash is acked without a rewrite, and a conflict is refused.
- **Binds in code:** TM, TC and HTTP default to `127.0.0.1`; only the link listens on 0.0.0.0, and it serves only `/link` and `/healthz`.

---

# Re-review 2026-10-29 (protocol v2, package 0.2.0)

**Scope:**
- `LINK_REVIEW_RESPONSE.md`;
- `LINK_DESIGN.md` §3 (v2);
- `channel.py`, and the changed `mux.py`, `gateway.py`, `agent.py`, `httpproxy.py` and `protocol.py`;
- `docker/compose.yaml`;
- `tests/test_link/test_security.py`.

**Baseline:** `tests/test_link/{test_security,test_unit,test_component}.py` gave **159 passed** in 24 s. `test_e2e.py` was not run, because another agent is editing it.

**New adversarial scripts** (in the same scratchpad folder, read-only against the repo):

| Script | What it does |
|---|---|
| `harness2.py` | A v2 fake agent that does the mutual handshake and seals frames itself, so it can also mis-seal them |
| `t2_channel.py` | Reflection, replay, reorder, truncation, bit-flip, unsealed injection, supersede with a silent old agent, wrong-label MAC, reflected nonce, AUTH sent in a v1 frame |
| `t2_allowlist.py` | 35 crafted request lines through a real GSG and a real Agent to a mock sim that has the config, report and dot-file routes |
| `t2_headers.py` | Request and response header allowlists |
| `t2_preauth_dos.py`, `t2_401.py` | Pre-auth slot exhaustion |
| `t2_ttl.py` | Agent-side TC TTL under agent clock steps |

## R1. Original findings

| # | Verdict | Evidence |
|---|---|---|
| H1 FIN instead of RST | **VERIFIED FIXED** | <ul><li>`t2_channel.py`, supersede while the old agent is silent: B's WELCOME arrives in **0.01 s** (v1: about 5 s), and the MCS-style TC client is already reset.</li><li>Every integrity failure (reflection, replay, reorder, truncation, bit-flip, unsealed frame) resets the TC client within about 0.6 s.</li><li>The code paths now RST: `LinkConnection.abort()` runs `on_close` synchronously, as do `_handle_tc` (default `abort=True`), `stop()` and the 0.25 s watchdog.</li><li>Residual: a GSG crash (SIGKILL or OOM) still gives the kernel's FIN. This is unavoidable here and should be fixed in the MCS (read the TC socket for EOF).</li></ul> |
| H2 channel not authenticated | **VERIFIED FIXED** (integrity and authenticity) | <ul><li>The labels are distinct and prefix-free (`…/v2/agent`, `…/v2/gsg`, `…/v2/k_a2g`, `…/v2/k_g2a`, and the v1 header's `v1\n…`). The session is length-prefixed and the nonce order differs per direction.</li><li>Keys are per-direction and per-connection, with a fresh pair of 32-byte nonces each time. The tag covers the direction label, a u64 implicit counter, the header and the payload, and is compared with `compare_digest`.</li><li>Attacks refused:<ul><li>a GSG frame reflected back to the GSG;</li><li>an agent MAC computed with the GSG label (4401);</li><li>`nonce_a == nonce_g` (4401);</li><li>AUTH in a v1 frame (4002);</li><li>a v1 header (401, per the tests);</li><li>replay, reorder, truncation, bit-flip and unsealed frames (link closed, TC reset).</li></ul></li><li>The agent verifies `mac_g` before HELLO, so a rogue GSG only ever receives AUTH.</li><li>A relaying MITM gains nothing beyond what follows: it can drop frames (the link dies) or delay them (bounded by the TC TTL, see N2).</li><li>The counter cannot desync across reconnects, because every connection has new keys.</li><li>Confidentiality on the LB→GSG hop is still **open, and documented as deferred**.</li></ul> |
| H3 credentials and response headers | **VERIFIED FIXED** | <ul><li>`t2_headers.py`: the agent received only `User-Agent` and `Origin: checked`. Cookie, Authorization, the IAP JWT, X-Forwarded-For, Forwarded and X-HTTP-Method-Override were dropped.</li><li>`Set-Cookie`, `Location`, `Link`, CORS and the agent's own CSP were dropped. A CR/LF reason phrase was ignored. nosniff, CSP, XFO and CORP were added.</li><li>**Residual (LOW, documented):** a hostile space side can still return `text/html` with inline script on any allowlisted route, because CSP allows `'unsafe-inline'`. See N4.</li></ul> |
| H4 compose binds | **VERIFIED FIXED** | <ul><li>All four published ports use `${SMO_PUBLISH_ADDR:-127.0.0.1}`.</li><li>GSG TM/TC bind 127.0.0.1 in the shared namespace.</li><li>`local-demo` sets `SMO_LINK_ALLOW_INSECURE=1` explicitly.</li><li>The simulator still binds 0.0.0.0 inside its container (deferred; nothing beyond host loopback is published).</li></ul> |
| M1 deny-list bypass | **VERIFIED FIXED** | <ul><li>`t2_allowlist.py`, end to end: **0 hits** on `/config`, `/api/config/*`, `POST /api/reports/{generate,validate}` and `/static/.secret` across 35 variants: `#`, `%23`, `;`, `%3b`, `..`, `%2e%2e`, `%2f`, `%252e`, `//`, `/./`, case, absolute-form, backslash, NUL, non-ASCII, a WS upgrade to a non-`/ws` path, OPTIONS, POST on read routes.</li><li>The only sim hits were allowlisted `/static/a` requests.</li><li>The agent re-checks the canonical path and the final `URL.build(encoded=True)`.</li></ul> |
| M2 handler exceptions | **VERIFIED FIXED** | `_dispatch_safe` isolates each frame. Only tag, decode and text-frame violations close the link. Strict JSON via `loads_obj` and `parse_constant`. The dump `OSError` path gives a NACK. Tests pass, and the code was re-read |
| M3 resource exhaustion | **VERIFIED FIXED** | <ul><li>Receive credit (`_rx_budget`, giving `StreamViolation` and a 1008 on that stream only).</li><li>WINDOW grant capped at 4× the window.</li><li>`recv_message(max_size)`.</li><li>TM client byte cap.</li><li>Dumps: per-file, in-flight and free-disk limits.</li><li>GSG `_tm_buf` cap.</li></ul> |
| M4 link-port DoS and logs | **PARTIAL** | <ul><li>Half-open connections are now reaped after 10 s (`timeouts=128` in `t2_preauth_dos.py`).</li><li>A malformed `sig` gives 401, never 500.</li><li>Logs are rate-limited.</li><li>**But the global cap of 64 lets an unauthenticated attacker lock out the real agent:** see N1.</li></ul> |
| M5 stale TC | **PARTIAL** | <ul><li>The GSG queue deadline (monotonic, checked at pop) is correct.</li><li>DEGRADED counts as DOWN for TC, with RST.</li><li>The 8-byte stamp is inside the MAC.</li><li>**But the agent-side age check fails open on an agent clock step:** see N2.</li></ul> |
| M6 header replay | **VERIFIED FIXED** | A replayed header only passes the filter. Binding needs `mac_a` over a fresh `nonce_g`, and the test was re-read |
| L1 bind race | VERIFIED FIXED | There is no `await` between `old.abort()` and `self.link = conn` |
| L2 TCs dropped on supersede | VERIFIED FIXED | Supersede now goes through `_unbind` |
| L3 oversized TC record | VERIFIED FIXED | `MAX_TC_RECORD` 65 518, enforced with an RST |
| L4 agent TC framing | VERIFIED FIXED | Only whole records are written. The implicit counter replaces the seq check |
| L5 dump name `\n` | VERIFIED FIXED | Uses `fullmatch` with ASCII |
| L6 short secret | VERIFIED FIXED | ≥ 32 bytes required |
| L7 `--secret` on the command line | MITIGATED | A warning is logged |
| L8 TmClient task exceptions | VERIFIED FIXED | Done-callback (code read) |
| L9 replay window | VERIFIED FIXED | 40 s / 16 MiB |
| L10 TM loss on GSG restart | PARTIAL (accepted) | Now logged as `tm-continuity-unknown` |
| L11 DNS rebinding | VERIFIED FIXED | Host allowlist (IP literals, localhost, configured names) |
| L12 back-pressure | VERIFIED FIXED | Room is awaited before the frame is chosen, and an unreadable buffer size is logged |

## R2. New findings

### N1 — MEDIUM (availability, fails safe): unauthenticated pre-auth slot exhaustion locks out the agent [CONFIRMED]
- **Where:** `gateway.py:211-228` `PreAuthGuard.admit` refuses the **newest** connection once `max_total` (64) is reached. A connection is released only on authentication, close or the 10 s timeout. **A completed 401 stays pending on keep-alive** until the timeout (`t2_401.py`).
- **Repro (direct):** `t2_preauth_dos.py`. Four source addresses, 16 half-open connections each, reopened as they are reaped (about 115 per minute per address, just under the 120 limit). The legitimate agent bound **2 of 25 times** in 25 s.
- **Repro (well-formed requests):** `t2_401.py`. Seventy well-formed upgrade requests with a junk credential got 401, yet still held all 64 slots, and the legitimate bind failed (`ServerDisconnectedError`). These requests pass any load balancer, so the GCP firewall alone does not stop this. It depends on how many backend connections the GFE opens, and Cloud Armor is the documented mitigation.
- **Per-IP cap behind the LB.** Behind the LB the per-IP limits key on Google front-end addresses, which the attacker and the agent share.
- **Impact:** the link stays DOWN, and TC is refused with RST, so the failure is safe. There is no integrity impact.
- **Fix:**
  1. Close the connection right after any 401 (`Connection: close`, then `transport.close()`), so a refused request never holds a slot.
  2. When the cap is full, **evict the oldest pending** connection instead of refusing the new one. A real agent finishes its handshake in one RTT, so the attacker would need more than 64 new connections per RTT.
  3. Keep per-IP limits off (or high) when `SMO_GSG_BEHIND_LB=1`, and rely on Cloud Armor.

### N2 — LOW (a defence layer fails open): agent-side TC TTL is defeated by an agent wall-clock step [CONFIRMED]
- **Where:** `agent.py:315-341` computes `age = time.time() + offset − stamp`.
  - The offset comes from `ClockEstimator` (minimum delay of the last 8 samples, `clock.py`), which mixes the agent **wall** clock into the estimate.
  - There is no lower bound on age, so a stamp from the future is accepted.
- **Repro** (`t2_ttl.py`), with 8 PING samples taken first:
  - After the agent clock steps **back 30 s**, a **20 s old TC is DELIVERED**.
  - After 7 more post-step samples, the estimator still reports offset 0.0 (the true offset is +30), and stale TCs are still delivered. This lasts up to 8 pings, about 80 s.
  - A forward step makes every fresh TC `tc-expired`, which is an availability problem.
- **Triggers:** an NTP correction, or a laptop waking from sleep. The GSG's monotonic queue deadline still holds, so a stale TC needs this clock step **plus** network or kernel delay, or an on-path delayer combined with spoofed NTP on a student network.
- **Fix:**
  - Anchor the offset to the agent's **monotonic** clock: sample `gsg_wall − agent_monotonic` in PONG handling, and compute `gsg_now = monotonic() + off`.
  - Drop estimator samples older than about 30 s, or reset the estimator when consecutive samples disagree by more than 1 s.
  - Also refuse `age < −TTL` (a stamp from the future).

### N3 — LOW: the agent-side sim-TC refusal does not reach the MCS
When the agent's simulator TC socket is down, TCs are refused with a `tc-discarded` NOTICE that the GSG only logs. The MCS TC socket stays open and the MCS shows SENT. This is the same as "simulator TC port closed" today, so it is not a regression.

**Fix:** let the agent report `sim_tc: up|down` in STATUS or NOTICE, and have the GSG treat `down` like DEGRADED (RST the clients).

### N4 — LOW (residual, documented): hostile space side can run script on the proxy origin
`t2_headers.py`: `text/html` plus an inline `<script>` on `/api/instructor/snapshot` was served, and CSP `'unsafe-inline'` lets it run.

`connect-src` and `form-action 'self'` and the header filters mean it can only talk back to the same (attacker's) sim. The remaining risk is navigation or phishing in the instructor's tab.

**Fix:**
- Serve the proxy on its own host with host-only cookies (already required by §3.7).
- Add `Content-Security-Policy: sandbox` to `/api/*` and `/dumps`/`/reports` downloads, and force `application/json` on `/api/*` responses.
- Plan nonce-based CSP for the consoles.

### N5 — INFO
- **Allowed `Content-Disposition`** lets the space side force a download with any filename. Harmless with nosniff and CSP.
- **`host_is_private` accepts RFC 1918 hosts for `ws://`.** On a campus 10/8 network that is plaintext but still integrity-protected. This is acceptable, and the deferred confidentiality item covers it.

## R3. Verdict

**Acceptable to carry telecommands in a teaching deployment behind the GCP edge**, on these conditions:
1. The deployment follows `deploy/gcp/README.md`: TLS at the LB, the VM firewall limited to LB and IAP ranges, `SMO_PUBLISH_ADDR` set to the internal IP, and the proxy on its own IAP-protected host.
2. The Cloud Armor per-client rate limit is enabled on `/link` until N1 is fixed.
3. N1 and N2 are scheduled. Both are small changes.

**Why it is acceptable.** No path was found for anyone without the session secret to:
- bind;
- inject, replay, reorder or reflect a frame;
- reach a non-allowlisted simulator route;
- obtain ground credentials.

Every link-integrity failure resets the MCS TC socket within about 0.6 s.

**What remains:**
- availability, through N1;
- a fail-open corner of the second TTL layer (N2), which the GSG's own queue TTL already covers;
- confidentiality inside the VPC (deferred).

**Not acceptable as-is for a real ground station or flight hardware.** That would need confidentiality to the GSG (TLS or AEAD), N1 and N2 fixed, an MCS that detects TC socket EOF, per-operator authorisation of TCs, and an independent penetration test.
