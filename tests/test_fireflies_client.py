"""
Unit tests for Fireflies API client.

Tests cover GraphQL queries, authentication, error handling, rate limiting,
and pagination functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

import httpx

from src.fireflies_client import (
    FirefliesClient,
    FirefliesAPIError
)


@pytest.fixture
def api_key():
    """Test API key fixture."""
    return "test_fireflies_api_key_12345"


@pytest.fixture
def client(api_key):
    """FirefliesClient fixture."""
    return FirefliesClient(api_key=api_key)


@pytest.fixture
def mock_transcript_response():
    """Mock transcript response data."""
    return {
        "data": {
            "transcripts": [
                {
                    "id": "transcript_123",
                    "title": "Test Meeting",
                    "date": "2024-06-15T14:30:00.000Z",
                    "dateString": "June 15, 2024 2:30:00 PM UTC",
                    "organizer_email": "organizer@example.com",
                    "duration": 3600
                },
                {
                    "id": "transcript_456",
                    "title": "Another Meeting",
                    "date": "2024-06-16T10:00:00.000Z",
                    "dateString": "June 16, 2024 10:00:00 AM UTC",
                    "organizer_email": "host@example.com",
                    "duration": 2400
                }
            ]
        }
    }


@pytest.fixture
def mock_transcript_details_response():
    """Mock transcript details response data."""
    return {
        "data": {
            "transcript": {
                "id": "transcript_123",
                "title": "Test Meeting",
                "date": "2024-06-15T14:30:00.000Z",
                "dateString": "June 15, 2024 2:30:00 PM UTC",
                "duration": 3600,
                "organizer_email": "organizer@example.com",
                "participants": ["user1@example.com", "user2@example.com"],
                "fireflies_users": ["fireflies@example.com"],
                "meeting_attendees": [
                    {
                        "displayName": "John Doe",
                        "email": "john@example.com",
                        "phoneNumber": "+1234567890",
                        "name": "John Doe",
                        "location": "New York"
                    }
                ],
                "speakers": [
                    {"id": "speaker_1", "name": "John Doe"},
                    {"id": "speaker_2", "name": "Jane Smith"}
                ],
                "sentences": [
                    {
                        "index": 0,
                        "speaker_name": "John Doe",
                        "speaker_id": "speaker_1",
                        "text": "Hello everyone, let's start the meeting.",
                        "raw_text": "Hello everyone, let's start the meeting.",
                        "start_time": 5.2,
                        "end_time": 8.1
                    },
                    {
                        "index": 1,
                        "speaker_name": "Jane Smith",
                        "speaker_id": "speaker_2",
                        "text": "Thanks John. Let's review the agenda.",
                        "raw_text": "Thanks John. Let's review the agenda.",
                        "start_time": 8.5,
                        "end_time": 11.3
                    }
                ],
                "summary": {
                    "keywords": ["meeting", "agenda", "review"],
                    "action_items": ["Review quarterly reports", "Schedule follow-up meeting"],
                    "outline": "Meeting outline here",
                    "overview": "Meeting overview here",
                    "shorthand_bullet": "• Key point 1\n• Key point 2",
                    "bullet_gist": "Main points discussed",
                    "gist": "Brief summary",
                    "short_summary": "Short meeting summary",
                    "short_overview": "Brief overview",
                    "meeting_type": "team_meeting",
                    "topics_discussed": ["Project updates", "Budget review"],
                    "transcript_chapters": []
                },
                "transcript_url": "https://app.fireflies.ai/view/transcript_123",
                "meeting_link": "https://zoom.us/j/123456789",
                "calendar_id": "cal_123",
                "cal_id": "calendar_456",
                "calendar_type": "google"
            }
        }
    }


class TestFirefliesClientInitialization:
    """Test FirefliesClient initialization."""
    
    def test_init_with_valid_api_key(self, api_key):
        """Test successful initialization with valid API key."""
        client = FirefliesClient(api_key=api_key)
        
        assert client.api_key == api_key
        assert client.base_url == "https://api.fireflies.ai/graphql"
        assert client.headers["Authorization"] == f"Bearer {api_key}"
        assert client.headers["Content-Type"] == "application/json"
    
    def test_init_with_custom_base_url(self, api_key):
        """Test initialization with custom base URL."""
        custom_url = "https://custom.fireflies.ai/graphql"
        client = FirefliesClient(api_key=api_key, base_url=custom_url)
        
        assert client.base_url == custom_url
    
    def test_init_with_empty_api_key(self):
        """Test initialization fails with empty API key."""
        with pytest.raises(ValueError, match="API key is required"):
            FirefliesClient(api_key="")
    
    def test_init_with_none_api_key(self):
        """Test initialization fails with None API key."""
        with pytest.raises(ValueError, match="API key is required"):
            FirefliesClient(api_key=None)


class TestFirefliesClientRequests:
    """Test FirefliesClient API request functionality."""
    
    @pytest.mark.asyncio
    async def test_make_request_success(self, client):
        """Test successful GraphQL request."""
        mock_response_data = {"data": {"test": "success"}}
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client.post.return_value = mock_response
            
            result = await client._make_request("query { test }")
            
            assert result == mock_response_data
            mock_client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_make_request_graphql_error(self, client):
        """Test GraphQL error handling."""
        error_response = {
            "errors": [
                {
                    "message": "Invalid query",
                    "extensions": {"code": "invalid_arguments"}
                }
            ]
        }
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = error_response
            mock_client.post.return_value = mock_response
            
            with pytest.raises(FirefliesAPIError) as exc_info:
                await client._make_request("invalid query")
            
            assert "Invalid query" in str(exc_info.value)
            assert exc_info.value.error_code == "invalid_arguments"
    
    @pytest.mark.asyncio
    async def test_make_request_rate_limit(self, client):
        """Test rate limit handling with retry."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # First request: rate limited
            rate_limit_response = Mock()
            rate_limit_response.status_code = 429
            rate_limit_response.headers = {"Retry-After": "1"}
            
            # Second request: success
            success_response = Mock()
            success_response.status_code = 200
            success_response.json.return_value = {"data": {"success": True}}
            
            mock_client.post.side_effect = [rate_limit_response, success_response]
            
            with patch('asyncio.sleep') as mock_sleep:
                result = await client._make_request("query { test }")
                
                assert result == {"data": {"success": True}}
                mock_sleep.assert_called_once_with(1)
                assert mock_client.post.call_count == 2
    
    @pytest.mark.asyncio
    async def test_make_request_forbidden(self, client):
        """Test forbidden (403) error handling."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = Mock()
            mock_response.status_code = 403
            mock_client.post.return_value = mock_response
            
            with pytest.raises(FirefliesAPIError) as exc_info:
                await client._make_request("query { test }")
            
            assert "API key invalid or expired" in str(exc_info.value)
            assert exc_info.value.error_code == "forbidden"
    
    @pytest.mark.asyncio
    async def test_make_request_network_error(self, client):
        """Test network error handling with retry."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Simulate network error
            mock_client.post.side_effect = httpx.RequestError("Network error")
            
            with patch('asyncio.sleep') as mock_sleep:
                with pytest.raises(FirefliesAPIError) as exc_info:
                    await client._make_request("query { test }", max_retries=2)
                
                assert "Network error" in str(exc_info.value)
                # Should have made 2 attempts (original + 1 retry)
                assert mock_client.post.call_count == 2
                # Should have slept once between retries
                mock_sleep.assert_called_once_with(1)  # 2^0 = 1


