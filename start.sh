#!/bin/bash
# ═══════════════════════════════════════════════════════
#  DurianDetector IDS — One-Click Startup Script
#  FYP-26-S1-08
# ═══════════════════════════════════════════════════════

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

echo -e "${BLUE}${BOLD}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║       🛡️  DurianDetector IDS  🛡️          ║"
echo "  ║       FYP-26-S1-08 Startup Script        ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${NC}"

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Shutting down DurianDetector...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}All processes stopped. Goodbye!${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

# ─── Check Python ───
echo -e "${BLUE}[1/5]${NC} Checking Python..."
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo -e "${RED}Python not found! Install Python 3.10+ first.${NC}"
    exit 1
fi
echo -e "  ✓ Using $($PYTHON --version)"

# ─── Check Node ───
echo -e "${BLUE}[2/5]${NC} Checking Node.js..."
if ! command -v node &>/dev/null; then
    echo -e "${RED}Node.js not found! Install Node.js 18+ first.${NC}"
    exit 1
fi
echo -e "  ✓ Using Node $(node --version)"

# ─── Install backend deps if needed ───
echo -e "${BLUE}[3/5]${NC} Setting up backend..."
if [ ! -d "$BACKEND_DIR/venv" ] && [ -z "$VIRTUAL_ENV" ]; then
    echo -e "  ${YELLOW}No virtualenv found. Creating one...${NC}"
    $PYTHON -m venv "$BACKEND_DIR/venv"
fi

if [ -d "$BACKEND_DIR/venv" ]; then
    source "$BACKEND_DIR/venv/bin/activate"
    echo -e "  ✓ Activated virtualenv"
fi

# Install requirements if needed
if ! $PYTHON -c "import django" 2>/dev/null; then
    echo -e "  ${YELLOW}Installing Python dependencies...${NC}"
    pip install -r "$BACKEND_DIR/requirements.txt" -q
fi
echo -e "  ✓ Backend dependencies ready"

# ─── Run migrations ───
echo -e "${BLUE}[4/5]${NC} Running database migrations..."
cd "$BACKEND_DIR"
$PYTHON manage.py migrate --run-syncdb -v 0 2>/dev/null
echo -e "  ✓ Database ready"

# ─── Install frontend deps if needed ───
echo -e "${BLUE}[5/5]${NC} Setting up frontend..."
cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ]; then
    echo -e "  ${YELLOW}Installing npm dependencies (first time only)...${NC}"
    npm install --legacy-peer-deps 2>/dev/null
fi
echo -e "  ✓ Frontend dependencies ready"

# ═══════════════════════════════════════════════════════
#  START SERVERS
# ═══════════════════════════════════════════════════════
echo ""
echo -e "${GREEN}${BOLD}Starting DurianDetector...${NC}"
echo ""

# Start Django backend
cd "$BACKEND_DIR"
$PYTHON manage.py runserver 8000 &
BACKEND_PID=$!
echo -e "  ${GREEN}✓${NC} Backend  → ${BOLD}http://127.0.0.1:8000${NC}  (PID: $BACKEND_PID)"

# Start Vite frontend
cd "$FRONTEND_DIR"
npm run dev -- --port 5173 &
FRONTEND_PID=$!
echo -e "  ${GREEN}✓${NC} Frontend → ${BOLD}http://localhost:5173${NC}   (PID: $FRONTEND_PID)"

echo ""
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  DurianDetector is running!${NC}"
echo -e "${GREEN}${BOLD}  Open: ${BLUE}http://localhost:5173${NC}"
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════${NC}"
echo ""
echo -e "  Admin login: ${BOLD}admin@ids.local${NC} / ${BOLD}admin123${NC}"
echo -e "  Press ${RED}Ctrl+C${NC} to stop all servers"
echo ""

# Wait for both processes
wait
