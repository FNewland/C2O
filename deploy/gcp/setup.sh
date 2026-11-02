#!/usr/bin/env bash
# C2O on Google Cloud: create (or repair) everything in one project.
#
#   cd ~/C2O && cp deploy/gcp/c2o.env.example deploy/gcp/c2o.env   # edit PROJECT
#   bash deploy/gcp/setup.sh
#
# Idempotent: every resource is looked up first and created only if missing;
# settings that may drift (firewall ranges, backend timeouts, IAP, Cloud Armor
# rates, URL map) are re-applied on every run. Safe to rerun after a failure.
# Prerequisites: README steps 1-4 (Cloud Identity, 2SV, groups, project+billing).
set -euo pipefail
# shellcheck source=common.sh
. "$(dirname "$0")/common.sh"

retry() {  # retry CMD...: new service accounts take a few seconds to exist everywhere
    local n=0
    until "$@"; do
        n=$((n + 1)); [ "$n" -ge 6 ] && return 1
        info "(not ready yet, retrying in 10 s)"; sleep 10
    done
}

# tools_each FUNC: call FUNC key label port where who title, for each tool
# that will exist (the sim-side tools only when the sim VM is created).
tools_each() {
    local key label port where who title
    while read -r key label port where who title; do
        [ -n "$key" ] || continue
        [ "$where" = sim ] && [ "$CREATE_SIM_VM" != yes ] && continue
        "$1" "$key" "$label" "$port" "$where" "$who" "$title"
    done <<<"$TOOLS"
}

require_gcloud_login
log "Project $PROJECT, region $REGION, zone $ZONE, domain $DOMAIN"

billing="$(gcloud billing projects describe "$PROJECT" --format='value(billingEnabled)' 2>/dev/null || true)"
[ "$billing" = "True" ] || die "Billing is not enabled on $PROJECT. Link it first (README step 4)."

parent="$(gcloud projects describe "$PROJECT" --format='value(parent.type)')"
[ "$parent" = "organization" ] || warn "$PROJECT is not directly under an organisation (parent type '$parent'). The Google-managed IAP client admits only users of the project's organisation: move the project into the $DOMAIN organisation (README step 4)."

[ -f "$REPO_ROOT/sim/docker/compose.yaml" ] || die "Run this from a C2O checkout (sim/docker/compose.yaml not found under $REPO_ROOT)."

# ── 1. APIs ─────────────────────────────────────────────────────────────
log "Enabling APIs (first time: about a minute)"
gcloud services enable compute.googleapis.com iap.googleapis.com secretmanager.googleapis.com \
    oslogin.googleapis.com iam.googleapis.com cloudresourcemanager.googleapis.com \
    logging.googleapis.com

# ── 2. Network, NAT, firewall ───────────────────────────────────────────
log "Network"
if ! exists compute networks describe "$NET"; then
    gcloud compute networks create "$NET" --subnet-mode=custom
fi
if ! exists compute networks subnets describe "$SUBNET" --region="$REGION"; then
    gcloud compute networks subnets create "$SUBNET" --network="$NET" --region="$REGION" \
        --range="$SUBNET_RANGE" --enable-private-ip-google-access
fi
if ! exists compute routers describe "$ROUTER" --region="$REGION"; then
    gcloud compute routers create "$ROUTER" --network="$NET" --region="$REGION"
fi
if ! exists compute routers nats describe "$NAT" --router="$ROUTER" --region="$REGION"; then
    # Outbound only: the VMs have no external IP but must reach GitHub,
    # Docker Hub, PyPI and the Debian mirrors.
    gcloud compute routers nats create "$NAT" --router="$ROUTER" --region="$REGION" \
        --auto-allocate-nat-external-ips --nat-all-subnet-ip-ranges
fi

