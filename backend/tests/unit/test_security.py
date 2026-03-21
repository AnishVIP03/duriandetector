"""
Unit Tests — Security
Tests for JWT token creation and password hashing security.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.mark.django_db
class TestSecurity:

    def test_jwt_token_contains_user_id(self, free_user):
        """Test that JWT access token contains the correct user_id claim."""
        refresh = RefreshToken.for_user(free_user)
        access = refresh.access_token
        assert int(access["user_id"]) == free_user.id

    def test_jwt_refresh_token_is_valid(self, free_user):
        """Test that a refresh token can be generated for a user."""
        refresh = RefreshToken.for_user(free_user)
        assert str(refresh) is not None
        assert len(str(refresh)) > 20

    def test_hash_and_verify_password(self, create_user):
        """Test that password hashing and verification works correctly."""
        user = create_user(password="SecureP@ss123")
        assert user.check_password("SecureP@ss123") is True
        assert user.check_password("WrongPassword") is False

    def test_email_uniqueness(self, create_user, db):
        """Test that duplicate emails are rejected."""
        create_user(username="user1", email="unique@test.com")
        with pytest.raises(Exception):
            create_user(username="user2", email="unique@test.com")
