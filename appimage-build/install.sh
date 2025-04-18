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
    echo -e "  ${GREEN}-F, --fallback${NC}     Use fallback installation method (no AppImage)"
    echo -e "  ${GREEN}-M, --menu${NC}         Force-create menu entries (if app doesn't appear in menu)"
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
            if [ $? -ne 0 ]; then
                echo -e "${RED}::${NC} Failed to make appimagetool executable. Check your permissions."
                exit 1
            fi
            echo -e "${GREEN}::${NC} appimagetool downloaded successfully"
        else
            echo -e "${RED}::${NC} Failed to download appimagetool. Please check your internet connection and try again."
            exit 1
        fi
    else
        echo -e "${GREEN}::${NC} appimagetool is already available"
    fi
    
    # Verify that appimagetool is working correctly
    echo -e "${BLUE}::${NC} Verifying appimagetool"
    if ! "$APPIMAGETOOL" --version &>/dev/null; then
        echo -e "${RED}::${NC} appimagetool is not working correctly"
        echo -e "${YELLOW}::${NC} Trying to fix permissions and file format"
        
        # Try to fix permissions
        chmod +x "$APPIMAGETOOL"
        
        # Try to make it executable if it's not
        if [[ $(head -c 4 "$APPIMAGETOOL") != $'\x7fELF' ]]; then
            echo -e "${RED}::${NC} appimagetool is not a valid executable"
            echo -e "${YELLOW}::${NC} Downloading again..."
            rm -f "$APPIMAGETOOL"
            ensure_appimagetool
            return
        fi
        
        # Try one more time
        if ! "$APPIMAGETOOL" --version &>/dev/null; then
            echo -e "${RED}::${NC} appimagetool is still not working"
            echo -e "${YELLOW}::${NC} Please download manually from https://github.com/AppImage/AppImageKit/releases"
            echo -e "${YELLOW}::${NC} and save it to $APPIMAGETOOL"
            exit 1
        fi
    fi
    
    echo -e "${GREEN}::${NC} appimagetool verified successfully"
}

