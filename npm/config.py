"""Configuration management for NPM Discovery application.

Loads settings from environment variables with sane defaults.
"""
import os
from pathlib import Path
from typing import Optional


class Config:
    """Application configuration loaded from environment variables."""
    
    def __init__(self):
        """Initialize configuration from environment."""
        # API Keys
        self.libraries_io_api_key: Optional[str] = os.getenv("LIBRARIES_IO_API_KEY")
        
        # API Endpoints
        self.npm_registry_url: str = os.getenv(
            "NPM_REGISTRY_URL", 
            "https://registry.npmjs.org"
        )
        self.npm_downloads_url: str = "https://api.npmjs.org/downloads"
        self.unpkg_url: str = os.getenv("UNPKG_URL", "https://unpkg.com")
        
        # Cache Settings
        self.cache_ttl_days: int = int(os.getenv("CACHE_TTL_DAYS", "7"))
        self.cache_dir: Path = Path.home() / ".npm_discovery" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # HTTP Settings
        self.max_concurrent_requests: int = int(
            os.getenv("MAX_CONCURRENT_REQUESTS", "40")
        )
        self.request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
        self.user_agent: str = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
        
        # Download Settings
        default_download_dir = Path.home() / "npm_packages"
        self.download_dir: Path = Path(
            os.getenv("DOWNLOAD_DIR", str(default_download_dir))
        )
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Logging Settings
        self.log_dir: Path = Path.home() / ".npm_discovery" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file: Path = self.log_dir / "npm_discovery.log"
        self.log_max_bytes: int = 5 * 1024 * 1024  # 5MB
        self.log_backup_count: int = 2
    
    def validate(self) -> None:
        """Validate required configuration.
        
        Raises:
            ValueError: If required configuration is missing or invalid.
        """
        if not self.libraries_io_api_key:
            raise ValueError(
                "LIBRARIES_IO_API_KEY environment variable is required. "
                "Get your key at https://libraries.io/account and set it in .env file."
            )
        
        if self.cache_ttl_days < 1:
            raise ValueError("CACHE_TTL_DAYS must be at least 1")
        
        if self.max_concurrent_requests < 1:
            raise ValueError("MAX_CONCURRENT_REQUESTS must be at least 1")
        
        if self.request_timeout < 1:
            raise ValueError("REQUEST_TIMEOUT must be at least 1")
    
    def __repr__(self) -> str:
        """String representation of config (masks API key)."""
        return (
            f"Config("
            f"libraries_io_api_key={'***' if self.libraries_io_api_key else None}, "
            f"npm_registry_url={self.npm_registry_url}, "
            f"unpkg_url={self.unpkg_url}, "
            f"cache_ttl_days={self.cache_ttl_days})"
        )


# Global config instance
_config: Optional[Config] = None


def get_config(validate: bool = False) -> Config:
    """Get or create the global configuration instance.
    
    Args:
        validate: If True, validate required configuration.
        
    Returns:
        Config instance.
        
    Raises:
        ValueError: If validate=True and configuration is invalid.
    """
    global _config
    if _config is None:
        _config = Config()
        if validate:
            _config.validate()
    return _config


def reset_config() -> None:
    """Reset the global configuration instance (useful for testing)."""
    global _config
    _config = None

