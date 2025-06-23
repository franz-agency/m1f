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

# Get the script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
BIN_DIR="$PROJECT_ROOT/bin"

echo -e "${BLUE}m1f Installation${NC}"
echo -e "${BLUE}================${NC}"
echo

# Check Python version
echo -e "${GREEN}Checking Python version...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}Error: Python is not installed. Please install Python 3.10 or higher.${NC}"
    exit 1
fi

# Check Python version is 3.10+
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.minor)")

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo -e "${RED}Error: Python 3.10 or higher is required. Found Python $PYTHON_VERSION${NC}"
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
source .venv/bin/activate

# Upgrade pip first
pip install --upgrade pip --quiet

# Install requirements
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}Error: requirements.txt not found${NC}"
    exit 1
fi

# Step 3: Generate initial m1f bundles
echo
echo -e "${GREEN}Step 3: Generating initial m1f bundles...${NC}"
source .venv/bin/activate && python -m tools.m1f auto-bundle --quiet
echo -e "${GREEN}✓ Initial bundles generated${NC}"

# Step 4: Setup PATH
echo
echo -e "${GREEN}Step 4: Setting up system PATH...${NC}"

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

# PATH line to add
PATH_LINE="export PATH=\"$BIN_DIR:\$PATH\"  # m1f tools"

# Check if already in PATH
if grep -q "# m1f tools" "$SHELL_CONFIG" 2>/dev/null; then
    echo -e "${YELLOW}m1f tools already in PATH${NC}"
else
    # Add to PATH
    echo "" >> "$SHELL_CONFIG"
    echo "$PATH_LINE" >> "$SHELL_CONFIG"
    echo -e "${GREEN}✓ Added m1f to PATH in $SHELL_CONFIG${NC}"
fi

# Step 5: Create symlinks (optional)
if [ -d "$HOME/.local/bin" ]; then
    # Check if any m1f symlinks already exist
    if [ -L "$HOME/.local/bin/m1f" ]; then
        echo -e "${YELLOW}Symlinks already exist in ~/.local/bin${NC}"
    else
        echo
        echo -e "${YELLOW}Creating symlinks in ~/.local/bin for system-wide access...${NC}"
        mkdir -p "$HOME/.local/bin"
        for cmd in "$BIN_DIR"/*; do
            if [ -x "$cmd" ]; then
                cmd_name=$(basename "$cmd")
                ln -sf "$cmd" "$HOME/.local/bin/$cmd_name"
            fi
        done
        echo -e "${GREEN}✓ Symlinks created${NC}"
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
echo "  • m1f-token-counter - Count tokens in files"
echo "  • m1f-update        - Regenerate m1f bundles"
echo "  • m1f-init          - Initialize m1f for your project"
echo "  • m1f-claude        - Advanced setup with topic-specific bundles"
echo "  • m1f-help          - Show available commands"
echo

# Try to make commands available immediately
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    # Script is being sourced, we can update the current shell
    export PATH="$BIN_DIR:$PATH"
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