# fw NAME --direction... : create, or re-apply ranges/ports if it exists.
fw() {
    local name="$1" allow="$2" targets="$3"; shift 3
    if exists compute firewall-rules describe "$name"; then
        gcloud compute firewall-rules update "$name" --allow="$allow" --target-tags="$targets" "$@"
    else
        gcloud compute firewall-rules create "$name" --network="$NET" --direction=INGRESS \
            --allow="$allow" --target-tags="$targets" "$@"
    fi
}
log "Firewall (nothing else reaches the VMs: the VPC denies all other ingress)"
# Google front ends and health checkers -> the published ground ports
# (MCS, planner, instructor proxy, link, and the tool viewers 8092-8095).
fw "$FW_LB" tcp:8080,tcp:9090,tcp:9091,tcp:9100,tcp:8092-8095 "$TAG_GROUND" \
    --source-ranges=130.211.0.0/22,35.191.0.0/16
# ... and -> the instructor tools next to the cloud simulator.
if [ "$CREATE_SIM_VM" = yes ]; then
    fw "$FW_LB_SIM" tcp:8096-8097 "$TAG_SIM" --source-ranges=130.211.0.0/22,35.191.0.0/16
fi
# IAP TCP forwarding -> SSH, both VMs (admin only; needs IAM on top).
fw "$FW_IAP" tcp:22 "$TAG_GROUND,$TAG_SIM" --source-ranges=35.235.240.0/20
# Cloud simulator VM -> ground link port, private network only.
fw "$FW_SIM" tcp:9100 "$TAG_GROUND" --source-tags="$TAG_SIM"

# ── 3. Service accounts and the link secret ─────────────────────────────
log "Service accounts"
for sa in "$SA_GROUND:C2O ground VM" "$SA_SIM:C2O simulator VM"; do
    id="${sa%%:*}"
    if ! exists iam service-accounts describe "$id@$PROJECT.iam.gserviceaccount.com"; then
        gcloud iam service-accounts create "$id" --display-name="${sa#*:}"
    fi
    retry gcloud projects add-iam-policy-binding "$PROJECT" \
        --member="serviceAccount:$id@$PROJECT.iam.gserviceaccount.com" \
        --role=roles/logging.logWriter --condition=None --quiet >/dev/null
done

log "Secret $SECRET (the link session id + secret; the ground VM writes the first version)"
if ! exists secrets describe "$SECRET"; then
    gcloud secrets create "$SECRET" --replication-policy=user-managed --locations="$REGION" \
        --labels=app=c2o
fi
retry gcloud secrets add-iam-policy-binding "$SECRET" --member="serviceAccount:$SA_GROUND_EMAIL" \
    --role=roles/secretmanager.secretAccessor --condition=None >/dev/null
retry gcloud secrets add-iam-policy-binding "$SECRET" --member="serviceAccount:$SA_GROUND_EMAIL" \
    --role=roles/secretmanager.secretVersionAdder --condition=None >/dev/null
retry gcloud secrets add-iam-policy-binding "$SECRET" --member="serviceAccount:$SA_SIM_EMAIL" \
    --role=roles/secretmanager.secretAccessor --condition=None >/dev/null

# ── 4. VMs ──────────────────────────────────────────────────────────────
log "Fixed internal addresses ($GROUND_IP ground, $SIM_IP simulator)"
if ! exists compute addresses describe "$ADDR_GROUND_INT" --region="$REGION"; then
    gcloud compute addresses create "$ADDR_GROUND_INT" --region="$REGION" --subnet="$SUBNET" \
        --addresses="$GROUND_IP"
fi
if [ "$CREATE_SIM_VM" = "yes" ] && ! exists compute addresses describe "$ADDR_SIM_INT" --region="$REGION"; then
    gcloud compute addresses create "$ADDR_SIM_INT" --region="$REGION" --subnet="$SUBNET" \
        --addresses="$SIM_IP"
fi

