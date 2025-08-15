#!/bin/bash
# Test script to verify all m1f tools work globally from any directory

set -e  # Exit on error

echo "==================================="
echo "m1f Global Tool Test Suite"
echo "==================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test a command
test_command() {
    local cmd="$1"
    local args="$2"
    local expected="$3"
    
    echo -n "Testing $cmd $args ... "
    
    if output=$($cmd $args 2>&1); then
        if [[ -z "$expected" ]] || [[ "$output" == *"$expected"* ]]; then
            echo -e "${GREEN}✓ PASSED${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠ Output mismatch${NC}"
            echo "Expected: $expected"
            echo "Got: $output"
            return 1
        fi
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "Error: $output"
        return 1
    fi
}

# Create a test directory
TEST_DIR="/tmp/m1f_test_$$"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

echo "Test directory: $TEST_DIR"
echo ""

# Create some test files
echo "Creating test files..."
mkdir -p src docs
echo "# Test Project" > README.md
echo "def main(): pass" > src/main.py
echo "# API Documentation" > docs/api.md
echo ""

echo "=== Testing Core Tools ==="
echo ""

# Test m1f
test_command "m1f" "--version" "m1f"

# Test m1f-init
test_command "m1f-init" "--no-symlink" "Quick Setup Complete"

# Test m1f-update (should work after init)
test_command "m1f-update" "" "Creating bundle"

# Test m1f-help
test_command "m1f-help" "" "m1f"

# Test m1f-claude
test_command "m1f-claude" "--help" "m1f-claude"

# Test m1f basic bundling
test_command "m1f" "-s . -o test_bundle.txt --quiet" ""

# Test s1f extraction
echo "Testing s1f extraction..."
if m1f -s . -o bundle.txt --quiet; then
    test_command "s1f" "bundle.txt extracted/" ""
else
    echo -e "${RED}✗ Failed to create bundle for s1f test${NC}"
fi

# Test m1f-token-counter
test_command "m1f-token-counter" "--help" "token"

echo ""
echo "=== Testing Advanced Tools ==="
echo ""

# Test m1f-html2md
test_command "m1f-html2md" "--help" "html2md"

# Test m1f-scrape
test_command "m1f-scrape" "--help" "scrape"

# Test m1f-research
test_command "m1f-research" "--help" "research"

echo ""
echo "=== Testing from Different Directories ==="
echo ""

# Test from home directory
cd ~
test_command "m1f" "--version" "m1f"

# Test from root tmp
cd /tmp
test_command "m1f" "--version" "m1f"

# Cleanup
echo ""
echo "Cleaning up test directory..."
rm -rf "$TEST_DIR"

echo ""
echo "==================================="
echo -e "${GREEN}All tests completed!${NC}"
echo "==================================="