function create_desktop_entry() {
    local app_path="$1"
    local app_name="${2:-ATL-GUI}"
    local app_comment="${3:-Android Translation Layer GUI Application}"
    
    echo -e "${BLUE}::${NC} Creating desktop entry"
    
    # Create both system and user desktop entries for better visibility
    # 1. User desktop entry (standard location)
    mkdir -p "$APP_DESKTOP_DIR"
    
    # Create desktop file
    echo -e "${BLUE}::${NC} Creating desktop file at $APP_DESKTOP_DIR/atl-gui.desktop"
    cat > "$APP_DESKTOP_DIR/atl-gui.desktop" << EOF
[Desktop Entry]
Type=Application
Name=$app_name
GenericName=Android Translation Layer
Comment=$app_comment
Exec=$app_path
Icon=$APP_ICON_DIR/atl-gui.png
Categories=Development;Utility;
Keywords=Android;Translation;ATL;
Terminal=false
StartupNotify=true
StartupWMClass=atl-gui
EOF
    
    # Make desktop file executable (not required but good practice)
    chmod +x "$APP_DESKTOP_DIR/atl-gui.desktop"
    
    # 2. Create a second desktop entry in ~/.local/share/applications (more standard location)
    mkdir -p "$HOME/.local/share/applications"
    if [ "$APP_DESKTOP_DIR" != "$HOME/.local/share/applications" ]; then
        echo -e "${BLUE}::${NC} Creating desktop file at $HOME/.local/share/applications/atl-gui.desktop"
        cp "$APP_DESKTOP_DIR/atl-gui.desktop" "$HOME/.local/share/applications/atl-gui.desktop"
    fi
    
    # Copy icon to multiple locations for better detection
    mkdir -p "$APP_ICON_DIR"
    
    # Standard XDG icon location
    mkdir -p "$HOME/.local/share/icons/hicolor/256x256/apps"
    
    if [ -f "$PROJECT_DIR/res/android_translation_layer.png" ]; then
        echo -e "${BLUE}::${NC} Installing icon to multiple locations for better visibility"
        cp "$PROJECT_DIR/res/android_translation_layer.png" "$APP_ICON_DIR/atl-gui.png"
        cp "$PROJECT_DIR/res/android_translation_layer.png" "$HOME/.local/share/icons/hicolor/256x256/apps/atl-gui.png"
    else
        echo -e "${YELLOW}::${NC} Icon file not found, desktop entry might not display correctly"
    fi
    
    # Update desktop database with additional output
    echo -e "${BLUE}::${NC} Updating desktop database"
    if command -v update-desktop-database &> /dev/null; then
        echo -e "${BLUE}::${NC} Running update-desktop-database"
        update-desktop-database "$HOME/.local/share/applications" || true
        if [ "$APP_DESKTOP_DIR" != "$HOME/.local/share/applications" ]; then
            update-desktop-database "$APP_DESKTOP_DIR" || true
        fi
        echo -e "${GREEN}::${NC} Desktop database updated"
    else
        echo -e "${YELLOW}::${NC} update-desktop-database command not found, skipping"
    fi
    
    # Update icon cache
    if command -v gtk-update-icon-cache &> /dev/null; then
        echo -e "${BLUE}::${NC} Updating icon cache"
        gtk-update-icon-cache -f "$HOME/.local/share/icons/hicolor" || true
        echo -e "${GREEN}::${NC} Icon cache updated"
    fi
    
    echo -e "${GREEN}::${NC} Desktop entry created successfully"
    
    # Create a notification if possible
    if command -v notify-send &> /dev/null; then
        notify-send "ATL-GUI Installed" "The application has been installed and should appear in your application menu." --icon="$APP_ICON_DIR/atl-gui.png" || true
    fi
    
    # Provide additional help
    echo -e "\n${BLUE}::${NC} Desktop entry created. Here are some troubleshooting tips if the app doesn't appear in your menu:"
    echo -e "   ${YELLOW}1. Try running: ${NC}xdg-desktop-menu forceupdate"
    echo -e "   ${YELLOW}2. Log out and log back in${NC}"
    echo -e "   ${YELLOW}3. You can always start the app from the command line:${NC}"
    
    if [[ "$app_path" == *"AppImage"* ]]; then
        echo -e "      ${CYAN}$app_path${NC}"
    else
        echo -e "      ${CYAN}atl-gui${NC}"
    fi
    
    # Explicitly install the desktop file using xdg-desktop-menu
    if command -v xdg-desktop-menu &> /dev/null; then
        echo -e "${BLUE}::${NC} Registering desktop entry with xdg-desktop-menu"
        xdg-desktop-menu install --novendor "$APP_DESKTOP_DIR/atl-gui.desktop" 2>/dev/null || true
        xdg-desktop-menu forceupdate 2>/dev/null || true
        echo -e "${GREEN}::${NC} Desktop menu entry registered"
    fi
    
    # Create a direct link on the desktop if requested
    echo -e "${YELLOW}?${NC} Would you like to create a desktop shortcut? [y/N] "
    read -p "" CREATE_DESKTOP_SHORTCUT
    if [[ "$CREATE_DESKTOP_SHORTCUT" =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}::${NC} Creating desktop shortcut"
        cp "$APP_DESKTOP_DIR/atl-gui.desktop" "$HOME/Desktop/atl-gui.desktop" 2>/dev/null || true
        chmod +x "$HOME/Desktop/atl-gui.desktop" 2>/dev/null || true
        echo -e "${GREEN}::${NC} Desktop shortcut created"
    fi
}

# Function to ensure a file has executable permissions
function ensure_executable() {
    local file_path="$1"
    local description="${2:-file}"
    
    if [ -f "$file_path" ]; then
        if [ ! -x "$file_path" ]; then
            echo -e "${YELLOW}::${NC} Making $description executable"
            chmod +x "$file_path"
            if [ $? -ne 0 ]; then
                echo -e "${RED}::${NC} Failed to make $description executable"
                echo -e "${YELLOW}::${NC} Try running: sudo chmod +x \"$file_path\""
                return 1
            fi
        fi
    else
        echo -e "${RED}::${NC} $description not found: $file_path"
        return 1
    fi
    
    return 0
}

function check_path() {
    # Check if ~/.local/bin is in PATH
    if ! echo "$PATH" | tr ':' '\n' | grep -q "$HOME/.local/bin"; then
        echo -e "\n${YELLOW}::${NC} ${BOLD}~/.local/bin is not in your PATH${NC}"
        echo -e "${YELLOW}::${NC} This is needed for the fallback installation and other user-installed programs"
        echo -e "${YELLOW}::${NC} Would you like to add it to your PATH? [Y/n] "
        read -p "" ADD_TO_PATH
        
        if [[ ! "$ADD_TO_PATH" =~ ^[Nn]$ ]]; then
            echo -e "${BLUE}::${NC} Adding ~/.local/bin to PATH"
            
            # Determine shell configuration file
            SHELL_CONFIG=""
            if [ -n "$BASH_VERSION" ]; then
                if [ -f "$HOME/.bashrc" ]; then
                    SHELL_CONFIG="$HOME/.bashrc"
                elif [ -f "$HOME/.bash_profile" ]; then
                    SHELL_CONFIG="$HOME/.bash_profile"
                fi
            elif [ -n "$ZSH_VERSION" ]; then
                SHELL_CONFIG="$HOME/.zshrc"
            else
                # Default to .profile for other shells
                SHELL_CONFIG="$HOME/.profile"
            fi
            
            if [ -n "$SHELL_CONFIG" ]; then
                echo -e "\n# Add ~/.local/bin to PATH for ATL-GUI and other user programs" >> "$SHELL_CONFIG"
                echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_CONFIG"
                echo -e "${GREEN}::${NC} Added to $SHELL_CONFIG"
                echo -e "${YELLOW}::${NC} You need to run: source $SHELL_CONFIG"
                echo -e "${YELLOW}::${NC} Or log out and log back in for the changes to take effect"
            else
                echo -e "${RED}::${NC} Could not determine shell configuration file"
                echo -e "${YELLOW}::${NC} Please add this to your shell configuration file manually:"
                echo -e "${CYAN}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
            fi
        else
            echo -e "${YELLOW}::${NC} Not adding to PATH. You'll need to run the app with full path:"
            echo -e "${CYAN}$HOME/.local/bin/atl-gui${NC}"
        fi
    fi
}

function build_appimage() {
    echo -e "${BLUE}::${NC} ${CYAN}${BOLD}Building ATL-GUI AppImage${NC}"
    
    # Check for required commands
    local MISSING_DEPS=()
    for cmd in python3 pip3; do
        if ! command -v $cmd &> /dev/null; then
            MISSING_DEPS+=($cmd)
        fi
    done
    
    if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
        echo -e "${RED}::${NC} Missing required dependencies: ${MISSING_DEPS[*]}"
        echo -e "${YELLOW}::${NC} Please install them and try again"
        return 1
    fi
    
    # Ask if user wants to skip building AppImage and just install files locally
    if [ "$1" == "--skip-appimage" ]; then
        USE_FALLBACK=true
    else
        echo -e "${YELLOW}?${NC} Would you like to:"
        echo -e "  1) Build an AppImage (recommended)"
        echo -e "  2) Use fallback installation method (if AppImage fails)"
        read -p "$(echo -e "${CYAN}?${NC} Choose option [1/2]: ")" INSTALL_CHOICE
        
        if [[ "$INSTALL_CHOICE" == "2" ]]; then
            USE_FALLBACK=true
            
            # Check if ~/.local/bin is in PATH before using fallback
            check_path
        else
            USE_FALLBACK=false
        fi
    fi
    
    if [ "$USE_FALLBACK" == "true" ]; then
        build_fallback_install
        return $?
    fi
    
    # Check Python version
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 6) else 1)" &> /dev/null; then
        echo -e "${GREEN}::${NC} Python version $PYTHON_VERSION is supported"
    else
        echo -e "${RED}::${NC} Python version $PYTHON_VERSION is not supported"
        echo -e "${YELLOW}::${NC} Please use Python 3.6 or newer"
        return 1
    fi
    
    # Check for GTK4 and libadwaita
    if ! python3 -c "import gi" &> /dev/null; then
        echo -e "${RED}::${NC} PyGObject (python3-gi) is not installed on your system"
        echo -e "${YELLOW}::${NC} Please install PyGObject using your system package manager"
        echo -e "${YELLOW}::${NC} You may need: python3-gi, gir1.2-gtk-4.0, libadwaita-1-0"
        return 1
    fi
    
    # Check for required GTK4 and Adwaita
    echo -e "${BLUE}::${NC} Checking for required system libraries"
    if ! python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk" &> /dev/null; then
        echo -e "${YELLOW}::${NC} GTK 4.0 not detected on your system"
        echo -e "${YELLOW}::${NC} Users will need to install GTK 4.0 to run the app"
    else
        echo -e "${GREEN}::${NC} GTK 4.0 detected successfully"
    fi
    
    if ! python3 -c "import gi; gi.require_version('Adw', '1'); from gi.repository import Adw" &> /dev/null; then
        echo -e "${YELLOW}::${NC} libadwaita not detected on your system"
        echo -e "${YELLOW}::${NC} Users will need to install libadwaita to run the app correctly"
    else
        echo -e "${GREEN}::${NC} libadwaita detected successfully"
    fi
    
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
    if [ $? -ne 0 ]; then
        echo -e "${RED}::${NC} Failed to copy application files to AppDir"
        return 1
    fi
    show_progress "Building AppImage" 30
    
    # Install Python dependencies
    mkdir -p "$APPDIR/usr/share/atl-gui/lib"
    if [ $? -ne 0 ]; then
        echo -e "${RED}::${NC} Failed to create lib directory in AppDir"
        return 1
    fi
    
    # Install all requirements from requirements.txt
    echo -e "${BLUE}::${NC} Installing Python dependencies from requirements.txt"
    if [ -f "$PROJECT_DIR/requirements.txt" ]; then
        # First check if pip is available
        if ! command -v pip3 &> /dev/null; then
            echo -e "${RED}::${NC} pip3 is not installed. Please install Python3 and pip3 to continue."
            exit 1
        fi
        
        # Install all dependencies from requirements.txt to AppDir, excluding system packages
        # Create a temporary requirements file without GTK/Adwaita dependencies
        TMP_REQ_FILE="$(mktemp)"
        grep -v -E 'libadwaita|PyGObject|Gtk' "$PROJECT_DIR/requirements.txt" > "$TMP_REQ_FILE"
        
        # Install only Python packages that aren't system dependencies
        echo -e "${BLUE}::${NC} Installing Python-only dependencies (excluding GTK/Adwaita)"
        pip3 install --target="$APPDIR/usr/share/atl-gui/lib" -r "$TMP_REQ_FILE"
        rm -f "$TMP_REQ_FILE"
        
        # Check for installation success
        if [ $? -ne 0 ]; then
            echo -e "${RED}::${NC} Failed to install Python dependencies. Please check your internet connection."
            exit 1
        fi
        
        # Only install distro package with pip if needed
        if ! pip3 list | grep -q "distro"; then
            echo -e "${BLUE}::${NC} Installing distro package"
            pip3 install --target="$APPDIR/usr/share/atl-gui/lib" distro
        fi
    else
        echo -e "${YELLOW}::${NC} requirements.txt not found at $PROJECT_DIR/requirements.txt"
        echo -e "${YELLOW}::${NC} Installing minimal dependencies"
        pip3 install --target="$APPDIR/usr/share/atl-gui/lib" distro
    fi
    show_progress "Building AppImage" 40
    
    # Check if we need to bundle GTK libraries (optional)
    echo -e "${BLUE}::${NC} Checking for GTK dependencies"
    if ! python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk" &> /dev/null; then
        echo -e "${YELLOW}::${NC} GTK 4.0 not found. The AppImage will use system libraries."
        echo -e "${YELLOW}::${NC} Users will need to install GTK 4.0 and libadwaita to run the app."
        
        # Create a more visible warning message in the app directory
        mkdir -p "$APPDIR/usr/share/atl-gui/notices"
        cat > "$APPDIR/usr/share/atl-gui/notices/DEPENDENCIES.txt" << EOD
