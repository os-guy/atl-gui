import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

# Import detect_app_status function from test_handlers
from src.handlers.test_handlers import detect_app_status

def process_terminal_output(self):
    """
    Process output from the terminal module.
    This is called periodically via GLib timeout.
    
    Returns:
        bool: True to continue calling this function, False to stop
    """
    if not hasattr(self, 'terminal_manager') or not self.terminal_manager.is_running:
        print("[DEBUG] Terminal manager not running in process_terminal_output")
        return False
        
    # Get any available output
    output_messages = self.terminal_manager.get_output()
    if not output_messages:
        # Check if the terminal process is still healthy
        if not self.terminal_manager.check_health():
            buffer = self.terminal_output.get_buffer()
            error_message = "\n\n[ERROR] Terminal process crashed. Attempting to restart...\n"
            buffer.insert(buffer.get_end_iter(), error_message)
            self.terminal_output.scroll_to_iter(buffer.get_end_iter(), 0, False, 0, 0)
            
            # Try to restart
            if self.terminal_manager.restart():
                buffer.insert(buffer.get_end_iter(), "[SYSTEM] Terminal process restarted.\n")
            else:
                buffer.insert(buffer.get_end_iter(), "[SYSTEM] Failed to restart terminal process.\n")
            
            # Either way, continue checking
            return True
            
        # No output but still healthy, keep checking
        return True
    
    # Process each message
    buffer = self.terminal_output.get_buffer()
    current_apk = self.apk_files[self.current_apk_index] if self.current_apk_index < len(self.apk_files) else None
    
    for message in output_messages:
        if message["status"] == "output":
            # Normal output from command
            buffer.insert(buffer.get_end_iter(), message["message"])
            self.terminal_output.scroll_to_iter(buffer.get_end_iter(), 0, False, 0, 0)
            
            # Save to terminal logs
            if current_apk and current_apk in self.terminal_logs:
                self.terminal_logs[current_apk] += message["message"]
                
        elif message["status"] == "completed":
            # Command finished
            buffer.insert(buffer.get_end_iter(), f"\n[COMMAND COMPLETE] Exit code: {message['exit_code']}\n")
            
            # Process terminal output for auto-detection
            if hasattr(self, 'current_apk_ready') and self.current_apk_ready and current_apk:
                # Get terminal output
                start_iter = buffer.get_start_iter()
                end_iter = buffer.get_end_iter()
                output_text = buffer.get_text(start_iter, end_iter, True)
                
                # Check output using app detection logic
                auto_detected, success_probability, detection_reason = detect_app_status(output_text)
                
                # Add detection results to terminal
                buffer.insert(buffer.get_end_iter(), f"\n\n[AUTO DETECTION] App analysis complete. Score: {success_probability}%\n")
                buffer.insert(buffer.get_end_iter(), f"[AUTO DETECTION] {detection_reason}\n")
                
                # Take action based on detection score
                if auto_detected:
                    # Application likely working
                    GLib.idle_add(self.auto_mark_as_working)
                else:
                    # Application likely not working
                    GLib.idle_add(self.auto_mark_as_not_working)
        
        elif message["status"] == "error":
            # Error from terminal process
            buffer.insert(buffer.get_end_iter(), f"\n[ERROR] {message['message']}\n")
            self.terminal_output.scroll_to_iter(buffer.get_end_iter(), 0, False, 0, 0)
            
            # Save to terminal logs
            if current_apk and current_apk in self.terminal_logs:
                self.terminal_logs[current_apk] += f"\n[ERROR] {message['message']}\n"
                
        elif message["status"] == "crashed":
            # Terminal process crashed
            buffer.insert(buffer.get_end_iter(), f"\n[SYSTEM] Terminal process crashed: {message['message']}\n")
            buffer.insert(buffer.get_end_iter(), "[SYSTEM] Attempting to restart terminal process...\n")
            self.terminal_output.scroll_to_iter(buffer.get_end_iter(), 0, False, 0, 0)
            
            # Try to restart
            if self.terminal_manager.restart():
                buffer.insert(buffer.get_end_iter(), "[SYSTEM] Terminal process restarted.\n")
            else:
                buffer.insert(buffer.get_end_iter(), "[SYSTEM] Failed to restart terminal process.\n")
    
    # Continue checking for output
    return True 

def check_terminal_health(self):
    """
    Periodically check the health of the terminal module.
    This runs independently from the process_terminal_output function.
    
    Returns:
        bool: True to continue checking, False to stop
    """
    if not hasattr(self, 'using_terminal_module') or not self.using_terminal_module:
        print("[DEBUG] Terminal module not in use in check_terminal_health")
        return False
    
    if not hasattr(self, 'terminal_manager') or not self.terminal_manager.is_running:
        print("[DEBUG] Terminal manager not running in check_terminal_health")
        return False
    
    if not hasattr(self, 'terminal_health_check_count'):
        self.terminal_health_check_count = 0
    
    # Increment check count
    self.terminal_health_check_count += 1
    
    # Only report issues every 10 checks to avoid spamming
    if not self.terminal_manager.check_health() and self.terminal_health_check_count % 10 == 0:
        # Terminal process has crashed
        buffer = self.terminal_output.get_buffer()
        buffer.insert(buffer.get_end_iter(), "\n[SYSTEM CHECK] Terminal process is not responding.\n")
        buffer.insert(buffer.get_end_iter(), "[SYSTEM CHECK] The terminal has crashed, but the main application is still running.\n")
        buffer.insert(buffer.get_end_iter(), "[SYSTEM CHECK] You can continue using the application or restart the test.\n")
        self.terminal_output.scroll_to_iter(buffer.get_end_iter(), 0, False, 0, 0)
        
        # Update status
        self.status_value_label.set_text("Terminal Crashed")
        self.status_icon.set_from_icon_name("dialog-warning-symbolic")
        
        # Show toast notification
        toast = Adw.Toast.new("Terminal process crashed but application is still running")
        toast.set_timeout(5)
        self.toast_overlay.add_toast(toast)
        
        # Try to restart
        if self.terminal_manager.restart():
            buffer.insert(buffer.get_end_iter(), "[SYSTEM CHECK] Terminal process restarted automatically.\n")
            
            # Show toast notification
            toast = Adw.Toast.new("Terminal process restarted successfully")
            self.toast_overlay.add_toast(toast)
        else:
            buffer.insert(buffer.get_end_iter(), "[SYSTEM CHECK] Failed to restart terminal process.\n")
        
        # Reset check count
        self.terminal_health_check_count = 0
    
    # Continue checking
    return True 