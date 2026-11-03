#!/usr/bin/env bash
# C2O voice VM bootstrap: the startup script of c2o-voice-vm (setup.sh
# installs it as instance metadata). Runs as root on EVERY boot; idempotent.
#
#   1. install Docker Engine + the compose plugin (first boot only)
#   2. read the LiveKit API key pair from Secret Manager (setup.sh wrote it)
#   3. write /opt/c2o-voice/: livekit.yaml (mode 600: it holds the secret),
#      caddy.json and compose.yaml, from the metadata below
#   4. docker compose up -d: LiveKit + Caddy (layer-4 build), pinned images,
#      host networking (LiveKit needs the UDP range on the host)
#
# Layout (LiveKit's documented single-VM deployment, without Redis, which a
# single node does not need):
#   :443  Caddy, split by TLS SNI:
#           voice.<domain>       -> TLS ends in Caddy -> 127.0.0.1:7880 (signalling, WSS)
#           voice-turn.<domain>  -> TLS ends in Caddy -> 127.0.0.1:5349 (TURN/TLS, with
#                                   a PROXY v2 header so TURN sees the client's address)
#   :80   Caddy, Let's Encrypt HTTP-01 challenges (both names)
#   7881/tcp, 50000-60000/udp  LiveKit ICE;  3478/udp  embedded TURN/UDP
# Both names must resolve to this VM's static IP before Caddy can obtain the
# certificates (README "Voice loops": two A records).
#
# Instance metadata (set by setup.sh):
#   c2o-voice-host       voice.c2o.live        c2o-voice-turn-host  voice-turn.c2o.live
#   c2o-voice-secret     Secret Manager secret: LIVEKIT_API_KEY=..., LIVEKIT_API_SECRET=...
#   c2o-acme-email       optional Let's Encrypt contact
#
# By hand on the VM (gcloud compute ssh c2o-voice-vm --tunnel-through-iap):
#   sudo bash /opt/c2o-voice/voice-bootstrap.sh            # same as a boot
#   sudo bash /opt/c2o-voice/voice-bootstrap.sh refresh    # re-read the secret, recreate
#   sudo bash /opt/c2o-voice/voice-bootstrap.sh status     # containers + last log lines
#   sudo bash /opt/c2o-voice/voice-bootstrap.sh down       # stop the containers
set -euo pipefail

ACTION="${1:-boot}"
DIR="${C2O_VOICE_DIR:-/opt/c2o-voice}"   # override only for offline tests
MD=http://metadata.google.internal/computeMetadata/v1
# Pinned (tag AND digest). livekit-server v1.13.10, 2026-10-14; caddyl4
# v2.11.3 (Caddy + caddy-l4, LiveKit's image for this layout), 2026-06-04.
LIVEKIT_IMAGE="livekit/livekit-server:v1.13.10@sha256:89ca9ce0791e18d6e03bf6e2c49ceb27e1c754eae8bd50c989386c1a5963791a"
CADDY_IMAGE="livekit/caddyl4:v2.11.3@sha256:9dd090159a6042a907dbff0ce9dda27a21d2a559dc7b03b60a8e6b1b60b8348e"

say() { echo "c2o-voice: $*" >&2; logger -t c2o-voice -- "$*" 2>/dev/null || true; }
die() { say "ERROR: $*"; exit 1; }

md()   { curl -fsS -H 'Metadata-Flavor: Google' "$MD/$1"; }
attr() { md "instance/attributes/$1" 2>/dev/null || printf '%s' "${2:-}"; }

HOST="$(attr c2o-voice-host)"
TURN_HOST="$(attr c2o-voice-turn-host)"
SECRET="$(attr c2o-voice-secret c2o-livekit-keys)"
ACME_EMAIL="$(attr c2o-acme-email)"
PROJECT="$(md project/project-id)"
EXT_IP="$(md instance/network-interfaces/0/access-configs/0/external-ip 2>/dev/null || true)"

host_ok() { [[ "$1" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$ ]]; }
host_ok "$HOST" || die "metadata c2o-voice-host is not a host name: '$HOST'"
host_ok "$TURN_HOST" || die "metadata c2o-voice-turn-host is not a host name: '$TURN_HOST'"
[[ "$EXT_IP" =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}$ ]] || die "this VM has no external IP (setup.sh gives it the static address)"
[ -z "$ACME_EMAIL" ] || [[ "$ACME_EMAIL" =~ ^[^@[:space:]\"]+@[^@[:space:]\"]+$ ]] || { say "ignoring malformed c2o-acme-email"; ACME_EMAIL=""; }

# ── Docker ──────────────────────────────────────────────────────────────
install_docker() {
    if command -v docker >/dev/null && docker compose version >/dev/null 2>&1; then
        return
    fi
    say "installing Docker Engine and the compose plugin"
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -q
    apt-get install -y -q ca-certificates curl python3
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    # shellcheck disable=SC1091
    codename="$(. /etc/os-release && echo "$VERSION_CODENAME")"
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $codename stable" \
        > /etc/apt/sources.list.d/docker.list
    apt-get update -q
    apt-get install -y -q docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable --now docker
}

# ── Secret Manager (REST with the VM's service-account token) ───────────
token() {
    md instance/service-accounts/default/token \
        | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])'
}
# keys: "KEY SECRET" on stdout, validated; waits for setup.sh to add the version.
keys() {
    local body code n
    body="$(mktemp)"
    for n in $(seq 1 60); do
        code="$(curl -sS -o "$body" -w '%{http_code}' -H "Authorization: Bearer $(token)" \
            "https://secretmanager.googleapis.com/v1/projects/$PROJECT/secrets/$SECRET/versions/latest:access" \
            2>/dev/null)" || code=000
        [ "$code" = 200 ] && break
        say "secret $SECRET not readable yet (HTTP $code, try $n of 60); setup.sh adds it"
        sleep 10
    done
    [ "$code" = 200 ] || { rm -f "$body"; die "could not read the LiveKit keys from Secret Manager ($SECRET)"; }
    if python3 - "$body" <<'PY'
import base64, json, re, sys
raw = base64.b64decode(json.load(open(sys.argv[1]))["payload"]["data"]).decode()
kv = dict(l.split("=", 1) for l in raw.replace("\r", "").splitlines() if "=" in l)
k, s = kv.get("LIVEKIT_API_KEY", ""), kv.get("LIVEKIT_API_SECRET", "")
if not re.fullmatch(r"[A-Za-z0-9_-]{3,64}", k) or not re.fullmatch(r"[A-Za-z0-9_-]{32,128}", s):
    sys.exit("secret must hold LIVEKIT_API_KEY=<3-64 chars> and LIVEKIT_API_SECRET=<32-128 url-safe chars>")
print(k, s)
PY
    then rm -f "$body"; else rm -f "$body"; return 1; fi
}

