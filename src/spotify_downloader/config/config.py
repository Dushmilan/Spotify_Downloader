"""
Configuration management for the Spotify Downloader.

Provides centralized configuration management with default values
and environment-based overrides.
"""
import os
from typing import Dict, Any, Optional


class Config:
    """Configuration class for Spotify Downloader."""
    
    # Default values
    DEFAULT_OUTPUT_DIR = "./downloads"
    DEFAULT_AUDIO_FORMAT = "mp3"
    DEFAULT_AUDIO_QUALITY = "192k"
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_TIMEOUT = 30
    
    def __init__(self):
        """Initialize configuration with environment variable overrides."""
        self.output_dir = os.getenv("SPOTIFY_OUTPUT_DIR", self.DEFAULT_OUTPUT_DIR)
        self.audio_format = os.getenv("SPOTIFY_AUDIO_FORMAT", self.DEFAULT_AUDIO_FORMAT)
        self.audio_quality = os.getenv("SPOTIFY_AUDIO_QUALITY", self.DEFAULT_AUDIO_QUALITY)
        self.max_retries = int(os.getenv("SPOTIFY_MAX_RETRIES", str(self.DEFAULT_MAX_RETRIES)))
        self.timeout = int(os.getenv("SPOTIFY_TIMEOUT", str(self.DEFAULT_TIMEOUT)))
        
    def get_config(self) -> Dict[str, Any]:
        """Get all configuration values as a dictionary."""
        return {
            "output_dir": self.output_dir,
            "audio_format": self.audio_format,
            "audio_quality": self.audio_quality,
            "max_retries": self.max_retries,
            "timeout": self.timeout
        }
    
    def update(self, **kwargs) -> None:
        """Update configuration values."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @staticmethod
    def load_from_file(config_path: Optional[str] = None) -> 'Config':
        """Load configuration from a file (TOML, JSON, or environment file)."""
        config = Config()
        # In a real implementation, you would parse a config file here
        # For now, just return the default config
        return config