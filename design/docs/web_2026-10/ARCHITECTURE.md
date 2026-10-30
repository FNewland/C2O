# Running SMO and SpaceCDF on the web: architecture (rev 2)

*Design of record, rev 2 (2026-10-28, 21:00). Author: Claude for Franz Newland. Status: **proposed**. The decisions are in §12.*
*Rev 2 adds Franz's requirements of 20:43:*
- *Google Cloud Toronto*
- *simulator on a cloud server*
- *a link to a real ground station*
- *at least two-factor login*
- *a public web page rather than the university network*
- *a practice (gamified) mode*
- *the full design-to-ops lifecycle vision*

*Evidence: `WEB_CURRENT_STATE.md` (code survey with file and line references) and `WEB_OPTIONS_RESEARCH.md` (options and sources), both in this folder.*

## 1. What we are building

1. **SMO as a website.** The MCS, planner and wall display, instructor console, RF pages and tools are reachable from any browser at a public address behind strong login. They do not run on the university network.
2. **The spacecraft side runs wherever it suits:**
   - **a simulator on a cloud server**, the default;
   - a simulator on Franz's laptop;
   - **later, a real ground station** through the RF chain;
   - eventually, hardware-in-the-loop with a flatsat.
3. **Two operating modes:**
   - **Class mode:** an instructor-controlled simulator with a full team.
   - **Practice mode (gamified):** one person or a small group practises alone. Missing roles are filled by automated crew members, and failures are injected to suit the roles present once the operator declares ready.
4. **Voice loops**, mission-control style, in the browser.
5. **SpaceCDF:** join a running instance or start your own.
6. **The long-term vision (§10):** a full **design → develop → test → fly** suite. The CDF's preliminary design feeds detailed subsystem tools, board layouts, the bill of materials and flight software. The simulator becomes the real mission, with hardware-in-the-loop testing and then operations. A document library spans the whole cycle.

**Constraints:**
- one maintainer and a teaching budget;
- **login security beyond doubt (two-factor at minimum)**;
- Canadian hosting (Danish partners under GDPR);
- bilingual EN/FR;
- ground tools stay **spacecraft-agnostic**, so the MCS behaves the same against a simulator, a ground station or real hardware.

## 2. Where things stand today

1. **Every link is opened by the ground side towards the simulator:** TC on 8001, TM on 8002, HTTP/WS on 8080. The cloud MCS also polls `/api/state`. The instructor console and config editor live inside the simulator process.
2. **Nothing is authenticated.** The operator's position is whatever the browser claims, unknown positions are allowed, and the raw TM/TC sockets accept anyone. `smo-gateway` cannot relay TCs.
3. **There is no voice, chat or second-key interlock.**
4. **SpaceCDF is a single process with in-memory rooms.** Identity is self-declared, and a per-request API key leaks to other users.

## 3. Architecture at a glance

```
                       PUBLIC INTERNET (browsers anywhere)
                                   │ HTTPS only
               ┌───────────────────▼────────────────────┐
               │  Google Cloud external HTTPS LB + Cloud Armor (WAF, rate limits)
               │  Identity-Aware Proxy: nobody reaches any app without a
               │  verified login + second factor (§5)
               └───────┬──────────────────────┬─────────┘
                       │                      │
  ┌────────────────────▼───────────┐   ┌──────▼──────────────────────────┐
  │ GROUND SEGMENT (per session)    │   │ PLATFORM (once)                  │
  │  MCS · planner/wall · tools     │   │  Portal: missions, teams,        │
  │  rfsim bridge + radio page      │   │   sessions, rosters, practice    │
  │  GSG ground-station gateway ◄───┼─┐ │  Game director + crew bots (§7)  │
  └─────────────────────────────────┘ │ │  LiveKit voice + TURN (§6)       │
                                       │ │  SpaceCDF hub (§8)               │
  SPACE-SEGMENT PROVIDERS (pick one) ──┤ │  Postgres · object storage       │
   a) cloud simulator container ───────┤ └─────────────────────────────────┘
      (same VPC, no WAN; the default)  │
   b) laptop simulator + space-link    │
      agent (outbound WSS 443)  ───────┤
   c) real ground station (later) ─────┤   all three present the same interface
   d) HIL flatsat (vision) ────────────┘   to the GSG, so the MCS never knows which
```