# ── Config files ────────────────────────────────────────────────────────
write_config() {
    local kp key sec tmp
    kp="$(keys)" || die "the LiveKit key pair in $SECRET is malformed"
    case "$kp" in *" "?*) ;; *) die "the LiveKit key pair in $SECRET is malformed" ;; esac
    key="${kp%% *}"; sec="${kp#* }"
    install -d -m 0755 "$DIR"
    cp -f "$0" "$DIR/voice-bootstrap.sh" 2>/dev/null || true
    tmp="$(mktemp "$DIR/.livekit.XXXX")"; chmod 600 "$tmp"
    cat > "$tmp" <<EOF
# Written by voice-bootstrap.sh $(date -u +%FT%TZ). Holds the API secret: mode 600.
port: 7880
bind_addresses: ["127.0.0.1"]     # signalling only through Caddy on 443
rtc:
  tcp_port: 7881
  port_range_start: 50000
  port_range_end: 60000
  use_external_ip: false
  node_ip: $EXT_IP                 # the static external IP (GCP 1:1 NAT)
turn:
  enabled: true
  domain: $TURN_HOST
  tls_port: 5349                   # plain TCP behind Caddy; advertised as turns:...:443
  external_tls: true
  proxy_protocol: true             # Caddy sends PROXY v2 (client address for TURN)
  udp_port: 3478
room:
  empty_timeout: 300
  max_participants: 60
logging:
  level: info
keys:
  $key: $sec
EOF
    mv -f "$tmp" "$DIR/livekit.yaml"
    python3 - "$HOST" "$TURN_HOST" "$ACME_EMAIL" > "$DIR/caddy.json" <<'PY'
import json, sys
host, turn, email = sys.argv[1:4]
issuer = {"module": "acme"}
if email:
    issuer["email"] = email
print(json.dumps({
    "logging": {"logs": {"default": {"level": "INFO"}}},
    "storage": {"module": "file_system", "root": "/data"},
    "apps": {
        "tls": {
            "certificates": {"automate": [host, turn]},
            "automation": {"policies": [{"subjects": [host, turn], "issuers": [issuer]}]},
        },
        "layer4": {"servers": {"main": {"listen": [":443"], "routes": [
            {"match": [{"tls": {"sni": [turn]}}],
             "handle": [{"handler": "tls"},
                        {"handler": "proxy", "proxy_protocol": "v2",
                         "upstreams": [{"dial": ["127.0.0.1:5349"]}]}]},
            {"match": [{"tls": {"sni": [host]}}],
             "handle": [{"handler": "tls", "connection_policies": [{"alpn": ["http/1.1"]}]},
                        {"handler": "proxy", "upstreams": [{"dial": ["127.0.0.1:7880"]}]}]},
        ]}}},
    },
}, indent=2))
PY
    cat > "$DIR/compose.yaml" <<EOF
# Written by voice-bootstrap.sh. LiveKit + Caddy (layer 4), host network.
name: c2o-voice
services:
  livekit:
    image: $LIVEKIT_IMAGE
    command: ["--config", "/etc/livekit.yaml"]
    network_mode: host
    restart: unless-stopped
    volumes:
      - ./livekit.yaml:/etc/livekit.yaml:ro
  caddy:
    image: $CADDY_IMAGE
    command: ["run", "--config", "/etc/caddy.json"]
    network_mode: host
    restart: unless-stopped
    volumes:
      - ./caddy.json:/etc/caddy.json:ro
      - caddy-data:/data
volumes:
  caddy-data:    # Let's Encrypt account and certificates (kept across restarts)
EOF
    say "wrote $DIR (voice $HOST, TURN $TURN_HOST, node IP $EXT_IP, key $key)"
}

compose() { (cd "$DIR" && docker compose -f compose.yaml "$@"); }

case "$ACTION" in
    boot)    install_docker; write_config; compose up -d --remove-orphans; compose ps ;;
    refresh) write_config; compose up -d --force-recreate --remove-orphans; compose ps ;;
    status)  compose ps; compose logs --tail 20 ;;
    down)    compose down ;;
    *)       die "usage: voice-bootstrap.sh [boot|refresh|status|down]" ;;
esac
say "done ($ACTION, $HOST at $EXT_IP)"
