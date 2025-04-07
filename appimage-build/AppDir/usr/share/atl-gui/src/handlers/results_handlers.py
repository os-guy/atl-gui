import gi
import os
import datetime
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Pango, Gdk, GObject, GLib
import re
from src.utils.css_provider import load_css_data

def extract_errors_from_log(log_text):
    """Extract and categorize error lines from a log text, returning structured error data."""
    error_groups = []
    
    # Common error indicators by severity - removed UI Issues and General Warnings
    error_indicators = {
        "File Not Found": ["Failed to open file", "No such file or directory"],
        "Failed Execution": ["Failed execv", "non-0 exit status", "Error terminating process"],
        "Dex Compilation": ["dex2oat", "Failed to compile dex file"],
        "Package Parsing": ["PackageParser", "Unknown element", "Binary XML file"],
        "Java Exceptions": ["java.lang.", "Exception:", "Caused by:"],
        "Native Errors": ["E/", "ERROR:", "Error:", "error:"],
        "Asset Errors": ["AssetsProvider", "Failed to load", "Could not load"],
        "Permissions": ["Permission denied", "requires permission"]
    }
    
    # Process the log line by line to find errors
    for line in log_text.splitlines():
        # Check each error category
        for error_type, indicators in error_indicators.items():
            for indicator in indicators:
                if indicator in line:
                    # Ignore common less important messages that cause noise
                    if any(ignore in line for ignore in [
                        "Gtk-WARNING", "Theme parser error", "gtk.css",
                        "libadwaita", "gtk-application-prefer-dark-theme",
                        "Failed to load module", "Warning: Unable to load"
                    ]):
                        continue
                        
                    # Try to extract a more specific error cause
                    error_cause = extract_error_cause(line, indicator)
                    
                    # Create a new error entry
                    error_entry = {
                        "type": error_type,
                        "cause": error_cause,
                        "line": line,
                        "details": []  # Will contain related lines
                    }
                    
                    # Look for related lines (context) - up to 5 lines before and after
                    lines = log_text.splitlines()
                    try:
                        line_index = lines.index(line)
                        start = max(0, line_index - 5)
                        end = min(len(lines), line_index + 5)
                        
                        # Add context lines
                        for i in range(start, end + 1):
                            if i != line_index and i < len(lines):  # Skip the main error line
                                error_entry["details"].append(lines[i])
                    except ValueError:
                        # If line not found, just continue
                        pass
                    
                    # Add to error groups
                    error_groups.append(error_entry)
                    break
            else:
                # Continue if the inner loop wasn't broken
                continue
            # Inner loop was broken, break the outer loop too
            break
    
    # Sort errors by type
    error_groups.sort(key=lambda x: x["type"])
    
    return error_groups

def extract_error_cause(line, indicator):
    """Extract a more specific error cause from an error line."""
    try:
        # Try to extract what's after the indicator
        if indicator in line:
            parts = line.split(indicator, 1)
            if len(parts) > 1:
                # Special case for file not found errors - include path
                if indicator in ["Failed to open file", "No such file or directory"]:
                    # Try to extract file path
                    path_match = extract_file_path(parts[1])
                    if path_match:
                        return f"Path: {path_match}"
                
                # Special case for dex file errors
                if "dex" in indicator.lower():
                    path_match = extract_file_path(parts[1])
                    if path_match:
                        return f"Dex file: {path_match}"
                        
                # Check for asset errors
                if any(asset_indicator in indicator for asset_indicator in ["Failed to load", "Could not load", "AssetsProvider"]):
                    path_match = extract_file_path(parts[1])
                    if path_match:
                        return f"Asset: {path_match}"
                
                # Get what's after the indicator until the end of line or first :
                cause = parts[1].strip()
                if ":" in cause:
                    cause = cause.split(":", 1)[0].strip()
                # Truncate if too long
                return cause[:50] + ("..." if len(cause) > 50 else "")
    except Exception:
        pass
    
    # If all else fails, return a general message
    return "See details for more information"

