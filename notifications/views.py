from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from .serializers import NotificationSerializer, MessageNotificationSerializer
from notifications.models import Notification, MessageNotification
from rest_framework.permissions import IsAuthenticated



class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch"]

    def get_queryset(self):
        return Notification.objects.filter(receiver=self.request.user).select_related("sender")

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    @action(detail=True, methods=["patch"])
    def mark_read(self, request, pk=None):

        notification = self.get_object()
        notification.is_read = True
        notification.save()

        return Response({"message": "Notification marked as read"})



class MessageNotificationViewSet(viewsets.ModelViewSet):

    serializer_class = MessageNotificationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch"]

    def get_queryset(self):
        return MessageNotification.objects.filter(
            receiver=self.request.user
        ).select_related("sender")

    def perform_create(self, serializer):
       serializer.save(sender=self.request.user)
        

    @action(detail=True, methods=["patch"])
    def mark_read(self, request, pk=None):

        notification = self.get_object()
        notification.is_read = True
        notification.save()

        return Response({"message": "Message notification marked as read"})