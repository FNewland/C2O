# Space link: interface specification (SMO simulator ⇄ cloud ground segment)

Read-only analysis, 2026-10-29. Paths are relative to `/home/claude/work/smo`, and `file:line` refers to the working copy.
Inputs: `../research/WEB_CURRENT_STATE.md` (survey) and `docs/web_2026-10/ARCHITECTURE.md` §4 (target design).
Measurements were taken in a scratch directory. The repo was not modified (`git status` is clean).

**Goal.** Specify exactly what the sim-side **space-link agent** and the cloud **ground-station gateway (GSG)** must
reproduce so that **MCS, planner, rfsim, delayed-TM viewer and wall display run unchanged**.

---

## 0. Summary of the contract (what the GSG must look like from the ground)

The cheapest zero-change design is for the **GSG to impersonate the simulator's three sockets on the ground host**. Every
ground default then works without edits:

| Ground-host listener (GSG) | Impersonates | Consumers (unchanged) | Evidence the defaults already point here |
|---|---|---|---|
| `127.0.0.1:8002` TCP TM | sim TM server | MCS `--connect 127.0.0.1:8002`; rfsim `sim_tm_*` | `start.sh:291`; `configs/eosat1/rfsim.yaml:131-132` |
| `127.0.0.1:8001` TCP TC | sim TC server | MCS (TC host = TM host, `smo-mcs/.../server.py:1606-1609`); rfsim `sim_tc_*` | `rfsim.yaml:133-134` |
| `127.0.0.1:8080` HTTP+WS | sim instructor app | MCS/planner `GET /api/state`; rfsim `ws://127.0.0.1:8080/ws`; instructor browsers (proxied) | `start.sh:226`; `smo-planner/.../server.py:130`; `rfsim.yaml:135` |
| `$SMO_DUMP_DIR` (filesystem) | sim dump writer | MCS `/dumps`, `/reports`; `tools/delayed_tm_viewer.py` | `smo-common/.../dump_store.py:24-28,113-125`; `start.sh:81-82,306` |

The agent (space side) is a **client of the same three sim sockets on loopback**, so it also needs **no simulator code
change**. It dials out over WSS to the GSG.

Six hard constraints found in the code (details in §1–§4):

1. **Never close the TM socket of the rfsim bridge.** The bridge connects once and does not reconnect
   (`smo-rfsim/.../bridge.py:134-141`, `264-269`). The GSG TM listener must be up **before** rfsim starts and must stay
   up while the space link is down.
2. **Read sim TM promptly on the space side.** The sim drops any TM client whose `drain()` takes more than 2 s
   (`smo-simulator/.../server.py:156-168`). The agent must decouple the WAN from the sim socket with its own queue.
3. **Dropping the TC connection: use RST, not FIN.** The MCS never reads its TC socket. After a FIN (plain close) its
   `writer.is_closing()` stays False and the **next TC "succeeds" into a dead socket** (measured, §1.6). Recommended
   behaviour while the link is DOWN: abortive close (SO_LINGER 0) of TC clients and refuse new TC connects. The MCS then
   returns `503 No TC connection` (`server.py:3000-3004`), which is the same as "simulator down" today.
4. **Serve `/api/state` from the last STATE, with `sim_time` and `met_s` advanced locally.** On failure the MCS and
   planner keep their last anchor (`server.py:2076-2077`; planner `server.py:599-602`). After 4.5 s without a fresh
   payload they drop the sim illumination and fall back to their own propagators (`server.py:1171,2117`; planner
   `server.py:735`). Serve for at most ~5 s after the last STATE, then return 503.
5. **Store dumps byte-identical under the same filename in the ground `SMO_DUMP_DIR`**, written atomically under a name
   that does not match `dump_*.bin` until it is complete (`dump_store.py:85-89`).
6. **Never expose the sim's write-capable `/config` editor through the instructor proxy** (`instructor/app.py:114-139`,
   `confedit/api.py:250-258`).

---

## 1. TM/TC sockets

### 1.1 Framing (`smo-common/src/smo_common/protocol/framing.py`)
- Each frame is a 2-byte **big-endian unsigned length**, then that many bytes of a raw CCSDS/PUS packet (`:13,17-22`).
  There is no sync marker, CRC, handshake, greeting, keep-alive or auth on either socket.
- `MAX_PACKET_SIZE = 65535` (`:14`). `frame_packet` raises above that (`:20-21`).
- Reader `read_framed_packet` (`:25-39`): `readexactly(2)`, then `readexactly(len)`. **A length of 0 or more than 65535
  returns `None`, and every caller treats `None` as end of connection** (sim TC `server.py:119-121`, MCS TM
  `server.py:1630-1632`, rfsim `bridge.py:266-269`). One corrupt length byte therefore kills the connection.
  `deframe_sync` (`:42-59`) resyncs byte by byte, but no socket path uses it.
- The packet inside is not validated by the socket layer. The sim parses TCs on the tick thread
  (`engine.py:2610-2633`). The MCS calls `decommutate_packet` and **silently ignores** anything without a secondary header
  (`server.py:1633-1635`).
- Packet sizes:
  - TM primary header 6 B, PUS-C secondary header 9 B (`0x10, svc, sub, CUC 4+2`), data, and CRC-16 2 B
    (`smo-common/.../telemetry/tm_builder.py:213-234`).
  - Measured HK packet sizes from `configs/eosat1/telemetry/hk_structures.yaml`: SID1 105 B, SID2 152 B (largest HK),
    SID3 49, SID4 88, SID5 75, SID6 65, SID7 101, SID8 45, SID9 59, SID11 29 (beacon), SID12 59.
  - **S13.4 image segment = 6 + 9 + 4 + 1024 + 2 = 1045 B** (`service_dispatch.py:2665-2672`), the largest routine TM
    packet.
  - "Report all" packets are segmented to about 256 B with CCSDS grouping flags (`tm_builder.py:236-260`). The MCS
    reassembles them and discards a continuation that has no first segment (`server.py:1639-1670`), so **dropping one
    segment loses the whole report**.
  - TCs are small (`build_tc_packet`, PUS v2 3-byte secondary header, `ecss_packet.py:484`). An S11.4 carries embedded TCs.
  - Practical ceiling: about 1.1 kB per frame. The framing allows 64 kB.

### 1.2 Simulator TM server (port 8002, `smo-simulator/src/smo_simulator/server.py`)
- **Multiple TM clients are supported.** Each accepted writer is appended to `_tm_clients` (`:132-135`). The handler never
  reads from the socket: it sleeps 1 s and checks `is_closing()` (`:137-141`). Bytes sent *to* the TM port are ignored
  (this is why `smo-gateway` TCs never worked). `mission.yaml network.tm_max_clients: 8` is **not enforced**: the only
  reference is the schema (`smo-common/.../config/schemas.py:119`).
- **On connect:** no greeting and **no replay or backfill**. A client receives only packets dequeued after it joined.
- **Broadcast** (`:149-170`): one coroutine pops `engine.tm_queue` (a thread `queue.Queue(maxsize=2000)`,
  `engine.py:103`), frames each packet, and for each client in turn calls `write` + `await wait_for(drain(), 2.0)`. A
  client that errors or times out is removed and closed (`:163-168`). Consequences:
  - **Ordering:** a single serial producer, so every client sees the same packet order.
  - **Head-of-line blocking:** one slow client delays every other client's TM by up to 2 s per packet.
  - **No clients connected:** packets are still dequeued and discarded (`:150-154`), so TM is lost and not buffered.
  - When the queue is empty, the loop sleeps 50 ms (`:169-170`). Added latency is ≤ 50 ms.
