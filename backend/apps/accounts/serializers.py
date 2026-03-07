"""
Serializers for accounts app.
Handles registration, login, user profile, and password reset.
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration — US-02."""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'first_name', 'last_name', 'password', 'password_confirm']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password'],
            role=CustomUser.Role.FREE,
        )
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login — US-05."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username=attrs['email'],
            password=attrs['password'],
        )
        if not user:
            raise serializers.ValidationError('Invalid email or password.')
        if user.is_suspended:
            raise serializers.ValidationError('Your account has been suspended.')
        if not user.is_active:
            raise serializers.ValidationError('Your account is inactive.')
        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for viewing/updating user profile."""
    environment_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'role', 'team_role', 'is_suspended', 'created_at',
            'updated_at', 'last_login_ip', 'environment_name',
        ]
        read_only_fields = ['id', 'email', 'role', 'is_suspended', 'created_at', 'updated_at', 'last_login_ip']

    def get_environment_name(self, obj):
        membership = obj.environment_memberships.select_related('environment').first()
        if membership:
            return membership.environment.name
        return None


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting a password reset — US-06."""
    email = serializers.EmailField()

    def validate_email(self, value):
        if not CustomUser.objects.filter(email=value).exists():
            # Don't reveal that email doesn't exist
            pass
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming a password reset — US-06."""
    token = serializers.UUIDField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Passwords do not match.'})
        return attrs


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer for admin user management — US-30, US-31, US-32, US-33."""
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'role', 'team_role', 'is_suspended', 'suspended_at',
            'suspended_reason', 'is_active', 'created_at',
            'updated_at', 'last_login', 'last_login_ip',
        ]
        read_only_fields = ['id', 'email', 'created_at', 'updated_at', 'last_login']
