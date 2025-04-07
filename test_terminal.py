#!/usr/bin/env python3
"""
Simple test script to verify that the terminal module works correctly by itself.
This script initializes the terminal module, runs a simple command, and cleans up.
"""
import os
import sys
import time
from src.utils.terminal_module import TerminalManager

def test_terminal_module():
    """Test the terminal module with a simple command."""
    print(f"Main process PID: {os.getpid()}")
    
    # Initialize terminal manager
    terminal = TerminalManager()
    print("Terminal manager initialized")
    
    # Start the terminal process
    if terminal.start():
        print("Terminal process started successfully")
    else:
        print("Failed to start terminal process")
        return
    
    # Check if it's running
    if terminal.check_health():
        print("Terminal process is healthy")
    else:
        print("Terminal process is not healthy")
        return
    
    # Run a simple command
    print("Running 'ls -la' command...")
    terminal.execute_command("ls -la", shell=True)
    
    # Get output for a few seconds
    start_time = time.time()
    while time.time() - start_time < 5:  # Get output for up to 5 seconds
        output = terminal.get_output()
        if output:
            print("Received output:")
            for msg in output:
                print(f"  {msg['status']}: {msg.get('message', '')[:100]}")
        time.sleep(0.1)
    
    # Clean up
    print("Stopping terminal process...")
    terminal.stop()
    print("Test completed")

if __name__ == "__main__":
    print("Starting terminal module test")
    test_terminal_module()
    print("Test finished") 