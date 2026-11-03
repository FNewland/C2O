#!/usr/bin/env bash
# C2O VM bootstrap: the startup script of both VMs (setup.sh installs it as
# instance metadata). It runs as root on EVERY boot and is idempotent:
#
#   1. install Docker Engine + the compose plugin (first boot only)
#   2. clone C2O into /opt/c2o (first boot only; later updates: `update`)
#   3. fetch the link credentials from Secret Manager (the ground VM creates
#      them if the secret has no version yet; the sim VM waits for them)
#   4. write sim/docker/ground.env or space.env from deploy/gcp/env/*.example
#   5. docker compose up -d --build with the right profiles (ground + rf, or space)
#
# Instance metadata it reads (set by setup.sh):
#   c2o-role       ground | sim
#   c2o-repo       git URL          c2o-ref     branch or tag
#   c2o-domain     c2o.live         c2o-ground-ip  ground VM internal IP
#   c2o-secret     Secret Manager secret holding SMO_LINK_SESSION/SECRET
#   c2o-rf-mode    FRAME | RF: the ground VM's RF bridge mode (radio view)
#   c2o-ai-secret  Secret Manager secret holding the Anthropic API key for
#                  SpaceCDF's AI advisor (ground VM; optional: no version =
#                  SpaceCDF runs in manual mode)
#   c2o-voice-secret, c2o-voice-host, c2o-voice-instructors, c2o-instructors
#                  voice loops (ground VM; optional): the LiveKit key pair the
#                  MCS signs tokens with, the voice server's name, and the
#                  accounts with the instructor role -> sim/docker/voice.env
#
# By hand on a VM (gcloud compute ssh ... --tunnel-through-iap):
#   sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh            # same as a boot
#   sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh refresh    # re-read secret, recreate containers
#   sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh rotate     # ground only: NEW credentials
#   sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh update     # git pull c2o-ref, rebuild, restart
#   sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh down       # stop the containers
#   sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh sizes      # size of each data volume (c2o data list)
#   sudo bash /opt/c2o/deploy/gcp/vm-bootstrap.sh clean telemetry dumps reports [designs] [logbooks]
#        empty those recording volumes on this VM: stops the containers that
#        use them, deletes the files with the already-built image (no pulls),
#        starts them again. Never touches scenarios, breakpoints, config
#        history or link state (space-workspace). `c2o data clean` runs this.
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
AI_SECRET="$(attr c2o-ai-secret c2o-anthropic-key)"
RF_MODE="$(attr c2o-rf-mode FRAME)"
case "$RF_MODE" in FRAME|RF) ;; *) RF_MODE=FRAME ;; esac
PROJECT="$(md project/project-id)"
MY_IP="$(md instance/network-interfaces/0/ip)"

case "$ROLE" in
    ground) PROFILES=(ground rf design); ENV_NAME=ground.env ;;   # rf: radio view; design: SpaceCDF
    sim)    PROFILES=(space);     ENV_NAME=space.env ;;
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
        sed -e "s|@DOMAIN@|$DOMAIN|g" -e "s|@GROUND_IP@|$GROUND_IP|g" -e "s|@MY_IP@|$MY_IP|g" -e "s|@RF_MODE@|$RF_MODE|g" "$tmpl" \
            | grep -v -E '^SMO_LINK_(SESSION|SECRET)='
        echo
        echo "# From Secret Manager ($SECRET), written by vm-bootstrap.sh $(date -u +%FT%TZ)"
        printf '%s\n' "$creds"
        # Instructor accounts (c2o.env VOICE_INSTRUCTORS, mirrors the
        # c2o-instructors group): the welcome page and the voice loops read
        # SMO_INSTRUCTORS; empty = nobody (closed by default behind IAP).
        echo "SMO_INSTRUCTORS=$(printf '%s' "$(attr c2o-instructors)" | tr -cd 'A-Za-z0-9._%+@ -')"
    } > "$tmp"
    mv -f "$tmp" "$ENV_FILE"
    say "wrote $ENV_FILE (session $(sed -n 's/^SMO_LINK_SESSION=//p' "$ENV_FILE"))"
}

