#!/bin/bash
# Install m1f Git Hooks
# This script installs the m1f git hooks into your project

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're running from a URL (curl/wget)
if [ -z "${BASH_SOURCE[0]}" ] || [ "${BASH_SOURCE[0]}" = "-" ]; then
    # Script is being piped from curl/wget
    # Download the hook directly from GitHub
    HOOK_URL="https://raw.githubusercontent.com/franzundfranz/m1f/main/scripts/hooks/pre-commit"
    USE_REMOTE=true
else
    # Script is being run locally
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    HOOKS_DIR="$SCRIPT_DIR/hooks"
    USE_REMOTE=false
fi

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not in a git repository!${NC}"
    echo "Please run this script from the root of your git project."
    exit 1
fi

# Get the git directory
GIT_DIR=$(git rev-parse --git-dir)

echo -e "${BLUE}Installing m1f Git Hooks...${NC}"

# Function to install a hook
install_hook() {
    local hook_name=$1
    local target_file="$GIT_DIR/hooks/$hook_name"
    
    # Check if hook already exists
    if [ -f "$target_file" ]; then
        echo -e "${YELLOW}Warning: $hook_name hook already exists.${NC}"
        echo -n "Do you want to replace it? (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo "Skipping $hook_name hook."
            return 0
        fi
        # Backup existing hook
        cp "$target_file" "$target_file.backup.$(date +%Y%m%d_%H%M%S)"
        echo "Backed up existing hook to $target_file.backup.*"
    fi
    
    # Install the hook
    if [ "$USE_REMOTE" = true ]; then
        # Download from GitHub
        echo "Downloading pre-commit hook from GitHub..."
        if command -v curl &> /dev/null; then
            curl -sSL "$HOOK_URL" -o "$target_file"
        elif command -v wget &> /dev/null; then
            wget -qO "$target_file" "$HOOK_URL"
        else
            echo -e "${RED}Error: Neither curl nor wget found. Cannot download hook.${NC}"
            return 1
        fi
    else
        # Copy from local directory
        local source_file="$HOOKS_DIR/$hook_name"
        if [ ! -f "$source_file" ]; then
            echo -e "${RED}Error: Hook file $source_file not found!${NC}"
            return 1
        fi
        cp "$source_file" "$target_file"
    fi
    
    chmod +x "$target_file"
    echo -e "${GREEN}✓ Installed $hook_name hook${NC}"
}

# Install pre-commit hook
install_hook "pre-commit"

echo ""
echo -e "${GREEN}Git hooks installation complete!${NC}"
echo ""
echo "The pre-commit hook will automatically:"
echo "  - Format Python files with Black (if installed)"
echo "  - Check Markdown files formatting"
echo "  - Run m1f-update if .m1f.config.yml exists"
echo ""
echo "Prerequisites:"
echo "  - For m1f auto-bundle: .m1f.config.yml must exist in your project root"
echo "  - For m1f development: run from m1f repository with .venv activated"
echo "  - For other projects: install m1f locally (cd /path/to/m1f && pip install -e .)"
echo "  - Optional: Black for Python formatting (pip install black)"
echo "  - Optional: Prettier for Markdown formatting (npm install prettier)"
echo ""
echo "To disable the hook temporarily, use:"
echo "  git commit --no-verify"
echo ""
echo "To uninstall, remove the hook file:"
echo "  rm $GIT_DIR/hooks/pre-commit"