# vm NAME ROLE MACHINE IP TAG SA
vm() {
    local name="$1" role="$2" mtype="$3" ip="$4" tag="$5" sa="$6"
    local md="c2o-role=$role,c2o-repo=$REPO_URL,c2o-ref=$REPO_REF,c2o-domain=$DOMAIN,c2o-ground-ip=$GROUND_IP,c2o-secret=$SECRET,enable-oslogin=TRUE"
    if [ "$(vm_status "$name")" = "NONE" ]; then
        info "creating $name ($mtype, no external IP); first boot installs Docker and builds the image (10-15 min)"
        gcloud compute instances create "$name" --zone="$ZONE" --machine-type="$mtype" \
            --subnet="$SUBNET" --private-network-ip="$ip" --no-address --tags="$tag" \
            --service-account="$sa" --scopes=cloud-platform \
            --image-family=debian-12 --image-project=debian-cloud \
            --boot-disk-size="${BOOT_DISK_GB}GB" --boot-disk-type=pd-balanced \
            --shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring \
            --metadata="$md" --metadata-from-file=startup-script="$GCP_DIR/vm-bootstrap.sh" \
            --labels=app=c2o,role="$role"
    else
        info "$name exists: refreshing its startup script and settings (applied at next boot)"
        gcloud compute instances add-metadata "$name" --zone="$ZONE" \
            --metadata="$md" --metadata-from-file=startup-script="$GCP_DIR/vm-bootstrap.sh"
    fi
}
log "VMs"
vm "$VM_GROUND" ground "$GROUND_MACHINE_TYPE" "$GROUND_IP" "$TAG_GROUND" "$SA_GROUND_EMAIL"
if [ "$CREATE_SIM_VM" = "yes" ]; then
    vm "$VM_SIM" sim "$SIM_MACHINE_TYPE" "$SIM_IP" "$TAG_SIM" "$SA_SIM_EMAIL"
fi

# ── 5. Load balancer back end ───────────────────────────────────────────
log "Instance group and named ports"
if ! exists compute instance-groups unmanaged describe "$IG" --zone="$ZONE"; then
    gcloud compute instance-groups unmanaged create "$IG" --zone="$ZONE"
fi
if ! gcloud compute instance-groups unmanaged list-instances "$IG" --zone="$ZONE" \
        --format='value(instance)' | grep -q "$VM_GROUND"; then
    gcloud compute instance-groups unmanaged add-instances "$IG" --zone="$ZONE" --instances="$VM_GROUND"
fi
# Named ports: the four core services, plus one per tool on that VM.
tool_port() { [ "$4" = "$want" ] && printf ',%s:%s' "$1" "$3"; return 0; }
want=ground; ground_tool_ports="$(tools_each tool_port)"
gcloud compute instance-groups unmanaged set-named-ports "$IG" --zone="$ZONE" \
    --named-ports="mcs:9090,planner:9091,instructor:8080,link:9100$ground_tool_ports"
if [ "$CREATE_SIM_VM" = yes ]; then
    # The sim VM gets its own group: a backend service sends traffic to every
    # VM in a group, and only the sim VM runs the instructor tools.
    if ! exists compute instance-groups unmanaged describe "$IG_SIM" --zone="$ZONE"; then
        gcloud compute instance-groups unmanaged create "$IG_SIM" --zone="$ZONE"
    fi
    if ! gcloud compute instance-groups unmanaged list-instances "$IG_SIM" --zone="$ZONE" \
            --format='value(instance)' | grep -q "$VM_SIM"; then
        gcloud compute instance-groups unmanaged add-instances "$IG_SIM" --zone="$ZONE" --instances="$VM_SIM"
    fi
    want=sim; sim_tool_ports="$(tools_each tool_port)"
    gcloud compute instance-groups unmanaged set-named-ports "$IG_SIM" --zone="$ZONE" \
        --named-ports="${sim_tool_ports#,}"
fi

