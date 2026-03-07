from django.db import models
from django.conf import settings


class CaptureSession(models.Model):
    """A packet capture session within an environment."""

    class Status(models.TextChoices):
        RUNNING = 'running', 'Running'
        STOPPED = 'stopped', 'Stopped'
        ERROR = 'error', 'Error'

    environment = models.ForeignKey(
        'environments.Environment',
        on_delete=models.CASCADE,
        related_name='capture_sessions',
    )
    interface = models.CharField(max_length=50)
    started_at = models.DateTimeField(auto_now_add=True)
    stopped_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.RUNNING,
    )
    packets_captured = models.IntegerField(default=0)
    alerts_generated = models.IntegerField(default=0)
    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='capture_sessions',
    )

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"Capture on {self.interface} ({self.status}) - {self.environment}"


class NetworkFeature(models.Model):
    """Extracted network features from a captured packet."""

    session = models.ForeignKey(
        CaptureSession,
        on_delete=models.CASCADE,
        related_name='features',
    )
    timestamp = models.DateTimeField()
    src_ip = models.GenericIPAddressField()
    dst_ip = models.GenericIPAddressField()
    src_port = models.IntegerField(null=True, blank=True)
    dst_port = models.IntegerField(null=True, blank=True)
    protocol = models.CharField(max_length=10)
    packet_length = models.IntegerField()
    ttl = models.IntegerField()
    flags = models.CharField(max_length=50, blank=True, default='')
    inter_arrival_time = models.FloatField(null=True, blank=True)
    features_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.src_ip}:{self.src_port} -> {self.dst_ip}:{self.dst_port} ({self.protocol})"
