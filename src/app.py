#!/usr/bin/env python3
import gi
import os
import sys

# Import our display_backend module for Wayland/X11 support
from src.utils import display_backend

# Configure backend before GTK initialization
display_backend.configure_backend()

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw

from src.window import AtlGUIWindow

class AtlGUIApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='org.example.atlgui')
        # Set backend-specific application properties if needed
        self.backend = display_backend.get_current_backend()

    def do_activate(self):
        win = AtlGUIWindow(application=self)
        # Apply backend-specific settings to the window
        display_backend.apply_backend_specific_settings(win)
        win.present()

def main():
    # Check if we should skip launching the app (for debug tools)
    if os.environ.get('ATL_NO_LAUNCH') == '1':
        print("Application launch skipped due to ATL_NO_LAUNCH environment variable.")
        return 0
        
    app = AtlGUIApp()
    return app.run(None)

if __name__ == '__main__':
    main() 