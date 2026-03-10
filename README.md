# DurianDetector IDS

An AI-powered Intrusion Detection System with real-time attack detection, multi-tier subscription access, and an intelligent security chatbot.

Final Year Project (FYP-26-S1-08).

---

## Features

- **Real-Time Attack Detection** — Captures and analyzes network packets using Scapy + scikit-learn ML models
- **Multi-Tier Subscriptions** — Free, Premium, and Exclusive tiers with progressively unlocked features
- **DurianBot AI Chatbot** — Security assistant with tier-based response quality (Basic / Enhanced / AI Mode)
- **MITRE ATT&CK Integration** — Maps detected attacks to MITRE tactics and techniques
- **3D Globe Visualization** — Geographic attack origin display using react-globe.gl
- **Attack Chain Analysis** — Multi-stage attack correlation and visualization
- **Incident Management** — Create, track, and resolve security incidents
- **Report Generation** — PDF security reports with WeasyPrint
- **GeoIP Mapping** — Leaflet-based map showing alert source locations
- **Real-Time WebSocket Alerts** — Live dashboard updates via Django Channels + Redis

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Django 6, Django REST Framework, Django Channels |
| **Frontend** | React 18, Vite, Zustand, Tailwind CSS |
| **Database** | PostgreSQL 16 (3 isolated databases for demo) |
| **Cache / Broker** | Redis 7 (Celery task queue + WebSocket channel layer) |
| **ML Engine** | scikit-learn (network traffic classification) |
| **AI Chatbot** | Ollama (Mistral 7B / Llama 3.2) |
| **Packet Capture** | Scapy |
| **Auth** | JWT (SimpleJWT with multi-database token claims) |
| **Containerization** | Docker Compose |

---

## Quick Start (Development)

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL (or Docker)
- Redis (or Docker)

### Backend Setup

```bash
cd backend
python -m venv ../venv
source ../venv/bin/activate    # Windows: ..\venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_mitre
python manage.py seed_threats
python manage.py seed_plans
python manage.py runserver
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:5173` and the backend on `http://localhost:8000`.

---

## 5-Computer Live Demo Setup

The demo mode runs the full system across 5 computers on a LAN to simulate a real-world IDS deployment.

### Architecture

```
PC1 (Server + Admin)          PC2-4 (Users via Browser)        PC5 (Attacker)
┌─────────────────────┐       ┌──────────────────────┐       ┌─────────────┐
│  Django Backend      │       │  Browser             │       │  nmap       │
│  PostgreSQL (3 DBs)  │◄──────│  http://<IP>:5173    │       │  hping3     │
│  Redis               │       │  Login per tier      │       │  hydra      │
│  Celery Worker       │       └──────────────────────┘       │             │
│  Vite Frontend       │                                      │  Attacks    │
│  0.0.0.0:5173/8000   │◄─────────────────────────────────────│  ──────►    │
└─────────────────────┘                                       └─────────────┘
```

| PC | Role | What It Does |
|----|------|-------------|
| **PC1** | Server + Admin | Runs all services. Admin logs in here. |
| **PC2** | Free User | Browser only. Basic dashboard + limited chatbot. |
| **PC3** | Premium User | Browser only. Incidents, ML, Reports, MITRE, enhanced chatbot. |
| **PC4** | Exclusive User | Browser only. All features + AI chatbot. |
| **PC5** | Attacker | Runs attack tools against PC1. |

### Prerequisites for PC1

#### macOS

```bash
# Install Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop/

# Clone and setup
git clone https://github.com/AnishVIP03/duriandetector.git
cd duriandetector
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..
```

#### Windows

```bash
# Install:
# - Python 3.10+: https://python.org
# - Node.js 18+: https://nodejs.org
# - Docker Desktop: https://docker.com/products/docker-desktop
# - Git: https://git-scm.com (includes Git Bash)

# Clone and setup (in Git Bash or WSL)
git clone https://github.com/AnishVIP03/duriandetector.git
cd duriandetector
python -m venv venv
source venv/Scripts/activate    # Git Bash
# OR: venv\Scripts\activate     # CMD / PowerShell
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..
```

#### Linux

```bash
# Install Docker
sudo apt update && sudo apt install -y docker.io docker-compose python3-venv nodejs npm
sudo systemctl start docker
sudo usermod -aG docker $USER  # Then re-login

# Clone and setup
git clone https://github.com/AnishVIP03/duriandetector.git
cd duriandetector
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..
```

### Run the Demo

```bash
chmod +x demo-setup.sh
./demo-setup.sh
```

The script automatically:
1. Starts Docker (PostgreSQL with 3 databases + Redis)
2. Waits for databases to be ready
3. Runs migrations on all 3 databases
4. Seeds users, MITRE ATT&CK data, and threat intelligence
5. Starts Celery worker
6. Starts Django on `0.0.0.0:8000`
7. Starts Vite on `0.0.0.0:5173`

When complete, it displays the LAN IP and login credentials.

**To stop:** Press `Ctrl+C` — cleanly shuts down everything.

### Login Credentials

| PC | Tier | Email | Password |
|----|------|-------|----------|
| PC1 | Admin | `admin@ids.local` | `admin123` |
| PC2 | Free | `free@demo.local` | `demo123` |
| PC3 | Premium | `premium@demo.local` | `demo123` |
| PC4 | Exclusive | `exclusive@demo.local` | `demo123` |

All users access the same URL: `http://<LAN-IP>:5173`

### Attack Commands (PC5)

Run from any Linux machine on the same network:

```bash
# Port Scan (MITRE T1046 - Network Service Discovery)
sudo nmap -sS -p 1-1000 <LAN-IP>

# DoS Flood (MITRE T1498 - Network Denial of Service)
sudo hping3 -S --flood -p 80 <LAN-IP>

# SSH Brute Force (MITRE T1110 - Brute Force)
hydra -l root -P /usr/share/wordlists/rockyou.txt <LAN-IP> ssh
```

