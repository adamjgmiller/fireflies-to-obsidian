"""Unit tests for StateManager."""
import os
import json
import tempfile
import shutil
from datetime import datetime
import pytest

from src.state_manager import StateManager


class TestStateManager:
    """Test cases for StateManager functionality."""
    
    @pytest.fixture
    def temp_state_file(self):
        """Create a temporary state file for testing."""
        temp_dir = tempfile.mkdtemp()
        state_file = os.path.join(temp_dir, 'test_state.json')
        yield state_file
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_init_creates_state_file(self, temp_state_file):
        """Test that StateManager creates state file on init."""
        manager = StateManager(temp_state_file)
        assert os.path.exists(temp_state_file)
        assert manager.state_file.exists()
    
    def test_init_loads_existing_state(self, temp_state_file):
        """Test loading existing state from file."""
        # Create initial state
        initial_data = {
            'processed_meetings': ['meeting1', 'meeting2'],
            'last_sync': '2025-01-15T10:00:00',
            'metadata': {'key': 'value'}
        }
        with open(temp_state_file, 'w') as f:
            json.dump(initial_data, f)
        
        # Load state
        manager = StateManager(temp_state_file)
        
        # Verify loaded data
        assert manager.is_processed('meeting1')
        assert manager.is_processed('meeting2')
        # Check through stats instead of direct attribute
        stats = manager.get_stats()
        assert stats['total_processed'] == 2
        assert manager.get_metadata('key') == 'value'
    
    def test_mark_processed(self, temp_state_file):
        """Test marking meetings as processed."""
        manager = StateManager(temp_state_file)
        
        # Mark single meeting
        manager.mark_processed('meeting1')
        assert manager.is_processed('meeting1')
        assert not manager.is_processed('meeting2')
        
        # Verify persistence
        with open(temp_state_file, 'r') as f:
            data = json.load(f)
            assert 'meeting1' in data['processed_meetings']
    
    def test_mark_multiple_processed(self, temp_state_file):
        """Test marking multiple meetings as processed."""
        manager = StateManager(temp_state_file)
        
        # Mark multiple meetings
        manager.mark_multiple_processed(['meeting1', 'meeting2', 'meeting3'])
        
        # Verify all marked
        assert manager.is_processed('meeting1')
        assert manager.is_processed('meeting2')
        assert manager.is_processed('meeting3')
        # Check through stats
        stats = manager.get_stats()
        assert stats['total_processed'] == 3
    
    def test_duplicate_marking(self, temp_state_file):
        """Test that marking same meeting twice doesn't duplicate."""
        manager = StateManager(temp_state_file)
        
        # Mark same meeting multiple times
        manager.mark_processed('meeting1')
        manager.mark_processed('meeting1')
        manager.mark_multiple_processed(['meeting1', 'meeting2'])
        
        # Verify no duplicates through stats
        stats = manager.get_stats()
        assert stats['total_processed'] == 2
        
        # Check file
        with open(temp_state_file, 'r') as f:
            data = json.load(f)
            assert len(data['processed_meetings']) == 2
    
    def test_last_sync_time(self, temp_state_file):
        """Test last sync time tracking."""
        manager = StateManager(temp_state_file)
        
        # Initially no sync time
        assert manager.get_last_sync_time() is None
        
        # Mark a meeting (triggers save with sync time)
        manager.mark_processed('meeting1')
        
        # Get sync time
        sync_time = manager.get_last_sync_time()
        assert sync_time is not None
        assert isinstance(sync_time, datetime)
        
        # Verify it's recent
        time_diff = datetime.now() - sync_time
        assert time_diff.total_seconds() < 5  # Within 5 seconds
    
    def test_metadata_operations(self, temp_state_file):
        """Test metadata get/set operations."""
        manager = StateManager(temp_state_file)
        
        # Set metadata
        manager.set_metadata('key1', 'value1')
        manager.set_metadata('key2', {'nested': 'value'})
        manager.set_metadata('key3', [1, 2, 3])
        
        # Get metadata
        assert manager.get_metadata('key1') == 'value1'
        assert manager.get_metadata('key2') == {'nested': 'value'}
        assert manager.get_metadata('key3') == [1, 2, 3]
        
        # Get with default
        assert manager.get_metadata('nonexistent', 'default') == 'default'
    
    def test_clear_state(self, temp_state_file):
        """Test clearing all state data."""
        manager = StateManager(temp_state_file)
        
        # Add some data
        manager.mark_multiple_processed(['meeting1', 'meeting2'])
        manager.set_metadata('key', 'value')
        
        # Clear state
        manager.clear_state()
        
        # Verify cleared
        stats = manager.get_stats()
        assert stats['total_processed'] == 0
        assert not manager.is_processed('meeting1')
        assert manager.get_metadata('key') is None
        
        # Verify file updated
        with open(temp_state_file, 'r') as f:
            data = json.load(f)
            assert len(data['processed_meetings']) == 0
            assert len(data['metadata']) == 0
    
    def test_get_stats(self, temp_state_file):
        """Test statistics retrieval."""
        manager = StateManager(temp_state_file)
        
        # Add test data
        manager.mark_multiple_processed(['m1', 'm2', 'm3'])
        
        # Get stats
        stats = manager.get_stats()
        
        assert stats['total_processed'] == 3
        assert stats['state_file'] == temp_state_file
        assert 'last_sync' in stats
    
    def test_corrupted_state_file(self, temp_state_file):
        """Test handling of corrupted state file."""
        # Write invalid JSON
        with open(temp_state_file, 'w') as f:
            f.write('{"invalid": json content')
        
        # Should handle corrupted file gracefully
        manager = StateManager(temp_state_file)
        # The corrupted file still exists, so it won't create a new one
        # But _load_state should return empty state on error
        stats = manager.get_stats()
        assert stats['total_processed'] == 0
    
    def test_default_state_directory(self):
        """Test default state directory creation."""
        # Don't provide state file path
        manager = StateManager()
        
        # Should create .state directory in project root
        assert manager.state_file.parent.name == '.state'
        assert manager.state_file.name == 'processed_meetings.json'
        
        # Cleanup
        if manager.state_file.exists():
            os.remove(manager.state_file)
        if manager.state_file.parent.exists():
            os.rmdir(manager.state_file.parent)