#!/bin/bash
# File Watcher for Auto Bundle
# Watches for file changes and automatically updates m1f bundles

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
# Use python directly for auto-bundle
PYTHON_CMD="cd \"$PROJECT_ROOT\" && source .venv/bin/activate && m1f-update"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
WATCH_INTERVAL=5  # seconds
DEBOUNCE_TIME=2   # seconds to wait after last change

# State tracking
LAST_CHANGE=0
PENDING_UPDATE=false

print_info() {
    echo -e "${BLUE}[WATCHER]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[WATCHER]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WATCHER]${NC} $1"
}

# Function to check if required tools are installed
check_dependencies() {
    local missing_deps=()
    
    # Check for inotify-tools (Linux) or fswatch (macOS)
    if command -v inotifywait &> /dev/null; then
        WATCH_COMMAND="inotifywait"
        print_info "Using inotifywait for file watching"
    elif command -v fswatch &> /dev/null; then
        WATCH_COMMAND="fswatch"
        print_info "Using fswatch for file watching"
    else
        print_warning "No file watcher found. Install one of:"
        echo "  - Linux: sudo apt-get install inotify-tools"
        echo "  - macOS: brew install fswatch"
        echo ""
        echo "Falling back to polling mode (less efficient)"
        WATCH_COMMAND="poll"
    fi
}

# Function to get list of files to watch
get_watch_paths() {
    echo "$PROJECT_ROOT/tools"
    echo "$PROJECT_ROOT/docs"
    echo "$PROJECT_ROOT/tests"
    echo "$PROJECT_ROOT/README.md"
    echo "$PROJECT_ROOT/pyproject.toml"
    echo "$PROJECT_ROOT/requirements.txt"
    
    # Add any .py files in root
    find "$PROJECT_ROOT" -maxdepth 1 -name "*.py" 2>/dev/null || true
}

# Get dynamic ignore patterns from config
get_ignore_regex() {
    python3 "$SCRIPT_DIR/get_watcher_ignores.py" --regex 2>/dev/null || echo "(\.m1f/|\.venv/|__pycache__|\.git/|\.pyc$)"
}

# Function to check if file should trigger update
should_update_for_file() {
    local file="$1"
    local ignore_regex=$(get_ignore_regex)
    
    # Check against dynamic ignore patterns
    if echo "$file" | grep -qE "$ignore_regex"; then
        return 1
    fi
    
    # Check for relevant extensions
    if [[ "$file" == *.py ]] || [[ "$file" == *.md ]] || \
       [[ "$file" == *.txt ]] || [[ "$file" == *.yml ]] || \
       [[ "$file" == *.yaml ]] || [[ "$file" == *.json ]]; then
        return 0
    fi
    
    return 1
}

