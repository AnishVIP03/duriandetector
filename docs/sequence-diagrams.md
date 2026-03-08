# DurianDetector IDS — Sequence Diagrams
## FYP-26-S1-08

> Paste any of these into [mermaid.live](https://mermaid.live) to render and export as PNG/SVG for your report.

---

## 1. User Registration & Login (Multi-Database JWT)

```mermaid
sequenceDiagram
    actor U as User
    participant F as Frontend (React)
    participant A as Django API
    participant DB1 as free_db
    participant DB2 as premium_db
    participant DB3 as exclusive_db

    Note over U,DB3: Registration Flow
    U->>F: Fill registration form (name, email, password)
    F->>A: POST /api/accounts/register/
    A->>DB1: Create user with role=free
    DB1-->>A: User created
    A->>DB1: Create SubscriptionPlan (Free)
    A-->>F: 201 Created
    F-->>U: Redirect to Login page

    Note over U,DB3: Login Flow (Multi-DB)
    U->>F: Enter email & password
    F->>A: POST /api/accounts/token/
    A->>DB1: Try authenticate (free_db)
    alt User found in free_db
        DB1-->>A: User authenticated
    else Not in free_db
        A->>DB2: Try authenticate (premium_db)
        alt User found in premium_db
            DB2-->>A: User authenticated
        else Not in premium_db
            A->>DB3: Try authenticate (exclusive_db)
            DB3-->>A: User authenticated or 401
        end
    end
    A->>A: Generate JWT with db claim + role
    A-->>F: {access_token, refresh_token}
    F->>F: Store tokens in Zustand store
    F-->>U: Redirect to Dashboard
```

---

## 2. Real-Time Alert Detection Pipeline

```mermaid
sequenceDiagram
    actor ATK as Attacker (PC5)
    participant NW as Network Interface
    participant SC as Scapy Capture
    participant FE as Feature Extractor
    participant ML as ML Engine
    participant GEO as GeoIP2
    participant MITRE as MITRE Mapper
    participant DB as PostgreSQL
    participant WS as WebSocket (Channels)
    participant UI as React Dashboard

    ATK->>NW: Send malicious packets (nmap/hping3/hydra)
    NW->>SC: Raw packet captured
    SC->>FE: Extract 54 features (ports, protocol, size, TTL, flags)
    FE->>ML: Feature vector

    alt Random Forest
        ML->>ML: Classify with Random Forest
    else SVM
        ML->>ML: Classify with SVM
    else Isolation Forest
        ML->>ML: Classify with Isolation Forest
    end

    alt Anomaly Detected (confidence > threshold)
        ML->>GEO: Lookup source IP
        GEO-->>ML: {country, city, lat, lng}
        ML->>MITRE: Map alert type to MITRE technique
        MITRE-->>ML: {tactic, technique_id}
        ML->>DB: CREATE Alert (src_ip, dst_ip, severity, type, geo, mitre)

        opt Demo Mode (DEMO_MODE=True)
            ML->>DB: Fan out alert to free_db
            ML->>DB: Fan out alert to premium_db
            ML->>DB: Fan out alert to exclusive_db
        end

        ML->>WS: Broadcast new alert
        WS->>UI: WebSocket push {alert data}
        UI->>UI: Update dashboard in real-time
        UI-->>UI: Show alert in feed + update charts
    else Normal Traffic
        ML->>DB: Log as normal traffic
    end
```

---

## 3. DurianBot Chatbot Interaction (All Tiers)

```mermaid
sequenceDiagram
    actor U as User
    participant F as Frontend (React)
    participant A as Django API
    participant CH as Chatbot Handler
    participant OL as Ollama LLM
    participant DB as PostgreSQL

    U->>F: Type message in chat
    F->>A: POST /api/chatbot/send/ {message, session_id?}
    A->>A: Check user role from JWT

    alt No session_id
        A->>DB: Create new ChatSession
    end
    A->>DB: Save user message (role=user)

    alt Free User (Basic Mode)
        A->>CH: _fallback_free_response(message)
        CH->>CH: Check greeting/casual patterns
        alt Casual conversation (hi, thanks, joke)
            CH-->>A: Friendly conversational response
        else Security question
            CH->>CH: Pattern match (port scan, brute force, etc.)
            CH-->>A: Concise tip + upgrade prompt
        end
    else Premium User (Enhanced Mode)
        A->>CH: _fallback_response(message)
        CH->>CH: Check greeting/casual patterns
        alt Casual conversation
            CH-->>A: Friendly response with personality
        else Security question
            CH->>CH: Pattern match with MITRE ATT&CK
            CH->>DB: Query recent alerts for context
            DB-->>CH: Alert summary
            CH-->>A: Detailed response + MITRE mapping + alert context
        end
    else Exclusive / Admin (AI Mode)
        A->>DB: Fetch last 20 messages (history)
        A->>DB: Query alerts for context
        DB-->>A: Alert data + chat history
        A->>A: Build system prompt + alert context
        A->>OL: POST /api/chat {model, messages, system_prompt}
        alt Ollama available
            OL-->>A: AI-generated response
        else Ollama unavailable
            A->>CH: Fallback to _fallback_response()
            CH-->>A: Enhanced mode response
        end
    end

    A->>DB: Save assistant message (role=assistant)
    A-->>F: {session_id, user_message, assistant_message, tier}
    F-->>U: Display response with markdown formatting
```

---

## 4. Demo Simulation Flow

```mermaid
sequenceDiagram
    actor U as User
    participant F as Frontend (React)
    participant A as Django API
    participant DB1 as free_db
    participant DB2 as premium_db
    participant DB3 as exclusive_db
    participant WS as WebSocket

    U->>F: Click "Run Full Simulation"
    F->>A: POST /api/demo/simulate/
    A->>A: Get or create user environment

    loop Generate 30-50 Alerts
        A->>A: Random source IP from global pool
        A->>A: Random alert type (port_scan, brute_force, dos, etc.)
        A->>A: Random severity (low/medium/high/critical)
        A->>A: GeoIP data (country, city, lat/lng)
        A->>A: MITRE technique mapping
        A->>A: Timestamp spread over 24 hours
        A->>DB1: Save alert to free_db
        A->>DB2: Save alert to premium_db
        A->>DB3: Save alert to exclusive_db
    end

    A->>A: Create Attack Chains from correlated alerts
    A->>A: Calculate risk scores

    A->>WS: Broadcast alerts to all connected clients
    A-->>F: {alert_count, chain_count, summary}
    F-->>U: Dashboard populated with live data

    Note over U,WS: All 4 users (PC1-PC4) now see same alerts
```

---

## 5. Incident Management Flow

```mermaid
sequenceDiagram
    actor U as Premium/Exclusive User
    participant F as Frontend
    participant A as Django API
    participant DB as PostgreSQL

    Note over U,DB: Create Incident
    U->>F: Navigate to Incidents page
    U->>F: Click "Create Incident"
    U->>F: Fill title, description, severity
    F->>A: POST /api/incidents/ {title, desc, severity}
    A->>A: Check permission (SubscriptionRequired: premium)
    A->>DB: Create Incident (status=open)
    DB-->>A: Incident created
    A-->>F: 201 Created {incident_id}

    Note over U,DB: Link Alerts
    U->>F: Select alerts to link
    F->>A: PATCH /api/incidents/{id}/ {alert_ids: [...]}
    A->>DB: Add alerts to incident.alerts M2M
    A-->>F: Updated incident

    Note over U,DB: Add Investigation Notes
    U->>F: Type investigation note
    F->>A: POST /api/incidents/{id}/notes/ {content}
    A->>DB: Create IncidentNote
    A-->>F: Note added

    Note over U,DB: Resolve Incident
    U->>F: Click "Resolve"
    F->>A: PATCH /api/incidents/{id}/ {status: resolved}
    A->>DB: Update status, set resolved_at
    A-->>F: Incident resolved
    F-->>U: Status updated to "Resolved"
```

---

## 6. PDF Report Generation

```mermaid
sequenceDiagram
    actor U as Premium/Exclusive User
    participant F as Frontend
    participant A as Django API
    participant DB as PostgreSQL
    participant WP as WeasyPrint

    U->>F: Navigate to Reports page
    U->>F: Select date range & report type
    F->>A: POST /api/reports/generate/ {date_from, date_to, type}
    A->>A: Check permission (SubscriptionRequired: premium)

    A->>DB: Query alerts in date range
    DB-->>A: Alert data

    A->>DB: Query incidents in date range
    DB-->>A: Incident data

    A->>DB: Query MITRE technique hits
    DB-->>A: MITRE coverage data

    A->>A: Build report content (JSON)
    A->>A: Render HTML template with data
    A->>WP: Convert HTML to PDF
    WP-->>A: PDF binary
    A->>DB: Save Report record + PDF file
    A-->>F: {report_id, pdf_url}
    F-->>U: Download PDF report
```

---

## 7. Subscription Upgrade Flow

```mermaid
sequenceDiagram
    actor U as Free User
    participant F as Frontend
    participant A as Django API
    participant DB as PostgreSQL

    U->>F: Navigate to Subscription page
    U->>F: View tier comparison table
    U->>F: Click "Upgrade to Premium"
    F->>F: Show checkout modal

    U->>F: Enter card: 4242 4242 4242 4242
    F->>F: Show processing animation (1.5s)
    F->>A: POST /api/subscriptions/checkout/ {plan: premium}
    A->>DB: Get SubscriptionPlan (premium)
    A->>DB: Update UserSubscription (plan=premium)
    A->>DB: Update user.role = premium
    DB-->>A: Updated
    A-->>F: {success, new_plan}
    F->>F: Update Zustand store (user.role = premium)
    F-->>U: "Subscription upgraded!" toast
    F->>F: Unlock premium features in sidebar
```

---

## 8. Attack Chain Analysis

```mermaid
sequenceDiagram
    actor U as Exclusive User
    participant F as Frontend
    participant A as Django API
    participant DB as PostgreSQL

    U->>F: Navigate to Attack Chains page
    F->>A: GET /api/attack-chains/
    A->>A: Check permission (SubscriptionRequired: exclusive)
    A->>DB: Query AttackChains for environment
    DB-->>A: List of chains with alerts + MITRE techniques
    A-->>F: Attack chain data

    F->>F: Render kill chain timeline
    F->>F: Render risk score badges
    F-->>U: Display attack chains

    Note over U,DB: View Chain Details
    U->>F: Click on attack chain
    F->>A: GET /api/attack-chains/{id}/
    A->>DB: Get chain with related alerts + MITRE techniques
    DB-->>A: Chain detail
    A-->>F: {src_ip, chain_type, alerts[], mitre_techniques[], risk_score}
    F-->>U: Show timeline: Recon -> Exploit -> Impact
```

---

## 9. Admin User Management

```mermaid
sequenceDiagram
    actor AD as Admin
    participant F as Frontend
    participant A as Django API
    participant DB as PostgreSQL

    AD->>F: Navigate to Admin panel
    F->>A: GET /api/accounts/users/
    A->>A: Check is_staff or role=admin
    A->>DB: Query all users
    DB-->>A: User list
    A-->>F: Users with roles, status, last login

    Note over AD,DB: Suspend User
    AD->>F: Click "Suspend" on user
    F->>A: POST /api/accounts/users/{id}/suspend/ {reason}
    A->>DB: user.suspend(reason)
    DB-->>A: Updated
    A-->>F: User suspended
    F-->>AD: Status updated to "Suspended"

    Note over AD,DB: View Audit Logs
    AD->>F: Navigate to Audit Logs
    F->>A: GET /api/audit/logs/
    A->>DB: Query AuditLog ordered by timestamp
    DB-->>A: Audit log entries
    A-->>F: {user, action, target, timestamp, ip_address}
    F-->>AD: Display audit log table
```

---

## 10. WebSocket Real-Time Alert Flow

```mermaid
sequenceDiagram
    participant SC as Scapy/Celery Worker
    participant RD as Redis (Channel Layer)
    participant DC as Django Channels
    participant WS as WebSocket Connection
    participant F as Frontend (React)

    Note over SC,F: Connection Setup
    F->>DC: WS Connect ws://<IP>:8000/ws/alerts/
    DC->>RD: Subscribe to alert group
    DC-->>F: Connection accepted

    Note over SC,F: Alert Detection & Push
    SC->>SC: Packet classified as malicious
    SC->>RD: Publish alert to channel group
    RD->>DC: Notify consumer
    DC->>WS: Send alert JSON
    WS->>F: onmessage event
    F->>F: Update Zustand store
    F->>F: Add alert to dashboard feed
    F->>F: Update severity charts
    F->>F: Show toast notification

    Note over SC,F: Multiple Clients
    RD->>DC: Same alert to PC2 (Free)
    RD->>DC: Same alert to PC3 (Premium)
    RD->>DC: Same alert to PC4 (Exclusive)
```

---

## 11. Network Packet Capture & ML Classification

```mermaid
sequenceDiagram
    actor U as Premium/Exclusive User
    participant F as Frontend
    participant A as Django API
    participant CL as Celery Worker
    participant SC as Scapy
    participant ML as ML Engine
    participant DB as PostgreSQL

    U->>F: Navigate to Packet Inspector
    U->>F: Click "Start Capture"
    F->>A: POST /api/network-capture/start/
    A->>DB: Create CaptureSession (status=running)
    A->>CL: Queue capture task

    loop Continuous Capture
        CL->>SC: Sniff packets on interface
        SC-->>CL: Raw packet data
        CL->>CL: Extract features (54 dimensions)
        CL->>DB: Save NetworkFeature
        CL->>ML: Classify feature vector

        alt Malicious (confidence > threshold)
            ML-->>CL: {alert_type, severity, confidence}
            CL->>DB: Create Alert
            CL->>DB: Increment session.alerts_generated
        else Normal
            ML-->>CL: Normal traffic
            CL->>DB: Increment session.packets_captured
        end
    end

    U->>F: Click "Stop Capture"
    F->>A: POST /api/network-capture/stop/
    A->>DB: Update CaptureSession (status=stopped)
    A-->>F: {packets_captured, alerts_generated}
```

---

## 12. Team Management Flow

```mermaid
sequenceDiagram
    actor TL as Team Leader (Exclusive)
    actor M as New Member
    participant F as Frontend
    participant A as Django API
    participant DB as PostgreSQL

    TL->>F: Navigate to Team Management
    F->>A: GET /api/environments/{env_id}/members/
    A-->>F: Current team members

    Note over TL,DB: Invite Member
    TL->>F: Enter member email + role
    F->>A: POST /api/environments/{env_id}/invite/ {email, role}
    A->>DB: Create EnvironmentMembership
    A-->>F: Invitation created
    F-->>TL: Member added

    Note over M,DB: Member Joins
    M->>F: Login with invited email
    F->>A: GET /api/environments/
    A->>DB: Fetch memberships for user
    A-->>F: Environment with role
    F-->>M: Access granted to environment

    Note over TL,DB: Change Role
    TL->>F: Change member role to security_analyst
    F->>A: PATCH /api/environments/{env_id}/members/{id}/ {role}
    A->>DB: Update membership role
    A-->>F: Role updated
```