class TestFirefliesClientTranscripts:
    """Test transcript retrieval methods."""
    
    @pytest.mark.asyncio
    async def test_get_recent_transcripts(self, client, mock_transcript_response):
        """Test getting recent transcripts."""
        with patch.object(client, '_make_request', return_value=mock_transcript_response):
            transcripts = await client.get_recent_transcripts("2024-06-13T00:00:00.000Z")
            
            assert len(transcripts) == 2
            assert transcripts[0]["id"] == "transcript_123"
            assert transcripts[1]["id"] == "transcript_456"
    
    @pytest.mark.asyncio
    async def test_get_recent_transcripts_with_params(self, client, mock_transcript_response):
        """Test getting recent transcripts with all parameters."""
        with patch.object(client, '_make_request', return_value=mock_transcript_response) as mock_request:
            await client.get_recent_transcripts(
                from_date="2024-06-13T00:00:00.000Z",
                to_date="2024-06-20T00:00:00.000Z",
                limit=5,
                skip=10
            )
            
            # Check that the request was made with correct variables
            call_args = mock_request.call_args
            variables = call_args[1]['variables']  # Second argument (keyword args)
            
            assert variables["fromDate"] == "2024-06-13T00:00:00.000Z"
            assert variables["toDate"] == "2024-06-20T00:00:00.000Z"
            assert variables["limit"] == 5
            assert variables["skip"] == 10
    
    @pytest.mark.asyncio
    async def test_get_transcript_details(self, client, mock_transcript_details_response):
        """Test getting transcript details."""
        with patch.object(client, '_make_request', return_value=mock_transcript_details_response):
            transcript = await client.get_transcript_details("transcript_123")
            
            assert transcript["id"] == "transcript_123"
            assert transcript["title"] == "Test Meeting"
            assert len(transcript["sentences"]) == 2
            assert len(transcript["summary"]["action_items"]) == 2
    
    @pytest.mark.asyncio
    async def test_get_transcript_details_not_found(self, client):
        """Test transcript not found error."""
        empty_response = {"data": {"transcript": None}}
        
        with patch.object(client, '_make_request', return_value=empty_response):
            with pytest.raises(FirefliesAPIError) as exc_info:
                await client.get_transcript_details("nonexistent_id")
            
            assert "not found or not accessible" in str(exc_info.value)
            assert exc_info.value.error_code == "object_not_found"


