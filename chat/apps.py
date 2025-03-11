from django.apps import AppConfig
import threading
import time
import os

class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'

    def ready(self):
        if os.environ.get('RUN_MAIN'):  # Only run in the main process
            def check_scheduled_messages():
                while True:
                    try:
                        # Import here to avoid premature import
                        from django.utils import timezone
                        import pytz
                        from chat.models import ScheduledMessage, Message
                        
                        # Get current time in India timezone
                        indian_tz = pytz.timezone('Asia/Kolkata')
                        now = timezone.now().astimezone(indian_tz)
                        
                        # Find messages that need to be sent
                        pending_messages = ScheduledMessage.objects.filter(
                            scheduled_time__lte=now,
                            sent=False
                        ).order_by('scheduled_time')
                        
                        if pending_messages.exists():
                            print(f"[Scheduled Messages] Found {pending_messages.count()} messages to send")
                            print("[Scheduled Messages] Messages to process:")
                            for msg in pending_messages:
                                try:
                                    print(f"  - Message {msg.id}: scheduled for {msg.scheduled_time.astimezone(indian_tz)} (India time)")
                                    
                                    # Create regular message using the model's save method
                                    Message.objects.create(
                                        room=msg.room,
                                        sender=msg.sender,
                                        content=msg.content,  # The model will handle encryption
                                        message_type='text'
                                    )
                                    
                                    # Mark as sent
                                    msg.sent = True
                                    msg.save()
                                    
                                    print(f"[Scheduled Messages] Successfully processed message {msg.id}")
                                except Exception as e:
                                    print(f"[Scheduled Messages] Error processing message {msg.id}: {e}")
                                    
                    except Exception as e:
                        print(f"Error checking scheduled messages: {e}")
                    
                    time.sleep(5)  # Check every 5 seconds

            thread = threading.Thread(target=check_scheduled_messages, daemon=True)
            thread.start()
