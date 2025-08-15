#!/usr/bin/env bash
# Complete installation script for m1f tools
# This script handles the entire setup process after git clone

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Help function
show_help() {
    cat << EOF
${BLUE}m1f Installation Script${NC}
${BLUE}======================${NC}

${YELLOW}USAGE:${NC}
    ./install.sh [OPTIONS]

${YELLOW}DESCRIPTION:${NC}
    This script installs the m1f (Make One File) toolkit and all its dependencies.
    It performs a complete setup including:
    - Creating a Python virtual environment
    - Installing all required dependencies
    - Setting up PATH configuration
    - Creating command shortcuts

${YELLOW}OPTIONS:${NC}
    -h, --help     Show this help message and exit

${YELLOW}REQUIREMENTS:${NC}
    - Python 3.10 or higher
    - pip package manager
    - bash or zsh shell

${YELLOW}EXAMPLES:${NC}
    # Basic installation
    ./scripts/install.sh

    # Run with source to immediately enable commands
    source ./scripts/install.sh

${YELLOW}WHAT IT DOES:${NC}
    1. Creates a Python virtual environment in .venv/
    2. Installs all dependencies from requirements.txt
    3. Tests the m1f installation
    4. Adds m1f/bin to your PATH in ~/.bashrc or ~/.zshrc
    5. Optionally creates symlinks in ~/.local/bin

${YELLOW}AFTER INSTALLATION:${NC}
    - Run 'source ~/.bashrc' (or ~/.zshrc) to activate PATH changes
    - Or simply open a new terminal window
    - Test with 'm1f --help'

${YELLOW}TO UNINSTALL:${NC}
    Run: ./scripts/uninstall.sh

For more information, visit: https://github.com/denoland/m1f
EOF
}

# Check for help flag
for arg in "$@"; do
    case $arg in
        -h|--help)
            show_help
            exit 0
            ;;
    esac
done

# Get the script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
# Use .venv/bin for entry points instead of bin/
VENV_BIN_DIR="$PROJECT_ROOT/.venv/bin"
# Keep old bin dir reference for backwards compatibility
BIN_DIR="$PROJECT_ROOT/bin"

echo -e "${BLUE}m1f Installation${NC}"
echo -e "${BLUE}================${NC}"
echo

# Check if this is an upgrade from an old installation
if [ -d ".venv" ] && [ -d "bin" ] && [ -f "bin/m1f" ]; then
    echo -e "${YELLOW}📦 Upgrade detected: Migrating to Python entry points system${NC}"
    echo
fi

# Check if running in virtual environment already
if [ -n "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Warning: Script is running inside a virtual environment.${NC}"
    echo -e "${YELLOW}It's recommended to run the installer outside of any virtual environment.${NC}"
    echo
fi

# Check Python version
echo -e "${GREEN}Checking Python version...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}Error: Python is not installed. Please install Python 3.10 or higher.${NC}"
    echo -e "${YELLOW}Run './install.sh --help' for more information.${NC}"
    exit 1
fi

# Check Python version is 3.10+
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.minor)")

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]; }; then
    echo -e "${RED}Error: Python 3.10 or higher is required. Found Python $PYTHON_VERSION${NC}"
    echo -e "${YELLOW}Run './install.sh --help' for more information.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
echo

# Step 1: Create virtual environment
echo -e "${GREEN}Step 1: Creating virtual environment...${NC}"
cd "$PROJECT_ROOT"

if [ -d ".venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists.${NC}"
else
    $PYTHON_CMD -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Step 2: Activate virtual environment and install dependencies
echo
echo -e "${GREEN}Step 2: Installing dependencies...${NC}"
# shellcheck source=/dev/null
source .venv/bin/activate

# Upgrade pip first
pip install --upgrade pip --quiet

# Install requirements
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}Error: requirements.txt not found${NC}"
    echo -e "${YELLOW}Run './install.sh --help' for more information.${NC}"
    exit 1
fi

# Install m1f package in editable mode (creates all entry points)
echo -e "${GREEN}Installing m1f package with all tools...${NC}"
pip install -e tools/ --quiet
echo -e "${GREEN}✓ m1f package installed with all entry points${NC}"

# Step 3: Test m1f installation
echo
echo -e "${GREEN}Step 3: Testing m1f installation...${NC}"
# shellcheck source=/dev/null
if source .venv/bin/activate && python -m tools.m1f --version >/dev/null 2>&1; then
    echo -e "${GREEN}✓ m1f is working correctly${NC}"
    
    # Create symlink for main documentation if needed
    if [ -f "m1f/m1f/87_m1f_only_docs.txt" ] && [ ! -e "m1f/m1f.txt" ]; then
        ln -sf "m1f/87_m1f_only_docs.txt" "m1f/m1f.txt"
        echo -e "${GREEN}✓ Created m1f.txt symlink to main documentation${NC}"
    fi
else
    echo -e "${YELLOW}Warning: Could not verify m1f installation${NC}"
    echo -e "${YELLOW}You can test it manually with 'm1f --help'${NC}"
fi

# Step 4: Setup PATH
echo
echo -e "${GREEN}Step 4: Setting up system PATH...${NC}"

