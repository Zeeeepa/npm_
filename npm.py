#!/usr/bin/env python3
"""NPM Package Discovery Tool - Main Launcher

This is the main entry point for the NPM Package Discovery Tool.
Run this file to start the GUI application.

Usage:
    python npm.py              # Start GUI
    python npm.py --cli        # Start CLI mode
    python npm.py --help       # Show help
"""
import sys
import argparse
from npm.ui.app import NPMDiscoveryApp
from npm.cli import main as cli_main


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="NPM Package Discovery Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python npm.py                    # Start GUI
  python npm.py --cli              # Start CLI
  python npm.py --cli search react # Search for React packages
        """
    )
    parser.add_argument(
        '--cli',
        action='store_true',
        help='Run in CLI mode instead of GUI'
    )
    
    args, remaining = parser.parse_known_args()
    
    if args.cli:
        # Run CLI mode
        sys.argv = [sys.argv[0]] + remaining
        cli_main()
    else:
        # Run GUI mode
        print("Starting NPM Discovery GUI...")
        app = NPMDiscoveryApp()
        app.run()


if __name__ == '__main__':
    main()

