#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw

from src.window import AtlGUIWindow

class AtlGUIApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='org.example.atlgui')

    def do_activate(self):
        win = AtlGUIWindow(application=self)
        win.present()

def main():
    # Check if we should skip launching the app (for debug tools)
    import os
    if os.environ.get('ATL_NO_LAUNCH') == '1':
        print("Application launch skipped due to ATL_NO_LAUNCH environment variable.")
        return 0
        
    app = AtlGUIApp()
    return app.run(None)

if __name__ == '__main__':
    main() 