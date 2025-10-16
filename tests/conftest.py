"""Pytest configuration and shared fixtures."""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, Any


@pytest.fixture
def clean_env(monkeypatch):
    """Provide clean environment without any NPM-related vars."""
    env_vars = [
        "LIBRARIES_IO_API_KEY",
        "NPM_REGISTRY_URL",
        "UNPKG_URL",
        "CACHE_TTL_DAYS",
        "MAX_CONCURRENT_REQUESTS",
        "REQUEST_TIMEOUT",
        "DOWNLOAD_DIR",
    ]
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)
    return monkeypatch


@pytest.fixture
def mock_env(monkeypatch):
    """Provide mock environment with valid config."""
    monkeypatch.setenv("LIBRARIES_IO_API_KEY", "test-api-key-12345")
    monkeypatch.setenv("NPM_REGISTRY_URL", "https://registry.npmjs.org")
    monkeypatch.setenv("UNPKG_URL", "https://unpkg.com")
    monkeypatch.setenv("CACHE_TTL_DAYS", "7")
    monkeypatch.setenv("MAX_CONCURRENT_REQUESTS", "40")
    monkeypatch.setenv("REQUEST_TIMEOUT", "30")
    return monkeypatch


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Provide temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def temp_download_dir(tmp_path):
    """Provide temporary download directory."""
    download_dir = tmp_path / "downloads"
    download_dir.mkdir()
    return download_dir


@pytest.fixture
def mock_response():
    """Create a mock HTTP response."""
    def _make_response(json_data: Dict[str, Any] = None, status_code: int = 200, text: str = ""):
        response = Mock()
        response.status_code = status_code
        response.json.return_value = json_data or {}
        response.text = text
        response.raise_for_status = Mock()
        if status_code >= 400:
            from requests.exceptions import HTTPError
            response.raise_for_status.side_effect = HTTPError(f"HTTP {status_code}")
        return response
    return _make_response


@pytest.fixture
def mock_session(mock_response):
    """Create a mock requests session."""
    session = Mock()
    session.get.return_value = mock_response({"test": "data"})
    session.post.return_value = mock_response({"test": "data"})
    session.headers = {}
    return session


@pytest.fixture
def sample_package_data():
    """Sample NPM package data for testing."""
    return {
        "name": "lodash",
        "version": "4.17.21",
        "description": "Lodash modular utilities.",
        "keywords": ["modules", "stdlib", "util"],
        "homepage": "https://lodash.com/",
        "repository": {
            "type": "git",
            "url": "git+https://github.com/lodash/lodash.git"
        },
        "license": "MIT",
        "author": "John-David Dalton",
        "maintainers": [
            {"name": "jdalton", "email": "john.david.dalton@gmail.com"}
        ],
        "dist": {
            "tarball": "https://registry.npmjs.org/lodash/-/lodash-4.17.21.tgz"
        }
    }


@pytest.fixture
def sample_libraries_io_response():
    """Sample Libraries.io API response."""
    return {
        "total_count": 1000,
        "items": [
            {
                "name": "lodash",
                "platform": "NPM",
                "description": "Lodash modular utilities.",
                "homepage": "https://lodash.com/",
                "repository_url": "https://github.com/lodash/lodash",
                "normalized_licenses": ["MIT"],
                "rank": 1,
                "latest_release_number": "4.17.21",
                "latest_stable_release_number": "4.17.21",
                "dependents_count": 150000,
                "dependent_repos_count": 2000000,
                "stars": 55000,
            }
        ]
    }


@pytest.fixture(autouse=True)
def reset_config():
    """Reset global config after each test."""
    yield
    from npm_discovery.config import reset_config
    reset_config()

