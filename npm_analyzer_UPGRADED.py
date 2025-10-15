#!/usr/bin/env python3
"""
NPM Package Analyzer Ultimate
Complete implementation with burst fetch, countdown timer, and 20K+ support
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import sqlite3
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict, field
import configparser
import tarfile
import csv
import webbrowser


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('npm_analyzer.log', maxBytes=5*1024*1024, backupCount=2),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration constants
CACHE_DB = "npm_cache.db"
SETTINGS_FILE = "npm_analyzer_settings.ini"
DOWNLOADS_DIR = "npm_downloads"
CACHE_TTL_DAYS = 7
DEFAULT_MAX_RESULTS = 20000
LIBRARIES_IO_BASE = "https://libraries.io/api"
NPM_REGISTRY_BASE = "https://registry.npmjs.org"
UNPKG_BASE = "https://unpkg.com"

# Burst fetch configuration
BURST_SIZE = 6000  # 60 requests × 100 packages
REQUESTS_PER_BURST = 60
PACKAGES_PER_REQUEST = 100
COOLDOWN_SECONDS = 60
RATE_LIMIT_PER_MINUTE = 60

# Theme colors
class Theme:
    BG = "#0D1117"
    BG_SECONDARY = "#161B22"
    BG_TERTIARY = "#21262D"
    TEXT = "#E6EDF3"
    TEXT_SECONDARY = "#8B949E"
    ACCENT = "#58A6FF"
    SUCCESS = "#3FB950"
    WARNING = "#D29922"
    ERROR = "#F85149"


@dataclass
class FileNode:
    """File tree node for unpkg browsing."""
    path: str
    type: str  # 'file' or 'directory'
    size: int = 0
    children: List['FileNode'] = field(default_factory=list)



@dataclass
class PackageInfo:
    """Complete package information with ALL features."""
    # Primary metrics
    name: str
    version: str
    file_count: int = 0  # PRIMARY METRIC from NPM Registry
    unpacked_size: int = 0
    
    # Basic info
    description: str = ""
    license: str = ""
    homepage: str = ""
    repository_url: str = ""
    npm_url: str = ""
    
    # Dependencies
    dependencies: Dict[str, str] = field(default_factory=dict)
    dev_dependencies: Dict[str, str] = field(default_factory=dict)
    peer_dependencies: Dict[str, str] = field(default_factory=dict)
    
    # Download stats (from NPM Registry)
    npm_downloads_weekly: int = 0
    npm_downloads_monthly: int = 0
    npm_downloads_daily: int = 0
    
    # Stats
    dependents_count: int = 0
    
    # File tree (from unpkg)
    file_tree: Optional[FileNode] = None
    
    # Package metadata
    keywords: List[str] = field(default_factory=list)
    maintainers: List[Dict] = field(default_factory=list)
    author: str = ""
    
    # Dates
    created_at: str = ""
    last_published: str = ""
    cache_timestamp: float = field(default_factory=time.time)
    
    # Enrichment flags
    enriched_npm: bool = False
    enriched_unpkg: bool = False
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        # Handle FileNode separately
        if self.file_tree:
            result['file_tree'] = self._file_node_to_dict(self.file_tree)
        return result
    
    def _file_node_to_dict(self, node: FileNode) -> Dict:
        return {
            'path': node.path,
            'type': node.type,
            'size': node.size,
            'children': [self._file_node_to_dict(c) for c in node.children]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PackageInfo':
        # Remove file_tree for now, handle separately if needed
        data_copy = data.copy()
        data_copy.pop('file_tree', None)
        return cls(**{k: v for k, v in data_copy.items() if k in cls.__annotations__})




class SettingsManager:
    """Manage application settings with INI file persistence."""
    
    def __init__(self, settings_file: str = SETTINGS_FILE):
        self.settings_file = settings_file
        self.config = configparser.ConfigParser()
        self._load_settings()
    
    def _load_settings(self):
        if os.path.exists(self.settings_file):
            self.config.read(self.settings_file)
        else:
            self._create_default_settings()
    
    def _create_default_settings(self):
        self.config['General'] = {
            'api_key': '',
            'max_results': str(DEFAULT_MAX_RESULTS)
        }
        self.config['UI'] = {
            'window_width': '1400',
            'window_height': '900'
        }
        self._save_settings()
    
    def _save_settings(self):
        with open(self.settings_file, 'w') as f:
            self.config.write(f)
    
    def get(self, section: str, key: str, fallback: str = '') -> str:
        return self.config.get(section, key, fallback=fallback)
    
    def set(self, section: str, key: str, value: str):
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self._save_settings()


class CacheManager:
    """SQLite-based caching with TTL support."""
    
    def __init__(self, db_path: str, ttl_days: int = CACHE_TTL_DAYS):
        self.db_path = db_path
        self.ttl_days = ttl_days
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS packages (
                key TEXT PRIMARY KEY,
                data TEXT,
                timestamp REAL
            )
        ''')
        conn.commit()
        conn.close()
    
    def get_package(self, name: str) -> Optional[PackageInfo]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT data, timestamp FROM packages WHERE key = ?',
            (name,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            data_json, timestamp = row
            age_days = (time.time() - timestamp) / 86400
            if age_days < self.ttl_days:
                return PackageInfo.from_dict(json.loads(data_json))
        return None
    
    def save_package(self, package: PackageInfo):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'REPLACE INTO packages (key, data, timestamp) VALUES (?, ?, ?)',
            (package.name, json.dumps(package.to_dict()), time.time())
        )
        conn.commit()
        conn.close()
    
    def clear_expired(self):
        cutoff = time.time() - (self.ttl_days * 86400)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM packages WHERE timestamp < ?', (cutoff,))
        conn.commit()
        conn.close()


class SearchHistoryManager:
    """Manage search history with SQLite."""

    def __init__(self, db_path: str = "npm_search_history.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create history table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                max_results INTEGER,
                result_count INTEGER,
                timestamp REAL,
                duration_seconds REAL
            )
        ''')
        conn.commit()
        conn.close()

    def save_search(self, query: str, max_results: int,
                    result_count: int, duration: float):
        """Save search to history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO search_history
            (query, max_results, result_count, timestamp, duration_seconds)
            VALUES (?, ?, ?, ?, ?)
        ''', (query, max_results, result_count, time.time(), duration))
        conn.commit()
        conn.close()

    def get_recent_searches(self, limit: int = 10) -> List[Dict]:
        """Get recent search history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT query, max_results, result_count,
                   timestamp, duration_seconds
            FROM search_history
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        results = []
        for row in cursor.fetchall():
            results.append({
                'query': row[0],
                'max_results': row[1],
                'result_count': row[2],
                'timestamp': datetime.datetime.fromtimestamp(row[3]),
                'duration': row[4]
            })
        conn.close()
        return results

    def clear_history(self):
        """Clear all search history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM search_history')
        conn.commit()
        conn.close()


class FavoritesManager:
    """Manage favorite packages."""

    def __init__(self, db_path: str = "npm_favorites.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create favorites table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                package_name TEXT PRIMARY KEY,
                added_timestamp REAL
            )
        ''')
        conn.commit()
        conn.close()

    def add_favorite(self, package_name: str):
        """Add package to favorites."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO favorites (package_name, added_timestamp)
            VALUES (?, ?)
        ''', (package_name, time.time()))
        conn.commit()
        conn.close()

    def remove_favorite(self, package_name: str):
        """Remove package from favorites."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM favorites WHERE package_name = ?',
                       (package_name,))
        conn.commit()
        conn.close()

    def is_favorite(self, package_name: str) -> bool:
        """Check if package is favorited."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM favorites WHERE package_name = ?',
                       (package_name,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def get_all_favorites(self) -> List[str]:
        """Get all favorite packages."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT package_name FROM favorites ORDER BY added_timestamp DESC')
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        return results


