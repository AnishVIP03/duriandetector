"""
Views for alerts app — US-07 through US-13.
Full CRUD, filtering, blocking, and GeoIP aggregation.
"""
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from django.db.models import Count, Q

from .models import Alert, BlockedIP, WhitelistedIP, TrafficFilterRule, LogUpload
from .serializers import (
    AlertListSerializer,
    AlertDetailSerializer,
    GeoIPAlertSerializer,
    BlockedIPSerializer,
    BlockIPActionSerializer,
    WhitelistedIPSerializer,
    TrafficFilterRuleSerializer,
    LogUploadSerializer,
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


# ── Feature 1: Block Control List ──

class BlockedIPListView(generics.ListAPIView):
    """List all blocked IPs for the user's environment."""
    serializer_class = BlockedIPSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        env = _get_user_environment(self.request.user)
        if not env:
            return BlockedIP.objects.none()
        qs = BlockedIP.objects.filter(environment=env)
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(ip_address__icontains=search)
        return qs


class UnblockIPByIdView(APIView):
    """Unblock a blocked IP by its BlockedIP ID."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        env = _get_user_environment(request.user)
        if not env:
            return Response({'error': 'No environment found.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            blocked = BlockedIP.objects.get(id=pk, environment=env)
        except BlockedIP.DoesNotExist:
            return Response({'error': 'Blocked IP not found.'}, status=status.HTTP_404_NOT_FOUND)
        blocked.is_active = False
        blocked.unblocked_at = timezone.now()
        blocked.save(update_fields=['is_active', 'unblocked_at'])
        Alert.objects.filter(
            environment=env, src_ip=blocked.ip_address
        ).update(is_blocked=False, blocked_at=None, blocked_by=None)
        return Response({'message': f'IP {blocked.ip_address} has been unblocked.'})


# ── Feature 3: IP Whitelist ──

class WhitelistedIPListCreateView(generics.ListCreateAPIView):
    """List and add whitelisted IPs."""
    serializer_class = WhitelistedIPSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        env = _get_user_environment(self.request.user)
        if not env:
            return WhitelistedIP.objects.none()
        return WhitelistedIP.objects.filter(environment=env, is_active=True)

    def perform_create(self, serializer):
        env = _get_user_environment(self.request.user)
        serializer.save(added_by=self.request.user, environment=env)


class WhitelistedIPDeleteView(generics.DestroyAPIView):
    """Remove an IP from the whitelist."""
    serializer_class = WhitelistedIPSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        env = _get_user_environment(self.request.user)
        if not env:
            return WhitelistedIP.objects.none()
        return WhitelistedIP.objects.filter(environment=env)


# ── Feature 4: Alert Analytics ──

class AlertAnalyticsView(APIView):
    """Analytics endpoint for custom visualizations."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.db.models.functions import TruncHour, TruncDay, TruncWeek
        from django.db.models import Avg

        env = _get_user_environment(request.user)
        if not env:
            return Response({'error': 'No environment found.'}, status=status.HTTP_400_BAD_REQUEST)

        qs = Alert.objects.filter(environment=env)

        date_from = request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(timestamp__gte=date_from)
        date_to = request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(timestamp__lte=date_to)

        group_by = request.query_params.get('group_by', 'day')
        trunc_fn = {'hour': TruncHour, 'day': TruncDay, 'week': TruncWeek}.get(group_by, TruncDay)

        breakdown_by = request.query_params.get('breakdown_by')

        if breakdown_by and breakdown_by in ('severity', 'alert_type', 'protocol', 'country'):
            data = qs.annotate(
                period=trunc_fn('timestamp')
            ).values('period', breakdown_by).annotate(
                count=Count('id'),
                avg_confidence=Avg('confidence_score'),
            ).order_by('period')
        else:
            data = qs.annotate(
                period=trunc_fn('timestamp')
            ).values('period').annotate(
                count=Count('id'),
                avg_confidence=Avg('confidence_score'),
            ).order_by('period')

        results = []
        for row in data:
            item = {
                'period': row['period'].isoformat() if row['period'] else None,
                'count': row['count'],
                'avg_confidence': round(row['avg_confidence'] or 0, 3),
            }
            if breakdown_by:
                item[breakdown_by] = row.get(breakdown_by, '')
            results.append(item)

        return Response({'data': results, 'group_by': group_by, 'breakdown_by': breakdown_by})


# ── Feature 5: Traffic Filter Rules ──

class TrafficFilterRuleListCreateView(generics.ListCreateAPIView):
    """List and create traffic filter rules."""
    serializer_class = TrafficFilterRuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        env = _get_user_environment(self.request.user)
        if not env:
            return TrafficFilterRule.objects.none()
        return TrafficFilterRule.objects.filter(environment=env)

    def perform_create(self, serializer):
        env = _get_user_environment(self.request.user)
        serializer.save(created_by=self.request.user, environment=env)


class TrafficFilterRuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a traffic filter rule."""
    serializer_class = TrafficFilterRuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        env = _get_user_environment(self.request.user)
        if not env:
            return TrafficFilterRule.objects.none()
        return TrafficFilterRule.objects.filter(environment=env)


class TrafficFilterRuleToggleView(APIView):
    """Toggle a traffic filter rule active/inactive."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        env = _get_user_environment(request.user)
        if not env:
            return Response({'error': 'No environment found.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            rule = TrafficFilterRule.objects.get(id=pk, environment=env)
        except TrafficFilterRule.DoesNotExist:
            return Response({'error': 'Rule not found.'}, status=status.HTTP_404_NOT_FOUND)
        rule.is_active = not rule.is_active
        rule.save(update_fields=['is_active'])
        return Response(TrafficFilterRuleSerializer(rule).data)


# ── Feature 6: Log Ingestion ──

class LogUploadView(APIView):
    """Upload CSV or JSON log files to create alerts."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        import csv
        import json
        import io

        env = _get_user_environment(request.user)
        if not env:
            return Response({'error': 'No environment found.'}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

        file_name = file.name
        if file_name.endswith('.csv'):
            file_format = 'csv'
        elif file_name.endswith('.json'):
            file_format = 'json'
        else:
            return Response({'error': 'Unsupported file format. Use CSV or JSON.'}, status=status.HTTP_400_BAD_REQUEST)

        upload = LogUpload.objects.create(
            environment=env,
            uploaded_by=request.user,
            file_name=file_name,
            file_format=file_format,
            status='processing',
        )

        try:
            content = file.read().decode('utf-8')
            records = []

            if file_format == 'csv':
                reader = csv.DictReader(io.StringIO(content))
                for row in reader:
                    records.append(row)
            else:
                parsed = json.loads(content)
                if isinstance(parsed, list):
                    records = parsed
                elif isinstance(parsed, dict) and 'records' in parsed:
                    records = parsed['records']
                else:
                    records = [parsed]

            upload.records_total = len(records)
            imported = 0
            failed = 0
            errors = []

            for i, record in enumerate(records):
                try:
                    Alert.objects.create(
                        environment=env,
                        src_ip=record.get('src_ip', '0.0.0.0'),
                        dst_ip=record.get('dst_ip', '0.0.0.0'),
                        src_port=int(record.get('src_port', 0)) or None,
                        dst_port=int(record.get('dst_port', 0)) or None,
                        protocol=record.get('protocol', 'TCP'),
                        alert_type=record.get('alert_type', 'other'),
                        severity=record.get('severity', 'low'),
                        confidence_score=float(record.get('confidence_score', 0.5)),
                        raw_payload=record.get('raw_payload', ''),
                        country=record.get('country', ''),
                        city=record.get('city', ''),
                        latitude=float(record['latitude']) if record.get('latitude') else None,
                        longitude=float(record['longitude']) if record.get('longitude') else None,
                        mitre_tactic=record.get('mitre_tactic', ''),
                        mitre_technique_id=record.get('mitre_technique_id', ''),
                    )
                    imported += 1
                except Exception as e:
                    failed += 1
                    if len(errors) < 5:
                        errors.append(f"Row {i + 1}: {str(e)}")

            upload.records_imported = imported
            upload.records_failed = failed
            upload.status = 'completed'
            upload.error_message = '\n'.join(errors)
            upload.save()

            return Response({
                'message': f'Imported {imported} of {len(records)} records.',
                'upload': LogUploadSerializer(upload).data,
            })

        except Exception as e:
            upload.status = 'failed'
            upload.error_message = str(e)
            upload.save()
            return Response({'error': f'Failed to parse file: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


class LogUploadHistoryView(generics.ListAPIView):
    """List past log uploads."""
    serializer_class = LogUploadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        env = _get_user_environment(self.request.user)
        if not env:
            return LogUpload.objects.none()
        return LogUpload.objects.filter(environment=env)
