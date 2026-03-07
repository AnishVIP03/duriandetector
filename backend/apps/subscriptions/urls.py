"""
URL routes for subscriptions app.
Base path: /api/subscriptions/
"""
from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('plans/', views.PlanListView.as_view(), name='plan-list'),
    path('my/', views.MySubscriptionView.as_view(), name='my-subscription'),
    path('upgrade/', views.UpgradeSubscriptionView.as_view(), name='upgrade'),
    path('manage/', views.ManageTeamSubscriptionView.as_view(), name='manage-team'),
]
