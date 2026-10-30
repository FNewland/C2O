# Space link: research for the sim → cloud ground-station gateway

Compiled 2026-10-29 for the SMO suite's "space link". A Python client (asyncio + aiohttp) beside the simulator dials
**out** over WSS:443, through campus or home NAT, Google Cloud's **global external Application Load Balancer** (ALB) and
IAP, to a cloud **ground-station gateway (GSG)**. The GSG re-exposes the sim's TM/TC TCP sockets, the state JSON, the
instructor console and delayed-TM dump files to unchanged ground software.

This document goes deeper on §B.2 of `WEB_OPTIONS_RESEARCH.md`, and it changes one assumption there: **TLS is
terminated by the GCP load balancer, not Caddy.**

Legend: **[V]** verified against the cited primary source today. **[S]** checked in source code or measured locally.
**[J]** engineering judgement. **[U]** not verified, so check before relying on it.

---

## 0. Recommendations at a glance

| Topic | Recommendation |
|---|---|
| Transport | One WSS connection per sim. Binary messages only. **One WS message = one link frame.** No compression. `max_msg_size` = 1 MiB on both sides. Frames ≤ 64 KiB, bulk chunks ≤ 16 KiB. |
| Frame | An **8-byte header**: `ver/type (1) · flags (1) · stream (2) · seq (4)`, then the payload. It is the same size as smux and SLE ISP1, and the WS message already carries the length (§1.4). |
| Streams | Static IDs: 0 control, 1 TC, 2 TM-realtime, 3 STATE, 4 dump/file, 5 clock. Dynamic IDs ≥ 256 for proxied HTTP requests and nested WebSockets. |
| Flow control | **Credit windows (yamux/muxado style) only on bulk and dynamic streams** (dumps, HTTP bodies, nested WS). TM-realtime uses SLE **online-timely** semantics: transfer buffer + latency limit + discard-with-notification. TC is tiny and never windowed. |
| Priority | One writer task with **strict priority**: control/clock > TC > TM-RT > STATE > HTTP > dumps. It feeds the socket only while the transport buffer is below ~64 KiB, so urgent frames can overtake bulk. |
| Keepalive | **Global** external ALB, not Classic. Set the link backend service `timeoutSec` to **3600** (idle WS are cut at this value, default **30 s**). Send an app-level PING every **10 s**, which also gives a clock sample. aiohttp `heartbeat=20` as dead-peer detection. Expect a forced close **≤ 24 h** and at any GFE maintenance. |
| Reconnect | Full-jitter exponential backoff: base 0.5 s, cap 30 s, reset after 60 s stable. Resume with HELLO carrying `session_id` + last received seq per stream. |
| Delivery | TM-RT: **online-timely** (bounded replay ≤ 10 s / 2 MiB, then a GAP notice). Dumps: **online-complete / offline**, resumable by `(file_id, offset)`. **TC: at-most-once. Never replay.** Discard queued TCs on link loss and report it, as FCLTU does. |
| Clock | NTP 4-timestamp exchange every 10 s. Keep the last 8 samples and use the **minimum-delay** one (RFC 5905 clock filter). Publish a `sim_time` anchor `{gw_wall, sim_time, rate, ±err}`. |
| Auth | The `/link` path goes to a **separate backend service without IAP**. IAP is per backend service, and IAP checks a WS only at upgrade. The link uses its own **per-team link secret** with an ISP1/"Protected-1"-style HMAC credential in the upgrade header (§4.4). IAP stays on the console, MCS and planner paths. mTLS is supported by GCP but kept for later. |
| Hosting | Debian + Docker CE + compose plugin on Compute Engine. No external IP, IAP-TCP SSH, Cloud NAT for egress. One image with several entrypoints, compose profiles `space` / `ground`. No Caddy. |
| Impaired-net tests | **Toxiproxy** (unprivileged Go binary or container, v2.13.0, 2026-10-14), driven by its REST API from pytest, plus a ~80-line **in-process asyncio fault proxy** for deterministic unit tests. `tc netem` only for manual or privileged runs. |

---

## 1. Multiplexing many logical channels over one WebSocket

### 1.1 Prior art

| Project | Transport / mux | Frame header | Flow control | Notes |
|---|---|---|---|---|
| **chisel** | SSH (Go `crypto/ssh`) inside one WebSocket (gorilla/websocket) [V go.mod] | SSH channel framing | SSH per-channel windows | Default keepalive **25 s**, "to stay under CDN idle timeouts". Auto-reconnect with exponential backoff. Keepalive pings now time out so dead links reconnect [V README]. SSH adds a second crypto layer, which is unnecessary when the LB already terminates TLS. |
| **wstunnel** | **One WS (or HTTP/2) connection per tunnelled TCP connection**, i.e. no mux. A pool of pre-opened connections hides setup latency (`--connection-min-idle`) [V README] | n/a | TCP's own | Default WS ping **30 s**. Warns that HTTP/2 transport rarely survives reverse proxies, which buffer or downgrade it [V README]. One WS per channel would multiply LB connections and IAP checks, so it is not a fit here. |
| **frp** | Control + data connections multiplexed by **yamux** (`fatedier/yamux` fork) [V go.mod]. `transport.protocol = "websocket"`/`"wss"`. `tcpMux` is on by default and is "like HTTP2 multiplexing" [V README] | yamux, 12 B | yamux per-stream window | The closest drop-in analogue. Shows that yamux-over-WS works through proxies. |
| **cloudflared** | **QUIC** by default (UDP 7844); falls back to **HTTP/2** over TCP 443 if UDP fails (`--protocol auto|http2|quic`) [V Cloudflare docs]. Control RPC is Cap'n Proto [V go.mod] | QUIC / H2 frames | QUIC/H2 flow control | Moved to QUIC to escape TCP head-of-line (HOL) blocking. That isn't available through a GCP HTTPS LB backend path. |
| **ngrok agent** | **muxado**, "the stream multiplexing protocol that powers ngrok's tunnels" [V docs.rs] | `uint24 Length · uint4 Type · bits4 Flags · uint32 StreamID` = **8 B**. Types RST / DATA / WNDINC / GOAWAY. Flags FIN, SYN [V PROTOCOL.md] | Per-stream `WNDINC` credit | The cleanest minimal spec. Streams open implicitly with a SYN-flagged DATA frame. |
| **yamux** (HashiCorp) | Any reliable stream | `ver(1) type(1) flags(2) streamID(4) length(4)` = **12 B**. Types Data / WindowUpdate / Ping / GoAway. Flags SYN / ACK / FIN / RST. Client uses odd IDs, server even, 0 = session [V spec.md] | **256 KiB initial per-stream window**, delta updates, no session window [V] | Ping carries an opaque value echoed back (RTT). GoAway codes: 0 normal, 1 protocol error, 2 internal [V]. |
| **smux** (xtaci) | Any reliable stream | `ver(1) cmd(1) len(2) streamID(4)` = **8 B**. Commands SYN / FIN / PSH / NOP / UPD [V README] | v2 adds per-stream sliding window, `UPD = consumed(4) window(4)` [V] | `MaxFrameSize`, `KeepAliveInterval/Timeout` and `MaxReceiveBuffer`/`MaxStreamBuffer` are the knobs [V]. |
| **SLE ISP1** (CCSDS 913.1-B-2) | One TCP connection per SLE association | **8-octet TML header** (message type + body length). Context message carries 'ISP1', version, heartbeat-interval and dead-factor. Heartbeat = header only, length 0 [V] | Relies on TCP backpressure ("flow control that notifies backpressure to the application layer") [V] | No mux: one association per connection. Its **heartbeat-interval × dead-factor** liveness rule is worth copying verbatim (§2.2). |
| **HTTP/2 over WS / WS over HTTP/2** | RFC 8441 (WS over H2 extended CONNECT) and RFC 9220 (WS over H3) | | | The GCP ALB **does** support RFC 8441 to the backend [V LB doc], but there is no maintained Python H2-in-WS mux. Re-implementing H2 framing, HPACK and priorities is far beyond "minimal". |