log "Health checks (they bypass IAP; small JSON endpoints, every 10 s)"
hc() {  # hc NAME PORT PATH
    if exists compute health-checks describe "$1" --global; then
        gcloud compute health-checks update http "$1" --global --port="$2" --request-path="$3" \
            --check-interval=10s --timeout=5s --healthy-threshold=2 --unhealthy-threshold=3 >/dev/null
    else
        gcloud compute health-checks create http "$1" --global --port="$2" --request-path="$3" \
            --check-interval=10s --timeout=5s --healthy-threshold=2 --unhealthy-threshold=3
    fi
}
hc "$HC_OPS"  9090 /api/client-config
hc "$HC_PLAN" 9091 /api/time-source
hc "$HC_SIM"  8080 /healthz
hc "$HC_LINK" 9100 /healthz
tool_hc() { hc "$PREFIX-hc-$1" "$3" /; }
tools_each tool_hc

log "Cloud Armor policy $ARMOR"
if ! exists compute security-policies describe "$ARMOR"; then
    gcloud compute security-policies create "$ARMOR" --description="C2O per-client rate limits"
fi
armor_rule() {  # armor_rule PRIORITY create-flags...
    local prio="$1"; shift
    if gcloud compute security-policies rules describe "$prio" --security-policy="$ARMOR" >/dev/null 2>&1; then
        gcloud compute security-policies rules update "$prio" --security-policy="$ARMOR" "$@" >/dev/null
    else
        gcloud compute security-policies rules create "$prio" --security-policy="$ARMOR" "$@"
    fi
}
# /link upgrades: a few reconnects a minute is normal; a flood earns a 10-min ban.
armor_rule 1000 --expression="request.path == '/link'" --action=rate-based-ban \
    --rate-limit-threshold-count="$LINK_RATE_PER_MIN" --rate-limit-threshold-interval-sec=60 \
    --ban-duration-sec=600 --conform-action=allow --exceed-action=deny-429 --enforce-on-key=ip \
    --description="link: per-IP upgrade rate"
# Everything else: generous per-IP throttle (a class may share one campus NAT IP).
armor_rule 2000 --src-ip-ranges='*' --action=throttle \
    --rate-limit-threshold-count="$UI_RATE_PER_MIN" --rate-limit-threshold-interval-sec=60 \
    --conform-action=allow --exceed-action=deny-429 --enforce-on-key=ip \
    --description="UIs: per-IP throttle"

log "Backend services"
# be NAME PORTNAME HEALTHCHECK
# timeout 3600 s: for a global external ALB the backend timeout is also the
# longest a WebSocket may stay open. The consoles and the agent reconnect.
be() {  # be NAME PORTNAME HEALTHCHECK [INSTANCE-GROUP]
    local group="${4:-$IG}"
    if ! exists compute backend-services describe "$1" --global; then
        gcloud compute backend-services create "$1" --global --load-balancing-scheme=EXTERNAL_MANAGED \
            --protocol=HTTP --port-name="$2" --health-checks="$3" --timeout=3600s
    fi
    gcloud compute backend-services update "$1" --global --port-name="$2" --health-checks="$3" \
        --timeout=3600s --security-policy="$ARMOR" >/dev/null
    if ! gcloud compute backend-services describe "$1" --global --format='value(backends[].group)' \
            | grep -q "/instanceGroups/$group\$"; then
        gcloud compute backend-services add-backend "$1" --global --instance-group="$group" \
            --instance-group-zone="$ZONE" --balancing-mode=UTILIZATION --max-utilization=0.8
    fi
}
be "$BE_OPS"  mcs        "$HC_OPS"
be "$BE_PLAN" planner    "$HC_PLAN"
be "$BE_SIM"  instructor "$HC_SIM"
be "$BE_LINK" link       "$HC_LINK"
tool_be() {
    local group="$IG"; [ "$4" = sim ] && group="$IG_SIM"
    be "$PREFIX-be-$1" "$1" "$PREFIX-hc-$1" "$group"
}
tools_each tool_be

log "IAP on ops, plan, sim and the tool pages (Google-managed OAuth client: @$DOMAIN accounts only)"
tool_be_name() { printf '%s-be-%s\n' "$PREFIX" "$1"; }
for b in "$BE_OPS" "$BE_PLAN" "$BE_SIM" $(tools_each tool_be_name); do
    # No oauth2-client-id: IAP uses the Google-managed client.
    gcloud compute backend-services update "$b" --global --iap=enabled >/dev/null
