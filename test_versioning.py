#!/usr/bin/env python3
"""Test the file versioning functionality"""
import json
from pathlib import Path
from src.obsidian_sync import ObsidianSync
from src.state_manager import StateManager

# Remove a meeting from processed list
state_file = Path(".state/processed_meetings.json")
with open(state_file, 'r') as f:
    data = json.load(f)

# Remove the meeting ID
meeting_id = "01JXE1FQY9NMXVXH4TSVR785GK"
if meeting_id in data['processed_meetings']:
    data['processed_meetings'].remove(meeting_id)
    with open(state_file, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Removed {meeting_id} from processed list")

# Now test the sync with this meeting
import subprocess
result = subprocess.run(
    ["python", "-m", "src.main", "--test", meeting_id],
    capture_output=True,
    text=True
)

print("\n--- STDOUT ---")
print(result.stdout)
print("\n--- STDERR ---")
print(result.stderr)