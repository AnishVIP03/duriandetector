from django.db import models
from django.conf import settings


class Alert(models.Model):
    """A network security alert detected by the IDS."""

    class Protocol(models.TextChoices):
        TCP = 'TCP', 'TCP'
        UDP = 'UDP', 'UDP'
        ICMP = 'ICMP', 'ICMP'
        HTTP = 'HTTP', 'HTTP'
        DNS = 'DNS', 'DNS'
        SSH = 'SSH', 'SSH'
        FTP = 'FTP', 'FTP'
        OTHER = 'OTHER', 'Other'

    class AlertType(models.TextChoices):
        PORT_SCAN = 'port_scan', 'Port Scan'
        DOS = 'dos', 'Denial of Service'
        BRUTE_FORCE = 'brute_force', 'Brute Force'
        SQL_INJECTION = 'sql_injection', 'SQL Injection'
        XSS = 'xss', 'Cross-Site Scripting'
        PROTOCOL_ANOMALY = 'protocol_anomaly', 'Protocol Anomaly'
        SUSPICIOUS_IP = 'suspicious_ip', 'Suspicious IP'
        OTHER = 'other', 'Other'

    class Severity(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        CRITICAL = 'critical', 'Critical'

    environment = models.ForeignKey(
        'environments.Environment',
        on_delete=models.CASCADE,
        related_name='alerts',
    )
    src_ip = models.GenericIPAddressField()
    dst_ip = models.GenericIPAddressField()
    src_port = models.IntegerField(null=True, blank=True)
    dst_port = models.IntegerField(null=True, blank=True)
    protocol = models.CharField(max_length=10, choices=Protocol.choices)
    alert_type = models.CharField(max_length=30, choices=AlertType.choices)
    severity = models.CharField(max_length=10, choices=Severity.choices)
    confidence_score = models.FloatField(
        help_text='Confidence score between 0 and 1.',
    )
    raw_payload = models.TextField(blank=True, default='')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    is_blocked = models.BooleanField(default=False)
    blocked_at = models.DateTimeField(null=True, blank=True)
    blocked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blocked_alerts',
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    ml_model_used = models.CharField(max_length=100, null=True, blank=True)
    mitre_tactic = models.CharField(max_length=100, null=True, blank=True)
    mitre_technique_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.severity}] {self.alert_type} from {self.src_ip} ({self.timestamp})"


class BlockedIP(models.Model):
    """An IP address that has been blocked by a user."""

    ip_address = models.GenericIPAddressField()
    environment = models.ForeignKey(
        'environments.Environment',
        on_delete=models.CASCADE,
        related_name='blocked_ips',
    )
    blocked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blocked_ips',
    )
    reason = models.TextField()
    blocked_at = models.DateTimeField(auto_now_add=True)
    unblocked_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-blocked_at']

    def __str__(self):
        return f"{self.ip_address} (blocked by {self.blocked_by})"
