"""
Attack chain correlation engine.

Automatically groups related alerts into AttackChain objects based on:
- Same source IP within a configurable time window
- Multiple distinct attack types from the same source (multi-stage)
- Known attack progression patterns (e.g. recon -> exploit -> C2)

Called after each alert is created to check whether the new alert
should be added to an existing chain or trigger creation of a new one.
"""
import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count

logger = logging.getLogger(__name__)

# Minimum number of alerts from the same source IP within the time window
# required to form or extend an attack chain.
MIN_ALERTS_FOR_CHAIN = 3

# Time window to look back when correlating alerts from the same source.
CORRELATION_WINDOW_HOURS = 6

# Known attack progression patterns: if alerts from the same IP match
# these sequences (subset match), they are classified as specific chain types.
CHAIN_PATTERNS = {
    'recon_to_exploit': {
        'required': {'port_scan'},
        'plus_any': {'sql_injection', 'xss', 'brute_force', 'protocol_anomaly'},
    },
    'scan_to_brute': {
        'required': {'port_scan', 'brute_force'},
        'plus_any': set(),
    },
    'dos_campaign': {
        'required': {'dos'},
        'plus_any': set(),
        'min_count': 3,  # Need at least 3 DoS alerts to call it a campaign
    },
}

# Severity weights for risk score calculation
SEVERITY_WEIGHTS = {
    'critical': 25,
    'high': 15,
    'medium': 8,
    'low': 3,
}


def _classify_chain(alert_types, alert_count):
    """Determine chain type based on the set of alert types observed."""
    for chain_type, pattern in CHAIN_PATTERNS.items():
        required = pattern['required']
        plus_any = pattern.get('plus_any', set())
        min_count = pattern.get('min_count', 2)

        if required.issubset(alert_types):
            if not plus_any or plus_any.intersection(alert_types):
                if alert_count >= min_count:
                    return chain_type

    # If multiple distinct attack types but no specific pattern matched
    if len(alert_types) >= 2:
        return 'multi_stage'

    return 'other'


def _calculate_risk_score(alerts):
    """Calculate a risk score (0-100) for a chain based on its alerts."""
    if not alerts:
        return 0

    score = 0
    for alert in alerts:
        score += SEVERITY_WEIGHTS.get(alert.severity, 3)
        # Bonus for high-confidence detections
        if alert.confidence_score and alert.confidence_score > 0.85:
            score += 5

    # Factor in number of distinct attack types (diversity = higher risk)
    unique_types = len(set(a.alert_type for a in alerts))
    score += unique_types * 5

    return min(100, score)


def correlate_alert(alert):
    """
    Check whether a newly created alert should be correlated into an
    attack chain. Either extends an existing chain or creates a new one.

    Args:
        alert: The Alert instance that was just created.

    Returns:
        The AttackChain instance the alert was added to, or None.
    """
    from .models import AttackChain
    from apps.alerts.models import Alert

    try:
        env = alert.environment
        now = timezone.now()
        window_start = now - timedelta(hours=CORRELATION_WINDOW_HOURS)

        # 1. Check if there is an existing active chain for this source IP
        existing_chain = AttackChain.objects.filter(
            environment=env,
            src_ip=alert.src_ip,
            status='active',
            last_seen_at__gte=window_start,
        ).first()

        if existing_chain:
            # Add alert to existing chain and update metadata
            existing_chain.alerts.add(alert)
            existing_chain.last_seen_at = now

            # Recalculate risk score and chain type with all alerts
            chain_alerts = list(existing_chain.alerts.all())
            alert_types = set(a.alert_type for a in chain_alerts)
            existing_chain.chain_type = _classify_chain(
                alert_types, len(chain_alerts)
            )
            existing_chain.risk_score = _calculate_risk_score(chain_alerts)
            existing_chain.save(
                update_fields=['last_seen_at', 'chain_type', 'risk_score']
            )

            logger.info(
                f"Extended attack chain {existing_chain.id} with alert "
                f"{alert.id} (now {len(chain_alerts)} alerts)"
            )
            return existing_chain

        # 2. No existing chain -- check if we have enough recent alerts
        #    from this source IP to justify creating a new chain.
        recent_alerts = list(
            Alert.objects.filter(
                environment=env,
                src_ip=alert.src_ip,
                timestamp__gte=window_start,
            ).order_by('timestamp')
        )

        if len(recent_alerts) < MIN_ALERTS_FOR_CHAIN:
            return None

        # Enough alerts to form a chain
        alert_types = set(a.alert_type for a in recent_alerts)
        chain_type = _classify_chain(alert_types, len(recent_alerts))
        risk_score = _calculate_risk_score(recent_alerts)

        chain = AttackChain.objects.create(
            environment=env,
            src_ip=alert.src_ip,
            chain_type=chain_type,
            started_at=recent_alerts[0].timestamp,
            last_seen_at=now,
            risk_score=risk_score,
            status='active',
        )
        chain.alerts.set(recent_alerts)

        logger.info(
            f"Created new attack chain {chain.id}: {chain_type} from "
            f"{alert.src_ip} with {len(recent_alerts)} alerts "
            f"(risk={risk_score})"
        )
        return chain

    except Exception as e:
        logger.error(f"Attack chain correlation failed for alert {alert.id}: {e}")
        return None
