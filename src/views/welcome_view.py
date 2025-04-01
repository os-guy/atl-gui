import gi
import os
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Pango, GLib, Gdk, Gio, GObject
from src.utils.recent_apks import load_recent_apks

def create_welcome_view(window):
    # Main container (centers content based on window size)
    welcome_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    welcome_container.set_vexpand(True)
    welcome_container.set_valign(Gtk.Align.FILL)
    
    # Add flexible spacing to center contents
    top_spacer = Gtk.Box()
    top_spacer.set_vexpand(True)
    welcome_container.append(top_spacer)
    
    # Create a horizontal box to hold the main content and recent APKs side by side
    horizontal_layout = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
    horizontal_layout.set_valign(Gtk.Align.CENTER)
    horizontal_layout.set_halign(Gtk.Align.CENTER)
    welcome_container.append(horizontal_layout)
    
    # Main content box (centered)
    welcome_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
    welcome_box.set_valign(Gtk.Align.CENTER)
    welcome_box.set_halign(Gtk.Align.CENTER)
    horizontal_layout.append(welcome_box)

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
    env_card.set_margin_top(12)
    env_card.set_margin_bottom(12)
    
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
    button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    button_box.set_halign(Gtk.Align.CENTER)
    button_box.set_margin_top(8)

    # Normal buttons for file/folder selection
    select_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
    select_buttons.set_halign(Gtk.Align.CENTER)
    
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
    select_buttons.append(select_file_button)

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

    select_buttons.append(select_folder_button)
    button_box.append(select_buttons)
    
    # Drag & drop area (initially hidden)
    drag_drop_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    drag_drop_area.set_halign(Gtk.Align.CENTER)
    drag_drop_area.add_css_class("drop-area")
    drag_drop_area.set_visible(False)
    
    # Icon for drag and drop
    drop_icon = Gtk.Image.new_from_icon_name("folder-download-symbolic")
    drop_icon.set_pixel_size(48)
    drop_icon.add_css_class("dim-label")
    drag_drop_area.append(drop_icon)
    
    # Label for instructions
    drop_label = Gtk.Label(label="Release to load APK(s)")
    drop_label.add_css_class("title-4")
    drop_label.add_css_class("accent")
    drag_drop_area.append(drop_label)
    
    # Add sub-label for additional info
    drop_sublabel = Gtk.Label(label="Drop single file, folder or multiple APKs")
    drop_sublabel.add_css_class("caption")
    drop_sublabel.add_css_class("dim-label")
    drag_drop_area.append(drop_sublabel)
    
    button_box.append(drag_drop_area)
    welcome_box.append(button_box)
    
    # Store references to button and drop areas for toggling visibility
    window.button_select_area = select_buttons
    window.button_drop_area = drag_drop_area
    
    # Recent APKs section - Now in the right column
    recent_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    recent_box.set_halign(Gtk.Align.START)
    recent_box.set_valign(Gtk.Align.START)
    recent_box.set_size_request(350, -1)  # Fixed width, natural height
    horizontal_layout.append(recent_box)
    
    # Create main preferences group for Recent APKs
    recent_card = Adw.PreferencesGroup()
    recent_card.set_title("Recent APKs")
    recent_card.set_description("Recently tested Android applications")
    recent_card.add_css_class("card")
    recent_box.append(recent_card)
    
    # Create the search container
    search_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    search_container.set_margin_start(8)
    search_container.set_margin_end(8)
    search_container.set_margin_top(8)
    search_container.set_margin_bottom(8)
    search_container.add_css_class("search-container")
    
    # Search entry
    search_entry = Gtk.SearchEntry()
    search_entry.set_hexpand(True)
    search_entry.set_placeholder_text("Search APKs...")
    search_entry.connect("search-changed", lambda entry: filter_recent_apks(window, entry.get_text()))
    window.recent_search_entry = search_entry
    search_container.append(search_entry)
    
    # Search button with keyboard shortcut (Ctrl+F)
    search_button = Gtk.Button()
    search_button.set_icon_name("system-search-symbolic")
    search_button.add_css_class("flat")
    search_button.add_css_class("circular")
    search_button.set_tooltip_text("Search recent APKs (Ctrl+F)")
    search_container.append(search_button)
    
    # Add search container to recent card
    recent_card.add(search_container)
    
    # Set up key event controller for Ctrl+F shortcut
    key_controller = Gtk.EventControllerKey.new()
    welcome_container.add_controller(key_controller)
    key_controller.connect("key-pressed", on_key_pressed, search_button, search_entry)
    
    # Add an additional event controller for drag & drop safety (reset if Escape is pressed)
    drag_safety_controller = Gtk.EventControllerKey.new()
    welcome_container.add_controller(drag_safety_controller)
    drag_safety_controller.connect("key-pressed", on_drag_key_pressed, window)
    
    # Connect search button with search bar
    search_button.connect("clicked", lambda btn: toggle_search_focus(search_entry))
    
    # Create scrollable area for recent APKs
    recent_scroll = Gtk.ScrolledWindow()
    recent_scroll.set_min_content_height(320)
    recent_scroll.set_max_content_height(400)
    recent_scroll.set_propagate_natural_height(True)
    recent_scroll.set_vexpand(True)
    recent_scroll.add_css_class("card")
    
    # Content box for recent APKs
    apks_content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    apks_content_box.set_margin_start(8)
    apks_content_box.set_margin_end(8)
    apks_content_box.set_margin_top(4)
    apks_content_box.set_margin_bottom(4)
    
    # Load recent APKs
    window.recent_apks_list = apks_content_box
    window.all_recent_apks = []  # Store loaded APKs to allow filtering
    update_recent_apks_list(window)
    
    recent_scroll.set_child(apks_content_box)
    recent_card.add(recent_scroll)
    
    # Setup drag and drop for the entire welcome view
    # Primary drop target for files
    drop_target = Gtk.DropTarget.new(Gio.File, Gdk.DragAction.COPY)
    drop_target.set_gtypes([Gio.File])
    drop_target.set_actions(Gdk.DragAction.COPY)
    drop_target.connect("drop", on_drop, window)
    drop_target.connect("enter", on_welcome_drag_enter, window)
    drop_target.connect("leave", on_welcome_drag_leave, window)
    welcome_container.add_controller(drop_target)
    
    # Drop target for file lists (multiple files)
    # Create content formats for array of GFiles
    list_drop_target = Gtk.DropTarget.new(GObject.TYPE_NONE, Gdk.DragAction.COPY)
    list_drop_target.set_gtypes([Gio.File, GObject.TYPE_POINTER])
    list_drop_target.set_actions(Gdk.DragAction.COPY)
    list_drop_target.connect("drop", on_drop_file_list, window)
    list_drop_target.connect("enter", on_welcome_drag_enter, window)
    list_drop_target.connect("leave", on_welcome_drag_leave, window)
    welcome_container.add_controller(list_drop_target)
    
    # Drop target for URI lists (common in many file managers)
    uri_formats = Gdk.ContentFormats.new(["text/uri-list"])
    uri_drop_target = Gtk.DropTarget.new(uri_formats, Gdk.DragAction.COPY)
    uri_drop_target.connect("drop", on_drop_uri_list, window)
    uri_drop_target.connect("enter", on_welcome_drag_enter, window)
    uri_drop_target.connect("leave", on_welcome_drag_leave, window)
    welcome_container.add_controller(uri_drop_target)
    
    # Drop target for text content (path lists)
    text_formats = Gdk.ContentFormats.new(["text/plain", "STRING"])
    text_drop_target = Gtk.DropTarget.new(text_formats, Gdk.DragAction.COPY)
    text_drop_target.connect("drop", on_drop_text, window)
    text_drop_target.connect("enter", on_welcome_drag_enter, window)
    text_drop_target.connect("leave", on_welcome_drag_leave, window)
    welcome_container.add_controller(text_drop_target)
    
    # Drop target with wildcard content type
    # This is important for file managers that don't use standard content types
    wildcard_formats = Gdk.ContentFormats.new_for_gtype(GObject.TYPE_OBJECT)
    wildcard_drop_target = Gtk.DropTarget.new(wildcard_formats, Gdk.DragAction.COPY) 
    wildcard_drop_target.connect("drop", on_drop_wildcard, window)
    wildcard_drop_target.connect("enter", on_welcome_drag_enter, window)
    wildcard_drop_target.connect("leave", on_welcome_drag_leave, window)
    welcome_container.add_controller(wildcard_drop_target)
    
    # Bottom spacer
    bottom_spacer = Gtk.Box()
    bottom_spacer.set_vexpand(True)
    welcome_container.append(bottom_spacer)

    return welcome_container 

