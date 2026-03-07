"""
Management command to seed the ThreatIntelligence table with ~30 realistic
threat entries covering a mix of sources, threat types, and MITRE ATT&CK
mappings.

Usage:
    python manage.py seed_threats
    python manage.py seed_threats --clear   # delete existing entries first
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.threats.models import ThreatIntelligence


# ── Seed data ────────────────────────────────────────────────────────────────

THREAT_ENTRIES = [
    # ── Scanners (T1595 - Active Scanning) ───────────────────────────────
    {
        "ip_address": "185.220.101.1",
        "domain": None,
        "threat_type": "scanner",
        "source": "AbuseIPDB",
        "confidence": 0.95,
        "description": "Aggressive port scanner targeting SSH and RDP services across multiple networks.",
        "tags": ["port-scan", "ssh", "rdp", "reconnaissance"],
        "mitre_tactic": "Reconnaissance",
        "mitre_technique": "Active Scanning",
        "mitre_technique_id": "T1595",
    },
    {
        "ip_address": "45.33.32.10",
        "domain": None,
        "threat_type": "scanner",
        "source": "Emerging Threats",
        "confidence": 0.88,
        "description": "Known Shodan-like scanner probing for exposed IoT devices and open databases.",
        "tags": ["iot", "scanner", "database", "reconnaissance"],
        "mitre_tactic": "Reconnaissance",
        "mitre_technique": "Active Scanning",
        "mitre_technique_id": "T1595",
    },
    {
        "ip_address": "198.51.100.15",
        "domain": None,
        "threat_type": "scanner",
        "source": "AlienVault OTX",
        "confidence": 0.82,
        "description": "Horizontal scanner probing TCP/443 and TCP/8443 looking for vulnerable web servers.",
        "tags": ["web", "https", "scanner"],
        "mitre_tactic": "Reconnaissance",
        "mitre_technique": "Active Scanning",
        "mitre_technique_id": "T1595",
    },
    {
        "ip_address": "203.0.113.50",
        "domain": None,
        "threat_type": "scanner",
        "source": "Built-in",
        "confidence": 0.75,
        "description": "Low-rate stealth scanner performing SYN scans across class-B networks.",
        "tags": ["syn-scan", "stealth", "reconnaissance"],
        "mitre_tactic": "Reconnaissance",
        "mitre_technique": "Active Scanning",
        "mitre_technique_id": "T1595",
    },
    # ── Brute Force (T1110 - Brute Force) ────────────────────────────────
    {
        "ip_address": "185.220.101.22",
        "domain": None,
        "threat_type": "brute_force",
        "source": "AbuseIPDB",
        "confidence": 0.97,
        "description": "Persistent SSH brute-force attacker with over 50,000 login attempts in 24 hours.",
        "tags": ["ssh", "brute-force", "credential-stuffing"],
        "mitre_tactic": "Credential Access",
        "mitre_technique": "Brute Force",
        "mitre_technique_id": "T1110",
    },
    {
        "ip_address": "45.33.32.25",
        "domain": None,
        "threat_type": "brute_force",
        "source": "Emerging Threats",
        "confidence": 0.91,
        "description": "RDP brute-force source using common username/password combinations.",
        "tags": ["rdp", "brute-force", "windows"],
        "mitre_tactic": "Credential Access",
        "mitre_technique": "Brute Force",
        "mitre_technique_id": "T1110",
    },
    {
        "ip_address": "198.51.100.33",
        "domain": None,
        "threat_type": "brute_force",
        "source": "AlienVault OTX",
        "confidence": 0.85,
        "description": "FTP brute-force source targeting web hosting providers.",
        "tags": ["ftp", "brute-force", "web-hosting"],
        "mitre_tactic": "Credential Access",
        "mitre_technique": "Brute Force",
        "mitre_technique_id": "T1110",
    },
    {
        "ip_address": "203.0.113.77",
        "domain": None,
        "threat_type": "brute_force",
        "source": "Built-in",
        "confidence": 0.78,
        "description": "Distributed brute-force campaign against WordPress admin panels.",
        "tags": ["wordpress", "brute-force", "http"],
        "mitre_tactic": "Credential Access",
        "mitre_technique": "Brute Force",
        "mitre_technique_id": "T1110",
    },
    # ── Botnet (T1071 - Application Layer Protocol) ──────────────────────
    {
        "ip_address": "185.220.101.40",
        "domain": "c2-node1.badnet.example",
        "threat_type": "botnet",
        "source": "AbuseIPDB",
        "confidence": 0.99,
        "description": "Confirmed Mirai botnet C2 server actively issuing DDoS commands.",
        "tags": ["mirai", "botnet", "c2", "ddos"],
        "mitre_tactic": "Command and Control",
        "mitre_technique": "Application Layer Protocol",
        "mitre_technique_id": "T1071",
    },
    {
        "ip_address": "45.33.32.41",
        "domain": "beacon.darkcloud.example",
        "threat_type": "botnet",
        "source": "AlienVault OTX",
        "confidence": 0.93,
        "description": "Emotet botnet relay node distributing spam payloads via HTTPS.",
        "tags": ["emotet", "botnet", "spam", "relay"],
        "mitre_tactic": "Command and Control",
        "mitre_technique": "Application Layer Protocol",
        "mitre_technique_id": "T1071",
    },
    {
        "ip_address": "198.51.100.55",
        "domain": "bot-ctrl.evilnet.example",
        "threat_type": "botnet",
        "source": "Emerging Threats",
        "confidence": 0.87,
        "description": "IRC-based botnet controller associated with credential-harvesting campaigns.",
        "tags": ["irc", "botnet", "credential-harvest"],
        "mitre_tactic": "Command and Control",
        "mitre_technique": "Application Layer Protocol",
        "mitre_technique_id": "T1071",
    },
    {
        "ip_address": "203.0.113.99",
        "domain": None,
        "threat_type": "botnet",
        "source": "Built-in",
        "confidence": 0.72,
        "description": "Suspected botnet drone sending periodic DNS beacons to known C2 domains.",
        "tags": ["dns-beacon", "botnet", "drone"],
        "mitre_tactic": "Command and Control",
        "mitre_technique": "Application Layer Protocol",
        "mitre_technique_id": "T1071",
    },
    # ── Malware (T1204 - User Execution) ─────────────────────────────────
    {
        "ip_address": "185.220.101.60",
        "domain": "payload.malhost.example",
        "threat_type": "malware",
        "source": "AbuseIPDB",
        "confidence": 0.96,
        "description": "Hosts obfuscated JavaScript payloads that drop ransomware on victim machines.",
        "tags": ["ransomware", "javascript", "dropper"],
        "mitre_tactic": "Execution",
        "mitre_technique": "User Execution",
        "mitre_technique_id": "T1204",
    },
    {
        "ip_address": "45.33.32.62",
        "domain": "dl.trojan-kit.example",
        "threat_type": "malware",
        "source": "AlienVault OTX",
        "confidence": 0.90,
        "description": "Serves trojanised software installers bundled with keylogger payloads.",
        "tags": ["trojan", "keylogger", "installer"],
        "mitre_tactic": "Execution",
        "mitre_technique": "User Execution",
        "mitre_technique_id": "T1204",
    },
    {
        "ip_address": "198.51.100.70",
        "domain": "update.fakeav.example",
        "threat_type": "malware",
        "source": "Emerging Threats",
        "confidence": 0.83,
        "description": "Fake antivirus update server distributing info-stealer malware.",
        "tags": ["fake-av", "infostealer", "social-engineering"],
        "mitre_tactic": "Execution",
        "mitre_technique": "User Execution",
        "mitre_technique_id": "T1204",
    },
    {
        "ip_address": "203.0.113.120",
        "domain": None,
        "threat_type": "malware",
        "source": "Built-in",
        "confidence": 0.68,
        "description": "Suspected malware staging server with encrypted payloads over port 8443.",
        "tags": ["staging", "encrypted", "malware"],
        "mitre_tactic": "Execution",
        "mitre_technique": "User Execution",
        "mitre_technique_id": "T1204",
    },
    # ── Phishing ─────────────────────────────────────────────────────────
    {
        "ip_address": "185.220.101.80",
        "domain": "login-secure.bankfraud.example",
        "threat_type": "phishing",
        "source": "AbuseIPDB",
        "confidence": 0.94,
        "description": "Hosts convincing banking phishing page mimicking a major financial institution.",
        "tags": ["phishing", "banking", "credential-theft"],
        "mitre_tactic": "Initial Access",
        "mitre_technique": "Phishing",
        "mitre_technique_id": "T1566",
    },
    {
        "ip_address": "45.33.32.82",
        "domain": "office365-verify.phish.example",
        "threat_type": "phishing",
        "source": "AlienVault OTX",
        "confidence": 0.89,
        "description": "Office 365 credential-harvesting page with valid TLS certificate.",
        "tags": ["phishing", "office365", "credential-harvest"],
        "mitre_tactic": "Initial Access",
        "mitre_technique": "Phishing",
        "mitre_technique_id": "T1566",
    },
    {
        "ip_address": "198.51.100.84",
        "domain": "secure-update.phish.example",
        "threat_type": "phishing",
        "source": "Emerging Threats",
        "confidence": 0.80,
        "description": "Phishing kit impersonating cloud provider login to steal API keys.",
        "tags": ["phishing", "cloud", "api-keys"],
        "mitre_tactic": "Initial Access",
        "mitre_technique": "Phishing",
        "mitre_technique_id": "T1566",
    },
    # ── Tor Exit Nodes ───────────────────────────────────────────────────
    {
        "ip_address": "185.220.101.100",
        "domain": None,
        "threat_type": "tor_exit_node",
        "source": "AbuseIPDB",
        "confidence": 0.98,
        "description": "Active Tor exit node frequently associated with abuse reports.",
        "tags": ["tor", "exit-node", "anonymisation"],
        "mitre_tactic": "Command and Control",
        "mitre_technique": "Proxy",
        "mitre_technique_id": "T1090",
    },
    {
        "ip_address": "45.33.32.101",
        "domain": None,
        "threat_type": "tor_exit_node",
        "source": "Emerging Threats",
        "confidence": 0.92,
        "description": "Tor exit node listed in multiple blocklists for scanning activity.",
        "tags": ["tor", "exit-node", "blocklist"],
        "mitre_tactic": "Command and Control",
        "mitre_technique": "Proxy",
        "mitre_technique_id": "T1090",
    },
    {
        "ip_address": "198.51.100.102",
        "domain": None,
        "threat_type": "tor_exit_node",
        "source": "AlienVault OTX",
        "confidence": 0.86,
        "description": "Known Tor exit relay used to tunnel brute-force traffic.",
        "tags": ["tor", "exit-node", "brute-force-tunnel"],
        "mitre_tactic": "Command and Control",
        "mitre_technique": "Proxy",
        "mitre_technique_id": "T1090",
    },
    # ── Proxy ────────────────────────────────────────────────────────────
    {
        "ip_address": "185.220.101.110",
        "domain": None,
        "threat_type": "proxy",
        "source": "AbuseIPDB",
        "confidence": 0.88,
        "description": "Open SOCKS proxy used to relay attack traffic and obfuscate origins.",
        "tags": ["socks-proxy", "open-proxy", "relay"],
        "mitre_tactic": "Command and Control",
        "mitre_technique": "Proxy",
        "mitre_technique_id": "T1090",
    },
    {
        "ip_address": "45.33.32.112",
        "domain": None,
        "threat_type": "proxy",
        "source": "Built-in",
        "confidence": 0.74,
        "description": "Residential proxy endpoint associated with credential-stuffing campaigns.",
        "tags": ["residential-proxy", "credential-stuffing"],
        "mitre_tactic": "Command and Control",
        "mitre_technique": "Proxy",
        "mitre_technique_id": "T1090",
    },
    # ── Spam ─────────────────────────────────────────────────────────────
    {
        "ip_address": "198.51.100.120",
        "domain": "mail.spammer.example",
        "threat_type": "spam",
        "source": "AbuseIPDB",
        "confidence": 0.91,
        "description": "High-volume spam relay sending phishing lures and malware attachments.",
        "tags": ["spam", "email", "phishing-lure"],
        "mitre_tactic": "Initial Access",
        "mitre_technique": "Phishing",
        "mitre_technique_id": "T1566",
    },
    {
        "ip_address": "203.0.113.130",
        "domain": "bulk.spambot.example",
        "threat_type": "spam",
        "source": "Emerging Threats",
        "confidence": 0.84,
        "description": "Spam botnet node distributing pharmaceutical and advance-fee fraud messages.",
        "tags": ["spam", "botnet", "fraud"],
        "mitre_tactic": "Initial Access",
        "mitre_technique": "Phishing",
        "mitre_technique_id": "T1566",
    },
    {
        "ip_address": "185.220.101.135",
        "domain": None,
        "threat_type": "spam",
        "source": "AlienVault OTX",
        "confidence": 0.77,
        "description": "Compromised mail server sending unsolicited bulk email with malicious links.",
        "tags": ["spam", "compromised-server", "malicious-links"],
        "mitre_tactic": "Initial Access",
        "mitre_technique": "Phishing",
        "mitre_technique_id": "T1566",
    },
    # ── Additional mixed entries ─────────────────────────────────────────
    {
        "ip_address": "45.33.32.140",
        "domain": "cryptominer.pool.example",
        "threat_type": "malware",
        "source": "AlienVault OTX",
        "confidence": 0.86,
        "description": "Cryptojacking pool proxy redirecting compromised hosts to mine cryptocurrency.",
        "tags": ["cryptominer", "cryptojacking", "mining-pool"],
        "mitre_tactic": "Execution",
        "mitre_technique": "User Execution",
        "mitre_technique_id": "T1204",
    },
    {
        "ip_address": "198.51.100.150",
        "domain": None,
        "threat_type": "scanner",
        "source": "Built-in",
        "confidence": 0.70,
        "description": "DNS enumeration scanner probing for zone transfer vulnerabilities.",
        "tags": ["dns", "zone-transfer", "enumeration"],
        "mitre_tactic": "Reconnaissance",
        "mitre_technique": "Active Scanning",
        "mitre_technique_id": "T1595",
    },
    {
        "ip_address": "203.0.113.160",
        "domain": None,
        "threat_type": "brute_force",
        "source": "AbuseIPDB",
        "confidence": 0.92,
        "description": "Distributed SSH brute-force source rotating through cloud provider IP ranges.",
        "tags": ["ssh", "brute-force", "cloud", "distributed"],
        "mitre_tactic": "Credential Access",
        "mitre_technique": "Brute Force",
        "mitre_technique_id": "T1110",
    },
]


class Command(BaseCommand):
    help = "Seed the ThreatIntelligence table with ~30 known malicious IPs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing ThreatIntelligence entries before seeding.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            count, _ = ThreatIntelligence.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f"Deleted {count} existing threat entries.")
            )

        now = timezone.now()
        created = 0

        for entry_data in THREAT_ENTRIES:
            _, was_created = ThreatIntelligence.objects.get_or_create(
                ip_address=entry_data["ip_address"],
                threat_type=entry_data["threat_type"],
                source=entry_data["source"],
                defaults={
                    "domain": entry_data.get("domain") or "",
                    "confidence": entry_data["confidence"],
                    "last_seen": now,
                    "description": entry_data["description"],
                    "tags": entry_data["tags"],
                    "mitre_tactic": entry_data.get("mitre_tactic", ""),
                    "mitre_technique": entry_data.get("mitre_technique", ""),
                    "mitre_technique_id": entry_data.get("mitre_technique_id", ""),
                    "is_active": True,
                },
            )
            if was_created:
                created += 1

        total = len(THREAT_ENTRIES)
        skipped = total - created
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeding complete: {created} created, {skipped} already existed "
                f"(total defined: {total})."
            )
        )
