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
        .accent {
            color: #3584e4;
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
        
        /* Recent APKs styling */
        button.card {
            padding: 0;
            margin: 4px 0;
            border-radius: 8px;
            transition: all 0.2s ease;
            background-color: alpha(@card_bg_color, 0.7);
        }
        
        button.card:hover {
            background-color: mix(@accent_bg_color, @card_bg_color, 0.1);
        }
        
        button.card:active {
            background-color: mix(@accent_bg_color, @card_bg_color, 0.2);
        }
        
        button.circular {
            border-radius: 9999px;
            padding: 8px;
            min-height: 0;
            min-width: 0;
        }
        
        /* Side-by-side layout improvements */
        preferencesgroup.card {
            margin: 4px;
        }
        
        /* Search styling */
        searchbar {
            background: transparent;
            border: none;
            box-shadow: none;
            padding: 0;
            margin: 0;
        }
        
        searchentry {
            border-radius: 16px;
            min-height: 32px;
            background-color: mix(@card_bg_color, @window_bg_color, 0.7);
            border: 1px solid alpha(@borders, 0.5);
            margin: 0;
            padding: 0 8px;
        }
        
        searchentry:focus {
            background-color: @card_bg_color;
            border-color: @accent_bg_color;
        }
        
        /* Combined search container */
        box.search-container {
            background-color: mix(@card_bg_color, @window_bg_color, 0.5);
            border-radius: 8px;
            padding: 4px;
        }
        
        /* Drag and drop area */
        box.drop-area {
            border: 2px dashed alpha(@borders, 0.5);
            border-radius: 8px;
            padding: 24px;
            margin: 8px;
            min-height: 120px;
            min-width: 300px;
            transition: all 0.3s ease;
            background-color: alpha(@card_bg_color, 0.3);
        }
        
        @keyframes fade-in {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes fade-out {
            from { opacity: 1; }
            to { opacity: 0; }
        }
        
        @keyframes pop-in {
            0% { 
                opacity: 0;
                transform: scale(0.8);
            }
            70% {
                transform: scale(1.05);
            }
            100% { 
                opacity: 1;
                transform: scale(1);
            }
        }
        
        @keyframes pop-out {
            0% { 
                opacity: 1;
                transform: scale(1);
            }
            30% {
                opacity: 1;
                transform: scale(1.05);
            }
            100% { 
                opacity: 0;
                transform: scale(0.8);
            }
        }
        
        /* Animation states */
        .fade-in {
            animation: fade-in 0.2s ease forwards;
        }
        
        .fade-out {
            animation: fade-out 0.2s ease forwards;
        }
        
        /* Apply special animations to the drag & drop elements */
        box.drop-area.fade-in {
            animation: pop-in 0.25s ease-out forwards;
        }
        
        box.drop-area.fade-out {
            animation: pop-out 0.2s ease-in forwards;
        }
        
        box.drop-area-active {
            border-color: @accent_bg_color;
            background-color: alpha(@accent_bg_color, 0.1);
            transform: scale(1.02);
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }
        
        box.drop-area image {
            margin-bottom: 12px;
            opacity: 0.7;
            transition: all 0.2s ease;
        }
        
        box.drop-area-active image {
            opacity: 1;
            transform: translateY(-4px);
        }
        
        box.drop-area label {
            transition: all 0.2s ease;
            color: @window_fg_color;
        }
        
        box.drop-area-active label {
            color: @accent_color;
            font-weight: bold;
        }
        
        /* Style for the sublabel in drop area */
        box.drop-area label.caption {
            font-size: 0.85em;
            margin-top: 0;
            opacity: 0.7;
        }
        
        box.drop-area-active label.caption {
            opacity: 0.9;
            font-weight: normal;
        }
    """
    
    # Use the utility function to load CSS data
    load_css_data(css_provider, css_data, "main application CSS")
    
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), 
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    ) 