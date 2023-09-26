# chat/models.py
from django.contrib.auth.models import User
from django.db import models

class Group(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='owned_groups')
    members = models.ManyToManyField(User, related_name='group')
    deleted = models.BooleanField(default=False)  # For soft deleting the group :)

    def __str__(self):
        return self.name

class Message(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sender')
    likes = models.ManyToManyField(User, related_name='liked_messages', blank=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender.username}: {self.content}'
