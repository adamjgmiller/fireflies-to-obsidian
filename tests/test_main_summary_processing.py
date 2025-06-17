"""
Integration tests for main processing loop with summary readiness checking.

Tests cover the complete process_meetings function to verify it correctly
handles meetings with ready and non-ready summaries.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.main import process_meetings
from src.fireflies_client import FirefliesClient
from src.obsidian_sync import ObsidianSync
from src.state_manager import StateManager


@pytest.fixture
def mock_fireflies_client():
    """Mock FirefliesClient for testing."""
    client = Mock(spec=FirefliesClient)
    return client


@pytest.fixture
def mock_obsidian_sync():
    """Mock ObsidianSync for testing."""
    sync = Mock(spec=ObsidianSync)
    sync.create_meeting_note.return_value = "/path/to/note.md"
    return sync


@pytest.fixture
def mock_state_manager():
    """Mock StateManager for testing."""
    manager = Mock(spec=StateManager)
    manager.is_processed.return_value = False
    return manager


@pytest.fixture
def mock_meeting_ready():
    """Mock meeting data with ready summary."""
    return {
        "id": "meeting_ready_123",
        "title": "Ready Meeting",
        "meeting_info": {
            "fred_joined": True,
            "silent_meeting": False,
            "summary_status": "processed"
        },
        "summary": {
            "overview": "Meeting summary here",
            "action_items": ["Task 1", "Task 2"]
        }
    }


@pytest.fixture
def mock_meeting_processing():
    """Mock meeting data with processing summary."""
    return {
        "id": "meeting_processing_456",
        "title": "Processing Meeting",
        "meeting_info": {
            "fred_joined": True,
            "silent_meeting": False,
            "summary_status": "processing"
        }
    }


@pytest.fixture
def mock_meeting_failed():
    """Mock meeting data with failed summary."""
    return {
        "id": "meeting_failed_789",
        "title": "Failed Meeting",
        "meeting_info": {
            "fred_joined": True,
            "silent_meeting": False,
            "summary_status": "failed"
        }
    }


class TestMainProcessingIntegration:
    """Integration tests for main processing loop with summary readiness."""
    
    @patch('src.main.get_notification_service')
    def test_process_meetings_skips_non_ready_summaries(
        self,
        mock_get_notification_service,
        mock_fireflies_client,
        mock_obsidian_sync,
        mock_state_manager,
        mock_meeting_ready,
        mock_meeting_processing,
        mock_meeting_failed
    ):
        """Test that process_meetings correctly skips meetings with non-ready summaries."""
        # Mock notification service
        mock_notification_service = Mock()
        mock_get_notification_service.return_value = mock_notification_service
        
        # Setup mock for recent meetings list
        recent_meetings = [
            {"id": "meeting_ready_123"},
            {"id": "meeting_processing_456"},
            {"id": "meeting_failed_789"}
        ]
        mock_fireflies_client.get_recent_meetings.return_value = recent_meetings
        
        # Setup get_meeting_with_summary_check to return None for non-ready meetings
        def mock_get_meeting_with_summary_check(meeting_id):
            if meeting_id == "meeting_ready_123":
                return mock_meeting_ready
            else:
                # Non-ready meetings return None
                return None
        
        mock_fireflies_client.get_meeting_with_summary_check.side_effect = mock_get_meeting_with_summary_check
        
        # Run the process
        result = process_meetings(
            mock_fireflies_client,
            mock_obsidian_sync,
            mock_state_manager,
            enable_notifications=False
        )
        
        # Verify only ready meeting was processed
        assert result == 1
        
        # Verify get_meeting_with_summary_check was called for all meetings
        assert mock_fireflies_client.get_meeting_with_summary_check.call_count == 3
        
        # Verify only the ready meeting was created as a note
        mock_obsidian_sync.create_meeting_note.assert_called_once_with(mock_meeting_ready)
        
        # Verify only the ready meeting was marked as processed
        mock_state_manager.mark_processed.assert_called_once_with("meeting_ready_123")
    
    @patch('src.main.get_notification_service')
    def test_process_meetings_processes_ready_summaries_normally(
        self,
        mock_get_notification_service,
        mock_fireflies_client,
        mock_obsidian_sync,
        mock_state_manager,
        mock_meeting_ready
    ):
        """Test that process_meetings processes meetings with ready summaries normally."""
        # Mock notification service
        mock_notification_service = Mock()
        mock_get_notification_service.return_value = mock_notification_service
        
        # Setup mock for recent meetings list
        recent_meetings = [{"id": "meeting_ready_123"}]
        mock_fireflies_client.get_recent_meetings.return_value = recent_meetings
        
        # Setup get_meeting_with_summary_check to return ready meeting
        mock_fireflies_client.get_meeting_with_summary_check.return_value = mock_meeting_ready
        
        # Run the process
        result = process_meetings(
            mock_fireflies_client,
            mock_obsidian_sync,
            mock_state_manager,
            enable_notifications=False
        )
        
        # Verify meeting was processed
        assert result == 1
        
        # Verify the meeting was created as a note
        mock_obsidian_sync.create_meeting_note.assert_called_once_with(mock_meeting_ready)
        
        # Verify the meeting was marked as processed
        mock_state_manager.mark_processed.assert_called_once_with("meeting_ready_123")
    
    @patch('src.main.get_notification_service')
    def test_process_meetings_test_mode_with_ready_meeting(
        self,
        mock_get_notification_service,
        mock_fireflies_client,
        mock_obsidian_sync,
        mock_state_manager,
        mock_meeting_ready
    ):
        """Test process_meetings in test mode with a ready meeting."""
        # Mock notification service
        mock_notification_service = Mock()
        mock_get_notification_service.return_value = mock_notification_service
        
        # Setup get_meeting_with_summary_check to return ready meeting
        mock_fireflies_client.get_meeting_with_summary_check.return_value = mock_meeting_ready
        
        # Run the process in test mode
        result = process_meetings(
            mock_fireflies_client,
            mock_obsidian_sync,
            mock_state_manager,
            meeting_ids=["meeting_ready_123"],
            enable_notifications=False
        )
        
        # Verify meeting was processed
        assert result == 1
        
        # Verify get_meeting_with_summary_check was called for the specific meeting
        mock_fireflies_client.get_meeting_with_summary_check.assert_called_once_with("meeting_ready_123")
        
        # Verify the meeting was created as a note
        mock_obsidian_sync.create_meeting_note.assert_called_once_with(mock_meeting_ready)
        
        # Verify the meeting was marked as processed
        mock_state_manager.mark_processed.assert_called_once_with("meeting_ready_123")
    
    @patch('src.main.get_notification_service')
    def test_process_meetings_test_mode_with_non_ready_meeting(
        self,
        mock_get_notification_service,
        mock_fireflies_client,
        mock_obsidian_sync,
        mock_state_manager
    ):
        """Test process_meetings in test mode with a non-ready meeting."""
        # Mock notification service
        mock_notification_service = Mock()
        mock_get_notification_service.return_value = mock_notification_service
        
        # Setup get_meeting_with_summary_check to return None (non-ready)
        mock_fireflies_client.get_meeting_with_summary_check.return_value = None
        
        # Run the process in test mode
        result = process_meetings(
            mock_fireflies_client,
            mock_obsidian_sync,
            mock_state_manager,
            meeting_ids=["meeting_processing_456"],
            enable_notifications=False
        )
        
        # Verify no meetings were processed
        assert result == 0
        
        # Verify get_meeting_with_summary_check was called for the specific meeting
        mock_fireflies_client.get_meeting_with_summary_check.assert_called_once_with("meeting_processing_456")
        
        # Verify no meeting note was created
        mock_obsidian_sync.create_meeting_note.assert_not_called()
        
        # Verify no meeting was marked as processed
        mock_state_manager.mark_processed.assert_not_called()
    
    @patch('src.main.get_notification_service')
    def test_process_meetings_already_processed_meeting(
        self,
        mock_get_notification_service,
        mock_fireflies_client,
        mock_obsidian_sync,
        mock_state_manager,
        mock_meeting_ready
    ):
        """Test that already processed meetings are skipped even if summary is ready."""
        # Mock notification service
        mock_notification_service = Mock()
        mock_get_notification_service.return_value = mock_notification_service
        
        # Setup mock for recent meetings list
        recent_meetings = [{"id": "meeting_ready_123"}]
        mock_fireflies_client.get_recent_meetings.return_value = recent_meetings
        
        # Setup get_meeting_with_summary_check to return ready meeting
        mock_fireflies_client.get_meeting_with_summary_check.return_value = mock_meeting_ready
        
        # Mark meeting as already processed
        mock_state_manager.is_processed.return_value = True
        
        # Run the process
        result = process_meetings(
            mock_fireflies_client,
            mock_obsidian_sync,
            mock_state_manager,
            enable_notifications=False
        )
        
        # Verify no meetings were processed
        assert result == 0
        
        # Verify the meeting was fetched but not created as a note
        mock_fireflies_client.get_meeting_with_summary_check.assert_called_once_with("meeting_ready_123")
        mock_obsidian_sync.create_meeting_note.assert_not_called()
        
        # Verify the meeting was not marked as processed again
        mock_state_manager.mark_processed.assert_not_called()
    
    @patch('src.main.get_notification_service')
    def test_process_meetings_mixed_readiness_states(
        self,
        mock_get_notification_service,
        mock_fireflies_client,
        mock_obsidian_sync,
        mock_state_manager,
        mock_meeting_ready
    ):
        """Test process_meetings with a mix of ready and non-ready meetings."""
        # Mock notification service
        mock_notification_service = Mock()
        mock_get_notification_service.return_value = mock_notification_service
        
        # Setup mock for recent meetings list
        recent_meetings = [
            {"id": "meeting_ready_123"},
            {"id": "meeting_processing_456"},
            {"id": "meeting_failed_789"},
            {"id": "meeting_ready_2_101"}
        ]
        mock_fireflies_client.get_recent_meetings.return_value = recent_meetings
        
        # Create second ready meeting
        mock_meeting_ready_2 = {
            "id": "meeting_ready_2_101",
            "title": "Another Ready Meeting",
            "meeting_info": {
                "fred_joined": True,
                "silent_meeting": False,
                "summary_status": "processed"
            }
        }
        
        # Setup get_meeting_with_summary_check
        def mock_get_meeting_with_summary_check(meeting_id):
            if meeting_id == "meeting_ready_123":
                return mock_meeting_ready
            elif meeting_id == "meeting_ready_2_101":
                return mock_meeting_ready_2
            else:
                # Non-ready meetings return None
                return None
        
        mock_fireflies_client.get_meeting_with_summary_check.side_effect = mock_get_meeting_with_summary_check
        
        # Run the process
        result = process_meetings(
            mock_fireflies_client,
            mock_obsidian_sync,
            mock_state_manager,
            enable_notifications=False
        )
        
        # Verify only ready meetings were processed
        assert result == 2
        
        # Verify get_meeting_with_summary_check was called for all meetings
        assert mock_fireflies_client.get_meeting_with_summary_check.call_count == 4
        
        # Verify both ready meetings were created as notes
        assert mock_obsidian_sync.create_meeting_note.call_count == 2
        mock_obsidian_sync.create_meeting_note.assert_any_call(mock_meeting_ready)
        mock_obsidian_sync.create_meeting_note.assert_any_call(mock_meeting_ready_2)
        
        # Verify both ready meetings were marked as processed
        assert mock_state_manager.mark_processed.call_count == 2
        mock_state_manager.mark_processed.assert_any_call("meeting_ready_123")
        mock_state_manager.mark_processed.assert_any_call("meeting_ready_2_101") 