done
# /link must NOT be behind IAP: the agent is not a browser; its HMAC proves it.
if [ "$(gcloud compute backend-services describe "$BE_LINK" --global --format='value(iap.enabled)')" = "True" ]; then
    gcloud compute backend-services update "$BE_LINK" --global --iap=disabled >/dev/null
fi
iap_grant() {  # iap_grant BACKEND GROUP
    gcloud iap web add-iam-policy-binding --resource-type=backend-services --service="$1" \
        --member="group:$2" --role=roles/iap.httpsResourceAccessor --condition=None >/dev/null
    info "$2 -> $1"
}
iap_grant "$BE_OPS"  "$STUDENTS_GROUP"
iap_grant "$BE_OPS"  "$INSTRUCTORS_GROUP"
iap_grant "$BE_PLAN" "$STUDENTS_GROUP"
iap_grant "$BE_PLAN" "$INSTRUCTORS_GROUP"
iap_grant "$BE_SIM"  "$INSTRUCTORS_GROUP"
tool_iap() {
    [ "$5" = all ] && iap_grant "$PREFIX-be-$1" "$STUDENTS_GROUP"
    iap_grant "$PREFIX-be-$1" "$INSTRUCTORS_GROUP"
}
tools_each tool_iap

# ── 6. Load balancer front end ──────────────────────────────────────────
log "URL map (host rules; only link.$DOMAIN/link reaches the IAP-off back end)"
bs() { printf 'https://www.googleapis.com/compute/v1/projects/%s/global/backendServices/%s' "$PROJECT" "$1"; }
ops_hosts="- $HOST_OPS"
[ "$INCLUDE_APEX" = "yes" ] && ops_hosts="$ops_hosts
    - $DOMAIN"
tool_hostrule() { printf '  - hosts:\n    - %s.%s\n    pathMatcher: %s\n' "$2" "$DOMAIN" "$1"; }
tool_matcher()  { printf '  - name: %s\n    defaultService: %s\n' "$1" "$(bs "$PREFIX-be-$1")"; }
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
cat > "$tmp/urlmap.yaml" <<EOF
name: $URLMAP
defaultService: $(bs "$BE_OPS")
hostRules:
  - hosts:
    $ops_hosts
    pathMatcher: ops
  - hosts:
    - $HOST_PLAN
    pathMatcher: plan
  - hosts:
    - $HOST_SIM
    pathMatcher: sim
  - hosts:
    - $HOST_LINK
    pathMatcher: link
$(tools_each tool_hostrule)
pathMatchers:
  - name: ops
    defaultService: $(bs "$BE_OPS")
  - name: plan
    defaultService: $(bs "$BE_PLAN")
  - name: sim
    defaultService: $(bs "$BE_SIM")
  - name: link
    # Any other path on link.$DOMAIN goes to the IAP-protected MCS.
    defaultService: $(bs "$BE_OPS")
    pathRules:
      - paths:
        - /link
        service: $(bs "$BE_LINK")
$(tools_each tool_matcher)
EOF
gcloud compute url-maps import "$URLMAP" --global --source="$tmp/urlmap.yaml" --quiet >/dev/null

cat > "$tmp/redirect.yaml" <<EOF
name: $REDIRECT_MAP
defaultUrlRedirect:
  httpsRedirect: true
  redirectResponseCode: MOVED_PERMANENTLY_DEFAULT
  stripQuery: false
EOF
gcloud compute url-maps import "$REDIRECT_MAP" --global --source="$tmp/redirect.yaml" --quiet >/dev/null

log "TLS: Google-managed certificate for $CERT_DOMAINS"
if ! exists compute ssl-policies describe "$SSL_POLICY" --global; then
    gcloud compute ssl-policies create "$SSL_POLICY" --global --profile=MODERN --min-tls-version=1.2
