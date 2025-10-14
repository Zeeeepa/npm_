"""
NPM Package Analyzer - Usage Examples

This file demonstrates various ways to use the consolidated NPM analyzer.
Run each example independently by uncommenting the desired section.
"""

import os
from npm_consolidated import NPMAnalyzer, PackageInfo

# Set your API key
API_KEY = os.environ.get("LIBRARIES_IO_KEY", "your-key-here")


# ============================================================================
# Example 1: Basic Search
# ============================================================================

def example_basic_search():
    """Search for packages and display results."""
    print("=" * 80)
    print("Example 1: Basic Search")
    print("=" * 80)
    
    analyzer = NPMAnalyzer(API_KEY)
    
    try:
        # Search for React packages
        packages = analyzer.search("react", limit=10)
        
        print(f"\nFound {len(packages)} packages:\n")
        for i, pkg in enumerate(packages, 1):
            print(f"{i}. {pkg.name} ({pkg.version})")
            print(f"   ⭐ {pkg.stars} stars | 🔀 {pkg.forks} forks")
            print(f"   {pkg.description[:100]}...")
            print()
    
    finally:
        analyzer.close()


# ============================================================================
# Example 2: Package Enrichment
# ============================================================================

def example_package_enrichment():
    """Enrich package data with NPM registry information."""
    print("=" * 80)
    print("Example 2: Package Enrichment")
    print("=" * 80)
    
    analyzer = NPMAnalyzer(API_KEY)
    
    try:
        # Search for Express
        packages = analyzer.search("express", limit=1)
        if not packages:
            print("No packages found!")
            return
        
        pkg = packages[0]
        print(f"\nBefore enrichment:")
        print(f"  Name: {pkg.name}")
        print(f"  Dependencies: {len(pkg.dependencies)}")
        print(f"  Maintainers: {len(pkg.maintainers)}")
        
        # Enrich with NPM data
        pkg = analyzer.enrich_package(pkg)
        
        print(f"\nAfter enrichment:")
        print(f"  Name: {pkg.name}")
        print(f"  Version: {pkg.version}")
        print(f"  Dependencies: {len(pkg.dependencies)}")
        print(f"  Dev Dependencies: {len(pkg.dev_dependencies)}")
        print(f"  Maintainers: {len(pkg.maintainers)}")
        print(f"  Created: {pkg.created_at}")
        print(f"  Updated: {pkg.updated_at}")
        
        if pkg.dependencies:
            print(f"\n  Top 5 Dependencies:")
            for name, version in list(pkg.dependencies.items())[:5]:
                print(f"    - {name}: {version}")
    
    finally:
        analyzer.close()


# ============================================================================
# Example 3: File Tree Exploration
# ============================================================================

def example_file_tree():
    """Browse package file structure."""
    print("=" * 80)
    print("Example 3: File Tree Exploration")
    print("=" * 80)
    
    analyzer = NPMAnalyzer(API_KEY)
    
    try:
        # Get lodash package
        packages = analyzer.search("lodash", limit=1)
        if not packages:
            print("Package not found!")
            return
        
        pkg = packages[0]
        print(f"\n📁 Fetching file tree for {pkg.name}...")
        
        tree = analyzer.get_file_tree(pkg)
        if tree:
            print_tree_recursive(tree, indent=0)
        else:
            print("Failed to fetch file tree")
    
    finally:
        analyzer.close()


def print_tree_recursive(node, indent=0):
    """Helper to print tree structure."""
    name = node.get("path", "/").split("/")[-1] or "/"
    node_type = node.get("type", "file")
    prefix = "  " * indent
    icon = "📁" if node_type == "directory" else "📄"
    
    print(f"{prefix}{icon} {name}")
    
    if node_type == "directory":
        for child in node.get("files", [])[:5]:  # Limit to 5 per directory
            print_tree_recursive(child, indent + 1)
        
        if len(node.get("files", [])) > 5:
            print(f"{prefix}  ... and {len(node.get('files', [])) - 5} more")


# ============================================================================
# Example 4: File Content Viewing
# ============================================================================

def example_file_content():
    """View specific file contents."""
    print("=" * 80)
    print("Example 4: File Content Viewing")
    print("=" * 80)
    
    analyzer = NPMAnalyzer(API_KEY)
    
    try:
        # Get React package
        packages = analyzer.search("react", limit=1)
        if not packages:
            print("Package not found!")
            return
        
        pkg = packages[0]
        print(f"\n📄 Fetching README.md from {pkg.name}...")
        
        content = analyzer.get_file_content(pkg, "README.md")
        if content:
            # Show first 1000 characters
            print("\n" + "=" * 80)
            print(content[:1000])
            if len(content) > 1000:
                print(f"\n... (truncated, total {len(content)} characters)")
            print("=" * 80)
        else:
            print("Failed to fetch file content")
    
    finally:
        analyzer.close()


