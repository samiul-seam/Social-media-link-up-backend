from rest_framework import viewsets
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from .models import Post, PostMedia, Like, Comment, Reply, CommentLike, ReplyLike
from accounts.models import Follow
from .serializers import PostSerializer, PostMediaSerializer, LikeSerializer, CommentSerializer, ReplySerializer, CommentLikeSerializer, ReplyLikeSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from .permissions import IsOwnerOrAdminOrReadOnly
from notifications.utils import create_notification
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from django.db.models import Count


# Post ViewSet
class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly]
    filter_backends = [SearchFilter, DjangoFilterBackend]

    search_fields = [
        'caption',            
        'user__first_name',  
        'user__last_name',  
        'mood_status',      
    ]

    def get_queryset(self):
        user = self.request.user
        from django.db.models import Q

        user_id = self.request.query_params.get('user', None)
        if user_id:
            return Post.objects.filter(
                user_id=user_id,
                status='public'
            ).order_by('-created_at')

        queryset = Post.objects.filter(
            Q(status="public") |
            Q(status="followers", user__followers__follower=user)
        ).distinct()

        if self.action == "list":
            liked_posts = Like.objects.filter(user=user).values_list("post_id", flat=True)
            return (
                queryset
                .exclude(id__in=liked_posts)
                .exclude(user=user)
                .distinct()
                .order_by("?")
            )

        return queryset.order_by("-created_at")


    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # Own posts
    @action(detail=False, methods=["get"])
    def my_posts(self, request):
        user = request.user
        own_posts = Post.objects.filter(user=user).order_by("-created_at")
        serializer = self.get_serializer(own_posts, many=True)
        return Response(serializer.data)
    
    # share post
    @action(detail=True, methods=["get"])
    def share(self, request, pk=None):
        post = self.get_object()  
        share_url = f"{request.scheme}://{request.get_host()}/api/posts/{post.id}/"
        return Response({"share_url": share_url})
    
    @action(detail=False, methods=["get"])
    def user_posts(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response([])
        posts = Post.objects.filter(
            user_id=user_id,
            status='public'
        ).order_by('-created_at')
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)


# for # uses
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trending_moods(request):
    trends = (
        Post.objects
        .exclude(mood_status__isnull=True)
        .exclude(mood_status='')
        .values('mood_status')
        .annotate(count=Count('mood_status'))
        .order_by('-count')[:7]
    )
    return Response([f"#{t['mood_status']}" for t in trends])



# PostMedia ViewSet
class PostMediaViewSet(viewsets.ModelViewSet):
    serializer_class = PostMediaSerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly]

    def get_queryset(self):
        post_id = self.kwargs.get('post_pk')
        return PostMedia.objects.filter(post=post_id)

    def perform_create(self, serializer):
        post_id = self.kwargs.get('post_pk')
        post = get_object_or_404(Post, id=post_id)
        serializer.save(post=post)



# Like ViewSet
class LikeViewSet(viewsets.ModelViewSet):
    serializer_class = LikeSerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly]

    def get_queryset(self):
        post_id = self.kwargs.get('post_pk')
        return Like.objects.filter(post_id=post_id).select_related("user", "post")

    def perform_create(self, serializer):
        user = self.request.user
        post_id = self.kwargs.get('post_pk')
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise ValidationError("Post not found")

        exists = Like.objects.filter(user=user, post=post).exists()

        if exists:
            raise ValidationError("You have already Liked this post")

        share_url = f"{self.request.scheme}://{self.request.get_host()}/api/posts/{post.id}/"
        like = serializer.save(user=user, post=post)
        post = like.post

        if post.user != user:
            create_notification(
                sender=self.request.user,
                receiver=post.user,
                notification_type="like",
                post_id=post.id,
                text="liked your post",
                url=share_url
            )



# Comment ViewSet
class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly]

    def get_queryset(self):
        post_id = self.kwargs.get('post_pk')
        return Comment.objects.filter(
            post_id=post_id
        ).select_related(
            "user", "post"
        ).annotate(
            like_count=Count('likes')  # ← add
        ).order_by("created_at")

    def perform_create(self, serializer):
        post_id = self.kwargs.get('post_pk')
        post = get_object_or_404(Post, id=post_id)
        share_url = f"{self.request.scheme}://{self.request.get_host()}/api/posts/{post.id}/"

        comment = serializer.save(user=self.request.user, post=post)

        if post.user != self.request.user:
            create_notification(
                sender=self.request.user,
                receiver=post.user,
                notification_type="comment",
                post_id=post.id,
                text="commented on your post",
                url=share_url
            )


class ReplyViewSet(viewsets.ModelViewSet):
    serializer_class = ReplySerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly]

    def get_queryset(self):
        comment_id = self.kwargs.get('comment_pk')
        return Reply.objects.filter(comment_id=comment_id).annotate(
            like_count=Count('likes')
        ).order_by('created_at')

    def perform_create(self, serializer):
        comment_id = self.kwargs.get('comment_pk')
        comment = get_object_or_404(Comment, id=comment_id)
        post_id = self.kwargs.get('post_pk')
        post = get_object_or_404(Post, id=post_id)

        share_url = f"{self.request.scheme}://{self.request.get_host()}/api/posts/{post_id}/comments/{comment.id}/"

        reply = serializer.save(
            user=self.request.user,
            comment=comment
        )

        if comment.user != self.request.user:
            create_notification(
                sender=self.request.user,
                receiver=comment.user,
                notification_type="reply",
                post_id=comment.post.id,
                text="replied to your comment",
                url=share_url
            )


class CommentLikeViewSet(viewsets.ModelViewSet):
    serializer_class = CommentLikeSerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly]

    def get_queryset(self):
        comment_id = self.kwargs.get('comment_pk')
        return CommentLike.objects.filter(comment_id=comment_id).select_related("user", "comment")

    def perform_create(self, serializer):
        user = self.request.user
        comment_id = self.kwargs.get('comment_pk')

        try:
            comment = Comment.objects.select_related('user', 'post').get(id=comment_id)
        except Comment.DoesNotExist:
            raise ValidationError("Comment not found")

        if CommentLike.objects.filter(user=user, comment=comment).exists():
            raise ValidationError("You have already liked this comment")

        like = serializer.save(user=user, comment=comment)

        if comment.user != user:
            share_url = f"{self.request.scheme}://{self.request.get_host()}/api/posts/{comment.post.id}/"
            create_notification(
                sender=user,
                receiver=comment.user,
                notification_type="like",
                post_id=comment.post.id,
                text="liked your comment",
                url=share_url
            )


class ReplyLikeViewSet(viewsets.ModelViewSet):
    serializer_class = ReplyLikeSerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly]

    def get_queryset(self):
        reply_id = self.kwargs.get('reply_pk')
        return ReplyLike.objects.filter(reply_id=reply_id).select_related("user", "reply")

    def perform_create(self, serializer):
        user = self.request.user
        reply_id = self.kwargs.get('reply_pk')

        try:
            reply = Reply.objects.select_related('user', 'comment__post').get(id=reply_id)
        except Reply.DoesNotExist:
            raise ValidationError("Reply not found")

        if ReplyLike.objects.filter(user=user, reply=reply).exists():
            raise ValidationError("You have already liked this reply")

        like = serializer.save(user=user, reply=reply)

        if reply.user != user:
            share_url = f"{self.request.scheme}://{self.request.get_host()}/api/posts/{reply.comment.post.id}/"
            create_notification(
                sender=user,
                receiver=reply.user,
                notification_type="like",
                post_id=reply.comment.post.id,
                text="liked your reply",
                url=share_url
            )