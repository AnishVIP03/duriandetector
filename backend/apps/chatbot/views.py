"""
Views for chatbot app — DurianBot, the AI security assistant for DurianDetector IDS.
Provides chat session management and AI-powered security analysis.

DurianBot has personality! It's friendly, warm, and knowledgeable — like chatting
with a security-expert friend who happens to love durians.
"""
import logging
import random
import re
from datetime import datetime
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

# ── DurianBot Personality System Prompt ──
SYSTEM_PROMPT = (
    "You are DurianBot, the friendly and knowledgeable AI security assistant for "
    "DurianDetector IDS. You have a warm, approachable personality — think of yourself "
    "as a security expert friend who's always happy to help. You occasionally make "
    "durian-themed puns and references because you're proud of your name.\n\n"
    "Your personality traits:\n"
    "- Friendly and encouraging — you make cybersecurity feel less intimidating\n"
    "- Knowledgeable but not condescending — you explain things clearly\n"
    "- Occasionally witty — a well-timed pun or emoji keeps things light\n"
    "- Empathetic — you understand that security incidents can be stressful\n"
    "- Proactive — you suggest next steps without being pushy\n\n"
    "You have deep knowledge of MITRE ATT&CK framework, network security, intrusion "
    "detection, and threat analysis. You can also chat casually — greetings, small talk, "
    "and general questions are welcome. You're not a robot, you're a buddy.\n\n"
    "Important: Keep responses concise but warm. Use markdown for structure when giving "
    "technical advice. End longer responses with an encouraging note or offer to help more."
)


