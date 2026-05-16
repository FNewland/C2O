#!/usr/bin/env bash
# ============================================================================
# SpaceCDF — Automated Installation Script (macOS / Linux)
# ============================================================================
#
# Usage:
#   chmod +x install.sh
#   ./install.sh              # Full install (backend + frontend)
#   ./install.sh --backend    # Backend only
#   ./install.sh --frontend   # Frontend only
#   ./install.sh --docker     # Docker Compose setup
#   ./install.sh --check      # Check prerequisites only
#   ./install.sh --ai         # Include optional AI package (spacecdf-ai)
#
# Requirements: Python 3.11+, Node.js 18+, Git
# ============================================================================

set -euo pipefail

# ── Colours ─────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No colour

# ── Globals ─────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_BACKEND=true
INSTALL_FRONTEND=true
INSTALL_AI=false
DOCKER_MODE=false
CHECK_ONLY=false

# ── Helpers ─────────────────────────────────────────────────────────────────
info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail()    { echo -e "${RED}[FAIL]${NC}  $*"; }
header()  { echo -e "\n${BOLD}━━━ $* ━━━${NC}\n"; }

die() {
    fail "$@"
    exit 1
}

# ── Parse arguments ─────────────────────────────────────────────────────────
for arg in "$@"; do
    case "$arg" in
        --backend)  INSTALL_BACKEND=true;  INSTALL_FRONTEND=false ;;
        --frontend) INSTALL_BACKEND=false; INSTALL_FRONTEND=true  ;;
        --docker)   DOCKER_MODE=true ;;
        --ai)       INSTALL_AI=true ;;
        --check)    CHECK_ONLY=true ;;
        --help|-h)
            echo "Usage: $0 [--backend|--frontend|--docker|--ai|--check|--help]"
            exit 0
            ;;
        *) die "Unknown option: $arg" ;;
    esac
done

# ── Version comparison ──────────────────────────────────────────────────────
version_ge() {
    # Returns 0 (true) if $1 >= $2 using semantic versioning
    printf '%s\n%s' "$2" "$1" | sort -t. -k1,1n -k2,2n -k3,3n -C
}

# ── Prerequisite checks ────────────────────────────────────────────────────
check_prerequisites() {
    header "Checking prerequisites"
    local ok=true

    # Python
    if command -v python3 &>/dev/null; then
        PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')
        PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
        if [ "$PY_MINOR" -ge 11 ]; then
            success "Python $PY_VERSION"
        else
            fail "Python $PY_VERSION — need 3.11 or later"
            ok=false
        fi
    else
        fail "Python 3 not found"
        echo "       Install: https://www.python.org/downloads/"
        echo "       macOS:   brew install python@3.12"
        echo "       Ubuntu:  sudo apt install python3 python3-pip python3-venv"
        ok=false
    fi

    # Node.js
    if command -v node &>/dev/null; then
        NODE_VERSION=$(node --version | sed 's/^v//')
        NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d. -f1)
        if [ "$NODE_MAJOR" -ge 18 ]; then
            success "Node.js $NODE_VERSION"
        else
            fail "Node.js $NODE_VERSION — need 18 or later"
            ok=false
        fi
    else
        fail "Node.js not found"
        echo "       Install: https://nodejs.org/en/download"
        echo "       macOS:   brew install node"
        ok=false
    fi

    # npm
    if command -v npm &>/dev/null; then
        success "npm $(npm --version)"
    else
        fail "npm not found (should come with Node.js)"
        ok=false
    fi

    # Git
    if command -v git &>/dev/null; then
        success "Git $(git --version | awk '{print $3}')"
    else
        fail "Git not found"
        echo "       Install: https://git-scm.com/downloads"
        ok=false
    fi

    # Docker (only if docker mode)
    if $DOCKER_MODE; then
        if command -v docker &>/dev/null && command -v docker-compose &>/dev/null || docker compose version &>/dev/null 2>&1; then
            success "Docker $(docker --version | awk '{print $3}' | tr -d ',')"
        else
            fail "Docker or docker-compose not found"
            echo "       Install: https://docs.docker.com/get-docker/"
            ok=false
        fi
    fi

    echo ""
    if $ok; then
        success "All prerequisites satisfied"
    else
        die "Missing prerequisites — install them and re-run this script"
    fi
}