def toggle_search_focus(search_entry):
    """Toggle search entry focus and clear text when unfocused"""
    if search_entry.has_focus():
        search_entry.set_text("")
        search_entry.get_root().set_focus(None)
    else:
        search_entry.grab_focus()

def on_key_pressed(controller, keyval, keycode, state, search_button, search_entry):
    """Handle keyboard shortcuts"""
    # Check for Ctrl+F to activate search
    if keyval == Gdk.KEY_f and (state & Gdk.ModifierType.CONTROL_MASK):
        toggle_search_focus(search_entry)
        return True
    # Check for Escape to close search
    elif keyval == Gdk.KEY_Escape and search_entry.has_focus():
        search_entry.set_text("")
        search_entry.get_root().set_focus(None)
        return True
    return False

def update_recent_apks_list(window):
    """Update the list of recent APKs in the welcome view."""
    # Clear existing children
    while window.recent_apks_list.get_first_child():
        window.recent_apks_list.remove(window.recent_apks_list.get_first_child())
        
    # Load recent APKs
    recent_apks = load_recent_apks()
    window.all_recent_apks = recent_apks
    
    if not recent_apks:
        # No recent APKs found
        no_recent_label = Gtk.Label(label="No recent applications")
        no_recent_label.set_halign(Gtk.Align.CENTER)
        no_recent_label.set_margin_top(24)
        no_recent_label.set_margin_bottom(24)
        no_recent_label.add_css_class("dim-label")
        window.recent_apks_list.append(no_recent_label)
        return
    
    # Add each recent APK
    for apk_data in recent_apks:
        apk_row = create_recent_apk_row(window, apk_data)
        window.recent_apks_list.append(apk_row)

