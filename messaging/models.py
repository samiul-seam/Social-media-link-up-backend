from django.db import models
from accounts.models import User


# Create your models here.
class ChatList(models.Model):
    user1 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="inbox_user1",
        null=True, blank=True
    )
    user2 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="inbox_user2",
        null=True, blank=True
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user1", "user2")

    def __str__(self):
        return f"{self.user1} - {self.user2}"
    


class Message(models.Model):
    inbox = models.ForeignKey(ChatList, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sender")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviever")

    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender} - {self.receiver}"
    
    @property
    def sender_profile(self):
        return self.sender

    @property
    def receiver_profile(self):
        return self.receiver 



class ImageMessage(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='message_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for message {self.message.id} by {self.message.sender.username}"
