"""
Serializers for alerts app — US-07 through US-13.
"""
from rest_framework import serializers
from .models import Alert, BlockedIP


class AlertListSerializer(serializers.ModelSerializer):
    """Compact alert serializer for list views — US-07, US-09, US-10."""

    class Meta:
        model = Alert
        fields = [
            'id', 'src_ip', 'dst_ip', 'src_port', 'dst_port',
            'protocol', 'alert_type', 'severity', 'confidence_score',
            'country', 'city', 'is_blocked', 'timestamp',
            'mitre_tactic', 'mitre_technique_id',
        ]


class AlertDetailSerializer(serializers.ModelSerializer):
    """Full alert serializer for detail view — US-08."""
    blocked_by_email = serializers.CharField(source='blocked_by.email', read_only=True, default=None)

    class Meta:
        model = Alert
        fields = [
            'id', 'environment', 'src_ip', 'dst_ip', 'src_port', 'dst_port',
            'protocol', 'alert_type', 'severity', 'confidence_score',
            'raw_payload', 'latitude', 'longitude', 'country', 'city',
            'is_blocked', 'blocked_at', 'blocked_by', 'blocked_by_email',
            'timestamp', 'ml_model_used', 'mitre_tactic', 'mitre_technique_id',
        ]


class GeoIPAlertSerializer(serializers.ModelSerializer):
    """Serializer for GeoIP map data — US-11."""

    class Meta:
        model = Alert
        fields = [
            'id', 'src_ip', 'alert_type', 'severity', 'confidence_score',
            'latitude', 'longitude', 'country', 'city', 'timestamp',
        ]


class BlockedIPSerializer(serializers.ModelSerializer):
    """Serializer for blocked IPs — US-13."""
    blocked_by_email = serializers.CharField(source='blocked_by.email', read_only=True)

    class Meta:
        model = BlockedIP
        fields = [
            'id', 'ip_address', 'environment', 'blocked_by',
            'blocked_by_email', 'reason', 'blocked_at',
            'unblocked_at', 'is_active',
        ]
        read_only_fields = ['id', 'blocked_at', 'blocked_by']


class BlockIPActionSerializer(serializers.Serializer):
    """Serializer for block/unblock IP action."""
    reason = serializers.CharField(required=False, default='Blocked via IDS alert action')
