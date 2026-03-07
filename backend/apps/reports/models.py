from django.db import models
from django.conf import settings


class Report(models.Model):
    """A generated report for an environment."""

    class ReportType(models.TextChoices):
        SUMMARY = 'summary', 'Summary'
        DETAILED = 'detailed', 'Detailed'
        INCIDENT = 'incident', 'Incident'
        THREAT = 'threat', 'Threat'

    environment = models.ForeignKey(
        'environments.Environment',
        on_delete=models.CASCADE,
        related_name='reports',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports',
    )
    title = models.CharField(max_length=255)
    report_type = models.CharField(max_length=10, choices=ReportType.choices)
    date_from = models.DateTimeField()
    date_to = models.DateTimeField()
    content = models.JSONField(default=dict, blank=True)
    pdf_file = models.FileField(upload_to='reports/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.report_type}) - {self.environment}"
