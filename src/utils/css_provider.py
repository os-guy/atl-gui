import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

def load_css_data(css_provider, css_data, name="CSS"):
    """
    Utility function to load CSS data in a way that's compatible with different GTK versions
    
    Args:
        css_provider: Gtk.CssProvider instance to load the data into
        css_data: CSS string data to load
        name: Name for error messages (e.g., "terminal CSS")
    """
    # Try different method signatures for load_from_data
    encoded_data = css_data.encode('utf-8')
    try:
        # First try the 2-argument version
        css_provider.load_from_data(encoded_data)
    except TypeError:
        try:
            # Try the 3-argument version (data, length)
            css_provider.load_from_data(encoded_data, len(encoded_data))
        except (TypeError, ValueError):
            try:
                # Try the version that just takes a string
                css_provider.load_from_data(css_data)
            except:
                # If all else fails, let the user know
                print(f"Warning: Could not load {name}. The UI might not look as intended.")


def setup_css(window):
    """Set up the application's CSS styling"""
    # Create the CSS provider
    css_provider = Gtk.CssProvider()
    
    # Get the current backend
    from src.utils.display_backend import get_current_backend
    backend = get_current_backend()
    
    # Define our base CSS
    css_data = """
    /* Base styles for all backends */
    window {
        background-color: @window_bg_color;
    }
    
    .main-title {
        font-size: 24px;
        font-weight: bold;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    
    .section-title {
        font-size: 18px;
        font-weight: bold;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    
    .header-bar {
        min-height: 48px;
        padding: 0;
    }
    
    .welcome-box {
        background-color: alpha(@accent_bg_color, 0.1);
        border-radius: 8px;
        padding: 20px;
    }
    
    .welcome-message {
        font-size: 16px;
        margin-bottom: 10px;
    }
    
    .input-box {
        background-color: alpha(@accent_bg_color, 0.08);
        border-radius: 8px;
        padding: 16px;
    }
    
    .files-list {
        margin-top: 20px;
    }
    
    .apk-name {
        font-weight: bold;
    }
    
    .system-info-box {
        background-color: alpha(@accent_bg_color, 0.05);
        border-radius: 8px;
        padding: 10px;
        margin-top: 10px;
    }
    
    .system-info-item {
        font-family: monospace;
        font-size: 14px;
    }
    
    .terminal-output {
        font-family: monospace;
        font-size: 14px;
        background-color: rgba(0, 0, 0, 0.8);
        color: #ffffff;
        border-radius: 5px;
        padding: 10px;
    }
    
    .test-buttons button {
        margin-right: 10px;
    }
    
    .results-row {
        padding: 10px;
        border-bottom: 1px solid alpha(@borders, 0.5);
    }
    
    .results-row:last-child {
        border-bottom: none;
    }
    
    .working-app {
        color: #2ecc71;
    }
    
    .not-working-app {
        color: #e74c3c;
    }
    
    .result-status {
        font-weight: bold;
        padding: 5px 10px;
        border-radius: 4px;
    }
    
    .result-status.working {
        background-color: rgba(46, 204, 113, 0.1);
        color: #2ecc71;
    }
    
    .result-status.not-working {
        background-color: rgba(231, 76, 60, 0.1);
        color: #e74c3c;
    }
    
    .settings-button-box button {
        margin-right: 8px;
    }
    
    .file-path {
        font-family: monospace;
        font-size: 13px;
        opacity: 0.8;
        margin-top: 5px;
    }
    
    .custom-entry {
        min-height: 36px;
        padding: 0 10px;
    }
    
    .command-box {
        background-color: rgba(0, 0, 0, 0.05);
        border-radius: 5px;
        padding: 10px;
        font-family: monospace;
    }
    
    .script-path-box {
        margin-top: 10px;
        padding: 5px;
    }
    
    .log-entry {
        border-radius: 4px;
        margin: 5px 0;
        padding: 5px;
    }
    
    .log-entry.error {
        background-color: rgba(231, 76, 60, 0.1);
    }
    
    .log-entry.warning {
        background-color: rgba(241, 196, 15, 0.1);
    }
    
    .log-entry.info {
        background-color: rgba(52, 152, 219, 0.1);
    }
    
    .log-entry.attention {
        background-color: rgba(155, 89, 182, 0.1);
    }
    
    .bold-text {
        font-weight: bold;
    }
    
    .error-output {
        font-family: monospace;
        font-size: 14px;
        background-color: rgba(231, 76, 60, 0.1);
        color: #e74c3c;
        border-radius: 5px;
        padding: 10px;
        margin-top: 10px;
    }
    
    .scrolled-window.terminal {
        margin-top: 15px;
        margin-bottom: 15px;
    }
    
    .category-box {
        margin-top: 10px;
        margin-bottom: 10px;
    }
    
    .category-name {
        font-weight: bold;
        font-size: 14px;
        margin-bottom: 5px;
    }
    
    .error-pattern {
        font-family: monospace;
        background-color: rgba(0, 0, 0, 0.03);
        border-left: 3px solid @accent_color;
        padding: 5px 10px;
        margin: 5px 0;
    }
    """
    
    # Add Wayland-specific styles if needed
    if backend == 'wayland':
        wayland_css = """
        /* Wayland-specific styles */
        .window-handle {
            /* Properties for better window handling in Wayland */
            margin: 0;
            padding: 0;
        }
        
        /* Improve touch handling for Wayland's better touch support */
        button {
            min-height: 36px;
            min-width: 36px;
        }
        
        /* Better HiDPI support common in Wayland environments */
        .icon-button {
            min-width: 24px;
            min-height: 24px;
            padding: 6px;
        }
        
        /* Smooth window corners for Wayland compositors that support it */
        window.rounded {
            border-radius: 12px;
        }
        """
        css_data += wayland_css
    
    # Use the utility function to load CSS data
    load_css_data(css_provider, css_data, "main application CSS")
    
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), 
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    ) 