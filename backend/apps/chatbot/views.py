"""
Views for chatbot app — Ollama-powered AI assistant for DurianDetector IDS.
Provides chat session management and AI-powered security analysis.
"""
import logging
import requests
from django.conf import settings
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChatSession, ChatMessage
from .serializers import (
    ChatSessionListSerializer,
    ChatSessionDetailSerializer,
    ChatInputSerializer,
    ChatMessageSerializer,
)
from apps.alerts.models import Alert
from apps.environments.models import EnvironmentMembership

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are DurianBot, the AI security assistant for DurianDetector IDS. "
    "You help security analysts understand alerts, investigate threats, and "
    "recommend mitigation strategies. You have knowledge of MITRE ATT&CK "
    "framework, network security, and intrusion detection. Be concise and actionable."
)


def _get_user_environment(user):
    """Helper to get user's environment."""
    membership = EnvironmentMembership.objects.filter(
        user=user
    ).select_related('environment').first()
    return membership.environment if membership else None


def _build_alert_context(user):
    """Build context string from recent alerts for the LLM."""
    env = _get_user_environment(user)
    if not env:
        return "No environment configured. No alert data available."

    recent_alerts = Alert.objects.filter(environment=env).order_by('-timestamp')[:10]
    if not recent_alerts:
        return "No recent alerts detected in the current environment."

    lines = ["Recent IDS Alerts (last 10):"]
    for alert in recent_alerts:
        lines.append(
            f"- [{alert.severity.upper()}] {alert.get_alert_type_display()} | "
            f"Src: {alert.src_ip}:{alert.src_port or '?'} -> Dst: {alert.dst_ip}:{alert.dst_port or '?'} | "
            f"Protocol: {alert.protocol} | Confidence: {alert.confidence_score:.0%} | "
            f"MITRE: {alert.mitre_tactic or 'N/A'} ({alert.mitre_technique_id or 'N/A'}) | "
            f"Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M')}"
        )

    # Summary stats
    from django.db.models import Count
    severity_counts = (
        Alert.objects.filter(environment=env)
        .values('severity')
        .annotate(count=Count('id'))
    )
    summary_parts = [f"{s['severity']}: {s['count']}" for s in severity_counts]
    lines.append(f"\nAlert severity breakdown: {', '.join(summary_parts) if summary_parts else 'None'}")

    return "\n".join(lines)


