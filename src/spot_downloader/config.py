"""
Configuration validation using Pydantic.
Provides type-safe configuration with validation.
"""

import json
import os
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator


class ConfigModel(BaseModel):
    """Pydantic model for configuration validation."""
    
    download_path: str = Field(default="downloads", description="Directory for downloaded files")
    max_concurrent_downloads: int = Field(default=5, ge=1, le=10, description="Max simultaneous downloads")
    download_quality: str = Field(default="320kbps", description="Audio quality")
    file_format: str = Field(default="mp3", description="Output format")
    enable_logging: bool = Field(default=True, description="Enable logging")
    log_level: str = Field(default="INFO", description="Logging level")
    retry_attempts: int = Field(default=3, ge=0, le=10, description="Retry attempts")
    timeout_seconds: int = Field(default=30, ge=5, le=300, description="Network timeout")
    safe_mode: bool = Field(default=True, description="Enable safe mode")
    
    @field_validator("download_quality")
    @classmethod
    def validate_quality(cls, v: str) -> str:
        """Validate download quality setting."""
        valid_qualities = ["128kbps", "256kbps", "320kbps"]
        if v not in valid_qualities:
            raise ValueError(f"Invalid quality: {v}. Must be one of {valid_qualities}")
        return v
    
    @field_validator("file_format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate file format setting."""
        valid_formats = ["mp3", "flac", "m4a"]
        if v not in valid_formats:
            raise ValueError(f"Invalid format: {v}. Must be one of {valid_formats}")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level setting."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()
    
    @field_validator("download_path")
    @classmethod
    def validate_download_path(cls, v: str) -> str:
        """Validate download path."""
        if not v or not isinstance(v, str):
            raise ValueError("Download path must be a non-empty string")
        # Normalize path
        return v.replace("\\", "/")


class Config:
    """Application configuration with Pydantic validation."""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self._config_model = self._load_and_validate()

    def _load_and_validate(self) -> ConfigModel:
        """Load configuration from file and validate with Pydantic."""
        defaults = self._get_defaults()
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)
                # Merge with defaults
                merged = {**defaults, **loaded_config}
                return ConfigModel(**merged)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config file: {e}. Using defaults.")
                return ConfigModel(**defaults)
            except Exception as e:
                print(f"Config validation error: {e}. Using defaults.")
                return ConfigModel(**defaults)
        else:
            return ConfigModel(**defaults)

    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "download_path": "downloads",
            "max_concurrent_downloads": 5,
            "download_quality": "320kbps",
            "file_format": "mp3",
            "enable_logging": True,
            "log_level": "INFO",
            "retry_attempts": 3,
            "timeout_seconds": 30,
            "safe_mode": True,
        }

    def save_config(self) -> bool:
        """Save current configuration to file."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config_model.model_dump(), f, indent=2)
            return True
        except IOError as e:
            print(f"Error saving config file: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return getattr(self._config_model, key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value (with validation on next save)."""
        try:
            # Update the model - will validate on save
            updated = self._config_model.model_dump()
            updated[key] = value
            self._config_model = ConfigModel(**updated)
        except Exception as e:
            raise ValueError(f"Invalid config value for {key}: {e}")

    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple configuration values."""
        try:
            updated = self._config_model.model_dump()
            updated.update(updates)
            self._config_model = ConfigModel(**updated)
        except Exception as e:
            raise ValueError(f"Config validation error: {e}")

    def validate(self) -> bool:
        """Validate current configuration."""
        try:
            ConfigModel(**self._config_model.model_dump())
            return True
        except Exception:
            return False

    @property
    def download_path(self) -> str:
        """Get the download path."""
        return self._config_model.download_path

    @property
    def max_concurrent_downloads(self) -> int:
        """Get the maximum number of concurrent downloads."""
        return self._config_model.max_concurrent_downloads

    @property
    def download_quality(self) -> str:
        """Get the download quality setting."""
        return self._config_model.download_quality

    @property
    def file_format(self) -> str:
        """Get the file format setting."""
        return self._config_model.file_format

    @property
    def enable_logging(self) -> bool:
        """Check if logging is enabled."""
        return self._config_model.enable_logging

    @property
    def log_level(self) -> str:
        """Get the log level."""
        return self._config_model.log_level

    @property
    def retry_attempts(self) -> int:
        """Get the number of retry attempts."""
        return self._config_model.retry_attempts

    @property
    def timeout_seconds(self) -> int:
        """Get the timeout in seconds."""
        return self._config_model.timeout_seconds

    @property
    def safe_mode(self) -> bool:
        """Check if safe mode is enabled."""
        return self._config_model.safe_mode


# Global configuration instance
app_config = Config()
