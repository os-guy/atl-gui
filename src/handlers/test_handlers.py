import gi
import os
import subprocess
import shlex
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

def test_next_apk(self):
    if self.current_apk_index >= len(self.apk_files):
        # All tests completed
        toast = Adw.Toast.new("All applications have been run!")
        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)

        # Show results screen
        self.show_test_results()
        return

    # Get the next APK to test
    apk_path = self.apk_files[self.current_apk_index]
    apk_name = os.path.basename(apk_path)
    folder_path = os.path.dirname(apk_path)

    # Update UI - For modified status section
    self.apk_value_label.set_text(apk_name)
    self.status_value_label.set_text("Ready")
    self.status_icon.set_from_icon_name("media-playback-pause-symbolic")
    self.command_value_label.set_text("-")
    
    # Update APK name and progress information
    self.apk_name_label.set_text(apk_name)
    self.progress_label.set_text(f"Progress: {self.current_apk_index + 1}/{len(self.apk_files)}")
    self.progress_bar.set_fraction((self.current_apk_index) / len(self.apk_files))
    
    # Test UI settings - Show button, hide test buttons
    self.start_test_button.set_visible(True)
    self.settings_button.set_visible(True)
    self.test_button_box.set_visible(False)
    self.test_question_label.set_visible(False)
    
    # Clear terminal output
    self.terminal_output.get_buffer().set_text("")
    
    # Successfully loaded notification
    toast = Adw.Toast.new(f"Application loaded: {apk_name}")
    self.toast_overlay.add_toast(toast)
    
def on_skip_clicked(self, button):
    # Show toast
    toast = Adw.Toast.new("Application skipped")
    self.toast_overlay.add_toast(toast)
    
    # Update status information
    self.status_value_label.set_text("Skipped")
    self.status_icon.set_from_icon_name("action-unavailable-symbolic")
    self.status_icon.remove_css_class("success")
    self.status_icon.remove_css_class("error")

    # Save result as skipped
    current_apk = self.apk_files[self.current_apk_index]
    self.test_results[current_apk] = "skipped"
    
    # Check terminal logs
    if not hasattr(self, 'terminal_logs'):
        self.terminal_logs = {}
        
    # Update or create log record for this APK
    if current_apk not in self.terminal_logs:
        self.terminal_logs[current_apk] = "[USER: Application skipped]\n"
    else:
        self.terminal_logs[current_apk] += "\n\n[USER: Application skipped]\n"
    
    # Stop process and move to next
    self.kill_current_process()
    self.current_apk_index += 1
    self.test_next_apk()
    
    # Hide question label
    self.test_question_label.set_visible(False)

def on_finish_all_clicked(self, button):
    # Show toast
    toast = Adw.Toast.new("All applications terminated")
    self.toast_overlay.add_toast(toast)
    
    # Stop process
    self.kill_current_process()
    
    # Show results screen
    self.show_test_results()

