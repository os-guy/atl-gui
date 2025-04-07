import gi
import os
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

def on_file_clicked(self, button):
    # Skip dialog in debug mode
    if os.environ.get('ATL_DEBUG_MODE'):
        print("Debug mode: Skipping file dialog")
        return
        
    file_dialog = Gtk.FileDialog()
    file_dialog.set_title("Select APK File")

    # APK dosya filtresi ekle
    file_filter = Gtk.FileFilter()
    file_filter.set_name("Android Applications")
    file_filter.add_pattern("*.apk")
    
    filters = Gtk.FilterListModel()
    filters.set_filter(file_filter)
    file_dialog.set_filters(filters)

    file_dialog.open(self, None, self.on_file_selected)
    
def on_file_selected(self, dialog, result):
    try:
        file = dialog.open_finish(result)
        if file:
            path = file.get_path()
            
            # Dosya uzantısını kontrol et
            if not path.lower().endswith('.apk'):
                toast = Adw.Toast.new("Selected file is not an APK!")
                toast.set_timeout(3)
                self.toast_overlay.add_toast(toast)
                return
            
            # Tek APK'yı bir liste olarak ayarla
            self.apk_files = [path]
            
            # Çevre değişkenlerini oku ve ayarla
            self.parse_env_variables()

            # Test görünümünü göster, karşılama görünümünü gizle
            self.welcome_view.set_visible(False)
            self.testing_view.set_visible(True)

            # Durumu güncelle
            self.apk_value_label.set_text(os.path.basename(path))
            self.status_value_label.set_text("Ready")
            self.status_icon.set_from_icon_name("media-playback-pause-symbolic")
            self.command_value_label.set_text("-")

            # Teste başla
            self.test_next_apk()
    except Exception as e:
        print(f"Error selecting file: {e}")
        toast = Adw.Toast.new(f"Could not select file: {str(e)}")
        self.toast_overlay.add_toast(toast)
        
def on_folder_clicked(self, button):
    # Skip dialog in debug mode
    if os.environ.get('ATL_DEBUG_MODE'):
        print("Debug mode: Skipping folder dialog")
        return
        
    file_dialog = Gtk.FileDialog()
    file_dialog.set_title("Select Folder with APK Files")
    
    # Use the correct method for GTK4 - in GTK4, we need to use Gtk.FileDialog
    try:
        print("Opening folder dialog...")
        # This is the correct method for GTK4
        file_dialog.select_folder(self, None, lambda dialog, result: self.on_folder_selected(dialog, result))
    except Exception as e:
        print(f"Error showing folder dialog: {e}")
        toast = Adw.Toast.new(f"Could not open folder dialog: {str(e)}")
        self.toast_overlay.add_toast(toast)

def on_folder_selected(self, dialog, result):
    try:
        print("Folder dialog callback received")
        # This is the correct method for GTK4
        folder = dialog.select_folder_finish(result)
        if folder:
            print(f"Folder selected: {folder.get_path()}")
            path = folder.get_path()
            self.find_apk_files(path)
            
            # Environment variables
            self.parse_env_variables()

            if self.apk_files:
                # Show test view, hide welcome view
                self.welcome_view.set_visible(False)
                self.testing_view.set_visible(True)

                # Update status
                self.apk_value_label.set_text(os.path.basename(self.apk_files[0]))
                self.status_value_label.set_text("Ready")
                self.status_icon.set_from_icon_name("media-playback-pause-symbolic")
                self.command_value_label.set_text("-")

                # Start testing
                self.test_next_apk()
            else:
                # Show toast if no APKs found
                toast = Adw.Toast.new("No APK files found in the selected folder!")
                toast.set_timeout(3)
                self.toast_overlay.add_toast(toast)
    except Exception as e:
        print(f"Error selecting folder: {e}")
        toast = Adw.Toast.new(f"Could not select folder: {str(e)}")
        self.toast_overlay.add_toast(toast)
        
def parse_env_variables(self):
    buffer = self.env_text_view.get_buffer()
    start_iter = buffer.get_start_iter()
    end_iter = buffer.get_end_iter()
    env_text = buffer.get_text(start_iter, end_iter, True)
    
    # Reset environment variables
    self.env_variables = {}
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
        self.env_variables[key] = value
        
    # If there are invalid lines, notify the user
    if invalid_lines:
        self.show_error_dialog(
            "Invalid Environment Variables",
            "The following lines are not in KEY=VALUE format and will be skipped:",
            "\n".join(invalid_lines)
        )
        
def show_error_dialog(self, title, message, details=None):
    dialog = Adw.AlertDialog()
    dialog.set_title(title)
    dialog.set_body(message)
    
    if details:
        dialog.set_body(f"{message}\n\n{details}")
    
    dialog.add_response("ok", "OK")
    dialog.set_default_response("ok")
    dialog.set_close_response("ok")
    
    dialog.present()

def find_apk_files(self, folder):
    self.apk_files = []
    try:
        for file in os.listdir(folder):
            if file.lower().endswith('.apk'):
                self.apk_files.append(os.path.join(folder, file))
        self.current_apk_index = 0
    except Exception as e:
        print(f"Error listing directory: {e}")
        toast = Adw.Toast.new(f"Could not read folder: {str(e)}")
        self.toast_overlay.add_toast(toast) 