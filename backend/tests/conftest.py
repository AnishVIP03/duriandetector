"""
Shared fixtures for all DurianDetector tests.
"""
import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.environments.models import Environment

User = get_user_model()


@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def create_user(db):
    """Factory fixture to create users."""
    def _create_user(
        username="testuser",
        email="test@duriandetector.com",
        password="TestPass123!",
        role="free",
        **kwargs,
    ):
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            **kwargs,
        )
        return user
    return _create_user


@pytest.fixture
def free_user(create_user):
    """Return a free-tier user."""
    return create_user()


@pytest.fixture
def premium_user(create_user):
    """Return a premium-tier user."""
    return create_user(
        username="premiumuser",
        email="premium@duriandetector.com",
        role="premium",
    )


@pytest.fixture
def admin_user(create_user):
    """Return an admin user."""
    return create_user(
        username="adminuser",
        email="admin@duriandetector.com",
        role="admin",
        is_staff=True,
    )


@pytest.fixture
def authenticated_client(api_client, free_user):
    """Return an API client authenticated as a free user."""
    api_client.force_authenticate(user=free_user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Return an API client authenticated as an admin."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def environment(db, free_user):
    """Return a test environment."""
    return Environment.objects.create(
        name="Test Environment",
        owner=free_user,
        description="Test environment for unit tests",
        organisation="Test Org",
        network_interface="en0",
    )
