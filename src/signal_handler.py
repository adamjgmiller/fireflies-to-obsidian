"""Signal handling utilities for triggering immediate sync."""
import signal
import threading
import platform
from typing import Optional, Callable
from .utils.logger import get_logger

logger = get_logger(__name__)

# Thread-safe event for sync requests
_sync_request = threading.Event()

# Store original signal handlers for cleanup
_original_handlers = {}

# Flag to track if we're on a Unix-like system
IS_UNIX = platform.system() in ['Darwin', 'Linux', 'FreeBSD', 'OpenBSD', 'NetBSD']


def trigger_immediate_sync(signum: int, frame) -> None:
    """Signal handler that triggers an immediate sync.
    
    Args:
        signum: Signal number received
        frame: Current stack frame (unused)
    """
    logger.info(f"[MANUAL] Received signal {signum} for immediate sync")
    _sync_request.set()


def setup_signal_handlers() -> None:
    """Register signal handlers for immediate sync triggering.
    
    On Unix systems, registers SIGUSR1 handler.
    On non-Unix systems, logs a warning and returns gracefully.
    """
    if not IS_UNIX:
        logger.warning("Signal-based sync not available on non-Unix systems")
        return
    
    try:
        # Store original handler for cleanup
        _original_handlers[signal.SIGUSR1] = signal.signal(signal.SIGUSR1, trigger_immediate_sync)
        logger.info("Signal handler registered for SIGUSR1")
    except Exception as e:
        logger.error(f"Failed to register signal handler: {e}")


def cleanup_signal_handlers() -> None:
    """Restore original signal handlers."""
    if not IS_UNIX:
        return
    
    for sig, handler in _original_handlers.items():
        try:
            signal.signal(sig, handler)
            logger.debug(f"Restored original handler for signal {sig}")
        except Exception as e:
            logger.error(f"Failed to restore signal handler for {sig}: {e}")
    
    _original_handlers.clear()


def is_sync_requested() -> bool:
    """Check if an immediate sync has been requested via signal.
    
    Returns:
        bool: True if sync was requested, False otherwise
    """
    return _sync_request.is_set()


def clear_sync_request() -> None:
    """Clear the sync request flag after processing."""
    if _sync_request.is_set():
        _sync_request.clear()
        logger.debug("Sync request flag cleared")


def wait_for_sync_request(timeout: Optional[float] = None) -> bool:
    """Wait for a sync request with optional timeout.
    
    Args:
        timeout: Maximum time to wait in seconds, None for no timeout
        
    Returns:
        bool: True if sync was requested, False if timeout occurred
    """
    return _sync_request.wait(timeout)