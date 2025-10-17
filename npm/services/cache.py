"""Cache manager using SQLite for persistent storage."""
import sqlite3
import json
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any
from npm.config import get_config
from npm.models import PackageInfo

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages package information cache using SQLite."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize cache manager.
        
        Args:
            db_path: Path to SQLite database (uses config default if None).
        """
        if db_path is None:
            config = get_config()
            db_path = config.cache_dir / "npm_cache.db"
        
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS package_cache (
                    cache_key TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    version TEXT,
                    data TEXT NOT NULL,
                    last_fetched REAL NOT NULL,
                    created_at REAL NOT NULL DEFAULT (julianday('now'))
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_name ON package_cache(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_last_fetched ON package_cache(last_fetched)")
            conn.commit()
    
    def get(self, cache_key: str) -> Optional[PackageInfo]:
        """Retrieve package info from cache.
        
        Args:
            cache_key: Cache key for the package.
            
        Returns:
            PackageInfo if found and valid, None otherwise.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT data FROM package_cache WHERE cache_key = ?",
                    (cache_key,)
                )
                row = cursor.fetchone()
                
                if row:
                    data = json.loads(row['data'])
                    package = PackageInfo.from_dict(data)
                    
                    config = get_config()
                    if package.is_cache_valid(config.cache_ttl_days):
                        logger.debug(f"Cache hit for {cache_key}")
                        return package
                    else:
                        logger.debug(f"Cache expired for {cache_key}")
                        self.delete(cache_key)
                
                return None
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            return None
    
    def set(self, package: PackageInfo) -> bool:
        """Store package info in cache.
        
        Args:
            package: PackageInfo to cache.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            data = json.dumps(package.to_dict())
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO package_cache 
                    (cache_key, name, version, data, last_fetched)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    package.cache_key,
                    package.name,
                    package.version,
                    data,
                    package.last_fetched
                ))
                conn.commit()
            
            logger.debug(f"Cached package {package.name}@{package.version}")
            return True
        except Exception as e:
            logger.error(f"Error storing in cache: {e}")
            return False
    
    def delete(self, cache_key: str) -> bool:
        """Delete package from cache.
        
        Args:
            cache_key: Cache key to delete.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM package_cache WHERE cache_key = ?", (cache_key,))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False
    
    def clear_expired(self, ttl_days: Optional[int] = None) -> int:
        """Clear expired cache entries.
        
        Args:
            ttl_days: Time-to-live in days (uses config default if None).
            
        Returns:
            Number of entries deleted.
        """
        if ttl_days is None:
            config = get_config()
            ttl_days = config.cache_ttl_days
        
        import time
        cutoff_time = time.time() - (ttl_days * 24 * 60 * 60)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM package_cache WHERE last_fetched < ?",
                    (cutoff_time,)
                )
                deleted = cursor.rowcount
                conn.commit()
            
            logger.info(f"Cleared {deleted} expired cache entries")
            return deleted
        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")
            return 0
    
    def clear_all(self) -> bool:
        """Clear all cache entries.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM package_cache")
                conn.commit()
            logger.info("Cleared all cache entries")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) as count FROM package_cache")
                count = cursor.fetchone()[0]
                
                cursor = conn.execute("""
                    SELECT COUNT(*) as expired FROM package_cache 
                    WHERE last_fetched < ?
                """, (time.time() - (get_config().cache_ttl_days * 24 * 60 * 60),))
                expired = cursor.fetchone()[0]
            
            return {
                "total_entries": count,
                "expired_entries": expired,
                "valid_entries": count - expired,
                "db_path": str(self.db_path),
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}