def create_recent_apk_row(window, apk_data):
    """Create a row for a recent APK."""
    # Create row
    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    row.set_margin_top(4)
    row.set_margin_bottom(4)
    row.set_margin_start(4)
    row.set_margin_end(4)
    
    # Status icon
    status = apk_data.get('status', 'unknown')
    icon_name = "help-about-symbolic"  # Default for unknown
    css_class = ""
    
    if status == "working":
        icon_name = "emblem-ok-symbolic"
        css_class = "success"
    elif status == "not_working":
        icon_name = "dialog-warning-symbolic"
        css_class = "error"
    elif status == "skipped":
        icon_name = "action-unavailable-symbolic"
    
    status_icon = Gtk.Image.new_from_icon_name(icon_name)
    if css_class:
        status_icon.add_css_class(css_class)
    row.append(status_icon)
    
    # APK info
    info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    info_box.set_hexpand(True)
    
    # APK name
    name_label = Gtk.Label(label=apk_data.get('name', 'Unknown'))
    name_label.add_css_class("heading")
    name_label.set_halign(Gtk.Align.START)
    name_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
    info_box.append(name_label)
    
    # APK path
    path_label = Gtk.Label(label=apk_data.get('path', ''))
    path_label.add_css_class("caption")
    path_label.set_halign(Gtk.Align.START)
    path_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
    info_box.append(path_label)
    
    # Last run time
    last_run = apk_data.get('last_run', '')
    if last_run:
        try:
            # Format the timestamp in a simpler way to avoid errors
            # Just extract date and time from ISO format
            if "T" in last_run:
                date_part, time_part = last_run.split("T", 1)
                if "." in time_part:
                    time_part = time_part.split(".", 1)[0]
                formatted_date = f"{date_part} {time_part}"
                time_label = Gtk.Label(label=f"Last run: {formatted_date}")
                time_label.add_css_class("caption")
                time_label.add_css_class("dim-label")
                time_label.set_halign(Gtk.Align.START)
                info_box.append(time_label)
        except Exception as e:
            print(f"Error formatting timestamp: {e}")
    
    row.append(info_box)
    
    # Run button
    run_button = Gtk.Button()
    run_button.set_icon_name("media-playback-start-symbolic")
    run_button.add_css_class("flat")
    run_button.add_css_class("circular")
    run_button.connect("clicked", lambda btn: on_recent_apk_clicked(window, apk_data))
    row.append(run_button)
    
    # Create a button to wrap the row and make it clickable
    button_row = Gtk.Button()
    button_row.set_child(row)
    button_row.add_css_class("card")
    button_row.connect("clicked", lambda btn: on_recent_apk_clicked(window, apk_data))
    
    return button_row

def on_recent_apk_clicked(window, apk_data):
    """Handle click on a recent APK item."""
    path = apk_data.get('path', '')
    if not path or not os.path.exists(path):
        # Show error toast if file doesn't exist
        toast = Adw.Toast.new(f"File not found: {path}")
        toast.set_timeout(3)
        window.toast_overlay.add_toast(toast)
        return
        
    # Set the APK as the current file
    window.apk_files = [path]
    
    # Parse environment variables
    window.parse_env_variables()
    
    # Show test view, hide welcome view
    window.welcome_view.set_visible(False)
    window.testing_view.set_visible(True)
    
    # Update status
    window.apk_value_label.set_text(os.path.basename(path))
    window.status_value_label.set_text("Ready")
    window.status_icon.set_from_icon_name("media-playback-pause-symbolic")
    window.command_value_label.set_text("-")
    
    # Start testing the APK
    window.test_next_apk()

def filter_recent_apks(window, search_text):
    """Filter recent APKs based on search text."""
    # Clear existing children
    while window.recent_apks_list.get_first_child():
        window.recent_apks_list.remove(window.recent_apks_list.get_first_child())
    
    if not window.all_recent_apks:
        # No APKs to filter
        no_recent_label = Gtk.Label(label="No recent applications")
        no_recent_label.set_halign(Gtk.Align.CENTER)
        no_recent_label.set_margin_top(24)
        no_recent_label.set_margin_bottom(24)
        no_recent_label.add_css_class("dim-label")
        window.recent_apks_list.append(no_recent_label)
        return
    
    # Filter APKs that match the search text
    search_text = search_text.lower()
    filtered_apks = []
    
    for apk_data in window.all_recent_apks:
        apk_name = apk_data.get('name', '').lower()
        apk_path = apk_data.get('path', '').lower()
        
        if search_text in apk_name or search_text in apk_path:
            filtered_apks.append(apk_data)
    
    if not filtered_apks:
        # No matches found
        no_matches_label = Gtk.Label(label=f"No APKs matching '{search_text}'")
        no_matches_label.set_halign(Gtk.Align.CENTER)
        no_matches_label.set_margin_top(24)
        no_matches_label.set_margin_bottom(24)
        no_matches_label.add_css_class("dim-label")
        window.recent_apks_list.append(no_matches_label)
        return
    
    # Add each matching APK
    for apk_data in filtered_apks:
        apk_row = create_recent_apk_row(window, apk_data)
        window.recent_apks_list.append(apk_row)

def on_welcome_drag_enter(drop_target, x, y, window):
    """Hide buttons and show drop area when dragging begins"""
    if not window.button_drop_area.get_visible():
        # Store initial window size
        width, height = window.get_default_size()
        window.original_width = width
        window.original_height = height
        
        # Apply animation class to start transition
        window.button_select_area.add_css_class("fade-out")
        window.button_drop_area.add_css_class("fade-in")
        
        # Schedule the actual visibility change after a short delay for animation
        GLib.timeout_add(100, lambda: toggle_drop_area_visibility(window, True))
    
    return Gdk.DragAction.COPY

