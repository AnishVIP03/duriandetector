from django.contrib import admin
from .models import AuditLog, SystemHealth


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'action', 'target_type', 'target_id',
        'ip_address', 'environment', 'timestamp',
    ]
    list_filter = ['action', 'target_type']
    search_fields = ['action', 'ip_address']


@admin.register(SystemHealth)
class SystemHealthAdmin(admin.ModelAdmin):
    list_display = [
        'checked_at', 'celery_status', 'redis_status', 'postgres_status',
        'capture_sessions_active', 'alerts_last_hour',
        'disk_usage_percent', 'cpu_percent', 'memory_percent',
    ]