# ── Backend installation ────────────────────────────────────────────────────
install_backend() {
    header "Installing Python backend"
    cd "$SCRIPT_DIR"

    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        info "Creating Python virtual environment..."
        python3 -m venv .venv
        success "Virtual environment created at .venv/"
    else
        info "Virtual environment already exists"
    fi

    # Activate
    source .venv/bin/activate
    info "Virtual environment activated"

    # Upgrade pip
    info "Upgrading pip..."
    pip install --upgrade pip setuptools wheel --quiet

    # Install packages in dependency order
    info "Installing spacecdf-common..."
    pip install -e packages/spacecdf-common --quiet
    success "spacecdf-common installed"

    info "Installing spacecdf-kb..."
    pip install -e packages/spacecdf-kb --quiet
    success "spacecdf-kb installed"

    info "Installing spacecdf-agents..."
    pip install -e packages/spacecdf-agents --quiet
    success "spacecdf-agents installed"

    info "Installing spacecdf-server..."
    pip install -e packages/spacecdf-server --quiet
    success "spacecdf-server installed"

    # Optional AI package
    if $INSTALL_AI; then
        info "Installing spacecdf-ai (optional AI capabilities)..."
        pip install -e packages/spacecdf-ai --quiet
        success "spacecdf-ai installed"
        warn "Set ANTHROPIC_API_KEY in .env to enable AI features"
    fi

    # Create .env from example if it doesn't exist
    if [ ! -f ".env" ] && [ -f ".env.example" ]; then
        cp .env.example .env
        info "Created .env from .env.example — edit it to configure your instance"
    fi

    # Smoke test
    header "Running backend smoke test"
    if python -c "from spacecdf_common.models import Mission; print('  spacecdf-common: OK')" 2>/dev/null; then
        success "spacecdf-common imports OK"
    else
        warn "spacecdf-common import failed — check installation"
    fi

    if python -c "from spacecdf_server.app import app; print('  spacecdf-server: OK')" 2>/dev/null; then
        success "spacecdf-server imports OK"
    else
        warn "spacecdf-server import failed — check installation"
    fi

    # Run design smoke test if config exists
    if [ -f "scripts/run_design.py" ] && [ -f "configs/examples/6u_eo_cubesat.yaml" ]; then
        info "Running design loop smoke test..."
        if python scripts/run_design.py configs/examples/6u_eo_cubesat.yaml > /dev/null 2>&1; then
            success "Design loop converges — backend is working"
        else
            warn "Design loop smoke test failed — backend may have issues"
        fi
    fi
}

# ── Frontend installation ───────────────────────────────────────────────────
install_frontend() {
    header "Installing frontend (React + Vite)"
    cd "$SCRIPT_DIR/frontend"

    info "Installing npm dependencies..."
    npm install --loglevel warn
    success "Frontend dependencies installed"

    # Quick build check
    info "Verifying TypeScript compilation..."
    if npx tsc --noEmit 2>/dev/null; then
        success "TypeScript compilation OK"
    else
        warn "TypeScript has some type errors — the dev server will still work"
    fi
}

# ── Docker installation ────────────────────────────────────────────────────
install_docker() {
    header "Setting up Docker environment"
    cd "$SCRIPT_DIR"

    if [ ! -f "Dockerfile" ]; then
        die "Dockerfile not found — run this script without --docker first"
    fi

    # Create .env from example if it doesn't exist
    if [ ! -f ".env" ] && [ -f ".env.example" ]; then
        cp .env.example .env
        info "Created .env from .env.example"
    fi

    info "Building and starting containers..."
    if docker compose version &>/dev/null 2>&1; then
        docker compose up --build -d
    else
        docker-compose up --build -d
    fi

    success "Containers started"
    echo ""
    info "SpaceCDF is running at:"
    echo "    Backend API:  http://localhost:8000"
    echo "    API docs:     http://localhost:8000/docs"
    echo "    PostgreSQL:   localhost:5432"
    echo "    Redis:        localhost:6379"
    echo ""
    warn "Frontend is not included in Docker — run it locally:"
    echo "    cd frontend && npm install && npm run dev"
}

# ── Summary ─────────────────────────────────────────────────────────────────
print_summary() {
    header "Installation complete"

    echo -e "${GREEN}SpaceCDF is ready to use.${NC}\n"

    echo "To start SpaceCDF:"
    echo ""
    echo "  Option 1 — Quick start (both servers):"
    echo "    ./scripts/start.sh"
    echo ""
    echo "  Option 2 — Manual start (two terminals):"
    echo "    Terminal 1 (backend):"
    echo "      source .venv/bin/activate"
    echo "      uvicorn spacecdf_server.app:app --reload --port 8000"
    echo ""
    echo "    Terminal 2 (frontend):"
    echo "      cd frontend && npm run dev"
    echo ""
    echo "  Then open: http://localhost:5173"
    echo ""

    if $INSTALL_AI; then
        echo "  AI features: Set ANTHROPIC_API_KEY in .env"
        echo "  AI config:   Edit configs/genai.yaml"
        echo ""
    fi

    echo "  API docs:    http://localhost:8000/docs"
    echo "  Design test: python scripts/run_design.py configs/examples/6u_eo_cubesat.yaml"
    echo ""
}

# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

echo -e "${BOLD}"
echo "  ╔═══════════════════════════════════════════════════════════╗"
echo "  ║              SpaceCDF — Installation Script               ║"
echo "  ║       AI-Powered Concurrent Design Facility               ║"
echo "  ╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

check_prerequisites

if $CHECK_ONLY; then
    exit 0
fi

if $DOCKER_MODE; then
    install_docker
    exit 0
fi

if $INSTALL_BACKEND; then
    install_backend
fi

if $INSTALL_FRONTEND; then
    install_frontend
fi

print_summary
