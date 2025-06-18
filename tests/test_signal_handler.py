"""Unit tests for signal handling functionality."""
import pytest
import signal
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from src import signal_handler


class TestSignalHandler:
    """Test signal handling utilities."""
    
    def setup_method(self):
        """Reset state before each test."""
        # Clear any existing sync requests
        signal_handler.clear_sync_request()
        # Clear stored handlers
        signal_handler._original_handlers.clear()
    
    def teardown_method(self):
        """Clean up after each test."""
        # Ensure signal handlers are cleaned up
        signal_handler.cleanup_signal_handlers()
        signal_handler.clear_sync_request()
    
    def test_sync_request_flag_operations(self):
        """Test sync request flag set/check/clear operations."""
        # Initially should not be requested
        assert not signal_handler.is_sync_requested()
        
        # Set the flag directly
        signal_handler._sync_request.set()
        assert signal_handler.is_sync_requested()
        
        # Clear the flag
        signal_handler.clear_sync_request()
        assert not signal_handler.is_sync_requested()
    
    def test_trigger_immediate_sync(self):
        """Test the signal handler function sets the sync flag."""
        # Ensure flag is clear
        assert not signal_handler.is_sync_requested()
        
        # Call the signal handler
        signal_handler.trigger_immediate_sync(signal.SIGUSR1, None)
        
        # Flag should be set
        assert signal_handler.is_sync_requested()
    
    @pytest.mark.skipif(not signal_handler.IS_UNIX, reason="Signal handling only on Unix")
    def test_setup_signal_handlers_unix(self):
        """Test signal handler registration on Unix systems."""
        with patch('signal.signal') as mock_signal:
            # Setup should register SIGUSR1
            signal_handler.setup_signal_handlers()
            
            # Verify signal was registered
            mock_signal.assert_called_once_with(signal.SIGUSR1, signal_handler.trigger_immediate_sync)
    
    @pytest.mark.skipif(signal_handler.IS_UNIX, reason="Testing non-Unix behavior")
    def test_setup_signal_handlers_non_unix(self):
        """Test graceful handling on non-Unix systems."""
        with patch('src.signal_handler.IS_UNIX', False):
            with patch('signal.signal') as mock_signal:
                # Setup should not register any signals
                signal_handler.setup_signal_handlers()
                
                # Verify no signals were registered
                mock_signal.assert_not_called()
    
    @pytest.mark.skipif(not signal_handler.IS_UNIX, reason="Signal handling only on Unix")
    def test_cleanup_signal_handlers(self):
        """Test signal handler cleanup restores original handlers."""
        original_handler = signal.signal(signal.SIGUSR1, signal.SIG_IGN)
        
        try:
            # Setup handlers
            signal_handler.setup_signal_handlers()
            
            # Cleanup should restore original
            signal_handler.cleanup_signal_handlers()
            
            # Verify original handler is restored
            current_handler = signal.signal(signal.SIGUSR1, signal.SIG_DFL)
            assert current_handler == signal.SIG_IGN
        finally:
            # Restore actual original handler
            signal.signal(signal.SIGUSR1, original_handler)
    
    def test_wait_for_sync_request_timeout(self):
        """Test waiting for sync request with timeout."""
        # Ensure flag is clear
        signal_handler.clear_sync_request()
        
        # Wait should timeout and return False
        start_time = time.time()
        result = signal_handler.wait_for_sync_request(timeout=0.1)
        elapsed = time.time() - start_time
        
        assert not result
        assert elapsed >= 0.1
        assert elapsed < 0.2  # Should not wait much longer than timeout
    
    def test_wait_for_sync_request_signaled(self):
        """Test waiting for sync request that gets signaled."""
        # Clear flag
        signal_handler.clear_sync_request()
        
        # Set flag in another thread after short delay
        def set_flag():
            time.sleep(0.05)
            signal_handler._sync_request.set()
        
        thread = threading.Thread(target=set_flag)
        thread.start()
        
        # Wait should return True when flag is set
        start_time = time.time()
        result = signal_handler.wait_for_sync_request(timeout=0.5)
        elapsed = time.time() - start_time
        
        thread.join()
        
        assert result
        assert elapsed < 0.1  # Should return quickly after flag is set
    
    def test_multiple_signal_handlers(self):
        """Test that multiple signals don't interfere."""
        # Set flag multiple times
        signal_handler.trigger_immediate_sync(signal.SIGUSR1, None)
        signal_handler.trigger_immediate_sync(signal.SIGUSR1, None)
        signal_handler.trigger_immediate_sync(signal.SIGUSR1, None)
        
        # Should still just be set once
        assert signal_handler.is_sync_requested()
        
        # Clear once should clear it
        signal_handler.clear_sync_request()
        assert not signal_handler.is_sync_requested()
    
    def test_thread_safety(self):
        """Test thread safety of sync request flag."""
        results = []
        
        def worker():
            # Each thread sets and clears the flag
            for i in range(100):
                signal_handler._sync_request.set()
                if signal_handler.is_sync_requested():
                    results.append(True)
                signal_handler.clear_sync_request()
        
        # Run multiple threads
        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All operations should have succeeded
        assert len(results) == 500  # 5 threads * 100 iterations