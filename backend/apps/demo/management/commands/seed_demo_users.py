"""
Management command to seed demo users across all tier databases.
Each database gets its own user, environment, subscription,
MITRE ATT&CK data, and threat intelligence.

Run: python manage.py seed_demo_users
"""
from django.core.management.base import BaseCommand
from apps.accounts.models import CustomUser
from apps.subscriptions.models import SubscriptionPlan, UserSubscription
from apps.environments.models import Environment, EnvironmentMembership
from apps.mitre.models import MitreTactic, MitreTechnique
from apps.threats.models import ThreatIntelligence


# Seed data for subscription plans (same as seed_plans.py but applied per-DB)
PLANS = [
    {
        'name': 'free',
        'display_name': 'Free',
        'price': 0.00,
        'billing_cycle': 'forever',
        'description': 'Basic monitoring for individuals.',
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
        'description': 'Advanced detection for professionals.',
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
        'description': 'Enterprise-grade security.',
        'sort_order': 3,
        'features': {
            'max_alerts_per_day': -1,
            'can_view_alerts': True,
            'can_view_dashboard': True,
            'can_use_chatbot': True,
            'can_configure_ml': True,
            'can_manage_incidents': True,
            'can_generate_reports': True,
            'can_manage_teams': True,
            'can_view_threats': True,
            'can_view_packets': True,
            'max_environments': -1,
        },
    },
]

# Demo users: each is seeded into its corresponding tier database
DEMO_USERS = [
    {
        'db': 'free_db',
        'email': 'free@demo.local',
        'username': 'freeuser',
        'password': 'demo123',
        'first_name': 'Free',
        'last_name': 'User',
        'role': 'free',
        'plan_name': 'free',
        'env_name': 'Free Monitoring',
    },
    {
        'db': 'premium_db',
        'email': 'premium@demo.local',
        'username': 'premiumuser',
        'password': 'demo123',
        'first_name': 'Premium',
        'last_name': 'User',
        'role': 'premium',
        'plan_name': 'premium',
        'env_name': 'Premium SOC',
    },
    {
        'db': 'exclusive_db',
        'email': 'exclusive@demo.local',
        'username': 'exclusiveuser',
        'password': 'demo123',
        'first_name': 'Exclusive',
        'last_name': 'User',
        'role': 'exclusive',
        'plan_name': 'exclusive',
        'env_name': 'Exclusive Security',
    },
    {
        'db': 'free_db',
        'email': 'admin@ids.local',
        'username': 'admin',
        'password': 'admin123',
        'first_name': 'Admin',
        'last_name': 'User',
        'role': 'admin',
        'plan_name': 'exclusive',
        'env_name': 'Admin Environment',
        'is_staff': True,
        'is_superuser': True,
    },
]


class Command(BaseCommand):
    help = 'Seed demo users, environments, and subscriptions across all tier databases'

    def handle(self, *args, **options):
        databases = ['free_db', 'premium_db', 'exclusive_db']

        # Step 1: Seed subscription plans into every database
        for db in databases:
            for plan_data in PLANS:
                SubscriptionPlan.objects.using(db).update_or_create(
                    name=plan_data['name'],
                    defaults=plan_data,
                )
            self.stdout.write(f'  Plans seeded in {db}')

        # Step 2: Seed MITRE ATT&CK data into every database
        for db in databases:
            self._seed_mitre(db)

        # Step 3: Seed threat intelligence into every database
        for db in databases:
            self._seed_threats(db)

        # Step 4: Create demo users in their respective databases
        for user_data in DEMO_USERS:
            db = user_data['db']
            self._create_user(db, user_data)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Demo data seeded successfully!'))
        self.stdout.write('')
        self.stdout.write('  Login Credentials:')
        self.stdout.write('  ──────────────────────────────')
        self.stdout.write('  Admin:     admin@ids.local / admin123')
        self.stdout.write('  Free:      free@demo.local / demo123')
        self.stdout.write('  Premium:   premium@demo.local / demo123')
        self.stdout.write('  Exclusive: exclusive@demo.local / demo123')

    def _create_user(self, db, data):
        """Create a user with environment and subscription in the specified database."""
        email = data['email']

        # Check if user already exists
        if CustomUser.objects.using(db).filter(email=email).exists():
            self.stdout.write(f'  User {email} already exists in {db}, skipping.')
            return

        # Create user
        user = CustomUser(
            email=email,
            username=data['username'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data['role'],
            is_staff=data.get('is_staff', False),
            is_superuser=data.get('is_superuser', False),
        )
        user.set_password(data['password'])
        user.save(using=db)

        # Create environment
        env = Environment(
            name=data['env_name'],
            owner=user,
            description=f'Demo environment for {data["first_name"]} {data["last_name"]}',
            network_interface='en0',
        )
        env.save(using=db)

        # Create membership
        EnvironmentMembership.objects.using(db).create(
            user=user,
            environment=env,
            role='team_leader',
        )

        # Create subscription
        plan = SubscriptionPlan.objects.using(db).get(name=data['plan_name'])
        UserSubscription.objects.using(db).update_or_create(
            user=user,
            defaults={'plan': plan, 'is_active': True},
        )

        self.stdout.write(self.style.SUCCESS(
            f'  Created {email} ({data["role"]}) in {db} with environment "{data["env_name"]}"'
        ))

    def _seed_mitre(self, db):
        """Seed MITRE ATT&CK data into the specified database."""
        from apps.mitre.management.commands.seed_mitre import MITRE_DATA

        tactics_created = 0
        techniques_created = 0

        for tactic_data in MITRE_DATA:
            tactic, created = MitreTactic.objects.using(db).update_or_create(
                tactic_id=tactic_data['tactic_id'],
                defaults={
                    'name': tactic_data['name'],
                    'description': tactic_data['description'],
                },
            )
            if created:
                tactics_created += 1

            for tech_data in tactic_data['techniques']:
                _, tech_created = MitreTechnique.objects.using(db).update_or_create(
                    technique_id=tech_data['technique_id'],
                    defaults={
                        'name': tech_data['name'],
                        'tactic': tactic,
                        'description': tech_data['description'],
                        'detection_hint': tech_data.get('detection_hint', ''),
                        'mitigation': tech_data.get('mitigation', ''),
                        'maps_to_alert_types': tech_data.get('maps_to_alert_types', []),
                    },
                )
                if tech_created:
                    techniques_created += 1

        self.stdout.write(
            f'  MITRE seeded in {db}: {tactics_created} tactics, {techniques_created} techniques'
        )

    def _seed_threats(self, db):
        """Seed threat intelligence data into the specified database."""
        from django.utils import timezone
        from apps.threats.management.commands.seed_threats import THREAT_ENTRIES

        created_count = 0
        for entry in THREAT_ENTRIES:
            _, created = ThreatIntelligence.objects.using(db).update_or_create(
                ip_address=entry.get('ip_address', ''),
                defaults={
                    'domain': entry.get('domain'),
                    'threat_type': entry.get('threat_type', 'unknown'),
                    'source': entry.get('source', 'Manual'),
                    'confidence': entry.get('confidence', 0.5),
                    'description': entry.get('description', ''),
                    'tags': entry.get('tags', []),
                    'last_seen': timezone.now(),
                    'mitre_tactic': entry.get('mitre_tactic', ''),
                    'mitre_technique': entry.get('mitre_technique', ''),
                    'mitre_technique_id': entry.get('mitre_technique_id', ''),
                    'is_active': True,
                },
            )
            if created:
                created_count += 1

        self.stdout.write(f'  Threats seeded in {db}: {created_count} entries')
