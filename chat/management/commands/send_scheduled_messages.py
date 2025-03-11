from django.core.management.base import BaseCommand
from django.utils import timezone
from chat.models import ScheduledMessage, Message
from cryptography.fernet import Fernet

class Command(BaseCommand):
    help = 'Sends scheduled messages that are due'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        self.stdout.write(f'Current time (UTC): {now}')
        self.stdout.write(f'Current time (Local): {timezone.localtime(now)}')
        
        # Get all scheduled messages
        all_messages = ScheduledMessage.objects.filter(sent=False)
        self.stdout.write(f'All pending messages: {all_messages.count()}')
        for msg in all_messages:
            local_time = timezone.localtime(msg.scheduled_time)
            self.stdout.write(f'Message {msg.id} scheduled for: {msg.scheduled_time} UTC ({local_time} Local)')
        
        # Get due messages
        scheduled_messages = ScheduledMessage.objects.filter(
            scheduled_time__lte=now,
            sent=False
        )
        
        self.stdout.write(f'Found {scheduled_messages.count()} messages due to send')
        
        for scheduled_message in scheduled_messages:
            try:
                self.stdout.write(f'Processing message {scheduled_message.id} scheduled for {scheduled_message.scheduled_time}')
                
                # Create a regular message from the scheduled message
                f = Fernet(scheduled_message.room.encryption_key.encode())
                encrypted_content = f.encrypt(scheduled_message.content.encode()).decode()

                Message.objects.create(
                    room=scheduled_message.room,
                    sender=scheduled_message.sender,
                    content=scheduled_message.content,
                    encrypted_content=encrypted_content,
                    message_type='text'
                )

                # Mark the scheduled message as sent
                scheduled_message.sent = True
                scheduled_message.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully sent scheduled message {scheduled_message.id}'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error sending message {scheduled_message.id}: {str(e)}'
                    )
                ) 