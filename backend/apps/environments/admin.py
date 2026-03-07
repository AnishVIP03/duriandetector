from django.contrib import admin
from .models import Environment, EnvironmentMembership


@admin.register(Environment)
class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'pin', 'organisation', 'created_at']
    search_fields = ['name', 'organisation', 'owner__email']


@admin.register(EnvironmentMembership)
class EnvironmentMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'environment', 'role', 'joined_at']
    list_filter = ['role']
