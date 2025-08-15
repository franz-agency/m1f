# Shared Utilities for m1f Tools

This module provides common functionality that can be used across all m1f tools.

## Overview

The `tools/shared` module contains reusable components for:

- Prompt loading and management
- Configuration file handling
- Path and text utilities

## Components

### Prompt Loader

Universal prompt loading system with caching and fallback support:

```python
from tools.shared.prompts import PromptLoader, load_prompt, format_prompt

# Create a loader with search paths
loader = PromptLoader([
    Path("my_tool/prompts"),
    Path("shared/prompts")
])

# Load a prompt
prompt = loader.load("analysis/synthesis.md")

# Load and format in one step
formatted = loader.format("analysis/synthesis.md",
    query="machine learning",
    summaries="..."
)

# Use the global loader
prompt = load_prompt("analysis/synthesis.md")
```

### Configuration Loader

Support for JSON, YAML, and TOML configuration files:

```python
from tools.shared.config import load_config_file, save_config_file, merge_configs

# Load configuration
config = load_config_file("config.yaml")

# Load with defaults and environment overrides
config = load_config_with_defaults(
    path="config.yaml",
    defaults={"timeout": 30},
    env_prefix="M1F_TOOL_"
)

# Merge multiple configs
final_config = merge_configs(defaults, file_config, cli_config)
```

### Path Utilities

Common path operations:

```python
from tools.shared.utils import ensure_path, get_project_root, find_files

# Ensure path exists and create parents
path = ensure_path("output/results.txt", create_parents=True)

# Find project root
root = get_project_root()

# Find all Python files
for py_file in find_files(root, "**/*.py", exclude_dirs=[".venv", "__pycache__"]):
    print(py_file)
```

### Text Utilities

Text processing helpers:

```python
from tools.shared.utils import truncate_text, clean_whitespace, extract_json_from_text

# Truncate with word boundaries
truncated = truncate_text(long_text, max_length=100, break_on_word=True)

# Clean whitespace while preserving paragraphs
cleaned = clean_whitespace(messy_text, preserve_paragraphs=True)

# Extract JSON from mixed content
json_str = extract_json_from_text(response_with_json)
```

## Adding to Your Tool

1. Import what you need:

```python
from tools.shared.prompts import PromptLoader
from tools.shared.config import load_config_file
from tools.shared.utils import ensure_path
```

2. Add your tool's prompt directory to the loader:

```python
loader = PromptLoader([
    Path(__file__).parent / "prompts",
    Path(__file__).parent.parent / "shared/prompts"
])
```

3. Use the utilities in your code:

```python
# Load and format a prompt
prompt = loader.format("my_prompt.md", variable="value")

# Load configuration
config = load_config_file("config.yaml")

# Ensure output path exists
output_path = ensure_path("output/result.txt", create_parents=True)
```

## Prompt Organization

Prompts should be organized by tool and category:

```
tools/shared/prompts/
├── research/           # Research tool prompts
│   ├── analysis/       # Analysis prompts
│   ├── bundle/         # Bundle creation prompts
│   └── llm/           # LLM interaction prompts
├── html2md/           # HTML to Markdown prompts
└── common/            # Shared prompts
```

## Best Practices

1. **Prompt Loading**: Always use the PromptLoader for consistency and caching
2. **Configuration**: Use `load_config_with_defaults()` for robust config
   handling
3. **Paths**: Use `ensure_path()` to avoid path-related errors
4. **Text Processing**: Use the provided utilities instead of reimplementing

## Contributing

When adding new shared functionality:

1. Place it in the appropriate submodule
2. Add comprehensive docstrings
3. Include type hints
4. Add unit tests
5. Update this README
