#!/bin/bash
# ═══════════════════════════════════════════════════════
#  DurianDetector IDS — One-Click Startup Script
#  FYP-26-S1-08
# ═══════════════════════════════════════════════════════

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
echo "  ╔══════════════════════════════════════╗"
echo "  ║                                      ║"
echo "  ║      DurianDetector IDS  [v1.0]      ║"
echo "  ║      FYP-26-S1-08 Startup Script     ║"
echo "  ║                                      ║"
echo "  ╚══════════════════════════════════════╝"
echo -e "${NC}"

# Cleanup function — kill all child processes on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down DurianDetector...${NC}"
    kill $REDIS_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null
    # Celery runs as root on macOS, needs sudo to kill
    if [ -n "$CELERY_PID" ]; then
        sudo kill $CELERY_PID 2>/dev/null
    fi
    echo -e "${GREEN}All processes stopped. Goodbye!${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

# ─── Check Python ───
echo -e "${BLUE}[1/6]${NC} Checking Python..."
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
echo -e "${BLUE}[2/6]${NC} Checking Node.js..."
if ! command -v node &>/dev/null; then
    echo -e "${RED}Node.js not found! Install Node.js 18+ first.${NC}"
    exit 1
fi
echo -e "  ✓ Using Node $(node --version)"

# ─── Install backend deps if needed ───
echo -e "${BLUE}[3/6]${NC} Setting up backend..."
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
echo -e "${BLUE}[4/6]${NC} Running database migrations..."
cd "$BACKEND_DIR"
MIGRATE_FAIL=0
for DB in default free_db premium_db exclusive_db; do
    timeout 30 $PYTHON manage.py migrate --database=$DB -v 0 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "  ✓ $DB migrated"
    else
        # Check if DB is simply already up to date
        STATUS=$(timeout 10 $PYTHON manage.py showmigrations --database=$DB 2>/dev/null | grep -c "\[ \]")
        if [ "$STATUS" = "0" ] 2>/dev/null; then
            echo -e "  ✓ $DB already up to date"
        else
            echo -e "  ${YELLOW}⚠ $DB had issues (${STATUS} pending)${NC}"
            MIGRATE_FAIL=$((MIGRATE_FAIL + 1))
        fi
    fi
done
if [ "$MIGRATE_FAIL" -eq 0 ]; then
    echo -e "  ${GREEN}✓ All databases ready${NC}"
fi

# ─── Install frontend deps if needed ───
echo -e "${BLUE}[5/6]${NC} Setting up frontend..."
cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ]; then
    echo -e "  ${YELLOW}Installing npm dependencies (first time only)...${NC}"
    npm install --legacy-peer-deps 2>/dev/null
fi
echo -e "  ✓ Frontend dependencies ready"

# ─── Start Redis ───
echo -e "${BLUE}[6/6]${NC} Starting Redis..."
if command -v /opt/homebrew/bin/redis-server &>/dev/null; then
    REDIS_CMD="/opt/homebrew/bin/redis-server"
elif command -v redis-server &>/dev/null; then
    REDIS_CMD="redis-server"
else
    REDIS_CMD=""
fi

if [ -n "$REDIS_CMD" ]; then
    # Check if Redis is already running
    if /opt/homebrew/bin/redis-cli ping 2>/dev/null | grep -q PONG; then
        echo -e "  ✓ Redis already running"
        REDIS_PID=""
    else
        $REDIS_CMD --daemonize no --loglevel warning > /dev/null 2>&1 &
        REDIS_PID=$!
        sleep 1
        echo -e "  ✓ Redis started (PID: $REDIS_PID)"
    fi
else
    echo -e "  ${YELLOW}Redis not found, skipping (install: brew install redis)${NC}"
    REDIS_PID=""
fi

# ═══════════════════════════════════════════════════════
#  START SERVERS
# ═══════════════════════════════════════════════════════
echo ""
echo -e "${GREEN}${BOLD}Starting DurianDetector...${NC}"
echo ""

