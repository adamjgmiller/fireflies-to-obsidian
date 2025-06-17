"""
Unit tests for Markdown formatter.

Tests cover Markdown template generation, YAML frontmatter, transcript formatting,
and filename generation functionality.
"""

import pytest
from datetime import datetime
from unittest.mock import patch

from src.markdown_formatter import MarkdownFormatter


@pytest.fixture
def formatter():
    """MarkdownFormatter fixture."""
    return MarkdownFormatter()


@pytest.fixture
def sample_meeting_data():
    """Sample meeting data matching Fireflies API structure."""
    return {
        "id": "transcript_123",
        "title": "Test Meeting",
        "date": "2024-06-15T14:30:00.000Z",
        "dateString": "June 15, 2024 2:30:00 PM UTC",
        "duration": 60,
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
            },
            {
                "displayName": "Jane Smith",
                "email": "jane@example.com",
                "phoneNumber": "+0987654321",
                "name": "Jane Smith",
                "location": "San Francisco"
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
            },
            {
                "index": 2,
                "speaker_name": "John Doe",
                "speaker_id": "speaker_1",
                "text": "First item is the quarterly review.",
                "raw_text": "First item is the quarterly review.",
                "start_time": 12.0,
                "end_time": 15.2
            }
        ],
        "summary": {
            "keywords": ["meeting", "agenda", "review", "quarterly"],
            "action_items": ["Review quarterly reports", "Schedule follow-up meeting"],
            "outline": "Meeting outline here",
            "overview": "This meeting covered quarterly reviews and planning.",
            "shorthand_bullet": "• Quarterly review discussion\n• Follow-up meeting planning",
            "bullet_gist": "Main points discussed",
            "gist": "Brief summary",
            "short_summary": "Short meeting summary",
            "short_overview": "Brief overview",
            "meeting_type": "team_meeting",
            "topics_discussed": ["Project updates", "Budget review", "Team planning"],
            "transcript_chapters": []
        },
        "transcript_url": "https://app.fireflies.ai/view/transcript_123",
        "meeting_link": "https://zoom.us/j/123456789",
        "calendar_id": "cal_123",
        "cal_id": "calendar_456",
        "calendar_type": "google"
    }


@pytest.fixture
def minimal_meeting_data():
    """Minimal meeting data with only required fields."""
    return {
        "id": "minimal_123",
        "title": "Minimal Meeting",
        "date": "2024-06-15T14:30:00.000Z"
    }


class TestMarkdownFormatterInitialization:
    """Test MarkdownFormatter initialization."""
    
    def test_init_default(self):
        """Test default initialization."""
        formatter = MarkdownFormatter()
        assert formatter.template_config == {}
    
    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = {"custom_option": "value"}
        formatter = MarkdownFormatter(template_config=config)
        assert formatter.template_config == config


class TestMarkdownFormatterFormatMeeting:
    """Test complete meeting formatting."""
    
    def test_format_meeting_complete(self, formatter, sample_meeting_data):
        """Test formatting complete meeting data."""
        result = formatter.format_meeting(sample_meeting_data)
        
        # Check that all sections are present
        assert "---" in result  # YAML frontmatter
        assert "title: \"Test Meeting\"" in result
        assert "# Test Meeting" in result  # Header
        assert "## Meeting Details" in result
        assert "## Attendees" in result
        assert "## Summary" in result
        assert "## Transcript" in result
        
        # Check specific content
        assert "organizer@example.com" in result
        assert "John Doe" in result
        assert "Jane Smith" in result
        assert "Review quarterly reports" in result
    
    def test_format_meeting_minimal(self, formatter, minimal_meeting_data):
        """Test formatting minimal meeting data."""
        result = formatter.format_meeting(minimal_meeting_data)
        
        # Should still have basic structure
        assert "---" in result
        assert "# Minimal Meeting" in result
        assert "## Meeting Details" in result
        assert "## Attendees" in result
        assert "## Summary" in result
        assert "## Transcript" in result


