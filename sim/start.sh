#!/usr/bin/env bash
# Start the SMO suite: Simulator ($SMO_SIM_HTTP_PORT, default 8080),
# MCS (9090), Planner (9091)
#
# Usage:
#   ./start.sh            # standard mode (no RF)
#   ./start.sh --rf       # with RF bridge in FRAME mode (CCSDS framing + BER)
#   ./start.sh --rf=RF    # with RF bridge in RF mode (BPSK mod/demod)
#   ./start.sh --rf=FRAME # same as --rf
#
# Launch profiles (docs/web_2026-10/LINK_DESIGN.md §5) — SMO_PROFILE or --profile=:
#   SMO_PROFILE=all     (default) everything on this host, exactly as before
#   SMO_PROFILE=space   simulator + space-link agent (+ scenario generator,
#                       ADCS viewer); needs SMO_LINK_URL (or --same-host)
#   SMO_PROFILE=ground  ground-segment gateway (GSG) + MCS + planner (+ RF
#                       bridge with --rf) + delayed-TM viewer, orbit tools,
#                       doc viewer
#   Both ends share a session id + secret: the ground profile creates
#   workspace/link/session.env on first run and both read it (copy it to the
#   simulator host); SMO_LINK_SESSION/SMO_LINK_SECRET[_FILE] override it.
#   --same-host: both profiles on one machine (GSG stand-ins on 180xx).
#
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ── Parse arguments ──
RF_MODE=""
PUBLIC=""
REAL=""
UI_ARG=""
PROFILE_ARG=""
SAME_HOST="${SMO_LINK_SAME_HOST:-}"
for arg in "$@"; do
    case "$arg" in
        --rf)       RF_MODE="RF" ;;
        --rf=*)     RF_MODE="${arg#--rf=}" ;;
        --public)   PUBLIC=1 ;;
        --real)     REAL=1 ;;
        --classic)  UI_ARG="classic" ;;
        --modern)   UI_ARG="modern" ;;
        --host=*)   SMO_BIND="${arg#--host=}" ;;
        --profile=*) PROFILE_ARG="${arg#--profile=}" ;;
        --same-host) SAME_HOST=1 ;;
        *)          echo "Unknown option: $arg"; echo "Usage: $0 [--rf | --rf=FRAME | --rf=RF] [--public] [--real] [--classic | --modern] [--host=ADDR] [--profile=all|space|ground] [--same-host]"; exit 1 ;;
    esac
done

# ── Launch profile (LINK_DESIGN §5) ──
# Not exported: it only selects which blocks below run. `all` takes exactly
# the code path this script had before profiles existed.
SMO_PROFILE="${SMO_PROFILE:-all}"
if [ -n "$PROFILE_ARG" ]; then
    SMO_PROFILE="$PROFILE_ARG"
fi
case "$SMO_PROFILE" in
    all|space|ground) ;;
    *) echo "ERROR: SMO_PROFILE must be all, space or ground (got '$SMO_PROFILE')."; exit 1 ;;
esac

