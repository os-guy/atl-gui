import subprocess
import multiprocessing
import queue
import time
import os
import signal
import sys
from typing import Dict, Optional, List, Tuple

print("[DEBUG] Terminal module imported!")

class TerminalProcess(multiprocessing.Process):
    """
    A separate process for handling terminal commands.
    This isolates the terminal functionality so if it crashes,
    it won't affect the main application.
    """
    
    def __init__(self, command_queue, output_queue, exit_event):
        """
        Initialize the terminal process.
        
        Args:
            command_queue: Queue for receiving commands from the main process
            output_queue: Queue for sending output back to the main process
            exit_event: Event to signal when the process should exit
        """
        super().__init__()
        self.command_queue = command_queue
        self.output_queue = output_queue
        self.exit_event = exit_event
        self.current_process = None
        self.daemon = True  # Allow the process to exit when the main program exits
        print(f"[DEBUG] TerminalProcess initialized with PID: {os.getpid()}")
    
    def run(self):
        """Main process loop that waits for commands and processes them."""
        print(f"[DEBUG] TerminalProcess run() started with PID: {os.getpid()}")
        try:
            while not self.exit_event.is_set():
                try:
                    # Check for new commands with a timeout to allow checking the exit event
                    command = self.command_queue.get(timeout=0.1)
                    print(f"[DEBUG] Terminal process received command: {command['action']}")
                    
                    if command["action"] == "execute":
                        self._execute_command(
                            command["command"],
                            command["shell"],
                            command["env_vars"]
                        )
                    elif command["action"] == "terminate":
                        self._terminate_process()
                    elif command["action"] == "ping":
                        # Respond to ping to verify the process is still alive
                        self.output_queue.put({"status": "alive", "message": "Terminal process is running"})
                    elif command["action"] == "exit":
                        # Exit the process
                        print("[DEBUG] Terminal process received exit command")
                        self._terminate_process()
                        break
                        
                except queue.Empty:
                    # No commands in queue, continue waiting
                    continue
                except Exception as e:
                    # Send error back to main process
                    error_msg = f"Terminal process error: {str(e)}"
                    print(f"[DEBUG] {error_msg}")
                    self.output_queue.put({"status": "error", "message": error_msg})
                    
            # Clean up before exiting
            print("[DEBUG] Terminal process exiting, cleaning up")
            self._terminate_process()
                    
        except Exception as e:
            # Log any unexpected errors
            print(f"[DEBUG] Terminal process crashed with error: {str(e)}")
            # Try to notify main process
            try:
                self.output_queue.put({"status": "crashed", "message": str(e)})
            except:
                pass
    
    def _execute_command(self, command, shell=True, env_vars=None):
        """
        Execute a command and stream output back to the main process.
        
        Args:
            command: Command string to execute
            shell: Whether to use shell=True
            env_vars: Environment variables dictionary
        """
        # Terminate any existing process first
        self._terminate_process()
        
        try:
            # Prepare environment variables
            env = os.environ.copy()
            if env_vars:
                env.update(env_vars)
            
            print(f"[DEBUG] Terminal executing command: {command}")
            
            # Start the process
            self.current_process = subprocess.Popen(
                command,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            
            # Notify main process that command has started
            self.output_queue.put({
                "status": "started",
                "message": f"Command started: {command}"
            })
            
            # Process stdout and stderr
            while self.current_process.poll() is None:
                # Check if we should exit
                if self.exit_event.is_set():
                    self._terminate_process()
                    return
                
                # Read stdout
                stdout_line = self.current_process.stdout.readline()
                if stdout_line:
                    self.output_queue.put({
                        "status": "output",
                        "stream": "stdout",
                        "message": stdout_line
                    })
                
                # Read stderr
                stderr_line = self.current_process.stderr.readline()
                if stderr_line:
                    self.output_queue.put({
                        "status": "output",
                        "stream": "stderr",
                        "message": stderr_line
                    })
                
                # Small sleep to prevent tight loop
                if not stdout_line and not stderr_line:
                    time.sleep(0.01)
            
            # Process any remaining output
            for line in self.current_process.stdout:
                self.output_queue.put({
                    "status": "output",
                    "stream": "stdout",
                    "message": line
                })
            
            for line in self.current_process.stderr:
                self.output_queue.put({
                    "status": "output",
                    "stream": "stderr",
                    "message": line
                })
            
            # Send exit code
            exit_code = self.current_process.returncode
            print(f"[DEBUG] Command completed with exit code {exit_code}")
            self.output_queue.put({
                "status": "completed",
                "exit_code": exit_code,
                "message": f"Command completed with exit code {exit_code}"
            })
            
            # Clear reference to completed process
            self.current_process = None
            
        except Exception as e:
            error_msg = f"Error executing command: {str(e)}"
            print(f"[DEBUG] {error_msg}")
            self.output_queue.put({
                "status": "error",
                "message": error_msg
            })
    
    def _terminate_process(self):
        """Immediately terminate the current process if it exists."""
        if self.current_process:
            try:
                process_pid = self.current_process.pid
                print(f"[DEBUG] Forcefully terminating process with PID: {process_pid}")
                
                # Skip graceful termination and use SIGKILL immediately for instant termination
                try:
                    # Send SIGKILL for immediate termination
                    os.kill(process_pid, signal.SIGKILL)
                    print(f"[DEBUG] SIGKILL sent to process {process_pid}")
                    
                    # Brief wait to confirm termination
                    try:
                        self.current_process.wait(timeout=0.5)
                    except subprocess.TimeoutExpired:
                        print(f"[DEBUG] Process {process_pid} still not terminated, trying alternative methods")
                        # Try additional termination techniques as fallback
                        self.current_process.kill()
                except Exception as e:
                    print(f"[DEBUG] Error during SIGKILL: {e}, trying fallback kill")
                    self.current_process.kill()
                    
                # Ensure stdout/stderr are closed to prevent hanging
                try:
                    if hasattr(self.current_process, 'stdout') and self.current_process.stdout:
                        self.current_process.stdout.close()
                    if hasattr(self.current_process, 'stderr') and self.current_process.stderr:
                        self.current_process.stderr.close()
                except Exception as e:
                    print(f"[DEBUG] Error closing streams: {e}")
                    
                # Notify completion
                self.output_queue.put({
                    "status": "terminated",
                    "message": f"Process {process_pid} forcefully terminated"
                })
            except Exception as e:
                error_msg = f"Error terminating process: {str(e)}"
                print(f"[DEBUG] {error_msg}")
                self.output_queue.put({
                    "status": "error",
                    "message": error_msg
                })
            finally:
                self.current_process = None


class TerminalManager:
    """
    Manages communication with the terminal process from the main application.
    """
    
    def __init__(self):
        """Initialize the terminal manager."""
        print(f"[DEBUG] TerminalManager initialized in process {os.getpid()}")
        self.command_queue = multiprocessing.Queue()
        self.output_queue = multiprocessing.Queue()
        self.exit_event = multiprocessing.Event()
        self.terminal_process = None
        self.is_running = False
        self._last_ping_response = 0
        
    def start(self):
        """Start the terminal process."""
        if not self.is_running:
            print("[DEBUG] Starting terminal process")
            try:
                # Create and start the terminal process
                self.terminal_process = TerminalProcess(
                    self.command_queue,
                    self.output_queue,
                    self.exit_event
                )
                self.terminal_process.start()
                self.is_running = True
                print(f"[DEBUG] Terminal process started with PID: {self.terminal_process.pid}")
                return True
            except Exception as e:
                print(f"[DEBUG] Error starting terminal process: {str(e)}")
                self.is_running = False
                return False
        return False
    
    def restart(self):
        """Restart the terminal process if it has crashed."""
        print("[DEBUG] Restarting terminal process")
        self.stop()
        time.sleep(0.5)  # Give it a moment to clean up
        return self.start()
    
    def stop(self):
        """Stop the terminal process."""
        if self.is_running:
            print("[DEBUG] Stopping terminal process")
            # Signal the process to exit
            self.exit_event.set()
            try:
                # Send exit command
                self.command_queue.put({"action": "exit"})
                # Wait for process to terminate
                if self.terminal_process:
                    print(f"[DEBUG] Waiting for terminal process {self.terminal_process.pid} to exit...")
                    self.terminal_process.join(timeout=5)
                    if self.terminal_process.is_alive():
                        print(f"[DEBUG] Terminal process {self.terminal_process.pid} still alive, terminating forcefully")
                        self.terminal_process.terminate()
            except Exception as e:
                print(f"[DEBUG] Error stopping terminal process: {str(e)}")
            finally:
                # Reset state
                self.is_running = False
                self.terminal_process = None
                self.exit_event.clear()
                
                # Create new queues to ensure clean state
                self.command_queue = multiprocessing.Queue()
                self.output_queue = multiprocessing.Queue()
                
                print("[DEBUG] Terminal process stopped")
            return True
        return False
    
    def execute_command(self, command, shell=True, env_vars=None):
        """
        Execute a command in the terminal process.
        
        Args:
            command: Command string to execute
            shell: Whether to use shell=True
            env_vars: Environment variables dictionary
        
        Returns:
            bool: True if command was sent, False if terminal process isn't running
        """
        if self.is_running:
            print(f"[DEBUG] Sending execute command: {command[:50]}...")
            try:
                self.command_queue.put({
                    "action": "execute",
                    "command": command,
                    "shell": shell,
                    "env_vars": env_vars
                })
                return True
            except Exception as e:
                print(f"[DEBUG] Error sending command to terminal process: {str(e)}")
                return False
        else:
            print("[DEBUG] Cannot execute command: Terminal process not running")
            return False
    
    def terminate_command(self):
        """
        Immediately terminate the currently running command.
        
        Returns:
            bool: True if terminate request was sent, False if terminal process isn't running
        """
        if self.is_running:
            print("[DEBUG] Forcefully terminating command in terminal process")
            try:
                # Send terminate command to the process
                self.command_queue.put({"action": "terminate"})
                
                # If we have access to the terminal process and it's still alive, force kill any processes
                if self.terminal_process and self.terminal_process.is_alive():
                    if hasattr(self.terminal_process, 'current_process') and self.terminal_process.current_process:
                        try:
                            # Attempt to get PID of the running command
                            pid = self.terminal_process.current_process.pid
                            if pid:
                                print(f"[DEBUG] Sending SIGKILL to process {pid} for immediate termination")
                                os.kill(pid, signal.SIGKILL)
                        except Exception as e:
                            print(f"[DEBUG] Error during force kill of command: {e}")
                
                return True
            except Exception as e:
                print(f"[DEBUG] Error sending terminate command: {str(e)}")
                return False
        return False
    
    def check_health(self):
        """
        Check if the terminal process is still healthy.
        
        Returns:
            bool: True if healthy, False if not responding
        """
        if not self.is_running or not self.terminal_process:
            print("[DEBUG] Terminal process not running in check_health")
            return False
            
        if not self.terminal_process.is_alive():
            print(f"[DEBUG] Terminal process {self.terminal_process.pid} not alive")
            return False
            
        # Send ping command
        try:
            print("[DEBUG] Sending ping to terminal process")
            self.command_queue.put({"action": "ping"})
            # Don't wait for response here, just check if process is alive
            return self.terminal_process.is_alive()
        except Exception as e:
            print(f"[DEBUG] Error sending ping: {str(e)}")
            return False
    
    def get_output(self, timeout=0.01):
        """
        Get any available output from the terminal process.
        
        Args:
            timeout: How long to wait for output (in seconds)
        
        Returns:
            List of output messages or None if no output is available
        """
        if not self.is_running:
            return None
            
        output_messages = []
        try:
            while True:
                try:
                    message = self.output_queue.get(block=True, timeout=timeout)
                    output_messages.append(message)
                    
                    # Only use timeout for the first message
                    timeout = 0
                except queue.Empty:
                    break
        except Exception as e:
            print(f"[DEBUG] Error getting output: {str(e)}")
            
        return output_messages if output_messages else None
    
    def kill_terminal(self):
        """
        Immediately kill the terminal process without exiting the application.
        This function will be called when an APK test finishes/terminates
        or when a close command is sent to the application.
        """
        print("[DEBUG] Terminal kill command received - forcefully terminating...")
        
        # First try to terminate any running command
        if self.is_running and self.terminal_process:
            # Force terminate the process immediately
            try:
                self.terminate_command()
                
                # If process still exists, kill it with os.kill to ensure immediate termination
                if self.terminal_process and self.terminal_process.is_alive():
                    pid = self.terminal_process.pid
                    if pid:
                        print(f"[DEBUG] Forcefully killing terminal process with PID {pid}")
                        try:
                            os.kill(pid, signal.SIGKILL)
                        except Exception as e:
                            print(f"[DEBUG] Error during force kill: {e}")
                
                # Immediately stop the terminal process
                self.stop()
                
                print("[DEBUG] Terminal process forcefully terminated")
                return True
            except Exception as e:
                print(f"[DEBUG] Error killing terminal: {e}")
        
        return False 