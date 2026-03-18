"""
Serializers for network_capture app.
"""
from rest_framework import serializers
from .models import CaptureSession, NetworkFeature


class CaptureSessionSerializer(serializers.ModelSerializer):
    started_by_email = serializers.CharField(source='started_by.email', read_only=True)
    duration = serializers.SerializerMethodField()

    class Meta:
        model = CaptureSession
        fields = [
            'id', 'environment', 'interface', 'started_at', 'stopped_at',
            'status', 'packets_captured', 'alerts_generated',
            'started_by', 'started_by_email', 'duration',
        ]
        read_only_fields = [
            'id', 'started_at', 'stopped_at', 'status',
            'packets_captured', 'alerts_generated', 'started_by',
        ]

    def get_duration(self, obj):
        if obj.stopped_at and obj.started_at:
            delta = obj.stopped_at - obj.started_at
            return int(delta.total_seconds())
        return None


class StartCaptureSerializer(serializers.Serializer):
    interface = serializers.CharField(required=False, allow_blank=True, default='')
    duration = serializers.IntegerField(default=300, min_value=10, max_value=3600, required=False)
    packet_count = serializers.IntegerField(default=0, min_value=0, required=False)


class NetworkFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkFeature
        fields = '__all__'