- **Engine-side producers and drops:**
  - Real-time TM goes through `_enqueue_tm` (`engine.py:3715-3765`). It is gated by `downlink_active`
    (`engine.py:1741`). Inactive means the packet is dropped (and still stored on board, `:3751-3765`).
  - When `rt_tm_pacing` is active, packets join `_rt_pending` (cap `rt_tm_backlog_max: 2000`,
    `configs/eosat1/simulation.yaml`). They are released by a byte budget of `tier_bps/8 × dt_sim` per tick
    (`engine.py:3692-3713`). `_put_tm` counts drops on a full queue (`engine.py:65-79`).
  - S15 dump packets bypass `_enqueue_tm` and are **dropped silently** when `tm_queue` is full (`engine.py:3511-3516`).
    The dump pending list is capped at 5000 packets (`engine.py:3440-3446`).

### 1.3 Simulator TC server (port 8001)
- **Multiple TC clients are supported.** Each connection has its own reader loop (`server.py:114-130`). Every framed
  packet goes to `engine.tc_queue.put_nowait` (`Queue(maxsize=500)`, `engine.py:104`). If the queue is full, the TC is
  **dropped with a log warning only**: no NAK and no TM (`server.py:124-126`).
- Packets from different connections interleave at packet granularity, in arrival order. The sim **never writes to a
  TC socket**: no ack and no greeting. Acknowledgement happens only through S1 TM on the TM socket.
- The tick thread drains the whole `tc_queue` once per tick (`engine.py:2272`, `2610-2633`). If `uplink_active` is false
  (`engine.py:1832-1857`: override, or in contact with link_status ≥ 2), the sim answers with **S1.2 error 0x0005** on
  TM rather than silently. TC latency inside the sim is therefore up to one tick (1 s at the default
  `sim_tick_hz: 1.0`, `mission.yaml network`).
- On disconnect the handler just closes (`:129-130`). Commands already queued still execute.

### 1.4 Ports and bind
- The **TM/TC ports are hard-coded** in `main()`: `"tc_port": 8001, "tm_port": 8002` (`server.py:274-278`). They are
  configurable only through `SimulatorServer(config=...)` (`:33-34`), which tests use. `mission.yaml network.tc_port/
  tm_port` are read by nobody (`WEB_CURRENT_STATE.md` L1).
- Bind address: `--host` > `$SMO_BIND` > `0.0.0.0` (`server.py:39-40`). HTTP port: `--port` > `$SMO_SIM_HTTP_PORT` >
  8080 (`:226-231`). In the `space` profile, bind the simulator to **127.0.0.1** so only the agent reaches it.

### 1.5 MCS connection behaviour (`smo-mcs/src/smo_mcs/server.py`)
- CLI: `--connect host:port` is the TM source (default `localhost:8002`). `--tc-port` defaults to 8001, and **the TC host
  is always the TM host** (`:5487-5489, 5517-5523`, `1606-1609`). There is no env var for `--connect` or `--tc-port`.
- **TM loop** (`:1622-1637`): `open_connection`, then `read_framed_packet` until `None`.
  - On `None` (EOF or bad length) the inner loop breaks and the outer loop **reconnects immediately, with no sleep**, and
    does not close the old writer.
  - On an exception (for example connection refused) it sleeps 2 s.
  - So **if the GSG accepts and then immediately closes, the MCS hot-loops**. Keep the TM listener stable, or refuse.
  - Each packet is processed inline (`_process_tm`, `:1672-`), including the WS fan-out to browsers (`:2017-2031`).
- **TC loop** (`:1603-1620`): connects, stores `_tc_writer`, then checks `writer.is_closing()` every 2 s. It sleeps 3 s
  after an error.
  - All TC paths check `_tc_writer is None or is_closing()` and return "No TC connection":
    `/api/pus-command` (`:3000-3009`, HTTP 503), the procedure runner (`:3483-3490`), S11 upload (`:3644, 3704-3705`) and
    TM-dump (`:5057-5067`).
  - Each send is `write(frame)` + `await drain()` under `_tc_send_lock`. A command is recorded as `SENT` *before* the
    socket check (`:2985-2997`).
  - **Assumption:** TC delivery is fire-and-forget over TCP. Verification comes only through S1 TM, and
    `tc_manager._pending_verifications` has no timeout (`WEB_CURRENT_STATE.md` §4).
- The MCS never sends on the TM socket and never reads the TC socket.

### 1.6 Measured: what the MCS notices when its TC peer goes away
Measured with a scratch script using the same asyncio stream API the MCS uses:

| Peer action | `is_closing()` before writing | 1st write + drain | 2nd write |
|---|---|---|---|
| `close()` (FIN) | **False** | **succeeds (TC lost)** | `ConnectionResetError` |
| SO_LINGER 0 + close (RST) | **True** | `ConnectionResetError` | — |

So the GSG should RST TC clients when the link drops (`sock.setsockopt(SO_LINGER, struct.pack('ii',1,0))` then
`close()`) and refuse or abort new TC connects until the link is UP. The MCS then returns 503 within ≤ 2 s
(`server.py:1615-1620`). Note that the asyncio `transport.abort()` alone still sent a FIN in this test.

### 1.7 rfsim bridge (sim side: TM 8002, TC 8001, WS 8080/ws)
- **Configuration comes from the YAML only** (`smo-rfsim/.../config.py:308-324`; `configs/eosat1/rfsim.yaml:129-145`):
  `sim_tm_host/port 127.0.0.1:8002`, `sim_tc_host/port 127.0.0.1:8001`, `sim_ws_url ws://127.0.0.1:8080/ws`,
  downstream `mcs_tm_port 8012`, `mcs_tc_port 8011`, `mcs_bind 0.0.0.0`. No env overrides exist (the only env reads are
  `SMO_PASS_ROLLUPS` and `SMO_UI`).
- **TM:**
  - It connects **once** in `start()`. If that fails it logs and **returns, so the bridge does nothing**
    (`bridge.py:134-141`). It opens its MCS listeners only after this (`:147-151`).
  - `_relay_tm` breaks on `None` ("Spacecraft TM connection lost") and **never reconnects** (`:264-269`).
  - Downstream fan-out is sequential `write` + `drain` with no timeout (`:386-397`). In RF mode it backs off 50 ms when
    the TX queue is more than 80 % full (`:286-292`).
  - **Requirement: the GSG TM listener is up before rfsim starts and never drops the rfsim connection.**
- **TC:** it connects lazily on the first TC and reconnects when `is_closing()` is true (`:242-251`). A failure logs and
  the TC is lost. In RF or FRAME mode a TC may be dropped by the channel model (`:210-240`).
- **WS feedback:**
  - It uses `aiohttp ws_connect(sim_ws_url)` and retries every **5 s** (`:634-660`). It never sends on the WS.
  - It treats every text frame as `data.get("state", data)` (`:675`), so reply frames like `{"status":"ok"}` are
    harmless.
  - **Fields read from `state`** (`:674-905`): `sim_time`; `ttc.{eb_n0_db, doppler_hz, tx_active, pa_on,
    ttc_tx_line_on, carrier_lock, bit_sync, frame_sync, tm_tier, tm_tier_name, tm_coding, data_rate_bps,
    modulation_mode, gs_penalty_db, rssi_dbm, range_km}`; `override_passes`; `in_contact`; `ground_station_name`.
  - It also reads `contact_station` / `ground_station` / `contact.station` (`:694-700`). **None of these exist in the
    summary**, which publishes `ground_station_name` (`engine.py:4487`). This is a pre-existing mismatch:
    `set_ground_station` is never driven from the feed. The GSG should not try to fix it.
