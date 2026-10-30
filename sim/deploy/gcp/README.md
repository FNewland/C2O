# WP-0: SMO ground segment on Google Cloud (Toronto)

The **ground profile** (`docker/compose.yaml`: GSG + MCS + planner + tools) on one VM in `northamerica-northeast2`,
behind a global external Application Load Balancer. The simulator runs elsewhere (laptop, or the `space` /
`local-demo` profile) and dials **out** to `/link`. Design: `docs/web_2026-10/LINK_DESIGN.md` §5, §7.

> **Every `gcloud` snippet below is UNTESTED** (written from the docs; check flags during the spike and fix this file). **[verify]** = open question.

```
browser ──HTTPS──► ALB (managed cert, Cloud Armor) ──┬─ IAP ON ─► VM :9090 MCS, :9091 planner, :8080 instructor proxy (GSG)
agent   ──WSS───►  same ALB, host link.<domain>  ────┴─ IAP OFF ► VM :9100 GSG /link (HMAC token, timeoutSec 3600)
VM: no external IP · egress via Cloud NAT · admin via IAP SSH · GSG TM/TC 8001/8002 never published
```

## 1. Project, network, NAT, firewall

```bash
export PROJECT=smo-ops-spike REGION=northamerica-northeast2 ZONE=northamerica-northeast2-a
gcloud config set project $PROJECT
gcloud services enable compute.googleapis.com iap.googleapis.com identitytoolkit.googleapis.com \
    certificatemanager.googleapis.com secretmanager.googleapis.com
gcloud compute networks create smo-vpc --subnet-mode=custom
gcloud compute networks subnets create smo-ground --network=smo-vpc --region=$REGION --range=10.20.0.0/24
gcloud compute routers create smo-router --network=smo-vpc --region=$REGION
gcloud compute routers nats create smo-nat --router=smo-router --region=$REGION \
    --auto-allocate-nat-external-ips --nat-all-subnet-ip-ranges      # VM pulls packages/images
# Google front ends + health checkers only (LINK_DESIGN §7). Nothing else reaches the service ports.
gcloud compute firewall-rules create smo-allow-lb --network=smo-vpc --direction=INGRESS \
    --source-ranges=130.211.0.0/22,35.191.0.0/16 --target-tags=smo-ground \
    --allow=tcp:8080,tcp:9090,tcp:9091,tcp:9100
# IAP TCP forwarding for SSH (admin only):
gcloud compute firewall-rules create smo-allow-iap-ssh --network=smo-vpc --direction=INGRESS \
    --source-ranges=35.235.240.0/20 --target-tags=smo-ground --allow=tcp:22
```

## 2. VM (Debian 12, Docker + compose plugin, no external IP)

```bash
#!/bin/bash
# startup.sh — passed as instance metadata; idempotent
set -euo pipefail
command -v docker >/dev/null && exit 0
apt-get update && apt-get install -y ca-certificates curl gnupg git
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian bookworm stable" \
    > /etc/apt/sources.list.d/docker.list
apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
systemctl enable --now docker
```

```bash
gcloud compute instances create smo-ground-1 --zone=$ZONE --machine-type=e2-standard-4 \
    --subnet=smo-ground --no-address --tags=smo-ground --shielded-secure-boot \
    --image-family=debian-12 --image-project=debian-cloud --boot-disk-size=50GB \
    --metadata-from-file=startup-script=startup.sh
gcloud compute ssh smo-ground-1 --zone=$ZONE --tunnel-through-iap
# on the VM: clone/copy the repo, create docker/ground.env (§5), then
#   export SMO_CONFIG_HASH=$(docker/config-hash.sh)
#   export SMO_PUBLISH_ADDR=$(curl -s -H 'Metadata-Flavor: Google' \
#       http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/ip)
#   sudo -E docker compose -f docker/compose.yaml --profile ground up -d --build
```

