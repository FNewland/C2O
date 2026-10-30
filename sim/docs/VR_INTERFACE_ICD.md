# VR Visualisation Interface — ICD `smo-vr/1`

**Status:** issue 1, 2026-09-27 · **Owner:** SMO suite (smo-simulator `vr_bridge.py`)
**Users:** first-year VR headset teams (GNG) and anyone building an external 3-D viewer.

## 1. Purpose

The simulator streams what a camera floating next to EOSAT-1 would need to draw
the scene: where the spacecraft is, how it is oriented, where the Sun and Earth
are, and whether the solar wings and antenna are deployed. A headset may
(optionally) send back a short status line so the instructor console shows
whether each headset is receiving data and is happy.

This is **simulation truth for visualisation**. It is not spacecraft telemetry,
it does not pass through the MCS or the radio, and nothing a headset sends can
change the simulation.

```
 smo-simulator (engine tick, 1 Hz at x1)
   └─ vr_bridge ── TCP 8100 (NDJSON) ──►  Unity / Unreal / native headset app
                └─ WS  8101 /vr     ──►  WebXR / three.js / A-Frame page
                ◄── optional "status" lines ──┘
   └─ instructor console header: "VR n OK" badge, GET /api/vr
```

The stand-alone stub `tools/vr_stub/vr_stub.py` speaks exactly the same protocol,
so teams can develop without the simulator.

## 2. Transports

| | TCP | WebSocket |
|---|---|---|
| Default port | **8100** | **8101**, path `/vr` (or `/`) |
| Framing | one JSON object per line, UTF-8, `\n` terminated | one JSON object per text message |
| Suits | Unity (`TcpClient`), Unreal, Python, C++ | browsers (WebXR, three.js) — browsers cannot open raw TCP |
| Inbound limit | 4096 bytes per line | 4096 bytes per message |

* The simulator is the **server**; headsets connect as clients. Any number of
  clients may connect; each gets the same stream.
* Configuration: `configs/eosat1/mission.yaml` → `network.vr_*`; overrides
  `smo-simulator --vr-port / --vr-ws-port / --no-vr`, env `SMO_VR_PORT`,
  `SMO_VR_WS_PORT`, `SMO_VR=0`.
* **Headsets on Wi-Fi:** start the suite with `./start.sh --public` (LAN bind).
  The default local mode binds loopback only, which a headset cannot reach.
  The machine's firewall must allow inbound 8100/8101.
* A client that cannot keep up (write blocked > 2 s) is disconnected. Reconnect.

## 3. Message flow

1. On connect the server sends one **`hello`**, then immediately the latest
   **`state`** (if any).
2. Then one `state` per new simulator tick (1 Hz at speed ×1), plus a repeat of
   the latest frame at least once a second while the simulation is frozen.
   Never faster than `max_rate_hz` (default 10).
3. The client may send **`status`** lines at any time; ~1 Hz is ideal.

Positions change by ~7.5 km per second of sim time, so **interpolate** between
frames for smooth motion (slerp the quaternion, lerp the position, or propagate
with `vel_eci_km_s`). At high time acceleration (`speed` ≫ 10) frames are far
apart in the orbit: snap instead of interpolating.

## 4. `hello` (server → client, once)

Static description; the full text is in the message. Key fields:

| Field | Meaning |
|---|---|
| `type` | `"hello"` |
| `schema` | `"smo-vr/1"` — refuse to run if the major version differs |
| `source` | `"smo-simulator"` or `"vr-stub"` |
| `max_rate_hz` | upper bound on frame rate |
| `frames` | text definitions of the frames (§6) |
| `status_bits`, `healthy_mask` | the status-word definition (§7) |
| `spacecraft` | body-axis meaning, bus size `[0.100, 0.226, 0.366]` m (X, Y, Z), wing size, SADA convention, suggested antenna model |

## 5. `state` (server → client, ~1 Hz)

