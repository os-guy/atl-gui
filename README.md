# Android Translation Layer GUI

<p align="center">
  <img src="res/android_translation_layer.svg" alt="ATL GUI Logo" width="150">
</p>

A sleek, modern **UNOFFICAL** GTK4 graphical user interface for Android Translation Layer that simplifies testing Android applications on Linux.

## Features

- 🚀 Run and test single APK files or entire directories
- 📋 Record test results (working/not working)
- 📊 Export detailed test reports
- 🔧 Configure custom environment variables
- 🌐 No-internet mode with custom scripts
- 📱 Custom resolution and activity settings
- 🔍 Automatic detection of application success/failure
- 🖥️ Terminal output monitoring
- 🔎 Comprehensive error detection and analysis

## Prerequisites

⚠️ **IMPORTANT**: This application requires `android-translation-layer` to be installed on your system. ATL GUI is just a frontend for the command-line tool.

If you haven't installed Android Translation Layer yet, please visit the [official repository](https://gitlab.com/android_translation_layer/android_translation_layer) for installation instructions.

For Arch Users, it's available in the AUR.
For Alpine Users, it's also available in alpine:edge repos.

## Error Detection System

The application includes a sophisticated error detection system that analyzes application behavior and identifies issues:

### Automatic Detection Features

- **Window Creation Detection**: Checks if application windows are properly created and rendered
- **Crash Monitoring**: Identifies various types of crashes (fatal exceptions, ANRs, segmentation faults)
- **UI Responsiveness Assessment**: Evaluates user interface responsiveness through rendering signals
- **Process Initialization Tracking**: Monitors application startup processes to ensure proper initialization
- **Common Success Signal Collection**: Identifies patterns indicating successful application operation

### Error Categorization

Errors are automatically categorized into types:
- File Not Found errors (missing files/resources)
- Failed Execution issues
- Dex Compilation problems
- Package Parsing errors
- Java Exceptions
- Native Errors
- Asset Errors
- Permission Issues

### Error Analysis Features

- **Path Extraction**: Automatically extracts and displays file paths from error messages
- **Search Functionality**: Filter and search through errors to find specific issues
- **Error Counts**: Shows error counts for each application
- **Detailed Context**: Provides surrounding context for each error to assist debugging
- **Visual Indicators**: Specialized icons and formatting to highlight different error types

### Smart Assessment

The system uses a weighted scoring algorithm to determine if an application is working properly:
- Balances multiple indicators (window creation, crash status, UI signals)
- Provides clear reasoning for its assessment
- Displays detailed scoring and rationale for each application
- Works immediately without waiting for manual review

## Installation

### Dependencies

#### Arch Linux and Derivatives (Manjaro, EndeavourOS, etc.)

```bash
sudo pacman -S python-gobject gtk4 libadwaita python-pip
```

#### Debian/Ubuntu and Derivatives (Pop!_OS, Linux Mint, etc.)

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 libadwaita-1-0 gir1.2-adw-1 python3-pip
```

#### Fedora

```bash
sudo dnf install python3-gobject gtk4 libadwaita python3-pip
```

#### openSUSE

```bash
sudo zypper install python3-gobject gtk4 libadwaita python3-pip
```

### Clone Repository

```bash
git clone https://github.com/os-guy/atl-gui.git
cd atl-gui
```

## Running the Application

The application is now available in a modularized version with improved code organization.
Make the script executable and run it:

```bash
chmod +x atl_gui_new.py
./atl_gui_new.py
```

Or using Python directly:

```bash
python3 atl_gui_new.py
```

## Directory Structure (Modular Version)

```
atl-tester/
├── atl_gui_new.py
├── res/                        # Resources directory
└── src/                        # Source code package
    ├── __init__.py             # Package marker
    ├── app.py                  # Application initialization
    ├── window.py               # Main window class
    ├── handlers/               # Event handlers
    │   ├── __init__.py
    │   ├── file_handlers.py    # File/folder selection handlers
    │   ├── test_handlers.py    # Testing process handlers
    │   ├── settings_handlers.py # Settings dialog handlers
    │   └── results_handlers.py  # Results view handlers
    ├── utils/                  # Utilities
    │   ├── __init__.py
    │   └── css_provider.py     # CSS styling setup
    └── views/                  # UI views
        ├── __init__.py
        ├── welcome_view.py     # Welcome screen
        ├── testing_view.py     # Testing screen
        └── results_view.py     # Results screen
