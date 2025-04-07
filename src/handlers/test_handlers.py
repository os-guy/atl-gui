import gi
import os
import subprocess
import shlex
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
from src.utils.recent_apks import save_recent_apk

def test_next_apk(self):
    if self.current_apk_index >= len(self.apk_files):
        # All tests completed
        toast = Adw.Toast.new("All applications have been run!")
        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)

        # Reset drag & drop UI state if we came from there
        if hasattr(self, 'button_select_area') and hasattr(self, 'button_drop_area'):
            self.button_select_area.set_visible(True)
            self.button_drop_area.set_visible(False)
            self.button_drop_area.remove_css_class("drop-area-active")
            self.button_drop_area.remove_css_class("fade-in")
            self.button_drop_area.remove_css_class("fade-out")
            self.button_select_area.remove_css_class("fade-in")
            self.button_select_area.remove_css_class("fade-out")

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
    
    # Get APK architecture and system information
    self.update_system_info(apk_path)

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
    
    # Save to recent APKs
    save_recent_apk(current_apk, "skipped")
    
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
    # The on_output function is now only used as a fallback
    if hasattr(self, 'using_terminal_module') and self.using_terminal_module:
        return False
        
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
                detection_reason = ""
                success_probability = 0  # 0-100 probability of success
                
                # Use improved app detection logic
                auto_detected, success_probability, detection_reason = detect_app_status(output_text)
                
                # Add detection results to terminal
                buffer.insert(buffer.get_end_iter(), f"\n\n[AUTO DETECTION] App analysis complete. Score: {success_probability}%\n")
                buffer.insert(buffer.get_end_iter(), f"[AUTO DETECTION] {detection_reason}\n")
                
                # Take action based on detection score - call immediately instead of using timeout
                if auto_detected:
                    # Application likely working
                    self.auto_mark_as_working()
                else:
                    # Application likely not working
                    self.auto_mark_as_not_working()
            
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
        
        # Save to recent APKs
        save_recent_apk(current_apk, "working")
        
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
        
        # Save to recent APKs
        save_recent_apk(current_apk, "not_working")
        
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
    if hasattr(self, 'terminal_manager') and self.terminal_manager.is_running:
        self.terminal_manager.terminate_command()
    elif self.current_process:
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
    
    # Save to recent APKs
    save_recent_apk(current_apk, "working")
    
    # Terminate the process if it's still running
    self.kill_current_process()
    
    # Add info to terminal
    buffer = self.terminal_output.get_buffer()
    info_message = "\n\n[USER ASSESSMENT: MARKED AS WORKING]\n"
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
    
    # Move to next APK
    self.current_apk_index += 1
    self.test_next_apk()
    
    # Hide buttons and question label
    self.test_button_box.set_visible(False)
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
    
    # Save to recent APKs
    save_recent_apk(current_apk, "not_working")
    
    # Terminate the process if it's still running
    self.kill_current_process()
    
    # Add info to terminal
    buffer = self.terminal_output.get_buffer()
    info_message = "\n\n[USER ASSESSMENT: MARKED AS NOT WORKING]\n"
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
    
    # Move to next APK
    self.current_apk_index += 1
    self.test_next_apk()
    
    # Hide buttons and question label
    self.test_button_box.set_visible(False)
    self.test_question_label.set_visible(False)

def on_start_test_clicked(self, button):
    # Mevcut APK için test başlatma işlemi
    if self.current_apk_index < len(self.apk_files):
        apk_path = self.apk_files[self.current_apk_index]
        self.start_test(apk_path)

