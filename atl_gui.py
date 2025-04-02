#!/usr/bin/env python3
"""
ATL GUI - Android Translation Layer GUI Application
This is the main entry point that starts the application
"""
import sys
import os
import argparse

# Add the project directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="ATL GUI - Android Translation Layer GUI Application"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run the debug tool to find and test functions before starting the application"
    )
    
    parser.add_argument(
        "--debug-advanced",
        action="store_true",
        help="Run the advanced debug tool with dependency mocking"
    )
    
    parser.add_argument(
        "--debug-module",
        help="Only debug a specific module (e.g., 'src.handlers')"
    )
    
    parser.add_argument(
        "--debug-output",
        help="Save debug results to a file"
    )
    
    parser.add_argument(
        "--debug-interactive", "-i",
        action="store_true",
        help="Run the debug tool in interactive mode, asking which debug mode to use"
    )
    
    # Add display backend options
    display_group = parser.add_argument_group('Display Backend Options')
    backend_selection = display_group.add_mutually_exclusive_group()
    backend_selection.add_argument(
        "--wayland",
        action="store_true",
        help="Force using Wayland as the display backend"
    )
    backend_selection.add_argument(
        "--x11",
        action="store_true",
        help="Force using X11 as the display backend"
    )
    display_group.add_argument(
        "--show-backend",
        action="store_true",
        help="Show which display backend is being used and exit"
    )
    
    return parser.parse_args()

def run_debug_tool(args):
    """Run the debug tool based on command-line arguments"""
    print("Running ATL GUI Debug Tool...")
    
    # Always ask user which debug mode to use, unless explicitly specified
    if not args.debug_advanced:
        use_advanced = input("\nWhich debug mode would you like to use?\n1. Normal Debug\n2. Advanced Debug (mocks dependencies)\nYour choice (1/2): ")
        args.debug_advanced = use_advanced.strip() == "2"
        
        if args.debug_advanced:
            print("Using advanced debug mode...")
        else:
            print("Using normal debug mode...")
    else:
        print("Using advanced debug mode...")
    
    # Set debug environment variable for advanced mode to prevent file dialogs
    if args.debug_advanced:
        os.environ['ATL_DEBUG_MODE'] = '1'
    
    # Import the debug tool
    if args.debug_advanced:
        from src.utils.debug_tool_advanced import AdvancedDebugTool as DebugTool
    else:
        from src.utils.debug_tool import DebugTool
    
    # Create and configure the debug tool
    debug_tool = DebugTool()
    
    # Scan the codebase
    if args.debug_module:
        scanner = debug_tool.scanner
        scanner.scan_module(args.debug_module)
        debug_tool.functions = scanner.functions
        print(f"Found {len(debug_tool.functions)} functions/methods in module {args.debug_module}")
    else:
        debug_tool.scan_codebase()
    
    # Run tests
    if args.debug_advanced:
        debug_tool.advanced_test_functions()
        if args.debug_output:
            from debug_atl import save_results_to_file
            save_results_to_file(debug_tool.test_results, args.debug_output, True)
        else:
            debug_tool.print_advanced_results()
    else:
        debug_tool.test_functions()
        if args.debug_output:
            from debug_atl import save_results_to_file
            save_results_to_file(debug_tool.test_results, args.debug_output)
        else:
            debug_tool.print_results()
    
    print("Debug testing complete.")

def configure_display_backend(args):
    """Configure the display backend based on command-line arguments"""
    from src.utils import display_backend
    
    # Configure the backend based on command-line args
    backend = display_backend.configure_backend(
        force_wayland=args.wayland,
        force_x11=args.x11
    )
    
    # If --show-backend is specified, display the backend and exit
    if args.show_backend:
        print(f"ATL GUI is using the {backend} display backend")
        # Print detailed display server information
        display_backend.print_display_info()
        sys.exit(0)
    
    return backend

from src.app import main

if __name__ == "__main__":
    args = parse_args()
    
    # Configure display backend first
    configure_display_backend(args)
    
    # Run the debug tool if requested
    if args.debug or args.debug_advanced or args.debug_interactive:
        run_debug_tool(args)
        print("Debug mode completed. Exiting without starting application.")
        sys.exit(0)
    
    # Start the main application
    sys.exit(main()) 