**Principles**
- **The provider changes; the ground segment does not.** The GSG accepts a cloud simulator, a laptop simulator, a real station or a flatsat behind one interface (TM out, TC in, link status, time). This is the spacecraft-agnostic rule turned into an architecture.
- **Nothing is reachable without strong login.** Authentication happens at Google's edge (IAP), *before* any of our code runs. Inside, authority comes from the session roster, which one service holds for both commanding and voice.
- **One isolated ground-segment stack per session** (class team or practice run), because the MCS and planner hold global state.
- **One container image, several profiles:**

  | Profile | Contents |
  | --- | --- |
  | `space` | simulator (+ agent when on a laptop) |
  | `ground` | MCS, planner, rfsim, tools, GSG |
  | `platform` | portal, director/bots, voice, SpaceCDF hub |

  The image tag pins `configs/eosat1/`, so the simulator and MCS always decode identically.
- **Organised by Mission → Team → Session from day one.** The lifecycle vision (§10) hangs everything on a *mission*.

## 4. The space-segment link

### 4.1 Ground-station gateway (GSG)
- Re-exposes TC and TM as local sockets for the MCS and rfsim. It also serves `/api/state` locally, from pushed STATE data with the transit delay removed. That ends WAN polling and the planner's blocking stall.
- Proxies the instructor console (instructor role only). The `/config` editor is never exposed.
- Receives S15 dumps.
- Publishes **GS LINK UP / DEGRADED / DOWN** to the MCS header and console log.
- Delivery modes are borrowed from CCSDS SLE: *online-timely* (drop on backlog) or *online-complete* (buffer and replay). TCs are never replayed.
- Refuses to bind if the provider's config hash differs from the ground's.

### 4.2 Providers
| Provider | Connection | Notes |
| --- | --- | --- |
| **Cloud simulator** (default) | Container on the same private network as the GSG; plain TCP, never exposed | Started per session by the portal: class sessions on instructor request, practice sessions automatically |
| **Laptop simulator** | **Space-link agent** on the laptop dials **out** over WSS 443 with a per-session token | Works from any network; no inbound ports |
| **Real ground station** (later) | The rfsim already produces CCSDS frames and IQ. A station adapter links the GSG/rfsim to a station's interface: SDR at a partner station, or an SLE provider (yamcs jsle). | **Receive-only first.** Uplink stays disabled by configuration. Enabling it needs a licensed station and spacecraft, instructor arm plus FD second key, and a separate admin-only switch |
| **HIL flatsat** (vision, §10) | A real OBC on a bench, wired through the same agent pattern; the simulator provides environment and sensors | Same interface to the GSG |

## 5. Login and authorisation: "very sure"

**Recommendation: Google Identity-Aware Proxy (IAP) with Identity Platform external identities, MFA required for every account.**

- **IAP checks identity before any request reaches a VM.** Our apps are not on the internet at all, only behind the load balancer and IAP. A bug in our code can't expose an unauthenticated page.
- **Identity Platform holds the accounts:**
  - invite-only e-mail accounts;
  - optional "Sign in with Google/Microsoft" for convenience;
  - **TOTP authenticator apps as the mandatory second factor**, with SMS allowed only as a fallback if you want.
  - Google runs brute-force protection, credential handling and the sign-in UI. It is not a server we have to secure. *Spike item: confirm the MFA options and the self-enrolment flow in WP-0.*
