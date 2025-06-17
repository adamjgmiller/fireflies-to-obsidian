"""
Fireflies API Client for GraphQL operations.

This module provides a client for interacting with the Fireflies.ai GraphQL API
to retrieve meeting transcripts, summaries, and metadata.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any

import httpx

from src.utils.logger import get_logger

logger = get_logger(__name__)


class FirefliesAPIError(Exception):
    """Custom exception for Fireflies API errors."""
    
    def __init__(self, message: str, error_code: str = None, response_data: Dict = None):
        super().__init__(message)
        self.error_code = error_code
        self.response_data = response_data


class FirefliesClient:
    """
    Client for interacting with the Fireflies.ai GraphQL API.
    
    Provides methods for retrieving meeting transcripts, summaries, and metadata
    with proper rate limiting, error handling, and authentication.
    """
    
    # GraphQL queries from fireflies-api.md documentation
    GET_RECENT_TRANSCRIPTS_QUERY = """
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
    """
    
    GET_TRANSCRIPT_DETAILS_QUERY = """
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
        meeting_info {
          fred_joined
          silent_meeting
          summary_status
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
      }
    }
    """
    
    # Error codes from fireflies-api.md
    ERROR_CODES = {
        'object_not_found': 'Meeting not accessible',
        'too_many_requests': 'Rate limit exceeded (HTTP 429)',
        'forbidden': 'API key invalid/expired (HTTP 403)',
        'invalid_arguments': 'Invalid query parameters',
        'paid_required': 'Feature requires paid plan',
        'args_required': 'Missing required arguments'
    }
    
    def __init__(self, api_key: str, base_url: str = "https://api.fireflies.ai/graphql"):
        """
        Initialize the Fireflies API client.
        
        Args:
            api_key: Fireflies API key
            base_url: GraphQL endpoint URL (default: https://api.fireflies.ai/graphql)
        """
        if not api_key:
            raise ValueError("API key is required")
            
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        
        logger.info("Fireflies client initialized")
    
    async def _make_request(self, query: str, variables: Dict = None, max_retries: int = 3) -> Dict:
        """
        Make a GraphQL request with retry logic and error handling.
        
        Args:
            query: GraphQL query string
            variables: Query variables
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dict: GraphQL response data
            
        Raises:
            FirefliesAPIError: For API-specific errors
        """
        variables = variables or {}
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        self.base_url,
                        json={"query": query, "variables": variables},
                        headers=self.headers
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Check for GraphQL errors
                        if 'errors' in data:
                            error = data['errors'][0]
                            error_code = error.get('extensions', {}).get('code', 'unknown')
                            error_message = error.get('message', 'Unknown GraphQL error')
                            
                            logger.error(f"GraphQL error: {error_message} (code: {error_code})")
                            raise FirefliesAPIError(
                                f"{error_message} (code: {error_code})",
                                error_code=error_code,
                                response_data=data
                            )
                        
                        logger.debug(f"API request successful (attempt {attempt + 1})")
                        return data
                    
                    elif response.status_code == 429:  # Rate limit exceeded
                        retry_after = int(response.headers.get('Retry-After', 60))
                        logger.warning(f"Rate limit exceeded, retrying after {retry_after} seconds")
                        
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_after)
                            continue
                        else:
                            raise FirefliesAPIError(
                                "Rate limit exceeded - max retries reached",
                                error_code='too_many_requests'
                            )
                    
                    elif response.status_code == 403:
                        raise FirefliesAPIError(
                            "API key invalid or expired",
                            error_code='forbidden'
                        )
                    
                    else:
                        error_msg = f"HTTP {response.status_code}: {response.text}"
                        logger.error(f"API request failed: {error_msg}")
                        
                        if attempt < max_retries - 1:
                            # Exponential backoff
                            await asyncio.sleep(2 ** attempt)
                            continue
                        else:
                            raise FirefliesAPIError(f"API request failed: {error_msg}")
            
            except httpx.RequestError as e:
                logger.error(f"Network error (attempt {attempt + 1}): {e}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise FirefliesAPIError(f"Network error: {e}")
        
        raise FirefliesAPIError(f"Max retries ({max_retries}) exceeded")
    
    async def get_recent_transcripts(
        self,
        from_date: str,
        to_date: Optional[str] = None,
        limit: int = 10,
        skip: int = 0
    ) -> List[Dict]:
        """
        Get list of recent meeting transcripts.
        
        Args:
            from_date: ISO 8601 DateTime string (e.g., "2024-06-13T00:00:00.000Z")
            to_date: Optional ISO 8601 DateTime string to bound the time window
            limit: Maximum number of transcripts to return (max 50)
            skip: Number of transcripts to skip for pagination
            
        Returns:
            List[Dict]: List of transcript metadata
            
        Raises:
            FirefliesAPIError: For API-specific errors
        """
        variables = {
            "fromDate": from_date,
            "limit": min(limit, 50),  # API maximum is 50
            "skip": skip
        }
        
        if to_date:
            variables["toDate"] = to_date
        
        logger.info(f"Fetching recent transcripts from {from_date} (limit: {limit}, skip: {skip})")
        
        response = await self._make_request(self.GET_RECENT_TRANSCRIPTS_QUERY, variables)
        transcripts = response.get('data', {}).get('transcripts', [])
        
        logger.info(f"Retrieved {len(transcripts)} transcripts")
        return transcripts
    
    async def get_transcript_details(self, transcript_id: str) -> Dict:
        """
        Get complete transcript details including content, speakers, summary, and meeting info.
        
        Args:
            transcript_id: Fireflies transcript ID
            
        Returns:
            Dict: Complete transcript data including:
                - Basic meeting metadata (id, title, date, duration, etc.)
                - meeting_info: Contains fred_joined, silent_meeting, and summary_status fields
                - speakers: List of speakers in the meeting
                - sentences: Full transcript sentences with timing
                - summary: AI-generated meeting summary with action items, keywords, etc.
                - Additional metadata (URLs, calendar info, etc.)
                
            The meeting_info.summary_status field indicates summary processing state:
            - 'processing': Summary is still being generated
            - 'processed': Summary is ready and complete
            - 'failed': Summary generation failed
            - 'skipped': Summary was skipped for this meeting
            
        Raises:
            FirefliesAPIError: For API-specific errors
        """
        variables = {"transcriptId": transcript_id}
        
        logger.info(f"Fetching transcript details for ID: {transcript_id}")
        
        response = await self._make_request(self.GET_TRANSCRIPT_DETAILS_QUERY, variables)
        transcript = response.get('data', {}).get('transcript')
        
        if not transcript:
            raise FirefliesAPIError(
                f"Transcript not found or not accessible: {transcript_id}",
                error_code='object_not_found'
            )
        
        logger.info(f"Retrieved transcript details: {transcript.get('title', 'Unknown')}")
        return transcript
    
    async def test_connection(self) -> bool:
        """
        Test API connection and authentication.
        
        Returns:
            bool: True if connection is successful
            
        Raises:
            FirefliesAPIError: For connection or authentication errors
        """
        logger.info("Testing API connection...")
        
        try:
            # Try to fetch a small number of recent transcripts
            from_date = datetime.now(timezone.utc).replace(day=1).isoformat()
            await self.get_recent_transcripts(from_date=from_date, limit=1)
            
            logger.info("API connection test successful")
            return True
            
        except FirefliesAPIError as e:
            logger.error(f"API connection test failed: {e}")
            raise
    
    async def get_all_transcripts_since(
        self,
        from_date: str,
        to_date: Optional[str] = None,
        batch_size: int = 10
    ) -> List[Dict]:
        """
        Get all transcripts since a given date using pagination.
        
        This method automatically handles pagination to retrieve all available
        transcripts, making multiple API calls as needed.
        
        Args:
            from_date: ISO 8601 DateTime string (e.g., "2024-06-13T00:00:00.000Z")
            to_date: Optional ISO 8601 DateTime string to bound the time window
            batch_size: Number of transcripts to fetch per API call (max 50)
            
        Returns:
            List[Dict]: Complete list of all transcript metadata
            
        Raises:
            FirefliesAPIError: For API-specific errors
        """
        all_transcripts = []
        skip = 0
        batch_size = min(batch_size, 50)  # API maximum is 50
        
        logger.info(f"Fetching all transcripts since {from_date} with pagination")
        
        while True:
            # Get a batch of transcripts
            batch = await self.get_recent_transcripts(
                from_date=from_date,
                to_date=to_date,
                limit=batch_size,
                skip=skip
            )
            
            if not batch:
                # No more transcripts available
                break
            
            all_transcripts.extend(batch)
            
            # If we got fewer than batch_size, we've reached the end
            if len(batch) < batch_size:
                break
            
            # Move to next batch
            skip += batch_size
            
            # Add a small delay between requests to be respectful to the API
            await asyncio.sleep(0.1)
        
        logger.info(f"Retrieved {len(all_transcripts)} total transcripts using pagination")
        return all_transcripts
    
    async def get_transcripts_by_date_range(
        self,
        from_date: str,
        to_date: str,
        batch_size: int = 10
    ) -> List[Dict]:
        """
        Get transcripts within a specific date range.
        
        Args:
            from_date: ISO 8601 DateTime string for start of range
            to_date: ISO 8601 DateTime string for end of range
            batch_size: Number of transcripts to fetch per API call
            
        Returns:
            List[Dict]: List of transcript metadata within date range
            
        Raises:
            FirefliesAPIError: For API-specific errors
        """
        logger.info(f"Fetching transcripts from {from_date} to {to_date}")
        
        return await self.get_all_transcripts_since(
            from_date=from_date,
            to_date=to_date,
            batch_size=batch_size
        )
    
    async def get_transcript_details_batch(self, transcript_ids: List[str]) -> List[Dict]:
        """
        Get details for multiple transcripts in parallel.
        
        This method makes concurrent API calls to retrieve details for multiple
        transcripts efficiently while respecting rate limits.
        
        Args:
            transcript_ids: List of Fireflies transcript IDs
            
        Returns:
            List[Dict]: List of complete transcript data (successful requests only)
            
        Raises:
            FirefliesAPIError: For critical API errors that affect all requests
        """
        if not transcript_ids:
            return []
        
        logger.info(f"Fetching details for {len(transcript_ids)} transcripts in parallel")
        
        # Create tasks for parallel execution
        tasks = [
            self.get_transcript_details(transcript_id)
            for transcript_id in transcript_ids
        ]
        
        # Execute requests in parallel with some concurrency control
        semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent requests
        
        async def fetch_with_semaphore(task):
            async with semaphore:
                try:
                    return await task
                except FirefliesAPIError as e:
                    logger.warning(f"Failed to fetch transcript details: {e}")
                    return None
        
        results = await asyncio.gather(*[
            fetch_with_semaphore(task) for task in tasks
        ], return_exceptions=True)
        
        # Filter out failed requests and exceptions
        successful_results = [
            result for result in results
            if result is not None and not isinstance(result, Exception)
        ]
        
        failed_count = len(transcript_ids) - len(successful_results)
        if failed_count > 0:
            logger.warning(f"{failed_count} transcript details failed to fetch")
        
        logger.info(f"Successfully fetched details for {len(successful_results)} transcripts")
        return successful_results
    
    def get_error_message(self, error_code: str) -> str:
        """
        Get human-readable error message for a given error code.
        
        Args:
            error_code: Error code from API response
            
        Returns:
            str: Human-readable error message
        """
        return self.ERROR_CODES.get(error_code, f"Unknown error: {error_code}")
    
    # Synchronous wrapper methods for use in non-async code
    def get_recent_meetings(self, since_date: datetime = None, limit: int = 100) -> List[Dict]:
        """
        Synchronous wrapper for get_recent_transcripts.
        
        Args:
            since_date: Get meetings since this date (default: 7 days ago)
            limit: Maximum number of meetings to retrieve
            
        Returns:
            List of meeting data dictionaries
        """
        import asyncio
        
        # Handle datetime conversion properly to avoid JSON serialization issues
        if since_date is None:
            # Default to 7 days ago
            since_date = datetime.now(timezone.utc) - timedelta(days=7)
        
        # Convert datetime to ISO string format expected by the API
        if isinstance(since_date, datetime):
            from_date_str = since_date.isoformat()
        else:
            from_date_str = since_date
            
        return asyncio.run(self.get_recent_transcripts(from_date_str, limit=limit))
    
    def get_meeting(self, meeting_id: str) -> Optional[Dict]:
        """
        Synchronous wrapper for get_transcript_details.
        
        Args:
            meeting_id: ID of the meeting to retrieve
            
        Returns:
            Meeting data dictionary or None if not found
        """
        import asyncio
        try:
            return asyncio.run(self.get_transcript_details(meeting_id))
        except FirefliesAPIError as e:
            if e.error_code == 'object_not_found':
                return None
            raise

    def is_summary_ready(self, meeting_data: Dict) -> bool:
        """
        Check if a meeting's summary is ready for processing.
        
        Args:
            meeting_data: Meeting data dictionary from Fireflies API
            
        Returns:
            bool: True if summary is ready (status == 'processed'), False otherwise
        """
        try:
            # Handle None or invalid input
            if not meeting_data or not isinstance(meeting_data, dict):
                logger.warning("Invalid meeting data provided for summary readiness check")
                return False
            
            # Navigate to the summary_status field
            meeting_info = meeting_data.get('meeting_info', {})
            if not isinstance(meeting_info, dict):
                logger.warning(f"Meeting {meeting_data.get('id', 'unknown')} has invalid meeting_info structure")
                return False
                
            summary_status = meeting_info.get('summary_status')
            
            if summary_status is None:
                logger.warning(f"Meeting {meeting_data.get('id', 'unknown')} missing summary_status field")
                return False
            
            is_ready = summary_status == 'processed'
            
            if not is_ready:
                logger.info(f"Meeting {meeting_data.get('id', 'unknown')} summary not ready - status: {summary_status}")
            
            return is_ready
            
        except (KeyError, AttributeError, TypeError) as e:
            meeting_id = 'unknown'
            try:
                if meeting_data and isinstance(meeting_data, dict):
                    meeting_id = meeting_data.get('id', 'unknown')
            except:
                pass
            logger.warning(f"Error checking summary readiness for meeting {meeting_id}: {e}")
            return False

    def get_meeting_with_summary_check(self, meeting_id: str) -> Optional[Dict]:
        """
        Get meeting data only if the summary is ready for processing.
        
        Args:
            meeting_id: ID of the meeting to retrieve
            
        Returns:
            Optional[Dict]: Meeting data if summary is ready, None otherwise
        """
        try:
            # Get the meeting data
            meeting_data = self.get_meeting(meeting_id)
            
            if meeting_data is None:
                logger.warning(f"Meeting {meeting_id} not found")
                return None
            
            # Check if summary is ready
            if not self.is_summary_ready(meeting_data):
                # Get current status for logging
                meeting_info = meeting_data.get('meeting_info', {})
                current_status = meeting_info.get('summary_status', 'unknown')
                logger.info(f"Skipping meeting {meeting_id} - summary not ready (current status: {current_status})")
                return None
            
            logger.debug(f"Meeting {meeting_id} summary is ready for processing")
            return meeting_data
            
        except FirefliesAPIError as e:
            logger.error(f"Error retrieving meeting {meeting_id} with summary check: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error checking meeting {meeting_id} summary readiness: {e}")
            return None