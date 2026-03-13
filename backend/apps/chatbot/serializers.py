"""
Serializers for the DurianBot chatbot app.

Handles serialization of chat sessions and messages for the REST API,
including list views (with message counts) and detail views (with full
message history).
"""
from rest_framework import serializers
from .models import ChatSession, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serialize a single chat message (role, content, timestamp)."""

    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'timestamp']


class ChatSessionListSerializer(serializers.ModelSerializer):
    """
    Compact session serializer for the sidebar session list.

    Includes computed fields for message count and a preview of the
    last message (truncated to 100 chars).
    """
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'message_count', 'last_message', 'created_at', 'updated_at']

    def get_message_count(self, obj):
        """Return total number of messages in the session."""
        return obj.messages.count()

    def get_last_message(self, obj):
        """Return a 100-char preview of the most recent message, or None."""
        last = obj.messages.order_by('-timestamp').first()
        return last.content[:100] if last else None


class ChatSessionDetailSerializer(serializers.ModelSerializer):
    """Full session serializer with nested message history for the chat view."""
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'messages', 'created_at', 'updated_at']


class ChatInputSerializer(serializers.Serializer):
    """Validate incoming chat messages from the user."""
    message = serializers.CharField(max_length=2000)
    session_id = serializers.IntegerField(required=False)