# SpaceCDF's AI key (ground VM only). Absent or unreadable = manual mode;
# never fatal, because SpaceCDF works without it.
write_design_env() {
    [ "$ROLE" = ground ] || return 0
    local file="$SIM_DIR/docker/design.env" body code tmp key=""
    body="$(mktemp)"
    code="$(curl -sS -o "$body" -w '%{http_code}' -H "Authorization: Bearer $(token)" \
        "https://secretmanager.googleapis.com/v1/projects/$PROJECT/secrets/$AI_SECRET/versions/latest:access" \
        2>/dev/null)" || code=000
    if [ "$code" = 200 ]; then
        key="$(python3 -c 'import base64,json,sys; sys.stdout.write(base64.b64decode(json.load(open(sys.argv[1]))["payload"]["data"]).decode().strip())' "$body")"
    fi
    rm -f "$body"
    tmp="$(mktemp "$file.XXXX")"; chmod 600 "$tmp"
    if [[ "$key" =~ ^sk-ant-[A-Za-z0-9_-]{20,}$ ]]; then
        printf 'ANTHROPIC_API_KEY=%s\n' "$key" > "$tmp"
        say "wrote $file (AI advisor on)"
    else
        [ -n "$key" ] && say "secret $AI_SECRET does not look like an Anthropic key (sk-ant-...): AI advisor off"
        [ -z "$key" ] && say "no version in secret $AI_SECRET (HTTP $code): SpaceCDF runs without the AI advisor"
        : > "$tmp"
    fi
    mv -f "$tmp" "$file"
}

# Voice loops (ground VM only): sim/docker/voice.env for the MCS token
# service. No secret or no voice VM = an empty file = the Voice panel says
# "unavailable"; never fatal.
write_voice_env() {
    [ "$ROLE" = ground ] || return 0
    local file="$SIM_DIR/docker/voice.env" vsecret vhost vinstr body code tmp kv=""
    vsecret="$(attr c2o-voice-secret)"; vhost="$(attr c2o-voice-host)"; vinstr="$(attr c2o-voice-instructors)"
    tmp="$(mktemp "$file.XXXX")"; chmod 600 "$tmp"
    if [ -n "$vsecret" ] && [ -n "$vhost" ]; then
        body="$(mktemp)"
        code="$(curl -sS -o "$body" -w '%{http_code}' -H "Authorization: Bearer $(token)" \
            "https://secretmanager.googleapis.com/v1/projects/$PROJECT/secrets/$vsecret/versions/latest:access" \
            2>/dev/null)" || code=000
        if [ "$code" = 200 ]; then
            kv="$(python3 - "$body" <<'PY'
import base64, json, re, sys
raw = base64.b64decode(json.load(open(sys.argv[1]))["payload"]["data"]).decode()
kv = dict(l.split("=", 1) for l in raw.replace("\r", "").splitlines() if "=" in l)
k, s = kv.get("LIVEKIT_API_KEY", ""), kv.get("LIVEKIT_API_SECRET", "")
if re.fullmatch(r"[A-Za-z0-9_-]{3,64}", k) and re.fullmatch(r"[A-Za-z0-9_-]{32,128}", s):
    print("LIVEKIT_API_KEY=" + k)
    print("LIVEKIT_API_SECRET=" + s)
PY
)" || kv=""
        fi
        rm -f "$body"
    fi
    if [ -n "$kv" ] && [[ "$vhost" =~ ^[a-z0-9.-]+$ ]]; then
        {
            echo "# Voice loops, written by vm-bootstrap.sh $(date -u +%FT%TZ) from $vsecret"
            echo "LIVEKIT_URL=wss://$vhost"
            printf '%s\n' "$kv"
            echo "SMO_VOICE_REQUIRE_IAP=1"
            echo "SMO_VOICE_INSTRUCTORS=$(printf '%s' "$vinstr" | tr -cd 'A-Za-z0-9._%+@ -')"
        } > "$tmp"
        say "wrote $file (voice loops via wss://$vhost)"
    else
        [ -n "$vsecret" ] && say "voice loops off: no readable LiveKit key pair in ${vsecret} (HTTP ${code:-none})"
        : > "$tmp"
    fi
    mv -f "$tmp" "$file"
}

