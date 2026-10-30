#!/usr/bin/env bash
# C2O VM bootstrap: the startup script of both VMs (setup.sh installs it as
# instance metadata). It runs as root on EVERY boot and is idempotent:
#
#   1. install Docker Engine + the compose plugin (first boot only)
#   2. clone C2O into /opt/c2o (first boot only; later updates: `update`)
#   3. fetch the link credentials from Secret Manager (the ground VM creates
#      them if the secret has no version yet; the sim VM waits for them)
#   4. write sim/docker/ground.env or space.env from deploy/gcp/env/*.example
#   5. docker compose up -d --build with the right profile
#
# Instance metadata it reads (set by setup.sh):
#   c2o-role       ground | sim
#   c2o-repo       git URL          c2o-ref     branch or tag
#   c2o-domain     c2o.live         c2o-ground-ip  ground VM internal IP
#   c2o-secret     Secret Manager secret holding SMO_LINK_SESSION/SECRET
#
# By hand on a VM (gcloud compute ssh ... --tunnel-through-iap):
#   sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh            # same as a boot
#   sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh refresh    # re-read secret, recreate containers
#   sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh rotate     # ground only: NEW credentials
#   sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh update     # git pull c2o-ref, rebuild, restart
#   sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh down       # stop the containers
set -euo pipefail
shopt -s inherit_errexit

ACTION="${1:-boot}"
APP_DIR="${C2O_APP_DIR:-/opt/c2o}"     # override only for offline tests
SIM_DIR="$APP_DIR/sim"
MD=http://metadata.google.internal/computeMetadata/v1

say() { echo "c2o-bootstrap: $*" >&2; logger -t c2o-bootstrap -- "$*" 2>/dev/null || true; }
die() { say "ERROR: $*"; exit 1; }

md()   { curl -fsS -H 'Metadata-Flavor: Google' "$MD/$1"; }
attr() { md "instance/attributes/$1" 2>/dev/null || printf '%s' "${2:-}"; }

ROLE="$(attr c2o-role)"
REPO="$(attr c2o-repo https://github.com/FNewland/C2O.git)"
REF="$(attr c2o-ref main)"
DOMAIN="$(attr c2o-domain c2o.live)"
GROUND_IP="$(attr c2o-ground-ip)"
SECRET="$(attr c2o-secret c2o-link-session)"
PROJECT="$(md project/project-id)"
MY_IP="$(md instance/network-interfaces/0/ip)"

case "$ROLE" in
    ground) PROFILE=ground; ENV_NAME=ground.env ;;
    sim)    PROFILE=space;  ENV_NAME=space.env ;;
    *)      die "instance metadata c2o-role must be 'ground' or 'sim' (got '$ROLE')" ;;
esac
ENV_FILE="$SIM_DIR/docker/$ENV_NAME"

# ── Docker ──────────────────────────────────────────────────────────────
install_docker() {
    if command -v docker >/dev/null && docker compose version >/dev/null 2>&1; then
        return
    fi
    say "installing Docker Engine and the compose plugin"
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -q
    apt-get install -y -q ca-certificates curl git python3
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    # shellcheck disable=SC1091
    codename="$(. /etc/os-release && echo "$VERSION_CODENAME")"
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $codename stable" \
        > /etc/apt/sources.list.d/docker.list
    apt-get update -q
    apt-get install -y -q docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable --now docker
}

# ── Code ────────────────────────────────────────────────────────────────
clone_repo() {
    if [ -d "$APP_DIR/.git" ]; then return; fi
    say "cloning $REPO ($REF) into $APP_DIR"
    git clone --branch "$REF" "$REPO" "$APP_DIR"
}
update_repo() {
    say "updating $APP_DIR to the latest $REF"
    git -C "$APP_DIR" fetch --prune origin
    git -C "$APP_DIR" checkout "$REF"
    git -C "$APP_DIR" pull --ff-only origin "$REF"
}

