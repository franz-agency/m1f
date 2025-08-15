#!/usr/bin/env bash
# Uninstall script for m1f tools
# This removes m1f from your system and cleans up all components

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
${BLUE}m1f Uninstallation Script${NC}
${BLUE}========================${NC}

${YELLOW}USAGE:${NC}
    ./uninstall.sh [OPTIONS]

${YELLOW}DESCRIPTION:${NC}
    This script safely removes the m1f (Make One File) toolkit from your system.
    It cleans up all components installed by the install.sh script.

${YELLOW}OPTIONS:${NC}
    -h, --help     Show this help message and exit

${YELLOW}WHAT IT REMOVES:${NC}
    - PATH entries added to shell configuration files
    - Symbolic links in ~/.local/bin
    - m1f pip package (editable installation)
    - Python virtual environment (optional)
    - Generated m1f bundles (optional)
    - Creates backups of modified shell configs

${YELLOW}INTERACTIVE MODE:${NC}
    The script will ask for confirmation before:
    - Proceeding with uninstallation
    - Removing generated m1f bundles
    - Removing the Python virtual environment

${YELLOW}SAFETY FEATURES:${NC}
    - Creates backups of shell configuration files
    - Only removes symlinks that point to m1f binaries
    - Prompts for confirmation before destructive actions

${YELLOW}EXAMPLES:${NC}
    # Run the uninstaller
    ./scripts/uninstall.sh

    # Show help
    ./scripts/uninstall.sh --help

${YELLOW}AFTER UNINSTALLATION:${NC}
    - Reload your shell or open a new terminal
    - Shell config backups are saved with .m1f-backup suffix

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
BIN_DIR="$PROJECT_ROOT/bin"
VENV_DIR="$PROJECT_ROOT/.venv"

echo -e "${BLUE}m1f Uninstallation${NC}"
echo -e "${BLUE}==================${NC}"
echo

# Detect shell configs to check
SHELL_CONFIGS=()
[ -f "$HOME/.bashrc" ] && SHELL_CONFIGS+=("$HOME/.bashrc")
[ -f "$HOME/.zshrc" ] && SHELL_CONFIGS+=("$HOME/.zshrc")
[ -f "$HOME/.bash_profile" ] && SHELL_CONFIGS+=("$HOME/.bash_profile")

# Track what we'll remove
FOUND_IN_CONFIGS=()
FOUND_SYMLINKS=()
COMPONENTS_TO_REMOVE=()

# Check for virtual environment
if [ -d "$VENV_DIR" ]; then
    COMPONENTS_TO_REMOVE+=("Python virtual environment (.venv)")
fi

# Check shell configs
for config in "${SHELL_CONFIGS[@]}"; do
    if grep -q "# m1f tools" "$config" 2>/dev/null; then
        FOUND_IN_CONFIGS+=("$config")
    fi
done

# Check for symlinks in ~/.local/bin
if [ -d "$HOME/.local/bin" ]; then
    for cmd in m1f m1f-s1f m1f-html2md m1f-scrape m1f-research m1f-token-counter m1f-update m1f-help m1f-init m1f-claude; do
        if [ -L "$HOME/.local/bin/$cmd" ]; then
            # Check if symlink points to our bin directory
            link_target=$(readlink -f "$HOME/.local/bin/$cmd" 2>/dev/null || true)
            if [[ "$link_target" == "$BIN_DIR/"* ]]; then
                FOUND_SYMLINKS+=("$HOME/.local/bin/$cmd")
            fi
        fi
    done
fi

