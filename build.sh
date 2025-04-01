#!/bin/bash
set -e

echo "=== ATL GUI AppImage Builder ==="
echo "Preparing AppImage structure..."

# Define variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
APPDIR="$SCRIPT_DIR/AppDir"
APPIMAGETOOL="$SCRIPT_DIR/appimagetool"
OUTPUT_NAME="ATL_GUI-x86_64.AppImage"
APPIMAGE_PATH="$SCRIPT_DIR/$OUTPUT_NAME"

# Detect Linux distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VERSION=$VERSION_ID
else
    OS=$(uname -s)
    VERSION=$(uname -r)
fi

echo "Detected OS: $OS $VERSION"

# Download appimagetool if not present
if [ ! -x "$APPIMAGETOOL" ]; then
    echo "Downloading appimagetool..."
    wget -c "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" -O "$APPIMAGETOOL"
    chmod +x "$APPIMAGETOOL"
fi

# Install system dependencies based on distribution
echo "Installing system dependencies..."
case $OS in
    "Arch Linux")
        sudo pacman -Syu --noconfirm \
            python \
            python-pip \
            python-gobject \
            python-cairo \
            gtk4 \
            gobject-introspection \
            cairo \
            pkg-config \
            gcc \
            glib2 \
            android-tools \
            libadwaita
        ;;
    "Ubuntu"|"Debian GNU/Linux")
        sudo apt-get update
        sudo apt-get install -y \
            python3 \
            python3-pip \
            python3-gi \
            python3-gi-cairo \
            gir1.2-gtk-4.0 \
            libgirepository1.0-dev \
            libcairo2-dev \
            pkg-config \
            python3-dev \
            gcc \
            libglib2.0-dev \
            aapt2 \
            libadwaita-1-0
        ;;
    "Fedora")
        sudo dnf update -y
        sudo dnf install -y \
            python3 \
            python3-pip \
            python3-gobject \
            python3-cairo \
            gtk4 \
            gobject-introspection-devel \
            cairo-devel \
            pkgconf-pkg-config \
            gcc \
            glib2-devel \
            android-tools \
            libadwaita
        ;;
    "openSUSE")
        sudo zypper refresh
        sudo zypper install -y \
            python3 \
            python3-pip \
            python3-gobject \
            python3-cairo \
            gtk4 \
            gobject-introspection-devel \
            cairo-devel \
            pkg-config \
            gcc \
            glib2-devel \
            android-tools \
            libadwaita
        ;;
    *)
        echo "Unsupported distribution: $OS"
        echo "Please install the required dependencies manually:"
        echo "- Python 3"
        echo "- Python GObject"
        echo "- GTK4"
        echo "- Android Tools (aapt2)"
        echo "- Other development tools (gcc, pkg-config, etc.)"
        exit 1
        ;;
esac

# Install Python and dependencies in AppDir
echo "Installing Python and dependencies..."
mkdir -p "$APPDIR/usr/bin"
python3 -m venv "$APPDIR/usr"
"$APPDIR/usr/bin/pip" install --upgrade pip
"$APPDIR/usr/bin/pip" install PyGObject distro

# Copy system libraries based on distribution
echo "Copying system libraries..."
mkdir -p "$APPDIR/usr/lib" "$APPDIR/usr/lib/girepository-1.0"

case $OS in
    "Arch Linux")
        cp -L /usr/lib/libadwaita-1.so* "$APPDIR/usr/lib/"
        cp -r /usr/lib/girepository-1.0/* "$APPDIR/usr/lib/girepository-1.0/"
        cp -L /usr/lib/libgtk-4.so* "$APPDIR/usr/lib/"
        cp -L /usr/lib/libglib-2.0.so* "$APPDIR/usr/lib/"
        cp -L /usr/lib/libgobject-2.0.so* "$APPDIR/usr/lib/"
        cp -L /usr/lib/libgio-2.0.so* "$APPDIR/usr/lib/"
        ;;
    "Ubuntu"|"Debian GNU/Linux")
        cp -L /usr/lib/x86_64-linux-gnu/libadwaita-1.so* "$APPDIR/usr/lib/"
        cp -r /usr/lib/girepository-1.0/* "$APPDIR/usr/lib/girepository-1.0/"
        cp -L /usr/lib/x86_64-linux-gnu/libgtk-4.so* "$APPDIR/usr/lib/"
        cp -L /usr/lib/x86_64-linux-gnu/libglib-2.0.so* "$APPDIR/usr/lib/"
        cp -L /usr/lib/x86_64-linux-gnu/libgobject-2.0.so* "$APPDIR/usr/lib/"
        cp -L /usr/lib/x86_64-linux-gnu/libgio-2.0.so* "$APPDIR/usr/lib/"
        ;;
    "Fedora"|"openSUSE")
        cp -L /usr/lib64/libadwaita-1.so* "$APPDIR/usr/lib/"
        cp -r /usr/lib64/girepository-1.0/* "$APPDIR/usr/lib/girepository-1.0/"
        cp -L /usr/lib64/libgtk-4.so* "$APPDIR/usr/lib/"
        cp -L /usr/lib64/libglib-2.0.so* "$APPDIR/usr/lib/"
        cp -L /usr/lib64/libgobject-2.0.so* "$APPDIR/usr/lib/"
        cp -L /usr/lib64/libgio-2.0.so* "$APPDIR/usr/lib/"
        ;;
esac

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