- MCS-facing ports 8011/8012 and the radio UI on 8094 are ground-only and are unaffected.

### 1.8 VR bridge (sim side, ports 8100 TCP NDJSON / 8101 WS `/vr` or `/`)
- It runs inside the simulator process (`server.py:73-77, 87-112`; `vr_bridge.py:1-30, 517-541`). Server to client:
  one `hello`, then `state` frames at the tick rate (keepalive 1 Hz, cap `max_rate_hz` 10). Client to server: optional
  `status` lines ≤ 4096 B (`vr_bridge.py:56`). A slow client is dropped after 2 s (`:57`). Measured frame body is about
  **0.9 kB**.
- **No ground process consumes it.** The only consumer of its *summary* is the instructor console, through
  `state.vr_link` (`engine.py:4632`) and `GET /api/vr` (`instructor/app.py:311-321`), and both travel through the proxied
  8080.
- For a cloud or laptop sim, headsets must reach the space host directly, or a later GSG feature relays VR frames (about
  9 kB/s at 10 Hz). Out of scope for a zero-change link: set `SMO_VR=0` on a cloud sim (`server.py:241-243`).

### 1.9 TM rates (for sizing the WSS link)
- **Real-time HK**, all SIDs enabled except the beacon: **1743 bit/s ≈ 218 B/s, 2.27 packets/s at ×1**, computed from
  `hk_structures.yaml` with the real `TMBuilder`. The `simulation.yaml` comment says 1351.5 bit/s, which predates SIDs 7
  and 12. At boot only the bootloader beacon flows: measured **6 packets / 294 B in 12 s** with pass override on. HK
  SIDs are enabled by TC(3,5) (defect #75).
- **Pacing is in sim time.** Both pacers add `tier_bps/8 × dt_sim` bytes per tick (`engine.py:3502, 3700`), so the
  **wall-clock TM rate scales with speed**. Speed is clamped by `simulation.yaml speed.max: 1000`.
- Tiers (`configs/eosat1/subsystems/ttc.yaml:91-…`): SAFE 1 kbit/s, LOW 16 kbit/s, HIGH 128 kbit/s.

| Case | Wall bytes/s | Packets/s (approx.) |
|---|---|---|
| ×1, LOW, real-time HK only | ~220 B/s | ~2.3 |
| ×1, HIGH, S15 HK-store dump (about 100 B per packet) | 16 kB/s | ~150 |
| ×1, HIGH, S13 image (1045 B segments, **one per S13.3 TC**, `service_dispatch.py:2630-2672`) | ≤ 16 kB/s | ≤ 15 (TC-paced) |
| ×10, HIGH dump | 160 kB/s | ~1 500 |
| ×60, HIGH dump | ~960 kB/s | ~9 000 (per 1 s tick; bounded by `tm_queue` 2000 per tick and 5000 dump pending, so the sim drops the excess itself) |

- **Image product:** the payload "transfer engine" only drains a counter (0x062E) and emits no TM bytes
  (`service_dispatch.py:2597-2616`). Image bytes cross the link only as S13.4 responses.
- **STATE push:** `/api/state` JSON measured at **10.8 kB** (447 entries in `params`), 1 Hz, so about 11 kB/s
  uncompressed. Use WS `compress` (permessage-deflate). The instructor snapshot is **23.6 kB**, polled every 2 s by each
  instructor tab (`instructor.js` header). Design the link for **≥ 1 MB/s bursts**, with typical traffic under
  30 kB/s.

---

## 2. Simulator HTTP endpoints called by the ground, and `/api/state`

### 2.1 Every sim HTTP/WS call made by a ground process
| Caller | Request | Cadence / timeout | Evidence |
|---|---|---|---|
| MCS | `GET {sim_state_url}` | every 1.5 s, `ClientTimeout(total=2.0)`, new session per poll | `server.py:2033-2077` |
| Planner | `GET {sim_state_url}` (**blocking urllib**) | at most 1/s, 1.5 s timeout, called from `_get_now()` | planner `server.py:575-602, 737-752` |
| rfsim bridge | `WS {sim_ws_url}` (default `ws://127.0.0.1:8080/ws`) | push 1 Hz; reconnect every 5 s | `bridge.py:634-660` |
| Delayed-TM viewer `--api` | `GET {base}/api/dumps`, `GET {base}/api/dumps/file?name=` | on demand | `tools/delayed_tm_viewer.py:207-260`. **start.sh runs it in local mode** (`start.sh:306`) |
| start.sh / deploy readiness | `GET /api/state` | start-up only | `start.sh:235`; `deploy/start-all.sh:152` |

Nothing else on the ground calls the sim. The MCS source is even tested to contain no `8080` (`tests/test_back_channel_closed.py:40-49`).
The wall display reads **MCS** `/api/state` and rfsim, not the sim (`smo-planner/.../static/modern/wide.js:184-200`).
URL resolution:
- MCS: `--sim-state-url` > `SMO_SIM_STATE_URL` > `mission.yaml sim_state_url` >
  `http://<connect_host>:$SMO_SIM_HTTP_PORT|8080/api/state` (`server.py:211-223`).
- Planner: CLI > env > mission > `planner.yaml time.sim_state_url` > `http://<connect_host>:8080/api/state`
  (planner `server.py:125-131`).
- Sim-time polling runs only when `time_source == "sim"`: CLI > `SMO_TIME_SOURCE` > `mission.yaml time_source` > "sim"
  (`server.py:174-179`).

### 2.2 How `/api/state` is produced
- Handler: `web.json_response(engine.get_state_summary())` (`instructor/app.py:307-309`).
- The summary is an **immutable snapshot published at the end of every tick** under `_params_lock` (`engine.py:2187`,
  `4398-4433`). Before the first tick it is built inline (`:4435-4447`). Requests are served in about 1.6 ms (measured).
- `sim_time = self._sim_time.isoformat()`, a timezone-aware UTC value such as `"2026-08-20T12:00:14+00:00"` (microseconds
  appear only when non-zero) (`engine.py:4469`). It is the sim time **as of the last completed tick**, so it lags the
  engine by up to one tick (1 s × speed). The update rate is the tick rate (`mission.yaml network.sim_tick_hz: 1.0`,
  `engine.py:2040-2067`).
- `speed = self.speed`: 0.0 when frozen (`engine.py:3929, 4030-4035`), clamped to `speed.max` (`:3919`).
- `met_s = self.met_s`, defined as `sim_time − t0_epoch` (`engine.py:4472`).
- The snapshot carries **no wall-clock timestamp**, so the receiver cannot measure its age.

### 2.3 Full schema and which consumer reads each field
Top-level keys in order (`engine.py:4466-4635`). `M` = MCS, `P` = planner, `R` = rfsim (through WS `state_update`),
`I` = instructor UI.

| Field | Type / origin | Read by |
|---|---|---|
| `tick` | int | I |
| `sim_time` | ISO-8601 UTC | **M** clock anchor + jump detect (`:2054-2066, 2164-2214`); **P** anchor + jump (`:603-645`); **R** rollup clock (`:678-686`); I |
| `met_s` | float | **P** (anchored with sim_time, `:684-692`); I |
| `speed` | float | **M** (`:2064-2065`); **P** (`:681-683`); I |
| `sc_mode` | str/int | **M** FDIR window (`:2375-2382`); I |
| `in_eclipse`, `sun_fraction`, `in_penumbra`, `shadow_model` | bool/float/bool/str | **M** (`:2080-2115`); **P** (`:651-670`) |
| `time_to_eclipse_entry_s`, `time_to_eclipse_exit_s` (from `_get_eclipse_transition`, `:4359`) | float/null | **M** (`:2110-2111`) |
| `in_contact` | bool | **R** (`:752-765`); I |
| `ground_station_name` | str | **R** (`:760`); I |
| `gs_elevation_deg`, `gs_range_km`, `lat`, `lon`, `alt_km` | float | I |
| `orbit_epoch_version`, `orbit_elset{tle_line1,tle_line2,…}` | int, dict | **M** (`:2119-2162`); **P** (`:712-735`) |
| `eps{…}`, `aocs{…}`, `tcs{…}`, `obdh{…}`, `payload{…}`, `prop{…}` | dicts | I |
| `ttc{mode, link_status, rssi_dbm, link_margin_dB, range_km, elevation_deg, eb_n0_db, ber, carrier_lock, bit_sync, frame_sync, doppler_hz, modulation_mode, gs_penalty_db, pa_temp_C, tx_power_W, data_rate_bps, tm_tier, tm_tier_name, tm_coding, symbol_rate_bd, downlink_mode, pa_on, tx_active, tx_gate_status, eirp_dbw, antenna_deployed, beacon_mode, beacon_tx_on, beacon_active, beacon_margin_dB, beacon_dl_freq_mhz, beacon_tx_power_W, ttc_tx_line_on}` (`:4537-4590`) | dict | **M** reads `tm_tier, tm_tier_name, tm_coding, symbol_rate_bd, downlink_mode, data_rate_bps, elevation_deg` (`:2398-2407`); **R** reads the list in §1.7 |
| `spacecraft_phase`, `downlink_active`, `uplink_active`, `override_passes` | | **R** reads `override_passes`; I |
| `active_failures`, `tm_stores` | list/dict | I |
| `scheduler{enabled,…}` | dict | **M** `enabled` (`:2385-2387`) |
| `engine_fault`, `engine_fault_count`, `tm_rate_bps`, `rt_tm_backlog` | | **M** (`:2377-2383`) |
| `tm_tier`, `tm_tier_name` (top level) | | I |
| `hk_enabled` | `{sid:int → bool}` (keys become strings in JSON) | **M** (`:2409-2429`) |
| `hk_enable_reset` | dict/null | **M** (`:2431-2458`) |
| `fdir` | dict | **M** (`:2392-2394`) |
| `vr_link` | dict/null | I |
| `params` | `{param_id:int → float}` (447 entries; keys become strings) | I (MCS no longer uses it) |

**GSG rule:** serve the pushed JSON **verbatim** (same keys and order), rewriting only the time-dependent fields:

```
age      = now_ground_wall − t_sample_ground        # t_sample_ground = agent sample time mapped to the ground clock (§2.4)
sim_time = iso(sim_time_pushed + age × speed)        # aware UTC, isoformat(); keep the "+00:00" form
met_s    = met_s_pushed + age × speed
time_to_eclipse_{entry,exit}_s = max(0, v − age × speed)   # optional; null stays null
```

If no STATE arrived in the last **`STATE_STALE_S` = 5 s** (just above the 4.5 s illumination max age), return
**HTTP 503**. The MCS then keeps its anchor and the planner sets `sim_reachable=False`, which is today's "sim
unreachable" behaviour.

### 2.4 Clock anchoring done by consumers (what the GSG must feed)
- **MCS** (`server.py:1085-1111, 2033-2077`): `ground_epoch = sim_time_received`, `start_wall = time.time()` at
  *receipt*, `sim_now = epoch + (wall − start_wall) × speed + offset`. The request latency is ignored, so today's error
  is one-way latency plus snapshot age (≤ 1 tick), multiplied by speed. Jump tolerance is
  `max(_jump_tolerance_s, 3 × 1.5 × max(1, |speed|))` (`:2186-2188`). A jump clears schedule, stores and memory
  reports (`:2196-2213`).
- **Planner** (`server.py:591-735`): the same anchor-at-receipt rule, refreshed at most 1/s from `_get_now()`. Tolerance
  is `max(planner.yaml time.jump_tolerance_s, 3 × anchor_refresh_s × max(1, |speed|))` (`:621-625`). A jump sets
  `_plan_dirty`.
- **rfsim:** `_last_sim_ts = sim_time` from the latest WS frame, no extrapolation (`bridge.py:662-686`).
- **Implication:** with the GSG on loopback, the consumer's own latency is about 0. The GSG estimates the agent→GSG
  one-way delay and serves `sim_time` extrapolated to "now". Recommended method:
  - The agent stamps each STATE with `t_agent` (its monotonic-derived wall time at sample).
  - The GSG keeps an NTP-style offset estimate from app-level ping/pong
    (`offset = ((t1−t0)+(t2−t3))/2`, keeping the minimum-RTT sample over a sliding window).
  - `t_sample_ground = t_agent − offset`.
  - If the agent samples through the sim's WS `state_update`, add nothing for snapshot age: it is the same ≤ 1 tick that
    exists today.
- **Speed changes:** between pushes the GSG extrapolates with the old speed. A freeze is visible at the next push, an
  overshoot of ≤ (push interval + delay) × old speed, which is well inside both jump tolerances. The agent should push
  immediately when `speed` or `tick` changes, which is natural when it subscribes to the sim's `/ws`.

### 2.5 Other sim endpoints (instructor only, see §3)
`/api/instructor/snapshot`, `/api/vr`, `/api/command`, `/api/scenarios`, `/api/scenario/debrief`, `/api/failures`,
`/api/failure-catalog`, `/api/breakpoints`, `/api/breakpoint/{save,load}`, `/api/dumps*`, `/api/reports*`,
`/api/config/*`. **No MCS, planner or rfsim code calls any of these.**

---

## 3. Instructor console on 8080: what a proxy must forward

### 3.1 Route table (`smo-simulator/.../instructor/app.py:66-158` plus the mounted libraries)
| Method | Path | Handler / source | Proxy policy |
|---|---|---|---|
| GET | `/`, `/classic`, `/modern` | `_serve_index` (`:214-264`). `?ui=` and `?lang=` resolved per request (`:214-224`); `Cache-Control: no-cache` | forward |
| GET (WS) | `/ws` | `handle_ws` (`:267-304`) | forward / synthesize (§3.2) |
| GET | `/api/state` | `:307-309` | **serve locally** (§2.3) |
| GET | `/api/instructor/snapshot` | ground truth, 23.6 kB (`:477-485`) | forward (instructor only) |
| GET | `/api/vr` | `:311-321` | forward |
| POST | `/api/command` | allowlisted instructor command; 403 for TC-looking payloads (`:324-362`, `engine.py:3776-3787`) | forward (instructor only) |
| GET | `/api/scenarios`, `/api/scenario/debrief`, `/api/failures`, `/api/failure-catalog`, `/api/breakpoints` | `:365-435` | forward |
| POST | `/api/breakpoint/save`, `/api/breakpoint/load` | run on the tick thread, **wait up to 10 s** (`engine.py:3849-3850`); write `workspace/breakpoints/*.json` on the sim host (`breakpoints.py:148-152`) | forward, **proxy timeout ≥ 15 s** |
| GET | `/api/dumps`, `/api/dumps/`, `/api/dumps/file`, `/api/dumps/summary`, `/api/dumps/{name}`, `/api/dumps/{name}/summary`, `/dumps` | `dump_store.py:522-531` (read-only) | forward (optional; the MCS serves the ground copy) |
| GET, POST | `/api/reports`, `/api/reports/`, `/api/reports/templates`, `/api/reports/templates/{id}`, POST `/api/reports/validate`, **POST `/api/reports/generate`** (writes `workspace/reports/` on the sim host, `reporting/generate.py:31`), `/api/reports/file`, `/reports` | `reporting/api.py:212-220` | read routes: forward. `generate`: **block** (use MCS `/reports`) |
| GET, POST | `/api/config/files`, `/file`, `/schema`, POST `/validate`, POST `/diff`, `/history`, `/revisions/{rev}`, `/diff/{a}..{b}`, `/crosschecks`, `/baselines` | `confedit/api.py:240-249` | **block all** (MCS has `/config` read-only, `smo-mcs/.../server.py:1521-1523`) |
| **PUT** | `/api/config/file` | **writes `configs/` and shadow git** | **BLOCK** |
| **POST** | `/api/config/revert`, `/api/config/baselines`, `/api/config/baselines/{name}/apply` | writes | **BLOCK** |
| GET | `/config` | page rendered with `READONLY=false` (`confedit/api.py:230-235`, `instructor/app.py:130-137`) | **BLOCK** (it would show edit controls) |
| GET | `/static/shared/*` | `smo_common/ui/` (`components.js`, `design-system.css`, `format.js`, `glyphs.svg`, `i18n.js`, `i18n/`) (`:141-154`) | forward (or serve from the identical image) |
| GET | `/static/*` | `instructor/static/` (`index.html`, `modern/{index.html,instructor.js,i18n/fr.json}`, `vendor →` symlink to repo `vendor/`: `css/fonts.css`, `fonts/*.woff2`, `js/chart.umd.min.js`) (`:156-158`) | forward |

Middleware sets `Cache-Control: no-cache` on `/static/modern/*` and `/static/shared/*` (`:41-47`). aiohttp sends ETags.
The proxy must pass through `ETag`, `If-None-Match` and 304 responses.

### 3.2 WS `/ws` messages
- **Server → client:**
  - `{"type":"state_update","state":<get_state_summary()>}`, once per second to every client, through one serial loop
    (`server.py:172-187`; about 10.8 kB per message).
  - Per inbound message, one reply: `{"status":"ok"}` or `{"status":"denied","message":…}`. Malformed JSON gives
    `"malformed JSON: …"`; a TC-looking payload gives `TC_BACK_CHANNEL_DENIED`; failure-catalogue validation or the
    engine allowlist give their own reason (`app.py:276-297`).
  - The UIs also handle `event`, `failure_injected` and `failure_cleared` (`static/index.html:1622-1633`,
    `modern/instructor.js:164-171`), but **the sim never sends them** (only `state_update` is ever emitted).
- **Client → server:** JSON instructor commands. The **classic** page sends commands on the WS (and also POSTs some),
  for example `start_scenario`, `stop_scenario`, `failure_inject` payloads, `failure_clear`, `failure_clear_all`,
  `load_breakpoint`, `set_speed`, `set_battery_soc`, `freeze`, `resume` (`static/index.html:2053-2497`, `wsSend`
  `:1612-1618`). The **modern** page is inbound-only and commands go through POST `/api/command`
  (`modern/instructor.js:8-16, 148-172`).
  - Allowed types: `set_speed, freeze, resume, inject, clear_failure, failure_inject, failure_clear,
    failure_clear_all, override_passes, set_phase, pause_scenario, start_separation, save_breakpoint, load_breakpoint,
    start_scenario, stop_scenario, set_battery_soc` (`engine.py:3776-3787`).
- **Reconnect:** classic uses `WS_RECONNECT_DELAY`; modern uses the shared `wsClient` "house 3-second reconnect"
  (`smo-common/.../ui/components.js:660-685`).
- **Recommended GSG implementation:**
  - Synthesize `state_update` locally from the STATE stream (with the §2.3 time rewrite) for **all** local `/ws` clients,
    including rfsim. This needs one WAN stream instead of 11 kB/s per client.
  - Forward each inbound text frame verbatim as a `CMD` message to the agent. The agent submits it to the sim's
    `/ws` (keeping one WS to the sim, so the WS semantics are exact) and returns the reply to the originating client only.
  - Fallback: a transparent per-client WS relay.

### 3.3 Origin and path assumptions
- **Root-relative everywhere:** module imports `"/static/shared/components.js?v=1"`, `"/static/shared/i18n.js"`
  (`modern/instructor.js:24-30`); CSS `/static/shared/design-system.css?v=1` and script
  `/static/modern/instructor.js?v=1` (`modern/index.html:32, 588`); `href="/config"` (`index.html:1137`,
  `modern/index.html:307`); `apiGet("/api/...")`.
- **WS URL:** `${proto}//${location.host}/ws` with `wss:` under https (`index.html:1583-1584`,
  `modern/instructor.js:159-162`). Classic uses `API_BASE = window.location.origin` (`index.html:1545`).
- **No hard-coded host or port** in instructor JS or HTML (grep finds no `:80xx` or `:90xx`). **No cookies, no
  localStorage auth.**
- ⇒ It works behind TLS on its **own origin** (subdomain or dedicated port). It **cannot be mounted under a path
  prefix** such as `/instructor/` without rewriting. The `/config` link appears in both UIs, so the GSG should return a
  clear 403 or a redirect to the MCS `/config`.

---

## 4. Delayed-TM dumps (S15)

### 4.1 Writer (simulator)
- `SimulationEngine.queue_dump(store_id)` (`engine.py:3418-3482`) is called from the S15.9 handler **on the tick
  thread**.
  - It copies the store packets into `_dump_pending` (cap 5000) for paced emission.
  - It **synchronously writes the complete raw dump** to `self._dump_dir / f"dump_sid{store_id:02d}_{YYYYMMDDThhmmssZ}.bin"`
    (`:3452-3473`).
- **Timestamp:** the **sim time** at the dump command, in UTC. On collision the name steps +1 s, up to 60 times
  (`:3456-3468`). The name must match `DUMP_NAME_RE = ^dump_sid(\d+)_(\d{8}T\d{6}Z)\.bin$` (`dump_store.py:85-89`).
- **Format:** repeated `uint32 BE length` + raw packet bytes (`engine.py:3469-3472`; `dump_store.py:27-28`). The file
  holds **all** stored packets, including ones the RF link later loses.
- **Not atomic:** `path.open("wb")`, written in place with no temp file and no fsync. It is written in one burst by the
  tick thread, so a concurrent `GET /api/dumps` listing can see a partial file.
- **Sizes:** store capacities are HK 18 000 (circular), Event 2 000, Science 10 000, Alarm 500 packets
  (`tm_storage.py:33-38`). An HK dump is ≤ ~18 000 × (4 + ~100 B) ≈ **1.9 MB**. S13 is never stored
  (`tm_storage.py:69`).
- The location is resolved once at engine init: `resolve_dump_dir(mission_cfg)` = `SMO_DUMP_DIR` > `mission.yaml
  dump_dir` > `workspace/dumps`, relative to the cwd (`engine.py:396-398`; `dump_store.py:105-125`). start.sh pins an
  absolute path (`start.sh:81-82`).

### 4.2 Readers (ground)
- **MCS:** `_dump_dir` comes from the same resolver (`server.py:576-584`). It mounts `/api/dumps*` and `/dumps`
  (`:1498-1502`) and `/api/reports*` and `/reports` over the same dir (`:1509-1515`). Listing = `glob("dump_*.bin")`,
  sorted, with metadata `size_bytes` and `mtime` (ISO from `st_mtime`) (`dump_store.py:180-213`). Download and summary
  go through `resolve_dump_file` (basename-only containment, `:217-264`).
- **`tools/delayed_tm_viewer.py`:**
  - Local mode: `--dumps` > `SMO_DUMP_DIR` > mission > default, resolved to an absolute path (`:1366-1375`). start.sh
    and start-all.sh use `--dumps "$SMO_DUMP_DIR"` (`start.sh:306`; `deploy/start-all.sh:211-212`).
  - `--api URL` (or `SMO_DUMP_API`) mode: `RemoteDumpStore` appends `/api/dumps`, lists with `GET`, fetches
    `GET /api/dumps/file?name=` into a temp cache, and validates the name with `DUMP_NAME_RE` (`:207-260, 1289-1293,
    1360-1363`).
- The report generator and `generate_report` read the same files (`reporting/api.py:65-100`).

### 4.3 Spec for shipping dumps
- **Agent:**
  - Poll the sim's own `GET http://127.0.0.1:8080/api/dumps` every 2–5 s (the route exists on the sim,
    `instructor/app.py:91-99`). This avoids filesystem coupling and keeps the agent a pure client. Alternative: watch
    `SMO_DUMP_DIR` directly.
  - Treat a file as complete when `size_bytes` and `mtime` are unchanged across two polls, or its `mtime` is ≥ 2 s old.
  - Fetch it with `GET /api/dumps/file?name=…` and send a `DUMP` message: `{name, size, sha256, mtime_utc}` plus the bytes
    in ≤ 256 kB chunks.
  - Track names already acknowledged by the GSG. Resend after reconnect until acknowledged.
