from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q, Subquery, OuterRef, F
from .models import ChatList, Message, ImageMessage, InboxDeletion
from .serializers import MessageSerializer, ImageMessageSerializer, InboxSerializer
from .permissions import IsSenderOrReadOnly, IsParticipantOrReadOnly
from notifications.utils import create_message_notification
from rest_framework import status


class InboxListView(viewsets.ModelViewSet):
    serializer_class = InboxSerializer
    permission_classes = [IsAuthenticated, IsParticipantOrReadOnly]

    def get_queryset(self):
        user = self.request.user

        deletion_time = InboxDeletion.objects.filter(
            inbox=OuterRef('pk'), user=user
        ).values('deleted_at')[:1]

        return (
            ChatList.objects
            .filter(Q(user1=user) | Q(user2=user))
            .annotate(user_deleted_at=Subquery(deletion_time))
            .filter(
                Q(user_deleted_at__isnull=True) |
                Q(messages__created_at__gt=F('user_deleted_at'))
            )
            .prefetch_related('messages')
            .select_related('user1', 'user2')
            .distinct()
            .order_by('-updated_at')
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user1 = request.user
        user2 = serializer.validated_data['user2']

        existing = ChatList.objects.filter(
            Q(user1=user1, user2=user2) | Q(user1=user2, user2=user1)
        ).first()

        if existing:
            return Response(self.get_serializer(existing).data, status=status.HTTP_200_OK)

        instance = serializer.save(user1=user1)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        inbox = self.get_object()
        InboxDeletion.objects.get_or_create(inbox=inbox, user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsSenderOrReadOnly]

    def get_queryset(self):
        inbox_id = self.kwargs.get('inbox_pk')
        user = self.request.user

        try:
            deletion = InboxDeletion.objects.get(inbox_id=inbox_id, user=user)
            return Message.objects.filter(
                inbox_id=inbox_id,
                created_at__gt=deletion.deleted_at
            ).order_by('-created_at')
        except InboxDeletion.DoesNotExist:
            return Message.objects.filter(inbox_id=inbox_id).order_by('-created_at')

    def perform_create(self, serializer):
        inbox = get_object_or_404(ChatList, id=self.kwargs.get('inbox_pk'))
        receiver = inbox.user2 if inbox.user1 == self.request.user else inbox.user1

        # restore inbox only for sender
        InboxDeletion.objects.filter(inbox=inbox, user=self.request.user).delete()

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

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.message = request.data.get('message', instance.message)
        instance.is_edited = True
        instance.save()
        return Response(MessageSerializer(instance).data)

    @action(detail=False, methods=['post'])
    def mark_read(self, request, inbox_pk=None):
        inbox = get_object_or_404(ChatList, id=inbox_pk)
        Message.objects.filter(
            inbox=inbox, receiver=request.user, is_read=False
        ).update(is_read=True)
        return Response({"message": "All messages marked as read"})


class ImageMessageViewSet(viewsets.ModelViewSet):
    queryset = ImageMessage.objects.all()
    serializer_class = ImageMessageSerializer
    permission_classes = [IsAuthenticated, IsSenderOrReadOnly]

    def get_queryset(self):
        return self.queryset.filter(
            Q(message__inbox__user1=self.request.user) |
            Q(message__inbox__user2=self.request.user)
        ).select_related('message', 'message__sender')