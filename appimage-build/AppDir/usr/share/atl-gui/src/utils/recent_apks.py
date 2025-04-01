import os
import json
import datetime
from pathlib import Path

# Maximum number of recent APKs to store
MAX_RECENT_APKS = 5

def get_config_dir():
    """Get the configuration directory for the application."""
    config_dir = os.path.join(Path.home(), ".config", "atl-gui")
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

def get_recent_apks_file():
    """Get the path to the recent APKs file."""
    return os.path.join(get_config_dir(), "recent_apks.json")

def load_recent_apks():
    """Load recent APKs from the config file."""
    try:
        recent_file = get_recent_apks_file()
        if os.path.exists(recent_file):
            with open(recent_file, 'r') as f:
                data = json.load(f)
                return data.get('recent_apks', [])
        return []
    except Exception as e:
        print(f"Error loading recent APKs: {e}")
        return []

def save_recent_apk(apk_path, status="unknown"):
    """
    Add an APK to the recent list with metadata.
    
    Args:
        apk_path (str): Path to the APK file
        status (str): Status of the APK (working, not_working, skipped, or unknown)
    """
    if not os.path.exists(apk_path):
        return
        
    # Load existing recent APKs
    recent_apks = load_recent_apks()
    
    # Get current timestamp
    timestamp = datetime.datetime.now().isoformat()
    
    # Create metadata for the APK
    apk_name = os.path.basename(apk_path)
    apk_data = {
        'path': apk_path,
        'name': apk_name,
        'last_run': timestamp,
        'status': status
    }
    
    # Remove this APK if already in the list
    recent_apks = [apk for apk in recent_apks if apk.get('path') != apk_path]
    
    # Add the APK at the beginning of the list
    recent_apks.insert(0, apk_data)
    
    # Limit the number of recent APKs
    recent_apks = recent_apks[:MAX_RECENT_APKS]
    
    # Save the updated list
    try:
        with open(get_recent_apks_file(), 'w') as f:
            json.dump({'recent_apks': recent_apks}, f, indent=2)
    except Exception as e:
        print(f"Error saving recent APKs: {e}") 