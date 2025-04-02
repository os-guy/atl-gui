#!/usr/bin/env python3
import gi
import os
import sys
import time
import json
from pathlib import Path
import subprocess
import tempfile

# Import our display_backend module for Wayland/X11 support
from src.utils import display_backend

# Configure backend before GTK initialization
display_backend.configure_backend()

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, GdkPixbuf, Gdk

from src.window import AtlGUIWindow
from src.utils.css_provider import setup_css
from src.utils.initial_setup import check_first_run, SetupAssistant

class SetupWindow(Adw.Window):
    """A setup window that properly handles closing"""
    def __init__(self, app):
        super().__init__(application=app)
        self.app = app
        self.set_title("ATL-GUI Initial Setup")
        self.set_default_size(650, 700)
        self.set_modal(True)
        
        # Set window icon for Wayland
        self.set_window_icon()
        
        # Connect to destroy signal to ensure main window is shown if we're closed
        # This handles cases like clicking the window close button
        self.connect("destroy", self._on_destroy)
        
        # Content box
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_margin_top(24)
        box.set_margin_bottom(24)
        box.set_margin_start(24)
        box.set_margin_end(24)
        self.set_content(box)
        
        # Logo
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "res", "android_translation_layer.png")
        if os.path.exists(logo_path):
            logo = Gtk.Image()
            logo.set_from_file(logo_path)
            logo.set_pixel_size(96)
            logo.set_margin_bottom(24)
            logo.set_halign(Gtk.Align.CENTER)
            box.append(logo)
        
        # Welcome title
        title = Gtk.Label(label="Android Translation Layer GUI Setup")
        title.add_css_class("title-1")
        title.set_margin_bottom(12)
        box.append(title)
        
        # Welcome description
        description = Gtk.Label(label="Configure the settings for Android Translation Layer")
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
        
        # Load configuration
        self.config = self.load_config()
        
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
        self.atl_path_entry.set_hexpand(True)
        atl_path_entry_value = self.config.get("atl_executable_path", "")
        if atl_path_entry_value:
            self.atl_path_entry.set_text(atl_path_entry_value)
        
        # Add Auto-Detect button
        detect_button = Gtk.Button(label="Auto-Detect")
        detect_button.add_css_class("flat")
        detect_button.connect("clicked", self.on_autodetect_atl_clicked)
        
        browse_button = Gtk.Button(label="Browse")
        browse_button.add_css_class("flat")
        browse_button.connect("clicked", self.on_browse_atl_clicked)
        
        atl_path_row.add_suffix(self.atl_path_entry)
        atl_path_row.add_suffix(detect_button)
        atl_path_row.add_suffix(browse_button)
        atl_group.add(atl_path_row)
        
        # 2. Environment Variables group
        env_group = Adw.PreferencesGroup()
        env_group.set_title("Environment Variables")
        env_group.set_description("Required variables for running Android applications.")
        content_box.append(env_group)
        
        # Text view for environment variables
        env_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        env_box.set_margin_start(8)
        env_box.set_margin_end(8)
        env_box.set_margin_top(8)
        env_box.set_margin_bottom(8)
        
        env_label = Gtk.Label(label="Enter one KEY=VALUE per line")
        env_label.set_halign(Gtk.Align.START)
        env_label.add_css_class("caption")
        env_box.append(env_label)
        
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
        self.display_row = Adw.ComboRow()
        self.display_row.set_title("Display Mode")
        self.display_row.set_subtitle("Optimized display for Wayland or X11.")
        
        display_model = Gtk.StringList()
        display_model.append("Auto-detect")
        display_model.append("Wayland")
        display_model.append("X11")
        
        self.display_row.set_model(display_model)
        
        # Set selected display mode from config
        display_mode = self.config.get("display_mode", "auto")
        if display_mode == "wayland":
            self.display_row.set_selected(1)
        elif display_mode == "x11":
            self.display_row.set_selected(2)
        else:
            self.display_row.set_selected(0)
        
        display_group.add(self.display_row)
        
        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_margin_top(24)
        button_box.set_halign(Gtk.Align.END)
        box.append(button_box)
        
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", self.on_cancel_clicked)
        button_box.append(cancel_button)
        
        save_button = Gtk.Button(label="Save")
        save_button.add_css_class("suggested-action")
        save_button.connect("clicked", self.on_save_clicked)
        button_box.append(save_button)
    
    def set_window_icon(self):
        """Set the window icon for Wayland compatibility"""
        try:
            # Path to the application icon
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                    "res", "android_translation_layer.png")
            
            if os.path.exists(icon_path):
                print(f"[DEBUG] Setting setup window icon from: {icon_path}")
                try:
                    # Import GdkPixbuf for icon loading
                    from gi.repository import GdkPixbuf, Gdk
                    
                    # Load icon as pixbuf
                    icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file(icon_path)
                    
                    # Set the window icon
                    self.set_icon(icon_pixbuf)
                    
                    # For Wayland, try additional methods
                    try:
                        texture = Gdk.Texture.new_for_pixbuf(icon_pixbuf)
                        self.set_default_icon(texture)
                    except Exception as e:
                        print(f"[WARNING] Could not set texture icon for setup window: {e}")
                    
                    print("[DEBUG] Setup window icon set successfully")
                except Exception as e:
                    print(f"[ERROR] Failed to set setup window icon: {e}")
            else:
                print(f"[WARNING] Icon file not found for setup window: {icon_path}")
        except Exception as e:
            print(f"[ERROR] Error in set_window_icon: {e}")
    
    def load_config(self):
        """Load configuration or create default if it doesn't exist"""
        config_dir = os.path.join(str(Path.home()), ".config", "atl-gui")
        config_file = os.path.join(config_dir, "config.json")
        
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
            
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return self.get_default_config()
        else:
            return self.get_default_config()
    
    def get_default_config(self):
        """Return default configuration"""
        return {
            "first_run": False,
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
        config_dir = os.path.join(str(Path.home()), ".config", "atl-gui")
        config_file = os.path.join(config_dir, "config.json")
        
        # Make sure directory exists
        os.makedirs(config_dir, exist_ok=True)
        
        # Log what we're about to save
        print(f"[DEBUG] Saving config to {config_file}")
        print(f"[DEBUG] Config contains ATL executable path: '{self.config.get('atl_executable_path', '')}'")
        
        try:
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"[DEBUG] Config successfully saved to {config_file}")
        except Exception as e:
            print(f"[ERROR] Error saving config: {e}")
    
    def on_browse_atl_clicked(self, button):
        """Handle browse button click for ATL executable"""
        file_chooser = Gtk.FileDialog()
        file_chooser.set_title("Select android-translation-layer File")
        file_chooser.open(self, None, self._on_file_dialog_response)
    
    def on_autodetect_atl_clicked(self, button):
        """Auto-detect and set the android-translation-layer path when clicked"""
        detected_path = self.auto_detect_atl_path()
        if detected_path:
            self.atl_path_entry.set_text(detected_path)
            # Show success toast using dialog since SetupWindow doesn't have toast overlay
            toast_dialog = Adw.AlertDialog()
            toast_dialog.set_title("Auto-Detect Successful")
            toast_dialog.set_body(f"Found android-translation-layer at:\n{detected_path}")
            toast_dialog.add_response("ok", "OK")
            toast_dialog.present(self)
        else:
            # Show error dialog if not found
            error_dialog = Adw.AlertDialog()
            error_dialog.set_title("Auto-Detect Failed")
            error_dialog.set_body("Could not find android-translation-layer executable in common locations or PATH.\n\nPlease make sure it's installed and accessible.")
            error_dialog.add_response("ok", "OK")
            error_dialog.present(self)
    
    def _on_file_dialog_response(self, dialog, result):
        """Handle file dialog response"""
        try:
            file = dialog.open_finish(result)
            if file:
                path = file.get_path()
                self.atl_path_entry.set_text(path)
        except Exception as e:
            print(f"File dialog error: {e}")
    
    def on_cancel_clicked(self, button):
        """Close dialog without saving"""
        self.close()
    
    def on_save_clicked(self, button):
        """Save settings and close dialog"""
        # Save ATL path
        atl_path = self.atl_path_entry.get_text().strip()
        
        # Validate the path if provided
        if atl_path and not os.path.exists(atl_path):
            # Show warning if the path doesn't exist
            warning_dialog = Adw.AlertDialog()
            warning_dialog.set_title("Path Not Found")
            warning_dialog.set_body(f"The specified path does not exist:\n{atl_path}\n\nDo you want to save it anyway?")
            warning_dialog.add_response("cancel", "Cancel")
            warning_dialog.add_response("save", "Save Anyway")
            warning_dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
            warning_dialog.set_default_response("cancel")
            warning_dialog.connect("response", self._on_path_warning_response)
            warning_dialog.present(self)
            return
            
        # Continue with normal save
        self._save_settings()
    
    def _on_path_warning_response(self, dialog, response):
        """Handle response from path warning dialog"""
        if response == "save":
            # User wants to save despite warning
            self._save_settings()
        # else: do nothing, keep dialog open
    
    def _save_settings(self):
        """Save all settings to config"""
        # Save ATL path
        atl_path = self.atl_path_entry.get_text().strip()
        
        # Print the path being saved
        print(f"[DEBUG] Saving ATL executable path: '{atl_path}'")
        
        # If no path specified, try to auto-detect it
        if not atl_path:
            atl_path = self.auto_detect_atl_path()
            if atl_path:
                self.atl_path_entry.set_text(atl_path)
                print(f"[DEBUG] Auto-detected android-translation-layer path: {atl_path}")
            else:
                print("[DEBUG] Could not auto-detect android-translation-layer path")
        elif atl_path and not os.path.exists(atl_path):
            # Log warning if path doesn't exist
            print(f"[WARNING] Saving non-existent ATL path: {atl_path}")
        
        # Assign to config and print confirmation
        self.config["atl_executable_path"] = atl_path
        print(f"[DEBUG] Config updated with ATL executable path: '{self.config['atl_executable_path']}'")
        
        # Try to directly update the parent window's ATL executable path if possible
        parent_window = self.get_transient_for()
        if parent_window and hasattr(parent_window, 'atl_executable_path'):
            parent_window.atl_executable_path = atl_path
            print(f"[DEBUG] DIRECTLY updated parent window's ATL path to: '{atl_path}'")
        
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
        
        # Save config
        self.save_config()
        
        # Mark first run as false
        self.config["first_run"] = False
        self.save_config()
        
        # Get application reference
        app = self.get_application()
        
        # Close the setup window
        self.close()

        # Show the main window directly in this process
        print("[DEBUG] Initial setup completed, showing main window in current process")
        if app:
            # Force immediate show_main_window call
            app.show_main_window()
        else:
            print("[ERROR] Could not get application reference to show main window")
    
    def auto_detect_atl_path(self):
        """Auto-detect the android-translation-layer binary path"""
        # Common locations to check
        common_paths = [
            "/usr/bin/android-translation-layer",
            "/usr/local/bin/android-translation-layer",
            "/opt/android-translation-layer/android-translation-layer",
            "/opt/android-translation-layer/bin/android-translation-layer",
            os.path.expanduser("~/.local/bin/android-translation-layer"),
            os.path.expanduser("~/bin/android-translation-layer"),
            os.path.expanduser("~/Android/android-translation-layer/android-translation-layer"),
            os.path.expanduser("~/android-translation-layer/android-translation-layer")
        ]
        
        # Check if the binary exists in common locations
        for path in common_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                print(f"[DEBUG] Found android-translation-layer at: {path}")
                return path
        
        # Try to find it using 'which' command
        try:
            result = subprocess.run(["which", "android-translation-layer"], 
                                   capture_output=True, text=True, check=False)
            if result.returncode == 0 and result.stdout.strip():
                path = result.stdout.strip()
                print(f"[DEBUG] Found android-translation-layer using 'which': {path}")
                return path
        except Exception as e:
            print(f"[DEBUG] Error using 'which' command: {e}")
        
        # Try with executable name variations
        try:
            for exe_name in ["android-translation-layer", "android_translation_layer", "atl"]:
                result = subprocess.run(["which", exe_name], 
                                      capture_output=True, text=True, check=False)
                if result.returncode == 0 and result.stdout.strip():
                    path = result.stdout.strip()
                    print(f"[DEBUG] Found {exe_name} using 'which': {path}")
                    return path
        except Exception as e:
            print(f"[DEBUG] Error using 'which' for variations: {e}")
            
        # Not found
        print("[DEBUG] Could not auto-detect android-translation-layer path")
        return ""

    def _on_destroy(self, window):
        """Ensure main window is shown if we're closed"""
        print("[DEBUG] Setup window destroyed, launching main application")
        
        # Get application reference
        app = self.get_application()
        
        # Show the main window directly in this process
        print("[DEBUG] Initial setup closed, showing main window in current process")
        if app:
            # Force immediate show_main_window call
            app.show_main_window()
        else:
            print("[ERROR] Could not get application reference to show main window")

