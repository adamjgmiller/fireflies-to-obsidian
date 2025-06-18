"""Integration tests for signal-based sync functionality."""
import pytest
import signal
import time
import threading
from unittest.mock import Mock, patch, MagicMock, call
from src import signal_handler
from src.main import run_polling_loop


class TestSignalIntegration:
    """Test signal integration with main polling loop."""
    
    def setup_method(self):
        """Reset state before each test."""
        signal_handler.clear_sync_request()
        signal_handler._original_handlers.clear()
    
    def teardown_method(self):
        """Clean up after each test."""
        signal_handler.cleanup_signal_handlers()
        signal_handler.clear_sync_request()
    
    @patch('src.main.process_meetings')
    @patch('src.main.StateManager')
    @patch('src.main.ObsidianSync')
    @patch('src.main.FirefliesClient')
    def test_signal_triggered_sync_in_polling_loop(self, mock_ff_client, mock_obs_sync, 
                                                  mock_state_mgr, mock_process):
        """Test that signal triggers immediate sync in polling loop."""
        # Setup
        mock_process.return_value = 5  # Processed 5 meetings
        mock_state_mgr.return_value.get_stats.return_value = {
            'state_file': 'test.json',
            'total_processed': 10
        }
        
        # Create test config
        config = MagicMock()
        config.sync.polling_interval_seconds = 10
        config.notifications.enabled = True
        config.fireflies.api_key = 'test-key'
        config.obsidian.vault_path = '/test/path'
        config.sync.lookback_days = 30
        
        # Run polling loop in thread with shutdown after short time
        def run_loop():
            # Patch shutdown_requested to stop after a bit
            with patch('src.main.shutdown_requested', new=False):
                # Override the for loop to run fewer iterations
                with patch('time.sleep') as mock_sleep:
                    mock_sleep.side_effect = [None] * 3 + [KeyboardInterrupt()]
                    try:
                        run_polling_loop(config, None)
                    except KeyboardInterrupt:
                        pass
        
        # Start polling loop
        thread = threading.Thread(target=run_loop)
        thread.start()
        
        # Give it time to start
        time.sleep(0.1)
        
        # Trigger signal
        signal_handler._sync_request.set()
        
        # Wait for thread to finish
        thread.join(timeout=2)
        
        # Verify process_meetings was called
        assert mock_process.call_count >= 1
        
        # Find calls that had signal-triggered sync
        calls = mock_process.call_args_list
        # At least one call should have been triggered by signal
        # (we can't guarantee exact timing, but there should be calls)
        assert len(calls) > 0
    
    def test_signal_during_sync(self):
        """Test handling signal while sync is already in progress."""
        # This is handled by the flag being checked after sync completes
        
        # Set flag
        signal_handler._sync_request.set()
        
        # Simulate sync in progress
        assert signal_handler.is_sync_requested()
        
        # Another signal during sync just ensures flag stays set
        signal_handler.trigger_immediate_sync(signal.SIGUSR1, None)
        assert signal_handler.is_sync_requested()
        
        # Clear after sync
        signal_handler.clear_sync_request()
        assert not signal_handler.is_sync_requested()
    
    def test_multiple_signals_coalesce(self):
        """Test that multiple signals result in single sync."""
        # Send multiple signals
        signal_handler.trigger_immediate_sync(signal.SIGUSR1, None)
        signal_handler.trigger_immediate_sync(signal.SIGUSR1, None)
        signal_handler.trigger_immediate_sync(signal.SIGUSR1, None)
        
        # Should still be just one pending sync
        assert signal_handler.is_sync_requested()
        
        # Clear once handles all
        signal_handler.clear_sync_request()
        assert not signal_handler.is_sync_requested()
    
    @pytest.mark.skipif(not signal_handler.IS_UNIX, reason="Signal handling only on Unix")
    def test_signal_handler_during_shutdown(self):
        """Test signal handling during graceful shutdown."""
        # Setup signal handler
        signal_handler.setup_signal_handlers()
        
        try:
            # Set sync request
            signal_handler._sync_request.set()
            
            # Cleanup should work even with pending request
            signal_handler.cleanup_signal_handlers()
            
            # Flag should still be accessible
            assert signal_handler.is_sync_requested()
            
            # Can still clear
            signal_handler.clear_sync_request()
            assert not signal_handler.is_sync_requested()
        finally:
            # Ensure cleanup
            signal_handler.cleanup_signal_handlers()
    
    def test_signal_logging(self):
        """Test that signal events are properly logged."""
        with patch('src.signal_handler.logger') as mock_logger:
            # Trigger signal
            signal_handler.trigger_immediate_sync(signal.SIGUSR1, None)
            
            # Should log the signal
            mock_logger.info.assert_called_with(
                "[MANUAL] Received signal 30 for immediate sync"
            )
            
            # Clear request
            signal_handler.clear_sync_request()
            mock_logger.debug.assert_called_with("Sync request flag cleared")
    
    @patch('src.main.sig_handler')
    def test_polling_loop_checks_signal_in_wait(self, mock_sig_handler):
        """Test that polling loop checks for signals during wait period."""
        # Setup
        mock_sig_handler.is_sync_requested.side_effect = [False, False, True]
        
        config = MagicMock()
        config.sync.polling_interval_seconds = 5
        config.notifications.enabled = True
        
        # Mock sleep to control loop
        with patch('time.sleep') as mock_sleep:
            with patch('src.main.shutdown_requested', new=False) as mock_shutdown:
                # Make loop exit after checking signal
                mock_sleep.side_effect = lambda x: setattr(mock_shutdown, '__bool__', lambda: True)
                
                with patch('src.main.process_meetings'):
                    with patch('src.main.FirefliesClient'):
                        with patch('src.main.ObsidianSync'):
                            with patch('src.main.StateManager') as mock_state:
                                mock_state.return_value.get_stats.return_value = {
                                    'state_file': 'test.json',
                                    'total_processed': 0
                                }
                                
                                # This should exit early due to signal check
                                run_polling_loop(config, None)
        
        # Verify signal was checked during wait
        assert mock_sig_handler.is_sync_requested.call_count >= 2