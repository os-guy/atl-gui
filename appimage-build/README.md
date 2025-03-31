# ATL GUI AppImage

This directory contains all the files needed to build an AppImage for the Android Translation Layer (ATL) GUI application.

## What is an AppImage?

An [AppImage](https://appimage.org/) is a portable format for distributing applications on Linux without requiring installation. The AppImage bundles the application and its dependencies in a way that allows it to run on most Linux distributions.

## Building and Installing

To build the ATL GUI AppImage and automatically add it to your application menu:

```bash
./build.sh
```

The script will:
1. Download the `appimagetool` if it's not already available
2. Prepare the AppDir structure
3. Copy application files from the parent directory
4. Create the necessary AppRun script and desktop files
5. Build the AppImage file
6. Add the application to your desktop menu

After a successful build, you'll find the AppImage file (`ATL_GUI-x86_64.AppImage`) in this directory and the application will be available in your application menu under "Development".

## Running the AppImage

To run the ATL GUI AppImage directly:

```bash
./ATL_GUI-x86_64.AppImage
```

Or launch it from your application menu by searching for "ATL GUI".

## Installation Options

### Installing the Menu Entry Separately

If you already have the AppImage and just want to add it to your application menu:

```bash
./install-menu.sh
```

### Complete Removal

To completely remove the AppImage from your application menu and optionally delete the AppImage file:

```bash
./remove.sh
```

This script will:
1. Remove the desktop menu entry and icon
2. Ask if you want to delete the AppImage file
3. Remove integration markers

## Requirements

The AppImage requires:
- A Linux distribution with GTK4 and libadwaita
- Python 3
- `android-translation-layer` installed on the system (the AppImage doesn't bundle this dependency)

## Directory Structure

```
appimage-build/
├── AppDir/              # The AppDir structure used to build the AppImage
├── appimagetool         # Tool for building AppImages
├── build.sh             # Script to build the AppImage and add to menu
├── install-menu.sh      # Script to add the app to the menu
├── remove.sh            # Script to remove the app from menu
├── README.md            # This file
└── ATL_GUI-x86_64.AppImage  # The generated AppImage (after building)
```

## Troubleshooting

If the application doesn't appear in your menu immediately:
1. Try logging out and logging back in
2. Run `update-desktop-database ~/.local/share/applications` if available
3. Use the application directly by running the AppImage 