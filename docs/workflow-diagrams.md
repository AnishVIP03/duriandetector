# DurianDetector IDS — Workflow Diagrams
## FYP-26-S1-08

> Paste any of these into [mermaid.live](https://mermaid.live) or import into draw.io (Extras > Mermaid)

---

## 1. System Architecture (Mind Map)

```mermaid
mindmap
  root((DurianDetector IDS))
    Frontend — React 18
      Landing Page
        3D Globe Background
        Pricing Tiers
        Registration / Login
      SOC Dashboard
        Risk Score Gauge
        Severity Breakdown
        Hourly Trend Chart
        Live Alert Feed
      Alert Management
        Alert List with Filters
        Alert Detail View
        GeoIP Map
      Threat Intelligence
        Threat Feed
        MITRE ATT&CK Heatmap
        Attack Kill Chain Timeline
      Advanced Features
        3D Attack Globe
        Packet Inspector
        DurianBot AI Chatbot
        Demo Simulation Mode
      Account Management
        Subscription & Payment
        Team Management
        User Profile
      Admin Panel
        User Management
        Audit Logs
        System Health
    Backend — Django 6
      REST API — DRF
        JWT Authentication (Multi-DB)
        58+ Endpoints
        Pagination & Filtering
      15 Django Apps
        accounts
        alerts
        environments
        threats
        incidents
        ml_engine
        network_capture
        reports
        subscriptions
        mitre
        chatbot
        attack_chains
        audit
        demo
      Real-Time
        Django Channels
        WebSocket Consumers
        Alert Broadcasting
      Background Tasks
        Celery Workers
        Redis Broker
        Packet Processing
    ML Engine
      Random Forest
      SVM Classifier
      Isolation Forest
      Feature Extraction
      Model Training & Prediction
    External Services
      Scapy — Packet Capture
      Ollama — Local LLM
      Redis — Cache & Broker
      PostgreSQL 16 (3 databases)
      GeoIP2 — IP Geolocation
```

---

## 2. User Journey Workflow

```mermaid
flowchart TD
    A[Visitor arrives at Landing Page] --> B{Has Account?}
    B -->|No| C[Click Get Started Free]
    C --> D[Registration Page]
    D --> E[Enter Name, Email, Password]
    E --> F[Account Created — Free Tier]
    F --> G[Redirect to Login]

    B -->|Yes| G[Login Page]
    G --> H[Enter Email & Password]
    H --> I[JWT Token Issued]
    I --> J[Dashboard]

    J --> K{What to do?}

    K --> L[View Alerts]
    L --> L1[Filter by Severity]
    L1 --> L2[Click Alert for Detail]
    L2 --> L3[See GeoIP, MITRE Mapping, Raw Packet]

    K --> M[Run Demo Simulation]
    M --> M1[Click Run Full Simulation]
    M1 --> M2[30-50 Fake Alerts Generated]
    M2 --> M3[Alerts populate across all pages]
    M3 --> J

    K --> N[Explore Visualisations]
    N --> N1[3D Attack Globe]
    N --> N2[MITRE ATT&CK Heatmap]
    N --> N3[Attack Kill Chain Timeline]
    N --> N4[GeoIP Map]

    K --> O[Use AI Chatbot]
    O --> O1[Ask DurianBot about alerts]
    O1 --> O2[Bot analyses via Ollama LLM]
    O2 --> O3[Returns MITRE techniques & mitigations]

    K --> P[Upgrade Subscription]
    P --> P1{Choose Tier}
    P1 -->|Premium $29.99/mo| P2[Checkout Modal]
    P1 -->|Exclusive $99.99/mo| P2
    P2 --> P3[Enter Card Details]
    P3 --> P4[Processing Animation]
    P4 --> P5[Subscription Upgraded]
    P5 --> J

    K --> Q[Manage Team]
    Q --> Q1[Invite Members by Email]
    Q1 --> Q2[Assign Roles]
    Q2 --> Q3[Team Dashboard]

    K --> R[Generate Reports]
    R --> R1[Select Date Range]
    R1 --> R2[PDF Report Generated]

    K --> S[Admin Panel]
    S --> S1[Manage Users]
    S --> S2[View Audit Logs]
    S --> S3[System Health Check]

    style A fill:#1e293b,stroke:#3b82f6,color:#fff
    style J fill:#1e293b,stroke:#22c55e,color:#fff
    style M1 fill:#1e293b,stroke:#f97316,color:#fff
    style P5 fill:#1e293b,stroke:#eab308,color:#fff
```

---

## 3. Attack Detection Data Flow

```mermaid
flowchart LR
    subgraph Network
        A[Network Traffic] -->|Raw Packets| B[Scapy Capture]
    end

    subgraph Backend ["Backend (Django)"]
        B --> C[Feature Extractor]
        C -->|54 features| D[ML Engine]

        D --> D1[Random Forest]
        D --> D2[SVM Classifier]
        D --> D3[Isolation Forest]

        D1 --> E{Anomaly Detected?}
        D2 --> E
        D3 --> E

        E -->|Yes| F[Create Alert]
        E -->|No| G[Log Normal Traffic]

        F --> H[GeoIP Lookup]
        H --> I[MITRE ATT&CK Mapping]
        I --> J[Attack Chain Correlation]
        J --> K[Risk Score Calculation]
        K --> L[Save to Database]
        L --> M[WebSocket Broadcast]
    end

    subgraph Frontend ["Frontend (React)"]
        M -->|Real-time| N[SOC Dashboard]
        N --> O[Alert Feed]
        N --> P[Risk Gauge]
        N --> Q[Severity Chart]

        L --> R[3D Globe]
        L --> S[MITRE Heatmap]
        L --> T[Kill Chain Timeline]
        L --> U[GeoIP Map]
    end

    subgraph AI ["AI Assistant"]
        O -->|User asks| V[DurianBot]
        V -->|Query| W[Ollama LLM]
        W -->|Analysis| V
        V -->|Response| X[Recommendations & Mitigations]
    end

    style A fill:#ef4444,stroke:#ef4444,color:#fff
    style F fill:#f97316,stroke:#f97316,color:#fff
    style N fill:#22c55e,stroke:#22c55e,color:#fff
    style W fill:#3b82f6,stroke:#3b82f6,color:#fff
```

---

## 4. Technology Stack

```mermaid
flowchart TB
    subgraph Client ["Client Layer"]
        R[React 18] --- V[Vite]
        R --- TW[Tailwind CSS]
        R --- FM[Framer Motion]
        R --- GL[react-globe.gl / Three.js]
        R --- ZS[Zustand State]
        R --- AX[Axios HTTP]
    end

    subgraph API ["API Layer"]
        DJ[Django 6] --- DRF[Django REST Framework]
        DJ --- JWT[SimpleJWT Auth]
        DJ --- CH[Django Channels]
        DJ --- CL[Celery]
    end

    subgraph ML ["ML Layer"]
        SK[scikit-learn] --- RF[Random Forest]
        SK --- SVM[SVM]
        SK --- IF[Isolation Forest]
        SC[Scapy] --- FE[Feature Extractor]
    end

    subgraph Data ["Data Layer"]
        DB[(PostgreSQL 16)]
        RD[(Redis)]
        OL[Ollama LLM]
        GI[GeoIP2 Database]
    end

    Client <-->|REST + WebSocket| API
    API <--> ML
    API <--> Data

    style Client fill:#1e293b,stroke:#3b82f6,color:#fff
    style API fill:#1e293b,stroke:#22c55e,color:#fff
    style ML fill:#1e293b,stroke:#f97316,color:#fff
    style Data fill:#1e293b,stroke:#a855f7,color:#fff
```

---

## 5. Subscription & Access Control Flow

```mermaid
flowchart TD
    A[User Registers] --> B[Free Tier Assigned]

    B --> C{Feature Access Check}

    C --> D[Free Features]
    D --> D1[Basic Dashboard]
    D --> D2[Alert Monitoring — 100/day]
    D --> D3[Community Support]

    C --> E{Premium?}
    E -->|No| F[Upgrade Prompt]
    F --> G[Subscription Page]
    G --> H[Checkout Modal]
    H --> I[Card: 4242 4242 4242 4242]
    I --> J[1.5s Processing]
    J --> K[Tier Updated in DB]
    K --> C

    E -->|Yes| L[Premium Features]
    L --> L1[ML Model Config]
    L --> L2[Incident Management]
    L --> L3[PDF Reports]
    L --> L4[MITRE Mapping]
    L --> L5[Unlimited Alerts]

    C --> M{Exclusive?}
    M -->|Yes| N[Exclusive Features]
    N --> N1[DurianBot AI Chatbot]
    N --> N2[3D Attack Globe]
    N --> N3[Kill Chain Analysis]
    N --> N4[Team Management — 25 users]
    N --> N5[Audit Logging]
    N --> N6[Priority Support SLA]

    style B fill:#3b82f6,stroke:#3b82f6,color:#fff
    style L fill:#6366f1,stroke:#6366f1,color:#fff
    style N fill:#eab308,stroke:#eab308,color:#000
```

---

## 6. Demo Simulation Flow

```mermaid
flowchart TD
    A[User clicks Demo Mode] --> B[/demo page loads/]
    B --> C[Click Run Full Simulation]
    C --> D[Backend: _get_or_create_user_environment]

    D --> E{Environment exists?}
    E -->|No| F[Auto-create Demo Environment]
    F --> G[Assign user as team_leader]
    E -->|Yes| G[Use existing environment]

    G --> H[Generate 30-50 Random Alerts]

    H --> I[For each alert:]
    I --> I1[Random source IP from global pool]
    I --> I2[Random severity: low/medium/high/critical]
    I --> I3[Random alert type: port_scan/brute_force/malware/etc]
    I --> I4[GeoIP data: country, city, lat/lng]
    I --> I5[MITRE technique mapping]
    I --> I6[Timestamps spread over 24h]

    H --> J[Create Attack Chains]
    J --> J1[Link related alerts]
    J --> J2[Calculate risk scores]
    J --> J3[Map to Kill Chain phases]

    H --> K[Return Summary]
    K --> L[Dashboard now populated]
    L --> M[All pages show real data]

    M --> M1[Alerts page: 30-50 alerts]
    M --> M2[Globe: attack arcs worldwide]
    M --> M3[MITRE: technique heatmap]
    M --> M4[Kill Chain: timeline view]
    M --> M5[GeoIP Map: pin markers]

    style C fill:#f97316,stroke:#f97316,color:#fff
    style H fill:#ef4444,stroke:#ef4444,color:#fff
    style L fill:#22c55e,stroke:#22c55e,color:#fff
```

---

## 7. 5-Computer Live Demo Architecture

```mermaid
flowchart TB
    subgraph PC1["PC1 — Server + Admin"]
        DJ[Django 6 Backend]
        VT[Vite Frontend]
        PG[(PostgreSQL 16)]
        RD[(Redis 7)]
        CL[Celery Worker]
        OL[Ollama LLM]

        PG --- DB1[(free_db)]
        PG --- DB2[(premium_db)]
        PG --- DB3[(exclusive_db)]

        DJ <--> PG
        DJ <--> RD
        DJ <--> CL
        DJ <--> OL
    end

    subgraph PC2["PC2 — Free User"]
        B1[Browser]
    end

    subgraph PC3["PC3 — Premium User"]
        B2[Browser]
    end

    subgraph PC4["PC4 — Exclusive User"]
        B3[Browser]
    end

    subgraph PC5["PC5 — Attacker"]
        NM[nmap]
        HP[hping3]
        HY[hydra]
    end

    B1 <-->|HTTP + WebSocket| VT
    B2 <-->|HTTP + WebSocket| VT
    B3 <-->|HTTP + WebSocket| VT
    VT <-->|REST API| DJ

    NM -->|Port Scan| DJ
    HP -->|DoS Flood| DJ
    HY -->|Brute Force| DJ

    style PC1 fill:#1e293b,stroke:#22c55e,color:#fff
    style PC2 fill:#1e293b,stroke:#3b82f6,color:#fff
    style PC3 fill:#1e293b,stroke:#6366f1,color:#fff
    style PC4 fill:#1e293b,stroke:#eab308,color:#fff
    style PC5 fill:#1e293b,stroke:#ef4444,color:#fff
```

---

## 8. DurianBot Chatbot Tier Flow

```mermaid
flowchart TD
    A[User sends message] --> B{Check user.role}

    B -->|role = free| C[Basic Mode]
    C --> C1{Casual conversation?}
    C1 -->|Yes| C2[Greeting / Thanks / Joke / Identity]
    C1 -->|No| C3{Security question match?}
    C3 -->|Yes| C4[Concise tip + upgrade prompt]
    C3 -->|No| C5[Friendly generic fallback]

    B -->|role = premium| D[Enhanced Mode]
    D --> D1{Casual conversation?}
    D1 -->|Yes| D2[Friendly response with personality]
    D1 -->|No| D3{Security question match?}
    D3 -->|Yes| D4[Detailed steps + MITRE ATT&CK + alert context]
    D3 -->|No| D5[Helpful fallback with suggestions]

    B -->|role = exclusive / admin| E[AI Mode]
    E --> E1[Build system prompt + alert context]
    E1 --> E2[Load last 20 messages as history]
    E2 --> E3{Ollama available?}
    E3 -->|Yes| E4[Full LLM response with personality]
    E3 -->|No| E5[Fallback to Enhanced Mode]

    C2 --> F[Save to ChatMessage + return]
    C4 --> F
    C5 --> F
    D2 --> F
    D4 --> F
    D5 --> F
    E4 --> F
    E5 --> F

    style C fill:#3b82f6,color:#fff
    style D fill:#6366f1,color:#fff
    style E fill:#eab308,color:#000
```

---

## How to Use These Diagrams

1. **Mermaid Live Editor**: Go to [mermaid.live](https://mermaid.live), paste any code block
2. **Draw.io**: Open draw.io > Extras > Edit Diagram > paste Mermaid code
3. **GitHub**: These render automatically in `.md` files on GitHub
4. **VS Code**: Install "Mermaid Markdown Syntax" extension for preview
5. **Export**: Use mermaid.live to export as PNG/SVG for your FYP report
