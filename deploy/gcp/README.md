# C2O on Google Cloud: runbook

This runbook puts the SMO ground segment (MCS, planner and the instructor console through the space-link
gateway) on the web at `c2o.live`. It sits behind Google sign-in with mandatory 2-step verification. The
simulator runs either on **your laptop** or on a **cloud simulator VM**.

Written 2026-10-30. **Nothing here has been run against a real Google Cloud project yet.** See
[What was checked offline](#what-was-checked-offline-and-what-was-not); every **[verify]** marks a point
only a real run can settle.

```
                  ┌──────────── Google global external Application Load Balancer (IP: c2o-lb-ip) ───────────┐
browser ─HTTPS──► │ managed cert · TLS 1.2+ · Cloud Armor rate limits · http→https redirect                 │
                  │  ops.c2o.live, c2o.live ─ IAP (students+instructors) ─► ground VM :9090 MCS           │
                  │  plan.c2o.live          ─ IAP (students+instructors) ─► ground VM :9091 planner       │
                  │  sim.c2o.live           ─ IAP (instructors only)     ─► ground VM :8080 GSG proxy     │
laptop agent ─WSS►│  link.c2o.live/link     ─ IAP OFF (HMAC secret)      ─► ground VM :9100 GSG /link     │
                  └──────────────────────────────────────────────────────────────────────────────────────────┘
VPC c2o-vpc 10.20.0.0/24 (Toronto) · no external IPs on VMs · outbound via Cloud NAT · admin SSH via IAP
  c2o-ground-vm 10.20.0.10  docker compose --profile ground   (GSG, MCS, planner, tools)
  c2o-sim-vm    10.20.0.11  docker compose --profile space    → ws://10.20.0.10:9100/link (private, never via the LB)
```

**Who can reach what.** IAP admits only `@c2o.live` accounts, because the Google-managed OAuth client
serves internal users only. Students and instructors reach ops and plan; only instructors reach sim. The
`/link` path is the one way in without IAP: the agent proves the link session secret (HMAC upgrade header,
then a mutual challenge, then a MAC on every frame). The VPC firewall lets in only Google's load-balancer
ranges (and the sim VM on port 9100), plus IAP on port 22.

**Files in this folder**

| File | What it is |
|---|---|
| `c2o.env.example` | Settings; copy to `c2o.env` (git-ignored) and set `PROJECT` |
| `setup.sh` | Creates or repairs everything. Idempotent, so rerun it after any failure |
| `vm-bootstrap.sh` | The VMs' startup script: Docker, clone, credentials, `docker compose up` |
| `start.sh` / `stop.sh` | Class day on and off |
| `rotate-link-secret.sh` | New link session secret, rolled out to both VMs |
| `teardown.sh` | Deletes everything `setup.sh` made |
| `env/*.example` | The cloud `ground.env` / `space.env` templates that `vm-bootstrap.sh` fills in |

Run every script from the repository root in **Google Cloud Shell** (gcloud is already signed in there),
for example `bash deploy/gcp/start.sh`. Do not confuse `deploy/gcp/start.sh` (the cloud) with
`sim/start.sh` (the simulator suite on your laptop).

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

**Users.** **Directory → Users → Add new user**: first name, last name, primary email (`name@c2o.live`).
Let Google generate the password and choose "ask for a password change at next sign-in". Send the
sign-in details to the student's university address. Then add the user to the right group: open the
group, choose **Add members**, and paste several addresses at once.

For a whole class, use **Users → Bulk update users → Download blank CSV template**. Fill in *First Name,
Last Name, Email Address, Password, Change Password at Next Sign-In = TRUE* and upload it, then paste
the addresses into the group's *Add members*.

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

It enables the APIs and creates the following:

- the VPC, subnet, Cloud NAT and three firewall rules;
- two service accounts and the Secret Manager secret `c2o-link-session`;
- two VMs: Debian 12, e2-standard-2, 30 GB, no external IP, Shielded VM;
- the instance group with named ports `mcs:9090 planner:9091 instructor:8080 link:9100`;
- four health checks and four backend services (timeout 3600 s);
- Cloud Armor, IAP and its group bindings;
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

## 6. DNS A records at Squarespace (10 min)

The IP is the one `setup.sh` printed. To show it again:

```bash
gcloud compute addresses describe c2o-lb-ip --global --format='value(address)'
```

At <https://account.squarespace.com/domains> → **c2o.live → DNS**, first **delete** any existing records
on these names that point elsewhere. Look for the A, AAAA and CNAME records on `@`, `ops`, `plan`, `sim`
and `link`. A domain moved from Google Domains or set up by Squarespace may carry preset records
(*Squarespace Defaults*, parked-page A records, a `www` CNAME). `www` itself may stay. Also turn off any
domain forwarding on the bare domain. Then **Add record** five times:

| Name (host) | Type | Data | TTL |
|---|---|---|---|
| `@` | A | *LB IP* | 1 hour (3600) or less |
| `ops` | A | *LB IP* | same |
| `plan` | A | *LB IP* | same |
| `sim` | A | *LB IP* | same |
| `link` | A | *LB IP* | same |

Keep the TTL the same on all of them; Squarespace asks for that on its Google-hosted DNS. Do **not** add
AAAA records: the load balancer has an IPv4 address only, and a stray AAAA blocks the certificate. If
you set `INCLUDE_APEX=no`, skip `@`.

Check from Cloud Shell; every name must print the LB IP:

```bash
for h in c2o.live ops.c2o.live plan.c2o.live sim.c2o.live link.c2o.live; do echo "$h $(dig +short "$h" A)"; done
```

## 7. Wait for the managed certificate (15-60 min, sometimes longer)

```bash
gcloud compute ssl-certificates describe c2o-cert --global --format='yaml(managed)'
```

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

(The four LB-facing ports listen on the VM's internal IP, not on `localhost`. The tool viewers are on
`localhost` only.)

**By hand** (to redo a step on a VM, or if the startup script failed):

```bash
sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh            # same as a boot
sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh refresh    # re-read the secret, recreate containers
sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh update     # git pull REPO_REF, rebuild, restart
# if /opt/c2o is missing because the clone failed, run the startup script again:
sudo google_metadata_script_runner startup
```

**Ground-only tools** (delayed-TM viewer 8092, orbit tools 8093, documentation 8095) are deliberately
not on the load balancer. Reach them through an SSH tunnel, then use Cloud Shell's **Web preview**
(change the port to 8092), or run the same command on a laptop with gcloud:

```bash
gcloud compute ssh c2o-ground-vm --zone=northamerica-northeast2-a --tunnel-through-iap \
    -- -N -L 8092:localhost:8092 -L 8093:localhost:8093 -L 8095:localhost:8095
```

(The old draft's `gcloud compute start-iap-tunnel … 8092` cannot work: IAP connects to the VM's network
interface, and these ports are published on its loopback.)

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
| 1 | `bash deploy/gcp/start.sh` | All four backends `HEALTHY` |
| 2 | `curl -sI http://ops.c2o.live` | `301` to `https://ops.c2o.live/` |
| 3 | `curl -sI https://ops.c2o.live` | `302` to `accounts.google.com` (IAP) |
| 4 | `curl -si https://link.c2o.live/link \| head -1` | `401` from the GSG (IAP off, no HMAC header) **[verify]** (a 400 also means "reached the GSG, refused") |
| 5 | Browser, a personal Gmail account → ops.c2o.live | Refused by Google (not an internal user) |
| 6 | Browser, `test.student@c2o.live` → ops.c2o.live | Password, then 2SV enrolment or prompt, then the **MCS** |
| 7 | Same student → plan.c2o.live | Planner |
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

**Class day**

```bash
cd ~/C2O
bash deploy/gcp/start.sh           # 3-5 min until healthy; SIM_MODE from c2o.env (or --sim=laptop / --sim=cloud)
# … class …
bash deploy/gcp/stop.sh            # stops both VMs; disks, data, IP, cert and IAP all stay
```

- A stopped VM costs only its disk. The **load balancer** costs about USD 0.025/h while its forwarding
  rules exist, whether or not the VMs run.
- For a break of weeks, `bash deploy/gcp/stop.sh --lb` also deletes the two forwarding rules. That nets
  about USD 11/month, because the reserved IP then costs USD 0.01/h. `start.sh` recreates them; allow a
  few minutes. **[verify]** Managed certificates renew about 30 days before expiry, so if the rules are
  gone at that moment, renewal may wait until they are back.
- Cloud Armor's policy and rules are billed whether or not anything runs (~USD 7/month). Delete them
  only with `teardown.sh`.

**Adding students:** step 3 (Admin console user plus `c2o-students` membership). They sign in at
<https://ops.c2o.live>, change their password and enrol 2SV within the enrolment period. At the end of
term, **suspend** or **delete** accounts; deleting frees a place under the 50-user cap.

**Lost phone / 2SV lockout:** Admin console → Users → the user → **Security** →
*Get backup verification codes*, which you then give to the student.

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

A stopped sim VM must be started for this (`start.sh --sim=cloud`). Otherwise it keeps its old
checkout. After editing anything in `deploy/gcp/` itself, rerun `setup.sh`: it refreshes the startup
script in the VMs' metadata.

**Logs** (on the ground VM, `cd /opt/c2o/sim`):
`sudo docker compose --env-file docker/ground.env -f docker/compose.yaml --profile ground logs -f gsg mcs`.
Link events are `key=value` lines (`event=link_up`, `link_down`, `link_superseded`, …).

**Backing up the MCS TM archive** before risky changes:
`gcloud compute disks snapshot c2o-ground-vm --zone=northamerica-northeast2-a`.

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

Biggest levers: stop the VMs (`stop.sh`); the load balancer's ~CAD 25/month is the floor while the site
exists. An e2-standard-2 for the ground VM is a guess. Check `docker stats` in a real class and resize if
it is idle or saturated (`gcloud compute instances set-machine-type`, VM stopped).

## 13. Teardown

1. Keep anything you want first: the snapshot from step 11, or copy reports and dumps off the VM
   (`gcloud compute scp --tunnel-through-iap c2o-ground-vm:/path . --zone=…`).
2. `bash deploy/gcp/teardown.sh`. Type the project id to confirm. It deletes the VMs **and their
   disks**, the LB, IP, certificate, Armor policy, network, secret and service accounts. The project,
   billing link and Cloud Identity remain.
   *Or*, if the project holds nothing else: `gcloud projects delete c2o-live-prod`. Google keeps it
   recoverable for 30 days, and billing stops at once.
3. Delete the five A records at Squarespace.
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
  9091, 8080 and 9100 on 10.20.0.10, tools on 127.0.0.1, and `SMO_GSG_ALLOWED_ORIGINS=https://sim.c2o.live`.
  `--profile space` gives the agent `SMO_LINK_URL=ws://10.20.0.10:9100/link`. `--profile local-demo`
  also validates.
- The agent's plaintext rule (`smo_link/channel.py host_is_private`) was exercised directly:
  `ws://10.20.0.10:9100/link` is accepted; `ws://link.c2o.live/link` and `ws://<public IP>` are refused;
  `wss://…` is accepted.

**Not checked (needs a real project):** anything that calls Google: API enablement, resource creation,
IAP with the Google-managed client, WebSockets through IAP and the 3600 s reconnect, health-check
results, the certificate, Secret Manager from the VM, the Docker image build and first-boot time on
Debian 12, the Cloud Identity / Admin console / Squarespace click paths, and prices. All are marked
**[verify]**, or covered by the smoke test in step 10.
