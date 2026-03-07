"""
URL routes for audit app (admin panel).
Base path: /api/admin-panel/
"""
from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    path('audit-logs/', views.AuditLogListView.as_view(), name='audit-logs'),
    path('system-health/', views.SystemHealthView.as_view(), name='system-health'),
    path('capture-status/', views.CaptureStatusView.as_view(), name='capture-status'),
]
