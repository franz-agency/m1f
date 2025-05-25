"""
Configuration loader for m1f presets.
Handles loading presets from user home directory and project directories.
"""

from pathlib import Path
from typing import List, Optional
import os
import logging

logger = logging.getLogger(__name__)


class PresetConfigLoader:
    """Loads preset configurations from various locations."""

    @staticmethod
    def get_user_preset_dir() -> Path:
        """Get the user's m1f preset directory."""
        # Support XDG_CONFIG_HOME on Linux/Unix
        if os.name != "nt" and "XDG_CONFIG_HOME" in os.environ:
            config_home = Path(os.environ["XDG_CONFIG_HOME"])
        else:
            config_home = Path.home()

        return config_home / ".m1f"

    @staticmethod
    def get_global_preset_file() -> Path:
        """Get the global preset file path."""
        return PresetConfigLoader.get_user_preset_dir() / "global-presets.yml"

    @staticmethod
    def get_user_presets_dir() -> Path:
        """Get the directory for user preset files."""
        return PresetConfigLoader.get_user_preset_dir() / "presets"

    @classmethod
    def load_all_presets(
        cls,
        project_presets: Optional[List[Path]] = None,
        include_global: bool = True,
        include_user: bool = True,
    ) -> List[Path]:
        """
        Load all preset files in order of precedence.

        Order (highest to lowest priority):
        1. Project-specific presets (from command line)
        2. User presets (~/.m1f/presets/)
        3. Global presets (~/.m1f/global-presets.yml)

        Args:
            project_presets: List of project-specific preset files
            include_global: Whether to include global presets
            include_user: Whether to include user presets

        Returns:
            List of preset file paths to load
        """
        preset_files = []

        # 1. Global presets (lowest priority)
        if include_global:
            global_preset = cls.get_global_preset_file()
            if global_preset.exists():
                preset_files.append(global_preset)
                logger.debug(f"Found global preset file: {global_preset}")

        # 2. User presets
        if include_user:
            user_dir = cls.get_user_presets_dir()
            if user_dir.exists() and user_dir.is_dir():
                # Load all .yml and .yaml files
                for pattern in ["*.yml", "*.yaml"]:
                    for preset_file in sorted(user_dir.glob(pattern)):
                        preset_files.append(preset_file)
                        logger.debug(f"Found user preset file: {preset_file}")

        # 3. Project presets (highest priority)
        if project_presets:
            for preset_file in project_presets:
                if preset_file.exists():
                    preset_files.append(preset_file)
                    logger.debug(f"Found project preset file: {preset_file}")
                else:
                    logger.warning(f"Project preset file not found: {preset_file}")

        return preset_files

    @classmethod
    def init_user_config(cls) -> None:
        """Initialize user configuration directory with example files."""
        user_dir = cls.get_user_preset_dir()
        presets_dir = cls.get_user_presets_dir()

        # Create directories
        user_dir.mkdir(exist_ok=True)
        presets_dir.mkdir(exist_ok=True)

        # Create example global preset if it doesn't exist
        global_preset = cls.get_global_preset_file()
        if not global_preset.exists():
            example_content = """# Global m1f preset configuration
# These settings apply to all m1f operations unless overridden

# Global defaults for all projects
global_defaults:
  description: "Global defaults for all file types"
  priority: 1  # Lowest priority
  
  global_settings:
    # Default encoding and formatting
    encoding: "utf-8"
    separator_style: "Detailed"
    line_ending: "lf"
    
    # Global exclude patterns
    exclude_patterns:
      - "*.pyc"
      - "__pycache__"
      - ".git"
      - ".svn"
      - "node_modules"
    
    # File filtering options
    include_dot_paths: false      # Include hidden files by default
    include_binary_files: false   # Skip binary files
    max_file_size: "50MB"        # Skip very large files
    
    # Processing options
    remove_scraped_metadata: false  # Keep metadata by default
    abort_on_encoding_error: false  # Be resilient to encoding issues
    
    # Extension-specific defaults
    extensions:
      # HTML files - strip common tags by default
      .html:
        actions:
          - strip_tags
          - compress_whitespace
        strip_tags:
          - "script"
          - "style"
          - "meta"
          - "link"
      
      # Markdown - clean up formatting
      .md:
        actions:
          - remove_empty_lines
      
      # CSS files - minify
      .css:
        actions:
          - minify
          - strip_comments
      
      # JavaScript - remove comments
      .js:
        actions:
          - strip_comments
          - compress_whitespace
      
      # JSON - compress by default
      .json:
        actions:
          - compress_whitespace
      
      # Log files - truncate
      .log:
        actions:
          - custom
        custom_processor: "truncate"
        processor_args:
          max_chars: 5000

# Personal project defaults
personal_projects:
  description: "Settings for personal projects"
  priority: 5
  enabled: false  # Enable this in your projects
  
  global_settings:
    # Override for personal projects
    separator_style: "Markdown"
    
    # Additional excludes for personal projects
    exclude_patterns:
      - "*.bak"
      - "*.tmp"
      - "*.swp"
  
  presets:
    # Keep test files minimal
    tests:
      patterns:
        - "**/test_*.py"
        - "**/*_test.py"
      max_lines: 100
    
    # Documentation files
    docs:
      extensions: [".md", ".rst", ".txt"]
      separator_style: "Markdown"
      actions:
        - remove_empty_lines
"""
            global_preset.write_text(example_content)
            logger.info(f"Created example global preset: {global_preset}")

        # Create README
        readme = user_dir / "README.md"
        if not readme.exists():
            readme_content = """# m1f User Configuration

This directory contains your personal m1f preset configurations.

## Structure

- `global-presets.yml` - Global defaults for all m1f operations
- `presets/` - Directory for additional preset files

## Usage

1. Global presets are automatically loaded for all m1f operations
2. Add custom presets to the `presets/` directory
3. Override global settings in your project-specific presets

## Preset Priority

1. Project presets (highest) - specified with --preset
2. User presets - files in ~/.m1f/presets/
3. Global presets (lowest) - ~/.m1f/global-presets.yml

## Example

To disable global HTML stripping for a specific project:

```yaml
my_project:
  priority: 100  # Higher than global
  
  globals:
    extensions:
      .html:
        actions: []  # No processing
```
"""
            readme.write_text(readme_content)
            logger.info(f"Created README: {readme}")