**Publish address (review H4).** Compose publishes MCS 9090, planner 9091, instructor proxy 8080 and link 9100 on
`${SMO_PUBLISH_ADDR:-127.0.0.1}`. None of these has its own login (the MCS can send TCs), so the default keeps them
on the VM's loopback, where the load balancer cannot reach them either. On this VM set `SMO_PUBLISH_ADDR` to the
VM's **internal** IP (above, or put it in `docker/ground.env`). Never `0.0.0.0` on a machine with a public or campus
address: Docker-published ports bypass ufw/iptables INPUT rules. What reaches the four ports is then decided by the
VPC firewall of §1 alone: the Google front-end and health-check ranges `130.211.0.0/22` and `35.191.0.0/16` (and
nothing else) on 8080/9090/9091/9100, and IAP TCP forwarding `35.235.240.0/20` on 22 only. Do not add a rule that
opens these ports to `0.0.0.0/0` or to the campus range. The link port 9100 is handled the same way: it is reached
only through the LB's IAP-off `/link` backend, and inside the VPC the hop from the LB to the GSG is plaintext HTTP.
That hop cannot forge or replay frames (every link frame is MACed end to end with a key from the session secret,
LINK_DESIGN §3.3), but it **can read them**: confidentiality exists only from the agent to the LB (TLS).

Tools (8092/8093/8095) and radio UI (8094) publish on VM loopback only: `gcloud compute start-iap-tunnel smo-ground-1 8092 --local-host-port=localhost:8092 --zone=$ZONE`.

## 3. Load balancer

One unmanaged instance group, one backend service per named port. Host rules, not path prefixes (the consoles use absolute paths).

```bash
gcloud compute instance-groups unmanaged create smo-ig --zone=$ZONE
gcloud compute instance-groups unmanaged add-instances smo-ig --zone=$ZONE --instances=smo-ground-1
gcloud compute instance-groups set-named-ports smo-ig --zone=$ZONE \
    --named-ports=mcs:9090,planner:9091,instructor:8080,link:9100
gcloud compute health-checks create http smo-hc-gsg --port=8080 --request-path=/healthz
gcloud compute health-checks create http smo-hc-mcs --port=9090 --request-path=/
gcloud compute health-checks create http smo-hc-planner --port=9091 --request-path=/api/schedule

# (a) human UIs — IAP ON. The consoles hold WebSockets, and an ALB backend timeout also caps a WebSocket's
#     lifetime, so give them a long timeout too [verify the UIs reconnect cleanly at the cap].
for svc in mcs:smo-hc-mcs planner:smo-hc-planner instructor:smo-hc-gsg; do
  name=${svc%%:*}; hc=${svc##*:}
  gcloud compute backend-services create smo-$name --global --protocol=HTTP --port-name=$name \
      --health-checks=$hc --timeout=3600s --load-balancing-scheme=EXTERNAL_MANAGED
  gcloud compute backend-services add-backend smo-$name --global --instance-group=smo-ig --instance-group-zone=$ZONE
  gcloud compute backend-services update smo-$name --global --iap=enabled
done

# (b) /link — its own backend service, IAP OFF (the agent is not a browser; the HMAC token authenticates it),
#     timeoutSec 3600 so the WebSocket survives; the agent reconnects with backoff when the LB cuts it.
gcloud compute backend-services create smo-link --global --protocol=HTTP --port-name=link \
    --health-checks=smo-hc-gsg --timeout=3600s --load-balancing-scheme=EXTERNAL_MANAGED
gcloud compute backend-services add-backend smo-link --global --instance-group=smo-ig --instance-group-zone=$ZONE

gcloud compute url-maps create smo-urlmap --default-service=smo-mcs
gcloud compute url-maps add-path-matcher smo-urlmap --path-matcher-name=link --default-service=smo-mcs \
    --new-hosts=link.ops.example.ca --path-rules="/link=smo-link"     # only /link reaches the IAP-off backend
gcloud compute url-maps add-path-matcher smo-urlmap --path-matcher-name=planner \
    --default-service=smo-planner --new-hosts=planner.ops.example.ca
gcloud compute url-maps add-path-matcher smo-urlmap --path-matcher-name=instructor \
    --default-service=smo-instructor --new-hosts=instructor.ops.example.ca
#   ops.example.ca (and anything else) → smo-mcs, the default service.

gcloud compute ssl-certificates create smo-cert --global \
    --domains=ops.example.ca,planner.ops.example.ca,instructor.ops.example.ca,link.ops.example.ca
gcloud compute target-https-proxies create smo-https --url-map=smo-urlmap --ssl-certificates=smo-cert
gcloud compute addresses create smo-ip --global
gcloud compute forwarding-rules create smo-fr --global --load-balancing-scheme=EXTERNAL_MANAGED \
    --address=smo-ip --target-https-proxy=smo-https --ports=443
```
# Point the four DNS names at smo-ip; the managed cert provisions once DNS resolves (up to ~1 h).

