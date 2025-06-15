"""
Logging utility for the Fireflies to Obsidian sync tool.

This module provides centralized logging configuration with support for
file and console output, configurable log levels, and log rotation.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "fireflies_sync",
    log_level: str = "INFO",
    log_file_path: Optional[str] = None,
    max_file_size_mb: int = 10,
    backup_count: int = 5,
    console_output: bool = True
) -> logging.Logger:
    """
    Set up and configure a logger with file and console handlers.
    
    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file_path: Path to log file. If None, logs to 'logs/fireflies_sync.log'
        max_file_size_mb: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        console_output: Whether to output logs to console
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Prevent duplicate handlers if logger already exists
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set up file handler with rotation
    if log_file_path is None:
        log_file_path = "logs/fireflies_sync.log"
    
    # Create logs directory if it doesn't exist
    log_dir = Path(log_file_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=max_file_size_mb * 1024 * 1024,  # Convert MB to bytes
        backupCount=backup_count
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = "fireflies_sync") -> logging.Logger:
    """
    Get an existing logger or create a new one with default settings.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # If logger doesn't have handlers, set it up with defaults
    if not logger.handlers:
        # Get log level from environment variable or default to INFO
        log_level = os.getenv("LOG_LEVEL", "INFO")
        logger = setup_logger(name=name, log_level=log_level)
    
    return logger


# Create a default logger instance
default_logger = get_logger()


def log_api_request(url: str, method: str = "GET", status_code: Optional[int] = None):
    """
    Log API request details.
    
    Args:
        url: API endpoint URL
        method: HTTP method
        status_code: Response status code (if available)
    """
    if status_code:
        default_logger.info(f"API {method} {url} - Status: {status_code}")
    else:
        default_logger.info(f"API {method} {url}")


def log_file_operation(operation: str, file_path: str, success: bool = True):
    """
    Log file operation details.
    
    Args:
        operation: Type of operation (create, update, delete, etc.)
        file_path: Path to the file
        success: Whether the operation was successful
    """
    status = "SUCCESS" if success else "FAILED"
    default_logger.info(f"File {operation} - {file_path} - {status}")


def log_sync_status(processed_count: int, error_count: int = 0):
    """
    Log sync operation status.
    
    Args:
        processed_count: Number of meetings processed
        error_count: Number of errors encountered
    """
    if error_count == 0:
        default_logger.info(f"Sync completed successfully - Processed {processed_count} meetings")
    else:
        default_logger.warning(
            f"Sync completed with errors - Processed {processed_count} meetings, "
            f"{error_count} errors"
        )


# Convenience functions for common logging patterns
def debug(message: str, *args, **kwargs):
    """Log debug message."""
    default_logger.debug(message, *args, **kwargs)


def info(message: str, *args, **kwargs):
    """Log info message."""
    default_logger.info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs):
    """Log warning message."""
    default_logger.warning(message, *args, **kwargs)


def error(message: str, *args, **kwargs):
    """Log error message."""
    default_logger.error(message, *args, **kwargs)


def critical(message: str, *args, **kwargs):
    """Log critical message."""
    default_logger.critical(message, *args, **kwargs) 