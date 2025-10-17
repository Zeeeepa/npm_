"""Command-line interface for NPM discovery."""
import sys
import logging
from typing import Optional
from npm.config import get_config
from npm.services.discovery import DiscoveryService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def search_command(service: DiscoveryService, query: str, limit: int = 10):
    """Search for packages."""
    print(f"\n🔍 Searching for: {query}\n")
    
    results = service.search_packages(query, per_page=limit)
    
    if not results:
        print("No results found.")
        return
    
    for i, result in enumerate(results[:limit], 1):
        print(f"{i}. {result.name} (v{result.version})")
        if result.description:
            print(f"   {result.description[:80]}...")
        print(f"   ⭐ {result.stars} | 📦 {result.dependents_count} dependents")
        print()


def details_command(service: DiscoveryService, name: str, show_tree: bool = False):
    """Show package details."""
    print(f"\n📦 Fetching details for: {name}\n")
    
    package = service.get_package_details(name, fetch_file_tree=show_tree)
    
    if not package:
        print("Package not found.")
        return
    
    print(f"Name: {package.name}")
    print(f"Version: {package.version}")
    print(f"Description: {package.description}")
    print(f"Author: {package.author}")
    print(f"License: {package.license}")
    print(f"Homepage: {package.homepage}")
    print(f"Repository: {package.repository}")
    print(f"Downloads (last month): {package.downloads_last_month:,}")
    print(f"Dependencies: {package.dependencies_count}")
    print(f"Dev Dependencies: {package.dev_dependencies_count}")
    print(f"Total Versions: {package.total_versions}")
    print(f"Maintainers: {package.maintainers_count}")
    
    if package.keywords:
        print(f"Keywords: {', '.join(package.keywords[:10])}")
    
    if show_tree and package.file_tree:
        print(f"\n📁 File Tree:")
        print(f"  Total files: {package.file_tree.get('file_count', 0)}")


def cache_stats_command(service: DiscoveryService):
    """Show cache statistics."""
    print("\n📊 Cache Statistics\n")
    
    stats = service.get_cache_stats()
    print(f"Total entries: {stats.get('total_entries', 0)}")
    print(f"Valid entries: {stats.get('valid_entries', 0)}")
    print(f"Expired entries: {stats.get('expired_entries', 0)}")
    print(f"Database: {stats.get('db_path', 'Unknown')}")


def main():
    """Main CLI entry point."""
    try:
        # Validate config
        config = get_config(validate=True)
        logger.info("Configuration validated successfully")
        
        # Create service
        service = DiscoveryService()
        
        # Simple command parsing
        if len(sys.argv) < 2:
            print("NPM Discovery CLI")
            print("\nUsage:")
            print("  python -m npm_discovery.cli search <query>")
            print("  python -m npm_discovery.cli details <package>")
            print("  python -m npm_discovery.cli tree <package>")
            print("  python -m npm_discovery.cli cache-stats")
            sys.exit(1)
        
        command = sys.argv[1]
        
        if command == "search":
            if len(sys.argv) < 3:
                print("Usage: search <query>")
                sys.exit(1)
            query = " ".join(sys.argv[2:])
            search_command(service, query)
        
        elif command == "details":
            if len(sys.argv) < 3:
                print("Usage: details <package>")
                sys.exit(1)
            name = sys.argv[2]
            details_command(service, name)
        
        elif command == "tree":
            if len(sys.argv) < 3:
                print("Usage: tree <package>")
                sys.exit(1)
            name = sys.argv[2]
            details_command(service, name, show_tree=True)
        
        elif command == "cache-stats":
            cache_stats_command(service)
        
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease set LIBRARIES_IO_API_KEY environment variable.")
        sys.exit(1)
    
    except Exception as e:
        logger.exception("Unexpected error")
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

