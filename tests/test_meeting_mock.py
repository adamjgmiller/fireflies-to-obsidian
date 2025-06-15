#!/usr/bin/env python3
"""Mock test to demonstrate meeting sync functionality without API credentials."""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.obsidian_sync import ObsidianSync
from src.utils.logger import get_logger

logger = get_logger(__name__)


def test_meeting_mock(meeting_id: str):
    """Test with mock meeting data."""
    try:
        # Mock meeting data that would come from Fireflies API
        mock_meeting = {
            'id': meeting_id,
            'title': 'Product Strategy Meeting - Q1 Planning',
            'date': '2024-12-10T14:30:00Z',
            'duration': 3600,  # 1 hour in seconds
            'attendees': ['John Smith', 'Jane Doe', 'Bob Johnson'],
            'organizer_email': 'john.smith@example.com',
            'summary': 'Discussed Q1 product roadmap, key features, and resource allocation.',
            'transcript': """John Smith: Welcome everyone to our Q1 planning meeting.
Jane Doe: Thanks for organizing this, John.
Bob Johnson: Happy to be here.
John Smith: Let's start with our key objectives for Q1..."""
        }
        
        logger.info(f"Using mock data for meeting: {meeting_id}")
        logger.info(f"Meeting title: {mock_meeting['title']}")
        logger.info(f"Date: {mock_meeting['date']}")
        logger.info(f"Duration: {mock_meeting['duration']} seconds")
        logger.info(f"Attendees: {', '.join(mock_meeting['attendees'])}")
        
        # Mock Obsidian vault path (would come from config)
        vault_path = "/tmp/test_obsidian_vault"
        Path(vault_path).mkdir(exist_ok=True)
        
        # Initialize Obsidian sync
        obsidian = ObsidianSync(vault_path)
        logger.info(f"Obsidian sync initialized with vault: {vault_path}")
        
        # Create markdown content (this would normally be done by markdown_formatter)
        content = f"""---
meeting_id: {mock_meeting['id']}
title: {mock_meeting['title']}
date: {mock_meeting['date']}
duration: {mock_meeting['duration']}
attendees: {', '.join(mock_meeting['attendees'])}
organizer: {mock_meeting['organizer_email']}
---

# {mock_meeting['title']}

**Date**: {mock_meeting['date']}
**Duration**: {mock_meeting['duration'] // 60} minutes
**Attendees**: {', '.join(mock_meeting['attendees'])}
**Organizer**: {mock_meeting['organizer_email']}

## Summary
{mock_meeting['summary']}

## Transcript
{mock_meeting['transcript']}

## Action Items
- [ ] Review Q1 objectives
- [ ] Allocate resources for key features
- [ ] Schedule follow-up meetings

## Key Topics
- Q1 Product Roadmap
- Resource Allocation
- Feature Prioritization
"""
        
        # Save to Obsidian
        file_path = obsidian.save_meeting(mock_meeting, content)
        
        if file_path:
            logger.info(f"Meeting saved successfully: {file_path}")
            logger.info(f"File content preview:")
            print("-" * 60)
            print(content[:500] + "..." if len(content) > 500 else content)
            print("-" * 60)
        else:
            logger.warning("Meeting already exists in vault")
            
    except Exception as e:
        logger.error(f"Error in mock test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Test with the provided meeting ID
    test_meeting_id = "01JXDVB2EF0ETQWDJ40TPX7TF2"
    
    # Also check if meeting ID is provided as command line argument
    if len(sys.argv) > 1:
        test_meeting_id = sys.argv[1]
    
    logger.info(f"Testing with mock data for meeting ID: {test_meeting_id}")
    test_meeting_mock(test_meeting_id)