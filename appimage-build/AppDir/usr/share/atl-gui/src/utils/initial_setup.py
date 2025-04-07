import gi
import os
import subprocess
import pathlib
from pathlib import Path
import shutil
import json
import logging
import sys
import traceback

# Set up logging
log_dir = os.path.join(str(Path.home()), ".config", "atl-gui", "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "debug.log")
logging.basicConfig(filename=log_file, level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('initial_setup')
logger.info("Logger initialized")

# Also log to console
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
logger.addHandler(console_handler)

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

CONFIG_DIR = os.path.join(str(Path.home()), ".config", "atl-gui")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# Global reference to keep the setup dialog alive
_active_setup_dialog = None
_active_setup_assistant = None

class SetupAssistant:
    def __init__(self, window):
        self.window = window
        self.config = self.load_config()
        self.callback = None
        self.dialog = None
    
    def load_config(self):
        """Load configuration or create default if it doesn't exist"""
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR, exist_ok=True)
            
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return self.get_default_config()
        else:
            return self.get_default_config()
    
    def get_default_config(self):
        """Return default configuration"""
        return {
            "first_run": True,
            "atl_executable_path": "",
            "environment_variables": {
                "SCALE": "2",
                "LOG_LEVEL": "debug"
            },
            "display_mode": "auto",  # auto, wayland, x11
            "last_used_directory": str(Path.home()),
            "recent_apks": []
        }
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def show_setup_dialog(self, callback=None):
        """Show the initial setup dialog"""
        global _active_setup_dialog, _active_setup_assistant
        
        logger.info(f"Starting setup_dialog with callback: {callback}")
        self.callback = callback
        
        # Create dialog
        self.dialog = Adw.Window()
        self.dialog.set_title("ATL-GUI Initial Setup")
        self.dialog.set_default_size(650, 700)
        if self.window:
            self.dialog.set_transient_for(self.window)
        self.dialog.set_modal(True)
        
        # Keep global references to prevent garbage collection
        _active_setup_dialog = self.dialog
        _active_setup_assistant = self
        
        # Connect to the close-request signal to track when dialog is closed
        self.dialog.connect("close-request", self.on_dialog_close_request)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_margin_top(24)
        box.set_margin_bottom(24)
        box.set_margin_start(24)
        box.set_margin_end(24)
        self.dialog.set_content(box)
        
        # Logo
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "res", "android_translation_layer.png")
        if os.path.exists(logo_path):
            logo = Gtk.Image()
            logo.set_from_file(logo_path)
            logo.set_pixel_size(96)
            logo.set_margin_bottom(24)
            logo.set_halign(Gtk.Align.CENTER)
            box.append(logo)
        
        # Welcome title
        title = Gtk.Label(label="ATL-GUI Initial Setup")
        title.add_css_class("title-1")
        title.set_margin_bottom(12)
        box.append(title)
        
        # Welcome description
        description = Gtk.Label(label="Please configure the initial settings\nto use Android Translation Layer application.")
        description.set_justify(Gtk.Justification.CENTER)
        description.add_css_class("body")
        description.set_margin_bottom(24)
        box.append(description)
        
        # Setup content in a ScrolledWindow
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        box.append(scrolled)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content_box.set_margin_top(8)
        content_box.set_margin_bottom(8)
        content_box.set_margin_start(8)
        content_box.set_margin_end(8)
        scrolled.set_child(content_box)
        
        # 1. ATL Executable Path group
        atl_group = Adw.PreferencesGroup()
        atl_group.set_title("Android Translation Layer Executable")
        atl_group.set_description("The executable file is required to run the application.")
        content_box.append(atl_group)
        
        # Path input row
        atl_path_row = Adw.ActionRow()
        atl_path_row.set_title("android-translation-layer Path")
        atl_path_row.set_subtitle("You can skip this step if it's already installed on your system.")
        
        self.atl_path_entry = Gtk.Entry()
        self.atl_path_entry.set_valign(Gtk.Align.CENTER)
        atl_path_entry_value = self.config.get("atl_executable_path", "")
        if atl_path_entry_value:
            self.atl_path_entry.set_text(atl_path_entry_value)
        
        browse_button = Gtk.Button(label="Browse")
        browse_button.add_css_class("flat")
        browse_button.connect("clicked", self.on_browse_atl_clicked)
        
        atl_path_row.add_suffix(self.atl_path_entry)
        atl_path_row.add_suffix(browse_button)
        atl_group.add(atl_path_row)
        
        # Auto-detect button row
        autodetect_row = Adw.ActionRow()
        autodetect_row.set_title("Auto-detect")
        
        autodetect_button = Gtk.Button(label="Search")
        autodetect_button.add_css_class("flat")
        autodetect_button.connect("clicked", self.on_autodetect_clicked)
        
        autodetect_row.add_suffix(autodetect_button)
        atl_group.add(autodetect_row)
        
        # Status row
        self.atl_status_row = Adw.ActionRow()
        self.atl_status_row.set_title("Status")
        
        self.atl_status_icon = Gtk.Image()
        self.atl_status_icon.set_from_icon_name("emblem-important-symbolic")
        self.atl_status_icon.add_css_class("error")
        
        self.atl_status_label = Gtk.Label(label="Not verified")
        
        self.atl_status_row.add_suffix(self.atl_status_label)
        self.atl_status_row.add_suffix(self.atl_status_icon)
        atl_group.add(self.atl_status_row)
        
        # 2. Environment Variables group
        env_group = Adw.PreferencesGroup()
        env_group.set_title("Environment Variables")
        env_group.set_description("Required variables for running Android applications.")
        content_box.append(env_group)
        
        # Text view for environment variables
        env_row = Adw.ActionRow()
        env_row.set_title("Environment Variables")
        env_row.set_subtitle("Enter one KEY=VALUE per line.")
        
        env_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        env_box.set_hexpand(True)
        
        self.env_text_view = Gtk.TextView()
        self.env_text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.env_text_view.set_top_margin(8)
        self.env_text_view.set_bottom_margin(8)
        self.env_text_view.set_left_margin(8)
        self.env_text_view.set_right_margin(8)
        self.env_text_view.set_monospace(True)
        
        # Set environment variables from config
        env_vars = self.config.get("environment_variables", {})
        env_text = "\n".join([f"{key}={value}" for key, value in env_vars.items()])
        self.env_text_view.get_buffer().set_text(env_text if env_text else "SCALE=2\nLOG_LEVEL=debug")
        
        env_scroll = Gtk.ScrolledWindow()
        env_scroll.set_min_content_height(100)
        env_scroll.set_vexpand(False)
        env_scroll.set_child(self.env_text_view)
        env_scroll.add_css_class("card")
        
        env_box.append(env_scroll)
        env_group.add(env_box)
        
        # 3. Display Mode group
        display_group = Adw.PreferencesGroup()
        display_group.set_title("Display Mode")
        display_group.set_description("Display server selection.")
        content_box.append(display_group)
        
        # Display mode row
        display_row = Adw.ComboRow()
        display_row.set_title("Display Mode")
        display_row.set_subtitle("Optimized display for Wayland or X11.")
        
        display_model = Gtk.StringList()
        display_model.append("Auto-detect")
        display_model.append("Wayland")
        display_model.append("X11")
        
        display_row.set_model(display_model)
        
        # Set selected display mode from config
        display_mode = self.config.get("display_mode", "auto")
        if display_mode == "wayland":
            display_row.set_selected(1)
        elif display_mode == "x11":
            display_row.set_selected(2)
        else:
            display_row.set_selected(0)
        
        self.display_row = display_row
        display_group.add(display_row)
        
        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_margin_top(24)
        button_box.set_halign(Gtk.Align.END)
        box.append(button_box)
        
        skip_button = Gtk.Button(label="Skip")
        skip_button.connect("clicked", self.on_skip_clicked)
        button_box.append(skip_button)
        
        save_button = Gtk.Button(label="Save")
        save_button.add_css_class("suggested-action")
        save_button.connect("clicked", self.on_save_clicked)
        button_box.append(save_button)
        
        # Show dialog
        self.dialog.present()
        
        # Check ATL path status
        GLib.idle_add(self.check_atl_path)
    
    def on_browse_atl_clicked(self, button):
        """Handle browse button click for ATL executable"""
        file_chooser = Gtk.FileDialog()
        file_chooser.set_title("Select android-translation-layer File")
        
        # Create filter for executable files
        filters = Gtk.FilterListModel()
        
        # Filter for executable files
        exe_filter = Gtk.FileFilter()
        exe_filter.set_name("Executable files")
        exe_filter.add_mime_type("application/x-executable")
        exe_filter.add_pattern("*")
        
        file_chooser.open(self.window, None, self._on_file_dialog_response)
    
    def _on_file_dialog_response(self, dialog, result):
        """Handle file dialog response"""
        try:
            file = dialog.open_finish(result)
            if file:
                path = file.get_path()
                self.atl_path_entry.set_text(path)
                self.check_atl_path()
        except Exception as e:
            print(f"File dialog error: {e}")
    
    def on_autodetect_clicked(self, button):
        """Attempt to automatically detect android-translation-layer in PATH"""
        path = self.find_atl_in_path()
        if path:
            self.atl_path_entry.set_text(path)
            self.check_atl_path()
            self.update_atl_status(True, f"Found: {path}")
        else:
            self.update_atl_status(False, "Not found in PATH")
    
    def find_atl_in_path(self):
        """Find android-translation-layer in PATH"""
        try:
            path = shutil.which("android-translation-layer")
            if path:
                return path
                
            # Check common locations
            common_locations = [
                "/usr/bin/android-translation-layer",
                "/usr/local/bin/android-translation-layer",
                f"{str(Path.home())}/bin/android-translation-layer",
                f"{str(Path.home())}/.local/bin/android-translation-layer"
            ]
            
            for location in common_locations:
                if os.path.exists(location) and os.access(location, os.X_OK):
                    return location
                    
            return None
        except Exception as e:
            print(f"Error finding ATL: {e}")
            return None
    
    def check_atl_path(self):
        """Check if the ATL executable path is valid"""
        path = self.atl_path_entry.get_text().strip()
        
        if not path:
            self.update_atl_status(False, "No path specified")
            return False
            
        if not os.path.exists(path):
            self.update_atl_status(False, "File not found")
            return False
            
        if not os.access(path, os.X_OK):
            self.update_atl_status(False, "No execute permission")
            return False
            
        # Try to run with --version
        try:
            result = subprocess.run([path, "--version"], 
                                    capture_output=True, 
                                    text=True, 
                                    timeout=2)
            
            if result.returncode == 0:
                version = result.stdout.strip()
                self.update_atl_status(True, f"Verified: {version}")
                return True
            else:
                self.update_atl_status(False, "Failed to execute")
                return False
        except subprocess.TimeoutExpired:
            self.update_atl_status(False, "Timeout")
            return False
        except Exception as e:
            self.update_atl_status(False, f"Error: {str(e)}")
            return False
    
    def update_atl_status(self, success, message):
        """Update the ATL status row"""
        self.atl_status_label.set_text(message)
        
        if success:
            self.atl_status_icon.set_from_icon_name("emblem-ok-symbolic")
            self.atl_status_icon.remove_css_class("error")
            self.atl_status_icon.add_css_class("success")
        else:
            self.atl_status_icon.set_from_icon_name("emblem-important-symbolic")
            self.atl_status_icon.remove_css_class("success")
            self.atl_status_icon.add_css_class("error")
    
    def show_error_dialog(self, message):
        """Show an error dialog with the given message"""
        dialog = Adw.MessageDialog.new(self.window, "Error", message)
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
        dialog.present()
        return False  # Return False to stop the idle timeout if used with GLib.timeout_add
    
    def on_skip_clicked(self, button):
        """Skip setup and close dialog"""
        logger.info("Skip button clicked")
        self.config["first_run"] = False
        self.save_config()
        
        # Close dialog and call callback
        self.finish_dialog(True)
    
    def on_save_clicked(self, button):
        """Save settings and close dialog"""
        logger.info("Save button clicked")
        # Save ATL path
        self.config["atl_executable_path"] = self.atl_path_entry.get_text().strip()
        
        # Save environment variables
        buffer = self.env_text_view.get_buffer()
        start, end = buffer.get_bounds()
        env_text = buffer.get_text(start, end, False)
        
        env_vars = {}
        for line in env_text.splitlines():
            line = line.strip()
            if line and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
        
        self.config["environment_variables"] = env_vars
        
        # Save display mode
        selected = self.display_row.get_selected()
        if selected == 1:
            self.config["display_mode"] = "wayland"
        elif selected == 2:
            self.config["display_mode"] = "x11"
        else:
            self.config["display_mode"] = "auto"
        
        # Mark setup as completed
        self.config["first_run"] = False
        
        # Save config
        self.save_config()
        
        # Close dialog and call callback
        self.finish_dialog(True)
    
    def finish_dialog(self, invoke_callback=False):
        """Close dialog and handle callback"""
        global _active_setup_dialog, _active_setup_assistant
        
        logger.info(f"Finishing dialog, invoke_callback={invoke_callback}")
        
        # Close dialog
        if self.dialog:
            logger.info("Closing dialog")
            self.dialog.close()
        
        # Call callback if needed
        if invoke_callback and self.callback:
            logger.info(f"Scheduling callback from finish_dialog: {self.callback}")
            # Use a timeout to ensure dialog is fully closed before callback runs
            GLib.timeout_add(500, self._run_callback_with_cleanup)
    
    def _run_callback_with_cleanup(self):
        """Run the callback and clean up references"""
        global _active_setup_dialog, _active_setup_assistant
        
        logger.info("Running delayed callback with cleanup")
        callback = self.callback
        
        if callback:
            try:
                logger.info("Executing callback")
                callback()
                logger.info("Callback executed successfully")
            except Exception as e:
                error_details = traceback.format_exc()
                logger.error(f"Error in delayed callback: {e}\n{error_details}")
                self.show_error_dialog(f"Error: {str(e)}")
        
        # Clear references
        _active_setup_dialog = None
        _active_setup_assistant = None
        
        return False
    
    def on_dialog_close_request(self, dialog):
        """Handle dialog close request"""
        logger.info("Dialog received close-request signal")
        # Don't call callback on direct close
        self.finish_dialog(False)
        return False  # Allow dialog to close

def check_first_run(window, show_dialog=True):
    """Check if this is the first run and show setup if needed"""
    print(f"[DEBUG] check_first_run called, show_dialog={show_dialog}")
    setup = SetupAssistant(window)
    if setup.config.get("first_run", True) and show_dialog:
        print("[DEBUG] First run confirmed, showing setup dialog")
        setup.show_setup_dialog()
    return setup.config 