class NPMRegistryClient:
    """Client for NPM Registry API to get file counts and downloads."""
    
    def __init__(self):
        self.session = self._create_session()
    
    def _create_session(self):
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def enrich_package(self, package: PackageInfo) -> PackageInfo:
        """Enrich package with NPM Registry data including file count."""
        try:
            # Get package metadata
            url = f"{NPM_REGISTRY_BASE}/{package.name}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Get latest version data
            latest_version = package.version
            if latest_version in data.get('versions', {}):
                version_data = data['versions'][latest_version]
                
                # File count from dist
                if 'dist' in version_data:
                    dist = version_data['dist']
                    package.file_count = dist.get('fileCount', 0)
                    package.unpacked_size = dist.get('unpackedSize', 0)
                
                # Dependencies
                package.dependencies = version_data.get('dependencies', {})
                package.dev_dependencies = version_data.get('devDependencies', {})
                package.peer_dependencies = version_data.get('peerDependencies', {})
                
                # Metadata
                package.keywords = version_data.get('keywords', [])
                package.author = str(version_data.get('author', {}).get('name', ''))
            
            # Maintainers
            package.maintainers = data.get('maintainers', [])
            
            # Dates
            if 'time' in data:
                package.created_at = data['time'].get('created', '')
                package.last_published = data['time'].get('modified', '')
            
            # Get download stats
            package.npm_downloads_weekly = self._get_downloads(package.name, 'last-week')
            package.npm_downloads_monthly = self._get_downloads(package.name, 'last-month')
            
            package.enriched_npm = True
            logger.info(f"Enriched {package.name}: {package.file_count} files")
            
        except Exception as e:
            logger.error(f"Failed to enrich {package.name}: {e}")
        
        return package
    
    def _get_downloads(self, package_name: str, period: str) -> int:
        """Get download count for a package."""
        try:
            url = f"https://api.npmjs.org/downloads/point/{period}/{package_name}"
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            return data.get('downloads', 0)
        except Exception as e:
            logger.debug(f"Failed to get downloads for {package_name}: {e}")
            return 0


class UnpkgClient:
    """Client for unpkg.com to browse file trees and download files."""
    
    def __init__(self):
        self.session = self._create_session()
    
    def _create_session(self):
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def get_file_tree(self, package_name: str, version: str) -> Optional[FileNode]:
        """Get file tree for a package version from unpkg."""
        try:
            url = f"{UNPKG_BASE}/{package_name}@{version}/?meta"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Parse file tree
            root = FileNode(path="/", type="directory")
            self._parse_unpkg_tree(data, root)
            
            logger.info(f"Fetched file tree for {package_name}@{version}")
            return root
            
        except Exception as e:
            logger.error(f"Failed to get file tree for {package_name}@{version}: {e}")
            return None
    
    def _parse_unpkg_tree(self, data: Dict, parent: FileNode):
        """Recursively parse unpkg file tree."""
        if data.get('type') == 'directory':
            for file_data in data.get('files', []):
                node = FileNode(
                    path=file_data.get('path', ''),
                    type=file_data.get('type', 'file'),
                    size=file_data.get('size', 0)
                )
                parent.children.append(node)
                
                if node.type == 'directory':
                    self._parse_unpkg_tree(file_data, node)
    
    def get_file_content(self, package_name: str, version: str, file_path: str) -> Optional[str]:
        """Get content of a specific file."""
        try:
            url = f"{UNPKG_BASE}/{package_name}@{version}{file_path}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to get file content: {e}")
            return None
    
    def download_package(self, package_name: str, version: str, output_dir: str) -> bool:
        """Download entire package as tarball."""
        try:
            # Get tarball URL from NPM registry
            url = f"{NPM_REGISTRY_BASE}/{package_name}/{version}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            tarball_url = data.get('dist', {}).get('tarball')
            if not tarball_url:
                logger.error(f"No tarball URL found for {package_name}@{version}")
                return False
            
            # Download tarball
            tarball_response = self.session.get(tarball_url, timeout=30, stream=True)
            tarball_response.raise_for_status()
            
            # Save and extract
            os.makedirs(output_dir, exist_ok=True)
            tarball_path = os.path.join(output_dir, f"{package_name}-{version}.tgz")
            
            with open(tarball_path, 'wb') as f:
                for chunk in tarball_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract
            extract_dir = os.path.join(output_dir, f"{package_name}-{version}")
            with tarfile.open(tarball_path, 'r:gz') as tar:
                tar.extractall(extract_dir)
            
            # Clean up tarball
            os.remove(tarball_path)
            
            logger.info(f"Downloaded {package_name}@{version} to {extract_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {package_name}@{version}: {e}")
            return False