- **GSG:**
  - Validate the name with `DUMP_NAME_RE` and the hash.
  - Write `$SMO_DUMP_DIR/.part-<name>` (a leading dot so it does not match `dump_*.bin`), fsync, then
    `os.replace` to `<name>`, then `os.utime(path, (mtime, mtime))` so `/api/dumps` `mtime` matches the sim's listing.
  - Never overwrite an existing name with different bytes: log and keep both by refusing. Names are already
    collision-stepped by the sim.
  - The MCS, viewer and report tools then see identical files with no code change.
- Retention and object-storage copies (ARCHITECTURE §9) are GSG-side extras, invisible to the readers.

---

## 5. Config identity (bind check)

Facts:
- Each process loads `configs/eosat1/` itself at start-up. The MCS decodes HK only through `hk_structures.yaml`
  (`server.py:280-306`). `mission.yaml time_epoch` sets the process-wide CUC epoch (`config/loader.py:55-66`), and the
  APIDs come from `mission.yaml` (`server.py:309-319`).
- The config editor already classifies files. `interface_defining=True` marks `telemetry/hk_structures.yaml`,
  `telemetry/*.yaml`, `commands/tc_catalog.yaml`, `events/event_catalog.yaml` and `memory/memory_map.yaml`
  (`smo-common/.../confedit/classification.py:94-111`).