**Python mux libraries.** No maintained, general-purpose "multiplexed websocket" library for asyncio turned up. Search
hits are Rust (`yamux`, `muxado`) and Go crates, plus one vendored private `_yamux` module inside LangSmith's sandbox
SDK [U: not a public dependency]. **[J] Write the mux in about 400 lines.** It is the core of the link, and it must
encode SLE semantics (timely/complete, TC never replayed) that no generic library has.

### 1.2 Head-of-line blocking: what matters here

- Everything on one TCP connection is FIFO **once it leaves user space**. A 1 MiB dump chunk already in the kernel send
  buffer delays every TC or TM frame queued behind it. This is why cloudflared moved to QUIC. Through a GCP HTTPS LB
  we can't, so **HOL has to be bounded in the sender** [J].
- The **traffic is asymmetric**, which helps:
  - *cloud → sim* (downlink of the tunnel) carries TC, HTTP requests, ACKs and credits, all small. HOL is negligible
    here.
  - *sim → cloud* carries TM, STATE, dumps and HTTP response bodies. Dumps and console assets compete with real-time
    TM. This is the direction that needs priority.
- Bounding technique [J, standard]:
  1. Put all priority logic **before** `ws.send_bytes()`, in one writer task over per-class queues.
  2. Only hand a frame to aiohttp while `transport.get_write_buffer_size()` < ~64 KiB.
  3. Chunk bulk data to ≤ 16 KiB. At a 1 Mbit/s home uplink, one 16 KiB chunk is ~131 ms of HOL in the worst case.
     8 KiB halves that.
  4. Optional, Linux only: `TCP_NOTSENT_LOWAT` (option 25) limits unsent bytes in the kernel buffer. Cloudflare uses
     it for HTTP/2 prioritisation [Cloudflare blog]. Python 3.13 does **not** expose a named constant (checked
     locally), so it would need `setsockopt(IPPROTO_TCP, 25, 16384)` on the aiohttp transport's socket. **[U]** The
     benefit through home routers hasn't been measured.
- aiohttp itself only awaits drain when its per-writer counter exceeds `limit` **and** the protocol is paused [S:
  `_websocket/writer.py` in 3.14.5]. The client's default limit is `DEFAULT_CHUNK_SIZE` = 256 KiB; the server's
  `writer_limit` is 64 KiB [V/S]. So `await ws.send_bytes()` usually returns immediately. **It is not a scheduler.**

### 1.3 Flow control and priority design

| Stream class | Flow control | On congestion | Priority |
|---|---|---|---|
| 0 CONTROL (HELLO, BIND/START/STOP, GOAWAY, ACK, CREDIT) | none | never dropped | 0 (highest) |
| 5 CLOCK (PING/PONG with timestamps) | none | never dropped (queue of 1, newest wins) | 0 |
| 1 TC (cloud→sim) | none (≤ a few kB/s) | **never replayed**; discarded and reported on link loss | 1 |
| 2 TM-RT (sim→cloud) | **SLE online-timely**: transfer buffer (e.g. 16 KiB) released on full **or latency limit** (e.g. 50 ms). Bounded backlog (e.g. 2 MiB or 10 s) | discard the **oldest whole transfer buffer**, set GAP flag + count on the next frame ("data discarded due to excessive backlog") | 2 |
| 3 STATE JSON (1 Hz) | none | **latest-only** (queue depth 1) | 3 |
| ≥ 256 HTTP / nested WS | **credit window** (yamux: initial 256 KiB; CREDIT when the consumer drains half) | the sender blocks on credit, so the browser sees a slow response | 4 |
| 4 DUMP / FILE | **credit window** (256 KiB–1 MiB) | blocks; resumable by offset | 5 (lowest) |

Use **strict priority**. Bulk only gets bandwidth that real-time traffic doesn't use. That is right here because TM-RT
is kB/s and STATE is ~1 kB/s, so bulk can't starve in practice [J]. For safety, add a starvation guard, e.g. one bulk
frame after every 32 higher-priority frames.

### 1.4 Recommended frame format (v1)

One WebSocket **binary message** = one frame. The WS layer already gives the message length, so the header has no
length field. All integers are big-endian, as in ISP1 and yamux.

```
 0               1               2               3
 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7
+-------+-------+---------------+-------------------------------+
|  ver  | type  |     flags     |           stream (u16)        |
+-------+-------+---------------+-------------------------------+
|                          seq (u32)                            |
+---------------------------------------------------------------+
|                     payload (0 .. 64 KiB)                     |
```

- `ver` = 1.
- `type`:

  | Value | Type | Meaning |
  |---|---|---|
  | 0 | DATA | stream data |
  | 1 | ACK | `seq` = cumulative last-received seq on `stream` |
  | 2 | CREDIT | `seq` = window increment in bytes |
  | 3 | OPEN | payload = JSON: kind `http`/`ws`/`file`, method, path, headers… |
  | 4 | CLOSE | half-close (FIN). Payload optional: status/close code |
  | 5 | RESET | payload = u32 error code |
  | 6 | PING | payload = `t1` u64 ns |
  | 7 | PONG | payload = `t1, t2, t3` u64 ns |
  | 8 | CTRL | payload = JSON control message (HELLO, BIND, START, STOP, UNBIND, GOAWAY, STATUS) |

