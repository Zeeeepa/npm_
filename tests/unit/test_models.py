"""Unit tests for data models."""
import pytest
import json
from npm_discovery.models import PackageInfo, SearchResult


class TestPackageInfo:
    """Test PackageInfo model."""
    
    def test_creates_with_minimal_data(self):
        """Test creating PackageInfo with just name."""
        package = PackageInfo(name="lodash")
        
        assert package.name == "lodash"
        assert package.version == ""
        assert package.cache_key != ""
        assert package.last_fetched > 0
    
    def test_generates_cache_key(self):
        """Test cache key generation."""
        package1 = PackageInfo(name="lodash", version="4.17.21")
        package2 = PackageInfo(name="lodash", version="4.17.21")
        package3 = PackageInfo(name="lodash", version="4.17.20")
        
        assert package1.cache_key == package2.cache_key
        assert package1.cache_key != package3.cache_key
    
    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        original = PackageInfo(
            name="test-package",
            version="1.0.0",
            description="Test package",
            keywords=["test", "package"],
            maintainers=["Alice", "Bob"],
            dependencies=["dep1", "dep2"],
        )
        
        # Convert to dict
        data = original.to_dict()
        assert isinstance(data['keywords'], str)  # JSON string
        
        # Convert back
        restored = PackageInfo.from_dict(data)
        assert restored.name == original.name
        assert restored.keywords == original.keywords
        assert restored.maintainers == original.maintainers
    
    def test_cache_validity(self):
        """Test cache validity checking."""
        package = PackageInfo(name="test")
        
        # Just created, should be valid
        assert package.is_cache_valid(ttl_days=7)
        
        # Simulate old cache
        package.last_fetched = package.last_fetched - (8 * 24 * 60 * 60)
        assert not package.is_cache_valid(ttl_days=7)


class TestSearchResult:
    """Test SearchResult model."""
    
    def test_creates_search_result(self):
        """Test creating SearchResult."""
        result = SearchResult(
            name="lodash",
            description="Utility library",
            version="4.17.21",
            stars=50000,
        )
        
        assert result.name == "lodash"
        assert result.stars == 50000
        assert result.platform == "NPM"
    
    def test_converts_to_package_info(self):
        """Test converting SearchResult to PackageInfo."""
        result = SearchResult(
            name="lodash",
            description="Utility library",
            version="4.17.21",
            stars=50000,
            dependents_count=150000,
        )
        
        package = result.to_package_info()
        assert package.name == "lodash"
        assert package.description == "Utility library"
        assert package.github_stars == "50000"

