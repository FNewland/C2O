# shellcheck shell=bash disable=SC2034  # names below are used by the scripts that source this
# Shared settings and helpers for the C2O Google Cloud scripts.
# Sourced by setup.sh, start.sh, stop.sh, rotate-link-secret.sh, teardown.sh.

GCP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$GCP_DIR/../.." && pwd)"

log()  { printf '\n==> %s\n' "$*"; }
info() { printf '    %s\n' "$*"; }
warn() { printf '\n!!  %s\n' "$*" >&2; }
die()  { printf '\nERROR: %s\n' "$*" >&2; exit 1; }

# ── Settings ────────────────────────────────────────────────────────────
C2O_ENV="${C2O_ENV:-$GCP_DIR/c2o.env}"
[ -f "$C2O_ENV" ] || die "$C2O_ENV not found. Run:  cp $GCP_DIR/c2o.env.example $GCP_DIR/c2o.env  and edit PROJECT."
# shellcheck source=c2o.env.example
. "$C2O_ENV"

: "${PROJECT:?set PROJECT in c2o.env}"
: "${REGION:?set REGION in c2o.env}"
: "${ZONE:?set ZONE in c2o.env}"
: "${DOMAIN:?set DOMAIN in c2o.env}"
: "${INSTRUCTORS_GROUP:?set INSTRUCTORS_GROUP in c2o.env}"
: "${STUDENTS_GROUP:?set STUDENTS_GROUP in c2o.env}"
INCLUDE_APEX="${INCLUDE_APEX:-yes}"
SIM_MODE="${SIM_MODE:-cloud}"
RF_MODE="${RF_MODE:-FRAME}"
case "$RF_MODE" in FRAME|RF) ;; *) die "RF_MODE in c2o.env must be FRAME or RF (got $RF_MODE)" ;; esac
REPO_URL="${REPO_URL:-https://github.com/FNewland/C2O.git}"
REPO_REF="${REPO_REF:-main}"
GROUND_MACHINE_TYPE="${GROUND_MACHINE_TYPE:-e2-standard-2}"
SIM_MACHINE_TYPE="${SIM_MACHINE_TYPE:-e2-standard-2}"
BOOT_DISK_GB="${BOOT_DISK_GB:-30}"
SUBNET_RANGE="${SUBNET_RANGE:-10.20.0.0/24}"
GROUND_IP="${GROUND_IP:-10.20.0.10}"
SIM_IP="${SIM_IP:-10.20.0.11}"
CREATE_SIM_VM="${CREATE_SIM_VM:-yes}"
UI_RATE_PER_MIN="${UI_RATE_PER_MIN:-6000}"
LINK_RATE_PER_MIN="${LINK_RATE_PER_MIN:-30}"
PREFIX="${PREFIX:-c2o}"

# Every gcloud call goes to this project, whatever the Cloud Shell default is.
export CLOUDSDK_CORE_PROJECT="$PROJECT"

# Every gcloud call in these scripts goes through this wrapper. A dropped
# connection (timeout, reset, TLS EOF: "gcloud crashed (...Error)") is
# retried up to 4 times with a growing pause, so a flaky network does not
# stop setup.sh halfway. Real errors (permissions, bad arguments) are not
# retried: they fail at once as before.
#
# The real binary is called by its path, not as `command gcloud`: under
# macOS bash 3.2 a failing `command X || ...` still ends a `set -e` script,
# so every "does it exist?" check that answered no would stop the script.
gcloud() {
    local n=0 rc errf bin
    bin="$(type -P gcloud)" || { echo "gcloud not found on PATH" >&2; return 127; }
    errf="$(mktemp)"
    while :; do
        rc=0
        "$bin" "$@" 2>"$errf" || rc=$?
        if [ "$rc" -ne 0 ] && [ "$n" -lt 4 ] && grep -qE \
            'gcloud crashed \((ConnectTimeout|ConnectionError|SSLError|ReadTimeout|RemoteDisconnected|ProtocolError)|Connection (aborted|reset)|timed out' "$errf"; then
            n=$((n + 1))
            printf '    (network dropped; retrying in %s s, attempt %s of 4)\n' "$((n * 10))" "$n" >&2
            sleep "$((n * 10))"
            continue
        fi
        cat "$errf" >&2; rm -f "$errf"
        return "$rc"
    done
}

