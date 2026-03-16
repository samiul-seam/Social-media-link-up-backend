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
    class Meta:
        model = User
        fields = ['id', 'username', 'profile_picture']


class InboxSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChatList
        fields = ['id', 'user2', 'updated_at']



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