def start_test(self, apk_path):
    try:
        # SELF-TEST: Print the direct attribute value to verify it's been properly set
        print(f"[SELF-TEST] Direct ATL path attribute: '{getattr(self, 'atl_executable_path', 'NOT FOUND')}'")
        print(f"[SELF-TEST] Config contains ATL path: '{self.config.get('atl_executable_path', 'NOT IN CONFIG')}'")
        
        # Use the configured ATL executable path or fall back to "android-translation-layer" in PATH
        # Check if the attribute exists and has a non-empty value
        if hasattr(self, 'atl_executable_path') and self.atl_executable_path:
            atl_executable = self.atl_executable_path
            print(f"[DEBUG] Using configured ATL executable path: '{atl_executable}'")
        else:
            atl_executable = "android-translation-layer"
            print(f"[DEBUG] No ATL executable path configured, falling back to: '{atl_executable}'")
        
        # Add enhanced debugging information
        print("\nDEBUG: ======= STARTING TEST WITH FINAL SETTINGS =======")
        print(f"DEBUG: APK Path: {apk_path}")
        print(f"DEBUG: Using ATL Binary: '{atl_executable}' (exact path from settings)")
        print(f"DEBUG: Activity name: '{self.activity_name}' (use: {self.use_activity})")
        print(f"DEBUG: Instrumentation class: '{self.instrumentation_class}' (use: {self.use_instrumentation})")
        print(f"DEBUG: URI value: '{self.uri_value}' (use: {self.use_uri})")
        print(f"DEBUG: Window dimensions: {self.window_width}x{self.window_height}")
        print(f"DEBUG: JVM options count: {len(self.jvm_options) if hasattr(self, 'jvm_options') else 0}")
        print(f"DEBUG: String keys count: {len(self.string_keys) if hasattr(self, 'string_keys') else 0}")
        print("DEBUG: ===============================================\n")
        
        # Get environment variables
        env_vars = self.env_variables.copy()
        
        # Add standard variables
        env_vars.update({
            'ANDROID_TRANSLATION_LAYER_APK_PATH': apk_path,
            'ANDROID_TRANSLATION_LAYER_FOLDER_PATH': os.path.dirname(apk_path)
        })
        
        # Add additional environment variables
        if self.additional_env_vars:
            env_vars.update(self.additional_env_vars)
            
        # Debugging: Print attributes for troubleshooting
        print("DEBUG: Checking settings attributes:")
        print(f"activity_name: {self.activity_name}")
        print(f"instrumentation_class: {self.instrumentation_class}")
        print(f"uri_value: {self.uri_value}")
        print(f"window_width: {self.window_width}")
        print(f"window_height: {self.window_height}")
        print(f"jvm_options: {self.jvm_options}")
        print(f"string_keys: {self.string_keys}")
            
        # Check if script is specified and exists
        script_error = None
        if self.script_path:
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
            error_dialog.present()
            return
        
        # Create command arguments - first element is the executable itself
        command_args = [atl_executable]
        
        # Add the APK path
        command_args.append(apk_path)
        
        # Track flags for better display
        flags = []
        
        # Add activity launcher option if activity name is provided
        if self.activity_name:
            command_args.extend(["-l", self.activity_name])
            flags.append(f"-l {self.activity_name}")
        
        # Add instrumentation option if provided
        if self.instrumentation_class:
            command_args.extend(["--instrument", self.instrumentation_class])
            flags.append(f"--instrument={self.instrumentation_class}")
        
        # Add width and height if specified
        if self.window_width:
            command_args.extend(["-w", str(self.window_width)])
            flags.append(f"-w {self.window_width}")
        
        if self.window_height:
            command_args.extend(["-h", str(self.window_height)])
            flags.append(f"-h {self.window_height}")
        
        # Add URI if specified
        if self.uri_value:
            command_args.extend(["-u", self.uri_value])
            flags.append(f"-u {self.uri_value}")
        
        # Add extra JVM options
        if self.jvm_options:
            for option in self.jvm_options:
                command_args.extend(["-X", option])
                flags.append(f"-X \"{option}\"")
        
        # Add extra string key/value pairs
        if self.string_keys:
            for key, value in self.string_keys.items():
                command_args.extend(["-e", f"{key}={value}"])
                flags.append(f"-e {key}={value}")
        
        # Add any other flags if needed
        if hasattr(self, 'install_flag') and self.install_flag:
            command_args.append("-i")
            flags.append("-i (install)")
            
        if hasattr(self, 'install_internal') and self.install_internal:
            command_args.append("--install-internal")
            flags.append("--install-internal")
        
        # Add GApplication options if enabled
        if hasattr(self, 'gapplication_app_id') and self.gapplication_app_id:
            command_args.append(f"--gapplication-app-id={self.gapplication_app_id}")
            flags.append(f"--gapplication-app-id={self.gapplication_app_id}")
        
        # Script handling code
        if self.script_path and os.path.exists(self.script_path):
            # Environment variables need to be properly exported
            env_vars_string = " ".join([f"export {key}={shlex.quote(str(value))}" for key, value in env_vars.items()])
            
            # Print debug information
            print(f"[DEBUG] Using script: {self.script_path}")
            print(f"[DEBUG] Script will execute binary: {atl_executable}")
            
            # Command with script (with or without sudo)
            if self.sudo_password:
                # With sudo - pass as environment variables
                env_vars_exports = "; ".join([f"export {key}={shlex.quote(str(value))}" for key, value in env_vars.items()])
                # Use the exact binary path without modifications
                command = f"echo {shlex.quote(self.sudo_password)} | sudo -S bash -c '{env_vars_exports}; {self.script_path} {shlex.quote(atl_executable)} {' '.join(shlex.quote(arg) for arg in command_args[1:])}'"
            else:
                # Without sudo - pass as environment variables
                env_vars_exports = "; ".join([f"export {key}={shlex.quote(str(value))}" for key, value in env_vars.items()])
                # Use the exact binary path without modifications
                command = f"bash -c '{env_vars_exports}; {self.script_path} {shlex.quote(atl_executable)} {' '.join(shlex.quote(arg) for arg in command_args[1:])}'"
        else:
            # Basic command without script, but with environment variables
            env_vars_exports = " ".join([f"{key}={shlex.quote(str(value))}" for key, value in env_vars.items()])
            
            # Print debug info
            print(f"[DEBUG] Running direct command (no script)")
            print(f"[DEBUG] Binary to execute: {atl_executable}")
            
            # Use the exact executable path without modifications - ensure it's properly quoted
            command = f"{env_vars_exports} {shlex.quote(atl_executable)} {' '.join(shlex.quote(arg) for arg in command_args[1:])}"
        
        # Run command using the terminal module from the window
        # Ensure terminal module is running - the terminal_manager is already initialized in the window class
        print(f"[DEBUG] Terminal manager: {hasattr(self, 'terminal_manager')}")
        if hasattr(self, 'terminal_manager'):
            print(f"[DEBUG] Terminal manager type: {type(self.terminal_manager).__name__}")
            print(f"[DEBUG] Terminal manager running: {self.terminal_manager.is_running}")
            
        if not self.terminal_manager.is_running:
            self.terminal_manager.start()
            print(f"[DEBUG] Started terminal manager, running: {self.terminal_manager.is_running}")
        
        # Mark that we're using the terminal module
        self.using_terminal_module = True
        
        # Clear terminal output
        self.terminal_output.get_buffer().set_text("")
        
        # Add command info to terminal output in a more readable format
        buffer = self.terminal_output.get_buffer()
        
        # Hide sudo password for security
        if "sudo" in command:
            # Mask the sudo password completely
            display_command = command.replace(f"echo {shlex.quote(self.sudo_password)} | sudo -S", "sudo")
        else:
            display_command = command
        
        # Create a more readable format for the command display
        command_summary = f"Command being executed:\n"
        command_summary += f"----------------------------------------\n"
        command_summary += f"APK: {os.path.basename(apk_path)}\n"
        command_summary += f"Using Binary: {atl_executable}\n"
        
        # Add options if any
        if flags:
            command_summary += "Options:\n"
            for flag in flags:
                command_summary += f"  • {flag}\n"
        else:
            command_summary += "Options: None\n"
            
        # Add environment variables if any custom ones
        if self.additional_env_vars:
            command_summary += "Environment Variables:\n"
            for key, value in self.additional_env_vars.items():
                command_summary += f"  • {key}={value}\n"
        
        # Add script info if used
        if self.script_path and os.path.exists(self.script_path):
            command_summary += f"Using script: {self.script_path}\n"
            
        command_summary += f"----------------------------------------\n"
        command_summary += f"Full command: {display_command}\n\n"
        
        buffer.set_text(command_summary)
        
        # Execute command in separate process
        self.terminal_manager.execute_command(command, shell=True, env_vars=env_vars)
        
        # Set up GLib timeout to check for output from terminal module
        GLib.timeout_add(100, self.process_terminal_output)
        
        # Also set up a separate health check that runs less frequently
        GLib.timeout_add(3000, self.check_terminal_health)
        
        # Update status information
        self.status_value_label.set_text("Running")
        self.status_icon.set_from_icon_name("media-playback-start-symbolic")
        self.command_value_label.set_text(display_command)
        
        # Initialize terminal logs for this APK
        current_apk = self.apk_files[self.current_apk_index]
        if not hasattr(self, 'terminal_logs'):
            self.terminal_logs = {}
        self.terminal_logs[current_apk] = command_summary
        
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

