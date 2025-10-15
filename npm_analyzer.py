#!/usr/bin/env python3
"""
NPM Package Analyzer - Complete Production Version
All-in-one NPM package search, analysis, and file browsing tool
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

# Configuration
CACHE_DB = "npm_cache.db"
CACHE_TTL_DAYS = 7
DEFAULT_MAX_RESULTS = 20000
LIBRARIES_IO_BASE = "https://libraries.io/api"
NPM_REGISTRY_BASE = "https://registry.npmjs.org"
UNPKG_BASE = "https://unpkg.com"

# Burst fetch settings
BURST_SIZE = 6000  # 60 requests × 100 packages
REQUESTS_PER_BURST = 60
PACKAGES_PER_REQUEST = 100
COOLDOWN_SECONDS = 60


# Data Models
@dataclass
class PackageInfo:
    """Package information from multiple sources."""
    name: str = ""
    version: str = ""
    description: str = ""
    homepage: str = ""
    repository_url: str = ""
    npm_url: str = ""
    license: str = ""
    dependents_count: int = 0
    
    # NPM Registry enrichment
    file_count: int = 0
    unpacked_size: int = 0
    dependencies: Dict = field(default_factory=dict)
    dev_dependencies: Dict = field(default_factory=dict)
    peer_dependencies: Dict = field(default_factory=dict)
    keywords: List[str] = field(default_factory=list)
    author: str = ""
    maintainers: List = field(default_factory=list)
    created_at: str = ""
    last_published: str = ""
    npm_downloads_weekly: int = 0
    npm_downloads_monthly: int = 0
    enriched_npm: bool = False


@dataclass
class FileNode:
    """File tree node."""
    path: str
    type: str  # 'file' or 'directory'
    size: int = 0
    children: List['FileNode'] = field(default_factory=list)


# Theme
class Theme:
    BG = "#1e1e1e"
    FG = "#ffffff"
    ACCENT = "#007acc"
    SECONDARY = "#2d2d2d"
    TEXT_SECONDARY = "#cccccc"
    SUCCESS = "#4ec9b0"
    WARNING = "#f48771"
    ERROR = "#f44747"


# Cache Manager
class CacheManager:
    """SQLite-based cache for API responses."""
    
    def __init__(self, db_path: str = CACHE_DB):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    timestamp REAL
                )
            """)
            conn.commit()
    
    def get(self, key: str) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT value, timestamp FROM cache WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            if row:
                value, timestamp = row
                age_days = (time.time() - timestamp) / 86400
                if age_days < CACHE_TTL_DAYS:
                    return value
        return None
    
    def set(self, key: str, value: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, timestamp) VALUES (?, ?, ?)",
                (key, value, time.time())
            )
            conn.commit()


