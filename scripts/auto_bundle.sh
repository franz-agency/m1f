#!/bin/bash
# Auto Bundle Script for m1f Projects
# Supports both simple mode and advanced YAML configuration mode

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
CONFIG_FILE="$PROJECT_ROOT/.m1f.config.yml"

# Default bundle configurations (fallback when no config file)
declare -A BUNDLES=(
    ["docs"]="Documentation bundle"
    ["src"]="Source code bundle"
    ["tests"]="Test files bundle"
    ["complete"]="Complete project bundle"
)

# Operation mode
MODE="simple"  # Can be "simple" or "advanced"

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

# Parse YAML config using Python
parse_config() {
    python3 -c "
import yaml
import sys
import json

try:
    with open('$CONFIG_FILE', 'r') as f:
        config = yaml.safe_load(f)
    
    # Get bundle names or specific bundle
    if len(sys.argv) > 1:
        bundle_name = sys.argv[1]
        if bundle_name in config.get('bundles', {}):
            print(json.dumps({bundle_name: config['bundles'][bundle_name]}))
        else:
            print(json.dumps({}))
    else:
        print(json.dumps(config.get('bundles', {})))
except Exception as e:
    print(json.dumps({'error': str(e)}))
" "$1"
}

# Get global config value
get_global_config() {
    local key="$1"
    python3 -c "
import yaml
try:
    with open('$CONFIG_FILE', 'r') as f:
        config = yaml.safe_load(f)
    global_conf = config.get('global', {})
    keys = '$key'.split('.')
    value = global_conf
    for k in keys:
        value = value.get(k, '')
    print(value)
except:
    print('')
"
}

# Build m1f command from YAML config
build_m1f_command_yaml() {
    local bundle_json="$1"
    local bundle_name="$2"
    
    python3 << EOF
import json
import sys

bundle = json.loads('''$bundle_json''')['$bundle_name']

# Start building command
cmd_parts = ['python', '"$M1F_TOOL"']

# Process sources
sources = bundle.get('sources', [])
for source in sources:
    path = source.get('path', '.')
    cmd_parts.extend(['-s', f'"$PROJECT_ROOT/{path}"'])
    
    # Include extensions
    if 'include_extensions' in source:
        for ext in source['include_extensions']:
            cmd_parts.extend(['--include-extensions', ext])
    
    # Include patterns - Note: m1f doesn't support --include-patterns
    if 'include_patterns' in source:
        print(f"WARNING: include_patterns is not supported by m1f tool. Skipping patterns for source: {path}", file=sys.stderr)
    
    # Excludes
    if 'excludes' in source:
        cmd_parts.append('--excludes')
        for exclude in source['excludes']:
            cmd_parts.append(f'"{exclude}"')

# Output file
output = bundle.get('output', '')
if output:
    cmd_parts.extend(['-o', f'"$PROJECT_ROOT/{output}"'])

# Separator style
sep_style = bundle.get('separator_style', 'Standard')
cmd_parts.extend(['--separator-style', sep_style])

# Other options
if bundle.get('filename_mtime_hash'):
    cmd_parts.append('--filename-mtime-hash')

if bundle.get('minimal_output', True):
    cmd_parts.append('--minimal-output')

cmd_parts.append('-f')  # Force overwrite

print(' '.join(cmd_parts))
EOF
}