def validate_options(self):
    """Validate all options and return a list of invalid options with error messages"""
    invalid_options = []
    
    # Debug message to show what we're validating
    print("DEBUG: VALIDATING OPTIONS:")
    print(f"  activity_name: {self.activity_name}")
    print(f"  instrumentation_class: {self.instrumentation_class}")
    print(f"  uri_value: {self.uri_value}")
    print(f"  window_width: {self.window_width}")
    print(f"  window_height: {self.window_height}")
    print(f"  jvm_options: {self.jvm_options}")
    print(f"  string_keys: {self.string_keys}")
    
    # Validate activity name
    if self.activity_name:
        # Basic validation for activity name format (should be in format com.package.ActivityName)
        if not '.' in self.activity_name or len(self.activity_name.split('.')) < 2:
            print(f"DEBUG: Invalid activity_name: {self.activity_name}")
            invalid_options.append(("Activity Name", 
                                    "Invalid activity name format. Should be in format 'com.package.ActivityName'",
                                    "activity_name"))
    
    # Validate instrumentation class
    if self.instrumentation_class:
        # Basic validation for instrumentation class format
        if not '.' in self.instrumentation_class or len(self.instrumentation_class.split('.')) < 2:
            print(f"DEBUG: Invalid instrumentation_class: {self.instrumentation_class}")
            invalid_options.append(("Instrumentation Class", 
                                    "Invalid instrumentation class format. Should be in format 'com.package.TestClass'",
                                    "instrumentation_class"))
    
    # Validate URI
    if self.uri_value:
        # Basic validation for URI format (should start with a scheme like http://, https://, etc.)
        if not '://' in self.uri_value:
            print(f"DEBUG: Invalid uri_value: {self.uri_value}")
            invalid_options.append(("URI", 
                                    "Invalid URI format. URI should include a scheme (e.g., http://, https://, content://)",
                                    "uri_value"))
    
    # Validate window dimensions
    if self.window_width is not None:
        try:
            width = int(self.window_width)
            if width <= 0 or width > 5000:
                print(f"DEBUG: Invalid window_width: {self.window_width}")
                invalid_options.append(("Window Width", 
                                        f"Invalid window width: {self.window_width}. Value should be between 1 and 5000.",
                                        "window_width"))
        except (ValueError, TypeError):
            print(f"DEBUG: Invalid window_width type: {self.window_width}")
            invalid_options.append(("Window Width", 
                                    f"Invalid window width: {self.window_width}. Must be a valid number.",
                                    "window_width"))
            
    if self.window_height is not None:
        try:
            height = int(self.window_height)
            if height <= 0 or height > 5000:
                print(f"DEBUG: Invalid window_height: {self.window_height}")
                invalid_options.append(("Window Height", 
                                        f"Invalid window height: {self.window_height}. Value should be between 1 and 5000.",
                                        "window_height"))
        except (ValueError, TypeError):
            print(f"DEBUG: Invalid window_height type: {self.window_height}")
            invalid_options.append(("Window Height", 
                                    f"Invalid window height: {self.window_height}. Must be a valid number.",
                                    "window_height"))
    
    # Validate JVM options (basic check)
    if self.jvm_options:
        for i, option in enumerate(self.jvm_options):
            if not option.strip():
                print(f"DEBUG: Invalid jvm_option at index {i}: '{option}'")
                invalid_options.append(("JVM Option", 
                                        f"Empty JVM option at line {i+1}",
                                        "jvm_options"))
    
    # Validate string key/value pairs
    if self.string_keys:
        for key, value in self.string_keys.items():
            if not key.strip():
                print(f"DEBUG: Invalid string_key: '{key}'")
                invalid_options.append(("String Key", 
                                        "Empty key found in string key/value pairs",
                                        "string_keys"))
    
    print(f"DEBUG: Validation complete. Found {len(invalid_options)} invalid options.")
    if invalid_options:
        print(f"DEBUG: Invalid options: {[option[0] for option in invalid_options]}")
    
    return invalid_options

