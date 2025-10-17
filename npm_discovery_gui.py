#!/usr/bin/env python3
"""Launch NPM Discovery GUI application."""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from npm_discovery.ui import main

if __name__ == "__main__":
    main()

