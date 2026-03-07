"""
ASGI config for IDS project.
Exposes the ASGI application with Django Channels WebSocket routing.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from apps.alerts.routing import websocket_urlpatterns as alert_ws
from apps.network_capture.routing import websocket_urlpatterns as capture_ws

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AllowedHostsOriginValidator(
        URLRouter(
            alert_ws + capture_ws
        )
    ),
})