IMPORTANT: ATL-GUI SYSTEM DEPENDENCIES NOTICE
===========================================

This application requires the following libraries to be installed on your system:
- GTK 4.0
- libadwaita (>= 1.0)
- PyGObject (Python GTK bindings)

These libraries MUST BE INSTALLED WITH YOUR SYSTEM PACKAGE MANAGER.
They cannot be bundled with the AppImage due to technical limitations.

If the application fails to start, please install these dependencies using your
distribution's package manager.

For example:
- On Debian/Ubuntu: sudo apt install python3-gi gir1.2-gtk-4.0 libadwaita-1-0
- On Fedora: sudo dnf install python3-gobject gtk4 libadwaita
- On Arch Linux: sudo pacman -S python-gobject gtk4 libadwaita

DO NOT attempt to install these with pip as it will not work properly.

====================
EOD
    else
        echo -e "${GREEN}::${NC} GTK 4.0 found. The AppImage will work on systems with similar GTK setup."
    fi
    
    show_progress "Building AppImage" 50
    
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
    
    # Make desktop file executable (good practice)
    chmod +x "$APP_DESKTOP_DIR/atl-gui.desktop" 2>/dev/null || true
    
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
        log "INFO" "The application should appear in your menu after logging out and back in"
    fi
    
    # Save installation path for future reference
    log "INFO" "Saving AppImage location to $APP_CONFIG_DIR/appimage_path"
    echo "$APPIMAGE_PATH" > "$APP_CONFIG_DIR/appimage_path"
