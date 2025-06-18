# PRD: File Versioning for Duplicate Meeting Files

## Overview

Currently, when the fireflies-to-obsidian sync tool encounters an existing file, it overwrites it. This PRD outlines the implementation of a file versioning system that appends version numbers (1), (2), etc. to filenames when duplicates are detected.

## Problem Statement

- When a meeting is removed from `.state/processed_meetings.json` and the sync runs again, the meeting file should be re-created without overwriting the existing file
- Currently, the `save_meeting` method overwrites existing files without warning
- The `check_duplicate` method exists but is not used in production code
- Users may lose data if files are overwritten

## Functional Requirements

### FR1: Unique Filename Generation
- When saving a meeting file, check if a file with the same name already exists
- If it exists, append a version number in parentheses: `(1)`, `(2)`, `(3)`, etc.
- The version number should be placed before the file extension
- Example: `2024-01-15-10-30-Team Meeting.md` → `2024-01-15-10-30-Team Meeting (1).md`

### FR2: Version Number Increment
- Start with `(1)` for the first duplicate
- Increment sequentially: `(1)`, `(2)`, `(3)`, etc.
- Find the next available version number (skip existing ones)

### FR3: Preserve Original Behavior
- First instance of a file should not have a version number
- State management (processed_meetings.json) remains unchanged
- Meeting processing flow remains the same

## Technical Requirements

### TR1: Implementation Location
- Modify `src/obsidian_sync.py` to implement versioning logic
- Remove unused `check_duplicate` method

### TR2: Method Structure
- Create a new `get_unique_filename` method
- Update `save_meeting` method to use the new logic
- Ensure atomic file operations

### TR3: Testing
- Update existing tests that expect duplicate handling
- Add comprehensive tests for version numbering scenarios

## User Stories

### US1: Re-processing Removed Meetings
As a user, when I remove a meeting from processed_meetings.json and run the sync again, I want the meeting to be re-downloaded and saved with a version number so that I don't lose the original file.

### US2: Multiple Versions
As a user, I want to be able to have multiple versions of the same meeting file so that I can track changes or recover from accidental modifications.

## Success Criteria

1. No existing files are overwritten
2. Version numbers increment correctly
3. Re-processed meetings create versioned files
4. All existing tests pass with updated expectations
5. New tests cover all versioning scenarios

## Out of Scope

- Automatic cleanup of old versions
- Version comparison or diff functionality
- UI for managing versions
- Modification of state tracking logic