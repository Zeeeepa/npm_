"""Settings dialog."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from npm.ui.theme import DarkTheme
from npm.config import get_config, reset_config
import os
import asyncio
import aiohttp
from pathlib import Path


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
        
        # API key label
        tk.Label(
            section,
            text="Libraries.io API Key:",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_SECONDARY,
            font=('Arial', 10)
        ).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # API key input
        api_key = os.getenv('LIBRARIES_IO_API_KEY', '')
        self.api_key_var = tk.StringVar(value=api_key)
        
        key_entry = tk.Entry(
            section,
            textvariable=self.api_key_var,
            bg=DarkTheme.BG_TERTIARY,
            fg=DarkTheme.TEXT,
            font=('Arial', 10),
            show='*'
        )
        key_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=(10, 5))
        
        # Show/Hide button
        self.show_key = False
        self.show_key_btn = tk.Button(
            section,
            text="👁",
            command=self._toggle_api_key_visibility,
            bg=DarkTheme.BG_HOVER,
            fg=DarkTheme.TEXT,
            relief=tk.FLAT,
            font=('Arial', 10),
            cursor='hand2',
            width=3
        )
        self.show_key_btn.grid(row=0, column=2, pady=5, padx=(0, 5))
        self.key_entry = key_entry
        
        # Validate button and status
        btn_frame = tk.Frame(section, bg=DarkTheme.BG_SECONDARY)
        btn_frame.grid(row=1, column=0, columnspan=3, pady=(10, 5), sticky=tk.W)
        
        self.validate_btn = tk.Button(
            btn_frame,
            text="Test API Key",
            command=self._validate_api_key,
            bg=DarkTheme.ACCENT,
            fg=DarkTheme.TEXT,
            relief=tk.FLAT,
            font=('Arial', 9, 'bold'),
            cursor='hand2',
            padx=15,
            pady=5
        )
        self.validate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.api_status_label = tk.Label(
            btn_frame,
            text="",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_SECONDARY,
            font=('Arial', 9)
        )
        self.api_status_label.pack(side=tk.LEFT)
        
        # Help text
        help_text = tk.Label(
            section,
            text="Get your free API key at: https://libraries.io/account",
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_MUTED,
            font=('Arial', 8),
            cursor='hand2'
        )
        help_text.grid(row=2, column=0, columnspan=3, pady=(5, 0), sticky=tk.W)
        help_text.bind('<Button-1>', lambda e: os.system('xdg-open https://libraries.io/account 2>/dev/null || open https://libraries.io/account 2>/dev/null'))
        
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
    
    def _toggle_api_key_visibility(self):
        """Toggle API key visibility."""
        self.show_key = not self.show_key
        self.key_entry.config(show='' if self.show_key else '*')
        self.show_key_btn.config(text='👁‍🗨' if self.show_key else '👁')
    
    def _validate_api_key(self):
        """Validate API key by testing it."""
        api_key = self.api_key_var.get().strip()
        
        if not api_key:
            self.api_status_label.config(text="❌ ERROR: API key is empty", fg='#ff4444')
            return
        
        # Disable button during validation
        self.validate_btn.config(state=tk.DISABLED, text="Testing...")
        self.api_status_label.config(text="⏳ Validating...", fg=DarkTheme.TEXT_SECONDARY)
        self.update()
        
        # Test the API key
        async def test_key():
            url = f"https://libraries.io/api/platforms?api_key={api_key}"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            return True, "✅ OK: API key is valid"
                        elif response.status == 401:
                            return False, "❌ ERROR: Invalid API key"
                        elif response.status == 429:
                            return False, "⚠️ WARNING: Rate limit exceeded (but key is valid)"
                        else:
                            return False, f"❌ ERROR: HTTP {response.status}"
            except asyncio.TimeoutError:
                return False, "❌ ERROR: Connection timeout"
            except Exception as e:
                return False, f"❌ ERROR: {str(e)}"
        
        # Run async test
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success, message = loop.run_until_complete(test_key())
            loop.close()
            
            # Update UI
            color = '#44ff44' if success else '#ff4444' if 'ERROR' in message else '#ffaa44'
            self.api_status_label.config(text=message, fg=color)
        except Exception as e:
            self.api_status_label.config(text=f"❌ ERROR: {e}", fg='#ff4444')
        finally:
            self.validate_btn.config(state=tk.NORMAL, text="Test API Key")
    
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
        """Save settings to .env file."""
        try:
            # Validate TTL
            ttl = int(self.ttl_var.get())
            if ttl < 1:
                raise ValueError("TTL must be at least 1 day")
            
            # Get values
            api_key = self.api_key_var.get().strip()
            download_dir = self.download_dir_var.get()
            
            # Write to .env file
            env_file = Path.cwd() / '.env'
            env_lines = []
            
            # Read existing .env if it exists
            existing_vars = {}
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            existing_vars[key.strip()] = value.strip()
            
            # Update values
            existing_vars['LIBRARIES_IO_API_KEY'] = api_key
            existing_vars['CACHE_TTL_DAYS'] = str(ttl)
            existing_vars['DOWNLOAD_DIR'] = download_dir
            
            # Write .env file
            with open(env_file, 'w') as f:
                f.write("# NPM Discovery Configuration\n")
                f.write("# Generated by Settings Dialog\n\n")
                
                # Write Libraries.io API key
                f.write("# Libraries.io API Key (Required)\n")
                f.write("# Get yours at: https://libraries.io/account\n")
                f.write(f"LIBRARIES_IO_API_KEY={existing_vars.get('LIBRARIES_IO_API_KEY', '')}\n\n")
                
                # Write other settings
                f.write("# Cache TTL in days (default: 7)\n")
                f.write(f"CACHE_TTL_DAYS={existing_vars.get('CACHE_TTL_DAYS', '7')}\n\n")
                
                f.write("# Download directory\n")
                f.write(f"DOWNLOAD_DIR={existing_vars.get('DOWNLOAD_DIR', '~/npm_packages')}\n\n")
                
                # Write any other existing vars
                standard_vars = {'LIBRARIES_IO_API_KEY', 'CACHE_TTL_DAYS', 'DOWNLOAD_DIR'}
                other_vars = {k: v for k, v in existing_vars.items() if k not in standard_vars}
                if other_vars:
                    f.write("# Other settings\n")
                    for key, value in other_vars.items():
                        f.write(f"{key}={value}\n")
            
            # Update environment
            os.environ['LIBRARIES_IO_API_KEY'] = api_key
            os.environ['CACHE_TTL_DAYS'] = str(ttl)
            os.environ['DOWNLOAD_DIR'] = download_dir
            
            # Reset config to pick up new values
            reset_config()
            
            messagebox.showinfo(
                "Settings Saved",
                f"Settings saved to {env_file}\n\n"
                "Changes applied immediately!"
            )
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save settings: {e}")