fi

# Setup environment variables
log "INFO" "Setting up environment variables"

# Python environment
export PYTHONPATH="$APPDIR/usr/share/atl-gui:$APPDIR/usr/share/atl-gui/lib:$PYTHONPATH"

# GTK and GI environment setup
export GI_TYPELIB_PATH="/usr/lib/girepository-1.0:/usr/lib64/girepository-1.0:$APPDIR/usr/lib/girepository-1.0:${GI_TYPELIB_PATH}"
export LD_LIBRARY_PATH="/usr/lib:/usr/lib64:$APPDIR/usr/lib:${LD_LIBRARY_PATH}"
export XDG_DATA_DIRS="/usr/share:$APPDIR/usr/share:${XDG_DATA_DIRS}"

# Check for system GTK libraries
if ! python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk" &> /dev/null; then
    log "ERROR" "GTK 4.0 not found. This application requires GTK 4.0 to be installed on your system."
    log "INFO" "Please install GTK 4.0 using your distribution's package manager."
    log "INFO" "For example:"
    log "INFO" "  Debian/Ubuntu: sudo apt install python3-gi gir1.2-gtk-4.0"
    log "INFO" "  Fedora: sudo dnf install python3-gobject gtk4"
    log "INFO" "  Arch Linux: sudo pacman -S python-gobject gtk4"
    
    # Show a dialog if zenity is available
    if command -v zenity &> /dev/null; then
        zenity --error --title="ATL-GUI: Missing Dependencies" \
               --text="GTK 4.0 not found. Please install GTK 4.0 using your distribution's package manager.\n\nFor example:\nDebian/Ubuntu: sudo apt install python3-gi gir1.2-gtk-4.0 libadwaita-1-0\nFedora: sudo dnf install python3-gobject gtk4 libadwaita\nArch Linux: sudo pacman -S python-gobject gtk4 libadwaita" \
               --width=400 2>/dev/null
    fi
    
    exit 1
fi

# Check for libadwaita
if ! python3 -c "import gi; gi.require_version('Adw', '1'); from gi.repository import Adw" &> /dev/null; then
    log "ERROR" "libadwaita not found. This application requires libadwaita to be installed on your system."
    log "INFO" "Please install libadwaita using your distribution's package manager."
    log "INFO" "For example:"
    log "INFO" "  Debian/Ubuntu: sudo apt install libadwaita-1-0"
    log "INFO" "  Fedora: sudo dnf install libadwaita"
    log "INFO" "  Arch Linux: sudo pacman -S libadwaita"
    
    # Show a dialog if zenity is available
    if command -v zenity &> /dev/null; then
        zenity --error --title="ATL-GUI: Missing Dependencies" \
               --text="libadwaita not found. Please install libadwaita using your distribution's package manager.\n\nFor example:\nDebian/Ubuntu: sudo apt install libadwaita-1-0\nFedora: sudo dnf install libadwaita\nArch Linux: sudo pacman -S libadwaita" \
               --width=400 2>/dev/null
    fi
    
    exit 1
