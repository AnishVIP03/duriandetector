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
]
