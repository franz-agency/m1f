#!/usr/bin/env bash
# Uninstall script for m1f tools
# This removes m1f from your PATH and cleans up symlinks

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

# Check shell configs
for config in "${SHELL_CONFIGS[@]}"; do
    if grep -q "# m1f tools" "$config" 2>/dev/null; then
        FOUND_IN_CONFIGS+=("$config")
    fi
done

# Check for symlinks in ~/.local/bin
if [ -d "$HOME/.local/bin" ]; then
    for cmd in m1f m1f-s1f m1f-html2md m1f-scrape m1f-token-counter m1f-update m1f-link m1f-help; do
        if [ -L "$HOME/.local/bin/$cmd" ]; then
            # Check if symlink points to our bin directory
            link_target=$(readlink -f "$HOME/.local/bin/$cmd" 2>/dev/null || true)
            if [[ "$link_target" == "$BIN_DIR/"* ]]; then
                FOUND_SYMLINKS+=("$HOME/.local/bin/$cmd")
            fi
        fi
    done
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
if [ ${#FOUND_IN_CONFIGS[@]} -eq 0 ] && [ ${#FOUND_SYMLINKS[@]} -eq 0 ] && [ "$OLD_STYLE_FOUND" = false ]; then
    echo -e "${YELLOW}No m1f installation found.${NC}"
    exit 0
fi

echo "The following will be removed:"
echo

if [ ${#FOUND_IN_CONFIGS[@]} -gt 0 ]; then
    echo "PATH entries in:"
    for config in "${FOUND_IN_CONFIGS[@]}"; do
        echo "  - $config"
    done
    echo
fi

if [ ${#FOUND_SYMLINKS[@]} -gt 0 ]; then
    echo "Symlinks:"
    for link in "${FOUND_SYMLINKS[@]}"; do
        echo "  - $link"
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