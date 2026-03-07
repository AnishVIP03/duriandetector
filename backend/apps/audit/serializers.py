"""
Serializers for audit app — US-34, US-35.
"""
from rest_framework import serializers
from .models import AuditLog, SystemHealth


class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_email', 'environment', 'action',
            'target_type', 'target_id', 'ip_address', 'user_agent',
            'metadata', 'timestamp',
        ]


class SystemHealthSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemHealth
        fields = '__all__'
