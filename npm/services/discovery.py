"""Package discovery service orchestrating all components."""
import logging
from typing import List, Optional
from npm.api import LibrariesIOClient, NpmRegistryClient, UnpkgClient
from npm.services.cache import CacheManager
from npm.models import PackageInfo, SearchResult

logger = logging.getLogger(__name__)


class DiscoveryService:
    """Orchestrates package discovery across multiple APIs."""
    
    def __init__(
        self,
        libraries_io: Optional[LibrariesIOClient] = None,
        npm_registry: Optional[NpmRegistryClient] = None,
        unpkg: Optional[UnpkgClient] = None,
        cache: Optional[CacheManager] = None,
    ):
        """Initialize discovery service.
        
        Args:
            libraries_io: Libraries.io client (creates default if None).
            npm_registry: NPM registry client (creates default if None).
            unpkg: Unpkg client (creates default if None).
            cache: Cache manager (creates default if None).
        """
        self.libraries_io = libraries_io or LibrariesIOClient()
        self.npm_registry = npm_registry or NpmRegistryClient()
        self.unpkg = unpkg or UnpkgClient()
        self.cache = cache or CacheManager()
    
    def search_packages(
        self,
        query: str,
        page: int = 1,
        per_page: int = 100,
        use_cache: bool = True,
    ) -> List[SearchResult]:
        """Search for packages.
        
        Args:
            query: Search query string.
            page: Page number (1-indexed).
            per_page: Results per page.
            use_cache: Whether to use cached results.
            
        Returns:
            List of SearchResult objects.
        """
        logger.info(f"Searching for packages: {query}")
        
        try:
            results = self.libraries_io.search(
                query=query,
                page=page,
                per_page=per_page,
            )
            logger.info(f"Found {len(results)} packages")
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_package_details(
        self,
        name: str,
        use_cache: bool = True,
        fetch_file_tree: bool = False,
    ) -> Optional[PackageInfo]:
        """Get detailed package information.
        
        Args:
            name: Package name.
            use_cache: Whether to use cached data.
            fetch_file_tree: Whether to fetch file tree from unpkg.
            
        Returns:
            PackageInfo object or None if not found.
        """
        logger.info(f"Fetching details for package: {name}")
        
        # Try cache first
        if use_cache:
            # Generate cache key for lookup
            temp_package = PackageInfo(name=name)
            cached = self.cache.get(temp_package.cache_key)
            if cached:
                logger.info(f"Using cached data for {name}")
                return cached
        
        # Fetch from NPM registry
        try:
            package = self.npm_registry.get_package(name)
            
            # Optionally fetch file tree
            if fetch_file_tree:
                try:
                    file_tree = self.unpkg.get_file_tree(name, package.version)
                    package.file_tree = file_tree
                    logger.info(f"Added file tree to {name}")
                except Exception as e:
                    logger.warning(f"Could not fetch file tree: {e}")
            
            # Cache the result
            if use_cache:
                self.cache.set(package)
            
            return package
        
        except Exception as e:
            logger.error(f"Failed to fetch package details: {e}")
            return None
    
    def get_file_tree(
        self,
        name: str,
        version: Optional[str] = None,
    ) -> dict:
        """Get file tree for a package.
        
        Args:
            name: Package name.
            version: Package version (uses latest if None).
            
        Returns:
            File tree dictionary.
        """
        try:
            tree = self.unpkg.get_file_tree(name, version)
            return tree
        except Exception as e:
            logger.error(f"Failed to fetch file tree: {e}")
            return {}
    
    def get_readme(
        self,
        name: str,
        version: Optional[str] = None,
    ) -> str:
        """Get README content for a package.
        
        Args:
            name: Package name.
            version: Package version (uses latest if None).
            
        Returns:
            README content as markdown string.
        """
        try:
            readme = self.unpkg.get_readme(name, version)
            return readme
        except Exception as e:
            logger.error(f"Failed to fetch README: {e}")
            return ""
    
    def clear_cache(self) -> bool:
        """Clear all cached data.
        
        Returns:
            True if successful.
        """
        return self.cache.clear_all()
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats.
        """
        return self.cache.get_stats()