def show_invalid_options_dialog(self, invalid_options, apk_path):
    """Show dialog for invalid options with detailed information"""
    dialog = Adw.AlertDialog()
    dialog.set_title("Invalid Options Detected")
    
    # Create the content
    content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    content_box.set_margin_top(16)
    content_box.set_margin_bottom(16)
    content_box.set_margin_start(16)
    content_box.set_margin_end(16)
    
    # Add warning label
    warning_label = Gtk.Label()
    warning_label.set_markup("<b>The following options have validation issues:</b>")
    warning_label.set_halign(Gtk.Align.START)
    content_box.append(warning_label)
    
    # Add each invalid option to the content
    for option_name, error_message, _ in invalid_options:
        option_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        option_box.set_margin_top(8)
        
        option_label = Gtk.Label()
        option_label.set_markup(f"<b>{option_name}:</b>")
        option_label.set_halign(Gtk.Align.START)
        option_box.append(option_label)
        
        error_label = Gtk.Label(label=error_message)
        error_label.set_halign(Gtk.Align.START)
        error_label.set_wrap(True)
        error_label.add_css_class("caption")
        option_box.append(error_label)
        
        content_box.append(option_box)
    
    dialog.set_extra_child(content_box)
    
    # Add responses
    dialog.add_response("back", "Go Back")
    dialog.add_response("continue", "Continue Anyway")
    dialog.set_response_appearance("continue", Adw.ResponseAppearance.SUGGESTED)
    dialog.set_default_response("back")
    
    # Handle the response
    dialog.connect("response", handle_invalid_options_response, self, apk_path, invalid_options)
    
    # Show the dialog
    dialog.present()

