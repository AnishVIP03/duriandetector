"""
Views for subscriptions app — US-01, US-14, US-15, US-29, US-33.
"""
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from .models import SubscriptionPlan, UserSubscription
from .serializers import (
    SubscriptionPlanSerializer,
    UserSubscriptionSerializer,
    UpgradeSubscriptionSerializer,
)


class PlanListView(generics.ListAPIView):
    """Public: List all available subscription plans — US-01."""
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]
    queryset = SubscriptionPlan.objects.filter(is_active=True)


class MySubscriptionView(APIView):
    """View current user's subscription — US-14."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            sub = UserSubscription.objects.select_related('plan').get(user=request.user)
            return Response(UserSubscriptionSerializer(sub).data)
        except UserSubscription.DoesNotExist:
            return Response({
                'message': 'No active subscription. You are on the Free tier.',
                'plan': 'free',
            })


class UpgradeSubscriptionView(APIView):
    """Upgrade the user's subscription — US-15."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = UpgradeSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan_name = serializer.validated_data['plan_name']

        try:
            plan = SubscriptionPlan.objects.get(name=plan_name, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response({'error': 'Plan not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Create or update subscription
        sub, created = UserSubscription.objects.update_or_create(
            user=request.user,
            defaults={
                'plan': plan,
                'is_active': True,
                'started_at': timezone.now(),
            }
        )

        # Update user role to match plan
        request.user.role = plan_name
        request.user.save(update_fields=['role'])

        return Response({
            'message': f'Subscription upgraded to {plan.display_name}.',
            'subscription': UserSubscriptionSerializer(sub).data,
        })


class ManageTeamSubscriptionView(APIView):
    """Team leader manages team subscription — US-29."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.team_role != 'team_leader':
            return Response(
                {'error': 'Only team leaders can manage team subscriptions.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        plan_name = request.data.get('plan_name')
        if not plan_name:
            return Response({'error': 'plan_name is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plan = SubscriptionPlan.objects.get(name=plan_name, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response({'error': 'Plan not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Update team leader's subscription
        sub, _ = UserSubscription.objects.update_or_create(
            user=request.user,
            defaults={'plan': plan, 'is_active': True, 'started_at': timezone.now()},
        )
        request.user.role = plan_name
        request.user.save(update_fields=['role'])

        return Response({
            'message': f'Team subscription updated to {plan.display_name}.',
            'subscription': UserSubscriptionSerializer(sub).data,
        })
