"""
Audit logging signals for the IDS project.

Listens to Django signals across the application and creates AuditLog
entries for security-relevant events: authentication, alerts, IP blocking,
environment management, incident lifecycle, and subscription changes.
"""
import logging

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.audit.models import AuditLog

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def log_audit(user, action, target_type=None, target_id=None,
              environment=None, metadata=None):
    """Create an AuditLog entry.

    Parameters
    ----------
    user : User | None
        The user who triggered the action.
    action : str
        A short verb phrase describing the action (e.g. "user.login").
    target_type : str | None
        The model/entity type affected (e.g. "Alert", "BlockedIP").
    target_id : int | None
        The primary key of the affected object.
    environment : Environment | None
        The environment context, if applicable.
    metadata : dict | None
        Arbitrary extra data stored as JSON.
    """
    try:
        AuditLog.objects.create(
            user=user,
            action=action,
            target_type=target_type,
            target_id=target_id,
            environment=environment,
            metadata=metadata or {},
        )
    except Exception:
        logger.exception("Failed to write audit log entry for action=%s", action)


# ---------------------------------------------------------------------------
# Authentication signals
# ---------------------------------------------------------------------------

@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    """Log when a user successfully authenticates."""
    log_audit(
        user=user,
        action='user.login',
        target_type='User',
        target_id=user.pk,
        metadata={
            'email': user.email,
        },
    )


@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    """Log when a user logs out."""
    log_audit(
        user=user,
        action='user.logout',
        target_type='User',
        target_id=user.pk if user else None,
        metadata={
            'email': user.email if user else None,
        },
    )


# ---------------------------------------------------------------------------
# Alert signals
# ---------------------------------------------------------------------------

@receiver(post_save, sender='alerts.Alert')
def on_alert_saved(sender, instance, created, **kwargs):
    """Log when a new alert is created by the IDS."""
    if not created:
        return

    log_audit(
        user=None,
        action='alert.created',
        target_type='Alert',
        target_id=instance.pk,
        environment=instance.environment,
        metadata={
            'alert_type': instance.alert_type,
            'severity': instance.severity,
            'src_ip': instance.src_ip,
            'dst_ip': instance.dst_ip,
            'protocol': instance.protocol,
            'confidence_score': instance.confidence_score,
        },
    )


# ---------------------------------------------------------------------------
# Blocked IP signals
# ---------------------------------------------------------------------------

@receiver(post_save, sender='alerts.BlockedIP')
def on_blocked_ip_saved(sender, instance, created, **kwargs):
    """Log when an IP address is blocked or unblocked."""
    if created:
        action = 'ip.blocked'
    elif not instance.is_active:
        action = 'ip.unblocked'
    else:
        action = 'ip.updated'

    log_audit(
        user=instance.blocked_by,
        action=action,
        target_type='BlockedIP',
        target_id=instance.pk,
        environment=instance.environment,
        metadata={
            'ip_address': instance.ip_address,
            'reason': instance.reason,
            'is_active': instance.is_active,
        },
    )


# ---------------------------------------------------------------------------
# Environment signals
# ---------------------------------------------------------------------------

@receiver(post_save, sender='environments.Environment')
def on_environment_saved(sender, instance, created, **kwargs):
    """Log when an environment is created."""
    if not created:
        return

    log_audit(
        user=instance.owner,
        action='environment.created',
        target_type='Environment',
        target_id=instance.pk,
        environment=instance,
        metadata={
            'name': instance.name,
            'organisation': instance.organisation,
        },
    )


# ---------------------------------------------------------------------------
# Membership signals
# ---------------------------------------------------------------------------

@receiver(post_save, sender='environments.EnvironmentMembership')
def on_membership_saved(sender, instance, created, **kwargs):
    """Log when a membership is created or its role is changed."""
    if created:
        action = 'membership.created'
    else:
        action = 'membership.updated'

    log_audit(
        user=instance.user,
        action=action,
        target_type='EnvironmentMembership',
        target_id=instance.pk,
        environment=instance.environment,
        metadata={
            'role': instance.role,
            'member_email': instance.user.email,
            'environment_name': instance.environment.name,
            'invited_by': (
                instance.invited_by.email if instance.invited_by else None
            ),
        },
    )


@receiver(post_delete, sender='environments.EnvironmentMembership')
def on_membership_deleted(sender, instance, **kwargs):
    """Log when a member is removed from an environment."""
    log_audit(
        user=instance.user,
        action='membership.removed',
        target_type='EnvironmentMembership',
        target_id=instance.pk,
        environment=instance.environment,
        metadata={
            'role': instance.role,
            'member_email': instance.user.email,
            'environment_name': instance.environment.name,
        },
    )


# ---------------------------------------------------------------------------
# Incident signals
# ---------------------------------------------------------------------------

@receiver(post_save, sender='incidents.Incident')
def on_incident_saved(sender, instance, created, **kwargs):
    """Log when an incident is created or its status changes."""
    if created:
        action = 'incident.created'
    else:
        action = 'incident.status_changed'

    metadata = {
        'title': instance.title,
        'severity': instance.severity,
        'status': instance.status,
    }
    if instance.assigned_to:
        metadata['assigned_to'] = instance.assigned_to.email

    log_audit(
        user=instance.created_by,
        action=action,
        target_type='Incident',
        target_id=instance.pk,
        environment=instance.environment,
        metadata=metadata,
    )


# ---------------------------------------------------------------------------
# Subscription signals
# ---------------------------------------------------------------------------

@receiver(post_save, sender='subscriptions.UserSubscription')
def on_subscription_saved(sender, instance, created, **kwargs):
    """Log when a subscription is created or upgraded/changed."""
    if created:
        action = 'subscription.created'
    else:
        action = 'subscription.upgraded'

    log_audit(
        user=instance.user,
        action=action,
        target_type='UserSubscription',
        target_id=instance.pk,
        metadata={
            'plan': instance.plan.name,
            'is_active': instance.is_active,
        },
    )