def on_output(self, source, condition):
    if condition == GLib.IO_HUP:
        # Command finished (HUP - connection closed)
        if self.current_apk_ready:
            # Check terminal output of APK
            if self.current_apk_index < len(self.apk_files):
                current_apk = self.apk_files[self.current_apk_index]
                # Get terminal output
                buffer = self.terminal_output.get_buffer()
                start_iter = buffer.get_start_iter()
                end_iter = buffer.get_end_iter()
                output_text = buffer.get_text(start_iter, end_iter, True)
                
                # Check output - Was it closed successfully?
                auto_detected = False
                
                # Try to detect activity lifecycle completion pattern
                if "I/Activity" in output_text:
                    # Get the last 50 lines of output for more reliable detection
                    output_lines = output_text.splitlines()
                    last_lines = output_lines[-50:] if len(output_lines) > 50 else output_lines
                    
                    # Debug - add the last lines to terminal for inspection
                    buffer.insert(buffer.get_end_iter(), "\n\n[DEBUG] Last lines being checked for activity lifecycle completion:\n")
                    for i, line in enumerate(last_lines):
                        buffer.insert(buffer.get_end_iter(), f"{i}: {line}\n")
                    
                    # Look for specific pattern at the end that indicates successful activity shutdown
                    patterns_found = {}
                    
                    # Check for the common Android Activity lifecycle events
                    for i, line in enumerate(last_lines):
                        if "I/Activity" in line:
                            # Keep track of lifecycle events we care about
                            if "onPause" in line:
                                patterns_found["onPause"] = i
                            if "onStop" in line:
                                patterns_found["onStop"] = i
                            if "onDestroy" in line:
                                patterns_found["onDestroy"] = i
                            if "onWindowFocusChanged" in line and "hasFocus: false" in line:
                                patterns_found["focusLost"] = i
                    
                    # Add debug info about patterns found
                    buffer.insert(buffer.get_end_iter(), "\n[DEBUG] Activity lifecycle events detected:\n")
                    buffer.insert(buffer.get_end_iter(), str(patterns_found) + "\n")
                    
                    # Several patterns that indicate successful closure:
                    
                    # Pattern 1: onPause -> onStop -> focusLost in order
                    if ("onPause" in patterns_found and 
                        "onStop" in patterns_found and 
                        "focusLost" in patterns_found):
                        
                        # Check if they're in the right order
                        if (patterns_found["onPause"] < patterns_found["onStop"] and
                            (patterns_found["focusLost"] > patterns_found["onPause"])):
                            buffer.insert(buffer.get_end_iter(), "\n[DEBUG] ✓ Found pattern 1: onPause -> onStop -> focusLost\n")
                            auto_detected = True
                    
                    # Pattern 2: onPause -> onStop -> onDestroy in order
                    elif ("onPause" in patterns_found and 
                          "onStop" in patterns_found and 
                          "onDestroy" in patterns_found):
                        
                        # Check if they're in the right order
                        if (patterns_found["onPause"] < patterns_found["onStop"] and
                            patterns_found["onStop"] < patterns_found["onDestroy"]):
                            buffer.insert(buffer.get_end_iter(), "\n[DEBUG] ✓ Found pattern 2: onPause -> onStop -> onDestroy\n")
                            auto_detected = True
                            
                    # Pattern 3: Just checking for onPause and onStop near the end
                    elif ("onPause" in patterns_found and "onStop" in patterns_found):
                        # Check if they're in the last part of the output and in order
                        if (patterns_found["onPause"] < patterns_found["onStop"] and
                            patterns_found["onStop"] >= len(last_lines) - 10):
                            buffer.insert(buffer.get_end_iter(), "\n[DEBUG] ✓ Found pattern 3: onPause -> onStop at the end\n")
                            auto_detected = True
                
                # Check for explicit success messages
                elif "UserClosedProcess" in output_text or "Application exited normally" in output_text:
                    auto_detected = True
                
                # Update UI based on detection
                if auto_detected:
                    # Application closed properly, mark as working
                    buffer.insert(buffer.get_end_iter(), "\n[AUTO DETECTION] Successfully detected clean application shutdown!\n")
                    GLib.timeout_add(500, self.auto_mark_as_working)
                else:
                    # Not detected as working
                    buffer.insert(buffer.get_end_iter(), "\n[AUTO DETECTION] Could not detect clean application shutdown.\n")
                    GLib.timeout_add(1000, self.auto_mark_as_not_working)
            
        return False

    line = source.readline()
    if line:
        buffer = self.terminal_output.get_buffer()
        buffer.insert(buffer.get_end_iter(), line)
        self.terminal_output.scroll_to_iter(buffer.get_end_iter(), 0, False, 0, 0)
        
        # Save terminal log
        if self.current_apk_index < len(self.apk_files):
            current_apk = self.apk_files[self.current_apk_index]
            if current_apk in self.terminal_logs:
                self.terminal_logs[current_apk] += line

    return True
    
def auto_mark_as_working(self):
    # If still in test waiting state (buttons are still visible)
    if self.test_button_box.get_visible():
        # Mark APK as working
        current_apk = self.apk_files[self.current_apk_index]
        self.test_results[current_apk] = "working"
        
        # Update status information
        self.status_value_label.set_text("Success (Auto)")
        self.status_icon.set_from_icon_name("emblem-ok-symbolic")
        self.status_icon.remove_css_class("error")
        self.status_icon.add_css_class("success")
        
        # Add info to terminal
        buffer = self.terminal_output.get_buffer()
        info_message = "\n\n[AUTO ASSESSMENT: Application closed properly - MARKED AS WORKING]\n"
        buffer.insert(buffer.get_end_iter(), info_message)
        self.terminal_output.scroll_to_iter(buffer.get_end_iter(), 0, False, 0, 0)
        
        # Check terminal logs
        if not hasattr(self, 'terminal_logs'):
            self.terminal_logs = {}
        
        # Add to terminal log
        if current_apk in self.terminal_logs:
            self.terminal_logs[current_apk] += info_message
        else:
            self.terminal_logs[current_apk] = info_message
        
        # Show toast notification
        toast = Adw.Toast.new("Auto assessment: Application marked as working")
        self.toast_overlay.add_toast(toast)
        
        # Move to next APK
        self.current_apk_index += 1
        self.test_next_apk()
        
        # Hide buttons and question label
        self.test_button_box.set_visible(False)
        self.test_question_label.set_visible(False)
        
    return False # end timeout

