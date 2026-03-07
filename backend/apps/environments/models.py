"""
Models for environments (workspaces/teams) — US-03, US-04, US-25–US-28.
Each environment is a workspace where teams monitor network traffic.
"""
import uuid
import random
import string
from django.db import models
from django.conf import settings


class Environment(models.Model):
    """
    A workspace/environment where a team monitors network traffic.
    Has a PIN for quick joins and an invitation code for secure invites.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    organisation = models.CharField(max_length=200, blank=True, default='')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_environments',
    )
    pin = models.CharField(max_length=6, unique=True, editable=False)
    invitation_code = models.UUIDField(default=uuid.uuid4, unique=True)
    network_interface = models.CharField(
        max_length=50,
        default='eth0',
        help_text='Network interface for packet capture (e.g. eth0, en0, wlan0).',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} (Owner: {self.owner.email})"

    def save(self, *args, **kwargs):
        if not self.pin:
            self.pin = self._generate_unique_pin()
        super().save(*args, **kwargs)

    def _generate_unique_pin(self):
        """Generate a unique 6-digit PIN."""
        while True:
            pin = ''.join(random.choices(string.digits, k=6))
            if not Environment.objects.filter(pin=pin).exists():
                return pin

    def regenerate_invitation_code(self):
        """Regenerate the invitation code — US-28."""
        self.invitation_code = uuid.uuid4()
        self.save(update_fields=['invitation_code'])
        return self.invitation_code


class EnvironmentMembership(models.Model):
    """
    Tracks which users belong to which environments, with their team role.
    """
    class MemberRole(models.TextChoices):
        MEMBER = 'member', 'Member'
        SECURITY_ANALYST = 'security_analyst', 'Security Analyst'
        TEAM_LEADER = 'team_leader', 'Team Leader'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='environment_memberships',
    )
    environment = models.ForeignKey(
        Environment,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    role = models.CharField(
        max_length=20,
        choices=MemberRole.choices,
        default=MemberRole.MEMBER,
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_invitations',
    )

    class Meta:
        unique_together = ('user', 'environment')
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.email} → {self.environment.name} ({self.role})"
