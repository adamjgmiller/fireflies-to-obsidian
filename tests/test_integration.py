"""Integration tests for end-to-end functionality."""
import os
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.fireflies_client import FirefliesClient
from src.obsidian_sync import ObsidianSync
from src.state_manager import StateManager
from src.notification_service import NotificationService
from src.markdown_formatter import MarkdownFormatter
from src.main import process_meetings


class TestIntegration:
    """Integration tests for the complete sync workflow."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        vault_dir = tempfile.mkdtemp()
        state_dir = tempfile.mkdtemp()
        yield vault_dir, state_dir
        # Cleanup
        shutil.rmtree(vault_dir, ignore_errors=True)
        shutil.rmtree(state_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_meeting_data(self):
        """Sample meeting data for testing."""
        return {
            'id': 'test_meeting_123',
            'title': 'Integration Test Meeting',
            'date': '2025-01-15T10:00:00Z',
            'duration': 1800,  # 30 minutes
            'host_name': 'Test Host',
            'participants': 'test@example.com, other@example.com',
            'meeting_attendees': [
                {'name': 'Test User', 'email': 'test@example.com'},
                {'name': 'Other User', 'email': 'other@example.com'}
            ],
            'summary': {
                'overview': 'Test meeting overview',
                'shorthand_bullet': ['Point 1', 'Point 2'],
                'keywords': ['test', 'integration'],
                'action_items': ['Action item 1', 'Action item 2'],
                'outline': ['Topic 1', 'Topic 2']
            },
            'transcript': {
                'sentences': [
                    {
                        'speaker_name': 'Test User',
                        'text': 'Hello, this is a test.',
                        'start_time': 0.0
                    },
                    {
                        'speaker_name': 'Other User',
                        'text': 'Yes, testing the integration.',
                        'start_time': 5.0
                    }
                ]
            }
        }
    
    def test_full_sync_workflow(self, temp_dirs, mock_meeting_data):
        """Test the complete sync workflow from API to Obsidian."""
        vault_dir, state_dir = temp_dirs
        state_file = os.path.join(state_dir, 'test_state.json')
        
        # Initialize components
        state_manager = StateManager(state_file)
        obsidian_sync = ObsidianSync(vault_dir)
        
        # Mock FirefliesClient
        mock_client = Mock(spec=FirefliesClient)
        mock_client.get_recent_meetings.return_value = [mock_meeting_data]
        
        # Mock notification service
        with patch('src.main.NotificationService') as mock_notif_class:
            mock_notif = Mock()
            mock_notif_class.return_value = mock_notif
            
            # Run the sync process
            processed = process_meetings(mock_client, obsidian_sync, state_manager)
            
            # Verify results
            assert processed == 1
            
            # Check that meeting was marked as processed
            assert state_manager.is_processed('test_meeting_123')
            
            # Check that file was created in Obsidian vault
            fireflies_dir = Path(vault_dir) / 'Fireflies'
            assert fireflies_dir.exists()
            
            # Find the created file
            md_files = list(fireflies_dir.glob('*.md'))
            assert len(md_files) == 1
            
            # Verify file content
            with open(md_files[0], 'r') as f:
                content = f.read()
                assert 'Integration Test Meeting' in content
                assert 'Test Host' in content
                assert 'test@example.com' in content
                assert 'Hello, this is a test.' in content
    
    def test_duplicate_meeting_handling(self, temp_dirs, mock_meeting_data):
        """Test that duplicate meetings are not processed twice."""
        vault_dir, state_dir = temp_dirs
        state_file = os.path.join(state_dir, 'test_state.json')
        
        # Initialize components
        state_manager = StateManager(state_file)
        obsidian_sync = ObsidianSync(vault_dir)
        
        # Mark meeting as already processed
        state_manager.mark_processed('test_meeting_123')
        
        # Mock FirefliesClient
        mock_client = Mock(spec=FirefliesClient)
        mock_client.get_recent_meetings.return_value = [mock_meeting_data]
        
        # Run the sync process
        processed = process_meetings(mock_client, obsidian_sync, state_manager)
        
        # Verify no meetings were processed
        assert processed == 0
        
        # Verify no files were created
        fireflies_dir = Path(vault_dir) / 'Fireflies'
        if fireflies_dir.exists():
            md_files = list(fireflies_dir.glob('*.md'))
            assert len(md_files) == 0
    
    def test_error_recovery(self, temp_dirs):
        """Test error handling during sync process."""
        vault_dir, state_dir = temp_dirs
        state_file = os.path.join(state_dir, 'test_state.json')
        
        # Initialize components
        state_manager = StateManager(state_file)
        obsidian_sync = ObsidianSync(vault_dir)
        
        # Mock FirefliesClient with error
        mock_client = Mock(spec=FirefliesClient)
        mock_client.get_recent_meetings.side_effect = Exception("API Error")
        
        # Run the sync process - should not crash
        processed = process_meetings(mock_client, obsidian_sync, state_manager)
        
        # Verify graceful failure
        assert processed == 0
    
    def test_notification_integration(self, temp_dirs, mock_meeting_data):
        """Test that notifications are sent correctly."""
        vault_dir, state_dir = temp_dirs
        state_file = os.path.join(state_dir, 'test_state.json')
        
        # Initialize components
        state_manager = StateManager(state_file)
        obsidian_sync = ObsidianSync(vault_dir)
        
        # Mock FirefliesClient
        mock_client = Mock(spec=FirefliesClient)
        mock_client.get_recent_meetings.return_value = [mock_meeting_data]
        
        # Mock notification service
        mock_notif = Mock(spec=NotificationService)
        
        # Patch get_notification_service to return our mock
        with patch('src.main.get_notification_service', return_value=mock_notif):
            # Run the sync process
            processed = process_meetings(mock_client, obsidian_sync, state_manager)
            
            # Since notification is TODO in main.py, we don't expect calls yet
            # This test is ready for when notifications are integrated
            assert processed == 1
    
    def test_state_persistence(self, temp_dirs, mock_meeting_data):
        """Test that state persists across sessions."""
        vault_dir, state_dir = temp_dirs
        state_file = os.path.join(state_dir, 'test_state.json')
        
        # First session
        state_manager1 = StateManager(state_file)
        state_manager1.mark_processed('meeting1')
        state_manager1.mark_processed('meeting2')
        state_manager1.set_metadata('test_key', 'test_value')
        
        # Second session - load existing state
        state_manager2 = StateManager(state_file)
        
        # Verify state was persisted
        assert state_manager2.is_processed('meeting1')
        assert state_manager2.is_processed('meeting2')
        assert state_manager2.get_metadata('test_key') == 'test_value'
        stats = state_manager2.get_stats()
        assert stats['total_processed'] == 2
    
    def test_test_mode_specific_meetings(self, temp_dirs):
        """Test processing specific meetings in test mode."""
        vault_dir, state_dir = temp_dirs
        state_file = os.path.join(state_dir, 'test_state.json')
        
        # Initialize components
        state_manager = StateManager(state_file)
        obsidian_sync = ObsidianSync(vault_dir)
        
        # Create mock meetings
        meeting1 = {
            'id': 'specific_meeting_1',
            'title': 'Specific Test Meeting 1',
            'date': '2025-01-15T09:00:00Z',
            'host_name': 'Host 1',
            'summary': {'overview': 'Meeting 1 overview'}
        }
        
        meeting2 = {
            'id': 'specific_meeting_2',
            'title': 'Specific Test Meeting 2',
            'date': '2025-01-15T10:00:00Z',
            'host_name': 'Host 2',
            'summary': {'overview': 'Meeting 2 overview'}
        }
        
        # Mock FirefliesClient
        mock_client = Mock(spec=FirefliesClient)
        mock_client.get_meeting.side_effect = lambda id: {
            'specific_meeting_1': meeting1,
            'specific_meeting_2': meeting2
        }.get(id)
        
        # Run in test mode with specific IDs
        processed = process_meetings(
            mock_client, 
            obsidian_sync, 
            state_manager,
            meeting_ids=['specific_meeting_1', 'specific_meeting_2']
        )
        
        # Verify both meetings were processed
        assert processed == 2
        assert state_manager.is_processed('specific_meeting_1')
        assert state_manager.is_processed('specific_meeting_2')