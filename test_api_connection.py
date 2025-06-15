#!/usr/bin/env python3
"""
Test script to verify Fireflies API connection.

This script will:
1. Load your API key from .env file
2. Test the connection to Fireflies API
3. Show recent meetings (if any)
4. Test specific meeting IDs if provided
"""

import asyncio
import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import get_config, ConfigError
from src.fireflies_client import FirefliesClient, FirefliesAPIError


async def test_api_connection():
    """Test the Fireflies API connection."""
    print("🔥 Fireflies API Connection Test")
    print("=" * 40)
    
    try:
        # Load configuration
        print("📋 Loading configuration...")
        config = get_config()
        print(f"✅ API URL: {config.fireflies.api_url}")
        print(f"✅ API Key: {config.fireflies.api_key[:10]}...")
        
        # Create client
        print("\n🔌 Creating Fireflies client...")
        client = FirefliesClient(api_key=config.fireflies.api_key)
        
        # Test connection
        print("🧪 Testing API connection...")
        await client.test_connection()
        print("✅ API connection successful!")
        
        # Get recent meetings
        print(f"\n📅 Fetching recent meetings since {config.sync.from_date}...")
        try:
            transcripts = await client.get_recent_transcripts(
                from_date=config.sync.from_date,
                limit=5
            )
            
            if transcripts:
                print(f"✅ Found {len(transcripts)} recent meetings:")
                for i, transcript in enumerate(transcripts, 1):
                    print(f"   {i}. {transcript['title']} ({transcript['id']})")
                    print(f"      Date: {transcript['dateString']}")
                    print(f"      Duration: {transcript['duration']}s")
                    print(f"      Organizer: {transcript['organizer_email']}")
                    print()
                
                # Test getting details for first meeting
                if transcripts:
                    print("🔍 Testing transcript details retrieval...")
                    first_id = transcripts[0]['id']
                    details = await client.get_transcript_details(first_id)
                    print(f"✅ Successfully retrieved details for: {details['title']}")
                    print(f"   Speakers: {len(details.get('speakers', []))}")
                    print(f"   Sentences: {len(details.get('sentences', []))}")
                    print(f"   Action Items: {len(details.get('summary', {}).get('action_items', []))}")
            else:
                print("ℹ️  No recent meetings found since June 13, 2024")
        
        except FirefliesAPIError as e:
            print(f"⚠️  Could not fetch meetings: {e}")
        
        # Test specific meeting IDs if configured
        if config.sync.test_meeting_ids:
            print(f"\n🎯 Testing specific meeting IDs...")
            for meeting_id in config.sync.test_meeting_ids:
                try:
                    print(f"   Testing: {meeting_id}")
                    details = await client.get_transcript_details(meeting_id)
                    print(f"   ✅ {details['title']} - {details['dateString']}")
                except FirefliesAPIError as e:
                    print(f"   ❌ Failed: {e}")
        
        print(f"\n🎉 All tests completed successfully!")
        
    except ConfigError as e:
        print(f"❌ Configuration error: {e}")
        print("\nMake sure you have:")
        print("1. Created a .env file with FIREFLIES_API_KEY")
        print("2. Set OBSIDIAN_VAULT_PATH to your vault location")
        return False
        
    except FirefliesAPIError as e:
        print(f"❌ API error: {e}")
        print("\nCheck that:")
        print("1. Your API key is correct")
        print("2. Your Fireflies account has API access")
        print("3. You're not hitting rate limits")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True


if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_api_connection())
    sys.exit(0 if success else 1) 