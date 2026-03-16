
from .models import Notification, MessageNotification


def create_notification(sender, receiver, notification_type, post_id=None, text="", url=""):
    
    if sender == receiver:
        return

    Notification.objects.create(
        sender=sender,
        receiver=receiver,
        notification_type=notification_type,
        post_id=post_id,
        text=text,
        url=url
    )


def create_message_notification(sender, receiver, message_id, text="", url=""):

    if sender == receiver:
        return

    MessageNotification.objects.create(
        sender=sender,
        receiver=receiver,
        message_id=message_id,
        text=text,
        url=url
    )