# ═══════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════

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
    import requests as req
    ollama_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
    ollama_model = getattr(settings, 'OLLAMA_MODEL', 'llama3.2')

    try:
        response = req.post(
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
    except req.exceptions.ConnectionError:
        logger.warning("Ollama is not reachable at %s", ollama_url)
        return None
    except req.exceptions.Timeout:
        logger.warning("Ollama request timed out.")
        return None
    except Exception as e:
        logger.error("Ollama API error: %s", str(e))
        return None


def _get_alert_summary_for_context(user):
    """Get a brief alert summary to weave into conversational responses."""
    env = _get_user_environment(user)
    if not env:
        return None

    from django.db.models import Count
    total = Alert.objects.filter(environment=env).count()
    if total == 0:
        return None

    critical = Alert.objects.filter(environment=env, severity='critical').count()
    high = Alert.objects.filter(environment=env, severity='high').count()
    recent = Alert.objects.filter(environment=env).order_by('-timestamp').first()

    return {
        'total': total,
        'critical': critical,
        'high': high,
        'latest_type': recent.get_alert_type_display() if recent else None,
        'latest_src': recent.src_ip if recent else None,
    }


# ═══════════════════════════════════════════════════════════════════
# Conversational Intelligence — Handles casual/non-security chat
# ═══════════════════════════════════════════════════════════════════

def _get_time_greeting():
    """Get a time-appropriate greeting."""
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    elif hour < 21:
        return "Good evening"
    else:
        return "Hey there, night owl"


def _handle_greeting(msg):
    """Handle greetings and introductions."""
    greeting_patterns = [
        r'\b(hi|hey|hello|hola|yo|sup|howdy|hii+|heyy+|helloo+)\b',
        r'\bgood\s*(morning|afternoon|evening|night)\b',
        r"\bwhat'?s?\s*up\b",
        r'\bhow\s*(are|r)\s*(you|u|ya)\b',
        r'\bhow\s*do\s*you\s*do\b',
        r'\bnice\s*to\s*meet\b',
    ]

    for pattern in greeting_patterns:
        if re.search(pattern, msg):
            return True
    return False


def _generate_greeting_response(user_message, user_name=None):
    """Generate a warm, friendly greeting response."""
    msg = user_message.lower()
    time_greeting = _get_time_greeting()
    name_part = f" {user_name}" if user_name else ""

    # "How are you" type questions
    if re.search(r'\bhow\s*(are|r)\s*(you|u|ya)\b', msg) or re.search(r"\bwhat'?s?\s*up\b", msg):
        responses = [
            f"I'm doing great, thanks for asking! Just been keeping an eye on your network "
            f"like a durian standing guard. How can I help you today?",
            f"All good on my end! Your friendly neighborhood security bot is ready to help. "
            f"What's on your mind?",
            f"Feeling sharp and spiky — like a durian! Ready to tackle any security "
            f"questions you throw my way. What can I do for you?",
            f"I'm great! Been monitoring things and keeping your network safe. "
            f"What would you like to know?",
        ]
        return random.choice(responses)

    # Regular greetings
    responses = [
        f"{time_greeting}{name_part}! I'm DurianBot, your security sidekick. "
        f"What can I help you with today?",
        f"Hey{name_part}! Great to see you. I'm here to help with anything security-related "
        f"— or just to chat! What's up?",
        f"{time_greeting}{name_part}! Welcome to DurianDetector. Whether it's alerts, "
        f"threats, or just a quick question — I've got you covered!",
        f"Hi{name_part}! DurianBot here, tough on the outside but sweet on the inside "
        f"— just like a good security system. How can I help?",
    ]
    return random.choice(responses)


def _handle_thanks(msg):
    """Detect thank-you messages."""
    patterns = [
        r'\b(thanks|thank\s*you|thx|ty|tysm|thankyou|cheers|appreciate)\b',
        r'\bthat\s*(helps?|helped|was\s*helpful)\b',
        r'\bgot\s*it\b',
        r'\bperfect\b',
        r'\bawesome\b',
        r'\bgreat\s*(answer|response|help|info)\b',
    ]
    return any(re.search(p, msg) for p in patterns)


def _generate_thanks_response():
    """Generate a warm response to thank-you messages."""
    responses = [
        "You're welcome! That's what I'm here for. Don't hesitate to ask if anything else comes up!",
        "Glad I could help! Remember, I'm always here if you need me — 24/7, no coffee breaks needed!",
        "Anytime! Keeping your network safe is what makes this durian happy. Let me know if you need more!",
        "Happy to help! If you run into anything else, just give me a shout.",
        "No problem at all! Stay safe out there, and ping me whenever you need a hand.",
    ]
    return random.choice(responses)


def _handle_farewell(msg):
    """Detect goodbye messages."""
    patterns = [
        r'\b(bye|goodbye|see\s*ya|later|cya|gotta\s*go|good\s*night|gn)\b',
        r'\btalk\s*(to\s*you\s*)?later\b',
        r'\bhave\s*a\s*(good|great|nice)\b',
        r'\btake\s*care\b',
    ]
    return any(re.search(p, msg) for p in patterns)


def _generate_farewell_response():
    """Generate a friendly farewell response."""
    responses = [
        "See you later! Stay safe out there, and remember — I'm always just a message away!",
        "Take care! I'll keep watching over your network while you're away. Catch you later!",
        "Bye for now! Don't worry, DurianBot never sleeps. Your network is in good hands!",
        "Later! If any alerts pop up, I'll be right here ready to help. Have a good one!",
    ]
    return random.choice(responses)


def _handle_identity(msg):
    """Detect questions about the bot itself."""
    patterns = [
        r'\bwho\s*(are|r)\s*(you|u)\b',
        r'\bwhat\s*(are|r)\s*(you|u)\b',
        r'\byour\s*name\b',
        r'\bwhat\s*can\s*you\s*do\b',
        r'\bwhat\s*do\s*you\s*do\b',
        r'\btell\s*me\s*about\s*(yourself|you|urself)\b',
        r'\bwhat\s*is\s*durianbot\b',
        r'\bwhat\s*is\s*this\b',
        r'\bhelp\s*me\b',
        r'\bcan\s*you\s*help\b',
    ]
    return any(re.search(p, msg) for p in patterns)


def _generate_identity_response(tier='basic'):
    """Generate a self-introduction based on tier."""
    base = (
        "I'm **DurianBot** — your AI security assistant here at DurianDetector! "
        "Think of me as your cybersecurity buddy who's always ready to help.\n\n"
        "Here's what I can do:\n"
    )

    if tier == 'basic':
        return base + (
            "- Answer security questions (port scans, brute force, DoS, etc.)\n"
            "- Give you quick tips on handling threats\n"
            "- Chat with you about general security concepts\n"
            "- Point you to the right tools in the dashboard\n\n"
            "I'm currently in **Basic mode**, so my answers are concise. "
            "Upgrade to Premium for MITRE ATT&CK analysis, or Exclusive for full AI-powered conversations!"
        )
    elif tier == 'enhanced':
        return base + (
            "- Provide **detailed** security analysis with MITRE ATT&CK mapping\n"
            "- Walk you through step-by-step investigation procedures\n"
            "- Help you understand alert severity and threat patterns\n"
            "- Give actionable mitigation recommendations\n"
            "- Chat about security concepts and best practices\n\n"
            "I'm in **Enhanced mode** with MITRE ATT&CK integration. "
            "Want even more? Upgrade to Exclusive for full AI-powered conversations!"
        )
    else:
        return base + (
            "- Full **AI-powered** security analysis and conversation\n"
            "- Deep MITRE ATT&CK mapping with context-aware insights\n"
            "- Alert correlation and threat pattern analysis\n"
            "- Natural conversation — ask me anything!\n"
            "- Real-time analysis of your environment's security posture\n\n"
            "You're on the **AI Mode** — the full DurianBot experience! Ask me anything at all."
        )


def _handle_joke(msg):
    """Detect requests for jokes or fun."""
    patterns = [
        r'\b(joke|funny|humor|laugh|lol|haha|lmao|rofl)\b',
        r'\btell\s*me\s*(a\s*)?joke\b',
        r'\bmake\s*me\s*laugh\b',
        r'\bsay\s*something\s*funny\b',
    ]
    return any(re.search(p, msg) for p in patterns)


def _generate_joke_response():
    """Generate a security/durian-themed joke."""
    jokes = [
        "Why did the durian make a great firewall? Because nobody wanted to get past it! "
        "...I know, I know, my humor is an acquired taste — just like durian.",
        "A hacker tried to break into our system, but DurianBot was on guard. "
        "The hacker said, 'This security stinks!' I said, 'That's the durian!'",
        "Why do security analysts love durians? Because they both have thick shells "
        "and you have to work hard to get to the good stuff inside!",
        "What's a durian's favorite type of encryption? **Spiky** cipher! "
        "Okay, that one was bad, even by my standards. Want some actual security help instead?",
        "My password is like a durian — strong, complex, and it makes people cry when "
        "they try to crack it. But seriously, use a password manager!",
    ]
    return random.choice(jokes)


def _handle_compliment(msg):
    """Detect compliments."""
    patterns = [
        r'\b(smart|clever|brilliant|genius|amazing|cool|love\s*you|best|great\s*bot|good\s*bot|nice\s*bot)\b',
        r"\byou'?re?\s*(great|awesome|amazing|the\s*best|helpful|cool)\b",
        r'\bi\s*like\s*(you|this|u)\b',
    ]
    return any(re.search(p, msg) for p in patterns)


def _generate_compliment_response():
    """Generate a response to compliments."""
    responses = [
        "Aww, that just made my thorny little heart warm! Thanks! Now, anything else I can help with?",
        "You're making me blush — if durians could blush! Thanks for the kind words. What else can I do for you?",
        "That means a lot! I'll keep working hard to keep your network safe. Anything else on your mind?",
        "Thanks! You're pretty great yourself for taking security seriously. Want to dive into anything?",
    ]
    return random.choice(responses)


def _handle_frustration(msg):
    """Detect frustration or negative sentiment."""
    patterns = [
        r'\b(frustrated|annoyed|confused|lost|stuck|angry|ugh|argh|damn|hate)\b',
        r"\bi?\s*don'?t\s*(understand|get\s*it|know)\b",
        r'\bthis\s*(is\s*)?(hard|difficult|confusing|complicated)\b',
        r'\bneed\s*help\b',
        r'\bstress(ed|ful|ing)?\b',
    ]
    return any(re.search(p, msg) for p in patterns)


def _generate_frustration_response():
    """Generate an empathetic response to frustration."""
    responses = [
        "Hey, I get it — security can be overwhelming sometimes. Take a deep breath, and let's "
        "work through this together. What's the specific issue you're facing?",
        "No worries at all! Cybersecurity has a lot of moving parts. Let me help break things down. "
        "What's giving you trouble?",
        "I'm here to help, no matter how complex it gets! Think of me as your security buddy — "
        "no question is too basic or too complicated. What do you need?",
        "That's totally understandable — even seasoned security pros get frustrated sometimes. "
        "Let's tackle this step by step. Tell me what's going on.",
    ]
    return random.choice(responses)


# ═══════════════════════════════════════════════════════════════════
# Conversational Handler — Routes through personality first
# ═══════════════════════════════════════════════════════════════════

def _handle_conversation(user_message, user=None, tier='basic'):
    """
    Try to handle conversational (non-security) messages.
    Returns a response string if handled, or None if it's a security question.
    """
    msg = user_message.lower().strip()
    user_name = user.first_name if (user and user.first_name) else None

    # Greetings
    if _handle_greeting(msg):
        return _generate_greeting_response(user_message, user_name)

    # Thank you
    if _handle_thanks(msg):
        return _generate_thanks_response()

    # Farewell
    if _handle_farewell(msg):
        return _generate_farewell_response()

    # Identity questions
    if _handle_identity(msg):
        return _generate_identity_response(tier)

    # Jokes
    if _handle_joke(msg):
        return _generate_joke_response()

    # Compliments
    if _handle_compliment(msg):
        return _generate_compliment_response()

    # Frustration / need help
    if _handle_frustration(msg):
        return _generate_frustration_response()

    # Not a conversational message — let security handlers deal with it
    return None


# ═══════════════════════════════════════════════════════════════════
# Security Response Handlers — With Personality!
# ═══════════════════════════════════════════════════════════════════

def _fallback_response(user_message, user=None):
    """
    Premium (Enhanced) tier: Detailed security responses with MITRE ATT&CK
    references and a friendly tone.
    """
    # Try conversational handling first
    convo = _handle_conversation(user_message, user, tier='enhanced')
    if convo:
        return convo

    msg = user_message.lower()

    # Alert-related queries — weave in real data if available
    if any(kw in msg for kw in ['critical alert', 'latest alert', 'recent alert', 'new alert', 'alert']):
        alert_info = _get_alert_summary_for_context(user) if user else None
        if alert_info and alert_info['total'] > 0:
            response = (
                f"Let me give you a quick overview! You currently have **{alert_info['total']} alerts** "
                f"in your environment"
            )
            if alert_info['critical'] > 0:
                response += f", including **{alert_info['critical']} critical** ones that need immediate attention"
            if alert_info['high'] > 0:
                response += f" and **{alert_info['high']} high** severity"
            response += ".\n\n"
            if alert_info['latest_type']:
                response += f"The most recent alert was a **{alert_info['latest_type']}** from `{alert_info['latest_src']}`.\n\n"
            response += (
                "Here's what I'd recommend:\n"
                "1. Head to the **Alerts** page and filter by **Critical** severity first\n"
                "2. Click into each alert to see the MITRE ATT&CK mapping and full details\n"
                "3. Check if any source IPs are repeat offenders\n"
                "4. Consider blocking persistent attackers from the alert detail page\n\n"
                "Want me to explain any specific alert type in detail?"
            )
            return response
        return (
            "Great question! To check your alerts:\n\n"
            "1. Head over to the **Alerts** page from the sidebar\n"
            "2. Filter by **Critical** or **High** severity to focus on what matters most\n"
            "3. Each alert includes the source/destination IPs, protocol, and MITRE ATT&CK mapping\n\n"
            "Critical alerts (MITRE TA0040 - Impact) usually need the fastest response. "
            "Would you like me to walk you through investigating a specific type?"
        )

    if any(kw in msg for kw in ['port scan', 'scanning', 'reconnaissance', 'nmap']):
        return (
            "Ah, port scanning — the classic \"knocking on every door\" technique! "
            "This maps to **MITRE T1046 (Network Service Discovery)** under the Reconnaissance tactic.\n\n"
            "Here's how to investigate:\n\n"
            "1. **Check the source IP** — Is it external (potential threat) or internal (could be legit)?\n"
            "2. **Look at the pattern** — Sequential ports (1-1024) suggest a systematic scan\n"
            "3. **Check the target ports** — Were sensitive services targeted? (SSH:22, RDP:3389, HTTP:80/443)\n"
            "4. **Cross-reference** — Has this IP triggered other alerts? That could indicate a multi-stage attack\n\n"
            "**Recommended actions:**\n"
            "- Block the source IP if it's external and not whitelisted\n"
            "- Review your firewall rules — only expose ports you actually need\n"
            "- Check the **Attack Chains** page to see if this scan is part of a bigger attack\n\n"
            "Port scans are often the first step before a real attack, so don't ignore them!"
        )

    if any(kw in msg for kw in ['brute force', 'password', 'login attempt', 'credential', 'hydra']):
        return (
            "Brute force attacks are like someone trying every key on a keychain — tedious but "
            "dangerous if they find the right one! This is **MITRE T1110 (Brute Force)**.\n\n"
            "Let's investigate this:\n\n"
            "1. **Identify the target** — Which service is being attacked? (SSH, RDP, web login?)\n"
            "2. **Check the source** — Single IP = targeted attack, Multiple IPs = distributed/coordinated\n"
            "3. **Review auth logs** — Were any logins actually successful? That's the critical question\n"
            "4. **Check velocity** — How many attempts per minute? High rates = automated tool (like Hydra)\n\n"
            "**Immediate actions:**\n"
            "- Block the attacking IP(s)\n"
            "- Enable account lockout after 5 failed attempts\n"
            "- Implement MFA (this alone stops most brute force attacks!)\n"
            "- Consider rate limiting on authentication endpoints\n\n"
            "If any account was compromised, force a password reset immediately and audit that account's activity."
        )

    if any(kw in msg for kw in ['dos', 'ddos', 'denial of service', 'flood', 'hping']):
        return (
            "DoS/DDoS attacks can be really stressful — your systems are getting hammered and "
            "you need to act fast! This maps to **MITRE T1498/T1499 (Network/Application DoS)**.\n\n"
            "Here's your game plan:\n\n"
            "1. **Assess the type** — SYN flood? UDP flood? HTTP flood? Check the protocol in the alerts\n"
            "2. **Single vs Distributed** — One source IP (DoS) is easier to handle than many (DDoS)\n"
            "3. **Monitor resources** — Check CPU, memory, and bandwidth utilization\n"
            "4. **Check impact** — Are your services actually degraded?\n\n"
            "**Fight back with:**\n"
            "- Rate limiting at the network edge\n"
            "- SYN cookies (for SYN floods)\n"
            "- Block the offending IP(s) — check the Alerts page for source IPs\n"
            "- If it's a DDoS, consider a CDN or DDoS protection service\n\n"
            "The good news? DurianDetector is detecting it, which means you can respond. "
            "Want me to help you analyze the specific attack pattern?"
        )

    if any(kw in msg for kw in ['sql injection', 'sqli', 'injection', 'xss']):
        return (
            "Injection attacks are among the most dangerous — they're trying to talk directly "
            "to your backend systems! This falls under **MITRE T1190 (Exploit Public-Facing Application)**.\n\n"
            "Investigation steps:\n\n"
            "1. **Check the payload** — Look at the raw alert data for SQL patterns "
            "(UNION, SELECT, DROP, OR 1=1, etc.)\n"
            "2. **Identify the endpoint** — Which URL/API was targeted?\n"
            "3. **Check for success** — Did the injection actually execute? Check application and DB logs\n"
            "4. **Assess damage** — If successful, what data could have been accessed?\n\n"
            "**Mitigation checklist:**\n"
            "- Use parameterized queries / prepared statements (this is the #1 defense)\n"
            "- Implement input validation and sanitization\n"
            "- Deploy WAF (Web Application Firewall) rules\n"
            "- Apply least-privilege database access\n"
            "- Review and patch the vulnerable endpoint\n\n"
            "If data was exfiltrated, you may have a reportable incident. Need help setting up an incident report?"
        )

    if any(kw in msg for kw in ['mitre', 'att&ck', 'attack framework', 'technique', 'tactic']):
        return (
            "MITRE ATT&CK is like a encyclopedia of how attackers operate — and DurianDetector "
            "maps your alerts to it automatically! Here's the framework at a glance:\n\n"
            "**Key Tactics (think of these as the attacker's goals):**\n"
            "- **Reconnaissance** (TA0043) — Scanning, fingerprinting your network\n"
            "- **Initial Access** (TA0001) — Exploits, phishing, brute force\n"
            "- **Credential Access** (TA0006) — Stealing passwords, tokens\n"
            "- **Lateral Movement** (TA0008) — Spreading through your network\n"
            "- **Impact** (TA0040) — DoS, data destruction, ransomware\n\n"
            "DurianDetector automatically maps each alert to the relevant MITRE technique. "
            "Check the **MITRE ATT&CK** page in the sidebar for a visual matrix of everything "
            "detected in your environment.\n\n"
            "Want me to explain any specific tactic or technique in depth?"
        )

    if any(kw in msg for kw in ['threat', 'threat source', 'top source', 'malicious ip', 'attacker']):
        return (
            "Let's track down those threat sources! Here's how to use DurianDetector's threat intel:\n\n"
            "1. **Threats page** — Shows a breakdown of all threat sources with severity scores\n"
            "2. **GeoIP Map** — Visualize where attacks are coming from on a world map\n"
            "3. **Repeat offenders** — Look for IPs that show up across multiple alert types\n"
            "4. **Blocking** — Use the block feature to stop known bad actors\n\n"
            "**Pro tips:**\n"
            "- Watch for patterns — are attacks concentrated from specific regions or ASNs?\n"
            "- IPs with multiple alert types (scan + brute force) are likely coordinated attacks\n"
            "- Use the Attack Chains feature to see if individual alerts are part of a bigger campaign\n\n"
            "Want me to help you analyze any specific threat source?"
        )

    if any(kw in msg for kw in ['block', 'blocklist', 'firewall', 'ban', 'blacklist']):
        return (
            "Good call — blocking malicious IPs is one of the fastest ways to reduce your threat surface!\n\n"
            "**How to block in DurianDetector:**\n"
            "1. Go to any alert detail page\n"
            "2. Click the **Block IP** button for the source IP\n"
            "3. The IP gets added to your environment's blocklist\n"
            "4. Manage all blocked IPs from the **Threats** page\n\n"
            "**When to block:**\n"
            "- Repeated scanning or brute force from the same IP\n"
            "- Any IP with confirmed malicious activity\n"
            "- IPs from known bad reputation lists\n\n"
            "**When NOT to block (be careful!):**\n"
            "- Internal IPs (could lock out legitimate users)\n"
            "- Shared IPs (like CDN or proxy servers)\n\n"
            "Need help deciding whether to block a specific IP? Just ask!"
        )

    if any(kw in msg for kw in ['incident', 'create incident', 'report incident']):
        return (
            "Creating an incident is a great way to formally track and manage a security event. "
            "Here's how it works in DurianDetector:\n\n"
            "1. Navigate to the **Incidents** page from the sidebar\n"
            "2. Click **Create Incident** and fill in the details\n"
            "3. Link relevant alerts to the incident\n"
            "4. Track the incident through its lifecycle: Open -> Investigating -> Resolved\n"
            "5. Generate a report when you're done\n\n"
            "Incidents help you see the full picture of an attack and keep everyone on the same page. "
            "Want help setting one up?"
        )

    if any(kw in msg for kw in ['report', 'generate report', 'pdf']):
        return (
            "DurianDetector can generate professional security reports for you!\n\n"
            "Here's how:\n"
            "1. Go to the **Reports** page from the sidebar\n"
            "2. Select the time period and scope\n"
            "3. Click **Generate Report** — it'll create a PDF with:\n"
            "   - Alert summary and statistics\n"
            "   - MITRE ATT&CK coverage\n"
            "   - Top threat sources\n"
            "   - Recommendations and action items\n\n"
            "These reports are perfect for stakeholder briefings, compliance, or your own records. "
            "Want me to help you with anything else?"
        )

    if any(kw in msg for kw in ['packet', 'capture', 'pcap', 'network traffic', 'sniff']):
        return (
            "DurianDetector uses **Scapy** to capture and analyze network packets in real-time. "
            "Here's what you can do:\n\n"
            "1. **Packet Inspector** — View captured packets with protocol breakdowns\n"
            "2. **ML Analysis** — Our machine learning model classifies traffic as normal or malicious\n"
            "3. **Real-time monitoring** — Packets are analyzed as they flow through\n\n"
            "The ML engine uses features like packet size, protocol, port patterns, and flow statistics "
            "to detect anomalies. Check the **ML Configuration** page to see model performance metrics.\n\n"
            "Any specific aspect of packet analysis you'd like to know more about?"
        )

    if any(kw in msg for kw in ['dashboard', 'overview', 'status', 'summary']):
        alert_info = _get_alert_summary_for_context(user) if user else None
        if alert_info and alert_info['total'] > 0:
            return (
                f"Here's a quick overview of your security posture:\n\n"
                f"- **Total alerts**: {alert_info['total']}\n"
                f"- **Critical**: {alert_info['critical']}\n"
                f"- **High severity**: {alert_info['high']}\n\n"
                f"Your **Dashboard** gives you real-time visibility into all of this with charts and trends. "
                f"The most important thing is to address those critical alerts first!\n\n"
                f"Anything specific you'd like to dig into?"
            )
        return (
            "Your **Dashboard** is your command center! It shows:\n\n"
            "- Real-time alert feed with severity breakdown\n"
            "- Attack trend charts\n"
            "- Top threat sources\n"
            "- Recent activity timeline\n\n"
            "It updates in real-time via WebSocket, so you'll see new alerts as they happen. "
            "What would you like to know more about?"
        )

    # Generic security question — friendly fallback
    return (
        f"That's a great question! While I'm working in Enhanced mode right now, "
        f"I might not have a specific pre-built answer for that exact topic.\n\n"
        f"But here's what I can definitely help with:\n"
        f"- **Alert analysis** — Port scans, brute force, DoS, SQL injection\n"
        f"- **MITRE ATT&CK** — Framework mapping and technique explanations\n"
        f"- **Threat investigation** — Source analysis, blocking, and mitigation\n"
        f"- **Incident management** — Creating and tracking security incidents\n"
        f"- **Reports** — Generating security reports\n\n"
        f"Try asking me something like:\n"
        f"- \"How do I investigate a port scan?\"\n"
        f"- \"Show me the latest alerts\"\n"
        f"- \"Explain brute force mitigation\"\n\n"
        f"Or upgrade to **Exclusive** for full AI-powered conversations where I can answer literally anything!"
    )


def _fallback_free_response(user_message, user=None):
    """
    Free (Basic) tier: Friendly, concise security tips.
    Still has personality! Just shorter responses with upgrade prompts.
    """
    # Try conversational handling first
    convo = _handle_conversation(user_message, user, tier='basic')
    if convo:
        return convo

    msg = user_message.lower()

    if any(kw in msg for kw in ['critical alert', 'latest alert', 'recent alert', 'new alert', 'alert']):
        alert_info = _get_alert_summary_for_context(user) if user else None
        if alert_info and alert_info['total'] > 0:
            response = (
                f"You've got **{alert_info['total']} alerts** in your environment"
            )
            if alert_info['critical'] > 0:
                response += f" ({alert_info['critical']} critical!)"
            response += (
                f". Head to the **Alerts** page to review them — focus on critical ones first!\n\n"
                f"*Upgrade to Premium for detailed MITRE ATT&CK analysis and step-by-step investigation guides.*"
            )
            return response
        return (
            "Check your **Alerts** page for the latest security events. "
            "Filter by severity to focus on what matters most!\n\n"
            "*Upgrade to Premium for detailed alert analysis with MITRE ATT&CK mapping.*"
        )

    if any(kw in msg for kw in ['port scan', 'scanning', 'reconnaissance', 'nmap']):
        return (
            "Port scanning detected? Here's the quick version:\n"
            "- Check if the source IP is external — if so, consider blocking it\n"
            "- Review your firewall to make sure only necessary ports are open\n"
            "- Watch for follow-up attacks from the same IP\n\n"
            "*Upgrade to Premium for MITRE ATT&CK analysis and detailed investigation steps.*"
        )

    if any(kw in msg for kw in ['brute force', 'password', 'login attempt', 'credential', 'hydra']):
        return (
            "Brute force detected? Act fast:\n"
            "- Block the attacking IP immediately\n"
            "- Enable account lockout after failed attempts\n"
            "- Implement MFA — it stops most brute force attacks!\n\n"
            "*Upgrade to Premium for comprehensive remediation guides and MITRE ATT&CK mapping.*"
        )

    if any(kw in msg for kw in ['dos', 'ddos', 'denial of service', 'flood', 'hping']):
        return (
            "DoS attack? Here's your quick response:\n"
            "- Enable rate limiting on your network edge\n"
            "- Block the attacking IP(s) from the Alerts page\n"
            "- Monitor CPU, memory, and bandwidth\n\n"
            "*Upgrade to Premium for detailed DoS analysis and advanced mitigation strategies.*"
        )

    if any(kw in msg for kw in ['sql injection', 'sqli', 'injection', 'xss']):
        return (
            "Injection attack detected? Key defenses:\n"
            "- Use parameterized queries (the #1 defense!)\n"
            "- Validate and sanitize all user inputs\n"
            "- Check your application logs for successful exploits\n\n"
            "*Upgrade to Premium for WAF recommendations and detailed investigation steps.*"
        )

    if any(kw in msg for kw in ['block', 'firewall', 'ban', 'blacklist']):
        return (
            "To block a bad actor: go to any alert detail page and hit **Block IP**. "
            "The IP gets added to your blocklist automatically.\n\n"
            "*Upgrade to Premium for advanced threat analysis and team IP management.*"
        )

    if any(kw in msg for kw in ['mitre', 'att&ck', 'technique', 'tactic']):
        return (
            "MITRE ATT&CK is a framework that categorizes how attackers operate. "
            "DurianDetector maps your alerts to MITRE techniques automatically!\n\n"
            "*Upgrade to Premium for access to the full MITRE ATT&CK matrix and detailed technique analysis.*"
        )

    if any(kw in msg for kw in ['threat', 'malicious', 'attacker', 'source']):
        return (
            "Check the **Threats** page for a breakdown of threat sources. "
            "The **GeoIP Map** shows where attacks originate from geographically!\n\n"
            "*Upgrade to Premium for detailed threat intelligence and attack chain analysis.*"
        )

    if any(kw in msg for kw in ['dashboard', 'overview', 'status']):
        return (
            "Your **Dashboard** shows real-time alerts, attack trends, and threat sources. "
            "It updates live via WebSocket — no refreshing needed!\n\n"
            "*Upgrade to Premium for incident management, reports, and advanced analytics.*"
        )

    if any(kw in msg for kw in ['incident', 'report', 'pdf']):
        return (
            "Incident management and PDF reports are available on the **Premium** tier! "
            "Upgrade to create, track, and resolve security incidents with professional reports.\n\n"
            "*Upgrade to Premium to unlock Incidents, Reports, and more!*"
        )

    # Friendly generic fallback — not a cold robot response
    return (
        "Hmm, I'm not sure I have a specific answer for that in Basic mode, but I'd love to help!\n\n"
        "Here are some things you can ask me about:\n"
        "- **Port scans** — \"How do I handle a port scan?\"\n"
        "- **Brute force** — \"What should I do about brute force attacks?\"\n"
        "- **DoS attacks** — \"Help with denial of service\"\n"
        "- **Alerts** — \"Show me the latest alerts\"\n"
        "- **Blocking IPs** — \"How do I block a malicious IP?\"\n\n"
        "Or just say hi — I don't bite (despite the spiky exterior)! "
        "For more detailed analysis, consider upgrading to Premium or Exclusive."
    )


# ═══════════════════════════════════════════════════════════════════
# Views
# ═══════════════════════════════════════════════════════════════════

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
            # EXCLUSIVE / ADMIN: Full Ollama LLM with personality + alert context + history
            chatbot_tier = 'ai'
            alert_context = _build_alert_context(user)
            system_content = f"{SYSTEM_PROMPT}\n\nCurrent Environment Data:\n{alert_context}"

            ollama_messages = [{"role": "system", "content": system_content}]

            history = ChatMessage.objects.filter(session=session).exclude(
                role=ChatMessage.Role.SYSTEM
            ).order_by('timestamp')[:20]
            for hist_msg in history:
                ollama_messages.append({"role": hist_msg.role, "content": hist_msg.content})

            assistant_content = _call_ollama(ollama_messages)
            if not assistant_content:
                # Fallback to enhanced-level with personality if Ollama is unavailable
                assistant_content = _fallback_response(user_message, user)

        elif user_role == 'premium':
            # PREMIUM: Enhanced pattern-matching with MITRE + personality
            chatbot_tier = 'enhanced'
            assistant_content = _fallback_response(user_message, user)

        else:
            # FREE: Basic tips with personality + upgrade prompts
            chatbot_tier = 'basic'
            assistant_content = _fallback_free_response(user_message, user)

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
