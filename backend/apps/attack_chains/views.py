"""
Views for attack_chains app — Attack Kill Chain Timeline & Dynamic Risk Score.
"""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta

from .models import AttackChain, EnvironmentRiskScore
from .serializers import (
    AttackChainListSerializer,
    AttackChainDetailSerializer,
    EnvironmentRiskScoreSerializer,
)
from apps.alerts.models import Alert, BlockedIP
from apps.environments.models import EnvironmentMembership


def _get_user_environment(user):
    """Helper to get user's environment."""
    membership = EnvironmentMembership.objects.filter(
        user=user
    ).select_related('environment').first()
    return membership.environment if membership else None


class AttackChainListView(generics.ListAPIView):
    """
    List attack chains for the user's environment.
    Returns existing AttackChain objects ordered by most recent activity.
    """
    serializer_class = AttackChainListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        env = _get_user_environment(self.request.user)
        if not env:
            return AttackChain.objects.none()

        qs = AttackChain.objects.filter(environment=env)

        # Optional filters
        chain_status = self.request.query_params.get('status')
        if chain_status:
            qs = qs.filter(status=chain_status)

        chain_type = self.request.query_params.get('chain_type')
        if chain_type:
            qs = qs.filter(chain_type=chain_type)

        src_ip = self.request.query_params.get('src_ip')
        if src_ip:
            qs = qs.filter(src_ip=src_ip)

        return qs.prefetch_related('alerts', 'mitre_techniques')


class AttackChainDetailView(generics.RetrieveAPIView):
    """
    Detail view for a single attack chain with all linked alerts.
    """
    serializer_class = AttackChainDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        env = _get_user_environment(self.request.user)
        if not env:
            return AttackChain.objects.none()
        return AttackChain.objects.filter(
            environment=env
        ).prefetch_related('alerts', 'mitre_techniques')


class DynamicRiskScoreView(APIView):
    """
    Calculate real-time risk score based on:
    - Alert severity distribution (last 24h)
    - Active threat count
    - Blocked IP ratio
    - System health metrics
    Returns score 0-100 with contributing factors breakdown.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        env = _get_user_environment(request.user)
        if not env:
            return Response(
                {'error': 'No environment found.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_1h = now - timedelta(hours=1)

        alerts_24h = Alert.objects.filter(
            environment=env, timestamp__gte=last_24h
        )

        # ------------------------------------------------------------------
        # Factor 1: Severity distribution (0-40 points)
        # ------------------------------------------------------------------
        severity_counts = {
            'critical': alerts_24h.filter(severity='critical').count(),
            'high': alerts_24h.filter(severity='high').count(),
            'medium': alerts_24h.filter(severity='medium').count(),
            'low': alerts_24h.filter(severity='low').count(),
        }
        total_24h = sum(severity_counts.values())

        severity_score = min(40, (
            severity_counts['critical'] * 8 +
            severity_counts['high'] * 4 +
            severity_counts['medium'] * 1.5 +
            severity_counts['low'] * 0.5
        ))

        # ------------------------------------------------------------------
        # Factor 2: Active threat count (0-25 points)
        # ------------------------------------------------------------------
        unique_threat_ips = alerts_24h.values('src_ip').distinct().count()
        active_chains = AttackChain.objects.filter(
            environment=env, status='active'
        ).count()
        threat_score = min(25, unique_threat_ips * 2 + active_chains * 5)

        # ------------------------------------------------------------------
        # Factor 3: Blocked IP ratio (0-15 points, lower ratio = higher risk)
        # ------------------------------------------------------------------
        blocked_count = BlockedIP.objects.filter(
            environment=env, is_active=True
        ).count()
        if unique_threat_ips > 0:
            blocked_ratio = blocked_count / max(unique_threat_ips, 1)
            # If many threats are unblocked, risk is higher
            block_score = max(0, min(15, 15 - int(blocked_ratio * 15)))
        else:
            block_score = 0

        # ------------------------------------------------------------------
        # Factor 4: Recent surge / velocity (0-20 points)
        # ------------------------------------------------------------------
        alerts_1h = alerts_24h.filter(timestamp__gte=last_1h).count()
        avg_hourly = total_24h / 24 if total_24h > 0 else 0
        if avg_hourly > 0:
            surge_ratio = alerts_1h / avg_hourly
            surge_score = min(20, int(surge_ratio * 5))
        else:
            surge_score = min(20, alerts_1h * 3)

        # ------------------------------------------------------------------
        # Total risk score
        # ------------------------------------------------------------------
        risk_score = min(100, int(
            severity_score + threat_score + block_score + surge_score
        ))

        # Persist snapshot
        breakdown = {
            'severity_score': round(severity_score, 1),
            'threat_score': threat_score,
            'block_score': block_score,
            'surge_score': surge_score,
            'severity_counts': severity_counts,
            'total_alerts_24h': total_24h,
            'unique_threat_ips': unique_threat_ips,
            'active_chains': active_chains,
            'blocked_ips': blocked_count,
            'alerts_last_hour': alerts_1h,
        }

        snapshot = EnvironmentRiskScore.objects.create(
            environment=env,
            score=risk_score,
            breakdown=breakdown,
        )

        return Response({
            'score': risk_score,
            'factors': {
                'severity_distribution': {
                    'score': round(severity_score, 1),
                    'max': 40,
                    'details': severity_counts,
                },
                'active_threats': {
                    'score': threat_score,
                    'max': 25,
                    'unique_ips': unique_threat_ips,
                    'active_chains': active_chains,
                },
                'blocked_ip_coverage': {
                    'score': block_score,
                    'max': 15,
                    'blocked': blocked_count,
                    'total_threats': unique_threat_ips,
                },
                'alert_velocity': {
                    'score': surge_score,
                    'max': 20,
                    'alerts_last_hour': alerts_1h,
                    'avg_hourly': round(avg_hourly, 1),
                },
            },
            'total_alerts_24h': total_24h,
            'calculated_at': snapshot.calculated_at.isoformat(),
        })