# The split profiles talk over smo-link. Check the credentials before anything
# starts: an agent or GSG without them would only fail later, in a log.
if [ "$SMO_PROFILE" != "all" ]; then
    # Shared credentials file (mode 600). Explicit SMO_LINK_* variables win;
    # otherwise both profiles read this file, and the ground profile creates it
    # on first run. Copy the SAME file to the other end (same path), or pass
    # its two values as environment variables there.
    SMO_LINK_ENV_FILE="${SMO_LINK_ENV_FILE:-$SCRIPT_DIR/workspace/link/session.env}"
    LINK_CREDS_FROM=""
    LINK_CREDS_NEW=""
    if [ -z "${SMO_LINK_SESSION:-}" ] && [ -z "${SMO_LINK_SECRET:-}" ] \
       && [ -z "${SMO_LINK_SECRET_FILE:-}" ]; then
        if [ ! -f "$SMO_LINK_ENV_FILE" ] && [ "$SMO_PROFILE" = "ground" ]; then
            mkdir -p "$(dirname "$SMO_LINK_ENV_FILE")"
            LINK_PY="$(command -v python3 || command -v python)"
            if [ -z "$LINK_PY" ]; then
                echo "ERROR: python3 is needed to create link credentials."; exit 1
            fi
            ( umask 077
              "$LINK_PY" -c 'import secrets
print("# smo-link session credentials - keep private; both ends need the same file")
print("SMO_LINK_SESSION=s-" + secrets.token_hex(8))
print("SMO_LINK_SECRET=" + secrets.token_hex(32))' > "$SMO_LINK_ENV_FILE" ) \
                || { echo "ERROR: could not write $SMO_LINK_ENV_FILE"; exit 1; }
            LINK_CREDS_NEW=1
        fi
        if [ -f "$SMO_LINK_ENV_FILE" ]; then
            while IFS='=' read -r LINK_K LINK_V || [ -n "$LINK_K" ]; do
                LINK_V="${LINK_V%$'\r'}"
                case "$LINK_K" in
                    SMO_LINK_SESSION|SMO_LINK_SECRET) export "$LINK_K=$LINK_V" ;;
                esac
            done < "$SMO_LINK_ENV_FILE"
            LINK_CREDS_FROM="$SMO_LINK_ENV_FILE"
        fi
    fi
    if [ "$SMO_PROFILE" = "space" ] && [ -z "${SMO_LINK_URL:-}" ] && [ -n "$SAME_HOST" ]; then
        export SMO_LINK_URL="ws://127.0.0.1:${SMO_GSG_LINK_PORT:-9100}/link"
    fi
    LINK_MISSING=""
    if [ "$SMO_PROFILE" = "space" ] && [ -z "${SMO_LINK_URL:-}" ]; then
        LINK_MISSING="$LINK_MISSING SMO_LINK_URL"
    fi
    [ -z "${SMO_LINK_SESSION:-}" ] && LINK_MISSING="$LINK_MISSING SMO_LINK_SESSION"
    if [ -z "${SMO_LINK_SECRET:-}" ] && [ -z "${SMO_LINK_SECRET_FILE:-}" ]; then
        LINK_MISSING="$LINK_MISSING SMO_LINK_SECRET(or SMO_LINK_SECRET_FILE)"
    fi
    if [ -n "$LINK_MISSING" ]; then
        echo "ERROR: SMO_PROFILE=$SMO_PROFILE needs these environment variables:"
        echo "      $LINK_MISSING"
        if [ "$SMO_PROFILE" = "space" ]; then
            echo "       Credentials: start the ground side first (it creates"
            echo "       workspace/link/session.env) and copy that file here, or set"
            echo "       SMO_LINK_SESSION and SMO_LINK_SECRET to the ground side's values."
            echo "       SMO_LINK_URL is the ground side's link endpoint, e.g."
            echo "       wss://<ground-host>/link — or use --same-host when both run on"
            echo "       this machine."
        else
            echo "       Set SMO_LINK_SESSION and SMO_LINK_SECRET (or SMO_LINK_SECRET_FILE)"
            echo "       to the same values on both ends."
        fi
        echo "       See docs/web_2026-10/LINK_DESIGN.md §4."
        exit 1
    fi
    if [ -z "${SMO_LINK_SECRET:-}" ] && [ ! -r "$SMO_LINK_SECRET_FILE" ]; then
        echo "ERROR: SMO_LINK_SECRET_FILE=$SMO_LINK_SECRET_FILE is not a readable file."
        exit 1
    fi
    if [ -n "$LINK_CREDS_NEW" ]; then
        echo "==> Created link credentials: $LINK_CREDS_FROM (session $SMO_LINK_SESSION)."
        echo "    The simulator side needs the same file: copy it to workspace/link/"
        echo "    in the checkout there (not needed with --same-host on this machine)."
    elif [ -n "$LINK_CREDS_FROM" ]; then
        echo "==> Link credentials from $LINK_CREDS_FROM (session $SMO_LINK_SESSION)."
    fi
    if [ "$SMO_PROFILE" = "space" ]; then
        # The simulator needs 8001/8002; a ground profile started here without
        # --same-host would be holding them.
        for LINK_P in 8001 8002; do
            if (exec 3<>"/dev/tcp/127.0.0.1/$LINK_P") 2>/dev/null; then
                echo "ERROR: port $LINK_P is already in use on this machine, so the simulator"
                echo "       cannot start. If the ground side is running here, restart BOTH with"
                echo "       --same-host:  SMO_PROFILE=ground ./start.sh --same-host"
                echo "                     SMO_PROFILE=space  ./start.sh --same-host"
                echo "       To see what holds it:  lsof -nP -iTCP:$LINK_P -sTCP:LISTEN"
                exit 1
            fi
        done
        # The simulator's web console (8080 by default) can move: the agent
        # follows SMO_SIM_HTTP_PORT. Pick a free port if 8080 is taken.
        if [ -z "${SMO_SIM_HTTP_PORT:-}" ] && (exec 3<>"/dev/tcp/127.0.0.1/8080") 2>/dev/null; then
            for LINK_P in 8090 8180 8280 8380; do
                if ! (exec 3<>"/dev/tcp/127.0.0.1/$LINK_P") 2>/dev/null; then
                    export SMO_SIM_HTTP_PORT="$LINK_P"
                    echo "==> Port 8080 is already in use on this machine (see what by:"
                    echo "    lsof -nP -iTCP:8080 -sTCP:LISTEN), so the simulator's web console"
                    echo "    uses $LINK_P instead. The ground side is unaffected."
                    break
                fi
            done
        fi
    fi
fi

# ── UI generation (design_2026-08 plan §1.2) ──
# Which console every server's "/" serves. Precedence in each service:
# --ui CLI (passed below) > SMO_UI env > mission-config `ui:` > default.
# Per-request ?ui= and the /classic and /modern routes always work for
# live comparison, whatever is selected here.
#
# FINAL FLIP (2026-08-18): the Agent-5 verification gate passed — modern is
# the shipped default. Escape hatches: ./start.sh --classic, SMO_UI=classic,
# per-request ?ui=classic, and GET /classic on every server.
SMO_UI="${SMO_UI:-modern}"
if [ -n "$UI_ARG" ]; then
    SMO_UI="$UI_ARG"
fi
export SMO_UI

# ── Time source (ground UTC / Planner "now") ──
# "sim"  → MCS & Planner closed-loop follow the simulator's sim_time/speed.
# "real" → both use real wall-clock UTC (for a real mission link).
# Children inherit these env vars; we also pass --time-source explicitly.
# Precedence in each service: CLI flag > env > mission-config field > default.
SMO_TIME_SOURCE="${SMO_TIME_SOURCE:-sim}"
if [ -n "$REAL" ]; then
    SMO_TIME_SOURCE="real"
