# Web deployment options: research (SMO suite + SpaceCDF)

Research date 2026-10-28. Companion to `WEB_CURRENT_STATE.md` (code survey). This document covers external
options only, with citations. Version and date facts were checked live against package registries (PyPI, npm,
Go module proxy `proxy.golang.org`) on 2026-10-28 unless marked otherwise. GitHub itself was **not reachable** from
this session, so licence and activity claims for GitHub-only projects come from secondary sources (ecosyste.ms,
pkg.go.dev, vendor sites) and are flagged where weak.

Requirements, restated:

1. **Split SMO.** The simulator runs on Franz's laptop (behind NAT or university Wi-Fi). MCS, planner/wall,
   instructor and RF pages run on a cloud server and are used from browsers by remote teams in Canada and Denmark.
2. **Voice loops** in the browser, mission-control style.
3. **SpaceCDF.** Users can join a running instance or start their own.
4. **Constraints.** Single maintainer, teaching budget, open source and self-hostable preferred, student privacy
   (uOttawa/FIPPA, plus GDPR for Danish partners).

---

## 0. Recommendations at a glance

| Area | Recommendation | Runner-up / fallback |
|---|---|---|
| A. Voice loops | **Self-hosted LiveKit** (Apache-2.0). Use **one room per team session**, with each operator publishing **one always-muted mic track** and unmuting it for **PTT**. The talk loop is a participant attribute. Monitoring = selective subscription (`autoSubscribe:false`). Per-loop volume uses WebAudio. A small Python "loop controller" mints tokens from `positions.yaml` and enforces listen/talk rights with `updateSubscriptions`. A Python recorder bot does debrief recording with sim-time stamps. | **Spike openvocs first (1 day).** It is DLR/GSOC's Apache-2.0 browser mission-control voice system with TALK/MONITOR/NONE loops and RBAC, open-sourced July 2025. If it deploys cleanly, it is the most authentic option. Janus AudioBridge (MCU per loop, built-in recording) is the server-mix alternative. |
| B. Laptop sim ↔ cloud | **Short term:** Tailscale (free personal plan; Franz needs about 2 devices). The cloud MCS reaches the laptop's 8001/8002/8080 with **zero code change**. **Target:** a sim-initiated **outbound WSS "space-link agent"** to a cloud **ground-station gateway** that re-exposes TM/TC/state locally to the MCS. Model it on CCSDS **SLE** (bind/start, RAF online-timely vs online-complete, FCLTU). | frp (Apache-2.0, v0.71.1, Oct 2026) as a self-hosted reverse tunnel. Headscale (BSD-3) if Tailscale's SaaS coordination server is unacceptable. |
| C. Auth | **Keycloak** (Apache-2.0, 26.8.1, Oct 2026) as the identity broker. It brokers uOttawa Entra ID (OIDC; needs an IT admin-consent request), Danish institutions (SAML/WAYF/eduGAIN, longer-term), and local invite-only accounts. Put **Caddy `forward_auth` + oauth2-proxy** in front of the legacy SMO pages. Apps read identity headers and map them to a **server-side position roster** set by the instructor. | Authentik (MIT core; lighter than Keycloak, still needs Postgres and Redis). Pocket ID (passkeys only) if federation is dropped. |
| D. SpaceCDF instances | **Phase 1:** one hosted multi-tenant instance. "Join" means a study/session link. Add auth, owner columns and a single worker. **Phase 2 ("start my own"):** **JupyterHub + DockerSpawner + `jupyter-standaloneproxy`** (all BSD) gives auth, per-user containers, idle culling and proxying off the shelf. Local install plus Tailscale Funnel covers power users. | Sablier (AGPL-3.0) scale-to-zero behind Caddy/Traefik for per-team containers. Fly.io Machines (Toronto region) if you don't want to run a host. |
| D'. LLM keys | Keep BYO keys **in the browser only** (sessionStorage), send them per request over TLS, build a **per-request client** (fix the cache bug), and never log them. For a course-paid key, put **LiteLLM proxy** (MIT, 1.106.6) in front with per-user virtual keys and budgets. | Encrypted-at-rest per-user key storage only if background jobs need it. |
| E. Hosting | **OVHcloud Beauharnois (BHS, Québec)** VPS, about 4–8 vCPU / 8–24 GB for roughly €8–25/month with unmetered traffic. It is Canadian-resident and cheapest. **DigitalOcean TOR1** ($48/month for 4 vCPU/8 GB with 5 TB transfer) is the easiest managed alternative. Ask the **Alliance (Arbutus) RAS**, which is free to PIs, whether teaching use is allowed. | AWS ca-central-1 / Azure Canada Central only if uOttawa IT mandates them (3–5× cost). |
| F. Edge/ops | **Caddy** (v2.11.7) as the single TLS edge with one subdomain per UI. This fixes the root-relative-path problem and lets cross-service calls become same-site. Use Docker Compose profiles `ground` (cloud) and `space` (laptop). Backups with restic to Canadian object storage. Monitoring with Uptime Kuma plus LiveKit Prometheus. | Traefik if you move to many spawned containers (native Docker discovery). |

---

## A. Voice loops

### A.1 How real mission-control voice systems behave (the spec to emulate)

