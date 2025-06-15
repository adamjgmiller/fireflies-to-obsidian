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

- [x] 1.0 Set up virtual environment and project foundation
  - [x] 1.1 Create virtual environment with `python -m venv venv`
  - [x] 1.2 Create project directory structure (src/, tests/, config files)
  - [x] 1.3 Create requirements.txt with dependencies (httpx, pyyaml, pytest)
  - [x] 1.4 Set up .env.example and config.yaml template files
  - [x] 1.5 Initialize git repository and create .gitignore
  - [x] 1.6 Create basic logging configuration in src/utils/logger.py
- [ ] 2.0 Implement Fireflies API client with GraphQL support
  - [ ] 2.1 Create src/fireflies_client.py with GraphQL query methods
  - [ ] 2.2 Implement authentication and API key management
  - [ ] 2.3 Add meeting data retrieval with pagination support
  - [ ] 2.4 Implement rate limiting and exponential backoff
  - [ ] 2.5 Add error handling for API failures and network issues
  - [ ] 2.6 Create unit tests for API client functionality
- [ ] 3.0 Build Obsidian vault integration and file management
  - [ ] 3.1 Create src/obsidian_sync.py for file operations
  - [ ] 3.2 Implement Fireflies folder creation in Obsidian vault
  - [ ] 3.3 Add file naming logic (YYYY-MM-DD-HH-MM-[Meeting Title].md)
  - [ ] 3.4 Implement duplicate file detection and handling
  - [ ] 3.5 Add configuration for custom Obsidian vault path
  - [ ] 3.6 Create unit tests for file operations
- [ ] 4.0 Create meeting data processing and Markdown formatting
  - [ ] 4.1 Create src/markdown_formatter.py with template system
  - [ ] 4.2 Implement YAML frontmatter generation with all metadata
  - [ ] 4.3 Format transcript with grouped speaker sections
  - [ ] 4.4 Add meeting details, attendees, and summary sections
  - [ ] 4.5 Process action items and key topics from Fireflies data
  - [ ] 4.6 Create unit tests for Markdown formatting
- [ ] 5.0 Implement continuous polling service with state management
  - [ ] 5.1 Create src/state_manager.py to track processed meetings
  - [ ] 5.2 Implement main polling loop in src/main.py with 15-second intervals
  - [ ] 5.3 Add macOS notification system in src/notification_service.py
  - [ ] 5.4 Implement test mode for specific Meeting IDs
  - [ ] 5.5 Add graceful shutdown handling and error recovery
  - [ ] 5.6 Create startup script that activates venv and runs service
  - [ ] 5.7 Add integration tests for end-to-end functionality