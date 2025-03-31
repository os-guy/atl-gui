import gi
import os
import shlex
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

def on_settings_clicked(self, button):
    # Mevcut APK için ek seçenekler menüsünü tekrar aç
    if self.current_apk_index < len(self.apk_files):
        apk_path = self.apk_files[self.current_apk_index]
        apk_name = os.path.basename(apk_path)
        self.show_test_settings_dialog(apk_name)

def on_browse_script_clicked(self, button):
    # Script dosya seçim diyaloğu
    file_dialog = Gtk.FileDialog()
    file_dialog.set_title("Select No-Internet Script")
    
    # Filtre ekle
    script_filter = Gtk.FileFilter()
    script_filter.set_name("Shell Scripts")
    script_filter.add_pattern("*.sh")
    
    filters = Gtk.FilterListModel()
    filters.set_filter(script_filter)
    file_dialog.set_filters(filters)

    file_dialog.open(self, None, self.on_script_selected)
    
def on_script_selected(self, dialog, result):
    try:
        file = dialog.open_finish(result)
        if file:
            path = file.get_path()
            self.script_entry.set_text(path)
            
            # Validate the selected script
            if not os.path.exists(path):
                self.show_script_error(f"Script not found: '{path}'")
            elif not os.path.isfile(path):
                self.show_script_error(f"The specified path is not a file: '{path}'")
            elif not os.access(path, os.X_OK):
                self.show_script_error(f"Script is not executable: '{path}'\n\nPlease make it executable with:\nchmod +x {shlex.quote(path)}")
    except Exception as e:
        print(f"Error selecting script: {e}")
        toast = Adw.Toast.new(f"Could not select script: {str(e)}")
        self.toast_overlay.add_toast(toast)
        
def show_script_error(self, message):
    error_dialog = Adw.AlertDialog()
    error_dialog.set_title("Script Error")
    error_dialog.set_body(message)
    error_dialog.add_response("ok", "OK")
    error_dialog.present(self)

