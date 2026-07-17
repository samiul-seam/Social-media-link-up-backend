from rest_framework import serializers
from .models import Post, PostMedia, Like, Comment, Reply, CommentLike, ReplyLike
import mimetypes
from django.urls import reverse


class CommentLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentLike
        fields = ['id', 'user', 'comment', 'created_at']
        read_only_fields = ['id', 'user', 'comment', 'created_at']


class ReplyLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReplyLike
        fields = ['id', 'user', 'reply', 'created_at']
        read_only_fields = ['id', 'user', 'reply', 'created_at']


class ReplySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_profile = serializers.ImageField(source='user.profile_picture', read_only=True)
    reply_like = ReplyLikeSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    like_id = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()

    class Meta:
        model = Reply
        fields = ['id', 'user', 'reply_like', 'user_profile', 'user_name', 'comment', 'content', 'created_at' , 'is_liked', 'like_id', 'like_count']
        read_only_fields = ['user', 'comment','is_liked', 'like_id', 'like_count']

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if hasattr(obj, '_prefetched_objects_cache') and 'likes' in obj._prefetched_objects_cache:
                return any(like.user_id == request.user.id for like in obj.likes.all())
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_like_id(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if hasattr(obj, '_prefetched_objects_cache') and 'likes' in obj._prefetched_objects_cache:
                for like in obj.likes.all():
                    if like.user_id == request.user.id:
                        return like.id
                return None
            like = obj.likes.filter(user=request.user).first()
            return like.id if like else None
        return None

    def get_like_count(self, obj):
        if hasattr(obj, '_prefetched_objects_cache') and 'likes' in obj._prefetched_objects_cache:
            return len(obj.likes.all())
        if hasattr(obj, 'like_count'):
            return obj.like_count
        return obj.likes.count()

 
class CommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_profile = serializers.ImageField(source='user.profile_picture', read_only=True)
    replies = ReplySerializer(many=True, read_only=True)  
    comment_like = CommentLikeSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    like_id = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'user', 'comment_like', 'user_name', 'user_profile', 'content', 'replies', 'created_at', 'updated_at', 'is_liked', 'like_id', 'like_count']
        read_only_fields = ['user','is_liked','like_id', 'like_count' ]

    def update(self, instance, validated_data):
        instance.content = validated_data.get('content', instance.content)
        instance.save()
        return instance
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if hasattr(obj, '_prefetched_objects_cache') and 'likes' in obj._prefetched_objects_cache:
                return any(like.user_id == request.user.id for like in obj.likes.all())
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_like_id(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if hasattr(obj, '_prefetched_objects_cache') and 'likes' in obj._prefetched_objects_cache:
                for like in obj.likes.all():
                    if like.user_id == request.user.id:
                        return like.id
                return None
            like = obj.likes.filter(user=request.user).first()
            return like.id if like else None
        return None

    def get_like_count(self, obj):
        if hasattr(obj, '_prefetched_objects_cache') and 'likes' in obj._prefetched_objects_cache:
            return len(obj.likes.all())
        if hasattr(obj, 'like_count'):
            return obj.like_count
        return obj.likes.count()


# PostMedia Serializer
class PostMediaSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        return obj.image.url if obj.image else None

    class Meta:
        model = PostMedia
        fields = ['id', 'image']
        read_only_fields = ['post']


# Like Serializer
class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'user', 'post', 'created_at']
        read_only_fields = ['user', 'post']

 

# Post Serializer
class PostSerializer(serializers.ModelSerializer):
    images = PostMediaSerializer(many=True, required=False)
    likes = LikeSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    like_id = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    profile_picture = serializers.SerializerMethodField()

    def get_profile_picture(self, obj):
        return obj.user.profile_picture.url if obj.user.profile_picture else None

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if hasattr(obj, '_prefetched_objects_cache') and 'likes' in obj._prefetched_objects_cache:
                return any(like.user_id == request.user.id for like in obj.likes.all())
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_like_id(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if hasattr(obj, '_prefetched_objects_cache') and 'likes' in obj._prefetched_objects_cache:
                for like in obj.likes.all():
                    if like.user_id == request.user.id:
                        return like.id
                return None
            like = obj.likes.filter(user=request.user).first()
            return like.id if like else None
        return None

    class Meta:
        model = Post
        fields = [
            'id', 'user', 'user_name', 'profile_picture', 'caption',
            'images', 'likes', 'comments',
            'created_at', 'updated_at',
            'status', 'mood_status', 'is_liked', 'like_id'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'is_liked', 'like_id']

    def create(self, validated_data):
        request = self.context.get('request')
        post = Post.objects.create(**validated_data)

        files = request.FILES.getlist('images')
        for file in files:
            PostMedia.objects.create(post=post, image=file)

        return post

    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        instance.caption = validated_data.get('caption', instance.caption)
        instance.status = validated_data.get('status', instance.status)
        instance.mood_status = validated_data.get('mood_status', instance.mood_status)
        instance.save()

        files = request.FILES.getlist('images')
        if files:
            instance.images.all().delete() 
            for file in files:
                PostMedia.objects.create(post=instance, image=file)

        return instance