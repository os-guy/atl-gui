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
    apk_path = button.apk_path
    apk_name = os.path.basename(apk_path)
    
    if hasattr(self, 'terminal_logs') and apk_path in self.terminal_logs:
        log_text = self.terminal_logs[apk_path]
        error_groups = extract_errors_from_log(log_text)
        
        # Create and show the error dialog
        dialog = Adw.Window()
        dialog.set_title(f"Errors: {apk_name}")
        dialog.set_default_size(800, 600)
        dialog.set_transient_for(self)
        
        # Main container with header bar
        header_bar = Adw.HeaderBar()
        header_bar.set_title_widget(Gtk.Label(label=f"Errors for {apk_name}"))
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
        
        content_box.append(info_box)
        
        # Search box
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        search_box.set_margin_bottom(8)
        
        # Create search entry
        search_entry = Gtk.SearchEntry()
        search_entry.set_placeholder_text("Search in errors...")
        search_entry.set_hexpand(True)
        search_box.append(search_entry)
        
        # Add case sensitive checkbox
        case_check = Gtk.CheckButton()
        case_check.set_label("Case sensitive")
        search_box.append(case_check)
        
        content_box.append(search_box)
        
        # Store search matches reference
        search_matches = []
        
        # Define consistent CSS for text views
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
        
        # Errors list container
        errors_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        errors_list_box.set_vexpand(True)
        
        # Create a scrolled window for the errors list
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.add_css_class("card")
        
        # Check if we have any errors
        if error_groups:
            # Create expandable rows for each error
            errors_list = Gtk.ListBox()
            errors_list.set_selection_mode(Gtk.SelectionMode.NONE)
            errors_list.add_css_class("boxed-list")
            
            # Add each error as an expandable row
            for error in error_groups:
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
            
            # Add list to scroll container
            scroll.set_child(errors_list)
            errors_list_box.append(scroll)
            
        else:
            # No errors message
            no_errors_label = Gtk.Label(label="No specific errors detected in the logs.")
            no_errors_label.set_margin_top(24)
            no_errors_label.set_margin_bottom(24)
            no_errors_label.add_css_class("dim-label")
            errors_list_box.append(no_errors_label)
            
            # Add full logs button
            full_logs_button = Gtk.Button(label="View Full Logs")
            full_logs_button.add_css_class("pill")
            full_logs_button.set_halign(Gtk.Align.CENTER)
            
            def on_full_logs_clicked(btn):
                # Show full logs in a dialog
                self.show_full_apk_logs(apk_path)
            
            full_logs_button.connect("clicked", on_full_logs_clicked)
            errors_list_box.append(full_logs_button)
        
        content_box.append(errors_list_box)
        
        # Buttons at the bottom
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_margin_top(16)
        button_box.set_halign(Gtk.Align.END)
        
        # View full logs button
        full_logs_button = Gtk.Button(label="View Full Logs")
        full_logs_button.add_css_class("pill")
        
        def on_full_logs_clicked(btn):
            # Show full logs in a dialog
            self.show_full_apk_logs(apk_path)
        
        full_logs_button.connect("clicked", on_full_logs_clicked)
        button_box.append(full_logs_button)
        
        # Copy to clipboard button
        copy_button = Gtk.Button(label="Copy Errors")
        copy_button.add_css_class("pill")
        
        # Copy function
        def on_copy_clicked(btn):
            # Format errors for clipboard
            error_text = []
            for error in error_groups:
                error_text.append(f"Error Type: {error['type']}")
                error_text.append(f"Cause: {error['cause']}")
                error_text.append(f"Line: {error['line']}")
                if error['details']:
                    error_text.append("Context:")
                    for detail in error['details']:
                        error_text.append(f"  {detail}")
                error_text.append("---")
            
            # Join all errors
            text_to_copy = "\n".join(error_text)
            if not text_to_copy:
                text_to_copy = "No specific errors detected in the logs."
            
            # Copy to clipboard using GDK clipboard
            display = self.get_display()
            clipboard = Gdk.Display.get_clipboard(display)
            clipboard.set_text(text_to_copy, -1)
            
            # Show toast for confirmation
            toast = Adw.Toast.new("Errors copied to clipboard")
            toast.set_timeout(2)
            self.toast_overlay.add_toast(toast)
        
        copy_button.connect("clicked", on_copy_clicked)
        button_box.append(copy_button)
        
        # Export Errors button
        export_button = Gtk.Button(label="Export Errors")
        export_button.add_css_class("pill")
        
        # Export function
        def on_export_clicked(btn):
            # Create file dialog for saving errors
            file_dialog = Gtk.FileDialog()
            file_dialog.set_title("Export Errors")
            file_dialog.set_initial_name(f"{apk_name}_errors.txt")
            
            # Filtre ekle
            text_filter = Gtk.FileFilter()
            text_filter.set_name("Text Files")
            text_filter.add_mime_type("text/plain")
            
            # Show dialog
            file_dialog.save(self, None, lambda dialog, result: export_errors_response(dialog, result))
        
        # Export dialog response handler
        def export_errors_response(dialog, result):
            try:
                file = dialog.save_finish(result)
                if file:
                    path = file.get_path()
                    export_errors_to_file(path)
                    
                    # Show success notification
                    toast = Adw.Toast.new(f"Errors exported to: {path}")
                    toast.set_timeout(5)
                    self.toast_overlay.add_toast(toast)
            except Exception as e:
                # Error notification
                print(f"Error saving errors: {e}")
                toast = Adw.Toast.new(f"Could not export errors: {str(e)}")
                self.toast_overlay.add_toast(toast)
        
        # Function to write errors to file
        def export_errors_to_file(file_path):
            try:
                with open(file_path, 'w') as f:
                    # Write header
                    f.write(f"===== ERRORS FOR {apk_name} =====\n")
                    f.write(f"Status: {self.test_results.get(apk_path, 'Unknown')}\n")
                    f.write(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    # Write organized errors
                    if error_groups:
                        for i, error in enumerate(error_groups, 1):
                            f.write(f"ERROR #{i}: {error['type']}\n")
                            f.write(f"CAUSE: {error['cause']}\n")
                            f.write(f"LINE: {error['line']}\n")
                            
                            if error['details']:
                                f.write("CONTEXT:\n")
                                for detail in error['details']:
                                    f.write(f"  {detail}\n")
                            
                            f.write("\n" + "-" * 80 + "\n\n")
                    else:
                        f.write("No specific errors detected in the logs.\n")
            except Exception as e:
                print(f"Error writing to file: {e}")
                toast = Adw.Toast.new(f"Error saving to file: {str(e)}")
                self.toast_overlay.add_toast(toast)
        
        export_button.connect("clicked", on_export_clicked)
        button_box.append(export_button)
        
        # Close button
        close_button = Gtk.Button(label="Close")
        close_button.add_css_class("suggested-action")
        close_button.add_css_class("pill")
        close_button.connect("clicked", lambda btn: dialog.destroy())
        button_box.append(close_button)
        
        content_box.append(button_box)
        
        # Search function
        def perform_search(text, case_sensitive=False):
            nonlocal search_matches
            
            # Reset matches
            search_matches = []
            
            # First, make all rows visible again
            if error_groups:
                for i in range(len(error_groups)):
                    row = errors_list.get_row_at_index(i)
                    if row:
                        row.set_visible(True)
            
            if not text or not text.strip():
                return
            
            # Directly search in the error_groups data structure instead of traversing widgets
            if error_groups:
                for i, error in enumerate(error_groups):
                    # Check error type
                    title_match = False
                    error_type = error.get('type', '')
                    if error_type:
                        if case_sensitive and text in error_type:
                            title_match = True
                        elif not case_sensitive and text.lower() in error_type.lower():
                            title_match = True
                    
                    # Check error cause
                    subtitle_match = False
                    error_cause = error.get('cause', '')
                    if error_cause:
                        if case_sensitive and text in error_cause:
                            subtitle_match = True
                        elif not case_sensitive and text.lower() in error_cause.lower():
                            subtitle_match = True
                    
                    # Get the row
                    row = errors_list.get_row_at_index(i)
                    if row:
                        # If no match, hide the row
                        if not title_match and not subtitle_match:
                            row.set_visible(False)
                        else:
                            # Add to matches for reference
                            search_matches.append({"type": "header", "row": row})
            
        # Hook up event handlers
        def on_search_changed(entry):
            # Immediately perform search on every text change
            text = entry.get_text()
            perform_search(text, case_check.get_active())
            
        def on_case_toggled(button):
            # Re-perform the search when case sensitivity is toggled
            text = search_entry.get_text()
            perform_search(text, button.get_active())
        
        # Connect signals
        search_entry.connect("search-changed", on_search_changed)
        case_check.connect("toggled", on_case_toggled)
        
        # Show dialog
        dialog.set_content(main_box)
        dialog.present()
    else:
        # Show toast if no logs found
        toast = Adw.Toast.new(f"No logs available for {apk_name}")
        self.toast_overlay.add_toast(toast)

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
    dialog.present()

def on_new_test_clicked(self, button):
    # Yeni bir test için başlangıç sayfasına dön
    self.welcome_view.set_visible(True)
    self.results_view.set_visible(False)
    self.testing_view.set_visible(False)
    
    # Değişkenleri sıfırla
    self.current_apk_index = 0
    self.apk_files = []
    self.test_results = {}

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