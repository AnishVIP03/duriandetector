from django.contrib import admin
from .models import AttackChain, EnvironmentRiskScore


@admin.register(AttackChain)
class AttackChainAdmin(admin.ModelAdmin):
    list_display = [
        'chain_type', 'src_ip', 'environment', 'risk_score',
        'status', 'started_at', 'last_seen_at',
    ]
    list_filter = ['chain_type', 'status']
    search_fields = ['src_ip']


@admin.register(EnvironmentRiskScore)
class EnvironmentRiskScoreAdmin(admin.ModelAdmin):
    list_display = ['environment', 'score', 'calculated_at']
