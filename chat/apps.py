from django.apps import AppConfig
import threading
import time
import os
import subprocess
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'

    def ready(self):
        if os.environ.get('RUN_MAIN'):  # Only run in the main process
            # Start the scheduled messages thread
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
            
            # Start the data cleanup thread
            def run_data_cleanup():
                while True:
                    try:
                        # Run cleanup at midnight
                        now = datetime.now()
                        # Calculate seconds until midnight
                        seconds_until_midnight = (
                            ((24 - now.hour - 1) * 60 * 60) +  # Hours until midnight
                            ((60 - now.minute - 1) * 60) +     # Minutes until next hour
                            (60 - now.second)                   # Seconds until next minute
                        )
                        
                        # Sleep until midnight
                        time.sleep(seconds_until_midnight)
                        
                        # Run the cleanup command (default 30 days retention)
                        from django.core.management import call_command
                        logger.info("Running scheduled data cleanup")
                        
                        # Use the retention days from settings
                        from django.conf import settings
                        retention_days = getattr(settings, 'DATA_RETENTION_DAYS', 30)
                        logger.info(f"Running data cleanup with {retention_days} days retention period")
                        call_command('cleanup_old_messages', days=retention_days)
                        
                        # Sleep for a day to avoid running multiple times
                        time.sleep(60)  # Sleep for a minute to avoid running twice at midnight
                    except Exception as e:
                        logger.error(f"Error running data cleanup: {e}")
                        time.sleep(3600)  # Sleep for an hour if there's an error
            
            # Start the threads
            scheduled_messages_thread = threading.Thread(target=check_scheduled_messages, daemon=True)
            scheduled_messages_thread.start()
            
            cleanup_thread = threading.Thread(target=run_data_cleanup, daemon=True)
            cleanup_thread.start()
