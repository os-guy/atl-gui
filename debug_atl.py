#!/usr/bin/env python3
"""
Command-line script to run the debug tool for ATL GUI
"""
import sys
import os
import argparse
from pathlib import Path

# Add the project directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.utils.debug_tool import DebugTool
from src.utils.debug_tool_advanced import AdvancedDebugTool

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="ATL GUI Debug Tool - Automatically find and test functions in the codebase"
    )
    
    parser.add_argument(
        "--package", "-p",
        default="src",
        help="Base package to scan (default: src)"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output file to save results (default: print to console)"
    )
    
    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="Only scan for functions without running tests"
    )
    
    parser.add_argument(
        "--module", "-m",
        help="Scan only a specific module (e.g., 'src.handlers')"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show more detailed output"
    )
    
    parser.add_argument(
        "--advanced",
        action="store_true",
        help="Use advanced testing with mock dependencies"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode, asking which debug mode to use"
    )
    
    return parser.parse_args()

def save_results_to_file(results, output_path, advanced=False):
    """Save test results to a file"""
    with open(output_path, 'w') as f:
        f.write("# ATL GUI Debug Tool Results\n\n")
        
        if advanced:
            f.write("*Using advanced mode with detailed function information*\n\n")
        else:
            f.write("*Using normal testing mode*\n\n")
        
        # Count total functions
        total = len(results)
        
        if advanced:
            # For advanced mode, just count functions analyzed
            f.write(f"## Summary\n")
            f.write(f"- Total functions analyzed: {total}\n\n")
        else:
            # For normal mode, count pass/fail
            passed = sum(1 for r in results.values() if r['status'] == 'PASS')
            failed = sum(1 for r in results.values() if r['status'] != 'PASS')
            
            f.write(f"## Summary\n")
            f.write(f"- Total functions: {total}\n")
            f.write(f"- Passed: {passed}\n")
            f.write(f"- Failed: {failed}\n\n")
        
        # Group by module
        modules = {}
        for func_str, result in results.items():
            module_name = result['function'].module_name
            if module_name not in modules:
                modules[module_name] = []
            modules[module_name].append(result)
        
        # Write results by module
        f.write("## Results by Module\n\n")
        for module_name, module_results in sorted(modules.items()):
            if advanced:
                f.write(f"### {module_name}: {len(module_results)} functions\n\n")
            else:
                pass_count = sum(1 for r in module_results if r['status'] == 'PASS')
                total = len(module_results)
                f.write(f"### {module_name}: {pass_count}/{total} passed\n\n")
            
            # Write results for each function
            for result in sorted(module_results, key=lambda r: r['function'].name):
                func_info = result['function']
                
                if advanced:
                    # For advanced mode, show function information
                    if func_info.is_method:
                        f.write(f"#### {func_info.class_name}.{func_info.name}{func_info.signature}\n\n")
                    else:
                        f.write(f"#### {func_info.name}{func_info.signature}\n\n")
                    
                    details = result.get('details', {})
                    
                    # Basic information
                    f.write("**Type:** ")
                    f.write("Class method" if func_info.is_method else "Function")
                    f.write("\n\n")
                    
                    # Source location
                    if 'file' in details:
                        f.write(f"**Source:** {details['file']}:{details['line']}\n\n")
                    
                    # Docstring
                    if 'docstring' in details and details['docstring'] != "No documentation":
                        f.write(f"**Documentation:**\n\n```\n{details['docstring']}\n```\n\n")
                    
                    # Parameters
                    if 'parameters' in details and details['parameters']:
                        f.write("**Parameters:**\n\n")
                        for name, param_info in details['parameters'].items():
                            param_str = f"- `{name}`"
                            if 'annotation' in param_info:
                                param_str += f" ({param_info['annotation']})"
                            if 'has_default' in param_info and param_info['has_default']:
                                param_str += f" = {param_info['default']}"
                            f.write(param_str + "\n")
                        f.write("\n")
                    
                    # Return type
                    if 'return_type' in details:
                        f.write(f"**Returns:** {details['return_type']}\n\n")
                    
                    # First few lines of source code
                    if 'source' in details:
                        source_lines = details['source'].strip().split("\n")
                        if len(source_lines) > 10:
                            source_preview = "\n".join(source_lines[:10]) + "\n..."
                        else:
                            source_preview = details['source'].strip()
                        f.write(f"**Source Code:**\n\n```python\n{source_preview}\n```\n\n")
                    
                    # Any errors
                    if result['error']:
                        f.write(f"**Error:** {result['error'].split('\\n')[0]}\n\n")
                
                else:
                    # For normal mode, show pass/fail status
                    status = "✓ PASS" if result['status'] == 'PASS' else "✗ FAIL"
                    
                    if func_info.is_method:
                        f.write(f"- **{status}** `{func_info.class_name}.{func_info.name}{func_info.signature}`\n")
                    else:
                        f.write(f"- **{status}** `{func_info.name}{func_info.signature}`\n")
                        
                    if result['status'] != 'PASS':
                        error_lines = result['error'].split('\n')
                        f.write(f"  - Error: {error_lines[0]}\n")
                
            f.write("\n")
    
    print(f"Results saved to {output_path}")

def main():
    """Main entry point for the debug tool"""
    args = parse_args()
    
    # Always ask user which debug mode to use, unless explicitly specified with --advanced flag
    if not args.advanced and not args.scan_only:
        use_advanced = input("\nWhich debug mode would you like to use?\n1. Normal Debug (tests functions)\n2. Advanced Debug (shows detailed function information)\nYour choice (1/2): ")
        args.advanced = use_advanced.strip() == "2"
        
        if args.advanced:
            print("Using advanced debug mode...")
        else:
            print("Using normal debug mode...")
    elif args.advanced and not args.interactive:
        print("Using advanced debug mode...")
    
    # Prevent app launch when in debug mode
    os.environ['ATL_NO_LAUNCH'] = '1'
    
    # Determine which debug tool to use
    if args.advanced:
        debug_tool = AdvancedDebugTool(base_package=args.package)
    else:
        debug_tool = DebugTool(base_package=args.package)
    
    # Scan the codebase
    if args.module:
        # Scan just one module
        scanner = debug_tool.scanner
        scanner.scan_module(args.module)
        debug_tool.functions = scanner.functions
        
        if scanner.errors and args.verbose:
            print("Errors encountered during scanning:")
            for error in scanner.errors:
                print(f"  - {error}")
        
        print(f"Found {len(debug_tool.functions)} functions/methods in module {args.module}")
    else:
        # Scan the whole package
        debug_tool.scan_codebase()
    
    # Run tests or analysis if not in scan-only mode
    if not args.scan_only:
        if args.advanced:
            print("Collecting detailed function information...")
            debug_tool.advanced_test_functions()
        else:
            print("Testing functions...")
            debug_tool.test_functions()
        
        if args.output:
            # Save results to file
            save_results_to_file(debug_tool.test_results, args.output, args.advanced)
        else:
            # Print results to console
            if args.advanced:
                debug_tool.print_advanced_results()
            else:
                debug_tool.print_results()
    
    print("Debug analysis complete. Exiting without starting application.")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 