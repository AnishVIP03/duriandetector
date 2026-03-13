"""
URL routes for alerts app.
Base path: /api/alerts/
"""
from django.urls import path
from . import views

app_name = 'alerts'

urlpatterns = [
    path('', views.AlertListView.as_view(), name='list'),
    path('stats/', views.DashboardStatsView.as_view(), name='stats'),
    path('geoip/', views.GeoIPDataView.as_view(), name='geoip'),
    path('<int:pk>/', views.AlertDetailView.as_view(), name='detail'),
    path('<int:alert_id>/block/', views.BlockIPView.as_view(), name='block'),
    path('<int:alert_id>/unblock/', views.UnblockIPView.as_view(), name='unblock'),
    # Block control list
    path('blocked-ips/', views.BlockedIPListView.as_view(), name='blocked-ips'),
    path('blocked-ips/<int:pk>/unblock/', views.UnblockIPByIdView.as_view(), name='unblock-by-id'),
    # Whitelist
    path('whitelist/', views.WhitelistedIPListCreateView.as_view(), name='whitelist'),
    path('whitelist/<int:pk>/', views.WhitelistedIPDeleteView.as_view(), name='whitelist-delete'),
    # Analytics
    path('analytics/', views.AlertAnalyticsView.as_view(), name='analytics'),
    # Traffic filters
    path('traffic-filters/', views.TrafficFilterRuleListCreateView.as_view(), name='traffic-filters'),
    path('traffic-filters/<int:pk>/', views.TrafficFilterRuleDetailView.as_view(), name='traffic-filter-detail'),
    path('traffic-filters/<int:pk>/toggle/', views.TrafficFilterRuleToggleView.as_view(), name='traffic-filter-toggle'),
    # Log ingestion
    path('log-ingestion/upload/', views.LogUploadView.as_view(), name='log-upload'),
    path('log-ingestion/history/', views.LogUploadHistoryView.as_view(), name='log-upload-history'),
]
