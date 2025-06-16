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
        
        # Initialize with empty state if file doesn't exist
        if not self.state_file.exists():
            self._initialize_empty_state()
    
    def _initialize_empty_state(self) -> None:
        """Initialize an empty state file."""
        state_data = {
            'processed_meetings': [],
            'last_sync': None,
            'metadata': {}
        }
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
            logger.info("Initialized empty state file")
        except IOError as e:
            logger.error(f"Error creating state file: {e}")
    
    def _load_state(self) -> Dict:
        """Load state from file. Always reads from disk."""
        if not self.state_file.exists():
            self._initialize_empty_state()
            return {
                'processed_meetings': [],
                'last_sync': None,
                'metadata': {}
            }
        
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading state file: {e}")
            logger.info("Returning empty state")
            return {
                'processed_meetings': [],
                'last_sync': None,
                'metadata': {}
            }
    
    def _save_state(self, state_data: Dict) -> None:
        """Save state to file."""
        try:
            state_data['last_sync'] = datetime.now().isoformat()
            
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
            logger.debug(f"Saved state with {len(state_data.get('processed_meetings', []))} processed meetings")
        except IOError as e:
            logger.error(f"Error saving state file: {e}")
    
    def is_processed(self, meeting_id: str) -> bool:
        """Check if a meeting has already been processed."""
        state_data = self._load_state()
        return meeting_id in state_data.get('processed_meetings', [])
    
    def mark_processed(self, meeting_id: str) -> None:
        """Mark a meeting as processed."""
        state_data = self._load_state()
        processed_meetings = state_data.get('processed_meetings', [])
        
        if meeting_id not in processed_meetings:
            processed_meetings.append(meeting_id)
            state_data['processed_meetings'] = processed_meetings
            self._save_state(state_data)
            logger.info(f"Marked meeting {meeting_id} as processed")
    
    def mark_multiple_processed(self, meeting_ids: list[str]) -> None:
        """Mark multiple meetings as processed in a single operation."""
        state_data = self._load_state()
        processed_meetings = set(state_data.get('processed_meetings', []))
        new_meetings = set(meeting_ids) - processed_meetings
        
        if new_meetings:
            processed_meetings.update(new_meetings)
            state_data['processed_meetings'] = list(processed_meetings)
            self._save_state(state_data)
            logger.info(f"Marked {len(new_meetings)} new meetings as processed")
    
    def get_last_sync_time(self) -> Optional[datetime]:
        """Get the last sync timestamp."""
        state_data = self._load_state()
        if state_data.get('last_sync'):
            try:
                return datetime.fromisoformat(state_data['last_sync'])
            except ValueError:
                return None
        return None
    
    def set_metadata(self, key: str, value: any) -> None:
        """Set a metadata value."""
        state_data = self._load_state()
        
        # Convert datetime objects to ISO string format for JSON serialization
        if isinstance(value, datetime):
            value = value.isoformat()
        
        if 'metadata' not in state_data:
            state_data['metadata'] = {}
        
        state_data['metadata'][key] = value
        self._save_state(state_data)
    
    def get_metadata(self, key: str, default=None) -> any:
        """Get a metadata value."""
        state_data = self._load_state()
        return state_data.get('metadata', {}).get(key, default)
    
    def clear_state(self) -> None:
        """Clear all processed meetings (useful for testing)."""
        state_data = {
            'processed_meetings': [],
            'last_sync': None,
            'metadata': {}
        }
        self._save_state(state_data)
        logger.info("Cleared all state data")
    
    def get_stats(self) -> Dict:
        """Get statistics about the current state."""
        state_data = self._load_state()
        return {
            'total_processed': len(state_data.get('processed_meetings', [])),
            'last_sync': self.get_last_sync_time(),
            'state_file': str(self.state_file)
        }