# ── Compose ─────────────────────────────────────────────────────────────
compose() {
    # --env-file: the compose file interpolates SMO_PUBLISH_ADDR (and the
    # image tag) from it; env_file inside compose.yaml only reaches the
    # containers, not the `ports:` lines.
    local pargs=() p
    for p in "${PROFILES[@]}"; do pargs+=(--profile "$p"); done
    (cd "$SIM_DIR" && SMO_CONFIG_HASH="$(sh docker/config-hash.sh)" \
        docker compose --env-file "docker/$ENV_NAME" -f docker/compose.yaml "${pargs[@]}" "$@")
}
up() {
    say "docker compose --profile ${PROFILES[*]} up (first build: several minutes)"
    compose up -d --build --remove-orphans
    compose ps
}

# ── Recordings (c2o data list / clean) ──────────────────────────────────
# Compose names its volumes <project>_<volume>; the project is "smo".
VOL_PREFIX=smo_

# recording_spec WHAT: "volume|services that mount it|paths inside it" for
# this VM's role, or nothing if this VM holds no such recording. Paths are
# relative to the volume root; "." = every file in the volume.
recording_spec() {
    case "$ROLE:$1" in
        ground:telemetry) echo "ground-archive|mcs|." ;;
        ground:dumps)     echo "ground-dumps|gsg mcs dtm-viewer|." ;;
        ground:reports)   echo "ground-workspace|gsg mcs planner rfsim dtm-viewer|reports pass_rollups*" ;;
        ground:designs)   echo "spacecdf-data|spacecdf|." ;;
        # Participant logbooks (LOGBOOK_SPEC.md): every ground screen and
        # SpaceCDF write workspace/logbook; on the sim VM only the instructor.
        ground:logbooks)  echo "ground-workspace|gsg mcs planner rfsim dtm-viewer orbit-tools doc-viewer portal spacecdf|logbook" ;;
        sim:dumps)        echo "space-dumps|sim|." ;;
        sim:logbooks)     echo "space-workspace|sim|logbook" ;;
        *:telemetry|*:dumps|*:reports|*:designs|*:logbooks) ;;
        *) die "clean: unknown recording '$1' (telemetry, dumps, reports, designs, logbooks)" ;;
    esac
}

vol_kb() {  # vol_kb VOLUME -> size in KiB, or nothing if the volume does not exist
    local mp
    mp="$(docker volume inspect -f '{{.Mountpoint}}' "$VOL_PREFIX$1" 2>/dev/null)" || return 0
    du -sk "$mp" 2>/dev/null | awk '{print $1}' || true
}

# sizes: one line per data volume ("vol NAME KiB"), the participant logbooks
# inside a workspace volume ("sub VOLUME/logbook KiB FILES"), plus the boot
# disk ("disk USED_KiB SIZE_KiB"), for c2o data list.
sizes() {
    local v kb mp n
    echo "role $ROLE"
    for v in $(docker volume ls -q 2>/dev/null | sed -n "s/^$VOL_PREFIX//p" | sort); do
        kb="$(vol_kb "$v")"
        echo "vol $v ${kb:-0}"
        case "$v" in
            ground-workspace|space-workspace)
                mp="$(docker volume inspect -f '{{.Mountpoint}}' "$VOL_PREFIX$v" 2>/dev/null)" || continue
                [ -d "$mp/logbook" ] || continue
                kb="$(du -sk "$mp/logbook" 2>/dev/null | awk '{print $1}')"
                n="$(find "$mp/logbook" -maxdepth 1 -name '*.jsonl' 2>/dev/null | wc -l | tr -d ' ')"
                echo "sub $v/logbook ${kb:-0} ${n:-0}" ;;
        esac
    done
    df -Pk / | awk 'NR == 2 {print "disk", $3, $2}'
}

