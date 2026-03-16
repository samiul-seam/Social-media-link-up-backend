from rest_framework import viewsets
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Post, PostMedia, Like, Comment, Reply
from accounts.models import Follow
from .serializers import PostSerializer, PostMediaSerializer, LikeSerializer, CommentSerializer, ReplySerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.exceptions import ValidationError
from .permissions import IsOwnerOrAdminOrReadOnly
from notifications.utils import create_notification
from .pagination import PostPagination


# Post ViewSet
class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly]
    pagination_class = PostPagination

    def get_queryset(self):
        user = self.request.user
        all_posts = Post.objects.all().order_by("-created_at")
        liked_post = Like.objects.filter(user=user).values_list("post_id", flat=True)
        visible_post_ids = []

        for post in all_posts:
            if post.status == "public":
                visible_post_ids.append(post.id)
            elif post.user == user:
                visible_post_ids.append(post.id)
            elif post.status == "friends":
                if Follow.objects.filter(follower=user, following=post.user).exists():
                    visible_post_ids.append(post.id)

        queryset = Post.objects.filter(id__in=visible_post_ids)
    
        if self.action == "list":
            liked_posts = Like.objects.filter(
                user=user
            ).values_list("post_id", flat=True)

            queryset = queryset.exclude(id__in=liked_posts)

        return queryset.order_by("?")[:10]


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
        return Comment.objects.filter(post_id=post_id).select_related("user", "post").order_by("created_at")

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
        return Reply.objects.filter(comment_id=comment_id).order_by('created_at')

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
