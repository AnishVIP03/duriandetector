from django.db import models


class MitreTactic(models.Model):
    """A MITRE ATT&CK tactic (e.g. Reconnaissance, Initial Access)."""

    tactic_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()

    class Meta:
        ordering = ['tactic_id']

    def __str__(self):
        return f"{self.tactic_id} - {self.name}"


class MitreTechnique(models.Model):
    """A MITRE ATT&CK technique linked to a tactic."""

    technique_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    tactic = models.ForeignKey(
        MitreTactic,
        on_delete=models.CASCADE,
        related_name='techniques',
    )
    description = models.TextField()
    detection_hint = models.TextField(null=True, blank=True)
    mitigation = models.TextField(null=True, blank=True)
    maps_to_alert_types = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['technique_id']

    def __str__(self):
        return f"{self.technique_id} - {self.name}"