class PackageEnricher:
    """Orchestrate enrichment from multiple sources."""
    
    def __init__(self, cache: 'CacheManager'):
        self.npm_client = NPMRegistryClient()
        self.unpkg_client = UnpkgClient()
        self.cache = cache
    
    def enrich_packages_batch(
        self,
        packages: List[PackageInfo],
        progress_callback: Optional[Callable] = None,
        include_file_tree: bool = False
    ) -> List[PackageInfo]:
        """Enrich multiple packages concurrently."""
        enriched = []
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {
                executor.submit(
                    self.enrich_single,
                    pkg,
                    include_file_tree
                ): pkg
                for pkg in packages
            }
            
            completed = 0
            for future in as_completed(futures):
                try:
                    enriched_pkg = future.result(timeout=15)
                    enriched.append(enriched_pkg)
                    self.cache.save_package(enriched_pkg)
                    
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, len(packages))
                        
                except Exception as e:
                    pkg = futures[future]
                    logger.error(f"Failed to enrich {pkg.name}: {e}")
                    enriched.append(pkg)
        
        return enriched
    
    def enrich_single(self, package: PackageInfo, include_file_tree: bool = False) -> PackageInfo:
        """Enrich a single package with all data."""
        # Check cache first
        cached = self.cache.get_package(package.name)
        if cached and cached.enriched_npm:
            return cached
        
        # Enrich with NPM Registry (includes file count)
        package = self.npm_client.enrich_package(package)
        
        # Optionally get file tree from unpkg
        if include_file_tree:
            file_tree = self.unpkg_client.get_file_tree(package.name, package.version)
            if file_tree:
                package.file_tree = file_tree
                package.enriched_unpkg = True
        
        return package


class BatchProcessor:
    """Process multiple packages in batch."""

    def __init__(self, libraries_client: 'LibrariesIOClient',
                 enricher: 'PackageEnricher'):
        self.libraries_client = libraries_client
        self.enricher = enricher

    def process_package_list(self, package_names: List[str],
                             progress_callback: Optional[Callable] = None) -> List[PackageInfo]:
        """Process a list of package names."""
        results = []
        total = len(package_names)

        for i, name in enumerate(package_names):
            try:
                # Search for exact package name
                search_gen = self.libraries_client.search_packages_burst(
                    name, max_results=1
                )
                
                for batch_packages, _, _ in search_gen:
                    if batch_packages:
                        pkg = batch_packages[0]
                        # Enrich package
                        enriched = self.enricher.enrich_single(pkg)
                        results.append(enriched)
                        break

                if progress_callback:
                    progress_callback(i + 1, total)

            except Exception as e:
                logger.error(f"Failed to process {name}: {e}")
                continue

        return results

    def process_from_file(self, filepath: str,
                          progress_callback: Optional[Callable] = None) -> List[PackageInfo]:
        """Process packages from a text file (one per line)."""
        with open(filepath, 'r', encoding='utf-8') as f:
            package_names = [line.strip() for line in f if line.strip()]

        return self.process_package_list(package_names, progress_callback)