- `flags`:

  | Bit | Flag | Meaning |
  |---|---|---|
  | 0x01 | FIN | |
  | 0x02 | GAP | frames were discarded before this one; payload is prefixed with u32 discarded-count |
  | 0x04 | TEXT | nested-WS opcode was text |
  | 0x08 | LAST_CHUNK | end of a file |
  | 0x10 | URGENT | reserved |

- `stream` IDs: 0 control, 1 TC, 2 TM-RT, 3 STATE, 4 DUMP, 5 CLOCK, 6–255 reserved. Dynamic IDs ≥ 256: the **GSG
  allocates even IDs, the client odd IDs** (the yamux rule).
- `seq`: a per-stream frame counter (mod 2³²) for DATA. ACK and CREDIT reuse the field as shown above.
- **TM/TC payload** = one or more complete records, each `[u16 len][CCSDS packet]`, **byte-identical to the sim's TCP
  framing**. The GSG writes them verbatim to its local 8002 clients; the client writes TC verbatim to the sim's 8001.
  Batching several packets into one frame is the SLE RAF **transfer buffer** (several TRANSFER-DATA in one
  `RafTransferBuffer` PDU, released when full or when the **latency limit** release timer expires) [V 911.1-B-5
  §2.6.4.6.2].

**Byte-level example.** An 18-byte TM packet `08 64 C0 2A 00 0B …` (APID 0x064, seq count 42, data length 11)
travels as DATA on stream 2, frame seq 1000:

```
10 00 00 02 00 00 03 E8   00 12   08 64 C0 2A 00 0B 20 03 19 00 00 00 00 01 2C 00 00 00
^^ ver=1,type=0 (DATA)    ^^^^^   ^^^^^^^^^^^^^^^^^^^ 18-byte CCSDS/PUS packet …
   ^^ flags=0             u16 len=18
      ^^^^^ stream=2 (TM-RT)
            ^^^^^^^^^^^ seq=1000
```

The GSG acknowledges cumulatively, which frees the client's replay buffer up to 1000:

```
11 00 00 02 00 00 03 E8         ver=1,type=1 (ACK), stream 2, seq 1000
```

After the client discarded 37 frames under backlog, the next TM frame says so (SLE "data discarded" sync-notify):

```
10 02 00 02 00 00 04 0E  00 00 00 25  00 12 08 64 …   flags=GAP, seq=1038, discarded=37
```

A TC frame (cloud→sim), stream 1, TC link-seq 57:

```
10 00 00 01 00 00 00 39  00 0F  18 C8 C0 05 00 08 …   one 15-byte PUS-C TC
```

The client answers on the control stream with
`CTRL {"op":"TC_STATUS","seq":57,"status":"radiated","t":…}`. This is the analogue of the FCLTU
"radiated" notification.

Overhead is 8 B per frame, plus 2–14 B of WS header, plus ~29 B of TLS record overhead. That is negligible at
kB/s–1 Mbit/s.

Why not reuse yamux's exact wire format? There is no maintained asyncio implementation, and its 12-byte header
duplicates the WS length. More importantly, a per-stream **seq/ACK** for resumption and a **GAP** flag are needed;
neither yamux nor muxado has these because they assume the underlying stream never breaks [J].

---

## 2. Reliability

### 2.1 GCP load balancer facts that set the numbers **[V]**

From *Request distribution for external ALBs → Timeouts and retries* and *External ALB overview*:

- **The backend service timeout is 30 s by default.**
  - **Global external ALB:** "Active websocket connections don't use the configured backend service timeout… closed
    after **24 hours** (86,400 seconds)… **Idle websocket connections are closed after the backend service times
    out**."
  - **Classic ALB:** "Websocket connections, **whether idle or active**, automatically close after the backend service
    times out."
  - **Regional external ALB:** same idle rule, but it uses `routeAction.timeout` if that is set.
- "Google Cloud doesn't guarantee that an underlying TCP connection can remain open for the entirety of the value of
  the backend service timeout… **Client systems must implement retry logic**." GFEs restart for maintenance, so a
  higher timeout makes a maintenance cut more likely.
- Client HTTP keepalive timeout is 610 s and backend keepalive 600 s (fixed). The 60-minute max-age close of client
  connections "doesn't interfere with… upgraded WebSocket connections".
- The ALB supports WebSocket over HTTP/1.1 Upgrade **and** RFC 8441 over HTTP/2 with no configuration. Session affinity
  works as for HTTP. A 426/502 from the backend is passed through.
- Client request headers + URL are limited to **60 KiB** (global), which is ample for tokens.
- GFE source ranges for the backend firewall are **130.211.0.0/22** and **35.191.0.0/16** (health checks come from
  35.191.0.0/16).

**Consequences [J]:**

1. Use the **global external ALB, not Classic.** On Classic every link would die at `timeoutSec`.
2. Give `/link` its own backend service with `timeoutSec = 3600`. That bounds how long a silently dead backend half
   lingers while staying far from 24 h. Then **guarantee traffic at least every 10 s in both directions.**
3. **[U]** The docs don't say whether a bare WS ping/pong control frame resets the GFE idle timer. It almost certainly
   does, since bytes cross the connection, but **app-level PING/PONG data frames** remove the doubt and double as clock
   samples.
4. Plan for a reconnect **at least daily** and at random maintenance. Make it invisible: resume, replay TM, warn on TC.

### 2.2 Heartbeats

- ISP1 (913.1-B-2 §2.5.3) [V]: send a heartbeat whenever nothing has been sent for `heartbeat-interval`. Declare the
  connection dead if nothing is received for `heartbeat-interval × dead-factor`. It explicitly rejects TCP keepalive
  because its default probe interval is ≥ 2 h.
- Typical defaults found: chisel 25 s, wstunnel 30 s, smux `KeepAliveInterval` (configurable) [V].
- **Recommended:**
  - App PING every **10 s** (clock + liveness), dead-factor 3, so dead after 30 s without any frame.
  - In addition, aiohttp `ws_connect(heartbeat=20)`. aiohttp pings every 20 s and fails if no PONG within
    `heartbeat/2` = 10 s. "The timer is reset on any inbound data reception" [V docs; S `client_ws.py`
    `_pong_heartbeat = heartbeat / 2`], so on a busy link it sends nothing extra.
  - On the GSG: `WebSocketResponse(heartbeat=20)`. The server doesn't ping by default ("you need to do this explicitly")
    [V].

### 2.3 Reconnect

- Use **Full Jitter**: `sleep = random(0, min(cap, base·2^attempt))`. AWS's analysis shows Full and Decorrelated Jitter
  both cut work sharply versus plain exponential, and calls Equal Jitter "the loser" [V AWS blog]. Parameters
  [J]: base 0.5 s, cap 30 s, reset `attempt` after 60 s of stable connection.
