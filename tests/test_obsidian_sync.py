import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import shutil
from src.obsidian_sync import ObsidianSync


@pytest.fixture
def temp_vault():
    """Create a temporary directory to act as Obsidian vault."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir)


@pytest.fixture
def obsidian_sync(temp_vault):
    """Create ObsidianSync instance with temporary vault."""
    return ObsidianSync(vault_path=temp_vault)


@pytest.fixture
def sample_meeting_data():
    """Sample meeting data for testing."""
    return {
        'id': 'meeting123',
        'title': 'Team Standup Meeting',
        'date': '2024-01-15T10:30:00Z',
        'duration': 1800,
        'attendees': ['John Doe', 'Jane Smith'],
        'summary': 'Weekly team sync'
    }


class TestObsidianSync:
    
    def test_initialize_vault_folder(self, obsidian_sync):
        """Test Fireflies folder creation."""
        obsidian_sync.initialize_vault_folder()
        
        assert obsidian_sync.fireflies_folder.exists()
        assert obsidian_sync.fireflies_folder.is_dir()
    
    def test_initialize_vault_folder_idempotent(self, obsidian_sync):
        """Test that folder creation is idempotent."""
        # Create folder first time
        obsidian_sync.initialize_vault_folder()
        
        # Create folder second time should not raise error
        obsidian_sync.initialize_vault_folder()
        
        assert obsidian_sync.fireflies_folder.exists()
    
    def test_generate_filename_basic(self, obsidian_sync, sample_meeting_data):
        """Test basic filename generation."""
        filename = obsidian_sync.generate_filename(sample_meeting_data)
        
        assert filename == "2024-01-15-10-30-Team Standup Meeting.md"
        assert filename.endswith(".md")
    
    def test_generate_filename_special_characters(self, obsidian_sync):
        """Test filename generation with special characters."""
        meeting_data = {
            'title': 'Meeting: <Project>\\Review/Update | Q&A?',
            'date': '2024-01-15T10:30:00Z'
        }
        
        filename = obsidian_sync.generate_filename(meeting_data)
        
        # Special characters should be removed
        assert filename == "2024-01-15-10-30-Meeting ProjectReviewUpdate  Q&A.md"
        assert '<' not in filename
        assert '>' not in filename
        assert ':' not in filename[10:]  # Colon allowed in time part
        assert '/' not in filename
        assert '\\' not in filename
        assert '|' not in filename
        assert '?' not in filename
        assert '*' not in filename
    
    def test_generate_filename_no_title(self, obsidian_sync):
        """Test filename generation without title."""
        meeting_data = {
            'date': '2024-01-15T10:30:00Z'
        }
        
        filename = obsidian_sync.generate_filename(meeting_data)
        
        assert filename == "2024-01-15-10-30-Untitled Meeting.md"
    
    def test_generate_filename_datetime_object(self, obsidian_sync):
        """Test filename generation with datetime object."""
        meeting_data = {
            'title': 'Test Meeting',
            'date': datetime(2024, 1, 15, 10, 30, 0)
        }
        
        filename = obsidian_sync.generate_filename(meeting_data)
        
        assert filename == "2024-01-15-10-30-Test Meeting.md"
    
    def test_check_duplicate_not_exists(self, obsidian_sync):
        """Test duplicate check when file doesn't exist."""
        obsidian_sync.initialize_vault_folder()
        
        assert not obsidian_sync.check_duplicate("non-existent-file.md")
    
    def test_check_duplicate_exists(self, obsidian_sync):
        """Test duplicate check when file exists."""
        obsidian_sync.initialize_vault_folder()
        
        # Create a test file
        test_file = obsidian_sync.fireflies_folder / "test-meeting.md"
        test_file.write_text("Test content")
        
        assert obsidian_sync.check_duplicate("test-meeting.md")
    
    def test_save_meeting_success(self, obsidian_sync, sample_meeting_data):
        """Test successful meeting save."""
        content = "# Test Meeting\n\nThis is test content."
        
        file_path = obsidian_sync.save_meeting(sample_meeting_data, content)
        
        assert file_path is not None
        assert file_path.exists()
        assert file_path.read_text() == content
        assert file_path.name == "2024-01-15-10-30-Team Standup Meeting.md"
    
    def test_save_meeting_duplicate(self, obsidian_sync, sample_meeting_data):
        """Test saving duplicate meeting."""
        content = "# Test Meeting\n\nThis is test content."
        
        # Save first time
        file_path1 = obsidian_sync.save_meeting(sample_meeting_data, content)
        assert file_path1 is not None
        
        # Try to save again
        file_path2 = obsidian_sync.save_meeting(sample_meeting_data, content)
        assert file_path2 is None  # Should return None for duplicate
    
    def test_get_existing_meeting_ids_empty(self, obsidian_sync):
        """Test getting meeting IDs from empty folder."""
        meeting_ids = obsidian_sync.get_existing_meeting_ids()
        
        assert isinstance(meeting_ids, set)
        assert len(meeting_ids) == 0
    
    def test_get_existing_meeting_ids_with_meetings(self, obsidian_sync):
        """Test getting meeting IDs from folder with meetings."""
        obsidian_sync.initialize_vault_folder()
        
        # Create test meeting files with frontmatter
        meeting1_content = """---
meeting_id: meeting123
title: Test Meeting 1
date: 2024-01-15
---

# Test Meeting 1
Content here."""
        
        meeting2_content = """---
meeting_id: meeting456
title: Test Meeting 2
date: 2024-01-16
---

# Test Meeting 2
Content here."""
        
        # Write test files
        (obsidian_sync.fireflies_folder / "meeting1.md").write_text(meeting1_content)
        (obsidian_sync.fireflies_folder / "meeting2.md").write_text(meeting2_content)
        
        # Get existing IDs
        meeting_ids = obsidian_sync.get_existing_meeting_ids()
        
        assert len(meeting_ids) == 2
        assert "meeting123" in meeting_ids
        assert "meeting456" in meeting_ids
    
    def test_get_existing_meeting_ids_invalid_frontmatter(self, obsidian_sync):
        """Test getting meeting IDs with invalid frontmatter."""
        obsidian_sync.initialize_vault_folder()
        
        # Create test file with no frontmatter
        no_frontmatter = "# Meeting without frontmatter\nContent here."
        
        # Create test file with malformed frontmatter
        bad_frontmatter = """---
title: Test Meeting
---

# Test Meeting
No meeting_id field."""
        
        # Write test files
        (obsidian_sync.fireflies_folder / "no_frontmatter.md").write_text(no_frontmatter)
        (obsidian_sync.fireflies_folder / "bad_frontmatter.md").write_text(bad_frontmatter)
        
        # Should not raise error, just skip files without meeting_id
        meeting_ids = obsidian_sync.get_existing_meeting_ids()
        
        assert len(meeting_ids) == 0
    
    def test_save_meeting_creates_folder(self, obsidian_sync, sample_meeting_data):
        """Test that save_meeting creates folder if it doesn't exist."""
        # Ensure folder doesn't exist
        assert not obsidian_sync.fireflies_folder.exists()
        
        content = "# Test Meeting"
        file_path = obsidian_sync.save_meeting(sample_meeting_data, content)
        
        assert file_path is not None
        assert obsidian_sync.fireflies_folder.exists()
        assert file_path.exists()