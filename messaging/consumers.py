import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatList, Message
from notifications.utils import create_message_notification

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope['user']
        self.room_group_name = None
        self.in_group = False

        if not self.user.is_authenticated:
            await self.close()
            return

        self.inbox_id = self.scope['url_route']['kwargs']['inbox_id']
        self.room_group_name = f'chat_{self.inbox_id}'

        is_participant = await self.is_participant()
        if not is_participant:
            await self.close()
            return

        # Accept first — never let a Redis failure cause rejection
        await self.accept()

        try:
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            self.in_group = True
        except Exception as e:
            logger.error(f"ChatConsumer: Redis group_add failed: {e}")

    async def disconnect(self, close_code):
        if self.in_group and self.room_group_name:
            try:
                await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            except Exception as e:
                logger.warning(f"ChatConsumer disconnect error: {e}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        content = data.get('message', '').strip()

        if not content:
            return

        message, receiver = await self.save_message(content)

        try:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message_id': message.id,
                    'message': message.message,
                    'sender_id': self.user.id,
                    'sender_name': self.user.full_name,
                    'receiver_id': receiver.id,
                    'created_at': str(message.created_at),
                    'is_read': message.is_read,
                }
            )

            receiver_unread = await self.get_unread_count(receiver)

            await self.channel_layer.group_send(f'inbox_{self.user.id}', {
                'type': 'inbox_update',
                'chat_id': int(self.inbox_id),
                'message': message.message,
                'sender_id': self.user.id,
                'created_at': str(message.created_at),
                'unread_count': 0,
            })
            await self.channel_layer.group_send(f'inbox_{receiver.id}', {
                'type': 'inbox_update',
                'chat_id': int(self.inbox_id),
                'message': message.message,
                'sender_id': self.user.id,
                'created_at': str(message.created_at),
                'unread_count': receiver_unread,
            })

        except Exception as e:
            logger.warning(f"ChatConsumer receive channel error: {e}")

    async def chat_message(self, event):
        try:
            await self.send(text_data=json.dumps({
                'message_id': event['message_id'],
                'message': event['message'],
                'sender_id': event['sender_id'],
                'sender_name': event['sender_name'],
                'receiver_id': event['receiver_id'],
                'created_at': event['created_at'],
                'is_read': event['is_read'],
            }))
        except Exception as e:
            logger.warning(f"ChatConsumer chat_message error: {e}")

    @database_sync_to_async
    def is_participant(self):
        return (
            ChatList.objects.filter(id=self.inbox_id, user1=self.user).exists() or
            ChatList.objects.filter(id=self.inbox_id, user2=self.user).exists()
        )

    @database_sync_to_async
    def save_message(self, content):
        inbox = ChatList.objects.get(id=self.inbox_id)
        receiver = inbox.user2 if inbox.user1 == self.user else inbox.user1

        message = Message.objects.create(
            inbox=inbox,
            sender=self.user,
            receiver=receiver,
            message=content,
        )
        inbox.save()

        if receiver != self.user:
            create_message_notification(
                sender=self.user,
                receiver=receiver,
                message_id=message.id,
                text="sent you a message",
                url=f"/api/inboxes/{inbox.id}/messages/"
            )

        return message, receiver

    @database_sync_to_async
    def get_unread_count(self, user):
        inbox = ChatList.objects.get(id=self.inbox_id)
        return inbox.messages.filter(is_read=False).exclude(sender=user).count()


class InboxConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope['user']
        self.group_name = None
        self.in_group = False

        if not self.user.is_authenticated:
            await self.close()
            return

        self.group_name = f'inbox_{self.user.id}'

        # Accept first — never let a Redis failure cause rejection
        await self.accept()

        try:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            self.in_group = True
        except Exception as e:
            logger.error(f"InboxConsumer: Redis group_add failed: {e}")

    async def disconnect(self, close_code):
        if self.in_group and self.group_name:
            try:
                await self.channel_layer.group_discard(self.group_name, self.channel_name)
            except Exception as e:
                logger.warning(f"InboxConsumer disconnect error: {e}")

    async def inbox_update(self, event):
        try:
            await self.send(text_data=json.dumps({
                'chat_id': event['chat_id'],
                'message': event['message'],
                'sender_id': event['sender_id'],
                'created_at': event['created_at'],
                'unread_count': event.get('unread_count', 0),
            }))
        except Exception as e:
            logger.warning(f"InboxConsumer inbox_update error: {e}")