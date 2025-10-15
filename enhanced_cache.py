
class SafeUIOperation:
    """Context manager for safe UI operations with guaranteed cleanup - PREVENTS UI FREEZING"""
    def __init__(self, root, status_var, progress_bar=None, loading_message="Processing...", success_message="Complete"):
        self.root = root
        self.status_var = status_var
        self.progress_bar = progress_bar
        self.loading_message = loading_message
        self.success_message = success_message
        self._original_cursor = None
        self._entered = False
    
    def __enter__(self):
        self._original_cursor = self.root.cget("cursor")
        self.root.config(cursor="watch")
        self.status_var.set(self.loading_message)
        if self.progress_bar:
            self.progress_bar["value"] = 0
        self._entered = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._entered:
            self.root.config(cursor=self._original_cursor or "")
            if self.progress_bar:
                self.progress_bar["value"] = 100
            if exc_type is None:
                self.status_var.set(self.success_message)
            else:
                self.status_var.set(f"Error: {str(exc_val)[:50]}...")
                logger.error(f"UI operation failed: {exc_val}", exc_info=True)
        return False

def safe_ui_thread(root, status_var=None, progress_bar=None):
    """Decorator for thread functions that ensures UI cleanup"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cleanup_done = False
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"Thread error in {func.__name__}: {e}", exc_info=True)
                if root and hasattr(root, 'after'):
                    root.after(0, lambda: messagebox.showerror("Error", f"Operation failed: {str(e)[:100]}"))
                raise
            finally:
                if not cleanup_done and root and hasattr(root, 'after'):
                    root.after(0, lambda: root.config(cursor=""))
                    if progress_bar and hasattr(progress_bar, 'configure'):
                        root.after(0, lambda: progress_bar.configure(value=100))
                    if status_var:
                        root.after(0, lambda: status_var.set("Ready"))
                    cleanup_done = True
        return wrapper
    return decorator

