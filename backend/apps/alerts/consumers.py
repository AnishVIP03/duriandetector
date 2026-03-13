"""
WebSocket consumer for real-time alert notifications.

Uses Django Channels to push new IDS alerts to connected clients
in real time. All authenticated users join the 'alerts' group and
receive alerts as they are created by the detection engine.

Message format sent to clients:
    { "id": int, "severity": str, "src_ip": str, "alert_type": str, ... }
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class AlertConsumer(AsyncWebsocketConsumer):
    """
    Async WebSocket consumer for broadcasting IDS alerts.

    Clients connect to ws://<host>/ws/alerts/ and automatically
    join the 'alerts' channel group. When a new alert is created,
    the backend sends a message to this group, and all connected
    clients receive the alert data in real time.
    """

    async def connect(self):
        """Accept the WebSocket connection and join the alerts broadcast group."""
        self.group_name = 'alerts'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """Leave the alerts broadcast group on disconnect."""
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """Handle incoming messages from the client (currently unused — server-push only)."""
        pass

    async def alert_message(self, event):
        """
        Handle alert broadcast events from the channel layer.

        Called when the backend sends an alert via:
            channel_layer.group_send('alerts', {'type': 'alert_message', 'data': {...}})

        Forwards the alert data as JSON to the connected WebSocket client.
        """
        await self.send(text_data=json.dumps(event['data']))
