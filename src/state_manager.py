"""State management for tracking processed meetings."""
import json
import os
from datetime import datetime
from typing import Dict, Set, Optional
from pathlib import Path
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class StateManager:
    """Manages state of processed meetings to avoid duplicates."""
    
    def __init__(self, state_file_path: str = None):
        """Initialize state manager with optional custom state file path."""
        if state_file_path is None:
            # Default to .state directory in project root
            project_root = Path(__file__).parent.parent
            state_dir = project_root / '.state'
            state_dir.mkdir(exist_ok=True)
            self.state_file = state_dir / 'processed_meetings.json'
        else:
            self.state_file = Path(state_file_path)
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.processed_meetings: Set[str] = set()
        self.state_data: Dict = {
            'processed_meetings': [],
            'last_sync': None,
            'metadata': {}
        }
        self._load_state()
    
    def _load_state(self) -> None:
        """Load state from file if it exists."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    self.state_data = json.load(f)
                    self.processed_meetings = set(self.state_data.get('processed_meetings', []))
                    logger.info(f"Loaded state with {len(self.processed_meetings)} processed meetings")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading state file: {e}")
                logger.info("Starting with empty state")
    
    def _save_state(self) -> None:
        """Save current state to file."""
        try:
            self.state_data['processed_meetings'] = list(self.processed_meetings)
            self.state_data['last_sync'] = datetime.now().isoformat()
            
            with open(self.state_file, 'w') as f:
                json.dump(self.state_data, f, indent=2)
            logger.debug(f"Saved state with {len(self.processed_meetings)} processed meetings")
        except IOError as e:
            logger.error(f"Error saving state file: {e}")
    
    def is_processed(self, meeting_id: str) -> bool:
        """Check if a meeting has already been processed."""
        return meeting_id in self.processed_meetings
    
    def mark_processed(self, meeting_id: str) -> None:
        """Mark a meeting as processed."""
        if meeting_id not in self.processed_meetings:
            self.processed_meetings.add(meeting_id)
            self._save_state()
            logger.info(f"Marked meeting {meeting_id} as processed")
    
    def mark_multiple_processed(self, meeting_ids: list[str]) -> None:
        """Mark multiple meetings as processed in a single operation."""
        new_meetings = set(meeting_ids) - self.processed_meetings
        if new_meetings:
            self.processed_meetings.update(new_meetings)
            self._save_state()
            logger.info(f"Marked {len(new_meetings)} new meetings as processed")
    
    def get_last_sync_time(self) -> Optional[datetime]:
        """Get the last sync timestamp."""
        if self.state_data.get('last_sync'):
            try:
                return datetime.fromisoformat(self.state_data['last_sync'])
            except ValueError:
                return None
        return None
    
    def set_metadata(self, key: str, value: any) -> None:
        """Set a metadata value."""
        self.state_data['metadata'][key] = value
        self._save_state()
    
    def get_metadata(self, key: str, default=None) -> any:
        """Get a metadata value."""
        return self.state_data['metadata'].get(key, default)
    
    def clear_state(self) -> None:
        """Clear all processed meetings (useful for testing)."""
        self.processed_meetings.clear()
        self.state_data['processed_meetings'] = []
        self.state_data['metadata'] = {}
        self._save_state()
        logger.info("Cleared all state data")
    
    def get_stats(self) -> Dict:
        """Get statistics about the current state."""
        return {
            'total_processed': len(self.processed_meetings),
            'last_sync': self.get_last_sync_time(),
            'state_file': str(self.state_file)
        }