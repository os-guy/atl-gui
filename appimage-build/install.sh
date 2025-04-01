#!/bin/bash

# Colors for pacman-like output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Define variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
APPDIR="$SCRIPT_DIR/AppDir"
APPIMAGETOOL="$SCRIPT_DIR/appimagetool"
OUTPUT_NAME="ATL_GUI-x86_64.AppImage"
APPIMAGE_PATH="$SCRIPT_DIR/$OUTPUT_NAME"

function show_usage() {
    echo -e "${CYAN}:: ${NC}ATL-GUI AppImage Manager"
    echo
    echo -e "Usage: $0 [OPTION]"
    echo -e "  ${GREEN}-S, --sync${NC}         Build and install the AppImage"
    echo -e "  ${RED}-R, --remove${NC}       Remove the AppImage and desktop entries"
    echo -e "  ${BLUE}-Q, --query${NC}        Show information about installed AppImage"
    echo -e "  ${YELLOW}-h, --help${NC}        Show this help message"
    echo
}

function build_appimage() {
    echo -e "${BLUE}::${NC} ${CYAN}Building ATL-GUI AppImage${NC}"
    
    # Clean up previous builds if they exist
    if [ -f "$APPIMAGE_PATH" ]; then
        echo -e "${BLUE}::${NC} Removing previous AppImage"
        rm -f "$APPIMAGE_PATH"
    fi
    
    echo -e "${BLUE}::${NC} Preparing AppImage structure"
    
    # Ensure AppDir structure exists
    mkdir -p "$APPDIR/usr/share/atl-gui"
    mkdir -p "$APPDIR/usr/share/applications"
    mkdir -p "$APPDIR/usr/share/icons/hicolor/scalable/apps"
    
    # Download appimagetool if not present
    if [ ! -x "$APPIMAGETOOL" ]; then
        echo -e "${BLUE}::${NC} Downloading appimagetool"
        wget -c "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" -O "$APPIMAGETOOL"
        chmod +x "$APPIMAGETOOL"
    fi
    
    # Clean AppDir content
    echo -e "${BLUE}::${NC} Cleaning AppDir content"
    rm -rf "$APPDIR/usr/share/atl-gui"/*
    
    # Copy application files
    echo -e "${BLUE}::${NC} Copying application files"
    cp -r "$PROJECT_DIR/atl_gui.py" "$PROJECT_DIR/src" "$PROJECT_DIR/res" "$APPDIR/usr/share/atl-gui/"
    
    # Install Python dependencies
    echo -e "${BLUE}::${NC} Installing Python dependencies"
    mkdir -p "$APPDIR/usr/share/atl-gui/lib"
    pip3 install --target="$APPDIR/usr/share/atl-gui/lib" distro
    
    # Create AppRun script with desktop integration
    echo -e "${BLUE}::${NC} Creating AppRun script"
    cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash

# Find the AppDir - this is where the AppImage is mounted
APPDIR="$(dirname "$(readlink -f "${0}")")"

# Add desktop integration - install desktop file and icon when run
if [ "$1" != "--no-desktop-integration" ]; then
    # Create desktop file in user's applications directory
    DESKTOP_DIR="$HOME/.local/share/applications"
    ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
    
    mkdir -p "$DESKTOP_DIR"
    mkdir -p "$ICON_DIR"
    
    # Get the AppImage path
    APPIMAGE_PATH="$(readlink -f "${APPIMAGE:-$0}")"
    
    # Create desktop file with absolute path
    cat > "$DESKTOP_DIR/atl-gui.desktop" << EOD
[Desktop Entry]
Type=Application
Name=ATL-GUI
Comment=Android Translation Layer GUI Application
Exec=${APPIMAGE_PATH}
Icon=$ICON_DIR/atl-gui.png
Categories=Development;
Terminal=false
StartupNotify=true
EOD
    
    # Copy icon
    if [ -f "$APPDIR/usr/share/atl-gui/res/android_translation_layer.png" ]; then
        cp "$APPDIR/usr/share/atl-gui/res/android_translation_layer.png" "$ICON_DIR/atl-gui.png"
    elif [ -f "$APPDIR/usr/share/icons/hicolor/scalable/apps/atl-gui.png" ]; then
        cp "$APPDIR/usr/share/icons/hicolor/scalable/apps/atl-gui.png" "$ICON_DIR/atl-gui.png"
    fi
    
    # Update desktop database
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

# Export Python path to include our app directory
export PYTHONPATH="$APPDIR/usr/share/atl-gui:$APPDIR/usr/share/atl-gui/lib:$PYTHONPATH"

# Launch the application with Python 3
exec python3 "$APPDIR/usr/share/atl-gui/atl_gui.py" "$@"
EOF
    chmod +x "$APPDIR/AppRun"
    
    # Create desktop file template (used within the AppImage)
    echo -e "${BLUE}::${NC} Creating desktop file"
    cat > "$APPDIR/usr/share/applications/atl-gui.desktop" << EOF
[Desktop Entry]
Type=Application
Name=ATL-GUI
Comment=Android Translation Layer GUI Application
Exec=AppRun
Icon=atl-gui
Categories=Development;
Terminal=false
StartupNotify=true
EOF
    
    # Create symlinks and copy the icon to the AppDir
    echo -e "${BLUE}::${NC} Creating symlinks"
    ln -sf usr/share/applications/atl-gui.desktop "$APPDIR/atl-gui.desktop"
    cp "$PROJECT_DIR/res/android_translation_layer.png" "$APPDIR/usr/share/icons/hicolor/scalable/apps/atl-gui.png"
    ln -sf usr/share/icons/hicolor/scalable/apps/atl-gui.png "$APPDIR/atl-gui.png"
    
    # Build the AppImage
    echo -e "${BLUE}::${NC} Building AppImage"
    ARCH=x86_64 "$APPIMAGETOOL" "$APPDIR" "$APPIMAGE_PATH"
    chmod +x "$APPIMAGE_PATH"
    
    # Install desktop file and icon immediately
    echo -e "${BLUE}::${NC} Installing desktop entry"
    DESKTOP_DIR="$HOME/.local/share/applications"
    ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
    
    mkdir -p "$DESKTOP_DIR" "$ICON_DIR"
    
    # Create desktop file with absolute path
    cat > "$DESKTOP_DIR/atl-gui.desktop" << EOF
[Desktop Entry]
Type=Application
Name=ATL-GUI
Comment=Android Translation Layer GUI Application
Exec=$APPIMAGE_PATH
Icon=$ICON_DIR/atl-gui.png
Categories=Development;
Terminal=false
StartupNotify=true
EOF
    
    # Copy icon
    cp "$PROJECT_DIR/res/android_translation_layer.png" "$ICON_DIR/atl-gui.png"
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
    
    echo -e "${GREEN}:: ${NC}ATL-GUI installation completed successfully"
    echo -e "   AppImage path: ${YELLOW}$APPIMAGE_PATH${NC}"
    echo -e "   Desktop entry: ${YELLOW}$DESKTOP_DIR/atl-gui.desktop${NC}"
}

function remove_appimage() {
    echo -e "${BLUE}::${NC} ${RED}Removing ATL-GUI AppImage${NC}"
    
    # Define paths
    DESKTOP_FILE="$HOME/.local/share/applications/atl-gui.desktop"
    ICON_FILE="$HOME/.local/share/icons/hicolor/scalable/apps/atl-gui.png"
    
    # Remove AppImage
    if [ -f "$APPIMAGE_PATH" ]; then
        echo -e "${BLUE}::${NC} Removing AppImage file"
        rm -f "$APPIMAGE_PATH"
    else
        echo -e "${YELLOW}::${NC} AppImage not found at $APPIMAGE_PATH"
    fi
    
    # Remove desktop entry
    if [ -f "$DESKTOP_FILE" ]; then
        echo -e "${BLUE}::${NC} Removing desktop entry"
        rm -f "$DESKTOP_FILE"
    else
        # Try to find any related desktop files
        FOUND_FILES=$(find "$HOME/.local/share/applications" -name "*atl*gui*.desktop" 2>/dev/null || true)
        if [ -n "$FOUND_FILES" ]; then
            echo -e "${BLUE}::${NC} Removing desktop files"
            rm -f $FOUND_FILES
        else
            echo -e "${YELLOW}::${NC} No desktop entries found"
        fi
    fi
    
    # Remove icon
    if [ -f "$ICON_FILE" ]; then
        echo -e "${BLUE}::${NC} Removing icon"
        rm -f "$ICON_FILE"
    else
        # Try to find any related icon files
        FOUND_ICONS=$(find "$HOME/.local/share/icons" -name "*atl*gui*.png" 2>/dev/null || true)
        if [ -n "$FOUND_ICONS" ]; then
            echo -e "${BLUE}::${NC} Removing icon files"
            rm -f $FOUND_ICONS
        else
            echo -e "${YELLOW}::${NC} No icon files found"
        fi
    fi
    
    # Update desktop database
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
    
    echo -e "${GREEN}:: ${NC}ATL-GUI removal completed successfully"
}

function query_appimage() {
    echo -e "${BLUE}::${NC} ${CYAN}ATL-GUI AppImage Information${NC}"
    
    if [ -f "$APPIMAGE_PATH" ]; then
        APPIMAGE_SIZE=$(du -h "$APPIMAGE_PATH" | cut -f1)
        APPIMAGE_DATE=$(date -r "$APPIMAGE_PATH" "+%Y-%m-%d %H:%M:%S")
        echo -e "${GREEN}Location:${NC} $APPIMAGE_PATH"
        echo -e "${GREEN}Size:${NC} $APPIMAGE_SIZE"
        echo -e "${GREEN}Created:${NC} $APPIMAGE_DATE"
        echo -e "${GREEN}Status:${NC} Installed"
    else
        echo -e "${RED}AppImage not installed${NC}"
        echo -e "${YELLOW}Use '$0 -S' to install${NC}"
        return 1
    fi
    
    DESKTOP_FILE="$HOME/.local/share/applications/atl-gui.desktop"
    if [ -f "$DESKTOP_FILE" ]; then
        echo -e "${GREEN}Desktop Entry:${NC} Installed at $DESKTOP_FILE"
    else
        echo -e "${YELLOW}Desktop Entry:${NC} Not installed"
    fi
    
    ICON_FILE="$HOME/.local/share/icons/hicolor/scalable/apps/atl-gui.png"
    if [ -f "$ICON_FILE" ]; then
        echo -e "${GREEN}Icon:${NC} Installed at $ICON_FILE"
    else
        echo -e "${YELLOW}Icon:${NC} Not installed"
    fi
    
    return 0
}

function interactive_menu() {
    echo -e "${CYAN}:: ${NC}ATL-GUI AppImage Manager"
    echo
    echo -e "${GREEN}1)${NC} Build and install ATL-GUI AppImage"
    echo -e "${RED}2)${NC} Remove ATL-GUI AppImage"
    echo -e "${BLUE}3)${NC} Show ATL-GUI AppImage information"
    echo -e "${YELLOW}4)${NC} Exit"
    echo
    read -p "Enter your choice [1-4]: " choice
    
    case $choice in
        1)
            build_appimage
            ;;
        2)
            remove_appimage
            ;;
        3)
            query_appimage
            ;;
        4)
            echo -e "${GREEN}Exiting...${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option. Please try again.${NC}"
            interactive_menu
            ;;
    esac
}

# Parse command line arguments
if [ $# -eq 0 ]; then
    interactive_menu
    exit 0
fi

case "$1" in
    -S|--sync)
        build_appimage
        ;;
    -R|--remove)
        remove_appimage
        ;;
    -Q|--query)
        query_appimage
        ;;
    -h|--help|*)
        show_usage
        ;;
esac 