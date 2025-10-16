"""Unit tests for cache manager."""
import pytest
import time
from pathlib import Path
from npm_discovery.services.cache import CacheManager
from npm_discovery.models import PackageInfo


class TestCacheManager:
    """Test CacheManager functionality."""
    
    def test_creates_database(self, tmp_path):
        """Test database creation."""
        db_path = tmp_path / "test_cache.db"
        cache = CacheManager(db_path)
        
        assert db_path.exists()
    
    def test_stores_and_retrieves_package(self, tmp_path):
        """Test storing and retrieving package."""
        cache = CacheManager(tmp_path / "test.db")
        
        package = PackageInfo(
            name="lodash",
            version="4.17.21",
            description="Utility library"
        )
        
        # Store
        assert cache.set(package)
        
        # Retrieve
        retrieved = cache.get(package.cache_key)
        assert retrieved is not None
        assert retrieved.name == "lodash"
        assert retrieved.version == "4.17.21"
    
    def test_returns_none_for_missing_package(self, tmp_path):
        """Test retrieving non-existent package."""
        cache = CacheManager(tmp_path / "test.db")
        
        result = cache.get("nonexistent-key")
        assert result is None
    
    def test_deletes_package(self, tmp_path):
        """Test deleting package from cache."""
        cache = CacheManager(tmp_path / "test.db")
        
        package = PackageInfo(name="test")
        cache.set(package)
        
        # Delete
        assert cache.delete(package.cache_key)
        
        # Should not exist anymore
        assert cache.get(package.cache_key) is None
    
    def test_clears_expired_entries(self, tmp_path):
        """Test clearing expired cache entries."""
        cache = CacheManager(tmp_path / "test.db")
        
        # Create old package
        old_package = PackageInfo(name="old")
        old_package.last_fetched = time.time() - (10 * 24 * 60 * 60)  # 10 days old
        cache.set(old_package)
        
        # Create fresh package
        new_package = PackageInfo(name="new")
        cache.set(new_package)
        
        # Clear expired (TTL 7 days)
        deleted = cache.clear_expired(ttl_days=7)
        assert deleted >= 1
        
        # Old should be gone, new should remain
        assert cache.get(old_package.cache_key) is None
        assert cache.get(new_package.cache_key) is not None
    
    def test_clears_all_entries(self, tmp_path):
        """Test clearing all cache entries."""
        cache = CacheManager(tmp_path / "test.db")
        
        # Add multiple packages
        for i in range(5):
            package = PackageInfo(name=f"package{i}")
            cache.set(package)
        
        # Clear all
        assert cache.clear_all()
        
        # Check stats
        stats = cache.get_stats()
        assert stats["total_entries"] == 0
    
    def test_get_stats(self, tmp_path):
        """Test getting cache statistics."""
        cache = CacheManager(tmp_path / "test.db")
        
        # Add some packages
        for i in range(3):
            package = PackageInfo(name=f"pkg{i}")
            cache.set(package)
        
        stats = cache.get_stats()
        assert stats["total_entries"] == 3
        assert "db_path" in stats

