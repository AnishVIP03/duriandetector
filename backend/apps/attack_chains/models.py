from django.db import models


class AttackChain(models.Model):
    """A chain of related alerts representing a multi-stage attack."""

    class ChainType(models.TextChoices):
        RECON_TO_EXPLOIT = 'recon_to_exploit', 'Recon to Exploit'
        SCAN_TO_BRUTE = 'scan_to_brute', 'Scan to Brute Force'
        DOS_CAMPAIGN = 'dos_campaign', 'DoS Campaign'
        MULTI_STAGE = 'multi_stage', 'Multi-Stage'
        OTHER = 'other', 'Other'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        RESOLVED = 'resolved', 'Resolved'

    environment = models.ForeignKey(
        'environments.Environment',
        on_delete=models.CASCADE,
        related_name='attack_chains',
    )
    src_ip = models.GenericIPAddressField()
    chain_type = models.CharField(max_length=20, choices=ChainType.choices)
    alerts = models.ManyToManyField(
        'alerts.Alert',
        blank=True,
        related_name='attack_chains',
    )
    started_at = models.DateTimeField()
    last_seen_at = models.DateTimeField()
    risk_score = models.IntegerField()
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    mitre_techniques = models.ManyToManyField(
        'mitre.MitreTechnique',
        blank=True,
        related_name='attack_chains',
    )

    class Meta:
        ordering = ['-last_seen_at']

    def __str__(self):
        return f"{self.chain_type} from {self.src_ip} (risk={self.risk_score})"


class EnvironmentRiskScore(models.Model):
    """Calculated risk score for an environment at a point in time."""

    environment = models.ForeignKey(
        'environments.Environment',
        on_delete=models.CASCADE,
        related_name='risk_scores',
    )
    score = models.IntegerField()
    calculated_at = models.DateTimeField(auto_now_add=True)
    breakdown = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-calculated_at']

    def __str__(self):
        return f"Risk {self.score} for {self.environment} ({self.calculated_at})"