- Treat **401/403 at upgrade** as non-retryable without new credentials. Show it to the operator.
- On a CTRL GOAWAY with `reason:"maintenance"` or `"replaced"`, reconnect at once (one attempt, no backoff).
- **[J]** One link per team session: a new HELLO for a bound session **replaces** the old socket (newest wins). This
  avoids a zombie half-open socket blocking the reconnect. SLE instead rejects a second BIND with "already bound"
  [V 911.1-B-5 §4.2.1.5]. Accepting the replacement is better for flaky NAT, provided the credential checks out.

### 2.4 Session resumption, replay buffers, delivery semantics

HELLO (client→GSG, first frame):

```json
{"op":"HELLO","proto":1,"session":"team7-2026-10-29T13:00Z","resume":true,
 "rx":{"1":57,"0":812},"config_sha256":"…","sim_build":"…"}
```

The reply carries the GSG's last received seq for streams 2, 3, 4 and 0, and the last TC seq it **sent** with status
`unknown/radiated`.

| Stream | Semantics | Replay buffer | On resume |
|---|---|---|---|
| TM-RT (2) | **online-timely** (RAF) [V 911.1-B-5 §2.3, §2.6.4.6.2] | client ring of ≤ 10 s **and** ≤ 2 MiB [J] | resend frames after the GSG's ACKed seq if still buffered, otherwise one GAP frame with the count |
| DUMP (4) | **online-complete / offline**: files are already on disk, so they're idempotent | none; the file is the buffer | `OPEN file` with `{file_id, sha256, offset}`; GSG replies with the offset it has |
| STATE (3) | latest-value | 1 | send current |
| HTTP / nested WS | not resumable | — | RESET all; browsers retry; the console's WS reconnects itself |
| **TC (1)** | **at-most-once**. Never replayed | **none** | GSG reports every TC sent but not confirmed as `TC_STATUS unknown` to the MCS side. Any TC still queued at the GSG when the link dropped is **discarded** and reported |

Basis for "never replay telecommands":

- FCLTU: "When an association is released or aborted… production of CLTUs stops… **Any buffered CLTUs are discarded**"
  (except the opt-in protocol-abort-mode 'continue') [V 912.1-B-5 §2.6.4.4].
- FCLTU numbers CLTUs with a **monotonically increasing `cltu-identification`**. The provider returns the next
  expected ID and rejects anything out of sequence [V §3.6.2.5].

Copy both rules:

- The client keeps `last_tc_seq_delivered`. Any TC frame with `seq ≤ last` is **dropped and reported** (a duplicate),
  never delivered.
- **Idempotency [J]:** the link guarantees at-most-once. The *spacecraft* (PUS S1 acceptance/execution reports, using
  sequence counts) is the end-to-end truth. Operators re-send consciously; that is realistic ops, and good pedagogy.

### 2.5 SLE-flavoured link status to show the MCS

`UNBOUND → READY (bound) → ACTIVE (started)`, per the RAF/FCLTU state tables [V 911.1-B-5 Table 4-1] (§5). Map
`link up` = READY/ACTIVE. Inject a ground-station status (GS) packet or banner showing `LINK UP/DOWN/DEGRADED`,
RTT, discarded-frame count and clock uncertainty.

---

## 3. Clock: offset, latency and a published `sim_time` anchor

- **NTP on-wire** [V RFC 5905 §8]: with T1 (GSG send), T2 (client receive), T3 (client send), T4 (GSG receive):
  - offset θ = ½[(T2 − T1) + (T3 − T4)]
  - round-trip delay δ = (T4 − T1) − (T3 − T2)

  The error in θ is bounded by δ/2 when paths are asymmetric.
- **Cristian's algorithm** is the 2-timestamp special case (T2 = T3): `server_time + RTT/2`. Use the 4-timestamp form,
  because the client's processing time then drops out.
- **Filtering** [V RFC 5905 §10]: the clock filter keeps the **last 8 samples** in a shift register, **sorts by
  increasing δ** and uses the lowest-delay sample. Its dispersion weights later samples by 1/2^(i+1). Do the same: 8
  samples at 10 s gives an 80 s window. Use the min-δ sample's θ, with uncertainty `δ_min/2 + jitter`. Reject samples
  with δ > 3 × median [J, popcorn-spike style].
- **Which clocks.** Timestamp with the **wall clock** (`time.time_ns()`) for θ, since that is what you translate between.
  Use `time.monotonic_ns()` locally to age anchors [J]. The sim's **SIM TIME** and **ONBOARD TIME** stay separate (see
  the 2026-08 time-architecture work). The link only removes **transport** latency.
- **Publishing the anchor.** The client sends STATE with `sim_time_s` and `t_client_wall` (the instant `sim_time_s`
  was valid). The GSG converts this to its own wall clock, `t_gsg = t_client_wall − θ`, and publishes:

  ```json
  {"sim_time": 812345.250, "at_gw_wall": 1793300000.1234, "rate": 1.0,
   "err_s": 0.012, "rtt_s": 0.041, "link": "ACTIVE"}
  ```

  Any consumer computes `sim_now = sim_time + rate·(now_gw_wall − at_gw_wall)`. This is the "latency-corrected" sim
  time. `rate` is the sim speed factor; it is 0 when paused. Re-anchor on every STATE (1 Hz) and on every
  pause/speed change, which must also push an immediate STATE.
- TM packets keep their onboard CUC time untouched. The GSG may add an **ERT** (earth-receive time) annotation, the
  way RAF annotates frames with ERT [V 911.1-B-5 §1.6.1.7.4]. ERT = GSG receive time, or better, client capture time
  translated by θ.

---

## 4. Authentication

### 4.1 How IAP treats WebSockets and machines **[V]**

- "IAP only supports WebSocket for **initial requests** and doesn't continuously check authorization… After this, IAP
  does not monitor the requests or refresh the session" (IAP *sessions* how-to). An expiring credential doesn't kill
  an open link; only **reconnects** need a fresh one.
- Programmatic access accepts:
  1. a Google OIDC **ID token** with `aud` = the IAP OAuth client ID;
  2. an **OAuth access token** with `openid` + `email` scopes;
  3. a **service-account-signed JWT** with `aud` = the exact URL or `https://host/*` and `exp` ≤ `iat` + 3600.

  These go in `Authorization` **or `Proxy-Authorization`**. When IAP finds a valid credential in
  `Proxy-Authorization`, it uses that and **strips it**, leaving `Authorization` free for the app.
- User accounts: only Google identities are supported for programmatic access. Identity Platform and Workforce
  Identity Federation identities are not. Desktop apps need an allow-listed OAuth desktop client and a refresh-token
  flow.
- IAP is enabled **per backend service**: "only that backend service is protected by IAP".
- Behind IAP, apps should verify the **`x-goog-iap-jwt-assertion`** signed header in case IAP is bypassed.
- **IAP TCP forwarding** is for admin access (SSH/RDP) to VMs without external IPs. Firewall source is
  35.235.240.0/20; role `roles/iap.tunnelResourceAccessor`. It is **not** a path for the sim link.