def extract_file_path(text):
    """Extract a file path from text using regex patterns."""
    # Try different patterns to extract file paths
    # Pattern 1: Quoted paths
    path_matches = re.findall(r"['\"]([^'\"]*?(?:/|\\)[^'\"]*?)['\"]", text)
    if path_matches:
        return path_matches[0]
        
    # Pattern 2: Common Unix paths starting with /
    path_matches = re.findall(r"(/[^ :,\"']*)", text)
    if path_matches:
        return path_matches[0]
        
    # Pattern 3: Paths with extension
    path_matches = re.findall(r"(\S+\.(apk|dex|so|jar|xml|png|jpg))", text)
    if path_matches:
        return path_matches[0][0]
        
    # Pattern 4: Windows-style paths
    path_matches = re.findall(r"([A-Za-z]:\\[^ :,\"']*)", text)
    if path_matches:
        return path_matches[0]
    
    return None

def show_test_results(self):
    # Forcefully kill any running terminal process to ensure it's not running in the background
    if hasattr(self, 'terminal_manager') and self.terminal_manager.is_running:
        print("[DEBUG] Forcefully killing terminal process before showing results")
        self.terminal_manager.kill_terminal()
    
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
    
    # Auto-detect working/not working based on error logs
    for apk_path, result in self.test_results.items():
        # If it's already set to working or not_working, leave it alone
        if result != "unknown" and result != "skipped":
            continue
            
        # Check logs for auto-detection of working status
        if hasattr(self, 'terminal_logs') and apk_path in self.terminal_logs:
            log_text = self.terminal_logs[apk_path]
            
            # Check for success indicators
            successful_launch = False
            common_errors = False
            
            # Success indicators
            if "Successfully launched" in log_text or "app started" in log_text.lower():
                successful_launch = True
                
            # Common error indicators that suggest the app didn't work
            error_indicators = [
                "FATAL EXCEPTION", 
                "Java.lang.RuntimeException",
                "app has stopped",
                "ANR in",
                "process crashed",
                "Failed to launch",
                "Unable to start activity"
            ]
            
            for indicator in error_indicators:
                if indicator in log_text:
                    common_errors = True
                    break
                    
            # Make the determination
            if successful_launch and not common_errors:
                self.test_results[apk_path] = "working"
            elif common_errors:
                self.test_results[apk_path] = "not_working"
                
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
            
        # Add Errors button if the APK is in test_results and not a result file
        is_result_file = os.path.dirname(apk_path) == os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test_results")
        
        if not is_result_file and hasattr(self, 'terminal_logs') and apk_path in self.terminal_logs:
            # Get error count
            log_text = self.terminal_logs[apk_path]
            error_groups = extract_errors_from_log(log_text)
            error_count = len(error_groups)
            
            errors_button = Gtk.Button(label=f"Errors ({error_count})")
            errors_button.add_css_class("pill")
            errors_button.add_css_class("error")
            errors_button.set_valign(Gtk.Align.CENTER)
            
            # Store APK path for error display
            errors_button.apk_path = apk_path
            errors_button.connect("clicked", self.show_apk_errors)
            
            # Add button to row
            expander.add_suffix(errors_button)
            
        # Terminal loglarını ekle - terminal_logs olup olmadığını kontrol et
        if hasattr(self, 'terminal_logs') and apk_path in self.terminal_logs:
            # Terminal logu varsa, bir metin görünümü içinde göster
            log_view = Gtk.TextView()
            log_view.set_editable(False)
            log_view.set_cursor_visible(False)
            log_view.add_css_class("log-view")
            log_view.get_buffer().set_text(self.terminal_logs[apk_path])
            
            # Loglar için CSS - daha ince border
            css_provider = Gtk.CssProvider()
            css_data = """
                textview.log-view {
                    background-color: #f8f8f8;
                    color: #202020;
                    padding: 8px;
                    border-radius: 3px;
                    font-family: monospace;
                    font-size: 12px;
                    border: none;
                    box-shadow: 0 0 2px rgba(0, 0, 0, 0.05);
                }
            """
            load_css_data(css_provider, css_data, "error view CSS")
            
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