def handle_invalid_options_response(dialog, response, window, apk_path, invalid_options):
    """Handle response from invalid options dialog"""
    if response == "continue":
        # User wants to continue despite invalid options
        toast = Adw.Toast.new("Continuing with invalid options")
        window.toast_overlay.add_toast(toast)
        
        # Debug message - before changes
        print("DEBUG: BEFORE handling invalid options:")
        print(f"  activity_name: {window.activity_name}")
        print(f"  instrumentation_class: {window.instrumentation_class}")
        print(f"  uri_value: {window.uri_value}")
        print(f"  window_width: {window.window_width}")
        print(f"  window_height: {window.window_height}")
        print(f"  jvm_options: {window.jvm_options}")
        print(f"  string_keys: {window.string_keys}")
        print(f"  Invalid options to handle: {[option[0] for option in invalid_options]}")
        
        # Store invalid options in the window object for later use in error display
        window.invalid_options = invalid_options
        
        # Just log the invalid options but don't modify them
        for option_name, error_message, option_attr in invalid_options:
            print(f"DEBUG: Found invalid option: {option_name} - {option_attr}")
            print(f"DEBUG: Keeping value: {getattr(window, option_attr)}")
        
        # Debug message - after changes (should be same as before)
        print("DEBUG: AFTER handling invalid options:")
        print(f"  activity_name: {window.activity_name}")
        print(f"  instrumentation_class: {window.instrumentation_class}")
        print(f"  uri_value: {window.uri_value}")
        print(f"  window_width: {window.window_width}")
        print(f"  window_height: {window.window_height}")
        print(f"  jvm_options: {window.jvm_options}")
        print(f"  string_keys: {window.string_keys}")
        
        # Show confirmation that settings are saved
        toast = Adw.Toast.new("Settings saved with invalid options preserved")
        window.toast_overlay.add_toast(toast)
    else:
        # User wants to go back to settings
        toast = Adw.Toast.new("Returned to settings")
        window.toast_overlay.add_toast(toast)
        
        # Let them edit settings
        if window.current_apk_index < len(window.apk_files):
            apk_name = os.path.basename(apk_path)
            window.show_test_settings_dialog(apk_name)

