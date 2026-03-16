from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from rest_framework.exceptions import ValidationError
from .models import ChatList, Message, ImageMessage
from .serializers import  MessageSerializer, ImageMessageSerializer, InboxSerializer
from .permissions import IsSenderOrReadOnly, IsParticipantOrReadOnly
from notifications.utils import create_message_notification
   
 
# Message ViewSet
class InboxListView(viewsets.ModelViewSet):
    serializer_class = InboxSerializer
    permission_classes = [IsAuthenticated, IsParticipantOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        return ChatList.objects.filter(user1=user) | ChatList.objects.filter(user2=user)

    def perform_create(self, serializer):
        user1 = self.request.user
        user2 = serializer.validated_data['user2']

        # prevent duplicate chat
        if ChatList.objects.filter(Q(user1=user1, user2=user2) | Q(user1=user2, user2=user1)).exists():
            raise ValidationError("An inbox already exists between these users.")

        serializer.save(user1=user1, user2=user2)
        


# Updated Message ViewSet for nested routing
class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsSenderOrReadOnly]

    def get_queryset(self):
        inbox_id = self.kwargs.get('inbox_pk')
        return Message.objects.filter(inbox_id=inbox_id).order_by('created_at')

    def perform_create(self, serializer):
        inbox = get_object_or_404(ChatList, id=self.kwargs.get('inbox_pk'))
        receiver = inbox.user2 if inbox.user1 == self.request.user else inbox.user1
        share_url = f"{self.request.scheme}://{self.request.get_host()}/api/inboxes/{inbox.id}/messages/"

        message = serializer.save(
            sender=self.request.user, 
            receiver=receiver, 
            inbox=inbox
        )

        if receiver != self.request.user:
            create_message_notification(
                sender=self.request.user,
                receiver=receiver, 
                message_id=message.id,
                text="sent you a message",
                url=share_url
            )



    @action(detail=False, methods=['post'])
    def mark_read(self, request, inbox_pk=None):
        inbox = get_object_or_404(ChatList, id=inbox_pk)
        Message.objects.filter(
            inbox=inbox, receiver=request.user, is_read=False
        ).update(is_read=True)
        return Response({"message": "All messages marked as read"})




# ImageMessage ViewSet (optional)
class ImageMessageViewSet(viewsets.ModelViewSet):
    queryset = ImageMessage.objects.all()
    serializer_class = ImageMessageSerializer
    permission_classes = [IsAuthenticated, IsSenderOrReadOnly]

    def get_queryset(self):
        return self.queryset.filter(
            Q(message__inbox__user1=self.request.user) |
            Q(message__inbox__user2=self.request.user)
        ).select_related('message', 'message__sender')