class StatisticsDashboard:
    """Display package statistics and analytics."""

    def __init__(self, packages: List[PackageInfo]):
        self.packages = packages
        self.window = None

    def show(self):
        """Display statistics window."""
        self.window = tk.Toplevel()
        self.window.title("Package Statistics")
        self.window.geometry("900x700")
        self.window.configure(bg=Theme.BG)

        # Create notebook for tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: Overview Stats
        overview = self._create_overview_tab(notebook)
        notebook.add(overview, text="📊 Overview")

        # Tab 2: Size Analysis
        sizes = self._create_size_tab(notebook)
        notebook.add(sizes, text="📦 Sizes")

        # Tab 3: Dependencies
        deps = self._create_dependencies_tab(notebook)
        notebook.add(deps, text="🔗 Dependencies")

        # Tab 4: Downloads
        downloads = self._create_downloads_tab(notebook)
        notebook.add(downloads, text="⬇️ Downloads")

    def _create_overview_tab(self, parent) -> tk.Frame:
        """Create overview statistics tab."""
        frame = tk.Frame(parent, bg=Theme.BG)

        # Calculate stats
        total_packages = len(self.packages)
        total_size = sum(p.unpacked_size for p in self.packages)
        total_files = sum(p.file_count for p in self.packages)
        avg_size = total_size / total_packages if total_packages > 0 else 0

        # Create stats labels
        stats = [
            ("Total Packages", f"{total_packages:,}"),
            ("Total Size", self._format_size(total_size)),
            ("Average Size", self._format_size(avg_size)),
            ("Total Files", f"{total_files:,}"),
            ("Avg Files/Package", f"{total_files/total_packages:.0f}" if total_packages > 0 else "0"),
        ]

        for i, (label, value) in enumerate(stats):
            tk.Label(
                frame, text=label, font=("Arial", 14),
                fg=Theme.TEXT_SECONDARY, bg=Theme.BG
            ).grid(row=i, column=0, sticky=tk.W, padx=30, pady=15)

            tk.Label(
                frame, text=value, font=("Arial", 20, "bold"),
                fg=Theme.ACCENT, bg=Theme.BG
            ).grid(row=i, column=1, sticky=tk.W, padx=30, pady=15)

        return frame

    def _create_size_tab(self, parent) -> tk.Frame:
        """Create size analysis tab."""
        frame = tk.Frame(parent, bg=Theme.BG)

        # Sort by size
        sorted_packages = sorted(
            self.packages,
            key=lambda p: p.unpacked_size,
            reverse=True
        )[:20]

        # Create text widget
        text = scrolledtext.ScrolledText(
            frame, height=30, width=100,
            bg=Theme.BG_SECONDARY, fg=Theme.TEXT,
            font=("Courier", 11)
        )
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add header
        text.insert(tk.END, "Top 20 Largest Packages\n")
        text.insert(tk.END, "=" * 90 + "\n\n")
        text.insert(tk.END, f"{'Rank':<6}{'Package':<40}{'Size':<20}{'Files'}\n")
        text.insert(tk.END, "-" * 90 + "\n")

        # Add packages
        for i, pkg in enumerate(sorted_packages, 1):
            size_str = self._format_size(pkg.unpacked_size)
            text.insert(
                tk.END,
                f"{i:<6}{pkg.name[:39]:<40}{size_str:<20}{pkg.file_count:,}\n"
            )

        text.configure(state=tk.DISABLED)
        return frame

    def _create_dependencies_tab(self, parent) -> tk.Frame:
        """Create dependencies analysis tab."""
        frame = tk.Frame(parent, bg=Theme.BG)

        # Count dependencies
        dep_counts = []
        for pkg in self.packages:
            total_deps = (
                len(pkg.dependencies) +
                len(pkg.dev_dependencies) +
                len(pkg.peer_dependencies)
            )
            dep_counts.append((pkg.name, total_deps,
                              len(pkg.dependencies),
                              len(pkg.dev_dependencies),
                              len(pkg.peer_dependencies)))

        # Sort by total deps
        dep_counts.sort(key=lambda x: x[1], reverse=True)

        # Create text widget
        text = scrolledtext.ScrolledText(
            frame, height=30, width=105,
            bg=Theme.BG_SECONDARY, fg=Theme.TEXT,
            font=("Courier", 11)
        )
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add header
        text.insert(tk.END, "Top 20 Packages by Dependencies\n")
        text.insert(tk.END, "=" * 95 + "\n\n")
        text.insert(tk.END, f"{'Rank':<6}{'Package':<35}{'Total':<10}{'Prod':<10}{'Dev':<10}{'Peer'}\n")
        text.insert(tk.END, "-" * 95 + "\n")

        # Add packages
        for i, (name, total, prod, dev, peer) in enumerate(dep_counts[:20], 1):
            text.insert(
                tk.END,
                f"{i:<6}{name[:34]:<35}{total:<10}{prod:<10}{dev:<10}{peer}\n"
            )

        text.configure(state=tk.DISABLED)
        return frame

    def _create_downloads_tab(self, parent) -> tk.Frame:
        """Create downloads analysis tab."""
        frame = tk.Frame(parent, bg=Theme.BG)

        # Sort by weekly downloads
        sorted_packages = sorted(
            [p for p in self.packages if p.npm_downloads_weekly > 0],
            key=lambda p: p.npm_downloads_weekly,
            reverse=True
        )[:20]

        # Create text widget
        text = scrolledtext.ScrolledText(
            frame, height=30, width=100,
            bg=Theme.BG_SECONDARY, fg=Theme.TEXT,
            font=("Courier", 11)
        )
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add header
        text.insert(tk.END, "Top 20 Most Downloaded Packages\n")
        text.insert(tk.END, "=" * 90 + "\n\n")
        text.insert(tk.END, f"{'Rank':<6}{'Package':<35}{'Weekly':<25}{'Monthly'}\n")
        text.insert(tk.END, "-" * 90 + "\n")

        # Add packages
        for i, pkg in enumerate(sorted_packages, 1):
            weekly = self._format_number(pkg.npm_downloads_weekly)
            monthly = self._format_number(pkg.npm_downloads_monthly)
            text.insert(
                tk.END,
                f"{i:<6}{pkg.name[:34]:<35}{weekly:<25}{monthly}\n"
            )

        text.configure(state=tk.DISABLED)
        return frame

    @staticmethod
    def _format_size(bytes_val: int) -> str:
        """Format bytes to human readable."""
        if bytes_val == 0:
            return "0 B"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} TB"

    @staticmethod
    def _format_number(num: int) -> str:
        """Format number with commas."""
        if num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num/1_000:.1f}K"
        return str(num)