# Detect shell
if [ -n "$ZSH_VERSION" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
else
    echo -e "${YELLOW}Warning: Could not detect shell. Assuming bash.${NC}"
    SHELL_CONFIG="$HOME/.bashrc"
fi

# PATH line to add (use venv bin for entry points)
PATH_LINE="export PATH=\"$VENV_BIN_DIR:\$PATH\"  # m1f tools"

# Check if already in PATH
if grep -q "# m1f tools" "$SHELL_CONFIG" 2>/dev/null; then
    # Update existing PATH entry if it points to old bin/ directory
    if grep -q "$BIN_DIR" "$SHELL_CONFIG" 2>/dev/null; then
        echo -e "${YELLOW}🔄 Detected old installation - upgrading to new entry point system${NC}"
        sed -i.bak "s|$BIN_DIR|$VENV_BIN_DIR|g" "$SHELL_CONFIG"
        echo -e "${GREEN}✓ Updated PATH from bin/ to .venv/bin/${NC}"
        echo -e "${GREEN}✓ Your tools will now use Python entry points${NC}"
        
        # Clean up old symlinks if they exist
        if [ -d "$HOME/.local/bin" ]; then
            echo -e "${YELLOW}Cleaning up old symlinks...${NC}"
            for old_link in "$HOME/.local/bin"/m1f*; do
                if [ -L "$old_link" ] && readlink "$old_link" | grep -q "$BIN_DIR"; then
                    rm -f "$old_link"
                fi
            done
            if [ -L "$HOME/.local/bin/s1f" ] && readlink "$HOME/.local/bin/s1f" | grep -q "$BIN_DIR"; then
                rm -f "$HOME/.local/bin/s1f"
            fi
            echo -e "${GREEN}✓ Old symlinks removed${NC}"
        fi
    else
        echo -e "${YELLOW}m1f tools already in PATH${NC}"
    fi
else
    # Backup shell config
    cp "$SHELL_CONFIG" "$SHELL_CONFIG.m1f-backup-$(date +%Y%m%d%H%M%S)"
    
    # Add to PATH
    echo "" >> "$SHELL_CONFIG"
    echo "$PATH_LINE" >> "$SHELL_CONFIG"
    echo -e "${GREEN}✓ Added m1f to PATH in $SHELL_CONFIG${NC}"
fi

# Step 5: Create symlinks (optional) - now using entry points from venv
if [ -d "$HOME/.local/bin" ] || mkdir -p "$HOME/.local/bin" 2>/dev/null; then
    # Check if any m1f symlinks already exist
    if [ -L "$HOME/.local/bin/m1f" ]; then
        # Update existing symlinks to point to venv entry points
        echo -e "${YELLOW}Updating symlinks in ~/.local/bin to use entry points...${NC}"
        # Remove old symlinks
        rm -f "$HOME/.local/bin"/m1f*
        # Create new symlinks to venv entry points
        for cmd in "$VENV_BIN_DIR"/m1f*; do
            if [ -f "$cmd" ]; then
                cmd_name=$(basename "$cmd")
                ln -sf "$cmd" "$HOME/.local/bin/$cmd_name"
            fi
        done
        echo -e "${GREEN}✓ Symlinks updated to use Python entry points${NC}"
    else
        echo
        echo -e "${YELLOW}Creating symlinks in ~/.local/bin for system-wide access...${NC}"
        for cmd in "$VENV_BIN_DIR"/m1f*; do
            if [ -f "$cmd" ]; then
                cmd_name=$(basename "$cmd")
                ln -sf "$cmd" "$HOME/.local/bin/$cmd_name"
            fi
        done
        # Also create symlinks for s1f
        if [ -f "$VENV_BIN_DIR/s1f" ]; then
            ln -sf "$VENV_BIN_DIR/s1f" "$HOME/.local/bin/s1f"
        fi
        echo -e "${GREEN}✓ Symlinks created${NC}"
        
        # Check if ~/.local/bin is in PATH
        if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
            echo -e "${YELLOW}Note: ~/.local/bin is not in your PATH. You may want to add it.${NC}"
        fi
    fi
fi

# Installation complete
echo
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ Installation complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo
echo -e "${YELLOW}Available commands:${NC}"
echo "  • m1f               - Main m1f tool for combining files"
echo "  • m1f-s1f           - Split combined files back to original structure"
echo "  • m1f-html2md       - Convert HTML to Markdown"
echo "  • m1f-scrape        - Download websites for offline viewing"
echo "  • m1f-research      - AI-powered research and content analysis"
echo "  • m1f-token-counter - Count tokens in files"
echo "  • m1f-update        - Regenerate m1f bundles"
echo "  • m1f-init          - Initialize m1f for your project"
echo "  • m1f-claude        - Advanced setup with topic-specific bundles"
echo "  • m1f-help          - Show available commands"
echo

# Try to make commands available immediately
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    # Script is being sourced, we can update the current shell
    export PATH="$VENV_BIN_DIR:$PATH"
    echo -e "${GREEN}✓ Commands are available immediately in this shell${NC}"
    echo
    echo -e "${YELLOW}Test installation:${NC}"
    echo -e "  ${BLUE}m1f --help${NC}"
else
    # Script is being executed, we can't update the parent shell
    echo -e "${YELLOW}To activate m1f commands:${NC}"
    echo -e "  ${BLUE}source $SHELL_CONFIG${NC}  # Or open a new terminal"
    echo
    echo -e "${YELLOW}Or run the installer with source:${NC}"
    echo -e "  ${BLUE}source ./scripts/install.sh${NC}"
fi

echo
echo -e "${YELLOW}To uninstall:${NC}"
echo -e "  ${BLUE}$SCRIPT_DIR/uninstall.sh${NC}"