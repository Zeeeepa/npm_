# ============================================================================
# FEATURE ADDITIONS - Add these methods to NPMAnalyzerApp class
# ============================================================================

# 1. ADD TO __init__ method (after line 1103):
"""
        # Initialize new managers
        self.history_manager = SearchHistoryManager()
        self.favorites_manager = FavoritesManager()
        self.batch_processor = BatchProcessor(self.client, self.enricher)
        
        # Sorting state
        self.sort_column = None
        self.sort_reverse = False
        
        # Filter vars  
        self.min_size_var = None
        self.max_size_var = None
        self.min_downloads_var = None
        self.license_var = None
"""

# 2. ADD NEW METHOD - Keyboard Shortcuts
def _setup_keyboard_shortcuts(self):
    """Setup keyboard shortcuts."""
    self.root.bind('<Control-s>', lambda e: self._on_export_clicked())
    self.root.bind('<Control-f>', lambda e: self.search_entry.focus())
    self.root.bind('<Control-r>', lambda e: self._on_search())
    self.root.bind('<Control-h>', lambda e: self._show_history())
    self.root.bind('<Control-q>', lambda e: self.root.quit())
    self.root.bind('<F5>', lambda e: self._on_search())
    self.root.bind('<Escape>', lambda e: self.search_entry.focus())


# 3. ADD NEW METHOD - Show History
def _show_history(self):
    """Show search history dropdown."""
    history = self.history_manager.get_recent_searches(10)
    
    if not history:
        messagebox.showinfo("History", "No search history yet")
        return
    
    # Create history window
    dialog = tk.Toplevel(self.root)
    dialog.title("Search History")
    dialog.geometry("600x400")
    dialog.configure(bg=Theme.BG)
    
    tk.Label(
        dialog, text="Recent Searches",
        font=("Arial", 16, "bold"),
        fg=Theme.TEXT, bg=Theme.BG
    ).pack(pady=10)
    
    # Create listbox
    listbox = tk.Listbox(
        dialog, font=("Arial", 11),
        bg=Theme.BG_SECONDARY, fg=Theme.TEXT,
        selectbackground=Theme.ACCENT
    )
    listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Add history items
    for item in history:
        timestamp = item['timestamp'].strftime('%Y-%m-%d %H:%M')
        text = f"{timestamp} | {item['query']} ({item['result_count']} results)"
        listbox.insert(tk.END, text)
    
    # Add buttons
    btn_frame = tk.Frame(dialog, bg=Theme.BG)
    btn_frame.pack(pady=10)
    
    def run_selected():
        sel = listbox.curselection()
        if sel:
            query = history[sel[0]]['query']
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, query)
            dialog.destroy()
            self._on_search()
    
    tk.Button(
        btn_frame, text="Run Selected",
        command=run_selected,
        bg=Theme.ACCENT, fg=Theme.TEXT,
        padx=20, pady=5
    ).pack(side=tk.LEFT, padx=5)
    
    tk.Button(
        btn_frame, text="Clear History",
        command=lambda: [self.history_manager.clear_history(), dialog.destroy()],
        bg=Theme.BG_TERTIARY, fg=Theme.TEXT,
        padx=20, pady=5
    ).pack(side=tk.LEFT, padx=5)


# 4. ADD NEW METHOD - Show Statistics
def _show_statistics(self):
    """Show statistics dashboard."""
    if not self.current_results:
        messagebox.showwarning("No Data", "No packages to analyze. Run a search first.")
        return
    
    dashboard = StatisticsDashboard(self.current_results)
    dashboard.show()


