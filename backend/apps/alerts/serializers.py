"""
Serializers for alerts app — US-07 through US-13.
"""
from rest_framework import serializers
from .models import Alert, BlockedIP, WhitelistedIP, TrafficFilterRule, LogUpload


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


class WhitelistedIPSerializer(serializers.ModelSerializer):
    """Serializer for whitelisted IPs."""
    added_by_email = serializers.CharField(source='added_by.email', read_only=True)

    class Meta:
        model = WhitelistedIP
        fields = [
            'id', 'ip_address', 'environment', 'added_by',
            'added_by_email', 'reason', 'created_at', 'is_active',
        ]
        read_only_fields = ['id', 'created_at', 'added_by', 'environment']


class TrafficFilterRuleSerializer(serializers.ModelSerializer):
    """Serializer for traffic filter rules."""
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)

    class Meta:
        model = TrafficFilterRule
        fields = [
            'id', 'name', 'filter_type', 'value', 'action',
            'is_active', 'created_by', 'created_by_email', 'created_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at']


class LogUploadSerializer(serializers.ModelSerializer):
    """Serializer for log upload records."""
    uploaded_by_email = serializers.CharField(source='uploaded_by.email', read_only=True)

    class Meta:
        model = LogUpload
        fields = [
            'id', 'file_name', 'file_format', 'records_total',
            'records_imported', 'records_failed', 'status',
            'error_message', 'uploaded_by', 'uploaded_by_email', 'uploaded_at',
        ]
        read_only_fields = ['id', 'uploaded_by', 'uploaded_at']