fi
export SMO_TIME_SOURCE
SMO_SIM_STATE_URL="${SMO_SIM_STATE_URL:-}"   # resolved once the bind is known
# ── Simulator HTTP port ──
# The simulator used to hard-code 8080, so a host where 8080 was already
# taken could not run the suite at all. It now takes --port; export the
# same name smo-mcs reads for the sim-state URL so both ends agree.
SMO_SIM_HTTP_PORT="${SMO_SIM_HTTP_PORT:-8080}"
export SMO_SIM_HTTP_PORT
# Also honour the environment variable (CLI takes priority)
if [ -z "$RF_MODE" ] && [ -n "${SMO_RF_MODE:-}" ]; then
    RF_MODE="$SMO_RF_MODE"
fi
# --public can also be requested via SMO_PUBLIC=1
if [ -z "$PUBLIC" ] && [ "${SMO_PUBLIC:-}" = "1" ]; then
    PUBLIC=1
fi

# Resolve the delayed-TM dump archive dir and export it so EVERY child agrees
# on one location: the simulator writes its S15 dumps there, and the MCS,
# the simulator's own dump API and the standalone viewer all read from it.
# Resolution order (see smo_common.dump_store): SMO_DUMP_DIR > mission.yaml
# `dump_dir:` > workspace/dumps. We pin an absolute path here so a child
# started from a different working directory still finds the same store.
DUMP_DIR="${SMO_DUMP_DIR:-$SCRIPT_DIR/workspace/dumps}"
export SMO_DUMP_DIR="$DUMP_DIR"

# Host name/IP to print in the banner. With --public the services bind
# 0.0.0.0, so printing "localhost" would hand students a URL that resolves to
# their OWN machine; print something reachable instead (defect #90).
if [ -n "$PUBLIC" ]; then
    ACCESS_HOST="$(hostname -I 2>/dev/null | awk '{print $1}')"
    [ -z "$ACCESS_HOST" ] && ACCESS_HOST="$(hostname -f 2>/dev/null || hostname)"
    [ -z "$ACCESS_HOST" ] && ACCESS_HOST="localhost"
else
    ACCESS_HOST="localhost"
fi

# Bind address. In LOCAL mode the banner used to claim "services bound to
# loopback where supported" while the simulator, MCS and planner hard-coded
# 0.0.0.0 unconditionally (D-2). They now honour --host/$SMO_BIND, so the
# banner and the sockets agree.
if [ -n "$PUBLIC" ]; then
    SMO_BIND="${SMO_BIND:-0.0.0.0}"
else
    SMO_BIND="${SMO_BIND:-127.0.0.1}"
fi
export SMO_BIND
# Address a readiness probe (and the children) should use to reach a service.
# 0.0.0.0 is a bind address, never a destination.
PROBE_HOST="$SMO_BIND"
[ "$PROBE_HOST" = "0.0.0.0" ] && PROBE_HOST="127.0.0.1"

# Where the MCS takes its TM/TC. `all`: the local simulator on its fixed
# sockets (no --tc-port passed, exactly as before). `ground`: the GSG.
UP_HOST="$PROBE_HOST"
UP_TM_PORT=8002
MCS_TC_ARGS=()
RFSIM_UPSTREAM_ARGS=()

if [ "$SMO_PROFILE" = "space" ] && [ -n "$RF_MODE" ]; then
    echo "ERROR: --rf is ground-side: run the RF bridge with SMO_PROFILE=ground."
    exit 1
fi

if [ "$SMO_PROFILE" = "ground" ]; then
    # ── Ground-segment gateway (smo-link GSG, LINK_DESIGN §4/§7) ──
    # Its TM, TC and HTTP listeners stand in for the simulator's, so they bind
    # loopback by default and --public does NOT open them: only the MCS,
    # planner and the tools follow --public. The instructor proxy (HTTP) is
    # meant to be reached through the authenticated edge (deploy/gcp/).
    # Only the /link listener faces the network; it requires the HMAC token.
    export SMO_GSG_BIND="${SMO_GSG_BIND:-127.0.0.1}"
    # --same-host: the simulator (space profile) runs on this machine too and
    # owns 8001/8002/8080, so the GSG's stand-ins move to 18001/18002/18080.
    if [ -n "$SAME_HOST" ]; then GSG_PORT_BASE=10000; else GSG_PORT_BASE=0; fi
    export SMO_GSG_TM_PORT="${SMO_GSG_TM_PORT:-$((8002 + GSG_PORT_BASE))}"
    export SMO_GSG_TC_PORT="${SMO_GSG_TC_PORT:-$((8001 + GSG_PORT_BASE))}"
    export SMO_GSG_HTTP_PORT="${SMO_GSG_HTTP_PORT:-$((8080 + GSG_PORT_BASE))}"
    export SMO_GSG_LINK_BIND="${SMO_GSG_LINK_BIND:-0.0.0.0}"
    export SMO_GSG_LINK_PORT="${SMO_GSG_LINK_PORT:-9100}"
    export SMO_CONFIG_DIR="${SMO_CONFIG_DIR:-$SCRIPT_DIR/configs/eosat1}"
    GSG_PROBE="$SMO_GSG_BIND"
    [ "$GSG_PROBE" = "0.0.0.0" ] && GSG_PROBE="127.0.0.1"
    UP_HOST="$GSG_PROBE"
    UP_TM_PORT="$SMO_GSG_TM_PORT"
    MCS_TC_ARGS=(--tc-port "$SMO_GSG_TC_PORT")
    # MCS and planner read the (re-timed) state from the GSG, not a simulator.
    SMO_SIM_STATE_URL="${SMO_SIM_STATE_URL:-http://$GSG_PROBE:$SMO_GSG_HTTP_PORT/api/state}"
    # The RF bridge's upstream is the GSG (wherever its stand-in ports are).
    RFSIM_UPSTREAM_ARGS=(--sim-host "$GSG_PROBE" --sim-tm-port "$SMO_GSG_TM_PORT"
                         --sim-tc-port "$SMO_GSG_TC_PORT"
                         --sim-ws-url "ws://$GSG_PROBE:$SMO_GSG_HTTP_PORT/ws")