- An edit "never affects the running simulation" (restart scope, `confedit/editor.py:1-14`). **Compute the hash when
  the agent starts, alongside the sim**, not on demand.
- Runtime writers into `configs/`:
  - the config editor (sim host; `workspace/config-history`, `editor.py:52-55`);
  - MCS custom procedures in `procedures/custom/` (`smo-mcs/.../server.py:4274-4291`);
  - the scenario generator in `scenarios/` (`tools/scenario_generator.py:244, 1036-1043`). Scenarios are loaded once at
    sim start (`scenario_engine.py:172-200`).

**Proposed BIND SET.** A mismatch means the GSG **refuses to bind** (TM would mis-decode, TCs would mis-encode, or the
time or geometry would disagree):

| File | Why both sides must agree | Space reader | Ground reader |
|---|---|---|---|
| `telemetry/hk_structures.yaml` | HK wire layout | engine HK packing | MCS `server.py:280-306, 3309`; dump summary/reports |
| `telemetry/parameters.yaml` | param ids/names | engine | MCS `:353, 3308` |
| `commands/tc_catalog.yaml` | TC encoding | dispatcher | MCS `:441`; `smo_common.commanding.catalog` |
| `events/event_catalog.yaml` | S5 ids | engine `:2710` | MCS / reports |
| `memory/memory_map.yaml` | S6 addresses | `memory_map.py` | MCS `:887` |
| `monitoring/s12_definitions.yaml`, `monitoring/s19_rules.yaml` | S12/S19 report ids | engine `:900-910` | MCS `:761, 786` |
| `subsystems/ttc.yaml` | rate ladder / `command_code` | ttc model | MCS `:2240`, `link_prediction.py:49`; rfsim |
| `orbit.yaml` | TLE, t0, canonical stations (contact windows) | orbit/contact model | MCS `:931, 1022`; planner |
| `mission.yaml`: **canonical subset only** | `name, spacecraft_apid, bootloader_apid, pus_version, time_epoch, start_in_bootloader` | engine | MCS `:309-319`, CUC epoch |

