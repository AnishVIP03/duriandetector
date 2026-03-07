from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    """Tracks user and system actions for auditing purposes."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    environment = models.ForeignKey(
        'environments.Environment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    action = models.CharField(max_length=255)
    target_type = models.CharField(max_length=100, null=True, blank=True)
    target_id = models.IntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} - {self.action} ({self.timestamp})"


class SystemHealth(models.Model):
    """Periodic system health check results."""

    checked_at = models.DateTimeField(auto_now_add=True)
    celery_status = models.CharField(max_length=50)
    redis_status = models.CharField(max_length=50)
    postgres_status = models.CharField(max_length=50)
    capture_sessions_active = models.IntegerField()
    alerts_last_hour = models.IntegerField()
    disk_usage_percent = models.FloatField()
    cpu_percent = models.FloatField()
    memory_percent = models.FloatField()

    class Meta:
        ordering = ['-checked_at']
        verbose_name = 'System Health'
        verbose_name_plural = 'System Health'

    def __str__(self):
        return f"Health check at {self.checked_at}"