fi

# ── Readiness ──
# `sleep 2` and hope was the previous contract: if smo-simulator died on a bad
# config, MCS and Planner still came up and showed an empty, plausible console
# (D-1). Poll the service's own endpoint instead, and abort loudly.
wait_for_http() {
    local name="$1" url="$2" pid="$3" timeout="${4:-30}"
    local waited=0
    while [ "$waited" -lt "$timeout" ]; do
        if [ -n "$pid" ] && ! kill -0 "$pid" 2>/dev/null; then
            echo ""
            echo "ERROR: $name exited during start-up. Its output is above."
            return 1
        fi
        if curl -fsS --max-time 2 "$url" >/dev/null 2>&1; then
            echo "    $name ready after ${waited}s"
            return 0
        fi
        sleep 1
        waited=$((waited + 1))
    done
    echo ""
    echo "ERROR: $name did not become ready within ${timeout}s ($url)."
    return 1
}

wait_for_port() {
    local name="$1" host="$2" port="$3" pid="$4" timeout="${5:-30}"
    local waited=0
    while [ "$waited" -lt "$timeout" ]; do
        if [ -n "$pid" ] && ! kill -0 "$pid" 2>/dev/null; then
            echo ""
            echo "ERROR: $name exited during start-up. Its output is above."
            return 1
        fi
        if python -c 'import socket,sys; s=socket.socket(); s.settimeout(1.0); sys.exit(0 if not s.connect_ex((sys.argv[1], int(sys.argv[2]))) else 1)' "$host" "$port" 2>/dev/null; then
            echo "    $name ready after ${waited}s"
            return 0
        fi
        sleep 1
        waited=$((waited + 1))
    done
    echo ""
    echo "ERROR: $name did not open $host:$port within ${timeout}s."
    return 1
}

die() {
    echo "==> Aborting start-up: $1"
    echo "    Nothing else was started; no half-live console is left behind."
    exit 1
}

# Activate virtual environment
if [ ! -f ".venv/bin/activate" ]; then
    echo "ERROR: .venv is missing or incomplete (.venv/bin/activate not found)."
    echo "Recreate it with:"
    echo "    rm -rf .venv && python3.11 -m venv .venv && source .venv/bin/activate \\"
    echo "      && pip install -e packages/smo-common -e packages/smo-simulator \\"
    echo "         -e packages/smo-mcs -e packages/smo-planner -e packages/smo-rfsim"
    exit 1
fi
source .venv/bin/activate

# Ensure local vendor symlinks are correct so the UI works fully offline
if [ -f "$SCRIPT_DIR/fix_vendor_symlinks.sh" ]; then
    bash "$SCRIPT_DIR/fix_vendor_symlinks.sh" >/dev/null 2>&1 || true
fi

# Skip pip install entirely if everything is already importable (no internet needed)
#
# D-3: a start script that reaches the network stalls for minutes in an
# offline classroom and then blames the wrong thing. The order is therefore
# (1) already installed → do nothing, (2) vendored wheels/ → install offline,
# (3) otherwise refuse and say exactly what to do. A networked developer who
# genuinely wants the online path opts in with SMO_ALLOW_NETWORK_INSTALL=1.
SMO_PKGS="-e packages/smo-common -e packages/smo-simulator -e packages/smo-mcs -e packages/smo-planner -e packages/smo-rfsim"
SMO_MODS="smo_common, smo_simulator, smo_mcs, smo_planner, smo_rfsim"
SMO_LINK_PKG=""
if [ "$SMO_PROFILE" != "all" ]; then
    # The split profiles also need packages/smo-link (agent / GSG).
    SMO_LINK_PKG="-e packages/smo-link"
    SMO_PKGS="$SMO_PKGS $SMO_LINK_PKG"
    SMO_MODS="$SMO_MODS, smo_link"
fi
if python -c "import $SMO_MODS" 2>/dev/null; then
    echo "==> Packages already installed (offline-ready, no pip needed)."
elif [ -d "$SCRIPT_DIR/wheels" ]; then
    echo "==> Installing packages from vendored wheels/ (offline, first run)..."
    pip install -q --no-index --find-links "$SCRIPT_DIR/wheels" $SMO_PKGS \
        || { echo "ERROR: offline install from $SCRIPT_DIR/wheels failed."
             echo "       The wheels/ directory is incomplete for this Python."
             exit 1; }
