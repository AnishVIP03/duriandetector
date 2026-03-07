"""
Serializers for subscriptions app.
"""
from rest_framework import serializers
from .models import SubscriptionPlan, UserSubscription


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Public serializer for subscription plans — US-01."""
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'display_name', 'price', 'billing_cycle',
            'description', 'features', 'sort_order',
        ]


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for a user's subscription — US-14."""
    plan = SubscriptionPlanSerializer(read_only=True)

    class Meta:
        model = UserSubscription
        fields = ['id', 'plan', 'started_at', 'expires_at', 'is_active']


class UpgradeSubscriptionSerializer(serializers.Serializer):
    """Serializer for upgrading subscription — US-15."""
    plan_name = serializers.ChoiceField(choices=SubscriptionPlan.PlanName.choices)
