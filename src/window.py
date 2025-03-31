import gi
import os
import subprocess
import signal
from pathlib import Path
import datetime
import shlex

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk, GLib, Pango

from src.views.welcome_view import create_welcome_view
from src.views.testing_view import create_testing_view
from src.views.results_view import create_results_view
from src.utils.css_provider import setup_css

class AtlGUIWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.set_default_size(1000, 700)
        self.set_title("Android Translation Layer")
        
        # Logo dosyasının tam yolunu kaydet
        self.logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "res", "android_translation_layer.svg")

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
    
    from src.handlers.settings_handlers import (
        on_settings_clicked, on_browse_script_clicked, on_script_selected,
        show_script_error, show_test_settings_dialog, on_settings_response,
        on_script_validation_response, on_sudo_warning_response
    )
    
    from src.handlers.results_handlers import (
        show_test_results, on_new_test_clicked, on_export_clicked,
        on_export_dialog_response, export_results_to_file
    ) 