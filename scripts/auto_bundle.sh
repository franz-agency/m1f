#!/bin/bash
# Auto Bundle Script for m1f Projects
# Automatically creates and updates m1f bundles for different project aspects

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory (works even with symlinks)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
M1F_DIR=".m1f"
M1F_TOOL="$PROJECT_ROOT/tools/m1f.py"
VENV_PATH="$PROJECT_ROOT/.venv"

# Bundle configurations
declare -A BUNDLES=(
    ["docs"]="Documentation bundle"
    ["src"]="Source code bundle"
    ["tests"]="Test files bundle"
    ["complete"]="Complete project bundle"
)

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to activate virtual environment
activate_venv() {
    if [ -d "$VENV_PATH" ]; then
        source "$VENV_PATH/bin/activate"
    else
        print_warning "Virtual environment not found at $VENV_PATH"
    fi
}

# Function to create m1f directory structure
setup_m1f_directory() {
    print_info "Setting up $M1F_DIR directory structure..."
    
    mkdir -p "$PROJECT_ROOT/$M1F_DIR"/{docs,src,tests,complete}
    
    # Create .gitignore if it doesn't exist
    if [ ! -f "$PROJECT_ROOT/$M1F_DIR/.gitignore" ]; then
        cat > "$PROJECT_ROOT/$M1F_DIR/.gitignore" << EOF
# Auto-generated m1f bundles
*.m1f
*.m1f.txt
*_filelist.txt
*_dirlist.txt
*.log

# But track the structure
!.gitkeep
EOF
    fi
    
    # Create .gitkeep files to preserve directory structure
    touch "$PROJECT_ROOT/$M1F_DIR"/{docs,src,tests,complete}/.gitkeep
    
    print_success "$M1F_DIR directory structure created"
}

# Function to create documentation bundle
create_docs_bundle() {
    local output_dir="$PROJECT_ROOT/$M1F_DIR/docs"
    local output_file="$output_dir/manual.m1f.txt"
    
    print_info "Creating documentation bundle..."
    
    # Bundle all markdown and text documentation
    python "$M1F_TOOL" \
        -s "$PROJECT_ROOT" \
        -o "$output_file" \
        --include-extensions .md .rst .txt \
        --excludes "**/node_modules/**" "**/.venv/**" "**/.*" \
        --separator-style Markdown \
        --minimal-output \
        -f
    
    # Also create a separate API docs bundle if docs/ exists
    if [ -d "$PROJECT_ROOT/docs" ]; then
        python "$M1F_TOOL" \
            -s "$PROJECT_ROOT/docs" \
            -o "$output_dir/api_docs.m1f.txt" \
            --include-extensions .md .rst .txt \
            --separator-style Markdown \
            --minimal-output \
            -f
    fi
    
    print_success "Documentation bundle created: $output_file"
}

# Function to create source code bundle
create_src_bundle() {
    local output_dir="$PROJECT_ROOT/$M1F_DIR/src"
    local output_file="$output_dir/source.m1f.txt"
    
    print_info "Creating source code bundle..."
    
    # Bundle all Python source files (excluding tests)
    python "$M1F_TOOL" \
        -s "$PROJECT_ROOT" \
        -o "$output_file" \
        --include-extensions .py \
        --excludes "**/test_*.py" "**/*_test.py" "**/tests/**" "**/node_modules/**" "**/.venv/**" "**/.*" \
        --separator-style Detailed \
        --minimal-output \
        -f
    
    # Create separate bundles for specific components if they exist
    if [ -d "$PROJECT_ROOT/tools" ]; then
        python "$M1F_TOOL" \
            -s "$PROJECT_ROOT/tools" \
            -o "$output_dir/tools.m1f.txt" \
            --include-extensions .py \
            --excludes "**/test_*.py" "**/*_test.py" \
            --separator-style Detailed \
            --minimal-output \
            -f
    fi
    
    print_success "Source code bundle created: $output_file"
}

# Function to create tests bundle
create_tests_bundle() {
    local output_dir="$PROJECT_ROOT/$M1F_DIR/tests"
    local output_file="$output_dir/tests.m1f.txt"
    
    print_info "Creating tests bundle..."
    
    # Bundle test structure and configs (but not test data files)
    python "$M1F_TOOL" \
        -s "$PROJECT_ROOT" \
        -o "$output_file" \
        --include-extensions .py .yml .yaml .json \
        --excludes "**/test_data/**" "**/fixtures/**" "**/node_modules/**" "**/.venv/**" "**/.*" \
        --separator-style Standard \
        --minimal-output \
        -f \
        2>/dev/null | grep -E "(test_|_test\.py|tests/)" || true
    
    # Create a test overview without test data
    if [ -d "$PROJECT_ROOT/tests" ]; then
        find "$PROJECT_ROOT/tests" -name "test_*.py" -o -name "*_test.py" | \
            xargs -I {} basename {} | \
            sort > "$output_dir/test_inventory.txt"
    fi
    
    print_success "Tests bundle created: $output_file"
}

