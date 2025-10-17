"""Main application UI."""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import logging
from typing import Optional, List
from npm_discovery.ui.theme import DarkTheme
from npm_discovery.services.discovery import DiscoveryService
from npm_discovery.models import SearchResult, PackageInfo

logger = logging.getLogger(__name__)


class NPMDiscoveryApp:
    """Main NPM Discovery application window."""
    
    def __init__(self):
        """Initialize the application."""
        self.root = tk.Tk()
        self.root.title("NPM Package Discovery")
        self.root.geometry("1200x800")
        self.root.configure(bg=DarkTheme.BG)
        
        # Service
        try:
            self.service = DiscoveryService()
        except ValueError as e:
            messagebox.showerror(
                "Configuration Error",
                f"Missing configuration: {e}\n\nPlease set LIBRARIES_IO_API_KEY environment variable."
            )
            self.root.destroy()
            return
        
        # State
        self.search_results: List[SearchResult] = []
        self.current_package: Optional[PackageInfo] = None
        
        # Build UI
        self._setup_styles()
        self._create_widgets()
    
    def _setup_styles(self):
        """Configure ttk styles for dark theme."""
        style = ttk.Style()
        style.theme_use('default')
        
        # Configure colors
        style.configure('Dark.TFrame', background=DarkTheme.BG)
        style.configure('Dark.TLabel',
                       background=DarkTheme.BG,
                       foreground=DarkTheme.TEXT)
        style.configure('Dark.TButton',
                       background=DarkTheme.BG_SECONDARY,
                       foreground=DarkTheme.TEXT)
        style.map('Dark.TButton',
                 background=[('active', DarkTheme.ACCENT)])
    
    def _create_widgets(self):
        """Create all UI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Search bar
        search_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.search_entry = tk.Entry(
            search_frame,
            bg=DarkTheme.BG_INPUT,
            fg=DarkTheme.TEXT,
            insertbackground=DarkTheme.TEXT,
            relief=tk.FLAT,
            font=('Arial', 12)
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 10))
        self.search_entry.bind('<Return>', lambda e: self.search())
        
        search_btn = tk.Button(
            search_frame,
            text="Search",
            command=self.search,
            bg=DarkTheme.ACCENT,
            fg=DarkTheme.TEXT,
            relief=tk.FLAT,
            font=('Arial', 11, 'bold'),
            cursor='hand2'
        )
        search_btn.pack(side=tk.RIGHT, ipadx=20, ipady=8)
        
        # Content area (paned window)
        paned = tk.PanedWindow(
            main_frame,
            orient=tk.HORIZONTAL,
            bg=DarkTheme.BG,
            sashwidth=2,
            sashrelief=tk.FLAT
        )
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Left panel: Search results
        left_frame = tk.Frame(paned, bg=DarkTheme.BG_SECONDARY)
        paned.add(left_frame, width=400)
        
        ttk.Label(left_frame, text="Search Results", style='Dark.TLabel',
                 font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Results listbox
        self.results_listbox = tk.Listbox(
            left_frame,
            bg=DarkTheme.BG_TERTIARY,
            fg=DarkTheme.TEXT,
            selectbackground=DarkTheme.SELECTION,
            selectforeground=DarkTheme.TEXT,
            relief=tk.FLAT,
            font=('Arial', 10),
            activestyle='none'
        )
        self.results_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.results_listbox.bind('<<ListboxSelect>>', self.on_package_select)
        
        # Right panel: Package details
        right_frame = tk.Frame(paned, bg=DarkTheme.BG_SECONDARY)
        paned.add(right_frame)
        
        ttk.Label(right_frame, text="Package Details", style='Dark.TLabel',
                 font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Details text area
        self.details_text = scrolledtext.ScrolledText(
            right_frame,
            bg=DarkTheme.BG_TERTIARY,
            fg=DarkTheme.TEXT,
            insertbackground=DarkTheme.TEXT,
            relief=tk.FLAT,
            font=('Courier', 10),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.details_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # File tree button
        tree_btn = tk.Button(
            right_frame,
            text="Show File Tree",
            command=self.show_file_tree,
            bg=DarkTheme.BG_HOVER,
            fg=DarkTheme.TEXT,
            relief=tk.FLAT,
            font=('Arial', 10),
            cursor='hand2'
        )
        tree_btn.pack(pady=(0, 10), ipadx=15, ipady=5)
        
        # Status bar
        self.status_label = ttk.Label(
            main_frame,
            text="Ready",
            style='Dark.TLabel',
            font=('Arial', 9)
        )
        self.status_label.pack(fill=tk.X, pady=(10, 0))
    
    def search(self):
        """Perform package search."""
        query = self.search_entry.get().strip()
        if not query:
            return
        
        self.set_status(f"Searching for: {query}")
        self.results_listbox.delete(0, tk.END)
        
        # Run in background thread
        def do_search():
            try:
                results = self.service.search_packages(query, per_page=50)
                self.search_results = results
                
                # Update UI in main thread
                self.root.after(0, lambda: self._update_results(results))
            except Exception as e:
                logger.exception("Search failed")
                self.root.after(0, lambda: self.set_status(f"Error: {e}"))
        
        threading.Thread(target=do_search, daemon=True).start()
    
    def _update_results(self, results: List[SearchResult]):
        """Update results listbox."""
        for result in results:
            self.results_listbox.insert(tk.END, f"{result.name} (v{result.version})")
        
        self.set_status(f"Found {len(results)} packages")
    
    def on_package_select(self, event):
        """Handle package selection."""
        selection = self.results_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index >= len(self.search_results):
            return
        
        result = self.search_results[index]
        self.set_status(f"Loading details for: {result.name}")
        
        # Run in background thread
        def load_details():
            try:
                package = self.service.get_package_details(result.name)
                self.current_package = package
                
                # Update UI in main thread
                if package:
                    self.root.after(0, lambda: self._display_details(package))
            except Exception as e:
                logger.exception("Failed to load package details")
                self.root.after(0, lambda: self.set_status(f"Error: {e}"))
        
        threading.Thread(target=load_details, daemon=True).start()
    
    def _display_details(self, package: PackageInfo):
        """Display package details."""
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        
        details = f"""