- **Defence in depth:**
  - Cloud Armor rate limits and WAF rules on the load balancer.
  - VMs with **no public IP**; admin SSH only through IAP TCP forwarding with OS Login and 2FA.
  - Apps verify the **IAP-signed JWT** on every request, so a request that bypassed IAP is rejected.
  - Short sessions, with re-authentication for instructor/admin actions.
  - Cloud Audit Logs for sign-ins and admin actions.
- **Authorisation inside the apps:**
  - Platform roles: `admin`, `instructor`, `operator`, `observer`, held in the portal database and keyed by the IAP identity.
  - **Session rosters** give positions. The MCS takes the position from the roster, never from the browser, and checks authority on every TC path. Unknown positions are denied; clock and sim controls are instructor-only. WebSocket origin checks are on.
  - **FD second key** for critical commands.
- **Voice media:** LiveKit's audio can't pass through IAP. Its access tokens are minted only by our portal after IAP authentication, are scoped to a room, and are short-lived.
- **Fallback if IAP doesn't fit** (e.g. a WebSocket issue found in the spike): self-hosted Keycloak with **WebAuthn passkeys or TOTP set as required actions**, plus oauth2-proxy in front of every app. This is the same model, run by us.

## 6. Voice loops
Unchanged from rev 1. Loops are configured in `voice_loops.yaml`. Each user can be OFF, MON (monitor, blue) or TALK (green) on a loop, monitoring many but talking on one. Push-to-talk, a volume per loop, a talker indicator, private lines, and opt-in recordings stamped with UTC and sim time, indexed in the console log.

It runs on self-hosted **LiveKit**:
- one room per session;
- each person's mic is muted until push-to-talk;
- the talk loop is a server-set attribute, and each browser listens only to the loops it monitors;
- a controller enforces rights from the roster.

A one-day trial of DLR's **openvocs** comes first. TURN over TLS on 443. In practice mode the bots speak on the loops too (§7).

## 7. Practice mode (gamified)

**Goal:** someone can open the site at any time, choose a scenario and a role, and fly a realistic session alone or with a few friends. The platform supplies the spacecraft, the missing crew, and the failures.

**Assumption to confirm:** "without a simulator" is read as *without anyone having to run or drive a simulator*. The platform starts a headless simulator container automatically for each practice session. This keeps the same physics, failure catalogue and telemetry as class mode. A purely scripted telemetry player is possible but would duplicate the spacecraft model and drift from it.

| Component | What it does |
| --- | --- |
| **Session launcher** (portal) | Picks a mission phase (LEOP, commissioning, nominal ops, contingency), difficulty and roles. It starts an isolated ground stack plus a cloud simulator and seats the user(s) in the roster. Idle sessions are torn down. |
| **Crew bots** | One per unfilled position, holding that position in the roster with a **BOT** badge, and acting only through the same MCS API a human uses. **Deterministic core:**<br>• answers GO/NO-GO polls from its subsystem's limits<br>• makes the standard callouts (AOS/LOS, limit violations, mode changes)<br>• runs its routine procedures when the FD asks<br>• executes contingency procedures only on FD instruction<br>• refuses anything outside its authority<br>**Optional language layer:** Claude for natural replies in chat. On voice, LiveKit Agents (speech-to-text → LLM → text-to-speech) so bots can talk and listen on the loops. A **callout menu** (standard phrases as buttons) keeps it usable without speech recognition. |
| **Game director** | Plays the instructor. It waits for the human's **READY**, then injects failures from the catalogue, **filtered by the roles that humans hold** (an EPS trainee gets EPS faults; bots handle faults in their own areas or escalate). It times injections to passes and eclipse, and ramps difficulty. It uses the existing instructor failure-injection API. |
| **Scoring** | Measured from the console log and telemetry:<br>• time to detect<br>• correct procedure chosen<br>• correct TCs (wrong or rejected ones penalised)<br>• callout discipline<br>• handovers<br>• spacecraft health at the end |
| **Game layer** | Levels per position, badges ("first LEOP", "clean contingency"), personal history and replay. Cohort leaderboards are opt-in. All bilingual. |
| **Debrief** | The existing report generator plus a scorecard, voice recording (if on) and a timeline of injected faults against the user's actions. |

