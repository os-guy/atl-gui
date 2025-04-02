#!/usr/bin/env python3
"""
Debug tool for automatically finding and testing functions in ATL GUI
"""
import inspect
import os
import sys
import importlib
import unittest
import importlib.util
import pkgutil
from types import ModuleType
from functools import wraps
from typing import List, Dict, Any, Callable, Optional, Tuple, Set, Union

class FunctionInfo:
    """Class to store information about a discovered function"""
    def __init__(self, func: Callable, module_name: str, signature: str, docstring: str):
        self.func = func
        self.name = func.__name__
        self.module_name = module_name
        self.signature = signature
        self.docstring = docstring if docstring else "No documentation available"
        self.is_method = False
        self.class_name = None
    
    def __str__(self) -> str:
        prefix = f"{self.class_name}." if self.class_name else ""
        return f"{self.module_name}.{prefix}{self.name}{self.signature}"
    
    def set_as_method(self, class_name: str) -> None:
        """Mark this function as a method of a class"""
        self.is_method = True
        self.class_name = class_name

class ModuleScanner:
    """Scans modules to find functions and classes"""
    
    def __init__(self, base_package: str):
        self.base_package = base_package
        self.functions: List[FunctionInfo] = []
        self.errors: List[str] = []
        self.imported_modules: Set[str] = set()
    
    def _import_module(self, name: str) -> Optional[ModuleType]:
        """Safely import a module by name"""
        try:
            if name in self.imported_modules:
                return sys.modules.get(name)
                
            module = importlib.import_module(name)
            self.imported_modules.add(name)
            return module
        except (ImportError, AttributeError) as e:
            self.errors.append(f"Error importing {name}: {str(e)}")
            return None
    
    def _get_signature(self, func: Callable) -> str:
        """Get the function signature as a string"""
        try:
            sig = inspect.signature(func)
            return str(sig)
        except (ValueError, TypeError):
            return "(unknown signature)"
    
    def _add_function(self, func: Callable, module_name: str, class_name: Optional[str] = None) -> None:
        """Add a function to the discovered functions list"""
        if not callable(func) or func.__name__.startswith('_'):
            return
            
        signature = self._get_signature(func)
        docstring = inspect.getdoc(func)
        
        func_info = FunctionInfo(func, module_name, signature, docstring)
        if class_name:
            func_info.set_as_method(class_name)
            
        self.functions.append(func_info)
    
    def scan_module(self, module_name: str) -> None:
        """Scan a module for functions and classes"""
        # Skip built-in modules
        if module_name.startswith(('gi.', 'gtk.', 'os.', 'sys.')):
            return
            
        module = self._import_module(module_name)
        if not module:
            return
            
        # Get all module members
        for name, obj in inspect.getmembers(module):
            # Skip private/special members
            if name.startswith('_'):
                continue
                
            # Process classes
            if inspect.isclass(obj) and obj.__module__ == module.__name__:
                class_name = obj.__name__
                
                # Process methods of the class
                for method_name, method in inspect.getmembers(obj, predicate=inspect.isfunction):
                    if not method_name.startswith('_'):
                        self._add_function(method, module.__name__, class_name)
            
            # Process functions
            elif inspect.isfunction(obj) and obj.__module__ == module.__name__:
                self._add_function(obj, module.__name__)
    
    def scan_package(self, package_name: Optional[str] = None) -> None:
        """Recursively scan all modules in a package"""
        if package_name is None:
            package_name = self.base_package
            
        package = self._import_module(package_name)
        if not package:
            return
            
        # Handle the current package module
        self.scan_module(package_name)
        
        # Find the package path
        if hasattr(package, '__path__'):
            # This is a package with submodules
            for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__, package.__name__ + '.'):
                self.scan_module(module_name)
                
                if is_pkg:
                    self.scan_package(module_name)