# ── Resource names ──────────────────────────────────────────────────────
NET="$PREFIX-vpc"
SUBNET="$PREFIX-subnet"
ROUTER="$PREFIX-router"
NAT="$PREFIX-nat"
FW_LB="$PREFIX-allow-lb"
FW_IAP="$PREFIX-allow-iap-ssh"
FW_SIM="$PREFIX-allow-sim-link"
FW_LB_SIM="$PREFIX-allow-lb-sim"
FW_PORTAL_SIM="$PREFIX-allow-portal-probe"
TAG_GROUND="$PREFIX-ground"
TAG_SIM="$PREFIX-sim"
SA_GROUND="$PREFIX-ground"
SA_SIM="$PREFIX-sim"
SA_GROUND_EMAIL="$SA_GROUND@$PROJECT.iam.gserviceaccount.com"
SA_SIM_EMAIL="$SA_SIM@$PROJECT.iam.gserviceaccount.com"
SECRET="$PREFIX-link-session"
ADDR_GROUND_INT="$PREFIX-ground-int"
ADDR_SIM_INT="$PREFIX-sim-int"
VM_GROUND="$PREFIX-ground-vm"
VM_SIM="$PREFIX-sim-vm"
IG="$PREFIX-ground-ig"
IG_SIM="$PREFIX-sim-ig"
HC_OPS="$PREFIX-hc-ops"
HC_PLAN="$PREFIX-hc-plan"
HC_SIM="$PREFIX-hc-sim"
HC_LINK="$PREFIX-hc-link"
HC_PORTAL="$PREFIX-hc-portal"
BE_OPS="$PREFIX-be-ops"
BE_PLAN="$PREFIX-be-plan"
BE_SIM="$PREFIX-be-sim"
BE_LINK="$PREFIX-be-link"
BE_PORTAL="$PREFIX-be-portal"
ARMOR="$PREFIX-armor"
URLMAP="$PREFIX-urlmap"
REDIRECT_MAP="$PREFIX-http-redirect"
CERT="$PREFIX-cert"
SECRET_AI="$PREFIX-anthropic-key"
SSL_POLICY="$PREFIX-tls"
T_HTTPS="$PREFIX-https-proxy"
T_HTTP="$PREFIX-http-proxy"
LB_IP="$PREFIX-lb-ip"
FR_HTTPS="$PREFIX-fr-https"
FR_HTTP="$PREFIX-fr-http"

HOST_OPS="ops.$DOMAIN"
HOST_PLAN="plan.$DOMAIN"
HOST_SIM="sim.$DOMAIN"
HOST_LINK="link.$DOMAIN"
CERT_DOMAINS="$HOST_OPS,$HOST_PLAN,$HOST_SIM,$HOST_LINK"
[ "$INCLUDE_APEX" = "yes" ] && CERT_DOMAINS="$DOMAIN,$CERT_DOMAINS"

# Tool pages, one host each (the tools use root-relative URLs, so each needs
# its own host rather than a path prefix). Fields:
#   key  host-label  port  where(ground|sim)  who(all|instructors)  title
# "all" = students + instructors. Ground tools run on the ground VM; the
# instructor tools run next to the simulator on the sim VM (the scenario
# generator must write where the simulator reads).
TOOLS="
tm        tm         8092 ground all         Delayed-TM viewer
orbit     orbit      8093 ground all         Orbit tools
radio     radio      8094 ground all         Radio view (RF bridge)
docs      docs       8095 ground all         Documentation
design    design     8000 ground all         SpaceCDF design tool
scenarios scenarios  8096 sim    instructors Scenario generator
adcs      adcs       8097 sim    instructors ADCS failure viewer
"
# On their own certificate, so adding them never re-provisions the main one.
# A managed certificate cannot gain names, so its name carries a hash of its
# name list: changing the list makes setup.sh create a new certificate, swap
# it in and delete the old one.
TOOL_HOSTS="$(awk 'NF{printf "%s%s.'"$DOMAIN"'", (n++?",":""), $2}' <<<"$TOOLS")"
CERT_TOOLS_PREFIX="$PREFIX-cert-tools"

# ── Helpers ─────────────────────────────────────────────────────────────
# exists <gcloud args...>: true if `gcloud <args> --format=value(name)` succeeds.
exists() { gcloud "$@" --format='value(name)' >/dev/null 2>&1; }

vm_status() {  # vm_status NAME -> RUNNING / TERMINATED / ... / NONE
    gcloud compute instances describe "$1" --zone="$ZONE" --format='value(status)' 2>/dev/null || echo NONE
}

require_gcloud_login() {
    command -v gcloud >/dev/null || die "gcloud not found. Run this in Google Cloud Shell."
    local acct
    acct="$(gcloud config get-value account 2>/dev/null || true)"
    [ -n "$acct" ] || die "gcloud is not signed in. In Cloud Shell sign in to the console as your @$DOMAIN admin, or run: gcloud auth login"
    case "$acct" in
        *@"$DOMAIN") ;;
        *) warn "gcloud is signed in as $acct, not an @$DOMAIN account. The project lives in the $DOMAIN organisation; if a step fails with PERMISSION_DENIED, open Cloud Shell from the console while signed in as your @$DOMAIN admin." ;;
    esac
    gcloud projects describe "$PROJECT" --format='value(projectId)' >/dev/null 2>&1 \
        || die "Project $PROJECT not found (or no access). Create it first: README step 4."
}

# The two LB forwarding rules (the only LB parts billed by the hour that
# stop.sh --lb removes). Needs the IP and both target proxies to exist.
ensure_forwarding_rules() {
    if ! exists compute forwarding-rules describe "$FR_HTTPS" --global; then
        info "creating $FR_HTTPS (443)"
        gcloud compute forwarding-rules create "$FR_HTTPS" --global \
            --load-balancing-scheme=EXTERNAL_MANAGED --network-tier=PREMIUM \
            --address="$LB_IP" --target-https-proxy="$T_HTTPS" --ports=443
    fi
    if ! exists compute forwarding-rules describe "$FR_HTTP" --global; then
        info "creating $FR_HTTP (80, redirects to https)"
        gcloud compute forwarding-rules create "$FR_HTTP" --global \
            --load-balancing-scheme=EXTERNAL_MANAGED --network-tier=PREMIUM \
            --address="$LB_IP" --target-http-proxy="$T_HTTP" --ports=80
    fi
}

ssh_vm() {  # ssh_vm VM 'command'   (IAP tunnel; the VMs have no external IP)
    gcloud compute ssh "$1" --zone="$ZONE" --tunnel-through-iap --command="$2"
}
