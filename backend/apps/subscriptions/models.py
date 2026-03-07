"""
Models for subscriptions — US-01, US-14, US-15, US-29, US-33.
Manages subscription plans (free/premium/exclusive) and user subscriptions.
"""
from django.db import models
from django.conf import settings


class SubscriptionPlan(models.Model):
    """Defines available subscription tiers."""

    class PlanName(models.TextChoices):
        FREE = 'free', 'Free'
        PREMIUM = 'premium', 'Premium'
        EXCLUSIVE = 'exclusive', 'Exclusive'

    name = models.CharField(max_length=20, choices=PlanName.choices, unique=True)
    display_name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    billing_cycle = models.CharField(max_length=20, default='monthly')
    description = models.TextField(blank=True)
    features = models.JSONField(
        default=dict,
        help_text='Feature flags: max_alerts, can_configure_ml, can_manage_teams, etc.',
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.display_name} (${self.price}/{self.billing_cycle})"


class UserSubscription(models.Model):
    """Tracks a user's active subscription."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription',
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='subscribers',
    )
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.user.email} → {self.plan.name}"
