import gi
import os
import subprocess
import signal
from pathlib import Path
import datetime
import shlex

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk, GLib, Pango, GdkPixbuf

from src.views.welcome_view import create_welcome_view
from src.views.testing_view import create_testing_view
from src.views.results_view import create_results_view
from src.utils.css_provider import setup_css
from src.utils.display_backend import get_current_backend
from src.utils.initial_setup import check_first_run
from src.utils.terminal_module import TerminalManager

class AtlGUIWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Store the current backend type
        self.backend_type = get_current_backend()
        print(f"Window created with {self.backend_type} backend")

        # Initialize terminal manager
        self.terminal_manager = TerminalManager()
        print("[DEBUG] Terminal manager initialized in window")
        
        # Start the terminal process to ensure it's ready when needed
        if self.terminal_manager.start():
            print("[DEBUG] Terminal process started successfully from window init")
        else:
            print("[DEBUG] Failed to start terminal process from window init")
        
        # Connect close request to clean up resources
        self.connect("close-request", self.on_window_close)

        self.set_default_size(1000, 700)
        self.set_title("Android Translation Layer")
        
        # Logo dosyasının tam yolunu kaydet
        self.logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "res", "android_translation_layer.png")

        # Set application icon (important for Wayland)
        self.set_icon_from_file()
        
        # CSS Sağlayıcı ayarla - kenarları kaldırmak için
        setup_css(self)

        # Create toast overlay for notifications
        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)

        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.toast_overlay.set_child(main_box)

        # Header bar
        self.header = Adw.HeaderBar()
        
        # Add settings button to header bar
        settings_button = Gtk.Button()
        settings_button.set_tooltip_text("Settings")
        
        # Create a box to hold icon and text
        settings_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        settings_box.set_margin_start(8)
        settings_box.set_margin_end(8)
        
        # Add icon
        settings_icon = Gtk.Image.new_from_icon_name("preferences-system-symbolic")
        settings_box.append(settings_icon)
        
        # Add text label
        settings_label = Gtk.Label(label="Settings")
        settings_box.append(settings_label)
        
        settings_button.set_child(settings_box)
        settings_button.connect("clicked", self.on_settings_button_clicked)
        
        self.header.pack_end(settings_button)
        
        main_box.append(self.header)

        # Main content
        self.main_content = Adw.Clamp()
        self.main_content.set_maximum_size(1200)
        self.main_content.set_tightening_threshold(800)
        main_box.append(self.main_content)

        # Padded box for main content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content_box.set_margin_top(32)
        content_box.set_margin_bottom(32)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        self.main_content.set_child(content_box)

        # Welcome view - shown initially
        self.welcome_view = create_welcome_view(self)
        content_box.append(self.welcome_view)

        # Testing view - shown after selecting a folder
        self.testing_view = create_testing_view(self)
        self.testing_view.set_visible(False)
        content_box.append(self.testing_view)

        # Results view - shown after tests are completed
        self.results_view = create_results_view(self)
        self.results_view.set_visible(False)
        content_box.append(self.results_view)

        # Test control area
        test_control_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        test_control_box.set_margin_top(16)
        
        content_box.append(test_control_box)

        # Initialize variables
        self.current_process = None
        self.apk_files = []
        self.current_apk_index = 0
        self.test_results = {}  # APK path: Result (working/not_working)
        self.env_variables = {}  # Environment variables
        self.current_apk_ready = False  # Test start status
        self.terminal_logs = {}  # APK path: Terminal output - To prevent error
        self.script_path = ""  # Path to no-internet script
        self.sudo_password = ""  # Sudo password if needed
        self.window_width = None  # Custom window width
        self.window_height = None  # Custom window height
        self.additional_env_vars = {}  # Additional environment variables
        self.use_activity = False  # Whether to use activity launcher (-l option)
        self.activity_name = ""  # Activity name to launch
        self.custom_pythonpath = ""  # Custom PYTHONPATH setting
        
        # Initialize new option attributes
        self.use_instrumentation = False
        self.instrumentation_class = ""
        self.use_uri = False
        self.uri_value = ""
        self.jvm_options = []
        self.string_keys = {}
        self.install_flag = False
        self.install_internal = False
        
        # GApplication options
        self.gapplication_app_id = ""
        
        # Settings dialog state tracking
        self._settings_dialog_active = False
        
        # Connect double-click handler to window
        click_controller = Gtk.GestureClick.new()
        click_controller.set_button(1)  # Left mouse button
        click_controller.connect("pressed", self._on_window_click_pressed)
        self.add_controller(click_controller)
        
        # Load configuration from initial setup
        self.config = check_first_run(self)
        
        # Apply configuration
        if self.config:
            # Set ATL executable path
            self.atl_executable_path = self.config.get("atl_executable_path", "")
            print(f"[DEBUG] Loaded ATL executable path from config: '{self.atl_executable_path}'")
            
            # Log a warning if the path is empty
            if not self.atl_executable_path:
                print("[WARNING] ATL executable path is empty in config")
            
            # Set environment variables
            env_vars = self.config.get("environment_variables", {})
            self.env_variables.update(env_vars)
            
            # Update environment variables text field if it exists
            if hasattr(self, 'env_text_view'):
                env_text = "\n".join([f"{key}={value}" for key, value in env_vars.items()])
                if env_text:
                    self.env_text_view.get_buffer().set_text(env_text)

    # Import all methods from the handlers
    from src.handlers.file_handlers import (
        on_file_clicked, on_file_selected, on_folder_clicked, on_folder_selected,
        parse_env_variables, show_error_dialog, find_apk_files
    )
    
    from src.handlers.test_handlers import (
        test_next_apk, on_skip_clicked, on_finish_all_clicked, on_output,
        auto_mark_as_working, auto_mark_as_not_working, kill_current_process,
        on_working_clicked, on_not_working_clicked, on_start_test_clicked,
        start_test, show_test_buttons
    )
    
    from src.handlers.terminal_handlers import (
        process_terminal_output, check_terminal_health
    )
    
    from src.handlers.settings_handlers import (
        on_settings_clicked, on_browse_script_clicked, on_script_selected,
        show_script_error, show_test_settings_dialog, on_settings_response,
        on_script_validation_response, on_sudo_warning_response
    )
    
    from src.handlers.results_handlers import (
        show_test_results, on_new_test_clicked, on_export_clicked,
        on_export_dialog_response, export_results_to_file, show_apk_errors,
        show_full_apk_logs
    )

    def set_icon_from_file(self):
        """Set the application icon from the logo file"""
        try:
            if os.path.exists(self.logo_path):
                print(f"[DEBUG] Setting window icon from: {self.logo_path}")
                
                # Load the icon using GdkPixbuf
                icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.logo_path)
                
                # For Wayland, we need to use set_icon_name in addition to set_icon
                self.set_icon(icon_pixbuf)
                
                # Force icon update via direct Wayland protocol if needed
                if self.backend_type == 'wayland':
                    # Try to create a texture from the pixbuf
                    try:
                        from gi.repository import Gdk
                        texture = Gdk.Texture.new_for_pixbuf(icon_pixbuf)
                        self.set_default_icon(texture)
                        print("[DEBUG] Set window icon with Wayland texture")
                    except Exception as e:
                        print(f"[WARNING] Could not create texture for Wayland icon: {e}")
                
                # Also try setting application-wide icon
                app = self.get_application()
                if app is not None:
                    try:
                        # For GTK4/Adw, we need to use set_default_icon for the app
                        Gtk.Window.set_default_icon(icon_pixbuf)
                        print("[DEBUG] Set application-wide default icon")
                    except Exception as e:
                        print(f"[WARNING] Could not set application icon: {e}")
                
                print("[DEBUG] Window icon set successfully")
            else:
                print(f"[WARNING] Icon file not found: {self.logo_path}")
        except Exception as e:
            print(f"[ERROR] Failed to set window icon: {e}")
            
    def restore_original_size(self):
        """Force window to resize to its original dimensions"""
        if hasattr(self, 'original_width') and hasattr(self, 'original_height'):
            print(f"DEBUG: Window trying to restore size to: {self.original_width}x{self.original_height}")
            
            # Get current size first
            current_width, current_height = self.get_default_size()
            print(f"DEBUG: Current window size before resize: {current_width}x{current_height}")
            
            # Set default size
            self.set_default_size(self.original_width, self.original_height)
            
            # Try to enforce the size with GTK 4 compatible methods
            # Force redraw
            self.queue_resize()
            
            # Try to use the surface API to resize
            surface = self.get_surface()
            if surface:
                try:
                    # Backend-specific resize approach
                    if self.backend_type == 'wayland':
                        # Wayland prefers to have the surface request the size
                        # rather than forcing it directly
                        if hasattr(surface, 'set_size_request'):
                            surface.set_size_request(self.original_width, self.original_height)
                        else:
                            surface.set_size(self.original_width, self.original_height)
                    else:
                        # X11 approach
                        surface.set_size(self.original_width, self.original_height)
                    
                    print(f"DEBUG: Set surface size to: {self.original_width}x{self.original_height}")
                except Exception as e:
                    print(f"DEBUG: Error setting surface size: {e}")
            
            # Get size after operations
            new_width, new_height = self.get_default_size()
            print(f"DEBUG: Window size after force resize: {new_width}x{new_height}")
            
            return True
        else:
            print("DEBUG: No original window size stored for restore")
            return False 

    def force_resize(self, width, height):
        """Direct window resize implementation for GTK 4"""
        print(f"FORCE RESIZE called with {width}x{height}")
        
        # First update default size
        self.set_default_size(width, height)
        
        # Get the top-level native object
        native = self.get_native()
        surface = self.get_surface()
        
        if surface:
            # Direct surface size request
            try:
                # Backend-specific approach
                if self.backend_type == 'wayland':
                    # For Wayland, we need to use a combination of approaches
                    # Request the size through different APIs
                    self.set_size_request(width, height)
                    
                    # Use present to trigger recalculation
                    GLib.timeout_add(10, lambda: self.present())
                    
                    # Some Wayland compositors need a hint that size changed
                    if hasattr(surface, 'set_size_request'):
                        surface.set_size_request(width, height)
                    else:
                        surface.set_size(width, height)
                else:
                    # X11 approach - direct size setting
                    surface.set_size(width, height)
                    
                print(f"Set surface size to {width}x{height}")
            except Exception as e:
                print(f"Surface resize error: {e}")
        
        # Request window manager to resize (most reliable method for window managers)
        GLib.timeout_add(10, lambda: self.present())
        
        # Immediately then set to correct size
        GLib.timeout_add(50, lambda: self.set_default_size(width, height))
        
        # Check result
        GLib.timeout_add(100, lambda: self._check_size(width, height))
        
        return True

    def _check_size(self, expected_width, expected_height):
        """Check if size was applied correctly"""
        actual_width, actual_height = self.get_default_size()
        print(f"Window size after force_resize: expected={expected_width}x{expected_height}, actual={actual_width}x{actual_height}")
        
        # Try again if it didn't work
        if actual_width != expected_width or actual_height != expected_height:
            print("Size mismatch, trying again...")
            self.set_default_size(expected_width, expected_height)
            
            # For Wayland, we may need additional approaches
            if self.backend_type == 'wayland':
                # Request a redraw which can help with Wayland resizing
                self.queue_resize()
                self.queue_draw()
        
        return False 

    def set_fixed_size(self, width, height):
        """Set the window to a fixed size and prevent further automatic resizing"""
        # Set the default size first
        self.set_default_size(width, height)
        
        # Use the surface API if available
        surface = self.get_surface()
        if surface:
            try:
                # Backend-specific approach
                if self.backend_type == 'wayland':
                    # For Wayland, prefer setting size constraints
                    # through the widget hierarchy
                    self.set_size_request(width, height)
                    
                    # Some Wayland implementations support surface sizing
                    if hasattr(surface, 'set_size_request'):
                        surface.set_size_request(width, height)
                    else:
                        surface.set_size(width, height)
                else:
                    # X11 approach
                    surface.set_size(width, height)
            except Exception as e:
                print(f"Set surface size error: {e}")
        
        # Schedule reset of size request
        GLib.timeout_add(10, lambda: self._reset_size_request(width, height))
        
        return True
    
    def _reset_size_request(self, width, height):
        """Reset min/max size constraints to enforce fixed size"""
        try:
            # Enforce fixed size by setting min/max size
            self.set_size_request(width, height)
            
            # For Wayland, we may need to add specific constraints
            if self.backend_type == 'wayland':
                # Set minimum and maximum size
                self.set_size_request(width, height)
                # Force a redraw to apply the size
                self.queue_resize()
                
            print(f"Size request set to fixed {width}x{height}")
        except Exception as e:
            print(f"Reset size request failed: {e}")
        return False 
        
    def _on_window_click_pressed(self, gesture, n_press, x, y):
        """Handle window click events to control fullscreen behavior"""
        # If this is a double click and we have settings dialog open
        if n_press == 2 and self._settings_dialog_active:
            # Prevent fullscreen action by consuming the event
            return True
        
        # Let other clicks proceed normally
        return False
    
    def mark_settings_dialog_active(self, active):
        """Mark settings dialog as active or inactive to control fullscreen behavior"""
        self._settings_dialog_active = active

    def on_settings_button_clicked(self, button):
        """Open the settings dialog when the settings button is clicked"""
        print("Settings button clicked")
        
        # Import the SetupWindow from app.py
        from src.app import SetupWindow
        
        # Mark settings dialog as active
        self.mark_settings_dialog_active(True)
        
        # Show the setup window
        setup_window = SetupWindow(self.get_application())
        # Set the parent to this window
        setup_window.set_transient_for(self)
        setup_window.connect("close-request", self.on_setup_window_close)
        setup_window.present()
    
    def on_setup_window_close(self, window):
        """Handle setup window closure"""
        print("Setup window closed")
        # Reset settings dialog active flag
        self.mark_settings_dialog_active(False)
        
        # Reload config
        from src.utils.initial_setup import check_first_run
        self.config = check_first_run(self, show_dialog=False)
        
        # Explicitly reload the ATL executable path from config
        try:
            import os
            import json
            from pathlib import Path
            
            config_dir = os.path.join(str(Path.home()), ".config", "atl-gui")
            config_file = os.path.join(config_dir, "config.json")
            
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    fresh_config = json.load(f)
                    # Set ATL executable path directly from fresh config
                    if 'atl_executable_path' in fresh_config:
                        self.atl_executable_path = fresh_config['atl_executable_path']
                        print(f"[DEBUG] EXPLICITLY reloaded ATL path: '{self.atl_executable_path}'")
        except Exception as e:
            print(f"[ERROR] Failed to reload ATL path: {e}")
        
        # Show a confirmation toast
        toast = Adw.Toast.new("Settings updated")
        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)
        
        return False

    def on_apk_selected(self, apk_path):
        """Handle APK selection"""
        if not apk_path:
            return
            
        self.current_apk = apk_path
        self.apk_label.set_text(f"Selected APK: {os.path.basename(apk_path)}")
        
        # Update system and APK information
        self.update_system_info(apk_path)

    def update_system_info(self, apk_path):
        """Update system and APK architecture information"""
        # Get APK architecture using our zipfile-based function
        architectures = self.get_apk_architectures(apk_path)
        if architectures:
            self.apk_arch_value.set_text(f"APK Arch: {', '.join(architectures)}")
        else:
            self.apk_arch_value.set_text("APK Arch: No native libraries found")
            
        # Get system information
        try:
            import platform
            import distro
            
            # Get system architecture
            self.arch_value.set_text(f"System Arch: {platform.machine()}")
            
            # Get distribution information
            try:
                distro_info = distro.linux_distribution(full_distribution_name=True)
                if distro_info and distro_info[0]:
                    self.distro_value.set_text(f"Distro: {distro_info[0]} {distro_info[1]}")
                else:
                    # Try alternative method
                    import os
                    if os.path.exists('/etc/os-release'):
                        with open('/etc/os-release', 'r') as f:
                            lines = f.readlines()
                            name = ''
                            version = ''
                            for line in lines:
                                if line.startswith('NAME='):
                                    name = line.split('=')[1].strip().strip('"\'')
                                elif line.startswith('VERSION='):
                                    version = line.split('=')[1].strip().strip('"\'')
                            if name:
                                self.distro_value.set_text(f"Distro: {name} {version}")
                            else:
                                self.distro_value.set_text("Distro: Unknown")
                    else:
                        self.distro_value.set_text("Distro: Unknown")
            except Exception as e:
                print(f"Error getting distro info: {e}")
                self.distro_value.set_text("Distro: Unknown")
        except Exception as e:
            print(f"Error getting system information: {e}")
            self.arch_value.set_text("System Arch: Unknown")
            self.distro_value.set_text("Distro: Unknown")

    def get_apk_architectures(self, apk_path):
        """Get supported architectures from an APK file using zipfile module"""
        try:
            import zipfile
            with zipfile.ZipFile(apk_path, 'r') as apk:
                architectures = set()
                for file in apk.namelist():
                    if file.startswith('lib/'):
                        parts = file.split('/')
                        if len(parts) > 1:
                            arch = parts[1]
                            architectures.add(arch)
                
                if not architectures:
                    return []
                return sorted(architectures)
        except Exception as e:
            print(f"Error extracting APK architectures: {e}")
            return []

    def on_window_close(self, window):
        """Handle cleanup when window is closed"""
        print("[DEBUG] Window close requested, cleaning up resources...")
        
        # Clean up terminal manager
        if hasattr(self, 'terminal_manager'):
            print("[DEBUG] Forcefully killing terminal process...")
            self.terminal_manager.kill_terminal()
            
        # Kill any running process
        self.kill_current_process()
        
        # Let the window close normally
        return False

