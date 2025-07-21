#!/usr/bin/env bash
# Auto-bundle with preset support
# This script is used by VS Code tasks for preset-based bundling

set -e

# Get the script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Function to show help
show_help() {
    cat << EOF
Auto-bundle with preset support for m1f

Usage: $0 [OPTIONS] [COMMAND]

OPTIONS:
    --help, -h              Show this help message
    --preset <file>         Use preset file for configuration
    --group <group>         Process only bundles in specified group

COMMANDS:
    all                     Run auto-bundle for all configured bundles
    focus <bundle>          Run auto-bundle for specific bundle
    preset <file> [group]   Use preset file (legacy syntax)

EXAMPLES:
    $0 all                              # Bundle all configured bundles
    $0 focus docs                       # Bundle only the 'docs' bundle
    $0 --preset wordpress.yml           # Use WordPress preset
    $0 --preset django.yml --group api  # Use Django preset, only API group

This script is used by VS Code tasks for preset-based bundling.
EOF
}

# Default values
PRESET=""
GROUP=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
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
                # shellcheck source=/dev/null
                cd "$PROJECT_ROOT" && source .venv/bin/activate && m1f-update
                exit 0
            elif [ "$1" = "focus" ] && [ -n "$2" ]; then
                # Run auto-bundle for specific bundle
                # shellcheck source=/dev/null
                cd "$PROJECT_ROOT" && source .venv/bin/activate && m1f-update "$2"
                exit 0
            elif [ "$1" = "preset" ] && [ -n "$2" ]; then
                PRESET="$2"
                GROUP="${3:-}"
                shift
                shift
                [ -n "$GROUP" ] && shift
            else
                echo "Error: Invalid arguments"
                echo "Try '$0 --help' for usage information"
                exit 1
            fi
            ;;
        *)
            echo "Error: Unknown option: $1"
            echo "Try '$0 --help' for usage information"
            exit 1
            ;;
    esac
done

# If preset is specified, use m1f with preset
if [ -n "$PRESET" ]; then
    # shellcheck source=/dev/null
    cd "$PROJECT_ROOT" && source .venv/bin/activate
    
    if [ -n "$GROUP" ]; then
        m1f --preset "$PRESET" --preset-group "$GROUP" -o ".ai-context/${GROUP}.txt"
    else
        m1f --preset "$PRESET" -o ".ai-context/preset-bundle.txt"
    fi
else
    # Default to running auto-bundle
    # shellcheck source=/dev/null
    cd "$PROJECT_ROOT" && source .venv/bin/activate && m1f-update
fi