**WARN SET** (log and raise a link-status advisory, but bind): `planning/ground_stations.yaml` (MCS
`link_prediction.py:77`, rfsim G/T; sim ttc model `ttc_basic.py:1924`), `subsystems/eps.yaml`, `subsystems/payload.yaml`,
`subsystems/prop.yaml` (MCS `:557`; planner budget, classification note `:115-117`), `fdir/fault_propagation.yaml` (MCS
`fault_graph.py:41`).

**EXCLUDE** (they legitimately differ or are one-sided):
- `mission.yaml` deployment keys: `network.*`, `sim_state_url`, `dump_dir`, `time_source`, `ui`, `ui_lang`.
- `rfsim.yaml` (ground-only endpoints); `mcs/**`; `planning/*` except `ground_stations.yaml`; `telemetry/derived.yaml`
  (ground-computed, `derived_params.py:27`).
- `procedures/**` (the MCS writes `custom/`); `scenarios/**` (written at runtime, space-only).
- `simulation.yaml`, `obcp/**`, `fdir/procedures/**`, other `subsystems/*.yaml` (space-only model tuning).
- `manual/**`, `i18n/**`, `reports/**` (ground docs and templates).
- `xtce/**`, `smdl/**` (generated, not read at runtime, `classification.py:66-71`).
- Dead files `aocs/aocs_mode_codes.yaml`, `subsystems/memory_map.yaml` (`:61-65`); `**/.DS_Store`.

**Algorithm** (stdlib):

```
digest = sha256()
for relpath in sorted(BIND_SET):                  # posix relpaths
    data = read_bytes(relpath).replace(b"\r\n", b"\n")   # Windows checkouts (cf. defect 134)
    if relpath == "mission.yaml":
        data = json.dumps({k: yaml[k] for k in MISSION_KEYS}, sort_keys=True).encode()
    digest.update(relpath.encode() + b"\0" + len(data).to_bytes(8,"big") + data)
```

Send it in `HELLO` together with a per-file digest map, so the GSG can name the differing file, plus the advisory
`smo_common` package version or image tag (the HK packing code also matters). `tools/source_revision.py:31-40` already
implements the same sorted-path sha256 pattern.

---

## 6. `smo-gateway` and `deploy/`: what to retire

- **Package:** `packages/smo-gateway/` contains `pyproject.toml` and `src/smo_gateway/{__init__,gateway,upstream,downstream}.py`.
  - `gateway.py` (129 lines) is the only one used. It is TM-only in practice: it connects upstream once with no
    reconnect (`:31-49`, `:80-83`), and its TCs go into the sim **TM** socket (`:59-67`), which never reads.
  - `upstream.py` and `downstream.py` are unused by `gateway.py` but are unit-tested.
  - **Replace it wholesale with the GSG plus the agent.** Nothing in it is reusable beyond `framing.py`.
