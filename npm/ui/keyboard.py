"""Keyboard shortcuts handler."""
import logging
from typing import Callable

logger = logging.getLogger(__name__)


class KeyboardShortcuts:
    """Manages keyboard shortcuts for the application."""
    
    SHORTCUTS = {
        '<Control-f>': 'Focus search',
        '<Control-r>': 'Show README',
        '<Control-t>': 'Show file tree',
        '<Control-d>': 'Download package',
        '<Control-c>': 'Add to comparison',
        '<Control-q>': 'Quit application',
        '<F5>': 'Refresh/Re-search',
        '<Escape>': 'Clear selection',
    }
    
    def __init__(self, root):
        """Initialize shortcuts.
        
        Args:
            root: Tkinter root window.
        """
        self.root = root
        self.handlers = {}
    
    def register(self, shortcut: str, callback: Callable):
        """Register a keyboard shortcut.
        
        Args:
            shortcut: Shortcut string (e.g., '<Control-f>').
            callback: Function to call when shortcut is pressed.
        """
        if shortcut in self.SHORTCUTS:
            self.handlers[shortcut] = callback
            self.root.bind(shortcut, lambda e: callback())
            logger.debug(f"Registered shortcut: {shortcut} -> {self.SHORTCUTS[shortcut]}")
    
    def unregister(self, shortcut: str):
        """Unregister a keyboard shortcut.
        
        Args:
            shortcut: Shortcut to remove.
        """
        if shortcut in self.handlers:
            self.root.unbind(shortcut)
            del self.handlers[shortcut]
            logger.debug(f"Unregistered shortcut: {shortcut}")
    
    def get_help_text(self) -> str:
        """Get help text for all shortcuts.
        
        Returns:
            Formatted help text.
        """
        lines = ["Keyboard Shortcuts:", ""]
        for shortcut, description in self.SHORTCUTS.items():
            lines.append(f"  {shortcut:20s} {description}")
        return "\n".join(lines)

