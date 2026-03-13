"""
Custom User model for the IDS platform.
Supports roles: unregistered, free, premium, exclusive, admin.
Supports team roles: member, security_analyst, team_leader.
"""
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    """Extended user model with role-based access and environment membership."""

    class Role(models.TextChoices):
        UNREGISTERED = 'unregistered', 'Unregistered'
        FREE = 'free', 'Free'
        PREMIUM = 'premium', 'Premium'
        EXCLUSIVE = 'exclusive', 'Exclusive'
        ADMIN = 'admin', 'Admin'

    class TeamRole(models.TextChoices):
        MEMBER = 'member', 'Member'
        SECURITY_ANALYST = 'security_analyst', 'Security Analyst'
        TEAM_LEADER = 'team_leader', 'Team Leader'

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.FREE,
    )
    team_role = models.CharField(
        max_length=20,
        choices=TeamRole.choices,
        null=True,
        blank=True,
    )
    is_suspended = models.BooleanField(default=False)
    suspended_at = models.DateTimeField(null=True, blank=True)
    suspended_reason = models.TextField(blank=True, default='')
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.email} ({self.role})"

    def suspend(self, reason=''):
        """
        Suspend this user account — US-31.

        Sets is_active=False to prevent login, records the suspension
        timestamp and reason for audit purposes.
        """
        self.is_suspended = True
        self.suspended_at = timezone.now()
        self.suspended_reason = reason
        self.is_active = False
        self.save(update_fields=['is_suspended', 'suspended_at', 'suspended_reason', 'is_active'])

    def unsuspend(self):
        """
        Reactivate a suspended user account — US-31.

        Clears all suspension fields and restores login access
        by setting is_active=True.
        """
        self.is_suspended = False
        self.suspended_at = None
        self.suspended_reason = ''
        self.is_active = True
        self.save(update_fields=['is_suspended', 'suspended_at', 'suspended_reason', 'is_active'])


class PasswordResetToken(models.Model):
    """Token for password reset flow."""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reset token for {self.user.email}"

    @property
    def is_valid(self):
        """Return True if the token has not been used and has not expired."""
        return not self.used and self.expires_at > timezone.now()
