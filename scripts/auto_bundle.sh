#!/usr/bin/env bash
#
# Wrapper script for auto_bundle.py
# This script simply calls the Python implementation

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Call the Python script with all arguments
python3 "$SCRIPT_DIR/auto_bundle.py" "$@"