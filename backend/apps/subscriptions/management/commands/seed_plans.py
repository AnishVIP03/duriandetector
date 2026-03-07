"""
Management command to seed subscription plans.
Run: python manage.py seed_plans
"""
from django.core.management.base import BaseCommand
from apps.subscriptions.models import SubscriptionPlan


PLANS = [
    {
        'name': 'free',
        'display_name': 'Free',
        'price': 0.00,
        'billing_cycle': 'forever',
        'description': 'Basic monitoring for individuals. View alerts, basic dashboard, and chatbot access.',
        'sort_order': 1,
        'features': {
            'max_alerts_per_day': 100,
            'can_view_alerts': True,
            'can_view_dashboard': True,
            'can_use_chatbot': True,
            'can_configure_ml': False,
            'can_manage_incidents': False,
            'can_generate_reports': False,
            'can_manage_teams': False,
            'can_view_threats': False,
            'can_view_packets': False,
            'max_environments': 1,
        },
    },
    {
        'name': 'premium',
        'display_name': 'Premium',
        'price': 29.99,
        'billing_cycle': 'monthly',
        'description': 'Advanced detection for professionals. ML configuration, incident management, reports, and threat intelligence.',
        'sort_order': 2,
        'features': {
            'max_alerts_per_day': 10000,
            'can_view_alerts': True,
            'can_view_dashboard': True,
            'can_use_chatbot': True,
            'can_configure_ml': True,
            'can_manage_incidents': True,
            'can_generate_reports': True,
            'can_manage_teams': False,
            'can_view_threats': True,
            'can_view_packets': True,
            'max_environments': 3,
        },
    },
    {
        'name': 'exclusive',
        'display_name': 'Exclusive',
        'price': 99.99,
        'billing_cycle': 'monthly',
        'description': 'Enterprise-grade security. Full team management, unlimited alerts, priority support, and all features.',
        'sort_order': 3,
        'features': {
            'max_alerts_per_day': -1,  # unlimited
            'can_view_alerts': True,
            'can_view_dashboard': True,
            'can_use_chatbot': True,
            'can_configure_ml': True,
            'can_manage_incidents': True,
            'can_generate_reports': True,
            'can_manage_teams': True,
            'can_view_threats': True,
            'can_view_packets': True,
            'max_environments': -1,  # unlimited
        },
    },
]


class Command(BaseCommand):
    help = 'Seed subscription plans into the database'

    def handle(self, *args, **options):
        for plan_data in PLANS:
            plan, created = SubscriptionPlan.objects.update_or_create(
                name=plan_data['name'],
                defaults=plan_data,
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action}: {plan.display_name}'))

        self.stdout.write(self.style.SUCCESS('Subscription plans seeded successfully.'))
