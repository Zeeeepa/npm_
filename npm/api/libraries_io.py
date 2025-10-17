"""Libraries.io API client for package discovery."""
import logging
from typing import List, Optional, Dict, Any
from npm.config import get_config
from npm.utils.http import get_json, HttpError, RateLimitError
from npm.models import SearchResult

logger = logging.getLogger(__name__)


class LibrariesIOClient:
    """Client for Libraries.io API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize client.
        
        Args:
            api_key: Libraries.io API key (uses config if None).
        """
        if api_key is None:
            config = get_config(validate=True)
            api_key = config.libraries_io_api_key
        
        self.api_key = api_key
        self.base_url = "https://libraries.io/api"
    
    def search(
        self,
        query: str,
        page: int = 1,
        per_page: int = 100,
        platforms: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """Search for packages.
        
        Args:
            query: Search query string.
            page: Page number (1-indexed).
            per_page: Results per page (max 100).
            platforms: Filter by platforms (defaults to ["NPM"]).
            
        Returns:
            List of SearchResult objects.
            
        Raises:
            HttpError: If request fails.
            RateLimitError: If rate limit exceeded.
        """
        if platforms is None:
            platforms = ["NPM"]
        
        url = f"{self.base_url}/search"
        params = {
            "q": query,
            "page": page,
            "per_page": min(per_page, 100),
            "platforms": ",".join(platforms),
            "api_key": self.api_key,
        }
        
        try:
            data = get_json(url, params=params)
            results = []
            
            for item in data:
                result = SearchResult(
                    name=item.get("name", ""),
                    description=item.get("description", ""),
                    version=item.get("latest_stable_release_number", ""),
                    repository_url=item.get("repository_url", ""),
                    homepage=item.get("homepage", ""),
                    stars=item.get("stars", 0),
                    rank=item.get("rank", 0),
                    dependents_count=item.get("dependents_count", 0),
                    platform=item.get("platform", "NPM"),
                )
                results.append(result)
            
            logger.info(f"Found {len(results)} packages for query: {query}")
            return results
        
        except RateLimitError:
            logger.warning("Libraries.io rate limit exceeded")
            raise
        except HttpError as e:
            logger.error(f"Libraries.io API error: {e}")
            raise
    
    def get_package(self, platform: str, name: str) -> Dict[str, Any]:
        """Get detailed package information.
        
        Args:
            platform: Platform name (e.g., "NPM").
            name: Package name.
            
        Returns:
            Package data dictionary.
            
        Raises:
            HttpError: If request fails.
        """
        url = f"{self.base_url}/{platform}/{name}"
        params = {"api_key": self.api_key}
        
        try:
            data = get_json(url, params=params)
            logger.debug(f"Retrieved package info for {name}")
            return data
        except HttpError as e:
            logger.error(f"Error fetching package {name}: {e}")
            raise
    
    def get_dependencies(self, platform: str, name: str, version: str) -> List[Dict[str, Any]]:
        """Get package dependencies.
        
        Args:
            platform: Platform name (e.g., "NPM").
            name: Package name.
            version: Package version.
            
        Returns:
            List of dependency dictionaries.
            
        Raises:
            HttpError: If request fails.
        """
        url = f"{self.base_url}/{platform}/{name}/{version}/dependencies"
        params = {"api_key": self.api_key}
        
        try:
            data = get_json(url, params=params)
            dependencies = data.get("dependencies", [])
            logger.debug(f"Found {len(dependencies)} dependencies for {name}@{version}")
            return dependencies
        except HttpError as e:
            logger.error(f"Error fetching dependencies for {name}@{version}: {e}")
            raise

