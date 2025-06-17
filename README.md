# Fireflies to Obsidian Sync Tool

**One-line purpose**: Automatically sync Fireflies.ai meeting transcripts to your Obsidian vault every 15 seconds  
**Core value**: Eliminates manual copying of meeting notes, providing immediate access to transcripts in your knowledge management system  
**Status**: ✅ Production Ready (v0.1) - All features implemented and tested

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
cp config.yaml.example config.yaml
# Edit config.yaml with your Fireflies API key and Obsidian vault path
```

### Configuration
The app uses `config.yaml` as the primary configuration file. You can also use environment variables to override any setting:

**Required settings** (set in `config.yaml` or as environment variables):
```yaml
# In config.yaml
fireflies:
  api_key: "your_fireflies_api_key_here"  # Or set FIREFLIES_API_KEY env var

obsidian:
  vault_path: "/path/to/your/obsidian/vault"  # Or set OBSIDIAN_VAULT_PATH env var
```

**Optional: Create `.env` file** for environment variables:
```bash
# Create .env file (optional - you can set these in config.yaml instead)
FIREFLIES_API_KEY=your_api_key_here
OBSIDIAN_VAULT_PATH=/path/to/your/vault
```

### First Run
```bash
# Test mode (processes specific meeting IDs)
./start_sync.sh --test MEETING_ID_1 MEETING_ID_2

# Normal operation (continuous polling)
./start_sync.sh

# Check service status
./manage_service.sh status

# View logs
tail -f logs/service.log
```

## Background Service Management

The app runs as a macOS LaunchAgent background service that starts automatically on login. Use these commands to manage the service:

```bash
# Restart the background service (recommended method)
./restart_service.sh

# Check if background service is running
launchctl list | grep fireflies

# View background service logs
tail -f logs/launch_agent.out.log  # Service startup/status logs
tail -f logs/launch_agent.err.log  # Application errors/API rate limits
```

**Important**: The LaunchAgent service runs independently of terminal sessions. Running `./start_sync.sh` directly will create a separate process that may conflict with the background service.

**Expected output**: macOS notification showing "🎙️ New Fireflies meeting synced" and new .md files in your Obsidian Fireflies folder.

## Architecture Overview

### Tech Stack
- **Python 3.13.5**: Main language with async support
- **httpx**: Async HTTP client for GraphQL API calls
- **PyYAML**: Configuration file parsing
- **pydantic**: Data validation and settings management
- **python-dotenv**: Environment variable management
- **pytest**: Testing framework

### Key Dependencies
- `httpx==0.27.0`: Fireflies GraphQL API communication
- `pyyaml==6.0.1`: Config and YAML frontmatter handling
- `pytest==7.4.4`: Unit and integration testing
- `python-dotenv==1.0.0`: Environment variable loading
- `aiofiles==23.2.1`: Async file operations
- `schedule==1.2.0`: Job scheduling for polling
- `pydantic==2.10.4`: Configuration validation
- `pytest-asyncio==0.23.2`: Async testing support

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
python -m src.main --config config.yaml

# Test specific meeting
python -m src.main --test MEETING_ID_123
```

### Testing Strategy
- **Unit tests**: Individual component testing (API client, formatters, etc.)
- **Integration tests**: End-to-end sync workflow
- **Test coverage**: All 8 core modules have corresponding test files
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
- User's actual `config.yaml` files
- Existing Obsidian notes (read-only operation)
- State management files during runtime

## Critical Context

### Business Logic
- **Meeting Filtering**: Only sync meetings after June 13, 2024 (configurable)
- **Duplicate Prevention**: Track processed meetings in JSON state file
- **Summary Readiness Checking**: Automatically wait for meeting summaries to be fully processed before syncing to Obsidian
- **File Naming**: `YYYY-MM-DD-HH-MM-[Meeting Title].md` for chronological sorting
- **Speaker Grouping**: Consecutive statements by same speaker under single header

