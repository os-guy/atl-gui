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
rm -rf "$APPDIR/usr/bin/aapt2" "$APPDIR/usr/bin/aapt" 2>/dev/null || true

# Copy application files
echo "Copying application files..."
cp -r "$PROJECT_DIR"/atl_gui.py "$PROJECT_DIR"/src "$PROJECT_DIR"/res "$APPDIR/usr/share/atl-gui/"

# Install Python dependencies
echo "Installing Python dependencies..."
mkdir -p "$APPDIR/usr/share/atl-gui/lib"
pip3 install --target="$APPDIR/usr/share/atl-gui/lib" distro

# Create AppRun script with desktop integration
echo "Creating AppRun script with desktop integration..."
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash

# Find the AppDir - this is where the AppImage is mounted
APPDIR="$(dirname "$(readlink -f "${0}")")"

# Export Python path to include our app directory
export PYTHONPATH="$APPDIR/usr/share/atl-gui:$APPDIR/usr/share/atl-gui/lib:$PYTHONPATH"

# Launch the application with Python 3
exec python3 "$APPDIR/usr/share/atl-gui/atl_gui.py" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# Create desktop file template
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

# Install desktop file and icon
echo "Installing desktop entry..."
mkdir -p "$HOME/.local/share/applications" "$HOME/.local/share/icons/hicolor/scalable/apps"

# Create desktop file with absolute path - use $HOME to make it portable
DESKTOP_CONTENT=$(cat "$APPDIR/usr/share/applications/atl-gui.desktop" | sed "s|Exec=AppRun|Exec=$APPIMAGE_PATH|g")
echo "$DESKTOP_CONTENT" > "$HOME/.local/share/applications/atl-gui.desktop"

# Copy icon
cp "$PROJECT_DIR/res/android_translation_layer.svg" "$HOME/.local/share/icons/hicolor/scalable/apps/atl-gui.svg"

# Update desktop file to use absolute path for icon - use $HOME to make it portable
ICON_PATH="$HOME/.local/share/icons/hicolor/scalable/apps/atl-gui.svg"
sed -i "s|Icon=atl-gui|Icon=$ICON_PATH|g" "$HOME/.local/share/applications/atl-gui.desktop"

# Try to update desktop database
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo "=== AppImage created and installed successfully ==="
echo "You can find the AppImage at: $APPIMAGE_PATH"
echo
echo "The application has been added to your application menu as 'ATL GUI'"
echo "If it doesn't appear immediately, you may need to log out and log back in."
echo
echo "To run the AppImage directly:"
echo "  $APPIMAGE_PATH"
echo
echo "To remove the application:"
echo "  $SCRIPT_DIR/remove.sh" 