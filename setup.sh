#!/usr/bin/env bash
set -euo pipefail

# AgentTeX Setup Script — Non-Docker Installation
# Usage: bash setup.sh

GREEN='\033[0;32m'
CYAN='\033[0;36m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${CYAN}${BOLD}  ╔══════════════════════════════════════╗${NC}"
echo -e "${CYAN}${BOLD}  ║          AgentTeX Setup              ║${NC}"
echo -e "${CYAN}${BOLD}  ║    Agent-oriented TeX Compiler       ║${NC}"
echo -e "${CYAN}${BOLD}  ╚══════════════════════════════════════╝${NC}"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# --- Check dependencies ---
check_cmd() {
    if command -v "$1" &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $1 found"
        return 0
    else
        echo -e "  ${DIM}✗${NC} $1 not found"
        return 1
    fi
}

echo -e "${BOLD}Checking dependencies...${NC}"
MISSING=0

check_cmd python3 || MISSING=1
check_cmd pip3 || MISSING=1
check_cmd node || MISSING=1
check_cmd npm || MISSING=1
check_cmd redis-server || MISSING=1
check_cmd latexmk || MISSING=1

if [ "$MISSING" -eq 1 ]; then
    echo ""
    echo -e "${DIM}Some dependencies are missing. Install them with:${NC}"
    echo ""
    echo "  # Ubuntu/Debian:"
    echo "  sudo apt install python3 python3-pip nodejs npm redis-server texlive-full"
    echo ""
    echo "  # macOS:"
    echo "  brew install python node redis texlive"
    echo ""
    echo "  Then re-run this script."
    exit 1
fi

echo ""

# --- Backend ---
echo -e "${BOLD}Setting up backend...${NC}"
python3 -m venv .venv 2>/dev/null || true
source .venv/bin/activate
pip install -q -r backend/requirements.txt
echo -e "  ${GREEN}✓${NC} Python dependencies installed"

# --- Frontend ---
echo -e "${BOLD}Building frontend...${NC}"
cd frontend
npm install --silent 2>/dev/null
npm run build 2>/dev/null
cd "$SCRIPT_DIR"
rm -rf backend/static
cp -r frontend/dist backend/static
echo -e "  ${GREEN}✓${NC} Frontend built"

# --- Data dirs ---
mkdir -p data/{uploads,projects,output}

# --- Env ---
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "  ${GREEN}✓${NC} Created .env from .env.example"
else
    echo -e "  ${GREEN}✓${NC} .env already exists"
fi

echo ""
echo -e "${GREEN}${BOLD}Setup complete!${NC}"
echo ""
echo "  Start the service:"
echo -e "    ${CYAN}bash start.sh${NC}"
echo ""
echo "  Or individually:"
echo -e "    ${DIM}source .venv/bin/activate${NC}"
echo -e "    ${DIM}redis-server &${NC}"
echo -e "    ${DIM}uvicorn backend.app.main:app --port 8000 &${NC}"
echo -e "    ${DIM}celery -A backend.app.tasks.celery_app worker --loglevel=info &${NC}"
echo ""
echo -e "  Open ${CYAN}http://localhost:8000${NC}"
echo ""
