#!/bin/bash
# ============================================================================
# DurianDetector — 5-Computer Live Demo Setup Script
# ============================================================================
#
# This script sets up the full demo environment on PC1 (the server).
# Other computers on the LAN connect via browser to:
#   Frontend:  http://<LAN-IP>:5173
#   Backend:   http://<LAN-IP>:8000
#
# Prerequisites:
#   - Docker & Docker Compose installed
#   - Python 3.10+ with virtualenv activated
#   - Node.js 18+ with npm
#   - pip install -r requirements.txt (backend deps)
#   - npm install (frontend deps)
#
# Usage:
#   chmod +x demo-setup.sh
#   ./demo-setup.sh
#
# Login credentials (printed at end):
#   Admin:     admin@ids.local     / admin123
#   Free:      free@demo.local     / demo123
#   Premium:   premium@demo.local  / demo123
#   Exclusive: exclusive@demo.local / demo123
# ============================================================================

set -e

# ── Paths ──
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.demo.yml"

# ── Activate Python virtualenv ──
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
    echo "  Activated virtualenv: $SCRIPT_DIR/venv"
elif [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
    echo "  Activated virtualenv: $SCRIPT_DIR/.venv"
else
    echo "  WARNING: No virtualenv found. Using system Python."
fi

# ── Colors ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ── Ensure Docker is available (macOS Docker Desktop PATH) ──
if ! command -v docker &>/dev/null; then
    # Docker Desktop on macOS — check all known install locations
    if [ -f "/usr/local/bin/docker" ]; then
        export PATH="/usr/local/bin:$PATH"
    elif [ -f "$HOME/.docker/bin/docker" ]; then
        export PATH="$HOME/.docker/bin:$PATH"
    elif [ -f "/opt/homebrew/bin/docker" ]; then
        export PATH="/opt/homebrew/bin:$PATH"
    elif [ -f "/Applications/Docker.app/Contents/Resources/bin/docker" ]; then
        export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
    else
        echo -e "${RED}✗ Docker is not installed.${NC}"
        echo ""
        echo "  Please install Docker Desktop from:"
        echo "  https://www.docker.com/products/docker-desktop/"
        echo ""
        echo "  After installing, open Docker Desktop and wait for it to start,"
        echo "  then re-run this script."
        exit 1
    fi
fi

# ── Verify Docker daemon is running; auto-start Docker Desktop on macOS ──
if ! docker info &>/dev/null 2>&1; then
    if [ -d "/Applications/Docker.app" ]; then
        echo -e "${YELLOW}  Docker Desktop is not running. Starting it now...${NC}"
        open -a Docker
        echo "  Waiting for Docker daemon to be ready..."
        DOCKER_RETRIES=0
        while ! docker info &>/dev/null 2>&1; do
            DOCKER_RETRIES=$((DOCKER_RETRIES + 1))
            if [ $DOCKER_RETRIES -ge 60 ]; then
                echo -e "${RED}  ✗ Docker daemon did not start after 120 seconds.${NC}"
                exit 1
            fi
            sleep 2
        done
        echo -e "${GREEN}  ✓ Docker Desktop is running${NC}"
    else
        echo -e "${RED}✗ Docker is installed but the daemon is not running.${NC}"
        echo ""
        echo "  Please open Docker Desktop and wait for it to start (whale icon in menu bar),"
        echo "  then re-run this script."
        exit 1
    fi
fi

# ── PIDs for cleanup ──
CELERY_PID=""
DJANGO_PID=""
VITE_PID=""

cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down demo services...${NC}"

    if [ -n "$VITE_PID" ] && kill -0 "$VITE_PID" 2>/dev/null; then
        kill "$VITE_PID" 2>/dev/null
        echo "  Stopped Vite dev server"
    fi

    if [ -n "$DJANGO_PID" ] && kill -0 "$DJANGO_PID" 2>/dev/null; then
        kill "$DJANGO_PID" 2>/dev/null
        echo "  Stopped Django server"
    fi

    if [ -n "$CELERY_PID" ] && kill -0 "$CELERY_PID" 2>/dev/null; then
        kill "$CELERY_PID" 2>/dev/null
        echo "  Stopped Celery worker"
    fi

    echo -e "${YELLOW}Stopping Docker containers...${NC}"
    docker compose -f "$COMPOSE_FILE" down 2>/dev/null || true

    echo -e "${GREEN}✅ Demo shutdown complete.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# ── Detect LAN IP ──
get_lan_ip() {
    # macOS
    if command -v ipconfig &>/dev/null; then
        ip=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "")
        if [ -n "$ip" ]; then
            echo "$ip"
            return
        fi
    fi
    # Linux
    if command -v hostname &>/dev/null; then
        ip=$(hostname -I 2>/dev/null | awk '{print $1}')
        if [ -n "$ip" ]; then
            echo "$ip"
            return
        fi
    fi
    # Fallback
    echo "127.0.0.1"
}

LAN_IP=$(get_lan_ip)

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║       🍈 DurianDetector — 5-Computer Live Demo Setup       ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  LAN IP: ${GREEN}$LAN_IP${NC}"
echo ""

# ── Set Django settings ──
export DJANGO_SETTINGS_MODULE=config.settings.demo

# ============================================================================
# Step 1: Start Docker (PostgreSQL + Redis)
# ============================================================================
echo -e "${CYAN}[1/7] Starting Docker containers (PostgreSQL + Redis)...${NC}"