def _call_ollama(messages):
    """
    Call the Ollama API for chat completion.
    Returns the assistant message content or None on failure.
    """
    ollama_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
    ollama_model = getattr(settings, 'OLLAMA_MODEL', 'llama3.2')

    try:
        response = requests.post(
            f"{ollama_url}/api/chat",
            json={
                "model": ollama_model,
                "messages": messages,
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("content", "").strip()
    except requests.exceptions.ConnectionError:
        logger.warning("Ollama is not reachable at %s", ollama_url)
        return None
    except requests.exceptions.Timeout:
        logger.warning("Ollama request timed out.")
        return None
    except Exception as e:
        logger.error("Ollama API error: %s", str(e))
        return None


def _fallback_response(user_message):
    """
    Generate a helpful pre-built response when Ollama is unavailable.
    Uses pattern matching for common IDS questions.
    """
    msg = user_message.lower()

    if any(kw in msg for kw in ['critical alert', 'latest alert', 'recent alert', 'new alert']):
        return (
            "I'm currently unable to connect to the AI model, but I can help guide you. "
            "To review your latest alerts:\n\n"
            "1. Navigate to the **Alerts** page from the sidebar\n"
            "2. Filter by **Critical** severity to see the most urgent items\n"
            "3. Click on any alert to view full details including source IP, "
            "destination, protocol, and MITRE ATT&CK mapping\n\n"
            "Critical alerts typically require immediate investigation and potential IP blocking."
        )

    if any(kw in msg for kw in ['port scan', 'scanning', 'reconnaissance']):
        return (
            "**Port Scanning** is a reconnaissance technique (MITRE T1046 - Network Service Discovery). "
            "Here's how to investigate:\n\n"
            "1. Check the source IP in your alerts — is it internal or external?\n"
            "2. Look for sequential port access patterns (e.g., ports 1-1024)\n"
            "3. If external, consider blocking the source IP\n"
            "4. Check if the target ports correspond to sensitive services (SSH:22, RDP:3389, etc.)\n"
            "5. Review if this IP has triggered other alert types\n\n"
            "**Mitigation**: Block the source IP, update firewall rules, and ensure only necessary ports are exposed."
        )

    if any(kw in msg for kw in ['brute force', 'password', 'login attempt']):
        return (
            "**Brute Force** attacks (MITRE T1110) involve repeated login attempts. "
            "Investigation steps:\n\n"
            "1. Identify the target service (SSH, RDP, web login)\n"
            "2. Check the source IP — single or distributed attack?\n"
            "3. Verify if any accounts were compromised\n"
            "4. Review authentication logs for successful logins\n\n"
            "**Mitigation**: Implement account lockout policies, use MFA, block the attacking IP, "
            "and consider rate limiting on authentication endpoints."
        )

    if any(kw in msg for kw in ['dos', 'ddos', 'denial of service', 'flood']):
        return (
            "**Denial of Service** attacks (MITRE T1499) aim to overwhelm your systems. "
            "Investigation steps:\n\n"
            "1. Check traffic volume and patterns in the alerts\n"
            "2. Identify if it's a single source (DoS) or distributed (DDoS)\n"
            "3. Look for common DoS types: SYN flood, UDP flood, HTTP flood\n"
            "4. Monitor system resources (CPU, memory, bandwidth)\n\n"
            "**Mitigation**: Enable rate limiting, use a CDN or DDoS protection service, "
            "block malicious IPs, and implement SYN cookies."
        )

    if any(kw in msg for kw in ['sql injection', 'sqli', 'injection']):
        return (
            "**SQL Injection** (MITRE T1190) targets web application databases. "
            "Investigation steps:\n\n"
            "1. Check the raw payload in the alert for SQL patterns (UNION, SELECT, DROP, etc.)\n"
            "2. Identify the targeted web endpoint\n"
            "3. Verify if the injection was successful by checking application logs\n"
            "4. Review database logs for unauthorized queries\n\n"
            "**Mitigation**: Use parameterized queries, implement WAF rules, "
            "validate all user inputs, and apply least-privilege database access."
        )

    if any(kw in msg for kw in ['mitre', 'att&ck', 'attack framework', 'technique']):
        return (
            "The **MITRE ATT&CK** framework categorizes adversary tactics and techniques. "
            "DurianDetector maps alerts to MITRE techniques. Key tactics to watch:\n\n"
            "- **Reconnaissance** (TA0043): Port scans, service discovery\n"
            "- **Initial Access** (TA0001): Exploits, phishing\n"
            "- **Credential Access** (TA0006): Brute force, credential dumping\n"
            "- **Lateral Movement** (TA0008): RDP, SSH tunneling\n"
            "- **Impact** (TA0040): DoS, data destruction\n\n"
            "Navigate to the **MITRE ATT&CK** page in the sidebar for a full matrix view of your alerts."
        )

    if any(kw in msg for kw in ['threat', 'threat source', 'top source', 'malicious ip']):
        return (
            "To analyze **threat sources** in DurianDetector:\n\n"
            "1. Visit the **Threats** page for a breakdown of top source IPs\n"
            "2. Use the **GeoIP Map** to visualize attack origins geographically\n"
            "3. Check for repeat offenders — IPs with multiple alert types\n"
            "4. Block persistent threats using the IP blocking feature\n\n"
            "Look for patterns: are attacks coming from the same country or ASN? "
            "This can help identify coordinated campaigns."
        )

    if any(kw in msg for kw in ['block', 'blocklist', 'firewall', 'ban']):
        return (
            "To **block a malicious IP** in DurianDetector:\n\n"
            "1. Navigate to the alert detail page\n"
            "2. Click the **Block IP** button for the source IP\n"
            "3. The IP will be added to your environment's blocklist\n"
            "4. You can manage blocked IPs from the Threats page\n\n"
            "Consider blocking IPs that show repeated malicious behavior across multiple alert types."
        )

    # Generic fallback
    return (
        "I'm DurianBot, your IDS security assistant. I'm currently running in offline mode "
        "(the AI model is not connected), but I can help with:\n\n"
        "- **Alert analysis**: Ask about specific alert types or severities\n"
        "- **Threat investigation**: Port scans, brute force, DoS, SQL injection\n"
        "- **MITRE ATT&CK**: Mapping alerts to the framework\n"
        "- **Mitigation strategies**: How to respond to specific threats\n\n"
        "Try asking something specific like:\n"
        "- 'How do I investigate a port scan?'\n"
        "- 'What are the latest critical alerts?'\n"
        "- 'Explain brute force attack mitigation'"
    )


def _fallback_free_response(user_message):
    """
    Free tier: short, basic tips without MITRE ATT&CK details.
    Encourages upgrading to Premium for more detail.
    """
    msg = user_message.lower()

    if any(kw in msg for kw in ['port scan', 'scanning', 'reconnaissance']):
        return (
            "Port scanning detected? Check if the source IP is external and consider blocking it. "
            "Review your firewall rules to ensure only necessary ports are exposed.\n\n"
            "*Upgrade to Premium for detailed MITRE ATT&CK analysis and step-by-step investigation guides.*"
        )

    if any(kw in msg for kw in ['brute force', 'password', 'login attempt']):
        return (
            "Brute force attack detected? Enable account lockout policies and consider implementing MFA. "
            "Block the attacking IP immediately.\n\n"
            "*Upgrade to Premium for detailed remediation steps and MITRE ATT&CK mapping.*"
        )

    if any(kw in msg for kw in ['dos', 'ddos', 'denial of service', 'flood']):
        return (
            "DoS/DDoS attack? Enable rate limiting and block malicious IPs. "
            "Monitor your system resources (CPU, memory, bandwidth).\n\n"
            "*Upgrade to Premium for comprehensive DoS analysis and mitigation strategies.*"
        )

    if any(kw in msg for kw in ['sql injection', 'sqli', 'injection']):
        return (
            "SQL injection detected? Ensure your application uses parameterized queries. "
            "Review the alert payload and check application logs.\n\n"
            "*Upgrade to Premium for detailed investigation steps and WAF recommendations.*"
        )

    if any(kw in msg for kw in ['block', 'firewall', 'ban']):
        return (
            "To block a malicious IP, go to the alert detail page and click 'Block IP'. "
            "The IP will be added to your environment's blocklist.\n\n"
            "*Upgrade to Premium for advanced threat analysis and team-based IP management.*"
        )

    if any(kw in msg for kw in ['help', 'what can you do', 'how']):
        return (
            "I'm DurianBot (Basic Mode). I can give you quick tips on:\n"
            "- Port scans, brute force, DoS attacks\n"
            "- IP blocking and basic firewall advice\n\n"
            "*Upgrade to Premium for MITRE ATT&CK analysis, or Exclusive for full AI-powered assistance.*"
        )

    return (
        "I'm DurianBot running in Basic mode. I can help with quick security tips.\n\n"
        "Try asking about: port scans, brute force attacks, DoS, SQL injection, or IP blocking.\n\n"
        "*Upgrade to Premium for detailed analysis or Exclusive for AI-powered responses.*"
    )


class ChatSessionListView(generics.ListAPIView):
    """List all chat sessions for the authenticated user."""
    serializer_class = ChatSessionListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)


class ChatSessionDetailView(generics.RetrieveAPIView):
    """Get a single chat session with all its messages."""
    serializer_class = ChatSessionDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)