fi

# Save environment variables for debugging
if [ -d "$APP_CONFIG_DIR" ]; then
    log "INFO" "Saving environment variables for debugging"
    (
        echo "APPDIR=$APPDIR"
        echo "XDG_CONFIG_HOME=$XDG_CONFIG_HOME"
        echo "XDG_DATA_HOME=$XDG_DATA_HOME" 
        echo "XDG_CACHE_HOME=$XDG_CACHE_HOME"
        echo "PYTHONPATH=$PYTHONPATH"
        echo "GI_TYPELIB_PATH=$GI_TYPELIB_PATH"
        echo "LD_LIBRARY_PATH=$LD_LIBRARY_PATH"
        echo "XDG_DATA_DIRS=$XDG_DATA_DIRS"
        echo "PATH=$PATH"
    ) > "$APP_CONFIG_DIR/last_run_env.txt"
fi

# Launch the application with Python 3
log "INFO" "Starting ATL-GUI application"
exec python3 "$APPDIR/usr/share/atl-gui/atl_gui.py" "$@"
EOF
    
    # Make AppRun executable
    ensure_executable "$APPDIR/AppRun" "AppRun script"
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
    if [ $? -ne 0 ]; then
        echo -e "${RED}::${NC} Failed to copy icon to AppDir"
        # Check if the icon file exists
        if [ ! -f "$PROJECT_DIR/res/android_translation_layer.png" ]; then
            echo -e "${RED}::${NC} Icon file not found: $PROJECT_DIR/res/android_translation_layer.png"
        fi
        return 1
    fi
    ln -sf usr/share/icons/hicolor/scalable/apps/atl-gui.png "$APPDIR/atl-gui.png"
    show_progress "Building AppImage" 70
    
    # Build the AppImage
    echo -e "${BLUE}::${NC} Running appimagetool to build the AppImage"
    
    # Create a temporary log file for appimagetool output
    APPIMAGE_LOG=$(mktemp)
    
    # Run appimagetool with full output captured to log
    ARCH=x86_64 "$APPIMAGETOOL" "$APPDIR" "$APPIMAGE_PATH" > "$APPIMAGE_LOG" 2>&1
    APPIMAGE_EXIT_CODE=$?
    
    # Check the exit code
    if [ $APPIMAGE_EXIT_CODE -ne 0 ]; then
        echo -e "${RED}::${NC} appimagetool failed with exit code $APPIMAGE_EXIT_CODE"
        echo -e "${YELLOW}::${NC} appimagetool output:"
        cat "$APPIMAGE_LOG"
        rm -f "$APPIMAGE_LOG"
        
        # Check common issues
        if grep -q "FUSE" "$APPIMAGE_LOG"; then
            echo -e "\n${YELLOW}::${NC} FUSE-related error detected. Please ensure FUSE is installed:"
            echo -e "   For Debian/Ubuntu: sudo apt install fuse libfuse2"
            echo -e "   For Fedora: sudo dnf install fuse fuse-libs"
            echo -e "   For Arch Linux: sudo pacman -S fuse2"
            echo -e "\n${YELLOW}::${NC} If FUSE is installed but still failing, try running with --appimage-extract-and-run:"
            echo -e "   ARCH=x86_64 $APPIMAGETOOL --appimage-extract-and-run $APPDIR $APPIMAGE_PATH"
        fi
        
        echo -e "\n${YELLOW}::${NC} You can try running appimagetool manually:"
        echo -e "   ARCH=x86_64 $APPIMAGETOOL $APPDIR $APPIMAGE_PATH"
        return 1
    fi
    
    rm -f "$APPIMAGE_LOG"
    
    # Check if the AppImage was created successfully
    if [ ! -f "$APPIMAGE_PATH" ]; then
        echo -e "${RED}::${NC} Failed to create AppImage at $APPIMAGE_PATH"
        echo -e "${YELLOW}::${NC} Trying alternative method with --appimage-extract-and-run..."
        
        # Try alternative method with --appimage-extract-and-run
        ARCH=x86_64 "$APPIMAGETOOL" --appimage-extract-and-run "$APPDIR" "$APPIMAGE_PATH" 2>/dev/null
        
        if [ ! -f "$APPIMAGE_PATH" ]; then
            echo -e "${RED}::${NC} Alternative method also failed"
            report_error "Failed to build AppImage" "You can try manually building the AppImage or use the fallback installation"
            return $?
        else
            echo -e "${GREEN}::${NC} Alternative method succeeded!"
        fi
    fi
    
    # Make the AppImage executable
    ensure_executable "$APPIMAGE_PATH" "AppImage"
    
    show_progress "Building AppImage" 90
    
    # Create desktop entry for the AppImage
    create_desktop_entry "$APPIMAGE_PATH"
    
    # Save installation path for future reference
    echo "$APPIMAGE_PATH" > "$APP_CONFIG_DIR/appimage_path"
    
    show_progress "Building AppImage" 100
    # Add a newline to finish the progress bar
    echo -e "\n"
    
    # Verify the installation
    if [ -f "$APPIMAGE_PATH" ] && [ -x "$APPIMAGE_PATH" ]; then
        echo -e "${GREEN}:: ${BOLD}ATL-GUI installation completed successfully${NC}"
        echo -e "   ${BOLD}AppImage path:${NC} ${YELLOW}$APPIMAGE_PATH${NC}"
        echo -e "   ${BOLD}Desktop entry:${NC} ${YELLOW}$APP_DESKTOP_DIR/atl-gui.desktop${NC}"
        echo -e "   ${BOLD}Configuration:${NC} ${YELLOW}$APP_CONFIG_DIR${NC}"
        echo -e "   ${BOLD}Data directory:${NC} ${YELLOW}$APP_DATA_DIR${NC}"
        
        echo -e "\n${BLUE}::${NC} Verifying AppImage integrity..."
        # Check file size (should be at least 10MB for a reasonable AppImage)
        APPIMAGE_SIZE=$(stat -c %s "$APPIMAGE_PATH" 2>/dev/null || echo "0")
        if [ "$APPIMAGE_SIZE" -lt 10000000 ]; then
            echo -e "${YELLOW}::${NC} Warning: AppImage size ($(numfmt --to=iec-i --suffix=B "$APPIMAGE_SIZE")) seems small, it might be incomplete"
        else
            echo -e "${GREEN}::${NC} AppImage size: $(numfmt --to=iec-i --suffix=B "$APPIMAGE_SIZE")"
        fi
        
        # Try running the AppImage with --appimage-extract-and-run --version to verify it works
        if "$APPIMAGE_PATH" --appimage-extract-and-run --version &>/dev/null; then
            echo -e "${GREEN}::${NC} AppImage verified: runs correctly"
        else
            echo -e "${YELLOW}::${NC} Warning: Couldn't verify if the AppImage runs correctly"
            echo -e "${YELLOW}::${NC} You may need to run: chmod +x \"$APPIMAGE_PATH\""
        fi
    else
        echo -e "${RED}:: ${BOLD}ATL-GUI installation failed${NC}"
        echo -e "${YELLOW}::${NC} The AppImage was not created correctly at: ${YELLOW}$APPIMAGE_PATH${NC}"
        echo -e "${YELLOW}::${NC} Please check for errors above and try again"
        return 1
    fi
}