fi
if exists compute ssl-certificates describe "$CERT" --global; then
    have="$(gcloud compute ssl-certificates describe "$CERT" --global --format='value(managed.domains)' | tr ';' ',')"
    if [ "$(tr ',' '\n' <<<"$have" | sort | paste -sd,)" != "$(tr ',' '\n' <<<"$CERT_DOMAINS" | sort | paste -sd,)" ]; then
        warn "Certificate $CERT covers [$have] but c2o.env now wants [$CERT_DOMAINS]. A managed certificate's domains cannot change: see README Troubleshooting, 'Changing the certificate's names'."
    fi
else
    gcloud compute ssl-certificates create "$CERT" --global --domains="$CERT_DOMAINS"
fi
# The tool pages are on a second certificate: managed certificates cannot
# gain names, and a separate one leaves the main certificate untouched.
tool_host() { printf '%s.%s\n' "$2" "$DOMAIN"; }
want_tools="$(tools_each tool_host | paste -sd, -)"
if exists compute ssl-certificates describe "$CERT_TOOLS" --global; then
    have="$(gcloud compute ssl-certificates describe "$CERT_TOOLS" --global --format='value(managed.domains)' | tr ';' ',')"
    if [ "$(tr ',' '\n' <<<"$have" | sort | paste -sd,)" != "$(tr ',' '\n' <<<"$want_tools" | sort | paste -sd,)" ]; then
        warn "Certificate $CERT_TOOLS covers [$have] but the tool list wants [$want_tools]. Delete it (detach it first: rerun after 'gcloud compute target-https-proxies update $T_HTTPS --global --ssl-certificates=$CERT') and rerun setup.sh."
    fi
else
    log "TLS: second managed certificate for the tool pages ($want_tools)"
    gcloud compute ssl-certificates create "$CERT_TOOLS" --global --domains="$want_tools"
fi

if exists compute target-https-proxies describe "$T_HTTPS" --global; then
    gcloud compute target-https-proxies update "$T_HTTPS" --global --url-map="$URLMAP" \
        --ssl-certificates="$CERT,$CERT_TOOLS" --ssl-policy="$SSL_POLICY" >/dev/null
else
    gcloud compute target-https-proxies create "$T_HTTPS" --global --url-map="$URLMAP" \
        --ssl-certificates="$CERT,$CERT_TOOLS" --ssl-policy="$SSL_POLICY"
fi
if ! exists compute target-http-proxies describe "$T_HTTP" --global; then
    gcloud compute target-http-proxies create "$T_HTTP" --global --url-map="$REDIRECT_MAP"
fi

if ! exists compute addresses describe "$LB_IP" --global; then
    gcloud compute addresses create "$LB_IP" --global --ip-version=IPV4 --network-tier=PREMIUM
fi
ensure_forwarding_rules

# ── Done ────────────────────────────────────────────────────────────────
ip="$(gcloud compute addresses describe "$LB_IP" --global --format='value(address)')"
log "Setup finished."
cat <<EOF

    Load balancer IP: $ip

    Add these A records at Squarespace (README step 6), TTL 1 hour or less:

        Name (host)   Type   Data
EOF
[ "$INCLUDE_APEX" = "yes" ] && printf '        %-13s A      %s\n' "@" "$ip"
for h in ops plan sim link; do printf '        %-13s A      %s\n' "$h" "$ip"; done
tool_dns() { printf '        %-13s A      %s\n' "$2" "$ip"; }
tools_each tool_dns
cat <<EOF

    Then watch the certificates (README step 7):
        gcloud compute ssl-certificates describe $CERT --global --format='yaml(managed)'
        gcloud compute ssl-certificates describe $CERT_TOOLS --global --format='yaml(managed)'

    The VMs are booting and building the image now (10-15 min). Progress:
        gcloud compute instances get-serial-port-output $VM_GROUND --zone=$ZONE | grep c2o-bootstrap
EOF
