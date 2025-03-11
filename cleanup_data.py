#!/usr/bin/env python
"""
Script to manually clean up old messages from the database.
This can be run directly from the command line.

Usage:
    python cleanup_data.py [--days=30] [--dry-run]

Options:
    --days      Number of days to keep messages (default: 30)
    --dry-run   Perform a dry run without deleting any data
"""

import os
import sys
import django
import argparse

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatterbox.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from chat.models import Message, ScheduledMessage

def cleanup_old_messages(days=30, dry_run=False):
    """
    Delete messages older than the specified number of days.
    
    Args:
        days (int): Number of days to keep messages
        dry_run (bool): If True, only show what would be deleted without actually deleting
    """
    print(f"Starting cleanup of messages older than {days} days...")
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    # Count messages to be deleted
    old_messages_count = Message.objects.filter(created_at__lt=cutoff_date).count()
    old_scheduled_messages_count = ScheduledMessage.objects.filter(
        created_at__lt=cutoff_date, 
        sent=True
    ).count()
    
    print(f"Found {old_messages_count} messages and {old_scheduled_messages_count} scheduled messages older than {days} days")
    
    if dry_run:
        print(f"DRY RUN: Would have deleted {old_messages_count + old_scheduled_messages_count} messages")
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
        
        print(f"Successfully deleted {deleted_count} messages and {deleted_scheduled_count} scheduled messages")
        
    except Exception as e:
        print(f"Error deleting old messages: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean up old messages from the database")
    parser.add_argument('--days', type=int, default=30, help='Number of days to keep messages (default: 30)')
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without deleting any data')
    
    args = parser.parse_args()
    
    sys.exit(cleanup_old_messages(days=args.days, dry_run=args.dry_run)) 