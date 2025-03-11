from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from cryptography.fernet import Fernet, InvalidToken

class ChatRoom(models.Model):
    name = models.CharField(max_length=100)
    participants = models.ManyToManyField(User, related_name='chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    encryption_key = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.encryption_key:
            self.encryption_key = Fernet.generate_key().decode()
        super().save(*args, **kwargs)

    def get_fernet(self):
        return Fernet(self.encryption_key.encode())

class Message(models.Model):
    TYPE_CHOICES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('voice', 'Voice'),
        ('sticker', 'Sticker'),
    ]

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    encrypted_content = models.TextField(blank=True)
    message_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='text')
    file = models.FileField(upload_to='chat_files/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')

    class Meta:
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        if not self.encrypted_content:  # Only encrypt if not already encrypted
            f = self.room.get_fernet()
            self.encrypted_content = f.encrypt(self.content.encode()).decode()
        super().save(*args, **kwargs)

    def get_decrypted_content(self):
        try:
            f = self.room.get_fernet()
            return f.decrypt(self.encrypted_content.encode()).decode()
        except Exception as e:
            return f"[Error: Unable to decrypt message]"

    @classmethod
    def fix_encryption(cls):
        """Fix encryption for all messages that have invalid encryption"""
        for message in cls.objects.all():
            try:
                # Try to decrypt
                message.get_decrypted_content()
            except Exception:
                # If decryption fails, re-encrypt
                f = message.room.get_fernet()
                message.encrypted_content = f.encrypt(message.content.encode()).decode()
                message.save(update_fields=['encrypted_content'])

class DiaryEntry(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='diary_entries')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diary_entries')
    title = models.CharField(max_length=200)
    content = models.TextField()
    encrypted_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

class ScheduledMessage(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='scheduled_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheduled_messages')
    content = models.TextField()
    encrypted_content = models.TextField()
    scheduled_time = models.DateTimeField()
    sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_time']

class CustomSticker(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='stickers/')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_stickers')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class RoomInvitation(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='invitations')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    invite_code = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.invite_code:
            # Generate a random invite code if not set
            import secrets
            import string
            alphabet = string.ascii_letters + string.digits
            self.invite_code = ''.join(secrets.choice(alphabet) for _ in range(10))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invite to {self.room.name} by {self.created_by.username}"
