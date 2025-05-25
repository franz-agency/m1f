#!/bin/bash
# Advanced Auto Bundle Script for m1f Projects
# Uses .m1f.config.yml for customizable bundling

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
CONFIG_FILE="$PROJECT_ROOT/.m1f.config.yml"
M1F_DIR=".m1f"
M1F_TOOL="$PROJECT_ROOT/tools/m1f.py"
VENV_PATH="$PROJECT_ROOT/.venv"

# Functions for colored output
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

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

# Check if directory exists for conditional bundles
check_enabled_condition() {
    local condition="$1"
    if [[ "$condition" == *"enabled_if_exists:"* ]]; then
        local dir=$(echo "$condition" | sed 's/.*enabled_if_exists: *//' | tr -d '"')
        [ -d "$PROJECT_ROOT/$dir" ]
    elif [[ "$condition" == "false" ]]; then
        return 1
    else
        return 0
    fi
}

# Activate virtual environment
activate_venv() {
    if [ -d "$VENV_PATH" ]; then
        source "$VENV_PATH/bin/activate"
    fi
}

# Create m1f directory structure
setup_directories() {
    # Extract unique directories from config
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
}

# Build m1f command from bundle config
build_m1f_command() {
    local bundle_json="$1"
    local bundle_name="$2"
    
    # Parse bundle configuration using Python
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
    
    # Include patterns
    if 'include_patterns' in source:
        for pattern in source['include_patterns']:
            # For patterns, we need to handle them differently
            # This is a simplified approach
            pass
    
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

# Global excludes
global_excludes = ${GLOBAL_EXCLUDES:-[]}
if global_excludes:
    for exclude in global_excludes:
        cmd_parts.extend(['--excludes', f'"{exclude}"'])

cmd_parts.append('-f')  # Force overwrite

print(' '.join(cmd_parts))
EOF
}

# Create a single bundle
create_bundle() {
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
    local cmd=$(build_m1f_command "$bundle_json" "$bundle_name")
    eval "$cmd" || {
        print_error "Failed to create bundle: $bundle_name"
        return 1
    }
    
    print_success "Created: $bundle_name"
}

# Show bundle priorities and recommendations
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
    print(f"Error reading config: {e}")
EOF
    
    echo "========================================="
}

# Main execution
main() {
    local start_time=$(date +%s)
    
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "Configuration file not found: $CONFIG_FILE"
        print_info "Creating default configuration..."
        # Copy the default config if this script was run without it
        cp "$SCRIPT_DIR/../.m1f.config.yml" "$CONFIG_FILE" 2>/dev/null || {
            print_error "Could not create config file"
            exit 1
        }
    fi
    
    print_info "M1F Auto-Bundle (Advanced Mode)"
    print_info "Using config: $CONFIG_FILE"
    
    # Get global excludes
    GLOBAL_EXCLUDES=$(get_global_config "global_excludes" | python3 -c "
import sys
line = sys.stdin.read().strip()
if line and line != '[]':
    items = line.strip('[]').split(', ')
    print(json.dumps([item.strip(\"'\") for item in items]))
else:
    print('[]')
")
    export GLOBAL_EXCLUDES
    
    # Activate virtual environment
    activate_venv
    
    # Setup directories
    setup_directories
    
    # Get bundles to create
    if [ $# -eq 0 ]; then
        # Create all bundles
        bundles_json=$(parse_config)
    else
        # Create specific bundle
        bundles_json=$(parse_config "$1")
        if [ "$bundles_json" == "{}" ]; then
            print_error "Unknown bundle: $1"
            print_info "Available bundles:"
            parse_config | python3 -c "
import json, sys
bundles = json.load(sys.stdin)
for name, config in bundles.items():
    desc = config.get('description', 'No description')
    print(f'  - {name}: {desc}')
"
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
        create_bundle "$bundle_name" "$bundles_json"
    done
    
    # Show AI hints
    if [ $# -eq 0 ]; then
        echo
        show_ai_hints
    fi
    
    # Show statistics
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_success "Auto-bundle completed in ${duration}s"
}

# Show help
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "Usage: $0 [bundle_name]"
    echo ""
    echo "Advanced auto-bundling with .m1f.config.yml"
    echo ""
    echo "Features:"
    echo "  - Configurable bundles via YAML"
    echo "  - Priority-based bundling for AI/LLM contexts"
    echo "  - Conditional bundles based on directory existence"
    echo "  - Custom focus areas and exclusions"
    echo "  - Global and per-bundle settings"
    echo ""
    echo "Configuration: .m1f.config.yml"
    exit 0
fi

# Check dependencies
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required"
    exit 1
fi

if ! python3 -c "import yaml" 2>/dev/null; then
    print_error "PyYAML is required. Install with: pip install pyyaml"
    exit 1
fi

# Run main
main "$@"