#!/bin/bash
# clean.sh - Remove Python cache files and directories

echo "Cleaning Python cache files..."

# Remove __pycache__ directories
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

# Remove .pyc and .pyo files
find . -name "*.pyc" -o -name "*.pyo" -delete

# Remove .pytest_cache directory if it exists
find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null

# Remove .coverage files
find . -name ".coverage" -delete

echo "Clean complete!" 