### 4.2 Should `/link` sit behind IAP?

| Option | How | Verdict |
|---|---|---|
| A. `/link` behind IAP, service-account JWT | Each sim client holds a GCP service-account key, signs a JWT (≤ 1 h) and sends it in `Proxy-Authorization`; the app token goes in `Authorization` | Shipping SA keys to **students' laptops** is poor key hygiene. Fine only for **staff-owned** lab machines. |
| B. `/link` behind IAP, user OAuth desktop flow | The student signs in once (refresh token), the client mints ID tokens | Only works for Google identities, so it doesn't fit uOttawa Entra unless IT federates. Extra moving parts. |
| **C. `/link` on its own backend service *without* IAP + own link credential** | URL map: `/link` → `be-link` (port 9443 on the VM, serves only `/link`). Everything else → `be-apps` with IAP | **Recommended.** IAP adds nothing for a non-browser device beyond what a good link credential gives. Keep it on every human-facing path. |

Defence in depth for C [J]:

- `be-link` listens on a **separate port** that serves **only** `/link` and `/healthz`, so a URL-map mistake can't
  expose IAP-protected apps without IAP.
- Firewall the VM to GFE ranges only.
- Optional Cloud Armor rate-limit on `/link`.
- Refuse the upgrade unless the credential is valid, so there are no unauthenticated sockets.
- 5-second deadline for HELLO.

### 4.3 Token formats compared

| Scheme | Pros | Cons |
|---|---|---|
| **JWT HS256** | Trivial (PyJWT, the default algorithm) [V] | The verifier can also mint tokens. Algorithm-confusion pitfalls. Follow RFC 8725: pin `algorithms=[…]`, validate `iss`/`aud`/`typ` [V section list]. |
| **JWT EdDSA (Ed25519)** | Portal signs, GSG only verifies with the public key. PyJWT supports EdDSA [V] (2.15.1, 2026-09-28) | A bearer token. Replayable until `exp` unless `jti` is tracked. |
| **PASETO v4.public** | No algorithm agility, so no confusion. `pyseto` 1.10.0 (2026-07-19) [V PyPI] | One more dependency, and less familiar to students. |
| **HMAC challenge/signature with a shared per-team secret** | No clock dependency if challenge-response. This is the **SLE ISP1 / ISO "Protected-1"** scheme: hash over DER(time, random, user, password) with SHA-256, checked against an acceptable time window [V 913.1-B-2 §3.1] | Needs a secret store on the GSG (hash it with a KDF or keep it encrypted). |
| **mTLS at the GCP LB** | **Yes, supported** on global external, classic and regional external ALBs. Configured on the target HTTPS proxy via ServerTlsPolicy + TrustConfig. Modes `REJECT_INVALID` / `ALLOW_INVALID_OR_MISSING_CLIENT_CERT`. Cert fingerprint and validation results can be passed in custom headers [V mTLS overview] | It is per target proxy, so it applies to every hostname on that LB. Browsers would need `ALLOW_INVALID_OR_MISSING`, with the backend checking the header on `/link`. Running a PKI (issue, rotate, revoke) is real work for one maintainer. **Defer.** |

### 4.4 Recommended link credential (v1)

1. **Issue.** In the instructor portal, the instructor creates a team session and gets a **link secret** (32 random
   bytes, shown once, base64url) bound to `{team_id, session_id, not_after}`. The GSG stores
   `HMAC-SHA256(server_pepper, secret)` and the binding. Revoke or rotate with one click; rotation creates a new
   secret and the old one dies at the next reconnect.
2. **Present at every upgrade** (pre-upgrade, so a bad credential gets a plain 401 and no socket):

   ```
   Authorization: SMOLink v1 kid=<team_session_id>, ts=<unix_s>, nonce=<16B b64url>,
                  sig=<b64url(HMAC-SHA256(secret, "v1\n"+kid+"\n"+ts+"\n"+nonce+"\nGET /link\n"+host))>
   ```

   The GSG accepts if `|now − ts| ≤ 120 s`, the nonce wasn't seen within the window (an in-memory set of ~2 min),
   `kid` is active and `sig` verifies (constant-time compare). This is ISP1's Protected-1 idea with HMAC instead of a
   bare hash [J].
3. **Bind** the WS to `kid`. One active link per `kid` (newest wins, §2.3).
4. **Revocation of open sockets.** Since nothing re-checks after upgrade (as with IAP), the GSG pushes
   `CTRL GOAWAY {"reason":"revoked"}` and closes. It also re-validates `not_after` every minute.
5. If the portal later issues tokens to other services, swap step 2 for an **EdDSA JWT** (5-min `exp`, `aud="link"`,
   `sub=team_session_id`, `jti` tracked) fetched from the portal using the link secret. The wire stays the same.

Pitfalls [J]:

- Never put credentials in the **query string**. LB and app logs record URLs.
- Check `Origin` on browser-facing WS (console) to stop cross-site WebSocket hijacking. The link client is not a
  browser, so ignore Origin on `/link`.
- Pin the server certificate chain only if you control rotation. Google-managed certs rotate, so rely on normal CA
  validation.

---

## 5. CCSDS SLE: concepts to borrow (correct terminology)

Sources:

- **CCSDS 911.1-B-5** RAF (July 2023; supersedes B-4 Aug 2016, which is ISO 22669:2021)
- **CCSDS 912.1-B-5** FCLTU (July 2023)
- **CCSDS 913.1-B-2** ISP1 (Sept 2015)

All are free from ccsds.org.

- **Roles.** SLE service **user** (here the GSG, acting for the MCS) and **provider** (the station side, here the sim
  client). An **association** is formed by **BIND** and released by **UNBIND**, or aborted by **PEER-ABORT**. The
  **initiator** invokes BIND, the **responder** performs it. A given service instance is either user-initiated or
  provider-initiated, never both [V 911.1-B-5 §2.x, §1.6.1.7]. Our outbound-dial link is **provider-initiated BIND**,
  which SLE explicitly allows. Good pedagogy.
- **States** (provider state table, RAF Table 4-1) [V]: **1 Unbound → 2 Ready → 3 Active.** BIND moves to Ready,
  **START** to Active (data flows), **STOP** back to Ready, UNBIND to Unbound. A second BIND for a bound instance is
  rejected with "already bound" [V §4.2.1.5]. A return timer on confirmed operations leads to PEER-ABORT on expiry
  [V Table 4-1 note 11].
- **Service instance provision period.** The scheduled window in which the instance may be bound [V §1.6.1.7.13]. Map
  it to the pass/contact schedule from the planner.