class TestMarkdownFormatterFrontmatter:
    """Test YAML frontmatter generation."""
    
    def test_generate_frontmatter_complete(self, formatter, sample_meeting_data):
        """Test frontmatter with complete data."""
        result = formatter._generate_frontmatter(sample_meeting_data)
        
        assert result.startswith("---")
        assert result.endswith("---")
        assert "title: \"Test Meeting\"" in result
        assert "meeting_id: \"transcript_123\"" in result
        assert "date: \"2024-06-15T14:30:00.000Z\"" in result
        assert "duration: 60" in result
        assert "organizer: \"organizer@example.com\"" in result
        assert "meeting_type: \"team_meeting\"" in result
        
        # Check attendees list
        assert "attendees:" in result
        assert "- \"john@example.com\"" in result
        assert "- \"jane@example.com\"" in result
        
        # Check that tags include the meeting_type
        assert "tags:" in result
        assert "- \"team_meeting\"" in result
        
        # Check URLs
        assert "transcript_url: \"https://app.fireflies.ai/view/transcript_123\"" in result
        assert "meeting_link: \"https://zoom.us/j/123456789\"" in result
        
        # Check tags
        assert "tags:" in result
        assert "- \"fireflies\"" in result
        assert "- \"meeting\"" in result
        assert "- \"team_meeting\"" in result
    
    def test_generate_frontmatter_minimal(self, formatter, minimal_meeting_data):
        """Test frontmatter with minimal data."""
        result = formatter._generate_frontmatter(minimal_meeting_data)
        
        assert result.startswith("---")
        assert result.endswith("---")
        assert "title: \"Minimal Meeting\"" in result
        assert "meeting_id: \"minimal_123\"" in result
        assert "duration: 0" in result
        assert "organizer: \"\"" in result
        # meeting_type is only added if it has a meaningful value
    
    def test_generate_frontmatter_fallback_participants(self, formatter):
        """Test frontmatter falls back to participants when meeting_attendees is empty."""
        data = {
            "id": "test_123",
            "title": "Test",
            "participants": ["user1@example.com", "user2@example.com"],
            "meeting_attendees": [],
            "summary": {}
        }
        
        result = formatter._generate_frontmatter(data)
        assert "- \"user1@example.com\"" in result
        assert "- \"user2@example.com\"" in result


class TestMarkdownFormatterHeader:
    """Test header generation."""
    
    def test_generate_header_complete(self, formatter, sample_meeting_data):
        """Test header with complete data."""
        result = formatter._generate_header(sample_meeting_data)
        
        assert "# Test Meeting" in result
        assert "**Date:** June 15, 2024 2:30:00 PM UTC" in result
    
    def test_generate_header_minimal(self, formatter, minimal_meeting_data):
        """Test header with minimal data."""
        result = formatter._generate_header(minimal_meeting_data)
        
        assert "# Minimal Meeting" in result
        assert "**Date:** " in result


class TestMarkdownFormatterMeetingDetails:
    """Test meeting details generation."""
    
    def test_generate_meeting_details_complete(self, formatter, sample_meeting_data):
        """Test meeting details with complete data."""
        result = formatter._generate_meeting_details(sample_meeting_data)
        
        assert "## Meeting Details" in result
        assert "- **Duration:** 60m" in result  # 60 minutes from the test data
        assert "- **Organizer:** organizer@example.com" in result
        assert "- **Transcript URL:** [View in Fireflies](https://app.fireflies.ai/view/transcript_123)" in result
        assert "- **Meeting Link:** [Join Meeting](https://zoom.us/j/123456789)" in result
    
    def test_generate_meeting_details_duration_with_seconds(self, formatter):
        """Test duration formatting with seconds."""
        data = {"duration": 61.25}  # 61.25 minutes = 61 minutes and 15 seconds
        result = formatter._generate_meeting_details(data)
        
        assert "- **Duration:** 61m 15s" in result
    
    def test_generate_meeting_details_real_fireflies_duration(self, formatter):
        """Test duration formatting with real Fireflies API data."""
        data = {"duration": 41.25}  # Real example from debug file: 41.25 minutes
        result = formatter._generate_meeting_details(data)
        
        assert "- **Duration:** 41m 15s" in result
    
    def test_generate_meeting_details_minimal(self, formatter, minimal_meeting_data):
        """Test meeting details with minimal data."""
        result = formatter._generate_meeting_details(minimal_meeting_data)
        
        assert "## Meeting Details" in result
        assert "- **Duration:** 0m" in result
        assert "- **Organizer:** " in result