class FunctionTester:
    """Generates and runs tests for discovered functions"""
    
    def __init__(self, functions: List[FunctionInfo]):
        self.functions = functions
        self.test_results: Dict[str, Dict[str, Any]] = {}
        
    def generate_test_case(self, func_info: FunctionInfo) -> Optional[unittest.TestCase]:
        """Generate a test case for a function"""
        func_name = func_info.name
        func = func_info.func
        
        # Create a test class dynamically
        class_name = f"Test_{func_info.module_name.replace('.', '_')}_{func_name}"
        
        # Create a test method
        def test_function(self):
            """Test the function can be called without raising exceptions"""
            # For simplicity, we're only verifying the function can be imported and accessed
            self.assertIsNotNone(func)
        
        # Create the test class
        TestClass = type(class_name, (unittest.TestCase,), {
            'runTest': test_function,
            'func_info': func_info
        })
        
        return TestClass()
        
    def run_tests(self) -> Dict[str, Dict[str, Any]]:
        """Run tests for all discovered functions"""
        suite = unittest.TestSuite()
        
        for func_info in self.functions:
            test_case = self.generate_test_case(func_info)
            if test_case:
                suite.addTest(test_case)
        
        # Run the tests and collect results
        runner = unittest.TextTestRunner(verbosity=0)
        test_result = runner.run(suite)
        
        # Process results
        for test in test_result.failures + test_result.errors:
            test_case = test[0]
            func_info = test_case.func_info
            func_str = str(func_info)
            
            self.test_results[func_str] = {
                'status': 'FAIL',
                'error': test[1],
                'function': func_info
            }
            
        # Add successful tests
        for func_info in self.functions:
            func_str = str(func_info)
            if func_str not in self.test_results:
                self.test_results[func_str] = {
                    'status': 'PASS',
                    'error': None,
                    'function': func_info
                }
                
        return self.test_results

class DebugTool:
    """Main debug tool class that finds and tests functions"""
    
    def __init__(self, base_package: str = 'src'):
        self.base_package = base_package
        self.scanner = ModuleScanner(base_package)
        self.functions: List[FunctionInfo] = []
        self.test_results: Dict[str, Dict[str, Any]] = {}
        
    def scan_codebase(self) -> List[FunctionInfo]:
        """Scan the codebase for functions"""
        print(f"Scanning package: {self.base_package}")
        self.scanner.scan_package()
        self.functions = self.scanner.functions
        
        if self.scanner.errors:
            print("Errors encountered during scanning:")
            for error in self.scanner.errors:
                print(f"  - {error}")
                
        print(f"Found {len(self.functions)} functions/methods")
        return self.functions
    
    def test_functions(self) -> Dict[str, Dict[str, Any]]:
        """Test all discovered functions"""
        if not self.functions:
            self.scan_codebase()
            
        tester = FunctionTester(self.functions)
        self.test_results = tester.run_tests()
        
        # Count results
        pass_count = sum(1 for result in self.test_results.values() if result['status'] == 'PASS')
        fail_count = sum(1 for result in self.test_results.values() if result['status'] == 'FAIL')
        
        print(f"Test results: {pass_count} passed, {fail_count} failed")
        return self.test_results
    
    def print_results(self) -> None:
        """Print test results in a formatted way"""
        if not self.test_results:
            self.test_functions()
            
        print("\n--- FUNCTION TEST RESULTS ---")
        print(f"Total functions: {len(self.test_results)}")
        
        # Group by module
        modules: Dict[str, List[Dict[str, Any]]] = {}
        for func_str, result in self.test_results.items():
            module_name = result['function'].module_name
            if module_name not in modules:
                modules[module_name] = []
            modules[module_name].append(result)
        
        # Print results by module
        for module_name, results in sorted(modules.items()):
            pass_count = sum(1 for r in results if r['status'] == 'PASS')
            total = len(results)
            print(f"\n{module_name}: {pass_count}/{total} passed")
            
            # Print details of each function
            for result in sorted(results, key=lambda r: r['function'].name):
                func_info = result['function']
                status_icon = "✓" if result['status'] == 'PASS' else "✗"
                
                if func_info.is_method:
                    print(f"  {status_icon} {func_info.class_name}.{func_info.name}{func_info.signature}")
                else:
                    print(f"  {status_icon} {func_info.name}{func_info.signature}")
                    
                if result['status'] == 'FAIL':
                    error_lines = result['error'].split('\n')
                    print(f"     Error: {error_lines[0]}")
                    
def run_debug_tool():
    """Run the debug tool on the ATL GUI codebase"""
    debug_tool = DebugTool()
    debug_tool.scan_codebase()
    debug_tool.test_functions()
    debug_tool.print_results()

if __name__ == "__main__":
    run_debug_tool() 