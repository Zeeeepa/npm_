"""Unit tests for API clients."""
import pytest
from unittest.mock import Mock, patch
from npm_discovery.api import LibrariesIOClient, NpmRegistryClient, UnpkgClient
from npm_discovery.utils.http import HttpError, RateLimitError


class TestLibrariesIOClient:
    """Test LibrariesIOClient."""
    
    @patch('npm_discovery.api.libraries_io.get_json')
    def test_search_success(self, mock_get_json):
        """Test successful search."""
        mock_get_json.return_value = [
            {
                "name": "lodash",
                "description": "Utility library",
                "latest_stable_release_number": "4.17.21",
                "stars": 50000,
                "repository_url": "https://github.com/lodash/lodash",
            }
        ]
        
        client = LibrariesIOClient(api_key="test_key")
        results = client.search("lodash")
        
        assert len(results) == 1
        assert results[0].name == "lodash"
        assert results[0].stars == 50000
    
    @patch('npm_discovery.api.libraries_io.get_json')
    def test_search_rate_limit(self, mock_get_json):
        """Test rate limit handling."""
        mock_get_json.side_effect = RateLimitError("Rate limit exceeded")
        
        client = LibrariesIOClient(api_key="test_key")
        with pytest.raises(RateLimitError):
            client.search("lodash")


class TestNpmRegistryClient:
    """Test NpmRegistryClient."""
    
    @patch('npm_discovery.api.npm_registry.get_json')
    def test_get_package(self, mock_get_json):
        """Test package retrieval."""
        mock_get_json.side_effect = [
            {
                "name": "lodash",
                "description": "Utility library",
                "dist-tags": {"latest": "4.17.21"},
                "versions": {
                    "4.17.21": {
                        "description": "Utility library",
                        "license": "MIT",
                        "author": {"name": "John Doe"},
                        "repository": {"url": "git+https://github.com/lodash/lodash.git"},
                        "dependencies": {"foo": "1.0.0"},
                    }
                },
                "time": {
                    "created": "2010-01-01",
                    "modified": "2024-01-01",
                },
                "maintainers": [{"name": "John"}],
            },
            {"downloads": 10000000},  # downloads API
        ]
        
        client = NpmRegistryClient()
        package = client.get_package("lodash")
        
        assert package.name == "lodash"
        assert package.version == "4.17.21"
        assert package.license == "MIT"
        assert package.downloads_last_month == 10000000


class TestUnpkgClient:
    """Test UnpkgClient."""
    
    @patch('npm_discovery.api.unpkg.get_json')
    def test_get_file_tree(self, mock_get_json):
        """Test file tree retrieval."""
        mock_get_json.return_value = {
            "name": "lodash",
            "version": "4.17.21",
            "files": [
                {"path": "/index.js", "type": "file", "size": 1000},
                {"path": "/package.json", "type": "file", "size": 500},
            ]
        }
        
        client = UnpkgClient()
        tree = client.get_file_tree("lodash")
        
        assert tree["name"] == "lodash"
        assert tree["file_count"] == 2
    
    @patch('npm_discovery.api.unpkg.get_text')
    def test_get_file_content(self, mock_get_text):
        """Test file content retrieval."""
        mock_get_text.return_value = "console.log('hello');"
        
        client = UnpkgClient()
        content = client.get_file_content("lodash", "index.js")
        
        assert "hello" in content