class TestMarkdownFormatterAttendees:
    """Test attendees section generation."""
    
    def test_generate_attendees_with_meeting_attendees(self, formatter, sample_meeting_data):
        """Test attendees section with detailed meeting_attendees."""
        result = formatter._generate_attendees_section(sample_meeting_data)
        
        assert "## Attendees" in result
        assert "- **John Doe** (john@example.com) - New York" in result
        assert "- **Jane Smith** (jane@example.com) - San Francisco" in result
    
    def test_generate_attendees_fallback_to_participants(self, formatter):
        """Test fallback to participants list."""
        data = {
            "meeting_attendees": [],
            "participants": ["user1@example.com", "user2@example.com"]
        }
        
        result = formatter._generate_attendees_section(data)
        
        assert "## Attendees" in result
        assert "- user1@example.com" in result
        assert "- user2@example.com" in result
    
    def test_generate_attendees_no_data(self, formatter):
        """Test attendees section with no data."""
        data = {"meeting_attendees": [], "participants": []}
        
        result = formatter._generate_attendees_section(data)
        
        assert "## Attendees" in result
        assert "- No attendee information available" in result
    
    def test_generate_attendees_partial_data(self, formatter):
        """Test attendees with partial data."""
        data = {
            "meeting_attendees": [
                {"displayName": "John Doe"},  # No email or location
                {"email": "jane@example.com"},  # No name
                {"name": "Bob Smith", "email": "bob@example.com", "location": "Chicago"}
            ],
            "participants": []
        }
        
        result = formatter._generate_attendees_section(data)
        
        assert "- **John Doe**" in result
        assert "- **Unknown** (jane@example.com)" in result
        assert "- **Bob Smith** (bob@example.com) - Chicago" in result


class TestMarkdownFormatterSummary:
    """Test summary section generation."""
    
    def test_generate_summary_complete(self, formatter, sample_meeting_data):
        """Test summary with complete data."""
        result = formatter._generate_summary_section(sample_meeting_data)
        
        assert "## Summary" in result
        assert "### Overview" in result
        assert "This meeting covered quarterly reviews and planning." in result
        assert "### Key Points" in result
        assert "• Quarterly review discussion" in result
        assert "### Action Items" in result
        assert "- [ ] Review quarterly reports" in result
        assert "- [ ] Schedule follow-up meeting" in result
        assert "### Topics Discussed" in result
        assert "- Project updates" in result
        assert "- Budget review" in result
        assert "### Keywords" in result
        assert "meeting, agenda, review, quarterly" in result
    
    def test_generate_summary_minimal(self, formatter):
        """Test summary with minimal data."""
        data = {"summary": {}}
        
        result = formatter._generate_summary_section(data)
        
        assert "## Summary" in result
        # Should not have subsections if no data
        assert "### Overview" not in result
        assert "### Key Points" not in result
    
    def test_generate_summary_fallback_overview(self, formatter):
        """Test overview fallback to short_overview."""
        data = {
            "summary": {
                "short_overview": "Brief meeting overview"
            }
        }
        
        result = formatter._generate_summary_section(data)
        
        assert "### Overview" in result
        assert "Brief meeting overview" in result


class TestMarkdownFormatterTranscript:
    """Test transcript section generation."""
    
    def test_generate_transcript_with_sentences(self, formatter, sample_meeting_data):
        """Test transcript with sentences data."""
        result = formatter._generate_transcript_section(sample_meeting_data)
        
        assert "## Transcript" in result
        assert "**John Doe** `[00:05]`: Hello everyone, let's start the meeting." in result
        assert "**John Doe** `[00:12]`: First item is the quarterly review." in result
        assert "**Jane Smith** `[00:08]`: Thanks John. Let's review the agenda." in result
    
    def test_generate_transcript_no_sentences(self, formatter):
        """Test transcript with no sentences."""
        data = {"sentences": []}
        
        result = formatter._generate_transcript_section(data)
        
        assert "## Transcript" in result
        assert "*No transcript available*" in result
    
    def test_generate_transcript_speaker_grouping(self, formatter):
        """Test that sentences are properly grouped by speaker."""
        data = {
            "sentences": [
                {"speaker_name": "Alice", "text": "First sentence.", "start_time": 0},
                {"speaker_name": "Alice", "text": "Second sentence.", "start_time": 5},
                {"speaker_name": "Bob", "text": "Bob's sentence.", "start_time": 10},
                {"speaker_name": "Alice", "text": "Alice again.", "start_time": 15}
            ]
        }
        
        result = formatter._generate_transcript_section(data)
        
        # Alice's first two sentences should be grouped
        assert "**Alice** `[00:00]`: First sentence. Second sentence." in result
        assert "**Bob** `[00:10]`: Bob's sentence." in result
        assert "**Alice** `[00:15]`: Alice again." in result
    
    def test_generate_transcript_missing_data(self, formatter):
        """Test transcript with missing speaker names and text."""
        data = {
            "sentences": [
                {"text": "Text without speaker", "start_time": 0},
                {"speaker_name": "Alice", "start_time": 5},  # No text
                {"speaker_name": "Bob", "text": "Bob's text", "start_time": 10}
            ]
        }
        
        result = formatter._generate_transcript_section(data)
        
        assert "**Unknown Speaker** `[00:00]`: Text without speaker" in result
        assert "**Bob** `[00:10]`: Bob's text" in result


