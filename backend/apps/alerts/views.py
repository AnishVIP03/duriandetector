"""
Views for alerts app — US-07 through US-13.
Full CRUD, filtering, blocking, and GeoIP aggregation.
"""
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Count, Q

from .models import Alert, BlockedIP
from .serializers import (
    AlertListSerializer,
    AlertDetailSerializer,
    GeoIPAlertSerializer,
    BlockedIPSerializer,
    BlockIPActionSerializer,
)
from apps.environments.models import EnvironmentMembership


def _get_user_environment(user):
    """Helper to get user's environment."""
    membership = EnvironmentMembership.objects.filter(
        user=user
    ).select_related('environment').first()
    return membership.environment if membership else None


class AlertListView(generics.ListAPIView):
    """
    List alerts with filtering — US-07, US-09, US-10.
    Supports filters: severity, alert_type, protocol, is_blocked, src_ip, country.
    Supports search: src_ip, dst_ip, country, city.
    Supports ordering: timestamp, severity, confidence_score.
    """
    serializer_class = AlertListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['severity', 'alert_type', 'protocol', 'is_blocked']
    search_fields = ['src_ip', 'dst_ip', 'country', 'city']
    ordering_fields = ['timestamp', 'severity', 'confidence_score']
    ordering = ['-timestamp']

    def get_queryset(self):
        env = _get_user_environment(self.request.user)
        if not env:
            return Alert.objects.none()

        qs = Alert.objects.filter(environment=env)

        # Additional custom filters
        src_ip = self.request.query_params.get('src_ip')
        if src_ip:
            qs = qs.filter(src_ip=src_ip)

        country = self.request.query_params.get('country')
        if country:
            qs = qs.filter(country__icontains=country)

        date_from = self.request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(timestamp__gte=date_from)

        date_to = self.request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(timestamp__lte=date_to)

        return qs


class AlertDetailView(generics.RetrieveAPIView):
    """View a single alert detail — US-08."""
    serializer_class = AlertDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        env = _get_user_environment(self.request.user)
        if not env:
            return Alert.objects.none()
        return Alert.objects.filter(environment=env)


class GeoIPDataView(APIView):
    """
    Get GeoIP data for map visualization — US-11.
    Returns alerts with lat/lng grouped by country.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        env = _get_user_environment(request.user)
        if not env:
            return Response({'error': 'No environment found.'}, status=status.HTTP_400_BAD_REQUEST)

        # Alerts with geo data
        alerts = Alert.objects.filter(
            environment=env,
            latitude__isnull=False,
            longitude__isnull=False,
        ).order_by('-timestamp')[:500]

        # Country aggregation
        country_stats = Alert.objects.filter(
            environment=env,
            country__isnull=False,
        ).exclude(country='').values('country').annotate(
            count=Count('id'),
            critical=Count('id', filter=Q(severity='critical')),
            high=Count('id', filter=Q(severity='high')),
        ).order_by('-count')[:30]

        return Response({
            'alerts': GeoIPAlertSerializer(alerts, many=True).data,
            'country_stats': list(country_stats),
            'total_with_geo': alerts.count(),
        })


class BlockIPView(APIView):
    """Block an IP address from an alert — US-13."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, alert_id):
        env = _get_user_environment(request.user)
        if not env:
            return Response({'error': 'No environment found.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            alert = Alert.objects.get(id=alert_id, environment=env)
        except Alert.DoesNotExist:
            return Response({'error': 'Alert not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = BlockIPActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Block the IP
        blocked, created = BlockedIP.objects.get_or_create(
            ip_address=alert.src_ip,
            environment=env,
            defaults={
                'blocked_by': request.user,
                'reason': serializer.validated_data.get('reason', ''),
            }
        )

        if not created:
            blocked.is_active = True
            blocked.unblocked_at = None
            blocked.save(update_fields=['is_active', 'unblocked_at'])

        # Mark all alerts from this IP as blocked
        Alert.objects.filter(
            environment=env, src_ip=alert.src_ip
        ).update(
            is_blocked=True,
            blocked_at=timezone.now(),
            blocked_by=request.user,
        )

        return Response({
            'message': f'IP {alert.src_ip} has been blocked.',
            'blocked_ip': BlockedIPSerializer(blocked).data,
        })


class UnblockIPView(APIView):
    """Unblock an IP address — US-13."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, alert_id):
        env = _get_user_environment(request.user)
        if not env:
            return Response({'error': 'No environment found.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            alert = Alert.objects.get(id=alert_id, environment=env)
        except Alert.DoesNotExist:
            return Response({'error': 'Alert not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Unblock
        BlockedIP.objects.filter(
            ip_address=alert.src_ip, environment=env
        ).update(
            is_active=False,
            unblocked_at=timezone.now(),
        )

        # Unmark alerts
        Alert.objects.filter(
            environment=env, src_ip=alert.src_ip
        ).update(is_blocked=False, blocked_at=None, blocked_by=None)

        return Response({'message': f'IP {alert.src_ip} has been unblocked.'})


class DashboardStatsView(APIView):
    """Dashboard statistics for the current environment."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        env = _get_user_environment(request.user)
        if not env:
            return Response({'error': 'No environment found.'}, status=status.HTTP_400_BAD_REQUEST)

        from datetime import timedelta
        now = timezone.now()
        one_hour_ago = now - timedelta(hours=1)
        twenty_four_hours_ago = now - timedelta(hours=24)

        alerts = Alert.objects.filter(environment=env)
        recent_alerts = alerts.filter(timestamp__gte=twenty_four_hours_ago)

        # Severity breakdown
        severity_counts = {}
        for sev in ['low', 'medium', 'high', 'critical']:
            severity_counts[sev] = recent_alerts.filter(severity=sev).count()

        # Alert type breakdown
        type_counts = {}
        for atype in alerts.values_list('alert_type', flat=True).distinct():
            type_counts[atype] = recent_alerts.filter(alert_type=atype).count()

        # Hourly trend (last 24h)
        hourly_trend = []
        for i in range(24):
            hour_start = now - timedelta(hours=i + 1)
            hour_end = now - timedelta(hours=i)
            count = alerts.filter(timestamp__gte=hour_start, timestamp__lt=hour_end).count()
            hourly_trend.append({
                'hour': hour_start.strftime('%H:%M'),
                'count': count,
            })
        hourly_trend.reverse()

        # Top source IPs
        top_ips = alerts.filter(
            timestamp__gte=twenty_four_hours_ago
        ).values('src_ip').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        from apps.network_capture.models import CaptureSession
        capture_running = CaptureSession.objects.filter(
            environment=env, status='running'
        ).exists()

        return Response({
            'total_alerts': alerts.count(),
            'alerts_24h': recent_alerts.count(),
            'alerts_1h': alerts.filter(timestamp__gte=one_hour_ago).count(),
            'critical_alerts': recent_alerts.filter(severity='critical').count(),
            'blocked_ips': BlockedIP.objects.filter(environment=env, is_active=True).count(),
            'severity_breakdown': severity_counts,
            'type_breakdown': type_counts,
            'hourly_trend': hourly_trend,
            'top_source_ips': list(top_ips),
            'capture_running': capture_running,
        })
