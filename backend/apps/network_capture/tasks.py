"""
Celery tasks for network packet capture using Scapy.
Captures packets, extracts features, runs ML inference, and creates alerts.
"""
import logging
import time
from celery import shared_task
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


def _fanout_alert(alert_data):
    """
    In demo mode, replicate an alert to ALL tier databases so every
    user (free/premium/exclusive) sees the same attack.
    """
    from django.conf import settings
    if not getattr(settings, 'DEMO_MODE', False):
        return

    from apps.alerts.models import Alert
    from apps.environments.models import Environment

    for db_alias in ['free_db', 'premium_db', 'exclusive_db']:
        try:
            env = Environment.objects.using(db_alias).first()
            if env:
                Alert.objects.using(db_alias).create(
                    environment=env,
                    **alert_data,
                )
        except Exception as e:
            logger.warning(f"Alert fanout to {db_alias} failed: {e}")


def _get_severity(confidence, alert_type):
    """Determine alert severity based on confidence and type."""
    if alert_type in ('dos', 'brute_force') and confidence > 0.8:
        return 'critical'
    if confidence > 0.85:
        return 'high'
    if confidence > 0.65:
        return 'medium'
    return 'low'


def _get_mitre_mapping(alert_type):
    """Map alert type to MITRE ATT&CK tactic/technique."""
    mappings = {
        'port_scan': ('Reconnaissance', 'T1046'),
        'dos': ('Impact', 'T1498'),
        'brute_force': ('Credential Access', 'T1110'),
        'protocol_anomaly': ('Discovery', 'T1046'),
        'suspicious_ip': ('Command and Control', 'T1071'),
        'sql_injection': ('Initial Access', 'T1190'),
        'xss': ('Initial Access', 'T1189'),
    }
    return mappings.get(alert_type, (None, None))


def _lookup_geoip(ip_address):
    """Look up GeoIP data for an IP address using the shared geoip module."""
    from apps.alerts.geoip import lookup_ip
    return lookup_ip(ip_address)


