"""
Tests for configuration validation.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from spot_downloader.config import Config, ConfigModel


class TestConfigModel:
    """Test ConfigModel validation."""

    def test_valid_config(self):
        """Test valid configuration is accepted."""
        config = ConfigModel(
            download_path="downloads",
            max_concurrent_downloads=5,
            download_quality="320kbps",
            file_format="mp3",
            log_level="INFO",
        )
        assert config.download_quality == "320kbps"
        assert config.file_format == "mp3"

    def test_invalid_quality(self):
        """Test invalid quality is rejected."""
        with pytest.raises(ValueError) as exc_info:
            ConfigModel(download_quality="invalid")
        assert "Invalid quality" in str(exc_info.value)

    def test_invalid_format(self):
        """Test invalid format is rejected."""
        with pytest.raises(ValueError) as exc_info:
            ConfigModel(file_format="wav")
        assert "Invalid format" in str(exc_info.value)

    def test_invalid_log_level(self):
        """Test invalid log level is rejected."""
        with pytest.raises(ValueError) as exc_info:
            ConfigModel(log_level="VERBOSE")
        assert "Invalid log level" in str(exc_info.value)

    def test_concurrent_downloads_min(self):
        """Test minimum concurrent downloads."""
        config = ConfigModel(max_concurrent_downloads=1)
        assert config.max_concurrent_downloads == 1

    def test_concurrent_downloads_max(self):
        """Test maximum concurrent downloads is enforced."""
        with pytest.raises(ValueError) as exc_info:
            ConfigModel(max_concurrent_downloads=11)
        assert "less than or equal to 10" in str(exc_info.value)

    def test_retry_attempts_range(self):
        """Test retry attempts range validation."""
        with pytest.raises(ValueError):
            ConfigModel(retry_attempts=11)
        
        config = ConfigModel(retry_attempts=0)
        assert config.retry_attempts == 0

    def test_timeout_range(self):
        """Test timeout range validation."""
        with pytest.raises(ValueError):
            ConfigModel(timeout_seconds=301)
        
        with pytest.raises(ValueError):
            ConfigModel(timeout_seconds=4)
        
        config = ConfigModel(timeout_seconds=60)
        assert config.timeout_seconds == 60

    def test_default_values(self):
        """Test default configuration values."""
        config = ConfigModel()
        assert config.download_path == "downloads"
        assert config.max_concurrent_downloads == 5
        assert config.download_quality == "320kbps"
        assert config.file_format == "mp3"
        assert config.enable_logging is True
        assert config.log_level == "INFO"


class TestConfig:
    """Test Config class."""

    def test_config_loads_defaults(self, tmp_path):
        """Test Config loads default values when no file exists."""
        config_file = tmp_path / "nonexistent.json"
        config = Config(str(config_file))
        assert config.download_quality == "320kbps"

    def test_config_saves_and_loads(self, tmp_path):
        """Test Config saves and loads correctly."""
        config_file = tmp_path / "test_config.json"
        config = Config(str(config_file))
        config.set("download_quality", "256kbps")
        config.save_config()
        
        # Load again
        config2 = Config(str(config_file))
        assert config2.download_quality == "256kbps"

    def test_config_validation_error(self, tmp_path):
        """Test Config handles validation errors gracefully."""
        config_file = tmp_path / "invalid_config.json"
        # Create invalid config file
        import json
        with open(config_file, "w") as f:
            json.dump({"download_quality": "invalid"}, f)
        
        # Should fall back to defaults
        config = Config(str(config_file))
        assert config.download_quality == "320kbps"  # Default