def show_test_settings_dialog(self, apk_name):
    # Create a settings dialog
    dialog = Adw.AlertDialog()
    dialog.set_title(f"Settings for {apk_name}")
    
    # Create content box
    content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
    content_box.set_margin_top(16)
    content_box.set_margin_bottom(16)
    content_box.set_margin_start(16)
    content_box.set_margin_end(16)
    
    # Top section with Resolution and Activity Launcher in horizontal layout
    top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
    top_box.set_homogeneous(True)
    
    # ===== COLUMN 1: Resolution settings =====
    resolution_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    resolution_label = Gtk.Label(label="Resolution Settings")
    resolution_label.set_halign(Gtk.Align.START)
    resolution_label.add_css_class("heading")
    resolution_box.append(resolution_label)
    
    resolution_desc = Gtk.Label(label="Set custom window size for the application")
    resolution_desc.set_halign(Gtk.Align.START)
    resolution_desc.add_css_class("caption")
    resolution_box.append(resolution_desc)
    
    # Width and height inputs
    dimensions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    dimensions_box.set_margin_top(8)
    
    # Width
    width_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    width_box.set_hexpand(True)
    width_label = Gtk.Label(label="Width")
    width_label.set_halign(Gtk.Align.START)
    width_box.append(width_label)
    
    self.width_entry = Gtk.Entry()
    self.width_entry.set_placeholder_text("Width (e.g. 800)")
    if hasattr(self, 'window_width') and self.window_width:
        self.width_entry.set_text(str(self.window_width))
    width_box.append(self.width_entry)
    dimensions_box.append(width_box)
    
    # Height
    height_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    height_box.set_hexpand(True)
    height_label = Gtk.Label(label="Height")
    height_label.set_halign(Gtk.Align.START)
    height_box.append(height_label)
    
    self.height_entry = Gtk.Entry()
    self.height_entry.set_placeholder_text("Height (e.g. 600)")
    if hasattr(self, 'window_height') and self.window_height:
        self.height_entry.set_text(str(self.window_height))
    height_box.append(self.height_entry)
    dimensions_box.append(height_box)
    
    resolution_box.append(dimensions_box)
    top_box.append(resolution_box)
    
    # ===== COLUMN 2: Activity Launcher settings =====
    activity_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    activity_label = Gtk.Label(label="Activity Launcher")
    activity_label.set_halign(Gtk.Align.START)
    activity_label.add_css_class("heading")
    activity_box.append(activity_label)
    
    activity_desc = Gtk.Label(label="Launch a specific activity from the APK (-l option)")
    activity_desc.set_halign(Gtk.Align.START)
    activity_desc.add_css_class("caption")
    activity_desc.set_wrap(True)
    activity_box.append(activity_desc)
    
    # Activity input
    self.activity_entry = Gtk.Entry()
    self.activity_entry.set_margin_top(8)
    self.activity_entry.set_placeholder_text("Activity name (optional)")
    if hasattr(self, 'activity_name') and self.activity_name:
        self.activity_entry.set_text(self.activity_name)
    activity_box.append(self.activity_entry)
    
    top_box.append(activity_box)
    content_box.append(top_box)
    
    # Middle section - No Internet Mode
    no_internet_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    no_internet_box.set_margin_top(16)
    no_internet_label = Gtk.Label(label="No Internet Mode")
    no_internet_label.set_halign(Gtk.Align.START)
    no_internet_label.add_css_class("heading")
    no_internet_box.append(no_internet_label)
    
    no_internet_desc = Gtk.Label(label="Disable internet access for the application using a script")
    no_internet_desc.set_halign(Gtk.Align.START)
    no_internet_desc.add_css_class("caption")
    no_internet_desc.set_wrap(True)
    no_internet_box.append(no_internet_desc)
    
    # Script selection and sudo password in a horizontal layout
    script_sudo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
    script_sudo_box.set_margin_top(8)
    
    # Script selection
    script_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    script_box.set_hexpand(True)
    
    script_label = Gtk.Label(label="Script Path")
    script_label.set_halign(Gtk.Align.START)
    script_box.append(script_label)
    
    script_entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    
    self.script_entry = Gtk.Entry()
    self.script_entry.set_placeholder_text("Path to script (optional)")
    self.script_entry.set_hexpand(True)
    # Fill with existing value if available
    if hasattr(self, 'script_path') and self.script_path:
        self.script_entry.set_text(self.script_path)
    script_entry_box.append(self.script_entry)
    
    browse_button = Gtk.Button(label="Browse")
    browse_button.connect("clicked", self.on_browse_script_clicked)
    script_entry_box.append(browse_button)
    
    script_box.append(script_entry_box)
    script_sudo_box.append(script_box)
    
    # Sudo password
    sudo_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    sudo_box.set_hexpand(True)
    
    sudo_label = Gtk.Label(label="Sudo Password")
    sudo_label.set_halign(Gtk.Align.START)
    sudo_box.append(sudo_label)
    
    # Use regular Entry instead of PasswordEntry
    self.sudo_entry = Gtk.Entry()
    self.sudo_entry.set_placeholder_text("Enter sudo password (optional)")
    self.sudo_entry.set_visibility(False)  # Password mode
    # Fill with existing value if available
    if hasattr(self, 'sudo_password') and self.sudo_password:
        self.sudo_entry.set_text(self.sudo_password)
    sudo_box.append(self.sudo_entry)
    
    script_sudo_box.append(sudo_box)
    no_internet_box.append(script_sudo_box)
    content_box.append(no_internet_box)
    
    # Additional environment variables
    env_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    env_box.set_margin_top(16)
    
    env_label = Gtk.Label(label="Additional Environment Variables")
    env_label.set_halign(Gtk.Align.START)
    env_label.add_css_class("heading")
    env_box.append(env_label)
    
    env_desc = Gtk.Label(label="Enter additional KEY=VALUE pairs below, one per line. These will override the default variables.")
    env_desc.set_halign(Gtk.Align.START)
    env_desc.add_css_class("caption")
    env_desc.set_wrap(True)
    env_box.append(env_desc)
    
    # Text area for environment variables
    self.additional_env_text_view = Gtk.TextView()
    self.additional_env_text_view.set_wrap_mode(Gtk.WrapMode.WORD)
    self.additional_env_text_view.set_top_margin(8)
    self.additional_env_text_view.set_bottom_margin(8)
    self.additional_env_text_view.set_left_margin(8)
    self.additional_env_text_view.set_right_margin(8)
    self.additional_env_text_view.set_monospace(True)
    
    # Fill with existing value if available
    if hasattr(self, 'additional_env_vars') and self.additional_env_vars:
        buffer_text = "\n".join([f"{key}={value}" for key, value in self.additional_env_vars.items()])
        self.additional_env_text_view.get_buffer().set_text(buffer_text)
    
    # Scrolled window for env vars
    env_scroll = Gtk.ScrolledWindow()
    env_scroll.set_min_content_height(100)
    env_scroll.set_vexpand(False)
    env_scroll.set_child(self.additional_env_text_view)
    env_scroll.add_css_class("card")
    
    env_box.append(env_scroll)
    content_box.append(env_box)
    
    # Set dialog content
    dialog.set_extra_child(content_box)
    
    # Add actions
    dialog.add_response("cancel", "Cancel")
    dialog.add_response("save", "Save")
    dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
    
    # Handle response
    dialog.connect("response", self.on_settings_response)
    
    # Show dialog
    dialog.present(self)