Class mode is the same machinery with the director switched off and a human instructor driving the simulator (cloud or laptop). The bots can still fill gaps in a small class.

## 8. SpaceCDF: join or start an instance
- **Phase 1:** one hosted course instance behind IAP. Studies and sessions get owners and members; share links.
- **Phase 2:** "start my own" from the portal, using **JupyterHub + DockerSpawner + standalone proxy**, all open source. You get named instances with templates (blank, EOSat-3U, UniSat-1, course weeks), sharing, idle shutdown and persistent volumes.
- **Phase 3 (optional):** a local install with `spacecdf share`.

**Required fixes:**
1. the key leak;
2. serve the built frontend;
3. support a base path and remove the `:8000` WebSocket rewrite;
4. take identity from IAP;
5. owners and members, with protected delete, import and export;
6. move the risk register and Pugh matrix server-side;
7. one worker per instance;
8. a production image.

**LLM keys:** either bring your own (kept in the browser and sent per request), or a course key behind a LiteLLM proxy with per-student budgets.

## 9. Hosting on Google Cloud, Toronto (northamerica-northeast2)
| Item | Choice |
| --- | --- |
| Project | A new project alongside communiversity.studio, or the same billing account. Region `northamerica-northeast2` (Toronto), giving Canadian residency for VMs, disks, Cloud SQL and Cloud Storage. |
| Compute | **Compute Engine VMs running Docker Compose**: one platform VM and one or more session VMs. Toronto list prices are about US$54/month (e2-standard-2), **US$108/month (e2-standard-4)** and US$215/month (e2-standard-8), before discounts. Practice sessions can later move to **GKE Autopilot** for per-session pods if demand grows. |
| Edge | External HTTPS load balancer, Google-managed certificates, **Cloud Armor**, **IAP**. A wildcard DNS record per session sub-domain lives in Cloud DNS. |
| Voice | LiveKit on its own small VM with a public IP for TURN and media (UDP 3478 and 50000–60000, TCP/TLS 443). |
| Data | Cloud SQL Postgres (portal, SpaceCDF) or Postgres in a container to start. Cloud Storage buckets in Toronto for recordings, dumps, documents and backups, with lifecycle rules for retention. |
| Ops | Cloud Logging and Monitoring with uptime checks (including "GS link up"), budget alerts, nightly snapshots. |
| Cost guide | Pilot: platform VM e2-standard-4 + voice VM e2-small + storage ≈ **US$140–180/month**. Class term with 4–6 teams: add one e2-standard-8 session VM, ≈ US$350–400/month. Practice mode scales with use, since idle sessions are torn down. |

## 10. The long-term vision: design → develop → test → fly

A single **mission digital thread**. Each stage writes to the same mission model, and the next stage starts from it.

| Stage | What exists today | What gets added |
| --- | --- | --- |
| **1. Preliminary design** | SpaceCDF: concurrent design, Arcadia-style functions, an ECSS-E-TM-10-25 parameter model, requirements, budgets, ECSS document exports | Becomes the mission's root record |
| **2. Detailed design** | Analysis closures in SpaceCDF (power, thermal network, AOCS physics, link, FMECA, V&V) | **Subsystem workbenches** (EPS, AOCS, TT&C, OBDH/flight software, thermal, structure, payload). Each refines its slice of the model, with its own documents and checks. External solvers where sensible (e.g. CalculiX for FEM) |
| **3. Develop** | The SMO TC/TM catalogue, XTCE and SMDL exports | **Generated products:**<br>• the TM/TC database (XTCE) feeding both ground and flight software<br>• a **flight-software skeleton** with PUS services (NASA F′ or cFS)<br>• **board designs in KiCad**: reference subsystem boards assembled from the design, with BOM and Gerbers ready for a fabrication order<br>• a COTS equipment library with datasheet-backed models |
| **4. Test** | The simulator with subsystem models and failure catalogue | **Simulator generated from the mission model** (real COTS parameters). **HIL:** a flatsat OBC running the generated flight software connects through the space-link agent, with the simulator supplying environment and sensors. **Environmental test records** (vibration, TVAC, EMC) are captured against the V&V matrix |
| **5. Fly** | MCS, planner, procedures, voice (this document) | Same ground segment against the real ground-station provider |
| **Throughout** | ECSS document exports, bilingual sync tool | **Document library:** the ECSS DRD tree per phase, versioned, both generated and authored, linked requirements → design → verification → test reports, review gates (SRR, PDR, CDR, QR, FRR), EN/FR |