class SplashScreen(Gtk.Window):
    def __init__(self, app):
        super().__init__(application=app)
        self.app = app
        self.set_title("ATL-GUI")
        self.set_default_size(400, 500)
        # Center window manually by setting position on show
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.add_css_class("splash-window")
        
        # Set window icon for Wayland
        self.set_window_icon()
        
        # Set up CSS provider
        setup_css(self)
        
        # Main container
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_margin_top(30)
        box.set_margin_bottom(30)
        box.set_margin_start(30)
        box.set_margin_end(30)
        box.set_vexpand(True)
        box.set_valign(Gtk.Align.FILL)
        self.set_child(box)
        
        # Spacer to push content to center
        top_spacer = Gtk.Box()
        top_spacer.set_vexpand(True)
        box.append(top_spacer)
        
        # Logo container (for animation)
        self.logo_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.logo_container.set_halign(Gtk.Align.CENTER)
        box.append(self.logo_container)
        
        # Logo
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "res", "android_translation_layer.png")
        if os.path.exists(logo_path):
            self.logo = Gtk.Image()
            self.logo.set_from_file(logo_path)
            self.logo.set_pixel_size(128)
            self.logo.set_opacity(0.0)  # Start with 0 opacity for fade-in
            self.logo.add_css_class("splash-logo")
            self.logo_container.append(self.logo)
        
        # Title
        self.title_label = Gtk.Label(label="Android Translation Layer GUI")
        self.title_label.add_css_class("title-1")
        self.title_label.add_css_class("splash-title")
        self.title_label.set_opacity(0.0)  # Start with 0 opacity for fade-in
        box.append(self.title_label)
        
        # Initial setup instructions
        self.instructions_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.instructions_box.set_margin_top(20)
        self.instructions_box.set_opacity(0.0)  # Start with 0 opacity for fade-in
        self.instructions_box.add_css_class("splash-instructions")
        box.append(self.instructions_box)
        
        # Setup instructions title
        setup_title = Gtk.Label(label="Initial Setup")
        setup_title.add_css_class("title-3")
        self.instructions_box.append(setup_title)
        
        # Instructions group
        setup_group = Adw.PreferencesGroup()
        setup_group.add_css_class("card")
        setup_group.add_css_class("setup-group")
        self.instructions_box.append(setup_group)
        
        # ATL executable path instruction
        atl_row = Adw.ActionRow()
        atl_row.set_title("Specify android-translation-layer Path")
        atl_row.set_subtitle("You can skip this step if it's already installed on your system.")
        atl_icon = Gtk.Image.new_from_icon_name("system-run-symbolic")
        atl_row.add_prefix(atl_icon)
        setup_group.add(atl_row)
        
        # Environment variables instruction
        env_row = Adw.ActionRow()
        env_row.set_title("Configure Environment Variables")
        env_row.set_subtitle("Required for custom graphics drivers or compatibility settings.")
        env_icon = Gtk.Image.new_from_icon_name("preferences-system-symbolic")
        env_row.add_prefix(env_icon)
        setup_group.add(env_row)
        
        # Display mode instruction
        display_row = Adw.ActionRow()
        display_row.set_title("Select Display Mode")
        display_row.set_subtitle("Optimized display for Wayland or X11.")
        display_icon = Gtk.Image.new_from_icon_name("preferences-desktop-display-symbolic")
        display_row.add_prefix(display_icon)
        setup_group.add(display_row)
        
        # Continue button (initially hidden)
        self.continue_button = Gtk.Button(label="Continue")
        self.continue_button.add_css_class("suggested-action")
        self.continue_button.add_css_class("pill")
        self.continue_button.add_css_class("splash-button")
        self.continue_button.set_halign(Gtk.Align.CENTER)
        self.continue_button.set_margin_top(20)
        self.continue_button.set_opacity(0.0)  # Start with 0 opacity
        self.continue_button.connect("clicked", self.on_continue_clicked)
        box.append(self.continue_button)
        
        # Bottom spacer to push content to center
        bottom_spacer = Gtk.Box()
        bottom_spacer.set_vexpand(True)
        box.append(bottom_spacer)
        
        # Start animation sequence after a short delay
        GLib.timeout_add(200, self.start_animation)
    
    def start_animation(self):
        self.animation_step = 0
        self.animation_total_steps = 40
        GLib.timeout_add(25, self.animate_step)
        return False
    
    def animate_step(self):
        self.animation_step += 1
        progress = self.animation_step / self.animation_total_steps
        
        # Logo fade-in and move
        if self.animation_step <= self.animation_total_steps * 0.5:
            # First half: fade in and slight move up
            self.logo.set_opacity(min(1.0, progress * 2))
            self.logo_container.set_margin_bottom(int(progress * 20))
        
        # Title fade-in
        if self.animation_step >= self.animation_total_steps * 0.2:
            title_progress = min(1.0, (self.animation_step - self.animation_total_steps * 0.2) / (self.animation_total_steps * 0.3))
            self.title_label.set_opacity(title_progress)
        
        # Instructions fade-in
        if self.animation_step >= self.animation_total_steps * 0.5:
            instructions_progress = min(1.0, (self.animation_step - self.animation_total_steps * 0.5) / (self.animation_total_steps * 0.3))
            self.instructions_box.set_opacity(instructions_progress)
        
        # Button fade-in
        if self.animation_step >= self.animation_total_steps * 0.7:
            button_progress = min(1.0, (self.animation_step - self.animation_total_steps * 0.7) / (self.animation_total_steps * 0.3))
            self.continue_button.set_opacity(button_progress)
        
        return self.animation_step < self.animation_total_steps
    
    def on_continue_clicked(self, button):
        """Close splash screen and show setup window"""
        print("[DEBUG] Splash screen continue button clicked")
        # Close splash screen
        self.close()
        
        # Mark first run as false
        config = check_first_run(None, show_dialog=False)
        config["first_run"] = False
        
        # Save config
        try:
            config_dir = os.path.join(str(Path.home()), ".config", "atl-gui")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "config.json")
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"[DEBUG] Config saved to {config_file}")
        except Exception as e:
            print(f"Error saving config: {e}")
        
        print("[DEBUG] Creating setup window after splash screen")
        # Create setup window
        setup_window = SetupWindow(self.app)
        
        # Present the setup window
        setup_window.present()
        print("[DEBUG] Setup window presented")
        
        # Show main window after setup is closed
        setup_window.connect("destroy", self._on_setup_window_closed)
        
        # Ensure main window is shown if setup window is closed without proper signal
        GLib.timeout_add(60000, lambda: self._ensure_main_window_shown())
    
    def _on_setup_window_closed(self, window):
        """Show main window after setup is completed"""
        print("[DEBUG] Setup window closed, opening main window in current process")
        
        # Check if we're already in a subprocess with special flags
        if "--force-main-window" in sys.argv and "--skip-setup" in sys.argv:
            print("[DEBUG] Already in a subprocess with special flags, not showing main window twice")
            return
        
        # Force reload of configuration before showing main window
        try:
            config_dir = os.path.join(str(Path.home()), ".config", "atl-gui")
            config_file = os.path.join(config_dir, "config.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    print(f"[DEBUG] Reloaded config: ATL executable path = '{config.get('atl_executable_path', '')}'")
        except Exception as e:
            print(f"[ERROR] Failed to reload config: {e}")
        
        # Show main window immediately in current process
        if self.app:
            self.app.show_main_window()
        else:
            print("[ERROR] Could not get application reference to show main window")

    def set_window_icon(self):
        """Set the window icon for Wayland compatibility"""
        try:
            # Path to the application icon
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                    "res", "android_translation_layer.png")
            
            if os.path.exists(icon_path):
                print(f"[DEBUG] Setting setup window icon from: {icon_path}")
                try:
                    # Import GdkPixbuf for icon loading
                    from gi.repository import GdkPixbuf, Gdk
                    
                    # Load icon as pixbuf
                    icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file(icon_path)
                    
                    # Set the window icon
                    self.set_icon(icon_pixbuf)
                    
                    # For Wayland, try additional methods
                    try:
                        texture = Gdk.Texture.new_for_pixbuf(icon_pixbuf)
                        self.set_default_icon(texture)
                    except Exception as e:
                        print(f"[WARNING] Could not set texture icon for setup window: {e}")
                    
                    print("[DEBUG] Setup window icon set successfully")
                except Exception as e:
                    print(f"[ERROR] Failed to set setup window icon: {e}")
            else:
                print(f"[WARNING] Icon file not found for setup window: {icon_path}")
        except Exception as e:
            print(f"[ERROR] Error in set_window_icon: {e}")

    def _ensure_main_window_shown(self):
        """Ensure the main window is shown as a fallback after a minute"""
        print("[DEBUG] SplashScreen fallback: Checking if main window needs to be shown")
        # If the app is still running, make sure the main window is shown
        if self.app:
            # Check if the app has any visible windows
            windows = self.app.get_windows()
            visible_windows = [w for w in windows if w.is_visible()]
            
            if not visible_windows:
                print("[DEBUG] SplashScreen fallback: No visible windows found, showing main window")
                self.app.show_main_window()
            else:
                print(f"[DEBUG] SplashScreen fallback: Found {len(visible_windows)} visible windows, no need for action")
        
        return False  # Don't repeat

class AtlGUIApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='org.example.atlgui')
        # Set backend-specific application properties if needed
        self.backend = display_backend.get_current_backend()
        
        # Set application icon
        self.set_app_icon()
    
    def set_app_icon(self):
        """Set the application icon"""
        try:
            # Path to the application icon
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                    "res", "android_translation_layer.png")
            
            if os.path.exists(icon_path):
                print(f"[DEBUG] Setting application icon from: {icon_path}")
                try:
                    # Import GdkPixbuf for icon loading
                    from gi.repository import GdkPixbuf, Gtk
                    
                    # Load icon as pixbuf
                    icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file(icon_path)
                    
                    # Set the default icon for all windows
                    Gtk.Window.set_default_icon(icon_pixbuf)
                    print("[DEBUG] Application icon set successfully")
                except Exception as e:
                    print(f"[ERROR] Failed to set application icon: {e}")
            else:
                print(f"[WARNING] Application icon file not found: {icon_path}")
        except Exception as e:
            print(f"[ERROR] Error in set_app_icon: {e}")
    
    def show_main_window(self):
        """Create and show the main application window"""
        print("[DEBUG] Explicitly showing main window")
        
        try:
            # Check if we already have a main window
            for window in self.get_windows():
                if isinstance(window, AtlGUIWindow):
                    print("[DEBUG] Found existing main window, presenting it")
                    window.present()
                    
                    # Force additional present call after a short delay
                    GLib.timeout_add(300, lambda win=window: win.present() or False)
                    
                    return window
            
            print("[DEBUG] No existing main window found, creating new one")
            
            # Ensure we're using the latest config by re-reading from disk
            config_dir = os.path.join(str(Path.home()), ".config", "atl-gui")
            config_file = os.path.join(config_dir, "config.json")
            fresh_config = None
            
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        fresh_config = json.load(f)
                        print(f"[DEBUG] Loaded fresh config for main window: ATL path = '{fresh_config.get('atl_executable_path', '')}'")
                except Exception as e:
                    print(f"[ERROR] Failed to load fresh config: {e}")
            
            # Create the window with the application
            win = AtlGUIWindow(application=self)
            
            # Explicitly set the ATL executable path from fresh config if available
            if fresh_config and 'atl_executable_path' in fresh_config:
                win.atl_executable_path = fresh_config['atl_executable_path']
                print(f"[DEBUG] Explicitly set ATL path on window: '{win.atl_executable_path}'")
            
            display_backend.apply_backend_specific_settings(win)
            
            # Present window immediately and schedule another present call
            win.present()
            GLib.timeout_add(200, lambda win=win: win.present() or False)
            
            # Set a flag to track that we've shown the main window
            self._main_window_shown = True
            
            return win
        except Exception as e:
            print(f"[ERROR] Failed to show main window: {e}")
            
            # Try one more time with a simpler approach
            try:
                print("[DEBUG] Attempting fallback window creation")
                win = AtlGUIWindow(application=self)
                win.present()
                return win
            except Exception as e:
                print(f"[ERROR] Even fallback window creation failed: {e}")
                return None

    def do_activate(self, force_main_window=False):
        """Activate the application and show the appropriate window"""
        print(f"[DEBUG] do_activate called with force_main_window={force_main_window}")
        
        # Check if command-line arguments were passed
        if "--force-main-window" in sys.argv:
            print("[DEBUG] --force-main-window argument detected")
            force_main_window = True
            
        if "--skip-setup" in sys.argv:
            print("[DEBUG] --skip-setup argument detected")
            # Mark first run as false in config 
            try:
                config_dir = os.path.join(str(Path.home()), ".config", "atl-gui")
                config_file = os.path.join(config_dir, "config.json")
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                        config["first_run"] = False
                    os.makedirs(config_dir, exist_ok=True)
                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=2)
                    print("[DEBUG] Config updated to skip first run")
            except Exception as e:
                print(f"[ERROR] Failed to update config: {e}")
            
            # Force main window to show
            force_main_window = True
        
        # Check existing windows
        windows = self.get_windows()
        if windows:
            print(f"[DEBUG] Application already has {len(windows)} windows")
            # Find an existing window to present
            for window in windows:
                if isinstance(window, AtlGUIWindow):
                    print("[DEBUG] Found existing main window, presenting it")
                    window.present()
                    return
        
        # Check if it's the first run
        config = check_first_run(None, show_dialog=False)
        
        # If force_main_window is True, skip the first-run check
        if force_main_window or not config.get("first_run", True):
            print("[DEBUG] Opening main window")
            self.show_main_window()
        else:
            print("[DEBUG] First run detected, showing splash screen")
            # Show splash screen on first run
            splash = SplashScreen(self)
            splash.present()
            
            # Add a fallback timer to ensure main window appears even if setup flow fails
            GLib.timeout_add(120000, self._ensure_main_window_shown)
    
    def _ensure_main_window_shown(self):
        """Ensure the main window is shown as a fallback if no windows are visible"""
        windows = self.get_windows()
        visible_windows = [w for w in windows if w.is_visible()]
        
        if not visible_windows:
            print("[DEBUG] Application fallback: No visible windows after timeout, showing main window")
            self.show_main_window()
        else:
            print(f"[DEBUG] Application has {len(visible_windows)} visible windows, fallback not needed")
            
        return False  # Don't repeat this timeout

