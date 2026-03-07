from rest_framework import serializers
from .models import ThreatIntelligence


class ThreatIntelligenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThreatIntelligence
        fields = '__all__'


class ThreatCorrelationSerializer(serializers.Serializer):
    ip_address = serializers.CharField()
    is_known_threat = serializers.BooleanField()
    threat_entries = ThreatIntelligenceSerializer(many=True)
    alert_count = serializers.IntegerField()
    recommendation = serializers.CharField()
