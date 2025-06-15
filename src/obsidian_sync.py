import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from .utils.logger import get_logger

logger = get_logger(__name__)


class ObsidianSync:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.fireflies_folder = self.vault_path / "Fireflies"
        
    def initialize_vault_folder(self) -> None:
        """Create Fireflies folder in Obsidian vault if it doesn't exist."""
        try:
            self.fireflies_folder.mkdir(parents=True, exist_ok=True)
            logger.info(f"Fireflies folder initialized at: {self.fireflies_folder}")
        except Exception as e:
            logger.error(f"Failed to create Fireflies folder: {e}")
            raise
    
    def generate_filename(self, meeting_data: Dict[str, Any]) -> str:
        """Generate filename in format: YYYY-MM-DD-HH-MM-[Meeting Title].md"""
        # Placeholder: Extract date from meeting data
        # This will be implemented when we have the actual meeting data structure
        meeting_date = meeting_data.get('date', datetime.now())
        if isinstance(meeting_date, str):
            # Parse date string if needed
            meeting_date = datetime.fromisoformat(meeting_date.replace('Z', '+00:00'))
        
        # Clean meeting title for filename
        title = meeting_data.get('title', 'Untitled Meeting')
        # Remove special characters that might cause issues in filenames
        clean_title = re.sub(r'[<>:"/\\|?*]', '', title)
        clean_title = clean_title.strip()
        
        # Format: YYYY-MM-DD-HH-MM-[Meeting Title].md
        filename = f"{meeting_date.strftime('%Y-%m-%d-%H-%M')}-{clean_title}.md"
        
        return filename
    
    def check_duplicate(self, filename: str) -> bool:
        """Check if a file with the given name already exists."""
        file_path = self.fireflies_folder / filename
        return file_path.exists()
    
    def save_meeting(self, meeting_data: Dict[str, Any], content: str) -> Optional[Path]:
        """Save meeting content to Obsidian vault."""
        try:
            # Ensure folder exists
            self.initialize_vault_folder()
            
            # Generate filename
            filename = self.generate_filename(meeting_data)
            file_path = self.fireflies_folder / filename
            
            # Check for duplicates
            if self.check_duplicate(filename):
                logger.warning(f"Meeting file already exists: {filename}")
                return None
            
            # Write content to file
            file_path.write_text(content, encoding='utf-8')
            logger.info(f"Meeting saved successfully: {filename}")
            
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save meeting: {e}")
            raise
    
    def get_existing_meeting_ids(self) -> set:
        """Get set of meeting IDs that have already been processed."""
        meeting_ids = set()
        
        try:
            if not self.fireflies_folder.exists():
                return meeting_ids
            
            # Iterate through all markdown files in the folder
            for file_path in self.fireflies_folder.glob("*.md"):
                # Read the file to extract meeting ID from frontmatter
                try:
                    content = file_path.read_text(encoding='utf-8')
                    # Look for meeting_id in YAML frontmatter
                    if content.startswith('---'):
                        frontmatter_end = content.find('---', 3)
                        if frontmatter_end != -1:
                            frontmatter = content[3:frontmatter_end]
                            for line in frontmatter.split('\n'):
                                if line.strip().startswith('meeting_id:'):
                                    meeting_id = line.split(':', 1)[1].strip()
                                    meeting_ids.add(meeting_id)
                                    break
                except Exception as e:
                    logger.warning(f"Failed to read meeting ID from {file_path}: {e}")
                    
            logger.info(f"Found {len(meeting_ids)} existing meetings in vault")
            return meeting_ids
            
        except Exception as e:
            logger.error(f"Failed to get existing meeting IDs: {e}")
            return meeting_ids