def find_main_script():
    """Find the main ATL-GUI script"""
    try:
        # Get direct paths
        src_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(src_dir)
        
        # Look for the main entry point in standard locations
        main_script_candidates = [
            os.path.join(project_dir, "atl_gui.py"),  # Most likely location
            os.path.join(project_dir, "main.py"),
            os.path.join(project_dir, "run.py"),
            os.path.join(project_dir, "app.py"),
            os.path.abspath(sys.argv[0])  # Current script as fallback
        ]
        
        # Find the first existing, executable candidate
        for candidate in main_script_candidates:
            if os.path.exists(candidate) and os.path.isfile(candidate):
                print(f"[DEBUG] Found main script: {candidate}")
                if candidate.endswith('.py') and os.access(candidate, os.X_OK):
                    return candidate
        
        # Return current script as last resort
        return os.path.abspath(sys.argv[0])
    except Exception as e:
        print(f"[ERROR] Error finding main script: {e}")
        return os.path.abspath(sys.argv[0])

def main():
    # Check if we should skip launching the app (for debug tools)
    if os.environ.get('ATL_NO_LAUNCH') == '1':
        print("Application launch skipped due to ATL_NO_LAUNCH environment variable.")
        return 0
    
    # Check if we're already running with special flags
    # If we are, we were likely launched by another process using subprocess
    # and should not create another app instance
    if "--force-main-window" in sys.argv and "--skip-setup" in sys.argv:
        # We only skip if BOTH flags are present to distinguish from user-provided flags
        print("[DEBUG] Detected existing subprocess with special flags.")
        print("[DEBUG] Will not create another app instance to prevent duplication.")
        
        # Create an environment variable to mark that we skipped
        # This helps with debugging if needed
        os.environ['ATL_SKIPPED_LAUNCH'] = '1'
        return 0
        
    app = AtlGUIApp()
    
    # Add a safety timeout to ensure a main window is shown
    GLib.timeout_add(3000, lambda: ensure_main_window_shown(app) or False)
    
    return app.run(None)

def ensure_main_window_shown(app):
    """Global fallback to ensure a main window is visible"""
    if not app:
        return False
        
    try:
        # Check if there are any visible windows
        windows = app.get_windows()
        visible_windows = [w for w in windows if w.is_visible()]
        
        if not visible_windows:
            print("[DEBUG] GLOBAL FALLBACK: No visible windows detected after 3 seconds")
            print("[DEBUG] GLOBAL FALLBACK: Forcing main window to appear")
            app.show_main_window()
    except Exception as e:
        print(f"[ERROR] GLOBAL FALLBACK failed: {e}")
    
    return False  # Don't repeat

if __name__ == '__main__':
    main() 