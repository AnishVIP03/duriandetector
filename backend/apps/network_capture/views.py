"""
Views for network_capture app — US-21, packet capture management.
"""
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from .models import CaptureSession
from .serializers import CaptureSessionSerializer, StartCaptureSerializer
from apps.environments.models import EnvironmentMembership
from apps.accounts.permissions import SubscriptionRequired


class StartCaptureView(APIView):
    """Start a new packet capture session."""
    permission_classes = [permissions.IsAuthenticated, SubscriptionRequired]
    required_tier = 'premium'

    def post(self, request):
        serializer = StartCaptureSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get user's environment
        membership = EnvironmentMembership.objects.filter(
            user=request.user
        ).select_related('environment').first()

        if not membership:
            return Response(
                {'error': 'You must belong to an environment to start capture.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        env = membership.environment

        # Check for existing running session
        running = CaptureSession.objects.filter(
            environment=env, status='running'
        ).first()
        if running:
            return Response(
                {'error': 'A capture session is already running.',
                 'session': CaptureSessionSerializer(running).data},
                status=status.HTTP_409_CONFLICT,
            )

        # Create capture session
        session = CaptureSession.objects.create(
            environment=env,
            interface=serializer.validated_data.get('interface', env.network_interface),
            status='running',
            started_by=request.user,
        )

        # Launch Celery task
        try:
            from .tasks import capture_packets_task
            capture_packets_task.delay(
                session_id=session.id,
                environment_id=env.id,
                interface=session.interface,
                packet_count=serializer.validated_data.get('packet_count', 0),
                duration=serializer.validated_data.get('duration', 300),
            )
        except Exception as e:
            # If Celery is not running, mark session as error
            session.status = 'error'
            session.save(update_fields=['status'])
            return Response(
                {'error': f'Failed to start capture task: {str(e)}. Is Celery running?'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                'message': 'Capture session started.',
                'session': CaptureSessionSerializer(session).data,
            },
            status=status.HTTP_201_CREATED,
        )


class StopCaptureView(APIView):
    """Stop a running capture session."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        membership = EnvironmentMembership.objects.filter(
            user=request.user
        ).select_related('environment').first()

        if not membership:
            return Response(
                {'error': 'No environment found.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session = CaptureSession.objects.filter(
            environment=membership.environment, status='running'
        ).first()

        if not session:
            return Response(
                {'error': 'No running capture session found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        session.status = 'stopped'
        session.stopped_at = timezone.now()
        session.save(update_fields=['status', 'stopped_at'])

        return Response({
            'message': 'Capture session stopped.',
            'session': CaptureSessionSerializer(session).data,
        })


class CaptureStatusView(APIView):
    """Get the current capture session status — US-21."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        membership = EnvironmentMembership.objects.filter(
            user=request.user
        ).select_related('environment').first()

        if not membership:
            return Response(
                {'error': 'No environment found.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get latest sessions
        sessions = CaptureSession.objects.filter(
            environment=membership.environment
        ).order_by('-started_at')[:10]

        # Current running session
        current = sessions.filter(status='running').first() if sessions else None

        return Response({
            'current_session': CaptureSessionSerializer(current).data if current else None,
            'is_capturing': current is not None,
            'recent_sessions': CaptureSessionSerializer(sessions, many=True).data,
        })