class LibrariesIOClient:
    """Client for Libraries.io API with burst fetch support."""
    
    def __init__(self, api_key: str, cache: CacheManager):
        self.api_key = api_key
        self.cache = cache
        self.session = self._create_session()
        self.burst_tracker = {'requests_made': 0, 'burst_start': 0}
    
    def _create_session(self):
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def search_packages_burst(
        self,
        query: str,
        max_results: int,
        progress_callback: Optional[Callable] = None,
        countdown_callback: Optional[Callable] = None
    ) -> List[PackageInfo]:
        """
        Search packages using burst fetch strategy.
        Fetches 6,000 packages instantly, then waits 60 seconds.
        """
        all_results = []
        bursts_needed = (max_results + BURST_SIZE - 1) // BURST_SIZE
        
        for burst_num in range(bursts_needed):
            remaining = max_results - len(all_results)
            this_burst_size = min(remaining, BURST_SIZE)
            
            logger.info(f"BURST {burst_num + 1}/{bursts_needed}: Fetching {this_burst_size} packages...")
            
            # BURST FETCH (instant)
            burst_results = self._fetch_burst_instant(
                query, this_burst_size, burst_num, progress_callback
            )
            all_results.extend(burst_results)
            
            logger.info(f"Fetched {len(all_results)} / {max_results} packages")
            
            # Countdown if more bursts needed
            if burst_num < bursts_needed - 1 and countdown_callback:
                countdown_callback(COOLDOWN_SECONDS)
        
        return all_results
    
    def _fetch_burst_instant(
        self,
        query: str,
        count: int,
        burst_offset: int,
        progress_callback: Optional[Callable] = None
    ) -> List[PackageInfo]:
        """Fire 60 requests simultaneously."""
        requests_needed = min((count + PACKAGES_PER_REQUEST - 1) // PACKAGES_PER_REQUEST, REQUESTS_PER_BURST)
        results = []
        
        with ThreadPoolExecutor(max_workers=REQUESTS_PER_BURST) as executor:
            page_start = burst_offset * REQUESTS_PER_BURST
            
            futures = {
                executor.submit(
                    self._fetch_single_page,
                    query, page_start + i
                ): i
                for i in range(requests_needed)
            }
            
            completed = 0
            for future in as_completed(futures):
                try:
                    page_results = future.result(timeout=10)
                    results.extend(page_results)
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, requests_needed)
                except Exception as e:
                    logger.error(f"Page fetch failed: {e}")
        
        return results[:count]
    
    def _fetch_single_page(self, query: str, page: int) -> List[PackageInfo]:
        """Fetch a single page from Libraries.io."""
        url = f"{LIBRARIES_IO_BASE}/search"
        params = {
            'q': query,
            'platforms': 'npm',
            'per_page': PACKAGES_PER_REQUEST,
            'page': page + 1,  # API pages are 1-indexed
            'api_key': self.api_key
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            packages = []
            for item in data:
                pkg = PackageInfo(
                    name=item.get('name', ''),
                    version=item.get('latest_stable_release_number', item.get('latest_release_number', 'unknown')),
                    description=item.get('description', '')[:200],
                    homepage=item.get('homepage', ''),
                    repository_url=item.get('repository_url', ''),
                    npm_url=f"https://www.npmjs.com/package/{item.get('name', '')}",
                    license=item.get('licenses', 'Unknown'),
                    dependents_count=item.get('dependents_count', 0)
                )
                packages.append(pkg)
            
            return packages
        except Exception as e:
            logger.error(f"Error fetching page {page}: {e}")
            return []


class CountdownTimer(tk.Frame):
    """Visual countdown timer component."""
    
    def __init__(self, parent, duration: int, on_complete: Callable):
        super().__init__(parent, bg=Theme.BG)
        self.duration = duration
        self.remaining = duration
        self.on_complete = on_complete
        self.running = False
        
        # Title
        title = tk.Label(
            self,
            text="⏳ RATE LIMIT COOLDOWN ⏳",
            font=("Arial", 16, "bold"),
            fg=Theme.WARNING,
            bg=Theme.BG
        )
        title.pack(pady=10)
        
        # Large countdown display
        self.time_label = tk.Label(
            self,
            text="01:00",
            font=("Arial", 48, "bold"),
            fg=Theme.ACCENT,
            bg=Theme.BG
        )
        self.time_label.pack(pady=20)
        
        # Progress bar
        self.progress = ttk.Progressbar(
            self,
            length=400,
            mode='determinate',
            maximum=duration
        )
        self.progress.pack(pady=10)
        
        # Message
        self.message_label = tk.Label(
            self,
            text="Next burst starts automatically...",
            font=("Arial", 12),
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG
        )
        self.message_label.pack(pady=10)
    
    def start(self):
        """Start countdown animation."""
        self.remaining = self.duration
        self.running = True
        self._countdown()
    
    def stop(self):
        """Stop countdown."""
        self.running = False
    
    def _countdown(self):
        if not self.running:
            return
        
        if self.remaining > 0:
            # Update display
            minutes = self.remaining // 60
            seconds = self.remaining % 60
            self.time_label.configure(text=f"{minutes:02d}:{seconds:02d}")
            self.progress.configure(value=self.duration - self.remaining)
            
            # Schedule next update
            self.remaining -= 1
            self.after(1000, self._countdown)
        else:
            # Countdown complete
            self.time_label.configure(text="Starting burst...")
            if self.on_complete:
                self.on_complete()


class NPMAnalyzerApp:
    """Main application with burst fetch and countdown timer."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("NPM Package Analyzer Ultimate - Burst Fetch Edition")
        self.root.geometry("1400x900")
        self.root.configure(bg=Theme.BG)
        
        # Initialize components
        self.settings = SettingsManager()
        self.cache = CacheManager(CACHE_DB)
        
        api_key = self.settings.get('General', 'api_key', '')
        if not api_key:
            api_key = self._prompt_for_api_key()
        
        self.client = LibrariesIOClient(api_key, self.cache)
        
        
        # Initialize enricher
        self.enricher = PackageEnricher(self.cache)
        self.unpkg_client = UnpkgClient()
        # State
        self.current_results: List[PackageInfo] = []
        self.search_running = False
        self.countdown_timer = None
        
        # Create UI
        self._create_ui()
    
    def _prompt_for_api_key(self) -> str:
        """Prompt user for Libraries.io API key."""
        dialog = tk.Toplevel(self.root)
        dialog.title("API Key Required")
        dialog.geometry("400x200")
        dialog.configure(bg=Theme.BG)
        
        tk.Label(
            dialog,
            text="Enter your Libraries.io API Key:",
            font=("Arial", 12),
            fg=Theme.TEXT,
            bg=Theme.BG
        ).pack(pady=20)
        
        entry = tk.Entry(dialog, width=40, font=("Arial", 10))
        entry.pack(pady=10)
        
        api_key_result = ['']
        
        def save_key():
            key = entry.get().strip()
            if key:
                self.settings.set('General', 'api_key', key)
                api_key_result[0] = key
                dialog.destroy()
        
        tk.Button(
            dialog,
            text="Save",
            command=save_key,
            bg=Theme.ACCENT,
            fg=Theme.TEXT,
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        ).pack(pady=10)
        
        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)
        
        return api_key_result[0]
    
    def _create_ui(self):
        """Create main UI."""
        # Top search bar
        search_frame = tk.Frame(self.root, bg=Theme.BG_SECONDARY, height=80)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        search_frame.pack_propagate(False)
        
        tk.Label(
            search_frame,
            text="Search:",
            font=("Arial", 12),
            fg=Theme.TEXT,
            bg=Theme.BG_SECONDARY
        ).pack(side=tk.LEFT, padx=(10, 5))
        
        self.search_entry = tk.Entry(
            search_frame,
            font=("Arial", 12),
            bg=Theme.BG_TERTIARY,
            fg=Theme.TEXT,
            insertbackground=Theme.TEXT,
            width=30
        )
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<Return>', lambda e: self._on_search())
        
        tk.Label(
            search_frame,
            text="Max:",
            font=("Arial", 12),
            fg=Theme.TEXT,
            bg=Theme.BG_SECONDARY
        ).pack(side=tk.LEFT, padx=(20, 5))
        
        self.max_results_var = tk.StringVar(value="20000")
        max_dropdown = ttk.Combobox(
            search_frame,
            textvariable=self.max_results_var,
            values=["1000", "5000", "10000", "20000", "50000"],
            width=10,
            state="readonly"
        )
        max_dropdown.pack(side=tk.LEFT, padx=5)
        
        self.search_btn = tk.Button(
            search_frame,
            text="🔍 Search",
            command=self._on_search,
            bg=Theme.ACCENT,
            fg=Theme.TEXT,
            font=("Arial", 12, "bold"),
            padx=20,
            pady=5,
            cursor="hand2"
        )
        self.search_btn.pack(side=tk.LEFT, padx=10)
        
        # Export button
        tk.Button(
            search_frame,
            text="💾 Export",
            command=self._on_export_clicked,
            bg=Theme.SUCCESS,
            fg=Theme.TEXT,
            font=("Arial", 12, "bold"),
            padx=15,
            pady=5,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)
        
        # View Files button
        tk.Button(
            search_frame,
            text="📁 Files",
            command=self._on_view_files_clicked,
            bg=Theme.ACCENT,
            fg=Theme.TEXT,
            font=("Arial", 12, "bold"),
            padx=15,
            pady=5,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        
        # Countdown timer frame (hidden by default)
        self.countdown_frame = tk.Frame(self.root, bg=Theme.BG_SECONDARY)
        # Not packed yet
        
        # Results info bar
        info_frame = tk.Frame(self.root, bg=Theme.BG_SECONDARY, height=40)
        info_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        info_frame.pack_propagate(False)
        
        self.results_label = tk.Label(
            info_frame,
            text="Results (0)",
            font=("Arial", 12, "bold"),
            fg=Theme.TEXT,
            bg=Theme.BG_SECONDARY
        )
        self.results_label.pack(side=tk.LEFT, padx=10)
        
        self.status_label = tk.Label(
            info_frame,
            text="Ready",
            font=("Arial", 10),
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_SECONDARY
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # Results treeview
        tree_frame = tk.Frame(self.root, bg=Theme.BG)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Scrollbars
        tree_scroll_y = ttk.Scrollbar(tree_frame)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview
        self.results_tree = ttk.Treeview(
            tree_frame,
            columns=("name", "version", "files", "size", "downloads", "dependents"),
            show="headings",
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set,
            height=25
        )
        
        # Configure columns
        self.results_tree.heading("name", text="Package Name")
        self.results_tree.heading("version", text="Version")
        self.results_tree.heading("files", text="📄 Files")
        self.results_tree.heading("size", text="📦 Size")
        self.results_tree.heading("downloads", text="↓ Weekly")
        self.results_tree.heading("dependents", text="👥 Dependents")
        
        self.results_tree.column("name", width=300)
        self.results_tree.column("version", width=100)
        self.results_tree.column("files", width=100)
        self.results_tree.column("size", width=100)
        self.results_tree.column("downloads", width=150)
        self.results_tree.column("dependents", width=150)
        
        self.results_tree.pack(fill=tk.BOTH, expand=True)
        
        # Bind double-click
        self.results_tree.bind("<Double-1>", self._on_package_double_click)
        
        tree_scroll_y.config(command=self.results_tree.yview)
        tree_scroll_x.config(command=self.results_tree.xview)
        
        # Apply dark theme to treeview
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            background=Theme.BG_TERTIARY,
            foreground=Theme.TEXT,
            fieldbackground=Theme.BG_TERTIARY,
            borderwidth=0
        )
        style.configure("Treeview.Heading", background=Theme.BG_SECONDARY, foreground=Theme.TEXT)
        style.map("Treeview", background=[("selected", Theme.ACCENT)])
    
    def _on_search(self):
        """Handle search button click."""
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Input Required", "Please enter a search query")
            return
        
        if self.search_running:
            messagebox.showinfo("Search Running", "A search is already in progress")
            return
        
        max_results = int(self.max_results_var.get())
        
        # Clear results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        self.current_results = []
        self.search_running = True
        self.search_btn.configure(state=tk.DISABLED)
        
        # Start search in background thread
        thread = threading.Thread(
            target=self._perform_search_burst,
            args=(query, max_results),
            daemon=True
        )
        thread.start()
    
    def _perform_search_burst(self, query: str, max_results: int):
        """Perform burst search in background thread."""
        try:
            def progress_callback(current, total):
                self.root.after(0, lambda: self._update_status(
                    f"Fetching burst: {current}/{total} requests..."
                ))
            
            def countdown_callback(seconds):
                # Show countdown timer
                self.root.after(0, lambda: self._show_countdown(seconds))
            
            results = self.client.search_packages_burst(
                query,
                max_results,
                progress_callback=progress_callback,
                countdown_callback=countdown_callback
            )
            

            # Enrich first 100 packages with real data
            if len(results) > 0:
                self.root.after(0, lambda: self._update_status("Enriching with real data..."))
                
                enrich_count = min(100, len(results))
                
                def enrich_progress(current, total):
                    self.root.after(0, lambda c=current, t=total: self._update_status(
                        f"Enriching: {c}/{t} packages..."
                    ))
                
                enriched = self.enricher.enrich_packages_batch(
                    results[:enrich_count],
                    progress_callback=enrich_progress,
                    include_file_tree=False
                )
                
                # Combine enriched + remaining
                results = enriched + results[enrich_count:]
            
            self.current_results = results
            self.root.after(0, lambda: self._display_results(results))
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            self.root.after(0, lambda: messagebox.showerror("Search Error", str(e)))
        finally:
            self.search_running = False
            self.root.after(0, lambda: self.search_btn.configure(state=tk.NORMAL))
            self.root.after(0, lambda: self._update_status("Search complete"))
    
    def _show_countdown(self, duration: int):
        """Show countdown timer and block until complete."""
        if self.countdown_frame.winfo_manager():
            self.countdown_frame.pack_forget()
        
        # Create new countdown timer
        for widget in self.countdown_frame.winfo_children():
            widget.destroy()
        
        timer = CountdownTimer(
            self.countdown_frame,
            duration,
            on_complete=lambda: self.countdown_frame.pack_forget()
        )
        timer.pack(fill=tk.BOTH, expand=True)
        
        self.countdown_frame.pack(fill=tk.X, padx=10, pady=10, after=self.search_btn.master)
        timer.start()
        
        # Block until countdown completes
        time.sleep(duration)
    
    def _display_results(self, packages: List[PackageInfo]):
        """Display search results in treeview."""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        for pkg in packages:
            self.results_tree.insert("", tk.END, values=(
                pkg.name,
                pkg.version,
                f"{pkg.file_count:,}" if pkg.file_count > 0 else "N/A",
                self._format_size(pkg.unpacked_size) if pkg.unpacked_size > 0 else "N/A",
                self._format_downloads(pkg.npm_downloads_weekly),
                f"{pkg.dependents_count:,}" if pkg.dependents_count > 0 else "N/A"
            ))
        
        self.results_label.configure(text=f"Results ({len(packages):,})")
    
    def _format_size(self, bytes_size: int) -> str:
        """Format bytes to human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} TB"
    
    def _format_downloads(self, count: int) -> str:
        """Format download count."""
        if count == 0:
            return "N/A"
        if count < 1000:
            return str(count)
        elif count < 1000000:
            return f"{count/1000:.1f}K"
        else:
            return f"{count/1000000:.1f}M"
    
    def _update_status(self, message: str):
        """Update status label."""
        self.status_label.configure(text=message)




    def _on_export_clicked(self):
        """Handle export button click."""
        if not self.current_results:
            messagebox.showwarning("No Results", "Search for packages first")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[
                ("JSON", "*.json"),
                ("CSV", "*.csv"),
                ("Text", "*.txt")
            ]
        )
        
        if filepath:
            self._export_results(filepath)
    
    def _export_results(self, filepath):
        """Export results to file."""
        ext = filepath.split('.')[-1].lower()
        
        try:
            if ext == 'json':
                with open(filepath, 'w') as f:
                    json.dump([p.to_dict() for p in self.current_results], f, indent=2)
            
            elif ext == 'csv':
                with open(filepath, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Name', 'Version', 'Files', 'Size', 'Downloads', 'Dependents'])
                    for pkg in self.current_results:
                        writer.writerow([
                            pkg.name,
                            pkg.version,
                            pkg.file_count,
                            pkg.unpacked_size,
                            pkg.npm_downloads_weekly,
                            pkg.dependents_count
                        ])
            
            elif ext == 'txt':
                with open(filepath, 'w') as f:
                    for pkg in self.current_results:
                        f.write(f"{pkg.name}@{pkg.version}\n")
                        f.write(f"  Files: {pkg.file_count:,}\n")
                        f.write(f"  Size: {self._format_size(pkg.unpacked_size)}\n")
                        f.write(f"  Downloads: {pkg.npm_downloads_weekly:,}/week\n\n")
            
            messagebox.showinfo("Success", f"Exported {len(self.current_results)} packages")
        
        except Exception as e:
            logger.error(f"Export failed: {e}")
            messagebox.showerror("Export Error", str(e))
    
    def _on_view_files_clicked(self):
        """Handle view files button click."""
        selected = self.results_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a package first")
            return
        
        idx = self.results_tree.index(selected[0])
        package = self.current_results[idx]
        self._show_file_tree_dialog(package)
    
    def _show_file_tree_dialog(self, package):
        """Show file tree dialog for package."""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Files: {package.name}@{package.version}")
        dialog.geometry("700x600")
        dialog.configure(bg=Theme.BG)
        
        status = tk.Label(
            dialog,
            text="Loading file tree...",
            font=("Arial", 12),
            bg=Theme.BG,
            fg=Theme.TEXT_SECONDARY
        )
        status.pack(pady=10)
        
        tree_frame = tk.Frame(dialog, bg=Theme.BG)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree = ttk.Treeview(
            tree_frame,
            show='tree',
            yscrollcommand=scrollbar.set
        )
        tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=tree.yview)
        
        def fetch_tree():
            try:
                file_tree = self.unpkg_client.get_file_tree(package.name, package.version)
                if file_tree:
                    dialog.after(0, lambda: self._populate_file_tree(tree, file_tree, status))
                else:
                    dialog.after(0, lambda: status.configure(
                        text="Failed to load file tree", fg=Theme.ERROR
                    ))
            except Exception:
                dialog.after(0, lambda: status.configure(
                    text=f"Error: {str(e)}", fg=Theme.ERROR
                ))
        
        threading.Thread(target=fetch_tree, daemon=True).start()
    
    def _populate_file_tree(self, tree, node, status_label):
        """Populate tree widget with file structure."""
        def count_files(n):
            count = 1 if n.type == 'file' else 0
            for child in n.children:
                count += count_files(child)
            return count
        
        total_files = count_files(node)
        status_label.configure(
            text=f"Loaded {total_files} files",
            fg=Theme.SUCCESS
        )
        
        def add_node(parent_id, node):
            icon = "📁" if node.type == "directory" else "📄"
            name = node.path.split('/')[-1] or node.path
            size_str = f" ({self._format_size(node.size)})" if node.size > 0 else ""
            text = f"{icon} {name}{size_str}"
            
            item_id = tree.insert(parent_id, 'end', text=text)
            
            for child in sorted(node.children, key=lambda x: (x.type != 'directory', x.path)):
                add_node(item_id, child)
        
        add_node('', node)
    
    def _on_package_double_click(self, event):
        """Handle package double-click."""
        selected = self.results_tree.selection()
        if selected:
            idx = self.results_tree.index(selected[0])
            package = self.current_results[idx]
            self._show_package_details(package)
    
    def _show_package_details(self, package):
        """Show package details dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Details: {package.name}")
        dialog.geometry("700x700")
        dialog.configure(bg=Theme.BG)
        
        text = scrolledtext.ScrolledText(
            dialog,
            bg=Theme.BG_TERTIARY,
            fg=Theme.TEXT,
            font=("Courier", 10),
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        details = f"""
╔═══════════════════════════════════════════════════════╗
║  {package.name}@{package.version}
╚═══════════════════════════════════════════════════════╝