def show_test_buttons(self):
    # Show test question and buttons
    self.test_question_label.set_visible(True)
    self.test_button_box.set_visible(True)
    self.start_test_button.set_visible(False)
    self.settings_button.set_visible(False)
    self.current_apk_ready = True
    return False  # Don't repeat the timeout 

def detect_app_status(output_text):
    """Improved detection of app status using multiple indicators"""
    success_probability = 20  # Start with a base score of 20
    detailed_reasons = []
    
    # 1. Window Creation Check - More relaxed indicators
    window_created = check_window_creation(output_text)
    if window_created:
        success_probability += 25
        detailed_reasons.append("Window creation signals detected")
    else:
        # Don't penalize too harshly - some logs might not show all signals
        success_probability -= 10
        detailed_reasons.append("Limited window creation signals")
    
    # 2. Crash Detection - This remains critical
    crashes = check_for_crashes(output_text)
    if crashes:
        success_probability -= 60  # Stronger penalty for crashes
        detailed_reasons.append(f"Application crashed: {crashes}")
    else:
        success_probability += 25  # Reward for no crashes
        detailed_reasons.append("No crashes detected")
    
    # 3. UI Responsiveness Check - Made more lenient
    ui_responsive = check_ui_responsiveness(output_text)
    if ui_responsive:
        success_probability += 20
        detailed_reasons.append("UI appears responsive")
    else:
        # No penalty if we're not sure
        detailed_reasons.append("UI responsiveness inconclusive")
    
    # 4. Proper Initialization - Essential check
    proper_init = check_proper_initialization(output_text)
    if proper_init:
        success_probability += 20
        detailed_reasons.append("Application initialized correctly")
    else:
        # Small penalty for lack of initialization signals
        success_probability -= 10
        detailed_reasons.append("Incomplete initialization signals")
    
    # 5. Check for activity creation - good indicator
    if "Activity:" in output_text or "Starting activity" in output_text:
        success_probability += 15
        detailed_reasons.append("Activity startup detected")
    
    # 6. Check for common success signals
    if check_common_success_signals(output_text):
        success_probability += 20
        detailed_reasons.append("Common success signals detected")
    
    # Ensure we stay in the 0-100 range
    success_probability = max(0, min(100, success_probability))
    
    # Format reasons into readable text
    detailed_reason = ", ".join(detailed_reasons)
    
    # Determine final status - lower threshold to 40%
    auto_detected = success_probability >= 40
    
    return auto_detected, success_probability, detailed_reason