def on_settings_response(self, dialog, response):
    if response == "save":
        # Save script path and sudo password
        script_path = self.script_entry.get_text().strip()
        self.sudo_password = self.sudo_entry.get_text().strip()
        
        # Validate script path if provided
        if script_path:
            script_error = None
            if not os.path.exists(script_path):
                script_error = f"Script not found: '{script_path}'"
            elif not os.path.isfile(script_path):
                script_error = f"The specified path is not a file: '{script_path}'"
            elif not os.access(script_path, os.X_OK):
                script_error = f"Script is not executable: '{script_path}'\n\nPlease make it executable with:\nchmod +x {shlex.quote(script_path)}"
            
            if script_error:
                # Show warning but allow user to continue if they want
                error_dialog = Adw.AlertDialog()
                error_dialog.set_title("Script Error")
                error_dialog.set_body(f"{script_error}\n\nDo you want to continue using this script anyway?")
                
                # Add responses
                error_dialog.add_response("discard", "Remove Script")
                error_dialog.add_response("continue", "Continue Anyway")
                error_dialog.set_response_appearance("discard", Adw.ResponseAppearance.DESTRUCTIVE)
                error_dialog.set_default_response("discard")
                
                # Handle response
                error_dialog.connect("response", self.on_script_validation_response, script_path, dialog)
                error_dialog.present(self)
                return
        
        # No script validation issues, save the script path
        self.script_path = script_path
        
        # Save activity launcher settings
        self.activity_name = self.activity_entry.get_text().strip()
        self.use_activity = bool(self.activity_name)  # Set to True if activity name is provided
        
        # Save resolution settings
        width_text = self.width_entry.get_text().strip()
        height_text = self.height_entry.get_text().strip()
        
        try:
            # Parse width and height if provided
            if width_text:
                self.window_width = int(width_text)
            else:
                self.window_width = None
                
            if height_text:
                self.window_height = int(height_text)
            else:
                self.window_height = None
        except ValueError:
            # Show error for invalid numeric input
            error_dialog = Adw.AlertDialog()
            error_dialog.set_title("Invalid Resolution")
            error_dialog.set_body("Width and height must be valid numbers. Using default resolution.")
            error_dialog.add_response("ok", "OK")
            error_dialog.present(self)
            self.window_width = None
            self.window_height = None
        
        # Show confirmation
        toast = Adw.Toast.new("Settings saved")
        self.toast_overlay.add_toast(toast)
        
        # Warning if script is specified but no sudo password
        if self.script_path and not self.sudo_password:
            error_dialog = Adw.AlertDialog()
            error_dialog.set_title("Missing Sudo Password")
            error_dialog.set_body("Script is specified but no sudo password was entered. The script may not work.")
            
            # Go back button
            error_dialog.add_response("back", "Go Back")
            error_dialog.set_response_appearance("back", Adw.ResponseAppearance.SUGGESTED)
            
            # Continue anyway button
            error_dialog.add_response("continue", "Continue Anyway")
            
            error_dialog.set_default_response("back")
            error_dialog.set_close_response("back")
            
            # Handle response
            error_dialog.connect("response", self.on_sudo_warning_response, dialog)
            error_dialog.present(self)
            return
        
        # Parse additional environment variables
        buffer = self.additional_env_text_view.get_buffer()
        start_iter = buffer.get_start_iter()
        end_iter = buffer.get_end_iter()
        env_text = buffer.get_text(start_iter, end_iter, True)
        
        # Create or update additional environment variables
        self.additional_env_vars = {}
        invalid_lines = []
        
        # Process each line
        for line_num, line in enumerate(env_text.splitlines(), 1):
            line = line.strip()
            if not line:  # Skip empty lines
                continue
                
            if "=" not in line:
                invalid_lines.append(f"Line {line_num}: '{line}' - not in KEY=VALUE format")
                continue
                
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            
            # Is key valid?
            if not key:
                invalid_lines.append(f"Line {line_num}: '{line}' - invalid KEY")
                continue
                
            # If everything is valid, add to environment variables
            self.additional_env_vars[key] = value
        
        # Show warning if invalid environment variables
        if invalid_lines:
            error_dialog = Adw.AlertDialog()
            error_dialog.set_title("Invalid Environment Variables")
            error_dialog.set_body("The following lines are not in KEY=VALUE format and will be skipped:\n\n" + 
                                "\n".join(invalid_lines))
            error_dialog.add_response("ok", "OK")
            error_dialog.present(self)
            
