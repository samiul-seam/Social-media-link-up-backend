from rest_framework import serializers
from .models import User, Follow


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        ref_name = 'CustomUser'
        fields = [
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "bio",
            "profile_picture"
        ]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
    
    
 
class UserSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "bio",
            "profile_picture"
        ]

    def get_username(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    


class FollowSerializer(serializers.ModelSerializer):
    follower = serializers.ReadOnlyField(source="follower.id") 
    following_username = serializers.CharField(source="following.username", read_only=True)
    following_profile = serializers.ImageField(source="following.profile_picture", read_only=True)

    class Meta:
        model = Follow
        fields = [
            "id",
            "follower",
            "following",
            "following_username",
            "following_profile",
            "created_at",
        ]