- **RAF START parameters**: start/stop time (ERT window) and requested frame quality. These are the **delivery
  criteria** [V §1.6.1.7.4].
- **Delivery modes** [V §2.3]:
  - **online timely** — "controlled discarding of telemetry frames… if it is not possible to deliver those frames
    within a certain amount of time"
  - **online complete** — never discard; backlog goes to an **online frame buffer**
  - **offline** — later retrieval from the **offline frame buffer**

  Each service instance supports exactly one mode, chosen by service management.
- **Transfer buffer and latency limit** [V §2.6.4.6.2, §3.1.9.1]: frames and sync notifications go into a transfer
  buffer.
  - When the first item enters an empty buffer, the **release timer** starts at the **latency limit**.
  - The buffer is released as one `RafTransferBuffer` PDU when full or when the timer expires.
  - In timely mode, if the buffer is full and can't be passed on because of congestion, **the whole buffer is
    discarded as one unit** and a "data discarded due to excessive backlog" sync-notify is inserted. Discarding "in
    chunks" maximises usefulness.
  - In complete and offline modes, data is never discarded.

  Adopt this literally for TM-RT. It is simple and well-justified.
- **FCLTU** [V 912.1-B-5]:
  - CLTU-START takes `first-cltu-identification`; each CLTU-TRANSFER-DATA carries a monotonically increasing
    `cltu-identification`, and the return gives the next expected ID [§3.6.2.5].
  - Optional `earliest-radiation-time` / `latest-radiation-time` (an expired CLTU gives "sldu expired") [§3.6.2.6–7].
  - The return reports `cltu-buffer-available`.
  - `production-status` (operational / interrupted / halted).
  - Async notifications such as radiated / expired / production-status change.
  - **Association loss discards buffered CLTUs** [§2.6.4.4].

  Map these onto TC stream 1: `tc_seq`, optional `latest_release` (drop if stale), `TC_STATUS radiated/expired/
  discarded`, and a "station uplink" status.
- **ISP1 heartbeat** [V 913.1-B-2 §2.5.3]: heartbeat-interval and dead-factor are negotiated in the TML context
  message, using an HBT timer and an HBR timer. Use the same names in our HELLO.
- **ISP1 credentials** [V §3.1]: authentication level `none` / `bind` / `all`. Credentials = time (CCSDS CDS) + random
  number + SHA-256 "protected", checked against a max allowed delay. This is the precedent for §4.4.
- **What not to copy** [J]: ASN.1/BER encoding, ISP1's one-association-per-TCP-connection, and inbound connections to
  the provider. Real SLE stays an optional advanced-lab path (jsle / LibreCube `sle`, see `WEB_OPTIONS_RESEARCH.md`
  §B.2).

---

## 6. Python / aiohttp implementation specifics

Verified against **aiohttp 3.14.5** (released 2026-10-11), both docs and installed source.

### 6.1 Client `ClientSession.ws_connect`

```python
ws = await session.ws_connect(
    url, headers={"Authorization": cred}, heartbeat=20, autoping=True, autoclose=True,
    compress=0, max_msg_size=1 << 20, proxy=os.environ.get("HTTPS_PROXY"), ssl=True)
```

| Parameter | Behaviour |
|---|---|
| `heartbeat` | Ping every N s; close if no PONG within N/2 s. Reset by any inbound data [V/S] |
| `autoping` | Default True, auto-PONG [V] |
| `compress` | Default **0 = off**; 9–15 = window bits [V] |
| `max_msg_size` | Default **4 MiB**, 0 = unlimited [V] |
| `timeout` | Now `ClientWSTimeout(ws_receive=None, ws_close=10.0)` by default. After upgrade, aiohttp **resets the connection's read timeout to None** when `ws_receive` is None [S `client.py`], so the session's request timeout doesn't cut a long-lived link. **[U]** Do confirm the 300 s session `total` timeout only bounds the handshake. Pass `ClientTimeout(total=None, sock_connect=10)` to be explicit. |

- **Single reader rule:** "You must use the only websocket task for both reading… and writing but may have multiple
  writer tasks" [V client quickstart]. Still use **one** writer task, because priority needs it (§1.2).
- Campus explicit proxies: `proxy=` or `trust_env=True` work for WSS via CONNECT. SOCKS needs `aiohttp-socks` 0.12.0
  [V PyPI].

### 6.2 Server `web.WebSocketResponse`

