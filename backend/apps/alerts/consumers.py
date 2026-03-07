import json
from channels.generic.websocket import AsyncWebsocketConsumer


class AlertConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'alerts'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        pass

    async def alert_message(self, event):
        await self.send(text_data=json.dumps(event['data']))