elif [ "${SMO_ALLOW_NETWORK_INSTALL:-0}" = "1" ]; then
    echo "==> Installing packages from the network (SMO_ALLOW_NETWORK_INSTALL=1)..."
    pip install -q -e packages/smo-common
    pip install -q -e packages/smo-simulator -e packages/smo-mcs -e packages/smo-planner -e packages/smo-rfsim $SMO_LINK_PKG
else
    echo "ERROR: the SMO packages are not installed in .venv and there is no"
    echo "       wheels/ directory to install them from offline."
    echo ""
    echo "       This script does not reach the network: in an offline"
    echo "       classroom that stalls and then reports the wrong failure."
    echo ""
    echo "       On a networked machine, run ONCE:"
    echo "           source .venv/bin/activate"
    echo "           pip install $SMO_PKGS"
    echo "       or re-run this script with SMO_ALLOW_NETWORK_INSTALL=1."
    echo ""
    echo "       For an offline lab, build the wheels once elsewhere:"
    echo "           pip wheel -w wheels/ $SMO_PKGS sgp4 numpy aiohttp"
    echo "       and ship wheels/ with the tree."
    exit 1
fi

# Cleanup on exit — kill all background jobs
cleanup() {
    echo ""
    echo "==> Shutting down..."
    kill $(jobs -p) 2>/dev/null
    wait 2>/dev/null
    echo "==> All services stopped."
}
trap cleanup EXIT INT TERM

export SMO_SIM_STATE_URL="${SMO_SIM_STATE_URL:-http://$PROBE_HOST:$SMO_SIM_HTTP_PORT/api/state}"

# Processes whose exit stops the suite (supervised at the bottom), "Name:PID".
SUPERVISE=()

if [ "$SMO_PROFILE" != "ground" ]; then
# (profiles all + space; body left unindented so the launch lines stay
# byte-identical to the single-host script)
# Start Simulator (TC:8001, TM:8002, HTTP/WS:$SMO_SIM_HTTP_PORT)
echo "==> Starting Simulator on $SMO_BIND:$SMO_SIM_HTTP_PORT..."
smo-simulator --config configs/eosat1/ --host "$SMO_BIND" --port "$SMO_SIM_HTTP_PORT" --ui "$SMO_UI" &
SIM_PID=$!
SUPERVISE+=("Simulator:$SIM_PID")
# The simulator is the root dependency: MCS and Planner showing an empty but
# plausible console because it died on a bad config is the exact failure mode
# N-1 was meant to eliminate, one layer up (D-1).
wait_for_http "Simulator" "http://$PROBE_HOST:$SMO_SIM_HTTP_PORT/api/state" "$SIM_PID" 40 \
    || die "the simulator never became ready"
wait_for_port "Simulator TM socket" "$PROBE_HOST" 8002 "$SIM_PID" 15 \
    || die "the simulator TM socket never opened"
fi

if [ "$SMO_PROFILE" = "space" ]; then
    # ── Space-link agent (LINK_DESIGN §2/§4) ──
    # Dials OUT to the GSG; nothing on this host listens for the ground. It
    # reconnects forever on its own, so "ready" here only means "still alive".
    export SMO_SIM_HOST="${SMO_SIM_HOST:-$PROBE_HOST}"
    export SMO_SIM_TM_PORT="${SMO_SIM_TM_PORT:-8002}"
    export SMO_SIM_TC_PORT="${SMO_SIM_TC_PORT:-8001}"
    export SMO_CONFIG_DIR="${SMO_CONFIG_DIR:-$SCRIPT_DIR/configs/eosat1}"
    export SMO_LINK_STATE_DIR="${SMO_LINK_STATE_DIR:-$SCRIPT_DIR/workspace/link}"
    mkdir -p "$SMO_LINK_STATE_DIR"
    echo "==> Starting space-link agent → $SMO_LINK_URL (session $SMO_LINK_SESSION)..."
    python -m smo_link.agent &
    AGENT_PID=$!
    SUPERVISE+=("Space-link agent:$AGENT_PID")
    sleep 2
    kill -0 "$AGENT_PID" 2>/dev/null \
        || die "the space-link agent exited at start-up (its output is above)"
fi

if [ "$SMO_PROFILE" = "ground" ]; then
    # ── Ground-segment gateway first: it owns the TM/TC/HTTP ports the MCS,
    # planner and RF bridge expect a simulator on. Its /healthz answers as soon
    # as the process is up (the link may still be DOWN — that is normal: TM
    # clients stay connected and the MCS sees "No TC connection" until an
    # agent binds).
    echo "==> Starting ground-segment gateway: TM/TC/HTTP on $SMO_GSG_BIND:$SMO_GSG_TM_PORT/$SMO_GSG_TC_PORT/$SMO_GSG_HTTP_PORT, link on $SMO_GSG_LINK_BIND:$SMO_GSG_LINK_PORT/link..."
    python -m smo_link.gateway &
    GSG_PID=$!
    SUPERVISE+=("Ground-segment gateway:$GSG_PID")
    wait_for_http "Ground-segment gateway" "http://$GSG_PROBE:$SMO_GSG_HTTP_PORT/healthz" "$GSG_PID" 40 \
        || die "the ground-segment gateway never became ready"
    # rfsim connects to TM exactly once and never retries (LINK_INTERFACES
    # §1.7), and the MCS needs it too: wait until the listener is open.
    wait_for_port "GSG TM socket" "$GSG_PROBE" "$SMO_GSG_TM_PORT" "$GSG_PID" 15 \
        || die "the GSG TM socket never opened"