docker compose -f "$COMPOSE_FILE" up -d

echo -e "${GREEN}  ✓ Docker containers started${NC}"

# ============================================================================
# Step 2: Wait for PostgreSQL to be ready
# ============================================================================
echo -e "${CYAN}[2/7] Waiting for PostgreSQL to be ready...${NC}"

MAX_RETRIES=30
RETRY=0
until docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U demo_user -q 2>/dev/null; do
    RETRY=$((RETRY + 1))
    if [ $RETRY -ge $MAX_RETRIES ]; then
        echo -e "${RED}  ✗ PostgreSQL failed to start after $MAX_RETRIES attempts.${NC}"
        exit 1
    fi
    echo "  Waiting... ($RETRY/$MAX_RETRIES)"
    sleep 2
done

echo -e "${GREEN}  ✓ PostgreSQL is ready${NC}"

# Give it an extra moment for the init script to create additional databases
sleep 3

# ============================================================================
# Step 3: Run migrations on all 3 databases
# ============================================================================
echo -e "${CYAN}[3/7] Running database migrations...${NC}"

cd "$BACKEND_DIR"

echo "  Migrating default (free_db)..."
python3 manage.py migrate --database=default --no-input

echo "  Migrating free_db..."
python3 manage.py migrate --database=free_db --no-input

echo "  Migrating premium_db..."
python3 manage.py migrate --database=premium_db --no-input

echo "  Migrating exclusive_db..."
python3 manage.py migrate --database=exclusive_db --no-input

echo -e "${GREEN}  ✓ All databases migrated${NC}"

# ============================================================================
# Step 4: Seed data into all databases
# ============================================================================
echo -e "${CYAN}[4/7] Seeding demo data...${NC}"

# Seed demo users, MITRE, threats, plans, environments, subscriptions (all DBs)
python3 manage.py seed_demo_users

echo -e "${GREEN}  ✓ Demo data seeded${NC}"

# ============================================================================
# Step 5: Start Celery worker
# ============================================================================
echo -e "${CYAN}[5/7] Starting Celery worker...${NC}"

cd "$BACKEND_DIR"
celery -A config worker -l info --concurrency=2 &
CELERY_PID=$!

sleep 3

if kill -0 "$CELERY_PID" 2>/dev/null; then
    echo -e "${GREEN}  ✓ Celery worker running (PID: $CELERY_PID)${NC}"
else
    echo -e "${YELLOW}  ⚠ Celery may not have started. Demo mode still works without it.${NC}"
    CELERY_PID=""
fi

# ============================================================================
# Step 6: Start Django (backend) on 0.0.0.0:8000
# ============================================================================
echo -e "${CYAN}[6/7] Starting Django backend on 0.0.0.0:8000...${NC}"

cd "$BACKEND_DIR"
python3 manage.py runserver 0.0.0.0:8000 &
DJANGO_PID=$!

sleep 3

if kill -0 "$DJANGO_PID" 2>/dev/null; then
    echo -e "${GREEN}  ✓ Django backend running (PID: $DJANGO_PID)${NC}"
else
    echo -e "${RED}  ✗ Django failed to start.${NC}"
    cleanup
fi

# ============================================================================
# Step 7: Start Vite (frontend) on 0.0.0.0:5173
# ============================================================================
echo -e "${CYAN}[7/7] Starting Vite frontend on 0.0.0.0:5173...${NC}"

cd "$FRONTEND_DIR"
npx vite --host 0.0.0.0 &
VITE_PID=$!

sleep 3

if kill -0 "$VITE_PID" 2>/dev/null; then
    echo -e "${GREEN}  ✓ Vite frontend running (PID: $VITE_PID)${NC}"
else
    echo -e "${RED}  ✗ Vite failed to start.${NC}"
    cleanup
fi

# ============================================================================
# Done — Print access info
# ============================================================================
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║              🍈 Demo Environment Ready!                    ║${NC}"
echo -e "${CYAN}╠══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║${NC}  Frontend:  ${GREEN}http://$LAN_IP:5173${NC}                       ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  Backend:   ${GREEN}http://$LAN_IP:8000${NC}                       ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  API Docs:  ${GREEN}http://$LAN_IP:8000/api/${NC}                  ${CYAN}║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}╠══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║${NC}  ${YELLOW}Login Credentials:${NC}                                     ${CYAN}║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║${NC}  PC1 Admin:     ${GREEN}admin@ids.local${NC}     / ${GREEN}admin123${NC}         ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  PC2 Free:      ${GREEN}free@demo.local${NC}     / ${GREEN}demo123${NC}          ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  PC3 Premium:   ${GREEN}premium@demo.local${NC}  / ${GREEN}demo123${NC}          ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  PC4 Exclusive: ${GREEN}exclusive@demo.local${NC} / ${GREEN}demo123${NC}         ${CYAN}║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}╠══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║${NC}  ${YELLOW}PC5 Attack Commands (run from attacker PC):${NC}               ${CYAN}║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║${NC}  Port scan:  ${RED}nmap -sS -p 1-1000 $LAN_IP${NC}               ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  DoS:        ${RED}hping3 -S --flood -p 80 $LAN_IP${NC}          ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  Brute SSH:  ${RED}hydra -l root -P wordlist.txt $LAN_IP ssh${NC} ${CYAN}║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}╠══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║${NC}  ${YELLOW}Press Ctrl+C to stop all services${NC}                        ${CYAN}║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Wait forever — Ctrl+C triggers cleanup
wait
