import logging
from .models import Notification, MessageNotification
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


def create_notification(sender, receiver, notification_type, text, url=None, post_id=None):
    notification = Notification.objects.create(
        sender=sender,
        receiver=receiver,
        notification_type=notification_type,
        post_id=post_id,
        text=text,
        url=url,
    )

    try:
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'notifications_{receiver.id}',
                {
                    'type': 'send_notification',
                    'notification_id': notification.id,
                    'notification_type': notification_type,
                    'sender_id': sender.id,
                    'sender_name': sender.full_name,
                    'post_id': post_id,
                    'text': text,
                    'url': url,
                    'created_at': str(notification.created_at),
                }
            )
    except Exception as e:
        logger.warning(f"Failed to send real-time notification via Channels: {e}")

    return notification


def create_message_notification(sender, receiver, message_id, text, url=None):
    notification = MessageNotification.objects.create(
        sender=sender,
        receiver=receiver,
        message_id=message_id,
        text=text,
        url=url,
    )

    try:
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'notifications_{receiver.id}',
                {
                    'type': 'send_message_notification',
                    'notification_id': notification.id,
                    'sender_id': sender.id,
                    'sender_name': sender.full_name,
                    'message_id': message_id,
                    'text': text,
                    'url': url,
                    'created_at': str(notification.created_at),
                }
            )
    except Exception as e:
        logger.warning(f"Failed to send real-time message notification via Channels: {e}")

    return notification