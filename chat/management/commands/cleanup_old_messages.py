from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from chat.models import Message, ScheduledMessage
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Deletes messages older than the specified retention period'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=settings.DATA_RETENTION_DAYS,
            help=f'Number of days to keep messages (default: {settings.DATA_RETENTION_DAYS})'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run without deleting any data'
        )

    def handle(self, *args, **options):
        retention_days = options['days']
        dry_run = options['dry_run']
        
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        
        # Count messages to be deleted
        old_messages_count = Message.objects.filter(created_at__lt=cutoff_date).count()
        old_scheduled_messages_count = ScheduledMessage.objects.filter(
            created_at__lt=cutoff_date, 
            sent=True
        ).count()
        
        self.stdout.write(
            self.style.WARNING(
                f'Found {old_messages_count} messages and {old_scheduled_messages_count} scheduled messages '
                f'older than {retention_days} days'
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN: Would have deleted {old_messages_count + old_scheduled_messages_count} messages'
                )
            )
            return
        
        # Delete old messages
        try:
            # First delete old messages
            deleted_count, _ = Message.objects.filter(created_at__lt=cutoff_date).delete()
            
            # Then delete old scheduled messages that have been sent
            deleted_scheduled_count, _ = ScheduledMessage.objects.filter(
                created_at__lt=cutoff_date,
                sent=True
            ).delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {deleted_count} messages and {deleted_scheduled_count} scheduled messages'
                )
            )
            
            logger.info(
                f'Cleanup completed: Deleted {deleted_count} messages and {deleted_scheduled_count} scheduled messages '
                f'older than {retention_days} days'
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Error deleting old messages: {str(e)}'
                )
            )
            logger.error(f'Error during message cleanup: {str(e)}') 