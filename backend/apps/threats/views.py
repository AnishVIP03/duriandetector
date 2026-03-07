from rest_framework import generics, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from .models import ThreatIntelligence
from .serializers import ThreatIntelligenceSerializer, ThreatCorrelationSerializer
from apps.alerts.models import Alert


class ThreatListView(generics.ListAPIView):
    """
    GET /api/threats/

    List all threat intelligence entries with filtering, searching,
    and ordering support.

    Filters: threat_type, source, is_active
    Search:  ip_address, domain, description
    Order:   confidence, last_seen  (prefix with '-' for descending)
    """

    queryset = ThreatIntelligence.objects.all()
    serializer_class = ThreatIntelligenceSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ['threat_type', 'source', 'is_active']
    search_fields = ['ip_address', 'domain', 'description']
    ordering_fields = ['confidence', 'last_seen']
    ordering = ['-last_seen']


class ThreatCorrelationView(APIView):
    """
    GET /api/threats/<ip>/correlate/

    Given an IP address, check whether it exists in the threat intelligence
    database, count how many alerts it has generated (as either source or
    destination), and return a recommendation.

    Requires authentication.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, ip):
        # Look up threat intelligence entries for this IP
        threat_entries = ThreatIntelligence.objects.filter(ip_address=ip)
        is_known_threat = threat_entries.exists()

        # Count alerts where this IP appears as source or destination
        alert_count = Alert.objects.filter(src_ip=ip).count() + \
            Alert.objects.filter(dst_ip=ip).count()

        # Build recommendation based on threat data and alert history
        recommendation = self._build_recommendation(
            is_known_threat, threat_entries, alert_count,
        )

        data = {
            'ip_address': ip,
            'is_known_threat': is_known_threat,
            'threat_entries': ThreatIntelligenceSerializer(
                threat_entries, many=True,
            ).data,
            'alert_count': alert_count,
            'recommendation': recommendation,
        }

        serializer = ThreatCorrelationSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_recommendation(is_known_threat, threat_entries, alert_count):
        """Return a human-readable recommendation string."""

        if not is_known_threat and alert_count == 0:
            return (
                "No threat intelligence data found and no alerts recorded "
                "for this IP. Continue monitoring."
            )

        if not is_known_threat and alert_count > 0:
            return (
                f"This IP is not in the threat intelligence database but "
                f"has generated {alert_count} alert(s). Investigate recent "
                f"activity and consider adding it to a watch list."
            )

        # At this point is_known_threat is True
        max_confidence = max(
            (entry.confidence for entry in threat_entries), default=0,
        )
        threat_types = sorted(
            {entry.threat_type for entry in threat_entries},
        )
        types_str = ', '.join(threat_types)

        if max_confidence >= 0.9 or alert_count >= 10:
            return (
                f"HIGH RISK - Known threat ({types_str}) with confidence "
                f"{max_confidence:.0%} and {alert_count} alert(s). "
                f"Immediate blocking recommended."
            )

        if max_confidence >= 0.7 or alert_count >= 3:
            return (
                f"MEDIUM RISK - Known threat ({types_str}) with confidence "
                f"{max_confidence:.0%} and {alert_count} alert(s). "
                f"Review and consider blocking."
            )

        return (
            f"LOW RISK - Threat intelligence match ({types_str}) with "
            f"confidence {max_confidence:.0%} and {alert_count} alert(s). "
            f"Monitor closely."
        )