Example (one line on the wire, pretty-printed here):

```json
{"type":"state","schema":"smo-vr/1","seq":1812,
 "sim_time":"2026-08-20T12:30:12.000Z","met_s":1812.0,"tick":1812,"speed":1.0,
 "orbit":{"pos_eci_km":[-4702.3,2515.9,4406.8],"vel_eci_km_s":[-3.09,4.07,-5.62],
          "lat_deg":39.8,"lon_deg":-77.1,"alt_km":505.2},
 "attitude":{"q_body_to_eci":[0.123,-0.702,0.281,0.643],"rate_body_deg_s":[0.0,-0.0635,0.0],
             "aocs_mode":"NOMINAL","pointing":"NADIR"},
 "sun":{"dir_eci":[-0.843,0.493,0.214],"dir_body":[0.41,0.47,-0.78],"in_eclipse":false,"sun_fraction":1.0},
 "earth":{"dir_body":[0.0,0.0,1.0],"gmst_deg":156.4,"radius_km":6371.0},
 "deploy":{"wing_py":{"state":"DEPLOYED","fraction":1.0},
           "wing_my":{"state":"DEPLOYING","fraction":0.43},
           "sada_angle_deg":-48.2,
           "antenna":{"state":"DEPLOYED","deployed":true,"sensor":"DEPLOYED"}},
 "mission":{"sc_mode":"SAFE","phase":"LEOP","in_contact":true,"ground_station":"Iqaluit"}}
```

| Field | Type / unit | Meaning |
|---|---|---|
| `seq` | int | increments by 1 per message **on this connection's server**; a gap = frames you missed, a repeat = keepalive |
| `sim_time` | ISO-8601 UTC | simulated time. **Can jump** (instructor loads a breakpoint, stub story loops) |
| `met_s` | s | mission elapsed time |
| `tick` | int | simulator tick; unchanged on keepalive repeats |
| `speed` | × | time acceleration |
| `orbit.pos_eci_km` | km, ECI | spacecraft position (Earth centre at origin) |
| `orbit.vel_eci_km_s` | km/s, ECI | velocity (for interpolation) |
| `orbit.lat_deg/lon_deg/alt_km` | deg, deg, km | sub-satellite point and altitude |
| `attitude.q_body_to_eci` | `[x,y,z,w]` | **the** attitude, see §6 |
| `attitude.rate_body_deg_s` | deg/s, body | body angular rate (spin the model between frames) |
| `attitude.aocs_mode` | enum | `OFF SAFE_BOOT DETUMBLE COARSE_SUN NOMINAL FINE_POINT SLEW DESAT ECLIPSE INERTIAL` |
| `attitude.pointing` | enum | `NADIR INERTIAL TARGET_TRACK SUN` (the reference the AOCS steers to) |
| `sun.dir_eci` | unit vector | direction **to** the Sun, ECI |
| `sun.dir_body` | unit vector | direction to the Sun in body axes (ready-made for a satellite-fixed camera) |
| `sun.in_eclipse` | bool | umbra: no direct sunlight — dim the sun light |
| `sun.sun_fraction` | 0–1 | visible fraction of the solar disc (penumbra fades) |
| `earth.dir_body` | unit vector | direction to Earth's centre in body axes (≈ `[0,0,1]` when nadir pointing) |
| `earth.gmst_deg` | deg | Earth rotation angle: ECEF = ECI rotated by −gmst about Z. Rotate your Earth model by **+gmst** about the pole so the continents are right |
| `earth.radius_km` | km | Earth radius the simulator uses |
| `deploy.wing_py`, `wing_my` | `{state, fraction}` | `STOWED` 0.0 → `DEPLOYING` 0–1 (≈30 s sweep) → `DEPLOYED` 1.0 |
| `deploy.sada_angle_deg` | deg | solar-array drive angle; wing cell normal in body = `(cos a, 0, sin a)` |
| `deploy.antenna.state` | enum | `STOWED`, `DEPLOYED`, `JAMMED` (partial deployment failure) |
| `deploy.antenna.deployed` | bool | truth: is the antenna out |
| `deploy.antenna.sensor` | enum | what the deployment microswitch reports (`UNKNOWN STOWED DEPLOYED JAMMED`) — may disagree with truth under failure injection |
| `mission.sc_mode` | enum | `SAFE NOMINAL SCIENCE EMERGENCY` |
| `mission.phase` | enum | `PRE_SEPARATION SEPARATION_TIMER INITIAL_POWER_ON BOOTLOADER_OPS LEOP COMMISSIONING NOMINAL` |
| `mission.in_contact`, `ground_station` | bool, str | a ground station can see the spacecraft (draw a link beam?) |

