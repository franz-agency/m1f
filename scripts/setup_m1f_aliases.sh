#!/bin/bash

# Setup script for m1f aliases
# This script creates convenient aliases to use m1f from anywhere

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo -e "${BLUE}m1f Alias Setup${NC}"
echo -e "${BLUE}=================${NC}"
echo

# Detect shell
if [ -n "$ZSH_VERSION" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
    SHELL_NAME="zsh"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
    SHELL_NAME="bash"
else
    echo -e "${YELLOW}Warning: Could not detect shell. Assuming bash.${NC}"
    SHELL_CONFIG="$HOME/.bashrc"
    SHELL_NAME="bash"
fi

# Create alias functions
ALIAS_CONTENT="
# m1f tools aliases (added by m1f setup script)
# Project root: $PROJECT_ROOT

# Main m1f command with virtual environment activation
m1f() {
    (cd \"$PROJECT_ROOT\" && source .venv/bin/activate && python tools/m1f.py \"\$@\")
}

# s1f command
s1f() {
    (cd \"$PROJECT_ROOT\" && source .venv/bin/activate && python tools/s1f.py \"\$@\")
}

# html2md command
html2md() {
    (cd \"$PROJECT_ROOT\" && source .venv/bin/activate && python tools/html2md.py \"\$@\")
}

# token-counter command
token-counter() {
    (cd \"$PROJECT_ROOT\" && source .venv/bin/activate && python tools/token_counter.py \"\$@\")
}

# Update m1f bundle files
m1f-update() {
    \"$PROJECT_ROOT/scripts/update_m1f_files.sh\"
}

# Create m1f symlink in current project
m1f-link() {
    if [ ! -d \".m1f\" ]; then
        mkdir -p .m1f
    fi
    
    if [ -e \".m1f/m1f\" ]; then
        echo \"m1f link already exists in .m1f/m1f\"
    else
        ln -s \"$PROJECT_ROOT/.m1f\" .m1f/m1f
        echo \"Created symlink: .m1f/m1f -> $PROJECT_ROOT/.m1f\"
        echo \"You can now access m1f bundles at .m1f/m1f/\"
    fi
}

# Show m1f help
m1f-help() {
    echo \"m1f Tools - Available Commands:\"
    echo \"  m1f          - Main m1f tool for combining files\"
    echo \"  s1f          - Split combined files back to original structure\"
    echo \"  html2md      - Convert HTML to Markdown\"
    echo \"  token-counter - Count tokens in files\"
    echo \"  m1f-update   - Update m1f bundle files\"
    echo \"  m1f-link     - Create symlink to m1f bundles in current project\"
    echo \"  m1f-help     - Show this help message\"
    echo \"\"
    echo \"For detailed help on each tool, use: <tool> --help\"
}
"

# Check if aliases already exist
if grep -q "# m1f tools aliases" "$SHELL_CONFIG" 2>/dev/null; then
    echo -e "${YELLOW}m1f aliases already exist in $SHELL_CONFIG${NC}"
    echo -e "To update, remove the existing m1f section and run this script again."
    exit 1
fi

# Add aliases to shell config
echo -e "${GREEN}Adding m1f aliases to $SHELL_CONFIG...${NC}"
echo "$ALIAS_CONTENT" >> "$SHELL_CONFIG"

# Create a standalone script for non-interactive use
STANDALONE_SCRIPT="$HOME/.local/bin/m1f"
mkdir -p "$HOME/.local/bin"

cat > "$STANDALONE_SCRIPT" << EOF
#!/bin/bash
# Standalone m1f script
cd "$PROJECT_ROOT" && source .venv/bin/activate && python tools/m1f.py "\$@"
EOF

chmod +x "$STANDALONE_SCRIPT"

echo -e "${GREEN}✓ Setup complete!${NC}"
echo
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Reload your shell configuration:"
echo -e "   ${BLUE}source $SHELL_CONFIG${NC}"
echo -e "   Or start a new terminal session"
echo
echo -e "2. Test the installation:"
echo -e "   ${BLUE}m1f --help${NC}"
echo
echo -e "3. In any project, create m1f symlink:"
echo -e "   ${BLUE}m1f-link${NC}"
echo
echo -e "4. View all available commands:"
echo -e "   ${BLUE}m1f-help${NC}"
echo
echo -e "${GREEN}Standalone script also created at: $STANDALONE_SCRIPT${NC}"