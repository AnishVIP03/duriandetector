"""
Views for demo app — Demo/Simulation Mode.
Creates realistic fake alerts, attack chains, and GeoIP data for demonstration.
"""
import random
from datetime import timedelta

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from apps.alerts.models import Alert
from apps.attack_chains.models import AttackChain
from apps.environments.models import Environment, EnvironmentMembership

# Demo data is tagged with this prefix in raw_payload for easy identification.
DEMO_TAG = '[DEMO_SIMULATED]'


def _get_or_create_user_environment(user):
    """Helper to get user's environment, or auto-create a demo one."""
    membership = EnvironmentMembership.objects.filter(
        user=user
    ).select_related('environment').first()
    if membership:
        return membership.environment

    # Auto-create environment for demo purposes
    env = Environment.objects.create(
        name='Demo Environment',
        owner=user,
        description='Auto-created for demo simulation',
        network_interface='eth0',
    )
    EnvironmentMembership.objects.create(
        user=user,
        environment=env,
        role='team_leader',
    )
    return env


# ---------------------------------------------------------------------------
# Realistic simulation data
# ---------------------------------------------------------------------------

ATTACK_PROFILES = [
    {
        'alert_type': 'port_scan',
        'protocols': ['TCP', 'UDP'],
        'severities': ['low', 'medium'],
        'dst_ports': [22, 80, 443, 445, 3389, 8080, 8443],
        'mitre_tactic': 'Reconnaissance',
        'mitre_technique_id': 'T1046',
        'description': 'Network Service Scanning',
    },
    {
        'alert_type': 'brute_force',
        'protocols': ['TCP', 'SSH'],
        'severities': ['medium', 'high'],
        'dst_ports': [22, 3389, 21],
        'mitre_tactic': 'Credential Access',
        'mitre_technique_id': 'T1110',
        'description': 'Brute Force',
    },
    {
        'alert_type': 'dos',
        'protocols': ['TCP', 'UDP', 'ICMP'],
        'severities': ['high', 'critical'],
        'dst_ports': [80, 443, 53],
        'mitre_tactic': 'Impact',
        'mitre_technique_id': 'T1499',
        'description': 'Endpoint Denial of Service',
    },
    {
        'alert_type': 'sql_injection',
        'protocols': ['HTTP', 'TCP'],
        'severities': ['high', 'critical'],
        'dst_ports': [80, 443, 8080],
        'mitre_tactic': 'Initial Access',
        'mitre_technique_id': 'T1190',
        'description': 'Exploit Public-Facing Application',
    },
    {
        'alert_type': 'xss',
        'protocols': ['HTTP'],
        'severities': ['medium', 'high'],
        'dst_ports': [80, 443],
        'mitre_tactic': 'Initial Access',
        'mitre_technique_id': 'T1189',
        'description': 'Drive-by Compromise',
    },
    {
        'alert_type': 'protocol_anomaly',
        'protocols': ['DNS', 'TCP', 'UDP'],
        'severities': ['medium', 'high'],
        'dst_ports': [53, 443, 8443],
        'mitre_tactic': 'Command and Control',
        'mitre_technique_id': 'T1071',
        'description': 'Application Layer Protocol',
    },
    {
        'alert_type': 'suspicious_ip',
        'protocols': ['TCP', 'HTTP'],
        'severities': ['low', 'medium', 'high'],
        'dst_ports': [80, 443, 8080],
        'mitre_tactic': 'Command and Control',
        'mitre_technique_id': 'T1102',
        'description': 'Web Service',
    },
]

# Realistic source IPs from various countries
SOURCE_IPS = [
    {'ip': '185.220.101.42', 'country': 'Germany', 'city': 'Frankfurt', 'lat': 50.1109, 'lng': 8.6821},
    {'ip': '103.253.41.98', 'country': 'China', 'city': 'Beijing', 'lat': 39.9042, 'lng': 116.4074},
    {'ip': '45.155.205.233', 'country': 'Russia', 'city': 'Moscow', 'lat': 55.7558, 'lng': 37.6173},
    {'ip': '91.240.118.172', 'country': 'Netherlands', 'city': 'Amsterdam', 'lat': 52.3676, 'lng': 4.9041},
    {'ip': '198.51.100.23', 'country': 'United States', 'city': 'New York', 'lat': 40.7128, 'lng': -74.0060},
    {'ip': '203.0.113.45', 'country': 'Japan', 'city': 'Tokyo', 'lat': 35.6762, 'lng': 139.6503},
    {'ip': '177.54.150.100', 'country': 'Brazil', 'city': 'Sao Paulo', 'lat': -23.5505, 'lng': -46.6333},
    {'ip': '41.203.67.82', 'country': 'Nigeria', 'city': 'Lagos', 'lat': 6.5244, 'lng': 3.3792},
    {'ip': '78.128.113.18', 'country': 'Romania', 'city': 'Bucharest', 'lat': 44.4268, 'lng': 26.1025},
    {'ip': '59.24.3.174', 'country': 'South Korea', 'city': 'Seoul', 'lat': 37.5665, 'lng': 126.9780},
    {'ip': '176.10.99.200', 'country': 'Switzerland', 'city': 'Zurich', 'lat': 47.3769, 'lng': 8.5417},
    {'ip': '14.161.12.88', 'country': 'Vietnam', 'city': 'Ho Chi Minh City', 'lat': 10.8231, 'lng': 106.6297},
]

