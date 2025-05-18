#!/usr/bin/env python3
"""
Check the encodings of the converted files using chardet.
"""

import chardet
from pathlib import Path

# Get the directory containing this script
script_dir = Path(__file__).parent

# Files to check (skipping the .utf8 backups)
files_to_check = [f for f in script_dir.glob("*.txt") if not f.name.endswith(".utf8")]

# Check each file
for filepath in files_to_check:
    with open(filepath, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        
    print(f"{filepath.name}: {result['encoding']} (confidence: {result['confidence']:.2f})") 