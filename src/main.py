"""Main application entry point for Fireflies to Obsidian sync."""
import sys
import time
import signal
import argparse
from datetime import datetime, timedelta
from typing import Optional, List
from src.fireflies_client import FirefliesClient
from src.obsidian_sync import ObsidianSync
from src.state_manager import StateManager
from src.config import get_config
from src.utils.logger import setup_logger
from src.notification_service import get_notification_service
from src import signal_handler as sig_handler

logger = setup_logger(__name__)

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True


def process_meetings(fireflies_client: FirefliesClient, 
                    obsidian_sync: ObsidianSync,
                    state_manager: StateManager,
                    config,
                    meeting_ids: Optional[List[str]] = None,
                    enable_notifications: bool = True) -> int:
    """
    Process meetings from Fireflies to Obsidian.
    
    Args:
        fireflies_client: Fireflies API client
        obsidian_sync: Obsidian sync handler
        state_manager: State manager for tracking processed meetings
        config: Application configuration object
        meeting_ids: Optional list of specific meeting IDs to process (test mode)
        enable_notifications: Whether to send notifications
    
    Returns:
        Number of meetings processed
    """
    processed_count = 0
    error_count = 0
    skipped_count = 0  # Track meetings skipped due to summary not ready
    notification_service = get_notification_service(enable_notifications)
    
    try:
        if meeting_ids:
            # Test mode: process specific meetings
            logger.info(f"Test mode: Processing {len(meeting_ids)} specific meetings")
            meetings = []
            for meeting_id in meeting_ids:
                try:
                    # Skip if already processed - avoid unnecessary API calls (same as normal mode)
                    if state_manager.is_processed(meeting_id):
                        logger.debug(f"Test meeting {meeting_id} already processed, skipping API fetch")
                        continue
                    
                    # Use summary check method to only get meetings with ready summaries
                    meeting = fireflies_client.get_meeting_with_summary_check(meeting_id)
                    if meeting:
                        meetings.append(meeting)
                    else:
                        # Meeting exists but summary not ready, or meeting doesn't exist
                        # Log will be handled by get_meeting_with_summary_check method
                        skipped_count += 1
                except Exception as e:
                    logger.error(f"Failed to fetch meeting {meeting_id}: {e}")
                    error_count += 1
        else:
            # Normal mode: get recent meetings
            # Use configured lookback days
            lookback_days = config.sync.lookback_days
            since_date = datetime.now() - timedelta(days=lookback_days)
            logger.info(f"Looking for meetings from the last {lookback_days} days")
            meetings_list = fireflies_client.get_recent_meetings(since_date)
            
            # Filter out already processed meetings first, then fetch full details
            logger.info(f"Found {len(meetings_list)} meetings, filtering already processed and checking summary readiness...")
            meetings = []
            already_processed_count = 0
            
            # Add progress tracking for large numbers of meetings
            total_to_check = len(meetings_list)
            checked_count = 0
            
            for meeting_summary in meetings_list:
                try:
                    meeting_id = meeting_summary.get('id')
                    if meeting_id:
                        # Skip if already processed - avoid unnecessary API calls
                        if state_manager.is_processed(meeting_id):
                            logger.debug(f"Meeting {meeting_id} already processed, skipping API fetch")
                            already_processed_count += 1
                            continue
                        
                        # Log progress for large batches
                        checked_count += 1
                        if checked_count % 10 == 0 or checked_count == 1:
                            logger.info(f"Checking meeting {checked_count} of {total_to_check - already_processed_count} unprocessed meetings...")
                        
                        # Use summary check method to only get meetings with ready summaries
                        full_meeting = fireflies_client.get_meeting_with_summary_check(meeting_id)
                        if full_meeting:
                            meetings.append(full_meeting)
                            logger.info(f"Added meeting {meeting_id} to processing queue (total: {len(meetings)})")
                        else:
                            # Meeting summary not ready - skip but don't count as error
                            skipped_count += 1
                except Exception as e:
                    logger.error(f"Failed to fetch full details for meeting {meeting_id}: {e}")
                    error_count += 1
            
            if already_processed_count > 0:
                logger.info(f"Skipped {already_processed_count} already processed meetings")
        
        logger.info(f"Found {len(meetings)} meetings with ready summaries to process")
        if skipped_count > 0:
            logger.info(f"Skipped {skipped_count} meetings with summaries not yet ready")
        
        for meeting in meetings:
            meeting_id = meeting.get('id')
            if not meeting_id:
                logger.warning("Meeting without ID found, skipping")
                continue
            
            # Note: Already filtered processed meetings during fetch phase for efficiency
            
            try:
                # Create Obsidian note
                file_path = obsidian_sync.create_meeting_note(meeting)
                if file_path:
                    state_manager.mark_processed(meeting_id)
                    processed_count += 1
                    logger.info(f"Successfully processed meeting {meeting_id} with ready summary")
                    
                    # Send notification for this meeting
                    notification_service.notify_meeting_synced(meeting)
                    
            except Exception as e:
                logger.error(f"Failed to process meeting {meeting_id}: {e}")
                error_count += 1
        
        # Enhanced logging for summary readiness tracking
        if skipped_count > 0:
            logger.info(f"Summary: {processed_count} meetings processed, {skipped_count} skipped (summaries not ready), {error_count} errors")
        else:
            logger.info(f"Processed {processed_count} new meetings")
        
        # Send summary notification if any meetings were processed or failed
        if processed_count > 0 or error_count > 0:
            notification_service.notify_sync_summary(processed_count, error_count)
        
    except Exception as e:
        logger.error(f"Error during meeting processing: {e}")
    
    return processed_count


