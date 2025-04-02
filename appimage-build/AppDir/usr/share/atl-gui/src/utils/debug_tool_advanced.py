#!/usr/bin/env python3
"""
Advanced debug tool for ATL GUI that provides detailed function information
without mocking dependencies or using complex testing approaches.
"""
import inspect
import os
import sys
import importlib
import traceback
from types import ModuleType, FunctionType
from typing import List, Dict, Any, Callable, Optional, Tuple, Set, Union

# Import the basic debug tool components
from src.utils.debug_tool import FunctionInfo, ModuleScanner, DebugTool as BasicDebugTool

class DetailedFunctionTester:
    """Test functions and collect detailed information about them"""
    
    def __init__(self, functions: List[FunctionInfo]):
        self.functions = functions
        self.test_results: Dict[str, Dict[str, Any]] = {}
        
    def analyze_function(self, func_info: FunctionInfo) -> Dict[str, Any]:
        """Analyze a function and collect detailed information about it"""
        func = func_info.func
        result = {
            'status': 'INFO',  # We're not actually testing, just analyzing
            'error': None,
            'function': func_info,
            'details': {}
        }
        
        try:
            # Get basic function information
            details = {
                'name': func_info.name,
                'module': func_info.module_name,
                'is_method': func_info.is_method,
            }
            
            if func_info.is_method:
                details['class'] = func_info.class_name
            
            # Source code information
            if hasattr(func, '__code__'):
                details['file'] = func.__code__.co_filename
                details['line'] = func.__code__.co_firstlineno
                details['end_line'] = details['line'] + func.__code__.co_linetable[-1] if hasattr(func.__code__, 'co_linetable') and func.__code__.co_linetable else "Unknown"
            
            # Function signature
            try:
                sig = inspect.signature(func)
                details['signature'] = str(sig)
                
                # Parameter information
                params = {}
                for name, param in sig.parameters.items():
                    param_info = {
                        'kind': str(param.kind),
                        'has_default': param.default != inspect.Parameter.empty,
                    }
                    
                    if param.default != inspect.Parameter.empty:
                        param_info['default'] = repr(param.default)
                    
                    if param.annotation != inspect.Parameter.empty:
                        param_info['annotation'] = str(param.annotation)
                    
                    params[name] = param_info
                
                details['parameters'] = params
                
                # Return type
                if sig.return_annotation != inspect.Parameter.empty:
                    details['return_type'] = str(sig.return_annotation)
            except Exception as e:
                details['signature_error'] = str(e)
            
            # Docstring
            if func.__doc__:
                details['docstring'] = func.__doc__.strip()
            else:
                details['docstring'] = "No documentation"
            
            # Source code
            try:
                source = inspect.getsource(func)
                # Limit source code to 1000 characters to avoid excessive output
                if len(source) > 1000:
                    source = source[:997] + "..."
                details['source'] = source
            except Exception as e:
                details['source_error'] = str(e)
            
            result['details'] = details
            
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = f"Analysis error: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        
        return result
    
    def analyze_all_functions(self) -> Dict[str, Dict[str, Any]]:
        """Analyze all functions and collect information about them"""
        print(f"Analyzing {len(self.functions)} functions...")
        
        for func_info in self.functions:
            func_str = str(func_info)
            try:
                result = self.analyze_function(func_info)
                self.test_results[func_str] = result
            except Exception as e:
                self.test_results[func_str] = {
                    'status': 'ERROR',
                    'error': f"Analysis error: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}",
                    'function': func_info,
                    'details': {}
                }
        
        print(f"Analysis complete. Collected details for {len(self.test_results)} functions.")
        return self.test_results


class AdvancedDebugTool(BasicDebugTool):
    """
    Advanced debug tool that provides detailed information about functions
    without changing their behavior or mocking dependencies.
    """
    
    def __init__(self, base_package: str = 'src'):
        """Initialize the advanced debug tool"""
        super().__init__(base_package)
        self.should_open_app = False
        os.environ['ATL_NO_LAUNCH'] = '1'  # Prevent app from launching
    
    def advanced_test_functions(self) -> Dict[str, Dict[str, Any]]:
        """Analyze functions and collect detailed information about them"""
        print("\nCollecting detailed function information...")
        
        if not self.functions:
            self.scan_codebase()
        
        # Use the detailed tester to collect function information
        tester = DetailedFunctionTester(self.functions)
        self.test_results = tester.analyze_all_functions()
        
        return self.test_results
    
    def print_advanced_results(self) -> None:
        """Print detailed function information"""
        if not self.test_results:
            self.advanced_test_functions()
        
        print("\n=== DETAILED FUNCTION INFORMATION ===")
        print(f"Total functions analyzed: {len(self.test_results)}")
        
        # Group by module
        modules = {}
        for func_str, result in self.test_results.items():
            module_name = result['function'].module_name
            if module_name not in modules:
                modules[module_name] = []
            modules[module_name].append(result)
        
        # Print results by module
        for module_name, results in sorted(modules.items()):
            print(f"\n==== Module: {module_name} ({len(results)} functions) ====")
            
            # Print details of each function
            for result in sorted(results, key=lambda r: r['function'].name):
                func_info = result['function']
                details = result.get('details', {})
                
                # Print function name and signature
                if func_info.is_method:
                    print(f"\n  {func_info.class_name}.{func_info.name}{func_info.signature}")
                    print(f"    Type: Class method in {func_info.class_name}")
                else:
                    print(f"\n  {func_info.name}{func_info.signature}")
                    print(f"    Type: Function")
                
                # Print file and line information
                if 'file' in details:
                    print(f"    File: {details['file']}")
                    print(f"    Line: {details['line']}")
                
                # Print docstring
                if 'docstring' in details:
                    docstring = details['docstring']
                    if len(docstring) > 200:
                        docstring = docstring[:197] + "..."
                    print(f"    Docstring: {docstring}")
                
                # Print parameter information
                if 'parameters' in details and details['parameters']:
                    print(f"    Parameters:")
                    for name, param_info in details['parameters'].items():
                        param_str = f"      - {name}"
                        if 'annotation' in param_info:
                            param_str += f" ({param_info['annotation']})"
                        if 'has_default' in param_info and param_info['has_default']:
                            param_str += f" = {param_info['default']}"
                        print(param_str)
                
                # Print return type
                if 'return_type' in details:
                    print(f"    Returns: {details['return_type']}")
                
                # Print first 3 lines of source if available
                if 'source' in details:
                    source_lines = details['source'].strip().split('\n')
                    print(f"    Source (first 3 lines):")
                    for i in range(min(3, len(source_lines))):
                        print(f"      {source_lines[i]}")
                    if len(source_lines) > 3:
                        print("      ...")
                
                # Print any errors
                if result['error']:
                    print(f"    Error: {result['error'].split('\\n')[0]}")


def run_advanced_debug_tool():
    """Run the advanced debug tool on the ATL GUI codebase"""
    print("\n=== ATL GUI Advanced Debug Tool ===")
    print("This tool analyzes functions and provides detailed information without launching the application.")
    
    # Prevent app launch
    os.environ['ATL_NO_LAUNCH'] = '1'
    
    debug_tool = AdvancedDebugTool()
    debug_tool.should_open_app = False
    
    print("Scanning codebase for functions...")
    debug_tool.scan_codebase()
    
    print(f"Found {len(debug_tool.functions)} functions to analyze.")
    debug_tool.advanced_test_functions()
    debug_tool.print_advanced_results()
    
    print("\nAnalysis complete. Application was NOT launched.")


if __name__ == "__main__":
    run_advanced_debug_tool() 