def auto_mark_as_not_working(self):
    # If still in test waiting state (buttons are still visible)
    if self.test_button_box.get_visible():
        # Mark APK as not working
        current_apk = self.apk_files[self.current_apk_index]
        self.test_results[current_apk] = "not_working"
        
        # Update status information
        self.status_value_label.set_text("Failed (Auto)")
        self.status_icon.set_from_icon_name("dialog-warning-symbolic")
        self.status_icon.remove_css_class("success")
        self.status_icon.add_css_class("error")
        
        # Add info to terminal
        buffer = self.terminal_output.get_buffer()
        info_message = "\n\n[AUTO ASSESSMENT: Terminated without user interaction - MARKED AS NOT WORKING]\n"
        buffer.insert(buffer.get_end_iter(), info_message)
        self.terminal_output.scroll_to_iter(buffer.get_end_iter(), 0, False, 0, 0)
        
        # Check terminal logs
        if not hasattr(self, 'terminal_logs'):
            self.terminal_logs = {}
        
        # Add to terminal log
        if current_apk in self.terminal_logs:
            self.terminal_logs[current_apk] += info_message
        else:
            self.terminal_logs[current_apk] = info_message
        
        # Show toast notification
        toast = Adw.Toast.new("Auto assessment: Application marked as not working")
        self.toast_overlay.add_toast(toast)
        
        # Move to next APK
        self.current_apk_index += 1
        self.test_next_apk()
        
        # Hide buttons and question label
        self.test_button_box.set_visible(False)
        self.test_question_label.set_visible(False)
        
    return False # end timeout

def kill_current_process(self):
    if self.current_process:
        try:
            self.current_process.terminate()
            try:
                self.current_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.current_process.kill()
        except Exception as e:
            print(f"Error terminating process: {e}")
            # Update status information
            self.status_value_label.set_text("Error")
            self.status_icon.set_from_icon_name("dialog-error-symbolic")
            self.status_icon.remove_css_class("success")
            self.status_icon.add_css_class("error")
        finally:
            self.current_process = None

def on_working_clicked(self, button):
    # Show toast
    toast = Adw.Toast.new("Application marked as working")
    self.toast_overlay.add_toast(toast)

    # Update status information
    self.status_value_label.set_text("Success")
    self.status_icon.set_from_icon_name("emblem-ok-symbolic")
    self.status_icon.remove_css_class("error")
    self.status_icon.add_css_class("success")

    # Save result
    current_apk = self.apk_files[self.current_apk_index]
    self.test_results[current_apk] = "working"
    
    # Check terminal logs
    if not hasattr(self, 'terminal_logs'):
        self.terminal_logs = {}
        
    # Update or create log record for this APK
    if current_apk not in self.terminal_logs:
        self.terminal_logs[current_apk] = "[USER: Application marked as working]\n"
    else:
        self.terminal_logs[current_apk] += "\n\n[USER: Application marked as working]\n"

    # Stop process and move to next
    self.kill_current_process()
    self.current_apk_index += 1
    self.test_next_apk()
    
    # Hide question label
    self.test_question_label.set_visible(False)

def on_not_working_clicked(self, button):
    # Show toast
    toast = Adw.Toast.new("Application marked as not working")
    self.toast_overlay.add_toast(toast)

    # Update status information
    self.status_value_label.set_text("Failed")
    self.status_icon.set_from_icon_name("dialog-warning-symbolic")
    self.status_icon.remove_css_class("success")
    self.status_icon.add_css_class("error")

    # Save result
    current_apk = self.apk_files[self.current_apk_index]
    self.test_results[current_apk] = "not_working"
    
    # Check terminal logs
    if not hasattr(self, 'terminal_logs'):
        self.terminal_logs = {}
        
    # Update or create log record for this APK
    if current_apk not in self.terminal_logs:
        self.terminal_logs[current_apk] = "[USER: Application marked as not working]\n"
    else:
        self.terminal_logs[current_apk] += "\n\n[USER: Application marked as not working]\n"

    # Stop process and move to next
    self.kill_current_process()
    self.current_apk_index += 1
    self.test_next_apk()
    
    # Hide question label
    self.test_question_label.set_visible(False)

def on_start_test_clicked(self, button):
    # Mevcut APK için test başlatma işlemi
    if self.current_apk_index < len(self.apk_files):
        apk_path = self.apk_files[self.current_apk_index]
        self.start_test(apk_path)

