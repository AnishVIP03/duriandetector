"""
System Tests — Authentication Endpoints
Tests for register, login, logout, and profile endpoints.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestRegisterEndpoint:

    def test_register_success(self, api_client):
        """Test successful user registration."""
        data = {
            "username": "newuser",
            "email": "newuser@duriandetector.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "role": "free",
        }
        response = api_client.post("/api/auth/register/", data, format="json")
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_200_OK,
        ]

    def test_register_duplicate_email(self, api_client, free_user):
        """Test that registering with an existing email fails."""
        data = {
            "username": "another",
            "email": free_user.email,
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "role": "free",
        }
        response = api_client.post("/api/auth/register/", data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLoginEndpoint:

    def test_login_invalid_credentials(self, api_client, free_user):
        """Test that login with wrong password is rejected."""
        data = {
            "email": free_user.email,
            "password": "WrongPassword123!",
        }
        response = api_client.post("/api/auth/login/", data, format="json")
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
        ]

    def test_login_success(self, api_client, create_user):
        """Test that login with correct credentials returns JWT."""
        user = create_user(
            username="loginuser",
            email="login@duriandetector.com",
            password="CorrectPass123!",
        )
        data = {
            "email": "login@duriandetector.com",
            "password": "CorrectPass123!",
        }
        response = api_client.post("/api/auth/login/", data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "tokens" in response.data or "access" in response.data


@pytest.mark.django_db
class TestProfileEndpoint:

    def test_profile_requires_auth(self, api_client):
        """Test that /profile/ endpoint requires authentication."""
        response = api_client.get("/api/auth/profile/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_profile_success(self, authenticated_client, free_user):
        """Test that authenticated user can access their profile."""
        response = authenticated_client.get("/api/auth/profile/")
        assert response.status_code == status.HTTP_200_OK
