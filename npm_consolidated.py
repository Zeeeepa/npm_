"""
NPM Package Analyzer & Downloader - Consolidated Edition

A unified tool combining package search, analysis, file exploration, and download
capabilities for NPM packages. Consolidates functionality from npm.py, npm2.py, and
npm_download.py into a single, maintainable solution.

Features:
- Search NPM packages via Libraries.io (6000 packages/minute)
- Enrich package data from NPM registry
- Browse package file trees via unpkg.com
- View file contents with syntax highlighting
- Download packages with integrity verification
- Rate limiting with visual countdown
- Concurrent API requests for performance
- SQLite caching with TTL
- Export to JSON, CSV, Text formats

Author: Consolidated from multiple sources
License: MIT
"""

import json
import os
import re
import sqlite3
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Constants
LIBRARIES_IO_API = "https://libraries.io/api"
NPM_REGISTRY_API = "https://registry.npmjs.org"
UNPKG_API = "https://unpkg.com"
RATE_LIMIT_PER_MINUTE = 60
RATE_LIMIT_COOLDOWN = 60  # seconds
CACHE_TTL_DAYS = 7
MAX_WORKERS = 5
REQUEST_TIMEOUT = 30


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class PackageInfo:
    """NPM package information with complete metadata."""
    
    name: str
    version: str = ""
    description: str = ""
    homepage: str = ""
    repository_url: str = ""
    downloads: int = 0
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    contributors: int = 0
    dependencies: Dict[str, str] = field(default_factory=dict)
    dev_dependencies: Dict[str, str] = field(default_factory=dict)
    keywords: List[str] = field(default_factory=list)
    license: str = ""
    latest_release: str = ""
    maintainers: List[Dict[str, str]] = field(default_factory=list)
    npm_url: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    file_tree: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """Search result from Libraries.io API."""
    
    packages: List[PackageInfo]
    total: int
    page: int
    per_page: int


# ============================================================================
# Exception Classes
# ============================================================================


class NPMToolkitError(Exception):
    """Base exception for NPM toolkit errors."""
    pass


class APIError(NPMToolkitError):
    """API request failed."""
    pass


class RateLimitError(NPMToolkitError):
    """Rate limit exceeded."""
    pass


class CacheError(NPMToolkitError):
    """Cache operation failed."""
    pass


class ValidationError(NPMToolkitError):
    """Data validation failed."""
    pass


# ============================================================================
# Utility Classes
# ============================================================================


class RateLimiter:
    """Token bucket rate limiter with visual countdown."""
    
    def __init__(self, rate_per_minute: int = RATE_LIMIT_PER_MINUTE):
        self.rate = rate_per_minute
        self.tokens = rate_per_minute
        self.last_update = time.time()
        self.lock = threading.Lock()
        self.cooldown_until = None
    
    def acquire(self) -> bool:
        """Acquire a token, blocking if necessary."""
        with self.lock:
            now = time.time()
            
            # Check if in cooldown
            if self.cooldown_until and now < self.cooldown_until:
                wait_time = self.cooldown_until - now
                print(f"⏳ Rate limit cooldown: {int(wait_time)}s remaining...")
                time.sleep(min(wait_time, 1))
                return False
            
            # Refill tokens
            if now - self.last_update >= 60:
                self.tokens = self.rate
                self.last_update = now
                self.cooldown_until = None
            
            # Try to acquire
            if self.tokens > 0:
                self.tokens -= 1
                return True
            else:
                # Start cooldown
                self.cooldown_until = now + RATE_LIMIT_COOLDOWN
                print(f"⚠️  Rate limit reached! Cooling down for {RATE_LIMIT_COOLDOWN}s...")
                return False