### Feature Access by Tier

| Feature | Free | Premium | Exclusive |
|---------|:----:|:-------:|:---------:|
| Dashboard & Alerts | Y | Y | Y |
| GeoIP Map | Y | Y | Y |
| DurianBot (Basic) | Y | Y | Y |
| Incident Management | - | Y | Y |
| ML Configuration | - | Y | Y |
| Reports & MITRE | - | Y | Y |
| Packet Inspector | - | Y | Y |
| Attack Chains | - | - | Y |
| 3D Globe | - | - | Y |
| Team Management | - | - | Y |
| DurianBot AI Mode | - | - | Y |

### DurianBot Chatbot Tiers

DurianBot has a friendly, conversational personality across all tiers — it handles greetings, jokes, casual chat, and security questions naturally.

- **Basic** (Free) — Concise security tips with personality, upgrade prompts
- **Enhanced** (Premium) — Detailed MITRE ATT&CK analysis, step-by-step guides, alert context
- **AI Mode** (Exclusive) — Full Ollama LLM with conversation history, personality, and deep analysis

### Enabling DurianBot AI Mode (Ollama)

The Exclusive tier's AI Mode requires Ollama running on PC1. Without it, the chatbot gracefully falls back to Enhanced mode. AI Mode gives the chatbot full conversational AI capabilities — it can answer any question, maintain context across messages, and provide deep security analysis.

#### Windows (Recommended for demo — more CPU power)

```powershell
# 1. Download and install Ollama from: https://ollama.com/download/windows
#    Run the installer — it adds 'ollama' to your PATH automatically.

# 2. Open PowerShell or CMD and pull the model:
ollama pull llama3.2

# 3. Start the Ollama server (keep this running during the demo):
ollama serve

# Ollama runs on http://localhost:11434 — Django connects automatically.
# If you have an NVIDIA GPU, Ollama uses it automatically for faster responses.
```

#### macOS

```bash
# Option 1: Homebrew
brew install ollama
ollama pull llama3.2
ollama serve

# Option 2: Download from https://ollama.com/download/mac
# Then run:
ollama pull llama3.2
ollama serve
```

#### Linux

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull model and start server
ollama pull llama3.2
ollama serve
```

> **Tip:** Run `ollama serve` in a separate terminal before starting `demo-setup.sh`. The chatbot will automatically detect and connect to it. If Ollama isn't running, Exclusive users still get Enhanced-level responses — no errors or crashes.

---

## Database Architecture (Demo Mode)

Each tier has an isolated PostgreSQL database:

| Database | Alias | Users |
|----------|-------|-------|
| `duriandetector_free` | `default` / `free_db` | Free user + Admin |
| `duriandetector_premium` | `premium_db` | Premium user |
| `duriandetector_exclusive` | `exclusive_db` | Exclusive user |

Routing is handled by `TierDatabaseRouter` using JWT token claims. Alerts are fanned out to all databases so every user sees the same attacks.

---

## Project Structure

```
duriandetector/
├── backend/
│   ├── apps/
│   │   ├── accounts/        # User auth, JWT, multi-DB login
│   │   ├── alerts/          # Security alert models & API
│   │   ├── attack_chains/   # Multi-stage attack analysis
│   │   ├── audit/           # Audit logging
│   │   ├── chatbot/         # DurianBot (tiered responses)
│   │   ├── demo/            # Demo simulation & seed commands
│   │   ├── environments/    # Network environment management
│   │   ├── incidents/       # Incident tracking
│   │   ├── mitre/           # MITRE ATT&CK framework
│   │   ├── ml_engine/       # ML model training & prediction
│   │   ├── network_capture/ # Packet capture with Scapy
│   │   ├── reports/         # PDF report generation
│   │   ├── subscriptions/   # Subscription plans & billing
│   │   └── threats/         # Threat intelligence
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py      # Shared settings
│   │   │   └── demo.py      # Demo mode (3 databases)
│   │   ├── db_router.py     # Multi-database routing
│   │   └── middleware.py     # Tier database middleware
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/             # Axios client (dynamic LAN URLs)
│       ├── components/      # TierGate, MainLayout, shared UI
│       ├── hooks/           # WebSocket, auth hooks
│       ├── pages/           # Dashboard, Alerts, Chatbot, etc.
│       └── store/           # Zustand state management
├── docs/                    # Workflow diagrams
├── demo-setup.sh            # One-command demo launcher
├── docker-compose.demo.yml  # PostgreSQL + Redis containers
├── init-demo-dbs.sql        # Creates premium & exclusive DBs
└── DurianDetector_Demo_Guide.docx  # Full demo walkthrough
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `docker: command not found` | Install Docker Desktop and open it before running the script |
| `No module named 'psycopg2'` | `pip install psycopg2-binary` |
| `python: command not found` | Use `python3` or activate the virtualenv |
| Port 8000/5173 in use | `lsof -i :8000` then `kill -9 <PID>` |
| Can't connect from other PCs | All PCs must be on the same WiFi. Check firewall settings. |
| Mac overheating | Normal during demo. Press Ctrl+C when done. |
| Chatbot AI mode not working | Install Ollama (see "Enabling DurianBot AI Mode" above), pull `llama3.2`, and run `ollama serve` |
| Ollama responses are slow | Normal on CPU-only machines. Use a PC with an NVIDIA GPU for faster responses |
| Windows: `demo-setup.sh` won't run | Use Git Bash or WSL to run the script |
| Windows: `ollama` not found | Restart your terminal after installing Ollama, or use the full path |

---

## License

This project is part of FYP-26-S1-08. All rights reserved.
