"""
Views for incidents app — US-16, US-17.
Incident management: create, list, detail, update, and notes.
"""
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from apps.environments.models import EnvironmentMembership
from apps.alerts.models import Alert
from .models import Incident, IncidentNote
from .serializers import (
    IncidentListSerializer,
    IncidentDetailSerializer,
    CreateIncidentSerializer,
    UpdateIncidentSerializer,
    IncidentNoteSerializer,
)

User = get_user_model()


def _get_user_environment(user):
    """Helper to get the user's current environment via membership."""
    membership = EnvironmentMembership.objects.filter(
        user=user
    ).select_related('environment').first()
    return membership.environment if membership else None


class IncidentListCreateView(generics.ListCreateAPIView):
    """
    List / create incidents — US-16.
    GET:  List incidents for the user's environment with filtering and search.
    POST: Create a new incident, optionally linking existing alert IDs.
    """
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['severity', 'status']
    search_fields = ['title']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateIncidentSerializer
        return IncidentListSerializer

    def get_queryset(self):
        env = _get_user_environment(self.request.user)
        if not env:
            return Incident.objects.none()
        return Incident.objects.filter(environment=env)

    def create(self, request, *args, **kwargs):
        serializer = CreateIncidentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        env = _get_user_environment(request.user)
        if not env:
            return Response(
                {'error': 'No environment found.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        incident = Incident.objects.create(
            environment=env,
            title=serializer.validated_data['title'],
            description=serializer.validated_data.get('description', ''),
            severity=serializer.validated_data['severity'],
            created_by=request.user,
        )

        # Link alerts if IDs were provided
        alert_ids = serializer.validated_data.get('alert_ids', [])
        if alert_ids:
            alerts = Alert.objects.filter(id__in=alert_ids, environment=env)
            incident.alerts.set(alerts)

        return Response(
            IncidentDetailSerializer(incident).data,
            status=status.HTTP_201_CREATED,
        )


class IncidentDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve / update an incident — US-17.
    GET:         Full incident detail with notes and linked alerts.
    PUT / PATCH: Update incident fields. Auto-sets resolved_at on status change.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = IncidentDetailSerializer

    def get_queryset(self):
        env = _get_user_environment(self.request.user)
        if not env:
            return Incident.objects.none()
        return Incident.objects.filter(environment=env)

    def update(self, request, *args, **kwargs):
        incident = self.get_object()
        serializer = UpdateIncidentSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Apply optional field updates
        if 'title' in data:
            incident.title = data['title']
        if 'description' in data:
            incident.description = data['description']
        if 'severity' in data:
            incident.severity = data['severity']

        # Handle status change — auto-set resolved_at
        if 'status' in data:
            old_status = incident.status
            incident.status = data['status']
            if data['status'] == Incident.Status.RESOLVED and old_status != Incident.Status.RESOLVED:
                incident.resolved_at = timezone.now()
            elif data['status'] != Incident.Status.RESOLVED:
                incident.resolved_at = None

        # Handle assigned_to (nullable user ID)
        if 'assigned_to' in data:
            if data['assigned_to'] is None:
                incident.assigned_to = None
            else:
                try:
                    incident.assigned_to = User.objects.get(id=data['assigned_to'])
                except User.DoesNotExist:
                    return Response(
                        {'error': 'Assigned user not found.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        incident.save()
        return Response(IncidentDetailSerializer(incident).data)


class IncidentNotesListView(generics.ListAPIView):
    """List notes for a specific incident."""
    serializer_class = IncidentNoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        env = _get_user_environment(self.request.user)
        if not env:
            return IncidentNote.objects.none()
        return IncidentNote.objects.filter(
            incident__environment=env,
            incident_id=self.kwargs['incident_id'],
        )


class IncidentNoteCreateView(generics.CreateAPIView):
    """Add a note to an incident."""
    serializer_class = IncidentNoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        env = _get_user_environment(request.user)
        if not env:
            return Response(
                {'error': 'No environment found.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify incident belongs to user's environment
        try:
            incident = Incident.objects.get(
                id=self.kwargs['incident_id'],
                environment=env,
            )
        except Incident.DoesNotExist:
            return Response(
                {'error': 'Incident not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        note = IncidentNote.objects.create(
            incident=incident,
            author=request.user,
            content=request.data.get('content', ''),
        )

        return Response(
            IncidentNoteSerializer(note).data,
            status=status.HTTP_201_CREATED,
        )
