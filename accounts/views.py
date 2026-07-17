from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from .models import Follow, User
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import FollowSerializer, UserSerializer, AllUserSerializer
from notifications.utils import create_notification
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter  
from django.db.models.functions import Concat
from django.db.models import Q, Value


from django.db.models import Q, Value
from django.db.models.functions import Concat

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AllUserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ['first_name', 'last_name', 'email']

    def get_queryset(self):
        queryset = User.objects.exclude(
            id=self.request.user.id
        ).prefetch_related('followers', 'following')

        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )

        return queryset

class FollowViewSet(viewsets.ModelViewSet):
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ['following__first_name', 'following__last_name']
    filterset_fields = ['following']

    def get_queryset(self):
        return Follow.objects.filter(follower=self.request.user)

    def perform_create(self, serializer):
        followee = serializer.validated_data["following"]

        # prevent duplicate follow
        if Follow.objects.filter(follower=self.request.user, following=followee).exists():
            raise ValidationError("You are already following this user.")

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
        user_id = request.query_params.get('user_id', None)
        target_user = User.objects.get(id=user_id) if user_id else request.user

        users = User.objects.filter(
            following__following=target_user
        ).prefetch_related('followers', 'following').distinct()

        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


    @action(detail=False, methods=["get"])
    def following(self, request):
        user_id = request.query_params.get('user_id', None)
        target_user = User.objects.get(id=user_id) if user_id else request.user

        users = User.objects.filter(
            followers__follower=target_user
        ).prefetch_related('followers', 'following').distinct()

        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)