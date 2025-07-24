# Unified Colorama Guide

This document describes the unified colorama approach used across all m1f tools.

## Overview

All m1f tools use a centralized color handling module located at
`tools/shared/colors.py`. This provides:

- Consistent color output across all tools
- Automatic fallback when colorama is not available
- Unified helper functions for common message types
- Cross-platform terminal color support

## Using the Unified Colors Module

### Basic Import

```python
from tools.shared.colors import Colors, success, error, warning, info, header
```

For relative imports within tools:

```python
from ..shared.colors import Colors, success, error, warning, info, header
```

### Available Colors

The `Colors` class provides these color constants:

- `Colors.BLACK`, `Colors.RED`, `Colors.GREEN`, `Colors.YELLOW`
- `Colors.BLUE`, `Colors.MAGENTA`, `Colors.CYAN`, `Colors.WHITE`
- `Colors.BRIGHT_BLACK`, `Colors.BRIGHT_RED`, `Colors.BRIGHT_GREEN`, etc.
- `Colors.RESET` - Reset all formatting
- `Colors.BOLD`, `Colors.DIM` - Text styles

### Helper Functions

Instead of using `print()` directly, use these semantic helper functions:

```python
# Success messages (green with checkmark)
success("Operation completed successfully!")

# Error messages (red with X, goes to stderr)
error("Failed to process file")

# Warning messages (yellow with warning symbol)
warning("File size exceeds recommended limit")

# Info messages (normal color)
info("Processing 10 files...")

# Headers (cyan and bold)
header("Starting Conversion", "Converting HTML to Markdown")
```

### Colored Logging

For tools using Python's logging module:

```python
import logging
from tools.shared.colors import ColoredFormatter

# Create logger with colored output
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter())
logger.addHandler(handler)
```

### Colored Argparse Help

For tools using argparse:

```python
import argparse
from tools.shared.colors import ColoredHelpFormatter

parser = argparse.ArgumentParser(
    formatter_class=ColoredHelpFormatter,
    description="Tool description"
)
```

## Migration from Rich

The m1f project has migrated from Rich to colorama for better compatibility. Key
changes:

1. Replace `from rich.console import Console` with imports from `shared.colors`
2. Replace `console.print()` with appropriate helper functions
3. Remove Rich from requirements.txt
4. Use colorama's simpler color syntax

## Best Practices

1. **Always use helper functions** - Don't use `print()` directly for
   user-facing messages
2. **Import from shared module** - Never define local Colors classes
3. **Handle missing colorama gracefully** - The shared module handles this
   automatically
4. **Use semantic functions** - Choose success/error/warning/info based on
   message type
5. **Keep it simple** - Avoid complex formatting; focus on readability

## Testing Color Output

To test with colors disabled:

```bash
export NO_COLOR=1
m1f --help
```

To force colors (even in pipes):

```bash
export FORCE_COLOR=1
m1f --help | less -R
```

## Common Patterns

### Status Messages

```python
info("Starting process...")
# ... do work ...
success("Process completed!")
```

### Error Handling

```python
try:
    # ... operation ...
except Exception as e:
    error(f"Operation failed: {e}")
```

### Progress Updates

```python
for i, file in enumerate(files):
    info(f"Processing file {i+1}/{len(files)}: {file.name}")
```

### Colored File Paths

```python
info(f"Reading from: {Colors.CYAN}{file_path}{Colors.RESET}")
```

## Troubleshooting

1. **Colors not showing on Windows**: Colorama should handle this automatically.
   If not, ensure colorama is installed.

2. **Colors in CI/CD logs**: Most CI systems support ANSI colors. The module
   respects NO_COLOR and CI environment variables.

3. **Import errors**: Ensure you're using the correct relative import path based
   on your tool's location.

## Module API Reference

### Colors Class

- Static class providing color constants
- All attributes return ANSI escape codes or empty strings
- Use `Colors.disable()` to turn off colors programmatically

### Helper Functions

- `success(msg: str)` - Print success message with green color
- `error(msg: str)` - Print error message with red color to stderr
- `warning(msg: str)` - Print warning message with yellow color
- `info(msg: str)` - Print info message with default color
- `header(title: str, subtitle: str = None)` - Print formatted header

### Formatters

- `ColoredFormatter` - Logging formatter with level-based colors
- `ColoredHelpFormatter` - Argparse formatter with colored help text

### Global Variables

- `COLORAMA_AVAILABLE` - Boolean indicating if colorama is installed
- Respects `NO_COLOR` and `FORCE_COLOR` environment variables
