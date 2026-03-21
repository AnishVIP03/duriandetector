"""
Signals for attack_chains app.

Listens for new Alert creation and triggers attack chain correlation
to automatically group related alerts into multi-stage attack chains.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='alerts.Alert')
def correlate_alert_into_chain(sender, instance, created, **kwargs):
    """
    After a new Alert is saved, run the correlation engine to check
    whether it should be grouped into an attack chain.

    Only runs on creation (not updates) to avoid infinite loops and
    unnecessary processing when alerts are modified (e.g. blocked).
    """
    if not created:
        return

    from .correlation import correlate_alert

    try:
        correlate_alert(instance)
    except Exception as e:
        # Never let correlation failures break alert creation
        logger.error(f"Attack chain correlation signal failed: {e}")
