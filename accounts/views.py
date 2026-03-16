from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from .models import Follow, User
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import FollowSerializer
from notifications.utils import create_notification  


class FollowViewSet(viewsets.ModelViewSet):
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # shows all users the current user is following
        return Follow.objects.filter(follower=self.request.user)

    def perform_create(self, serializer):
        followee = serializer.validated_data["following"]

        # prevent duplicate follow
        if Follow.objects.filter(follower=self.request.user, following=followee).exists():
            raise ValidationError("You are already following this user.")

        # save follow relation
        follow_instance = serializer.save(follower=self.request.user)

        # create notification
        create_notification(
            sender=self.request.user,
            receiver=followee,
            notification_type="follow",
            text="started following you"
        )

    @action(detail=False, methods=["get"])
    def followers(self, request):
        user = request.user
        followers = user.followers.all() 
        serializer = self.get_serializer(followers, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def following(self, request):
        user = request.user
        following = user.following.all()
        serializer = self.get_serializer(following, many=True)
        return Response(serializer.data)