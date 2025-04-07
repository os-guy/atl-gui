#!/usr/bin/env python3
"""
Display Backend Utilities for ATL GUI
Provides functions to set up and configure display backends (X11/Wayland)
"""
import os
import gi
import sys
import subprocess
import platform

gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Gdk

def detect_wayland():
    """
    Detect if Wayland is available as the current display server
    Returns True if Wayland is detected, False otherwise
    """
    # Check if WAYLAND_DISPLAY environment variable is set
    if 'WAYLAND_DISPLAY' in os.environ:
        return True
    
    # Check if XDG_SESSION_TYPE is set to wayland
    if os.environ.get('XDG_SESSION_TYPE') == 'wayland':
        return True
    
    # Additional check for current display server
    try:
        # Try to detect through loginctl
        result = subprocess.run(
            ['loginctl', 'show-session', '$(loginctl | grep $(whoami) | awk \'{print $1}\')', '-p', 'Type'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True
        )
        if 'wayland' in result.stdout.lower():
            return True
    except Exception:
        pass
    
    return False

def get_display_server_details():
    """
    Get detailed information about the user's display server environment
    
    Returns:
        dict: Dictionary containing display server details
    """
    details = {
        'backend': 'unknown',
        'compositor': 'unknown',
        'session_type': os.environ.get('XDG_SESSION_TYPE', 'unknown'),
        'wayland_display': os.environ.get('WAYLAND_DISPLAY', 'not set'),
        'display': os.environ.get('DISPLAY', 'not set'),
        'gdk_backend': os.environ.get('GDK_BACKEND', 'not set'),
        'gtk_version': '.'.join(str(x) for x in (Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())),
        'is_wayland': detect_wayland(),
        'platform': platform.system(),
        'desktop_session': os.environ.get('XDG_CURRENT_DESKTOP', 'unknown')
    }
    
    # If GDK_BACKEND is manually set, prioritize that for the active backend
    if details['gdk_backend'] != 'not set':
        details['backend'] = details['gdk_backend']
    
    # Try to get compositor info for Wayland
    if details['is_wayland']:
        try:
            # Check for common Wayland compositors
            if 'GNOME' in details['desktop_session']:
                details['compositor'] = 'Mutter (GNOME)'
            elif 'KDE' in details['desktop_session']:
                details['compositor'] = 'KWin (KDE Plasma)'
            elif 'Hyprland' in details['desktop_session']:
                details['compositor'] = 'Hyprland'
            elif 'sway' in details['desktop_session'].lower():
                details['compositor'] = 'Sway'
                
            # Try to detect Wayland compositor through available commands
            for compositor in ['sway', 'hyprctl', 'weston', 'wayfire', 'river']:
                try:
                    subprocess.run(['which', compositor], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if details['compositor'] == 'unknown':
                        details['compositor'] = compositor
                    break
                except subprocess.CalledProcessError:
                    pass
        except Exception:
            pass
    else:
        # For X11, try to detect window manager
        try:
            if 'GNOME' in details['desktop_session']:
                details['compositor'] = 'Mutter (GNOME)'
            elif 'KDE' in details['desktop_session']:
                details['compositor'] = 'KWin (KDE Plasma)'
            elif 'XFCE' in details['desktop_session']:
                details['compositor'] = 'Xfwm (XFCE)'
            elif 'i3' in details['desktop_session'].lower():
                details['compositor'] = 'i3'
        except Exception:
            pass
    
    # Only check display if GDK_BACKEND isn't already set
    if details['backend'] == 'unknown':
        # Get active display backend from GTK
        display = Gdk.Display.get_default()
        if display:
            display_name = display.get_name()
            details['display_name'] = display_name
            
            if 'wayland' in display_name.lower():
                details['backend'] = 'wayland'
            elif ':' in display_name: # X11 displays are typically like ":0"
                details['backend'] = 'x11'
    elif not 'display_name' in details:
        # Still try to get the display name even if we already know the backend
        try:
            display = Gdk.Display.get_default()
            if display:
                details['display_name'] = display.get_name()
        except:
            details['display_name'] = 'unknown'
    
    return details

def configure_backend(force_wayland=False, force_x11=False):
    """
    Configure the display backend based on preferences and availability
    
    Args:
        force_wayland: Force using Wayland backend if available
        force_x11: Force using X11 backend
        
    Returns:
        str: The selected backend name ('wayland', 'x11', or 'unknown')
    """
    # Check if specific backend is already forced through environment
    # But allow overriding it with command-line arguments
    if 'GDK_BACKEND' in os.environ and not force_wayland and not force_x11:
        backend = os.environ['GDK_BACKEND']
        print(f"Using pre-configured backend from environment: {backend}")
        return backend

    # Apply forced backends if requested
    if force_wayland and force_x11:
        print("Warning: Both Wayland and X11 backends requested, defaulting to system preference")
    elif force_wayland:
        # Explicitly override the GDK_BACKEND even if it was already set
        os.environ['GDK_BACKEND'] = 'wayland'
        print("Forcing Wayland backend")
        return 'wayland'
    elif force_x11:
        # Explicitly override the GDK_BACKEND even if it was already set
        os.environ['GDK_BACKEND'] = 'x11'
        print("Forcing X11 backend")
        return 'x11'
    
    # Auto-detect and use the active display server
    is_wayland = detect_wayland()
    
    if is_wayland:
        # When Wayland is detected, explicitly set it
        os.environ['GDK_BACKEND'] = 'wayland'
        print("Detected and using Wayland backend")
        return 'wayland'
    else:
        # Default to X11 if Wayland not detected
        os.environ['GDK_BACKEND'] = 'x11'
        print("Detected and using X11 backend")
        return 'x11'

def get_current_backend():
    """
    Get the current active backend being used
    
    Returns:
        str: Current backend name ('wayland', 'x11', or 'unknown')
    """
    # Check the environment variable first
    backend = os.environ.get('GDK_BACKEND')
    if backend:
        return backend
    
    # Try to identify from the current display
    display = Gdk.Display.get_default()
    if display:
        # Get display name or type information
        display_name = display.get_name()
        if 'wayland' in display_name:
            return 'wayland'
        elif 'x11' in display_name or ':' in display_name:
            return 'x11'
    
    # Fallback detection based on environment
    if detect_wayland():
        return 'wayland'
    
    return 'unknown'

def print_display_info():
    """
    Print detailed information about the user's display environment
    Useful for debugging display server issues
    """
    details = get_display_server_details()
    
    print("\n=== Display Server Information ===")
    print(f"Active Backend: {details['backend']}")
    print(f"Display Server: {details['session_type']}")
    print(f"Compositor/WM: {details['compositor']}")
    print(f"Desktop Environment: {details['desktop_session']}")
    print(f"Display Name: {details.get('display_name', 'unknown')}")
    print("\n=== Environment Variables ===")
    print(f"WAYLAND_DISPLAY: {details['wayland_display']}")
    print(f"DISPLAY: {details['display']}")
    print(f"GDK_BACKEND: {details['gdk_backend']}")
    print(f"XDG_SESSION_TYPE: {details['session_type']}")
    print("\n=== Platform Info ===")
    print(f"Platform: {details['platform']}")
    print(f"GTK Version: {details.get('gtk_version', 'unknown')}")
    print("==============================\n")
    
    return details

def apply_wayland_specific_settings(window):
    """
    Apply Wayland-specific settings and optimizations to a window
    
    Args:
        window: A Gtk.Window instance to apply settings to
    """
    backend = get_current_backend()
    if backend != 'wayland':
        return

    # Enable Wayland-specific features
    
    # Get the display
    display = window.get_display()
    surface = window.get_surface()
    
    # Set fractional scaling if supported and we have a surface
    if surface and display:
        try:
            # Different display classes might have different methods
            if hasattr(display, 'get_monitor_at_window'):
                monitor = display.get_monitor_at_window(surface)
            elif hasattr(display, 'get_monitor_at_surface'):
                monitor = display.get_monitor_at_surface(surface)
            else:
                # Fallback to first monitor
                monitor = display.get_monitor(0)
                
                # Enable smoother scaling if available on this monitor
                if monitor and hasattr(monitor, 'set_scale_factor'):
                    # For future: Custom scaling options
                    pass
        except Exception as e:
            print(f"Warning: Could not apply Wayland scaling settings: {e}")
    
    # Request client-side decorations explicitly if available
    if hasattr(window, 'set_hide_titlebar_when_maximized'):
        window.set_hide_titlebar_when_maximized(False)

def apply_backend_specific_settings(window):
    """
    Apply appropriate settings based on the active backend
    
    Args:
        window: A Gtk.Window instance to apply settings to
    """
    backend = get_current_backend()
    
    if backend == 'wayland':
        apply_wayland_specific_settings(window)
    elif backend == 'x11':
        # Apply any X11 specific settings if needed
        pass 