def show_apk_errors(self, button):
    print("DEBUG: show_apk_errors called")
    apk_path = button.apk_path
    apk_name = os.path.basename(apk_path)
    
    # Create a robust dialog using Gtk.Dialog instead of Adw.Window
    dialog = Gtk.Dialog(title=f"Errors: {apk_name}", 
                        transient_for=self,
                        modal=True,
                        destroy_with_parent=True)
    
    print(f"DEBUG: Creating dialog for APK: {apk_name}")
    dialog.set_default_size(800, 600)
    
    # Header bar can still be added but not needed in Gtk.Dialog
    header_bar = Gtk.HeaderBar()
    header_bar.set_title_widget(Gtk.Label(label=f"Errors for {apk_name}"))
    header_bar.add_css_class("flat")
    
    # Get content area
    content_area = dialog.get_content_area()
    content_area.set_spacing(8)
    content_area.set_margin_top(16)
    content_area.set_margin_bottom(16)
    content_area.set_margin_start(16)
    content_area.set_margin_end(16)
    
    # APK info card
    info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    info_box.add_css_class("card")
    info_box.set_margin_bottom(8)
    
    # APK details section
    apk_label = Gtk.Label(label=f"<b>APK:</b> {apk_name}")
    apk_label.set_use_markup(True)
    apk_label.set_xalign(0)
    apk_label.set_margin_top(12)
    apk_label.set_margin_start(12)
    apk_label.set_margin_end(12)
    info_box.append(apk_label)
    
    status_label = Gtk.Label(label=f"<b>Status:</b> {self.test_results.get(apk_path, 'Unknown')}")
    status_label.set_use_markup(True)
    status_label.set_xalign(0)
    status_label.set_margin_start(12)
    status_label.set_margin_bottom(12)
    status_label.set_margin_end(12)
    info_box.append(status_label)
    
    content_area.append(info_box)
    
    # Create search entry
    search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    search_box.set_margin_bottom(8)
    
    search_entry = Gtk.SearchEntry()
    search_entry.set_placeholder_text("Search in errors...")
    search_entry.set_hexpand(True)
    search_box.append(search_entry)
    
    # Add case sensitive checkbox
    case_check = Gtk.CheckButton()
    case_check.set_label("Case sensitive")
    search_box.append(case_check)
    
    content_area.append(search_box)
    
    # Errors list container
    errors_scroll = Gtk.ScrolledWindow()
    errors_scroll.set_vexpand(True)
    errors_scroll.add_css_class("card")
    
    # Create expandable rows for errors
    errors_list = Gtk.ListBox()
    errors_list.set_selection_mode(Gtk.SelectionMode.NONE)
    errors_list.add_css_class("boxed-list")
    
    # Connect search handler
    search_entry.connect("search-changed", lambda entry: filter_errors(entry.get_text(), case_check.get_active(), errors_list))
    case_check.connect("toggled", lambda check: filter_errors(search_entry.get_text(), check.get_active(), errors_list))
    
    # Define search filter function
    def filter_errors(search_text, case_sensitive, error_list):
        print(f"DEBUG: Filtering errors with text: '{search_text}', case sensitive: {case_sensitive}")
        if not search_text:
            # Show all rows
            child = error_list.get_first_child()
            while child:
                child.set_visible(True)
                child = child.get_next_sibling()
            return
        
        # Filter rows
        child = error_list.get_first_child()
        while child:
            visible = False
            
            if isinstance(child, Adw.ExpanderRow):
                # Get title and subtitle
                title = child.get_title() or ""
                subtitle = child.get_subtitle() or ""
                
                # Prepare comparison text
                if not case_sensitive:
                    title = title.lower()
                    subtitle = subtitle.lower()
                    compare_text = search_text.lower()
                else:
                    compare_text = search_text
                
                # Check if search text is in title or subtitle
                if compare_text in title or compare_text in subtitle:
                    visible = True
                else:
                    # For AdwExpanderRow, we need to check all the rows it contains
                    row_index = 0
                    row = None
                    
                    # First try to get child widgets directly
                    inner_content = ""
                    content_box = child.get_last_child()
                    if content_box:
                        inner_content = extract_text_from_widget(content_box)
                        
                    if not case_sensitive:
                        inner_content = inner_content.lower()
                    
                    if compare_text in inner_content:
                        visible = True
            elif isinstance(child, Gtk.ListBoxRow):
                # Handle regular list box rows (like "No errors found")
                label = find_label_in_widget(child)
                if label:
                    label_text = label.get_text() or ""
                    if not case_sensitive:
                        label_text = label_text.lower()
                        compare_text = search_text.lower()
                    else:
                        compare_text = search_text
                    
                    if compare_text in label_text:
                        visible = True
            
            # Set visibility based on our checks
            child.set_visible(visible)
            child = child.get_next_sibling()
    
    # Helper function to extract all text from a widget and its children
    def extract_text_from_widget(widget):
        result = ""
        
        # Check if it's a TextView
        if isinstance(widget, Gtk.TextView):
            buffer = widget.get_buffer()
            result += buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        
        # Check if it's a Label
        elif isinstance(widget, Gtk.Label):
            result += widget.get_text() or ""
        
        # Recursively process children for containers
        if hasattr(widget, 'get_first_child') and callable(getattr(widget, 'get_first_child')):
            child = widget.get_first_child()
            while child:
                result += extract_text_from_widget(child)
                child = child.get_next_sibling()
        
        return result
    
    # Helper function to find a label in a widget
    def find_label_in_widget(widget):
        if isinstance(widget, Gtk.Label):
            return widget
        
        if hasattr(widget, 'get_first_child') and callable(getattr(widget, 'get_first_child')):
            child = widget.get_first_child()
            while child:
                label = find_label_in_widget(child)
                if label:
                    return label
                child = child.get_next_sibling()
        
        return None
    
    # Helper function to find TextView widgets (kept for compatibility)
    def find_text_views(container):
        text_views = []
        
        if isinstance(container, Gtk.TextView):
            text_views.append(container)
        
        if hasattr(container, 'get_first_child'):
            child = container.get_first_child()
            while child:
                if isinstance(child, Gtk.Widget):
                    text_views.extend(find_text_views(child))
                child = child.get_next_sibling()
        
        return text_views
    
    # Define CSS for text views
    css_provider = Gtk.CssProvider()
    css_data = """
        textview.log-view, textview.error-line, textview.context-view {
            background-color: #f8f8f8;
            color: #202020;
            padding: 8px;
            border-radius: 3px;
            font-family: monospace;
            font-size: 12px;
            border: none;
            box-shadow: 0 0 2px rgba(0, 0, 0, 0.05);
        }
        
        textview.error-line text {
            background-color: #fff0f0;
            color: #cc0000;
        }
        
        textview.context-view text {
            background-color: #f8f8f8;
            color: #404040;
        }
    """
    load_css_data(css_provider, css_data, "error view CSS")
    
    # Populate errors list
    error_count = 0
    
    # Add invalid options if any
    if hasattr(self, 'invalid_options') and self.invalid_options:
        for option_name, error_message, option_attr in self.invalid_options:
            error_count += 1
            # Create expander row for each invalid option
            expander = Adw.ExpanderRow()
            expander.set_title(f"Invalid Option: {option_name}")
            expander.set_subtitle(f"Option: {option_attr}")
            
            # Add warning icon
            icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic")
            icon.add_css_class("warning")
            expander.add_prefix(icon)
            
            # Error details container
            details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            details_box.set_margin_start(8)
            details_box.set_margin_end(8)
            details_box.set_margin_bottom(8)
            
            # Error message
            error_line_label = Gtk.Label(label="<b>Error Message:</b>")
            error_line_label.set_use_markup(True)
            error_line_label.set_xalign(0)
            error_line_label.set_margin_top(8)
            details_box.append(error_line_label)
            
            # Error message in a monospace text view
            error_text = Gtk.TextView()
            error_text.set_editable(False)
            error_text.set_cursor_visible(False)
            error_text.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
            error_text.add_css_class("error-line")
            error_text.get_buffer().set_text(error_message)
            
            # Apply consistent CSS
            style_context = error_text.get_style_context()
            style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            
            # Add error text view to scrollable container
            error_scroll = Gtk.ScrolledWindow()
            error_scroll.set_min_content_height(80)
            error_scroll.set_child(error_text)
            details_box.append(error_scroll)
            
            # Current value
            current_value_label = Gtk.Label(label="<b>Current Value:</b>")
            current_value_label.set_use_markup(True)
            current_value_label.set_xalign(0)
            current_value_label.set_margin_top(12)
            details_box.append(current_value_label)
            
            # Current value in a monospace text view
            current_value_text = Gtk.TextView()
            current_value_text.set_editable(False)
            current_value_text.set_cursor_visible(False)
            current_value_text.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
            current_value_text.add_css_class("context-view")
            current_value_text.get_buffer().set_text(str(getattr(self, option_attr)))
            
            # Apply consistent CSS
            style_context = current_value_text.get_style_context()
            style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            
            # Add current value text view to scrollable container
            current_value_scroll = Gtk.ScrolledWindow()
            current_value_scroll.set_min_content_height(80)
            current_value_scroll.set_child(current_value_text)
            details_box.append(current_value_scroll)
            
            # Add details to expander
            expander.add_row(details_box)
            
            # Add expander to list
            errors_list.append(expander)
    
    # Extract and classify errors from logs
    if hasattr(self, 'terminal_logs') and apk_path in self.terminal_logs:
        log_text = self.terminal_logs[apk_path]
        error_groups = extract_errors_from_log(log_text)
        
        if error_groups:
            for error in error_groups:
                error_count += 1
                # Create expander row for each error
                expander = Adw.ExpanderRow()
                expander.set_title(f"{error['type']}")
                
                # Check if error cause contains a file path
                if error['cause'].startswith("Path:") or error['cause'].startswith("Dex file:") or error['cause'].startswith("Asset:"):
                    # Highlight file paths in subtitles
                    expander.set_subtitle(f"🗎 {error['cause']}")
                else:
                    expander.set_subtitle(f"{error['cause']}")
                
                # Add icon based on error type
                if "File Not Found" in error['type']:
                    icon = Gtk.Image.new_from_icon_name("document-missing-symbolic")
                    icon.add_css_class("error")
                    expander.add_prefix(icon)
                    expander.add_css_class("error")
                elif "Exception" in error['type'] or "Error" in error['type'] or "Failed" in error['type']:
                    icon = Gtk.Image.new_from_icon_name("dialog-error-symbolic")
                    icon.add_css_class("error")
                    expander.add_prefix(icon)
                    expander.add_css_class("error")
                else:
                    icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic")
                    icon.add_css_class("warning")
                    expander.add_prefix(icon)
                
                # Error details container
                details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                details_box.set_margin_start(8)
                details_box.set_margin_end(8)
                details_box.set_margin_bottom(8)
                
                # Original error line
                error_line_label = Gtk.Label(label="<b>Error Line:</b>")
                error_line_label.set_use_markup(True)
                error_line_label.set_xalign(0)
                error_line_label.set_margin_top(8)
                details_box.append(error_line_label)
                
                # Error line in a monospace text view
                error_text = Gtk.TextView()
                error_text.set_editable(False)
                error_text.set_cursor_visible(False)
                error_text.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
                error_text.add_css_class("error-line")
                error_text.get_buffer().set_text(error['line'])
                
                # Apply consistent CSS
                style_context = error_text.get_style_context()
                style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
                
                # Add error text view to scrollable container
                error_scroll = Gtk.ScrolledWindow()
                error_scroll.set_min_content_height(80)
                error_scroll.set_child(error_text)
                details_box.append(error_scroll)
                
                # Context details section
                if error['details']:
                    context_label = Gtk.Label(label="<b>Context:</b>")
                    context_label.set_use_markup(True)
                    context_label.set_xalign(0)
                    context_label.set_margin_top(12)
                    details_box.append(context_label)
                    
                    # Context in a monospace text view
                    context_text = Gtk.TextView()
                    context_text.set_editable(False)
                    context_text.set_cursor_visible(False)
                    context_text.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
                    context_text.add_css_class("context-view")
                    context_text.get_buffer().set_text("\n".join(error['details']))
                    
                    # Apply consistent CSS
                    style_context = context_text.get_style_context()
                    style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
                    
                    # Add context text view to scrollable container
                    context_scroll = Gtk.ScrolledWindow()
                    context_scroll.set_min_content_height(120)
                    context_scroll.set_vexpand(True)
                    context_scroll.set_child(context_text)
                    details_box.append(context_scroll)
                
                # Add details to expander
                expander.add_row(details_box)
                
                # Add expander to list
                errors_list.append(expander)
    
    # If no errors found, display a message
    if error_count == 0:
        no_errors_row = Gtk.ListBoxRow()
        no_errors_row.set_selectable(False)
        
        no_errors_label = Gtk.Label(label="No specific errors detected in the logs.")
        no_errors_label.set_margin_top(16)
        no_errors_label.set_margin_bottom(16)
        no_errors_label.add_css_class("dim-label")
        no_errors_label.set_halign(Gtk.Align.CENTER)
        
        no_errors_row.set_child(no_errors_label)
        errors_list.append(no_errors_row)
    
    errors_scroll.set_child(errors_list)
    content_area.append(errors_scroll)
    
    # Buttons container
    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    button_box.set_margin_top(16)
    button_box.set_halign(Gtk.Align.END)
    content_area.append(button_box)
    
    # View Full Logs button
    full_logs_button = Gtk.Button(label="View Full Logs")
    full_logs_button.add_css_class("pill")
    
    def on_full_logs_clicked(btn):
        # Show full logs in a dialog
        self.show_full_apk_logs(apk_path)
    
    full_logs_button.connect("clicked", on_full_logs_clicked)
    button_box.append(full_logs_button)
    
    # Export Errors button
    export_button = Gtk.Button(label="Export Errors")
    export_button.add_css_class("pill")
    
    # Export function
    def on_export_clicked(btn):
        # Skip dialog in debug mode
        if os.environ.get('ATL_DEBUG_MODE'):
            print("Debug mode: Skipping export dialog")
            return
        
        # Create file dialog
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Export Errors")
        file_dialog.set_initial_name(f"errors_{apk_name}.txt")
        
        # Add filter for text files
        text_filter = Gtk.FileFilter()
        text_filter.set_name("Text files")
        text_filter.add_mime_type("text/plain")
        filters = Gtk.FilterListModel()
        filters.set_filter(text_filter)
        file_dialog.set_filters(filters)
        
        # Show dialog
        file_dialog.save(dialog, None, on_export_dialog_response)
    
    # Function to handle export dialog response
    def on_export_dialog_response(dialog, result):
        try:
            file = dialog.save_finish(result)
            if file:
                path = file.get_path()
                
                # Format errors for export
                error_content = []
                error_content.append(f"ANDROID TRANSLATION LAYER - ERROR REPORT")
                error_content.append(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                error_content.append(f"APK: {apk_name}")
                error_content.append(f"Status: {self.test_results.get(apk_path, 'Unknown')}")
                error_content.append("")
                
                # Add invalid options
                if hasattr(self, 'invalid_options') and self.invalid_options:
                    error_content.append("=== INVALID OPTIONS ===")
                    for option_name, error_message, option_attr in self.invalid_options:
                        error_content.append(f"Option: {option_name}")
                        error_content.append(f"Error: {error_message}")
                        error_content.append(f"Current Value: {getattr(self, option_attr)}")
                        error_content.append("---")
                    error_content.append("")
                
                # Add error lines
                if hasattr(self, 'terminal_logs') and apk_path in self.terminal_logs:
                    log_text = self.terminal_logs[apk_path]
                    error_lines = []
                    for line in log_text.splitlines():
                        if "error" in line.lower() or "exception" in line.lower() or "failed" in line.lower():
                            error_lines.append(line)
                    
                    if error_lines:
                        error_content.append("=== ERROR LINES ===")
                        for line in error_lines:
                            error_content.append(line)
                        error_content.append("")
                
                # Write to file
                with open(path, 'w') as f:
                    f.write("\n".join(error_content))
                
                # Show confirmation toast
                toast = Adw.Toast.new(f"Errors exported to: {os.path.basename(path)}")
                toast.set_timeout(3)
                self.toast_overlay.add_toast(toast)
        except Exception as e:
            print(f"Error exporting errors: {e}")
            toast = Adw.Toast.new(f"Failed to export errors: {str(e)}")
            toast.set_timeout(3)
            self.toast_overlay.add_toast(toast)
    
    export_button.connect("clicked", on_export_clicked)
    button_box.append(export_button)
    
    # Close button
    close_button = Gtk.Button(label="Close")
    close_button.add_css_class("suggested-action")
    close_button.add_css_class("pill")
    close_button.connect("clicked", lambda btn: dialog.destroy())
    button_box.append(close_button)
    
    # Use standard dialog action areas (optional)
    # dialog.add_button("Close", Gtk.ResponseType.CLOSE)
    # Connect close button
    dialog.connect("response", lambda dialog, response: dialog.destroy())
    
    print("DEBUG: About to show dialog")
    dialog.show()
    
    # Store a reference to prevent garbage collection
    self._error_dialog = dialog
    print("DEBUG: Dialog reference stored and shown")

def show_full_apk_logs(self, apk_path):
    """Show the full logs for an APK in a separate dialog."""
    if not hasattr(self, 'terminal_logs') or apk_path not in self.terminal_logs:
        # Show toast if no logs found
        toast = Adw.Toast.new(f"No logs available for {os.path.basename(apk_path)}")
        self.toast_overlay.add_toast(toast)
        return
    
    log_text = self.terminal_logs[apk_path]
    apk_name = os.path.basename(apk_path)
    
    # Create dialog window
    dialog = Adw.Window()
    dialog.set_title(f"Full Logs: {apk_name}")
    dialog.set_default_size(900, 600)
    dialog.set_transient_for(self)
    
    # Main container with header bar
    header_bar = Adw.HeaderBar()
    header_bar.set_title_widget(Gtk.Label(label=f"Full Logs: {apk_name}"))
    header_bar.add_css_class("flat")
    
    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    main_box.append(header_bar)
    
    # Content area
    content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
    content_box.set_margin_top(16)
    content_box.set_margin_bottom(16)
    content_box.set_margin_start(16)
    content_box.set_margin_end(16)
    content_box.set_vexpand(True)
    main_box.append(content_box)
    
    # Create scrollable text view for logs
    log_view = Gtk.TextView()
    log_view.set_editable(False)
    log_view.set_cursor_visible(False)
    log_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
    log_view.add_css_class("log-view")
    log_view.get_buffer().set_text(log_text)
    
    # CSS for log view
    css_provider = Gtk.CssProvider()
    css_data = """
        textview.log-view {
            background-color: #f8f8f8;
            color: #202020;
            padding: 8px;
            border-radius: 3px;
            font-family: monospace;
            font-size: 12px;
            border: none;
            box-shadow: 0 0 2px rgba(0, 0, 0, 0.05);
        }
    """
    load_css_data(css_provider, css_data, "full logs CSS")
    
    style_context = log_view.get_style_context()
    style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    
    # Scrolled window for logs
    scroll = Gtk.ScrolledWindow()
    scroll.set_vexpand(True)
    scroll.add_css_class("card")
    scroll.set_child(log_view)
    content_box.append(scroll)
    
    # Buttons at the bottom
    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    button_box.set_margin_top(16)
    button_box.set_halign(Gtk.Align.END)
    
    # Copy to clipboard button
    copy_button = Gtk.Button(label="Copy Full Logs")
    copy_button.add_css_class("pill")
    
    # Copy function
    def on_copy_clicked(btn):
        buffer = log_view.get_buffer()
        start_iter = buffer.get_start_iter()
        end_iter = buffer.get_end_iter()
        text_to_copy = buffer.get_text(start_iter, end_iter, False)
        
        # Copy to clipboard using GDK clipboard
        display = self.get_display()
        clipboard = Gdk.Display.get_clipboard(display)
        clipboard.set_text(text_to_copy, -1)
        
        # Show toast for confirmation
        toast = Adw.Toast.new("Full logs copied to clipboard")
        toast.set_timeout(2)
        self.toast_overlay.add_toast(toast)
    
    copy_button.connect("clicked", on_copy_clicked)
    button_box.append(copy_button)
    
    # Close button
    close_button = Gtk.Button(label="Close")
    close_button.add_css_class("suggested-action")
    close_button.add_css_class("pill")
    close_button.connect("clicked", lambda btn: dialog.destroy())
    button_box.append(close_button)
    
    content_box.append(button_box)
    
    # Show dialog
    dialog.set_content(main_box)
    dialog.set_visible(True)
    dialog.present()
    
    # Store a reference to prevent garbage collection
    self._error_dialog = dialog

def on_new_test_clicked(self, button):
    # Hide result view and show welcome view for new test
    self.results_view.set_visible(False)
    self.testing_view.set_visible(False)
    self.welcome_view.set_visible(True)
    
    # Reset variables
    self.apk_files = []
    self.current_apk_index = 0
    self.test_results = {}
    self.current_apk_ready = False
    
    # Reset drag & drop UI state if we came from there
    if hasattr(self, 'button_select_area') and hasattr(self, 'button_drop_area'):
        self.button_select_area.set_visible(True)
        self.button_drop_area.set_visible(False)
        self.button_drop_area.remove_css_class("drop-area-active")
        self.button_drop_area.remove_css_class("fade-in")
        self.button_drop_area.remove_css_class("fade-out")
        self.button_select_area.remove_css_class("fade-in")
        self.button_select_area.remove_css_class("fade-out")
    
    # Update recent APKs list
    from src.views.welcome_view import update_recent_apks_list
    update_recent_apks_list(self)
    
    # Clear terminal and status
    self.terminal_output.get_buffer().set_text("")
    self.apk_value_label.set_text("Not selected yet")
    self.status_value_label.set_text("Waiting")
    self.status_icon.set_from_icon_name("content-loading-symbolic")
    self.command_value_label.set_text("-")

def on_export_clicked(self, button):
    # Skip dialog in debug mode
    if os.environ.get('ATL_DEBUG_MODE'):
        print("Debug mode: Skipping export dialog")
        return
        
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