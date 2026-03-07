"""
Management command to seed the database with realistic MITRE ATT&CK data.
Usage: python manage.py seed_mitre
"""
from django.core.management.base import BaseCommand
from apps.mitre.models import MitreTactic, MitreTechnique


MITRE_DATA = [
    {
        'tactic_id': 'TA0001',
        'name': 'Initial Access',
        'description': (
            'The adversary is trying to get into your network. '
            'Initial Access consists of techniques that use various entry vectors '
            'to gain their initial foothold within a network.'
        ),
        'techniques': [
            {
                'technique_id': 'T1190',
                'name': 'Exploit Public-Facing Application',
                'description': (
                    'Adversaries may attempt to exploit a weakness in an Internet-facing '
                    'host or system to initially access a network. The weakness may be a '
                    'software bug, a temporary glitch, or a misconfiguration.'
                ),
                'detection_hint': (
                    'Monitor application logs for abnormal behavior. Use web application '
                    'firewalls to detect exploit attempts against public-facing services.'
                ),
                'mitigation': (
                    'Keep software updated. Use WAFs. Perform regular vulnerability scanning.'
                ),
                'maps_to_alert_types': ['sql_injection', 'xss'],
            },
            {
                'technique_id': 'T1133',
                'name': 'External Remote Services',
                'description': (
                    'Adversaries may leverage external-facing remote services to initially '
                    'access or persist within a network. Remote services such as VPNs, '
                    'Citrix, and other access mechanisms allow users to connect to internal '
                    'resources from external locations.'
                ),
                'detection_hint': (
                    'Monitor for unusual login activity on remote services, especially '
                    'from unexpected geographic locations or at unusual times.'
                ),
                'mitigation': (
                    'Enforce MFA on remote services. Limit access to remote services '
                    'to authorized IP ranges. Monitor VPN logs for anomalies.'
                ),
                'maps_to_alert_types': ['suspicious_ip'],
            },
            {
                'technique_id': 'T1078',
                'name': 'Valid Accounts',
                'description': (
                    'Adversaries may obtain and abuse credentials of existing accounts '
                    'as a means of gaining initial access, persistence, privilege '
                    'escalation, or defense evasion.'
                ),
                'detection_hint': (
                    'Monitor for anomalous account activity such as logins at unusual '
                    'hours, from unexpected IPs, or concurrent sessions from different locations.'
                ),
                'mitigation': (
                    'Enforce strong password policies. Use MFA. Monitor for credential '
                    'leaks in threat intelligence feeds.'
                ),
                'maps_to_alert_types': ['brute_force', 'suspicious_ip'],
            },
        ],
    },
    {
        'tactic_id': 'TA0002',
        'name': 'Execution',
        'description': (
            'The adversary is trying to run malicious code. '
            'Execution consists of techniques that result in adversary-controlled '
            'code running on a local or remote system.'
        ),
        'techniques': [
            {
                'technique_id': 'T1059',
                'name': 'Command and Scripting Interpreter',
                'description': (
                    'Adversaries may abuse command and script interpreters to execute '
                    'commands, scripts, or binaries. These interfaces include PowerShell, '
                    'Bash, Python, and Windows Command Shell.'
                ),
                'detection_hint': (
                    'Monitor process creation for suspicious command-line arguments. '
                    'Log and review script execution events.'
                ),
                'mitigation': (
                    'Restrict script execution via AppLocker or similar controls. '
                    'Enable PowerShell logging. Use constrained language mode.'
                ),
                'maps_to_alert_types': ['protocol_anomaly'],
            },
            {
                'technique_id': 'T1203',
                'name': 'Exploitation for Client Execution',
                'description': (
                    'Adversaries may exploit software vulnerabilities in client '
                    'applications to execute code. Vulnerabilities exist in web browsers, '
                    'office applications, and other commonly installed software.'
                ),
                'detection_hint': (
                    'Monitor for unusual process spawning from client applications. '
                    'Look for browser or office suite processes launching command shells.'
                ),
                'mitigation': (
                    'Keep client applications patched. Use application sandboxing. '
                    'Deploy exploit protection tools.'
                ),
                'maps_to_alert_types': ['xss', 'sql_injection'],
            },
            {
                'technique_id': 'T1047',
                'name': 'Windows Management Instrumentation',
                'description': (
                    'Adversaries may abuse Windows Management Instrumentation (WMI) '
                    'to execute malicious commands and payloads. WMI provides a uniform '
                    'environment for local and remote access to Windows system components.'
                ),
                'detection_hint': (
                    'Monitor WMI activity and WMI event subscriptions. Look for '
                    'wmiprvse.exe spawning unexpected child processes.'
                ),
                'mitigation': (
                    'Restrict WMI access using DCOM permissions. Monitor WMI logs. '
                    'Use endpoint detection and response tools.'
                ),
                'maps_to_alert_types': ['protocol_anomaly'],
            },
        ],
    },
    {
        'tactic_id': 'TA0003',
        'name': 'Persistence',
        'description': (
            'The adversary is trying to maintain their foothold. '
            'Persistence consists of techniques that adversaries use to keep '
            'access to systems across restarts, changed credentials, and other '
            'interruptions.'
        ),
        'techniques': [
            {
                'technique_id': 'T1098',
                'name': 'Account Manipulation',
                'description': (
                    'Adversaries may manipulate accounts to maintain or elevate '
                    'access to victim systems. Account manipulation may consist of '
                    'modifying permissions, credentials, or security groups.'
                ),
                'detection_hint': (
                    'Monitor for changes to user account properties, group membership, '
                    'or permission settings.'
                ),
                'mitigation': (
                    'Enforce least-privilege access. Use privileged access management. '
                    'Audit account changes regularly.'
                ),
                'maps_to_alert_types': ['suspicious_ip'],
            },
            {
                'technique_id': 'T1136',
                'name': 'Create Account',
                'description': (
                    'Adversaries may create an account to maintain access to victim '
                    'systems. With sufficient access, creating accounts can be used '
                    'to establish secondary persistent access.'
                ),
                'detection_hint': (
                    'Monitor for newly created accounts, especially those created '
                    'outside of normal business procedures.'
                ),
                'mitigation': (
                    'Restrict account creation privileges. Audit new account creation '
                    'events. Use multi-factor authentication.'
                ),
                'maps_to_alert_types': ['suspicious_ip'],
            },
            {
                'technique_id': 'T1053',
                'name': 'Scheduled Task/Job',
                'description': (
                    'Adversaries may abuse task scheduling functionality to facilitate '
                    'initial or recurring execution of malicious code. Utilities such as '
                    'at, cron, and schtasks can be used to schedule programs.'
                ),
                'detection_hint': (
                    'Monitor scheduled task creation and modifications. Look for tasks '
                    'executing from unusual locations or with suspicious arguments.'
                ),
                'mitigation': (
                    'Restrict task scheduling to authorized users. Monitor and audit '
                    'scheduled task events.'
                ),
                'maps_to_alert_types': ['protocol_anomaly'],
            },
        ],
    },
    {
        'tactic_id': 'TA0004',
        'name': 'Privilege Escalation',
        'description': (
            'The adversary is trying to gain higher-level permissions. '
            'Privilege Escalation consists of techniques that adversaries use to '
            'gain higher-level permissions on a system or network.'
        ),
        'techniques': [
            {
                'technique_id': 'T1068',
                'name': 'Exploitation for Privilege Escalation',
                'description': (
                    'Adversaries may exploit software vulnerabilities in an attempt '
                    'to elevate privileges. Exploitation of a software vulnerability '
                    'occurs when an adversary takes advantage of a programming error.'
                ),
                'detection_hint': (
                    'Monitor for abnormal process behavior such as unexpected privilege '
                    'changes, unusual system calls, or suspicious parent-child process '
                    'relationships.'
                ),
                'mitigation': (
                    'Keep systems patched. Use exploit mitigation tools. Enforce '
                    'least privilege principles.'
                ),
                'maps_to_alert_types': ['protocol_anomaly', 'sql_injection'],
            },
            {
                'technique_id': 'T1055',
                'name': 'Process Injection',
                'description': (
                    'Adversaries may inject code into processes in order to evade '
                    'process-based defenses as well as possibly elevate privileges. '
                    'Process injection is a method of executing arbitrary code in the '
                    'address space of a live process.'
                ),
                'detection_hint': (
                    'Monitor for API calls associated with process injection such as '
                    'VirtualAllocEx, WriteProcessMemory, and CreateRemoteThread.'
                ),
                'mitigation': (
                    'Use endpoint detection tools with process injection monitoring. '
                    'Restrict debug privileges.'
                ),
                'maps_to_alert_types': ['protocol_anomaly'],
            },
        ],
    },
    {
        'tactic_id': 'TA0005',
        'name': 'Defense Evasion',
        'description': (
            'The adversary is trying to avoid being detected. '
            'Defense Evasion consists of techniques that adversaries use to '
            'avoid detection throughout their compromise.'
        ),
        'techniques': [
            {
                'technique_id': 'T1070',
                'name': 'Indicator Removal',
                'description': (
                    'Adversaries may delete or modify artifacts generated on a host '
                    'system, including logs and captured files, to remove evidence '
                    'of their presence or hinder defenses.'
                ),
                'detection_hint': (
                    'Monitor for file deletion of log files, clearing of event logs, '
                    'or modification of security tool configurations.'
                ),
                'mitigation': (
                    'Forward logs to a remote SIEM. Restrict access to log files. '
                    'Enable tamper protection on security tools.'
                ),
                'maps_to_alert_types': ['protocol_anomaly'],
            },
            {
                'technique_id': 'T1036',
                'name': 'Masquerading',
                'description': (
                    'Adversaries may attempt to manipulate features of their artifacts '
                    'to make them appear legitimate or benign to users and security tools. '
                    'Masquerading occurs when the name or location of an object is '
                    'manipulated.'
                ),
                'detection_hint': (
                    'Monitor for file names that do not match their expected file type. '
                    'Verify that system binaries are signed and in expected locations.'
                ),
                'mitigation': (
                    'Restrict file and directory permissions. Use code signing. '
                    'Monitor for files in unusual locations.'
                ),
                'maps_to_alert_types': ['protocol_anomaly'],
            },
            {
                'technique_id': 'T1027',
                'name': 'Obfuscated Files or Information',
                'description': (
                    'Adversaries may attempt to make an executable or file difficult '
                    'to discover or analyze by encrypting, encoding, or otherwise '
                    'obfuscating its contents.'
                ),
                'detection_hint': (
                    'Detect obfuscated scripts, base64-encoded payloads, and packed '
                    'executables using YARA rules or behavioral analysis.'
                ),
                'mitigation': (
                    'Use anti-malware tools with deobfuscation capabilities. '
                    'Monitor for script execution with encoded arguments.'
                ),
                'maps_to_alert_types': ['protocol_anomaly'],
            },
        ],
    },
    {
        'tactic_id': 'TA0006',
        'name': 'Credential Access',
        'description': (
            'The adversary is trying to steal account names and passwords. '
            'Credential Access consists of techniques for stealing credentials '
            'like account names and passwords.'
        ),
        'techniques': [
            {
                'technique_id': 'T1110',
                'name': 'Brute Force',
                'description': (
                    'Adversaries may use brute force techniques to gain access to '
                    'accounts when passwords are unknown or when password hashes are '
                    'obtained. They may systematically guess passwords or use credential '
                    'stuffing attacks.'
                ),
                'detection_hint': (
                    'Monitor authentication logs for multiple failed login attempts '
                    'from a single source. Set thresholds for lockout policies.'
                ),
                'mitigation': (
                    'Enforce account lockout policies. Use MFA. Implement rate limiting '
                    'on authentication endpoints.'
                ),
                'maps_to_alert_types': ['brute_force'],
            },
            {
                'technique_id': 'T1003',
                'name': 'OS Credential Dumping',
                'description': (
                    'Adversaries may attempt to dump credentials to obtain account '
                    'login and credential material, normally in the form of a hash '
                    'or clear text password.'
                ),
                'detection_hint': (
                    'Monitor for access to LSASS memory, SAM registry hive, or NTDS.dit. '
                    'Detect tools like Mimikatz through behavioral signatures.'
                ),
                'mitigation': (
                    'Enable Credential Guard. Restrict debug privileges. Monitor for '
                    'suspicious LSASS access.'
                ),
                'maps_to_alert_types': ['brute_force', 'suspicious_ip'],
            },
            {
                'technique_id': 'T1557',
                'name': 'Adversary-in-the-Middle',
                'description': (
                    'Adversaries may attempt to position themselves between two or '
                    'more networked devices to support follow-on behaviors such as '
                    'network sniffing or transmitted data manipulation.'
                ),
                'detection_hint': (
                    'Monitor for ARP spoofing, DNS poisoning, and LLMNR/NBT-NS '
                    'poisoning activity on the network.'
                ),
                'mitigation': (
                    'Enforce mutual authentication. Use encrypted protocols. '
                    'Disable LLMNR and NBT-NS where possible.'
                ),
                'maps_to_alert_types': ['protocol_anomaly'],
            },
        ],
    },
    {
        'tactic_id': 'TA0007',
        'name': 'Discovery',
        'description': (
            'The adversary is trying to figure out your environment. '
            'Discovery consists of techniques an adversary may use to gain '
            'knowledge about the system and internal network.'
        ),
        'techniques': [
            {
                'technique_id': 'T1046',
                'name': 'Network Service Discovery',
                'description': (
                    'Adversaries may attempt to get a listing of services running '
                    'on remote hosts and local network infrastructure devices, including '
                    'those that may be vulnerable to remote software exploitation.'
                ),
                'detection_hint': (
                    'Monitor network traffic for port scanning activity. Detect rapid '
                    'connection attempts to multiple ports on the same host.'
                ),
                'mitigation': (
                    'Segment the network. Use IDS/IPS to detect scanning. Restrict '
                    'unnecessary services on hosts.'
                ),
                'maps_to_alert_types': ['port_scan'],
            },
            {
                'technique_id': 'T1018',
                'name': 'Remote System Discovery',
                'description': (
                    'Adversaries may attempt to get a listing of other systems by '
                    'IP address, hostname, or other logical identifier on a network '
                    'that may be used for lateral movement.'
                ),
                'detection_hint': (
                    'Monitor for network enumeration commands like net view, ping sweeps, '
                    'or ARP scans.'
                ),
                'mitigation': (
                    'Restrict network discovery tools. Use network segmentation. '
                    'Monitor for unusual ICMP or ARP traffic patterns.'
                ),
                'maps_to_alert_types': ['port_scan'],
            },
            {
                'technique_id': 'T1082',
                'name': 'System Information Discovery',
                'description': (
                    'An adversary may attempt to get detailed information about the '
                    'operating system and hardware, including version, patches, '
                    'hotfixes, service packs, and architecture.'
                ),
                'detection_hint': (
                    'Monitor for execution of system information commands such as '
                    'systeminfo, hostname, and uname.'
                ),
                'mitigation': (
                    'Restrict unnecessary system commands for standard users. '
                    'Monitor for enumeration activity.'
                ),
                'maps_to_alert_types': ['protocol_anomaly'],
            },
        ],
    },
    {
        'tactic_id': 'TA0008',
        'name': 'Lateral Movement',
        'description': (
            'The adversary is trying to move through your environment. '
            'Lateral Movement consists of techniques that adversaries use to '
            'enter and control remote systems on a network.'
        ),
        'techniques': [
            {
                'technique_id': 'T1021',
                'name': 'Remote Services',
                'description': (
                    'Adversaries may use valid accounts to log into a service '
                    'specifically designed to accept remote connections, such as '
                    'SSH, RDP, VNC, or telnet.'
                ),
                'detection_hint': (
                    'Monitor for remote login events from unusual sources or at '
                    'unusual times. Track lateral authentication events.'
                ),
                'mitigation': (
                    'Enforce MFA for remote services. Restrict remote access to '
                    'authorized subnets. Monitor remote service logs.'
                ),
                'maps_to_alert_types': ['suspicious_ip', 'brute_force'],
            },
            {
                'technique_id': 'T1570',
                'name': 'Lateral Tool Transfer',
                'description': (
                    'Adversaries may transfer tools or other files between systems '
                    'in a compromised environment. Once brought into the victim '
                    'environment, files may be copied from one system to another.'
                ),
                'detection_hint': (
                    'Monitor for unusual SMB file transfers, especially of executables '
                    'or scripts between internal hosts.'
                ),
                'mitigation': (
                    'Restrict SMB traffic between workstations. Use application '
                    'whitelisting. Monitor for lateral file transfers.'
                ),
                'maps_to_alert_types': ['protocol_anomaly'],
            },
        ],
    },
    {
        'tactic_id': 'TA0009',
        'name': 'Collection',
        'description': (
            'The adversary is trying to gather data of interest to their goal. '
            'Collection consists of techniques adversaries may use to gather '
            'information relevant to their objectives.'
        ),
        'techniques': [
            {
                'technique_id': 'T1005',
                'name': 'Data from Local System',
                'description': (
                    'Adversaries may search local system sources, such as file systems '
                    'and configuration files, to find files of interest and sensitive '
                    'data prior to exfiltration.'
                ),
                'detection_hint': (
                    'Monitor for unusual file access patterns, especially to sensitive '
                    'directories or files containing credentials.'
                ),
                'mitigation': (
                    'Encrypt sensitive data at rest. Use data loss prevention tools. '
                    'Restrict file access permissions.'
                ),
                'maps_to_alert_types': ['protocol_anomaly'],
            },
            {
                'technique_id': 'T1039',
                'name': 'Data from Network Shared Drive',
                'description': (
                    'Adversaries may search network shares on computers they have '
                    'compromised to find files of interest. Sensitive data can be '
                    'collected from remote systems via shared network drives.'
                ),
                'detection_hint': (
                    'Monitor for excessive file access on network shares, especially '
                    'from hosts that do not typically access those shares.'
                ),
                'mitigation': (
                    'Restrict access to network shares. Audit share permissions. '
                    'Monitor for bulk file access activity.'
                ),
                'maps_to_alert_types': ['protocol_anomaly'],
            },
        ],
    },
    {
        'tactic_id': 'TA0011',
        'name': 'Command and Control',
        'description': (
            'The adversary is trying to communicate with compromised systems. '
            'Command and Control consists of techniques that adversaries may use '
            'to communicate with systems under their control.'
        ),
        'techniques': [
            {
                'technique_id': 'T1071',
                'name': 'Application Layer Protocol',
                'description': (
                    'Adversaries may communicate using OSI application layer protocols '
                    'to avoid detection by blending in with existing traffic. Commands '
                    'to the remote system may be embedded within HTTP, HTTPS, DNS, or '
                    'other protocols.'
                ),
                'detection_hint': (
                    'Analyze network traffic for unusual patterns in common protocols. '
                    'Look for DNS tunneling, HTTP beaconing, or unusual user-agent strings.'
                ),
                'mitigation': (
                    'Use deep packet inspection. Monitor for DNS tunneling. '
                    'Restrict outbound traffic to known good destinations.'
                ),
                'maps_to_alert_types': ['protocol_anomaly', 'suspicious_ip'],
            },
            {
                'technique_id': 'T1573',
                'name': 'Encrypted Channel',
                'description': (
                    'Adversaries may employ an encryption algorithm to conceal '
                    'command and control traffic. Encrypted channels may use '
                    'standard protocols like TLS/SSL or custom encryption.'
                ),
                'detection_hint': (
                    'Monitor for encrypted connections to unusual destinations. '
                    'Detect anomalous TLS certificate usage or JA3/JA3S fingerprints.'
                ),
                'mitigation': (
                    'Use TLS inspection for outbound traffic. Monitor for unusual '
                    'encrypted sessions. Maintain a baseline of normal TLS behavior.'
                ),
                'maps_to_alert_types': ['protocol_anomaly'],
            },
            {
                'technique_id': 'T1105',
                'name': 'Ingress Tool Transfer',
                'description': (
                    'Adversaries may transfer tools or other files from an external '
                    'system into a compromised environment. Tools or files may be '
                    'copied from an external adversary-controlled system.'
                ),
                'detection_hint': (
                    'Monitor for file downloads from unusual external sources. '
                    'Detect suspicious network connections followed by file writes.'
                ),
                'mitigation': (
                    'Restrict downloads from untrusted sources. Use application '
                    'whitelisting. Monitor outbound connections.'
                ),
                'maps_to_alert_types': ['suspicious_ip'],
            },
        ],
    },
    {
        'tactic_id': 'TA0010',
        'name': 'Exfiltration',
        'description': (
            'The adversary is trying to steal data. '
            'Exfiltration consists of techniques that adversaries may use to '
            'steal data from your network.'
        ),
        'techniques': [
            {
                'technique_id': 'T1041',
                'name': 'Exfiltration Over C2 Channel',
                'description': (
                    'Adversaries may steal data by exfiltrating it over an existing '
                    'command and control channel. Stolen data is encoded into the '
                    'normal communications channel used with the already-established '
                    'C2 infrastructure.'
                ),
                'detection_hint': (
                    'Monitor for unusual data volumes in outbound C2 traffic. '
                    'Detect data encoding or compression in network flows.'
                ),
                'mitigation': (
                    'Monitor outbound data volumes. Use DLP solutions. Restrict '
                    'outbound connections to authorized destinations.'
                ),
                'maps_to_alert_types': ['protocol_anomaly', 'suspicious_ip'],
            },
            {
                'technique_id': 'T1048',
                'name': 'Exfiltration Over Alternative Protocol',
                'description': (
                    'Adversaries may steal data by exfiltrating it over a different '
                    'protocol than that of the existing command and control channel. '
                    'The data may also be sent to an alternative network location.'
                ),
                'detection_hint': (
                    'Monitor for unusual protocol usage on the network, such as '
                    'DNS or ICMP carrying unexpected data volumes.'
                ),
                'mitigation': (
                    'Restrict unnecessary outbound protocols. Monitor for DNS '
                    'tunneling and ICMP exfiltration. Use network segmentation.'
                ),
                'maps_to_alert_types': ['protocol_anomaly'],
            },
        ],
    },
    {
        'tactic_id': 'TA0040',
        'name': 'Impact',
        'description': (
            'The adversary is trying to manipulate, interrupt, or destroy '
            'your systems and data. Impact consists of techniques that '
            'adversaries use to disrupt availability or compromise integrity.'
        ),
        'techniques': [
            {
                'technique_id': 'T1498',
                'name': 'Network Denial of Service',
                'description': (
                    'Adversaries may perform Network Denial of Service (DoS) attacks '
                    'to degrade or block the availability of targeted resources. '
                    'This may include volumetric floods or protocol-based attacks.'
                ),
                'detection_hint': (
                    'Monitor for sudden spikes in inbound traffic volume. Detect '
                    'SYN floods, UDP floods, and amplification attacks.'
                ),
                'mitigation': (
                    'Deploy DDoS mitigation services. Use rate limiting. '
                    'Implement network traffic filtering and scrubbing.'
                ),
                'maps_to_alert_types': ['dos'],
            },
            {
                'technique_id': 'T1499',
                'name': 'Endpoint Denial of Service',
                'description': (
                    'Adversaries may perform Endpoint Denial of Service attacks to '
                    'degrade or block the availability of services to users. These '
                    'attacks target specific services or applications.'
                ),
                'detection_hint': (
                    'Monitor for abnormal resource consumption on endpoints. Detect '
                    'application-layer attacks targeting specific services.'
                ),
                'mitigation': (
                    'Use auto-scaling infrastructure. Implement application-level '
                    'rate limiting. Deploy WAF rules for application DoS.'
                ),
                'maps_to_alert_types': ['dos'],
            },
            {
                'technique_id': 'T1486',
                'name': 'Data Encrypted for Impact',
                'description': (
                    'Adversaries may encrypt data on target systems or on large '
                    'numbers of systems in a network to interrupt availability '
                    'to system and network resources. This is commonly associated '
                    'with ransomware.'
                ),
                'detection_hint': (
                    'Monitor for mass file encryption activity, unusual file extension '
                    'changes, and rapid file modification patterns.'
                ),
                'mitigation': (
                    'Maintain offline backups. Use endpoint detection tools with '
                    'ransomware protection. Restrict write permissions.'
                ),
                'maps_to_alert_types': ['protocol_anomaly'],
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed the database with MITRE ATT&CK tactics and techniques.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing MITRE data before seeding.',
        )

    def handle(self, *args, **options):
        if options['clear']:
            MitreTechnique.objects.all().delete()
            MitreTactic.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared existing MITRE data.'))

        tactics_created = 0
        techniques_created = 0

        for tactic_data in MITRE_DATA:
            tactic, created = MitreTactic.objects.update_or_create(
                tactic_id=tactic_data['tactic_id'],
                defaults={
                    'name': tactic_data['name'],
                    'description': tactic_data['description'],
                },
            )
            if created:
                tactics_created += 1

            for tech_data in tactic_data['techniques']:
                _, tech_created = MitreTechnique.objects.update_or_create(
                    technique_id=tech_data['technique_id'],
                    defaults={
                        'name': tech_data['name'],
                        'tactic': tactic,
                        'description': tech_data['description'],
                        'detection_hint': tech_data.get('detection_hint', ''),
                        'mitigation': tech_data.get('mitigation', ''),
                        'maps_to_alert_types': tech_data.get('maps_to_alert_types', []),
                    },
                )
                if tech_created:
                    techniques_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded MITRE ATT&CK data: '
                f'{tactics_created} tactics created, '
                f'{techniques_created} techniques created. '
                f'Total: {MitreTactic.objects.count()} tactics, '
                f'{MitreTechnique.objects.count()} techniques.'
            )
        )