def start_test(self, apk_path):
    try:
        # Get environment variables
        env_vars = self.env_variables.copy()
        
        # Add standard variables
        env_vars.update({
            'ANDROID_TRANSLATION_LAYER_APK_PATH': apk_path,
            'ANDROID_TRANSLATION_LAYER_FOLDER_PATH': os.path.dirname(apk_path)
        })
        
        # Add additional environment variables
        if hasattr(self, 'additional_env_vars') and self.additional_env_vars:
            env_vars.update(self.additional_env_vars)
            
        # Check if script is specified and exists
        script_error = None
        if hasattr(self, 'script_path') and self.script_path:
            if not os.path.exists(self.script_path):
                script_error = f"Script not found: '{self.script_path}'"
            elif not os.path.isfile(self.script_path):
                script_error = f"The specified path is not a file: '{self.script_path}'"
            elif not os.access(self.script_path, os.X_OK):
                script_error = f"Script is not executable: '{self.script_path}'"
        
        if script_error:
            # Reset UI on error
            self.start_test_button.set_visible(True)
            self.settings_button.set_visible(True)
            self.test_button_box.set_visible(False)
            self.test_question_label.set_visible(False)
            
            # Show error message
            error_dialog = Adw.AlertDialog()
            error_dialog.set_title("Script Error")
            error_dialog.set_body(script_error)
            error_dialog.add_response("ok", "OK")
            error_dialog.set_default_response("ok")
            error_dialog.set_close_response("ok")
            error_dialog.present(self)
            return
        
        # Create the command using the correct format:
        # android-translation-layer .apk -l activity (if exists) -w (if-given) -h (if-given)
        base_command = "android-translation-layer"
        
        # Add the APK path
        base_command += f" {shlex.quote(apk_path)}"
        
        # Add activity launcher option if activity name is provided
        if hasattr(self, 'activity_name') and self.activity_name:
            base_command += f" -l {shlex.quote(self.activity_name)}"
        
        # Add width and height if specified
        if hasattr(self, 'window_width') and self.window_width:
            base_command += f" -w {self.window_width}"
        
        if hasattr(self, 'window_height') and self.window_height:
            base_command += f" -h {self.window_height}"
        
        # Script handling code
        if hasattr(self, 'script_path') and self.script_path and os.path.exists(self.script_path):
            # Environment variables need to be properly exported
            env_vars_string = " ".join([f"export {key}={shlex.quote(str(value))}" for key, value in env_vars.items()])
            
            # Command with script (with or without sudo)
            if hasattr(self, 'sudo_password') and self.sudo_password:
                # With sudo - pass as environment variables
                env_vars_exports = "; ".join([f"export {key}={shlex.quote(str(value))}" for key, value in env_vars.items()])
                command = f"echo {shlex.quote(self.sudo_password)} | sudo -S bash -c '{env_vars_exports}; {self.script_path} {base_command}'"
            else:
                # Without sudo - pass as environment variables
                env_vars_exports = "; ".join([f"export {key}={shlex.quote(str(value))}" for key, value in env_vars.items()])
                command = f"bash -c '{env_vars_exports}; {self.script_path} {base_command}'"
        else:
            # Basic command without script, but with environment variables
            env_vars_exports = " ".join([f"{key}={shlex.quote(str(value))}" for key, value in env_vars.items()])
            command = f"{env_vars_exports} {base_command}"
        
        # Run command
        self.current_process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Update terminal output
        self.terminal_output.get_buffer().set_text("")
        
        # Add command info to terminal output
        buffer = self.terminal_output.get_buffer()
        # Hide sudo password for security
        if "sudo" in command:
            # Mask the sudo password completely
            display_command = command.replace(f"echo {shlex.quote(self.sudo_password)} | sudo -S", "sudo")
        else:
            display_command = command
        
        buffer.set_text(f"Command being executed: {display_command}\n\n")
        
        # Connect stdout and stderr
        self.current_apk_ready = False
        GLib.io_add_watch(self.current_process.stdout, GLib.IO_IN | GLib.IO_HUP, self.on_output)
        GLib.io_add_watch(self.current_process.stderr, GLib.IO_IN | GLib.IO_HUP, self.on_output)
        
        # Update status information
        self.status_value_label.set_text("Running")
        self.status_icon.set_from_icon_name("media-playback-start-symbolic")
        self.command_value_label.set_text(display_command)
        
        # Initialize terminal logs for this APK
        current_apk = self.apk_files[self.current_apk_index]
        if not hasattr(self, 'terminal_logs'):
            self.terminal_logs = {}
        self.terminal_logs[current_apk] = f"Command: {display_command}\n\n"
        
        # Show test question and buttons after a short delay
        GLib.timeout_add(2000, self.show_test_buttons)
        
        # Show toast
        toast = Adw.Toast.new(f"Application started: {os.path.basename(apk_path)}")
        self.toast_overlay.add_toast(toast)
        
    except Exception as e:
        error_message = f"Error: {str(e)}"
        self.terminal_output.get_buffer().set_text(error_message)
        toast = Adw.Toast.new(error_message)
        self.toast_overlay.add_toast(toast)

def show_test_buttons(self):
    # Show test question and buttons
    self.test_question_label.set_visible(True)
    self.test_button_box.set_visible(True)
    self.start_test_button.set_visible(False)
    self.settings_button.set_visible(False)
    self.current_apk_ready = True
    return False  # Don't repeat the timeout 