class TestFirefliesClientPagination:
    """Test pagination functionality."""
    
    @pytest.mark.asyncio
    async def test_get_all_transcripts_single_page(self, client):
        """Test pagination with single page of results."""
        mock_response = {
            "data": {
                "transcripts": [
                    {"id": "transcript_1", "title": "Meeting 1"},
                    {"id": "transcript_2", "title": "Meeting 2"}
                ]
            }
        }
        
        with patch.object(client, 'get_recent_transcripts', return_value=mock_response["data"]["transcripts"]):
            transcripts = await client.get_all_transcripts_since("2024-06-13T00:00:00.000Z", batch_size=10)
            
            assert len(transcripts) == 2
            assert transcripts[0]["id"] == "transcript_1"
    
    @pytest.mark.asyncio
    async def test_get_all_transcripts_multiple_pages(self, client):
        """Test pagination with multiple pages."""
        # Mock responses for multiple pages
        page1_response = [{"id": f"transcript_{i}", "title": f"Meeting {i}"} for i in range(1, 6)]  # 5 items
        page2_response = [{"id": f"transcript_{i}", "title": f"Meeting {i}"} for i in range(6, 9)]  # 3 items
        
        with patch.object(client, 'get_recent_transcripts', side_effect=[page1_response, page2_response]):
            with patch('asyncio.sleep'):  # Mock sleep to speed up tests
                transcripts = await client.get_all_transcripts_since("2024-06-13T00:00:00.000Z", batch_size=5)
                
                assert len(transcripts) == 8
                assert transcripts[0]["id"] == "transcript_1"
                assert transcripts[7]["id"] == "transcript_8"
    
    @pytest.mark.asyncio
    async def test_get_transcript_details_batch(self, client, mock_transcript_details_response):
        """Test batch transcript details retrieval."""
        transcript_ids = ["transcript_123", "transcript_456", "transcript_789"]
        
        with patch.object(client, 'get_transcript_details', return_value=mock_transcript_details_response["data"]["transcript"]) as mock_details:
            results = await client.get_transcript_details_batch(transcript_ids)
            
            assert len(results) == 3
            assert mock_details.call_count == 3
    
    @pytest.mark.asyncio
    async def test_get_transcript_details_batch_with_failures(self, client, mock_transcript_details_response):
        """Test batch retrieval with some failures."""
        transcript_ids = ["transcript_123", "transcript_456", "transcript_789"]
        
        def mock_get_details(transcript_id):
            if transcript_id == "transcript_456":
                raise FirefliesAPIError("Not found", error_code="object_not_found")
            return mock_transcript_details_response["data"]["transcript"]
        
        with patch.object(client, 'get_transcript_details', side_effect=mock_get_details):
            results = await client.get_transcript_details_batch(transcript_ids)
            
            # Should get 2 successful results (excluding the failed one)
            assert len(results) == 2


class TestFirefliesClientConnectionTest:
    """Test API connection testing."""
    
    @pytest.mark.asyncio
    async def test_test_connection_success(self, client):
        """Test successful connection test."""
        mock_response = {"data": {"transcripts": []}}
        
        with patch.object(client, 'get_recent_transcripts', return_value=[]):
            result = await client.test_connection()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_test_connection_failure(self, client):
        """Test failed connection test."""
        with patch.object(client, 'get_recent_transcripts', side_effect=FirefliesAPIError("Connection failed")):
            with pytest.raises(FirefliesAPIError):
                await client.test_connection()


class TestFirefliesClientUtils:
    """Test utility methods."""
    
    def test_get_error_message_known_code(self, client):
        """Test getting error message for known error code."""
        message = client.get_error_message("too_many_requests")
        assert message == "Rate limit exceeded (HTTP 429)"
    
    def test_get_error_message_unknown_code(self, client):
        """Test getting error message for unknown error code."""
        message = client.get_error_message("unknown_error")
        assert message == "Unknown error: unknown_error"


class TestFirefliesAPIError:
    """Test FirefliesAPIError exception class."""
    
    def test_api_error_basic(self):
        """Test basic API error creation."""
        error = FirefliesAPIError("Test error")
        assert str(error) == "Test error"
        assert error.error_code is None
        assert error.response_data is None
    
    def test_api_error_with_code_and_data(self):
        """Test API error with error code and response data."""
        response_data = {"errors": [{"message": "Test error"}]}
        error = FirefliesAPIError("Test error", error_code="test_error", response_data=response_data)
        
        assert str(error) == "Test error"
        assert error.error_code == "test_error"
        assert error.response_data == response_data 