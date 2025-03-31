#!/bin/bash
set -e

echo "=== ATL GUI AppImage Removal Tool ==="

# Define variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPIMAGE_PATH="$SCRIPT_DIR/ATL_GUI-x86_64.AppImage"
DESKTOP_FILE="$HOME/.local/share/applications/atl-gui.desktop"
ICON_FILE="$HOME/.local/share/icons/hicolor/scalable/apps/atl-gui.svg"

# Remove desktop integration files
echo "Removing desktop integration..."
rm -f "$DESKTOP_FILE"
rm -f "$ICON_FILE"

# Try to update desktop database
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

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
else
    echo "AppImage not found at $APPIMAGE_PATH"
fi

# Remove configuration marker
rm -f "$HOME/.config/atl-gui/desktop-integrated"

echo "=== Removal complete ==="
echo "The application has been removed from your system."
echo "Note: User configuration in ~/.config/atl-gui may still exist."
echo "      Remove it manually if desired with: rm -rf ~/.config/atl-gui" 