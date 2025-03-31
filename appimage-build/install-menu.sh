#!/bin/bash
set -e

echo "=== ATL GUI Menu Installation Tool ==="

# Define variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
APPIMAGE_PATH="$SCRIPT_DIR/ATL_GUI-x86_64.AppImage"
ICON_PATH="$HOME/.local/share/icons/hicolor/scalable/apps/atl-gui.svg"

# Check if AppImage exists
if [ ! -f "$APPIMAGE_PATH" ]; then
    echo "Error: AppImage not found at $APPIMAGE_PATH"
    echo "Please build the AppImage first by running ./build.sh"
    exit 1
fi

# Make sure AppImage is executable
chmod +x "$APPIMAGE_PATH"

# Create directories if they don't exist
echo "Creating directories..."
mkdir -p "$HOME/.local/share/applications" "$HOME/.local/share/icons/hicolor/scalable/apps"

# Create desktop file
echo "Creating desktop entry..."
cat > "$HOME/.local/share/applications/atl-gui.desktop" << EOF
[Desktop Entry]
Type=Application
Name=ATL GUI
Comment=Android Translation Layer GUI Application
Exec=$APPIMAGE_PATH
Icon=$ICON_PATH
Categories=Development;
Terminal=false
StartupNotify=true
EOF

# Copy icon
echo "Installing application icon..."
cp "$PROJECT_DIR/res/android_translation_layer.svg" "$ICON_PATH"

# Try to update desktop database
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo "=== Installation Complete ==="
echo "ATL GUI has been added to your application menu."
echo "If it doesn't appear immediately, you may need to log out and log back in."
echo ""
echo "You can run the application directly with:"
echo "  $APPIMAGE_PATH"
echo ""
echo "To remove the application from your menu, run:"
echo "  $SCRIPT_DIR/remove.sh" 