fi

# ── RF Bridge (must start before MCS so it's listening) ──
RFSIM_MSG=""
RADIO_MSG=""
if [ -n "$RF_MODE" ]; then
    RFSIM_VENV="$SCRIPT_DIR/.venv-rfsim"
    # Look for a *runnable* interpreter inside the dedicated RF venv. This covers
    # both Unix (bin/) and Windows/Git-Bash (Scripts/) layouts, and guards against
    # a .venv-rfsim that was copied from another machine: such a venv has a console
    # script with a hard-coded shebang pointing at an interpreter that doesn't exist
    # here, which fails with "bad interpreter: No such file or directory". We probe
    # the interpreter directly and only use it if it can import smo_rfsim; otherwise
    # we fall back to the main venv's smo-rfsim (installed by the setup above).
    RFSIM_PY=""
    for cand in \
        "$RFSIM_VENV/bin/python3" "$RFSIM_VENV/bin/python" \
        "$RFSIM_VENV/Scripts/python.exe" "$RFSIM_VENV/Scripts/python"; do
        if [ -f "$cand" ] && "$cand" -c "import smo_rfsim" >/dev/null 2>&1; then
            RFSIM_PY="$cand"
            break
        fi
    done

    if [ -n "$RFSIM_PY" ]; then
        echo "==> Starting RF Bridge in $RF_MODE mode (dedicated .venv-rfsim)..."
        # Invoke via the interpreter directly (not the console script) so we never
        # depend on the console script's baked-in shebang path.
        "$RFSIM_PY" -c "import sys; from smo_rfsim.bridge import main; sys.exit(main())" \
            --config "$SCRIPT_DIR/configs/eosat1/rfsim.yaml" \
            --mode "$RF_MODE" --radio-web "${RFSIM_UPSTREAM_ARGS[@]}" &
    else
        if [ -d "$RFSIM_VENV" ]; then
            echo "==> Note: .venv-rfsim exists but has no runnable interpreter here"
            echo "         (e.g. copied from another machine) — falling back to main venv."
        fi
        echo "==> Starting RF Bridge in $RF_MODE mode (main venv)..."
        smo-rfsim --config "$SCRIPT_DIR/configs/eosat1/rfsim.yaml" \
                  --mode "$RF_MODE" --radio-web "${RFSIM_UPSTREAM_ARGS[@]}" &
    fi
    RFSIM_PID=$!
    wait_for_port "RF Bridge" "$PROBE_HOST" 8012 "$RFSIM_PID" 30 \
        || die "the RF bridge never opened its TM port"
    RFSIM_MSG="  RF Bridge:        mode=$RF_MODE  (MCS→TM:8012, TC:8011)"
    RADIO_MSG="  Radio Status:     http://$ACCESS_HOST:8094"
fi

if [ "$SMO_PROFILE" != "space" ]; then
# (profiles all + ground: the MCS, planner and ground tools)
# Start MCS — in RF mode, connect through the bridge; otherwise direct to the
# simulator (all) or the GSG (ground; UP_* and MCS_TC_ARGS are set above).
if [ -n "$RF_MODE" ]; then
    echo "==> Starting MCS on $SMO_BIND:9090 (via RF bridge: TM:8012, TC:8011)..."
    smo-mcs --config configs/eosat1/ --port 9090 --host "$SMO_BIND" --connect "$PROBE_HOST:8012" --tc-port 8011 --time-source "$SMO_TIME_SOURCE" --ui "$SMO_UI" &
elif [ "$SMO_PROFILE" = "ground" ]; then
    echo "==> Starting MCS on $SMO_BIND:9090 (via GSG: TM:$UP_TM_PORT, TC:$SMO_GSG_TC_PORT)..."
    smo-mcs --config configs/eosat1/ --port 9090 --host "$SMO_BIND" --connect "$UP_HOST:$UP_TM_PORT" "${MCS_TC_ARGS[@]}" --time-source "$SMO_TIME_SOURCE" --ui "$SMO_UI" &
else
    echo "==> Starting MCS on $SMO_BIND:9090 (direct: TM:8002, TC:8001)..."
    smo-mcs --config configs/eosat1/ --port 9090 --host "$SMO_BIND" --connect "$PROBE_HOST:8002" --time-source "$SMO_TIME_SOURCE" --ui "$SMO_UI" &
fi
MCS_PID=$!
SUPERVISE+=("MCS:$MCS_PID")
wait_for_http "MCS" "http://$PROBE_HOST:9090/api/state" "$MCS_PID" 40 \
    || die "the MCS never became ready"

# Start Planner (HTTP:9091). Its sim state comes from $SMO_SIM_STATE_URL
# (the GSG's /api/state in the ground profile).
echo "==> Starting Planner on $SMO_BIND:9091..."
smo-planner --config configs/eosat1/ --port 9091 --host "$SMO_BIND" --connect-host "$UP_HOST" --time-source "$SMO_TIME_SOURCE" --ui "$SMO_UI" &
PLANNER_PID=$!
SUPERVISE+=("Planner:$PLANNER_PID")
wait_for_http "Planner" "http://$PROBE_HOST:9091/api/schedule" "$PLANNER_PID" 40 \
    || die "the planner never became ready"