## 4. Cloud Armor (rate limits)

```bash
gcloud compute security-policies create smo-armor
# /link: a handful of reconnects per minute is normal; floods are not.
gcloud compute security-policies rules create 1000 --security-policy=smo-armor \
    --expression="request.path.startsWith('/link')" --action=rate-based-ban \
    --rate-limit-threshold-count=30 --rate-limit-threshold-interval-sec=60 \
    --ban-duration-sec=600 --conform-action=allow --exceed-action=deny-429 --enforce-on-key=IP
# UIs: generous per-IP throttle (polling consoles) [verify numbers against a real class].
gcloud compute security-policies rules create 2000 --security-policy=smo-armor --src-ip-ranges='*' \
    --action=throttle --rate-limit-threshold-count=1200 --rate-limit-threshold-interval-sec=60 \
    --conform-action=allow --exceed-action=deny-429 --enforce-on-key=IP
for b in smo-mcs smo-planner smo-instructor smo-link; do
  gcloud compute backend-services update $b --global --security-policy=smo-armor; done
```

## 5. Identity and the link secret

- **Humans:** IAP on the three UI backends. For non-Google (student) accounts use **Identity Platform** as
  IAP's external identity provider, with **MFA** (TOTP/SMS) required. **[verify in the spike]**: IAP +
  Identity Platform sign-in page, MFA enforcement, and that the console WebSockets pass IAP. Grant
  `roles/iap.httpsResourceAccessor` per backend (instructors only on `smo-instructor`).
- **The agent:** no IAP. It proves the session secret at the upgrade (HMAC header) and again in a mutual
  challenge-response inside the WebSocket; the GSG proves it back, and every frame after that is MACed
  (LINK_DESIGN §3.3). Behind the LB, set `SMO_GSG_ALLOWED_ORIGINS=https://instructor.ops.example.ca` in
  `docker/ground.env`: the instructor proxy answers only Host names it knows (DNS-rebinding guard).
  Issue a per-session secret on the VM and give the same pair to both ends:

```bash
sudo docker compose -f docker/compose.yaml run --rm --no-deps gsg python -m smo_link.token new
#   → session id + 32-byte hex secret → docker/ground.env (SMO_LINK_SESSION, SMO_LINK_SECRET); restart gsg.
#   Send the pair out of band to the space side's docker/space.env with SMO_LINK_URL=wss://link.ops.example.ca/link.
#   Optional: keep it in Secret Manager, mount it, set SMO_LINK_SECRET_FILE. Rotate = new pair + restart both ends.
```

## 6. Smoke test

1. `curl -s localhost:8080/healthz` on the VM → 200; `/link-status` shows `DOWN` until an agent binds.
2. Start the space side; `/link-status` → `UP`; MCS at `https://ops.example.ca` (after IAP login) shows TM.
3. No IAP login → sign-in redirect; `/link` without a token → 401; `instructor.…/config` → 403 (GSG route allowlist).
4. Kill the agent: MCS reports no TC connection within seconds; restart it: TM resumes.
