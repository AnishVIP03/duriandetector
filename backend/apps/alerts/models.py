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


class WhitelistedIP(models.Model):
    """An IP address whitelisted to suppress false-positive alerts."""

    ip_address = models.GenericIPAddressField()
    environment = models.ForeignKey(
        'environments.Environment',
        on_delete=models.CASCADE,
        related_name='whitelisted_ips',
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='whitelisted_ips',
    )
    reason = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['ip_address', 'environment']

    def __str__(self):
        return f"{self.ip_address} (whitelisted)"


class TrafficFilterRule(models.Model):
    """Saved traffic filter rules for auto-categorising alerts."""

    class FilterType(models.TextChoices):
        IP_RANGE = 'ip_range', 'IP Range'
        PORT_RANGE = 'port_range', 'Port Range'
        PROTOCOL = 'protocol', 'Protocol'
        COUNTRY = 'country', 'Country'
        ALERT_TYPE = 'alert_type', 'Alert Type'

    class TrafficCategory(models.TextChoices):
        VOLUME = 'volume', 'Volume-based'
        LOGIN = 'login', 'Login-based'
        DOMAIN = 'domain', 'Domain-based'
        CUSTOM = 'custom', 'Custom'

    class Action(models.TextChoices):
        SUPPRESS = 'suppress', 'Suppress'
        HIGHLIGHT = 'highlight', 'Highlight'
        AUTO_BLOCK = 'auto_block', 'Auto Block'
        ALERT_ONLY = 'alert_only', 'Alert Only'
        AUTO_BLOCK_TIMED = 'auto_block_timed', 'Auto-Block for 1 Hour'

    environment = models.ForeignKey(
        'environments.Environment',
        on_delete=models.CASCADE,
        related_name='traffic_filters',
    )
    name = models.CharField(max_length=200)
    filter_type = models.CharField(max_length=20, choices=FilterType.choices)
    value = models.CharField(max_length=500)
    action = models.CharField(max_length=20, choices=Action.choices)
    # Traffic category and threshold fields — US-52
    traffic_category = models.CharField(
        max_length=20, choices=TrafficCategory.choices,
        default='custom', blank=True,
    )
    threshold_count = models.IntegerField(
        null=True, blank=True,
        help_text='Number of events to trigger (e.g., 500 requests).',
    )
    threshold_window_seconds = models.IntegerField(
        null=True, blank=True,
        help_text='Time window in seconds (e.g., 60 for per-minute).',
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='traffic_filters',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.filter_type}: {self.value})"


class LogUpload(models.Model):
    """Record of a CSV/JSON log file upload."""

    class FileFormat(models.TextChoices):
        CSV = 'csv', 'CSV'
        JSON = 'json', 'JSON'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    environment = models.ForeignKey(
        'environments.Environment',
        on_delete=models.CASCADE,
        related_name='log_uploads',
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='log_uploads',
    )
    file_name = models.CharField(max_length=500)
    file_format = models.CharField(max_length=10, choices=FileFormat.choices)
    records_total = models.IntegerField(default=0)
    records_imported = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True, default='')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.file_name} ({self.status})"
