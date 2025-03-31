#!/usr/bin/env python3
import re
from pathlib import Path
from typing import Dict, List, Tuple

class ErrorDetector:
    def __init__(self):
        self.error_patterns = {
            'runtime': r'java\.lang\.RuntimeException|java\.lang\.NullPointerException|java\.lang\.ClassNotFoundException',
            'manifest': r'Unknown element under <manifest>|Failed to open file.*AndroidManifest\.xml',
            'dex': r'Failed to compile dex file|No dex files in zip file',
            'activity': r'Failed to find Activity to launch URI',
            'permission': r'uses-permission-sdk-',
            'assets': r'Failed to open file.*resources\.arsc'
        }
        
        self.error_categories = {
            'runtime': 'Runtime Error',
            'manifest': 'Manifest Error',
            'dex': 'DEX Error',
            'activity': 'Activity Error',
            'permission': 'Permission Error',
            'assets': 'Assets Error'
        }

    def analyze_log_file(self, log_file_path: str) -> List[Tuple[str, str, str]]:
        """
        Analyze a log file and return a list of errors found.
        Returns a list of tuples: (error_category, error_message, error_details)
        """
        errors = []
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for each error pattern
            for pattern_name, pattern in self.error_patterns.items():
                # Use search instead of finditer since we just want to know if any match exists
                match = re.search(pattern, content)
                if match:
                    errors.append((
                        self.error_categories[pattern_name],
                        f"Found {pattern_name.replace('_', ' ').title()} Issues",
                        ""
                    ))
                    
        except Exception as e:
            errors.append(('File Error', f'Failed to read log file: {str(e)}', ''))
            
        return errors

    def get_error_summary(self, log_file_path: str) -> Dict[str, int]:
        """
        Get a summary of error counts by category for a log file.
        """
        errors = self.analyze_log_file(log_file_path)
        summary = {}
        for category, _, _ in errors:
            summary[category] = summary.get(category, 0) + 1
        return summary 