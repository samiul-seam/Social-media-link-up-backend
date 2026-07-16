from django.urls import path, include
from rest_framework import routers
from rest_framework_nested import routers as nested_routers
from posts.views import PostViewSet, CommentViewSet, LikeViewSet, PostMediaViewSet, ReplyViewSet, trending_moods, CommentLikeViewSet, ReplyLikeViewSet
from messaging.views import InboxListView, MessageViewSet
from notifications.views import NotificationViewSet, MessageNotificationViewSet
from accounts.views import FollowViewSet, UserViewSet


# Main router
router = routers.DefaultRouter()
router.register('posts', PostViewSet, basename='post')
router.register('users', UserViewSet, basename='users')
router.register('follows', FollowViewSet, basename='follows')
router.register('inboxes', InboxListView, basename='inbox')
router.register('notification', NotificationViewSet, basename='notification')
router.register('message_notification', MessageNotificationViewSet, basename='message-notification')


# Nested routers for posts
posts_router = nested_routers.NestedDefaultRouter(router, 'posts', lookup='post')
posts_router.register('comments', CommentViewSet, basename='post-comments')
posts_router.register('likes', LikeViewSet, basename='post-likes')
posts_router.register('images', PostMediaViewSet, basename='post-image')


comments_router = nested_routers.NestedDefaultRouter(posts_router, 'comments', lookup='comment')
comments_router.register('replies', ReplyViewSet, basename='comment-replies')
comments_router.register('likes', CommentLikeViewSet, basename='comment-likes')


replies_router = nested_routers.NestedDefaultRouter(comments_router, 'replies', lookup='reply')
replies_router.register('likes', ReplyLikeViewSet, basename='reply-likes')


# Nested router for messages inside inboxes
inbox_router = nested_routers.NestedDefaultRouter(router, 'inboxes', lookup='inbox')
inbox_router.register('messages', MessageViewSet, basename='inbox-messages')


urlpatterns = [
    path("", include(router.urls)),
    path("", include(posts_router.urls)),
    path("", include(comments_router.urls)),
    path("", include(replies_router.urls)),
    path("", include(inbox_router.urls)), 
    path('trending/', trending_moods),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('auth/', include('djoser.urls.authtoken')),
]