def run_polling_loop(config, test_meeting_ids: Optional[List[str]] = None):
    """
    Run the main polling loop.
    
    Args:
        config: Application configuration (AppConfig object)
        test_meeting_ids: Optional list of meeting IDs for test mode
    """
    global shutdown_requested
    
    # Initialize components
    fireflies_client = FirefliesClient(config.fireflies.api_key)
    obsidian_sync = ObsidianSync(config.obsidian.vault_path)
    state_manager = StateManager()
    
    # Display startup info
    stats = state_manager.get_stats()
    logger.info("Starting Fireflies to Obsidian sync service")
    logger.info(f"Obsidian vault: {config.obsidian.vault_path}")
    logger.info(f"Lookback days: {config.sync.lookback_days}")
    logger.info(f"State file: {stats['state_file']}")
    logger.info(f"Previously processed meetings: {stats['total_processed']}")
    
    if test_meeting_ids:
        logger.info("Running in test mode with specific meeting IDs")
        process_meetings(fireflies_client, obsidian_sync, state_manager, config, test_meeting_ids)
        logger.info("Test mode completed")
        return
    
    # Normal polling mode
    poll_interval = config.sync.polling_interval_seconds
    logger.info(f"Starting polling loop with {poll_interval} second interval")
    
    while not shutdown_requested:
        try:
            # Check if immediate sync was requested via signal
            if sig_handler.is_sync_requested():
                logger.info("[MANUAL] Processing signal-triggered sync")
                sig_handler.clear_sync_request()
                
                # Process meetings immediately
                processed = process_meetings(fireflies_client, obsidian_sync, state_manager, config,
                                           enable_notifications=config.notifications.enabled)
                logger.info(f"[MANUAL] Signal-triggered sync completed, processed {processed} meetings")
            else:
                # Regular polling sync
                processed = process_meetings(fireflies_client, obsidian_sync, state_manager, config,
                                           enable_notifications=config.notifications.enabled)
            
            # Update last check time
            state_manager.set_metadata('last_poll_time', datetime.now().isoformat())
            
            # Wait for next poll (check for shutdown and signals every second)
            for _ in range(poll_interval):
                if shutdown_requested or sig_handler.is_sync_requested():
                    break
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            shutdown_requested = True
        except Exception as e:
            logger.error(f"Unexpected error in polling loop: {e}")
            # Wait before retrying to avoid rapid failure loops
            time.sleep(poll_interval)
    
    # Clean up signal handlers on shutdown
    sig_handler.cleanup_signal_handlers()
    logger.info("Sync service stopped")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Sync Fireflies meetings to Obsidian')
    parser.add_argument('--test', nargs='+', metavar='MEETING_ID',
                       help='Test mode: sync specific meeting IDs')
    parser.add_argument('--config', default='config.yaml',
                       help='Path to configuration file (default: config.yaml)')
    
    args = parser.parse_args()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Load configuration
        config = get_config()
        
        # Set up signal handlers for immediate sync
        sig_handler.setup_signal_handlers()
        
        # Run the service
        run_polling_loop(config, args.test)
        
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()