def on_script_validation_response(self, warning_dialog, response, script_path, settings_dialog):
    if response == "discard":
        # Remove the script path
        self.script_entry.set_text("")
        # Show settings dialog again
        settings_dialog.present(self)
    elif response == "continue":
        # User wants to continue with the invalid script
        self.script_path = script_path
        
        # Continue with rest of settings save process
        self.activity_name = self.activity_entry.get_text().strip()
        self.use_activity = bool(self.activity_name)
        
        # Parse resolution settings
        width_text = self.width_entry.get_text().strip()
        height_text = self.height_entry.get_text().strip()
        
        try:
            if width_text:
                self.window_width = int(width_text)
            else:
                self.window_width = None
                
            if height_text:
                self.window_height = int(height_text)
            else:
                self.window_height = None
        except ValueError:
            self.window_width = None
            self.window_height = None
        
        # Parse additional environment variables
        buffer = self.additional_env_text_view.get_buffer()
        start_iter = buffer.get_start_iter()
        end_iter = buffer.get_end_iter()
        env_text = buffer.get_text(start_iter, end_iter, True)
        
        # Create or update additional environment variables
        self.additional_env_vars = {}
        
        # Process each line
        for line in env_text.splitlines():
            line = line.strip()
            if not line or "=" not in line:
                continue
                
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            
            if key:
                self.additional_env_vars[key] = value
        
        # Show confirmation
        toast = Adw.Toast.new("Settings saved with invalid script")
        self.toast_overlay.add_toast(toast)
        
        # Check for sudo password
        if not self.sudo_password:
            error_dialog = Adw.AlertDialog()
            error_dialog.set_title("Missing Sudo Password")
            error_dialog.set_body("Script is specified but no sudo password was entered. The script may not work.")
            error_dialog.add_response("ok", "OK")
            error_dialog.present(self)

def on_sudo_warning_response(self, warning_dialog, response, settings_dialog):
    if response == "back":
        # Show settings dialog again
        settings_dialog.present(self)
    # Continue Anyway - do nothing, just continue 