# API Clients
class LibrariesIOClient:
    """Client for Libraries.io API with burst fetch."""
    
    def __init__(self, api_key: str, cache: CacheManager):
        self.api_key = api_key
        self.cache = cache
        self.session = self._create_session()
    
    def _create_session(self):
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
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
        """Search packages using burst fetch strategy."""
        all_results = []
        bursts_needed = (max_results + BURST_SIZE - 1) // BURST_SIZE
        
        for burst_num in range(bursts_needed):
            remaining = max_results - len(all_results)
            this_burst_size = min(remaining, BURST_SIZE)
            
            logger.info(f"BURST {burst_num + 1}/{bursts_needed}: Fetching {this_burst_size} packages...")
            
            burst_results = self._fetch_burst_instant(query, this_burst_size, burst_num, progress_callback)
            all_results.extend(burst_results)
            
            if burst_num < bursts_needed - 1 and countdown_callback:
                countdown_callback(COOLDOWN_SECONDS)
        
        return all_results
    
    def _fetch_burst_instant(self, query: str, count: int, burst_offset: int, progress_callback: Optional[Callable] = None) -> List[PackageInfo]:
        """Fire 60 requests simultaneously."""
        requests_needed = min((count + PACKAGES_PER_REQUEST - 1) // PACKAGES_PER_REQUEST, REQUESTS_PER_BURST)
        results = []
        
        with ThreadPoolExecutor(max_workers=REQUESTS_PER_BURST) as executor:
            page_start = burst_offset * REQUESTS_PER_BURST
            futures = {
                executor.submit(self._fetch_single_page, query, page_start + i): i
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
            'page': page + 1,
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


class NPMRegistryClient:
    """Client for NPM Registry API."""
    
    def __init__(self):
        self.session = self._create_session()
    
    def _create_session(self):
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def enrich_package(self, package: PackageInfo) -> PackageInfo:
        """Enrich package with NPM Registry data."""
        try:
            url = f"{NPM_REGISTRY_BASE}/{package.name}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            latest_version = package.version
            if latest_version in data.get('versions', {}):
                version_data = data['versions'][latest_version]
                
                if 'dist' in version_data:
                    dist = version_data['dist']
                    package.file_count = dist.get('fileCount', 0)
                    package.unpacked_size = dist.get('unpackedSize', 0)
                
                package.dependencies = version_data.get('dependencies', {})
                package.dev_dependencies = version_data.get('devDependencies', {})
                package.peer_dependencies = version_data.get('peerDependencies', {})
                package.keywords = version_data.get('keywords', [])
                package.author = str(version_data.get('author', {}).get('name', ''))
            
            package.maintainers = data.get('maintainers', [])
            
            if 'time' in data:
                package.created_at = data['time'].get('created', '')
                package.last_published = data['time'].get('modified', '')
            
            package.npm_downloads_weekly = self._get_downloads(package.name, 'last-week')
            package.npm_downloads_monthly = self._get_downloads(package.name, 'last-month')
            package.enriched_npm = True
            
        except Exception as e:
            logger.error(f"Failed to enrich {package.name}: {e}")
        
        return package
    
    def _get_downloads(self, package_name: str, period: str) -> int:
        try:
            url = f"https://api.npmjs.org/downloads/point/{period}/{package_name}"
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            return response.json().get('downloads', 0)
        except:
            return 0


class UnpkgClient:
    """Client for unpkg.com to browse files."""
    
    def __init__(self):
        self.session = self._create_session()
    
    def _create_session(self):
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def get_file_tree(self, package_name: str, version: str) -> Optional[FileNode]:
        """Get file tree for a package version."""
        try:
            url = f"{UNPKG_BASE}/{package_name}@{version}/?meta"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            root = FileNode(path="/", type="directory")
            self._parse_tree(data, root)
            return root
        except Exception as e:
            logger.error(f"Failed to get file tree: {e}")
            return None
    
    def _parse_tree(self, data: Dict, parent: FileNode):
        """Recursively parse file tree."""
        if data.get('type') == 'directory':
            for file_data in data.get('files', []):
                node = FileNode(
                    path=file_data.get('path', ''),
                    type=file_data.get('type', 'file'),
                    size=file_data.get('size', 0)
                )
                parent.children.append(node)
                if node.type == 'directory':
                    self._parse_tree(file_data, node)
    
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


# Main Application
class NPMAnalyzerApp(tk.Tk):
    """Main NPM Analyzer Application."""
    
    def __init__(self):
        super().__init__()
        
        self.title("NPM Package Analyzer")
        self.geometry("1400x900")
        self.configure(bg=Theme.BG)
        
        # Data
        self.packages = []
        self.api_key = None
        self.cache = CacheManager()
        self.libs_client = None
        self.npm_client = NPMRegistryClient()
        self.unpkg_client = UnpkgClient()
        
        # Setup UI
        self._setup_ui()
        self._prompt_api_key()
    
    def _setup_ui(self):
        """Setup the UI components."""
        # Top bar
        top_frame = tk.Frame(self, bg=Theme.BG)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(top_frame, text="Search:", bg=Theme.BG, fg=Theme.FG).pack(side=tk.LEFT, padx=5)
        
        self.search_entry = tk.Entry(top_frame, width=40, bg=Theme.SECONDARY, fg=Theme.FG, insertbackground=Theme.FG)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<Return>', lambda e: self._on_search())
        
        self.search_btn = tk.Button(top_frame, text="Search", command=self._on_search, bg=Theme.ACCENT, fg=Theme.FG)
        self.search_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Label(top_frame, text="Max Results:", bg=Theme.BG, fg=Theme.FG).pack(side=tk.LEFT, padx=5)
        
        self.max_results_var = tk.StringVar(value="20000")
        max_results_entry = tk.Entry(top_frame, textvariable=self.max_results_var, width=10, bg=Theme.SECONDARY, fg=Theme.FG, insertbackground=Theme.FG)
        max_results_entry.pack(side=tk.LEFT, padx=5)
        
        self.export_btn = tk.Button(top_frame, text="Export JSON", command=self._export_json, bg=Theme.SECONDARY, fg=Theme.FG)
        self.export_btn.pack(side=tk.LEFT, padx=5)
        
        self.export_csv_btn = tk.Button(top_frame, text="Export CSV", command=self._export_csv, bg=Theme.SECONDARY, fg=Theme.FG)
        self.export_csv_btn.pack(side=tk.LEFT, padx=5)
        
        # Results table
        table_frame = tk.Frame(self, bg=Theme.BG)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
        scrollbar_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        
        columns = ('name', 'version', 'description', 'license', 'dependents')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', 
                                 yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)
        
        self.tree.heading('name', text='Name')
        self.tree.heading('version', text='Version')
        self.tree.heading('description', text='Description')
        self.tree.heading('license', text='License')
        self.tree.heading('dependents', text='Dependents')
        
        self.tree.column('name', width=200)
        self.tree.column('version', width=100)
        self.tree.column('description', width=400)
        self.tree.column('license', width=150)
        self.tree.column('dependents', width=100)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        scrollbar_y.grid(row=0, column=1, sticky='ns')
        scrollbar_x.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        self.tree.bind('<Double-Button-1>', self._on_package_double_click)
        
        # Status bar
        self.status_label = tk.Label(self, text="Ready", bg=Theme.SECONDARY, fg=Theme.FG, anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)
    
    def _prompt_api_key(self):
        """Prompt for Libraries.io API key."""
        dialog = tk.Toplevel(self)
        dialog.title("Libraries.io API Key")
        dialog.geometry("400x150")
        dialog.configure(bg=Theme.BG)
        dialog.transient(self)
        dialog.grab_set()
        
        tk.Label(dialog, text="Enter your Libraries.io API Key:", bg=Theme.BG, fg=Theme.FG).pack(pady=10)
        
        entry = tk.Entry(dialog, width=40, bg=Theme.SECONDARY, fg=Theme.FG, insertbackground=Theme.FG)
        entry.pack(pady=10)
        entry.focus()
        
        def save_key():
            key = entry.get().strip()
            if key:
                self.api_key = key
                self.libs_client = LibrariesIOClient(key, self.cache)
                dialog.destroy()
            else:
                messagebox.showwarning("Invalid Key", "Please enter a valid API key")
        
        entry.bind('<Return>', lambda e: save_key())
        tk.Button(dialog, text="Save", command=save_key, bg=Theme.ACCENT, fg=Theme.FG).pack(pady=10)
        
        self.wait_window(dialog)
    
    def _on_search(self):
        """Handle search button click."""
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Empty Query", "Please enter a search query")
            return
        
        try:
            max_results = int(self.max_results_var.get())
        except ValueError:
            messagebox.showwarning("Invalid Number", "Max results must be a number")
            return
        
        self.status_label.config(text=f"Searching for '{query}'...")
        self.search_btn.config(state=tk.DISABLED)
        
        threading.Thread(target=self._search_packages, args=(query, max_results), daemon=True).start()
    
    def _search_packages(self, query: str, max_results: int):
        """Search packages in background thread."""
        try:
            def progress_cb(completed, total):
                self.after(0, lambda: self.status_label.config(text=f"Fetching: {completed}/{total} requests..."))
            
            def countdown_cb(seconds):
                for i in range(seconds, 0, -1):
                    self.after(0, lambda s=i: self.status_label.config(text=f"⏳ Rate limit cooldown: {s}s..."))
                    time.sleep(1)
            
            self.packages = self.libs_client.search_packages_burst(query, max_results, progress_cb, countdown_cb)
            
            self.after(0, self._display_results)
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            self.after(0, lambda: messagebox.showerror("Search Error", str(e)))
        finally:
            self.after(0, lambda: self.search_btn.config(state=tk.NORMAL))
    
    def _display_results(self):
        """Display search results in table."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for pkg in self.packages:
            self.tree.insert('', tk.END, values=(
                pkg.name,
                pkg.version,
                pkg.description[:100],
                pkg.license,
                pkg.dependents_count
            ))
        
        self.status_label.config(text=f"Found {len(self.packages)} packages")
    
    def _on_package_double_click(self, event):
        """Handle double-click on package."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        package_name = item['values'][0]
        
        pkg = next((p for p in self.packages if p.name == package_name), None)
        if pkg:
            self._show_package_details(pkg)
    
    def _show_package_details(self, pkg: PackageInfo):
        """Show detailed package information."""
        dialog = tk.Toplevel(self)
        dialog.title(f"Package: {pkg.name}")
        dialog.geometry("800x600")
        dialog.configure(bg=Theme.BG)
        
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Info tab
        info_frame = tk.Frame(notebook, bg=Theme.BG)
        notebook.add(info_frame, text="Info")
        
        info_text = scrolledtext.ScrolledText(info_frame, bg=Theme.SECONDARY, fg=Theme.FG, wrap=tk.WORD)
        info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.status_label.config(text=f"Enriching {pkg.name}...")
        
        def enrich_and_display():
            enriched = self.npm_client.enrich_package(pkg)
            
            info = f"""
Name: {enriched.name}
Version: {enriched.version}
License: {enriched.license}
Description: {enriched.description}

Homepage: {enriched.homepage}
Repository: {enriched.repository_url}
NPM URL: {enriched.npm_url}

File Count: {enriched.file_count}
Unpacked Size: {enriched.unpacked_size:,} bytes
Dependents: {enriched.dependents_count:,}

Weekly Downloads: {enriched.npm_downloads_weekly:,}
Monthly Downloads: {enriched.npm_downloads_monthly:,}

Author: {enriched.author}
Keywords: {', '.join(enriched.keywords)}

Created: {enriched.created_at}
Last Published: {enriched.last_published}

Dependencies: {len(enriched.dependencies)}
Dev Dependencies: {len(enriched.dev_dependencies)}
Peer Dependencies: {len(enriched.peer_dependencies)}
"""
            self.after(0, lambda: info_text.insert('1.0', info))
            self.after(0, lambda: self.status_label.config(text="Ready"))
        
        threading.Thread(target=enrich_and_display, daemon=True).start()
        
        # Files tab
        files_frame = tk.Frame(notebook, bg=Theme.BG)
        notebook.add(files_frame, text="Files")
        
        file_tree = ttk.Treeview(files_frame, show='tree')
        file_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        def load_files():
            root_node = self.unpkg_client.get_file_tree(pkg.name, pkg.version)
            if root_node:
                self._populate_file_tree(file_tree, '', root_node)
        
        threading.Thread(target=load_files, daemon=True).start()
        
        # Links
        links_frame = tk.Frame(dialog, bg=Theme.BG)
        links_frame.pack(fill=tk.X, padx=10, pady=10)
        
        if pkg.npm_url:
            tk.Button(links_frame, text="Open NPM", command=lambda: webbrowser.open(pkg.npm_url), bg=Theme.ACCENT, fg=Theme.FG).pack(side=tk.LEFT, padx=5)
        if pkg.repository_url:
            tk.Button(links_frame, text="Open Repo", command=lambda: webbrowser.open(pkg.repository_url), bg=Theme.ACCENT, fg=Theme.FG).pack(side=tk.LEFT, padx=5)
        if pkg.homepage:
            tk.Button(links_frame, text="Open Homepage", command=lambda: webbrowser.open(pkg.homepage), bg=Theme.ACCENT, fg=Theme.FG).pack(side=tk.LEFT, padx=5)
    
    def _populate_file_tree(self, tree_widget, parent, node: FileNode):
        """Populate file tree widget."""
        icon = "📁" if node.type == 'directory' else "📄"
        item = tree_widget.insert(parent, tk.END, text=f"{icon} {os.path.basename(node.path)}")
        for child in node.children:
            self._populate_file_tree(tree_widget, item, child)
    
    def _export_json(self):
        """Export results to JSON."""
        if not self.packages:
            messagebox.showwarning("No Data", "No packages to export")
            return
        
        filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if filename:
            with open(filename, 'w') as f:
                json.dump([asdict(p) for p in self.packages], f, indent=2)
            messagebox.showinfo("Success", f"Exported {len(self.packages)} packages to {filename}")
    
    def _export_csv(self):
        """Export results to CSV."""
        if not self.packages:
            messagebox.showwarning("No Data", "No packages to export")
            return
        
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if filename:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Name', 'Version', 'Description', 'License', 'Dependents', 'Homepage', 'Repository'])
                for p in self.packages:
                    writer.writerow([p.name, p.version, p.description, p.license, p.dependents_count, p.homepage, p.repository_url])
            messagebox.showinfo("Success", f"Exported {len(self.packages)} packages to {filename}")


if __name__ == "__main__":
    app = NPMAnalyzerApp()
    app.mainloop()
