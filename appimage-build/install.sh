#!/bin/bash

# Colors for pacman-like output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Define variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
APPDIR="$SCRIPT_DIR/AppDir"
APPIMAGETOOL="$SCRIPT_DIR/appimagetool"
OUTPUT_NAME="ATL_GUI-x86_64.AppImage"
APPIMAGE_PATH="$SCRIPT_DIR/$OUTPUT_NAME"

# XDG environment variables - respect user config
XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
XDG_CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"

# Application specific directories
APP_CONFIG_DIR="$XDG_CONFIG_HOME/atl-gui"
APP_DATA_DIR="$XDG_DATA_HOME/atl-gui"
APP_DESKTOP_DIR="$XDG_DATA_HOME/applications"
APP_ICON_DIR="$XDG_DATA_HOME/icons/hicolor/scalable/apps"
APP_CACHE_DIR="$XDG_CACHE_HOME/atl-gui"

# Progress display function
show_progress() {
    local message="$1"
    local progress="$2"
    local width=50
    local num_filled=$((progress * width / 100))
    local num_empty=$((width - num_filled))
    
    # Create progress bar
    local bar="["
    for ((i=0; i<num_filled; i++)); do
        bar+="="
    done
    if [ $num_filled -lt $width ]; then
        bar+=">"
        num_empty=$((num_empty - 1))
    fi
    for ((i=0; i<num_empty; i++)); do
        bar+=" "
    done
    bar+="]"
    
    # Print progress (use \r to stay on the same line)
    printf "\r${BLUE}::${NC} ${message} ${bar} ${progress}%% "
}

# Download function with progress indication
download_with_progress() {
    local url="$1"
    local output_file="$2"
    local description="$3"
    
    if command -v wget >/dev/null 2>&1; then
        # Use wget with progress
        wget -q --show-progress --progress=bar:force --no-check-certificate "$url" -O "$output_file"
    elif command -v curl >/dev/null 2>&1; then
        # Use curl with progress
        curl -L --progress-bar -o "$output_file" "$url"
    else
        echo -e "${RED}::${NC} Neither wget nor curl is available. Cannot download $description."
        return 1
    fi
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}::${NC} Failed to download $description."
        return 1
    fi
    
    return 0
}

function show_usage() {
    echo -e "${CYAN}:: ${BOLD}ATL-GUI AppImage Manager${NC}"
    echo
    echo -e "Usage: $0 [OPTION]"
    echo -e "  ${GREEN}-S, --sync${NC}         Build and install the AppImage"
    echo -e "  ${RED}-R, --remove${NC}       Remove the AppImage and desktop entries"
    echo -e "  ${BLUE}-Q, --query${NC}        Show information about installed AppImage"
    echo -e "  ${YELLOW}-h, --help${NC}        Show this help message"
    echo
}

function create_directories() {
    echo -e "${BLUE}::${NC} Ensuring all directories exist"
    
    # Create XDG config directories
    mkdir -p "$APP_CONFIG_DIR"
    mkdir -p "$APP_DATA_DIR"
    mkdir -p "$APP_DESKTOP_DIR"
    mkdir -p "$APP_ICON_DIR"
    mkdir -p "$APP_CACHE_DIR"
    
    # Create AppDir structure
    mkdir -p "$APPDIR/usr/share/atl-gui"
    mkdir -p "$APPDIR/usr/share/applications"
    mkdir -p "$APPDIR/usr/share/icons/hicolor/scalable/apps"
    
    echo -e "   ${GREEN}✓${NC} Directories created successfully"
}

function ensure_appimagetool() {
    # Check if appimagetool exists and is executable
    if [ ! -x "$APPIMAGETOOL" ]; then
        echo -e "${BLUE}::${NC} Downloading appimagetool"
        
        # URL for the latest continuous build
        APPIMAGETOOL_URL="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
        
        # Download appimagetool with progress
        if download_with_progress "$APPIMAGETOOL_URL" "$APPIMAGETOOL" "appimagetool"; then
            # Make the tool executable
            chmod +x "$APPIMAGETOOL"
            echo -e "${GREEN}::${NC} appimagetool downloaded successfully"
        else
            echo -e "${RED}::${NC} Failed to download appimagetool. Please check your internet connection and try again."
            exit 1
        fi
    else
        echo -e "${GREEN}::${NC} appimagetool is already available"
    fi
}

