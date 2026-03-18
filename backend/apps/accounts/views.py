"""
Views for accounts app.
Handles registration, login, logout, password reset, profile, and admin user management.
"""
import uuid
from datetime import timedelta

from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser, PasswordResetToken
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserProfileSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    AdminUserSerializer,
)
from .permissions import IsAdmin
from apps.audit.models import AuditLog


def _log_admin_action(request, action, target_user, metadata=None):
    """Create an AuditLog entry for an admin action — US-56."""
    AuditLog.objects.create(
        user=request.user,
        action=action,
        target_type='CustomUser',
        target_id=target_user.id,
        ip_address=request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
        or request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        metadata=metadata or {},
    )


class RegisterView(generics.CreateAPIView):
    """User registration — US-02."""
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        """Validate registration data, create the user, and return JWT tokens."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens for immediate login after registration
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Registration successful.',
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """User login — US-05. Returns JWT tokens."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Authenticate user credentials and return JWT access/refresh tokens."""
        from django.conf import settings

        # In demo mode, authenticate across all tier databases
        if getattr(settings, 'DEMO_MODE', False):
            return self._demo_login(request)

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # Update last login IP
        ip = self._get_client_ip(request)
        user.last_login_ip = ip
        user.save(update_fields=['last_login_ip'])

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Login successful.',
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })

    def _demo_login(self, request):
        """Login that checks all tier databases for the user."""
        from .auth_backends import authenticate_across_databases, get_tokens_for_user

        email = request.data.get('email', '')
        password = request.data.get('password', '')

        if not email or not password:
            return Response(
                {'error': 'Email and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user, db_alias = authenticate_across_databases(email, password)

        if not user:
            return Response(
                {'error': 'Invalid email or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if user.is_suspended:
            return Response(
                {'error': 'Your account has been suspended.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Update last login IP
        ip = self._get_client_ip(request)
        CustomUser.objects.using(db_alias).filter(pk=user.pk).update(
            last_login_ip=ip
        )

        # Generate tokens with db claim
        tokens = get_tokens_for_user(user, db_alias)

        return Response({
            'message': 'Login successful.',
            'user': UserProfileSerializer(user).data,
            'tokens': tokens,
        })

    def _get_client_ip(self, request):
        """Extract the client's real IP, respecting X-Forwarded-For from proxies."""
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class LogoutView(APIView):
    """User logout — US-05. Blacklists the refresh token."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Blacklist the provided refresh token to invalidate the session."""
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Logged out successfully.'})
        except Exception:
            return Response({'message': 'Logged out successfully.'})


class ProfileView(generics.RetrieveUpdateAPIView):
    """View/update current user profile."""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Return the currently authenticated user."""
        return self.request.user


class PasswordResetRequestView(APIView):
    """Request password reset — US-06. Generates reset token."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = CustomUser.objects.get(email=email)
            # Invalidate existing tokens
            PasswordResetToken.objects.filter(user=user, used=False).update(used=True)
            # Create new token
            token = PasswordResetToken.objects.create(
                user=user,
                expires_at=timezone.now() + timedelta(hours=1),
            )
            # In production, send email with token
            # For dev, return token in response
            return Response({
                'message': 'If an account with that email exists, a reset link has been sent.',
                'token': str(token.token),  # Remove in production
            })
        except CustomUser.DoesNotExist:
            pass

        return Response({
            'message': 'If an account with that email exists, a reset link has been sent.'
        })


class PasswordResetConfirmView(APIView):
    """Confirm password reset — US-06. Sets new password."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token_obj = PasswordResetToken.objects.get(
                token=serializer.validated_data['token']
            )
            if not token_obj.is_valid:
                return Response(
                    {'error': 'Token has expired or already been used.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Set new password
            user = token_obj.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            token_obj.used = True
            token_obj.save()

            return Response({'message': 'Password has been reset successfully.'})
        except PasswordResetToken.DoesNotExist:
            return Response(
                {'error': 'Invalid reset token.'},
                status=status.HTTP_400_BAD_REQUEST
            )


# ── Admin Views (US-30 to US-33) ──

class AdminUserListView(generics.ListAPIView):
    """Admin: List all users — US-30."""
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdmin]
    queryset = CustomUser.objects.all()
    filterset_fields = ['role', 'is_suspended', 'is_active']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering_fields = ['created_at', 'email', 'role']


class AdminSuspendUserView(APIView):
    """Admin: Suspend/unsuspend a user — US-31."""
    permission_classes = [IsAdmin]

    def post(self, request, user_id):
        """Suspend user."""
        try:
            user = CustomUser.objects.get(id=user_id)
            if user.role == CustomUser.Role.ADMIN:
                return Response({'error': 'Cannot suspend an admin.'}, status=status.HTTP_403_FORBIDDEN)
            reason = request.data.get('reason', '')
            user.suspend(reason=reason)
            _log_admin_action(request, 'suspend_user', user, {'reason': reason})
            return Response({'message': f'User {user.email} has been suspended.'})
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)


class AdminUnsuspendUserView(APIView):
    """Admin: Unsuspend a user — US-31."""
    permission_classes = [IsAdmin]

    def post(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
            user.unsuspend()
            _log_admin_action(request, 'unsuspend_user', user)
            return Response({'message': f'User {user.email} has been unsuspended.'})
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)


class AdminResetPasswordView(APIView):
    """Admin: Force reset a user's password — US-32."""
    permission_classes = [IsAdmin]

    def post(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
            new_password = request.data.get('new_password')
            if not new_password:
                return Response({'error': 'new_password is required.'}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(new_password)
            user.save()
            _log_admin_action(request, 'admin_reset_password', user)
            return Response({'message': f'Password for {user.email} has been reset.'})
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)


class AdminUpdateSubscriptionView(APIView):
    """Admin: Update a user's subscription/role — US-33."""
    permission_classes = [IsAdmin]

    def patch(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
            new_role = request.data.get('role')
            if new_role and new_role in dict(CustomUser.Role.choices):
                old_role = user.role
                user.role = new_role
                user.save(update_fields=['role'])
                _log_admin_action(request, 'update_subscription', user, {
                    'old_role': old_role, 'new_role': new_role,
                })
                return Response({
                    'message': f'User {user.email} role updated to {new_role}.',
                    'user': AdminUserSerializer(user).data,
                })
            return Response({'error': 'Invalid role.'}, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
