"""
Serializers for environments app.
"""
from rest_framework import serializers
from .models import Environment, EnvironmentMembership
from apps.accounts.serializers import UserProfileSerializer


class EnvironmentSerializer(serializers.ModelSerializer):
    """Serializer for Environment CRUD."""
    owner_email = serializers.CharField(source='owner.email', read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Environment
        fields = [
            'id', 'name', 'description', 'organisation', 'owner',
            'owner_email', 'pin', 'invitation_code', 'network_interface',
            'created_at', 'member_count',
        ]
        read_only_fields = ['id', 'owner', 'pin', 'invitation_code', 'created_at']

    def get_member_count(self, obj):
        return obj.memberships.count()


class CreateEnvironmentSerializer(serializers.ModelSerializer):
    """Serializer for creating a new environment — US-03."""
    class Meta:
        model = Environment
        fields = ['name', 'description', 'organisation', 'network_interface']


class JoinEnvironmentSerializer(serializers.Serializer):
    """Serializer for joining an environment — US-04."""
    pin = serializers.CharField(max_length=6, required=False)
    invitation_code = serializers.UUIDField(required=False)

    def validate(self, attrs):
        pin = attrs.get('pin')
        invitation_code = attrs.get('invitation_code')
        if not pin and not invitation_code:
            raise serializers.ValidationError('Either pin or invitation_code is required.')
        return attrs


class MembershipSerializer(serializers.ModelSerializer):
    """Serializer for environment memberships — US-25."""
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model = EnvironmentMembership
        fields = ['id', 'user', 'role', 'joined_at', 'invited_by']
        read_only_fields = ['id', 'joined_at', 'invited_by']


class InviteMemberSerializer(serializers.Serializer):
    """Serializer for inviting a member — US-26."""
    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=EnvironmentMembership.MemberRole.choices,
        default=EnvironmentMembership.MemberRole.MEMBER,
    )
