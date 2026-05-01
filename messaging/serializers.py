from rest_framework import serializers
from .models import ChatList, Message, ImageMessage
from django.contrib.auth import get_user_model
User = get_user_model()

# ImageMessage Serializer
class ImageMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageMessage
        fields = ['id', "message", 'image', 'uploaded_at']


class ProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'full_name', 'profile_picture']

    def get_profile_picture(self, obj):
        return obj.profile_picture.url if obj.profile_picture else None


class InboxSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatList
        fields = ['id', 'user2', 'other_user', 'last_message', 'unread_count', 'updated_at']

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request:
            return 0
        return obj.messages.filter(is_read=False).exclude(sender=request.user).count()

    def get_other_user(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        other = obj.user2 if obj.user1 == user else obj.user1
        return ProfileSerializer(other, context=self.context).data

    def get_last_message(self, obj):
        last = obj.messages.order_by('-created_at').first()
        if not last:
            return None
        return {
            "id": last.id,
            "message": last.message,
            "created_at": last.created_at,
            "is_read": last.is_read,
            "sender_id": last.sender_id,
        }

 

# Message Serializer
class MessageSerializer(serializers.ModelSerializer):
    images = ImageMessageSerializer(many=True, required=False)

    sender_profile = ProfileSerializer(read_only=True)
    receiver_profile = ProfileSerializer(read_only=True)

    class Meta:
        model = Message
        fields = [
            'id',  
            'message', 'sender_profile', 'receiver_profile', 'images', 'created_at', 'is_read'
        ]
        read_only_fields = ['created_at', 'is_read']

        def create(self, validated_data):
            images_data = validated_data.pop("images", [])
            message = Message.objects.create(**validated_data)
            for image_data in images_data:
                ImageMessage.objects.create(message=message, **image_data)
            return message

