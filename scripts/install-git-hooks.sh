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

# Function to show help
show_help() {
    cat << EOF
m1f Git Hooks Installer

Usage: $0 [OPTIONS]

OPTIONS:
    --help, -h    Show this help message

DESCRIPTION:
    This script installs m1f Git hooks into your project.
    
    Two types of hooks are available:
    1. Internal - For m1f project development
       • Formats Python files with Black
       • Formats Markdown files with Prettier
       • Runs m1f auto-bundle
    
    2. External - For projects using m1f
       • Runs m1f auto-bundle when .m1f.config.yml exists

    The script will automatically detect your project type and offer
    the appropriate hook option(s).

REQUIREMENTS:
    - Must be run from within a Git repository
    - m1f must be installed locally
    - For internal hooks: Black and Prettier (optional)

EXAMPLES:
    $0              # Interactive installation
    
To uninstall:
    rm .git/hooks/pre-commit
    rm .git/hooks/pre-commit.ps1  # Windows only

For more information, see:
    docs/05_development/56_git_hooks_setup.md
EOF
}

# Check for help flag
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    show_help
    exit 0
fi

# This script must be run from a local m1f installation
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
HOOKS_DIR="$SCRIPT_DIR/hooks"

# Check if hooks directory exists
if [ ! -d "$HOOKS_DIR" ]; then
    echo -e "${RED}Error: Hooks directory not found!${NC}"
    echo "This script must be run from a local m1f installation."
    echo "Please clone m1f first: git clone https://github.com/franz-agency/m1f.git"
    echo -e "${YELLOW}Run '$0 --help' for more information.${NC}"
    exit 1
fi

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not in a git repository!${NC}"
    echo "Please run this script from the root of your git project."
    echo -e "${YELLOW}Run '$0 --help' for more information.${NC}"
    exit 1
fi

GIT_DIR=$(git rev-parse --git-dir)

# Detect if we're in the m1f project itself
IS_M1F_PROJECT=false
if [ -f "tools/m1f.py" ] && [ -f ".m1f.config.yml" ] && [ -d "scripts/hooks" ]; then
    IS_M1F_PROJECT=true
fi

# Detect operating system
case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*|Windows_NT)
        IS_WINDOWS=true
        HOOK_EXTENSION=".ps1"
        ;;
    *)
        IS_WINDOWS=false
        HOOK_EXTENSION=""
        ;;
esac

echo -e "${BLUE}m1f Git Hook Installer${NC}"
echo -e "${BLUE}======================${NC}"
echo

# Function to download or copy hook
install_hook() {
    local hook_type=$1
    local target_file="$GIT_DIR/hooks/pre-commit"
    
    if [ "$IS_WINDOWS" = true ]; then
        # On Windows, install PowerShell wrapper
        cat > "$target_file" << 'EOF'
#!/bin/sh
# Git hook wrapper for PowerShell on Windows
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(dirname "$0")/pre-commit.ps1"
exit $?
EOF
        chmod +x "$target_file"
        target_file="$GIT_DIR/hooks/pre-commit.ps1"
    fi
    
    # Copy from local directory
    local source_file="$HOOKS_DIR/pre-commit-${hook_type}${HOOK_EXTENSION}"
    if [ ! -f "$source_file" ]; then
        echo -e "${RED}Error: Hook file not found: $source_file${NC}"
        echo -e "${YELLOW}Run '$0 --help' for more information.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Installing ${hook_type} hook...${NC}"
    cp "$source_file" "$target_file"
    
    # Make executable (not needed for PowerShell scripts)
    if [ "$IS_WINDOWS" = false ]; then
        chmod +x "$target_file"
    fi
    
    echo -e "${GREEN}✓ Installed ${hook_type} pre-commit hook${NC}"
}

# Show hook options
echo "Available hooks:"
echo
if [ "$IS_M1F_PROJECT" = true ]; then
    echo "  1) Internal - For m1f project development"
    echo "     • Formats Python files with Black"
    echo "     • Formats Markdown files with Prettier"
    echo "     • Runs m1f auto-bundle"
    echo
    echo "  2) External - For projects using m1f"
    echo "     • Runs m1f auto-bundle only"
    echo
    echo -n "Which hook would you like to install? [1/2] (default: 1): "
    read -r choice
    
    case "$choice" in
        2)
            HOOK_TYPE="external"
            ;;
        *)
            HOOK_TYPE="internal"
            ;;
    esac
else
    echo "  • External - For projects using m1f"
    echo "    Runs m1f auto-bundle when .m1f.config.yml exists"
    echo
    HOOK_TYPE="external"
fi

# Check for existing hook
if [ -f "$GIT_DIR/hooks/pre-commit" ] || [ -f "$GIT_DIR/hooks/pre-commit.ps1" ]; then
    echo -e "${YELLOW}Warning: A pre-commit hook already exists.${NC}"
    echo -n "Do you want to replace it? [y/N]: "
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
fi

# Install the hook
install_hook "$HOOK_TYPE"

echo
echo -e "${GREEN}✓ Git hook installation complete!${NC}"
echo

# Show platform-specific instructions
if [ "$IS_WINDOWS" = true ]; then
    echo "The PowerShell pre-commit hook has been installed."
    echo
fi

# Show usage instructions based on hook type
if [ "$HOOK_TYPE" = "internal" ]; then
    echo "The internal hook will:"
    echo "  - Format Python files with Black (if installed)"
    echo "  - Format Markdown files with Prettier (if installed)"
    echo "  - Run m1f auto-bundle"
    echo
    echo "Requirements:"
    echo "  - Black: pip install black"
    echo "  - Prettier: npm install -g prettier"
    echo "  - m1f: Already available in this project"
else
    echo "The external hook will:"
    echo "  - Run m1f auto-bundle if .m1f.config.yml exists"
    echo
    echo "Requirements:"
    echo "  - m1f installed and available in PATH"
    echo "  - .m1f.config.yml in your project root"
fi

echo
echo "To disable the hook temporarily, use:"
echo "  git commit --no-verify"
echo
echo "To uninstall, remove the hook file:"
if [ "$IS_WINDOWS" = true ]; then
    echo "  rm $GIT_DIR/hooks/pre-commit"
    echo "  rm $GIT_DIR/hooks/pre-commit.ps1"
else
    echo "  rm $GIT_DIR/hooks/pre-commit"
fi