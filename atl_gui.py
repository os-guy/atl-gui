#!/usr/bin/env python3
"""
ATL GUI - Android Translation Layer GUI Application
This is the main entry point that starts the application
"""
import sys
import os

# Add the project directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.app import main

if __name__ == "__main__":
    sys.exit(main()) 