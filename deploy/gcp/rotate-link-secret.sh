#!/usr/bin/env bash
# Issue NEW link credentials (session id + secret) and roll them out.
#
#   bash deploy/gcp/rotate-link-secret.sh
#
# 1. The ground VM generates the new pair, stores it as a new Secret Manager
#    version and restarts the ground containers with it (the TM archive and
#    dumps are on volumes and survive; open browser sessions reconnect).
# 2. If the cloud sim VM is running, it re-reads the secret and restarts.
#    (A stopped sim VM picks the new pair up on its next boot.)
# 3. Older versions are disabled, so the old secret no longer works anywhere.
# 4. A laptop simulator must fetch the new session.env (README step 9).
set -euo pipefail
# shellcheck source=common.sh
. "$(dirname "$0")/common.sh"
require_gcloud_login

[ "$(vm_status "$VM_GROUND")" = RUNNING ] || die "$VM_GROUND is not running: bash deploy/gcp/start.sh first"

log "New credentials on $VM_GROUND"
ssh_vm "$VM_GROUND" 'sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh rotate'

if [ "$(vm_status "$VM_SIM")" = RUNNING ]; then
    log "Restarting the cloud simulator with them"
    ssh_vm "$VM_SIM" 'sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh refresh'
fi

log "Disabling older secret versions"
latest="$(gcloud secrets versions describe latest --secret="$SECRET" --format='value(name)')"
latest="${latest##*/}"
for v in $(gcloud secrets versions list "$SECRET" --filter='state=ENABLED' --format='value(name)'); do
    v="${v##*/}"
    [ "$v" = "$latest" ] || gcloud secrets versions disable "$v" --secret="$SECRET" --quiet
done
info "current version: $latest"
cat <<EOF

    Laptop simulator? Fetch the new pair (README step 9):
        gcloud secrets versions access latest --secret=$SECRET > session.env
EOF
