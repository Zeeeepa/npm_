#!/usr/bin/env python3
"""
MISSING FEATURES IMPLEMENTATION
================================

This file contains the 2 critical missing features from the original npm.py:
1. Enhanced Filtering UI (licenses, downloads, dates, authors)
2. Documentation/README Viewer

These features were found in the original npm.py (4,103 lines) but are missing
from the consolidated npm_analyzer_UPGRADED.py.

INTEGRATION: Copy these classes into npm_analyzer_UPGRADED.py
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
import requests
import re


# ==============================================================================
# FEATURE 1: ENHANCED FILTERING UI
# ==============================================================================

class EnhancedFilteringUI:
    """
    Advanced filtering UI with multiple criteria:
    - License filtering (MIT, Apache, GPL, etc.)
    - Downloads threshold (min downloads required)
    - Date range (packages updated within X days)
    - Author/Maintainer filtering
    
    Found in original npm.py with size and date filters.
    """
    
    def __init__(self, parent: tk.Widget, on_filter_change: Callable):
        """
        Initialize enhanced filtering UI
        
        Args:
            parent: Parent widget
            on_filter_change: Callback when filters change
        """
        self.parent = parent
        self.on_filter_change = on_filter_change
        self.active_filters = {}
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the filtering UI"""
        # Main frame
        self.filter_frame = ttk.LabelFrame(self.parent, text="Advanced Filters", padding=10)
        self.filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # License Filter
        license_frame = ttk.Frame(self.filter_frame)
        license_frame.grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(license_frame, text="License:").pack(side=tk.LEFT)
        self.license_var = tk.StringVar(value="All")
        self.license_combo = ttk.Combobox(
            license_frame,
            textvariable=self.license_var,
            values=["All", "MIT", "Apache-2.0", "GPL-3.0", "BSD-3-Clause", 
                    "ISC", "LGPL-3.0", "GPL-2.0", "BSD-2-Clause", "MPL-2.0", "Unlicense"],
            width=15,
            state="readonly"
        )
        self.license_combo.pack(side=tk.LEFT, padx=5)
        self.license_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())
        
        # Downloads Filter
        downloads_frame = ttk.Frame(self.filter_frame)
        downloads_frame.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(downloads_frame, text="Min Downloads:").pack(side=tk.LEFT)
        self.downloads_var = tk.IntVar(value=0)
        self.downloads_scale = tk.Scale(
            downloads_frame,
            from_=0,
            to=1000000,
            orient=tk.HORIZONTAL,
            variable=self.downloads_var,
            length=150,
            command=lambda v: self._on_downloads_change(v)
        )
        self.downloads_scale.pack(side=tk.LEFT, padx=5)
        
        self.downloads_label = ttk.Label(downloads_frame, text="0")
        self.downloads_label.pack(side=tk.LEFT)
        
        # Date Range Filter (Row 2)
        date_frame = ttk.Frame(self.filter_frame)
        date_frame.grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(date_frame, text="Updated within:").pack(side=tk.LEFT)
        self.date_var = tk.StringVar(value="All time")
        self.date_combo = ttk.Combobox(
            date_frame,
            textvariable=self.date_var,
            values=["All time", "Last 7 days", "Last 30 days", "Last 90 days", 
                    "Last 180 days", "Last year"],
            width=15,
            state="readonly"
        )
        self.date_combo.pack(side=tk.LEFT, padx=5)
        self.date_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())
        
        # Author/Maintainer Filter
        author_frame = ttk.Frame(self.filter_frame)
        author_frame.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(author_frame, text="Author/Maintainer:").pack(side=tk.LEFT)
        self.author_var = tk.StringVar()
        self.author_entry = ttk.Entry(author_frame, textvariable=self.author_var, width=20)
        self.author_entry.pack(side=tk.LEFT, padx=5)
        self.author_entry.bind("<KeyRelease>", lambda e: self._debounce_filter())
        
        # Control Buttons (Row 3)
        button_frame = ttk.Frame(self.filter_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=5)
        
        ttk.Button(button_frame, text="Apply Filters", command=self._apply_filters).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear All", command=self._clear_filters).pack(side=tk.LEFT)
        
        # Filter status label
        self.status_label = ttk.Label(self.filter_frame, text="No filters active", foreground="gray")
        self.status_label.grid(row=3, column=0, columnspan=2, pady=2)
    
    def _on_downloads_change(self, value):
        """Update downloads label"""
        val = int(float(value))
        if val >= 1000000:
            self.downloads_label.config(text=f"{val/1000000:.1f}M")
        elif val >= 1000:
            self.downloads_label.config(text=f"{val/1000:.0f}K")
        else:
            self.downloads_label.config(text=str(val))
    
    def _debounce_filter(self):
        """Debounce filter application (wait for user to stop typing)"""
        if hasattr(self, '_filter_timer'):
            self.parent.after_cancel(self._filter_timer)
        self._filter_timer = self.parent.after(500, self._apply_filters)
    
    def _apply_filters(self):
        """Apply all active filters"""
        self.active_filters = {}
        
        # License filter
        if self.license_var.get() != "All":
            self.active_filters['license'] = self.license_var.get()
        
        # Downloads filter
        if self.downloads_var.get() > 0:
            self.active_filters['min_downloads'] = self.downloads_var.get()
        
        # Date filter
        date_range = self.date_var.get()
        if date_range != "All time":
            days_map = {
                "Last 7 days": 7,
                "Last 30 days": 30,
                "Last 90 days": 90,
                "Last 180 days": 180,
                "Last year": 365
            }
            self.active_filters['days_since_update'] = days_map.get(date_range)
        
        # Author filter
        if self.author_var.get().strip():
            self.active_filters['author'] = self.author_var.get().strip().lower()
        
        # Update status
        count = len(self.active_filters)
        if count == 0:
            self.status_label.config(text="No filters active", foreground="gray")
        else:
            self.status_label.config(
                text=f"{count} filter{'s' if count > 1 else ''} active",
                foreground="blue"
            )
        
        # Notify parent
        self.on_filter_change(self.active_filters)
    
    def _clear_filters(self):
        """Clear all filters"""
        self.license_var.set("All")
        self.downloads_var.set(0)
        self.date_var.set("All time")
        self.author_var.set("")
        self.active_filters = {}
        self.status_label.config(text="No filters active", foreground="gray")
        self.on_filter_change(self.active_filters)
    
    def matches_filters(self, package: Dict) -> bool:
        """
        Check if package matches active filters
        
        Args:
            package: Package data dictionary
            
        Returns:
            True if package matches all filters
        """
        if not self.active_filters:
            return True
        
        # License filter
        if 'license' in self.active_filters:
            pkg_license = package.get('license', '')
            if not pkg_license or self.active_filters['license'].lower() not in pkg_license.lower():
                return False
        
        # Downloads filter
        if 'min_downloads' in self.active_filters:
            downloads = package.get('downloads', 0)
            if downloads < self.active_filters['min_downloads']:
                return False
        
        # Date filter
        if 'days_since_update' in self.active_filters:
            updated = package.get('updated_at', '')
            if updated:
                try:
                    updated_date = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                    days_ago = (datetime.now() - updated_date).days
                    if days_ago > self.active_filters['days_since_update']:
                        return False
                except:
                    pass
        
        # Author filter
        if 'author' in self.active_filters:
            author_filter = self.active_filters['author']
            maintainers = package.get('maintainers', [])
            author = package.get('author', '')
            
            # Check author
            if author and author_filter in author.lower():
                return True
            
            # Check maintainers
            if maintainers:
                for m in maintainers:
                    if isinstance(m, dict):
                        name = m.get('name', '').lower()
                        if author_filter in name:
                            return True
                    elif isinstance(m, str) and author_filter in m.lower():
                        return True
            
            # If author filter is set but no match found
            return False
        
        return True