function build_appimage() {
    echo -e "${BLUE}::${NC} ${CYAN}${BOLD}Building ATL-GUI AppImage${NC}"
    
    # Ensure directories exist
    create_directories
    
    # Ensure appimagetool is available
    ensure_appimagetool
    
    # Clean up previous builds if they exist
    if [ -f "$APPIMAGE_PATH" ]; then
        echo -e "${BLUE}::${NC} Removing previous AppImage"
        rm -f "$APPIMAGE_PATH"
    fi
    
    echo -e "${BLUE}::${NC} Building AppImage..."
    
    # Clean AppDir content
    rm -rf "$APPDIR/usr/share/atl-gui"/*
    show_progress "Building AppImage" 10
    
    # Copy application files
    cp -r "$PROJECT_DIR/atl_gui.py" "$PROJECT_DIR/src" "$PROJECT_DIR/res" "$APPDIR/usr/share/atl-gui/"
    show_progress "Building AppImage" 30
    
    # Install Python dependencies
    mkdir -p "$APPDIR/usr/share/atl-gui/lib"
    pip3 install --target="$APPDIR/usr/share/atl-gui/lib" distro
    show_progress "Building AppImage" 40
    
    # Create AppRun script with desktop integration and XDG support
    cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash

# Set up colors for visual feedback
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Find the AppDir - this is where the AppImage is mounted
APPDIR="$(dirname "$(readlink -f "${0}")")"

# Define XDG paths - respect user environment variables
XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
XDG_CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"

# Application specific directories
APP_CONFIG_DIR="$XDG_CONFIG_HOME/atl-gui"
APP_DATA_DIR="$XDG_DATA_HOME/atl-gui"
APP_DESKTOP_DIR="$XDG_DATA_HOME/applications"
APP_ICON_DIR="$XDG_DATA_HOME/icons/hicolor/scalable/apps"
APP_CACHE_DIR="$XDG_CACHE_HOME/atl-gui"

# Log function - logs to console and to log file if available
log() {
    local level="$1"
    local message="$2"
    local color="$BLUE"
    
    case "$level" in
        "INFO") color="$GREEN" ;;
        "WARN") color="$YELLOW" ;;
        "ERROR") color="$RED" ;;
    esac
    
    echo -e "${color}[${level}]${NC} $message"
    
    # Log to file if directory exists
    if [ -d "$APP_CONFIG_DIR" ]; then
        mkdir -p "$APP_CONFIG_DIR/logs"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] $message" >> "$APP_CONFIG_DIR/logs/appimage.log"
    fi
}

# Ensure all directories exist
log "INFO" "Ensuring all required directories exist"
mkdir -p "$APP_CONFIG_DIR"
mkdir -p "$APP_DATA_DIR"
mkdir -p "$APP_DESKTOP_DIR"
mkdir -p "$APP_ICON_DIR"
mkdir -p "$APP_CACHE_DIR"

# Add desktop integration - install desktop file and icon when run
if [ "$1" != "--no-desktop-integration" ]; then
    log "INFO" "Setting up desktop integration"
    
    # Get the AppImage path
    APPIMAGE_PATH="$(readlink -f "${APPIMAGE:-$0}")"
    log "INFO" "Using AppImage path: $APPIMAGE_PATH"
    
    # Create desktop file with absolute path
    log "INFO" "Creating desktop entry at $APP_DESKTOP_DIR/atl-gui.desktop"
    cat > "$APP_DESKTOP_DIR/atl-gui.desktop" << EOD
[Desktop Entry]
Type=Application
Name=ATL-GUI
Comment=Android Translation Layer GUI Application
Exec=${APPIMAGE_PATH}
Icon=$APP_ICON_DIR/atl-gui.png
Categories=Development;
Terminal=false
StartupNotify=true
EOD
    
    # Copy icon
    if [ -f "$APPDIR/usr/share/atl-gui/res/android_translation_layer.png" ]; then
        log "INFO" "Installing icon from $APPDIR/usr/share/atl-gui/res/android_translation_layer.png"
        cp "$APPDIR/usr/share/atl-gui/res/android_translation_layer.png" "$APP_ICON_DIR/atl-gui.png"
    elif [ -f "$APPDIR/usr/share/icons/hicolor/scalable/apps/atl-gui.png" ]; then
        log "INFO" "Installing icon from $APPDIR/usr/share/icons/hicolor/scalable/apps/atl-gui.png"
        cp "$APPDIR/usr/share/icons/hicolor/scalable/apps/atl-gui.png" "$APP_ICON_DIR/atl-gui.png"
    else
        log "WARN" "Could not find application icon"
    fi
    
    # Update desktop database
    log "INFO" "Updating desktop database"
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$APP_DESKTOP_DIR" 2>/dev/null || true
    else
        log "WARN" "update-desktop-database command not found, skipping"
    fi
    
    # Save installation path for future reference
    log "INFO" "Saving AppImage location to $APP_CONFIG_DIR/appimage_path"
    echo "$APPIMAGE_PATH" > "$APP_CONFIG_DIR/appimage_path"
fi

# Export Python path to include our app directory
log "INFO" "Setting up Python environment"
export PYTHONPATH="$APPDIR/usr/share/atl-gui:$APPDIR/usr/share/atl-gui/lib:$PYTHONPATH"

# Save environment variables for debugging
if [ -d "$APP_CONFIG_DIR" ]; then
    log "INFO" "Saving environment variables for debugging"
    (
        echo "APPDIR=$APPDIR"
        echo "XDG_CONFIG_HOME=$XDG_CONFIG_HOME"
        echo "XDG_DATA_HOME=$XDG_DATA_HOME" 
        echo "XDG_CACHE_HOME=$XDG_CACHE_HOME"
        echo "PYTHONPATH=$PYTHONPATH"
        echo "PATH=$PATH"
    ) > "$APP_CONFIG_DIR/last_run_env.txt"
fi

# Launch the application with Python 3
log "INFO" "Starting ATL-GUI application"
exec python3 "$APPDIR/usr/share/atl-gui/atl_gui.py" "$@"
EOF
    chmod +x "$APPDIR/AppRun"
    show_progress "Building AppImage" 60
    
    # Create desktop file template (used within the AppImage)
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
    ln -sf usr/share/applications/atl-gui.desktop "$APPDIR/atl-gui.desktop"
    cp "$PROJECT_DIR/res/android_translation_layer.png" "$APPDIR/usr/share/icons/hicolor/scalable/apps/atl-gui.png"
    ln -sf usr/share/icons/hicolor/scalable/apps/atl-gui.png "$APPDIR/atl-gui.png"
    show_progress "Building AppImage" 70
    
    # Build the AppImage
    ARCH=x86_64 "$APPIMAGETOOL" -q "$APPDIR" "$APPIMAGE_PATH" 2>/dev/null
    chmod +x "$APPIMAGE_PATH"
    show_progress "Building AppImage" 90
    
    # Install desktop file and icon immediately
    # Create desktop file with absolute path
    cat > "$APP_DESKTOP_DIR/atl-gui.desktop" << EOF
[Desktop Entry]
Type=Application
Name=ATL-GUI
Comment=Android Translation Layer GUI Application
Exec=$APPIMAGE_PATH
Icon=$APP_ICON_DIR/atl-gui.png
Categories=Development;
Terminal=false
StartupNotify=true
EOF
    
    # Copy icon
    cp "$PROJECT_DIR/res/android_translation_layer.png" "$APP_ICON_DIR/atl-gui.png"
    update-desktop-database "$APP_DESKTOP_DIR" 2>/dev/null || true
    
    # Save installation path for future reference
    echo "$APPIMAGE_PATH" > "$APP_CONFIG_DIR/appimage_path"
    
    show_progress "Building AppImage" 100
    # Add a newline to finish the progress bar
    echo -e "\n\n${GREEN}:: ${BOLD}ATL-GUI installation completed successfully${NC}"
    echo -e "   ${BOLD}AppImage path:${NC} ${YELLOW}$APPIMAGE_PATH${NC}"
    echo -e "   ${BOLD}Desktop entry:${NC} ${YELLOW}$APP_DESKTOP_DIR/atl-gui.desktop${NC}"
    echo -e "   ${BOLD}Configuration:${NC} ${YELLOW}$APP_CONFIG_DIR${NC}"
    echo -e "   ${BOLD}Data directory:${NC} ${YELLOW}$APP_DATA_DIR${NC}"
}

function remove_appimage() {
    echo -e "${BLUE}::${NC} ${RED}${BOLD}Removing ATL-GUI AppImage${NC}"
    
    # Check for saved installation path
    if [ -f "$APP_CONFIG_DIR/appimage_path" ]; then
        SAVED_PATH=$(cat "$APP_CONFIG_DIR/appimage_path")
        if [ -f "$SAVED_PATH" ]; then
            echo -e "${BLUE}::${NC} Removing AppImage from saved path: $SAVED_PATH"
            rm -f "$SAVED_PATH"
        fi
    fi
    
    # Remove AppImage
    if [ -f "$APPIMAGE_PATH" ]; then
        echo -e "${BLUE}::${NC} Removing AppImage file"
        rm -f "$APPIMAGE_PATH"
    else
        echo -e "${YELLOW}::${NC} AppImage not found at $APPIMAGE_PATH"
    fi
    
    # Remove desktop entry
    if [ -f "$APP_DESKTOP_DIR/atl-gui.desktop" ]; then
        echo -e "${BLUE}::${NC} Removing desktop entry"
        rm -f "$APP_DESKTOP_DIR/atl-gui.desktop"
    else
        # Try to find any related desktop files
        FOUND_FILES=$(find "$XDG_DATA_HOME/applications" -name "*atl*gui*.desktop" 2>/dev/null || true)
        if [ -n "$FOUND_FILES" ]; then
            echo -e "${BLUE}::${NC} Removing desktop files"
            rm -f $FOUND_FILES
        else
            echo -e "${YELLOW}::${NC} No desktop entries found"
        fi
    fi
    
    # Remove icon
    if [ -f "$APP_ICON_DIR/atl-gui.png" ]; then
        echo -e "${BLUE}::${NC} Removing icon"
        rm -f "$APP_ICON_DIR/atl-gui.png"
    else
        # Try to find any related icon files
        FOUND_ICONS=$(find "$XDG_DATA_HOME/icons" -name "*atl*gui*.png" 2>/dev/null || true)
        if [ -n "$FOUND_ICONS" ]; then
            echo -e "${BLUE}::${NC} Removing icon files"
            rm -f $FOUND_ICONS
        else
            echo -e "${YELLOW}::${NC} No icon files found"
        fi
    fi
    
    # Ask if user wants to remove config and data
    echo
    read -p "$(echo -e "${YELLOW}?${NC} Remove configuration and data files? [y/N] ")" confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}::${NC} Removing configuration directory"
        rm -rf "$APP_CONFIG_DIR"
        echo -e "${BLUE}::${NC} Removing data directory"
        rm -rf "$APP_DATA_DIR"
        echo -e "${BLUE}::${NC} Removing cache directory"
        rm -rf "$APP_CACHE_DIR"
    else
        echo -e "${BLUE}::${NC} Keeping configuration and data files"
    fi
    
    # Update desktop database
    update-desktop-database "$APP_DESKTOP_DIR" 2>/dev/null || true
    
    echo -e "${GREEN}:: ${BOLD}ATL-GUI removal completed successfully${NC}"
}

function query_appimage() {
    echo -e "${BLUE}::${NC} ${CYAN}${BOLD}ATL-GUI AppImage Information${NC}"
    
    # Check for saved installation path first
    INSTALLED_PATH=""
    if [ -f "$APP_CONFIG_DIR/appimage_path" ]; then
        SAVED_PATH=$(cat "$APP_CONFIG_DIR/appimage_path")
        if [ -f "$SAVED_PATH" ]; then
            INSTALLED_PATH="$SAVED_PATH"
        fi
    fi
    
    # If no saved path or file doesn't exist, check the default location
    if [ -z "$INSTALLED_PATH" ] && [ -f "$APPIMAGE_PATH" ]; then
        INSTALLED_PATH="$APPIMAGE_PATH"
    fi
    
    if [ -n "$INSTALLED_PATH" ] && [ -f "$INSTALLED_PATH" ]; then
        APPIMAGE_SIZE=$(du -h "$INSTALLED_PATH" | cut -f1)
        APPIMAGE_DATE=$(date -r "$INSTALLED_PATH" "+%Y-%m-%d %H:%M:%S")
        echo -e "${GREEN}${BOLD}Location:${NC} $INSTALLED_PATH"
        echo -e "${GREEN}${BOLD}Size:${NC} $APPIMAGE_SIZE"
        echo -e "${GREEN}${BOLD}Created:${NC} $APPIMAGE_DATE"
        echo -e "${GREEN}${BOLD}Status:${NC} Installed"
        
        # Check permissions
        if [ -x "$INSTALLED_PATH" ]; then
            echo -e "${GREEN}${BOLD}Permissions:${NC} Executable (${YELLOW}$(stat -c "%a" "$INSTALLED_PATH")${NC})"
        else
            echo -e "${RED}${BOLD}Permissions:${NC} Not executable (${YELLOW}$(stat -c "%a" "$INSTALLED_PATH")${NC})"
            echo -e "${YELLOW}::${NC} Consider running: chmod +x \"$INSTALLED_PATH\""
        fi
    else
        echo -e "${RED}${BOLD}AppImage not installed${NC}"
        echo -e "${YELLOW}Use '$0 -S' to install${NC}"
        return 1
    fi
    
    # Check for desktop entry
    if [ -f "$APP_DESKTOP_DIR/atl-gui.desktop" ]; then
        echo -e "${GREEN}${BOLD}Desktop Entry:${NC} Installed at $APP_DESKTOP_DIR/atl-gui.desktop"
    else
        echo -e "${YELLOW}${BOLD}Desktop Entry:${NC} Not installed"
    fi
    
    # Check for icon
    if [ -f "$APP_ICON_DIR/atl-gui.png" ]; then
        echo -e "${GREEN}${BOLD}Icon:${NC} Installed at $APP_ICON_DIR/atl-gui.png"
    else
        echo -e "${YELLOW}${BOLD}Icon:${NC} Not installed"
    fi
    
    # Check configuration
    if [ -d "$APP_CONFIG_DIR" ]; then
        CONFIG_SIZE=$(du -sh "$APP_CONFIG_DIR" 2>/dev/null | cut -f1)
        echo -e "${GREEN}${BOLD}Config:${NC} $APP_CONFIG_DIR (${YELLOW}$CONFIG_SIZE${NC})"
    else
        echo -e "${YELLOW}${BOLD}Config:${NC} Not found at $APP_CONFIG_DIR"
    fi
    
    # Check for data directory
    if [ -d "$APP_DATA_DIR" ]; then
        DATA_SIZE=$(du -sh "$APP_DATA_DIR" 2>/dev/null | cut -f1)
        echo -e "${GREEN}${BOLD}Data:${NC} $APP_DATA_DIR (${YELLOW}$DATA_SIZE${NC})"
    else
        echo -e "${YELLOW}${BOLD}Data:${NC} Not found at $APP_DATA_DIR"
    fi
    
    # Additional info section
    echo -e "\n${CYAN}${BOLD}System Information:${NC}"
    echo -e "${GREEN}${BOLD}XDG Config Home:${NC} $XDG_CONFIG_HOME"
    echo -e "${GREEN}${BOLD}XDG Data Home:${NC} $XDG_DATA_HOME"
    
    return 0
}

function interactive_menu() {
    clear
    echo -e "${CYAN}${BOLD}==== ATL-GUI AppImage Manager ====${NC}"
    echo
    echo -e "1) ${GREEN}Build and install ATL-GUI AppImage${NC}"
    echo -e "2) ${RED}Remove ATL-GUI AppImage${NC}"
    echo -e "3) ${BLUE}Show ATL-GUI AppImage information${NC}"
    echo -e "4) ${YELLOW}Exit${NC}"
    echo
    read -p "$(echo -e "${CYAN}?${NC} Select an option (1-4): ")" choice
    
    case $choice in
        1)
            clear
            build_appimage
            ;;
        2)
            clear
            remove_appimage
            ;;
        3)
            clear
            query_appimage
            ;;
        4)
            echo -e "${YELLOW}Exiting...${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option${NC}"
            ;;
    esac
    
    echo
    read -p "$(echo -e "${CYAN}?${NC} Press enter to return to menu")"
    interactive_menu
}

# No arguments, show interactive menu
if [ $# -eq 0 ]; then
    interactive_menu
    exit 0
fi

# Parse arguments
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
    -h|--help)
        show_usage
        ;;
    *)
        echo -e "${RED}Invalid option: $1${NC}"
        show_usage
        exit 1
        ;;
esac

exit 0
