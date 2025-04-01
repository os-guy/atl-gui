# ATL GUI AppImage

This directory contains all the files needed to build an AppImage for the Android Translation Layer (ATL) GUI application.

## What is an AppImage?

An [AppImage](https://appimage.org/) is a portable format for distributing applications on Linux without requiring installation. The AppImage bundles the application and its dependencies in a way that allows it to run on most Linux distributions.

## Using the AppImage Manager

The AppImage manager provides a pacman-like interface to build, install, remove, and query the ATL-GUI AppImage.

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

## Requirements

The AppImage requires:
- A Linux distribution with GTK4 and libadwaita
- Python 3
- `android-translation-layer` installed on your system (the AppImage doesn't bundle this dependency)

## Directory Structure

```
appimage-build/
├── AppDir/                    # The AppDir structure used to build the AppImage
├── install.sh                 # The main AppImage manager script
├── uninstall.sh               # Symlink to install.sh
└── README.md                  # This file
```

## Troubleshooting

If the application doesn't appear in your menu after running it:
1. Try logging out and logging back in
2. Run `update-desktop-database ~/.local/share/applications` if available
3. Use the application directly by running the AppImage 