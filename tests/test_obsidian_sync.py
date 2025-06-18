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
        
        assert filename == "2024-01-15-10-30-Team-Standup-Meeting.md"
        assert filename.endswith(".md")
    
    def test_generate_filename_special_characters(self, obsidian_sync):
        """Test filename generation with special characters."""
        meeting_data = {
            'title': 'Meeting: <Project>\\Review/Update | Q&A?',
            'date': '2024-01-15T10:30:00Z'
        }
        
        filename = obsidian_sync.generate_filename(meeting_data)
        
        # Special characters should be removed
        assert filename == "2024-01-15-10-30-Meeting-ProjectReviewUpdate-QA.md"
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
        
        assert filename == "2024-01-15-10-30-Untitled-Meeting.md"
    
    def test_generate_filename_datetime_object(self, obsidian_sync):
        """Test filename generation with datetime object (falls back to current time)."""
        meeting_data = {
            'title': 'Test Meeting',
            'date': datetime(2024, 1, 15, 10, 30, 0)
        }
        
        filename = obsidian_sync.generate_filename(meeting_data)
        
        # Since datetime objects fall back to current time, just verify format
        assert filename.endswith("-Test-Meeting.md")
        assert len(filename) == len("2024-01-15-10-30-Test-Meeting.md")
    
    def test_save_meeting_success(self, obsidian_sync, sample_meeting_data):
        """Test successful meeting save."""
        content = "# Test Meeting\n\nThis is test content."
        
        file_path = obsidian_sync.save_meeting(sample_meeting_data, content)
        
        assert file_path is not None
        assert file_path.exists()
        assert file_path.read_text() == content
        assert file_path.name == "2024-01-15-10-30-Team-Standup-Meeting.md"
    
    def test_save_meeting_duplicate(self, obsidian_sync, sample_meeting_data):
        """Test saving duplicate meeting creates versioned file."""
        content = "# Test Meeting\n\nThis is test content."
        
        # Save first time
        file_path1 = obsidian_sync.save_meeting(sample_meeting_data, content)
        assert file_path1 is not None
        assert file_path1.name == "2024-01-15-10-30-Team-Standup-Meeting.md"
        
        # Try to save again - should create versioned file
        file_path2 = obsidian_sync.save_meeting(sample_meeting_data, content)
        assert file_path2 is not None
        assert file_path2.name == "2024-01-15-10-30-Team-Standup-Meeting (1).md"
        assert file_path2.exists()
        
        # Save a third time - should create version (2)
        file_path3 = obsidian_sync.save_meeting(sample_meeting_data, content)
        assert file_path3 is not None
        assert file_path3.name == "2024-01-15-10-30-Team-Standup-Meeting (2).md"
        assert file_path3.exists()
    
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
    
    def test_get_unique_filename_no_conflict(self, obsidian_sync):
        """Test get_unique_filename when no file exists."""
        obsidian_sync.initialize_vault_folder()
        
        base_path = obsidian_sync.fireflies_folder / "test-file.md"
        unique_path = obsidian_sync.get_unique_filename(base_path)
        
        assert unique_path == base_path
        assert unique_path.name == "test-file.md"
    
    def test_get_unique_filename_single_conflict(self, obsidian_sync):
        """Test get_unique_filename with one existing file."""
        obsidian_sync.initialize_vault_folder()
        
        # Create existing file
        base_path = obsidian_sync.fireflies_folder / "test-file.md"
        base_path.write_text("Original content")
        
        # Get unique filename
        unique_path = obsidian_sync.get_unique_filename(base_path)
        
        assert unique_path != base_path
        assert unique_path.name == "test-file (1).md"
    
    def test_get_unique_filename_multiple_conflicts(self, obsidian_sync):
        """Test get_unique_filename with multiple existing files."""
        obsidian_sync.initialize_vault_folder()
        
        # Create existing files
        base_path = obsidian_sync.fireflies_folder / "test-file.md"
        base_path.write_text("Original content")
        
        versioned_path1 = obsidian_sync.fireflies_folder / "test-file (1).md"
        versioned_path1.write_text("Version 1 content")
        
        versioned_path2 = obsidian_sync.fireflies_folder / "test-file (2).md"
        versioned_path2.write_text("Version 2 content")
        
        # Get unique filename
        unique_path = obsidian_sync.get_unique_filename(base_path)
        
        assert unique_path.name == "test-file (3).md"
    
    def test_save_meeting_creates_versioned_files(self, obsidian_sync, sample_meeting_data):
        """Test full flow of creating versioned files through save_meeting."""
        content1 = "# Meeting Version 1"
        content2 = "# Meeting Version 2"
        content3 = "# Meeting Version 3"
        
        # Save multiple versions
        file_path1 = obsidian_sync.save_meeting(sample_meeting_data, content1)
        file_path2 = obsidian_sync.save_meeting(sample_meeting_data, content2)
        file_path3 = obsidian_sync.save_meeting(sample_meeting_data, content3)
        
        # Verify all files exist with correct names
        assert file_path1.name == "2024-01-15-10-30-Team-Standup-Meeting.md"
        assert file_path2.name == "2024-01-15-10-30-Team-Standup-Meeting (1).md"
        assert file_path3.name == "2024-01-15-10-30-Team-Standup-Meeting (2).md"
        
        # Verify content is preserved
        assert file_path1.read_text() == content1
        assert file_path2.read_text() == content2
        assert file_path3.read_text() == content3
    
    def test_get_unique_filename_out_of_sequence(self, obsidian_sync):
        """Test get_unique_filename when version numbers exist out of sequence."""
        obsidian_sync.initialize_vault_folder()
        
        # Create files with gaps in version numbers
        base_path = obsidian_sync.fireflies_folder / "test-file.md"
        base_path.write_text("Original")
        
        # Skip (1) and create (2)
        versioned_path2 = obsidian_sync.fireflies_folder / "test-file (2).md"
        versioned_path2.write_text("Version 2")
        
        # Skip (3) and create (4)
        versioned_path4 = obsidian_sync.fireflies_folder / "test-file (4).md"
        versioned_path4.write_text("Version 4")
        
        # Should find (1) as the first available
        unique_path = obsidian_sync.get_unique_filename(base_path)
        assert unique_path.name == "test-file (1).md"