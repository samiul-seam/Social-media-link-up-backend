from rest_framework import serializers
from .models import Post, PostMedia, Like, Comment, Reply
import mimetypes
from django.urls import reverse


# Comment Serializer
class ReplySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Reply
        fields = ['id', 'user', 'user_name', 'comment', 'content', 'created_at']
        read_only_fields = ['user', 'comment']


class CommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    replies = ReplySerializer(many=True, read_only=True)  

    class Meta:
        model = Comment
        fields = ['id', 'user', 'user_name',  'content', 'replies', 'created_at']
        read_only_fields = ['user' ]



# PostMedia Serializer
class PostMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostMedia
        fields = ['id', 'file']
        read_only_fields = ['post']



# Like Serializer
class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'user', 'post', 'created_at']
        read_only_fields = ['user', 'post']




# Post Serializer
class PostSerializer(serializers.ModelSerializer):
    media = PostMediaSerializer(many=True, read_only=True)
    likes = LikeSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    media_files = serializers.ListField(
        child=serializers.FileField(max_length=1000000, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False
    )

    class Meta:
        model = Post
        fields = [
            'id', 'user', 'user_name', 'caption', 'media', 
            'media_files', 'likes', 'comments',
            'created_at', 'updated_at', 'status'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']


    def create(self, validated_data):
        media_files = validated_data.pop('media_files', [])
        post = Post.objects.create(**validated_data)

        for file in media_files:
            mime_type, _ = mimetypes.guess_type(file.name)
            media_type = 'video' if mime_type and mime_type.startswith('video') else 'image'
            PostMedia.objects.create(post=post, media=file, media_type=media_type)

        return post

    def update(self, instance, validated_data):
        media_files = validated_data.pop('media_files', None)
        instance.caption = validated_data.get('caption', instance.caption)
        instance.status = validated_data.get('status', instance.status)
        instance.save()

        if media_files:
            for file in media_files:
                mime_type, _ = mimetypes.guess_type(file.name)
                media_type = 'video' if mime_type and mime_type.startswith('video') else 'image'
                PostMedia.objects.create(post=instance, media=file, media_type=media_type)

        return instance