# Start Delayed TM Viewer (HTTP:8092) — reads workspace/dumps/ on demand
echo "==> Starting Delayed TM viewer on port 8092..."
python "$SCRIPT_DIR/tools/delayed_tm_viewer.py" --port 8092 --dumps "$DUMP_DIR" ${PUBLIC:+--public} &
DTM_PID=$!

# Start Orbit Tools (HTTP:8093) — TLE/state vector to TC command converter
if python -c "import sgp4, numpy, aiohttp" 2>/dev/null; then
    echo "==> Starting Orbit Tools on port 8093..."
    python "$SCRIPT_DIR/tools/orbit_tools.py" --serve --port 8093 &
    ORB_PID=$!
elif [ -d "$SCRIPT_DIR/wheels" ]; then
    # Offline classroom (D-3): a start script must never reach the network.
    # If the vendored wheels are present, install from them; otherwise say
    # exactly what is missing and carry on without Orbit Tools.
    echo "==> Orbit Tools: installing sgp4/numpy/aiohttp from vendored wheels/..."
    pip install -q --no-index --find-links "$SCRIPT_DIR/wheels" sgp4 numpy aiohttp 2>/dev/null || true
    if python -c "import sgp4, numpy, aiohttp" 2>/dev/null; then
        echo "==> Starting Orbit Tools on port 8093..."
        python "$SCRIPT_DIR/tools/orbit_tools.py" --serve --port 8093 &
        ORB_PID=$!
    else
        echo "==> WARNING: Orbit Tools not started — sgp4/numpy/aiohttp missing"
        echo "             and not available in $SCRIPT_DIR/wheels."
    fi
else
    echo "==> WARNING: Orbit Tools not started — sgp4/numpy/aiohttp are not"
    echo "             installed and there is no wheels/ directory to install"
    echo "             them from offline. Run:"
    echo "                 pip install sgp4 numpy aiohttp"
    echo "             once on a networked machine, or populate wheels/."
fi

# Start Documentation Viewer (HTTP:8095)
echo "==> Starting Documentation viewer on port 8095..."
python "$SCRIPT_DIR/tools/doc_viewer.py" --port 8095 --docs "$SCRIPT_DIR/configs/eosat1" &
DOC_PID=$!
fi

if [ "$SMO_PROFILE" != "ground" ]; then
# (profiles all + space: these two belong with the simulator — the scenario
# generator writes the sim's configs/eosat1/scenarios/)
# Start Scenario Generator (HTTP:8096) — authors configs/eosat1/scenarios/*.yaml
echo "==> Starting Scenario Generator on port 8096..."
python "$SCRIPT_DIR/tools/scenario_generator.py" --port 8096 ${PUBLIC:+--host 0.0.0.0} &
SCENGEN_PID=$!

# Start ADCS Failure-Scenario Viewer (HTTP:8097) — offline CERISE debris-strike
# explorer; physics comes from ADCS_failure_sim/cubesat_adcs_sim.py
echo "==> Starting ADCS Failure-Scenario viewer on port 8097..."
python "$SCRIPT_DIR/tools/adcs_sim_viewer.py" --port 8097 ${PUBLIC:+--public} &
ADCS_PID=$!
fi

# The tool viewers are auxiliary: a failure warns rather than aborting the
# class, but it must be *visible* — a printed URL for a port nothing listens
# on is the same "plausible but empty" failure as D-1, one tool down.
check_optional() {
    wait_for_port "$1" "$PROBE_HOST" "$2" "$3" 15 >/dev/null 2>&1 \
        || echo "==> WARNING: $1 did not come up on port $2 — its URL below will not work."
}
if [ "$SMO_PROFILE" != "space" ]; then
check_optional "Delayed TM viewer"   8092 "$DTM_PID"
if [ -n "${ORB_PID:-}" ]; then check_optional "Orbit Tools" 8093 "$ORB_PID"; fi
check_optional "Documentation viewer" 8095 "$DOC_PID"
fi
if [ "$SMO_PROFILE" != "ground" ]; then
check_optional "Scenario Generator"   8096 "$SCENGEN_PID"
check_optional "ADCS Failure viewer"  8097 "$ADCS_PID"
fi

