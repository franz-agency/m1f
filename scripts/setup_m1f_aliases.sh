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

# Explain what this script does
echo "This script will add the following aliases to your shell configuration:"
echo ""
echo "  • m1f          - Main m1f tool for combining files"
echo "  • s1f          - Split combined files back to original structure"
echo "  • html2md      - Convert HTML to Markdown"
echo "  • webscraper   - Download websites for offline viewing"
echo "  • token-counter - Count tokens in files"
echo "  • m1f-update   - Regenerate m1f bundles"
echo "  • m1f-link     - Create symlinks to m1f bundles"
echo "  • m1f-help     - Show available commands"
echo ""
echo "These aliases will be added to your shell configuration file."
echo ""

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

# Create alias content that sources the external file
ALIAS_CONTENT="
# m1f tools aliases (added by m1f setup script)
# Source the m1f aliases file
if [ -f \"$PROJECT_ROOT/scripts/m1f_aliases.sh\" ]; then
    source \"$PROJECT_ROOT/scripts/m1f_aliases.sh\"
fi
"

# Check if aliases already exist
if grep -q "# m1f tools aliases" "$SHELL_CONFIG" 2>/dev/null; then
    echo -e "${YELLOW}m1f aliases already exist in $SHELL_CONFIG${NC}"
    echo -e "To update, remove the existing m1f section and run this script again."
    echo ""
    echo -e "${YELLOW}To remove the aliases:${NC}"
    echo "1. Open $SHELL_CONFIG in your editor"
    echo "2. Find and remove the m1f source line (about 3-4 lines)"
    echo "3. Save the file and reload your shell"
    echo ""
    echo "Or run: sed -i '/# m1f tools aliases/,/^$/d' $SHELL_CONFIG"
    exit 1
fi

# Show what will be modified
echo -e "${YELLOW}Shell configuration file:${NC} $SHELL_CONFIG"
echo -e "${YELLOW}Project root:${NC} $PROJECT_ROOT"
echo ""

# Ask for confirmation
echo -e "${YELLOW}Do you want to continue? (y/N)${NC}"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "Setup cancelled."
    exit 0
fi

# Add aliases to shell config
echo ""
echo -e "${GREEN}Adding m1f aliases to $SHELL_CONFIG...${NC}"
echo "$ALIAS_CONTENT" >> "$SHELL_CONFIG"

# Create a standalone script for non-interactive use
STANDALONE_SCRIPT="$HOME/.local/bin/m1f"
mkdir -p "$HOME/.local/bin"

cat > "$STANDALONE_SCRIPT" << EOF
#!/bin/bash
# Standalone m1f script
cd "$PROJECT_ROOT" && source .venv/bin/activate && python -m tools.m1f "\$@"
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
echo
echo -e "${YELLOW}To remove the aliases later:${NC}"
echo "1. Open $SHELL_CONFIG in your editor"
echo "2. Find and remove the m1f source line (about 3-4 lines)"
echo "3. Save the file and reload your shell"
echo "4. Optionally remove: $STANDALONE_SCRIPT"
echo ""
echo "Or run: sed -i '/# m1f tools aliases/,/^$/d' $SHELL_CONFIG"