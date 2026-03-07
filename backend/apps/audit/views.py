"""
Views for audit app — US-34 (audit logs), US-35 (system health).
"""
import psutil
from datetime import timedelta

from django.utils import timezone
from django.db import connection
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AuditLog, SystemHealth
from .serializers import AuditLogSerializer, SystemHealthSerializer
from apps.accounts.permissions import IsAdmin


class AuditLogListView(generics.ListAPIView):
    """List audit logs — US-34. Admin only."""
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ['action', 'user']
    search_fields = ['action', 'target_type', 'ip_address']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    def get_queryset(self):
        return AuditLog.objects.select_related('user').all()


class SystemHealthView(APIView):
    """Live system health check — US-35."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # System metrics via psutil
        cpu = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Database check
        db_ok = True
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
        except Exception:
            db_ok = False

        # Redis check
        redis_ok = True
        try:
            import redis
            r = redis.Redis(host='127.0.0.1', port=6379, socket_timeout=2)
            r.ping()
        except Exception:
            redis_ok = False

        # Celery check
        celery_ok = False
        try:
            from config.celery import app as celery_app
            insp = celery_app.control.inspect(timeout=2.0)
            workers = insp.active_queues()
            celery_ok = workers is not None and len(workers) > 0
        except Exception:
            pass

        # Capture sessions
        from apps.network_capture.models import CaptureSession
        active_captures = CaptureSession.objects.filter(status='running').count()

        # Alerts in last hour
        from apps.alerts.models import Alert
        one_hour_ago = timezone.now() - timedelta(hours=1)
        alerts_last_hour = Alert.objects.filter(timestamp__gte=one_hour_ago).count()

        # Save health snapshot
        health = SystemHealth.objects.create(
            celery_status='online' if celery_ok else 'offline',
            redis_status='online' if redis_ok else 'offline',
            postgres_status='online' if db_ok else 'offline',
            capture_sessions_active=active_captures,
            alerts_last_hour=alerts_last_hour,
            disk_usage_percent=disk.percent,
            cpu_percent=cpu,
            memory_percent=memory.percent,
        )

        # Historical data (last 20 checks)
        history = SystemHealth.objects.all()[:20]

        return Response({
            'current': SystemHealthSerializer(health).data,
            'services': {
                'database': {'status': 'online' if db_ok else 'offline', 'type': 'SQLite/PostgreSQL'},
                'redis': {'status': 'online' if redis_ok else 'offline', 'type': 'Redis'},
                'celery': {'status': 'online' if celery_ok else 'offline', 'type': 'Celery Worker'},
                'capture': {'status': 'active' if active_captures > 0 else 'idle', 'sessions': active_captures},
            },
            'system': {
                'cpu_percent': round(cpu, 1),
                'memory_percent': round(memory.percent, 1),
                'memory_total_gb': round(memory.total / (1024 ** 3), 1),
                'memory_used_gb': round(memory.used / (1024 ** 3), 1),
                'disk_percent': round(disk.percent, 1),
                'disk_total_gb': round(disk.total / (1024 ** 3), 1),
                'disk_used_gb': round(disk.used / (1024 ** 3), 1),
            },
            'alerts_last_hour': alerts_last_hour,
            'history': SystemHealthSerializer(history, many=True).data,
        })


class CaptureStatusView(APIView):
    """Capture system status — US-21."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from apps.network_capture.models import CaptureSession
        from apps.environments.models import EnvironmentMembership

        membership = EnvironmentMembership.objects.filter(
            user=request.user
        ).select_related('environment').first()

        if not membership:
            return Response({'error': 'No environment found.'}, status=400)

        env = membership.environment
        sessions = CaptureSession.objects.filter(environment=env).order_by('-started_at')[:10]
        running = sessions.filter(status='running').first()

        from apps.network_capture.serializers import CaptureSessionSerializer

        return Response({
            'is_capturing': running is not None,
            'current_session': CaptureSessionSerializer(running).data if running else None,
            'recent_sessions': CaptureSessionSerializer(sessions, many=True).data,
            'interface': env.network_interface,
        })
