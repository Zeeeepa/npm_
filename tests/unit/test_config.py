"""Unit tests for configuration module."""
import pytest
from pathlib import Path
from npm_discovery.config import Config, get_config, reset_config


class TestConfig:
    """Test Config class functionality."""
    
    def test_config_loads_with_defaults(self, clean_env):
        """Test config loads with default values when env vars not set."""
        config = Config()
        
        assert config.libraries_io_api_key is None
        assert config.npm_registry_url == "https://registry.npmjs.org"
        assert config.unpkg_url == "https://unpkg.com"
        assert config.cache_ttl_days == 7
        assert config.max_concurrent_requests == 40
        assert config.request_timeout == 30
        assert isinstance(config.cache_dir, Path)
        assert isinstance(config.download_dir, Path)
    
    def test_config_loads_from_environment(self, mock_env):
        """Test config loads values from environment variables."""
        config = Config()
        
        assert config.libraries_io_api_key == "test-api-key-12345"
        assert config.npm_registry_url == "https://registry.npmjs.org"
        assert config.cache_ttl_days == 7
        assert config.max_concurrent_requests == 40
        assert config.request_timeout == 30
    
    def test_config_creates_directories(self, clean_env, tmp_path, monkeypatch):
        """Test config creates cache and download directories."""
        monkeypatch.setenv("DOWNLOAD_DIR", str(tmp_path / "downloads"))
        config = Config()
        
        assert config.cache_dir.exists()
        assert config.download_dir.exists()
        assert config.log_dir.exists()
    
    def test_validate_raises_without_api_key(self, clean_env):
        """Test validate() raises error when API key missing."""
        config = Config()
        
        with pytest.raises(ValueError, match="LIBRARIES_IO_API_KEY.*required"):
            config.validate()
    
    def test_validate_passes_with_api_key(self, mock_env):
        """Test validate() passes when API key present."""
        config = Config()
        config.validate()  # Should not raise
    
    def test_validate_raises_on_invalid_cache_ttl(self, mock_env):
        """Test validate() raises error for invalid cache TTL."""
        config = Config()
        config.cache_ttl_days = 0
        
        with pytest.raises(ValueError, match="CACHE_TTL_DAYS"):
            config.validate()
    
    def test_validate_raises_on_invalid_max_requests(self, mock_env):
        """Test validate() raises error for invalid max concurrent requests."""
        config = Config()
        config.max_concurrent_requests = 0
        
        with pytest.raises(ValueError, match="MAX_CONCURRENT_REQUESTS"):
            config.validate()
    
    def test_validate_raises_on_invalid_timeout(self, mock_env):
        """Test validate() raises error for invalid timeout."""
        config = Config()
        config.request_timeout = 0
        
        with pytest.raises(ValueError, match="REQUEST_TIMEOUT"):
            config.validate()
    
    def test_repr_masks_api_key(self, mock_env):
        """Test __repr__ masks the API key."""
        config = Config()
        repr_str = repr(config)
        
        assert "test-api-key-12345" not in repr_str
        assert "***" in repr_str or "libraries_io_api_key" in repr_str


class TestGetConfig:
    """Test get_config() function."""
    
    def test_get_config_returns_singleton(self, mock_env):
        """Test get_config returns same instance on multiple calls."""
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2
    
    def test_get_config_with_validation(self, mock_env):
        """Test get_config with validation flag."""
        config = get_config(validate=True)  # Should not raise
        assert config is not None
    
    def test_get_config_validation_failure(self, clean_env):
        """Test get_config raises when validation fails."""
        with pytest.raises(ValueError):
            get_config(validate=True)
    
    def test_reset_config_clears_singleton(self, mock_env):
        """Test reset_config clears the singleton instance."""
        config1 = get_config()
        reset_config()
        config2 = get_config()
        
        assert config1 is not config2

