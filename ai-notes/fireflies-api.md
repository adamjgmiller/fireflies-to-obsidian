---

# Fireflies API Internal Documentation
**For: fireflies-to-obsidian sync tool**

## Overview

The Fireflies API is a GraphQL-based API that provides access to meeting transcripts, summaries, and metadata. For our sync tool, we primarily need to:

1. **Query new transcripts** (polling every 15 seconds or webhook-based)
2. **Retrieve full transcript details** with speakers and content
3. **Get AI-generated summaries and action items**
4. **Access meeting metadata** (participants, duration, dates)

**API Endpoint**: `https://api.fireflies.ai/graphql`  
**Authentication**: Bearer token in Authorization header  

## Rate Limits (Updated Jun 2025)

| Plan | Rate Limit |
|------|------------|
| **Business/Enterprise** | 60 requests per minute |
| **Free & Pro** | 50 requests per day |

**Our Usage**:
- Polling mode: ~4 requests/minute (every 15 seconds)
- Webhook mode: Only on-demand requests (recommended)

## Required API Operations

### 1. Polling for New Transcripts

**Query**: `transcripts`  
**Purpose**: Get list of recent meetings for polling  
**Frequency**: Every 15 seconds (or replace with webhooks)

```graphql
query GetRecentTranscripts($fromDate: DateTime, $toDate: DateTime, $limit: Int, $skip: Int) {
  transcripts(fromDate: $fromDate, toDate: $toDate, limit: $limit, skip: $skip, mine: true) {
    id
    title
    date
    dateString
    organizer_email
    duration
  }
}
```