# ── Secret Manager (REST with the VM's service-account token; no gcloud needed) ──
SM="https://secretmanager.googleapis.com/v1/projects/$PROJECT/secrets/$SECRET"
token() {
    md instance/service-accounts/default/token \
        | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])'
}
# secret_get: credentials on stdout; exit 3 if the secret has no version yet.
secret_get() {
    local body code
    body="$(mktemp)"
    code="$(curl -sS -o "$body" -w '%{http_code}' -H "Authorization: Bearer $(token)" \
        "$SM/versions/latest:access")" || { rm -f "$body"; return 1; }
    if [ "$code" = 200 ]; then
        python3 -c 'import base64,json,sys; sys.stdout.write(base64.b64decode(json.load(open(sys.argv[1]))["payload"]["data"]).decode())' "$body"
        rm -f "$body"; return 0
    fi
    if [ "$code" = 404 ] || { [ "$code" = 400 ] && grep -q FAILED_PRECONDITION "$body"; }; then
        rm -f "$body"; return 3        # no (enabled) version yet
    fi
    say "Secret Manager answered HTTP $code: $(head -c 300 "$body")"
    rm -f "$body"; return 1
}
secret_add() {  # secret_add < payload
    local b64 code body
    b64="$(base64 -w0)"
    body="$(mktemp)"
    code="$(curl -sS -o "$body" -w '%{http_code}' -X POST -H "Authorization: Bearer $(token)" \
        -H 'Content-Type: application/json' \
        -d "{\"payload\":{\"data\":\"$b64\"}}" "$SM:addVersion")"
    [ "$code" = 200 ] || { say "addVersion failed, HTTP $code: $(head -c 300 "$body")"; rm -f "$body"; return 1; }
    rm -f "$body"
}
new_creds() {
    python3 -c 'import secrets
print("SMO_LINK_SESSION=s-" + secrets.token_hex(8))
print("SMO_LINK_SECRET=" + secrets.token_hex(32))'
}
# get_creds: validated credential lines on stdout.
get_creds() {
    local creds rc
    for _ in $(seq 1 90); do      # the sim VM may boot before the ground VM wrote them
        rc=0; creds="$(secret_get)" || rc=$?
        if [ "$rc" = 0 ]; then break; fi
        if [ "$rc" = 3 ] && [ "$ROLE" = ground ]; then
            say "secret $SECRET has no version: creating the first link credentials"
            new_creds | secret_add
            continue
        fi
        if [ "$rc" = 3 ]; then
            say "waiting for the ground VM to create the link credentials (secret $SECRET)"
        fi
        sleep 10
    done
    [ -n "${creds:-}" ] || die "could not read the link credentials from Secret Manager ($SECRET)"
    # Keep only the two expected keys, with the expected shapes.
    printf '%s\n' "$creds" | tr -d '\r' \
        | grep -E '^SMO_LINK_SESSION=[A-Za-z0-9._-]{1,64}$|^SMO_LINK_SECRET=[0-9a-fA-F]{64,}$' \
        | sort -u
}

# ── Env file ────────────────────────────────────────────────────────────
write_env() {
    local tmpl="$APP_DIR/deploy/gcp/env/$ENV_NAME.example" creds tmp
    [ -f "$tmpl" ] || die "$tmpl missing: push deploy/gcp/ to $REPO ($REF) before booting the VMs"
    creds="$(get_creds)"
    [ "$(grep -c . <<<"$creds")" = 2 ] || die "secret $SECRET must hold SMO_LINK_SESSION=... and SMO_LINK_SECRET=<64+ hex>"
    tmp="$(mktemp "$ENV_FILE.XXXX")"
    chmod 600 "$tmp"
    {
        sed -e "s|@DOMAIN@|$DOMAIN|g" -e "s|@GROUND_IP@|$GROUND_IP|g" -e "s|@MY_IP@|$MY_IP|g" "$tmpl" \
            | grep -v -E '^SMO_LINK_(SESSION|SECRET)='
        echo
        echo "# From Secret Manager ($SECRET), written by vm-bootstrap.sh $(date -u +%FT%TZ)"
        printf '%s\n' "$creds"
    } > "$tmp"
    mv -f "$tmp" "$ENV_FILE"
    say "wrote $ENV_FILE (session $(sed -n 's/^SMO_LINK_SESSION=//p' "$ENV_FILE"))"
}

# ── Compose ─────────────────────────────────────────────────────────────
compose() {
    # --env-file: the compose file interpolates SMO_PUBLISH_ADDR (and the
    # image tag) from it; env_file inside compose.yaml only reaches the
    # containers, not the `ports:` lines.
    (cd "$SIM_DIR" && SMO_CONFIG_HASH="$(sh docker/config-hash.sh)" \
        docker compose --env-file "docker/$ENV_NAME" -f docker/compose.yaml --profile "$PROFILE" "$@")
}
up() {
    say "docker compose --profile $PROFILE up (first build: several minutes)"
    compose up -d --build --remove-orphans
    compose ps
}

case "$ACTION" in
    boot)
        install_docker; clone_repo; write_env; up ;;
    refresh)
        write_env; up ;;
    rotate)
        [ "$ROLE" = ground ] || die "rotate runs on the ground VM only (the sim VM then runs: refresh)"
        say "issuing NEW link credentials"
        new_creds | secret_add
        write_env; up ;;
    update)
        update_repo; write_env; up ;;
    down)
        compose down ;;
    *)
        die "usage: vm-bootstrap.sh [boot|refresh|rotate|update|down]" ;;
esac
say "done ($ACTION, role $ROLE, $MY_IP)"