class DeleteChatSessionView(generics.DestroyAPIView):
    """Delete a chat session."""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)


class ChatSendMessageView(APIView):
    """
    Send a message and receive an AI response.
    Creates a new session if session_id is not provided.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChatInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_message = serializer.validated_data['message']
        session_id = serializer.validated_data.get('session_id')
        user = request.user

        # Get or create session
        if session_id:
            try:
                session = ChatSession.objects.get(id=session_id, user=user)
            except ChatSession.DoesNotExist:
                return Response(
                    {"error": "Chat session not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            # Auto-generate title from first message
            title = user_message[:50] + ('...' if len(user_message) > 50 else '')
            session = ChatSession.objects.create(user=user, title=title)

        # Save user message
        user_msg = ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.USER,
            content=user_message,
        )

        # ── Tier-based response logic ──
        user_role = user.role
        chatbot_tier = 'basic'

        if user_role in ('exclusive', 'admin'):
            # EXCLUSIVE: Full Ollama LLM with alert context + conversation history
            chatbot_tier = 'ai'
            alert_context = _build_alert_context(user)
            system_content = f"{SYSTEM_PROMPT}\n\nCurrent Environment Data:\n{alert_context}"

            ollama_messages = [{"role": "system", "content": system_content}]

            history = ChatMessage.objects.filter(session=session).exclude(
                role=ChatMessage.Role.SYSTEM
            ).order_by('timestamp')[:20]
            for msg in history:
                ollama_messages.append({"role": msg.role, "content": msg.content})

            assistant_content = _call_ollama(ollama_messages)
            if not assistant_content:
                # Fallback to premium-level if Ollama is unavailable
                assistant_content = _fallback_response(user_message)

        elif user_role == 'premium':
            # PREMIUM: Detailed pattern-matching with MITRE ATT&CK references
            chatbot_tier = 'enhanced'
            assistant_content = _fallback_response(user_message)

        else:
            # FREE: Basic short tips, encourages upgrade
            chatbot_tier = 'basic'
            assistant_content = _fallback_free_response(user_message)

        # Save assistant message
        assistant_msg = ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.ASSISTANT,
            content=assistant_content,
        )

        # Touch session updated_at
        session.save(update_fields=['updated_at'])

        return Response({
            "session_id": session.id,
            "session_title": session.title,
            "user_message": ChatMessageSerializer(user_msg).data,
            "assistant_message": ChatMessageSerializer(assistant_msg).data,
            "chatbot_tier": chatbot_tier,
        }, status=status.HTTP_200_OK)
