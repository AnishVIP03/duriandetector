"""
Views for the MITRE ATT&CK module.
Provides heatmap data and technique detail endpoints.
"""
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Q, Prefetch

from .models import MitreTactic, MitreTechnique
from .serializers import MitreTacticSerializer, MitreTechniqueSerializer
from apps.alerts.models import Alert
from apps.environments.models import EnvironmentMembership


def _get_user_environment(user):
    """Helper to get user's environment."""
    membership = EnvironmentMembership.objects.filter(
        user=user
    ).select_related('environment').first()
    return membership.environment if membership else None


class MitreHeatmapView(APIView):
    """
    GET — Return all tactics with their techniques annotated by alert counts.
    Used to render the MITRE ATT&CK heatmap on the frontend.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        env = _get_user_environment(request.user)

        # Build a filter condition scoped to the user's environment
        alert_filter = Q(technique_id__isnull=False)
        if env:
            alert_filter &= Q(alerts_env=env)

        # Annotate each technique with its alert count.
        # The Alert model stores mitre_technique_id as a CharField matching
        # MitreTechnique.technique_id.
        techniques_qs = MitreTechnique.objects.all()
        if env:
            techniques_qs = techniques_qs.annotate(
                alert_count=Count(
                    'id',
                    filter=Q(
                        technique_id__in=Alert.objects.filter(
                            environment=env,
                            mitre_technique_id__isnull=False,
                        ).values_list('mitre_technique_id', flat=True)
                    )
                )
            )
            # More accurate: use a Subquery for real counts
            from django.db.models import Subquery, OuterRef, IntegerField, Value
            from django.db.models.functions import Coalesce

            alert_counts = (
                Alert.objects.filter(
                    environment=env,
                    mitre_technique_id=OuterRef('technique_id'),
                )
                .order_by()
                .values('mitre_technique_id')
                .annotate(cnt=Count('id'))
                .values('cnt')
            )
            techniques_qs = MitreTechnique.objects.annotate(
                alert_count=Coalesce(
                    Subquery(alert_counts, output_field=IntegerField()),
                    Value(0),
                )
            )
        else:
            # No environment — just return zero counts
            from django.db.models import Value, IntegerField
            techniques_qs = MitreTechnique.objects.annotate(
                alert_count=Value(0, output_field=IntegerField())
            )

        tactics = MitreTactic.objects.prefetch_related(
            Prefetch('techniques', queryset=techniques_qs)
        ).all()

        serializer = MitreTacticSerializer(tactics, many=True)
        return Response(serializer.data)


class MitreTechniqueDetailView(APIView):
    """
    GET — Return a single technique's details along with recent matching alerts.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, technique_id):
        try:
            technique = MitreTechnique.objects.select_related('tactic').get(
                technique_id=technique_id
            )
        except MitreTechnique.DoesNotExist:
            return Response(
                {'error': 'Technique not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        env = _get_user_environment(request.user)

        # Get recent alerts for this technique
        alerts = []
        alert_count = 0
        if env:
            alert_qs = Alert.objects.filter(
                environment=env,
                mitre_technique_id=technique.technique_id,
            ).order_by('-timestamp')[:20]
            alert_count = Alert.objects.filter(
                environment=env,
                mitre_technique_id=technique.technique_id,
            ).count()
            alerts = [
                {
                    'id': a.id,
                    'alert_type': a.alert_type,
                    'severity': a.severity,
                    'src_ip': a.src_ip,
                    'dst_ip': a.dst_ip,
                    'timestamp': a.timestamp.isoformat(),
                    'country': a.country,
                }
                for a in alert_qs
            ]

        return Response({
            'id': technique.id,
            'technique_id': technique.technique_id,
            'name': technique.name,
            'description': technique.description,
            'detection_hint': technique.detection_hint,
            'mitigation': technique.mitigation,
            'tactic': {
                'id': technique.tactic.id,
                'tactic_id': technique.tactic.tactic_id,
                'name': technique.tactic.name,
            },
            'alert_count': alert_count,
            'recent_alerts': alerts,
        })