# Check for generated bundles
BUNDLE_FILES=()
if [ -d "$PROJECT_ROOT/m1f" ]; then
    while IFS= read -r -d '' file; do
        # Skip config files
        if [[ ! "$file" =~ config ]]; then
            BUNDLE_FILES+=("$file")
        fi
    done < <(find "$PROJECT_ROOT/m1f" -name "*.txt" -type f -print0)
    if [ ${#BUNDLE_FILES[@]} -gt 0 ]; then
        COMPONENTS_TO_REMOVE+=("Generated m1f bundles (${#BUNDLE_FILES[@]} files)")
    fi
fi

# Check for pip-installed package
PIP_PACKAGE_FOUND=false
if [ -d "$VENV_DIR" ]; then
    # Check if m1f is installed as a pip package
    if "$VENV_DIR/bin/python" -c "import pkg_resources; pkg_resources.get_distribution('m1f')" >/dev/null 2>&1; then
        PIP_PACKAGE_FOUND=true
        COMPONENTS_TO_REMOVE+=("m1f pip package (editable installation)")
    fi
fi

# Check for old-style aliases
OLD_STYLE_FOUND=false
for config in "${SHELL_CONFIGS[@]}"; do
    if grep -q "# m1f tools aliases" "$config" 2>/dev/null; then
        OLD_STYLE_FOUND=true
        echo -e "${YELLOW}Found old-style m1f aliases in $config${NC}"
    fi
done

# Show what will be removed
if [ ${#FOUND_IN_CONFIGS[@]} -eq 0 ] && [ ${#FOUND_SYMLINKS[@]} -eq 0 ] && [ "$OLD_STYLE_FOUND" = false ] && [ ${#COMPONENTS_TO_REMOVE[@]} -eq 0 ]; then
    echo -e "${YELLOW}No m1f installation found.${NC}"
    echo -e "${YELLOW}Run './uninstall.sh --help' for more information.${NC}"
    exit 0
fi

echo "The following will be removed:"
echo

if [ ${#COMPONENTS_TO_REMOVE[@]} -gt 0 ]; then
    echo "Components:"
    for component in "${COMPONENTS_TO_REMOVE[@]}"; do
        echo "  • $component"
    done
    echo
fi

if [ ${#FOUND_IN_CONFIGS[@]} -gt 0 ]; then
    echo "PATH entries in:"
    for config in "${FOUND_IN_CONFIGS[@]}"; do
        echo "  • $config"
    done
    echo
fi

if [ ${#FOUND_SYMLINKS[@]} -gt 0 ]; then
    echo "Symlinks:"
    for link in "${FOUND_SYMLINKS[@]}"; do
        echo "  • $link"
    done
    echo
fi

if [ "$OLD_STYLE_FOUND" = true ]; then
    echo -e "${YELLOW}Note: Old-style aliases found. Run the old setup script with remove option to clean those up.${NC}"
    echo
fi

# Ask for confirmation
echo -e "${YELLOW}Do you want to continue with uninstallation? (y/N)${NC}"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

# Remove from shell configs
for config in "${FOUND_IN_CONFIGS[@]}"; do
    echo -e "${GREEN}Removing m1f from $config...${NC}"
    # Create backup
    cp "$config" "$config.m1f-backup"
    # Remove the PATH line
    sed -i '/# m1f tools$/d' "$config"
    # Also remove any empty lines that might be left
    sed -i '/^[[:space:]]*$/N;/\n[[:space:]]*$/d' "$config"
done

# Remove symlinks
for link in "${FOUND_SYMLINKS[@]}"; do
    echo -e "${GREEN}Removing symlink: $link${NC}"
    rm -f "$link"
done

# Ask about generated bundles
if [ ${#BUNDLE_FILES[@]} -gt 0 ]; then
    echo
    echo -e "${YELLOW}Do you want to remove generated m1f bundles? (y/N)${NC}"
    read -r bundle_response
    if [[ "$bundle_response" =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Removing generated bundles...${NC}"
        for file in "${BUNDLE_FILES[@]}"; do
            rm -f "$file"
        done
        echo -e "${GREEN}✓ Bundles removed${NC}"
    else
        echo "Keeping generated bundles"
    fi
fi

# Remove pip package if found
if [ "$PIP_PACKAGE_FOUND" = true ] && [ -d "$VENV_DIR" ]; then
    echo
    echo -e "${GREEN}Uninstalling m1f pip package...${NC}"
    if "$VENV_DIR/bin/pip" uninstall m1f -y >/dev/null 2>&1; then
        echo -e "${GREEN}✓ m1f package uninstalled${NC}"
    else
        echo -e "${YELLOW}Warning: Could not uninstall m1f package automatically${NC}"
        echo -e "${YELLOW}You may need to run: $VENV_DIR/bin/pip uninstall m1f${NC}"
    fi
fi

# Ask about virtual environment
if [ -d "$VENV_DIR" ]; then
    echo
    echo -e "${YELLOW}Do you want to remove the Python virtual environment? (y/N)${NC}"
    read -r venv_response
    if [[ "$venv_response" =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Removing virtual environment...${NC}"
        # Deactivate if we're in the virtual environment
        if [ "$VIRTUAL_ENV" = "$VENV_DIR" ]; then
            deactivate 2>/dev/null || true
        fi
        rm -rf "$VENV_DIR"
        echo -e "${GREEN}✓ Virtual environment removed${NC}"
    else
        echo "Keeping virtual environment"
    fi
fi

echo
echo -e "${GREEN}✓ Uninstallation complete!${NC}"
echo

if [ ${#FOUND_IN_CONFIGS[@]} -gt 0 ]; then
    echo -e "${YELLOW}Please reload your shell or start a new terminal for changes to take effect.${NC}"
fi

if [ "$OLD_STYLE_FOUND" = true ]; then
    echo
    echo -e "${YELLOW}To remove old-style aliases, run:${NC}"
    echo -e "  ${BLUE}$SCRIPT_DIR/setup_m1f_aliases.sh${NC} (and follow removal instructions)"
fi