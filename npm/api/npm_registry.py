"""NPM Registry API client for package enrichment."""
import logging
from typing import Dict, Any, Optional
from npm.config import get_config
from npm.utils.http import get_json, HttpError
from npm.models import PackageInfo

logger = logging.getLogger(__name__)


class NpmRegistryClient:
    """Client for NPM Registry API."""
    
    def __init__(self, registry_url: Optional[str] = None):
        """Initialize client.
        
        Args:
            registry_url: NPM registry URL (uses config if None).
        """
        if registry_url is None:
            config = get_config()
            registry_url = config.npm_registry_url
        
        self.registry_url = registry_url.rstrip("/")
    
    def get_package(self, name: str) -> PackageInfo:
        """Get complete package information.
        
        Args:
            name: Package name.
            
        Returns:
            PackageInfo object with enriched data.
            
        Raises:
            HttpError: If request fails.
        """
        url = f"{self.registry_url}/{name}"
        
        try:
            data = get_json(url)
            return self._parse_package_data(data)
        except HttpError as e:
            logger.error(f"Error fetching package {name} from npm: {e}")
            raise
    
    def get_downloads(self, name: str, period: str = "last-month") -> Dict[str, Any]:
        """Get download statistics.
        
        Args:
            name: Package name.
            period: Time period ("last-day", "last-week", "last-month").
            
        Returns:
            Download statistics dictionary.
        """
        url = f"https://api.npmjs.org/downloads/point/{period}/{name}"
        
        try:
            data = get_json(url)
            return data
        except HttpError as e:
            logger.warning(f"Could not fetch download stats for {name}: {e}")
            return {"downloads": 0}
    
    def _parse_package_data(self, data: Dict[str, Any]) -> PackageInfo:
        """Parse npm registry response into PackageInfo.
        
        Args:
            data: Raw npm registry data.
            
        Returns:
            PackageInfo object.
        """
        # Get latest version info
        dist_tags = data.get("dist-tags", {})
        latest_version = dist_tags.get("latest", "")
        versions = data.get("versions", {})
        latest_data = versions.get(latest_version, {})
        
        # Extract basic info
        name = data.get("name", "")
        description = latest_data.get("description", data.get("description", ""))
        
        # Author info
        author_data = latest_data.get("author", data.get("author", {}))
        if isinstance(author_data, dict):
            author = author_data.get("name", "")
        else:
            author = str(author_data)
        
        # Repository info
        repo_data = latest_data.get("repository", data.get("repository", {}))
        if isinstance(repo_data, dict):
            repository = repo_data.get("url", "")
        else:
            repository = str(repo_data)
        
        # Clean up repository URL
        repository = repository.replace("git+", "").replace("git://", "https://")
        if repository.endswith(".git"):
            repository = repository[:-4]
        
        # Keywords
        keywords = latest_data.get("keywords", data.get("keywords", []))
        if not isinstance(keywords, list):
            keywords = []
        
        # Dependencies
        dependencies = latest_data.get("dependencies", {})
        dev_dependencies = latest_data.get("devDependencies", {})
        peer_dependencies = latest_data.get("peerDependencies", {})
        
        # Maintainers
        maintainers = data.get("maintainers", [])
        maintainer_names = [m.get("name", "") for m in maintainers if isinstance(m, dict)]
        
        # Time info
        time_data = data.get("time", {})
        published_date = time_data.get("created", "")
        modified_date = time_data.get("modified", "")
        
        # Get download stats
        downloads_data = self.get_downloads(name)
        downloads_last_month = downloads_data.get("downloads", 0)
        
        # Create PackageInfo
        package = PackageInfo(
            name=name,
            version=latest_version,
            description=description,
            author=author,
            license=latest_data.get("license", ""),
            homepage=latest_data.get("homepage", data.get("homepage", "")),
            repository=repository,
            downloads_last_month=downloads_last_month,
            dependencies_count=len(dependencies),
            dev_dependencies_count=len(dev_dependencies),
            peer_dependencies_count=len(peer_dependencies),
            total_versions=len(versions),
            published_date=published_date,
            modified_date=modified_date,
            keywords=keywords,
            maintainers_count=len(maintainers),
            maintainers=maintainer_names,
            dependencies=list(dependencies.keys()),
        )
        
        logger.info(f"Enriched package data for {name}")
        return package