@shared_task(bind=True)
def capture_packets_task(self, session_id, environment_id, interface='eth0',
                         packet_count=0, duration=300):
    """
    Main packet capture task.
    Captures packets using Scapy, extracts features, runs ML inference,
    creates alerts, and broadcasts via WebSocket.

    Args:
        session_id: CaptureSession ID
        environment_id: Environment ID
        interface: Network interface to capture on
        packet_count: Max packets (0 = unlimited until duration)
        duration: Max duration in seconds (default 5 min)
    """
    from apps.network_capture.models import CaptureSession, NetworkFeature
    from apps.alerts.models import Alert
    from apps.ml_engine.engine import IDSEngine

    logger.info(f"Starting capture on {interface} for env {environment_id}")

    try:
        session = CaptureSession.objects.get(id=session_id)
        session.status = 'running'
        session.save(update_fields=['status'])
    except CaptureSession.DoesNotExist:
        logger.error(f"CaptureSession {session_id} not found")
        return {'error': 'Session not found'}

    # Initialize ML engine and feature extractor
    engine = IDSEngine(environment_id=environment_id)
    from apps.network_capture.feature_extractor import PacketFeatureExtractor
    extractor = PacketFeatureExtractor()

    channel_layer = get_channel_layer()
    packets_captured = 0
    alerts_generated = 0
    start_time = time.time()

    try:
        from scapy.all import sniff

        def process_packet(packet):
            nonlocal packets_captured, alerts_generated

            # Check duration limit
            if time.time() - start_time > duration:
                return True  # Stop sniffing

            # Check if session was stopped externally
            session.refresh_from_db()
            if session.status == 'stopped':
                return True

            features = extractor.extract(packet)
            if features is None:
                return

            packets_captured += 1

            # Save network feature
            try:
                NetworkFeature.objects.create(
                    session=session,
                    src_ip=features['src_ip'],
                    dst_ip=features['dst_ip'],
                    src_port=features['src_port'],
                    dst_port=features['dst_port'],
                    protocol=features['protocol'],
                    packet_length=features['packet_length'],
                    ttl=features['ttl'],
                    flags=features['flags'],
                    inter_arrival_time=features['inter_arrival_time'],
                    features_json={'vector': features['feature_vector']},
                )
            except Exception as e:
                logger.warning(f"Failed to save feature: {e}")

            # ML inference
            label, confidence, probabilities = engine.predict(features['feature_vector'])

            # Broadcast packet to WebSocket (packet inspector)
            try:
                async_to_sync(channel_layer.group_send)('packets', {
                    'type': 'packet_message',
                    'data': {
                        'src_ip': features['src_ip'],
                        'dst_ip': features['dst_ip'],
                        'src_port': features['src_port'],
                        'dst_port': features['dst_port'],
                        'protocol': features['protocol'],
                        'length': features['packet_length'],
                        'prediction': label,
                        'confidence': round(confidence, 4),
                        'timestamp': features['timestamp'],
                    }
                })
            except Exception:
                pass

            # Create alert if not normal traffic
            if label != 'normal' and confidence > 0.5:
                # Get sensitivity threshold from ML config
                threshold = 0.5  # default
                try:
                    from apps.ml_engine.models import MLModelConfig
                    config = MLModelConfig.objects.filter(
                        environment_id=environment_id
                    ).first()
                    if config:
                        sensitivity_map = {'low': 0.3, 'medium': 0.5, 'high': 0.7}
                        threshold = sensitivity_map.get(config.sensitivity, 0.5)
                except Exception:
                    pass

                if confidence >= threshold:
                    severity = _get_severity(confidence, label)
                    mitre_tactic, mitre_technique_id = _get_mitre_mapping(label)

                    # GeoIP lookup
                    geo = _lookup_geoip(features['src_ip'])

                    alert_data = {
                        'src_ip': features['src_ip'],
                        'dst_ip': features['dst_ip'],
                        'src_port': features['src_port'],
                        'dst_port': features['dst_port'],
                        'protocol': features['protocol'],
                        'alert_type': label,
                        'severity': severity,
                        'confidence_score': round(confidence, 4),
                        'raw_payload': features.get('raw_payload', ''),
                        'latitude': geo.get('latitude'),
                        'longitude': geo.get('longitude'),
                        'country': geo.get('country', ''),
                        'city': geo.get('city', ''),
                        'ml_model_used': type(engine.model).__name__,
                        'mitre_tactic': mitre_tactic,
                        'mitre_technique_id': mitre_technique_id,
                    }

                    try:
                        alert = Alert.objects.create(
                            environment_id=environment_id,
                            **alert_data,
                        )
                        alerts_generated += 1

                        # Demo mode: fan out alert to all tier databases
                        _fanout_alert(alert_data)

                        # Broadcast alert to WebSocket
                        try:
                            async_to_sync(channel_layer.group_send)('alerts', {
                                'type': 'alert_message',
                                'data': {
                                    'id': alert.id,
                                    'src_ip': alert.src_ip,
                                    'dst_ip': alert.dst_ip,
                                    'protocol': alert.protocol,
                                    'alert_type': alert.alert_type,
                                    'severity': alert.severity,
                                    'confidence': float(alert.confidence_score),
                                    'country': alert.country,
                                    'city': alert.city,
                                    'mitre_technique_id': alert.mitre_technique_id,
                                    'timestamp': str(alert.timestamp),
                                }
                            })
                        except Exception:
                            pass

                    except Exception as e:
                        logger.error(f"Failed to create alert: {e}")

            # Update session counters periodically
            if packets_captured % 50 == 0:
                session.packets_captured = packets_captured
                session.alerts_generated = alerts_generated
                session.save(update_fields=['packets_captured', 'alerts_generated'])

        # Start sniffing
        sniff(
            iface=interface,
            prn=process_packet,
            count=packet_count if packet_count > 0 else 0,
            timeout=duration,
            store=False,
        )

    except PermissionError:
        logger.error("Permission denied for packet capture. Run with sudo or set capabilities.")
        session.status = 'error'
        session.save(update_fields=['status'])
        return {'error': 'Permission denied. Packet capture requires elevated privileges.'}
    except Exception as e:
        logger.error(f"Capture error: {e}")
        session.status = 'error'
        session.save(update_fields=['status'])
        return {'error': str(e)}

    # Finalize session
    session.status = 'stopped'
    session.stopped_at = timezone.now()
    session.packets_captured = packets_captured
    session.alerts_generated = alerts_generated
    session.save()

    logger.info(
        f"Capture complete: {packets_captured} packets, {alerts_generated} alerts"
    )

    return {
        'status': 'completed',
        'packets_captured': packets_captured,
        'alerts_generated': alerts_generated,
    }
