#!/bin/bash
# m1f tools aliases
# This file is sourced by your shell configuration

# Get the directory where this script is located
M1F_SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
M1F_PROJECT_ROOT="$(cd "$M1F_SCRIPTS_DIR/.." && pwd)"

# Main m1f command with virtual environment activation
m1f() {
    (cd "$M1F_PROJECT_ROOT" && source .venv/bin/activate && python -m tools.m1f "$@")
}

# m1f-s1f command
m1f-s1f() {
    (cd "$M1F_PROJECT_ROOT" && source .venv/bin/activate && python -m tools.s1f "$@")
}

# m1f-html2md command
m1f-html2md() {
    (cd "$M1F_PROJECT_ROOT" && source .venv/bin/activate && python -m tools.html2md "$@")
}

# m1f-scrape command
m1f-scrape() {
    (cd "$M1F_PROJECT_ROOT" && source .venv/bin/activate && python -m tools.webscraper "$@")
}

# m1f-token-counter command
m1f-token-counter() {
    (cd "$M1F_PROJECT_ROOT" && source .venv/bin/activate && python tools/token_counter.py "$@")
}

# Update m1f bundle files
m1f-update() {
    (cd "$M1F_PROJECT_ROOT" && source .venv/bin/activate && python -m tools.m1f auto-bundle "$@")
}

# Create m1f symlink in current project
m1f-link() {
    if [ ! -d ".m1f" ]; then
        mkdir -p .m1f
    fi
    
    if [ -e ".m1f/m1f" ]; then
        echo "m1f link already exists in .m1f/m1f"
    else
        ln -s "$M1F_PROJECT_ROOT/.m1f" .m1f/m1f
        echo "Created symlink: .m1f/m1f -> $M1F_PROJECT_ROOT/.m1f"
        echo "You can now access m1f bundles at .m1f/m1f/"
    fi
}

# Show m1f help
m1f-help() {
    echo "m1f Tools - Available Commands:"
    echo "  m1f               - Main m1f tool for combining files"
    echo "  m1f-s1f           - Split combined files back to original structure"
    echo "  m1f-html2md       - Convert HTML to Markdown"
    echo "  m1f-scrape        - Download websites for offline viewing"
    echo "  m1f-token-counter - Count tokens in files"
    echo "  m1f-update        - Update m1f bundle files"
    echo "  m1f-link          - Create symlink to m1f bundles in current project"
    echo "  m1f-help          - Show this help message"
    echo ""
    echo "For detailed help on each tool, use: <tool> --help"
}

# Export functions so they're available in subshells
export -f m1f m1f-s1f m1f-html2md m1f-scrape m1f-token-counter m1f-update m1f-link m1f-help