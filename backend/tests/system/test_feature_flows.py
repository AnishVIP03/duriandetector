"""
System Tests — Feature Flows
Tests for alerts, environments, incidents, chatbot, and admin flows.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestEnvironmentFlow:

    def test_create_environment(self, authenticated_client):
        """Test that a user can create an environment."""
        data = {
            "name": "My SOC Lab",
            "description": "Testing environment",
            "organisation": "TestOrg",
            "network_interface": "en0",
        }
        response = authenticated_client.post("/api/environments/", data, format="json")
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]

    def test_create_environment_requires_auth(self, api_client):
        """Test that environment creation requires authentication."""
        data = {
            "name": "Unauth Env",
            "description": "Should fail",
            "organisation": "TestOrg",
            "network_interface": "en0",
        }
        response = api_client.post("/api/environments/", data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestAlertFlow:

    def test_list_alerts_requires_auth(self, api_client):
        """Test that alert list requires authentication."""
        response = api_client.get("/api/alerts/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_alerts_authenticated(self, authenticated_client):
        """Test that authenticated user can list alerts."""
        response = authenticated_client.get("/api/alerts/")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestIncidentFlow:

    def test_list_incidents_requires_auth(self, api_client):
        """Test that incident list requires authentication."""
        response = api_client.get("/api/incidents/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_incidents_requires_premium(self, authenticated_client):
        """Test that incidents require premium tier access."""
        response = authenticated_client.get("/api/incidents/")
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestChatbotFlow:

    def test_chatbot_requires_auth(self, api_client):
        """Test that chatbot endpoints require authentication."""
        response = api_client.get("/api/chatbot/sessions/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestAdminAccessControl:

    def test_admin_user_list_forbidden_for_free_user(self, authenticated_client):
        """Test that free users cannot access admin endpoints."""
        response = authenticated_client.get("/api/auth/admin/users/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_user_list_allowed_for_admin(self, admin_client):
        """Test that admin users can access admin endpoints."""
        response = admin_client.get("/api/auth/admin/users/")
        assert response.status_code == status.HTTP_200_OK

    def test_admin_suspend_forbidden_for_free_user(self, authenticated_client, free_user):
        """Test that free users cannot suspend accounts."""
        response = authenticated_client.post(f"/api/auth/admin/users/{free_user.id}/suspend/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