DST_IPS = [
    '10.0.1.10', '10.0.1.20', '10.0.1.30', '10.0.2.10',
    '192.168.1.100', '192.168.1.200', '172.16.0.5', '172.16.0.10',
]

ML_MODELS = [
    'RandomForest_v2.3', 'XGBoost_v1.8', 'LSTM_AnomalyDetector_v3.0',
    'IsolationForest_v2.1', 'CNN_PacketClassifier_v1.5',
]


class DemoStartView(APIView):
    """
    Start a demo simulation that creates fake alerts with realistic data.
    Creates 30-50 alerts spread across the last 24 hours with various
    attack types, severities, source IPs, and GeoIP data.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        env = _get_or_create_user_environment(request.user)

        # Check if demo data already exists
        existing = Alert.objects.filter(
            environment=env,
            raw_payload__startswith=DEMO_TAG,
        ).count()
        if existing > 0:
            return Response(
                {
                    'error': 'Demo data already exists. Clear it first before starting a new demo.',
                    'existing_alerts': existing,
                },
                status=status.HTTP_409_CONFLICT,
            )

        now = timezone.now()
        num_alerts = random.randint(30, 50)
        created_alerts = []
        severity_summary = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        type_summary = {}

        for i in range(num_alerts):
            profile = random.choice(ATTACK_PROFILES)
            source = random.choice(SOURCE_IPS)
            severity = random.choice(profile['severities'])
            protocol = random.choice(profile['protocols'])
            dst_ip = random.choice(DST_IPS)
            dst_port = random.choice(profile['dst_ports'])
            src_port = random.randint(1024, 65535)

            # Spread timestamps across the last 24 hours with some clustering
            hours_ago = random.uniform(0, 24)
            timestamp = now - timedelta(hours=hours_ago)

            alert = Alert(
                environment=env,
                src_ip=source['ip'],
                dst_ip=dst_ip,
                src_port=src_port,
                dst_port=dst_port,
                protocol=protocol,
                alert_type=profile['alert_type'],
                severity=severity,
                confidence_score=round(random.uniform(0.65, 0.99), 2),
                raw_payload=f"{DEMO_TAG} Simulated {profile['description']} attack from {source['ip']}",
                latitude=source['lat'] + random.uniform(-0.5, 0.5),
                longitude=source['lng'] + random.uniform(-0.5, 0.5),
                country=source['country'],
                city=source['city'],
                is_blocked=False,
                ml_model_used=random.choice(ML_MODELS),
                mitre_tactic=profile['mitre_tactic'],
                mitre_technique_id=profile['mitre_technique_id'],
            )
            created_alerts.append(alert)
            severity_summary[severity] += 1
            type_summary[profile['alert_type']] = type_summary.get(
                profile['alert_type'], 0
            ) + 1

        # Bulk create all alerts
        Alert.objects.bulk_create(created_alerts)

        # Override auto_now_add timestamps by doing raw updates
        all_demo = Alert.objects.filter(
            environment=env,
            raw_payload__startswith=DEMO_TAG,
        ).order_by('id')

        for idx, alert in enumerate(all_demo):
            hours_ago = random.uniform(0, 24)
            ts = now - timedelta(hours=hours_ago)
            Alert.objects.filter(pk=alert.pk).update(timestamp=ts)

        # Demo mode: fan out alerts to other tier databases
        self._fanout_demo_alerts(created_alerts, now)

        # Create a couple of attack chains from the demo data
        demo_alerts = list(Alert.objects.filter(
            environment=env,
            raw_payload__startswith=DEMO_TAG,
        ).order_by('timestamp'))

        if len(demo_alerts) >= 5:
            # Chain 1: Recon to Exploit (port scan + sql injection from same IP)
            chain_ip = demo_alerts[0].src_ip
            chain_alerts_1 = [a for a in demo_alerts if a.src_ip == chain_ip][:5]
            if len(chain_alerts_1) >= 2:
                chain1 = AttackChain.objects.create(
                    environment=env,
                    src_ip=chain_ip,
                    chain_type='recon_to_exploit',
                    started_at=chain_alerts_1[0].timestamp,
                    last_seen_at=chain_alerts_1[-1].timestamp,
                    risk_score=random.randint(60, 90),
                    status='active',
                )
                chain1.alerts.set(chain_alerts_1)

            # Chain 2: DoS Campaign from another IP
            other_ips = list(set(
                a.src_ip for a in demo_alerts if a.src_ip != chain_ip
            ))
            if other_ips:
                chain_ip_2 = other_ips[0]
                chain_alerts_2 = [
                    a for a in demo_alerts if a.src_ip == chain_ip_2
                ][:4]
                if len(chain_alerts_2) >= 2:
                    chain2 = AttackChain.objects.create(
                        environment=env,
                        src_ip=chain_ip_2,
                        chain_type='dos_campaign',
                        started_at=chain_alerts_2[0].timestamp,
                        last_seen_at=chain_alerts_2[-1].timestamp,
                        risk_score=random.randint(70, 95),
                        status='active',
                    )
                    chain2.alerts.set(chain_alerts_2)

            # Chain 3: Multi-stage from yet another IP
            if len(other_ips) > 1:
                chain_ip_3 = other_ips[1]
                chain_alerts_3 = [
                    a for a in demo_alerts if a.src_ip == chain_ip_3
                ][:6]
                if len(chain_alerts_3) >= 2:
                    chain3 = AttackChain.objects.create(
                        environment=env,
                        src_ip=chain_ip_3,
                        chain_type='multi_stage',
                        started_at=chain_alerts_3[0].timestamp,
                        last_seen_at=chain_alerts_3[-1].timestamp,
                        risk_score=random.randint(50, 85),
                        status='active',
                    )
                    chain3.alerts.set(chain_alerts_3)

        return Response({
            'message': 'Demo simulation started successfully.',
            'total_alerts': num_alerts,
            'severity_summary': severity_summary,
            'type_summary': type_summary,
        }, status=status.HTTP_201_CREATED)

    def _fanout_demo_alerts(self, alert_templates, now):
        """Replicate demo alerts to other tier databases so all users see them."""
        from django.conf import settings as django_settings
        if not getattr(django_settings, 'DEMO_MODE', False):
            return

        from config.db_router import get_current_db

        current_db = get_current_db()
        other_dbs = [db for db in ['free_db', 'premium_db', 'exclusive_db'] if db != current_db]

        for db_alias in other_dbs:
            try:
                env = Environment.objects.using(db_alias).first()
                if not env:
                    continue

                db_alerts = []
                for template in alert_templates:
                    db_alerts.append(Alert(
                        environment=env,
                        src_ip=template.src_ip,
                        dst_ip=template.dst_ip,
                        src_port=template.src_port,
                        dst_port=template.dst_port,
                        protocol=template.protocol,
                        alert_type=template.alert_type,
                        severity=template.severity,
                        confidence_score=template.confidence_score,
                        raw_payload=template.raw_payload,
                        latitude=template.latitude,
                        longitude=template.longitude,
                        country=template.country,
                        city=template.city,
                        is_blocked=False,
                        ml_model_used=template.ml_model_used,
                        mitre_tactic=template.mitre_tactic,
                        mitre_technique_id=template.mitre_technique_id,
                    ))

                Alert.objects.using(db_alias).bulk_create(db_alerts)

                # Randomize timestamps
                fanout_demo = Alert.objects.using(db_alias).filter(
                    environment=env,
                    raw_payload__startswith=DEMO_TAG,
                ).order_by('id')
                for alert in fanout_demo:
                    hours_ago = random.uniform(0, 24)
                    ts = now - timedelta(hours=hours_ago)
                    Alert.objects.using(db_alias).filter(pk=alert.pk).update(timestamp=ts)

            except Exception:
                pass  # Don't fail if a tier DB is unavailable


class DemoStatusView(APIView):
    """Check if demo data exists for the user's environment."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        env = _get_or_create_user_environment(request.user)

        demo_count = Alert.objects.filter(
            environment=env,
            raw_payload__startswith=DEMO_TAG,
        ).count()

        demo_chains = AttackChain.objects.filter(
            environment=env,
            alerts__raw_payload__startswith=DEMO_TAG,
        ).distinct().count()

        return Response({
            'has_demo_data': demo_count > 0,
            'alert_count': demo_count,
            'chain_count': demo_chains,
        })


class DemoClearView(APIView):
    """Clear all demo-generated alerts and attack chains."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        env = _get_or_create_user_environment(request.user)

        # Delete attack chains that reference demo alerts
        demo_alert_ids = Alert.objects.filter(
            environment=env,
            raw_payload__startswith=DEMO_TAG,
        ).values_list('id', flat=True)

        chains_deleted = 0
        demo_chains = AttackChain.objects.filter(
            environment=env,
            alerts__id__in=demo_alert_ids,
        ).distinct()
        chains_deleted = demo_chains.count()
        demo_chains.delete()

        # Delete the demo alerts
        alerts_deleted, _ = Alert.objects.filter(
            environment=env,
            raw_payload__startswith=DEMO_TAG,
        ).delete()

        return Response({
            'message': 'Demo data cleared successfully.',
            'alerts_deleted': alerts_deleted,
            'chains_deleted': chains_deleted,
        })
