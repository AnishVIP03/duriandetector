from django.db import models


class ThreatIntelligence(models.Model):
    """External threat intelligence data for known malicious IPs/domains."""

    ip_address = models.GenericIPAddressField()
    domain = models.CharField(max_length=255, null=True, blank=True)
    threat_type = models.CharField(max_length=100)
    source = models.CharField(max_length=200)
    confidence = models.FloatField(
        help_text='Confidence score between 0 and 1.',
    )
    last_seen = models.DateTimeField()
    description = models.TextField()
    tags = models.JSONField(default=list, blank=True)
    mitre_tactic = models.CharField(max_length=100, blank=True, default='')
    mitre_technique = models.CharField(max_length=100, blank=True, default='')
    mitre_technique_id = models.CharField(max_length=50, blank=True, default='')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-last_seen']
        verbose_name = 'Threat Intelligence'
        verbose_name_plural = 'Threat Intelligence'

    def __str__(self):
        return f"{self.ip_address} - {self.threat_type} ({self.source})"
