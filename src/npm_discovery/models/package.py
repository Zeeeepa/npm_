"""Data models for NPM packages."""
import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any


@dataclass
class PackageInfo:
    """Enhanced NPM package information structure."""
    
    name: str
    version: str = ""
    description: str = ""
    author: str = ""
    license: str = ""
    homepage: str = ""
    repository: str = ""
    downloads_last_week: int = 0
    downloads_last_month: int = 0
    downloads_trend: str = "stable"
    size_unpacked: str = "Unknown"
    file_count: str = "Unknown"
    dependencies_count: int = 0
    dev_dependencies_count: int = 0
    peer_dependencies_count: int = 0
    total_versions: int = 0
    published_date: str = ""
    modified_date: str = ""
    last_publish: str = ""
    keywords: List[str] = field(default_factory=list)
    has_typescript: bool = False
    has_tests: bool = False
    has_readme: bool = False
    maintainers_count: int = 0
    maintainers: List[str] = field(default_factory=list)
    github_stars: str = "N/A"
    github_forks: str = "N/A"
    github_issues: str = "N/A"
    score_quality: float = 0.0
    score_popularity: float = 0.0
    score_maintenance: float = 0.0
    score_final: float = 0.0
    dependents: List[str] = field(default_factory=list)
    dependents_count: int = 0
    dependencies: List[str] = field(default_factory=list)
    readme: str = ""
    dependency_details: Dict[str, Dict] = field(default_factory=dict)
    dependent_details: Dict[str, Dict] = field(default_factory=dict)
    last_fetched: float = 0.0
    cache_key: str = ""
    file_tree: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Initialize and validate fields."""
        self.last_fetched = time.time()
        if not self.cache_key:
            self.cache_key = self._generate_cache_key()

    def _generate_cache_key(self) -> str:
        """Generate a cache key based on package name and version."""
        key_data = f"{self.name}:{self.version}".encode('utf-8')
        return hashlib.md5(key_data).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for caching."""
        d = asdict(self)
        # Convert lists to JSON strings for storage
        d['keywords'] = json.dumps(self.keywords)
        d['maintainers'] = json.dumps(self.maintainers)
        d['dependents'] = json.dumps(self.dependents)
        d['dependencies'] = json.dumps(self.dependencies)
        d['dependency_details'] = json.dumps(self.dependency_details)
        d['dependent_details'] = json.dumps(self.dependent_details)
        d['file_tree'] = json.dumps(self.file_tree)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PackageInfo":
        """Create PackageInfo from dictionary."""
        # Parse JSON strings back to lists/dicts
        if isinstance(data.get('keywords'), str):
            data['keywords'] = json.loads(data['keywords'])
        if isinstance(data.get('maintainers'), str):
            data['maintainers'] = json.loads(data['maintainers'])
        if isinstance(data.get('dependents'), str):
            data['dependents'] = json.loads(data['dependents'])
        if isinstance(data.get('dependencies'), str):
            data['dependencies'] = json.loads(data['dependencies'])
        if isinstance(data.get('dependency_details'), str):
            data['dependency_details'] = json.loads(data['dependency_details'])
        if isinstance(data.get('dependent_details'), str):
            data['dependent_details'] = json.loads(data['dependent_details'])
        if isinstance(data.get('file_tree'), str):
            data['file_tree'] = json.loads(data['file_tree'])
        
        return cls(**data)

    def is_cache_valid(self, ttl_days: int = 7) -> bool:
        """Check if cached data is still valid."""
        if not self.last_fetched:
            return False
        age_seconds = time.time() - self.last_fetched
        return age_seconds < (ttl_days * 24 * 60 * 60)


@dataclass
class SearchResult:
    """Search result from Libraries.io or npm registry."""
    
    name: str
    description: str = ""
    version: str = ""
    repository_url: str = ""
    homepage: str = ""
    stars: int = 0
    rank: int = 0
    dependents_count: int = 0
    platform: str = "NPM"
    
    def to_package_info(self) -> PackageInfo:
        """Convert to PackageInfo for further enrichment."""
        return PackageInfo(
            name=self.name,
            version=self.version,
            description=self.description,
            homepage=self.homepage,
            repository=self.repository_url,
            github_stars=str(self.stars),
            dependents_count=self.dependents_count,
        )