## 6. Frames and conventions

* **ECI** — Earth-centred inertial, right-handed, km. +X towards the vernal
  equinox, +Z through the North Pole. (Strictly SGP4's TEME frame; the
  difference from J2000 is invisible at VR scale.)
* **Body** — right-handed, fixed to the spacecraft:
  +X along-track (velocity) in nominal pointing · +Y cross-track, +Y wing and
  solar-array-drive axis · **+Z nadir** (imager, faces Earth) · −Z zenith.
  6U bus 0.100 × 0.226 × 0.366 m along X, Y, Z.
  These are the smo-vr/1 interface axes, and they are not the simulator's
  own body frame. Since author ruling Q4 (2026-10-30) the simulator and the
  operations manual use +Z = zenith and −Z = nadir (imager and radiator on
  −Z), with +Y = +orbit normal. The VR bridge converts every body-frame
  quantity, `v_vr = diag(1, −1, −1) · v_sim` (a 180° turn about X), so
  smo-vr/1 clients see exactly the axes above. A move of the ICD itself to
  the new convention would be a breaking change (smo-vr/2).
* **Quaternion** `q_body_to_eci = [x, y, z, w]` — scalar **last**, Hamilton
  convention, unit length. As an active rotation it takes a vector expressed in
  body axes into ECI: `v_eci = q ⊗ v_body ⊗ q*`. In a scene whose world axes are
  ECI, it is simply the satellite object's rotation.
  *Check:* in nominal nadir pointing, rotating body `[0,0,1]` by `q` gives
  `-pos_eci/|pos_eci|` (straight down).

### Converting to engine frames

| Engine | Axes | Vector `(x,y,z)` → | Quaternion `(x,y,z,w)` → |
|---|---|---|---|
| **Unity** (left-handed, Y up) | swap Y/Z | `(x, z, y)` | `(-x, -z, -y, w)` |
| **three.js / WebXR** (right-handed, Y up) | rotate −90° about X | `(x, z, -y)` | `(x, z, -y, w)` |
| **Unreal** (left-handed, Z up, cm) | flip Y | `(x, -y, z)`·1e5 | `(-x, y, -z, w)` |

Ready-made C# for Unity: `tools/vr_stub/unity/VRLinkClient.cs`.

### Scene-building tips (not requirements)
* A satellite-centred scene is easiest: keep the satellite at the origin, put
  Earth's centre at `-pos_eci_km` (scaled), point the directional light along
  `-sun.dir_eci`.
* Real scale is brutal: a 0.37 m spacecraft 513 km above a 6371 km Earth. Use
  separate scales (true-scale satellite, compressed Earth distance), or a
  skybox Earth rendered from `earth.dir_body`.
* In eclipse the Sun is behind the Earth — a physically-correct scene goes
  dark. Consider a faint "earthshine" ambient light.

## 7. `status` (client → server, optional)

```json
{"type":"status","team":"T07","status_word":15,"state":"OK","seq_ack":1812,"fps":72,"text":"all good"}
```

