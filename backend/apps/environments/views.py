"""
Views for environments app — US-03, US-04, US-25–US-28.
"""
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Environment, EnvironmentMembership
from .serializers import (
    EnvironmentSerializer,
    CreateEnvironmentSerializer,
    JoinEnvironmentSerializer,
    MembershipSerializer,
    InviteMemberSerializer,
)
from apps.accounts.models import CustomUser


class CreateEnvironmentView(generics.CreateAPIView):
    """Create a new environment — US-03."""
    serializer_class = CreateEnvironmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        env = serializer.save(owner=request.user)

        # Auto-add owner as team leader
        EnvironmentMembership.objects.create(
            user=request.user,
            environment=env,
            role=EnvironmentMembership.MemberRole.TEAM_LEADER,
        )
        # Update user team role
        request.user.team_role = CustomUser.TeamRole.TEAM_LEADER
        request.user.save(update_fields=['team_role'])

        return Response(
            EnvironmentSerializer(env).data,
            status=status.HTTP_201_CREATED,
        )


class JoinEnvironmentView(APIView):
    """Join an environment via PIN or invitation code — US-04."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = JoinEnvironmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pin = serializer.validated_data.get('pin')
        invitation_code = serializer.validated_data.get('invitation_code')

        try:
            if pin:
                env = Environment.objects.get(pin=pin)
            else:
                env = Environment.objects.get(invitation_code=invitation_code)
        except Environment.DoesNotExist:
            return Response(
                {'error': 'Invalid PIN or invitation code.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if already a member
        if EnvironmentMembership.objects.filter(user=request.user, environment=env).exists():
            return Response(
                {'error': 'You are already a member of this environment.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create membership
        EnvironmentMembership.objects.create(
            user=request.user,
            environment=env,
            role=EnvironmentMembership.MemberRole.MEMBER,
        )
        request.user.team_role = CustomUser.TeamRole.MEMBER
        request.user.save(update_fields=['team_role'])

        return Response({
            'message': f'Successfully joined {env.name}.',
            'environment': EnvironmentSerializer(env).data,
        })


class EnvironmentDetailView(generics.RetrieveUpdateAPIView):
    """View/update environment details."""
    serializer_class = EnvironmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Environment.objects.filter(
            memberships__user=self.request.user
        )


class EnvironmentMembersView(generics.ListAPIView):
    """List members of an environment — US-25."""
    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        env_id = self.kwargs['env_id']
        return EnvironmentMembership.objects.filter(
            environment_id=env_id,
            environment__memberships__user=self.request.user,
        ).select_related('user')


class InviteMemberView(APIView):
    """Invite a user to join the environment — US-26."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, env_id):
        serializer = InviteMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        env = get_object_or_404(Environment, id=env_id)

        # Check requester is team leader or owner
        membership = EnvironmentMembership.objects.filter(
            user=request.user, environment=env
        ).first()
        if not membership or membership.role not in ('team_leader',):
            return Response(
                {'error': 'Only team leaders can invite members.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Find user by email
        try:
            invitee = CustomUser.objects.get(email=serializer.validated_data['email'])
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'User with that email not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if already member
        if EnvironmentMembership.objects.filter(user=invitee, environment=env).exists():
            return Response(
                {'error': 'User is already a member.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create membership
        EnvironmentMembership.objects.create(
            user=invitee,
            environment=env,
            role=serializer.validated_data['role'],
            invited_by=request.user,
        )
        invitee.team_role = serializer.validated_data['role']
        invitee.save(update_fields=['team_role'])

        return Response({'message': f'{invitee.email} has been invited.'}, status=status.HTTP_201_CREATED)


class RemoveMemberView(APIView):
    """Remove a member from the environment — US-27."""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, env_id, user_id):
        env = get_object_or_404(Environment, id=env_id)

        # Check requester is team leader
        requester_membership = EnvironmentMembership.objects.filter(
            user=request.user, environment=env, role='team_leader'
        ).first()
        if not requester_membership and env.owner != request.user:
            return Response(
                {'error': 'Only team leaders can remove members.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Cannot remove owner
        if int(user_id) == env.owner.id:
            return Response(
                {'error': 'Cannot remove the environment owner.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership = get_object_or_404(
            EnvironmentMembership, user_id=user_id, environment=env
        )
        membership.delete()

        return Response({'message': 'Member removed.'}, status=status.HTTP_204_NO_CONTENT)


class RegenerateInviteView(APIView):
    """Regenerate the environment invitation code — US-28."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, env_id):
        env = get_object_or_404(Environment, id=env_id, owner=request.user)
        new_code = env.regenerate_invitation_code()
        return Response({
            'message': 'Invitation code regenerated.',
            'invitation_code': str(new_code),
        })
