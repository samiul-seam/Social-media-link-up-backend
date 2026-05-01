from django.urls import re_path
from messaging.consumers import ChatConsumer, InboxConsumer
from notifications.consumers import NotificationConsumer

websocket_urlpatterns = [
    re_path(r'^ws/chat/(?P<inbox_id>\d+)/$', ChatConsumer.as_asgi()),
    re_path(r'^ws/inbox/$', InboxConsumer.as_asgi()),
    re_path(r'^ws/notifications/$', NotificationConsumer.as_asgi()),
]