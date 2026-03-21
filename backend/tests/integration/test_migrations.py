"""
Integration Tests — Database Migrations
Tests that all migrations apply correctly and tables are created.
"""
import pytest


@pytest.mark.django_db
class TestMigrations:

    def test_all_tables_created(self):
        """Test that all expected Django app tables exist in the database."""
        from django.db import connection
        tables = connection.introspection.table_names()
        expected_tables = [
            "accounts_customuser",
            "accounts_passwordresettoken",
            "environments_environment",
            "alerts_alert",
            "alerts_blockedip",
            "alerts_whitelistedip",
            "incidents_incident",
        ]
        for table in expected_tables:
            assert table in tables, f"Table '{table}' not found in database"

    def test_user_model_fields_exist(self):
        """Test that the CustomUser model has all expected fields."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        expected_fields = [
            "id", "email", "username", "password", "role",
            "team_role", "is_suspended", "suspended_at",
            "created_at", "updated_at",
        ]
        model_fields = [f.name for f in User._meta.get_fields()]
        for field in expected_fields:
            assert field in model_fields, f"Field '{field}' not found in CustomUser model"
