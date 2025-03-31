#!/bin/bash
set -e

echo "=== ATL GUI AppImage Removal Tool ==="

# Define variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPIMAGE_PATH="$SCRIPT_DIR/ATL_GUI-x86_64.AppImage"

# Check if AppImage exists and is executable
if [ -f "$APPIMAGE_PATH" ] && [ -x "$APPIMAGE_PATH" ]; then
    # Remove desktop integration using the AppImage's built-in method
    echo "Removing desktop integration..."
    "$APPIMAGE_PATH" --uninstall
else
    # Manual removal if AppImage doesn't exist or isn't executable
    echo "AppImage not found or not executable. Removing desktop integration manually..."
    rm -f "$HOME/.local/share/applications/atl-gui.desktop"
    rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/atl-gui.svg"
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi

# Check if AppImage exists
if [ -f "$APPIMAGE_PATH" ]; then
    # Ask before removing the AppImage file
    echo -n "Do you want to delete the AppImage file? (y/N): "
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "Removing AppImage file..."
        rm -f "$APPIMAGE_PATH"
        echo "AppImage file removed."
    else
        echo "AppImage file kept."
    fi
fi

echo "=== Removal complete ==="
echo "The application has been removed from your system."
echo "Note: User configuration in ~/.config/atl-gui may still exist."
echo "      Remove it manually if desired with: rm -rf ~/.config/atl-gui" 