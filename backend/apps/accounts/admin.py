"""Admin configuration for accounts app."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, PasswordResetToken


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'username', 'role', 'team_role', 'is_suspended', 'is_active', 'created_at']
    list_filter = ['role', 'team_role', 'is_suspended', 'is_active']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-created_at']

    fieldsets = UserAdmin.fieldsets + (
        ('IDS Fields', {
            'fields': ('role', 'team_role', 'is_suspended', 'suspended_at', 'suspended_reason', 'last_login_ip'),
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('IDS Fields', {
            'fields': ('email', 'role'),
        }),
    )


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'expires_at', 'used']
    list_filter = ['used']