**What this means for the web work now** (cheap to do now, expensive later):
1. Organise the platform by **Mission → Team → Session**, with a mission record that SpaceCDF, documents, simulator configs and ops sessions all reference.
2. Treat **XTCE generated from the mission model** as the eventual source of `configs/eosat1/`. The SMO already exports XTCE/SMDL, so keep the config hash in the GSG bind.
3. Keep the GSG **provider-agnostic** (§4.2), so HIL and a real station are new providers, not a redesign.
4. Store documents and test evidence in **versioned object storage** with mission-scoped access from day one.

## 11. Phases and work packages

| Phase | WP | Content | Days |
| --- | --- | --- | --- |
| **0 · now** | WP-0 Platform | GCP project in Toronto, load balancer + Cloud Armor + **IAP with mandatory MFA** (spike: MFA enrolment, WebSockets through IAP), platform VM, current SMO in the cloud with a **cloud simulator** (no laptop link needed), SpaceCDF course instance with the key-leak, frontend and image fixes | 4–5 |
| | WP-V0 Voice trial | openvocs one day, LiveKit two-loop push-to-talk prototype one day | 2 |
| **1** | WP-1 GSG + providers | GSG, cloud-sim provider, laptop space-link agent, STATE push, instructor proxy, dumps; retire smo-gateway | 6–8 |
| | WP-2 Portal + containers | Mission/Team/Session model, rosters, session launcher, Compose profiles, teardown | 5–6 |
| | WP-3 Authority + hardening | Roster authority on every TC path, IAP JWT check, FD second key, console chat, hardening list | 5–6 |
| | WP-4 Voice | Loop config, controller, keyset panel, `/voice`, recorder | 6–8 |
| **2** | WP-5 Practice mode v1 | Game director, deterministic crew bots, callout menu, scoring, scorecard debrief | 8–10 |
| | WP-6 SpaceCDF multi-user + start-my-own | Fixes, owners and sharing, JupyterHub | 7–9 |
| | WP-7 Pilot | Class plus solo practice; measure bandwidth, voice delay, cost | 2 |
| **3** | WP-8 Bots that talk | LiveKit Agents speech-to-text/LLM/text-to-speech crew on the loops, Claude-backed replies | 5–7 |
| | WP-9 Real ground station (receive) | Station adapter, receive-only frames into the GSG, uplink locked | 5–8 |
| **4+ · vision** | WP-10… | Mission model as source of configs, subsystem workbenches, KiCad and flight-software generation, HIL provider, document library | multi-term |

## 12. Decisions for Franz
1. **GCP project:** a new project next to communiversity.studio (same billing), and which domain?
2. **Second factor:** TOTP app mandatory for everyone (recommended)? Allow SMS as a fallback? Passkeys optional?
3. **Practice mode:** confirm the reading of "without a simulator" (§7, an auto-started headless simulator). Should bots use deterministic callouts only at first, or include the Claude-backed language layer from the start?
4. **Voice:** openvocs or LiveKit after the trial? Recordings on or off by default?
5. **Real ground station:** which station do you have in mind (a partner's, SatNOGS, uOttawa's)? Receive-only first?
6. **Scale for the pilot:** how many concurrent class teams, and roughly how many practice users?
