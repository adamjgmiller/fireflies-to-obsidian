# Task List: Signal-Based Immediate Sync

Based on the manual sync plan for Option 1: Signal-Based Immediate Sync

## Relevant Files

- `src/main.py` - Main application entry point - Added signal handler integration and manual sync logic
- `src/signal_handler.py` - New module for signal handling logic with platform detection and thread-safe sync triggering
- `sync_now.sh` - New executable shell script to send SIGUSR1 signal to running service
- `manage_service.sh` - Service management script - Added `sync-now` command integration
- `tests/test_signal_handler.py` - New unit tests for signal handling functionality
- `tests/test_signal_integration.py` - New integration tests for signal-based sync workflow
- `README.md` - Documentation - Added manual sync instructions and troubleshooting section
- `config.yaml.example` - Configuration template - Added comment about signal-based sync

### Notes

- Signal handlers in Python use the `signal` module and should be registered during application startup
- Use `SIGUSR1` signal for triggering immediate sync as it's safe for user-defined purposes
- The LaunchAgent service PID can be found using `launchctl list | grep com.fireflies.obsidian.sync`
- Tests should verify signal handling without actually running the full sync process
- Use `python -m pytest tests/` to run all tests, or `python -m pytest tests/test_signal_handler.py` for specific tests

## Tasks

- [x] 1.0 Implement signal handling infrastructure
  - [x] 1.1 Create `src/signal_handler.py` module with signal handling utilities
  - [x] 1.2 Add `setup_signal_handlers()` function to register SIGUSR1 handler
  - [x] 1.3 Create `trigger_immediate_sync()` function to set sync flag
  - [x] 1.4 Add thread-safe sync request flag using threading.Event
  - [x] 1.5 Create `is_sync_requested()` and `clear_sync_request()` helper functions
  - [x] 1.6 Add platform detection and graceful handling for non-Unix systems

- [x] 2.0 Modify main polling loop for signal integration
  - [x] 2.1 Import signal_handler module in `src/main.py`
  - [x] 2.2 Call `setup_signal_handlers()` in main() function after configuration load
  - [x] 2.3 Modify `run_polling_loop()` to check for signal-triggered sync requests
  - [x] 2.4 Add immediate sync execution when signal is received (skip waiting)
  - [x] 2.5 Clear sync request flag after processing signal-triggered sync
  - [x] 2.6 Add logging for signal-triggered sync events
  - [x] 2.7 Add "[MANUAL]" prefix to log entries for signal-triggered syncs

- [x] 3.0 Create sync_now.sh script
  - [x] 3.1 Create executable shell script to find running service PID
  - [x] 3.2 Add logic to send SIGUSR1 signal to the service process
  - [x] 3.3 Implement error handling for service not running scenarios
  - [x] 3.4 Add user-friendly status messages for sync trigger success/failure
  - [x] 3.5 Add validation to ensure only one sync signal is sent per call
  - [x] 3.6 Check if sync is already running and provide appropriate feedback

- [x] 4.0 Update service management script
  - [x] 4.1 Add `sync-now` command to `manage_service.sh`
  - [x] 4.2 Integrate sync_now.sh functionality into service management
  - [x] 4.3 Update help text to include new sync-now command
  - [x] 4.4 Add status checking before attempting to send sync signal

- [x] 5.0 Add comprehensive testing
  - [x] 5.1 Create `tests/test_signal_handler.py` with unit tests for signal utilities
  - [x] 5.2 Test signal handler registration and cleanup
  - [x] 5.3 Test sync request flag management (set/clear/check operations)
  - [x] 5.4 Create `tests/test_signal_integration.py` for integration testing
  - [x] 5.5 Test signal-triggered sync in main polling loop
  - [x] 5.6 Add tests for edge cases (signal during sync, multiple signals)
  - [x] 5.7 Test signal handling during graceful shutdown scenarios

- [x] 6.0 Update documentation and user experience
  - [x] 6.1 Update README.md with manual sync instructions
  - [x] 6.2 Document sync_now.sh usage and requirements
  - [x] 6.3 Add troubleshooting section for signal-based sync
  - [x] 6.4 Create examples of checking service status before manual sync
  - [x] 6.5 Document integration with existing LaunchAgent workflow
  - [x] 6.6 Add signal configuration comment to config.yaml.example explaining signal usage 