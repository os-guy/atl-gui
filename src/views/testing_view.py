import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Pango, GLib, Gdk
from src.utils.css_provider import load_css_data

def create_testing_view(window):
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
    
    window.apk_value_label = Gtk.Label(label="Not selected yet")
    window.apk_value_label.set_hexpand(True)
    window.apk_value_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
    window.apk_value_label.set_wrap(True)
    window.apk_value_label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
    window.apk_value_label.set_max_width_chars(40)
    window.apk_value_label.set_lines(2)
    window.apk_value_label.set_xalign(0)
    status_row.append(window.apk_value_label)
    
    # Durum bilgisi
    status_label = Gtk.Label(label="Status:")
    status_label.add_css_class("heading")
    status_label.set_xalign(0)
    status_label.set_margin_start(4)
    status_row.append(status_label)
    
    # Durum değeri ve ikonu için kutu
    status_value_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    
    window.status_value_label = Gtk.Label(label="Waiting")
    window.status_value_label.set_xalign(0)
    status_value_box.append(window.status_value_label)
    
    window.status_icon = Gtk.Image.new_from_icon_name("content-loading-symbolic")
    status_value_box.append(window.status_icon)
    
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
    
    window.command_value_label = Gtk.Label(label="-")
    window.command_value_label.set_hexpand(True)
    window.command_value_label.set_ellipsize(Pango.EllipsizeMode.END)
    window.command_value_label.set_xalign(0)
    command_row.append(window.command_value_label)
    
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
    
    window.terminal_output = Gtk.TextView()
    window.terminal_output.set_editable(False)
    window.terminal_output.set_cursor_visible(False)
    window.terminal_output.set_vexpand(True)
    window.terminal_output.set_hexpand(True)
    window.terminal_output.add_css_class("monospace")
    
    # Terminal çıktısı için CSS ayarları
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
    # Create CSS provider
    css_provider = Gtk.CssProvider()
    
    # Load CSS data using the utility function
    load_css_data(css_provider, css_data, "terminal CSS")
    
    style_context = window.terminal_output.get_style_context()
    style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    
    terminal_scroll = Gtk.ScrolledWindow()
    terminal_scroll.set_vexpand(True)
    terminal_scroll.set_hexpand(True)
    terminal_scroll.set_min_content_height(450)
    terminal_scroll.set_min_content_width(650)
    terminal_scroll.set_size_request(650, 450)
    terminal_scroll.set_child(window.terminal_output)
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
    
    window.apk_name_label = Gtk.Label(label="")
    window.apk_name_label.set_halign(Gtk.Align.START)
    window.apk_name_label.set_wrap(True)
    window.apk_name_label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
    window.apk_name_label.set_lines(3)
    window.apk_name_label.set_max_width_chars(30)
    window.apk_name_label.add_css_class("title-4")
    apk_box.append(window.apk_name_label)
    
    window.test_question_label = Gtk.Label(label="Is this application working?")
    window.test_question_label.set_halign(Gtk.Align.START)
    window.test_question_label.set_margin_top(4)
    window.test_question_label.add_css_class("body")
    window.test_question_label.set_visible(False)
    apk_box.append(window.test_question_label)
    
    test_box.append(apk_box)
    
    # Kontrol butonları
    buttons_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    buttons_container.set_margin_start(8)
    buttons_container.set_margin_end(8)
    
    # Başlat/Ayarlar butonları
    start_settings_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    start_settings_box.set_halign(Gtk.Align.CENTER)
    
    window.start_test_button = Gtk.Button(label="Start Application")
    window.start_test_button.add_css_class("suggested-action")
    window.start_test_button.add_css_class("pill")
    window.start_test_button.connect("clicked", window.on_start_test_clicked)
    start_settings_box.append(window.start_test_button)
    
    window.settings_button = Gtk.Button(label="Options")
    window.settings_button.add_css_class("pill")
    window.settings_button.connect("clicked", window.on_settings_clicked)
    start_settings_box.append(window.settings_button)
    
    buttons_container.append(start_settings_box)
    
    # Çalışıyor/Çalışmıyor butonları
    window.test_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    window.test_button_box.set_halign(Gtk.Align.CENTER)
    window.test_button_box.set_visible(False)
    
    window.working_button = Gtk.Button(label="Working")
    window.working_button.add_css_class("suggested-action")
    window.working_button.add_css_class("pill")
    window.working_button.connect("clicked", window.on_working_clicked)
    window.test_button_box.append(window.working_button)
    
    window.not_working_button = Gtk.Button(label="Not Working")
    window.not_working_button.add_css_class("destructive-action")
    window.not_working_button.add_css_class("pill")
    window.not_working_button.connect("clicked", window.on_not_working_clicked)
    window.test_button_box.append(window.not_working_button)
    
    buttons_container.append(window.test_button_box)
    
    # Other control buttons
    control_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    control_button_box.set_halign(Gtk.Align.CENTER)
    control_button_box.set_margin_top(4)
    
    skip_button = Gtk.Button(label="Skip")
    skip_button.add_css_class("pill")
    skip_button.connect("clicked", window.on_skip_clicked)
    control_button_box.append(skip_button)
    
    finish_all_button = Gtk.Button(label="Finish All")
    finish_all_button.add_css_class("pill")
    finish_all_button.connect("clicked", window.on_finish_all_clicked)
    control_button_box.append(finish_all_button)
    
    buttons_container.append(control_button_box)
    test_box.append(buttons_container)
    
    # Progress information
    progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    progress_box.set_margin_top(8)
    progress_box.set_margin_bottom(8)
    progress_box.set_margin_start(8)
    progress_box.set_margin_end(8)
    
    window.progress_label = Gtk.Label(label="Progress: 0/0")
    window.progress_label.set_halign(Gtk.Align.CENTER)
    window.progress_label.add_css_class("caption")
    progress_box.append(window.progress_label)
    
    window.progress_bar = Gtk.ProgressBar()
    window.progress_bar.set_fraction(0)
    progress_box.append(window.progress_bar)
    
    test_box.append(progress_box)
    test_card.add(test_box)
    
    return testing_box 