# 5. ADD NEW METHOD - Batch Process
def _batch_process(self):
    """Process multiple packages from file."""
    filepath = filedialog.askopenfilename(
        title="Select Package List",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    
    if not filepath:
        return
    
    # Create progress dialog
    dialog = tk.Toplevel(self.root)
    dialog.title("Batch Processing")
    dialog.geometry("400x150")
    dialog.configure(bg=Theme.BG)
    dialog.transient(self.root)
    dialog.grab_set()
    
    tk.Label(
        dialog, text="Processing packages...",
        font=("Arial", 12),
        fg=Theme.TEXT, bg=Theme.BG
    ).pack(pady=20)
    
    progress_var = tk.StringVar(value="0/0 packages processed")
    tk.Label(
        dialog, textvariable=progress_var,
        fg=Theme.TEXT_SECONDARY, bg=Theme.BG
    ).pack()
    
    progress = ttk.Progressbar(dialog, length=350)
    progress.pack(pady=20)
    
    def update_progress(current, total):
        progress['maximum'] = total
        progress['value'] = current
        progress_var.set(f"{current}/{total} packages processed")
        dialog.update()
    
    def run_batch():
        try:
            results = self.batch_processor.process_from_file(
                filepath,
                progress_callback=update_progress
            )
            
            dialog.destroy()
            
            if results:
                self.current_results = results
                self._display_results(results)
                self._update_status(f"Loaded {len(results)} packages from file")
                messagebox.showinfo(
                    "Batch Complete",
                    f"Processed {len(results)} packages successfully"
                )
            else:
                messagebox.showwarning(
                    "No Results",
                    "No packages were found or processed"
                )
        except Exception as e:
            dialog.destroy()
            messagebox.showerror("Batch Error", str(e))
    
    # Run in thread
    threading.Thread(target=run_batch, daemon=True).start()


# 6. ADD NEW METHOD - Create Filter Controls
def _create_filter_controls(self, parent):
    """Create advanced filtering controls."""
    filter_frame = tk.Frame(parent, bg=Theme.BG_SECONDARY)
    filter_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # Size filter
    tk.Label(filter_frame, text="Min Size:",
            fg=Theme.TEXT, bg=Theme.BG_SECONDARY).pack(side=tk.LEFT, padx=5)
    self.min_size_var = tk.StringVar(value="0")
    tk.Entry(filter_frame, textvariable=self.min_size_var,
            width=10).pack(side=tk.LEFT, padx=5)
    
    tk.Label(filter_frame, text="Max Size:",
            fg=Theme.TEXT, bg=Theme.BG_SECONDARY).pack(side=tk.LEFT, padx=5)
    self.max_size_var = tk.StringVar(value="999999999")
    tk.Entry(filter_frame, textvariable=self.max_size_var,
            width=10).pack(side=tk.LEFT, padx=5)
    
    # Downloads filter
    tk.Label(filter_frame, text="Min Downloads:",
            fg=Theme.TEXT, bg=Theme.BG_SECONDARY).pack(side=tk.LEFT, padx=5)
    self.min_downloads_var = tk.StringVar(value="0")
    tk.Entry(filter_frame, textvariable=self.min_downloads_var,
            width=10).pack(side=tk.LEFT, padx=5)
    
    # License filter
    tk.Label(filter_frame, text="License:",
            fg=Theme.TEXT, bg=Theme.BG_SECONDARY).pack(side=tk.LEFT, padx=5)
    self.license_var = tk.StringVar(value="")
    tk.Entry(filter_frame, textvariable=self.license_var,
            width=15).pack(side=tk.LEFT, padx=5)
    
    # Apply button
    tk.Button(
        filter_frame, text="Apply Filters",
        command=self._apply_filters,
        bg=Theme.ACCENT, fg=Theme.TEXT
    ).pack(side=tk.LEFT, padx=10)
    
    # Clear button
    tk.Button(
        filter_frame, text="Clear",
        command=self._clear_filters,
        bg=Theme.BG_TERTIARY, fg=Theme.TEXT
    ).pack(side=tk.LEFT)


# 7. ADD NEW METHOD - Apply Filters
def _apply_filters(self):
    """Apply filters to current results."""
    if not self.current_results:
        return
    
    try:
        min_size = int(self.min_size_var.get() or 0)
        max_size = int(self.max_size_var.get() or 999999999)
        min_downloads = int(self.min_downloads_var.get() or 0)
        license_filter = self.license_var.get().lower()
        
        filtered = []
        for pkg in self.current_results:
            # Size filter
            if not (min_size <= pkg.unpacked_size <= max_size):
                continue
            
            # Downloads filter
            if pkg.npm_downloads_weekly < min_downloads:
                continue
            
            # License filter
            if license_filter and license_filter not in pkg.license.lower():
                continue
            
            filtered.append(pkg)
        
        self._display_results(filtered)
        self._update_status(f"Filtered: {len(filtered)} of {len(self.current_results)} packages")
        
    except ValueError as exc:
        messagebox.showerror("Filter Error", f"Invalid filter value: {exc}")


# 8. ADD NEW METHOD - Clear Filters
def _clear_filters(self):
    """Clear all filters and show all results."""
    self.min_size_var.set("0")
    self.max_size_var.set("999999999")
    self.min_downloads_var.set("0")
    self.license_var.set("")
    self._display_results(self.current_results)
    self._update_status(f"Showing all {len(self.current_results)} packages")


# 9. ADD NEW METHOD - Sort Column
def _sort_column(self, col):
    """Sort table by column."""
    if not self.current_results:
        return
    
    # Toggle reverse if same column
    if self.sort_column == col:
        self.sort_reverse = not self.sort_reverse
    else:
        self.sort_column = col
        self.sort_reverse = False
    
    # Sort mapping
    sort_keys = {
        'Name': lambda p: p.name.lower(),
        'Version': lambda p: p.version,
        'Files': lambda p: p.file_count,
        'Size': lambda p: p.unpacked_size,
        'Downloads': lambda p: p.npm_downloads_weekly,
        'License': lambda p: p.license.lower(),
    }
    
    if col in sort_keys:
        self.current_results.sort(
            key=sort_keys[col],
            reverse=self.sort_reverse
        )
        self._display_results(self.current_results)
        
        # Update column header to show sort direction
        for c in self.tree['columns']:
            indicator = ""
            if c == col:
                indicator = " ▼" if self.sort_reverse else " ▲"
            self.tree.heading(c, text=f"{c}{indicator}")


# 10. MODIFY _create_toolbar (ADD NEW BUTTONS):
"""
# Add after existing buttons:

        # History button
        tk.Button(
            toolbar, text="📜 History",
            command=self._show_history,
            bg=Theme.BG_TERTIARY, fg=Theme.TEXT
        ).pack(side=tk.LEFT, padx=2)
        
        # Statistics button
        tk.Button(
            toolbar, text="📊 Stats",
            command=self._show_statistics,
            bg=Theme.BG_TERTIARY, fg=Theme.TEXT
        ).pack(side=tk.LEFT, padx=2)
        
        # Batch button
        tk.Button(
            toolbar, text="📦 Batch",
            command=self._batch_process,
            bg=Theme.BG_TERTIARY, fg=Theme.TEXT
        ).pack(side=tk.LEFT, padx=2)
        
        # Shortcuts help button
        help_text = '''Keyboard Shortcuts:
        
Ctrl+S  - Export results
Ctrl+F  - Focus search box
Ctrl+R  - Run search
Ctrl+H  - Show history
Ctrl+Q  - Quit application
F5      - Refresh search
Esc     - Focus search box'''
        
        tk.Button(
            toolbar, text="❓ Shortcuts",
            command=lambda: messagebox.showinfo("Keyboard Shortcuts", help_text),
            bg=Theme.BG_TERTIARY, fg=Theme.TEXT
        ).pack(side=tk.RIGHT, padx=2)
"""


# 11. MODIFY _create_results_table (ADD SORTING):
"""
# Add after creating tree columns:
        
        # Add click handlers to column headers for sorting
        for col in self.tree['columns']:
            self.tree.heading(col, text=col,
                             command=lambda c=col: self._sort_column(c))
"""


# 12. MODIFY _export_results (ADD MARKDOWN):
"""
# Add elif block for markdown export:

        elif ext == '.md':
            # Markdown export
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("# NPM Package Analysis Report\\n\\n")
                f.write(f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
                f.write(f"**Total Packages:** {len(self.current_results)}\\n\\n")
                f.write("---\\n\\n")
                
                for pkg in self.current_results:
                    f.write(f"## {pkg.name} v{pkg.version}\\n\\n")
                    
                    if pkg.description:
                        f.write(f"{pkg.description}\\n\\n")
                    
                    f.write("### Package Info\\n\\n")
                    f.write(f"- **License:** {pkg.license or 'N/A'}\\n")
                    f.write(f"- **Homepage:** {pkg.homepage or 'N/A'}\\n")
                    f.write(f"- **Repository:** {pkg.repository_url or 'N/A'}\\n")
                    f.write(f"- **NPM URL:** {pkg.npm_url}\\n\\n")
                    
                    if pkg.file_count > 0:
                        f.write("### Stats\\n\\n")
                        f.write(f"- **Files:** {pkg.file_count:,}\\n")
                        f.write(f"- **Size:** {self._format_size(pkg.unpacked_size)}\\n")
                        
                        if pkg.npm_downloads_weekly > 0:
                            f.write(f"- **Weekly Downloads:** {self._format_downloads(pkg.npm_downloads_weekly)}\\n")
                            f.write(f"- **Monthly Downloads:** {self._format_downloads(pkg.npm_downloads_monthly)}\\n")
                        
                        f.write("\\n")
                    
                    if pkg.dependencies:
                        f.write("### Dependencies\\n\\n")
                        for dep, ver in list(pkg.dependencies.items())[:10]:
                            f.write(f"- `{dep}`: {ver}\\n")
                        if len(pkg.dependencies) > 10:
                            f.write(f"\\n*...and {len(pkg.dependencies) - 10} more*\\n")
                        f.write("\\n")
                    
                    f.write("---\\n\\n")
            
            messagebox.showinfo("Export Successful", 
                              f"Exported {len(self.current_results)} packages to Markdown")
"""


# 13. MODIFY _on_search (ADD HISTORY SAVE):
"""
# Add at the end of successful search (after displaying results):

        # Save to history
        self.history_manager.save_search(
            query=query,
            max_results=max_results,
            result_count=len(self.current_results),
            duration=search_duration
        )
"""


# 14. MODIFY _on_export_clicked (ADD .md FILETYPE):
"""
# Modify filetypes parameter:

        filetypes = [
            ("JSON", "*.json"),
            ("CSV", "*.csv"),
            ("Text", "*.txt"),
            ("Markdown", "*.md"),  # ADD THIS LINE
            ("All Files", "*.*")
        ]
"""

print("Feature additions documented. Apply these changes to NPMAnalyzerApp class.")