```

## Usage Guide

1. **Start the application** using one of the methods described above.
2. **Set environment variables** (optional) - The app provides default variables like `SCALE=2` and `LOG_LEVEL=debug`.
3. **Select an APK file or folder** containing multiple APK files.
4. **Start the application** testing with the "Start Application" button.
5. **Configure additional options** (optional):
   - Set custom window dimensions
   - Specify an activity to launch
   - Enable no-internet mode with a custom script
   - Add additional environment variables
6. **Rate the application** as "Working" or "Not Working" after testing.
7. **Export results** when all tests are complete.

## No-Internet Mode

The application supports testing APKs without internet access by using a custom script. The script must:

1. Be executable (`chmod +x script.sh`)
2. Accept the android-translation-layer command as a parameter
3. Manage network access for the application

Note: Using this feature might require sudo access, which is why the application allows you to input your sudo password.

## Environment Variables

The application allows you to set environment variables for Android Translation Layer:

- Default variables are set in the welcome screen
- Application-specific variables can be set in the options dialog
- Additional variables will override default ones with the same name

## Screenshots

<details>
  <summary>Welcome Screen</summary>
  <p align="center">
    <img src="res/ui_welcome.png" alt="Welcome Screen"><br>
    <em>Welcome Screen - Configure environment variables and select APK</em>
  </p>
</details>

<details>
  <summary>Testing Screen</summary>
  <p align="center">
    <img src="res/ui_tester.png" alt="Test Screen"><br>
    <em>Testing Screen - Run applications and monitor output</em>
  </p>
</details>

<details>
  <summary>Application Options</summary>
  <p align="center">
    <img src="res/ui_tester_options.png" alt="Test Options"><br>
    <em>Application Options - Configure resolution, activity, and network settings</em>
  </p>
</details>

<details>
  <summary>Results Screen</summary>
  <p align="center">
    <img src="res/ui_results.png" alt="Results Screen"><br>
    <em>Results Screen - View testing summary</em>
  </p>
</details>

<details>
  <summary>Detailed Results Log</summary>
  <p align="center">
    <img src="res/ui_results_log.png" alt="Results Log"><br>
    <em>Detailed Results - Expand to view terminal output logs</em>
  </p>
</details>

<details>
  <summary>Error Analysis Screen</summary>
  <p align="center">
    <img src="res/ui_errors.png" alt="Error Analysis Screen"><br>
    <em>Error Analysis - Detailed error categorization with file paths and search functionality</em>
  </p>
</details>

## Modular Architecture Benefits

The modularized version maintains all the functionality of the original while providing:

- **Separation of concerns**: UI components and logic are cleanly separated
- **Clear module boundaries**: Each file has a specific purpose
- **Improved maintainability**: Easier to navigate and understand the codebase
- **Extensibility**: Simpler to add new features without affecting existing functionality

## Development

To modify or extend the application:

1. For UI changes, modify the appropriate file in `src/views/`
2. For new functionality, add handlers in `src/handlers/`
3. For utility functions, add them to existing or new files in `src/utils/`

The modular version uses Python's importing system to split the code while maintaining the same functionality:

- The original class methods are imported directly into the main `AtlGUIWindow` class
- Each UI component is defined in its own module with a create function
- CSS styling is extracted to a utility function

This approach maintains the same structure and behavior as the original while improving maintainability.

## License

This project is released under the GPL License. See the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

Created by [os-guy](https://github.com/os-guy) 