def on_welcome_drag_leave(drop_target, window):
    """Show buttons and hide drop area when dragging ends"""
    if window.button_drop_area.get_visible():
        # Apply animation class to start transition
        window.button_select_area.add_css_class("fade-in")
        window.button_drop_area.add_css_class("fade-out")
        
        # Force window size reset using our new method
        if hasattr(window, 'original_width') and hasattr(window, 'original_height'):
            window.set_fixed_size(window.original_width, window.original_height)
        else:
            # Fallback to default size
            window.set_fixed_size(1000, 700)
        
        # Schedule the actual visibility change after a short delay for animation
        GLib.timeout_add(100, lambda: toggle_drop_area_visibility(window, False))

def toggle_drop_area_visibility(window, show_drop_area):
    """Helper function to toggle drop area visibility with proper animation cleanup"""
    if show_drop_area:
        window.button_select_area.set_visible(False)
        window.button_select_area.remove_css_class("fade-out")
        window.button_drop_area.set_visible(True)
        window.button_drop_area.remove_css_class("fade-in")
        window.button_drop_area.add_css_class("drop-area-active")
    else:
        window.button_select_area.set_visible(True)
        window.button_select_area.remove_css_class("fade-in")
        window.button_drop_area.set_visible(False)
        window.button_drop_area.remove_css_class("fade-out")
        window.button_drop_area.remove_css_class("drop-area-active")
    
    # Return False to ensure the timeout doesn't repeat
    return False