- Defaults: `compress=True` (!), `max_msg_size` 4 MiB, `writer_limit` 64 KiB ("Once the buffer is full, the websocket
  will pause to drain") [V]. The server doesn't ping unless `heartbeat` is set [V].
- Set `WebSocketResponse(heartbeat=20, compress=False, max_msg_size=1<<20)`.

### 6.3 Compression (permessage-deflate)

- Measured locally on synthetic PUS HK with float parameters (sinusoid + noise). This is **synthetic, so [U] for the
  real EOSAT-1 mix**; re-measure on a real capture. The sim emitted no TM without a contact in a quick headless run.

  | Mode | Ratio | CPU |
  |---|---|---|
  | context takeover, 1 packet/message | **1.02** | 16 µs/packet |
  | no-context-takeover | **0.93** (bigger than raw) | |
  | 4 packets/message | 1.16 | |
  | random / already-compressed dumps | 1.00 | |

- Costs: CPU, a ~zlib window per connection, and a compression-side-channel risk when secret and attacker-influenced
  data share a context [J, CRIME-class reasoning].
- **Verdict: off.** If console assets need it, the console's HTTP layer already gzips, so forward `Content-Encoding`
  untouched (§6.5).

### 6.4 Local TCP fan-out server at the GSG (re-exposed 8002) and TC ingress (8001)

- `asyncio.start_server` on **127.0.0.1** (or the compose-internal network).
- Per consumer:
  - an `asyncio.Queue(maxsize=N)` and a writer task doing `writer.write(rec); await writer.drain()`;
  - `transport.set_write_buffer_limits(high=256 KiB)`.
- **Drop policy [J]:** TM to a slow consumer is drop-oldest (timely). Count drops and log them. Disconnect a consumer
  stuck > 30 s, so one stuck MCS never blocks the link reader or other consumers. **Never `await` a consumer from
  the link's read loop.** Use `put_nowait`, and on `QueueFull` pop one and push.
- Framing: read with `readexactly(2)` and `readexactly(n)`. Validate `n` (≤ 65 535 plus a sanity cap, e.g. 4096 for
  TC). On EOF, clean up the consumer.
- **TC ingress:** accept only from the local MCS, assign `tc_seq`, put on the TC stream. If the link is down,
  **reject immediately**: drop and inject a "station not bound" status. Never queue for later (§2.4).

### 6.5 Reverse-proxying HTTP and WebSocket through the tunnel

| Concern | Do this |
|---|---|
| Hop-by-hop headers | Strip `Connection` **and every header it names**, plus `Keep-Alive`, `Proxy-Connection`, `TE`, `Transfer-Encoding`, `Upgrade` [V RFC 9110 §7.6.1], and `Trailer`, `Proxy-Authorization`, `Proxy-Authenticate` [J]. Recompute framing on each side. |
| Bodies | Stream them. Request: `request.content.iter_chunked(16384)` into DATA frames under credit. Response: `web.StreamResponse` + `await resp.write(chunk)`. Don't buffer whole bodies. |
| Decompression | Use a client-side `ClientSession(auto_decompress=False)` toward the local console, otherwise aiohttp un-gzips but forwards `Content-Encoding: gzip`, which breaks the page [V `auto_decompress` default True; consequence J]. |
| Timeouts | The default `ClientSession` total timeout is 300 s [V]. Use `ClientTimeout(total=None, sock_read=…)` for long-polls/SSE. |
| Host | Send `Host: 127.0.0.1:<port>` (what the local server expects). Add `X-Forwarded-Host/Proto/For` and `X-Forwarded-Prefix` if mounted under a path. |
| Origin (nested WS) | The GSG validates the browser's `Origin` against the public host **first**, then rewrites `Origin` to the local origin so the sim's own CSWSH check passes [J]. Never just disable the check. |
| Path prefix | If the console is mounted at `/t/<team>/instr/`, its absolute URLs (`/api/...`, `ws://host/ws`) break. Prefer **one hostname per role** (`instr.<domain>`) or make the console prefix-aware. Rewrite `Location` and cookie `Path` [J]. |
| Nested WS | Open → OPEN `{kind:"ws", path, subprotocols, headers}`. Relay messages with the TEXT flag for opcode. Propagate close code and reason in CLOSE. Ping/pong stay local to each hop. |
| Body limits | Cap request bodies (e.g. 8 MiB) at the GSG. |

### 6.6 Other pitfalls

- **Cancellation:** wrap per-stream tasks in a `TaskGroup` per connection, and cancel all on disconnect. Otherwise
  local sockets leak across reconnects.
- **Seq wraparound:** use serial-number arithmetic (RFC 1982 style) for u32 comparisons.
- Don't log payloads. Log frame type, stream, seq and size.
- Python 3.12+ `eager_start` tasks inside aiohttp's compressed send path [S] are irrelevant with compression off.

---

## 7. Containerisation and Compute Engine

- **One image, several entrypoints.** One `smo` image. Compose `command:` picks `smo-simulator`, `smo-link-client`,
  `smo-gsg`, `smo-mcs`, `smo-planner`. This keeps one dependency set and one `configs/` hash (§B.2 config-hash check).
- **Compose profiles** [V Docker docs]: "Services without a `profiles` attribute are always enabled." Select with
  `--profile` or `COMPOSE_PROFILES=a,b`; `--profile "*"` enables all. Use:
  - `space`: sim + link-client (laptop/lab)
  - `ground`: GSG + MCS + planner (VM)
  - `dev`: both on one host, linked over the real WS path through toxiproxy
- **Healthchecks.** The slim image has no curl, so use
  `test: ["CMD","python","-c","import urllib.request,sys;urllib.request.urlopen('http://127.0.0.1:9443/healthz',timeout=2)"]`.
  The GSG's `/healthz` returns 200 even with no sim bound, because the LB must not mark the VM unhealthy when a team
  is offline. Expose link state at `/readyz` for monitoring.
- **Compute Engine:**
  - The **container startup agent (konlet) and "Deploy container" / `create-with-container` are deprecated**. Use
    `docker run` in a startup script or cloud-init [V GCE docs].
  - **Container-Optimized OS:** Docker + containerd + cloud-init preinstalled, read-only root, writable `/var` and
    `/home` (`/var/lib/docker` stateful), weekly auto-updates, **no package manager**, no non-containerised apps
    [V COS docs]. **[U]** Whether the `docker compose` v2 plugin ships on current COS images was not confirmed; a
    community workaround runs compose as a container.
  - **Recommendation [J]:** **Debian 12/13 + Docker CE + compose plugin**, unattended-upgrades. It is simpler for one
    maintainer and Compose-native. Pick COS only if you go single-container.
- **Network:**
  - VM with **no external IP**, Cloud NAT for egress (image pulls), firewall ingress only from 130.211.0.0/22 and
    35.191.0.0/16 to ports 9443 (link) and 8443 (apps) [V ranges].
  - SSH via **IAP TCP forwarding** (35.235.240.0/20, `roles/iap.tunnelResourceAccessor`) [V].
  - **No Caddy**: the LB terminates TLS with a Google-managed cert. LB→backend can stay HTTP inside Google's network,
    or use HTTPS with a self-signed cert if policy demands it (the LB doesn't use SNI to backends) [V].
- **Backend services:**
  - `be-link` (no IAP, `timeoutSec 3600`, session affinity none, health check `/healthz`)
  - `be-apps` (IAP on; `timeoutSec` long enough for the console's own WebSockets, e.g. 3600)
  - URL map `/link` → `be-link`, `/*` → `be-apps`

---

## 8. Testing impaired networks without root

| Tool | Root? | Works in CI | Fit |
|---|---|---|---|
| **Toxiproxy** (Shopify) v2.13.0, 2026-10-14 [V CHANGELOG] | **No.** A TCP proxy in user space, Go binary or `ghcr.io/shopify/toxiproxy` | Yes, as a service container or background binary | Toxics [V README]: `latency` (+`jitter`), `bandwidth` (KB/s), `timeout` (blackhole, then close), `reset_peer` (RST), `slow_close`, `slicer` (fragmentation), `limit_data` (close after N bytes), `down` (disable proxy), `packet_loss`. 2.13.0 adds optional API bearer auth. **Python client `toxiproxy-python` is stale (0.1.1, 2019)** [V PyPI], so drive the REST API directly with aiohttp (POST `/proxies`, `/proxies/{p}/toxics`). |
| **In-process asyncio fault proxy** (~80 lines, write it) | No | Yes, inside pytest (pytest-asyncio 1.4.1) | Deterministic: `pause()`, `cut()` (RST or FIN), `delay(ms)`, `throttle(bps)`, `blackhole()` at exact points in a test. Best for resume/replay/TC-never-replayed unit tests. |
| **tc netem** | **Yes** (CAP_NET_ADMIN) | Only privileged runners or `--cap-add NET_ADMIN` containers | Real packet-level delay, loss, reorder, rate [V man page]. Good for manual soak tests of TCP behaviour under true loss. |

Notes [J]:

- Toxiproxy's `packet_loss` drops **chunks of the TCP byte stream**. Inside a TLS/WS stream that is *corruption*, not
  loss; real TCP turns loss into latency spikes. Use `latency`+`jitter`, `bandwidth`, `timeout` and `reset_peer` to
  model a bad link. Use `packet_loss` or `limit_data` only to prove the receiver rejects garbage and reconnects.
- In CI run the link as plain `ws://` through toxiproxy, which proxies raw TCP below TLS. Keep one nightly job
  against the real LB.
- Core scenarios:
  1. 300 ms RTT ± 100 ms jitter: the clock filter converges to < δ/2.
  2. Blackhole 45 s: dead-detect in ≤ 30 s, TM GAP reported, **zero TCs delivered twice**.
  3. `reset_peer` mid-dump: resume at the right offset, matching sha256.
  4. 64 KB/s bandwidth with a 20 MB dump in flight: TC latency stays < 200 ms (priority works).
  5. 24 h soak with forced reconnects every 10 min.

---

## 9. Open items / not verified

1. Whether WS **control-frame** pings reset the GFE idle timer. The docs say "idle" without defining it. Mitigated by
   app-level data PINGs.
2. Any GFE limit on **WS message/frame size**. None documented; search found nothing authoritative. Keep frames
   ≤ 64 KiB.
3. Whether the ALB passes WS **close codes/reasons** end-to-end on maintenance (e.g. 1001). Don't rely on them; rely
   on GOAWAY and resume.
4. Real EOSAT-1 TM compressibility (only synthetic data was measured).
5. Whether COS currently ships `docker compose`.
6. Whether `TCP_NOTSENT_LOWAT` helps through home routers. Measure before adopting.
7. aiohttp session `total` timeout vs long-lived `ws_connect`. Source suggests it doesn't apply after upgrade; set
   `total=None` anyway.

---

## Sources

GCP

- External ALB overview (WebSocket support, limitations): https://docs.cloud.google.com/load-balancing/docs/https
- Request distribution, timeouts, WebSocket timeouts, 60-min connection age: https://docs.cloud.google.com/load-balancing/docs/https/request-distribution
- Backend services (timeout): https://docs.cloud.google.com/load-balancing/docs/backend-service
- Quotas and limits (header size): https://docs.cloud.google.com/load-balancing/docs/quotas
- mTLS overview: https://docs.cloud.google.com/load-balancing/docs/mtls ; ServerTlsPolicy: https://cloud.google.com/load-balancing/docs/reference/network-security/rest/v1/projects.locations.serverTlsPolicies
- IAP programmatic authentication: https://docs.cloud.google.com/iap/docs/authentication-howto
- IAP sessions (WebSocket initial-request only): https://docs.cloud.google.com/iap/docs/sessions-howto
- IAP for Compute Engine (per backend service): https://docs.cloud.google.com/iap/docs/enabling-compute-howto
- IAP signed headers: https://docs.cloud.google.com/iap/docs/signed-headers-howto
- IAP TCP forwarding: https://docs.cloud.google.com/iap/docs/using-tcp-forwarding
- IAP release notes: https://docs.cloud.google.com/iap/docs/release-notes
- Deploying containers on VMs (konlet deprecated): https://docs.cloud.google.com/compute/docs/containers/deploying-containers
- COS features: https://docs.cloud.google.com/container-optimized-os/docs/concepts/features-and-benefits ; COS security: https://docs.cloud.google.com/container-optimized-os/docs/concepts/security

Tunnels / mux

- yamux spec: https://raw.githubusercontent.com/hashicorp/yamux/master/spec.md
- smux README: https://raw.githubusercontent.com/xtaci/smux/master/README.md
- chisel README / go.mod: https://raw.githubusercontent.com/jpillora/chisel/master/README.md
- wstunnel README: https://raw.githubusercontent.com/erebe/wstunnel/main/README.md
- frp README / go.mod: https://raw.githubusercontent.com/fatedier/frp/dev/README.md
- cloudflared run parameters: https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/configure-tunnels/run-parameters/ ; go.mod: https://raw.githubusercontent.com/cloudflare/cloudflared/master/go.mod
- muxado (ngrok) README and PROTOCOL.md: https://docs.rs/crate/muxado/0.5.3/source/README.md , https://docs.rs/crate/muxado/0.5.3/source/PROTOCOL.md
- RFC 8441 / RFC 9220: https://rfc-editor.org/rfc/rfc9220.html
- Cloudflare, HTTP/2 prioritisation with `tcp_notsent_lowat`: https://blog.cloudflare.com/http-2-prioritization-with-nginx/

CCSDS

- CCSDS 911.1-B-5 RAF (July 2023): https://ccsds.org/Pubs/911x1b5e1.pdf
- CCSDS 912.1-B-5 FCLTU (July 2023): https://ccsds.org/Pubs/912x1b5e1.pdf
- CCSDS 911.2-B-4 RCF: https://ccsds.org/Pubs/911x2b4e1.pdf
- CCSDS 913.1-B-2 ISP1 (Sept 2015): https://public.ccsds.org/Pubs/913x1b2.pdf
- ISO 22669:2021 (= 911.1-B-4) sample: https://cdn.standards.iteh.ai/samples/74554/c41dc6a668eb43318d803c9c5f188582/ISO-PRF-22669.pdf
- Yamcs SLE (delivery modes summary): https://docs.yamcs.org/yamcs-sle/about/

Time / auth / HTTP

- RFC 5905 NTPv4: https://www.rfc-editor.org/rfc/rfc5905.txt
- RFC 8725 JWT BCP: https://www.rfc-editor.org/rfc/rfc8725.txt
- RFC 9110 §7.6.1 Connection / hop-by-hop: https://www.rfc-editor.org/rfc/rfc9110.txt
- PyJWT algorithms: https://pyjwt.readthedocs.io/en/stable/algorithms.html
- AWS, Exponential Backoff and Jitter: https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/

Python

- aiohttp client reference: https://docs.aiohttp.org/en/stable/client_reference.html ; server: https://docs.aiohttp.org/en/stable/web_reference.html ; client quickstart (single reader rule, 300 s default timeout): https://docs.aiohttp.org/en/stable/client_quickstart.html
- PyPI JSON for aiohttp 3.14.5, PyJWT 2.15.1, pyseto 1.10.0, aiohttp-socks 0.12.0, toxiproxy-python 0.1.1, pytest-asyncio 1.4.1 (https://pypi.org/pypi/<name>/json)

Testing / containers

- Toxiproxy README and CHANGELOG: https://raw.githubusercontent.com/Shopify/toxiproxy/main/README.md , https://raw.githubusercontent.com/Shopify/toxiproxy/main/CHANGELOG.md
- tc-netem(8): https://man7.org/linux/man-pages/man8/tc-netem.8.html
- Docker Compose profiles: https://docs.docker.com/compose/how-tos/profiles/
