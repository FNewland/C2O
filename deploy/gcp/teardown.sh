#!/usr/bin/env bash
# Delete everything setup.sh created in the project (VMs and their disks,
# load balancer, IP, certificate, Armor policy, network, secret, service
# accounts). The project itself, billing and Cloud Identity are left alone.
#
#   bash deploy/gcp/teardown.sh
#
# THIS DELETES THE VM DISKS: the MCS TM archive, dumps and reports are gone.
# Copy anything you want first (README step 13).
# Even simpler, if the project holds nothing else:  gcloud projects delete PROJECT
set -euo pipefail
# shellcheck source=common.sh
. "$(dirname "$0")/common.sh"
require_gcloud_login

printf '\nThis permanently deletes the C2O deployment in project %s.\nType the project id to confirm: ' "$PROJECT"
read -r answer
[ "$answer" = "$PROJECT" ] || die "not confirmed; nothing deleted"

del() {  # del <describe-args...> -- <delete-args...>
    local d=() x=()
    while [ "$1" != -- ]; do d+=("$1"); shift; done; shift
    x=("$@")
    if exists "${d[@]}"; then info "deleting: ${x[*]}"; gcloud "${x[@]}" --quiet; fi
}

log "Load balancer front end"
del compute forwarding-rules describe "$FR_HTTPS" --global -- compute forwarding-rules delete "$FR_HTTPS" --global
del compute forwarding-rules describe "$FR_HTTP" --global -- compute forwarding-rules delete "$FR_HTTP" --global
del compute target-https-proxies describe "$T_HTTPS" --global -- compute target-https-proxies delete "$T_HTTPS" --global
del compute target-http-proxies describe "$T_HTTP" --global -- compute target-http-proxies delete "$T_HTTP" --global
del compute url-maps describe "$URLMAP" --global -- compute url-maps delete "$URLMAP" --global
del compute url-maps describe "$REDIRECT_MAP" --global -- compute url-maps delete "$REDIRECT_MAP" --global
del compute ssl-certificates describe "$CERT" --global -- compute ssl-certificates delete "$CERT" --global
for c in $(gcloud compute ssl-certificates list --global --filter="name ~ ^$CERT_TOOLS_PREFIX" --format='value(name)' 2>/dev/null); do
    del compute ssl-certificates describe "$c" --global -- compute ssl-certificates delete "$c" --global
done
del compute ssl-policies describe "$SSL_POLICY" --global -- compute ssl-policies delete "$SSL_POLICY" --global
del compute addresses describe "$LB_IP" --global -- compute addresses delete "$LB_IP" --global

log "Load balancer back end"
tool_keys="$(awk 'NF{print $1}' <<<"$TOOLS")"
# shellcheck disable=SC2086  # tool_keys is a plain word list
for b in "$BE_PORTAL" "$BE_OPS" "$BE_PLAN" "$BE_SIM" "$BE_LINK" $(printf "$PREFIX-be-%s " $tool_keys); do
    del compute backend-services describe "$b" --global -- compute backend-services delete "$b" --global
done
# shellcheck disable=SC2086
for h in "$HC_PORTAL" "$HC_OPS" "$HC_PLAN" "$HC_SIM" "$HC_LINK" $(printf "$PREFIX-hc-%s " $tool_keys); do
    del compute health-checks describe "$h" --global -- compute health-checks delete "$h" --global
done
del compute security-policies describe "$ARMOR" -- compute security-policies delete "$ARMOR"
for g in "$IG" "$IG_SIM"; do
    del compute instance-groups unmanaged describe "$g" --zone="$ZONE" -- compute instance-groups unmanaged delete "$g" --zone="$ZONE"
done

log "VMs (and their boot disks)"
for v in "$VM_GROUND" "$VM_SIM"; do
    del compute instances describe "$v" --zone="$ZONE" -- compute instances delete "$v" --zone="$ZONE" --delete-disks=all
done
# The automatic start/stop schedule (c2o schedule). Disk snapshots
# (c2o data snapshot) are NOT deleted: c2o data prune --keep 0 removes them.
del compute resource-policies describe "$PREFIX-schedule" --region="$REGION" -- compute resource-policies delete "$PREFIX-schedule" --region="$REGION"
for a in "$ADDR_GROUND_INT" "$ADDR_SIM_INT"; do
    del compute addresses describe "$a" --region="$REGION" -- compute addresses delete "$a" --region="$REGION"
done

log "Network"
del compute routers nats describe "$NAT" --router="$ROUTER" --region="$REGION" -- compute routers nats delete "$NAT" --router="$ROUTER" --region="$REGION"
del compute routers describe "$ROUTER" --region="$REGION" -- compute routers delete "$ROUTER" --region="$REGION"
for f in "$FW_LB" "$FW_LB_SIM" "$FW_PORTAL_SIM" "$FW_IAP" "$FW_SIM"; do
    del compute firewall-rules describe "$f" -- compute firewall-rules delete "$f"
done
del compute networks subnets describe "$SUBNET" --region="$REGION" -- compute networks subnets delete "$SUBNET" --region="$REGION"
del compute networks describe "$NET" -- compute networks delete "$NET"

log "Secret and service accounts"
del secrets describe "$SECRET" -- secrets delete "$SECRET"
del secrets describe "$SECRET_AI" -- secrets delete "$SECRET_AI"
for sa in "$SA_GROUND_EMAIL" "$SA_SIM_EMAIL"; do
    del iam service-accounts describe "$sa" -- iam service-accounts delete "$sa"
done

log "Teardown finished. Left in place: the project, its billing link, the IAP"
info "settings, the Squarespace DNS records and Cloud Identity (users, groups, 2SV)."
info "Remove the DNS A records at Squarespace so the names stop pointing at a released IP."
