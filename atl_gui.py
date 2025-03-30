#!/usr/bin/env python3
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

class AtlGUIWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.set_default_size(1000, 700)
        self.set_title("Android Translation Layer")
        
        # Logo dosyasının tam yolunu kaydet
        self.logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "res", "android_translation_layer.svg")

        # CSS Sağlayıcı ayarla - kenarları kaldırmak için
        css_provider = Gtk.CssProvider()
        css_data = """
            box {
                border: none;
            }
            box.card {
                padding: 12px;
                border-radius: 8px;
                background-color: @card_bg_color;
                border: none;
                box-shadow: 0 1px 2px rgba(0,0,0,0.08);
            }
            label {
                margin: 4px;
            }
            .content-padding {
                padding: 16px;
                margin: 8px;
            }
            .success {
                color: #2ec27e;
            }
            .error {
                color: #e01b24;
            }
            preferencesgroup {
                border: none;
                box-shadow: none;
            }
            preferencesgroup.card > box {
                padding: 8px;
                border-radius: 8px;
                background-color: @card_bg_color;
                border: none;
                box-shadow: 0 1px 2px rgba(0,0,0,0.08);
            }
            scrolledwindow.card {
                padding: 0;
                background-color: @card_bg_color;
                border: none;
                border-radius: 8px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.08);
            }
        """
        css_provider.load_from_data(css_data.encode('utf-8'))
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), 
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

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
        self.welcome_view = self.create_welcome_view()
        content_box.append(self.welcome_view)

        # Testing view - shown after selecting a folder
        self.testing_view = self.create_testing_view()
        self.testing_view.set_visible(False)
        content_box.append(self.testing_view)

        # Results view - shown after tests are completed
        self.results_view = self.create_results_view()
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

    def create_welcome_view(self):
        # Main container (centers content based on window size)
        welcome_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        welcome_container.set_vexpand(True)
        welcome_container.set_valign(Gtk.Align.FILL)
        
        # Add flexible spacing to center contents
        top_spacer = Gtk.Box()
        top_spacer.set_vexpand(True)
        welcome_container.append(top_spacer)
        
        # Main content box (centered)
        welcome_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=32)
        welcome_box.set_valign(Gtk.Align.CENTER)
        welcome_box.set_halign(Gtk.Align.CENTER)
        welcome_container.append(welcome_box)

        # Application icon - Use SVG logo
        logo = None
        
        # Logo file exists check
        if os.path.exists(self.logo_path) and os.path.isfile(self.logo_path):
            try:
                # Show SVG using Gtk.Image - more reliable method
                logo = Gtk.Image()
                logo.set_from_file(self.logo_path)
                logo.set_pixel_size(128)
            except Exception as e:
                print(f"Logo loading error: {e}")
                # Use default icon in case of error
                logo = Gtk.Image()
                logo.set_from_icon_name("application-x-executable")
                logo.set_pixel_size(128)
        else:
            # Use default icon if file doesn't exist
            print(f"Logo file not found: {self.logo_path}")
            logo = Gtk.Image()
            logo.set_from_icon_name("application-x-executable")
            logo.set_pixel_size(128)
            
        welcome_box.append(logo)

        # Welcome title
        title = Gtk.Label(label="Android Translation Layer")
        title.add_css_class("title-1")
        welcome_box.append(title)

        # Welcome description
        description = Gtk.Label(
            label="ATL user interface for running Android applications on Linux.\n"
                  "To get started, select a single APK file or test all APKs in a folder."
        )
        description.set_justify(Gtk.Justification.CENTER)
        description.add_css_class("body")
        welcome_box.append(description)
        
        # Environment variables card
        env_card = Adw.PreferencesGroup()
        env_card.set_title("Default Environment Variables")
        env_card.set_description("Specify environment variables to be used by Android-translation-layer")
        env_card.add_css_class("card")
        env_card.set_margin_top(16)
        env_card.set_margin_bottom(16)
        
        # Entry area for environment variables
        env_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        env_box.set_margin_top(8)
        env_box.set_margin_bottom(8)
        env_box.set_margin_start(8)
        env_box.set_margin_end(8)
        
        # Description label
        env_label = Gtk.Label(label="Enter one KEY=VALUE per line")
        env_label.set_halign(Gtk.Align.START)
        env_label.add_css_class("caption")
        env_box.append(env_label)
        
        # Text box for environment variables
        self.env_text_view = Gtk.TextView()
        self.env_text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.env_text_view.set_top_margin(8)
        self.env_text_view.set_bottom_margin(8)
        self.env_text_view.set_left_margin(8)
        self.env_text_view.set_right_margin(8)
        self.env_text_view.set_monospace(True)
        
        # Set example values
        example_env = "SCALE=2\nLOG_LEVEL=debug"
        self.env_text_view.get_buffer().set_text(example_env)
        
        # Scrolled area for text box
        env_scroll = Gtk.ScrolledWindow()
        env_scroll.set_min_content_height(100)
        env_scroll.set_vexpand(False)
        env_scroll.set_child(self.env_text_view)
        env_scroll.add_css_class("card")
        
        env_box.append(env_scroll)
        env_card.add(env_box)
        welcome_box.append(env_card)

        # Butonlar için yatay düzen
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_top(8)

        # Tek APK dosya seçim butonu
        select_file_button = Gtk.Button()
        select_file_button.add_css_class("pill")
        select_file_button.add_css_class("suggested-action")

        file_button_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        file_button_content.set_margin_start(12)
        file_button_content.set_margin_end(12)
        file_button_content.set_margin_top(8)
        file_button_content.set_margin_bottom(8)

        file_icon = Gtk.Image.new_from_icon_name("document-open-symbolic")
        file_button_content.append(file_icon)

        file_label = Gtk.Label(label="Select APK File")
        file_button_content.append(file_label)

        select_file_button.set_child(file_button_content)
        select_file_button.connect("clicked", self.on_file_clicked)
        button_box.append(select_file_button)

        # Klasör seçme butonu
        select_folder_button = Gtk.Button()
        select_folder_button.add_css_class("pill")

        folder_button_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        folder_button_content.set_margin_start(12)
        folder_button_content.set_margin_end(12)
        folder_button_content.set_margin_top(8)
        folder_button_content.set_margin_bottom(8)

        folder_icon = Gtk.Image.new_from_icon_name("folder-open-symbolic")
        folder_button_content.append(folder_icon)

        folder_label = Gtk.Label(label="Select APK Folder")
        folder_button_content.append(folder_label)

        select_folder_button.set_child(folder_button_content)
        select_folder_button.connect("clicked", self.on_folder_clicked)

        button_box.append(select_folder_button)
        welcome_box.append(button_box)
        
        # Alt kısım için esnek alan ekle
        bottom_spacer = Gtk.Box()
        bottom_spacer.set_vexpand(True)
        welcome_container.append(bottom_spacer)

        return welcome_container
        
    def on_file_clicked(self, button):
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
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Select APK Folder")
        
        # Open folder selection dialog directly
        file_dialog.select_folder(self, None, self.on_folder_selected)

    def create_testing_view(self):
        testing_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)

        # Durum kartı
        status_card = Adw.PreferencesGroup()
        status_card.set_margin_top(8)
        status_card.set_margin_start(8)
        status_card.set_margin_end(8)
        testing_box.append(status_card)
        
        # Durum bilgisi
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        status_box.add_css_class("card")
        status_box.set_margin_top(2)
        status_box.set_margin_bottom(2)
        status_box.set_margin_start(2)
        status_box.set_margin_end(2)
        
        status_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        status_row.set_margin_start(2)
        status_row.set_margin_end(2)
        status_row.set_margin_top(2)
        status_row.set_margin_bottom(2)
        
        # APK bilgisi
        apk_label = Gtk.Label(label="APK:")
        apk_label.add_css_class("heading")
        apk_label.set_xalign(0)
        status_row.append(apk_label)
        
        self.apk_value_label = Gtk.Label(label="Not selected yet")
        self.apk_value_label.set_hexpand(True)
        self.apk_value_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self.apk_value_label.set_wrap(True)
        self.apk_value_label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.apk_value_label.set_max_width_chars(40)
        self.apk_value_label.set_lines(2)
        self.apk_value_label.set_xalign(0)
        status_row.append(self.apk_value_label)
        
        # Durum bilgisi
        status_label = Gtk.Label(label="Status:")
        status_label.add_css_class("heading")
        status_label.set_xalign(0)
        status_label.set_margin_start(4)
        status_row.append(status_label)
        
        # Durum değeri ve ikonu için kutu
        status_value_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        
        self.status_value_label = Gtk.Label(label="Waiting")
        self.status_value_label.set_xalign(0)
        status_value_box.append(self.status_value_label)
        
        self.status_icon = Gtk.Image.new_from_icon_name("content-loading-symbolic")
        status_value_box.append(self.status_icon)
        
        status_row.append(status_value_box)
        status_box.append(status_row)
        
        # Komut bilgisi
        command_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        command_row.set_margin_start(2)
        command_row.set_margin_end(2)
        command_row.set_margin_bottom(2)
        
        command_label = Gtk.Label(label="Command:")
        command_label.add_css_class("heading")
        command_label.set_xalign(0)
        command_row.append(command_label)
        
        self.command_value_label = Gtk.Label(label="-")
        self.command_value_label.set_hexpand(True)
        self.command_value_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.command_value_label.set_xalign(0)
        command_row.append(self.command_value_label)
        
        status_box.append(command_row)
        status_card.add(status_box)
        
        # Test alanı - bölünmüş görünüm
        split_view = Adw.Clamp()
        split_view.set_maximum_size(1200)
        split_view.set_margin_top(4)
        split_view.set_vexpand(True)
        testing_box.append(split_view)
        
        split_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        split_view.set_child(split_box)
        
        # Terminal card
        terminal_card = Adw.PreferencesGroup()
        terminal_card.set_title("Terminal Output")
        terminal_card.set_hexpand(True)
        terminal_card.set_margin_start(8)
        split_box.append(terminal_card)
        
        terminal_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        terminal_box.add_css_class("card")
        terminal_box.set_margin_top(2)
        terminal_box.set_margin_bottom(2)
        terminal_box.set_margin_start(2)
        terminal_box.set_margin_end(2)
        terminal_box.set_vexpand(True)
        terminal_box.set_hexpand(True)
        
        self.terminal_output = Gtk.TextView()
        self.terminal_output.set_editable(False)
        self.terminal_output.set_cursor_visible(False)
        self.terminal_output.set_vexpand(True)
        self.terminal_output.set_hexpand(True)
        self.terminal_output.add_css_class("monospace")
        
        # Terminal çıktısı için CSS ayarları
        css_provider = Gtk.CssProvider()
        css_data = """
            textview.monospace {
                background-color: #2d2d2d;
                color: #f0f0f0;
                padding: 8px;
                border-radius: 4px;
                font-family: monospace;
                font-size: 13px;
                min-height: 450px;
                border: none;
            }
            textview.monospace text {
                background-color: #2d2d2d;
                color: #f0f0f0;
            }
        """
        css_provider.load_from_data(css_data.encode('utf-8'))
        style_context = self.terminal_output.get_style_context()
        style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        terminal_scroll = Gtk.ScrolledWindow()
        terminal_scroll.set_vexpand(True)
        terminal_scroll.set_hexpand(True)
        terminal_scroll.set_min_content_height(450)
        terminal_scroll.set_min_content_width(650)
        terminal_scroll.set_size_request(650, 450)
        terminal_scroll.set_child(self.terminal_output)
        terminal_box.append(terminal_scroll)
        
        terminal_card.add(terminal_box)
        
        # Kontrol paneli (sağ taraf)
        test_card = Adw.PreferencesGroup()
        test_card.set_title("Application Control")
        test_card.set_margin_end(8)
        test_card.set_hexpand(False)
        test_card.set_size_request(300, -1)
        split_box.append(test_card)
        
        test_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        test_box.add_css_class("card")
        test_box.set_margin_top(2)
        test_box.set_margin_bottom(2)
        test_box.set_margin_start(2)
        test_box.set_margin_end(2)
        test_box.set_vexpand(True)
        test_box.set_valign(Gtk.Align.FILL)
        
        # APK bilgisi
        apk_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        apk_box.set_margin_top(8)
        apk_box.set_margin_bottom(8)
        apk_box.set_margin_start(8)
        apk_box.set_margin_end(8)
        
        apk_label = Gtk.Label(label="Selected Application:")
        apk_label.set_halign(Gtk.Align.START)
        apk_label.add_css_class("heading")
        apk_box.append(apk_label)
        
        self.apk_name_label = Gtk.Label(label="")
        self.apk_name_label.set_halign(Gtk.Align.START)
        self.apk_name_label.set_wrap(True)
        self.apk_name_label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.apk_name_label.set_lines(3)
        self.apk_name_label.set_max_width_chars(30)
        self.apk_name_label.add_css_class("title-4")
        apk_box.append(self.apk_name_label)
        
        self.test_question_label = Gtk.Label(label="Is this application working?")
        self.test_question_label.set_halign(Gtk.Align.START)
        self.test_question_label.set_margin_top(4)
        self.test_question_label.add_css_class("body")
        self.test_question_label.set_visible(False)
        apk_box.append(self.test_question_label)
        
        test_box.append(apk_box)
        
        # Kontrol butonları
        buttons_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        buttons_container.set_margin_start(8)
        buttons_container.set_margin_end(8)
        
        # Başlat/Ayarlar butonları
        start_settings_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        start_settings_box.set_halign(Gtk.Align.CENTER)
        
        self.start_test_button = Gtk.Button(label="Start Application")
        self.start_test_button.add_css_class("suggested-action")
        self.start_test_button.add_css_class("pill")
        self.start_test_button.connect("clicked", self.on_start_test_clicked)
        start_settings_box.append(self.start_test_button)
        
        self.settings_button = Gtk.Button(label="Options")
        self.settings_button.add_css_class("pill")
        self.settings_button.connect("clicked", self.on_settings_clicked)
        start_settings_box.append(self.settings_button)
        
        buttons_container.append(start_settings_box)
        
        # Çalışıyor/Çalışmıyor butonları
        self.test_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.test_button_box.set_halign(Gtk.Align.CENTER)
        self.test_button_box.set_visible(False)
        
        self.working_button = Gtk.Button(label="Working")
        self.working_button.add_css_class("suggested-action")
        self.working_button.add_css_class("pill")
        self.working_button.connect("clicked", self.on_working_clicked)
        self.test_button_box.append(self.working_button)
        
        self.not_working_button = Gtk.Button(label="Not Working")
        self.not_working_button.add_css_class("destructive-action")
        self.not_working_button.add_css_class("pill")
        self.not_working_button.connect("clicked", self.on_not_working_clicked)
        self.test_button_box.append(self.not_working_button)
        
        buttons_container.append(self.test_button_box)
        
        # Other control buttons
        control_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        control_button_box.set_halign(Gtk.Align.CENTER)
        control_button_box.set_margin_top(4)
        
        skip_button = Gtk.Button(label="Skip")
        skip_button.add_css_class("pill")
        skip_button.connect("clicked", self.on_skip_clicked)
        control_button_box.append(skip_button)
        
        finish_all_button = Gtk.Button(label="Finish All")
        finish_all_button.add_css_class("pill")
        finish_all_button.connect("clicked", self.on_finish_all_clicked)
        control_button_box.append(finish_all_button)
        
        buttons_container.append(control_button_box)
        test_box.append(buttons_container)
        
        # Progress information
        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        progress_box.set_margin_top(8)
        progress_box.set_margin_bottom(8)
        progress_box.set_margin_start(8)
        progress_box.set_margin_end(8)
        
        self.progress_label = Gtk.Label(label="Progress: 0/0")
        self.progress_label.set_halign(Gtk.Align.CENTER)
        self.progress_label.add_css_class("caption")
        progress_box.append(self.progress_label)
        
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_fraction(0)
        progress_box.append(self.progress_bar)
        
        test_box.append(progress_box)
        test_card.add(test_box)
        
        return testing_box

    def create_results_view(self):
        results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        
        # Başlık
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        title_box.set_margin_bottom(16)
        
        title = Gtk.Label(label="Application Results")
        title.add_css_class("title-1")
        title.set_halign(Gtk.Align.CENTER)
        title_box.append(title)
        
        subtitle = Gtk.Label(label="All applications have been run")
        subtitle.add_css_class("subtitle-1")
        subtitle.set_halign(Gtk.Align.CENTER)
        title_box.append(subtitle)
        
        results_box.append(title_box)
        
        # Sonuç listesi için kaydırılabilir alan
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_hexpand(True)
        scrolled_window.set_min_content_height(350)  # Daha makul bir yükseklik
        scrolled_window.set_max_content_height(350)  # Maksimum yükseklik sınırı
        
        # Sonuç listesi
        self.results_list_box = Gtk.ListBox()
        self.results_list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.results_list_box.add_css_class("boxed-list")
        scrolled_window.set_child(self.results_list_box)
        
        results_box.append(scrolled_window)
        
        # Özet bilgisi
        self.summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.summary_box.set_margin_top(16)
        self.summary_box.set_halign(Gtk.Align.CENTER)
        
        self.summary_label = Gtk.Label()
        self.summary_label.add_css_class("heading")
        self.summary_box.append(self.summary_label)
        
        results_box.append(self.summary_box)
        
        # Butonlar kutusu
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        button_box.set_margin_top(16)
        button_box.set_halign(Gtk.Align.CENTER)
        
        # Yeni test butonu
        new_test_button = Gtk.Button(label="New Application Test")
        new_test_button.add_css_class("suggested-action")
        new_test_button.add_css_class("pill")
        new_test_button.connect("clicked", self.on_new_test_clicked)
        button_box.append(new_test_button)
        
        # Dışa aktar butonu
        export_button = Gtk.Button(label="Export Results")
        export_button.add_css_class("pill")
        export_button.connect("clicked", self.on_export_clicked)
        button_box.append(export_button)
        
        results_box.append(button_box)
        
        return results_box
    
    def show_test_results(self):
        # Görünümleri değiştir
        self.welcome_view.set_visible(False)
        self.testing_view.set_visible(False)
        self.results_view.set_visible(True)
        
        # Önceki sonuçları temizle - GTK4 uyumlu şekilde
        while True:
            row = self.results_list_box.get_first_child()
            if row is None:
                break
            self.results_list_box.remove(row)
        
        # Özet için sayaçlar
        working_count = 0
        not_working_count = 0
        skipped_count = 0
        
        # Her APK için sonuçları ekle
        for apk_path, result in self.test_results.items():
            apk_name = os.path.basename(apk_path)
            
            # Expandable row için bir container oluştur
            expander = Adw.ExpanderRow()
            expander.set_title(apk_name)
            
            # İkon ekle
            if result == "working":
                icon = Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
                icon.add_css_class("success")
                expander.add_prefix(icon)
                expander.add_css_class("success")
                expander.set_subtitle("Working")
                working_count += 1
            elif result == "not_working":
                icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic")
                icon.add_css_class("error")
                expander.add_prefix(icon)
                expander.add_css_class("error")
                expander.set_subtitle("Not Working")
                not_working_count += 1
            else:  # skipped
                icon = Gtk.Image.new_from_icon_name("action-unavailable-symbolic")
                expander.add_prefix(icon)
                expander.add_css_class("dim-label")
                expander.set_subtitle("Skipped")
                skipped_count += 1
                
            # Terminal loglarını ekle - terminal_logs olup olmadığını kontrol et
            if hasattr(self, 'terminal_logs') and apk_path in self.terminal_logs:
                # Terminal logu varsa, bir metin görünümü içinde göster
                log_view = Gtk.TextView()
                log_view.set_editable(False)
                log_view.set_cursor_visible(False)
                log_view.add_css_class("log-view")
                log_view.get_buffer().set_text(self.terminal_logs[apk_path])
                
                # Loglar için CSS - ince border
                css_provider = Gtk.CssProvider()
                css_data = """
                    textview.log-view {
                        background-color: #f8f8f8;
                        color: #202020;
                        padding: 4px;
                        border-radius: 3px;
                        font-family: monospace;
                        font-size: 12px;
                        margin: 4px;
                        border: 0.25px solid #e8e8e8;
                    }
                    textview.log-view text {
                        background-color: #f8f8f8;
                        color: #202020;
                    }
                """
                css_provider.load_from_data(css_data.encode('utf-8'))
                style_context = log_view.get_style_context()
                style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
                
                # Kaydırılabilir alan içine yerleştir
                log_scroll = Gtk.ScrolledWindow()
                log_scroll.set_min_content_height(150)
                log_scroll.set_vexpand(True)
                log_scroll.set_child(log_view)
                
                # İlk önce row'a prefixleri ekle, sonra log_box'ı
                log_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                log_box.set_margin_start(8)
                log_box.set_margin_end(8)
                log_box.set_margin_bottom(8)
                log_box.append(log_scroll)
                
                # İlk önce row'a prefixleri ekle, sonra log_box'ı
                expander.add_row(log_box)
            else:
                # Log yoksa bir mesaj göster
                no_log_label = Gtk.Label(label="No terminal output recorded for this application.")
                no_log_label.set_margin_start(16)
                no_log_label.set_margin_top(8)
                no_log_label.set_margin_bottom(8)
                no_log_label.set_xalign(0)  # Left align
                
                expander.add_row(no_log_label)
            
            self.results_list_box.append(expander)
        
        # Özet bilgisini güncelle
        total = working_count + not_working_count + skipped_count
        self.summary_label.set_text(f"Total: {total} APKs | Working: {working_count} | Not Working: {not_working_count} | Skipped: {skipped_count}")
    
    def on_new_test_clicked(self, button):
        # Yeni bir test için başlangıç sayfasına dön
        self.welcome_view.set_visible(True)
        self.results_view.set_visible(False)
        self.testing_view.set_visible(False)
        
        # Değişkenleri sıfırla
        self.current_apk_index = 0
        self.apk_files = []
        self.test_results = {}

    def on_folder_selected(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                path = folder.get_path()
                self.find_apk_files(path)
                
                # Çevre değişkenlerini oku ve ayarla
                self.parse_env_variables()

                if self.apk_files:
                    # Test görünümünü göster, karşılama görünümünü gizle
                    self.welcome_view.set_visible(False)
                    self.testing_view.set_visible(True)

                    # Durumu güncelle
                    self.apk_value_label.set_text(os.path.basename(self.apk_files[0]))
                    self.status_value_label.set_text("Ready")
                    self.status_icon.set_from_icon_name("media-playback-pause-symbolic")
                    self.command_value_label.set_text("-")

                    # Teste başla
                    self.test_next_apk()
                else:
                    # APK bulunamadı toast'u göster
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
        
        dialog.present(self)

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

    def on_settings_clicked(self, button):
        # Mevcut APK için ek seçenekler menüsünü tekrar aç
        if self.current_apk_index < len(self.apk_files):
            apk_path = self.apk_files[self.current_apk_index]
            apk_name = os.path.basename(apk_path)
            self.show_test_settings_dialog(apk_name)

    def on_export_clicked(self, button):
        # Dosya kaydetme diyaloğu
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Save Results")
        file_dialog.set_initial_name("android_translation_layer_results.txt")
        
        # Filtre ekle
        text_filter = Gtk.FileFilter()
        text_filter.set_name("Text Files")
        text_filter.add_mime_type("text/plain")
        
        # Diyaloğu göster
        file_dialog.save(self, None, self.on_export_dialog_response)
    
    def on_export_dialog_response(self, dialog, result):
        try:
            file = dialog.save_finish(result)
            if file:
                path = file.get_path()
                self.export_results_to_file(path)
                
                # Başarı bildirimi
                toast = Adw.Toast.new(f"Results exported to: {path}")
                toast.set_timeout(5)
                self.toast_overlay.add_toast(toast)
        except Exception as e:
            # Hata bildirimi
            print(f"Error saving file: {e}")
            toast = Adw.Toast.new(f"Could not export results: {str(e)}")
            self.toast_overlay.add_toast(toast)
    
    def export_results_to_file(self, file_path):
        # Çalışma zamanı bilgisi
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Özet sayıları hesapla
        working_count = sum(1 for result in self.test_results.values() if result == "working")
        not_working_count = sum(1 for result in self.test_results.values() if result == "not_working")
        skipped_count = sum(1 for result in self.test_results.values() if result == "skipped")
        total = len(self.test_results)
        
        with open(file_path, 'w') as f:
            # Başlık ve tarih
            f.write("===== ANDROID TRANSLATION LAYER - APPLICATION RESULTS =====\n")
            f.write(f"Date: {date_str}\n\n")
            
            # Özet
            f.write("===== SUMMARY =====\n")
            f.write(f"Total Applications: {total}\n")
            f.write(f"Working: {working_count}\n")
            f.write(f"Not Working: {not_working_count}\n")
            f.write(f"Skipped: {skipped_count}\n\n")
            
            # Detaylı sonuçlar
            f.write("===== DETAILED RESULTS =====\n")
            
            for apk_path, result in self.test_results.items():
                apk_name = os.path.basename(apk_path)
                result_text = "Working" if result == "working" else "Not Working" if result == "not_working" else "Skipped"
                f.write(f"{apk_name}: {result_text}\n")

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

    def show_test_buttons(self):
        # Show test question and buttons
        self.test_question_label.set_visible(True)
        self.test_button_box.set_visible(True)
        self.start_test_button.set_visible(False)
        self.settings_button.set_visible(False)
        self.current_apk_ready = True
        return False  # Don't repeat the timeout

class AtlGUIApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='org.example.atlgui')

    def do_activate(self):
        win = AtlGUIWindow(application=self)
        win.present()

def main():
    app = AtlGUIApp()
    return app.run(None)

if __name__ == '__main__':
    main()