# Start Django backend
cd "$BACKEND_DIR"
daphne -b 0.0.0.0 -p 8000 config.asgi:application &
BACKEND_PID=$!
echo -e "  ${GREEN}✓${NC} Backend  → ${BOLD}http://127.0.0.1:8000${NC}  (PID: $BACKEND_PID)"

# Start Celery worker (with sudo for packet capture on macOS)
cd "$BACKEND_DIR"
CELERY_BIN="$(which celery)"
if [ "$(uname)" = "Darwin" ]; then
    echo -e "  ${YELLOW}Celery needs sudo for packet capture on macOS...${NC}"
    # Cache sudo credentials first (prompts for password in foreground)
    sudo -v
    sudo -E "$CELERY_BIN" -A config worker --loglevel=info > /tmp/celery.log 2>&1 &
    CELERY_PID=$!
else
    celery -A config worker --loglevel=info > /tmp/celery.log 2>&1 &
    CELERY_PID=$!
fi
sleep 3
# Verify Celery actually started
if kill -0 $CELERY_PID 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Celery   → Worker started (PID: $CELERY_PID)"
else
    echo -e "  ${RED}✗${NC} Celery   → Failed to start (check /tmp/celery.log)"
fi

# Build & serve frontend (production mode = faster page loads)
cd "$FRONTEND_DIR"
echo -e "  ${YELLOW}Building frontend for production...${NC}"
npm run build 2>/dev/null
npx vite preview --port 5173 &
FRONTEND_PID=$!
echo -e "  ${GREEN}✓${NC} Frontend → ${BOLD}http://localhost:5173${NC}   (PID: $FRONTEND_PID)"

# ─── Seed data and setup (runs in background) ───
cd "$BACKEND_DIR"
$PYTHON manage.py setup_admin 2>/dev/null
$PYTHON manage.py seed_mitre > /dev/null 2>&1 &
$PYTHON manage.py seed_threats > /dev/null 2>&1 &

# ─── Auto-start capture after Django is ready ───
IFACE="en0"
if [ "$(uname)" != "Darwin" ]; then IFACE="eth0"; fi
(
    # Wait for Django to be ready
    for i in $(seq 1 30); do
        if curl -s http://127.0.0.1:8000/api/auth/login/ > /dev/null 2>&1; then break; fi
        sleep 2
    done
    # Login and start capture
    TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login/ \
        -H "Content-Type: application/json" \
        -d '{"email":"admin@ids.local","password":"admin123"}' 2>/dev/null | \
        $PYTHON -c "import sys,json; print(json.load(sys.stdin).get('tokens',{}).get('access',''))" 2>/dev/null)
    if [ -n "$TOKEN" ] && [ "$TOKEN" != "" ]; then
        curl -s -X POST http://127.0.0.1:8000/api/capture/start/ \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $TOKEN" \
            -d "{\"interface\":\"$IFACE\"}" > /dev/null 2>&1
    fi
) &
echo -e "  ${GREEN}✓${NC} Background setup (MITRE, threats, environment, auto-capture)..."

echo ""
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  DurianDetector is running!${NC}"
echo -e "${GREEN}${BOLD}  Open: ${BLUE}http://localhost:5173${NC}"
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}Demo Accounts:${NC}"
echo -e "  ──────────────────────────────────────────"
echo -e "  Admin:     ${BOLD}admin@ids.local${NC}      / ${BOLD}admin123${NC}"
echo -e "  Free:      ${BOLD}free@demo.local${NC}      / ${BOLD}demo123${NC}"
echo -e "  Premium:   ${BOLD}premium@demo.local${NC}   / ${BOLD}demo123${NC}"
echo -e "  Exclusive: ${BOLD}exclusive@demo.local${NC} / ${BOLD}demo123${NC}"
echo -e "  ──────────────────────────────────────────"
echo -e "  Press ${RED}Ctrl+C${NC} to stop all servers"
echo ""

# Wait for all processes
wait
