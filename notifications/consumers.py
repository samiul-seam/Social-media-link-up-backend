import json
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        # Each user has their own personal notification channel
        self.group_name = f'notifications_{self.user.id}'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Handler for post/like/comment/follow/reply notifications
    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification_id': event['notification_id'],
            'notification_type': event['notification_type'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'post_id': event.get('post_id'),
            'text': event['text'],
            'url': event.get('url'),
            'is_read': False,
            'created_at': event['created_at'],
        }))

    # Handler for message notifications
    async def send_message_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_notification',
            'notification_id': event['notification_id'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'message_id': event['message_id'],
            'text': event['text'],
            'url': event.get('url'),
            'is_read': False,
            'created_at': event['created_at'],
        }))