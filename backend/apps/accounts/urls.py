"""
URL routes for accounts app.
Base path: /api/auth/
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'accounts'

urlpatterns = [
    # Auth endpoints
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),

    # Admin endpoints
    path('admin/users/', views.AdminUserListView.as_view(), name='admin-user-list'),
    path('admin/users/<int:user_id>/suspend/', views.AdminSuspendUserView.as_view(), name='admin-suspend'),
    path('admin/users/<int:user_id>/unsuspend/', views.AdminUnsuspendUserView.as_view(), name='admin-unsuspend'),
    path('admin/users/<int:user_id>/reset-password/', views.AdminResetPasswordView.as_view(), name='admin-reset-password'),
    path('admin/users/<int:user_id>/subscription/', views.AdminUpdateSubscriptionView.as_view(), name='admin-update-subscription'),
]
