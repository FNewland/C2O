#!/usr/bin/env bash
# After class: stop paying for the VMs.
#
#   bash deploy/gcp/stop.sh            # stop both VMs (disks and data are kept)
#   bash deploy/gcp/stop.sh --sim      # stop only the cloud simulator VM
#   bash deploy/gcp/stop.sh --lb       # ALSO delete the two LB forwarding rules
#                                      # (net saving ~USD 0.015/h, about USD 11/month:
#                                      # the rules cost 0.025/h, but the kept IP then
#                                      # costs 0.01/h unattached. start.sh recreates
#                                      # them; IP, certificate and config are kept)
#
# A stopped VM costs only its disk. Everything else (IP, cert, IAP, Armor
# policy, URL map) stays, so start.sh brings the site back in a few minutes.
set -euo pipefail
# shellcheck source=common.sh
. "$(dirname "$0")/common.sh"

only_sim=no; lb=no
for a in "$@"; do
    case "$a" in
        --sim) only_sim=yes ;;
        --lb)  lb=yes ;;
        -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
        *) die "unknown option $a (see --help)" ;;
    esac
done
require_gcloud_login

stop_vm() {
    local s; s="$(vm_status "$1")"
    case "$s" in
        NONE|TERMINATED|STOPPING|SUSPENDED) info "$1: $s" ;;
        *) info "stopping $1"; gcloud compute instances stop "$1" --zone="$ZONE" --async ;;
    esac
}

log "Stopping VMs"
stop_vm "$VM_SIM"
[ "$only_sim" = yes ] || stop_vm "$VM_GROUND"

if [ "$lb" = yes ]; then
    log "Deleting the LB forwarding rules (the site is offline until start.sh)"
    for fr in "$FR_HTTPS" "$FR_HTTP"; do
        if exists compute forwarding-rules describe "$fr" --global; then
            gcloud compute forwarding-rules delete "$fr" --global --quiet
        fi
    done
fi
log "Done. Check:  gcloud compute instances list"