# Function to determine which bundle to update based on file
get_bundle_type_for_file() {
    local file="$1"
    
    # Documentation files
    if [[ "$file" == *.md ]] || [[ "$file" == *.rst ]] || \
       [[ "$file" == */docs/* ]] || [[ "$file" == */README* ]]; then
        echo "docs"
        return
    fi
    
    # Test files
    if [[ "$file" == */test_* ]] || [[ "$file" == *_test.py ]] || \
       [[ "$file" == */tests/* ]]; then
        echo "tests"
        return
    fi
    
    # Source files
    if [[ "$file" == *.py ]]; then
        echo "src"
        return
    fi
    
    # Default to complete for other files
    echo "complete"
}

# Function to run bundle update
run_bundle_update() {
    local bundle_type="$1"
    
    print_info "Updating $bundle_type bundle..."
    
    if [ -z "$bundle_type" ] || [ "$bundle_type" == "all" ]; then
        eval "$PYTHON_CMD"
    else
        eval "$PYTHON_CMD $bundle_type"
    fi
    
    print_success "Bundle update completed"
}

# Function to handle file change
handle_file_change() {
    local file="$1"
    local current_time=$(date +%s)
    
    if should_update_for_file "$file"; then
        print_info "Change detected: $file"
        LAST_CHANGE=$current_time
        PENDING_UPDATE=true
        
        # Determine which bundle needs updating
        local bundle_type=$(get_bundle_type_for_file "$file")
        echo "$bundle_type" >> /tmp/m1f_pending_bundles.txt
    fi
}

# Function to process pending updates
process_pending_updates() {
    if [ "$PENDING_UPDATE" = true ]; then
        local current_time=$(date +%s)
        local time_since_change=$((current_time - LAST_CHANGE))
        
        if [ $time_since_change -ge $DEBOUNCE_TIME ]; then
            PENDING_UPDATE=false
            
            # Get unique bundle types to update
            if [ -f /tmp/m1f_pending_bundles.txt ]; then
                local bundles=$(sort -u /tmp/m1f_pending_bundles.txt | tr '\n' ' ')
                rm -f /tmp/m1f_pending_bundles.txt
                
                # If multiple bundle types, just update all
                if [ $(echo "$bundles" | wc -w) -gt 2 ]; then
                    run_bundle_update "all"
                else
                    for bundle in $bundles; do
                        run_bundle_update "$bundle"
                    done
                fi
            fi
        fi
    fi
}

# Polling-based watcher (fallback)
watch_with_polling() {
    print_info "Starting polling-based file watcher (checking every ${WATCH_INTERVAL}s)..."
    
    # Get ignore regex
    local ignore_regex=$(get_ignore_regex)
    
    # Create initial checksums
    local checksum_file="/tmp/m1f_checksums_$(date +%s).txt"
    find "$PROJECT_ROOT" -type f -name "*.py" -o -name "*.md" -o -name "*.txt" | \
        grep -v -E "$ignore_regex" | \
        xargs md5sum > "$checksum_file" 2>/dev/null || true
    
    while true; do
        sleep $WATCH_INTERVAL
        
        # Create new checksums
        local new_checksum_file="/tmp/m1f_checksums_new.txt"
        find "$PROJECT_ROOT" -type f -name "*.py" -o -name "*.md" -o -name "*.txt" | \
            grep -v -E "$ignore_regex" | \
            xargs md5sum > "$new_checksum_file" 2>/dev/null || true
        
        # Compare checksums
        if ! diff -q "$checksum_file" "$new_checksum_file" > /dev/null 2>&1; then
            # Find changed files
            diff "$checksum_file" "$new_checksum_file" 2>/dev/null | \
                grep "^[<>]" | awk '{print $2}' | while read -r file; do
                handle_file_change "$file"
            done
            
            cp "$new_checksum_file" "$checksum_file"
        fi
        
        rm -f "$new_checksum_file"
        process_pending_updates
    done
}

# inotifywait-based watcher (Linux)
watch_with_inotifywait() {
    print_info "Starting inotifywait-based file watcher..."
    
    # Get ignore pattern for inotify
    local ignore_pattern=$(python3 "$SCRIPT_DIR/get_watcher_ignores.py" --inotify 2>/dev/null || echo '(\.m1f/|\.venv/|__pycache__|\.git/|\.pyc$)')
    
    # Watch for relevant events
    inotifywait -mr \
        --exclude "$ignore_pattern" \
        -e modify,create,delete,move \
        "$PROJECT_ROOT" |
    while read -r directory event file; do
        handle_file_change "${directory}${file}"
        
        # Process pending updates in background
        (sleep 0.1 && process_pending_updates) &
    done
}

# fswatch-based watcher (macOS)
watch_with_fswatch() {
    print_info "Starting fswatch-based file watcher..."
    
    # Get exclude arguments for fswatch
    local exclude_args=$(python3 "$SCRIPT_DIR/get_watcher_ignores.py" --fswatch 2>/dev/null || echo "--exclude '\.m1f/' --exclude '\.venv/' --exclude '__pycache__' --exclude '\.git/' --exclude '.*\.pyc$'")
    
    # Use eval to properly expand the exclude arguments
    eval "fswatch -r $exclude_args '$PROJECT_ROOT'" |
    while read -r file; do
        handle_file_change "$file"
        
        # Process pending updates in background
        (sleep 0.1 && process_pending_updates) &
    done
}

# Main execution
main() {
    print_info "File watcher for m1f auto-bundling"
    print_info "Project root: $PROJECT_ROOT"
    
    # Clean up any previous state
    rm -f /tmp/m1f_pending_bundles.txt
    
    # Check dependencies
    check_dependencies
    
    # Create initial bundles
    print_info "Creating initial bundles..."
    eval "$PYTHON_CMD"
    
    # Start watching based on available tool
    case "$WATCH_COMMAND" in
        inotifywait)
            watch_with_inotifywait
            ;;
        fswatch)
            watch_with_fswatch
            ;;
        poll)
            watch_with_polling
            ;;
        *)
            print_warning "No file watcher available"
            exit 1
            ;;
    esac
}

# Handle Ctrl+C gracefully
trap 'echo ""; print_info "Stopping file watcher..."; rm -f /tmp/m1f_pending_bundles.txt; exit 0' INT TERM

# Show usage
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "Usage: $0"
    echo ""
    echo "Watches for file changes and automatically updates m1f bundles."
    echo ""
    echo "Supported file watchers:"
    echo "  - inotifywait (Linux): apt-get install inotify-tools"
    echo "  - fswatch (macOS): brew install fswatch"
    echo "  - Polling mode (fallback): No dependencies"
    echo ""
    echo "The watcher will:"
    echo "  - Monitor Python, Markdown, and config files"
    echo "  - Update relevant bundles when changes are detected"
    echo "  - Use debouncing to avoid excessive updates"
    exit 0
fi

# Run main
main