| Field | Required | Meaning |
|---|---|---|
| `type` | yes | `"status"` |
| `status_word` | yes | integer 0–65535, **positive logic** (a bit set = that thing is working; 0 = nothing works) |
| `state` | no | `OK`, `WARN` or `ERROR` — the team's own verdict |
| `team` | no | ≤ 32 chars, shown on the instructor console |
| `seq_ack` | no | `seq` of the last frame you applied — the server reports how many frames you are behind |
| `fps` | no | headset frame rate |
| `text` | no | ≤ 200 chars, free text |

Status-word bits:

| Bit | Mask | Name | Set when |
|---|---|---|---|
| 0 | 0x0001 | `RX_OK` | frames are arriving |
| 1 | 0x0002 | `PARSE_OK` | the last frame parsed |
| 2 | 0x0004 | `RENDERING` | the scene is being drawn |
| 3 | 0x0008 | `DATA_FRESH` | newest frame is < 2 s old (wall clock) |
| 4 | 0x0010 | `DEPLOY_SHOWN` | optional: deployment is visualised |
| 5 | 0x0020 | `FRAMERATE_OK` | optional: holding target frame rate |
| 6–7 | | reserved | send 0 |
| 8–15 | 0xFF00 | team-defined | anything your team wants to report |

Bits 0–3 all set (`status_word & 0x000F == 0x000F`) = **healthy**.

How the simulator classifies each client (instructor badge `VR n <worst>`, `GET /api/vr`):

| Health | Meaning |
|---|---|
| `NO_REPLY` | connected, never sent a status line — fine, the return line is optional |
| `OK` | bits 0–3 set and `state` absent or `OK` |
| `DEGRADED` | replying, but a required bit is clear or `state` = `WARN` (badge amber) |
| `SILENT` | replied before, nothing for 5 s (badge amber) |
| `ERROR` | `state` = `ERROR` (badge red) |

Malformed status lines are counted (`rx_errors`, `last_error`) and ignored; the
connection stays up.

## 8. Rules for a robust client

1. **Ignore fields and message types you do not know.** New optional fields may
   appear in `smo-vr/1`; a breaking change becomes `smo-vr/2`.
2. **Skip a line that does not parse** and keep going — never crash on input.
3. `seq` gaps and repeats are normal. `sim_time` can jump backwards or forwards.
4. Reconnect automatically (every 2 s) when the socket drops.
5. Do socket I/O off the render thread; hand only the newest frame to it.
6. Test with `vr_stub.py --chaos` before demo day.

## 9. Flat files

`tools/vr_stub/sample_vr_frames.ndjson` — the exact wire messages (`hello` then
1135 `state` lines), one orbit at 5 s steps. `sample_vr_frames.csv` — the same
frames flattened: nested names joined with `_`, vectors as `_x/_y/_z`, the
quaternion as `_x/_y/_z/_w`, booleans as 0/1. The story (compressed LEOP):

| t (s) | Event |
|---|---|
| 0 | separated, tumbling ~2.7 °/s, everything stowed |
| 300 | detumble starts |
| 600 | antenna deploys |
| 900–1200 | acquires nadir pointing |
| 1300–1330 | +Y wing deploys |
| 1400–1430 | −Y wing deploys |
| 1440–1620 | solar-array drive starts tracking the Sun |
| 1980–4000 | eclipse |
| 4300–4800 | 25° roll slew for imaging, hold, slew back |
| 5670 | one orbit |

Record a real simulator session with
`tools/vr_stub/vr_client_example.py --record run.ndjson --csv run.csv` and
replay it with `vr_stub.py --replay run.ndjson`.

## 10. Known limitations (issue 1)

* During the bootloader phases (cold start, before LEOP) the simulator does
  not propagate attitude, so the quaternion stays at its initial value until
  the AOCS is running. The stub's story shows a tumble there instead.
* The stub uses a circular orbit and a cylindrical shadow; the simulator uses
  SGP4 and a conical shadow with penumbra. Positions agree to a few km and
  eclipse times to seconds for the reference epoch.
