"""Custom widgets for the UI."""
import tkinter as tk
from tkinter import ttk, scrolledtext
from npm_discovery.ui.theme import DarkTheme


class SearchFilters(ttk.Frame):
    """Advanced search filters widget."""
    
    def __init__(self, parent, on_filter_change=None):
        """Initialize filters.
        
        Args:
            parent: Parent widget.
            on_filter_change: Callback for filter changes.
        """
        super().__init__(parent, style='Dark.TFrame')
        self.on_filter_change = on_filter_change
        
        # Min stars filter
        ttk.Label(self, text="Min Stars:", style='Dark.TLabel').grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.min_stars_var = tk.StringVar(value="0")
        self.min_stars_entry = tk.Entry(
            self,
            textvariable=self.min_stars_var,
            bg=DarkTheme.BG_INPUT,
            fg=DarkTheme.TEXT,
            width=10
        )
        self.min_stars_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Min downloads filter
        ttk.Label(self, text="Min Downloads:", style='Dark.TLabel').grid(
            row=1, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.min_downloads_var = tk.StringVar(value="0")
        self.min_downloads_entry = tk.Entry(
            self,
            textvariable=self.min_downloads_var,
            bg=DarkTheme.BG_INPUT,
            fg=DarkTheme.TEXT,
            width=10
        )
        self.min_downloads_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # License filter
        ttk.Label(self, text="License:", style='Dark.TLabel').grid(
            row=2, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.license_var = tk.StringVar(value="Any")
        licenses = ["Any", "MIT", "Apache-2.0", "GPL-3.0", "BSD-3-Clause", "ISC"]
        self.license_combo = ttk.Combobox(
            self,
            textvariable=self.license_var,
            values=licenses,
            state="readonly",
            width=15
        )
        self.license_combo.grid(row=2, column=1, padx=5, pady=5)
        
        # Sort by
        ttk.Label(self, text="Sort By:", style='Dark.TLabel').grid(
            row=3, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.sort_var = tk.StringVar(value="Rank")
        sort_options = ["Rank", "Stars", "Downloads", "Name"]
        self.sort_combo = ttk.Combobox(
            self,
            textvariable=self.sort_var,
            values=sort_options,
            state="readonly",
            width=15
        )
        self.sort_combo.grid(row=3, column=1, padx=5, pady=5)
        
        # Apply button
        apply_btn = tk.Button(
            self,
            text="Apply Filters",
            command=self._apply_filters,
            bg=DarkTheme.ACCENT,
            fg=DarkTheme.TEXT,
            relief=tk.FLAT
        )
        apply_btn.grid(row=4, column=0, columnspan=2, pady=10)
    
    def _apply_filters(self):
        """Apply filters and notify callback."""
        if self.on_filter_change:
            filters = self.get_filters()
            self.on_filter_change(filters)
    
    def get_filters(self):
        """Get current filter values.
        
        Returns:
            Dictionary of filter values.
        """
        return {
            "min_stars": int(self.min_stars_var.get() or 0),
            "min_downloads": int(self.min_downloads_var.get() or 0),
            "license": self.license_var.get(),
            "sort_by": self.sort_var.get(),
        }


class MarkdownViewer(tk.Toplevel):
    """Simple markdown viewer window."""
    
    def __init__(self, parent, title, content):
        """Initialize viewer.
        
        Args:
            parent: Parent widget.
            title: Window title.
            content: Markdown content to display.
        """
        super().__init__(parent)
        self.title(title)
        self.geometry("800x600")
        self.configure(bg=DarkTheme.BG)
        
        # Text widget with scrollbar
        self.text = scrolledtext.ScrolledText(
            self,
            bg=DarkTheme.BG_TERTIARY,
            fg=DarkTheme.TEXT,
            font=('Courier', 10),
            wrap=tk.WORD,
            padx=20,
            pady=20
        )
        self.text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Display content
        self._render_markdown(content)
        self.text.config(state=tk.DISABLED)
    
    def _render_markdown(self, content):
        """Simple markdown rendering.
        
        Args:
            content: Markdown text.
        """
        # Basic rendering - headers, bold, code blocks
        lines = content.split('\n')
        
        for line in lines:
            # Headers
            if line.startswith('# '):
                self.text.insert(tk.END, line[2:] + '\n', 'h1')
            elif line.startswith('## '):
                self.text.insert(tk.END, line[3:] + '\n', 'h2')
            elif line.startswith('### '):
                self.text.insert(tk.END, line[4:] + '\n', 'h3')
            # Code blocks
            elif line.startswith('```'):
                continue
            # Regular text
            else:
                self.text.insert(tk.END, line + '\n')
        
        # Configure tags
        self.text.tag_config('h1', font=('Arial', 16, 'bold'), foreground=DarkTheme.ACCENT)
        self.text.tag_config('h2', font=('Arial', 14, 'bold'), foreground=DarkTheme.ACCENT)
        self.text.tag_config('h3', font=('Arial', 12, 'bold'), foreground=DarkTheme.TEXT_SECONDARY)


class PackageComparison(tk.Toplevel):
    """Package comparison window."""
    
    def __init__(self, parent, packages):
        """Initialize comparison.
        
        Args:
            parent: Parent widget.
            packages: List of PackageInfo objects to compare.
        """
        super().__init__(parent)
        self.title("Package Comparison")
        self.geometry("1000x600")
        self.configure(bg=DarkTheme.BG)
        
        # Create comparison table
        frame = ttk.Frame(self, style='Dark.TFrame')
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Headers
        metrics = [
            "Metric",
            *[pkg.name for pkg in packages]
        ]
        
        for col, text in enumerate(metrics):
            label = tk.Label(
                frame,
                text=text,
                bg=DarkTheme.BG_SECONDARY,
                fg=DarkTheme.TEXT,
                font=('Arial', 11, 'bold'),
                padx=10,
                pady=10
            )
            label.grid(row=0, column=col, sticky=tk.EW, padx=1, pady=1)
        
        # Metrics to compare
        comparison_metrics = [
            ("Version", lambda p: p.version),
            ("Downloads/Month", lambda p: f"{p.downloads_last_month:,}"),
            ("Dependencies", lambda p: str(p.dependencies_count)),
            ("Dev Dependencies", lambda p: str(p.dev_dependencies_count)),
            ("Total Versions", lambda p: str(p.total_versions)),
            ("License", lambda p: p.license),
            ("Maintainers", lambda p: str(p.maintainers_count)),
        ]
        
        for row, (metric_name, metric_func) in enumerate(comparison_metrics, start=1):
            # Metric name
            label = tk.Label(
                frame,
                text=metric_name,
                bg=DarkTheme.BG_TERTIARY,
                fg=DarkTheme.TEXT_SECONDARY,
                font=('Arial', 10),
                padx=10,
                pady=8,
                anchor=tk.W
            )
            label.grid(row=row, column=0, sticky=tk.EW, padx=1, pady=1)
            
            # Values for each package
            for col, pkg in enumerate(packages, start=1):
                value = metric_func(pkg)
                label = tk.Label(
                    frame,
                    text=value,
                    bg=DarkTheme.BG_TERTIARY,
                    fg=DarkTheme.TEXT,
                    font=('Arial', 10),
                    padx=10,
                    pady=8
                )
                label.grid(row=row, column=col, sticky=tk.EW, padx=1, pady=1)
        
        # Configure column weights
        for col in range(len(packages) + 1):
            frame.columnconfigure(col, weight=1)

