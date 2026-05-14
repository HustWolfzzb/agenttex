#!/usr/bin/env bash
set -euo pipefail

# AgentTeX Start Script
# Usage: bash start.sh [--dev]

GREEN='\033[0;32m'
CYAN='\033[0;36m'
DIM='\033[2m'
BOLD='\033[1m'
YELLOW='\033[0;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

DEV_MODE=false
[[ "${1:-}" == "--dev" ]] && DEV_MODE=true

echo ""
echo -e "${CYAN}${BOLD}  ◈ AgentTeX${NC}  ${DIM}starting...${NC}"
echo ""

# Source env
set -a; [ -f .env ] && source .env; set +a

# Activate venv if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Ensure data dirs
mkdir -p data/{uploads,projects,output}

# Check Redis
if ! redis-cli ping &>/dev/null; then
    echo -e "${YELLOW}Starting Redis...${NC}"
    redis-server --daemonize yes 2>/dev/null || true
    sleep 1
fi

# Load config
PORT="${AGENTTEX_PORT:-8000}"

# Cleanup function
cleanup() {
    echo ""
    echo -e "${DIM}Stopping services...${NC}"
    kill $(jobs -p) 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

if [ "$DEV_MODE" = true ]; then
    echo -e "${BOLD}Development mode${NC}"
    echo -e "  Frontend:  ${CYAN}http://localhost:5173${NC}"
    echo -e "  Backend:   ${CYAN}http://localhost:${PORT}${NC}"
    echo -e "  API Docs:  ${CYAN}http://localhost:${PORT}/docs${NC}"
    echo ""
    echo -e "${DIM}Press Ctrl+C to stop${NC}"
    echo ""

    uvicorn backend.app.main:app --host 127.0.0.1 --port "$PORT" --reload &
    celery -A backend.app.tasks.celery_app worker --loglevel=info --concurrency=1 -n dev@%h &
    cd frontend && npm run dev &
    cd "$SCRIPT_DIR"
else
    echo -e "${BOLD}Production mode${NC}"
    echo -e "  URL:       ${CYAN}http://localhost:${PORT}${NC}"
    echo -e "  API Docs:  ${CYAN}http://localhost:${PORT}/docs${NC}"
    echo ""
    echo -e "${DIM}Press Ctrl+C to stop${NC}"
    echo ""

    uvicorn backend.app.main:app --host "${AGENTTEX_HOST:-127.0.0.1}" --port "$PORT" &
    celery -A backend.app.tasks.celery_app worker --loglevel=info --concurrency=1 &
fi

wait
