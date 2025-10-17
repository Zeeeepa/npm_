"""Integration tests for discovery service."""
import pytest
from unittest.mock import Mock, patch
from npm_discovery.services.discovery import DiscoveryService
from npm_discovery.models import PackageInfo, SearchResult


class TestDiscoveryService:
    """Test DiscoveryService integration."""
    
    @patch('npm_discovery.services.discovery.LibrariesIOClient')
    @patch('npm_discovery.services.discovery.NpmRegistryClient')
    @patch('npm_discovery.services.discovery.UnpkgClient')
    @patch('npm_discovery.services.discovery.CacheManager')
    def test_search_packages(self, mock_cache, mock_unpkg, mock_npm, mock_libio):
        """Test searching for packages."""
        # Setup mock
        mock_client = Mock()
        mock_client.search.return_value = [
            SearchResult(name="lodash", description="Utility library", version="4.17.21"),
            SearchResult(name="axios", description="HTTP client", version="1.4.0"),
        ]
        mock_libio.return_value = mock_client
        
        # Create service
        service = DiscoveryService()
        
        # Search
        results = service.search_packages("http client")
        
        assert len(results) == 2
        assert results[0].name == "lodash"
        mock_client.search.assert_called_once()
    
    @patch('npm_discovery.services.discovery.LibrariesIOClient')
    @patch('npm_discovery.services.discovery.NpmRegistryClient')
    @patch('npm_discovery.services.discovery.UnpkgClient')
    @patch('npm_discovery.services.discovery.CacheManager')
    def test_get_package_details_without_cache(self, mock_cache_cls, mock_unpkg, mock_npm_cls, mock_libio):
        """Test fetching package details without cache."""
        # Setup mocks
        mock_npm = Mock()
        mock_npm.get_package.return_value = PackageInfo(
            name="lodash",
            version="4.17.21",
            description="Utility library"
        )
        mock_npm_cls.return_value = mock_npm
        
        mock_cache = Mock()
        mock_cache.get.return_value = None  # Not in cache
        mock_cache_cls.return_value = mock_cache
        
        # Create service
        service = DiscoveryService()
        
        # Get details
        package = service.get_package_details("lodash")
        
        assert package is not None
        assert package.name == "lodash"
        mock_npm.get_package.assert_called_once_with("lodash")
        mock_cache.set.assert_called_once()
    
    @patch('npm_discovery.services.discovery.LibrariesIOClient')
    @patch('npm_discovery.services.discovery.NpmRegistryClient')
    @patch('npm_discovery.services.discovery.UnpkgClient')
    @patch('npm_discovery.services.discovery.CacheManager')
    def test_get_package_details_from_cache(self, mock_cache_cls, mock_unpkg, mock_npm, mock_libio):
        """Test fetching package details from cache."""
        # Setup mock
        cached_package = PackageInfo(
            name="lodash",
            version="4.17.21",
            description="Cached package"
        )
        
        mock_cache = Mock()
        mock_cache.get.return_value = cached_package
        mock_cache_cls.return_value = mock_cache
        
        # Create service
        service = DiscoveryService()
        
        # Get details
        package = service.get_package_details("lodash", use_cache=True)
        
        assert package is not None
        assert package.description == "Cached package"
        mock_cache.get.assert_called_once()