# image_for SERVICE: the image an existing container of SERVICE was created
# from (already on this VM, so nothing is pulled or built).
image_for() {
    local id
    id="$(compose ps -a -q "$1" 2>/dev/null | head -n 1)"
    [ -n "$id" ] && docker inspect -f '{{.Image}}' "$id" 2>/dev/null
}

clean() {
    [ "$#" -gt 0 ] || die "usage: vm-bootstrap.sh clean telemetry|dumps|reports|designs|logbooks ..."
    local what spec vol svcs paths img stop_all=no todo=() stop=() s line
    for what in "$@"; do
        spec="$(recording_spec "$what")"
        if [ -z "$spec" ]; then say "clean $what: nothing of that kind on the $ROLE VM"; continue; fi
        todo+=("$spec")
        svcs="${spec#*|}"; svcs="${svcs%%|*}"
        for s in $svcs; do
            case " ${stop[*]:-} " in *" $s "*) ;; *) stop+=("$s") ;; esac
            # Other services share the GSG's (ground) or the simulator's
            # (sim) network namespace: stopping either means stopping all.
            case "$s" in gsg|sim) stop_all=yes ;; esac
        done
    done
    [ "${#todo[@]}" -gt 0 ] || { say "clean: nothing to do on this VM"; return 0; }

    if [ "$stop_all" = yes ]; then
        say "stopping all containers (they share the ${ROLE} network namespace)"
        compose stop
    else
        say "stopping ${stop[*]}"
        compose stop "${stop[@]}"
    fi
    for line in "${todo[@]}"; do
        vol="${line%%|*}"; svcs="${line#*|}"; paths="${svcs#*|}"; svcs="${svcs%%|*}"
        if ! docker volume inspect "$VOL_PREFIX$vol" >/dev/null 2>&1; then
            say "volume $VOL_PREFIX$vol does not exist yet: nothing to clean"; continue
        fi
        img="$(image_for "${svcs%% *}")" || img=""
        [ -n "$img" ] || img="$(docker images -q "smo-suite" | head -n 1)"
        [ -n "$img" ] || die "no local image to run the clean-up with (no pull is attempted)"
        say "emptying $VOL_PREFIX$vol ($paths) - was $(vol_kb "$vol") KiB"
        # Root inside a throw-away container of the SAME image, no network:
        # the files belong to the image's runtime user. Directories are kept
        # (with their owners), only files go.
        docker run --rm --network none --user 0:0 --entrypoint sh \
            -e C2O_PATHS="$paths" -v "$VOL_PREFIX$vol:/v" "$img" -c '
                cd /v || exit 1
                for p in $C2O_PATHS; do
                    [ -e "$p" ] || continue
                    if [ -d "$p" ]; then find "$p" -mindepth 1 ! -type d -exec rm -f {} +
                    else rm -f "$p"; fi
                done' </dev/null
        say "now $(vol_kb "$vol") KiB"
    done
    say "starting the containers again"
    compose up -d </dev/null
}

case "$ACTION" in
    boot)
        install_docker; clone_repo; write_env; write_design_env; write_voice_env; up ;;
    refresh)
        write_env; write_design_env; write_voice_env; up ;;
    rotate)
        [ "$ROLE" = ground ] || die "rotate runs on the ground VM only (the sim VM then runs: refresh)"
        say "issuing NEW link credentials"
        new_creds | secret_add
        write_env; write_design_env; write_voice_env; up ;;
    update)
        # Pull, then hand over to the NEW copy of this script: bash keeps
        # running the version it started with, which would apply the old
        # profiles and env templates to the new code.
        update_repo
        say "re-running the updated bootstrap (refresh)"
        exec bash "$APP_DIR/deploy/gcp/vm-bootstrap.sh" refresh ;;
    down)
        compose down ;;
    sizes)
        sizes; exit 0 ;;
    clean)
        shift; clean "$@" ;;
    *)
        die "usage: vm-bootstrap.sh [boot|refresh|rotate|update|down|sizes|clean WHAT...]" ;;
esac
say "done ($ACTION, role $ROLE, $MY_IP)"
