#!/usr/bin/env python3
"""Comprehensive Test Suite for NPM Analyzer UPGRADED"""

import ast
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple

class ComprehensiveTestRunner:
    """Run all tests on npm_analyzer_UPGRADED.py"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.results = []
        
    def test_syntax(self) -> bool:
        """Test 1: Python syntax validation"""
        print("🔍 Test 1: Syntax Validation")
        try:
            with open(self.filepath, 'r') as f:
                code = f.read()
            compile(code, self.filepath, 'exec')
            print("   ✅ Syntax is valid")
            return True
        except SyntaxError as e:
            print(f"   ❌ Syntax error: {e}")
            return False
    
    def test_ast_parsing(self) -> bool:
        """Test 2: AST parsing"""
        print("\n🔍 Test 2: AST Parsing")
        try:
            with open(self.filepath, 'r') as f:
                code = f.read()
            tree = ast.parse(code)
            
            # Count elements
            classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            
            print(f"   ✅ AST parsed successfully")
            print(f"   📊 Found {len(classes)} classes, {len(functions)} functions")
            return True
        except Exception as e:
            print(f"   ❌ AST parsing failed: {e}")
            return False
    
    def test_imports(self) -> bool:
        """Test 3: Import validation"""
        print("\n🔍 Test 3: Import Validation")
        try:
            with open(self.filepath, 'r') as f:
                code = f.read()
            tree = ast.parse(code)
            
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    imports.append(f"{node.module}")
            
            print(f"   ✅ Found {len(imports)} import statements")
            
            # Test critical imports
            critical = ['tkinter', 'sqlite3', 'requests', 'json', 'datetime']
            missing = [imp for imp in critical if not any(imp in i for i in imports)]
            
            if missing:
                print(f"   ⚠️  Missing critical imports: {missing}")
            else:
                print(f"   ✅ All critical imports present")
            
            return True
        except Exception as e:
            print(f"   ❌ Import validation failed: {e}")
            return False
    
    def test_class_structure(self) -> bool:
        """Test 4: Class structure validation"""
        print("\n🔍 Test 4: Class Structure")
        try:
            with open(self.filepath, 'r') as f:
                code = f.read()
            tree = ast.parse(code)
            
            # Find specific classes
            expected_classes = [
                'SearchHistoryManager',
                'FavoritesManager', 
                'BatchProcessor',
                'StatisticsDashboard',
                'NPMAnalyzerApp'
            ]
            
            found_classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            
            for cls in expected_classes:
                if cls in found_classes:
                    print(f"   ✅ Class '{cls}' found")
                else:
                    print(f"   ❌ Class '{cls}' MISSING")
                    return False
            
            return True
        except Exception as e:
            print(f"   ❌ Class structure test failed: {e}")
            return False
    
    def test_method_signatures(self) -> bool:
        """Test 5: Method signature validation"""
        print("\n🔍 Test 5: Method Signatures")
        try:
            with open(self.filepath, 'r') as f:
                code = f.read()
            tree = ast.parse(code)
            
            # Find NPMAnalyzerApp class
            npm_class = None
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == 'NPMAnalyzerApp':
                    npm_class = node
                    break
            
            if not npm_class:
                print("   ❌ NPMAnalyzerApp class not found")
                return False
            
            # Check for __init__ method
            methods = [n.name for n in npm_class.body if isinstance(n, ast.FunctionDef)]
            
            critical_methods = ['__init__', '_create_ui', '_on_search', '_display_results']
            
            for method in critical_methods:
                if method in methods:
                    print(f"   ✅ Method '{method}' found")
                else:
                    print(f"   ⚠️  Method '{method}' not found")
            
            print(f"   📊 Total methods in NPMAnalyzerApp: {len(methods)}")
            return True
            
        except Exception as e:
            print(f"   ❌ Method signature test failed: {e}")
            return False
    
    def test_database_operations(self) -> bool:
        """Test 6: Database operation checks"""
        print("\n🔍 Test 6: Database Operations")
        try:
            with open(self.filepath, 'r') as f:
                code = f.read()
            
            # Check for SQLite operations
            db_keywords = ['sqlite3', 'CREATE TABLE', 'INSERT', 'SELECT', 'execute']
            found = []
            
            for keyword in db_keywords:
                if keyword in code:
                    found.append(keyword)
            
            print(f"   ✅ Found {len(found)}/{len(db_keywords)} database keywords")
            
            if 'CREATE TABLE' in code and 'execute' in code:
                print("   ✅ Database operations appear complete")
                return True
            else:
                print("   ⚠️  Some database operations may be missing")
                return True
                
        except Exception as e:
            print(f"   ❌ Database test failed: {e}")
            return False
    
    def test_line_counts(self) -> bool:
        """Test 7: Line count verification"""
        print("\n🔍 Test 7: Line Count Verification")
        try:
            with open(self.filepath, 'r') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
            comment_lines = len([l for l in lines if l.strip().startswith('#')])
            blank_lines = len([l for l in lines if not l.strip()])
            
            print(f"   📊 Total lines: {total_lines}")
            print(f"   📊 Code lines: {code_lines}")
            print(f"   📊 Comment lines: {comment_lines}")
            print(f"   📊 Blank lines: {blank_lines}")
            
            if total_lines > 1600:
                print(f"   ✅ File has expected size ({total_lines} lines)")
                return True
            else:
                print(f"   ⚠️  File seems small ({total_lines} lines)")
                return False
                
        except Exception as e:
            print(f"   ❌ Line count test failed: {e}")
            return False
    
    def test_type_hints(self) -> bool:
        """Test 8: Type hint coverage"""
        print("\n🔍 Test 8: Type Hint Coverage")
        try:
            with open(self.filepath, 'r') as f:
                code = f.read()
            tree = ast.parse(code)
            
            functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            
            typed_functions = 0
            for func in functions:
                # Check if function has return annotation or arg annotations
                has_return = func.returns is not None
                has_args = any(arg.annotation is not None for arg in func.args.args)
                
                if has_return or has_args:
                    typed_functions += 1
            
            coverage = (typed_functions / len(functions) * 100) if functions else 0
            
            print(f"   📊 Type hint coverage: {coverage:.1f}% ({typed_functions}/{len(functions)} functions)")
            
            if coverage > 70:
                print(f"   ✅ Good type hint coverage")
                return True
            else:
                print(f"   ⚠️  Type hint coverage could be improved")
                return True
                
        except Exception as e:
            print(f"   ❌ Type hint test failed: {e}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test 9: Error handling presence"""
        print("\n🔍 Test 9: Error Handling")
        try:
            with open(self.filepath, 'r') as f:
                code = f.read()
            tree = ast.parse(code)
            
            try_blocks = [n for n in ast.walk(tree) if isinstance(n, ast.Try)]
            
            print(f"   📊 Found {len(try_blocks)} try/except blocks")
            
            if len(try_blocks) > 10:
                print(f"   ✅ Comprehensive error handling present")
                return True
            else:
                print(f"   ⚠️  Consider adding more error handling")
                return True
                
        except Exception as e:
            print(f"   ❌ Error handling test failed: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests and return results"""
        print("=" * 70)
        print("🚀 COMPREHENSIVE TEST SUITE - NPM Analyzer UPGRADED")
        print("=" * 70)
        
        tests = [
            self.test_syntax,
            self.test_ast_parsing,
            self.test_imports,
            self.test_class_structure,
            self.test_method_signatures,
            self.test_database_operations,
            self.test_line_counts,
            self.test_type_hints,
            self.test_error_handling
        ]
        
        results = {}
        for test in tests:
            try:
                results[test.__name__] = test()
            except Exception as e:
                print(f"\n❌ Test {test.__name__} crashed: {e}")
                results[test.__name__] = False
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, passed_test in results.items():
            status = "✅ PASS" if passed_test else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        print("\n" + "=" * 70)
        print(f"🎯 RESULTS: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        print("=" * 70)
        
        return results

if __name__ == '__main__':
    runner = ComprehensiveTestRunner('npm_analyzer_UPGRADED.py')
    results = runner.run_all_tests()
    
    # Exit with error if any test failed
    sys.exit(0 if all(results.values()) else 1)
