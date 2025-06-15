# Task List: Fireflies to Obsidian Sync Tool

Based on PRD: prd-fireflies-obsidian-sync.md

## Relevant Files

- `src/main.py` - Main application entry point and polling loop
- `src/fireflies_client.py` - Fireflies API client with GraphQL support
- `src/obsidian_sync.py` - Obsidian vault file creation and management
- `src/config.py` - Configuration management for API keys and settings
- `src/state_manager.py` - Track processed meetings to avoid duplicates
- `src/notification_service.py` - macOS notification system
- `src/markdown_formatter.py` - Format meeting data into structured Markdown
- `src/utils/logger.py` - Logging utility for debugging and monitoring
- `tests/test_fireflies_client.py` - Unit tests for Fireflies API client
- `tests/test_obsidian_sync.py` - Unit tests for Obsidian sync functionality
- `tests/test_markdown_formatter.py` - Unit tests for Markdown formatting
- `tests/test_state_manager.py` - Unit tests for state management
- `config.yaml` - User configuration file template
- `.env.example` - Environment variables template
- `requirements.txt` - Python dependencies

### Notes

- Unit tests should be placed in the `tests/` directory
- Use `pytest` to run tests: `pytest tests/` for all tests or `pytest tests/test_specific.py` for individual test files
- Configuration files should have example templates for user setup

## Tasks

- [ ] 1.0 Set up virtual environment and project foundation
- [ ] 2.0 Implement Fireflies API client with GraphQL support
- [ ] 3.0 Build Obsidian vault integration and file management
- [ ] 4.0 Create meeting data processing and Markdown formatting
- [ ] 5.0 Implement continuous polling service with state management