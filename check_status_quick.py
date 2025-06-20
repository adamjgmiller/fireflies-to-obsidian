#!/usr/bin/env python3
"""Quick status check for processed meetings."""

import json
from pathlib import Path
from datetime import datetime

# Load state file
state_file = Path(".state/processed_meetings.json")
if state_file.exists():
    with open(state_file) as f:
        state_data = json.load(f)
    
    processed_meetings = state_data.get('processed_meetings', [])
    last_sync = state_data.get('last_sync', 'Never')
    
    print(f"=== Fireflies to Obsidian Sync Status ===")
    print(f"Total processed meetings: {len(processed_meetings)}")
    print(f"Last sync: {last_sync}")
    
    # Check latest log entries
    log_file = Path("logs/fireflies_sync.log")
    if log_file.exists():
        print(f"\nRecent activity from log:")
        with open(log_file) as f:
            lines = f.readlines()
            
        # Find recent "Retrieved X total transcripts" entries
        recent_totals = []
        for line in reversed(lines[-1000:]):  # Check last 1000 lines
            if "Retrieved" in line and "total transcripts" in line:
                recent_totals.append(line.strip())
                if len(recent_totals) >= 5:
                    break
        
        for entry in reversed(recent_totals):
            print(f"  {entry}")
    
    print(f"\nBased on logs showing ~1487 total meetings available:")
    print(f"  - Processed: {len(processed_meetings)}")
    print(f"  - Unprocessed: ~{1487 - len(processed_meetings)}")
    print(f"  - Progress: {len(processed_meetings)/1487*100:.1f}%")
    
else:
    print("No state file found!")