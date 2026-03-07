from django.db import models
from django.conf import settings


class ChatSession(models.Model):
    """A chat session between a user and the AI assistant."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_sessions',
    )
    environment = models.ForeignKey(
        'environments.Environment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_sessions',
    )
    title = models.CharField(max_length=200, default='New Chat')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Chat session by {self.user} – {self.title} ({self.created_at})"


class ChatMessage(models.Model):
    """A single message in a chat session."""

    class Role(models.TextChoices):
        USER = 'user', 'User'
        ASSISTANT = 'assistant', 'Assistant'
        SYSTEM = 'system', 'System'

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.role}] {self.content[:50]}"
