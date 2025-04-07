#!/usr/bin/env python3
"""
ATL GUI - Android Translation Layer GUI Application
This is the main entry point that starts the application
"""
import sys
import os
import argparse
import tempfile
import atexit
import time

# GLOBAL EXECUTION GUARD - Exit immediately if another instance is running with the same flags
if "--force-main-window" in sys.argv and "--skip-setup" in sys.argv:
    # Check if we're being launched via subprocess
    if 'ATL_SINGLETON_PID' in os.environ:
        # Make sure we're actually a duplicate process
        parent_pid = os.environ.get('ATL_SINGLETON_PID')
        # If our parent already exited, allow this process to continue
        try:
            # Try to check if parent process exists on Unix
            if sys.platform != "win32" and parent_pid and int(parent_pid) > 0:
                try:
                    # Check if the process exists by sending signal 0 (no effect)
                    os.kill(int(parent_pid), 0)
                    # If we get here, the parent is still running - this is a duplicate
                    print(f"[DEBUG] Detected duplicate app launch (parent PID {parent_pid} still running)")
                    print("[DEBUG] Exiting immediately to prevent multiple windows")
                    sys.exit(0)
                except OSError:
                    # Parent process no longer exists - allow this one to continue
                    print(f"[DEBUG] Parent process {parent_pid} no longer exists, allowing this instance to run")
            elif parent_pid:
                # For Windows or other platforms, just print a message and continue
                print(f"[DEBUG] Launched by process {parent_pid} but will continue since parent may have exited")
        except Exception as e:
            print(f"[DEBUG] Error checking parent process: {e}")
            # Continue anyway in case of error
    
    # We're the first instance with these flags or our parent exited, set environment variable
    os.environ['ATL_SINGLETON_PID'] = str(os.getpid())
    print(f"[DEBUG] Set ATL_SINGLETON_PID={os.getpid()}")

# Add the project directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Create a singleton lock file
def create_singleton_lock():
    """Create a lock file to prevent multiple instances"""
    lock_file = os.path.join(tempfile.gettempdir(), "atl-gui.lock")
    
    # Check if the lock file exists
    if os.path.exists(lock_file):
        try:
            # Read the PID from the lock file
            with open(lock_file, 'r') as f:
                pid_str = f.read().strip()
                if pid_str and pid_str.isdigit():
                    pid = int(pid_str)
                    # Check if the process is still running
                    try:
                        if sys.platform != "win32":
                            # Unix-like - send signal 0 to check process exists
                            os.kill(pid, 0)
                            # Process exists
                            file_age = time.time() - os.path.getmtime(lock_file)
                            if file_age < 30:  # Lock is recent (30 seconds)
                                print(f"[DEBUG] Another instance is already running (PID: {pid}, lock file age: {file_age:.1f}s)")
                                return False
                            else:
                                print(f"[DEBUG] Found stale lock file from PID {pid} ({file_age:.1f}s old)")
                        else:
                            # On Windows, we can't easily check if a process exists
                            file_age = time.time() - os.path.getmtime(lock_file)
                            if file_age < 30:  # Consider the lock valid if it's less than 30 seconds old
                                print(f"[DEBUG] Found recent lock file (age: {file_age:.1f}s), assuming another instance is running")
                                return False
                    except OSError:
                        # Process doesn't exist, we can remove the lock file
                        print(f"[DEBUG] Process {pid} from lock file no longer exists")
        except Exception as e:
            print(f"[DEBUG] Error reading lock file: {e}")
        
        # If we got here, try to remove the lock file
        try:
            os.remove(lock_file)
            print(f"[DEBUG] Removed stale lock file: {lock_file}")
        except Exception as e:
            print(f"[WARNING] Could not remove stale lock file: {e}")
    
    # Create the lock file
    try:
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
        
        # Register cleanup to remove the lock file when we exit
        def cleanup_lock():
            try:
                if os.path.exists(lock_file):
                    # Make sure it's our lock file by checking the PID
                    try:
                        with open(lock_file, 'r') as f:
                            pid_str = f.read().strip()
                            if pid_str and pid_str.isdigit() and int(pid_str) == os.getpid():
                                os.remove(lock_file)
                                print(f"[DEBUG] Removed our lock file at exit: {lock_file}")
                    except Exception:
                        # If we can't read it, just try to remove it
                        os.remove(lock_file)
            except Exception as e:
                print(f"[WARNING] Failed to remove lock file at exit: {e}")
        
        atexit.register(cleanup_lock)
        
        print(f"[DEBUG] Created lock file: {lock_file}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create lock file: {e}")
        return False

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
    
    parser.add_argument(
        "--force-main-window",
        action="store_true",
        help="Force the main window to show even if first run"
    )
    
    parser.add_argument(
        "--skip-setup",
        action="store_true",
        help="Skip setup even if first run"
    )
    
    parser.add_argument(
        "--allow-multiple-instances",
        action="store_true",
        help="Allow multiple instances of the application to run simultaneously"
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
    
    # Check if we should enforce singleton behavior
    if not args.allow_multiple_instances:
        # Create lock file to prevent multiple instances
        if not create_singleton_lock():
            print("[ERROR] Failed to create singleton lock, but continuing anyway")
    
    # Configure display backend first
    configure_display_backend(args)
    
    # Run the debug tool if requested
    if args.debug or args.debug_advanced or args.debug_interactive:
        run_debug_tool(args)
        print("Debug mode completed. Exiting without starting application.")
        sys.exit(0)
    
    # Start the main application 
    if args.force_main_window or args.skip_setup:
        print("Starting with special flags:", end=" ")
        if args.force_main_window:
            print("force-main-window", end=" ")
        if args.skip_setup:
            print("skip-setup", end=" ")
        print()
        
        # Import the app module and force main window
        from src.app import AtlGUIApp
        app = AtlGUIApp()
        app.do_activate(force_main_window=True)
        sys.exit(app.run(None))
    else:
        # Normal startup
        sys.exit(main()) 