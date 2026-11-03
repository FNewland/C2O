# C2O on Google Cloud: runbook

This runbook puts the SMO ground segment (MCS, planner and the instructor console through the space-link
gateway) on the web at `c2o.live`. It sits behind Google sign-in with mandatory 2-step verification. The
simulator runs either on **your laptop** or on a **cloud simulator VM**.

`https://c2o.live` itself is the **welcome page**: every screen (mission control, planner, SpaceCDF,
the tool pages, and the instructor screens marked "instructors only") with its address and a live
status (available / not running / waiting for a simulator), plus a mission strip (simulator link,
spacecraft mode from telemetry, next pass) and the signed-in account. Every screen keeps its own
address (`ops.c2o.live` and so on); the welcome page only links to them. It is `sim/tools/portal.py`
on port 8090 of the ground VM.

Written 2026-10-30. **Nothing here has been run against a real Google Cloud project yet.** See
[What was checked offline](#what-was-checked-offline-and-what-was-not); every **[verify]** marks a point
only a real run can settle.

```
                  ┌──────────── Google global external Application Load Balancer (IP: c2o-lb-ip) ───────────┐
browser ─HTTPS──► │ managed cert · TLS 1.2+ · Cloud Armor rate limits · http→https redirect                 │
                  │  c2o.live (welcome)     ─ IAP (students+instructors) ─► ground VM :8090 portal        │
                  │  ops.c2o.live           ─ IAP (students+instructors) ─► ground VM :9090 MCS           │
                  │  plan.c2o.live          ─ IAP (students+instructors) ─► ground VM :9091 planner       │
                  │  sim.c2o.live           ─ IAP (instructors only)     ─► ground VM :8080 GSG proxy     │
laptop agent ─WSS►│  link.c2o.live/link     ─ IAP OFF (HMAC secret)      ─► ground VM :9100 GSG /link     │
                  │  tm. orbit. radio. docs ─ IAP (students+instructors) ─► ground VM :8092-8095 tools    │
                  │  scenarios. adcs.       ─ IAP (instructors only)     ─► sim VM :8096-8097 tools       │
                  └──────────────────────────────────────────────────────────────────────────────────────────┘
VPC c2o-vpc 10.20.0.0/24 (Toronto) · no external IPs on VMs · outbound via Cloud NAT · admin SSH via IAP
  c2o-ground-vm 10.20.0.10  docker compose --profile ground --profile rf  (GSG, MCS, planner, RF bridge, tools)
  c2o-sim-vm    10.20.0.11  docker compose --profile space    → ws://10.20.0.10:9100/link (private, never via the LB)
                            (+ scenario generator and ADCS failure viewer)
```

**Who can reach what.** IAP admits only `@c2o.live` accounts, because the Google-managed OAuth client
serves internal users only. Students and instructors reach the welcome page (`c2o.live`), ops, plan,
design and the tool pages (tm, orbit, radio, docs); only instructors reach sim, scenarios and adcs. The
welcome page lists the instructor screens to everyone, labelled "instructors only"; a student who
follows one gets IAP's "You don't have access". The
`/link` path is the one way in without IAP: the agent proves the link session secret (HMAC upgrade header,
then a mutual challenge, then a MAC on every frame). The VPC firewall lets in only Google's load-balancer
ranges (and the sim VM on port 9100), plus IAP on port 22. One private rule lets the ground VM reach
the sim VM's tool ports 8096-8097, so the welcome page can say whether they are up.

**Files in this folder**

| File | What it is |
|---|---|
| `c2o` | **The everyday command**: status and costs, up/down, automatic schedule, recordings, users (§11) |
| `c2o.env.example` | Settings; copy to `c2o.env` (git-ignored) and set `PROJECT` |
| `setup.sh` | Creates or repairs everything. Idempotent, so rerun it after any failure |
| `vm-bootstrap.sh` | The VMs' startup script: Docker, clone, credentials, `docker compose up` |
| `voice-bootstrap.sh` | The voice loops VM's startup script: Docker, LiveKit + Caddy config, `docker compose up` ([Voice loops](#voice-loops)) |
| `start.sh` / `stop.sh` | Class day on and off (what `c2o up` / `c2o down` run) |
| `rotate-link-secret.sh` | New link session secret, rolled out to both VMs |
| `teardown.sh` | Deletes everything `setup.sh` made |
| `env/*.example` | The cloud `ground.env` / `space.env` templates that `vm-bootstrap.sh` fills in |

Run every script from the repository root in **Google Cloud Shell** (gcloud is already signed in there),
for example `bash deploy/gcp/start.sh`, or on your Mac with gcloud installed and signed in as
`admin@c2o.live`. Do not confuse `deploy/gcp/start.sh` (the cloud) with `sim/start.sh` (the simulator
suite on your laptop). Once set up, day-to-day work goes through one command, **`c2o`** (§11). Install
it once, then open a new terminal:

```bash
echo "alias c2o='bash ~/C2O/deploy/gcp/c2o'" >> ~/.zshrc     # Mac (zsh)
echo "alias c2o='bash ~/C2O/deploy/gcp/c2o'" >> ~/.bashrc    # Cloud Shell, or a bash user
c2o help
```

(Adjust `~/C2O` if your checkout is elsewhere. `c2o` runs with the macOS bash 3.2 and with Linux bash.)

**Before you begin:** commit and push `deploy/gcp/` (and the `sim/docker` fixes) to
`github.com/FNewland/C2O` on `main`. The VMs clone the repository on first boot and read their env
templates from it.

---

## 1. Sign up for Cloud Identity Free on c2o.live (30-45 min, plus DNS wait)

Cloud Identity Free gives you `@c2o.live` Google accounts without Gmail or Drive, and it creates the
`c2o.live` Google Cloud **organisation** that the project must live in.

1. In a private browser window, open **<https://workspace.google.com/gcpidentity/signup?sku=identitybasic>**.
2. Follow the guided steps. Business name: e.g. *C2O Open Teaching Platform*. Number of employees: *2-9*.
   Region: *Canada*. Current email: `franz.newland@gmail.com`, which becomes the recovery address.
3. "Does your business have a domain?" Answer **Yes**, enter `c2o.live`, and confirm.
4. Create the first admin account. Use **`admin@c2o.live`**: Google requires the admin username to differ
   from the recovery email, and keeping administration separate from teaching is good practice. You can
   create `franz@c2o.live` for teaching in step 3.
5. Accept the terms. The Admin console (admin.google.com) opens and asks you to **verify the domain**.
   It shows a TXT record like `google-site-verification=AbC…`. Copy the whole value.
6. In another tab, add the TXT record at Squarespace **[verify the exact labels]**:
   1. Go to <https://account.squarespace.com/domains>, click **c2o.live**, then **DNS** in the side panel
      (sometimes labelled *DNS Settings*).
   2. Under **Custom records**, click **Add record**. Set **Type** `TXT`, **Name/Host** `@`, **Data** the
      full `google-site-verification=…` string, and leave TTL at the default. **Save.**
   3. Squarespace may ask for your password or 2FA first.
7. Back in the Admin console, click **Verify** (or *Protect* / *Verify domain*). Squarespace DNS usually
   updates within minutes, but allow up to a few hours. Leave the TXT record in place permanently.
8. When it shows as verified, the organisation `c2o.live` is created automatically within a few minutes.
   Check it at <https://console.cloud.google.com> (signed in as `admin@c2o.live`): the project picker
   should list **c2o.live** as an organisation.

> **User limit.** Cloud Identity Free gives you room for **50 free users** by default. For larger classes,
> the super admin submits Google's *Cloud Identity user increase* form (linked from Google's "How licensing
> works for Cloud Identity" page; the Admin console path is **[verify]**). Google decides,
> so ask **weeks before term**. Suspended users still count; deleted users don't.

Safety net for the admin account: give `admin@c2o.live` a security key or passkey, save its backup codes
(myaccount.google.com → Security → 2-Step Verification → Backup codes), and consider a second super admin
so one lost phone can't lock you out.

## 2. Enforce 2-step verification (10 min)

Admin console → **Security → Authentication → 2-step verification** (direct link: admin.google.com/ac/security/2sv).

| Setting | Value | Why |
|---|---|---|
| Allow users to turn on 2-Step Verification | **On** | Required before enforcement |
| Enforcement | **On** | Starts immediately. "From date" starts within 24-48 h of the date |
| New user enrollment period | **1 week** | A new student can sign in with only a password for this long, then must enrol. Create accounts about a week before the first lab and enrol everyone in that lab. Allowed range: 1 day to 6 months |
| Frequency | **Allow user to trust the device** ✔ | Students get fewer prompts on their own laptops. Untick it for a stricter regime |
| Methods | **Any except verification codes via text, phone call** | Allows authenticator apps (Google Authenticator, Microsoft Authenticator, 1Password…), security keys, passkeys and Google prompts, but not SMS. *Only security key* is too strict for students |

Click **Save**. **[verify]** that *Methods* is offered in Cloud Identity Free. Google's help page doesn't
list per-edition support. If the option is missing, *Any* is the fallback; it permits SMS.

Turn 2SV on for `admin@c2o.live` itself **before** enforcement reaches it.

## 3. Groups and the first users (15 min, then 1 min per user)

**Groups.** Admin console → **Directory → Groups → Create group**:

| Name | Email | Members |
|---|---|---|
| C2O Instructors | `c2o-instructors@c2o.live` | You, TAs |
| C2O Students | `c2o-students@c2o.live` | The class |

For each group, under *Access settings*, keep "Who can join the group" set to **Only invited users**.
External members should stay **Off**.

**Users, with `c2o`** (after step 5; the groups above must exist). Sign in once per computer for
user management. A browser opens: choose **admin@c2o.live** and allow the access it asks for.

```bash
c2o users login                                    # once per computer
c2o users add test.student --name "Test Student"   # a bare name means @c2o.live; role student
c2o users add franz --name "Franz Newland" --role instructor
c2o users list                                     # role, 2SV enrolled, suspended, last sign-in
```

`add` creates the account with a random temporary password, **printed once**, that must be changed at
the first sign-in, and puts it in `c2o-students` or `c2o-instructors`. Send the address and password
to the person's university email. For a whole class, put one line per person in a CSV file,
`email,first,last,role` (the header line is optional; role `student` if left empty; a bare name works
for the email):

```
email,first,last,role
jdoe,Jane,Doe,student
asmith,Alex,Smith,
ta.lee,Kim,Lee,instructor
```

```bash
c2o users import class.csv                         # dry run: shows what would happen
c2o users import class.csv --apply --out pw.csv    # does it; pw.csv (mode 600) = email,password
```

Delete `pw.csv` once the passwords are sent. Rerunning an import creates only the missing accounts.
The other user commands are in §11. `c2o users login` runs `gcloud auth application-default login`
with the Admin SDK scopes (`admin.directory.user`, `admin.directory.group.member`, plus
`cloud-platform`) and sets the project as its quota project; `setup.sh` enables the Admin SDK API.
**[verify]** that Google accepts those scopes with gcloud's own sign-in client; if it shows "This app
is blocked", create a *Desktop* OAuth client in the project (APIs & Services → Credentials), download
its JSON and run `gcloud auth application-default login --client-id-file=client.json
--scopes=…` with the same scopes.

**Or by hand in the Admin console:** **Directory → Users → Add new user** (first name, last name,
`name@c2o.live`, generated password, "ask for a password change at next sign-in"), then open the
group, **Add members**, and paste the addresses. For a class: **Users → Bulk update users**.

Create at least one **test student** (e.g. `test.student@c2o.live`) and add yourself (`franz@c2o.live`,
or `admin@c2o.live`) to `c2o-instructors`. Group changes reach IAP within minutes.

## 4. Project inside the organisation, plus billing (10 min)

Your billing account belongs to `franz.newland@gmail.com`. Give the new admin permission to use it:

1. Signed in as **franz.newland@gmail.com**, open <https://console.cloud.google.com/billing>, pick the
   billing account, then choose **Account management → Add principal**. Enter `admin@c2o.live` with role
   **Billing Account User**, then **Save**.
2. Sign in as **admin@c2o.live** (use a separate browser profile to stay sane), open
   <https://console.cloud.google.com>, and click **Activate Cloud Shell** (the `>_` icon, top right).
3. In Cloud Shell:

```bash
gcloud organizations list                      # note the ID of c2o.live
ORG_ID=123456789012                            # ← yours
PROJECT=c2o-live-prod                          # your choice; global and permanent
gcloud projects create "$PROJECT" --organization="$ORG_ID" --name="C2O Platform"
gcloud billing accounts list                   # note the ACCOUNT_ID (XXXXXX-XXXXXX-XXXXXX)
gcloud billing projects link "$PROJECT" --billing-account=XXXXXX-XXXXXX-XXXXXX
gcloud config set project "$PROJECT"
```

The project **must** be under the organisation (`--organization`). The Google-managed IAP client works
only for an organisation's own users, and that is what keeps out everyone without a `@c2o.live` account.

New organisations come with "secure by default" policies. One of them, *domain-restricted sharing*,
refuses IAM grants to accounts outside `c2o.live`, so you cannot add `franz.newland@gmail.com` to the
project. That is intended. Work as `admin@c2o.live` (or `franz@c2o.live` after granting it *Owner*).

**Set a budget alert now:** Billing → **Budgets & alerts → Create budget**. Scope: project
`c2o-live-prod`; amount e.g. **CAD 120/month**; alerts at 50 %, 90 % and 100 %.

## 5. Run the setup script (15 min)

In Cloud Shell (as `admin@c2o.live`):

```bash
git clone https://github.com/FNewland/C2O.git && cd C2O
cp deploy/gcp/c2o.env.example deploy/gcp/c2o.env
nano deploy/gcp/c2o.env          # set PROJECT; the rest is already c2o.live / Toronto
bash deploy/gcp/setup.sh
```

It enables the APIs (including the Admin SDK for `c2o users`) and creates the following:

- the VPC, subnet, Cloud NAT and three firewall rules;
- two service accounts and the Secret Manager secret `c2o-link-session`;
- two VMs: Debian 12, e2-standard-2, 30 GB, no external IP, Shielded VM;
- the instance group with named ports `mcs:9090 planner:9091 instructor:8080 link:9100`;
- four health checks and four backend services (timeout 3600 s);
- Cloud Armor, IAP and its group bindings;
- permission for the Compute Engine service agent to start and stop the VMs (role *Compute Instance
  Admin (v1)*), which the automatic schedule (`c2o schedule`) needs;
- the URL map with host rules, the managed certificate, the TLS policy, the http→https redirect, the
  global IP and the two forwarding rules.

At the end it prints the **load balancer IP** and the exact DNS records for step 6.

The scripts read the project from `c2o.env`, but the plain `gcloud` commands in steps 6 to 14 use your
shell's default project. If you have other projects, or open a new terminal, set it first:
`gcloud config set account admin@c2o.live && gcloud config set project c2o-live-prod`. An error that
names a different project in its URL means this step was skipped. To flip between several projects,
use `switch.sh` (run it with `help` for usage): `bash deploy/gcp/switch.sh add c2o admin@c2o.live
c2o-live-prod` once, then `bash deploy/gcp/switch.sh c2o`.

If anything fails, read the message, fix the cause and **rerun `setup.sh`**. It checks every resource
first and creates only what is missing.

### 5b. SpaceCDF's AI advisor key (optional, 2 min)

SpaceCDF (https://design.c2o.live) works without it, in manual mode. To turn on its AI advisor, store an
Anthropic API key in the secret `setup.sh` created, then refresh the ground VM:

```bash
printf %s 'sk-ant-…' | gcloud secrets versions add c2o-anthropic-key --data-file=-
gcloud compute ssh c2o-ground-vm --zone=northamerica-northeast2-a --tunnel-through-iap \
    --command='sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh refresh'
```

Every signed-in user then spends from that key; `design/configs/genai.yaml` sets the per-session token
limit. To turn the advisor off again, disable the secret's versions
(`gcloud secrets versions disable latest --secret=c2o-anthropic-key`) and refresh.

## 6. DNS A records at Squarespace (10 min)

The IP is the one `setup.sh` printed. To show it again:

```bash
gcloud compute addresses describe c2o-lb-ip --global --format='value(address)'
```

At <https://account.squarespace.com/domains> → **c2o.live → DNS**, first **delete** any existing records
on these names that point elsewhere. Look for the A, AAAA and CNAME records on `@`, `ops`, `plan`, `sim`
and `link`. A domain moved from Google Domains or set up by Squarespace may carry preset records
(*Squarespace Defaults*, parked-page A records, a `www` CNAME). `www` itself may stay. Also turn off any
domain forwarding on the bare domain. Then **Add record** for each name below (twelve in all; the
last seven are the tool pages and SpaceCDF):

| Name (host) | Type | Data | TTL |
|---|---|---|---|
| `@` | A | *LB IP* | 1 hour (3600) or less |
| `ops` | A | *LB IP* | same |
| `plan` | A | *LB IP* | same |
| `sim` | A | *LB IP* | same |
| `link` | A | *LB IP* | same |
| `tm`, `orbit`, `radio`, `docs`, `design` | A | *LB IP* | same (one record each) |
| `scenarios`, `adcs` | A | *LB IP* | same (one record each) |

Keep the TTL the same on all of them; Squarespace asks for that on its Google-hosted DNS. Do **not** add
AAAA records: the load balancer has an IPv4 address only, and a stray AAAA blocks the certificate. If
you set `INCLUDE_APEX=no`, skip `@`; there is then no welcome page (its back end exists but nothing
routes to it) and every screen is reached by its own address.

The voice loops need **two more** A records, `voice` and `voice-turn`, pointing at the voice VM's own
address rather than the LB IP: see [Voice loops](#voice-loops). `setup.sh` prints them.

Check from Cloud Shell; every name must print the LB IP:

```bash
for h in c2o.live ops plan sim link tm orbit radio docs design scenarios adcs; do
  case $h in *.*) n=$h ;; *) n=$h.c2o.live ;; esac; echo "$n $(dig +short "$n" A)"; done
```

## 7. Wait for the managed certificates (15-60 min, sometimes longer)

```bash
gcloud compute ssl-certificates describe c2o-cert --global --format='yaml(managed)'
gcloud compute ssl-certificates list --global --filter='name ~ ^c2o-cert-tools' --format='yaml(name,managed)'
```

`c2o-cert` covers the five main names; `c2o-cert-tools-<hash>` covers the tool pages and SpaceCDF. They
provision independently, so the main site can be up while the tool pages are still waiting. The hash
follows the list of tool names: if that list changes, `setup.sh` makes a new certificate, swaps it in
and deletes the old one, and the tool pages are briefly on the old one until the new one is ACTIVE.

Wait until `status: ACTIVE` and every domain shows `ACTIVE`. `PROVISIONING` with `FAILED_NOT_VISIBLE` on
a domain means Google can't yet see that name pointing at the LB IP: check step 6. Once DNS is right it
normally takes 15-60 min, and Google allows up to 24 h. Every listed name must resolve, including the
apex if it's on the certificate.

## 8. The two VMs bootstrap themselves (automatic, 10-15 min after setup)

You don't need to do anything here. On every boot `vm-bootstrap.sh` runs these steps:

1. It installs Docker Engine and the compose plugin (first boot only).
2. It clones `REPO_URL`@`REPO_REF` into `/opt/c2o` (first boot only).
3. It fetches the link credentials from Secret Manager. The ground VM **creates** them the first time;
   the sim VM waits for them.
4. It writes `sim/docker/ground.env` or `space.env` (mode 600) from `deploy/gcp/env/*.example`:
   - ground: `SMO_PUBLISH_ADDR=<its internal IP>`, `SMO_GSG_ALLOWED_ORIGINS=https://sim.c2o.live`, …
   - sim: `SMO_LINK_URL=ws://10.20.0.10:9100/link`
5. It runs `docker compose --env-file docker/<role>.env -f docker/compose.yaml --profile ground|space
   up -d --build`.

Watch progress:

```bash
gcloud compute instances get-serial-port-output c2o-ground-vm --zone=northamerica-northeast2-a | grep c2o-bootstrap
gcloud compute ssh c2o-ground-vm --zone=northamerica-northeast2-a --tunnel-through-iap   # then:
sudo journalctl -u google-startup-scripts -f                 # live log of the bootstrap
cd /opt/c2o/sim && sudo docker compose --env-file docker/ground.env -f docker/compose.yaml --profile ground ps
curl -s 10.20.0.10:8080/link-status; echo                    # "UP" once a simulator is connected
```

(The LB-facing ports, including the tool pages, listen on the VM's internal IP, not on `localhost`:
from an SSH session use `curl 10.20.0.10:8092/`.)

**By hand** (to redo a step on a VM, or if the startup script failed):

```bash
sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh            # same as a boot
sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh refresh    # re-read the secret, recreate containers
sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh update     # git pull REPO_REF, rebuild, restart
sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh sizes      # data volume sizes (c2o data list)
sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh clean telemetry dumps reports   # c2o data clean
# if /opt/c2o is missing because the clone failed, run the startup script again:
sudo google_metadata_script_runner startup
```

**Tool pages.** Each tool has its own address, behind the same sign-in:

| Address | Tool | Who | Runs on |
|---|---|---|---|
| https://tm.c2o.live | Delayed-TM viewer | students + instructors | ground VM :8092 |
| https://orbit.c2o.live | Orbit tools | students + instructors | ground VM :8093 |
| https://radio.c2o.live | Radio view (RF bridge) | students + instructors | ground VM :8094 |
| https://docs.c2o.live | Documentation | students + instructors | ground VM :8095 |
| https://design.c2o.live | SpaceCDF design tool | students + instructors | ground VM :8000 |
| https://scenarios.c2o.live | Scenario generator | instructors | sim VM :8096 |
| https://adcs.c2o.live | ADCS failure viewer | instructors | sim VM :8097 |

- The **RF bridge** runs as a tap beside the MCS: it reads the same telemetry and shows the S-band
  picture, but the MCS does not depend on it. (Putting the MCS behind it would hide the UHF beacon
  telemetry of LEOP, which the bridge does not model.) Its controls change the radio for everyone.
- The **scenario generator** saves into the simulator's workspace volume, which the simulator loads at
  start. To use a new scenario, restart the simulator:
  `gcloud compute ssh c2o-sim-vm --zone=northamerica-northeast2-a --tunnel-through-iap --command='sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh refresh'`.
- **scenarios** and **adcs** run next to the simulator, so they are down when the sim VM is stopped
  (`start.sh --sim=laptop`). On the laptop they are at http://localhost:8096 and :8097.

## 9. The laptop as the simulator (10 min the first time)

Only **one** simulator may be connected. A new agent supersedes the old one, and the old one keeps
reconnecting, so two running simulators knock each other off every few seconds. **Always stop one
before starting the other.**

1. Run the **same commit** as the cloud (`git pull`). The link refuses a different mission config
   (close 4409, `config-mismatch`).
2. In Cloud Shell, fetch the credentials and switch the cloud to laptop mode. This stops the sim VM:

   ```bash
   gcloud secrets versions access latest --secret=c2o-link-session > session.env
   bash deploy/gcp/start.sh --sim=laptop
   ```

   Download `session.env` (Cloud Shell ⋮ menu → **Download**), then delete it in Cloud Shell
   (`rm session.env`). On the laptop, put it at **`C2O/sim/workspace/link/session.env`** and run
   `chmod 600` on it. That path is git-ignored. With gcloud on the laptop (signed in as an `@c2o.live`
   admin) you can instead run
   `gcloud secrets versions access latest --secret=c2o-link-session --project=c2o-live-prod > sim/workspace/link/session.env`.
3. On the laptop, from `C2O/sim`:

   ```bash
   SMO_LINK_URL=wss://link.c2o.live/link SMO_PROFILE=space ./start.sh
   ```

   (The Docker alternative is `deploy/gcp/env/space.env.laptop.example`.)
4. Open <https://sim.c2o.live/link-status> and check for `"state": "UP"`.

**Switching**

| From → to | Do |
|---|---|
| laptop → cloud sim | Ctrl+C the laptop's `start.sh` first, then `bash deploy/gcp/start.sh --sim=cloud` |
| cloud sim → laptop | `bash deploy/gcp/start.sh --sim=laptop` (stops the sim VM), then start the laptop |

The spacecraft state does not move with the switch: each simulator has its own. Save a breakpoint in the
instructor console before switching if you need continuity. After a secret rotation (step 11) the laptop
needs the new `session.env`.

## 10. Smoke test (20 min)

Use a private browser window for each identity.

| # | Do | Expect |
|---|---|---|
| 1 | `bash deploy/gcp/start.sh` | All five backends (welcome, ops, plan, sim, link) `HEALTHY` |
| 2 | `curl -sI http://ops.c2o.live` | `301` to `https://ops.c2o.live/` |
| 3 | `curl -sI https://ops.c2o.live` | `302` to `accounts.google.com` (IAP) |
| 4 | `curl -si https://link.c2o.live/link \| head -1` | `401` from the GSG (IAP off, no HMAC header) **[verify]** (a 400 also means "reached the GSG, refused") |
| 5 | Browser, a personal Gmail account → ops.c2o.live | Refused by Google (not an internal user) |
| 6 | Browser, `test.student@c2o.live` → ops.c2o.live | Password, then 2SV enrolment or prompt, then the **MCS** |
| 7 | Same student → plan.c2o.live | Planner |
| 7b | Same student → https://c2o.live | The welcome page: "Signed in as test.student@c2o.live", every screen with its status; the simulator link reads "No simulator connected" until one binds |
| 8 | Same student → sim.c2o.live | IAP "You don't have access" |
| 9 | Instructor → sim.c2o.live | Instructor console (through the link) |
| 10 | Instructor → sim.c2o.live/link-status | JSON, `"state": "UP"` |
| 11 | Instructor → sim.c2o.live/config | `403` (never proxied) |
| 12 | Speed up the sim in the instructor console until a pass; in the MCS send S17.1 (connection test) | TM arrives; verification `COMPLETED` |
| 13 | Leave the MCS open 5 min | Live values keep updating (WebSocket through IAP) **[verify]** |
| 14 | `bash deploy/gcp/stop.sh --sim` (or Ctrl+C the laptop) | link-status `DOWN`; MCS shows *No TC connection* |
| 15 | `bash deploy/gcp/start.sh --sim=cloud` | link `UP` again within ~2 min, TM resumes |
| 16 | Leave a console open > 1 h | The LB closes WebSockets at 3600 s; the page should reconnect by itself **[verify]** |

## 11. Daily operations

Everything here is one command, `c2o` (install: see the top of this runbook). `c2o help` shows the
overview; `c2o COMMAND --help` the details. Anything that deletes asks first; `--yes` skips the
question. Run it on your Mac or in Cloud Shell, from anywhere.

**Everyday**

| Command | What it does |
|---|---|
| `c2o status` | Both VMs, the load balancer rules, every screen's health, both certificates, the simulator link (UP/DOWN), the automatic schedule, and a rough **cost per day in CAD** for the state things are in now, with one line on how to save more. `--quick` skips the link check (an SSH session) |
| `c2o up` | Class on: runs `start.sh` (3-5 min until healthy). `--sim=laptop` keeps the cloud simulator off (step 9); `--sim=cloud` uses it; default `SIM_MODE` in `c2o.env` |
| `c2o down` | Class off: runs `stop.sh`. A stopped VM costs only its disk; data, IP, certificates and sign-in all stay. `--sim` stops only the cloud simulator |
| `c2o down --all` | Also deletes the two load-balancer forwarding rules (`stop.sh --lb`): about CAD 0.50 a day less, but the site is unreachable until `c2o up`, which then takes a few minutes longer. For breaks of weeks |

**Automatic start and stop**

```bash
c2o schedule set "Mon-Fri 08:00-18:00"      # or "Mon,Wed 13:00-17:30", "Mon-Tue,Thu-Fri 08:45-12:15", "weekdays 09:00-17:00"
c2o schedule show
c2o schedule clear
```

This is a Compute Engine **instance schedule** (`c2o-schedule`, time zone America/Toronto) attached to
the ground VM, and to the simulator VM when `SIM_MODE=cloud` (`--ground-only` / `--with-sim` override).
One time window for all the chosen days: Google allows one start and one stop time per schedule.
Starts and stops can run up to 15 minutes late, so start a little early; a VM you start by hand is
stopped at the next stop time. The load balancer is billed around the clock either way, and the
schedule does not recreate it after `c2o down --all`. Between terms: `c2o schedule clear` and
`c2o down --all`.

**Users** (sign in once with `c2o users login`, step 3)

| Command | What it does |
|---|---|
| `c2o users list` | Every account: name, email, role (student / instructor / admin), 2SV enrolled, suspended, last sign-in |
| `c2o users seats` | Accounts used of the 50 Cloud Identity Free allows (suspended accounts count) |
| `c2o users add jdoe --name "Jane Doe" [--role instructor]` | New account, temporary password printed once, put in the role's group |
| `c2o users import class.csv [--apply]` | A class list (`email,first,last,role`), dry run first |
| `c2o users reset jdoe` | New temporary password (lost password) |
| `c2o users role jdoe instructor` | Move between `c2o-students` and `c2o-instructors` |
| `c2o users suspend jdoe` / `unsuspend` | Block or allow sign-in; the account still uses a seat |
| `c2o users remove jdoe` | Delete the account and free a seat. Permanent for the person; administrators are refused (use the Admin console for them) |

They sign in at <https://c2o.live> (the welcome page), change their password and enrol 2SV within
the enrolment period. At the end of term, `suspend` or `remove` accounts; removing frees a place
under the 50-user cap. Passwords and the access token never appear on a command line (`ps`): they
travel in temporary files readable only by you, deleted at once.

**Lost phone / 2SV lockout:** Admin console → Users → the user → **Security** →
*Get backup verification codes*, which you then give to the student.

**Recordings** (the data that grows: telemetry, dumps, reports)

```bash
c2o data list                                   # size of each store on each VM, plus snapshots
c2o data clean --telemetry                      # the MCS telemetry archive
c2o data clean --dumps --reports                # delayed-TM dumps (both VMs); reports and RF pass roll-ups
c2o data clean --all --snapshot                 # all three, after a disk snapshot (a way back)
c2o data clean --logbooks                       # every participant logbook, now (see below)
c2o data snapshot                               # snapshot both disks now
c2o data snapshots                              # list them
c2o data prune --keep 3                         # keep the newest 3 per VM, delete older
```

`clean` needs the VMs running (`c2o up`). It runs `vm-bootstrap.sh clean …` on each VM (your local copy,
sent over the IAP SSH session, so a VM does not need updating first): it stops the containers that
use those volumes, deletes the files with the image already on the VM (no downloads), and starts
them again; the screens are back in about a minute. It **never** touches saved scenarios, breakpoints,
config history or link state. `--designs` also deletes every SpaceCDF design; it asks twice, the
second time by typing `delete-designs`, even with `--yes`. Snapshots cost about USD 0.05 per GB-month
**[verify]**: prune them.

| Store (Docker volume) | VM | Holds | Cleared by |
|---|---|---|---|
| `ground-archive` | ground | MCS telemetry archive (SQLite) | `--telemetry` |
| `ground-dumps` | ground | Dumps received by the GSG | `--dumps` |
| `space-dumps` | sim | Dumps written by the simulator | `--dumps` |
| `ground-workspace` | ground | Reports, RF pass roll-ups | `--reports` |
| `ground-workspace/logbook` | ground | Participant logbooks (all screens and SpaceCDF) | `--logbooks` |
| `space-workspace` | sim | Scenarios, breakpoints, config history, link state | never |
| `space-workspace/logbook` | sim | The instructor's own logbook (console on the sim host) | `--logbooks` |
| `spacecdf-data` | ground | SpaceCDF designs | `--designs` only |

**Logbooks: privacy and retention.** Every screen has a **Logbook** button: participants note
decisions, observations and reflections and answer the course-workbook worksheets in context
(docs/plan_2026-11/LOGBOOK_SPEC.md).

- **Private.** A logbook belongs to the signed-in account (the IAP email; "this browser" when run
  locally). Only its owner can read it, through the screen they are using. Instructors get no view of
  participants' text, and `c2o` has no command that shows it. Students hand in the download if it is to
  be graded.
- **Kept 48 hours.** The server deletes a person's whole logbook 48 h after their last entry, and any
  entry older than 7 days even if they keep writing. Every screen runs this purge at start-up and
  hourly. Participants download it (Markdown, or printable HTML for a PDF) from the panel; the screens
  remind them at the end of a session and when less than 12 h remain.
- **Where.** One JSON-lines file per person (named by a hash of the account) in
  `ground-workspace/logbook/` on the ground VM, `space-workspace/logbook/` on the simulator VM for the
  instructor console. The logbook never crosses the space link. `c2o data list` shows its size;
  `c2o data clean --logbooks` deletes all of them at once (for example at the end of a term). It is not
  part of `--all`. Disk snapshots taken with `c2o data snapshot` contain logbooks for as long as the
  snapshot exists: prune them.
- **Settings** (ground.env / space.env): `SMO_LOGBOOK_RETENTION_H` (default 48) and
  `SMO_LOGBOOK_MAX_AGE_H` (default 168).

**Rotating the link secret** (each term, or at once if `session.env` may have leaked):

```bash
bash deploy/gcp/rotate-link-secret.sh
```

The ground VM issues the new pair, stores it in Secret Manager and restarts the ground containers. The
TM archive and dumps survive on volumes, and open consoles reconnect. A running sim VM re-reads it; a
stopped one picks it up at its next boot. Old versions are disabled. A laptop needs the new
`session.env` (step 9.2).

**Updating C2O** (push to GitHub first; update both VMs **and** the laptop to the same commit):

```bash
for vm in c2o-ground-vm c2o-sim-vm; do
  gcloud compute ssh $vm --zone=northamerica-northeast2-a --tunnel-through-iap \
      --command='sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh update'
done
```

A stopped sim VM must be started for this (`c2o up --sim=cloud`). Otherwise it keeps its old
checkout. After editing anything in `deploy/gcp/` itself, rerun `setup.sh`: it refreshes the startup
script in the VMs' metadata.

**Logs** (on the ground VM, `cd /opt/c2o/sim`):
`sudo docker compose --env-file docker/ground.env -f docker/compose.yaml --profile ground logs -f gsg mcs`.
Link events are `key=value` lines (`event=link_up`, `link_down`, `link_superseded`, …).

**What `c2o` calls** (to do a step by hand): `c2o up` = `bash deploy/gcp/start.sh [--sim=…]`;
`c2o down` = `bash deploy/gcp/stop.sh` (`--all` = `--lb`, removing the forwarding rules
`c2o-fr-https` and `c2o-fr-http`); `c2o data snapshot` =
`gcloud compute disks snapshot c2o-ground-vm --zone=northamerica-northeast2-a`; the schedule is
`gcloud compute resource-policies create instance-schedule c2o-schedule` plus
`gcloud compute instances add-resource-policies`; users go to the Admin SDK Directory API
(`admin.googleapis.com/admin/directory/v1`, users and group members).

## Voice loops

Mission-control voice loops in the browser (WP-4 prototype; Franz's rulings V1-V4 of 2026-11-02 in
`docs/plan_2026-11/REDESIGN_DECISIONS.md`): **LiveKit**, on **its own small VM with a static public
IP**, started and stopped with `c2o up` / `c2o down`, **recordings off**.

```
browser on ops.c2o.live (IAP)                       c2o-voice-vm  e2-small, static IP, Debian 12 + Docker
  /voice  keyset panel ──POST /api/voice/token──► MCS (ground VM): IAP identity + position
          (or the Voice button in the MCS header)     + voice_loops.yaml -> one JWT per loop (10 min)
          ──WSS 443  voice.c2o.live ─────────────────► Caddy ─► LiveKit :7880  (signalling)
          ──UDP 50000-60000 / TCP 7881 ──────────────► LiveKit  (audio, ICE)
          ──UDP 3478 / TLS 443 voice-turn.c2o.live ──► LiveKit embedded TURN (restrictive networks)
```

**Why audio does not go through the load balancer.** WebRTC media is UDP (or TURN) and cannot pass
the HTTPS load balancer or IAP. So the voice VM has a public address and only LiveKit's ports open.
Nobody gets in without a **token**, and only the MCS mints tokens, behind IAP. The token names
the person (the IAP email), their position, the one loop it is for, and whether they may talk. It
is valid for 10 minutes; the panel fetches new ones at 7.5 minutes.

**Loops are data**: `sim/configs/eosat1/voice/voice_loops.yaml`. Today there are nine: the FD loop (all
positions), Ops coordination, one per subsystem (EPS/TCS, AOCS/FD, TT&C, Payload, FDIR/Systems,
Propulsion) and Instructor/SIM. Each loop is one LiveKit room, `c2o-<loop id>`. For each position the
file gives the highest state (`OFF`, `MON` to listen, `TALK` to listen and push-to-talk) and the
state when the panel opens.

- A student's browser is **never told** that a loop with `OFF` access exists. The Instructor/SIM loop is
  `instructor_only`, and the MCS refuses to load a file that gives any student position access to it.
- `canPublish` is set only on TALK loops, so even a modified browser cannot talk on a MON loop.
- You talk on one loop at a time.
- The microphone is published muted and opened only while push-to-talk is held (Space, or the button)
  or latched. Echo cancellation, noise suppression and automatic gain are on.

**Who is who.**
- **Position:** until seat binding exists (WP10), the position is the one selected in the MCS
  header. It is browser-claimed, exactly like the MCS's own commanding position today.
- **Name:** the talker indicator shows the IAP email, which nobody can type over.
- **Instructor and SIM role-player seats, and the Instructor/SIM loop:** these need an account listed
  in `VOICE_INSTRUCTORS` in `c2o.env`. The app cannot read the `c2o-instructors` group, so keep the two
  lists in step. The same list decides who sees the instructor tools on the welcome page
  (`SMO_INSTRUCTORS` in `sim/docker/ground.env`, written by `vm-bootstrap.sh`); students do not see them.

### Set it up (once, about 20 minutes plus DNS)

1. **`c2o.env`** (see `c2o.env.example`): leave `CREATE_VOICE_VM=yes`. List the instructor accounts:
   `VOICE_INSTRUCTORS="admin@c2o.live prof@c2o.live"`. Optionally set `VOICE_ACME_EMAIL` (the address
   Let's Encrypt writes to).
2. **`bash deploy/gcp/setup.sh`**. In addition to everything else, it creates:
   - the secret `c2o-livekit-keys`. The API key pair is generated on your computer and piped
     into Secret Manager; it never appears on a command line or in a file.
   - the service account `c2o-voice`
   - the static IP `c2o-voice-ip`
   - the firewall rule `c2o-allow-voice`
   - the VM `c2o-voice-vm`

   It also gives the ground VM the voice settings (instance metadata).
3. **Two A records at Squarespace**, printed at the end of `setup.sh`. Both point to the **voice VM's
   address**, *not* the load balancer's:

   | Name (host) | Type | Data |
   |---|---|---|
   | `voice` | A | *voice IP* |
   | `voice-turn` | A | *voice IP* |

   To show the address again:
   `gcloud compute addresses describe c2o-voice-ip --region=northamerica-northeast2 --format='value(address)'`.
   TURN over TLS needs its own name and certificate, hence the second record. Caddy on the VM gets
   both certificates from Let's Encrypt as soon as the names resolve. It retries by itself, so the
   order does not matter.
4. **Ground VM:** push the branch, then bring the ground VM's code up to date. The new MCS code and the
   `livekit-api` package are in the image, and `voice.env` is written from the secret:

   ```bash
   gcloud compute ssh c2o-ground-vm --zone=northamerica-northeast2-a --tunnel-through-iap \
       --command='sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh update'
   ```

5. **Check:**
   - `curl https://voice.c2o.live/` prints `OK`.
   - `c2o status` shows "Voice loops server … UP".
   - In the MCS, the **Voice** button opens the panel; **Join voice loops**, then hold Space to talk.
   - The direct address is `https://ops.c2o.live/voice`.

### Every day

`c2o up` starts the voice VM along with the others and prints the voice address. `c2o down` stops it.
`c2o schedule set …` includes it, because the voice VM follows the ground VM. `c2o status` shows it,
whether LiveKit answers, and its cost. Stopped, it costs only its disk and its reserved IP.

**Using the panel.** Open it from the **Voice** button in the MCS header, or **Pop out** to a window
of its own (useful when you move around the console).
- Hiding the docked panel keeps you on the loops. **Leave** disconnects.
- Space talks while the panel has the keyboard focus, so click into the panel first. In a pop-out
  window this is always the case.
- Use a headset.

### Ports (firewall rule `c2o-allow-voice`, source anywhere)

These are LiveKit's documented ports for a single VM (checked 2026-11-02 against docs.livekit.io,
"Firewall configuration" and "Deploy to a VM", and the v1.13.10 source):

| Port | What |
|---|---|
| TCP 443 | Caddy, split by TLS name: `voice.` → LiveKit signalling (WSS); `voice-turn.` → TURN/TLS. TURN/TLS is the path through networks that allow only HTTPS |
| TCP 80 | Let's Encrypt HTTP-01 challenges |
| TCP 7881 | WebRTC over TCP, when UDP is blocked |
| UDP 3478 | Embedded TURN/UDP (also STUN) |
| UDP 50000-60000 | WebRTC over UDP, the normal path |

Port 7880 (LiveKit's HTTP) listens on 127.0.0.1 only. TURN/TLS: Caddy ends TLS and passes the
client address with a PROXY v2 header (`turn.proxy_protocol: true`); without it Firefox rejects the
TURN allocation. The two images are pinned by tag and digest in `voice-bootstrap.sh`
(`livekit/livekit-server:v1.13.10`, `livekit/caddyl4:v2.11.3`). No Redis, because a single node does
not need it.

### Change the loops

1. Edit `sim/configs/eosat1/voice/voice_loops.yaml` (comments at the top). Write `"OFF"` in quotes:
   YAML reads a bare OFF as false.
2. Run `python3 -m pytest -q sim/tests/test_content/test_voice_loops_config.py`.
3. Push, then run `vm-bootstrap.sh update` on the ground VM.

An invalid file switches off only voice: the MCS log says why and the panel says "unavailable".
Nothing on the voice VM changes, because rooms are created when someone joins.

### Rotate the voice keys

```bash
python3 -c 'import secrets; print("LIVEKIT_API_KEY=API" + secrets.token_hex(6)); print("LIVEKIT_API_SECRET=" + secrets.token_urlsafe(32))' \
  | gcloud secrets versions add c2o-livekit-keys --data-file=-
gcloud compute ssh c2o-voice-vm  --zone=northamerica-northeast2-a --tunnel-through-iap --command='sudo bash /opt/c2o-voice/voice-bootstrap.sh refresh'
gcloud compute ssh c2o-ground-vm --zone=northamerica-northeast2-a --tunnel-through-iap --command='sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh refresh'
```

People on the loops are disconnected once and must press **Rejoin**.

### On a laptop (no cloud)

From `sim/`:

```bash
docker compose -f docker/compose.yaml --profile voice up -d livekit   # LiveKit dev mode, loopback only
SMO_VOICE=dev ./start.sh                                             # or SMO_VOICE=dev in docker/ground.env
```

Open `http://localhost:9090`, then **Voice**. The `livekit` service runs `livekit-server --dev` on
127.0.0.1:7880 (signalling), 7881/tcp and 7882/udp with a fixed development key that the MCS knows
under `SMO_VOICE=dev`. Locally there is no sign-in: you type a name, which the panel shows as
"unverified", and anyone on the machine may take the instructor seats (`SMO_VOICE_LOCAL_INSTRUCTOR=0`
turns that off). Two browser windows with two names are enough to try a loop.

### Costs (list prices, Toronto, retrieved 2026-11-02)

| Item | Unit price | 24/7 | Class schedule (40 h/month) |
|---|---|---|---|
| Voice VM e2-small | $0.0184/h | $13.43 | $0.74 |
| 10 GB balanced disk | $0.11/GB-month | $1.10 | $1.10 |
| Static IPv4 | $0.005/h in use, $0.01/h reserved while the VM is stopped | $3.65 | $7.10 |
| Internet egress (audio flows only while someone talks: Opus about 30-50 kbit/s per listener) | $0.12/GiB | < $1 | < $0.20 |
| **Total** | | **≈ US$18 (CAD 25)** | **≈ US$9 (CAD 13)** |

The reserved IP is the largest part of the class-schedule cost. Releasing it would change the address
every term, and with it the two DNS records. One e2-small comfortably serves a class on audio only
(LiveKit forwards Opus packets, it does not mix) **[verify]** in a real class with `docker stats`.

### Not in the prototype

- **Recordings:** they stay off (`recordings: false`). The plan is an instructor-only switch using
  LiveKit egress into a Toronto bucket, stamped with UTC and sim time and indexed in the console log.
  `smo_mcs/voice.py: start_recording` is the stub.
- **Seat binding (WP10):** the position is still taken from the MCS header.
- **Verifying the IAP-signed JWT (WP-3):** the MCS trusts the IAP email header. The ground VM has no
  public IP and admits only the load balancer, so the header cannot be forged from outside.
- **Private lines and bots on the loops (WP-8).**
- **Per-session room prefixes:** the prefix is `c2o` for everyone. Set `SMO_VOICE_ROOM_PREFIX` per
  ground stack once there is more than one team.

## 12. Costs

List prices in USD from Google's pricing pages, retrieved **2026-10-30**. CAD at an **assumed 1.39**: if
your billing account is in CAD, Google bills its own CAD prices. Month = 730 h. Taxes excluded.
**[verify]** in the Pricing Calculator (region Toronto) before relying on it.

| Item | Unit price (Toronto) | 24/7 | Class schedule¹ |
|---|---|---|---|
| Ground VM e2-standard-2 | $0.0738/h | $53.87 | $2.95 |
| Sim VM e2-standard-2 | $0.0738/h | $53.87 | $2.95 |
| 2 × 30 GB balanced disk | $0.11/GB-month | $6.60 | $6.60 |
| ALB forwarding rules (2, first-5 bundle) | $0.025/h | $18.25 | $18.25 |
| ALB data processing (~30 GiB in+out) | $0.008/GiB | $0.24 | $0.10 |
| Cloud Armor policy + 2 rules² | $5 + $1/rule per month | $7.00 | $7.00 |
| Cloud Armor requests (5 M / 2 M) | $0.75 per M | $3.75 | $1.50 |
| Cloud NAT gateway (2 VMs) | $0.0014/VM-h | $2.04 | $0.11 |
| Cloud NAT IP³ | $0.005/h | $3.65 | $3.65 |
| Internet egress, premium tier (~30 / 10 GiB) | $0.12/GiB after 1 GiB free | $3.48 | $1.08 |
| LB IP address | free while attached to a forwarding rule | $0 | $0 |
| IAP, Cloud Identity Free, Secret Manager (<6 versions), Logging (<50 GiB) | free tier | $0 | $0 |
| **Total USD** | | **≈ $153** | **≈ $44** |
| **Total CAD (×1.39)** | | **≈ CAD 212** | **≈ CAD 61** |

¹ Both VMs running 40 h/month (e.g. 2 × 3 h classes a week plus prep), stopped otherwise; LB left up.
With `stop.sh --lb` between classes: about **CAD 47**. With the laptop as simulator instead of the sim
VM: subtract about CAD 9 (its hours, disk and NAT share), or about CAD 76 from the 24/7 figure.
² The default rule may also be billed at $1 **[verify]**.
³ Assumes the auto-allocated NAT IP is billed even while no VM uses it **[verify]**.

Biggest levers: stop the VMs (`c2o down`), or let a schedule do it:
`c2o schedule set "Mon-Fri 08:00-18:00"` runs both VMs about 217 h a month, roughly CAD 45 of VM time
instead of CAD 150 around the clock; a schedule for class hours only comes close to the "class
schedule" column. The voice loops VM adds about CAD 13 a month on a class schedule, CAD 25 around the
clock ([Voice loops](#voice-loops)). The schedule does not touch the load balancer: its ~CAD 25/month is the floor while
the site is up, and `c2o down --all` between terms removes most of it (the reserved IP then costs about
CAD 10/month). `c2o status` shows the rate for the state things are in now. An e2-standard-2 for the ground VM is a guess. Check `docker stats` in a real class and resize if
it is idle or saturated (`gcloud compute instances set-machine-type`, VM stopped).

## 13. Teardown

1. Keep anything you want first: a snapshot (`c2o data snapshot`; note that teardown does not delete
   snapshots, so `c2o data prune --keep 0` removes them when you no longer need them), or copy reports and dumps off the VM
   (`gcloud compute scp --tunnel-through-iap c2o-ground-vm:/path . --zone=…`).
2. `bash deploy/gcp/teardown.sh`. Type the project id to confirm. It deletes the VMs **and their
   disks**, the LB, IP, certificate, Armor policy, network, secret and service accounts. The project,
   billing link and Cloud Identity remain.
   *Or*, if the project holds nothing else: `gcloud projects delete c2o-live-prod`. Google keeps it
   recoverable for 30 days, and billing stops at once.
3. Delete the A records at Squarespace (twelve, including the tool pages and SpaceCDF, plus `voice` and
   `voice-turn`).
4. Cloud Identity Free costs nothing, so keep it for next term. To close it, delete the users, then
   remove the subscription in the Admin console under *Billing*.

## 14. Troubleshooting

| Symptom | Check |
|---|---|
| Certificate stays `PROVISIONING`, a domain says `FAILED_NOT_VISIBLE` | `dig +short NAME` must give the LB IP for **every** name on the cert. Remove old Squarespace A/AAAA/CNAME/forwarding on those names. A CAA record on the domain must allow `pki.goog`. After DNS is right, wait up to an hour |
| Browser: *"The server encountered a temporary error"* / 502 / `no healthy upstream` | Backend unhealthy. `gcloud compute backend-services get-health c2o-be-ops --global`. VM stopped or still building (step 8)? On the VM: `compose ps`, then `ss -ltnp \| grep -E '9090\|9091\|8080\|9100'`. Those ports must listen on **10.20.0.10**, not 127.0.0.1 (see the `--env-file` note below) |
| Ports listen on 127.0.0.1 only | Compose was started without `--env-file docker/ground.env`. `SMO_PUBLISH_ADDR` is read for the `ports:` lines only from the shell or `--env-file`, not from `env_file:`. Use `vm-bootstrap.sh refresh` |
| IAP: *"You don't have access"* | User not in the right group (sim = instructors only), group change still propagating (minutes), or the browser is signed into another Google account: use a private window |
| IAP error mentioning `org_internal` / external users | Expected for non-`@c2o.live` accounts. If it hits `@c2o.live` users, the project isn't under the c2o.live organisation (step 4) |
| `setup.sh`: IAP enable fails asking for an OAuth client / consent screen | **[verify]** case: the script relies on `--iap=enabled` without a client ID falling back to the Google-managed client. Enable IAP once in the console instead: *Security → Identity-Aware Proxy*, toggle the three backends, accept the Google-managed client. Then rerun `setup.sh` |
| Instructor console: 403 `host not allowed` | `SMO_GSG_ALLOWED_ORIGINS` in ground.env must be `https://sim.c2o.live` |
| link-status `DOWN`, agent logs `status=401` | Session/secret differ (a laptop with an old `session.env` after rotation) or a clock is > 120 s off |
| Agent: `refusing plaintext ws://` | The URL must be `wss://link.c2o.live/link` (laptop) or `ws://10.20.0.10:9100/link` (sim VM): private **IP literal** only |
| Agent: `config-mismatch` (4409) | Different commits on the two sides: update both (step 11) |
| Agent: HTTP 429 | Cloud Armor banned that IP for 10 min after > `LINK_RATE_PER_MIN` upgrades a minute. Wait, or raise it in `c2o.env` and rerun `setup.sh` |
| Link flaps, GSG logs `link_superseded` over and over | **Two simulators** are connected (laptop and sim VM). Stop one (step 9) |
| Students get 429 in class | A class behind one campus NAT IP shares `UI_RATE_PER_MIN`. Raise it and rerun `setup.sh` |
| Sim VM log: `waiting for the ground VM to create the link credentials` | The ground VM hasn't booted yet or can't write the secret: check its bootstrap log |
| Bootstrap: `deploy/gcp/env/… missing` | `deploy/gcp/` isn't pushed to `REPO_URL`@`REPO_REF` yet |
| `gcloud compute ssh` fails | Add `--troubleshoot`. Firewall `c2o-allow-iap-ssh` must exist; you need *IAP-secured Tunnel User* and OS Login rights (Owner has both) **[verify]** |
| MCS burn-plan card or classic map shows no planner data | The MCS now proxies the planner under its own origin (`/planner/api/...`, read-only), so this works behind the load balancer and IAP. If it still fails, check that the ground VM's MCS can reach the planner on `127.0.0.1:9091` (`docker compose logs mcs`). `SMO_PLANNER_PUBLIC_URL` overrides the address given to the browser |
| Changing the certificate's names (e.g. `INCLUDE_APEX`) | Managed certs are immutable. `gcloud compute ssl-certificates create c2o-cert-2 --global --domains=…`, then `gcloud compute target-https-proxies update c2o-https-proxy --global --ssl-certificates=c2o-cert-2`. Once it is ACTIVE, delete the old one (`gcloud compute ssl-certificates delete c2o-cert --global`) and set `CERT="$PREFIX-cert-2"` in `common.sh` so `setup.sh` keeps using it |
| Org-policy error adding a Gmail account to IAM | Intended (domain-restricted sharing). Use `@c2o.live` accounts |
| `c2o users …`: "needs a sign-in with admin rights" | Run `c2o users login` and sign in as `admin@c2o.live`. In Cloud Shell too: its built-in credentials lack the Admin SDK scopes |
| `c2o users …`: "Admin SDK API is not enabled" | Rerun `setup.sh` (it enables `admin.googleapis.com`), wait a minute |
| `c2o schedule`: VMs never start or stop | The Compute Engine service agent needs *Compute Instance Admin (v1)*: rerun `setup.sh` (or `c2o schedule set` again). Check the schedule's audit logs (Logging, resource *VM instance*, `compute.instances.start`) |

---

## What was checked offline and what was not

Checked on 2026-10-30 in a container with gcloud 570.0.0, Docker Compose v5.6.1 (no daemon) and
ShellCheck 0.11.0, **without any Google Cloud credentials**:

- **Every gcloud command group and flag** used in the scripts was checked against
  `gcloud <group> <command> --help`, mechanically (184 command/flag pairs; a planted bad flag was
  caught). Enumerated values were also checked: `rate-based-ban`, `throttle`, `deny-429`, `ip`, `MODERN`,
  TLS `1.2`, `EXTERNAL_MANAGED`, `--condition=None`, the `--iap=enabled` syntax and the IAP
  `--resource-type=backend-services` binding. The help text confirms that the backend `--timeout` caps a
  WebSocket's lifetime.
- `bash -n` and `shellcheck -x` are clean on all scripts.
- **Dry runs against a gcloud stub:** `setup.sh` from empty, then again with everything present
  (second run creates nothing); `start.sh --sim=laptop`, `stop.sh --lb`, `rotate-link-secret.sh`,
  `teardown.sh` (with and without confirmation). The generated URL map and redirect map YAML parse as
  intended.
- **`vm-bootstrap.sh` against stubbed metadata and Secret Manager:** the ground VM creates the first
  version, the sim VM reads the same pair, rotate adds a version, and rotate is refused on the sim VM.
  Env files are written mode 600.
- **`docker compose config`** with the rendered cloud env files: `--profile ground` publishes 9090,
  9091, 8080, 9100 and the tools 8092-8095 on 10.20.0.10, and `SMO_GSG_ALLOWED_ORIGINS=https://sim.c2o.live`.
  `--profile space` gives the agent `SMO_LINK_URL=ws://10.20.0.10:9100/link`. `--profile local-demo`
  also validates.
- **SpaceCDF online (2026-11-02):** `design/Dockerfile.web` built and run in Docker: the built frontend
  is served by the backend, unknown paths fall back to the app, `/api/whoami` reads the IAP header
  and pre-fills the name, a study survived a container restart on the `/data` volume, and the health
  check passes. The setup dry run creates the `design` backend, IAP grants, the AI-key secret and
  the seven-name tool certificate.
- **Tool pages (2026-11-01):** the whole stack (`local-demo` plus `rf`) built and run in Docker. All
  eleven pages answered 200; the MCS kept its telemetry with the RF bridge as a tap (behind the bridge it
  lost the LEOP beacon telemetry, hence the tap); a scenario saved in the generator appeared in the
  simulator after a restart; the ADCS viewer ran a simulation. `setup.sh` was dry-run against a gcloud
  stub for the new backends, IAP grants, URL map and second certificate.
- The agent's plaintext rule (`smo_link/channel.py host_is_private`) was exercised directly:
  `ws://10.20.0.10:9100/link` is accepted; `ws://link.c2o.live/link` and `ws://<public IP>` are refused;
  `wss://…` is accepted.

- **Welcome page (2026-11-02):** `sim/tools/portal.py` run against stub services (some up, some
  down); EN/FR, light/dark, 1440 and 390 px screenshots, axe clean. `setup.sh` dry run: the apex
  host rule routes to `c2o-be-portal` (named port `portal:8090`, health check `/healthz`, IAP for
  students + instructors); with `INCLUDE_APEX=no` the URL map has no apex rule and no portal
  matcher. `teardown.sh` deletes the portal back end, health check and the probe firewall rule.

- **`c2o` (2026-11-02):** `sim/tests/test_content/test_gcp_admin_cli.py` runs it against stub
  `gcloud`, `curl` and `ssh`: status and its cost line, schedule parsing and the resource-policy and
  IAM calls, `data clean` (confirmation, the `vm-bootstrap.sh clean` action, snapshot first),
  `data prune`, users add/remove/suspend/reset/role/import (dry run and apply), bare names, no
  password or token in any process's arguments, the missing or expired sign-in message. The main
  paths also ran under a real **bash 3.2.57** (the macOS version), which caught a bash 3.2 bug in
  `common.sh` (a failing `command gcloud … || …` ended the script; it now calls gcloud by path).
  `vm-bootstrap.sh clean` / `sizes` ran against a stub docker: right volumes and containers per
  role, no pulls or builds, the in-container delete keeps directories and other files.
  ShellCheck clean at `-S warning`.

- **Voice loops (2026-11-02):** the MCS token service and the `/voice` panel ran against a real
  **livekit-server v1.13.10** (built from source; dev mode, loopback). In two Chromium browsers with
  fake microphones, a Flight Director talking on the FD loop was shown as the active speaker
  ("Flight Director · name") in a Power & Thermal console monitoring it. The student never received
  the Instructor/SIM loop. Repeat it with
  `SMO_E2E=1 LIVEKIT_SERVER_BIN=<livekit-server> python3 -m pytest sim/tests/test_mcs/test_voice_livekit_e2e.py`.
  `voice-bootstrap.sh` rendered its config against stub metadata and Secret
  Manager, and that `livekit.yaml` was loaded by the same server binary. Not checked: Caddy's
  certificates and TURN/TLS on the real VM, and a class-sized load **[verify]**.

**Not checked (needs a real project):** anything that calls Google: API enablement, resource creation,
IAP with the Google-managed client, WebSockets through IAP and the 3600 s reconnect, health-check
results, the certificate, Secret Manager from the VM, instance schedules firing, the Admin SDK
with gcloud's sign-in client, script transfer over `gcloud compute ssh` stdin, the Docker image build and first-boot time on
Debian 12, the Cloud Identity / Admin console / Squarespace click paths, and prices. All are marked
**[verify]**, or covered by the smoke test in step 10.
