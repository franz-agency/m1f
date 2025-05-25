#!/bin/bash
# Auto Bundle Script with Preset Support
# Uses m1f presets for intelligent file bundling

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
M1F_TOOL="$PROJECT_ROOT/tools/m1f.py"
VENV_PATH="$PROJECT_ROOT/.venv"
OUTPUT_DIR="$PROJECT_ROOT/.ai-context"
PRESETS_DIR="$PROJECT_ROOT/presets"

# Functions for colored output
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Activate virtual environment
activate_venv() {
    if [ -d "$VENV_PATH" ]; then
        source "$VENV_PATH/bin/activate"
    fi
}

# Create output directory
setup_directories() {
    mkdir -p "$OUTPUT_DIR"
}

# Create bundle with preset
create_preset_bundle() {
    local preset_name="$1"
    local preset_group="$2"
    local output_suffix="$3"
    
    # Determine preset file
    local preset_file=""
    case "$preset_name" in
        wordpress|wp)
            preset_file="wordpress.m1f-presets.yml"
            ;;
        web|web-project)
            preset_file="web-project.m1f-presets.yml"
            ;;
        docs|documentation)
            preset_file="documentation.m1f-presets.yml"
            ;;
        example|globals)
            preset_file="example-globals.m1f-presets.yml"
            ;;
        *)
            # Check if it's a direct filename
            if [ -f "$PRESETS_DIR/$preset_name" ]; then
                preset_file="$preset_name"
            else
                print_error "Unknown preset: $preset_name"
                return 1
            fi
            ;;
    esac
    
    local preset_path="$PRESETS_DIR/$preset_file"
    if [ ! -f "$preset_path" ]; then
        print_error "Preset file not found: $preset_path"
        return 1
    fi
    
    # Build output filename
    local output_name="bundle_${preset_name}"
    if [ -n "$preset_group" ]; then
        output_name="${output_name}_${preset_group}"
    fi
    if [ -n "$output_suffix" ]; then
        output_name="${output_name}_${output_suffix}"
    fi
    output_name="${output_name}.m1f.txt"
    
    print_info "Creating bundle with preset: $preset_name"
    if [ -n "$preset_group" ]; then
        print_info "Using preset group: $preset_group"
    fi
    
    # Build command
    local cmd="python \"$M1F_TOOL\" \
        --source-directory \"$PROJECT_ROOT\" \
        --output-file \"$OUTPUT_DIR/$output_name\" \
        --preset \"$preset_path\""
    
    if [ -n "$preset_group" ]; then
        cmd="$cmd --preset-group \"$preset_group\""
    fi
    
    cmd="$cmd --separator-style MachineReadable --force --minimal-output"
    
    # Execute
    eval "$cmd" || {
        print_error "Failed to create bundle with preset: $preset_name"
        return 1
    }
    
    print_success "Created: $output_name"
}

# Create standard bundles using presets
create_standard_bundles() {
    print_info "Creating standard preset-based bundles..."
    
    # Documentation bundle
    create_preset_bundle "documentation" "" "docs"
    
    # Web project bundle (source code)
    create_preset_bundle "web-project" "" "source"
    
    # Full bundle with examples
    create_preset_bundle "example-globals" "" "complete"
}

# Create focused bundles
create_focused_bundles() {
    local focus="$1"
    
    case "$focus" in
        wordpress)
            create_preset_bundle "wordpress" "theme" "theme"
            create_preset_bundle "wordpress" "plugin" "plugin"
            ;;
        web)
            create_preset_bundle "web-project" "frontend" "frontend"
            create_preset_bundle "web-project" "backend" "backend"
            ;;
        docs)
            create_preset_bundle "documentation" "" "all_docs"
            ;;
        *)
            print_error "Unknown focus area: $focus"
            return 1
            ;;
    esac
}

# Show available presets
show_presets() {
    print_info "Available presets:"
    echo "===================="
    
    for preset in "$PRESETS_DIR"/*.m1f-presets.yml; do
        if [ -f "$preset" ]; then
            local name=$(basename "$preset" .m1f-presets.yml)
            echo "  - $name"
            
            # Show groups if available
            local groups=$(python3 -c "
import yaml
try:
    with open('$preset', 'r') as f:
        data = yaml.safe_load(f)
    groups = [k for k in data.keys() if k != 'globals']
    if groups:
        print('    Groups: ' + ', '.join(groups))
except:
    pass
" 2>/dev/null)
            if [ -n "$groups" ]; then
                echo "$groups"
            fi
        fi
    done
    echo "===================="
}

# Main execution
main() {
    local start_time=$(date +%s)
    
    print_info "M1F Auto-Bundle with Preset Support"
    
    # Activate virtual environment
    activate_venv
    
    # Setup directories
    setup_directories
    
    # Parse arguments
    case "${1:-all}" in
        all)
            create_standard_bundles
            ;;
        focus)
            if [ -z "$2" ]; then
                print_error "Focus area required"
                echo "Available: wordpress, web, docs"
                exit 1
            fi
            create_focused_bundles "$2"
            ;;
        preset)
            if [ -z "$2" ]; then
                show_presets
                exit 0
            fi
            create_preset_bundle "$2" "$3" "${4:-custom}"
            ;;
        list|--list)
            show_presets
            ;;
        --help|-h)
            echo "Usage: $0 [command] [options]"
            echo ""
            echo "Commands:"
            echo "  all                    Create all standard bundles (default)"
            echo "  focus <area>          Create focused bundles for specific area"
            echo "                        Areas: wordpress, web, docs"
            echo "  preset <name> [group] Create bundle with specific preset"
            echo "  list                  Show available presets"
            echo ""
            echo "Examples:"
            echo "  $0                    # Create all standard bundles"
            echo "  $0 focus wordpress    # Create WordPress-specific bundles"
            echo "  $0 preset web-project frontend  # Use web-project preset, frontend group"
            echo ""
            exit 0
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
    
    # Show completion time
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_success "Auto-bundle completed in ${duration}s"
    print_info "Bundles created in: $OUTPUT_DIR"
}

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