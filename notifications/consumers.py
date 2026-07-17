import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope['user']
        self.group_name = None

        if not self.user.is_authenticated:
            await self.close()
            return

        # Each user has their own personal notification channel
        self.group_name = f'notifications_{self.user.id}'

        try:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        except Exception as e:
            logger.error(f"NotificationConsumer connect error: {e}")
            await self.close()

    async def disconnect(self, close_code):
        if self.group_name:
            try:
                await self.channel_layer.group_discard(self.group_name, self.channel_name)
            except Exception as e:
                logger.warning(f"NotificationConsumer disconnect error: {e}")

    # Handler for post/like/comment/follow/reply notifications
    async def send_notification(self, event):
        try:
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
        except Exception as e:
            logger.warning(f"NotificationConsumer send_notification error: {e}")

    # Handler for message notifications
    async def send_message_notification(self, event):
        try:
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
        except Exception as e:
            logger.warning(f"NotificationConsumer send_message_notification error: {e}")