class TestMarkdownFormatterFilename:
    """Test filename generation."""
    
    def test_format_filename_complete(self, formatter, sample_meeting_data):
        """Test filename with complete data."""
        result = formatter.format_filename(sample_meeting_data)
        
        assert result == "2024-06-15-14-30-Test-Meeting.md"
    
    def test_format_filename_long_title(self, formatter):
        """Test filename with very long title."""
        data = {
            "date": "2024-06-15T14:30:00.000Z",
            "title": "This is a very long meeting title that should be truncated because it exceeds the maximum length limit"
        }
        
        result = formatter.format_filename(data)
        
        assert len(result.replace("2024-06-15-14-30-", "").replace(".md", "")) <= 50
        assert result.startswith("2024-06-15-14-30-")
        assert result.endswith(".md")
    
    def test_format_filename_special_characters(self, formatter):
        """Test filename with special characters in title."""
        data = {
            "date": "2024-06-15T14:30:00.000Z",
            "title": "Meeting with / \\ : * ? \" < > | special chars"
        }
        
        result = formatter.format_filename(data)
        
        assert result == "2024-06-15-14-30-Meeting-with-special-chars.md"
    
    def test_format_filename_no_date(self, formatter):
        """Test filename with no date (should use current time)."""
        data = {
            "title": "Test Meeting",
            "id": "test_123"
        }
        
        with patch('src.markdown_formatter.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2024-06-15-10-00"
            
            result = formatter.format_filename(data)
            
            assert result == "2024-06-15-10-00-Test-Meeting.md"
    
    def test_format_filename_error_fallback(self, formatter):
        """Test filename generation error fallback."""
        data = {
            "id": "error_test",
            "date": "invalid_date_format"
        }
        
        # This should trigger the exception handling
        result = formatter.format_filename(data)
        
        assert result == "meeting-error_test.md"
    
    def test_format_filename_no_title(self, formatter):
        """Test filename with no title."""
        data = {
            "date": "2024-06-15T14:30:00.000Z",
            "id": "no_title_123"
        }
        
        result = formatter.format_filename(data)
        
        assert result == "2024-06-15-14-30-Untitled-Meeting.md"


class TestMarkdownFormatterCustomConfig:
    """Test custom template configuration."""
    
    def test_custom_config_storage(self):
        """Test that custom config is stored correctly."""
        config = {"option1": "value1", "option2": "value2"}
        formatter = MarkdownFormatter(template_config=config)
        
        assert formatter.template_config == config


class TestMarkdownFormatterEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_meeting_data(self, formatter):
        """Test handling of empty meeting data."""
        result = formatter.format_meeting({})
        
        # Should not crash and should have basic structure
        assert "---" in result
        assert "# Untitled Meeting" in result
    
    def test_none_values_in_data(self, formatter):
        """Test handling of None values in meeting data."""
        data = {
            "id": None,
            "title": None,
            "date": None,
            "summary": None,
            "sentences": None
        }
        
        result = formatter.format_meeting(data)
        
        # Should handle None values gracefully
        assert "title: \"Untitled Meeting\"" in result
        assert "## Transcript" in result
        assert "*No transcript available*" in result 