📦 PACKAGE METRICS
─────────────────────────────────────────────────────────
📄 Files:          {package.file_count:,}
📦 Size:           {self._format_size(package.unpacked_size)}
↓ Weekly:          {self._format_downloads(package.npm_downloads_weekly)}
↓ Monthly:         {self._format_downloads(package.npm_downloads_monthly)}
👥 Dependents:     {package.dependents_count:,}

📝 DESCRIPTION
─────────────────────────────────────────────────────────
{package.description or 'No description'}

ℹ️  METADATA
─────────────────────────────────────────────────────────
License:    {package.license}
Author:     {package.author or 'Unknown'}
Homepage:   {package.homepage or 'N/A'}

🏷️  KEYWORDS
─────────────────────────────────────────────────────────
{', '.join(package.keywords[:15]) if package.keywords else 'None'}

📦 DEPENDENCIES ({len(package.dependencies)})
─────────────────────────────────────────────────────────
"""
        
        if package.dependencies:
            for name, version in list(package.dependencies.items())[:20]:
                details += f"  {name}: {version}\n"
            if len(package.dependencies) > 20:
                details += f"  ... and {len(package.dependencies) - 20} more\n"
        else:
            details += "  None\n"
        
        details += f"""
📅 TIMELINE
─────────────────────────────────────────────────────────
Created:    {package.created_at[:10] if package.created_at else 'Unknown'}
Updated:    {package.last_published[:10] if package.last_published else 'Unknown'}

🔗 LINKS
─────────────────────────────────────────────────────────
NPM:        {package.npm_url}
"""
        
        text.insert('1.0', details)
        text.configure(state='disabled')
        
        btn_frame = tk.Frame(dialog, bg=Theme.BG)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(
            btn_frame,
            text="Open NPM",
            command=lambda: webbrowser.open(package.npm_url),
            bg=Theme.ACCENT,
            fg=Theme.TEXT,
            padx=15,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        if package.homepage:
            tk.Button(
                btn_frame,
                text="Homepage",
                command=lambda: webbrowser.open(package.homepage),
                bg=Theme.ACCENT,
                fg=Theme.TEXT,
                padx=15,
                pady=5
            ).pack(side=tk.LEFT, padx=5)


def main():
    root = tk.Tk()
    NPMAnalyzerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
