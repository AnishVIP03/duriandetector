"""
Views for reports app — US-22 (generate/list reports), US-23 (export PDF).
"""
import logging
from datetime import timedelta

from django.db.models import Count, Q
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Report
from .serializers import (
    ReportListSerializer,
    ReportDetailSerializer,
    GenerateReportSerializer,
)
from apps.alerts.models import Alert, BlockedIP
from apps.environments.models import EnvironmentMembership
from apps.accounts.permissions import SubscriptionRequired

logger = logging.getLogger(__name__)


def _get_user_environment(user):
    """Helper to get user's environment."""
    membership = EnvironmentMembership.objects.filter(
        user=user
    ).select_related('environment').first()
    return membership.environment if membership else None


# ──────────────────────────────────────────────────────────
# US-22 — List reports for the environment
# ──────────────────────────────────────────────────────────

class ReportListView(generics.ListAPIView):
    """
    List all reports for the user's environment — US-22.
    Ordered by most recently created.
    """
    serializer_class = ReportListSerializer
    permission_classes = [permissions.IsAuthenticated, SubscriptionRequired]
    required_tier = 'premium'

    def get_queryset(self):
        env = _get_user_environment(self.request.user)
        if not env:
            return Report.objects.none()
        return Report.objects.filter(environment=env)


# ──────────────────────────────────────────────────────────
# US-22 — Generate a new report
# ──────────────────────────────────────────────────────────

class GenerateReportView(APIView):
    """
    Generate a new report by collecting stats from alerts — US-22.
    POST body: title, report_type, date_from, date_to.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        env = _get_user_environment(request.user)
        if not env:
            return Response(
                {'error': 'No environment found.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = GenerateReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        date_from = data['date_from']
        date_to = data['date_to']
        report_type = data['report_type']

        # ── Collect alert stats for the date range ──
        alerts = Alert.objects.filter(
            environment=env,
            timestamp__gte=date_from,
            timestamp__lte=date_to,
        )

        total_alerts = alerts.count()

        # Severity breakdown
        severity_breakdown = {}
        for sev in ['low', 'medium', 'high', 'critical']:
            severity_breakdown[sev] = alerts.filter(severity=sev).count()

        # Type breakdown
        type_breakdown = {}
        for row in alerts.values('alert_type').annotate(count=Count('id')).order_by('-count'):
            type_breakdown[row['alert_type']] = row['count']

        # Top 10 source IPs
        top_source_ips = list(
            alerts.values('src_ip')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

        # Blocked IPs count (active blocks in environment)
        blocked_ips_count = BlockedIP.objects.filter(
            environment=env, is_active=True,
        ).count()

        # Hourly trend across the date range
        hourly_trend = []
        total_hours = int((date_to - date_from).total_seconds() / 3600) or 1
        # Cap at 168 hours (7 days) to avoid huge lists
        step = max(1, total_hours // 168)
        current = date_from
        while current < date_to:
            next_hour = current + timedelta(hours=step)
            count = alerts.filter(
                timestamp__gte=current,
                timestamp__lt=next_hour,
            ).count()
            hourly_trend.append({
                'hour': current.strftime('%Y-%m-%d %H:%M'),
                'count': count,
            })
            current = next_hour

        # Build content dict
        content = {
            'total_alerts': total_alerts,
            'severity_breakdown': severity_breakdown,
            'type_breakdown': type_breakdown,
            'top_source_ips': top_source_ips,
            'blocked_ips_count': blocked_ips_count,
            'hourly_trend': hourly_trend,
        }

        # ── Extra data for incident reports ──
        if report_type == 'incident':
            from apps.incidents.models import Incident
            incidents = Incident.objects.filter(
                environment=env,
                created_at__gte=date_from,
                created_at__lte=date_to,
            )
            incident_status_breakdown = {}
            for s in ['open', 'in_progress', 'resolved', 'closed']:
                incident_status_breakdown[s] = incidents.filter(status=s).count()
            content['incident_status_breakdown'] = incident_status_breakdown
            content['total_incidents'] = sum(incident_status_breakdown.values())

        # ── Extra data for threat reports ──
        if report_type == 'threat':
            from apps.threats.models import ThreatIntelligence
            # Count alerts that match known threat IPs
            threat_ips = set(
                ThreatIntelligence.objects.filter(
                    is_active=True,
                ).values_list('ip_address', flat=True)
            )
            threat_matches = alerts.filter(src_ip__in=threat_ips).count()
            content['threat_intel_matches'] = threat_matches
            content['known_threat_ips_total'] = len(threat_ips)

        # ── Save the report ──
        report = Report.objects.create(
            environment=env,
            created_by=request.user,
            title=data['title'],
            report_type=report_type,
            date_from=date_from,
            date_to=date_to,
            content=content,
        )

        return Response(
            ReportDetailSerializer(report).data,
            status=status.HTTP_201_CREATED,
        )


# ──────────────────────────────────────────────────────────
# US-22 — View single report detail
# ──────────────────────────────────────────────────────────

class ReportDetailView(generics.RetrieveAPIView):
    """Retrieve a single report with full content — US-22."""
    serializer_class = ReportDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        env = _get_user_environment(self.request.user)
        if not env:
            return Report.objects.none()
        return Report.objects.filter(environment=env)


# ──────────────────────────────────────────────────────────
# US-23 — Export report as PDF
# ──────────────────────────────────────────────────────────

class ReportExportView(APIView):
    """
    Export a report as a PDF file — US-23.
    Uses WeasyPrint to render an HTML template into a downloadable PDF.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        env = _get_user_environment(request.user)
        if not env:
            return Response(
                {'error': 'No environment found.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            report = Report.objects.get(pk=pk, environment=env)
        except Report.DoesNotExist:
            return Response(
                {'error': 'Report not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if WeasyPrint is available
        try:
            from weasyprint import HTML
        except ImportError:
            return Response(
                {
                    'error': (
                        'WeasyPrint is not installed. '
                        'Install it with: pip install weasyprint'
                    ),
                },
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        # Build template context
        content = report.content or {}
        context = {
            'report': report,
            'title': report.title,
            'report_type': report.get_report_type_display(),
            'date_from': report.date_from,
            'date_to': report.date_to,
            'generated_at': timezone.now(),
            'environment_name': env.name,
            'total_alerts': content.get('total_alerts', 0),
            'severity_breakdown': content.get('severity_breakdown', {}),
            'type_breakdown': content.get('type_breakdown', {}),
            'top_source_ips': content.get('top_source_ips', []),
            'blocked_ips_count': content.get('blocked_ips_count', 0),
            'hourly_trend': content.get('hourly_trend', []),
            # Incident-specific
            'incident_status_breakdown': content.get('incident_status_breakdown', {}),
            'total_incidents': content.get('total_incidents', 0),
            # Threat-specific
            'threat_intel_matches': content.get('threat_intel_matches', 0),
            'known_threat_ips_total': content.get('known_threat_ips_total', 0),
        }

        # Render HTML template
        html_string = render_to_string(
            'reports/report_template.html', context,
        )

        # Generate PDF
        pdf_bytes = HTML(string=html_string).write_pdf()

        # Save PDF to model FileField
        from django.core.files.base import ContentFile
        filename = (
            f"report_{report.id}_{report.report_type}_"
            f"{report.date_from.strftime('%Y%m%d')}.pdf"
        )
        report.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)

        # Return PDF as download
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
