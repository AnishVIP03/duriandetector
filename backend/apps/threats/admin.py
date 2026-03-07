from django.contrib import admin
from .models import ThreatIntelligence


@admin.register(ThreatIntelligence)
class ThreatIntelligenceAdmin(admin.ModelAdmin):
    list_display = [
        'ip_address', 'domain', 'threat_type', 'source',
        'confidence', 'last_seen', 'is_active',
    ]
    list_filter = ['threat_type', 'source', 'is_active']
    search_fields = ['ip_address', 'domain', 'description']