- **Loops and per-role rights.** Control teams talk over many named circuits ("loops"), each with a purpose and
  audience. Each user gets **listen and/or talk permission per loop by role**. The facility "voice switch" can be
  linked across sites to act as one network. Users monitor several loops for long periods, so keyset design drives
  stress. NASA MSFC's guidance warns of "a very real risk of overcomplication" in software keysets.
  [Scott, *Suggestions for Layout and Functional Behavior of Software-Based Voice Switch Keysets*, SpaceOps 2010](https://ntrs.nasa.gov/citations/20100021109)
- **Monitor many, talk on one.** In Shuttle MCC, each channel is set to monitor or talk. Many can be monitored, but
  **only one can be in talk mode at a time**. Each loop has its **own volume**. Users talk with **PTT** (hand unit or
  foot pedal) on a headset. Users store loop layouts as "pages" with the most-used loops on the primary page. Loop
  types include the **flight director loop**, **front-to-back loops** (front room to back rooms), **conference loops**
  and **air-to-ground**. Listening to a loop without announcing yourself lets controllers judge when someone is
  interruptible; loop tempo shows a disturbance spreading.
  ([Patterson, Watts-Perotti & Woods, "Voice loops as coordination aids in Space Shuttle Mission Control", CSCW 1996 / summary](https://ferd.ca/notes/paper-voice-loops-as-coordination-aids-in-space-shuttle-mission-control.html); [Watts et al. CSCW96 PDF](https://www.interruptions.net/literature/Watts-CSCW96-p48-watts.pdf))
- **UI conventions.** Each loop is a tile with state **Off / Monitor / Talk**, shown **blue for MONITOR and green for
  TALK**, with headphone and microphone icons for rights. Loops can be recorded and replayed on request, and finding
  the right utterance in a recording is a known pain point (an argument for event-indexed recordings).
  [Schiffner & Burr, *Role-based Multi-Chat System for Space Mission Control*, SpaceOps 2023](https://publications.spaceops.org/2023/download_by_id.php?id=0205)
- **ESA/ESOC.** ESOC's operational VCS is a commercial voice switch. SITTI's M800IP MULTIFONO serves 133
  positions, ~30 telephone gateways and ~60 VoIP links to ground stations, with fully duplicated components
  ([SITTI in Space, 2018](https://www.atc-network.com/atc-news/sitti/sitti-in-space)). SITTI also supplied a voice
  recording system ([VRS for ESOC](https://www.atc-network.com/atc-news/sitti/voice-recording-system-vrs-for-esoc)).
  ESA's 2017 tender asked for an off-the-shelf "multi-conference voice system" over IP
  ([ESOC OCC VCS ITT](https://rosa.ro/frame-contract-esoc-occ-voice-communication-system/)). ESTRACK stations got a
  new VCS under ground-station harmonisation ([SpaceOps 2023-0667](https://publications.spaceops.org/2023/0667)).
- **Browser-based precedent: DLR/GSOC openvocs.** WebRTC media (Opus/SRTP) with a TURN server and WebSocket
  signalling. Clients use only a browser and headset, with a keyboard, on-screen or optional hardware PTT. Loops are
  per role with **TALK / MONITOR / NONE**, multi-conference, RBAC per role, LDAP or local login, dual-server failover,
  a SIP gateway, scalable mixer microservices ("each user gets their own mix"), and a recorder in development as of
  2023 ([Schiffner et al., *Openvocs, a light-weight VCS for Space Mission Control*, SpaceOps 2023](https://publications.spaceops.org/2023/download_by_id.php?id=0204)).
  **Open-sourced July 2025** at `github.com/openvocs/openvocs` under **Apache-2.0**
  ([DLR news 2025-07-03](https://www.dlr.de/de/rb/aktuelles/nachrichten/2025/gsoc-veroeffentlicht-open-source-kommunikationsplattform-openvocs-fuer-kontrollraeume); [Interoperable Europe](https://interoperable-europe.ec.europa.eu/node/731260)).
  Mission debut 2023 with MORABA at Kiruna ([DLR openvocs-R](https://www.dlr.de/de/rb/forschung-betrieb/projekte/kontrollzentrumstechnologie/openvocs-r)).
  The FrOSCon 2025 talk calls it "a software library for building voice conferences for mission control rooms"
  ([FrOSCon 2025](https://programm.froscon.org/froscon2025/speaker/a9f0197c-1f3d-5262-b8bf-aa7cc8071087/)).

**Derived functional spec for SMO voice (v1):**

| Feature | v1 behaviour |
|---|---|
| Loops | Defined in config, next to `positions.yaml`. Suggested set: `FD`, `FLIGHT-OPS` (conference), `AOCS-BR`, `EPS-TCS-BR`, `OBDH-BR`, `GND/RF` (ground station/network), `A/G` (instructor plays the spacecraft or LEOP agency), `PLAN`, `SIM-SUP` (instructor-only private line), `DEBRIEF`. Labels come from i18n strings (EN/FR/DA); **loop IDs stay English**, consistent with callout policy (`docs/i18n/PLAN.md:13`). |
| Rights | Per position: `listen: [..]`, `talk: [..]`. The instructor can listen to all loops and talk on any. |
| States | Each loop tile is OFF / MON / TALK. At most **one TALK** loop. Each tile has a volume slider and a mute. A "talker" indicator shows who is speaking and on which loop. |
| PTT | Hold-to-talk (Space key, on-screen button, or USB foot pedal acting as a keyboard key). Optional **talk-latch** (toggle) off by default, with an instructor-only "hot mic" exception. An optional Quindar-style beep on key/unkey adds flavour and also marks the talk spurt in logs. |
| Private lines | Two-party call (for example FD↔instructor) as an ad-hoc loop. |
| Recording | Per loop, time-indexed to **UTC and sim time**. Talk spurts are logged to the MCS console log so the debrief can jump to "AOCS on FD loop at T+00:12:31". |
| Accessibility | Keyboard-operable tiles, ARIA live region for "X talking on FD", visible talker indicator (deaf/HoH users), and optional live captions as a later add-on. |

### A.2 Candidate media servers

Versions are from registries on 2026-10-28.

| Project | Licence | Latest / activity | Model | Fit for "monitor N, talk 1, PTT" | Recording | TURN | Ops burden |
|---|---|---|---|---|---|---|---|
| **LiveKit server** | Apache-2.0 | v1.13.11, 2026-10-25 (Go proxy); JS client `livekit-client` 2.23.0 (2026-10-16); Python `livekit` 1.2.0 (2026-10-27), `livekit-api` 1.2.2 | SFU (Go, Pion) | Very good. Selective subscription, participant **attributes**, server `updateSubscriptions`, `mutePublishedTrack`, `updateParticipant` permissions, data channels, JWT grants (`canPublish`, `canSubscribe`, `canPublishSources`, `hidden`) | Egress v1.15.0 (separate container: room composite `audio_only`, per-track, auto-egress). Alternatively a Python bot recorder | **Built-in TURN** (UDP 3478/443, TLS 443 on its own domain) | Low–medium. A `livekit/generate` tool emits docker-compose + Caddy + Redis + cloud-init. Ports 443, 80, 7881/tcp, 3478/udp, 50000-60000/udp. Host networking recommended |
| **openvocs** | Apache-2.0 | Released July 2025. Current activity **unverified** (GitHub unreachable) | Server-side mixing ("own mix per user"), WebRTC proxy, C&C service | **Native**: TALK/MONITOR/NONE per loop, role-based | Recorder planned in 2023; status unverified | Uses a TURN server | **Unknown**. Mission-grade origin; docs, packaging and community size unverified. Needs a hands-on spike |
| **Janus + AudioBridge** | GPL-3.0 | 1.4.1 (Alpine build 2026-04-21) | **MCU per room** (server mixes each loop) | Good. One AudioBridge room per loop; client opens one plugin handle per loop (one PeerConnection each); `muted`/unmute as PTT; talking events; `allow_rtp_participants` | **Per room**: `record`, `record_file`/`record_dir`; per-participant `mjrs` | External (coturn) | Medium–high. C server, JSON API, separate signalling code to write |
| **mediasoup** | ISC | 3.32.0 (npm, 2026-10-26) | SFU library (Node/Rust) | You build everything (signalling, rooms, auth) | DIY (plain RTP to ffmpeg/GStreamer) | External | High. A library, not a product |
| **Galène** | MIT | Active commits to 2026-10-23 (Go proxy pseudo-version) | SFU | Fair. Groups are meetings. No PTT concept; one group per connection | Recording to disk | **Built-in** | Low. Single Go binary. ~0.25 core per 100-student lecture ([galene.org](https://galene.org/)) |
| **Eyevinn Open Intercom** | MIT (frontend per ecosyste.ms; manager licence not confirmed) | frontend last push 2025-04-29 per ecosyste.ms (may be stale) | Productions → **lines**, on Symphony Media Bridge | **Closest broadcast-intercom model**: multiple lines, PTT, hotkeys, listen-only "audio feed" lines, saved multi-line presets, invite links, WHIP/WHEP | Via WHEP egress to a recorder | SMB | Medium. Needs SMB + CouchDB/MongoDB. Small community ([OSC wiki](https://github-wiki-see.page/m/EyevinnOSC/community/wiki/Service:-Intercom); [manager](https://esyshub.st101.workers.dev/Eyevinn/intercom-manager)) |
| **Mumble (+ mumble-web)** | BSD-3 | Mumble 1.4+ | Low-latency voice server (not WebRTC) | Native client is excellent: **channel listeners** (1.4) give monitor-without-joining, one-way, visible "ear" in the channel, ACL-restrictable; whisper/shout ([Mumble 1.4.230](https://www.mumble.info/blog/mumble-1.4.230/)) | Client-side recording | n/a | Browser path is weak: mumble-web needs websockify, WebRTC forks are community-maintained, and listener support in web clients is unverified. A desktop install is a barrier for remote students |
| **Jitsi Meet** | Apache-2.0 | active | SFU + full meeting app | Poor fit (meeting UX, one conference per tab) | Jibri (heavy, Chrome per recording) | coturn | High for this use |
| **Pion** | MIT | webrtc v4.2.26 (2026-10-28) | Go library | Building block (LiveKit uses it) | DIY | DIY | High |

### A.3 Mapping "loops" onto LiveKit

**Pattern 1: single room per team, loops as routing metadata (recommended).**

- Each operator connects once (one PeerConnection) and publishes **one mic track**, muted by default.
  **PTT = unmute/mute.** LiveKit's docs recommend muting over unpublishing because publishing requires renegotiation,
  and muted tracks send no bytes ([tracks](https://docs.livekit.io/intro/basics/rooms-participants-tracks/tracks.md)).
- The **current talk loop** is a participant attribute, `talk_loop=FD`. Attributes are server-stored, synced to late
  joiners, and settable by the client (`canUpdateOwnMetadata`) or the server (`UpdateParticipant`). They are **not**
  meant for updates more often than every few seconds, which is fine for loop changes but not for PTT
  ([participant attributes](https://docs.livekit.io/transport/data/state/participant-attributes.md)).
- **Monitoring**: `autoSubscribe:false`. A client subscribes to the mic track of every participant whose `talk_loop` is
  in its monitored set. Each remote track goes through a WebAudio `GainNode` for that loop's volume, plus a per-loop
  pan/tone option so loops are separable by ear.
- **Enforcement**: a small **loop-controller** (Python, `livekit-api`) mints JWTs (`canPublishSources:["microphone"]`,
  `canPublishData`, `canUpdateOwnMetadata:false`). It sets `talk_loop` itself via `updateParticipant` after checking
  `positions.yaml` rights, and can force subscriptions with `updateSubscriptions(room, identity, trackSids, bool)` or
  server-mute with `mutePublishedTrack` (instructor "cut mic")
  ([RoomServiceClient source](https://cdn.jsdelivr.net/npm/livekit-server-sdk@2.15.3/src/RoomServiceClient.ts)).
  For a classroom, client-side subscription filtering plus server-set `talk_loop` is enough. Hard enforcement means
  the controller drives every subscription.
- Pros: one connection per user, instant loop switching, trivial mixing in the browser, and the SFU forwards only
  active talkers (with PTT, bandwidth ≈ talkers × listeners × ~40 kbps).
  Cons: "loop" semantics live in our code, not the server.

**Pattern 2: one LiveKit room per loop.** The client keeps N `Room` objects (N PeerConnections). Token grants give
server-enforced talk rights per loop. This is cleaner semantically but costs N× ICE/DTLS connections and TURN
allocations per student. Whether the JS SDK officially supports several simultaneous `Room` instances in one page
was **not verified**, so test it.

**SFU vs MCU for many monitored loops on student laptops.** With PTT, only a few tracks carry packets at once. Opus
decode of even 10–20 tracks is trivial for any laptop or Chromebook, so **SFU is fine**. An MCU (Janus AudioBridge,
openvocs mixers) wins when monitored loops × simultaneous talkers gets large, or on very weak clients. It also gives
the recorder a ready-mixed per-loop stream. The cost is server CPU (decode + mix + encode per loop and per listener
mix).

**TURN / campus networks.** University and eduroam networks commonly restrict UDP. Plan for **TURN over TLS on 443**.
LiveKit has an embedded TURN that needs its own domain/cert (for example `turn.example.ca`), and the generated Caddy
config handles TLS ([LiveKit VM deploy](https://docs.livekit.io/transport/self-hosting/vm.md); [deployment](https://docs.livekit.io/transport/self-hosting/deployment.md)).
Tailscale's docs show the same pattern (relay over 443 when UDP is blocked) ([firewall ports](https://tailscale.com/docs/reference/faq/firewall-ports.md)).
Self-signed certs do not work for LiveKit.

**Latency.** Ottawa↔Copenhagen RTT is typically ~90–110 ms (general knowledge, not measured here). One-way
mouth-to-ear through a Canadian SFU should land around 100–200 ms including the jitter buffer, within the usual
≤150–200 ms conversational target (ITU-T G.114). If Danish teams run their own sessions, a second LiveKit node in the
EU (multi-region needs Redis) is possible later.

**Recording for debrief.** Two routes:

1. **LiveKit Egress.** Auto-egress per track, or room composite `audio_only`. It is a separate heavy container
   (GStreamer/Chrome) ([egress](https://docs.livekit.io/transport/media/ingress-egress/egress.md)).
2. **Recommended: a Python recorder bot** using `livekit` (rtc). It joins hidden, subscribes to all mic tracks, writes
   **per-loop Opus/OGG** files segmented by talk spurt, and stamps each segment with UTC **and sim time**. Sim time
   comes from the MCS `sim_now()` (already re-anchored from the sim, `WEB_CURRENT_STATE.md` §4). Each spurt is also
   posted to the MCS console log (`kind: voice`), so the existing debrief/report tooling can index audio by event.
   This is lighter than Egress and aligns with sim time natively.

### A.4 Other "intercom / voice loop" projects found

- Eyevinn Open Intercom (above) is the best-maintained open broadcast intercom found. Its line/production model and
  "audio feed" listen-only lines map well, but it ties you to Symphony Media Bridge.
  [Eyevinn blog](https://eyevinntechnology.medium.com/the-future-of-broadcast-communication-open-source-intercom-solution-6e06ce0fddf1)
- `mint-dewit/openintercom` (TV broadcast, [repo](https://github.com/mint-dewit/openintercom)), `zemendaniel/intercom`,
  `matiaspl/intercom` and `Merve40/ptt` are small hobby projects; activity unverified.
- Quindar tones are just the Apollo in-band key/unkey tones ([Wikipedia](https://en.wikipedia.org/wiki/Quindar_tones)).
  They are worth adding as an optional sound effect. No open-source "spacecraft voice loop" project other than
  openvocs was found.

**Decision rule.** Spend one day trying openvocs (docker? docs? auth? recorder?). If it runs and its JS client can be
embedded or linked from the MCS, adopt it for authenticity. Otherwise build the LiveKit pattern-1 client, about
600–1000 LOC of JS plus a ~300 LOC Python controller/recorder, with the loop keyset as a panel inside the MCS shell.

---

## B. Connecting a laptop simulator to the cloud ground segment

Recall from the code survey: the cloud MCS needs **TM 8002, TC 8001, HTTP `/api/state` 8080**, the instructor lives in
the sim on 8080 (HTTP+WS), and rfsim needs sim WS. Every link is **ground → sim** today.

### B.1 Overlay / tunnel options (no code change)

| Option | Licence / cost | How it works for SMO | Pros | Cons |
|---|---|---|---|---|
| **Tailscale** (client v1.104.4, 2026-10-27) | Proprietary coordination + BSD clients. **Personal plan free up to 6 users**; 50% off for educational institutions ([plans](https://tailscale.com/docs/account/manage-plans/free-plans-discounts.md)) | Laptop and cloud VM join one tailnet. Cloud MCS uses `--connect laptop.tailnet:8002`, `SMO_SIM_STATE_URL=http://laptop.tailnet:8080/api/state`, and Caddy proxies the instructor page to `laptop.tailnet:8080` | Zero code change. NAT traversal, falls back to DERP relays over 443 when UDP is blocked ([connection types](https://Tailscale.com/kb/1257/connection-types)). ACLs. WireGuard crypto | Third-party SaaS control plane (metadata only). Relay adds latency if UDP is blocked. Some campus networks block it. Not pedagogical |
| **Headscale** (v0.29.6, 2026-10-24) | BSD-3 | Self-hosted Tailscale control server, single tailnet | Fully self-hosted | Pre-1.0. Maintainers don't encourage running it behind reverse proxies or in containers ([pkg.go.dev](https://pkg.go.dev/github.com/juanfont/headscale@v0.29.2)). One more service to run |
| **Plain WireGuard** | GPL/MIT | Laptop dials the cloud VM (persistent keepalive) | Simple, fast | UDP only, so it fails on UDP-blocking Wi-Fi without extra tooling (for example ProxyGuard, [FOSDEM 2025](https://ftp.fau.de/fosdem/2025/ua2114/fosdem-2025-4629-proxyguard-wireguard-behind-a-reverse-proxy.vtt)) |
| **frp** (v0.71.1, 2026-10-14) | Apache-2.0 | `frpc` on the laptop dials `frps` on the VM and publishes 8001/8002/8080 as VM-local ports (`tcp` proxies), optionally over websocket/TLS on 443 | Self-hosted, one binary each side, TLS default since v0.50, token/OIDC auth, very active (~100k stars) ([comparison](https://dev.to/instatunnel/rathole-vs-frp-vs-ngrok-what-the-benchmarks-actually-show-244o)) | Must lock down `allowPorts`. Still raw unauthenticated PUS on the VM side (bind to 127.0.0.1) |
| **rathole** | Apache-2.0 | As frp | Lean, fast | Last release v0.5.0, Oct 2023, effectively unmaintained ([same source](https://dev.to/instatunnel/rathole-vs-frp-vs-ngrok-what-the-benchmarks-actually-show-244o)) |
| **Cloudflare Tunnel** | Free tier | `cloudflared` outbound. HTTP/WS fine. Raw TCP needs `cloudflared access tcp` on the *client* (the cloud MCS) too | Outbound-only, free ([guide](https://ddingpy.github.io/mynote/posts/cloudflared-comprehensive-guide/)) | Traffic through a US provider's global edge (residency). Awkward for raw TCP |
| **ngrok** | Free tier requires a card for TCP. Hobbyist $8–10/month, 1 TCP address ([pricing](https://ngrok.com/pricing.md)) | TCP endpoints | Easy | Paid, US-hosted, 1 GB free transfer, endpoints limited |
| **SSH -R (autossh)** | free | `ssh -R 127.0.0.1:18002:localhost:8002 …` per port | Nothing new to install | Fragile reconnection, port-22 egress is often blocked on campus, manual |

### B.2 Redesign: sim-initiated "space-link" connection (recommended target)

**Shape.**

```
laptop (space segment)                          cloud (ground segment)
┌──────────────┐  outbound WSS :443, token     ┌──────────────────────────────┐
│ smo-simulator│◄─► space-link agent ──────────►│ ground-station gateway (GSG) │
│ 8001/8002/   │   (in-process or sidecar)      │  ├ TM fan-out → local :8002   │──► MCS, rfsim
│ 8080 local   │   channels: TM, TC, STATE,     │  ├ TC in      ← local :8001   │
└──────────────┘   INSTR, DUMP, VR              │  ├ /api/state (cached, pushed)│──► MCS, planner
                                                │  └ /instructor proxy (WS)     │──► browser via Caddy
                                                └──────────────────────────────┘
```

- **Transport.** WebSocket over TLS on 443 (aiohttp is already in the stack). It passes campus proxies and firewalls
  and Caddy terminates it. QUIC/WebTransport adds nothing at TM rates (kB/s), and TCP head-of-line blocking is
  irrelevant here.
- **Framing.** Binary WS frames: `[u8 channel][u32 seq][payload]`. TM/TC payloads are the existing PUS packets. STATE is
  the `/api/state` JSON **pushed** at 1 Hz instead of polled. This removes MCS L3 and planner L4 WAN polling, and with
  it the planner's blocking-urllib stall. Have the GSG stamp `sim_time` with the agent's send wall time to remove
  latency bias.
- **The MCS stays unchanged.** The GSG re-exposes 8001/8002/8080-equivalents on **127.0.0.1 inside the cloud host**. It
  is the one "relay near the sim" that `WEB_CURRENT_STATE.md` §4 called for, it fixes the broken `smo-gateway` TC
  path, and it is spacecraft-agnostic (the MCS can't tell a GSG from a real station).
- **Reconnection.** Exponential backoff. The sim-side agent buffers TM with sequence numbers during outages. The GSG
  reports `LINK: UP/DOWN/DEGRADED` to the MCS, either as a ground-station status packet or an MCS banner.
- **Security.** Per-session sim token (JWT minted by the GSG/instructor, bound to `team_id`). TLS only. The GSG
  accepts **one** sim per team session. TCs are accepted only from the local MCS socket; the MCS already does position
  checks once auth exists. Optional mTLS later.
- **Instructor console.** Split it out, or proxy it through the INSTR channel to the cloud. The read-write
  `/config` editor should stay **laptop-local only**, because `configs/` must be byte-identical on both sides.
  Distribute config via git or a hash check at link bind: the agent sends a SHA-256 of `configs/eosat1/` and the GSG
  refuses to bind on mismatch, which avoids silent HK mis-decoding.
- **Dumps (S15).** A DUMP channel streams new `dump_sid*.bin` files to the GSG's dump dir.

**SLE as the pedagogical model.** CCSDS SLE gives the vocabulary: **user/provider**, **BIND/START/STOP/UNBIND**,
**RAF** (return all frames), **RCF** (return channel frames), **FCLTU** (forward CLTU). RAF delivery modes are
**online-timely** (drop on backlog), **online-complete** (buffer, never drop) and **offline** (replay), which map
exactly to the reconnection/buffering choice above. Students can then see a "ground station network" layer the way
ESOC/ESTRACK operators do. Open implementations:

| Implementation | Side | Services | Licence | Status |
|---|---|---|---|---|
| **python `sle` (LibreCube)** | User API (they say it can build both) | RAF, RCF, CLTU | MIT | 0.3.0, 2025-07-17 ([PyPI](https://pypi.org/project/sle); [GitLab librecube/lib/python-sle](https://pypi.org/project/sle)) |
| **yamcs/jsle** | User **and provider**, plus an **SLE↔UDP bridge "intended as a front end for a simulator"** | FCLTU, RAF, RCF | not confirmed (Yamcs ecosystem is mostly AGPL/Apache) | last push ~1 yr ago ([README](https://github.com/yamcs/jsle/blob/master/README.md); [ecosyste.ms](https://repos.ecosyste.ms/hosts/GitHub/repositories/yamcs%2Fjsle)) |
| **dariol83/ccsds** | SLE user/provider + TM/TC frames, CLTU etc. (Java) | RAF, RCF, ROCF, CLTU (from memory, not verified) | Apache-2.0 | ~1 yr since push, 107 stars ([ecosyste.ms](https://repos.ecosyste.ms/hosts/GitHub/repositories/dariol83%2Fccsds)) |
| **esa/sleapi-j** | ESA SLE Java API | full | "other" licence | pushed 2025-02-13 ([ecosyste.ms](https://awesome.ecosyste.ms/projects/github.com%2Fesa%2Fsleapi-j)) |
| oswald2/esa-sle (Haskell), ocaml-sle | various | | | [esa-sle](https://github.com/oswald2/esa-sle), [ocaml-sle](https://tangled.org/gazagnaire.org/ocaml-sle) |

**Recommendation.** Implement **"SLE-lite" over WSS** first: the same states and delivery modes, JSON control
messages and binary data. The real SLE protocol is ISP1 over TCP with ASN.1 encoding, credentials and a
heartbeat. It needs inbound ports at the provider, which is the opposite of the NAT constraint, and it is heavy for
a single maintainer. Keep an optional path for an advanced lab where the rfsim (CLTU/TF capable) is fronted by jsle's
provider. Treat the space-link agent's API as "station-side SLE provider", so a later real-SLE swap is local.

**Phasing.** (1) Tailscale this term to unblock remote use, (2) build the GSG + agent, (3) retire `smo-gateway`.

---

## C. Authentication, roles and multi-team

### C.1 Identity provider

| IdP | Licence / latest | Footprint | Protocols | Notes |
|---|---|---|---|---|
| **Keycloak** | Apache-2.0, **26.8.1 (Oct 2026)** ([blog archive](https://www.keycloak.org/blog-archive)) | Heaviest: JVM/Quarkus, Postgres recommended. Plan for ~1 GB RAM | OIDC + **full SAML 2.0 as IdP and broker** ([comparison, Oct 2026](https://skycloak.io/blog/open-source-authentication-comparison-2026/)) | Best for **brokering several institutions** (Entra OIDC + SAML federations + local accounts), groups → roles, invite flows, FR/EN/DA login themes built in |
| **authentik** | MIT core (enterprise dir separate). Active (Go proxy 2026-10-28) | Python/Django + Go outposts, Postgres + Redis | OIDC, SAML IdP, LDAP, proxy outpost | Nicer admin UI. Built-in forward-auth proxy |
| **Zitadel** | **AGPL-3.0 since v3 (Mar 2025)** | Go + Postgres | OIDC, SAML | Event-sourced, harder to debug |
| **Authelia** | Apache-2.0, v4.39.28 | Tens of MB | OIDC provider, **no SAML** | Forward-auth gatekeeper. Weak for brokering |
| **Pocket ID** | active | tiny | OIDC, passkeys only | Simplest. No federation |
| **oauth2-proxy** | v7.15.5 (2026-10-01) | tiny | OIDC client | Gatekeeper in front of apps without auth, via Caddy `forward_auth` ([Caddy community template](https://caddy.community/t/oauth2-authentication-template-with-group-checks-using-oauth2-proxy-and-self-hosted-oidc/31611)) |

### C.2 Institutional SSO

- **uOttawa Microsoft Entra ID.** An external app registered as **multi-tenant** ("accounts in any organizational
  directory", `/organizations` endpoint) can sign in uOttawa users with only `openid profile email` (User.Read). If
  the tenant has **disabled user consent**, which is common at universities, an **admin must consent once**
  (`prompt=consent`) ([Microsoft Learn](https://learn.microsoft.com/en-us/entra/identity-platform/howto-convert-app-to-be-multi-tenant)).
  So it is feasible, but it needs a ticket to uOttawa IT. Other universities run formal "SSO/Entra integration
  request" processes (for example [UConn](https://uconn.atlassian.net/wiki/spaces/IKB/pages/28612362243/Microsoft+Entra+and+University+Single+Sign-On+SSO), [OSU](https://services.okstate.edu/TDClient/840/Portal/Requests/ServiceOffering/596/Request-Application-Integration-with-Entra-ID)).
  uOttawa's specific process **was not found publicly**. Register it in Keycloak as an OIDC identity provider and
  restrict it to the uOttawa `tid`.
- **Multi-institution (Canada + Denmark).** The proper long-term route is the **Canadian Access Federation (CAF)**
  (CANARIE) → **eduGAIN**, which Danish **WAYF** also feeds. CAF SPs can ask CANARIE to promote them to eduGAIN
  ([CAF FAQ](https://www.canarie.ca/identity/caf/faq/); [eduGAIN](https://canarie.ca/identity/fim/edugain)). This
  requires uOttawa to sponsor or register the SP. The participation criteria were not verified. Keycloak can be the
  SAML SP in that federation.
- **Pragmatic v1.** Keycloak with (a) uOttawa Entra if IT approves, (b) **instructor-issued invite links and local
  accounts** with email OTP or passkeys for Danish partners and guests, and (c) optional GitHub/Google for TAs. Keep
  personal data minimal: display name, institution, email.

### C.3 Roles → command authority

- Realm roles: `instructor`, `operator`, `observer`, `admin`. **Positions are not IdP roles.** They are **per-session
  assignments**: an instructor roster maps `user → team → position(s)`, editable live (handover). That mirrors real
  console logins.
- Caddy `forward_auth` → oauth2-proxy (or the apps validate the Keycloak JWT directly) and injects `X-User`,
  `X-Groups`. The MCS **ignores the self-declared `position`** in bodies and query strings and looks it up from the
  roster. This fixes `server.py:959, 986-989` (unknown position → allowed) and the unchecked S11/tm-dump/procedure
  paths.
- Exclusive positions with a lock and handover (one FD at a time; others may "monitor" read-only). The instructor
  gets the ground-time and sim controls. The voice-loop controller reads the same roster, so **one source of
  truth** covers both TC authority and voice talk rights.

### C.4 Multiple concurrent teams

- **One ground-segment stack per team** (compose project `team-a`, `team-b`: MCS + planner + GSG endpoint + LiveKit
  room `team-a`), each at its own subdomain (`a.ops.example.ca`). Each team's sim is a laptop, or a **cloud-hosted
  sim container** for teams without a capable laptop (same image, `space` profile, on the server). Per team, MCS +
  planner + sim ≈ 0.5–1 vCPU / 1–1.5 GB (estimate; measure).
- The current MCS/planner have global singletons (one procedure runner, one clock), so per-team process isolation is
  far cheaper than making them multi-tenant.

---

## D. SpaceCDF: "join a running instance" or "start your own"

### D.1 Patterns

| Pattern | Tooling (verified versions) | Pros | Cons | Fit |
|---|---|---|---|---|
| **Single multi-tenant deployment with workspaces** | FastAPI + Postgres + Keycloak | One thing to run. "Join" = study/session URL. Cheapest | Needs owner/tenant columns. Must stay **one worker** (in-memory rooms/caches, survey §5.4) or be rewritten onto Redis pub/sub | **Phase 1** |
| **Per-user/per-team container via JupyterHub** | JupyterHub 6.1.1 (2026-10-20), DockerSpawner 14.0.0, `jupyter-server-proxy[standalone]` 4.6.0 (runs **any** web app per user, [docs](https://jupyter-server-proxy.readthedocs.io/en/latest/standalone.html)), OAuthenticator 17.4.0 (Keycloak/Entra). All BSD-3 | Mature spawner, auth, routing, **idle culler**, named servers (one per team), persistent volumes, admin UI. Spawn form for "which version/config". Collaborators can be granted access to a named server | URLs live under `/user/<name>/`, so SpaceCDF must tolerate a path prefix (the frontend uses absolute `/api` and `/ws` and the `:8000` WS rewrite — fixable with a base-path setting) | **Phase 2, recommended** |
| **Sablier scale-to-zero** | Sablier v1.19.1 (2026-10-28), **AGPL-3.0**. Caddy/Traefik/nginx plugins. Docker/K8s/Podman/systemd providers ([pkg.go.dev](https://pkg.go.dev/github.com/sablierapp/sablier)) | Wakes a stopped container on first request with a waiting page, stops it after inactivity. Pre-declared per-team containers | You pre-create the containers (no self-service "new"). Auth handled separately | Good for a fixed set of team instances |
| **Coder** | v2.38.4 (2026-10-28), AGPL | Workspaces with templates and auto-stop | Built for developer IDE workspaces. Heavy for this | Overkill |
| **Kubernetes + operator** | — | Scales | Too much ops for one maintainer | No |
| **Fly.io Machines** | Memory now $6/GB-month. shared-cpu-1x 256 MB ≈ $2.19/month. Stopped-machine rootfs $0.15/GB-month. Volumes $0.15/GB. NA/EU egress $0.02/GB. **Toronto region exists** ([pricing update](https://fly.io/pricing-update/)) | Per-second, auto-stop/auto-start, API to spawn per user | US company (CLOUD Act). Another platform to learn | Fallback if no own host |
| **Railway/Render** | — | Easy | US-hosted. Not per-user spawning friendly | No |
| **Local install + share** | docker compose / installer + **Tailscale Funnel** (public HTTPS to a tailnet device), or connect the local instance outbound to a cloud relay (same agent idea as B.2) | Free, student-owned data | Host laptop must stay awake. Support burden | Power users / offline |

**Cost per student (estimate).** A SpaceCDF container idles at maybe ~150–300 MB RAM (FastAPI + caches; **not
measured**). With culling, 30 concurrent users ≈ 6–9 GB RAM, which fits a 16–24 GB VPS alongside SMO. Marginal cost
per student is about C$0.3–1/month on OVH-class pricing.

### D.2 BYO LLM key handling

1. **Fix first**: the process-wide client is replaced by a per-request key (survey §5.3). Construct a client **per
   request** when `X-API-Key` is present and never cache it.
2. **BYO mode**: the key lives in the browser (sessionStorage by default; localStorage opt-in "remember on this
   device"), is sent per request over TLS, and is **redacted** from logs, errors and OpenAPI examples. It is never
   persisted server-side. Set a CSP that forbids third-party scripts, since XSS is the main exfiltration path.
3. **Course-key mode**: run **LiteLLM proxy** (MIT, 1.106.6, 2026-10-28) between SpaceCDF and the provider. Issue
   **per-student virtual keys with budgets/RPM** that map to one real course key. The real key never leaves the
   server, and usage is per user.
4. Optional: encrypt stored keys with a server-held key (Fernet) only if background/async jobs need them.

---

## E. Hosting (Canadian residency)

### E.1 Privacy constraints

- **Ontario FIPPA** applies to universities. No explicit data-residency clause was found. The City of Toronto's
  analysis of the sister act MFIPPA states "MFIPPA does not specify requirements for data residency" and treats
  Canadian storage as policy, driven by "reasonable measures" security duties
  ([Toronto guideline](https://www.toronto.ca/wp-content/uploads/2023/08/966e-Data-Residency-for-Cloud-Technology-Guidelinev1.0.pdf)).
  By contrast, BC's FIPPA had a strict residency rule, relaxed in 2021
  ([UBC](https://privacymatters.ubc.ca/resources/bill22)). The IPC recommends a **PIA/TRA**, knowing the provider,
  and enforceable contracts for cloud services ([IPC slides](https://www.ipc.on.ca/en/media/2674/download)).
- **uOttawa AIPO** conducts **Privacy Impact Assessments** for new initiatives. Contact: AIPO (ext. 1851) / CPO
  ([AIPO](https://www.uottawa.ca/about-us/administration-services/aipo)). No public uOttawa guidance on third-party
  cloud tools was found; it may be behind VirtuO login. **Action: ask AIPO whether a PIA is needed** (voice
  recordings of students are personal information).
- **Danish partners (GDPR).** Hosting in Canada for Danish students' data needs a lawful transfer basis. The EU
  adequacy decision for Canada covers PIPEDA-scope commercial organisations, and its applicability to a university
  under provincial law is **not verified**. Minimise: invite accounts, display names, no voice recording of Danish
  students without consent, retention limits.
- **Implication.** Prefer a **Canadian-located, ideally non-US-parent** provider, minimise personal data, make
  recordings opt-in with a short retention period, and document it.

### E.2 Providers (prices as found; check before ordering)

| Provider / region | Example size | Price | Traffic | Notes |
|---|---|---|---|---|
| **OVHcloud, Beauharnois QC (BHS)** | VPS-2 4 vCore/8 GB/75 GB; VPS-3 6/12; VPS-4 8/24 | €8.48 / €12.24 / €23.48 per month ([vpsbenchmarks](https://www.vpsbenchmarks.com/hosters/ovhcloud)) | Unmetered (OVH VPS norm) | Canada DC confirmed. French parent. **Canadian-location pricing and plan availability not verified** (prices are EU listings, and a 2026/2027 range refresh is in progress) |
| **DigitalOcean TOR1** | s-4vcpu-8gb | $48/month; CPU-opt c-4 $84 ([onedollarvps](https://onedollarvps.com/pricing/digitalocean-pricing); [cloud-mercato](https://pcr.cloud-mercato.com/providers/digitalocean/flavors/s-4vcpu-8gb)) | 5 TB pooled, then $0.01/GB | TOR1 has Droplets, Spaces, managed Postgres, DOKS ([availability](https://docs.digitalocean.com/platform/regional-availability)). US parent |
| **AWS ca-central-1** (also ca-west-1) | t3.xlarge 4/16 | $0.1856/h ≈ $135/month ([doit](https://www.doit.com/compute/spot/ca-central-1/t3.xlarge)) | Egress ~ $0.09/GB (general knowledge) | Lightsail Canada exists (prices not retrieved) |
| **Azure Canada Central/East** | B4ms / D4s_v5 | not retrieved (D2_v4 $78/month for scale) ([azurespeed](https://www.azurespeed.com/AzureVmPricing/Regions/canadacentral)) | metered | Relevant only if uOttawa IT provides a subscription |
| **GCP Montréal / Toronto** | — | not researched in depth | — | — |
| **Hetzner** | — | — | — | **No Canadian location** (DE, FI, US-Ashburn, US-Hillsboro, SG) ([docs](https://docs.hetzner.com/cloud/general/locations/)) |
| **Alliance (Arbutus) cloud, RAS** | "modest" quota, up to 3 VMs per basic account | **Free to PIs** (faculty) ([UVic summary](https://uvic.ca/systems/researchcomputing/about-us/digital-research-alliance-of-canada/index.php)) | — | Exact RAS limits and **whether teaching/public web services are allowed: not verified** (docs page blocked). Worth one email. Students would be "sponsored users" |

### E.3 Sizing for ~30 concurrent students with voice (estimate)

- **Voice**: Opus ≈ 32 kbps payload, ~40–50 kbps on the wire. With PTT, ~2–3 simultaneous talkers × 30 listeners ≈
  3–5 Mbps peak, and an SFU uses negligible CPU at this size. TURN/TLS relaying (if many are UDP-blocked) roughly
  doubles bandwidth through the VM.
- **MCS WS**: full `state` JSON at 1 Hz per client plus per-packet TM messages. At an assumed 20–50 KB/s per client,
  that is 5–12 Mbps for 30 clients. **This is likely the bigger bandwidth item.** Measure it; diff/compress the state
  push if needed.
- **Total**: ~10–20 Mbps peak, ≈ 5–9 GB per 3-hour lab, ≈ 150–400 GB/term. That is free on OVH/DO and ~$15–35 per
  term on AWS.
- **VM**: 4 vCPU / 8 GB covers 1–2 team stacks + LiveKit + Caddy + Keycloak (~1 GB) + Postgres. **8 vCPU / 16–24 GB**
  covers 4–6 teams, cloud-hosted sims for some teams, and SpaceCDF containers.
- **Monthly**: OVH VPS-3/VPS-4 ≈ C$20–40. DO 4/8 ≈ C$66, or 8/16 ≈ C$130. Add object storage for backups and
  recordings ≈ C$5. **Rough all-in: C$25–45/month (OVH) or C$70–140 (DO).**

---

## F. Edge, containers, operations

- **Reverse proxy: Caddy** (v2.11.7, 2026-10-03). It gives automatic HTTPS by default and a short Caddyfile, and
  proxies WebSockets transparently. `forward_auth` integrates oauth2-proxy/authentik. Traefik (v3.7.16) is better
  when containers come and go (native Docker label discovery). nginx needs certbot and more config
  ([Dokploy comparison](https://dokploy.com/blog/caddy-vs-traefik-vs-nginx)). Caddy is the right choice for a
  single-maintainer, single-VM setup. Use `caddy-docker-proxy` or Sablier's Caddy plugin later if dynamic routing
  is needed. **Note:** LiveKit's generator ships its own Caddy config. It is believed to use Caddy's layer4 module to
  share 443 between HTTPS and TURN/TLS by SNI (**not verified**), so merge it into the single Caddy or give LiveKit's
  TURN a separate IP/port.
- **Subdomain per UI** (`mcs.a.ops…`, `plan.a.ops…`, `instr.a.ops…`, `radio.a.ops…`, `voice.ops…`, `cdf…`, `id…`). SMO
  pages use root-relative paths and can't live under `/mcs/` prefixes (survey §3.1). The L7/L8 cross-service browser
  calls then need either CORS headers for the sibling subdomains, or better, an `/x/planner/...` same-origin proxy
  route in Caddy on the MCS host.
- **Hardening that must ship with the cloud move:** bind 8001/8002/8011/8012/5555 to 127.0.0.1 or the internal
  network only; add a WS Origin check; make `/api/ground-time` instructor-only; never expose `/config` from the
  cloud; fix the `startswith` path checks; disable SpaceCDF `/docs` in production; Postgres/Redis not published.
- **Containerising SMO: compose profiles**
  - `space` (laptop): `smo-simulator` + space-link agent (+ optional rfsim, VR bridge, config editor). It makes only
    outbound connections.
  - `ground` (cloud, per team via `-p team-a`): `smo-mcs`, `smo-planner`, GSG, instructor proxy, delayed-TM viewer,
    orbit/doc tools.
  - `platform` (cloud, once): Caddy, Keycloak + Postgres, oauth2-proxy, LiveKit (host network), loop-controller +
    recorder, SpaceCDF (or JupyterHub), Uptime Kuma.
  - Use one image for all SMO Python packages with different entrypoints. Bake `configs/eosat1/` into the image tag,
    which guarantees the sim/ground config hash match.
- **Observability**: Caddy JSON access logs; `docker compose logs` → Loki optional; LiveKit Prometheus (:6789);
  **Uptime Kuma** (active, 2026-10-28) for HTTP/WS probes plus a "sim link up" push monitor from the GSG. Grafana
  only if needed.
- **Backups**: **restic** (v0.19.1, 2026-07-05) nightly for Postgres dumps, MCS SQLite archive, SpaceCDF data and
  voice recordings → OVH Object Storage BHS or DO Spaces TOR1 (Canadian). Test a restore each term.
- **Updates**: pin image tags; Renovate or a manual monthly bump; unattended-upgrades on the VM.

---

## G. What could not be verified

- **GitHub was unreachable** from this session (proxy policy), so README-level claims for openvocs (docs, Docker
  support, recorder status, activity since July 2025), Eyevinn intercom-manager's licence, mumble-web's maintenance,
  jsle's licence and dariol83/ccsds's SLE provider support are unconfirmed.
- **openvocs**: everything beyond "Apache-2.0, released July 2025, browser/WebRTC, TALK/MONITOR/NONE, RBAC" (from
  SpaceOps 2023 and DLR/EU pages). openvocs.org was blocked.
- **LiveKit**: whether multiple simultaneous `Room` instances in one browser page are supported; whether the
  generator's Caddy uses layer4 SNI multiplexing; egress CPU requirements (not in docs).
- **uOttawa**: a public SSO/Entra app-integration process; whether user consent is disabled in the uOttawa tenant;
  internal cloud/privacy guidance for instructors (likely VirtuO-gated).
- **FIPPA (Ontario provincial) residency**: inferred from MFIPPA analysis and the absence of a clause, not from an IPC
  ruling. GDPR transfer basis for a Canadian university: unverified, needs uOttawa/partner privacy offices.
- **CAF/eduGAIN**: SP participation criteria and cost.
- **Alliance Arbutus RAS**: quotas and whether teaching/public-facing services are permitted.
- **Prices**: OVH Canadian-location prices (EU listings used), Azure/GCP/Lightsail Canadian prices; AWS egress from
  memory.
- **Measurements**: SMO MCS WS bandwidth per client, SpaceCDF idle RAM, and real Ottawa/Copenhagen voice latency are
  estimates and should be measured in a pilot.

## H. Suggested next steps (ordered)

1. **This week**: a 1-day openvocs spike (deploy, test loops/PTT in Chrome and Firefox from eduroam). In parallel, a
   LiveKit `generate` deploy on a test VM with a 100-line keyset prototype (2 loops, PTT, per-loop volume).
2. Email **uOttawa IT** (Entra multi-tenant app admin consent), **AIPO** (PIA scope for voice recordings and the
   Danish partners), and the **Alliance** (RAS for teaching).
3. Stand up `platform` on an OVH BHS (or DO TOR1) VM with Caddy + Keycloak + LiveKit, and put the current SMO behind
   oauth2-proxy with **Tailscale to the laptop** as the interim link.
4. Implement the roster-based position authority in the MCS (removes self-declared positions).
5. Build the GSG + space-link agent ("SLE-lite"), then compose profiles `space`/`ground`/`platform`.
6. SpaceCDF: fix the key-leak bug and the `:8000` WS rewrite, serve `dist`, add auth/owners (phase 1). Then pilot
   JupyterHub + standalone-proxy for "start my own".