function build_fallback_install() {
    echo -e "${BLUE}::${NC} ${CYAN}${BOLD}Building ATL-GUI (fallback installation)${NC}"
    
    # Create direct installation into local directories
    create_directories
    
    # Check if ~/.local/bin is in PATH
    check_path
    
    echo -e "${BLUE}::${NC} Copying application files..."
    
    # Create main script in ~/.local/bin
    mkdir -p "$HOME/.local/bin"
    cat > "$HOME/.local/bin/atl-gui" << EOF
#!/bin/bash
# ATL-GUI launcher script
export PYTHONPATH="$APP_DATA_DIR:$PYTHONPATH"
exec python3 "$APP_DATA_DIR/atl_gui.py" "\$@"
EOF
    
    # Make launcher executable
    ensure_executable "$HOME/.local/bin/atl-gui" "launcher script"
    
    # Copy application files to data directory
    mkdir -p "$APP_DATA_DIR"
    cp -r "$PROJECT_DIR/atl_gui.py" "$PROJECT_DIR/src" "$PROJECT_DIR/res" "$APP_DATA_DIR/"
    
    # Install Python dependencies
    echo -e "${BLUE}::${NC} Installing Python dependencies..."
    if [ -f "$PROJECT_DIR/requirements.txt" ]; then
        # Create a temporary requirements file without GTK/Adwaita dependencies
        TMP_REQ_FILE="$(mktemp)"
        grep -v -E 'libadwaita|PyGObject|Gtk' "$PROJECT_DIR/requirements.txt" > "$TMP_REQ_FILE"
        
        # Install only Python packages that aren't system dependencies
        pip3 install --user -r "$TMP_REQ_FILE"
        rm -f "$TMP_REQ_FILE"
    fi
    
    # Create desktop entry
    create_desktop_entry "$HOME/.local/bin/atl-gui"
    
    # Create a "version" file to track installation
    echo "$(date '+%Y-%m-%d %H:%M:%S')" > "$APP_CONFIG_DIR/installed_version"
    
    echo -e "\n${GREEN}:: ${BOLD}ATL-GUI fallback installation completed${NC}"
    echo -e "   ${BOLD}Launcher:${NC} ${YELLOW}$HOME/.local/bin/atl-gui${NC}"
    echo -e "   ${BOLD}Desktop entry:${NC} ${YELLOW}$APP_DESKTOP_DIR/atl-gui.desktop${NC}"
    echo -e "   ${BOLD}Configuration:${NC} ${YELLOW}$APP_CONFIG_DIR${NC}"
    echo -e "   ${BOLD}Data directory:${NC} ${YELLOW}$APP_DATA_DIR${NC}"
    
    echo -e "\n${YELLOW}::${NC} Make sure $HOME/.local/bin is in your PATH variable"
    echo -e "${YELLOW}::${NC} You can run the application with: atl-gui"
    
    return 0
}