- **Tests referencing it:**
  - `tests/test_gateway/test_gateway.py` (301 lines; imports all three modules, `:25-27`). Delete.
  - `tests/conftest.py:10` (sys.path list). Remove the entry.
  - `tests/test_mcs/test_s11_time_tag_timezone.py:243` (PYTHONPATH list for a subprocess). Remove the entry; a missing
    dir is harmless.
  - `tests/test_content/test_deployment_consistency.py:85-98` asserts that `deploy/start-gateway.sh` contains
    `GATEWAY_BIND`, that `smo-env.conf` defines it and that `start-all.sh` uses it. **It must be edited** (drop that row
    or replace it with the GSG script) or it fails once the script is removed.
- **deploy/:** `start-gateway.sh` (whole file); `smo-env.conf:29-43, 126`; `start-all.sh:6, 56-58, 68, 157-170,
  279-281`; `start-mcs.sh:5, 43-47`; `install.sh:189, 295, 353`; `package.sh:49`; `INSTALLATION_MANUAL.html`.
- **Docs:** `README.md:54`; `docs/architecture.md:51`; `docs/DEPLOYMENT.md:97-129`; `docs/OPERATIONS_GUIDE.md:96-106`
  (and `docs/fr/`); `configs/eosat1/manual/software_architecture.md:236-252, 957-967` (and its FR i18n copy, which is in
  the config tree but excluded from the bind hash); `scripts/upload_and_file_defects.sh:160,199` (historical labels,
  leave).
- Also stale for the cloud: `deploy/start-mcs.sh` and `start-planner.sh` set no `SMO_SIM_STATE_URL`
  (`start-planner.sh:57-60`; `start-all.sh:179-197`). With the GSG on loopback this is harmless, because their defaults
  resolve to `connect_host:8080` and `localhost:8080`.

---

## 7. Process launch and wiring by environment

### 7.1 Current knobs
| Knob | Who reads it | Evidence |
|---|---|---|
| `SMO_BIND` (bind addr) | sim (`server.py:39-40`), MCS/planner `--host` default, start.sh (`:99-104`) | |
| `SMO_SIM_HTTP_PORT` | sim `--port` default (`server.py:226-231`), MCS default sim-state port (`smo-mcs/.../server.py:216-217`), start.sh (`:64-65`) | planner **ignores** it (hard 8080, planner `server.py:130`) |
| `SMO_SIM_STATE_URL` | MCS (`:218-223`), planner (`:125-131`); start.sh exports it (`:226`) | |
| `SMO_TIME_SOURCE` | MCS (`:174-179`), planner | |
| `SMO_PLANNER_URL` | MCS (`:598-602`); set by start-all (`:174-176`), **not** by start.sh | |
| `SMO_MCS_URL` | planner (`:264`) | |
| `SMO_DUMP_DIR` | sim, MCS, viewer (`dump_store.py:113-125`); start.sh (`:81-82`) | |
| `SMO_DUMP_API` | viewer `--api` (`delayed_tm_viewer.py:1289`) | |
| `SMO_UI`, `SMO_LANG` | all UIs | |
| `SMO_VR`, `SMO_VR_PORT`, `SMO_VR_WS_PORT` | sim (`server.py:234-262`) | |
| `SMO_TM_ARCHIVE`, `SMO_PASS_ROLLUPS` | MCS archive, rfsim rollups | |
| **CLI only** | MCS `--connect host:port`, `--tc-port` (`:5487-5523`); planner `--connect-host`; rfsim everything via `rfsim.yaml` network block | |
| **Hard-coded** | sim TM/TC 8001/8002 (`server.py:274-278`); planner default 8080; rfsim defaults `127.0.0.1:8001/8002/8080` | |

`start.sh` always launches and waits for the simulator (`:228-238`), then rfsim and MCS (`:243-295`), and the tools.
`deploy/start-all.sh` does the same (`:145-155`).

### 7.2 Profiles (new: wiring by env only, no service changes)
- **`space`** = simulator + agent, all on loopback.
  - Simulator: `SMO_BIND=127.0.0.1`, `SMO_SIM_HTTP_PORT=8080`, `SMO_DUMP_DIR=<space>/dumps`, `SMO_VR=0` on a cloud host
    (or VR ports for a laptop), then `smo-simulator --config configs/eosat1/ --host "$SMO_BIND" --port "$SMO_SIM_HTTP_PORT"`.
  - Agent (new; proposed env): `SMO_LINK_URL=wss://<gsg>/link`, `SMO_LINK_TOKEN=<session token>`,
    `SMO_SIM_HOST=127.0.0.1`, `SMO_SIM_TM_PORT=8002`, `SMO_SIM_TC_PORT=8001`, `SMO_SIM_HTTP_PORT` (reused),
    `SMO_CONFIG_DIR=configs/eosat1`.