# Create bundle in advanced mode
create_bundle_advanced() {
    local bundle_name="$1"
    local bundle_json="$2"
    
    # Check if bundle is enabled
    local enabled=$(echo "$bundle_json" | python3 -c "
import json, sys
bundle = json.load(sys.stdin)
enabled = bundle.get('$bundle_name', {}).get('enabled', True)
enabled_if = bundle.get('$bundle_name', {}).get('enabled_if_exists', '')
print(f'{enabled}|{enabled_if}')
")
    
    local is_enabled=$(echo "$enabled" | cut -d'|' -f1)
    local condition=$(echo "$enabled" | cut -d'|' -f2)
    
    if [[ "$is_enabled" == "False" ]]; then
        print_info "Skipping disabled bundle: $bundle_name"
        return
    fi
    
    if [[ -n "$condition" ]] && ! [ -d "$PROJECT_ROOT/$condition" ]; then
        print_info "Skipping bundle $bundle_name (condition not met: $condition)"
        return
    fi
    
    local description=$(echo "$bundle_json" | python3 -c "
import json, sys
bundle = json.load(sys.stdin)
print(bundle.get('$bundle_name', {}).get('description', ''))
")
    
    print_info "Creating bundle: $bundle_name - $description"
    
    # Build and execute command
    local cmd=$(build_m1f_command_yaml "$bundle_json" "$bundle_name")
    eval "$cmd" || {
        print_error "Failed to create bundle: $bundle_name"
        return 1
    }
    
    print_success "Created: $bundle_name"
}

# Show AI optimization hints
show_ai_hints() {
    print_info "AI/LLM Usage Recommendations:"
    echo "========================================="
    
    python3 << EOF
import yaml
try:
    with open('$CONFIG_FILE', 'r') as f:
        config = yaml.safe_load(f)
    
    # Get priorities
    ai_config = config.get('ai_optimization', {})
    priorities = ai_config.get('context_priority', [])
    hints = ai_config.get('usage_hints', {})
    
    print("Bundle Priority Order:")
    for i, bundle in enumerate(priorities, 1):
        hint = hints.get(bundle, '')
        print(f"  {i}. {bundle}: {hint}")
    
    print("\nToken Limits:")
    limits = ai_config.get('token_limits', {})
    for model, limit in limits.items():
        print(f"  - {model}: {limit:,} tokens")
except Exception as e:
    print(f"Error reading AI config: {e}")
EOF
    
    echo "========================================="
}

# Check if config file exists and has Python yaml support
check_advanced_mode() {
    if [ -f "$CONFIG_FILE" ] && command -v python3 &> /dev/null && python3 -c "import yaml" 2>/dev/null; then
        MODE="advanced"
    else
        MODE="simple"
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 [options] [bundle_type]"
    echo ""
    
    if [[ "$MODE" == "advanced" ]]; then
        echo "Running in ADVANCED mode (using .m1f.config.yml)"
        echo ""
        echo "Available bundles from config:"
        parse_config | python3 -c "
import json, sys
bundles = json.load(sys.stdin)
for name, config in bundles.items():
    desc = config.get('description', 'No description')
    print(f'  - {name}: {desc}')
"
    else
        echo "Running in SIMPLE mode (no config file found)"
        echo ""
        echo "Bundle types:"
        for bundle_type in "${!BUNDLES[@]}"; do
            echo "  $bundle_type - ${BUNDLES[$bundle_type]}"
        done
    fi
    
    echo ""
    echo "Options:"
    echo "  -h, --help    Show this help message"
    echo "  --simple      Force simple mode (ignore config file)"
    echo ""
    echo "If no bundle type is specified, all bundles will be created."
}

# Main execution for advanced mode
main_advanced() {
    local start_time=$(date +%s)
    
    print_info "M1F Auto-Bundle (Advanced Mode)"
    print_info "Using config: $CONFIG_FILE"
    
    # Activate virtual environment
    activate_venv
    
    # Setup directories based on config
    local dirs=$(parse_config | python3 -c "
import json, sys
from pathlib import Path
config = json.load(sys.stdin)
dirs = set()
for bundle in config.values():
    if isinstance(bundle, dict) and 'output' in bundle:
        output_path = Path(bundle['output'])
        dirs.add(str(output_path.parent))
print(' '.join(sorted(dirs)))
")
    
    for dir in $dirs; do
        mkdir -p "$PROJECT_ROOT/$dir"
    done
    
    # Create .gitignore
    if [ ! -f "$PROJECT_ROOT/$M1F_DIR/.gitignore" ]; then
        cat > "$PROJECT_ROOT/$M1F_DIR/.gitignore" << EOF
# Auto-generated m1f bundles
*.m1f
*.m1f.txt
*_filelist.txt
*_dirlist.txt
*.log

# But track the structure and config
!.gitkeep
!../.m1f.config.yml
EOF
    fi
    
    # Get bundles to create
    if [ $# -eq 0 ]; then
        # Create all bundles
        bundles_json=$(parse_config)
    else
        # Create specific bundle
        bundles_json=$(parse_config "$1")
        if [ "$bundles_json" == "{}" ]; then
            print_error "Unknown bundle: $1"
            show_usage
            exit 1
        fi
    fi
    
    # Create bundles
    echo "$bundles_json" | python3 -c "
import json, sys
bundles = json.load(sys.stdin)
for name in bundles:
    print(name)
" | while read -r bundle_name; do
        create_bundle_advanced "$bundle_name" "$bundles_json"
    done
    
    # Show AI hints if creating all bundles
    if [ $# -eq 0 ]; then
        echo
        show_ai_hints
    fi
    
    # Show statistics
    show_statistics
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_success "Auto-bundle completed in ${duration}s"
}

# Parse command line arguments
BUNDLE_TYPE=""
FORCE_SIMPLE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            check_advanced_mode
            show_usage
            exit 0
            ;;
        --simple)
            FORCE_SIMPLE=true
            shift
            ;;
        *)
            BUNDLE_TYPE="$1"
            shift
            ;;
    esac
done

# Check mode
if [[ "$FORCE_SIMPLE" == "true" ]]; then
    MODE="simple"
else
    check_advanced_mode
fi

# Run appropriate main function
if [[ "$MODE" == "advanced" ]]; then
    main_advanced "$BUNDLE_TYPE"
else
    main "$BUNDLE_TYPE"
fi