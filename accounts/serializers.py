from rest_framework import serializers
from .models import Follow
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        ref_name = 'CustomUser'
        fields = [
            "id", "email", "password",
            "first_name", "last_name",
            "bio", "profile_picture"
        ]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
 
 
class AllUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'bio', 'full_name', 'email', 'profile_picture', 'followers_count', 'following_count']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_profile_picture(self, obj):
        return obj.profile_picture.url if obj.profile_picture else None

    def get_followers_count(self, obj):
        if hasattr(obj, '_prefetched_objects_cache') and 'followers' in obj._prefetched_objects_cache:
            return len(obj.followers.all())
        return obj.followers.count()

    def get_following_count(self, obj):
        if hasattr(obj, '_prefetched_objects_cache') and 'following' in obj._prefetched_objects_cache:
            return len(obj.following.all())
        return obj.following.count()


class UserSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "email",
            "first_name", "last_name",
            "bio", "profile_picture",
            "followers_count", "following_count",
        ]

    def get_username(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_followers_count(self, obj):
        if hasattr(obj, '_prefetched_objects_cache') and 'followers' in obj._prefetched_objects_cache:
            return len(obj.followers.all())
        return obj.followers.count()

    def get_following_count(self, obj):
        if hasattr(obj, '_prefetched_objects_cache') and 'following' in obj._prefetched_objects_cache:
            return len(obj.following.all())
        return obj.following.count()

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['profile_picture'] = instance.profile_picture.url if instance.profile_picture else None
        return rep


class FollowSerializer(serializers.ModelSerializer):
    follower = serializers.ReadOnlyField(source="follower.id")
    follower_detail = serializers.SerializerMethodField()
    following_detail = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = [
            "id", "follower", "following",
            "follower_detail", "following_detail",
            "created_at",
        ]

    def validate_following(self, value):
       if self.context['request'].user == value:
           raise serializers.ValidationError("You cannot follow yourself.")
       return value

    def get_follower_detail(self, obj):
        return {
            "id": obj.follower.id,
            "full_name": f"{obj.follower.first_name} {obj.follower.last_name}",
            "profile_picture": obj.follower.profile_picture.url if obj.follower.profile_picture else None,
        }

    def get_following_detail(self, obj):
        return {
            "id": obj.following.id,
            "full_name": f"{obj.following.first_name} {obj.following.last_name}",
            "profile_picture": obj.following.profile_picture.url if obj.following.profile_picture else None,
        }