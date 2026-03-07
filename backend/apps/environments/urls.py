"""
URL routes for environments app.
Base path: /api/environments/
"""
from django.urls import path
from . import views

app_name = 'environments'

urlpatterns = [
    path('', views.CreateEnvironmentView.as_view(), name='create'),
    path('join/', views.JoinEnvironmentView.as_view(), name='join'),
    path('<int:pk>/', views.EnvironmentDetailView.as_view(), name='detail'),
    path('<int:env_id>/members/', views.EnvironmentMembersView.as_view(), name='members'),
    path('<int:env_id>/invite/', views.InviteMemberView.as_view(), name='invite'),
    path('<int:env_id>/members/<int:user_id>/', views.RemoveMemberView.as_view(), name='remove-member'),
    path('<int:env_id>/regenerate-invite/', views.RegenerateInviteView.as_view(), name='regenerate-invite'),
]