# ============================================================================
# Example 5: Batch Analysis
# ============================================================================

def example_batch_analysis():
    """Analyze multiple packages in batch."""
    print("=" * 80)
    print("Example 5: Batch Analysis")
    print("=" * 80)
    
    analyzer = NPMAnalyzer(API_KEY)
    
    try:
        # Popular frameworks to analyze
        queries = ["react", "vue", "angular", "svelte"]
        
        all_packages = []
        for query in queries:
            print(f"\n🔍 Searching for {query}...")
            packages = analyzer.search(query, limit=3)
            all_packages.extend(packages)
        
        print(f"\n✅ Found {len(all_packages)} total packages")
        
        # Enrich all packages
        print("\n🔄 Enriching packages...")
        for pkg in all_packages:
            analyzer.enrich_package(pkg)
        
        # Calculate statistics
        total_deps = sum(len(pkg.dependencies) for pkg in all_packages)
        total_stars = sum(pkg.stars for pkg in all_packages)
        
        print(f"\n📊 Statistics:")
        print(f"  Total packages: {len(all_packages)}")
        print(f"  Total dependencies: {total_deps}")
        print(f"  Total stars: {total_stars}")
        print(f"  Average dependencies per package: {total_deps / len(all_packages):.1f}")
        print(f"  Average stars per package: {total_stars / len(all_packages):.0f}")
    
    finally:
        analyzer.close()


# ============================================================================
# Example 6: Export Workflows
# ============================================================================

def example_exports():
    """Demonstrate export functionality."""
    print("=" * 80)
    print("Example 6: Export Workflows")
    print("=" * 80)
    
    analyzer = NPMAnalyzer(API_KEY)
    
    try:
        # Search for testing frameworks
        packages = analyzer.search("testing", limit=20)
        
        # Enrich packages
        print("\n🔄 Enriching packages...")
        for pkg in packages:
            analyzer.enrich_package(pkg)
        
        # Export to JSON
        json_path = "testing_frameworks.json"
        analyzer.export_json(packages, json_path)
        print(f"\n✅ Exported to {json_path}")
        
        # Export to text
        txt_path = "testing_frameworks.txt"
        analyzer.export_text(packages, txt_path)
        print(f"✅ Exported to {txt_path}")
        
        print(f"\n📁 Files created:")
        print(f"  - {json_path} ({os.path.getsize(json_path)} bytes)")
        print(f"  - {txt_path} ({os.path.getsize(txt_path)} bytes)")
    
    finally:
        analyzer.close()


# ============================================================================
# Example 7: Error Handling
# ============================================================================

def example_error_handling():
    """Demonstrate proper error handling."""
    print("=" * 80)
    print("Example 7: Error Handling")
    print("=" * 80)
    
    from npm_consolidated import APIError, RateLimitError
    
    analyzer = NPMAnalyzer(API_KEY)
    
    try:
        # Try to search with empty query
        try:
            packages = analyzer.search("", limit=10)
        except APIError as e:
            print(f"❌ API Error caught: {e}")
        
        # Try to get non-existent package
        try:
            pkg = analyzer.libraries_client.get_package("this-package-does-not-exist-12345")
            if pkg is None:
                print("❌ Package not found (returned None)")
        except APIError as e:
            print(f"❌ API Error: {e}")
        
        # Successful search
        packages = analyzer.search("express", limit=5)
        print(f"\n✅ Successfully retrieved {len(packages)} packages")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    finally:
        analyzer.close()


# ============================================================================
# Run Examples
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Check API key
    if API_KEY == "your-key-here":
        print("❌ Error: Please set LIBRARIES_IO_KEY environment variable!")
        print("\nGet your API key from: https://libraries.io/api")
        print("Then set it: export LIBRARIES_IO_KEY='your-key-here'")
        sys.exit(1)
    
    # Menu
    print("\nNPM Consolidated - Examples Menu")
    print("=" * 80)
    print("1. Basic Search")
    print("2. Package Enrichment")
    print("3. File Tree Exploration")
    print("4. File Content Viewing")
    print("5. Batch Analysis")
    print("6. Export Workflows")
    print("7. Error Handling")
    print("8. Run All Examples")
    print("0. Exit")
    
    choice = input("\nSelect example (0-8): ").strip()
    
    examples = {
        "1": example_basic_search,
        "2": example_package_enrichment,
        "3": example_file_tree,
        "4": example_file_content,
        "5": example_batch_analysis,
        "6": example_exports,
        "7": example_error_handling,
    }
    
    if choice == "0":
        print("Goodbye!")
    elif choice == "8":
        # Run all examples
        for func in examples.values():
            func()
            print("\n" + "=" * 80 + "\n")
    elif choice in examples:
        examples[choice]()
    else:
        print("Invalid choice!")

