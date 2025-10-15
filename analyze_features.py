#!/usr/bin/env python3
"""Comprehensive Feature Analysis of Original 3 NPM Files"""

import ast
import re
from typing import Dict, List, Set, Tuple
from pathlib import Path

class FeatureAnalyzer:
    """Analyze features in NPM Python files"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.filename = Path(filepath).name
        with open(filepath, 'r') as f:
            self.code = f.read()
        try:
            self.tree = ast.parse(self.code)
        except:
            self.tree = None
    
    def extract_features(self) -> Dict:
        """Extract all features from file"""
        features = {
            'filename': self.filename,
            'classes': self.get_classes(),
            'methods': self.get_methods(),
            'ui_elements': self.get_ui_elements(),
            'api_calls': self.get_api_calls(),
            'database_ops': self.get_database_ops(),
            'export_formats': self.get_export_formats(),
            'key_features': self.get_key_features(),
            'libraries': self.get_libraries(),
            'stats': self.get_stats()
        }
        return features
    
    def get_classes(self) -> List[str]:
        """Get all class names"""
        if not self.tree:
            return []
        return [node.name for node in ast.walk(self.tree) 
                if isinstance(node, ast.ClassDef)]
    
    def get_methods(self) -> List[str]:
        """Get all method/function names"""
        if not self.tree:
            return []
        methods = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                methods.append(node.name)
        return methods
    
    def get_ui_elements(self) -> Dict[str, List[str]]:
        """Detect UI elements and widgets"""
        ui = {
            'buttons': [],
            'labels': [],
            'entries': [],
            'treeviews': [],
            'text_widgets': [],
            'menus': [],
            'frames': []
        }
        
        # Button patterns
        button_patterns = [
            r'tk\.Button.*text=["\'](.*?)["\']',
            r'ttk\.Button.*text=["\'](.*?)["\']',
            r'Button.*text=["\'](.*?)["\']'
        ]
        for pattern in button_patterns:
            matches = re.findall(pattern, self.code, re.IGNORECASE)
            ui['buttons'].extend(matches)
        
        # Treeview
        if 'Treeview' in self.code:
            ui['treeviews'].append('Main results treeview')
        
        # Text widgets
        if 'Text(' in self.code or 'scrolledtext' in self.code.lower():
            ui['text_widgets'].append('Text display area')
        
        # Menu items
        menu_patterns = [
            r'\.add_command.*label=["\'](.*?)["\']',
            r'add_cascade.*label=["\'](.*?)["\']'
        ]
        for pattern in menu_patterns:
            matches = re.findall(pattern, self.code)
            ui['menus'].extend(matches)
        
        return ui
    
    def get_api_calls(self) -> List[str]:
        """Detect API endpoints used"""
        apis = []
        
        # Libraries.io
        if 'libraries.io' in self.code.lower():
            apis.append('Libraries.io API')
        
        # NPM Registry
        if 'registry.npmjs.org' in self.code or 'npmjs.com' in self.code:
            apis.append('NPM Registry API')
        
        # Unpkg
        if 'unpkg.com' in self.code:
            apis.append('Unpkg API')
        
        # GitHub
        if 'github.com/api' in self.code or 'api.github.com' in self.code:
            apis.append('GitHub API')
        
        return apis
    
    def get_database_ops(self) -> List[str]:
        """Detect database operations"""
        db_ops = []
        
        if 'sqlite3' in self.code:
            db_ops.append('SQLite database')
        
        if 'CREATE TABLE' in self.code:
            # Extract table names
            tables = re.findall(r'CREATE TABLE IF NOT EXISTS (\w+)', self.code, re.IGNORECASE)
            db_ops.extend([f"Table: {t}" for t in tables])
        
        return db_ops
    
    def get_export_formats(self) -> List[str]:
        """Detect export format support"""
        formats = []
        
        format_checks = {
            'JSON': ['json.dump', 'to_json', '.json'],
            'CSV': ['csv.writer', 'to_csv', '.csv'],
            'TXT': ['.txt', 'write('],
            'Markdown': ['.md', '# ', '## ', '| '],
            'Excel': ['.xlsx', 'openpyxl', 'xlsxwriter'],
            'HTML': ['.html', '<html>', '<table>']
        }
        
        for fmt, patterns in format_checks.items():
            if any(p in self.code for p in patterns):
                formats.append(fmt)
        
        return formats
    
    def get_key_features(self) -> List[str]:
        """Detect key features"""
        features = []
        
        feature_checks = {
            'Search History': ['history', 'recent_searches', 'search_history'],
            'Favorites/Bookmarks': ['favorite', 'bookmark', 'starred'],
            'Statistics Dashboard': ['statistics', 'stats', 'dashboard', 'analytics'],
            'Batch Processing': ['batch', 'bulk', 'multiple'],
            'Rate Limiting': ['rate_limit', 'RateLimit', 'sleep('],
            'Caching': ['cache', 'Cache', '@lru_cache'],
            'Progress Tracking': ['progress', 'Progress', 'progressbar'],
            'Error Handling': ['try:', 'except', 'Error'],
            'Keyboard Shortcuts': ['bind(', '<Control-', '<Alt-'],
            'Column Sorting': ['sort', 'Sort', 'heading'],
            'Filtering': ['filter', 'Filter'],
            'File Tree View': ['file_tree', 'tree_view', 'files'],
            'Dependency Graph': ['dependencies', 'deps', 'graph'],
            'Version Comparison': ['version', 'compare'],
            'Download Statistics': ['downloads', 'npm-stat'],
            'Package Size': ['size', 'bundle', 'minified'],
            'License Info': ['license', 'License'],
            'Repository Link': ['repository', 'repo', 'github'],
            'Documentation': ['readme', 'docs', 'documentation'],
            'Security Audit': ['security', 'vulnerabilities', 'audit'],
            'Multi-threading': ['Thread', 'ThreadPool', 'concurrent'],
            'Async Operations': ['async', 'await', 'asyncio'],
            'Copy to Clipboard': ['clipboard', 'copy'],
            'Theme Support': ['theme', 'dark', 'light'],
            'Auto-update': ['update', 'auto_update'],
            'Settings/Config': ['settings', 'config', 'preferences']
        }
        
        for feature, patterns in feature_checks.items():
            if any(p in self.code for p in patterns):
                features.append(feature)
        
        return features
    
    def get_libraries(self) -> List[str]:
        """Get imported libraries"""
        libs = []
        
        if not self.tree:
            return libs
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    libs.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    libs.append(node.module)
        
        return list(set(libs))
    
    def get_stats(self) -> Dict:
        """Get file statistics"""
        lines = self.code.split('\n')
        return {
            'total_lines': len(lines),
            'code_lines': len([l for l in lines if l.strip() and not l.strip().startswith('#')]),
            'comment_lines': len([l for l in lines if l.strip().startswith('#')]),
            'blank_lines': len([l for l in lines if not l.strip()])
        }

def compare_features(file1_features: Dict, file2_features: Dict, file3_features: Dict, 
                     consolidated_features: Dict) -> Dict:
    """Compare features across all files"""
    
    # Collect all unique features
    all_files = [file1_features, file2_features, file3_features]
    
    # Get unique features from originals
    original_features = set()
    for f in all_files:
        original_features.update(f['key_features'])
    
    # Get consolidated features
    consolidated_set = set(consolidated_features['key_features'])
    
    # Find missing features
    missing = original_features - consolidated_set
    
    # Find unique features per file
    unique_per_file = {
        file1_features['filename']: set(file1_features['key_features']) - 
                                     set(file2_features['key_features']) - 
                                     set(file3_features['key_features']),
        file2_features['filename']: set(file2_features['key_features']) - 
                                     set(file1_features['key_features']) - 
                                     set(file3_features['key_features']),
        file3_features['filename']: set(file3_features['key_features']) - 
                                     set(file1_features['key_features']) - 
                                     set(file2_features['key_features'])
    }
    
    return {
        'total_original_features': len(original_features),
        'consolidated_features': len(consolidated_set),
        'missing_features': list(missing),
        'unique_per_file': {k: list(v) for k, v in unique_per_file.items()},
        'all_original_features': list(original_features)
    }

def main():
    print("=" * 80)
    print("📊 COMPREHENSIVE FEATURE ANALYSIS - Original 3 NPM Files")
    print("=" * 80)
    
    # Analyze each file
    files = ['npm.py', 'npm2.py', 'npm_download.py']
    analyses = {}
    
    for filename in files:
        print(f"\n🔍 Analyzing {filename}...")
        analyzer = FeatureAnalyzer(filename)
        features = analyzer.extract_features()
        analyses[filename] = features
        
        print(f"   Classes: {len(features['classes'])}")
        print(f"   Methods: {len(features['methods'])}")
        print(f"   Key Features: {len(features['key_features'])}")
        print(f"   Lines: {features['stats']['total_lines']}")
    
    # Analyze consolidated
    print(f"\n🔍 Analyzing npm_analyzer_UPGRADED.py...")
    consolidated_analyzer = FeatureAnalyzer('npm_analyzer_UPGRADED.py')
    consolidated_features = consolidated_analyzer.extract_features()
    print(f"   Classes: {len(consolidated_features['classes'])}")
    print(f"   Methods: {len(consolidated_features['methods'])}")
    print(f"   Key Features: {len(consolidated_features['key_features'])}")
    
    # Compare
    print("\n" + "=" * 80)
    print("📊 FEATURE COMPARISON")
    print("=" * 80)
    
    comparison = compare_features(
        analyses['npm.py'],
        analyses['npm2.py'],
        analyses['npm_download.py'],
        consolidated_features
    )
    
    print(f"\n✅ Original Features: {comparison['total_original_features']}")
    print(f"✅ Consolidated Features: {comparison['consolidated_features']}")
    print(f"❌ Missing Features: {len(comparison['missing_features'])}")
    
    if comparison['missing_features']:
        print(f"\n🚨 MISSING FEATURES IN CONSOLIDATED VERSION:")
        for i, feature in enumerate(comparison['missing_features'], 1):
            print(f"   {i}. {feature}")
    
    # Detailed per-file analysis
    print("\n" + "=" * 80)
    print("📋 DETAILED FEATURE BREAKDOWN")
    print("=" * 80)
    
    for filename in files:
        features = analyses[filename]
        print(f"\n📄 {filename}:")
        print(f"   Total Lines: {features['stats']['total_lines']}")
        print(f"   Classes: {', '.join(features['classes'][:5])}...")
        print(f"   APIs: {', '.join(features['api_calls'])}")
        print(f"   Export Formats: {', '.join(features['export_formats'])}")
        print(f"   Key Features ({len(features['key_features'])}):")
        for feat in features['key_features'][:10]:
            print(f"      - {feat}")
        if len(features['key_features']) > 10:
            print(f"      ... and {len(features['key_features']) - 10} more")
    
    # Unique features
    print("\n" + "=" * 80)
    print("🎯 UNIQUE FEATURES PER FILE")
    print("=" * 80)
    
    for filename, unique_features in comparison['unique_per_file'].items():
        if unique_features:
            print(f"\n{filename} ONLY:")
            for feat in unique_features:
                print(f"   - {feat}")
    
    # Export formats comparison
    print("\n" + "=" * 80)
    print("📤 EXPORT FORMATS COMPARISON")
    print("=" * 80)
    
    for filename in files:
        formats = analyses[filename]['export_formats']
        print(f"{filename}: {', '.join(formats)}")
    
    print(f"Consolidated: {', '.join(consolidated_features['export_formats'])}")
    
    # API comparison
    print("\n" + "=" * 80)
    print("🌐 API ENDPOINTS COMPARISON")
    print("=" * 80)
    
    for filename in files:
        apis = analyses[filename]['api_calls']
        print(f"{filename}: {', '.join(apis) if apis else 'None'}")
    
    print(f"Consolidated: {', '.join(consolidated_features['api_calls'])}")
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
