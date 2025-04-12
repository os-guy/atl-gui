# ATL GUI AppImage

This directory contains all the files needed to build an AppImage for the Android Translation Layer (ATL) GUI application.

## What is an AppImage?

An [AppImage](https://appimage.org/) is a portable format for distributing applications on Linux without requiring installation. The AppImage bundles the application and its dependencies in a way that allows it to run on most Linux distributions.

## Using the AppImage Manager

The AppImage manager provides a pacman-like interface to build, install, remove, and query the ATL-GUI AppImage. It features enhanced visual feedback, proper XDG directory support, and improved path handling.

### Interactive Menu

To use the interactive menu, simply run:

```bash
./install.sh
```

This will present you with options to:
1. Build and install ATL-GUI AppImage
2. Remove ATL-GUI AppImage
3. Show ATL-GUI AppImage information
4. Exit

### Command-line Options

You can also use command-line options similar to pacman:

```bash
# Build and install the AppImage
./install.sh -S

# Remove the AppImage and all related files
./install.sh -R

# Show information about the installed AppImage
./install.sh -Q

# Show help
./install.sh -h
```

## Features

The AppImage manager includes several features to improve the user experience:

* **XDG Directory Support**: Properly respects the XDG Base Directory Specification
* **Visual Feedback**: Progress bars and colored output for better visual feedback
* **Clean Path Management**: All paths are saved consistently and handled properly
* **Detailed Logging**: Comprehensive logging to aid in troubleshooting
* **Improved Uninstallation**: Option to clean up or keep configuration files

## Running the AppImage

After installation, the AppImage will be added to your application menu as "ATL-GUI".

To run the ATL GUI AppImage directly:

```bash
./ATL_GUI-x86_64.AppImage
```

## Uninstalling

To uninstall the application:

```bash
./uninstall.sh
```

The uninstall script will remove:
- The AppImage file
- Desktop menu entry
- Application icon
- And optionally configuration files (you'll be prompted)

## Directory Structure

The application respects standard Linux directory conventions:

* **Configuration**: `~/.config/atl-gui/` or `$XDG_CONFIG_HOME/atl-gui/`
* **Data**: `~/.local/share/atl-gui/` or `$XDG_DATA_HOME/atl-gui/`
* **Cache**: `~/.cache/atl-gui/` or `$XDG_CACHE_HOME/atl-gui/`
* **Desktop Entry**: `~/.local/share/applications/` or `$XDG_DATA_HOME/applications/`
* **Icons**: `~/.local/share/icons/hicolor/scalable/apps/` or `$XDG_DATA_HOME/icons/hicolor/scalable/apps/`

## Requirements

The AppImage requires:
- A Linux distribution with GTK4 and libadwaita
- Python 3
- `android-translation-layer` installed on your system (the AppImage doesn't bundle this dependency)

## Troubleshooting

If the application doesn't appear in your menu after running it:
1. Try logging out and logging back in
2. Run `update-desktop-database ~/.local/share/applications` if available
3. Use the application directly by running the AppImage
4. Check the log file at `~/.config/atl-gui/logs/appimage.log`

## Project Directory

```
appimage-build/
├── AppDir/                    # The AppDir structure used to build the AppImage
├── install.sh                 # The main AppImage manager script
├── uninstall.sh               # Symlink to install.sh with -R parameter
└── README.md                  # This file
```

If you encounter any issues, please check the logs in `~/.config/atl-gui/logs/` or report the problem in the project's issue tracker. 