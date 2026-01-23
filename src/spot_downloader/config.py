"""
Configuration module for the Spotify Downloader application.
Handles application settings and default configurations.
"""

import json
import os
from typing import Dict, Any, Optional


class Config:
    """Application configuration class."""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.settings = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or return defaults."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return {**self._get_defaults(), **loaded_config}
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config file: {e}. Using defaults.")
                return self._get_defaults()
        else:
            return self._get_defaults()
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "download_path": "downloads",
            "max_concurrent_downloads": 5,
            "download_quality": "320kbps",  # Options: "128kbps", "256kbps", "320kbps"
            "file_format": "mp3",  # Options: "mp3", "flac", "m4a"
            "enable_logging": True,
            "log_level": "INFO",  # Options: "DEBUG", "INFO", "WARNING", "ERROR"
            "retry_attempts": 3,
            "timeout_seconds": 30,
            "safe_mode": True,  # Enable extra security validations
        }
    
    def save_config(self) -> bool:
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except IOError as e:
            print(f"Error saving config file: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self.settings[key] = value
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple configuration values."""
        self.settings.update(updates)
    
    @property
    def download_path(self) -> str:
        """Get the download path."""
        return self.settings.get("download_path", "downloads")
    
    @property
    def max_concurrent_downloads(self) -> int:
        """Get the maximum number of concurrent downloads."""
        return self.settings.get("max_concurrent_downloads", 5)
    
    @property
    def download_quality(self) -> str:
        """Get the download quality setting."""
        return self.settings.get("download_quality", "320kbps")
    
    @property
    def file_format(self) -> str:
        """Get the file format setting."""
        return self.settings.get("file_format", "mp3")
    
    @property
    def enable_logging(self) -> bool:
        """Check if logging is enabled."""
        return self.settings.get("enable_logging", True)
    
    @property
    def log_level(self) -> str:
        """Get the log level."""
        return self.settings.get("log_level", "INFO")
    
    @property
    def retry_attempts(self) -> int:
        """Get the number of retry attempts."""
        return self.settings.get("retry_attempts", 3)
    
    @property
    def timeout_seconds(self) -> int:
        """Get the timeout in seconds."""
        return self.settings.get("timeout_seconds", 30)
    
    @property
    def safe_mode(self) -> bool:
        """Check if safe mode is enabled."""
        return self.settings.get("safe_mode", True)


# Global configuration instance
app_config = Config()