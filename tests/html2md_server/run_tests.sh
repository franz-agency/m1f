#!/bin/bash
# Run HTML2MD Test Suite

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}HTML2MD Test Suite Runner${NC}"
echo "=========================="

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}Warning: No virtual environment detected${NC}"
    echo "Consider activating a virtual environment first"
    echo ""
fi

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install -r tests/html2md_server/requirements.txt

# Start test server in background
echo -e "${GREEN}Starting test server...${NC}"
python tests/html2md_server/server.py &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Stopping test server...${NC}"
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true
}

# Set trap to cleanup on exit
trap cleanup EXIT

# Check if server is running
if ! curl -s http://localhost:8090 > /dev/null; then
    echo -e "${RED}Error: Test server failed to start${NC}"
    exit 1
fi

echo -e "${GREEN}Test server running at http://localhost:8090${NC}"
echo ""

# Run tests
echo -e "${GREEN}Running tests...${NC}"
echo "================"

# Run pytest with options
pytest tests/test_html2md_server.py \
    -v \
    --tb=short \
    --color=yes \
    --cov=tools.mf1-html2md \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    "$@"

TEST_EXIT_CODE=$?

# Show results
echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo -e "Coverage report generated in: ${YELLOW}htmlcov/index.html${NC}"
else
    echo -e "${RED}✗ Some tests failed${NC}"
fi

# Optional: Open coverage report
if [ $TEST_EXIT_CODE -eq 0 ] && command -v xdg-open &> /dev/null; then
    read -p "Open coverage report in browser? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        xdg-open htmlcov/index.html
    fi
fi

exit $TEST_EXIT_CODE 