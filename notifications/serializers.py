from rest_framework import serializers
from .models import Notification, MessageNotification


class NotificationSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.first_name", read_only=True)

    sender_profile = serializers.ImageField(source="sender.profile_picture", read_only=True)


    class Meta:
        model = Notification
        fields = [
            "id",
            "sender",
            "sender_name",
            "sender_profile",
            "receiver",
            "notification_type",
            "post_id",
            "text",
            "url",
            "is_read",
            "created_at",
        ]
        read_only_fields = ["sender", "created_at"]


class MessageNotificationSerializer(serializers.ModelSerializer):

    sender_name = serializers.CharField(
        source="sender.first_name",
        read_only=True
    )

    class Meta:
        model = MessageNotification
        fields = [
            "id",
            "sender",
            "sender_name", 
            "receiver",
            "message_id",
            "text",
            "url",
            "is_read",
            "created_at",
        ]
        read_only_fields = ["sender", "created_at"]