def check_window_creation(output_text):
    """Check if application window was successfully created - expanded indicators"""
    window_indicators = [
        "createSurface",
        "Surface created",
        "ViewRootImpl",
        "DecorView",
        "WindowManager",
        "addView",
        "window visible",
        "I/ActivityTaskManager",
        "display added",
        "Displayed",
        "added window",
        "shown window",
        "Creating view",
        "HwBinder",
        "startActivity",
        "ActivityRecord",
        "SurfaceView",
        "I/art",
        "Starting display",
        "starting window",
        "relayoutWindow"
    ]
    
    # Count how many window creation indicators are found
    found_count = sum(1 for indicator in window_indicators if indicator in output_text)
    return found_count >= 2  # Need at least 2 indicators to confirm window creation

def check_for_crashes(output_text):
    """Check for crash indicators in the output"""
    crash_patterns = [
        "FATAL EXCEPTION",
        "Fatal signal",
        "Force finishing activity",
        "ANR ",
        "Application Not Responding",
        "Crash",
        "java.lang.NullPointerException",
        "SIGSEGV",
        "SIGABRT",
        "kernel panic",
        "The application may be doing too much work on its main thread"
    ]
    
    for pattern in crash_patterns:
        if pattern in output_text:
            return pattern
    
    return None

def check_ui_responsiveness(output_text):
    """Check for indicators that UI is responsive and interactive - more indicators"""
    responsive_indicators = [
        "onDraw", 
        "dispatchTouchEvent",
        "ViewGroup.dispatchDraw",
        "ViewGroup.updateDisplayListIfDirty",
        "choreographer",
        "onMeasure",
        "onLayout",
        "I/chatty",
        "I/InputReader",
        "I/InputDispatcher",
        "drawFrame",
        "animating",
        "handle motion",
        "MotionEvent",
        "reportFocus",
        "focus changed",
        "setFocusedWindow",
        "I/BufferQueue",
        "Vsync",
        "renderThread",
        "draw()"
    ]
    
    # Count how many responsiveness indicators are found
    found_count = sum(1 for indicator in responsive_indicators if indicator in output_text)
    return found_count >= 1  # Need only 1 indicator to suggest responsiveness

def check_proper_initialization(output_text):
    """Check if application initialized correctly - more indicators"""
    init_indicators = [
        "onCreate",
        "onStart",
        "onResume",
        "Activity started",
        "ApplicationInfo",
        "PackageManager.getApplicationInfo",
        "LoadedApk.makeApplication",
        "Added application",
        "ActivityThread.handleBindApplication",
        "Initializing",
        "ActivityManager",
        "activityIdle",
        "Starting: Intent",
        "initializeProcessState",
        "preload",
        "initializing",
        "Running ClassVerifier",
        "initialized",
        "ClassLoader",
        "Starting activity"
    ]
    
    found_count = sum(1 for indicator in init_indicators if indicator in output_text)
    return found_count >= 2  # Need only 2 indicators to confirm initialization

def check_common_success_signals(output_text):
    """Check for common signals that indicate successful app operation"""
    success_signals = [
        "I/zygote",
        "I/ActivityManager", 
        "I/art", 
        "I/System", 
        "I/OpenGLRenderer", 
        "I/SurfaceFlinger",
        "I/ActivityTaskManager",
        "D/libEGL",
        "D/gralloc",
        "D/SurfaceControl",
        "onConfigurationChanged",
        "updateConfiguration",
        "I/Choreographer",
        "I/audio",
        "I/media",
        "I/MediaPlayer",
        "I/TextInputI",
        "I/ViewRootImpl",
        "I/StatusBar",
        "prepared",
        "I/Timeline"
    ]
    
    # Count how many success signals are found
    found_count = sum(1 for signal in success_signals if signal in output_text)
    return found_count >= 3  # Need at least 3 success signals 