# DurianDetector IDS — BCE Class Diagrams (Boundary-Control-Entity)
## FYP-26-S1-08

> Paste any of these into [mermaid.live](https://mermaid.live) to render and export as PNG/SVG for your report.

---

## 1. User Authentication BCE

```mermaid
classDiagram
    class LoginPage {
        <<Boundary>>
        +emailField : TextInput
        +passwordField : PasswordInput
        +loginButton : Button
        +registerLink : Link
        +displayError(msg)
        +redirectToDashboard()
    }

    class RegistrationPage {
        <<Boundary>>
        +nameField : TextInput
        +emailField : TextInput
        +passwordField : PasswordInput
        +confirmPasswordField : PasswordInput
        +registerButton : Button
        +displaySuccess(msg)
    }

    class AuthController {
        <<Control>>
        +login(email, password) : JWT
        +register(name, email, password) : User
        +refreshToken(refresh) : JWT
        +tryAuthenticateAcrossDBs(email, password) : User
        +generateJWTWithDbClaim(user, db) : Token
    }

    class CustomUser {
        <<Entity>>
        +id : int
        +email : string
        +password : string
        +role : enum(free, premium, exclusive, admin)
        +team_role : enum(member, analyst, leader)
        +first_name : string
        +last_name : string
        +is_suspended : boolean
        +created_at : datetime
    }

    class UserSubscription {
        <<Entity>>
        +user : CustomUser
        +plan : SubscriptionPlan
        +started_at : datetime
        +is_active : boolean
    }

    LoginPage --> AuthController : submits credentials
    RegistrationPage --> AuthController : submits form
    AuthController --> CustomUser : authenticates / creates
    AuthController --> UserSubscription : creates default subscription
```

---

## 2. Alert Detection & Monitoring BCE

```mermaid
classDiagram
    class DashboardPage {
        <<Boundary>>
        +riskGauge : Component
        +severityChart : Component
        +alertFeed : Component
        +trendChart : Component
        +connectWebSocket()
        +updateOnNewAlert(alert)
    }

    class AlertsPage {
        <<Boundary>>
        +alertTable : DataTable
        +severityFilter : Dropdown
        +typeFilter : Dropdown
        +searchField : TextInput
        +blockIPButton : Button
        +displayAlertDetail(alert)
    }

    class AlertController {
        <<Control>>
        +listAlerts(filters) : Alert[]
        +getAlertDetail(id) : Alert
        +blockIP(alertId) : BlockedIP
        +broadcastAlert(alert) : void
        +fanOutToAllDBs(alert) : void
    }

    class PacketProcessor {
        <<Control>>
        +capturePackets(interface) : RawPacket
        +extractFeatures(packet) : FeatureVector
        +classifyTraffic(features) : Prediction
        +createAlert(prediction, geoData, mitre) : Alert
    }

    class Alert {
        <<Entity>>
        +id : int
        +environment : Environment
        +src_ip : IPAddress
        +dst_ip : IPAddress
        +src_port : int
        +dst_port : int
        +protocol : enum(TCP, UDP, ICMP, HTTP)
        +alert_type : enum(port_scan, dos, brute_force, ...)
        +severity : enum(low, medium, high, critical)
        +confidence_score : float
        +latitude : float
        +longitude : float
        +country : string
        +mitre_tactic : string
        +mitre_technique_id : string
        +timestamp : datetime
    }

    class BlockedIP {
        <<Entity>>
        +ip_address : IPAddress
        +environment : Environment
        +blocked_by : CustomUser
        +reason : string
        +is_active : boolean
    }

    DashboardPage --> AlertController : requests data
    AlertsPage --> AlertController : filters / blocks
    PacketProcessor --> AlertController : creates alerts
    AlertController --> Alert : CRUD operations
    AlertController --> BlockedIP : creates blocks
```

---

## 3. DurianBot Chatbot BCE

```mermaid
classDiagram
    class ChatbotPage {
        <<Boundary>>
        +messageInput : TextArea
        +sendButton : Button
        +sessionList : Sidebar
        +messageList : ScrollView
        +tierBadge : Badge
        +suggestedPrompts : ButtonGroup
        +formatMarkdown(text) : ReactNode
        +showTypingIndicator()
    }

    class ChatbotController {
        <<Control>>
        +sendMessage(msg, sessionId) : Response
        +createSession(title) : ChatSession
        +getSessionHistory(id) : ChatMessage[]
        +deleteSession(id) : void
        +handleConversation(msg, user, tier) : string
        +handleGreeting(msg) : string
        +handleSecurityQuestion(msg) : string
        +callOllama(messages) : string
        +getAlertContext(user) : string
    }

    class ChatSession {
        <<Entity>>
        +id : int
        +user : CustomUser
        +environment : Environment
        +title : string
        +created_at : datetime
        +updated_at : datetime
    }

    class ChatMessage {
        <<Entity>>
        +id : int
        +session : ChatSession
        +role : enum(user, assistant, system)
        +content : string
        +timestamp : datetime
    }

    ChatbotPage --> ChatbotController : sends message
    ChatbotController --> ChatSession : manages sessions
    ChatbotController --> ChatMessage : creates messages
    ChatbotController --> Alert : reads alert context
```

---

## 4. Incident Management BCE

```mermaid
classDiagram
    class IncidentsPage {
        <<Boundary>>
        +incidentTable : DataTable
        +createButton : Button
        +statusFilter : Dropdown
        +severityFilter : Dropdown
        +displayIncidentDetail(incident)
    }

    class IncidentFormModal {
        <<Boundary>>
        +titleField : TextInput
        +descriptionField : TextArea
        +severitySelect : Dropdown
        +alertSelector : MultiSelect
        +assigneeSelect : Dropdown
        +submitButton : Button
    }

    class IncidentController {
        <<Control>>
        +listIncidents(filters) : Incident[]
        +createIncident(data) : Incident
        +updateIncident(id, data) : Incident
        +addNote(incidentId, content) : IncidentNote
        +linkAlerts(incidentId, alertIds) : void
        +resolveIncident(id) : Incident
        +checkSubscription(user) : boolean
    }

    class Incident {
        <<Entity>>
        +id : int
        +environment : Environment
        +title : string
        +description : string
        +severity : enum(low, medium, high, critical)
        +status : enum(open, in_progress, resolved, closed)
        +created_by : CustomUser
        +assigned_to : CustomUser
        +alerts : Alert[]
        +created_at : datetime
        +resolved_at : datetime
    }

    class IncidentNote {
        <<Entity>>
        +id : int
        +incident : Incident
        +author : CustomUser
        +content : string
        +created_at : datetime
    }

    IncidentsPage --> IncidentController : list / filter
    IncidentFormModal --> IncidentController : create / update
    IncidentController --> Incident : CRUD
    IncidentController --> IncidentNote : adds notes
```

---

## 5. Report Generation BCE

```mermaid
classDiagram
    class ReportsPage {
        <<Boundary>>
        +reportTypeSelect : Dropdown
        +dateFromPicker : DateInput
        +dateToPicker : DateInput
        +generateButton : Button
        +reportList : DataTable
        +downloadLink : Link
    }

    class ReportController {
        <<Control>>
        +generateReport(type, dateFrom, dateTo) : Report
        +listReports() : Report[]
        +downloadPDF(reportId) : FileResponse
        +buildReportContent(alerts, incidents) : JSON
        +renderHTML(content) : string
        +convertToPDF(html) : binary
        +checkSubscription(user) : boolean
    }

    class Report {
        <<Entity>>
        +id : int
        +environment : Environment
        +created_by : CustomUser
        +title : string
        +report_type : enum(summary, detailed, incident, threat)
        +date_from : datetime
        +date_to : datetime
        +content : JSON
        +pdf_file : FileField
        +created_at : datetime
    }

    ReportsPage --> ReportController : requests generation
    ReportController --> Report : creates / queries
    ReportController --> Alert : aggregates data
    ReportController --> Incident : aggregates data
```

---

## 6. Subscription Management BCE

```mermaid
classDiagram
    class SubscriptionPage {
        <<Boundary>>
        +tierCards : PricingCard[]
        +currentPlanBadge : Badge
        +upgradeButton : Button
        +checkoutModal : Modal
        +cardInput : TextInput
        +processingAnimation : Spinner
    }

    class SubscriptionController {
        <<Control>>
        +getPlans() : SubscriptionPlan[]
        +getCurrentPlan(user) : UserSubscription
        +checkout(user, planName) : UserSubscription
        +updateUserRole(user, newRole) : void
        +cancelSubscription(user) : void
    }

    class SubscriptionPlan {
        <<Entity>>
        +id : int
        +name : enum(free, premium, exclusive)
        +display_name : string
        +price : decimal
        +billing_cycle : string
        +features : JSON
        +is_active : boolean
    }

    class UserSubscription {
        <<Entity>>
        +user : CustomUser
        +plan : SubscriptionPlan
        +started_at : datetime
        +expires_at : datetime
        +is_active : boolean
    }

    SubscriptionPage --> SubscriptionController : upgrade / view
    SubscriptionController --> SubscriptionPlan : queries plans
    SubscriptionController --> UserSubscription : creates / updates
    SubscriptionController --> CustomUser : updates role
```

---

## 7. ML Engine Configuration BCE

```mermaid
classDiagram
    class MLConfigPage {
        <<Boundary>>
        +modelTypeSelect : Dropdown
        +sensitivitySlider : Slider
        +thresholdInput : NumberInput
        +trainButton : Button
        +metricsDisplay : MetricsCard
        +accuracyChart : Chart
    }

    class MLController {
        <<Control>>
        +getConfig(envId) : MLModelConfig
        +updateConfig(envId, data) : MLModelConfig
        +trainModel(envId) : MLModelMetrics
        +predict(features) : Prediction
        +evaluateModel(config) : MLModelMetrics
        +checkSubscription(user) : boolean
    }

    class MLModelConfig {
        <<Entity>>
        +environment : Environment
        +model_type : enum(random_forest, svm, isolation_forest)
        +sensitivity : enum(low, medium, high)
        +detection_threshold : float
        +trained_at : datetime
        +model_file_path : string
        +is_active : boolean
    }

    class MLModelMetrics {
        <<Entity>>
        +config : MLModelConfig
        +accuracy : float
        +precision : float
        +recall : float
        +f1_score : float
        +training_samples : int
        +evaluated_at : datetime
    }

    MLConfigPage --> MLController : configure / train
    MLController --> MLModelConfig : CRUD
    MLController --> MLModelMetrics : evaluates
```

---

## 8. Attack Chain Analysis BCE

```mermaid
classDiagram
    class AttackChainsPage {
        <<Boundary>>
        +chainTimeline : KillChainView
        +chainList : DataTable
        +riskScoreBadge : Badge
        +mitreTechList : List
        +chainDetailModal : Modal
    }

    class AttackChainController {
        <<Control>>
        +listChains(envId) : AttackChain[]
        +getChainDetail(id) : AttackChain
        +correlateAlerts(alerts) : AttackChain[]
        +calculateRiskScore(chain) : int
        +mapToKillChain(chain) : Phase[]
        +checkSubscription(user) : boolean
    }

    class AttackChain {
        <<Entity>>
        +id : int
        +environment : Environment
        +src_ip : IPAddress
        +chain_type : enum(recon_to_exploit, scan_to_brute, ...)
        +alerts : Alert[]
        +mitre_techniques : MitreTechnique[]
        +risk_score : int
        +status : enum(active, resolved)
        +started_at : datetime
        +last_seen_at : datetime
    }

    class EnvironmentRiskScore {
        <<Entity>>
        +environment : Environment
        +score : int
        +breakdown : JSON
        +calculated_at : datetime
    }

    AttackChainsPage --> AttackChainController : views chains
    AttackChainController --> AttackChain : queries / correlates
    AttackChainController --> EnvironmentRiskScore : calculates
```

---

## 9. Admin Panel BCE

```mermaid
classDiagram
    class AdminDashboard {
        <<Boundary>>
        +userTable : DataTable
        +suspendButton : Button
        +auditLogTable : DataTable
        +healthPanel : StatusCards
        +searchField : TextInput
    }

    class AdminController {
        <<Control>>
        +listUsers() : CustomUser[]
        +suspendUser(id, reason) : void
        +unsuspendUser(id) : void
        +getAuditLogs(filters) : AuditLog[]
        +getSystemHealth() : SystemHealth
        +checkAdminPermission(user) : boolean
    }

    class AuditLog {
        <<Entity>>
        +id : int
        +user : CustomUser
        +environment : Environment
        +action : string
        +target_type : string
        +target_id : int
        +ip_address : IPAddress
        +metadata : JSON
        +timestamp : datetime
    }

    class SystemHealth {
        <<Entity>>
        +checked_at : datetime
        +celery_status : string
        +redis_status : string
        +postgres_status : string
        +cpu_percent : float
        +memory_percent : float
        +disk_usage_percent : float
        +alerts_last_hour : int
    }

    AdminDashboard --> AdminController : manages
    AdminController --> CustomUser : suspends / queries
    AdminController --> AuditLog : queries
    AdminController --> SystemHealth : monitors
```
