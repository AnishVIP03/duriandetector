# DurianDetector — 5-Computer Live Demo Plan

## Setup Overview

| Computer | Role | What it runs |
|----------|------|-------------|
| **PC 1** | Server + Admin | Django + PostgreSQL + Redis + Celery + Vite. Admin logs in here. |
| **PC 2** | Free User | Browser → `http://<PC1-IP>:5173`. Free tier account. |
| **PC 3** | Premium User | Browser → `http://<PC1-IP>:5173`. Premium tier account. |
| **PC 4** | Exclusive User | Browser → `http://<PC1-IP>:5173`. Exclusive tier account. |
| **PC 5** | Attacker | Runs nmap, hping3, hydra targeting PC 1's IP. |

All 5 PCs on the **same WiFi/LAN**.

---

## Implementation Steps

### Step 1 — Demo Settings (`backend/config/settings/demo.py`)
- PostgreSQL: `duriandetector_demo` database
- Redis channel layer (for WebSocket broadcasting across network)
- `ALLOWED_HOSTS = ['*']`, open CORS for LAN
- Django binds to `0.0.0.0:8000`

### Step 2 — Dynamic Frontend URLs
- `frontend/src/api/client.js`: Change `127.0.0.1` → `window.location.hostname`
- `frontend/src/hooks/useWebSocket.js`: Change hardcoded WS URL → dynamic
- Vite serves on `0.0.0.0:5173` with `--host`

### Step 3 — Backend Subscription Enforcement
- Add `SubscriptionRequired` permission class to gated views
- Free: dashboard, alerts, basic features
- Premium: + ML config, incidents, reports, MITRE, packets
- Exclusive: + chatbot, globe, attack chains, team, audit
- Return 403 with "upgrade required" message

### Step 4 — Frontend Tier Gating
- `TierGate` wrapper component checks user role
- Shows "Upgrade Required" modal for locked features
- Sidebar shows lock icons on inaccessible items

### Step 5 — Demo User Accounts
- Management command `seed_demo_users` creates:
  - `admin@ids.local / admin123` (admin, exclusive tier)
  - `free@demo.local / demo123` (analyst, free tier)
  - `premium@demo.local / demo123` (analyst, premium tier)
  - `exclusive@demo.local / demo123` (analyst, exclusive tier)
- Each gets their own environment + membership

### Step 6 — Demo Startup Script (`demo-setup.sh`)
- Starts PostgreSQL + Redis via Docker
- Runs migrations, seeds data + users
- Starts Django on 0.0.0.0:8000
- Starts Vite on 0.0.0.0:5173
- Starts Celery worker
- Prints LAN IP + login credentials

### Step 7 — Commit & Push