function update_desktop_db() {
    local desktop_dir="$1"
    echo -e "${BLUE}::${NC} Updating desktop database"
    
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$desktop_dir" 2>/dev/null || true
        echo -e "${GREEN}::${NC} Desktop database updated"
    else
        echo -e "${YELLOW}::${NC} update-desktop-database command not found, skipping"
        echo -e "${YELLOW}::${NC} You may need to log out and log back in to see the application in menus"
    fi
}

function remove_appimage() {
    echo -e "${BLUE}::${NC} ${RED}${BOLD}Removing ATL-GUI${NC}"
    
    # Variables to track what was removed
    local REMOVED_APPIMAGE=false
    local REMOVED_FALLBACK=false
    
    # Check for saved installation path
    if [ -f "$APP_CONFIG_DIR/appimage_path" ]; then
        SAVED_PATH=$(cat "$APP_CONFIG_DIR/appimage_path")
        if [ -f "$SAVED_PATH" ]; then
            echo -e "${BLUE}::${NC} Removing AppImage from saved path: $SAVED_PATH"
            rm -f "$SAVED_PATH"
            REMOVED_APPIMAGE=true
        fi
    fi
    
    # Remove AppImage
    if [ -f "$APPIMAGE_PATH" ]; then
        echo -e "${BLUE}::${NC} Removing AppImage file"
        rm -f "$APPIMAGE_PATH"
        REMOVED_APPIMAGE=true
    else
        echo -e "${YELLOW}::${NC} AppImage not found at $APPIMAGE_PATH"
    fi
    
    # Remove fallback installation
    if [ -f "$HOME/.local/bin/atl-gui" ]; then
        echo -e "${BLUE}::${NC} Removing fallback installation script"
        rm -f "$HOME/.local/bin/atl-gui"
        REMOVED_FALLBACK=true
    fi
    
    # Remove installation data in APP_DATA_DIR
    if [ -d "$APP_DATA_DIR" ] && [ -f "$APP_DATA_DIR/atl_gui.py" ]; then
        echo -e "${BLUE}::${NC} Removing application files from data directory"
        rm -f "$APP_DATA_DIR/atl_gui.py"
        # Keep the directory for now, full removal is optional below
        REMOVED_FALLBACK=true
    fi
    
    # Remove ALL desktop entries using various methods
    echo -e "${BLUE}::${NC} Removing ALL desktop entries"
    
    # 1. Standard locations
    local DESKTOP_LOCATIONS=(
        "$APP_DESKTOP_DIR"
        "$HOME/.local/share/applications"
        "$HOME/.gnome/apps"
        "$HOME/Desktop"
        "/usr/share/applications"
        "/usr/local/share/applications"
    )
    
    for location in "${DESKTOP_LOCATIONS[@]}"; do
        if [ -f "$location/atl-gui.desktop" ]; then
            echo -e "${BLUE}::${NC} Removing desktop entry from $location"
            rm -f "$location/atl-gui.desktop"
        fi
    done
    
    # 2. Use xdg-desktop-menu to uninstall
    if command -v xdg-desktop-menu &> /dev/null; then
        echo -e "${BLUE}::${NC} Unregistering desktop entry with xdg-desktop-menu"
        xdg-desktop-menu uninstall --novendor "$APP_DESKTOP_DIR/atl-gui.desktop" 2>/dev/null || true
        xdg-desktop-menu forceupdate 2>/dev/null || true
    fi
    
    # 3. Find any related desktop files via find
    FOUND_FILES=$(find "$HOME" -name "*atl*gui*.desktop" 2>/dev/null || true)
    if [ -n "$FOUND_FILES" ]; then
        echo -e "${BLUE}::${NC} Removing additional desktop files"
        for file in $FOUND_FILES; do
            echo -e "${YELLOW}::${NC} Removing: $file"
            rm -f "$file"
        done
    fi
    
    # Remove icons from ALL standard locations
    echo -e "${BLUE}::${NC} Removing ALL icon files"
    
    # 1. Standard locations
    local ICON_LOCATIONS=(
        "$APP_ICON_DIR"
        "$HOME/.local/share/icons/hicolor/256x256/apps"
        "$HOME/.local/share/icons/hicolor/scalable/apps"
        "/usr/share/icons/hicolor/scalable/apps"
        "/usr/local/share/icons/hicolor/scalable/apps"
    )
    
    for location in "${ICON_LOCATIONS[@]}"; do
        if [ -f "$location/atl-gui.png" ]; then
            echo -e "${BLUE}::${NC} Removing icon from $location"
            rm -f "$location/atl-gui.png"
        fi
    done
    
    # 2. Find any related icon files via find
    FOUND_ICONS=$(find "$HOME" -name "*atl*gui*.png" 2>/dev/null || true)
    if [ -n "$FOUND_ICONS" ]; then
        echo -e "${BLUE}::${NC} Removing additional icon files"
        for icon in $FOUND_ICONS; do
            echo -e "${YELLOW}::${NC} Removing: $icon"
            rm -f "$icon"
        done
    fi
    
    # Update icon cache
    if command -v gtk-update-icon-cache &> /dev/null; then
        echo -e "${BLUE}::${NC} Updating icon cache"
        gtk-update-icon-cache -f "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
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
    update_desktop_db "$APP_DESKTOP_DIR"
    update_desktop_db "$HOME/.local/share/applications"
    
    # Force an update of all menus
    if command -v xdg-desktop-menu &> /dev/null; then
        xdg-desktop-menu forceupdate 2>/dev/null || true
    fi
    
    # Summary message
    if [ "$REMOVED_APPIMAGE" = true ] || [ "$REMOVED_FALLBACK" = true ]; then
        echo -e "${GREEN}:: ${BOLD}ATL-GUI removal completed successfully${NC}"
        echo -e "${GREEN}::${NC} All desktop entries and icons have been removed"
    else
        echo -e "${YELLOW}:: ${BOLD}No ATL-GUI installation was found to remove${NC}"
    fi
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

function manual_menu_entry() {
    echo -e "\n${BLUE}::${NC} ${CYAN}${BOLD}Creating a manual menu entry${NC}"
    echo -e "${YELLOW}::${NC} This will attempt to force-create a menu entry for ATL-GUI"
    
    # Find the app path
    APP_PATH=""
    if [ -f "$HOME/.local/bin/atl-gui" ]; then
        APP_PATH="$HOME/.local/bin/atl-gui"
        echo -e "${GREEN}::${NC} Found fallback installation at $APP_PATH"
        
        # Check if ~/.local/bin is in PATH
        check_path
    elif [ -f "$APP_CONFIG_DIR/appimage_path" ]; then
        APP_PATH=$(cat "$APP_CONFIG_DIR/appimage_path")
        if [ -f "$APP_PATH" ]; then
            echo -e "${GREEN}::${NC} Found AppImage at $APP_PATH"
        else
            echo -e "${YELLOW}::${NC} Saved AppImage path not found"
            APP_PATH=""
        fi
    fi
    
    if [ -z "$APP_PATH" ]; then
        echo -e "${RED}::${NC} Could not find installed ATL-GUI"
        echo -e "${YELLOW}::${NC} Please install using ./install.sh -S or ./install.sh -F first"
        return 1
    fi
    
    # Create desktop entry with all possible methods
    create_desktop_entry "$APP_PATH"
    
    # Additional desktop entry method for older systems
    mkdir -p "$HOME/.gnome/apps"
    cat > "$HOME/.gnome/apps/atl-gui.desktop" << EOF
[Desktop Entry]
Type=Application
Name=ATL-GUI
GenericName=Android Translation Layer
Comment=Android Translation Layer GUI Application
Exec=$APP_PATH
Icon=$HOME/.local/share/icons/hicolor/256x256/apps/atl-gui.png
Categories=Development;Utility;
Keywords=Android;Translation;ATL;
Terminal=false
StartupNotify=true
EOF
    
    echo -e "\n${GREEN}::${NC} Manual menu entry creation completed"
    echo -e "${YELLOW}::${NC} You may need to log out and log back in to see the application in your menu"
    echo -e "${YELLOW}::${NC} You can always run the application directly using:"
    echo -e "   ${CYAN}$APP_PATH${NC}"
}

function interactive_menu() {
    clear
    echo -e "${CYAN}${BOLD}==== ATL-GUI AppImage Manager ====${NC}"
    echo
    echo -e "1) ${GREEN}Build and install ATL-GUI AppImage${NC}"
    echo -e "2) ${GREEN}Use fallback installation method${NC}"
    echo -e "3) ${GREEN}Force-create menu entries${NC}"
    echo -e "4) ${RED}Remove ATL-GUI${NC}"
    echo -e "5) ${BLUE}Show ATL-GUI information${NC}"
    echo -e "6) ${YELLOW}Exit${NC}"
    echo
    read -p "$(echo -e "${CYAN}?${NC} Select an option (1-6): ")" choice
    
    case $choice in
        1)
            clear
            build_appimage
            ;;
        2)
            clear
            build_fallback_install
            ;;
        3)
            clear
            manual_menu_entry
            ;;
        4)
            clear
            remove_appimage
            ;;
        5)
            clear
            query_appimage
            ;;
        6)
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

function report_error() {
    local error_msg="$1"
    local recovery_hint="$2"
    
    echo -e "\n${RED}ERROR: ${error_msg}${NC}"
    
    if [ -n "$recovery_hint" ]; then
        echo -e "${YELLOW}HINT: ${recovery_hint}${NC}"
    fi
    
    echo -e "\nWould you like to:"
    echo -e "  1) Try using the fallback installation method"
    echo -e "  2) Exit"
    
    read -p "$(echo -e "${CYAN}?${NC} Choose option [1/2]: ")" ERROR_CHOICE
    
    if [[ "$ERROR_CHOICE" == "1" ]]; then
        echo -e "${BLUE}::${NC} Trying fallback installation method"
        build_fallback_install
        return $?
    else
        echo -e "${YELLOW}Exiting...${NC}"
        return 1
    fi
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
    -F|--fallback)
        build_fallback_install
        ;;
    -M|--menu)
        manual_menu_entry
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