Name: {package.name}
Version: {package.version}
Description: {package.description}

Author: {package.author}
License: {package.license}
Homepage: {package.homepage}
Repository: {package.repository}

Downloads (last month): {package.downloads_last_month:,}
Dependencies: {package.dependencies_count}
Dev Dependencies: {package.dev_dependencies_count}
Total Versions: {package.total_versions}
Maintainers: {package.maintainers_count}

Published: {package.published_date}
Modified: {package.modified_date}
"""
        
        if package.keywords:
            details += f"\nKeywords: {', '.join(package.keywords[:15])}\n"
        
        if package.dependencies:
            details += f"\nDependencies:\n"
            for dep in package.dependencies[:10]:
                details += f"  - {dep}\n"
        
        self.details_text.insert(1.0, details)
        self.details_text.config(state=tk.DISABLED)
        self.set_status(f"Loaded details for: {package.name}")
    
    def show_file_tree(self):
        """Show file tree in popup window."""
        if not self.current_package:
            messagebox.showinfo("Info", "Please select a package first")
            return
        
        self.set_status(f"Fetching file tree for: {self.current_package.name}")
        
        def load_tree():
            try:
                tree = self.service.get_file_tree(
                    self.current_package.name,
                    self.current_package.version
                )
                self.root.after(0, lambda: self._display_tree(tree))
            except Exception as e:
                logger.exception("Failed to load file tree")
                self.root.after(0, lambda: self.set_status(f"Error: {e}"))
        
        threading.Thread(target=load_tree, daemon=True).start()
    
    def _display_tree(self, tree: dict):
        """Display file tree in popup."""
        window = tk.Toplevel(self.root)
        window.title(f"File Tree: {tree.get('name', 'Package')}")
        window.geometry("600x700")
        window.configure(bg=DarkTheme.BG)
        
        tree_text = scrolledtext.ScrolledText(
            window,
            bg=DarkTheme.BG_TERTIARY,
            fg=DarkTheme.TEXT,
            font=('Courier', 9),
            wrap=tk.NONE
        )
        tree_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Format tree
        output = f"Package: {tree.get('name')} v{tree.get('version')}\n"
        output += f"Total Files: {tree.get('file_count', 0)}\n\n"
        
        files = tree.get('files', {})
        output += self._format_tree(files)
        
        tree_text.insert(1.0, output)
        tree_text.config(state=tk.DISABLED)
        self.set_status("File tree loaded")
    
    def _format_tree(self, node: dict, prefix: str = "", is_last: bool = True) -> str:
        """Format tree structure for display."""
        output = ""
        items = list(node.items())
        
        for i, (name, value) in enumerate(items):
            is_last_item = (i == len(items) - 1)
            connector = "└── " if is_last_item else "├── "
            
            if isinstance(value, dict) and 'type' in value:
                # File node
                size = value.get('size', 0)
                output += f"{prefix}{connector}{name} ({size} bytes)\n"
            else:
                # Directory node
                output += f"{prefix}{connector}{name}/\n"
                extension = "    " if is_last_item else "│   "
                output += self._format_tree(value, prefix + extension, is_last_item)
        
        return output
    
    def set_status(self, message: str):
        """Update status bar."""
        self.status_label.config(text=message)
        logger.info(message)
    
    def run(self):
        """Start the application."""
        self.root.mainloop()


def main():
    """Application entry point."""
    app = NPMDiscoveryApp()
    app.run()


if __name__ == "__main__":
    main()

