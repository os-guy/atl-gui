import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

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