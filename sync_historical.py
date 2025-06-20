#!/usr/bin/env python3
"""One-time sync script for processing historical Fireflies meetings."""

import asyncio
import sys
import argparse
from datetime import datetime, timedelta
from src.fireflies_client import FirefliesClient
from src.obsidian_sync import ObsidianSync
from src.state_manager import StateManager
from src.config import get_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


async def sync_historical_meetings(days_back=1500, batch_size=50, dry_run=False):
    """
    Sync historical meetings from Fireflies to Obsidian.
    
    Args:
        days_back: Number of days to look back (default: 1500)
        batch_size: Number of meetings to process in each batch
        dry_run: If True, only show what would be processed without actually syncing
    """
    try:
        # Load configuration
        config = get_config()
        
        # Initialize components
        fireflies_client = FirefliesClient(config.fireflies.api_key)
        obsidian_sync = ObsidianSync(config.obsidian.vault_path)
        state_manager = StateManager()
        
        # Get current stats
        stats = state_manager.get_stats()
        logger.info(f"Currently processed meetings: {stats['total_processed']}")
        
        # Get all transcripts for the period
        since_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        logger.info(f"Fetching all meetings from the last {days_back} days...")
        
        try:
            all_transcripts = await fireflies_client.get_all_transcripts_since(since_date, batch_size=10)
            total_available = len(all_transcripts)
        except Exception as e:
            if "too_many_requests" in str(e):
                logger.error(f"Hit rate limit while fetching meeting list: {e}")
                logger.info("\nTry running with fewer days or wait before retrying.")
                logger.info("For example: python sync_historical.py --days 30")
                return False
            raise
        logger.info(f"Total meetings available: {total_available}")
        
        # Filter out already processed meetings
        unprocessed = []
        for transcript in all_transcripts:
            meeting_id = transcript.get('id')
            if meeting_id and not state_manager.is_processed(meeting_id):
                unprocessed.append(transcript)
        
        logger.info(f"Unprocessed meetings: {len(unprocessed)}")
        
        if dry_run:
            logger.info("\n=== DRY RUN MODE - No changes will be made ===")
            logger.info(f"Would process {len(unprocessed)} meetings")
            
            # Show first 10 unprocessed meetings
            logger.info("\nFirst 10 unprocessed meetings:")
            for transcript in unprocessed[:10]:
                date_str = transcript.get('dateString', 'Unknown date')
                title = transcript.get('title', 'No title')
                meeting_id = transcript.get('id', 'No ID')
                logger.info(f"  - {date_str}: {title} (ID: {meeting_id})")
            
            if len(unprocessed) > 10:
                logger.info(f"  ... and {len(unprocessed) - 10} more")
            
            return True
        
        # Process meetings in batches
        processed_count = 0
        skipped_count = 0
        error_count = 0
        
        logger.info(f"\nProcessing {len(unprocessed)} meetings in batches of {batch_size}...")
        
        for i in range(0, len(unprocessed), batch_size):
            batch = unprocessed[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(unprocessed) + batch_size - 1) // batch_size
            
            logger.info(f"\nProcessing batch {batch_num}/{total_batches} ({len(batch)} meetings)...")
            
            # Get full details for each meeting in the batch
            for j, transcript in enumerate(batch):
                meeting_id = transcript.get('id')
                if not meeting_id:
                    continue
                
                try:
                    # Check if summary is ready
                    full_meeting = await fireflies_client.get_transcript_details(meeting_id)
                    
                    if not fireflies_client.is_summary_ready(full_meeting):
                        meeting_info = full_meeting.get('meeting_info', {})
                        status = meeting_info.get('summary_status', 'unknown')
                        logger.info(f"  [{j+1}/{len(batch)}] Skipping {meeting_id} - summary not ready (status: {status})")
                        skipped_count += 1
                        continue
                    
                    # Create Obsidian note
                    file_path = obsidian_sync.create_meeting_note(full_meeting)
                    if file_path:
                        state_manager.mark_processed(meeting_id)
                        processed_count += 1
                        logger.info(f"  [{j+1}/{len(batch)}] Processed: {full_meeting.get('title', 'No title')}")
                    
                except Exception as e:
                    logger.error(f"  [{j+1}/{len(batch)}] Error processing {meeting_id}: {e}")
                    error_count += 1
                
                # Small delay between individual meetings to avoid rate limits
                await asyncio.sleep(0.5)
            
            # Longer delay between batches
            if i + batch_size < len(unprocessed):
                logger.info(f"Batch {batch_num} complete. Waiting before next batch...")
                await asyncio.sleep(2)
        
        # Final summary
        logger.info("\n=== SYNC COMPLETE ===")
        logger.info(f"Total meetings available: {total_available}")
        logger.info(f"Already processed before sync: {total_available - len(unprocessed)}")
        logger.info(f"Processed in this sync: {processed_count}")
        logger.info(f"Skipped (summary not ready): {skipped_count}")
        logger.info(f"Errors: {error_count}")
        logger.info(f"Total processed now: {stats['total_processed'] + processed_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during historical sync: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Sync historical Fireflies meetings to Obsidian')
    parser.add_argument('--days', type=int, default=1500,
                       help='Number of days to look back (default: 1500)')
    parser.add_argument('--batch-size', type=int, default=50,
                       help='Number of meetings to process in each batch (default: 50)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be processed without actually syncing')
    
    args = parser.parse_args()
    
    success = asyncio.run(sync_historical_meetings(
        days_back=args.days,
        batch_size=args.batch_size,
        dry_run=args.dry_run
    ))
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()