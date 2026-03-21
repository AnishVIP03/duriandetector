"""
Unit Tests — User Model
Tests for CustomUser model fields, roles, and password hashing.
"""
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:

    def test_create_user_with_valid_data(self, create_user):
        """Test that a user can be created with valid data."""
        user = create_user()
        assert user.username == "testuser"
        assert user.email == "test@duriandetector.com"
        assert user.role == "free"
        assert user.is_active is True

    def test_password_is_hashed(self, create_user):
        """Test that passwords are hashed and not stored in plain text."""
        user = create_user(password="MySecurePass123!")
        assert user.password != "MySecurePass123!"
        assert check_password("MySecurePass123!", user.password) is True

    def test_password_too_short_still_hashes(self, create_user):
        """Test that even short passwords are hashed by the model."""
        user = create_user(
            username="shortpw",
            email="short@test.com",
            password="123",
        )
        assert user.password != "123"
        assert check_password("123", user.password) is True

    def test_user_role_choices(self, create_user):
        """Test that user role values are valid choices."""
        valid_roles = ["unregistered", "free", "premium", "exclusive", "admin"]
        for role in valid_roles:
            user = create_user(
                username=f"user_{role}",
                email=f"{role}@test.com",
                role=role,
            )
            assert user.role == role

    def test_user_default_role_is_free(self, db):
        """Test that the default user role is 'free'."""
        user = User.objects.create_user(
            username="defaultrole",
            email="default@test.com",
            password="TestPass123!",
        )
        assert user.role == "free"

    def test_user_is_not_suspended_by_default(self, create_user):
        """Test that users are not suspended upon creation."""
        user = create_user()
        assert user.is_suspended is False
        assert user.suspended_at is None
