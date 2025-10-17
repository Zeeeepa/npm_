"""Settings dialog."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from npm.ui.theme import DarkTheme
from npm.config import get_config
import os


class SettingsDialog(tk.Toplevel):
    """Settings configuration dialog."""
    
    def __init__(self, parent):
        """Initialize settings dialog.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self.title("Settings")
        self.geometry("600x500")
        self.configure(bg=DarkTheme.BG)
        self.resizable(False, False)
        
        # Load current config
        self.config = get_config()
        
        # Create UI
        self._create_widgets()
        
        # Make modal
        self.transient(parent)
        self.grab_set()
    
    def _create_widgets(self):
        """Create dialog widgets."""
        # Main frame
        main_frame = ttk.Frame(self, style='Dark.TFrame', padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="Application Settings",
            bg=DarkTheme.BG,
            fg=DarkTheme.TEXT,
            font=('Arial', 14, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Settings sections
        self._create_api_section(main_frame)
        self._create_cache_section(main_frame)
        self._create_download_section(main_frame)
        
        # Buttons
        btn_frame = tk.Frame(main_frame, bg=DarkTheme.BG)
        btn_frame.pack(pady=20)
        
        save_btn = tk.Button(
            btn_frame,
            text="Save",
            command=self._save_settings,
            bg=DarkTheme.ACCENT,
            fg=DarkTheme.TEXT,
            relief=tk.FLAT,
            font=('Arial', 10, 'bold'),
            cursor='hand2',
            padx=20,
            pady=8
        )
        save_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            bg=DarkTheme.BG_HOVER,
            fg=DarkTheme.TEXT,
            relief=tk.FLAT,
            font=('Arial', 10),
            cursor='hand2',
            padx=20,
            pady=8
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
    
    def _create_api_section(self, parent):
        """Create API settings section."""
        section = tk.LabelFrame(
            parent,
            text="API Configuration",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT,
            font=('Arial', 11, 'bold'),
            padx=10,
            pady=10
        )
        section.pack(fill=tk.X, pady=10)
        
        # API key
        tk.Label(
            section,
            text="Libraries.io API Key:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_SECONDARY,
            font=('Arial', 10)
        ).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        api_key = os.getenv('LIBRARIES_IO_API_KEY', '')
        masked_key = '*' * len(api_key) if api_key else '(Not set)'
        
        self.api_key_label = tk.Label(
            section,
            text=masked_key,
            bg=DarkTheme.BG_TERTIARY,
            fg=DarkTheme.TEXT,
            font=('Arial', 10),
            padx=10,
            pady=5
        )
        self.api_key_label.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        section.columnconfigure(1, weight=1)
    
    def _create_cache_section(self, parent):
        """Create cache settings section."""
        section = tk.LabelFrame(
            parent,
            text="Cache Settings",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT,
            font=('Arial', 11, 'bold'),
            padx=10,
            pady=10
        )
        section.pack(fill=tk.X, pady=10)
        
        # Cache TTL
        tk.Label(
            section,
            text="Cache TTL (days):",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_SECONDARY,
            font=('Arial', 10)
        ).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.ttl_var = tk.StringVar(value=str(self.config.cache_ttl_days))
        ttl_entry = tk.Entry(
            section,
            textvariable=self.ttl_var,
            bg=DarkTheme.BG_TERTIARY,
            fg=DarkTheme.TEXT,
            font=('Arial', 10),
            width=10
        )
        ttl_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # Clear cache button
        clear_btn = tk.Button(
            section,
            text="Clear Cache",
            command=self._clear_cache,
            bg=DarkTheme.BG_HOVER,
            fg=DarkTheme.TEXT,
            relief=tk.FLAT,
            font=('Arial', 9),
            cursor='hand2',
            padx=15,
            pady=5
        )
        clear_btn.grid(row=1, column=0, columnspan=2, pady=10)
    
    def _create_download_section(self, parent):
        """Create download settings section."""
        section = tk.LabelFrame(
            parent,
            text="Download Settings",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT,
            font=('Arial', 11, 'bold'),
            padx=10,
            pady=10
        )
        section.pack(fill=tk.X, pady=10)
        
        # Download directory
        tk.Label(
            section,
            text="Download Directory:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_SECONDARY,
            font=('Arial', 10)
        ).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        dir_frame = tk.Frame(section, bg=DarkTheme.BG_SECONDARY)
        dir_frame.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        self.download_dir_var = tk.StringVar(value=str(self.config.download_dir))
        dir_entry = tk.Entry(
            dir_frame,
            textvariable=self.download_dir_var,
            bg=DarkTheme.BG_TERTIARY,
            fg=DarkTheme.TEXT,
            font=('Arial', 10)
        )
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_btn = tk.Button(
            dir_frame,
            text="Browse",
            command=self._browse_download_dir,
            bg=DarkTheme.BG_HOVER,
            fg=DarkTheme.TEXT,
            relief=tk.FLAT,
            font=('Arial', 9),
            cursor='hand2',
            padx=10
        )
        browse_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        section.columnconfigure(1, weight=1)
    
    def _browse_download_dir(self):
        """Browse for download directory."""
        directory = filedialog.askdirectory(
            title="Select Download Directory",
            initialdir=self.download_dir_var.get()
        )
        if directory:
            self.download_dir_var.set(directory)
    
    def _clear_cache(self):
        """Clear cache."""
        result = messagebox.askyesno(
            "Clear Cache",
            "This will delete all cached package data.\n\nContinue?"
        )
        if result:
            try:
                from npm.services.cache import CacheManager
                cache = CacheManager()
                cache.clear()
                messagebox.showinfo("Success", "Cache cleared successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear cache: {e}")
    
    def _save_settings(self):
        """Save settings."""
        try:
            # Validate TTL
            ttl = int(self.ttl_var.get())
            if ttl < 1:
                raise ValueError("TTL must be at least 1 day")
            
            # Would need to update .env file here
            # For now, just show message
            messagebox.showinfo(
                "Settings",
                "Settings will be applied on next restart.\n\n"
                "To persist changes, update your .env file."
            )
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))

