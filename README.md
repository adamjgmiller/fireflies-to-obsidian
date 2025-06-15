# Fireflies to Obsidian Sync Tool

**One-line purpose**: Automatically sync Fireflies.ai meeting transcripts to your Obsidian vault every 15 seconds  
**Core value**: Eliminates manual copying of meeting notes, providing immediate access to transcripts in your knowledge management system  
**Status**: In development - PRD and task list complete, implementation pending

## Quick Start (< 5 minutes)

### Prerequisites
- Python 3.13.5 or higher
- Fireflies.ai account with API access
- Obsidian vault (local folder)
- macOS (for notifications)

### Installation
```bash
# Clone and setup
git clone <repository-url>
cd fireflies-to-obsidian

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your Fireflies API key
# Edit config.yaml with your Obsidian vault path
```

### First Run
```bash
# Test mode (processes specific meeting IDs)
python src/main.py --test

# Normal operation (continuous polling)
python src/main.py
```

**Expected output**: macOS notification showing "🎙️ New Fireflies meeting synced" and new .md files in your Obsidian Fireflies folder.

## Architecture Overview

### Tech Stack
- **Python 3.13.5**: Main language with async support
- **httpx**: Async HTTP client for GraphQL API calls
- **PyYAML**: Configuration file parsing
- **pytest**: Testing framework

### Key Dependencies
- `httpx`: Fireflies GraphQL API communication
- `pyyaml`: Config and YAML frontmatter handling
- `pytest`: Unit and integration testing

### Data Flow
```
Fireflies API → GraphQL Client → Meeting Processor → Markdown Formatter → Obsidian Vault
                      ↓
State Manager (tracks processed meetings) → JSON persistence
                      ↓
macOS Notifications (sync status updates)
```

### Integration Points
- **Fireflies GraphQL API**: Meeting data retrieval
- **Local file system**: Obsidian vault integration
- **macOS Notification Center**: Status updates

## Development Workflow

### Local Development
```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
pytest tests/

# Run with debug logging
python src/main.py --debug

# Test specific meeting
python src/main.py --test --meeting-id abc123
```

### Testing Strategy
- **Unit tests**: Individual component testing (API client, formatters, etc.)
- **Integration tests**: End-to-end sync workflow
- **Test command**: `pytest tests/` or `pytest tests/test_specific.py`

### Build Process
No build step required - Python application runs directly from source.

## AI Collaboration Guidelines

### Project Rules Files
- Follow ALL rules in `adams-rules/` directory
- Use AI development workflow: PRD → Task List → Implementation
- Reference `ai-dev-tasks/tasks/tasks-prd-fireflies-obsidian-sync.md` for implementation tasks

### Code Style Preferences
- Python 3.13+ features and type hints
- Async/await patterns for API calls
- Clear separation of concerns (API, formatting, file operations)
- Comprehensive error handling with logging

### AI Should Modify
- Core application logic and new features
- Test files and documentation
- Configuration templates

### AI Should NOT Modify
- User's actual `.env` and `config.yaml` files
- Existing Obsidian notes (read-only operation)
- State management files during runtime

## Critical Context

### Business Logic
- **Meeting Filtering**: Only sync meetings after June 13, 2024 (configurable)
- **Duplicate Prevention**: Track processed meetings in JSON state file
- **File Naming**: `YYYY-MM-DD-HH-MM-[Meeting Title].md` for chronological sorting
- **Speaker Grouping**: Consecutive statements by same speaker under single header

### Security Considerations
- API keys stored in local `.env` file (never committed)
- No network exposure - purely local polling service
- Read-only access to Fireflies, write-only to Obsidian

### Performance Requirements
- **Polling Interval**: 15 seconds (configurable)
- **Sync Speed**: New meetings in Obsidian within 30 seconds
- **Batch Processing**: 5 meetings per API call to respect rate limits
- **Memory Efficient**: Process meetings individually, don't hold large datasets

### Known Limitations
- macOS only (notifications)
- No real-time webhooks (polling-based)
- No two-way sync (Obsidian → Fireflies)
- Won't update existing notes if meeting changes

## Team Knowledge

### Component Ownership
- **API Client** (`src/fireflies_client.py`): GraphQL communication and rate limiting
- **Sync Engine** (`src/obsidian_sync.py`): File operations and vault management  
- **Formatter** (`src/markdown_formatter.py`): Template system and YAML frontmatter
- **State Manager** (`src/state_manager.py`): Duplicate prevention and persistence
- **Main Service** (`src/main.py`): Polling loop and orchestration

### Key Design Decisions
- **Virtual Environment**: Isolated dependencies for reliable deployment
- **JSON State**: Simple persistence, can migrate to SQLite later
- **GraphQL**: Fireflies API standard, more efficient than REST
- **Async HTTP**: Better performance for polling architecture

### Documentation Links
- **PRD**: `ai-dev-tasks/tasks/prd-fireflies-obsidian-sync.md`
- **Task List**: `ai-dev-tasks/tasks/tasks-prd-fireflies-obsidian-sync.md`
- **Project Rules**: `adams-rules/` directory

### Troubleshooting
- **API Rate Limits**: Check exponential backoff implementation
- **Missing Meetings**: Verify date filter (June 13, 2024+)
- **Notification Issues**: Ensure macOS permissions for notifications
- **File Conflicts**: Check duplicate detection in state manager