# DurianDetector IDS — Use Case Diagrams
## FYP-26-S1-08

> Paste any of these into [mermaid.live](https://mermaid.live) to render and export as PNG/SVG for your report.

---

## 1. Overall System Use Case Diagram

```mermaid
flowchart TD
    subgraph Actors
        FU["Free User"]
        PU["Premium User"]
        EU["Exclusive User"]
        AD["Admin"]
        ATK["Attacker (External)"]
        SYS["System (Automated)"]
    end

    subgraph DurianDetector["DurianDetector IDS"]
        UC1["Register Account"]
        UC2["Login / JWT Auth"]
        UC3["View Dashboard"]
        UC4["View Alerts"]
        UC5["View GeoIP Map"]
        UC6["Use DurianBot Chatbot"]
        UC7["Run Demo Simulation"]
        UC8["Manage Incidents"]
        UC9["Configure ML Model"]
        UC10["Generate PDF Reports"]
        UC11["View MITRE ATT&CK Matrix"]
        UC12["Inspect Packets"]
        UC13["View 3D Attack Globe"]
        UC14["Analyze Attack Chains"]
        UC15["Manage Team"]
        UC16["DurianBot AI Mode"]
        UC17["Manage Users"]
        UC18["View Audit Logs"]
        UC19["System Health Check"]
        UC20["Block Malicious IP"]
        UC21["View Threat Intelligence"]
        UC22["Manage Subscription"]
        UC23["Capture Network Packets"]
        UC24["Detect Attacks via ML"]
        UC25["Broadcast Real-Time Alerts"]
        UC26["Fan Out Alerts to All DBs"]
        UC27["Generate Attack"]
    end

    %% Free User
    FU --> UC1
    FU --> UC2
    FU --> UC3
    FU --> UC4
    FU --> UC5
    FU --> UC6
    FU --> UC7
    FU --> UC22

    %% Premium User (inherits Free)
    PU --> UC2
    PU --> UC3
    PU --> UC4
    PU --> UC5
    PU --> UC6
    PU --> UC7
    PU --> UC8
    PU --> UC9
    PU --> UC10
    PU --> UC11
    PU --> UC12
    PU --> UC20
    PU --> UC21

    %% Exclusive User (inherits Premium)
    EU --> UC2
    EU --> UC3
    EU --> UC4
    EU --> UC5
    EU --> UC7
    EU --> UC8
    EU --> UC9
    EU --> UC10
    EU --> UC11
    EU --> UC12
    EU --> UC13
    EU --> UC14
    EU --> UC15
    EU --> UC16
    EU --> UC20
    EU --> UC21

    %% Admin
    AD --> UC2
    AD --> UC3
    AD --> UC4
    AD --> UC17
    AD --> UC18
    AD --> UC19
    AD --> UC16

    %% Attacker
    ATK --> UC27

    %% System
    SYS --> UC23
    SYS --> UC24
    SYS --> UC25
    SYS --> UC26

    style FU fill:#3b82f6,color:#fff
    style PU fill:#6366f1,color:#fff
    style EU fill:#eab308,color:#000
    style AD fill:#ef4444,color:#fff
    style ATK fill:#991b1b,color:#fff
    style SYS fill:#059669,color:#fff
```

---

## 2. Free User Use Cases

```mermaid
flowchart LR
    FU((Free User))

    FU --> UC1[Register Account]
    FU --> UC2[Login]
    FU --> UC3[View Dashboard]
    FU --> UC4[View Alerts & Filter by Severity]
    FU --> UC5[View GeoIP Map]
    FU --> UC6[Use DurianBot - Basic Mode]
    FU --> UC7[Run Demo Simulation]
    FU --> UC8[Upgrade Subscription]
    FU --> UC9[View Threat Feed]

    UC2 -->|includes| UC2a[JWT Token Issued]
    UC6 -->|includes| UC6a[Pattern-Matched Tips]
    UC6a -->|extends| UC6b[Upgrade Prompt Shown]

    style FU fill:#3b82f6,color:#fff
```

---

## 3. Premium User Use Cases

```mermaid
flowchart LR
    PU((Premium User))

    PU --> UC1[View Dashboard]
    PU --> UC2[View & Filter Alerts]
    PU --> UC3[Use DurianBot - Enhanced Mode]
    PU --> UC4[Create & Manage Incidents]
    PU --> UC5[Configure ML Model]
    PU --> UC6[Generate PDF Reports]
    PU --> UC7[View MITRE ATT&CK Matrix]
    PU --> UC8[Inspect Network Packets]
    PU --> UC9[Block Malicious IPs]
    PU --> UC10[View Threat Intelligence]
    PU --> UC11[View GeoIP Map]

    UC3 -->|includes| UC3a[MITRE ATT&CK Mapping]
    UC3 -->|includes| UC3b[Alert Context Summary]
    UC4 -->|includes| UC4a[Link Alerts to Incident]
    UC4 -->|includes| UC4b[Add Notes to Incident]
    UC4 -->|extends| UC4c[Assign to Team Member]
    UC6 -->|includes| UC6a[Select Date Range]
    UC6 -->|includes| UC6b[Download PDF]

    style PU fill:#6366f1,color:#fff
```

---

## 4. Exclusive User Use Cases

```mermaid
flowchart LR
    EU((Exclusive User))

    EU --> UC1[All Premium Features]
    EU --> UC2[Use DurianBot - AI Mode]
    EU --> UC3[View 3D Attack Globe]
    EU --> UC4[Analyze Attack Chains]
    EU --> UC5[Manage Team Members]

    UC2 -->|includes| UC2a[Ollama LLM Analysis]
    UC2 -->|includes| UC2b[Conversation History]
    UC2 -->|includes| UC2c[Real-Time Alert Context]
    UC4 -->|includes| UC4a[View Kill Chain Phases]
    UC4 -->|includes| UC4b[View Risk Scores]
    UC4 -->|includes| UC4c[MITRE Technique Mapping]
    UC5 -->|includes| UC5a[Invite by Email]
    UC5 -->|includes| UC5b[Assign Roles]

    style EU fill:#eab308,color:#000
```

---

## 5. Admin Use Cases

```mermaid
flowchart LR
    AD((Admin))

    AD --> UC1[Login to Admin Dashboard]
    AD --> UC2[Manage All Users]
    AD --> UC3[View Audit Logs]
    AD --> UC4[System Health Monitoring]
    AD --> UC5[Use DurianBot - AI Mode]
    AD --> UC6[View All Alerts]
    AD --> UC7[Run Demo Simulation]

    UC2 -->|includes| UC2a[Suspend / Unsuspend Users]
    UC2 -->|includes| UC2b[View User Details]
    UC3 -->|includes| UC3a[Filter by Action Type]
    UC3 -->|includes| UC3b[Filter by User]
    UC4 -->|includes| UC4a[Check Celery Status]
    UC4 -->|includes| UC4b[Check Redis Status]
    UC4 -->|includes| UC4c[Check CPU/Memory/Disk]

    style AD fill:#ef4444,color:#fff
```

---

## 6. System (Automated) Use Cases

```mermaid
flowchart LR
    SYS((System))

    SYS --> UC1[Capture Network Packets]
    SYS --> UC2[Extract Features from Packets]
    SYS --> UC3[Classify Traffic via ML]
    SYS --> UC4[Create Alert on Anomaly]
    SYS --> UC5[GeoIP Lookup for Source IP]
    SYS --> UC6[Map to MITRE ATT&CK]
    SYS --> UC7[Correlate Attack Chains]
    SYS --> UC8[Calculate Risk Score]
    SYS --> UC9[Broadcast via WebSocket]
    SYS --> UC10[Fan Out to All Databases]

    UC1 -->|triggers| UC2
    UC2 -->|triggers| UC3
    UC3 -->|if anomaly| UC4
    UC4 -->|triggers| UC5
    UC5 -->|triggers| UC6
    UC6 -->|triggers| UC7
    UC7 -->|triggers| UC8
    UC8 -->|triggers| UC9
    UC9 -->|demo mode| UC10

    style SYS fill:#059669,color:#fff
```
