#!/bin/bash
set -e

echo "=== ATL GUI Menu Installation Tool ==="

# Define variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPIMAGE_PATH="$SCRIPT_DIR/ATL_GUI-x86_64.AppImage"

# Check if AppImage exists
if [ ! -f "$APPIMAGE_PATH" ]; then
    echo "Error: AppImage not found at $APPIMAGE_PATH"
    echo "Please build the AppImage first by running ./build.sh"
    exit 1
fi

# Make sure AppImage is executable
chmod +x "$APPIMAGE_PATH"

# Use the AppImage's built-in installation method
echo "Installing menu entry..."
"$APPIMAGE_PATH" --install

echo "=== Installation Complete ==="
echo "ATL GUI has been added to your application menu."
echo "If it doesn't appear immediately, you may need to log out and log back in."
echo ""
echo "You can run the application directly with:"
echo "  $APPIMAGE_PATH"
echo ""
echo "To remove the application from your menu, run:"
echo "  $APPIMAGE_PATH --uninstall" 