"""
Custom JWT authentication for multi-database demo setup.
Embeds the database alias in the JWT token so each request
routes to the correct tier database automatically.
"""
import logging
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from apps.accounts.models import CustomUser
from config.db_router import ROLE_TO_DB, set_db_for_role, ALL_DBS

logger = logging.getLogger(__name__)


class MultiDBRefreshToken(RefreshToken):
    """RefreshToken subclass that adds a 'db' claim for multi-database routing."""

    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)
        # Embed database alias in token
        db_alias = ROLE_TO_DB.get(user.role, 'default')
        token['db'] = db_alias
        token['role'] = user.role
        return token


class MultiDBJWTAuthentication(JWTAuthentication):
    """
    JWT authentication that reads the 'db' claim from the token
    and fetches the user from the correct database.
    """

    def get_user(self, validated_token):
        user_id = validated_token.get('user_id')
        db_alias = validated_token.get('db', 'default')

        if not user_id:
            raise AuthenticationFailed('Token contained no user_id.')

        # Set the thread-local DB context before fetching the user
        try:
            # Map db_alias to role for the middleware
            role = validated_token.get('role', 'free')
            set_db_for_role(role)

            user = CustomUser.objects.using(db_alias).get(id=user_id)
        except CustomUser.DoesNotExist:
            raise AuthenticationFailed('User not found in database.')

        if not user.is_active:
            raise AuthenticationFailed('User is inactive.')

        if user.is_suspended:
            raise AuthenticationFailed('User account is suspended.')

        return user


def authenticate_across_databases(email, password):
    """
    Try to authenticate a user across all tier databases.
    Returns (user, db_alias) on success, or (None, None) on failure.
    """
    # Check databases in order: free, premium, exclusive
    db_order = ['free_db', 'premium_db', 'exclusive_db']

    for db_alias in db_order:
        try:
            user = CustomUser.objects.using(db_alias).get(email=email)
            if user.check_password(password):
                return user, db_alias
        except CustomUser.DoesNotExist:
            continue

    return None, None


def get_tokens_for_user(user, db_alias):
    """Generate JWT tokens with the database alias embedded."""
    refresh = MultiDBRefreshToken.for_user(user)
    # Ensure db claim is set correctly
    refresh['db'] = db_alias
    refresh['role'] = user.role
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