- **`ground`** = GSG + MCS + planner + (rfsim) + tools.
  - GSG (new): `SMO_GSG_BIND=127.0.0.1`, `SMO_GSG_TM_PORT=8002`, `SMO_GSG_TC_PORT=8001`, `SMO_GSG_HTTP_PORT=8080`
    (local `/api/state` + `/ws` + instructor proxy), `SMO_GSG_LINK_BIND=0.0.0.0:<port>` (WSS ingress behind the load
    balancer), `SMO_DUMP_DIR=<ground>/dumps`, `SMO_CONFIG_DIR`.
  - MCS: `--connect 127.0.0.1:8002` (direct) or `127.0.0.1:8012 --tc-port 8011` (RF), unchanged from `start.sh:288,291`;
    `SMO_SIM_STATE_URL=http://127.0.0.1:8080/api/state` (already the start.sh value); `SMO_PLANNER_URL`,
    `SMO_TIME_SOURCE=sim`, `SMO_DUMP_DIR` the same as the GSG.
  - Planner: `--connect-host 127.0.0.1` (or the inherited `SMO_SIM_STATE_URL`); `SMO_MCS_URL=http://127.0.0.1:9090`.
  - rfsim: shipped `rfsim.yaml` unchanged. **Start it only after the GSG TM port is open.**
  - Viewer: `--dumps "$SMO_DUMP_DIR"` (unchanged).
  - Scenario generator: belongs to `space` (it writes the sim's `scenarios/`) or must be dropped from `ground`.
- **start.sh needs a profile switch** (for example `SMO_PROFILE=space|ground`), because today it hard-wires "start
  simulator first" and its readiness probe is `GET :8080/api/state` (`:235`). In `ground` that probe hits the GSG and
  only passes once the link is UP, so the ground probe must be `wait_for_port 8002` instead, unless the GSG answers
  `/api/state` with 503 and readiness uses a GSG `/healthz`.
- **Port collision:** in the `ground` profile the GSG owns 8001/8002/8080, so no simulator may run on that host. A
  cloud-sim provider in the same VPC runs in its own container.

---

## 8. Test infrastructure for an end-to-end link test

- **Run here:** `cd /home/claude/work/smo && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/smo-rfsim/src python -m pytest -p no:cacheprovider -q tests/...`
  - `tests/conftest.py:9-13` adds `smo-common`, `-simulator`, `-gateway`, `-mcs` and `-planner` `src/` to `sys.path`,
    but **not rfsim**, hence the PYTHONPATH.
  - `pyproject.toml`: `asyncio_mode = "auto"`, markers `slow` and `e2e`.
  - Verified: 43 passed, 1 failed in 7 s on `test_http_port_configurable`, `test_gateway`, `test_back_channel_closed` and
    `test_mcs_hk_round_trip`. The failure is **pre-existing**: `test_mcs_hk_round_trip.py::test_sid7_aocs_determination_round_trip`,
    `KeyError 0x02C6`, `:155`.
  - The SMO packages are **not pip-installed** here (no `smo-*` in `pip list`), so the `smo-simulator` and other console
    scripts are absent. For subprocesses use `python -m smo_simulator.server`, `smo_mcs.server`, `smo_planner.server`
    and `smo_rfsim.bridge`, with PYTHONPATH covering all six `src/` dirs (each module has a `__main__` guard:
    sim `server.py:282`, MCS `:5529`, planner `:1793`, rfsim `bridge.py:976`).
- **In-process building blocks:**
  - `SimulatorServer(engine, config={"tc_port","tm_port","http_port","bind_host","vr":None})` takes **arbitrary ports**,
    unlike `main()`. See the `_free_port()` pattern in `tests/test_simulator/test_http_port_configurable.py:27-31,
    80-110`.
  - Measured: `SimulationEngine(config_dir=…)` initialises in **0.7 s**. POST `/api/command
    {"type":"override_passes","enabled":true}` makes TM flow within seconds (beacon only at boot).
  - `MCSServer(config_dir, connect_host, connect_port, http_port, tc_port=, sim_state_url=, time_source=, bind_host=)`
    (`smo-mcs/.../server.py:126-135`). `start()` runs the TM, TC and state-poll loops (`:1565-1576`).
  - `PlannerServer(config, port, time_source=, sim_state_url=, connect_host=, bind_host=)` (planner `server.py:80-81,
    1784-1791`).
  - Light harnesses: `aiohttp.test_utils.TestServer/TestClient` (`tests/test_common/test_ui_switch.py:93-94`); fake TC
    writer capturing frames (`tests/test_integration/test_planner_mcs_s11_chain.py:27-45`); engine + RF pipeline harness
    (`tests/test_acceptance/conftest.py:1-40`); `_process_tm` direct injection (`tests/test_mcs_hk_round_trip.py:39-60`).
- **Live-stack fixture:** `tests/test_e2e_browser/conftest.py:50-160` starts the sim, rfsim RF, MCS, planner and tools as
  subprocesses on the **fixed default ports** with console scripts, and skips if a port is busy. Use it as a template
  only: here it needs `python -m …` and the Playwright browser is gated by `SMO_E2E=1`.
- **Suggested link e2e:**
  - Topology: sim (free ports) ⇄ agent ⇄ in-process GSG (free ports, `ws://` loopback, optional injected delay or
    jitter) ⇄ MCSServer (`--connect` GSG TM, `tc_port` GSG TC, `sim_state_url` GSG) plus PlannerServer.
  - Assert:
    - TM byte equality: the sim TM tap and the GSG TM tap match.
    - A TC through the MCS `/api/pus-command` yields S1.1 and S1.7 at the MCS.
    - With 200 ms injected one-way delay at ×60, `|MCS sim_now − engine._sim_time| < 1 tick × speed` (about 60 s).
    - Link DOWN gives MCS `503 No TC connection` within 3 s and GSG `/api/state` 503 after 5 s, and the rfsim TM socket
      stays open.
    - S15.9 dump: same name and sha256 in both dump dirs, and `GET /api/dumps` on the MCS lists it.
  - Use `pytest-timeout` (installed).

---

## 9. Python and dependencies

- **This environment:** Python **3.13.18** (`/usr/local/bin/python3`). Installed: **aiohttp 3.14.5** (WS client and
  server, `compress` permessage-deflate, `heartbeat`), yarl 1.25.1, multidict 7.2.1, **PyJWT 2.15.0**, **cryptography
  50.0.1**, pydantic 2.13.5, PyYAML 6.0.3, numpy 2.5.3, sgp4 2.27, reedsolo 1.7.0, matplotlib 3.11.2, httpx 0.28.1,
  requests 2.34.2, pytest 9.1.1, pytest-asyncio 1.4.1, pytest-timeout 2.4.0, playwright 1.63.0. **`websockets` is NOT
  installed.**
- **Repo-declared deps:** smo-common `pydantic>=2, pyyaml>=6, sgp4>=2.20, numpy>=1.24` (+ `reports` extra matplotlib);
  smo-simulator, smo-mcs and smo-planner `aiohttp>=3.9`; smo-rfsim `aiohttp>=3.9, reedsolo>=1.7`; smo-gateway
  `smo-common` only. `requires-python >=3.10` per package and `>=3.11` at the root. start.sh tells users to build a
  `python3.11` venv (`start.sh:166-168`). **PyJWT and cryptography are not declared anywhere.**
- **Recommendation:** build both the agent and the GSG on **stdlib + aiohttp only**.
  - aiohttp: `ClientSession.ws_connect(..., heartbeat=10, compress=15)` on the agent; `web.WebSocketResponse` on the GSG.
  - Session token: stdlib `hmac` / `hashlib` / `secrets` (an HMAC-SHA256 signed `{session, exp, nonce}`).
  - TLS: stdlib `ssl` (or terminated at the load balancer).
  - Add a new `smo-link` package (or `smo-gateway` rewritten) depending only on `smo-common` and `aiohttp>=3.9`.
  - Verifying IAP JWTs (ES256) for the instructor proxy would need `cryptography` + `PyJWT`. Keep that in the
    WP-3 hardening layer, not in the link.

---

## 10. Proposed wire protocol on the WSS link (derived from the above)

One WSS connection, agent → GSG, binary messages `[1-byte type][payload]`:

| Type | Dir | Payload | Notes |
|---|---|---|---|
| `HELLO` | A→G | JSON `{proto:1, session, token, config_hash, config_files{path:sha}, sw_version, sim{tick_hz, speed, sim_time}}` | GSG refuses (close 4403) on token failure or BIND-SET mismatch |
| `TM` | A→G | concatenated `framing.frame_packet` frames, in sim order; flush every ≤ 20 ms or 32 kB | the GSG fans out exactly like `server.py:149-170` (2 s drain timeout per client) |
| `TC` | G→A | concatenated framed TCs, in arrival order across local clients | the agent writes them to its single sim TC socket; **never replayed** after reconnect |
| `STATE` | A→G | JSON `{t_agent, state:<summary>}` per sim `state_update` (1 Hz) and on speed change | the GSG serves `/api/state` and local `/ws` (§2.3, §3.2) |
| `CMD` / `CMD_REPLY` | G→A / A→G | `{id, json}` / `{id, reply}` (`status`/`message`) | instructor WS commands; HTTP proxy uses `HTTP_REQ`/`HTTP_RESP` (method, path, query, headers subset, body; streamed for `/api/dumps/file`) with a deny-list (§3.1) |
| `DUMP_META`, `DUMP_CHUNK`, `DUMP_ACK` | A→G, A→G, G→A | §4.3 | |
| `PING` / `PONG` | both | `{t0}` / `{t0,t1,t2}` | clock offset (§2.4) + link status UP/DEGRADED/DOWN |

**Buffering policy:**
- Agent TM queue: bounded (for example 20 000 packets). In *online-timely* mode, drop the oldest on overflow; in
  *online-complete* mode, block the queue but **never** the sim socket read (constraint 2).
- GSG downstream: no replay to local clients on their reconnect, because the sim never replays either (§1.2) and the MCS
  archive would double-insert.
