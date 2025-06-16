#!/usr/bin/env python3
"""Debug script to fetch and save raw Fireflies API response."""

import json
import sys
from datetime import datetime, timedelta
from src.fireflies_client import FirefliesClient
from src.config import get_config

def main():
    # Load configuration
    config = get_config()
    
    # Initialize Fireflies client
    client = FirefliesClient(config.fireflies.api_key)
    
    print("Fetching recent meetings from Fireflies...")
    
    # Get meetings from the last 7 days
    since_date = datetime.now() - timedelta(days=7)
    meetings_list = client.get_recent_meetings(since_date)
    
    if not meetings_list:
        print("No meetings found.")
        return
    
    print(f"Found {len(meetings_list)} meetings:")
    for i, meeting in enumerate(meetings_list):
        print(f"{i+1}. {meeting.get('title', 'Untitled')} - {meeting.get('dateString', 'Unknown date')}")
    
    # Ask user which meeting to fetch details for
    if len(sys.argv) > 1:
        choice = int(sys.argv[1]) - 1
    else:
        choice = int(input("\nEnter meeting number to fetch full details (or 0 for first): ")) - 1
    
    if 0 <= choice < len(meetings_list):
        meeting_id = meetings_list[choice].get('id')
        print(f"\nFetching full details for meeting ID: {meeting_id}")
        
        # Get full meeting details
        full_meeting = client.get_meeting(meeting_id)
        
        if full_meeting:
            # Save to file
            filename = f"debug_meeting_response_{meeting_id}.json"
            with open(filename, 'w') as f:
                json.dump(full_meeting, f, indent=2)
            print(f"\nFull meeting response saved to: {filename}")
            
            # Print summary of available fields
            print("\n=== Available Fields Summary ===")
            print_field_summary(full_meeting)
        else:
            print("Failed to fetch meeting details.")
    else:
        print("Invalid choice.")

def print_field_summary(data, prefix=""):
    """Recursively print field structure."""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                if isinstance(value, list) and value:
                    print(f"{prefix}{key}: [{len(value)} items]")
                    if isinstance(value[0], dict):
                        print(f"{prefix}  First item structure:")
                        print_field_summary(value[0], prefix + "    ")
                elif isinstance(value, dict):
                    print(f"{prefix}{key}:")
                    print_field_summary(value, prefix + "  ")
            else:
                if value is not None and str(value).strip():
                    value_preview = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                    print(f"{prefix}{key}: {value_preview}")

if __name__ == "__main__":
    main()