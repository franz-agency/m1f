#!/usr/bin/env python3
"""
Basic check of file encodings by trying to read them with different encodings.
"""

from pathlib import Path

# Define the file-to-encoding mappings
ENCODING_MAP = {
    "shiftjis.txt": "shift_jis",
    "big5.txt": "big5",
    "koi8r.txt": "koi8_r",
    "iso8859-8.txt": "iso8859_8",
    "euckr.txt": "euc_kr",
    "windows1256.txt": "cp1256",
}

# Get the directory containing this script
script_dir = Path(__file__).parent

# Check each file
for filename, expected_encoding in ENCODING_MAP.items():
    filepath = script_dir / filename
    
    # Try to read with expected encoding
    try:
        with open(filepath, 'r', encoding=expected_encoding) as f:
            content = f.read(100)  # Read first 100 chars
            print(f"{filename}: Successfully read with {expected_encoding}")
            print(f"Sample content: {content[:50]}...")
            
        # Try to read with UTF-8 (should fail if the file is properly encoded)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"WARNING: {filename} can be read as UTF-8, may not be properly encoded")
        except UnicodeDecodeError:
            print(f"{filename}: Proper encoding confirmed (fails with UTF-8)")
    except Exception as e:
        print(f"ERROR reading {filename} with {expected_encoding}: {e}")
        
    print()  # Empty line for readability 