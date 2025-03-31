#!/bin/bash
set -e

echo "=== ATL GUI AppImage Builder ==="
echo "Preparing AppImage structure..."

# Define variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
APPDIR="$SCRIPT_DIR/AppDir"
APPIMAGETOOL="$SCRIPT_DIR/appimagetool"
OUTPUT_NAME="ATL_GUI-x86_64.AppImage"
APPIMAGE_PATH="$SCRIPT_DIR/$OUTPUT_NAME"

# Download appimagetool if not present
if [ ! -x "$APPIMAGETOOL" ]; then
    echo "Downloading appimagetool..."
    wget -c "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" -O "$APPIMAGETOOL"
    chmod +x "$APPIMAGETOOL"
fi

# Clean AppDir
echo "Cleaning AppDir..."
rm -rf "$APPDIR/usr/share/atl-gui"/*

# Copy application files
echo "Copying application files..."
cp -r "$PROJECT_DIR"/atl_gui.py "$PROJECT_DIR"/src "$PROJECT_DIR"/res "$APPDIR/usr/share/atl-gui/"

# Create desktop file
echo "Creating desktop file..."
cat > "$APPDIR/usr/share/applications/atl-gui.desktop" << EOF
[Desktop Entry]
Type=Application
Name=ATL GUI
Comment=Android Translation Layer GUI Application
Exec=AppRun
Icon=atl-gui
Categories=Development;
Terminal=false
StartupNotify=true
EOF

# Create symlinks
echo "Creating symlinks..."
ln -sf usr/share/applications/atl-gui.desktop "$APPDIR/atl-gui.desktop"
cp "$PROJECT_DIR/res/android_translation_layer.svg" "$APPDIR/usr/share/icons/hicolor/scalable/apps/atl-gui.svg"
ln -sf usr/share/icons/hicolor/scalable/apps/atl-gui.svg "$APPDIR/atl-gui.svg"

# Build the AppImage
echo "Building AppImage..."
ARCH=x86_64 "$APPIMAGETOOL" "$APPDIR" "$APPIMAGE_PATH"

# Make it executable
chmod +x "$APPIMAGE_PATH"

# Install desktop entry using the AppImage's built-in method
echo "Installing desktop entry..."
"$APPIMAGE_PATH" --install

echo "=== AppImage created and installed successfully ==="
echo "You can find the AppImage at: $APPIMAGE_PATH"
echo
echo "The application has been added to your application menu as 'ATL GUI'"
echo "If it doesn't appear immediately, you may need to log out and log back in."
echo
echo "To run the AppImage directly:"
echo "  $APPIMAGE_PATH"
echo
echo "To add to application menu (on another system):"
echo "  $APPIMAGE_PATH --install"
echo
echo "To remove from application menu:"
echo "  $APPIMAGE_PATH --uninstall" 