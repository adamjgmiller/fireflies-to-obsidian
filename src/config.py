"""
Configuration management for Fireflies to Obsidian sync tool.

This module handles loading and managing configuration from environment variables,
YAML files, and provides validation for required settings.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

import yaml

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FirefliesConfig:
    """Configuration for Fireflies API."""
    api_key: str
    api_url: str = "https://api.fireflies.ai/graphql"
    rate_limit_requests_per_minute: int = 60
    retry_attempts: int = 3
    backoff_factor: int = 2
    webhook_url: str = ""


@dataclass
class ObsidianConfig:
    """Configuration for Obsidian vault integration."""
    vault_path: str
    fireflies_folder: str = "Fireflies"
    template_path: str = ""
    max_filename_length: int = 50


@dataclass
class SyncConfig:
    """Configuration for sync behavior."""
    polling_interval_seconds: int = 15
    batch_size: int = 10
    lookback_days: int = 7
    from_date: str = "2024-06-13T00:00:00.000Z"  # June 13, 2024 as specified in requirements
    test_mode: bool = False
    test_meeting_ids: list = None


@dataclass
class NotificationConfig:
    """Configuration for notifications."""
    enabled: bool = True
    show_success: bool = True
    show_errors: bool = True


@dataclass
class AppConfig:
    """Main application configuration."""
    fireflies: FirefliesConfig
    obsidian: ObsidianConfig
    sync: SyncConfig
    notifications: NotificationConfig
    debug: bool = False
    log_level: str = "INFO"


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass


class ConfigManager:
    """
    Manages application configuration from multiple sources.
    
    Priority order (highest to lowest):
    1. Environment variables
    2. config.yaml file
    3. Default values
    """
    
    def __init__(self, config_file: str = "config.yaml", env_file: str = ".env"):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to YAML configuration file
            env_file: Path to environment file
        """
        self.config_file = Path(config_file)
        self.env_file = Path(env_file)
        self._config_data = {}
        
    def load_config(self) -> AppConfig:
        """
        Load configuration from all sources.
        
        Returns:
            AppConfig: Complete application configuration
            
        Raises:
            ConfigError: If required configuration is missing or invalid
        """
        logger.info("Loading configuration...")
        
        # Load from .env file if exists
        self._load_env_file()
        
        # Load from YAML config file if exists
        yaml_config = self._load_yaml_config()
        
        # Build configuration with environment variable overrides
        config_data = self._merge_config_sources(yaml_config)
        
        # Validate and create configuration objects
        try:
            config = self._create_config_objects(config_data)
            logger.info("Configuration loaded successfully")
            return config
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise ConfigError(f"Invalid configuration: {e}")
    
    def _load_env_file(self):
        """Load environment variables from .env file."""
        if not self.env_file.exists():
            logger.debug(f".env file not found: {self.env_file}")
            return
        
        try:
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
            
            logger.debug(f"Loaded environment variables from {self.env_file}")
            
        except Exception as e:
            logger.warning(f"Failed to load .env file: {e}")
    
    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_file.exists():
            logger.info(f"Config file not found: {self.config_file}, using defaults")
            return {}
        
        try:
            with open(self.config_file, 'r') as f:
                config_data = yaml.safe_load(f) or {}
            
            logger.debug(f"Loaded YAML configuration from {self.config_file}")
            return config_data
            
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in config file: {e}")
            raise ConfigError(f"Invalid YAML configuration: {e}")
        
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            raise ConfigError(f"Failed to load configuration: {e}")
    
    def _merge_config_sources(self, yaml_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge configuration from YAML and environment variables.
        
        Args:
            yaml_config: Configuration loaded from YAML file
            
        Returns:
            Dict: Merged configuration with environment variable overrides
        """
        # Start with YAML config as base
        config = yaml_config.copy()
        
        # Environment variable mappings
        env_mappings = {
            'FIREFLIES_API_KEY': ['fireflies', 'api_key'],
            'FIREFLIES_API_URL': ['fireflies', 'api_url'],
            'FIREFLIES_WEBHOOK_URL': ['fireflies', 'webhook_url'],
            'OBSIDIAN_VAULT_PATH': ['obsidian', 'vault_path'],
            'OBSIDIAN_FIREFLIES_FOLDER': ['obsidian', 'fireflies_folder'],
            'OBSIDIAN_TEMPLATE_PATH': ['obsidian', 'template_path'],
            'SYNC_POLLING_INTERVAL': ['sync', 'polling_interval_seconds'],
            'SYNC_BATCH_SIZE': ['sync', 'batch_size'],
            'SYNC_LOOKBACK_DAYS': ['sync', 'lookback_days'],
            'SYNC_FROM_DATE': ['sync', 'from_date'],
            'SYNC_TEST_MODE': ['sync', 'test_mode'],
            'SYNC_TEST_MEETING_IDS': ['sync', 'test_meeting_ids'],
            'NOTIFICATIONS_ENABLED': ['notifications', 'enabled'],
            'DEBUG': ['debug'],
            'LOG_LEVEL': ['log_level'],
        }
        
        # Apply environment variable overrides
        for env_key, config_path in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                # Convert string values to appropriate types
                converted_value = self._convert_env_value(env_value, env_key)
                
                # Set nested configuration value
                current = config
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                current[config_path[-1]] = converted_value
                logger.debug(f"Environment override: {env_key} -> {config_path}")
        
        return config
    
    def _convert_env_value(self, value: str, key: str) -> Any:
        """
        Convert environment variable string to appropriate type.
        
        Args:
            value: String value from environment
            key: Environment variable key for type inference
            
        Returns:
            Converted value with appropriate type
        """
        # Boolean conversions
        if key in ['SYNC_TEST_MODE', 'NOTIFICATIONS_ENABLED', 'DEBUG']:
            return value.lower() in ('true', '1', 'yes', 'on')
        
        # Integer conversions
        if key in ['SYNC_POLLING_INTERVAL', 'SYNC_BATCH_SIZE', 'SYNC_LOOKBACK_DAYS']:
            try:
                return int(value)
            except ValueError:
                logger.warning(f"Invalid integer value for {key}: {value}")
                return value
        
        # List conversions (comma-separated)
        if key in ['SYNC_TEST_MEETING_IDS']:
            if value.strip():
                return [item.strip() for item in value.split(',') if item.strip()]
            return []
        
        # String values (default)
        return value
    
    def _create_config_objects(self, config_data: Dict[str, Any]) -> AppConfig:
        """
        Create typed configuration objects from configuration data.
        
        Args:
            config_data: Raw configuration dictionary
            
        Returns:
            AppConfig: Typed configuration object
            
        Raises:
            ConfigError: If required configuration is missing
        """
        # Extract section data with defaults
        fireflies_data = config_data.get('fireflies', {})
        obsidian_data = config_data.get('obsidian', {})
        sync_data = config_data.get('sync', {})
        notifications_data = config_data.get('notifications', {})
        
        # Validate required fields
        api_key = fireflies_data.get('api_key')
        if not api_key:
            raise ConfigError(
                "Fireflies API key is required. Set FIREFLIES_API_KEY environment variable "
                "or add it to config.yaml under fireflies.api_key"
            )
        
        vault_path = obsidian_data.get('vault_path')
        if not vault_path:
            raise ConfigError(
                "Obsidian vault path is required. Set OBSIDIAN_VAULT_PATH environment variable "
                "or add it to config.yaml under obsidian.vault_path"
            )
        
        # Validate vault path exists
        vault_path_obj = Path(vault_path).expanduser()
        if not vault_path_obj.exists():
            raise ConfigError(f"Obsidian vault path does not exist: {vault_path}")
        
        # Create configuration objects
        fireflies_config = FirefliesConfig(
            api_key=api_key,
            api_url=fireflies_data.get('api_url', "https://api.fireflies.ai/graphql"),
            rate_limit_requests_per_minute=fireflies_data.get('rate_limit', {}).get('requests_per_minute', 60),
            retry_attempts=fireflies_data.get('rate_limit', {}).get('retry_attempts', 3),
            backoff_factor=fireflies_data.get('rate_limit', {}).get('backoff_factor', 2),
            webhook_url=fireflies_data.get('webhook_url', "")
        )
        
        obsidian_config = ObsidianConfig(
            vault_path=str(vault_path_obj),
            fireflies_folder=obsidian_data.get('fireflies_folder', 'Fireflies'),
            template_path=obsidian_data.get('template_path', ''),
            max_filename_length=obsidian_data.get('max_filename_length', 50)
        )
        
        sync_config = SyncConfig(
            polling_interval_seconds=sync_data.get('polling_interval_seconds', 15),
            batch_size=sync_data.get('batch_size', 10),
            lookback_days=sync_data.get('lookback_days', 7),
            from_date=sync_data.get('from_date', "2024-06-13T00:00:00.000Z"),
            test_mode=sync_data.get('test_mode', False),
            test_meeting_ids=sync_data.get('test_meeting_ids') or []
        )
        
        notifications_config = NotificationConfig(
            enabled=notifications_data.get('enabled', True),
            show_success=notifications_data.get('show_success', True),
            show_errors=notifications_data.get('show_errors', True)
        )
        
        app_config = AppConfig(
            fireflies=fireflies_config,
            obsidian=obsidian_config,
            sync=sync_config,
            notifications=notifications_config,
            debug=config_data.get('debug', False),
            log_level=config_data.get('log_level', 'INFO')
        )
        
        return app_config
    
    def create_example_config(self, output_file: str = "config.yaml.example"):
        """
        Create an example configuration file.
        
        Args:
            output_file: Path to output example file
        """
        example_config = {
            'fireflies': {
                'api_key': 'your_fireflies_api_key_here',
                'api_url': 'https://api.fireflies.ai/graphql',
                'rate_limit': {
                    'requests_per_minute': 60,
                    'retry_attempts': 3,
                    'backoff_factor': 2
                },
                'webhook_url': ''  # Optional: for webhook mode instead of polling
            },
            'obsidian': {
                'vault_path': '/path/to/your/obsidian/vault',
                'fireflies_folder': 'Fireflies',
                'template_path': '',  # Optional: custom template file
                'max_filename_length': 50
            },
            'sync': {
                'polling_interval_seconds': 15,
                'batch_size': 10,
                'lookback_days': 7,
                'from_date': '2024-06-13T00:00:00.000Z',
                'test_mode': False,
                'test_meeting_ids': []  # For testing specific meetings
            },
            'notifications': {
                'enabled': True,
                'show_success': True,
                'show_errors': True
            },
            'debug': False,
            'log_level': 'INFO'
        }
        
        with open(output_file, 'w') as f:
            yaml.dump(example_config, f, default_flow_style=False, indent=2)
        
        logger.info(f"Created example configuration file: {output_file}")
    
    def create_example_env(self, output_file: str = ".env.example"):
        """
        Create an example environment file.
        
        Args:
            output_file: Path to output example file
        """
        example_env = """# Fireflies to Obsidian Sync Tool - Environment Variables
# Copy this file to .env and fill in your actual values

# Required: Fireflies API Key
# Get this from https://app.fireflies.ai/integrations/fireflies-api
FIREFLIES_API_KEY=your_fireflies_api_key_here

# Required: Path to your Obsidian vault
OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault

# Optional: Override default settings
# FIREFLIES_API_URL=https://api.fireflies.ai/graphql
# OBSIDIAN_FIREFLIES_FOLDER=Fireflies
# SYNC_POLLING_INTERVAL=15
# SYNC_BATCH_SIZE=10
# SYNC_LOOKBACK_DAYS=7
# NOTIFICATIONS_ENABLED=true
# DEBUG=false
# LOG_LEVEL=INFO
"""
        
        with open(output_file, 'w') as f:
            f.write(example_env)
        
        logger.info(f"Created example environment file: {output_file}")


# Global configuration instance
_config_manager = None
_app_config = None


def get_config() -> AppConfig:
    """
    Get the global application configuration.
    
    Returns:
        AppConfig: Application configuration instance
        
    Raises:
        ConfigError: If configuration cannot be loaded
    """
    global _config_manager, _app_config
    
    if _app_config is None:
        if _config_manager is None:
            _config_manager = ConfigManager()
        
        _app_config = _config_manager.load_config()
    
    return _app_config


def reload_config():
    """Reload configuration from files."""
    global _app_config
    _app_config = None 