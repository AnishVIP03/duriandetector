from django.apps import AppConfig


class AttackChainsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.attack_chains'
    verbose_name = 'Attack Chains'

    def ready(self):
        """Register signals for automatic attack chain correlation."""
        import apps.attack_chains.signals  # noqa: F401
