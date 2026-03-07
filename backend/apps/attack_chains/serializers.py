"""
Serializers for attack_chains app — Attack Kill Chain Timeline & Risk Score.
"""
from rest_framework import serializers
from .models import AttackChain, EnvironmentRiskScore
from apps.alerts.serializers import AlertListSerializer


class AttackChainListSerializer(serializers.ModelSerializer):
    """Compact serializer for attack chain list views."""
    alert_count = serializers.SerializerMethodField()
    mitre_technique_ids = serializers.SerializerMethodField()

    class Meta:
        model = AttackChain
        fields = [
            'id', 'src_ip', 'chain_type', 'started_at', 'last_seen_at',
            'risk_score', 'status', 'alert_count', 'mitre_technique_ids',
        ]

    def get_alert_count(self, obj):
        return obj.alerts.count()

    def get_mitre_technique_ids(self, obj):
        return list(
            obj.mitre_techniques.values_list('technique_id', flat=True)
        )


class AttackChainDetailSerializer(serializers.ModelSerializer):
    """Full serializer for attack chain detail view with nested alerts."""
    alerts = AlertListSerializer(many=True, read_only=True)
    mitre_techniques = serializers.SerializerMethodField()
    alert_count = serializers.SerializerMethodField()

    class Meta:
        model = AttackChain
        fields = [
            'id', 'src_ip', 'chain_type', 'started_at', 'last_seen_at',
            'risk_score', 'status', 'alert_count', 'alerts',
            'mitre_techniques',
        ]

    def get_alert_count(self, obj):
        return obj.alerts.count()

    def get_mitre_techniques(self, obj):
        return list(
            obj.mitre_techniques.values('technique_id', 'name', 'tactic__name')
        )


class EnvironmentRiskScoreSerializer(serializers.ModelSerializer):
    """Serializer for environment risk score snapshots."""

    class Meta:
        model = EnvironmentRiskScore
        fields = [
            'id', 'score', 'calculated_at', 'breakdown',
        ]
