#!/usr/bin/env bash
# Class day: bring C2O up.
#
#   bash deploy/gcp/start.sh                # simulator per SIM_MODE in c2o.env
#   bash deploy/gcp/start.sh --sim=cloud    # ground VM + cloud simulator VM
#   bash deploy/gcp/start.sh --sim=laptop   # ground VM only; STOPS the sim VM
#                                           # (your laptop runs the simulator)
#   bash deploy/gcp/start.sh --no-wait      # don't wait for the health checks
#
# Only ONE simulator may be connected: a second agent supersedes the first,
# and the first reconnects and supersedes back, every few seconds. So
# --sim=laptop always stops the cloud sim VM, and you must stop your laptop
# simulator before --sim=cloud.
set -euo pipefail
# shellcheck source=common.sh
. "$(dirname "$0")/common.sh"

sim="$SIM_MODE"; wait=yes
for a in "$@"; do
    case "$a" in
        --sim=cloud|--sim=laptop|--sim=none) sim="${a#--sim=}" ;;
        --no-wait) wait=no ;;
        -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
        *) die "unknown option $a (see --help)" ;;
    esac
done
[ "$sim" = cloud ] || [ "$sim" = laptop ] || [ "$sim" = none ] || die "SIM_MODE must be cloud or laptop"
require_gcloud_login

log "Load balancer front end"
ensure_forwarding_rules     # recreates the forwarding rules if stop.sh --lb removed them

start_vm() {
    local s; s="$(vm_status "$1")"
    case "$s" in
        RUNNING) info "$1 already running" ;;
        NONE)    die "$1 does not exist: run setup.sh" ;;
        *)       info "starting $1 ($s)"; gcloud compute instances start "$1" --zone="$ZONE" ;;
    esac
}
stop_vm() {
    local s; s="$(vm_status "$1")"
    case "$s" in
        RUNNING|PROVISIONING|STAGING) info "stopping $1 (only one simulator may be connected)"
                                      gcloud compute instances stop "$1" --zone="$ZONE" ;;
        *) ;;
    esac
}

log "VMs"
start_vm "$VM_GROUND"
# Voice loops server (LiveKit), if setup.sh created it.
if [ "$CREATE_VOICE_VM" = yes ] && [ "$(vm_status "$VM_VOICE")" != NONE ]; then start_vm "$VM_VOICE"; fi
case "$sim" in
    cloud)  start_vm "$VM_SIM" ;;
    *)      [ "$(vm_status "$VM_SIM")" = NONE ] || stop_vm "$VM_SIM" ;;
esac

if [ "$wait" = yes ]; then
    log "Waiting for the load balancer to see the ground VM as healthy (usually 2-4 min after boot)"
    for _ in $(seq 1 60); do
        states="$(for b in "$BE_PORTAL" "$BE_OPS" "$BE_PLAN" "$BE_SIM" "$BE_LINK"; do
            gcloud compute backend-services get-health "$b" --global \
                --format='value(status.healthStatus[0].healthState)' 2>/dev/null || echo UNKNOWN
        done | paste -sd' ' -)"  # '-': macOS paste needs the operand
        info "welcome ops plan sim link: $states"
        case "$states" in *UNHEALTHY*|*UNKNOWN*|"") sleep 10 ;; *) break ;; esac
    done
fi

log "Ready"
if [ "$INCLUDE_APEX" = yes ]; then
    printf '    %-17s https://%-14s (students + instructors; links to every screen below)\n' "Welcome page" "$DOMAIN"
fi
cat <<EOF
    MCS               https://$HOST_OPS       (students + instructors)
    Planner           https://$HOST_PLAN      (students + instructors)
    Instructor sim    https://$HOST_SIM       (instructors only)
    Link status       https://$HOST_SIM/link-status    (UP once a simulator is connected)
EOF
if [ "$CREATE_VOICE_VM" = yes ] && [ "$(vm_status "$VM_VOICE")" != NONE ]; then
    printf '    %-17s https://%s/voice  (or the Voice button in the MCS header; server wss://%s)\n' \
        "Voice loops" "$HOST_OPS" "$HOST_VOICE"
fi
while read -r key label _port where who title; do
    [ -n "$key" ] || continue
    [ "$where" = sim ] && [ "$sim" != cloud ] && continue
    printf '    %-20s https://%-22s (%s)\n' "$title" "$label.$DOMAIN" \
        "$([ "$who" = all ] && echo 'students + instructors' || echo 'instructors only')"
done <<<"$TOOLS"
[ "$sim" = cloud ] || echo "    (the scenario generator and ADCS viewer run with the simulator: on a laptop, localhost:8096 and :8097)"
if [ "$sim" = laptop ]; then
    cat <<EOF

    Now start the simulator on your laptop (README step 9), from C2O/sim:
        SMO_LINK_URL=wss://$HOST_LINK/link SMO_PROFILE=space ./start.sh
EOF
fi
