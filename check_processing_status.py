#!/usr/bin/env python3
"""Check the processing status of Fireflies meetings."""

import asyncio
import sys
from datetime import datetime, timedelta
from src.fireflies_client import FirefliesClient
from src.state_manager import StateManager
from src.config import get_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


async def check_processing_status():
    """Check how many meetings are available vs processed."""
    try:
        # Load configuration
        config = get_config()
        
        # Initialize components
        fireflies_client = FirefliesClient(config.fireflies.api_key)
        state_manager = StateManager()
        
        # Get current stats
        stats = state_manager.get_stats()
        processed_count = stats['total_processed']
        
        logger.info(f"Currently processed meetings: {processed_count}")
        logger.info(f"State file: {stats['state_file']}")
        
        # Check meetings for different time periods
        time_periods = [
            (7, "last week"),
            (30, "last month"),
            (365, "last year"),
            (1500, "last 4+ years")
        ]
        
        for days, period_name in time_periods:
            since_date = (datetime.now() - timedelta(days=days)).isoformat()
            logger.info(f"\nChecking meetings from {period_name} ({days} days)...")
            
            # Get all transcripts for this period
            transcripts = await fireflies_client.get_all_transcripts_since(since_date)
            total_available = len(transcripts)
            
            # Count how many are already processed
            already_processed = 0
            unprocessed = []
            summaries_not_ready = 0
            
            for transcript in transcripts:
                meeting_id = transcript.get('id')
                if meeting_id and state_manager.is_processed(meeting_id):
                    already_processed += 1
                else:
                    unprocessed.append(transcript)
            
            # Check summary status for unprocessed meetings (sample first 10)
            logger.info(f"Checking summary status for sample of unprocessed meetings...")
            sample_size = min(10, len(unprocessed))
            for i, transcript in enumerate(unprocessed[:sample_size]):
                meeting_id = transcript.get('id')
                if meeting_id:
                    try:
                        full_meeting = await fireflies_client.get_transcript_details(meeting_id)
                        if not fireflies_client.is_summary_ready(full_meeting):
                            summaries_not_ready += 1
                            meeting_info = full_meeting.get('meeting_info', {})
                            status = meeting_info.get('summary_status', 'unknown')
                            logger.info(f"  Meeting {meeting_id}: summary status = {status}")
                    except Exception as e:
                        logger.error(f"  Error checking meeting {meeting_id}: {e}")
            
            # Report results
            logger.info(f"\nResults for {period_name}:")
            logger.info(f"  Total meetings available: {total_available}")
            logger.info(f"  Already processed: {already_processed}")
            logger.info(f"  Unprocessed: {len(unprocessed)}")
            if sample_size > 0:
                logger.info(f"  Sample check: {summaries_not_ready}/{sample_size} have summaries not ready")
            
            # Show some details about unprocessed meetings
            if unprocessed:
                logger.info(f"\n  First 5 unprocessed meetings:")
                for transcript in unprocessed[:5]:
                    date_str = transcript.get('dateString', 'Unknown date')
                    title = transcript.get('title', 'No title')
                    meeting_id = transcript.get('id', 'No ID')
                    logger.info(f"    - {date_str}: {title} (ID: {meeting_id})")
                
                if len(unprocessed) > 5:
                    logger.info(f"    ... and {len(unprocessed) - 5} more")
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking processing status: {e}")
        return False


def main():
    """Main entry point."""
    success = asyncio.run(check_processing_status())
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()