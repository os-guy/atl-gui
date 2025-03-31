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
    app = AtlGUIApp()
    return app.run(None)

if __name__ == '__main__':
    main() 