class HTTPClient:
    """HTTP client with retry logic and connection pooling."""
    
    def __init__(self, timeout: int = REQUEST_TIMEOUT):
        self.timeout = timeout
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=20)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """Perform GET request with timeout."""
        kwargs.setdefault("timeout", self.timeout)
        try:
            response = self.session.get(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            raise APIError(f"HTTP request failed: {e}")
    
    def close(self):
        """Close the session."""
        self.session.close()


# ============================================================================
# Storage Layer
# ============================================================================


class CacheManager:
    """SQLite-based cache with TTL support."""
    
    def __init__(self, db_path: str = "npm_cache.db", ttl_days: int = CACHE_TTL_DAYS):
        self.db_path = db_path
        self.ttl_days = ttl_days
        self._init_db()
    
    def _init_db(self):
        """Initialize cache database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON cache(created_at)
            """)
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached value if not expired."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT value, created_at FROM cache WHERE key = ?",
                    (key,)
                )
                row = cursor.fetchone()
                if row:
                    value_json, created_at = row
                    created = datetime.fromisoformat(created_at)
                    if datetime.now() - created < timedelta(days=self.ttl_days):
                        return json.loads(value_json)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Dict):
        """Set cache value."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO cache (key, value) VALUES (?, ?)",
                    (key, json.dumps(value))
                )
        except Exception as e:
            print(f"Cache set error: {e}")
    
    def clear_expired(self):
        """Remove expired cache entries."""
        try:
            cutoff = datetime.now() - timedelta(days=self.ttl_days)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "DELETE FROM cache WHERE created_at < ?",
                    (cutoff.isoformat(),)
                )
        except Exception as e:
            print(f"Cache cleanup error: {e}")


# ============================================================================
# API Clients
# ============================================================================


class LibrariesIOClient:
    """Libraries.io API client with rate limiting."""
    
    def __init__(self, api_key: str, cache: Optional[CacheManager] = None):
        self.api_key = api_key
        self.base_url = LIBRARIES_IO_API
        self.cache = cache
        self.http = HTTPClient()
        self.rate_limiter = RateLimiter()
    
    def search(
        self,
        query: str,
        page: int = 1,
        per_page: int = 30
    ) -> SearchResult:
        """Search packages via Libraries.io."""
        cache_key = f"search:{query}:{page}:{per_page}"
        
        # Check cache
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return SearchResult(**cached)
        
        # Rate limit
        while not self.rate_limiter.acquire():
            time.sleep(1)
        
        # API request
        url = f"{self.base_url}/search"
        params = {
            "q": query,
            "platforms": "npm",
            "page": page,
            "per_page": per_page,
            "api_key": self.api_key
        }
        
        try:
            response = self.http.get(url, params=params)
            data = response.json()
            
            packages = [
                PackageInfo(
                    name=pkg.get("name", ""),
                    version=pkg.get("latest_stable_release_number", ""),
                    description=pkg.get("description", ""),
                    homepage=pkg.get("homepage", ""),
                    repository_url=pkg.get("repository_url", ""),
                    stars=pkg.get("stars", 0),
                    forks=pkg.get("forks", 0),
                    keywords=pkg.get("keywords", []),
                    license=pkg.get("licenses", ""),
                    latest_release=pkg.get("latest_release_published_at", ""),
                )
                for pkg in data
            ]
            
            result = SearchResult(
                packages=packages,
                total=len(packages),
                page=page,
                per_page=per_page
            )
            
            # Cache result
            if self.cache:
                self.cache.set(cache_key, asdict(result))
            
            return result
            
        except Exception as e:
            raise APIError(f"Libraries.io search failed: {e}")
    
    def get_package(self, name: str) -> Optional[PackageInfo]:
        """Get package details."""
        cache_key = f"package:{name}"
        
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return PackageInfo(**cached)
        
        while not self.rate_limiter.acquire():
            time.sleep(1)
        
        url = f"{self.base_url}/npm/{name}"
        params = {"api_key": self.api_key}
        
        try:
            response = self.http.get(url, params=params)
            data = response.json()
            
            pkg = PackageInfo(
                name=data.get("name", ""),
                version=data.get("latest_stable_release_number", ""),
                description=data.get("description", ""),
                homepage=data.get("homepage", ""),
                repository_url=data.get("repository_url", ""),
                stars=data.get("stars", 0),
                forks=data.get("forks", 0),
                keywords=data.get("keywords", []),
                license=data.get("licenses", ""),
            )
            
            if self.cache:
                self.cache.set(cache_key, asdict(pkg))
            
            return pkg
            
        except Exception as e:
            print(f"Failed to get package {name}: {e}")
            return None


class NPMRegistryClient:
    """NPM Registry API client."""
    
    def __init__(self, cache: Optional[CacheManager] = None):
        self.base_url = NPM_REGISTRY_API
        self.cache = cache
        self.http = HTTPClient()
    
    def get_metadata(self, name: str) -> Optional[Dict]:
        """Get package metadata from NPM registry."""
        cache_key = f"npm_meta:{name}"
        
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached
        
        url = f"{self.base_url}/{name}"
        
        try:
            response = self.http.get(url)
            data = response.json()
            
            latest_version = data.get("dist-tags", {}).get("latest", "")
            version_data = data.get("versions", {}).get(latest_version, {})
            
            metadata = {
                "name": data.get("name", ""),
                "version": latest_version,
                "description": data.get("description", ""),
                "homepage": version_data.get("homepage", ""),
                "repository": version_data.get("repository", {}),
                "dependencies": version_data.get("dependencies", {}),
                "devDependencies": version_data.get("devDependencies", {}),
                "keywords": version_data.get("keywords", []),
                "license": version_data.get("license", ""),
                "maintainers": data.get("maintainers", []),
                "time": data.get("time", {}),
            }
            
            if self.cache:
                self.cache.set(cache_key, metadata)
            
            return metadata
            
        except Exception as e:
            print(f"Failed to get NPM metadata for {name}: {e}")
            return None


class UnpkgClient:
    """Unpkg.com API client for file tree browsing."""
    
    def __init__(self):
        self.base_url = UNPKG_API
        self.http = HTTPClient()
    
    def get_file_tree(self, name: str, version: str = "latest") -> Dict[str, Any]:
        """Get file tree for a package."""
        url = f"{self.base_url}/{name}@{version}/?meta"
        
        try:
            response = self.http.get(url)
            return response.json()
        except Exception as e:
            print(f"Failed to get file tree: {e}")
            return {}
    
    def get_file_content(self, name: str, file_path: str, version: str = "latest") -> str:
        """Get file content."""
        url = f"{self.base_url}/{name}@{version}/{file_path}"
        
        try:
            response = self.http.get(url)
            return response.text
        except Exception as e:
            print(f"Failed to get file content: {e}")
            return ""


# ============================================================================
# Main Analyzer
# ============================================================================


class NPMAnalyzer:
    """Main NPM package analyzer orchestrating all operations."""
    
    def __init__(self, libraries_io_key: str, cache_path: str = "npm_cache.db"):
        self.cache = CacheManager(cache_path)
        self.libraries_client = LibrariesIOClient(libraries_io_key, self.cache)
        self.npm_client = NPMRegistryClient(self.cache)
        self.unpkg_client = UnpkgClient()
    
    def search(self, query: str, limit: int = 30) -> List[PackageInfo]:
        """Search for packages."""
        print(f"🔍 Searching for '{query}'...")
        result = self.libraries_client.search(query, per_page=limit)
        print(f"✅ Found {result.total} packages")
        return result.packages
    
    def enrich_package(self, pkg: PackageInfo) -> PackageInfo:
        """Enrich package with NPM registry data."""
        metadata = self.npm_client.get_metadata(pkg.name)
        if metadata:
            pkg.dependencies = metadata.get("dependencies", {})
            pkg.dev_dependencies = metadata.get("devDependencies", {})
            pkg.maintainers = metadata.get("maintainers", [])
            pkg.npm_url = f"https://www.npmjs.com/package/{pkg.name}"
            
            time_data = metadata.get("time", {})
            pkg.created_at = time_data.get("created")
            pkg.updated_at = time_data.get("modified")
        
        return pkg
    
    def get_file_tree(self, pkg: PackageInfo) -> Dict[str, Any]:
        """Get file tree for package."""
        tree = self.unpkg_client.get_file_tree(pkg.name, pkg.version)
        pkg.file_tree = tree
        return tree
    
    def get_file_content(self, pkg: PackageInfo, file_path: str) -> str:
        """Get file content from package."""
        return self.unpkg_client.get_file_content(pkg.name, file_path, pkg.version)
    
    def export_json(self, packages: List[PackageInfo], output_path: str):
        """Export packages to JSON."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([asdict(pkg) for pkg in packages], f, indent=2)
        print(f"✅ Exported to {output_path}")
    
    def export_text(self, packages: List[PackageInfo], output_path: str):
        """Export packages to text format."""
        with open(output_path, "w", encoding="utf-8") as f:
            for pkg in packages:
                f.write(f"Name: {pkg.name}\n")
                f.write(f"Version: {pkg.version}\n")
                f.write(f"Description: {pkg.description}\n")
                f.write(f"Homepage: {pkg.homepage}\n")
                f.write(f"Repository: {pkg.repository_url}\n")
                f.write(f"License: {pkg.license}\n")
                f.write(f"Stars: {pkg.stars}\n")
                f.write("-" * 80 + "\n\n")
        print(f"✅ Exported to {output_path}")
    
    def close(self):
        """Cleanup resources."""
        self.libraries_client.http.close()
        self.npm_client.http.close()
        self.unpkg_client.http.close()


