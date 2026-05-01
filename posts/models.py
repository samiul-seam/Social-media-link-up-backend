from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
User = get_user_model()
from cloudinary.models import CloudinaryField


# Create your models here.
class Post(models.Model):
    STATUS_CHOICES = (
        ("only_me", "Only Me"),
        ("followers", "Followers"),
        ("public", "Public"),
    )

    MOOD_STATUS = (
        ("happy",       "Happy"),
        ("excited",     "Excited"),
        ("thoughtful",  "Thoughtful"),
        ("grateful",    "Grateful"),
        ("motivated",   "Motivated"),
        ("relaxed",     "Relaxed"),
        ("sad",         "Sad"),
        ("frustrated",  "Frustrated"),
        ("creative",    "Creative"),
        ("tired",       "Tired"),
        ("in_love",     "In Love"),
        ("anxious",     "Anxious"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")

    caption = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="public")
    mood_status = models.CharField(max_length=15, choices=MOOD_STATUS, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.user.username}: {self.caption[:20]}"
    

class PostMedia(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")
    image = CloudinaryField('image', blank=True, null=True)
 

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')



class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(
        "posts.Post",
        on_delete=models.CASCADE,
        related_name="comments"
    )
    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}: {self.content}"
    

class Reply(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, related_name='replies'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} -> {self.comment.id}: {self.content}"
    

class CommentLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'comment')


class ReplyLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reply = models.ForeignKey(Reply, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'reply')