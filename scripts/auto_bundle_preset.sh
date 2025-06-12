#!/usr/bin/env bash
# Auto-bundle with preset support
# This script is used by VS Code tasks for preset-based bundling

set -e

# Get the script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Default values
PRESET=""
GROUP=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --preset)
            PRESET="$2"
            shift 2
            ;;
        --group)
            GROUP="$2"
            shift 2
            ;;
        all|focus|preset)
            # Legacy command support - convert to m1f-update
            if [ "$1" = "all" ]; then
                # Run auto-bundle for all bundles
                cd "$PROJECT_ROOT" && source .venv/bin/activate && m1f-update
                exit 0
            elif [ "$1" = "focus" ] && [ -n "$2" ]; then
                # Run auto-bundle for specific bundle
                cd "$PROJECT_ROOT" && source .venv/bin/activate && m1f-update "$2"
                exit 0
            elif [ "$1" = "preset" ] && [ -n "$2" ]; then
                PRESET="$2"
                GROUP="${3:-}"
                shift
                shift
                [ -n "$GROUP" ] && shift
            else
                echo "Usage: $0 [all|focus <bundle>|preset <file> [group]]"
                echo "   or: $0 --preset <file> [--group <group>]"
                exit 1
            fi
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# If preset is specified, use m1f with preset
if [ -n "$PRESET" ]; then
    cd "$PROJECT_ROOT" && source .venv/bin/activate
    
    if [ -n "$GROUP" ]; then
        m1f --preset "$PRESET" --preset-group "$GROUP" -o ".ai-context/${GROUP}.txt"
    else
        m1f --preset "$PRESET" -o ".ai-context/preset-bundle.txt"
    fi
else
    # Default to running auto-bundle
    cd "$PROJECT_ROOT" && source .venv/bin/activate && m1f-update
fi