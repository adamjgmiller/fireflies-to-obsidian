#!/usr/bin/env python3
"""Test script to check meeting sync functionality."""

import os
import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.fireflies_client import FirefliesClient
from src.obsidian_sync import ObsidianSync
from src.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def test_meeting(meeting_id: str):
    """Test fetching and saving a specific meeting."""
    try:
        # Load configuration
        config = get_config()
        logger.info(f"Configuration loaded successfully")
        
        # Initialize Fireflies client
        client = FirefliesClient(config.fireflies.api_key, config.fireflies.api_url)
        logger.info("Fireflies client initialized")
        
        # Initialize Obsidian sync
        obsidian = ObsidianSync(config.obsidian.vault_path)
        logger.info(f"Obsidian sync initialized with vault: {config.obsidian.vault_path}")
        
        # Test connection first
        logger.info("Testing Fireflies API connection...")
        connected = await client.test_connection()
        if not connected:
            logger.error("Failed to connect to Fireflies API")
            return
        logger.info("Successfully connected to Fireflies API")
        
        # Fetch meeting data
        logger.info(f"Fetching meeting: {meeting_id}")
        meeting = await client.get_transcript_details(meeting_id)
        
        if not meeting:
            logger.error(f"Meeting {meeting_id} not found")
            return
        
        logger.info(f"Meeting found: {meeting.get('title', 'Untitled')}")
        logger.info(f"Date: {meeting.get('date')}")
        logger.info(f"Duration: {meeting.get('duration')} seconds")
        
        # Extract attendees from meeting_attendees
        attendees = []
        if meeting.get('meeting_attendees'):
            attendees = [att.get('displayName', att.get('name', 'Unknown')) 
                        for att in meeting.get('meeting_attendees', [])]
        logger.info(f"Attendees: {attendees}")
        
        # Extract summary information
        summary_obj = meeting.get('summary', {})
        summary_text = summary_obj.get('overview', summary_obj.get('short_summary', 'No summary available'))
        action_items = summary_obj.get('action_items', [])
        keywords = summary_obj.get('keywords', [])
        
        # Build transcript from sentences
        transcript_lines = []
        for sentence in meeting.get('sentences', []):
            speaker = sentence.get('speaker_name', 'Unknown')
            text = sentence.get('text', '')
            transcript_lines.append(f"{speaker}: {text}")
        transcript = '\n'.join(transcript_lines) if transcript_lines else 'No transcript available'
        
        # For now, create a simple markdown content
        # (This would normally be done by the markdown_formatter module)
        content = f"""---
meeting_id: {meeting.get('id')}
title: {meeting.get('title', 'Untitled Meeting')}
date: {meeting.get('date')}
duration: {meeting.get('duration')}
attendees: {', '.join(attendees)}
organizer: {meeting.get('organizer_email', 'Unknown')}
keywords: {', '.join(keywords) if keywords else 'None'}
---

# {meeting.get('title', 'Untitled Meeting')}

**Date**: {meeting.get('date')}
**Duration**: {meeting.get('duration')} seconds
**Attendees**: {', '.join(attendees)}
**Organizer**: {meeting.get('organizer_email', 'Unknown')}

## Summary
{summary_text}

## Action Items
{chr(10).join(['- ' + item for item in action_items]) if action_items else '- No action items recorded'}

## Keywords
{', '.join(keywords) if keywords else 'No keywords identified'}

## Transcript
{transcript[:1000] + '...' if len(transcript) > 1000 else transcript}
"""
        
        # Save to Obsidian
        file_path = obsidian.save_meeting(meeting, content)
        
        if file_path:
            logger.info(f"Meeting saved successfully: {file_path}")
        else:
            logger.warning("Meeting already exists in vault")
            
    except Exception as e:
        logger.error(f"Error testing meeting: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Test with the provided meeting ID
    test_meeting_id = "01JXDVB2EF0ETQWDJ40TPX7TF2"
    
    # Also check if meeting ID is provided as command line argument
    if len(sys.argv) > 1:
        test_meeting_id = sys.argv[1]
    
    logger.info(f"Testing with meeting ID: {test_meeting_id}")
    asyncio.run(test_meeting(test_meeting_id))