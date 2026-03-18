"""
Management command to set up all demo users with environments, subscriptions,
and correct roles. Used by start.sh for one-click startup.
"""
import platform
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Set up admin and demo users with environments and subscriptions'

    def handle(self, *args, **options):
        from apps.accounts.models import CustomUser
        from apps.environments.models import Environment, EnvironmentMembership
        from apps.subscriptions.models import SubscriptionPlan, UserSubscription

        iface = 'en0' if platform.system() == 'Darwin' else 'eth0'
        databases = ['free_db', 'premium_db', 'exclusive_db']

        # Seed subscription plans into every database
        from apps.demo.management.commands.seed_demo_users import PLANS
        for db in databases:
            for plan_data in PLANS:
                SubscriptionPlan.objects.using(db).update_or_create(
                    name=plan_data['name'],
                    defaults=plan_data,
                )

        # Also seed plans into default (same as free_db but needed for queries)
        for plan_data in PLANS:
            SubscriptionPlan.objects.update_or_create(
                name=plan_data['name'],
                defaults=plan_data,
            )

        # Define all demo users
        demo_users = [
            {
                'db': 'free_db',
                'email': 'admin@ids.local',
                'username': 'admin',
                'password': 'admin123',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'admin',
                'plan_name': 'exclusive',
                'env_name': 'DurianDetector HQ',
                'is_staff': True,
                'is_superuser': True,
            },
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
        ]

        for user_data in demo_users:
            db = user_data['db']
            email = user_data['email']

            # Create or update user
            user, created = CustomUser.objects.using(db).update_or_create(
                email=email,
                defaults={
                    'username': user_data['username'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'role': user_data['role'],
                    'is_staff': user_data.get('is_staff', False),
                    'is_superuser': user_data.get('is_superuser', False),
                },
            )
            if created:
                user.set_password(user_data['password'])
                user.save(using=db)

            # Create environment if not exists
            if not EnvironmentMembership.objects.using(db).filter(user=user).exists():
                env = Environment(
                    name=user_data['env_name'],
                    owner=user,
                    description=f'Environment for {user_data["first_name"]}',
                    network_interface=iface,
                )
                env.save(using=db)
                EnvironmentMembership.objects.using(db).create(
                    user=user,
                    environment=env,
                    role='team_leader',
                )
            else:
                # Update interface
                membership = EnvironmentMembership.objects.using(db).filter(user=user).first()
                env = membership.environment
                if env.network_interface != iface:
                    env.network_interface = iface
                    env.save(using=db, update_fields=['network_interface'])

            # Create subscription
            plan = SubscriptionPlan.objects.using(db).get(name=user_data['plan_name'])
            UserSubscription.objects.using(db).update_or_create(
                user=user,
                defaults={'plan': plan, 'is_active': True},
            )

            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(
                f'  {action} {email} ({user_data["role"]}) in {db}'
            ))

        self.stdout.write(self.style.SUCCESS('\nAll demo users ready!'))