**Key Parameters**:
- `fromDate`: ISO 8601 DateTime (`2024-06-13T00:00:00.000Z`)
- `toDate`: Optional - bounds the time window
- `limit`: Maximum 50 per request (we'll use 10 for polling)
- `skip`: New parameter for pagination over historic meetings
- `mine: true`: Only meetings we own/have access to

### 2. Retrieving Full Transcript Details

**Query**: `transcript`  
**Purpose**: Get complete meeting data for syncing to Obsidian  
**Used**: When new meeting detected

```graphql
query GetTranscriptDetails($transcriptId: String!) {
  transcript(id: $transcriptId) {
    id
    title
    date
    dateString
    duration
    organizer_email
    participants
    fireflies_users
    meeting_attendees {
      displayName
      email
      phoneNumber
      name
      location
    }
    speakers {
      id
      name
    }
    sentences {
      index
      speaker_name
      speaker_id
      text
      raw_text
      start_time
      end_time
    }
    summary {
      keywords
      action_items
      outline
      overview
      shorthand_bullet
      bullet_gist
      gist
      short_summary
      short_overview
      meeting_type
      topics_discussed
      transcript_chapters
    }
    transcript_url
    meeting_link
    calendar_id
    cal_id
    calendar_type
    # Optional fields for future features:
    # audio_url        # Direct media download link
    # video_url        # Video download link  
    # analytics {      # Meeting analytics data
    #   sentiments { negative_pct neutral_pct positive_pct }
    #   categories { questions date_times metrics tasks }
    #   speakers {
    #     speaker_id name duration word_count
    #     longest_monologue monologues_count filler_words
    #     questions duration_pct words_per_minute
    #   }
    # }
  }
}
```

### 3. Required Data Fields

Based on our Obsidian template needs:

**Metadata Fields**:
- `id`: Fireflies meeting ID
- `title`: Meeting title
- `date`/`dateString`: Meeting date/time
- `duration`: Meeting length in seconds
- `organizer_email`: Meeting host
- `participants`: All attendee emails
- `meeting_attendees`: Structured attendee data
- `transcript_url`: Link to Fireflies dashboard
- `meeting_link`: Original meeting URL (Zoom, etc.)
- `calendar_id` / `cal_id`: Calendar event identifiers

**Content Fields**:
- `sentences[]`: Full transcript with speaker attribution and timestamps
- `summary.action_items`: AI-generated action items
- `summary.overview`: Meeting summary
- `summary.topics_discussed`: Key topics covered
- `speakers[]`: Speaker names and IDs

## Authentication Setup

```python
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {api_key}'
}
```

**API Key Location**: 
1. Sign in to [app.fireflies.ai](https://app.fireflies.ai)
2. Go to Integrations → Fireflies API
3. Copy API key to `.env` file

## Rate Limiting & Error Handling

**Updated Error Codes (Jun 2025)**:
```python
# Common error codes to handle
ERROR_CODES = {
    'object_not_found': 'Meeting not accessible',
    'too_many_requests': 'Rate limit exceeded (HTTP 429)',
    'forbidden': 'API key invalid/expired (HTTP 403)',
    'invalid_arguments': 'Invalid query parameters',
    'paid_required': 'Feature requires paid plan',
    'args_required': 'Missing required arguments'
}
```

**Enhanced Retry Strategy**:
```python
async def retry_with_backoff(request_func, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = await request_func()
            return response
        except Exception as e:
            # Check for retryAfter in response metadata
            if hasattr(e, 'extensions') and 'retryAfter' in e.extensions.get('metadata', {}):
                retry_after = e.extensions['metadata']['retryAfter']
                await asyncio.sleep(retry_after)
            else:
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
    
    raise Exception(f"Max retries ({max_retries}) exceeded")
```

## Webhook Alternative (Recommended)

**Instead of 15-second polling**, you can use Fireflies webhooks to eliminate API waste:

### Setting up Webhooks:
1. Go to [Dashboard → Developer Settings](https://app.fireflies.ai/settings)
2. Enter your HTTPS webhook URL
3. Save configuration

### Webhook Event:
```json
{
  "event": "transcription_complete",
  "transcript_id": "abc123",
  "title": "Project Meeting",
  "date": "2024-06-15T14:30:00.000Z"
}
```

### Development Setup:
```bash
# Use ngrok for local development
ngrok http 8000
# Then use the https URL in Fireflies dashboard
```

**Benefits**:
- Zero polling API calls
- Instant notifications when transcripts are ready
- Much more efficient for rate-limited plans

## Data Processing Notes

### Meeting Filtering
- Only sync meetings after June 13, 2024
- Use `fromDate` parameter in queries
- Track processed meetings in local JSON state file

### Speaker Grouping
- Group consecutive `sentences` by same `speaker_name`
- Use `start_time`/`end_time` for timestamp ranges
- Format as: "### Speaker Name (MM:SS - MM:SS)"

### File Naming & Sanitization
```python
def sanitize_filename(title: str, max_length: int = 50) -> str:
    # Strip emojis and non-BMP characters for Windows compatibility
    import re
    # Remove emojis and special Unicode characters
    title = re.sub(r'[^\w\s-]', '', title)
    # Replace spaces with hyphens, limit length
    return title.replace(' ', '-')[:max_length].strip('-')

# Convert dateString to: YYYY-MM-DD-HH-MM-[Title].md
filename = f"{date_str}-{sanitize_filename(title)}.md"
```

## Sample Implementation

```python
import httpx
import asyncio
from datetime import datetime, timezone

class FirefliesClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.fireflies.ai/graphql"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
    
    async def get_recent_transcripts(self, from_date: str, limit: int = 10, skip: int = 0):
        query = """
        query GetRecentTranscripts($fromDate: DateTime, $limit: Int, $skip: Int) {
          transcripts(fromDate: $fromDate, limit: $limit, skip: $skip, mine: true) {
            id
            title
            date
            dateString
            organizer_email
            duration
          }
        }
        """
        variables = {"fromDate": from_date, "limit": limit, "skip": skip}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                json={"query": query, "variables": variables},
                headers=self.headers
            )
            return response.json()
    
    async def get_transcript_details(self, transcript_id: str):
        # Implementation for full transcript retrieval
        pass
```

## Configuration Values

From `config.yaml`:
```yaml
fireflies:
  api_url: "https://api.fireflies.ai/graphql"
  rate_limit:
    requests_per_minute: 60
    retry_attempts: 3
    backoff_factor: 2
  webhook_url: ""  # Optional: replace polling with webhooks

sync:
  polling_interval_seconds: 15  # Only if not using webhooks
  batch_size: 10
  lookback_days: 7
```

## Testing Strategy

**Test Mode**: Process specific meeting IDs
```python
python src/main.py --test --meeting-id abc123
```

**Polling Test**: 
```python
# Test polling without processing
python src/main.py --test-polling
```

**Webhook Test**:
```python
# Test webhook endpoint locally
python src/main.py --webhook-mode --port 8000
```

## Security Considerations

- API keys stored in local `.env` file only
- Never commit API keys to version control
- No network exposure - purely local polling service
- Read-only access to Fireflies data
- Webhook endpoints should validate request signatures

## Migration Path: Polling → Webhooks

1. **Phase 1**: Keep current polling implementation
2. **Phase 2**: Add webhook endpoint alongside polling
3. **Phase 3**: Switch to webhook-only mode
4. **Benefits**: 
   - Eliminates 2,880 daily API calls (15-sec polling)
   - Works better with Free/Pro 50-request limit
   - Instant sync vs 15-second delay

## Links & Resources

- [Fireflies API Documentation](https://docs.fireflies.ai/getting-started/introduction)
- [GraphQL Query Examples](https://docs.fireflies.ai/graphql-api/query/transcripts)
- [Transcript Schema Reference](https://docs.fireflies.ai/schema/transcript)
- [Summary Schema Reference](https://docs.fireflies.ai/schema/summary)
- [Webhook Setup Guide](https://docs.fireflies.ai/graphql-api/webhooks)

## ✅ Updated Checklist (Jun 2025)

- [x] Endpoint & auth headers correct  
- [x] Queries compile unchanged  
- [x] Rate limit matches Business tier docs  
- [x] Updated error codes (`too_many_requests`, `forbidden`)  
- [x] Added Free/Pro plan limits (50 req/day)
- [x] Added webhook alternative to eliminate polling waste
- [x] Enhanced filename sanitization for Windows compatibility
- [x] Improved retry logic with server-provided `retryAfter`

---

This internal documentation covers all the Fireflies API functionality needed for your fireflies-to-obsidian sync tool, updated with the latest API changes and best practices as of June 2025. The focus is on the specific queries, data fields, and implementation details needed to build efficient polling or webhook-based sync functionality.