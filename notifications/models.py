from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Notification(models.Model):

    NOTIFICATION_TYPES = (
        ("like", "Like"),
        ("comment", "Comment"),
        ("follow", "Follow"),
        ("reply", "Reply")
    )
    sender = models.ForeignKey(User,on_delete=models.CASCADE,related_name="sent_notifications")
    
    receiver = models.ForeignKey(User,on_delete=models.CASCADE,related_name="notifications")

    notification_type = models.CharField(max_length=20,choices=NOTIFICATION_TYPES)
    post_id = models.IntegerField(null=True, blank=True)
    text = models.CharField(max_length=255, blank=True)
    url = models.TextField(blank=True, null=True)

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.sender} -> {self.receiver} ({self.notification_type})"
 


class MessageNotification(models.Model):

    sender = models.ForeignKey(User,on_delete=models.CASCADE,related_name="sent_message_notifications")

    receiver = models.ForeignKey(User,on_delete=models.CASCADE,related_name="message_notifications")
    text = models.CharField(max_length=255, blank=True)
    url = models.TextField(blank=True, null=True)

    message_id = models.IntegerField()
    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]