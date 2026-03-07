from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'price', 'billing_cycle', 'is_active']


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'started_at', 'is_active']
    list_filter = ['plan', 'is_active']
