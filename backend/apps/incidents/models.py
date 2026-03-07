from django.db import models
from django.conf import settings


class Incident(models.Model):
    """A security incident composed of one or more related alerts."""

    class Severity(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        CRITICAL = 'critical', 'Critical'

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'

    environment = models.ForeignKey(
        'environments.Environment',
        on_delete=models.CASCADE,
        related_name='incidents',
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=Severity.choices)
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.OPEN,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_incidents',
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_incidents',
    )
    alerts = models.ManyToManyField(
        'alerts.Alert',
        blank=True,
        related_name='incidents',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.severity}] {self.title} ({self.status})"


class IncidentNote(models.Model):
    """A note or comment on an incident."""

    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='notes',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='incident_notes',
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Note by {self.author} on {self.incident.title}"
