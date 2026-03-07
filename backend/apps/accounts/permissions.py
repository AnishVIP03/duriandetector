"""
Custom permission classes for role-based access control.
"""
from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Only allow admin users."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'admin'
        )


class IsPremiumOrAbove(BasePermission):
    """Allow premium, exclusive, and admin users."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ('premium', 'exclusive', 'admin')


class IsExclusiveOrAbove(BasePermission):
    """Allow exclusive and admin users."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ('exclusive', 'admin')


class IsTeamLeader(BasePermission):
    """Allow team leaders only."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.team_role == 'team_leader'


class IsSecurityAnalystOrAbove(BasePermission):
    """Allow security analysts and team leaders."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.team_role in ('security_analyst', 'team_leader')
