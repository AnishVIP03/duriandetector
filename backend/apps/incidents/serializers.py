"""
Serializers for incidents app — US-16, US-17.
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Incident, IncidentNote

User = get_user_model()


class IncidentNoteSerializer(serializers.ModelSerializer):
    """Serializer for incident notes / comments."""
    author = serializers.CharField(source='author.email', read_only=True)

    class Meta:
        model = IncidentNote
        fields = ['id', 'incident', 'author', 'content', 'created_at']
        read_only_fields = ['id', 'author', 'created_at']


class IncidentListSerializer(serializers.ModelSerializer):
    """Compact incident serializer for list views — US-16."""
    created_by = serializers.CharField(source='created_by.email', read_only=True)
    assigned_to = serializers.CharField(
        source='assigned_to.email', read_only=True, default=None,
    )
    alert_count = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = [
            'id', 'environment', 'title', 'severity', 'status',
            'created_by', 'assigned_to', 'alert_count',
            'created_at', 'updated_at',
        ]

    def get_alert_count(self, obj):
        return obj.alerts.count()


class IncidentDetailSerializer(serializers.ModelSerializer):
    """Full incident serializer for detail view — US-17."""
    created_by = serializers.CharField(source='created_by.email', read_only=True)
    assigned_to = serializers.CharField(
        source='assigned_to.email', read_only=True, default=None,
    )
    alerts = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    notes = IncidentNoteSerializer(many=True, read_only=True)
    alert_count = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = [
            'id', 'environment', 'title', 'description', 'severity', 'status',
            'created_by', 'assigned_to', 'alerts', 'alert_count', 'notes',
            'created_at', 'updated_at', 'resolved_at',
        ]

    def get_alert_count(self, obj):
        return obj.alerts.count()


class CreateIncidentSerializer(serializers.Serializer):
    """Serializer for creating a new incident — US-16."""
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, default='')
    severity = serializers.ChoiceField(choices=Incident.Severity.choices)
    alert_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=[],
    )


class UpdateIncidentSerializer(serializers.Serializer):
    """Serializer for updating an incident — US-17."""
    title = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False)
    severity = serializers.ChoiceField(
        choices=Incident.Severity.choices, required=False,
    )
    status = serializers.ChoiceField(
        choices=Incident.Status.choices, required=False,
    )
    assigned_to = serializers.IntegerField(required=False, allow_null=True)