if [ "$SMO_PROFILE" = "all" ]; then
echo ""
echo "========================================="
echo "  SMO Suite Running"
echo "========================================="
echo "  Simulator:        http://$ACCESS_HOST:$SMO_SIM_HTTP_PORT   (classic: /classic  modern: /modern)"
echo "  Config editor:    http://$ACCESS_HOST:$SMO_SIM_HTTP_PORT/config    (instructor, read-write)"
echo "  Report generator: http://$ACCESS_HOST:$SMO_SIM_HTTP_PORT/reports"
if [ "${SMO_VR:-1}" != "0" ]; then
echo "  VR bridge:        tcp://$ACCESS_HOST:${SMO_VR_PORT:-8100}  ws://$ACCESS_HOST:${SMO_VR_WS_PORT:-8101}/vr   (docs/VR_INTERFACE_ICD.md)"
fi
echo "  MCS:              http://$ACCESS_HOST:9090"
echo "    UI generation:  $SMO_UI   (classic: http://$ACCESS_HOST:9090/classic  modern: http://$ACCESS_HOST:9090/modern)"
echo "  MCS reports:      http://$ACCESS_HOST:9090/reports"
echo "  MCS config view:  http://$ACCESS_HOST:9090/config    (read-only)"
echo "  Delayed TM:       http://$ACCESS_HOST:9090/dumps    <- students use this"
echo "  Planner:          http://$ACCESS_HOST:9091   (classic: /classic  modern: /modern)"
echo "  Planner (wide):   http://$ACCESS_HOST:9091/wide"
echo "  Delayed TM view:  http://$ACCESS_HOST:8092          (rich decode/plots)"
if [ -n "${ORB_PID:-}" ]; then
echo "  Orbit Tools:      http://$ACCESS_HOST:8093"
else
echo "  Orbit Tools:      NOT RUNNING (sgp4/numpy/aiohttp unavailable)"
fi
echo "  Documentation:    http://$ACCESS_HOST:8095"
echo "  Scenario Gen:     http://$ACCESS_HOST:8096"
echo "  ADCS Failure Sim: http://$ACCESS_HOST:8097"
echo "  Dump store:       $DUMP_DIR"
echo "  Time source:      $SMO_TIME_SOURCE  (sim_state_url=$SMO_SIM_STATE_URL)"
echo "  UI generation:    $SMO_UI  (--classic/--modern or SMO_UI to change; ?ui= per tab)"
if [ -n "$RFSIM_MSG" ]; then
    echo "$RFSIM_MSG"
    echo "$RADIO_MSG"
fi
echo "========================================="
if [ -n "$PUBLIC" ]; then
    echo "  PUBLIC mode: services bound to $SMO_BIND — reachable from client"
    echo "  machines. Give students the URLs above (see docs/DEPLOYMENT.md)."
else
    echo "  LOCAL mode: simulator, MCS and planner bound to $SMO_BIND."
    echo "  Use --public (or --host=ADDR) for a classroom/server deployment."
fi
echo "========================================="
if [ -n "$RF_MODE" ]; then
    echo "  RF mode: $RF_MODE"
else
    echo "  RF mode: off  (use --rf to enable)"
fi
echo "  Press Ctrl+C to stop all services"
echo "========================================="
echo ""
elif [ "$SMO_PROFILE" = "space" ]; then
echo ""
echo "========================================="
echo "  SMO Suite Running — profile: space"
echo "========================================="
echo "  Simulator:        http://$ACCESS_HOST:$SMO_SIM_HTTP_PORT   (instructor console, local only)"
if [ "${SMO_VR:-1}" != "0" ]; then
echo "  VR bridge:        tcp://$ACCESS_HOST:${SMO_VR_PORT:-8100}  ws://$ACCESS_HOST:${SMO_VR_WS_PORT:-8101}/vr"
fi
echo "  Space-link agent: → $SMO_LINK_URL  (session $SMO_LINK_SESSION, mode ${SMO_LINK_MODE:-complete})"
echo "  Scenario Gen:     http://$ACCESS_HOST:8096"
echo "  ADCS Failure Sim: http://$ACCESS_HOST:8097"
echo "  Dump store:       $DUMP_DIR  (shipped to the ground by the agent)"
echo "  MCS, planner and the ground tools run on the ground host."
echo "========================================="
echo "  Press Ctrl+C to stop all services"
echo "========================================="
echo ""
else
echo ""
echo "========================================="
echo "  SMO Suite Running — profile: ground"
echo "========================================="
echo "  GSG link:         $SMO_GSG_LINK_BIND:$SMO_GSG_LINK_PORT/link   (agent only; HMAC token)"
echo "  GSG status:       http://$GSG_PROBE:$SMO_GSG_HTTP_PORT/link-status   (instructor proxy on the same port; loopback unless SMO_GSG_BIND is set)"
echo "  MCS:              http://$ACCESS_HOST:9090"
echo "  Delayed TM:       http://$ACCESS_HOST:9090/dumps    <- students use this"
echo "  Planner:          http://$ACCESS_HOST:9091"
echo "  Delayed TM view:  http://$ACCESS_HOST:8092"
if [ -n "${ORB_PID:-}" ]; then
echo "  Orbit Tools:      http://$ACCESS_HOST:8093"
else
echo "  Orbit Tools:      NOT RUNNING (sgp4/numpy/aiohttp unavailable)"
fi
echo "  Documentation:    http://$ACCESS_HOST:8095"
echo "  Dump store:       $DUMP_DIR  (written by the GSG)"
echo "  Time source:      $SMO_TIME_SOURCE  (sim_state_url=$SMO_SIM_STATE_URL)"
if [ -n "$RFSIM_MSG" ]; then
    echo "$RFSIM_MSG"
    echo "$RADIO_MSG"
fi
echo "  Until an agent binds, the link is DOWN: the MCS shows no TC connection."
echo "========================================="
echo "  Press Ctrl+C to stop all services"
echo "========================================="
echo ""
fi

# Wait for the FIRST child to exit, then stop everything (D-1). Bare `wait`
# waited for ALL children, so a simulator that died mid-exercise left the MCS
# and planner up, serving a frozen but plausible console. SUPERVISE holds the
# profile's core processes in start order (all: Simulator, MCS, Planner).
while :; do
    for entry in "${SUPERVISE[@]}"; do
        if ! kill -0 "${entry##*:}" 2>/dev/null; then
            echo ""
            echo "==> ${entry%:*} exited — stopping the suite."
            exit 1
        fi
    done
    sleep 2
done