### Security Considerations
- API keys stored in local `config.yaml` or environment variables (never committed)
- No network exposure - purely local polling service
- Read-only access to Fireflies, write-only to Obsidian

### Performance Requirements
- **Polling Interval**: 15 seconds (configurable)
- **Sync Speed**: New meetings in Obsidian within 30 seconds
- **Batch Processing**: 10 meetings per API call to respect rate limits
- **Memory Efficient**: Process meetings individually, don't hold large datasets

### Known Limitations
- macOS only (notifications) - core sync works on other platforms
- No real-time webhooks (polling-based) - 15-second interval
- No two-way sync (Obsidian → Fireflies) - read-only from Fireflies
- Won't update existing notes if meeting changes - prevents accidental overwrites

### Summary Readiness Feature

The sync tool automatically checks if Fireflies has finished processing meeting summaries before syncing to Obsidian. This ensures you always get complete meeting notes with full AI-generated summaries.

**How it works:**
- Before syncing each meeting, the tool checks the `summary_status` field from the Fireflies API
- Only meetings with `summary_status: 'processed'` are synced to Obsidian
- Meetings with incomplete summaries (`'processing'`, `'failed'`, or `'skipped'`) are temporarily skipped
- Skipped meetings are automatically retried in the next polling cycle (15 seconds later)
- No meetings are permanently lost - they remain in the queue until summaries are ready

**Benefits:**
- **Complete Data**: Always get fully processed transcripts with AI summaries, action items, and keywords
- **No Partial Syncs**: Eliminates incomplete notes that would need manual updates later
- **Automatic Retry**: Hands-off operation - the tool handles timing automatically
- **Intelligent Waiting**: Only waits when necessary, immediately syncs meetings with ready summaries

**Status Logging:**
- Logs show when meetings are skipped: `"Skipping meeting [ID] - summary not ready (current status: processing)"`
- Summary reports include skipped count: `"Summary: 3 meetings processed, 2 skipped (summaries not ready), 0 errors"`
- No action required from user - skipped meetings will be processed automatically once ready

## Team Knowledge

### Component Ownership
- **API Client** (`src/fireflies_client.py`): GraphQL communication and rate limiting
- **Sync Engine** (`src/obsidian_sync.py`): File operations and vault management  
- **Formatter** (`src/markdown_formatter.py`): Template system and YAML frontmatter
- **State Manager** (`src/state_manager.py`): Duplicate prevention and persistence
- **Configuration** (`src/config.py`): Settings management and validation
- **Notifications** (`src/notification_service.py`): macOS notification integration
- **Main Service** (`src/main.py`): Polling loop and orchestration

### Key Design Decisions
- **Virtual Environment**: Isolated dependencies for reliable deployment
- **JSON State**: Simple persistence, can migrate to SQLite later
- **GraphQL**: Fireflies API standard, more efficient than REST
- **Async HTTP**: Better performance for polling architecture
- **YAML + Environment Variables**: Flexible configuration with overrides

### Documentation Links
- **PRD**: `ai-dev-tasks/tasks/prd-fireflies-obsidian-sync.md`
- **Task List**: `ai-dev-tasks/tasks/tasks-prd-fireflies-obsidian-sync.md`
- **Project Rules**: `adams-rules/` directory

### Troubleshooting
- **API Rate Limits**: Check exponential backoff implementation in logs
- **Missing Meetings**: Verify date filter (June 13, 2024+) in config
- **Notification Issues**: System Preferences → Notifications → Python → Allow
- **File Conflicts**: Check `processed_meetings.json` in project root
- **Configuration Errors**: Validate `config.yaml` format and required fields
- **Service Issues**: Check `logs/launch_agent.out.log` and `logs/launch_agent.err.log`
- **Service Won't Start**: LaunchAgent uses `--launch-agent` flag to bypass conflict warnings

### Support
- **Issues**: Report bugs or feature requests via GitHub Issues
- **Documentation**: See `ai-notes/` for implementation details
- **Development**: Follow workflow in `ai-dev-tasks/`