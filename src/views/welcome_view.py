import gi
import os
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

def create_welcome_view(window):
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
    if os.path.exists(window.logo_path) and os.path.isfile(window.logo_path):
        try:
            # Show SVG using Gtk.Image - more reliable method
            logo = Gtk.Image()
            logo.set_from_file(window.logo_path)
            logo.set_pixel_size(128)
        except Exception as e:
            print(f"Logo loading error: {e}")
            # Use default icon in case of error
            logo = Gtk.Image()
            logo.set_from_icon_name("application-x-executable")
            logo.set_pixel_size(128)
    else:
        # Use default icon if file doesn't exist
        print(f"Logo file not found: {window.logo_path}")
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
    window.env_text_view = Gtk.TextView()
    window.env_text_view.set_wrap_mode(Gtk.WrapMode.WORD)
    window.env_text_view.set_top_margin(8)
    window.env_text_view.set_bottom_margin(8)
    window.env_text_view.set_left_margin(8)
    window.env_text_view.set_right_margin(8)
    window.env_text_view.set_monospace(True)
    
    # Set example values
    example_env = "SCALE=2\nLOG_LEVEL=debug"
    window.env_text_view.get_buffer().set_text(example_env)
    
    # Scrolled area for text box
    env_scroll = Gtk.ScrolledWindow()
    env_scroll.set_min_content_height(100)
    env_scroll.set_vexpand(False)
    env_scroll.set_child(window.env_text_view)
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
    select_file_button.connect("clicked", window.on_file_clicked)
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
    select_folder_button.connect("clicked", window.on_folder_clicked)

    button_box.append(select_folder_button)
    welcome_box.append(button_box)
    
    # Alt kısım için esnek alan ekle
    bottom_spacer = Gtk.Box()
    bottom_spacer.set_vexpand(True)
    welcome_container.append(bottom_spacer)

    return welcome_container 