import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from .utils.logger import get_logger
from .markdown_formatter import MarkdownFormatter

logger = get_logger(__name__)


class ObsidianSync:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.fireflies_folder = self.vault_path / "Fireflies"
        self.formatter = MarkdownFormatter()
        
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
        # Use the formatter's filename generation method
        return self.formatter.format_filename(meeting_data)
    
    def get_unique_filename(self, base_path: Path) -> Path:
        """Generate a unique filename by appending version numbers if needed.
        
        Args:
            base_path: The desired file path
            
        Returns:
            A unique file path that doesn't conflict with existing files
        """
        # Task 1.2: Check if base_path exists
        if not base_path.exists():
            logger.debug(f"Base path does not exist, using: {base_path}")
            return base_path
        
        logger.warning(f"File already exists: {base_path}, generating unique filename")
        
        # Task 1.3: Extract base name and extension
        stem = base_path.stem
        suffix = base_path.suffix
        parent = base_path.parent
        
        # Task 1.4: Loop to find next available version number
        version = 1
        while True:
            versioned_filename = f"{stem} ({version}){suffix}"
            versioned_path = parent / versioned_filename
            
            if not versioned_path.exists():
                # Task 1.5: Return the unique path
                logger.info(f"Using versioned filename: {versioned_filename}")
                return versioned_path
            
            version += 1
    
    def save_meeting(self, meeting_data: Dict[str, Any], content: str) -> Optional[Path]:
        """Save meeting content to Obsidian vault."""
        try:
            # Ensure folder exists
            self.initialize_vault_folder()
            
            # Generate filename
            filename = self.generate_filename(meeting_data)
            file_path = self.fireflies_folder / filename
            
            # Task 2.1: Call get_unique_filename before writing
            unique_file_path = self.get_unique_filename(file_path)
            
            # Task 2.2: Write content to the unique file path
            unique_file_path.write_text(content, encoding='utf-8')
            
            # Task 2.3: Update logging to show actual filename used
            actual_filename = unique_file_path.name
            if actual_filename != filename:
                logger.info(f"Meeting saved successfully: {actual_filename} (original: {filename})")
            else:
                logger.info(f"Meeting saved successfully: {actual_filename}")
            
            # Task 2.4: Return the actual path where file was saved
            return unique_file_path
            
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
    
    def create_meeting_note(self, meeting_data: Dict[str, Any]) -> Optional[Path]:
        """Create a formatted meeting note and save it to the vault.
        
        Args:
            meeting_data: Meeting data from Fireflies API
            
        Returns:
            Path to the created file, or None if creation failed
        """
        try:
            # Format the meeting content using MarkdownFormatter
            content = self.formatter.format_meeting(meeting_data)
            
            # Save the formatted content
            return self.save_meeting(meeting_data, content)
            
        except Exception as e:
            logger.error(f"Failed to create meeting note: {e}")
            return None