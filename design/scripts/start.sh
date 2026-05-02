#!/bin/bash
# SpaceCDF — Start both backend and frontend dev servers
#
# Usage:
#   ./scripts/start.sh          # Start both servers
#   ./scripts/start.sh backend  # Backend only
#   ./scripts/start.sh frontend # Frontend only
#   ./scripts/start.sh design   # Run design loop (no servers needed)

set -e
cd "$(dirname "$0")/.."
ROOT=$(pwd)

# Ensure venv exists
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install fastapi 'uvicorn[standard]' pydantic pyyaml numpy scipy sgp4 jinja2 python-docx
else
    source .venv/bin/activate
fi

export PYTHONPATH="$ROOT/packages/spacecdf-common/src:$ROOT/packages/spacecdf-agents/src:$ROOT/packages/spacecdf-kb/src:$ROOT/packages/spacecdf-server/src"

case "${1:-both}" in
    backend)
        echo "Starting SpaceCDF backend on http://localhost:8000"
        echo "  API docs: http://localhost:8000/docs"
        uvicorn spacecdf_server.app:app --reload --host 0.0.0.0 --port 8000
        ;;
    frontend)
        echo "Starting SpaceCDF frontend on http://localhost:5173"
        echo "  Remote access: http://$(tailscale ip -4 2>/dev/null || echo 'your-ip'):5173"
        cd frontend && npm run dev -- --host 0.0.0.0
        ;;
    design)
        echo "Running design loop..."
        python3 scripts/run_design.py "${2:-configs/examples/6u_eo_cubesat.yaml}"
        ;;
    both)
        echo "Starting SpaceCDF..."
        echo "  Backend:  http://localhost:8000 (API docs: http://localhost:8000/docs)"
        echo "  Frontend: http://localhost:5173"
        echo ""
        # Start backend in background
        uvicorn spacecdf_server.app:app --reload --host 0.0.0.0 --port 8000 &
        BACKEND_PID=$!
        # Start frontend
        cd frontend && npm run dev -- --host 0.0.0.0 &
        FRONTEND_PID=$!
        # Wait for either to exit
        trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
        wait
        ;;
    *)
        echo "Usage: $0 [backend|frontend|design|both]"
        exit 1
        ;;
esac