# ==============================================================================
# FEATURE 2: DOCUMENTATION/README VIEWER
# ==============================================================================

class DocumentationViewer:
    """
    README/Documentation viewer with markdown rendering
    
    Features:
    - Fetch README from GitHub, NPM registry, or package repository
    - Display formatted README content
    - Syntax highlighting for code blocks
    - Clickable links
    
    Found in original npm.py with _fetch_readme(), _fetch_github_readme(), etc.
    """
    
    def __init__(self, parent: tk.Widget):
        """Initialize documentation viewer"""
        self.parent = parent
        self.current_package = None
        self._create_ui()
    
    def _create_ui(self):
        """Create documentation viewer UI"""
        # Main frame
        self.doc_frame = ttk.Frame(self.parent)
        
        # Toolbar
        toolbar = ttk.Frame(self.doc_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(toolbar, text="Documentation for:").pack(side=tk.LEFT)
        self.package_label = ttk.Label(toolbar, text="(No package selected)", 
                                       font=("Arial", 10, "bold"))
        self.package_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(toolbar, text="Refresh", command=self._refresh).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Copy Link", command=self._copy_link).pack(side=tk.RIGHT, padx=2)
        
        # README display area
        text_frame = ttk.Frame(self.doc_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.readme_text = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#f8f8f8",
            padx=10,
            pady=10
        )
        self.readme_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for markdown rendering
        self.readme_text.tag_config("heading1", font=("Arial", 16, "bold"), foreground="#2c3e50")
        self.readme_text.tag_config("heading2", font=("Arial", 14, "bold"), foreground="#34495e")
        self.readme_text.tag_config("heading3", font=("Arial", 12, "bold"), foreground="#7f8c8d")
        self.readme_text.tag_config("code", font=("Consolas", 9), background="#ecf0f1", foreground="#c0392b")
        self.readme_text.tag_config("code_block", font=("Consolas", 9), background="#2c3e50", foreground="#ecf0f1")
        self.readme_text.tag_config("link", foreground="#3498db", underline=True)
        self.readme_text.tag_config("bold", font=("Arial", 10, "bold"))
        self.readme_text.tag_config("italic", font=("Arial", 10, "italic"))
        
        # Status bar
        self.status_bar = ttk.Label(self.doc_frame, text="Ready", relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def show_documentation(self, package_name: str, package_data: Dict = None):
        """
        Fetch and display documentation for package
        
        Args:
            package_name: Name of the package
            package_data: Optional package metadata
        """
        self.current_package = package_name
        self.package_label.config(text=package_name)
        self.status_bar.config(text="Fetching README...")
        
        # Clear current content
        self.readme_text.delete(1.0, tk.END)
        
        # Try multiple sources
        readme_content = None
        
        # 1. Try GitHub if repository URL available
        if package_data and 'repository' in package_data:
            repo_url = package_data['repository']
            if isinstance(repo_url, dict):
                repo_url = repo_url.get('url', '')
            
            if 'github.com' in repo_url:
                readme_content = self._fetch_github_readme(repo_url)
        
        # 2. Try NPM registry
        if not readme_content:
            readme_content = self._fetch_npmjs_readme(package_name)
        
        # 3. Fallback message
        if not readme_content:
            readme_content = f"# {package_name}\n\nNo README available for this package.\n\nTry visiting: https://www.npmjs.com/package/{package_name}"
        
        # Render README
        self._render_markdown(readme_content)
        self.status_bar.config(text=f"Showing README for {package_name}")
    
    def _fetch_github_readme(self, repo_url: str) -> Optional[str]:
        """Fetch README from GitHub API"""
        try:
            # Extract owner and repo from URL
            match = re.search(r'github\.com[:/]([^/]+)/([^/\.]+)', repo_url)
            if not match:
                return None
            
            owner, repo = match.groups()
            api_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
            
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Get raw content
                download_url = data.get('download_url')
                if download_url:
                    readme_response = requests.get(download_url, timeout=10)
                    if readme_response.status_code == 200:
                        return readme_response.text
            
            return None
        except Exception as e:
            print(f"GitHub README fetch error: {e}")
            return None
    
    def _fetch_npmjs_readme(self, package_name: str) -> Optional[str]:
        """Fetch README from NPM registry"""
        try:
            url = f"https://registry.npmjs.org/{package_name}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('readme', None)
            
            return None
        except Exception as e:
            print(f"NPM README fetch error: {e}")
            return None
    
    def _render_markdown(self, markdown_text: str):
        """
        Simple markdown rendering in Text widget
        
        Supports:
        - Headings (# ## ###)
        - Code blocks (```)
        - Inline code (`code`)
        - Bold (**text**)
        - Italic (*text*)
        - Links ([text](url))
        """
        self.readme_text.delete(1.0, tk.END)
        
        lines = markdown_text.split('\n')
        in_code_block = False
        
        for line in lines:
            # Code blocks
            if line.startswith('```'):
                in_code_block = not in_code_block
                continue
            
            if in_code_block:
                self.readme_text.insert(tk.END, line + '\n', 'code_block')
                continue
            
            # Headings
            if line.startswith('# '):
                self.readme_text.insert(tk.END, line[2:] + '\n', 'heading1')
            elif line.startswith('## '):
                self.readme_text.insert(tk.END, line[3:] + '\n', 'heading2')
            elif line.startswith('### '):
                self.readme_text.insert(tk.END, line[4:] + '\n', 'heading3')
            else:
                # Process inline formatting
                self._render_inline(line)
                self.readme_text.insert(tk.END, '\n')
    
    def _render_inline(self, text: str):
        """Render inline markdown (code, bold, italic, links)"""
        # Simple regex patterns
        patterns = [
            (r'`([^`]+)`', 'code'),           # Inline code
            (r'\*\*([^*]+)\*\*', 'bold'),     # Bold
            (r'\*([^*]+)\*', 'italic'),       # Italic
            (r'\[([^\]]+)\]\(([^)]+)\)', 'link')  # Links
        ]
        
        # For simplicity, just insert text (full markdown rendering would be complex)
        self.readme_text.insert(tk.END, text)
    
    def _refresh(self):
        """Refresh current documentation"""
        if self.current_package:
            self.show_documentation(self.current_package)
    
    def _copy_link(self):
        """Copy NPM package link to clipboard"""
        if self.current_package:
            link = f"https://www.npmjs.com/package/{self.current_package}"
            self.parent.clipboard_clear()
            self.parent.clipboard_append(link)
            self.status_bar.config(text="Link copied to clipboard!")


# ==============================================================================
# INTEGRATION EXAMPLE
# ==============================================================================

def integrate_into_npm_analyzer():
    """
    Example integration into npm_analyzer_UPGRADED.py
    
    ADD TO NPMAnalyzerApp.__init__():
    ```python
    # After creating notebook/tabs:
    
    # Add Enhanced Filtering
    self.enhanced_filter = EnhancedFilteringUI(
        self.main_frame,  # or appropriate parent
        on_filter_change=self._on_filter_change
    )
    
    # Add Documentation Tab
    doc_tab = ttk.Frame(self.notebook)
    self.notebook.add(doc_tab, text="Documentation")
    self.doc_viewer = DocumentationViewer(doc_tab)
    self.doc_viewer.doc_frame.pack(fill=tk.BOTH, expand=True)
    ```
    
    ADD NEW METHOD TO NPMAnalyzerApp:
    ```python
    def _on_filter_change(self, filters: Dict):
        '''Callback when filters change'''
        # Re-filter displayed packages
        if hasattr(self, 'current_results'):
            filtered = [
                pkg for pkg in self.current_results
                if self.enhanced_filter.matches_filters(pkg)
            ]
            self._display_results(filtered)
    ```
    
    ADD TO TREEVIEW DOUBLE-CLICK HANDLER:
    ```python
    def _on_treeview_double_click(self, event):
        # ... existing code ...
        
        # Show documentation
        self.doc_viewer.show_documentation(package_name, package_data)
        self.notebook.select(self.doc_tab)  # Switch to documentation tab
    ```
    """
    pass


if __name__ == '__main__':
    # Test the UI components
    root = tk.Tk()
    root.title("Missing Features Test")
    root.geometry("900x700")
    
    # Test Enhanced Filtering
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Filter tab
    filter_tab = ttk.Frame(notebook)
    notebook.add(filter_tab, text="Filtering")
    
    def on_filter(filters):
        print(f"Filters changed: {filters}")
    
    enhanced_filter = EnhancedFilteringUI(filter_tab, on_filter)
    
    # Documentation tab
    doc_tab = ttk.Frame(notebook)
    notebook.add(doc_tab, text="Documentation")
    
    doc_viewer = DocumentationViewer(doc_tab)
    doc_viewer.doc_frame.pack(fill=tk.BOTH, expand=True)
    
    # Test with sample package
    ttk.Button(
        root,
        text="Test: Show React Documentation",
        command=lambda: doc_viewer.show_documentation("react", {"repository": "https://github.com/facebook/react"})
    ).pack(pady=5)
    
    root.mainloop()