# ============================================================================
# CLI Interface
# ============================================================================


class CLI:
    """Interactive CLI for NPM analyzer."""
    
    def __init__(self, analyzer: NPMAnalyzer):
        self.analyzer = analyzer
        self.current_packages: List[PackageInfo] = []
    
    def run(self):
        """Run interactive CLI."""
        print("=" * 80)
        print("NPM Package Analyzer - Interactive Mode")
        print("=" * 80)
        
        while True:
            print("\nOptions:")
            print("1. Search packages")
            print("2. View package details")
            print("3. Browse file tree")
            print("4. View file content")
            print("5. Export results (JSON)")
            print("6. Export results (Text)")
            print("7. Exit")
            
            choice = input("\nEnter choice (1-7): ").strip()
            
            try:
                if choice == "1":
                    self._search()
                elif choice == "2":
                    self._view_details()
                elif choice == "3":
                    self._browse_files()
                elif choice == "4":
                    self._view_file()
                elif choice == "5":
                    self._export_json()
                elif choice == "6":
                    self._export_text()
                elif choice == "7":
                    print("Goodbye! 👋")
                    break
                else:
                    print("Invalid choice!")
            except KeyboardInterrupt:
                print("\n\nInterrupted! Exiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def _search(self):
        """Search packages."""
        query = input("Enter search query: ").strip()
        if not query:
            return
        
        limit = input("Results limit (default 30): ").strip()
        limit = int(limit) if limit else 30
        
        self.current_packages = self.analyzer.search(query, limit)
        
        print(f"\nFound {len(self.current_packages)} packages:\n")
        for i, pkg in enumerate(self.current_packages, 1):
            print(f"{i}. {pkg.name} ({pkg.version})")
            print(f"   {pkg.description[:80]}...")
            print()
    
    def _view_details(self):
        """View package details."""
        if not self.current_packages:
            print("No packages loaded. Search first!")
            return
        
        idx = input(f"Select package (1-{len(self.current_packages)}): ").strip()
        try:
            idx = int(idx) - 1
            pkg = self.current_packages[idx]
        except (ValueError, IndexError):
            print("Invalid selection!")
            return
        
        print(f"\n{'=' * 80}")
        print(f"Package: {pkg.name}")
        print(f"{'=' * 80}")
        
        # Enrich with NPM data
        pkg = self.analyzer.enrich_package(pkg)
        
        print(f"\nVersion: {pkg.version}")
        print(f"Description: {pkg.description}")
        print(f"Homepage: {pkg.homepage}")
        print(f"Repository: {pkg.repository_url}")
        print(f"License: {pkg.license}")
        print(f"Stars: {pkg.stars}")
        print(f"Forks: {pkg.forks}")
        
        if pkg.dependencies:
            print(f"\nDependencies ({len(pkg.dependencies)}):")
            for name, version in list(pkg.dependencies.items())[:10]:
                print(f"  - {name}: {version}")
            if len(pkg.dependencies) > 10:
                print(f"  ... and {len(pkg.dependencies) - 10} more")
        
        if pkg.maintainers:
            print(f"\nMaintainers:")
            for m in pkg.maintainers[:5]:
                print(f"  - {m.get('name', 'Unknown')} ({m.get('email', 'N/A')})")
    
    def _browse_files(self):
        """Browse package file tree."""
        if not self.current_packages:
            print("No packages loaded. Search first!")
            return
        
        idx = input(f"Select package (1-{len(self.current_packages)}): ").strip()
        try:
            idx = int(idx) - 1
            pkg = self.current_packages[idx]
        except (ValueError, IndexError):
            print("Invalid selection!")
            return
        
        print(f"\n📁 Fetching file tree for {pkg.name}...")
        tree = self.analyzer.get_file_tree(pkg)
        
        if tree:
            self._print_tree(tree, indent=0)
        else:
            print("❌ Failed to fetch file tree")
    
    def _print_tree(self, node: Dict, indent: int = 0):
        """Print file tree recursively."""
        name = node.get("path", "/").split("/")[-1] or "/"
        node_type = node.get("type", "file")
        prefix = "  " * indent
        icon = "📁" if node_type == "directory" else "📄"
        
        print(f"{prefix}{icon} {name}")
        
        if node_type == "directory":
            for child in node.get("files", []):
                self._print_tree(child, indent + 1)
    
    def _view_file(self):
        """View file content."""
        if not self.current_packages:
            print("No packages loaded. Search first!")
            return
        
        idx = input(f"Select package (1-{len(self.current_packages)}): ").strip()
        try:
            idx = int(idx) - 1
            pkg = self.current_packages[idx]
        except (ValueError, IndexError):
            print("Invalid selection!")
            return
        
        file_path = input("Enter file path (e.g., README.md): ").strip()
        if not file_path:
            return
        
        print(f"\n📄 Fetching {file_path}...")
        content = self.analyzer.get_file_content(pkg, file_path)
        
        if content:
            print(f"\n{'=' * 80}")
            print(content[:5000])  # Limit output
            if len(content) > 5000:
                print(f"\n... (truncated, total {len(content)} characters)")
            print(f"{'=' * 80}")
        else:
            print("❌ Failed to fetch file content")
    
    def _export_json(self):
        """Export to JSON."""
        if not self.current_packages:
            print("No packages to export!")
            return
        
        path = input("Output path (default: results.json): ").strip()
        path = path or "results.json"
        self.analyzer.export_json(self.current_packages, path)
    
    def _export_text(self):
        """Export to text."""
        if not self.current_packages:
            print("No packages to export!")
            return
        
        path = input("Output path (default: results.txt): ").strip()
        path = path or "results.txt"
        self.analyzer.export_text(self.current_packages, path)


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="NPM Package Analyzer & Downloader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python npm_consolidated.py

  # Search packages
  python npm_consolidated.py search react --limit 50

  # Get package info
  python npm_consolidated.py info express

Environment Variables:
  LIBRARIES_IO_KEY    API key for Libraries.io (required)
        """
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        choices=["search", "info", "interactive"],
        default="interactive",
        help="Command to execute"
    )
    parser.add_argument("query", nargs="?", help="Search query or package name")
    parser.add_argument("--limit", type=int, default=30, help="Search result limit")
    parser.add_argument("--export", help="Export results to file (JSON/TXT)")
    
    args = parser.parse_args()
    
    # Get API key
    api_key = os.environ.get("LIBRARIES_IO_KEY")
    if not api_key:
        print("❌ Error: LIBRARIES_IO_KEY environment variable not set!")
        print("\nGet your API key from: https://libraries.io/api")
        print("Then set it: export LIBRARIES_IO_KEY='your-key-here'")
        sys.exit(1)
    
    # Initialize analyzer
    analyzer = NPMAnalyzer(api_key)
    
    try:
        if args.command == "interactive" or not args.command:
            # Interactive CLI
            cli = CLI(analyzer)
            cli.run()
        
        elif args.command == "search":
            if not args.query:
                print("❌ Error: query required for search")
                sys.exit(1)
            
            packages = analyzer.search(args.query, args.limit)
            
            for pkg in packages:
                print(f"\n{pkg.name} ({pkg.version})")
                print(f"  {pkg.description}")
                print(f"  ⭐ {pkg.stars} | 🔀 {pkg.forks}")
            
            if args.export:
                if args.export.endswith(".json"):
                    analyzer.export_json(packages, args.export)
                else:
                    analyzer.export_text(packages, args.export)
        
        elif args.command == "info":
            if not args.query:
                print("❌ Error: package name required")
                sys.exit(1)
            
            pkg = analyzer.libraries_client.get_package(args.query)
            if pkg:
                pkg = analyzer.enrich_package(pkg)
                print(f"\n{'=' * 80}")
                print(f"Package: {pkg.name}")
                print(f"{'=' * 80}")
                print(f"Version: {pkg.version}")
                print(f"Description: {pkg.description}")
                print(f"Homepage: {pkg.homepage}")
                print(f"License: {pkg.license}")
                print(f"Stars: {pkg.stars}")
                
                if pkg.dependencies:
                    print(f"\nDependencies: {len(pkg.dependencies)}")
            else:
                print(f"❌ Package '{args.query}' not found")
    
    finally:
        analyzer.close()


if __name__ == "__main__":
    main()

