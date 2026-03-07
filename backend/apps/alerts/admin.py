from django.contrib import admin
from .models import Alert, BlockedIP


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = [
        'alert_type', 'severity', 'src_ip', 'dst_ip', 'protocol',
        'confidence_score', 'is_blocked', 'environment', 'timestamp',
    ]
    list_filter = ['severity', 'alert_type', 'protocol', 'is_blocked']
    search_fields = ['src_ip', 'dst_ip', 'country', 'city']


@admin.register(BlockedIP)
class BlockedIPAdmin(admin.ModelAdmin):
    list_display = [
        'ip_address', 'environment', 'blocked_by', 'reason',
        'blocked_at', 'is_active',
    ]
    list_filter = ['is_active']
    search_fields = ['ip_address']