def on_drop(drop_target, value, x, y, window):
    """Handle the drop of files into the application"""
    # Reset the drag and drop UI first - with animation
    window.button_select_area.add_css_class("fade-in")
    window.button_drop_area.add_css_class("fade-out")
    
    # Force window size reset using our new method
    if hasattr(window, 'original_width') and hasattr(window, 'original_height'):
        window.set_fixed_size(window.original_width, window.original_height)
    else:
        # Fallback to default size
        window.set_fixed_size(1000, 700)
    
    GLib.timeout_add(100, lambda: toggle_drop_area_visibility(window, False))
    
    apk_files = []
    
    # Process file or files
    try:
        print(f"Drop value type: {type(value)}, value: {value}")
        
        # Handle case where value might be a GList or other collection wrapper
        if hasattr(value, "get_data") and callable(value.get_data):
            try:
                print("Trying to get data from GLib.List-like object")
                files_list = value.get_data()
                print(f"Got files list: {files_list} (type: {type(files_list)})")
                if isinstance(files_list, (list, tuple)):
                    for file_item in files_list:
                        if isinstance(file_item, Gio.File):
                            file_path = file_item.get_path()
                            if file_path and os.path.isfile(file_path) and file_path.lower().endswith('.apk'):
                                apk_files.append(file_path)
                                print(f"Added APK from GList: {file_path}")
            except Exception as e:
                print(f"Error processing GList-like object: {e}")
        
        # Handle standard GFile case
        elif isinstance(value, Gio.File):
            # Single file or directory drop
            file_path = value.get_path()
            print(f"Got file path: {file_path}")
            
            if file_path:
                if os.path.isfile(file_path) and file_path.lower().endswith('.apk'):
                    # Single APK file
                    apk_files.append(file_path)
                    print(f"Added single APK file: {file_path}")
                elif os.path.isdir(file_path):
                    # Directory - collect all APKs inside
                    print(f"Scanning directory: {file_path}")
                    for file in os.listdir(file_path):
                        full_path = os.path.join(file_path, file)
                        if os.path.isfile(full_path) and file.lower().endswith('.apk'):
                            apk_files.append(full_path)
                            print(f"Added APK from directory: {full_path}")
                else:
                    print(f"File is not an APK or directory: {file_path}")
        
        # Handle array-like objects and iterables
        elif isinstance(value, (list, tuple)) or hasattr(value, '__iter__'):
            # Multiple files drop
            print(f"Processing multiple items, count: {len(value) if hasattr(value, '__len__') else 'unknown'}")
            for item in value:
                print(f"Processing item: {item} (type: {type(item)})")
                
                if isinstance(item, Gio.File):
                    file_path = item.get_path()
                    print(f"Processing file: {file_path}")
                    if file_path and os.path.isfile(file_path) and file_path.lower().endswith('.apk'):
                        apk_files.append(file_path)
                        print(f"Added APK file from list: {file_path}")
                elif isinstance(item, str):
                    print(f"Processing string path: {item}")
                    if os.path.isfile(item) and item.lower().endswith('.apk'):
                        apk_files.append(item)
                        print(f"Added APK file from string: {item}")
                elif hasattr(item, "get_uri") and callable(item.get_uri):
                    # Handle URI-based items
                    try:
                        uri = item.get_uri()
                        print(f"Got URI: {uri}")
                        if uri.startswith("file://"):
                            import urllib.parse
                            file_path = urllib.parse.unquote(uri[7:])
                            if os.path.isfile(file_path) and file_path.lower().endswith('.apk'):
                                apk_files.append(file_path)
                                print(f"Added APK from URI item: {file_path}")
                    except Exception as e:
                        print(f"Error processing URI item: {e}")
                else:
                    print(f"Unknown item type in list: {type(item)}")
                    # Try converting to string as a last resort
                    try:
                        str_item = str(item)
                        if os.path.isfile(str_item) and str_item.lower().endswith('.apk'):
                            apk_files.append(str_item)
                            print(f"Added APK from string conversion: {str_item}")
                    except:
                        pass
        else:
            print(f"Unhandled value type: {type(value)}")
            # Try string conversion as a last resort for unknown types
            try:
                str_value = str(value)
                if os.path.isfile(str_value) and str_value.lower().endswith('.apk'):
                    apk_files.append(str_value)
                    print(f"Added APK from string conversion of unknown type: {str_value}")
            except:
                print("Failed to convert unknown type to string")
    except Exception as e:
        print(f"Error processing drop: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Process the collected APK files
    if apk_files:
        print(f"Found {len(apk_files)} APK files: {apk_files}")
        window.apk_files = apk_files
        window.parse_env_variables()
        
        # Show test view after a longer delay to ensure size reset is applied
        GLib.timeout_add(300, lambda: change_to_test_view(window, apk_files))
        
        return True
    else:
        print("No APK files found in the dropped items")
        # Show error notification
        toast = Adw.Toast.new("No APK files found in the dropped items")
        window.toast_overlay.add_toast(toast)
        return False

def change_to_test_view(window, apk_files):
    """Change to test view after ensuring resize has been applied"""
    # Ensure window size is properly set before changing views
    if hasattr(window, 'original_width') and hasattr(window, 'original_height'):
        window.set_fixed_size(window.original_width, window.original_height)
    else:
        window.set_fixed_size(1000, 700)
    
    # Show test view, hide welcome view
    window.welcome_view.set_visible(False)
    window.testing_view.set_visible(True)
    
    # Update APK information in the UI
    if len(apk_files) == 1:
        # Single APK case
        first_apk = os.path.basename(apk_files[0])
        window.apk_value_label.set_text(first_apk)
    else:
        # Multiple APK case
        window.apk_value_label.set_text(f"{len(apk_files)} APK files selected")
    
    # Update status indicators
    window.status_value_label.set_text("Ready")
    window.status_icon.set_from_icon_name("media-playback-pause-symbolic")
    window.command_value_label.set_text("-")
    
    # Print information about loaded APKs
    print(f"\nLoaded {len(apk_files)} APK files:")
    for i, apk in enumerate(apk_files):
        print(f"{i+1}. {os.path.basename(apk)} - {apk}")
    
    # Start testing
    window.test_next_apk()
    
    # Show notification with appropriate message based on the number of APKs
    if len(apk_files) == 1:
        toast = Adw.Toast.new(f"APK loaded: {os.path.basename(apk_files[0])}")
    else:
        toast = Adw.Toast.new(f"Loading {len(apk_files)} APK files for testing")
    
    window.toast_overlay.add_toast(toast)
    
    # Add a final size check after everything is loaded
    GLib.timeout_add(500, lambda: ensure_fixed_size(window))
    
    return False  # Don't repeat

def ensure_fixed_size(window):
    """Make a final attempt to ensure the window size is fixed"""
    if hasattr(window, 'original_width') and hasattr(window, 'original_height'):
        current_width, current_height = window.get_default_size()
        if current_width != window.original_width or current_height != window.original_height:
            window.set_fixed_size(window.original_width, window.original_height)
    return False

def on_drag_key_pressed(controller, keyval, keycode, state, window):
    """Reset drag & drop UI if Escape is pressed during drag"""
    if keyval == Gdk.KEY_Escape and hasattr(window, 'button_drop_area') and window.button_drop_area.get_visible():
        # Reset drag & drop UI with animation
        window.button_select_area.add_css_class("fade-in")
        window.button_drop_area.add_css_class("fade-out")
        GLib.timeout_add(100, lambda: toggle_drop_area_visibility(window, False))
        return True
    return False 

def on_drop_uri_list(drop_target, value, x, y, window):
    """Handle drop of URI lists (common format for file managers)"""
    # Reset the drag and drop UI first - with animation
    window.button_select_area.add_css_class("fade-in")
    window.button_drop_area.add_css_class("fade-out")
    
    # Force window size reset using our new method
    if hasattr(window, 'original_width') and hasattr(window, 'original_height'):
        window.set_fixed_size(window.original_width, window.original_height)
    else:
        # Fallback to default size
        window.set_fixed_size(1000, 700)
    
    GLib.timeout_add(100, lambda: toggle_drop_area_visibility(window, False))
    
    apk_files = []
    
    # Process URI list
    try:
        print(f"URI drop value type: {type(value)}, value: {value}")
        
        # Handle both URI lists and strings
        uris = []
        if isinstance(value, str):
            # Try different separators for URI lists
            if "\r\n" in value:
                uris = value.strip().split("\r\n")
            elif "\n" in value:
                uris = value.strip().split("\n")
            else:
                uris = [value.strip()]
            print(f"Parsed {len(uris)} URIs from string")
        elif isinstance(value, (list, tuple)):
            uris = value
            print(f"Received {len(uris)} URIs as list/tuple")
        else:
            print(f"Unexpected URI list type: {type(value)}")
            uris = [str(value)]
            
        for uri in uris:
            print(f"Processing URI: {uri} (type: {type(uri)})")
            
            if isinstance(uri, str) and uri.strip():
                # Convert URI to file path
                file_path = None
                
                if uri.startswith("file://"):
                    # Remove 'file://' and decode URL encoding
                    file_path = uri[7:]
                    import urllib.parse
                    file_path = urllib.parse.unquote(file_path)
                    print(f"Converted URI to path: {file_path}")
                else:
                    file_path = uri
                    print(f"Using direct path: {file_path}")
                    
                if file_path:
                    if os.path.isfile(file_path) and file_path.lower().endswith('.apk'):
                        apk_files.append(file_path)
                        print(f"Added APK from URI: {file_path}")
                    elif os.path.isdir(file_path):
                        # Directory - collect all APKs inside
                        print(f"Scanning directory from URI: {file_path}")
                        for file in os.listdir(file_path):
                            full_path = os.path.join(file_path, file)
                            if os.path.isfile(full_path) and file.lower().endswith('.apk'):
                                apk_files.append(full_path)
                                print(f"Added APK from URI directory: {full_path}")
                    else:
                        print(f"URI path is not an APK or directory: {file_path}")
            elif isinstance(uri, Gio.File):
                file_path = uri.get_path()
                print(f"Processing Gio.File URI: {file_path}")
                if file_path and os.path.isfile(file_path) and file_path.lower().endswith('.apk'):
                    apk_files.append(file_path)
                    print(f"Added APK from Gio.File URI: {file_path}")
    except Exception as e:
        print(f"Error processing URI drop: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Process the collected APK files
    if apk_files:
        print(f"Found {len(apk_files)} APK files from URIs: {apk_files}")
        window.apk_files = apk_files
        window.parse_env_variables()
        
        # Show test view after a longer delay to ensure size reset is applied
        GLib.timeout_add(300, lambda: change_to_test_view(window, apk_files))
        
        return True
    else:
        print("No APK files found in the dropped URI items")
        # Show error notification
        toast = Adw.Toast.new("No APK files found in the dropped items")
        window.toast_overlay.add_toast(toast)
        return False

def on_drop_text(drop_target, value, x, y, window):
    """Handle drop of text content that might contain file paths"""
    # Reset the drag and drop UI first - with animation
    window.button_select_area.add_css_class("fade-in")
    window.button_drop_area.add_css_class("fade-out")
    
    # Force window size reset using our new method
    if hasattr(window, 'original_width') and hasattr(window, 'original_height'):
        window.set_fixed_size(window.original_width, window.original_height)
    else:
        # Fallback to default size
        window.set_fixed_size(1000, 700)
    
    GLib.timeout_add(100, lambda: toggle_drop_area_visibility(window, False))
    
    apk_files = []
    
    # Process text that might contain file paths
    try:
        print(f"Text drop value type: {type(value)}, value: {value}")
        
        if isinstance(value, str):
            # Split by common newline types
            if '\r\n' in value:
                lines = value.split('\r\n')
            elif '\n' in value:
                lines = value.split('\n')
            elif '\r' in value:
                lines = value.split('\r')
            else:
                # Single line
                lines = [value]
                
            print(f"Parsed {len(lines)} lines from text")
            
            for line in lines:
                line = line.strip()
                print(f"Processing text line: '{line}'")
                
                if line:
                    # Try as direct file path
                    if os.path.isfile(line) and line.lower().endswith('.apk'):
                        apk_files.append(line)
                        print(f"Added APK from text line as direct path: {line}")
                    # Try as URI
                    elif line.startswith('file://'):
                        try:
                            import urllib.parse
                            file_path = urllib.parse.unquote(line[7:])
                            if os.path.isfile(file_path) and file_path.lower().endswith('.apk'):
                                apk_files.append(file_path)
                                print(f"Added APK from text line as URI: {file_path}")
                        except Exception as e:
                            print(f"Error processing URI in text: {e}")
                    # Try as directory
                    elif os.path.isdir(line):
                        print(f"Scanning directory from text: {line}")
                        for file in os.listdir(line):
                            full_path = os.path.join(line, file)
                            if os.path.isfile(full_path) and file.lower().endswith('.apk'):
                                apk_files.append(full_path)
                                print(f"Added APK from text directory: {full_path}")
    except Exception as e:
        print(f"Error processing text drop: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Process the collected APK files
    if apk_files:
        print(f"Found {len(apk_files)} APK files from text: {apk_files}")
        window.apk_files = apk_files
        window.parse_env_variables()
        
        # Show test view after a longer delay to ensure size reset is applied
        GLib.timeout_add(300, lambda: change_to_test_view(window, apk_files))
        
        return True
    else:
        print("No APK files found in the dropped text")
        # Show error notification
        toast = Adw.Toast.new("No APK files found in the dropped text")
        window.toast_overlay.add_toast(toast)
        return False

def on_drop_file_list(drop_target, value, x, y, window):
    """Handle drop of file lists"""
    # Reset the drag and drop UI first - with animation
    window.button_select_area.add_css_class("fade-in")
    window.button_drop_area.add_css_class("fade-out")
    
    # Force window size reset using our new method
    if hasattr(window, 'original_width') and hasattr(window, 'original_height'):
        window.set_fixed_size(window.original_width, window.original_height)
    else:
        # Fallback to default size
        window.set_fixed_size(1000, 700)
    
    GLib.timeout_add(100, lambda: toggle_drop_area_visibility(window, False))
    
    apk_files = []
    
    # Process file list
    try:
        print(f"File list drop value type: {type(value)}, value: {value}")
        
        if value is None:
            print("Received None value in file list drop")
            return False
            
        # Special handling for GLib.List (common in GTK4 drag and drop)
        if hasattr(value, "get_n_items") and callable(getattr(value, "get_n_items", None)):
            try:
                n_items = value.get_n_items()
                print(f"Processing GLib.List-like object with {n_items} items")
                
                for i in range(n_items):
                    item = value.get_item(i)
                    if isinstance(item, Gio.File):
                        file_path = item.get_path()
                        if file_path and os.path.isfile(file_path) and file_path.lower().endswith('.apk'):
                            apk_files.append(file_path)
                            print(f"Added APK from GLib.List: {file_path}")
            except Exception as e:
                print(f"Error processing GLib.List: {e}")
                import traceback
                traceback.print_exc()
            
        # Handle case where value is a GdkFileList
        elif hasattr(value, "get_files") and callable(getattr(value, "get_files", None)):
            try:
                files = value.get_files()
                print(f"Got file list with {len(files)} items")
                for item in files:
                    if isinstance(item, Gio.File):
                        file_path = item.get_path()
                        if file_path and os.path.isfile(file_path) and file_path.lower().endswith('.apk'):
                            apk_files.append(file_path)
                            print(f"Added APK from file list get_files: {file_path}")
            except Exception as e:
                print(f"Error processing file list get_files: {e}")
                import traceback
                traceback.print_exc()
                
        # Standard list or tuple
        elif isinstance(value, list) or isinstance(value, tuple):
            print(f"Processing list/tuple with {len(value)} items")
            for item in value:
                print(f"Processing file list item: {item} (type: {type(item)})")
                
                if isinstance(item, Gio.File):
                    file_path = item.get_path()
                    print(f"Got file path from Gio.File: {file_path}")
                    
                    if file_path:
                        if os.path.isfile(file_path) and file_path.lower().endswith('.apk'):
                            apk_files.append(file_path)
                            print(f"Added APK from file list Gio.File: {file_path}")
                        elif os.path.isdir(file_path):
                            print(f"Scanning directory from file list: {file_path}")
                            for file in os.listdir(file_path):
                                full_path = os.path.join(file_path, file)
                                if os.path.isfile(full_path) and file.lower().endswith('.apk'):
                                    apk_files.append(full_path)
                                    print(f"Added APK from file list directory: {full_path}")
                elif isinstance(item, str):
                    print(f"Processing string path in file list: {item}")
                    if os.path.isfile(item) and item.lower().endswith('.apk'):
                        apk_files.append(item)
                        print(f"Added APK from file list string: {item}")
                    elif os.path.isdir(item):
                        print(f"Scanning directory from file list string: {item}")
                        for file in os.listdir(item):
                            full_path = os.path.join(item, file)
                            if os.path.isfile(full_path) and file.lower().endswith('.apk'):
                                apk_files.append(full_path)
                                print(f"Added APK from file list string directory: {full_path}")
                else:
                    print(f"Unhandled item type in file list: {type(item)}")
                    # Try to convert to string
                    try:
                        str_item = str(item)
                        if os.path.isfile(str_item) and str_item.lower().endswith('.apk'):
                            apk_files.append(str_item)
                            print(f"Added APK from file list item conversion: {str_item}")
                    except:
                        pass
        # Try to handle as a GObject
        elif hasattr(value, "get_item") and hasattr(value, "get_n_items"):
            # This might be a GListModel or similar
            count = value.get_n_items()
            print(f"Processing as GListModel with {count} items")
            for i in range(count):
                item = value.get_item(i)
                if isinstance(item, Gio.File):
                    file_path = item.get_path()
                    if file_path and os.path.isfile(file_path) and file_path.lower().endswith('.apk'):
                        apk_files.append(file_path)
                        print(f"Added APK from GListModel Gio.File: {file_path}")
        # Attempt to handle GFile array directly
        elif hasattr(value, "__len__") and hasattr(value, "__getitem__"):
            try:
                array_len = len(value)
                print(f"Trying to process as array-like with {array_len} items")
                for i in range(array_len):
                    item = value[i]
                    if isinstance(item, Gio.File):
                        file_path = item.get_path()
                        if file_path and os.path.isfile(file_path) and file_path.lower().endswith('.apk'):
                            apk_files.append(file_path)
                            print(f"Added APK from array-like: {file_path}")
            except Exception as e:
                print(f"Error processing as array-like: {e}")
        # Single file case        
        elif isinstance(value, Gio.File):
            file_path = value.get_path()
            print(f"Processing single Gio.File: {file_path}")
            if file_path and os.path.isfile(file_path) and file_path.lower().endswith('.apk'):
                apk_files.append(file_path)
                print(f"Added APK from single file: {file_path}")
            elif file_path and os.path.isdir(file_path):
                print(f"Scanning directory from single file: {file_path}")
                for file in os.listdir(file_path):
                    full_path = os.path.join(file_path, file)
                    if os.path.isfile(full_path) and file.lower().endswith('.apk'):
                        apk_files.append(full_path)
                        print(f"Added APK from single file directory: {full_path}")
        # String path case
        elif isinstance(value, str):
            print(f"Processing single string path: {value}")
            if os.path.isfile(value) and value.lower().endswith('.apk'):
                apk_files.append(value)
                print(f"Added APK from single string: {value}")
            elif os.path.isdir(value):
                print(f"Scanning directory from single string: {value}")
                for file in os.listdir(value):
                    full_path = os.path.join(value, file)
                    if os.path.isfile(full_path) and file.lower().endswith('.apk'):
                        apk_files.append(full_path)
                        print(f"Added APK from single string directory: {full_path}")
        else:
            print(f"Unhandled value type in file list: {type(value)}")
            # Try to convert to string as last resort
            try:
                str_value = str(value)
                if os.path.isfile(str_value) and str_value.lower().endswith('.apk'):
                    apk_files.append(str_value)
                    print(f"Added APK from file list value conversion: {str_value}")
            except:
                pass
    except Exception as e:
        print(f"Error processing file list drop: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Process the collected APK files
    if apk_files:
        print(f"Found {len(apk_files)} APK files from file list: {apk_files}")
        window.apk_files = apk_files
        window.parse_env_variables()
        
        # Show test view after a longer delay to ensure size reset is applied
        GLib.timeout_add(300, lambda: change_to_test_view(window, apk_files))
        
        return True
    else:
        print("No APK files found in the dropped file list")
        # Show error notification
        toast = Adw.Toast.new("No APK files found in the dropped files")
        window.toast_overlay.add_toast(toast)
        return False

def on_drop_wildcard(drop_target, value, x, y, window):
    """Handle drop with wildcard content type"""
    # Reset the drag and drop UI first - with animation
    window.button_select_area.add_css_class("fade-in")
    window.button_drop_area.add_css_class("fade-out")
    
    # Force window size reset using our new method
    if hasattr(window, 'original_width') and hasattr(window, 'original_height'):
        window.set_fixed_size(window.original_width, window.original_height)
    else:
        # Fallback to default size
        window.set_fixed_size(1000, 700)
    
    GLib.timeout_add(100, lambda: toggle_drop_area_visibility(window, False))
    
    apk_files = []
    
    # Try to process value based on its type
    try:
        print(f"Wildcard drop value type: {type(value)}, value: {value}")
        
        if value is None:
            print("Received None value in wildcard drop")
            return False
            
        if isinstance(value, Gio.File):
            # Single file
            file_path = value.get_path()
            print(f"Processing Gio.File in wildcard: {file_path}")
            
            if file_path:
                if os.path.isfile(file_path) and file_path.lower().endswith('.apk'):
                    apk_files.append(file_path)
                    print(f"Added APK from wildcard file: {file_path}")
                elif os.path.isdir(file_path):
                    # Directory - collect all APKs inside
                    print(f"Scanning directory from wildcard: {file_path}")
                    for file in os.listdir(file_path):
                        full_path = os.path.join(file_path, file)
                        if os.path.isfile(full_path) and file.lower().endswith('.apk'):
                            apk_files.append(full_path)
                            print(f"Added APK from wildcard directory: {full_path}")
        elif isinstance(value, str):
            # Check if it's a file path
            print(f"Processing string in wildcard: {value}")
            if os.path.isfile(value) and value.lower().endswith('.apk'):
                apk_files.append(value)
                print(f"Added APK from wildcard string: {value}")
            elif os.path.isdir(value):
                print(f"Scanning directory from wildcard string: {value}")
                for file in os.listdir(value):
                    full_path = os.path.join(value, file)
                    if os.path.isfile(full_path) and file.lower().endswith('.apk'):
                        apk_files.append(full_path)
                        print(f"Added APK from wildcard string directory: {full_path}")
        elif isinstance(value, (list, tuple)) or hasattr(value, '__iter__'):
            # Iterable - try to process each item
            try:
                item_count = len(value) if hasattr(value, '__len__') else "unknown"
                print(f"Processing iterable in wildcard with {item_count} items")
                
                for item in value:
                    print(f"Processing wildcard item: {item} (type: {type(item)})")
                    
                    if isinstance(item, Gio.File):
                        file_path = item.get_path()
                        if file_path and os.path.isfile(file_path) and file_path.lower().endswith('.apk'):
                            apk_files.append(file_path)
                            print(f"Added APK from wildcard iterable Gio.File: {file_path}")
                    elif isinstance(item, str):
                        if os.path.isfile(item) and item.lower().endswith('.apk'):
                            apk_files.append(item)
                            print(f"Added APK from wildcard iterable string: {item}")
            except Exception as e:
                print(f"Error processing wildcard iterable: {e}")
        else:
            # Try to convert to string as last resort
            try:
                str_value = str(value)
                print(f"Trying string conversion of unknown type: {str_value}")
                if os.path.isfile(str_value) and str_value.lower().endswith('.apk'):
                    apk_files.append(str_value)
                    print(f"Added APK from wildcard string conversion: {str_value}")
            except:
                print(f"Failed string conversion for type: {type(value)}")
    except Exception as e:
        print(f"Error processing wildcard drop: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Process the collected APK files
    if apk_files:
        print(f"Found {len(apk_files)} APK files from wildcard: {apk_files}")
        window.apk_files = apk_files
        window.parse_env_variables()
        
        # Show test view after a longer delay to ensure size reset is applied
        GLib.timeout_add(300, lambda: change_to_test_view(window, apk_files))
        
        return True
    else:
        print("No APK files found in the dropped wildcard items")
        # Show error notification
        toast = Adw.Toast.new("No APK files found in the dropped items")
        window.toast_overlay.add_toast(toast)
        return False 