# Function to create complete bundle
create_complete_bundle() {
    local output_dir="$PROJECT_ROOT/$M1F_DIR/complete"
    local output_file="$output_dir/project.m1f.txt"
    
    print_info "Creating complete project bundle..."
    
    # Bundle everything except test data and common exclusions
    python "$M1F_TOOL" \
        -s "$PROJECT_ROOT" \
        -o "$output_file" \
        --include-extensions .py .md .yml .yaml .json .txt .sh \
        --excludes "**/test_data/**" "**/fixtures/**" "**/*.pyc" "**/node_modules/**" "**/.venv/**" "**/.*" "**/htmlcov/**" \
        --separator-style Detailed \
        --filename-mtime-hash \
        --minimal-output \
        -f
    
    print_success "Complete project bundle created: $output_file"
}

# Function to create bundle info
create_bundle_info() {
    local info_file="$PROJECT_ROOT/$M1F_DIR/BUNDLE_INFO.md"
    
    cat > "$info_file" << EOF
# m1f Bundle Information

Generated: $(date)
Project: $(basename "$PROJECT_ROOT")

## Available Bundles

### Documentation (\`docs/\`)
- \`manual.m1f.txt\` - All project documentation
- \`api_docs.m1f.txt\` - API documentation (if docs/ exists)

### Source Code (\`src/\`)
- \`source.m1f.txt\` - All Python source files (excluding tests)
- \`tools.m1f.txt\` - Tools directory bundle (if tools/ exists)

### Tests (\`tests/\`)
- \`tests.m1f.txt\` - Test files (structure only, no test data)
- \`test_inventory.txt\` - List of all test files

### Complete (\`complete/\`)
- \`project.m1f.txt\` - Complete project bundle (no test data)

## Usage Examples

### In Claude or other LLMs:
\`\`\`
Please review the documentation in .m1f/docs/manual.m1f.txt
Check the source code structure in .m1f/src/source.m1f.txt
Look at the tests in .m1f/tests/tests.m1f.txt
\`\`\`

### With IDEs:
Most IDEs can open .m1f.txt files as regular text files for reference.

## Updating Bundles

Run \`scripts/auto_bundle.sh\` to update all bundles.

## File Watcher Integration

See \`scripts/watch_and_bundle.sh\` for automatic updates.
EOF
    
    print_success "Bundle info created: $info_file"
}

# Function to show bundle statistics
show_statistics() {
    print_info "Bundle Statistics:"
    echo "----------------------------------------"
    
    for bundle_type in "${!BUNDLES[@]}"; do
        local bundle_dir="$PROJECT_ROOT/$M1F_DIR/$bundle_type"
        if [ -d "$bundle_dir" ]; then
            local total_size=$(du -sh "$bundle_dir" 2>/dev/null | cut -f1)
            local file_count=$(find "$bundle_dir" -name "*.m1f.txt" -o -name "*.txt" | wc -l)
            echo "$bundle_type: $file_count files, $total_size"
        fi
    done
    
    echo "----------------------------------------"
}

# Function to run specific bundle
run_bundle() {
    local bundle_type="$1"
    
    case "$bundle_type" in
        docs)
            create_docs_bundle
            ;;
        src)
            create_src_bundle
            ;;
        tests)
            create_tests_bundle
            ;;
        complete)
            create_complete_bundle
            ;;
        *)
            print_error "Unknown bundle type: $bundle_type"
            return 1
            ;;
    esac
}

# Main execution
main() {
    local start_time=$(date +%s)
    
    print_info "Starting auto-bundle process..."
    
    # Activate virtual environment
    activate_venv
    
    # Setup directory structure
    setup_m1f_directory
    
    # Check if specific bundle type was requested
    if [ $# -eq 1 ]; then
        run_bundle "$1"
    else
        # Create all bundles
        for bundle_type in "${!BUNDLES[@]}"; do
            run_bundle "$bundle_type"
        done
    fi
    
    # Create bundle info
    create_bundle_info
    
    # Show statistics
    show_statistics
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_success "Auto-bundle completed in ${duration}s"
}

# Show usage if --help is passed
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "Usage: $0 [bundle_type]"
    echo ""
    echo "Bundle types:"
    for bundle_type in "${!BUNDLES[@]}"; do
        echo "  $bundle_type - ${BUNDLES[$bundle_type]}"
    done
    echo ""
    echo "If no bundle type is specified, all bundles will be created."
    exit 0
fi

# Run main function
main "$@"