# Copyright 2025 Franz und Franz GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Preset system for m1f - Apply file-specific processing rules.

This module provides a flexible preset system that allows different processing
rules for different file types within the same m1f bundle.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import yaml
import fnmatch
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ProcessingAction(Enum):
    """Available processing actions for files."""

    NONE = "none"
    MINIFY = "minify"
    STRIP_TAGS = "strip_tags"
    STRIP_COMMENTS = "strip_comments"
    COMPRESS_WHITESPACE = "compress_whitespace"
    REMOVE_EMPTY_LINES = "remove_empty_lines"
    JOIN_PARAGRAPHS = "join_paragraphs"
    CUSTOM = "custom"


@dataclass
class FilePreset:
    """Preset configuration for a specific file type or pattern."""

    # File matching
    patterns: List[str] = field(default_factory=list)  # Glob patterns
    extensions: List[str] = field(default_factory=list)  # File extensions

    # Processing options
    actions: List[ProcessingAction] = field(default_factory=list)
    strip_tags: List[str] = field(default_factory=list)  # HTML tags to strip
    preserve_tags: List[str] = field(default_factory=list)  # Tags to preserve

    # Output options
    separator_style: Optional[str] = (
        None  # DEPRECATED - use global_settings.separator_style instead
    )
    include_metadata: bool = True
    max_lines: Optional[int] = None  # Truncate after N lines

    # File-specific filter overrides
    max_file_size: Optional[str] = None  # Override max file size for these files
    security_check: Optional[str] = None  # Override security check for these files
    include_dot_paths: Optional[bool] = None
    include_binary_files: Optional[bool] = None
    remove_scraped_metadata: Optional[bool] = None

    # Custom processing
    custom_processor: Optional[str] = None  # Name of custom processor
    processor_args: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FilePreset":
        """Create FilePreset from dictionary."""
        # Convert action strings to enums
        if "actions" in data:
            data["actions"] = [
                ProcessingAction(action) if isinstance(action, str) else action
                for action in data["actions"]
            ]
        return cls(**data)


@dataclass
class GlobalSettings:
    """Global settings that apply to all files unless overridden."""

    # General settings
    encoding: Optional[str] = None  # Target encoding (e.g., 'utf-8')
    separator_style: Optional[str] = None  # Default separator style
    line_ending: Optional[str] = None  # 'lf' or 'crlf'

    # Input/Output settings
    source_directory: Optional[str] = None  # Source directory path
    input_file: Optional[str] = None  # Input file path
    output_file: Optional[str] = None  # Output file path
    input_include_files: Optional[Union[str, List[str]]] = None  # Intro files

    # Output control settings
    add_timestamp: Optional[bool] = None  # Add timestamp to filename
    filename_mtime_hash: Optional[bool] = None  # Add hash to filename
    force: Optional[bool] = None  # Force overwrite existing files
    minimal_output: Optional[bool] = None  # Only create main output file
    skip_output_file: Optional[bool] = None  # Skip creating main output file

    # Archive settings
    create_archive: Optional[bool] = None  # Create backup archive
    archive_type: Optional[str] = None  # 'zip' or 'tar.gz'

    # Runtime behavior
    verbose: Optional[bool] = None  # Enable verbose output
    quiet: Optional[bool] = None  # Suppress all output

    # Global include/exclude patterns
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    include_extensions: List[str] = field(default_factory=list)
    exclude_extensions: List[str] = field(default_factory=list)

    # File filtering options
    include_dot_paths: Optional[bool] = None
    include_binary_files: Optional[bool] = None
    include_symlinks: Optional[bool] = None
    no_default_excludes: Optional[bool] = None
    max_file_size: Optional[str] = None  # e.g., "50KB", "10MB"
    exclude_paths_file: Optional[Union[str, List[str]]] = None
    include_paths_file: Optional[Union[str, List[str]]] = None

    # Processing options
    remove_scraped_metadata: Optional[bool] = None
    abort_on_encoding_error: Optional[bool] = None
    prefer_utf8_for_text_files: Optional[bool] = None
    enable_content_deduplication: Optional[bool] = None

    # Security options
    security_check: Optional[str] = None  # 'abort', 'skip', 'warn'

    # Extension-specific defaults
    extension_settings: Dict[str, FilePreset] = field(default_factory=dict)


@dataclass
class PresetGroup:
    """A group of presets with shared configuration."""

    name: str
    description: str = ""
    base_path: Optional[Path] = None

    # File presets by name
    file_presets: Dict[str, FilePreset] = field(default_factory=dict)

    # Default preset for unmatched files
    default_preset: Optional[FilePreset] = None

    # Group-level settings
    enabled: bool = True
    priority: int = 0  # Higher priority groups are checked first

    # Global settings for this group
    global_settings: Optional[GlobalSettings] = None

    def get_preset_for_file(self, file_path: Path) -> Optional[FilePreset]:
        """Get the appropriate preset for a file, merging with global settings."""
        if not self.enabled:
            return None

        # First, check for specific preset match
        matched_preset = None

        # Check each preset's patterns
        for preset_name, preset in self.file_presets.items():
            # Check extensions
            if preset.extensions:
                if file_path.suffix.lower() in [
                    ext.lower() if ext.startswith(".") else f".{ext.lower()}"
                    for ext in preset.extensions
                ]:
                    logger.debug(
                        f"File {file_path} matched extension in preset {preset_name}"
                    )
                    matched_preset = preset
                    break

            # Check patterns
            if preset.patterns:
                for pattern in preset.patterns:
                    if fnmatch.fnmatch(str(file_path), pattern):
                        logger.debug(
                            f"File {file_path} matched pattern '{pattern}' in preset {preset_name}"
                        )
                        matched_preset = preset
                        break

            if matched_preset:
                break

        # If no specific match, use default
        if not matched_preset:
            matched_preset = self.default_preset
            if matched_preset:
                logger.debug(f"Using default preset for {file_path}")

        # Now merge with global settings if available
        if matched_preset and self.global_settings:
            return self._merge_with_globals(matched_preset, file_path)

        return matched_preset

    def _merge_with_globals(self, preset: FilePreset, file_path: Path) -> FilePreset:
        """Merge preset with global extension settings."""
        # Check for global extension defaults
        global_preset = None
        ext = file_path.suffix.lower()
        if ext in self.global_settings.extension_settings:
            global_preset = self.global_settings.extension_settings[ext]

        if not global_preset:
            # No global extension settings to merge
            return preset

        # Create merged preset - local settings override global
        from dataclasses import replace

        merged = replace(preset)

        # Merge actions (local takes precedence if defined)
        if not merged.actions and global_preset.actions:
            merged.actions = global_preset.actions.copy()

        # Merge strip_tags (local overrides)
        if not merged.strip_tags and global_preset.strip_tags:
            merged.strip_tags = global_preset.strip_tags.copy()

        # Merge preserve_tags (combine lists)
        if global_preset.preserve_tags:
            if merged.preserve_tags:
                merged.preserve_tags = list(
                    set(merged.preserve_tags + global_preset.preserve_tags)
                )
            else:
                merged.preserve_tags = global_preset.preserve_tags.copy()

        # Other settings - local always overrides
        if merged.separator_style is None and global_preset.separator_style:
            merged.separator_style = global_preset.separator_style

        if merged.max_lines is None and global_preset.max_lines:
            merged.max_lines = global_preset.max_lines

        return merged


class PresetManager:
    """Manages loading and applying presets."""

    def __init__(self):
        self.groups: Dict[str, PresetGroup] = {}
        self._builtin_processors = self._register_builtin_processors()
        self._merged_global_settings: Optional[GlobalSettings] = None

    def load_preset_file(self, preset_path: Path) -> None:
        """Load presets from a YAML file."""
        # Reset cached merged settings when loading new files
        self._merged_global_settings = None

        # Check file size limit (10MB max for preset files)
        MAX_PRESET_SIZE = 10 * 1024 * 1024  # 10MB
        if preset_path.stat().st_size > MAX_PRESET_SIZE:
            raise ValueError(
                f"Preset file {preset_path} is too large "
                f"({preset_path.stat().st_size / 1024 / 1024:.1f}MB). "
                f"Maximum size is {MAX_PRESET_SIZE / 1024 / 1024}MB"
            )

        try:
            with open(preset_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                raise ValueError(
                    f"Preset file must contain a dictionary, got {type(data)}"
                )

            # Load each group
            for group_name, group_data in data.items():
                if not isinstance(group_data, dict):
                    logger.warning(f"Skipping invalid group {group_name}")
                    continue

                group = self._parse_group(group_name, group_data)
                self.groups[group_name] = group
                logger.debug(
                    f"Loaded preset group '{group_name}' with {len(group.file_presets)} presets"
                )

        except Exception as e:
            logger.error(f"Failed to load preset file {preset_path}: {e}")
            raise

    def _parse_group(self, name: str, data: Dict[str, Any]) -> PresetGroup:
        """Parse a preset group from configuration."""
        group = PresetGroup(
            name=name,
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
            priority=data.get("priority", 0),
        )

        # Parse base path
        if "base_path" in data:
            from .utils import validate_path_traversal

            base_path = Path(data["base_path"])
            # Validate base path from preset files
            try:
                group.base_path = validate_path_traversal(base_path, from_preset=True)
            except ValueError as e:
                raise ValueError(f"Invalid base_path in preset: {e}")

        # Parse global settings
        if "global_settings" in data:
            global_data = data["global_settings"]
            group.global_settings = GlobalSettings()

            # Parse general settings
            if "encoding" in global_data:
                group.global_settings.encoding = global_data["encoding"]
            if "separator_style" in global_data:
                group.global_settings.separator_style = global_data["separator_style"]
            if "line_ending" in global_data:
                group.global_settings.line_ending = global_data["line_ending"]

            # Parse input/output settings
            if "source_directory" in global_data:
                group.global_settings.source_directory = global_data["source_directory"]
            if "input_file" in global_data:
                group.global_settings.input_file = global_data["input_file"]
            if "output_file" in global_data:
                group.global_settings.output_file = global_data["output_file"]
            if "input_include_files" in global_data:
                group.global_settings.input_include_files = global_data[
                    "input_include_files"
                ]

            # Parse output control settings
            if "add_timestamp" in global_data:
                group.global_settings.add_timestamp = global_data["add_timestamp"]
            if "filename_mtime_hash" in global_data:
                group.global_settings.filename_mtime_hash = global_data[
                    "filename_mtime_hash"
                ]
            if "force" in global_data:
                group.global_settings.force = global_data["force"]
            if "minimal_output" in global_data:
                group.global_settings.minimal_output = global_data["minimal_output"]
            if "skip_output_file" in global_data:
                group.global_settings.skip_output_file = global_data["skip_output_file"]

            # Parse archive settings
            if "create_archive" in global_data:
                group.global_settings.create_archive = global_data["create_archive"]
            if "archive_type" in global_data:
                group.global_settings.archive_type = global_data["archive_type"]

            # Parse runtime behavior
            if "verbose" in global_data:
                group.global_settings.verbose = global_data["verbose"]
            if "quiet" in global_data:
                group.global_settings.quiet = global_data["quiet"]

            # Parse include/exclude patterns
            if "include_patterns" in global_data:
                group.global_settings.include_patterns = global_data["include_patterns"]
            if "exclude_patterns" in global_data:
                group.global_settings.exclude_patterns = global_data["exclude_patterns"]
            if "include_extensions" in global_data:
                group.global_settings.include_extensions = global_data[
                    "include_extensions"
                ]
            if "exclude_extensions" in global_data:
                group.global_settings.exclude_extensions = global_data[
                    "exclude_extensions"
                ]

            # Parse file filtering options
            if "include_dot_paths" in global_data:
                group.global_settings.include_dot_paths = global_data[
                    "include_dot_paths"
                ]
            if "include_binary_files" in global_data:
                group.global_settings.include_binary_files = global_data[
                    "include_binary_files"
                ]
            if "include_symlinks" in global_data:
                group.global_settings.include_symlinks = global_data["include_symlinks"]
            if "no_default_excludes" in global_data:
                group.global_settings.no_default_excludes = global_data[
                    "no_default_excludes"
                ]
            if "max_file_size" in global_data:
                group.global_settings.max_file_size = global_data["max_file_size"]
            if "exclude_paths_file" in global_data:
                group.global_settings.exclude_paths_file = global_data[
                    "exclude_paths_file"
                ]
            if "include_paths_file" in global_data:
                group.global_settings.include_paths_file = global_data[
                    "include_paths_file"
                ]

            # Parse processing options
            if "remove_scraped_metadata" in global_data:
                group.global_settings.remove_scraped_metadata = global_data[
                    "remove_scraped_metadata"
                ]
            if "abort_on_encoding_error" in global_data:
                group.global_settings.abort_on_encoding_error = global_data[
                    "abort_on_encoding_error"
                ]

            # Parse security options
            if "security_check" in global_data:
                group.global_settings.security_check = global_data["security_check"]

            # Parse extension-specific settings
            if "extensions" in global_data:
                for ext, preset_data in global_data["extensions"].items():
                    # Normalize extension
                    ext = ext.lower() if ext.startswith(".") else f".{ext.lower()}"
                    group.global_settings.extension_settings[ext] = (
                        FilePreset.from_dict(preset_data)
                    )

        # Parse file presets
        presets_data = data.get("presets", {})
        for preset_name, preset_data in presets_data.items():
            if preset_name == "default":
                group.default_preset = FilePreset.from_dict(preset_data)
            else:
                group.file_presets[preset_name] = FilePreset.from_dict(preset_data)

        return group

    def get_preset_for_file(
        self, file_path: Path, group_name: Optional[str] = None
    ) -> Optional[FilePreset]:
        """Get the appropriate preset for a file."""
        # If specific group requested
        if group_name:
            if group_name in self.groups:
                return self.groups[group_name].get_preset_for_file(file_path)
            else:
                logger.warning(f"Preset group '{group_name}' not found")
                return None

        # Check all groups by priority
        sorted_groups = sorted(
            self.groups.values(), key=lambda g: g.priority, reverse=True
        )

        for group in sorted_groups:
            preset = group.get_preset_for_file(file_path)
            if preset:
                return preset

        return None

    def get_global_settings(self) -> Optional[GlobalSettings]:
        """Get merged global settings from all loaded preset groups."""
        if self._merged_global_settings is not None:
            return self._merged_global_settings

        # Sort groups by priority (highest first)
        sorted_groups = sorted(
            self.groups.values(), key=lambda g: g.priority, reverse=True
        )

        # Merge global settings from all groups
        merged = GlobalSettings()

        for group in sorted_groups:  # Process higher priority first
            if not group.enabled or not group.global_settings:
                continue

            gs = group.global_settings

            # Merge general settings (first non-None value wins due to priority order)
            if gs.encoding and merged.encoding is None:
                merged.encoding = gs.encoding
            if gs.separator_style and merged.separator_style is None:
                merged.separator_style = gs.separator_style
            if gs.line_ending and merged.line_ending is None:
                merged.line_ending = gs.line_ending

            # Merge input/output settings
            if gs.source_directory and merged.source_directory is None:
                merged.source_directory = gs.source_directory
            if gs.input_file and merged.input_file is None:
                merged.input_file = gs.input_file
            if gs.output_file and merged.output_file is None:
                merged.output_file = gs.output_file
            if gs.input_include_files and merged.input_include_files is None:
                merged.input_include_files = gs.input_include_files

            # Merge output control settings
            if gs.add_timestamp is not None and merged.add_timestamp is None:
                merged.add_timestamp = gs.add_timestamp
            if (
                gs.filename_mtime_hash is not None
                and merged.filename_mtime_hash is None
            ):
                merged.filename_mtime_hash = gs.filename_mtime_hash
            if gs.force is not None and merged.force is None:
                merged.force = gs.force
            if gs.minimal_output is not None and merged.minimal_output is None:
                merged.minimal_output = gs.minimal_output
            if gs.skip_output_file is not None and merged.skip_output_file is None:
                merged.skip_output_file = gs.skip_output_file

            # Merge archive settings
            if gs.create_archive is not None and merged.create_archive is None:
                merged.create_archive = gs.create_archive
            if gs.archive_type and merged.archive_type is None:
                merged.archive_type = gs.archive_type

            # Merge runtime behavior
            if gs.verbose is not None and merged.verbose is None:
                merged.verbose = gs.verbose
            if gs.quiet is not None and merged.quiet is None:
                merged.quiet = gs.quiet

            # Merge patterns (combine lists)
            merged.include_patterns.extend(gs.include_patterns)
            merged.exclude_patterns.extend(gs.exclude_patterns)
            merged.include_extensions.extend(gs.include_extensions)
            merged.exclude_extensions.extend(gs.exclude_extensions)

            # Merge file filtering options (higher priority overrides)
            if gs.include_dot_paths is not None and merged.include_dot_paths is None:
                merged.include_dot_paths = gs.include_dot_paths
            if (
                gs.include_binary_files is not None
                and merged.include_binary_files is None
            ):
                merged.include_binary_files = gs.include_binary_files
            if gs.include_symlinks is not None and merged.include_symlinks is None:
                merged.include_symlinks = gs.include_symlinks
            if (
                gs.no_default_excludes is not None
                and merged.no_default_excludes is None
            ):
                merged.no_default_excludes = gs.no_default_excludes
            if gs.max_file_size and merged.max_file_size is None:
                merged.max_file_size = gs.max_file_size
            if gs.exclude_paths_file and merged.exclude_paths_file is None:
                merged.exclude_paths_file = gs.exclude_paths_file
            if gs.include_paths_file and merged.include_paths_file is None:
                merged.include_paths_file = gs.include_paths_file

            # Merge processing options
            if (
                gs.remove_scraped_metadata is not None
                and merged.remove_scraped_metadata is None
            ):
                merged.remove_scraped_metadata = gs.remove_scraped_metadata
            if (
                gs.abort_on_encoding_error is not None
                and merged.abort_on_encoding_error is None
            ):
                merged.abort_on_encoding_error = gs.abort_on_encoding_error

            # Merge security options
            if gs.security_check and merged.security_check is None:
                merged.security_check = gs.security_check

            # Merge extension settings (higher priority overrides)
            for ext, preset in gs.extension_settings.items():
                if ext not in merged.extension_settings:
                    merged.extension_settings[ext] = preset

        # Remove duplicates from lists
        merged.include_patterns = list(set(merged.include_patterns))
        merged.exclude_patterns = list(set(merged.exclude_patterns))
        merged.include_extensions = list(set(merged.include_extensions))
        merged.exclude_extensions = list(set(merged.exclude_extensions))

        self._merged_global_settings = merged
        return merged

    def process_content(self, content: str, preset: FilePreset, file_path: Path) -> str:
        """Apply preset processing to file content."""
        if not preset.actions:
            return content

        for action in preset.actions:
            if action == ProcessingAction.NONE:
                continue
            elif action == ProcessingAction.MINIFY:
                content = self._minify_content(content, file_path)
            elif action == ProcessingAction.STRIP_TAGS:
                content = self._strip_tags(
                    content, preset.strip_tags, preset.preserve_tags
                )
            elif action == ProcessingAction.STRIP_COMMENTS:
                content = self._strip_comments(content, file_path)
            elif action == ProcessingAction.COMPRESS_WHITESPACE:
                content = self._compress_whitespace(content)
            elif action == ProcessingAction.REMOVE_EMPTY_LINES:
                content = self._remove_empty_lines(content)
            elif action == ProcessingAction.JOIN_PARAGRAPHS:
                content = self._join_paragraphs(content)
            elif action == ProcessingAction.CUSTOM:
                content = self._apply_custom_processor(
                    content, preset.custom_processor, preset.processor_args, file_path
                )

        # Apply line limit if specified
        if preset.max_lines:
            lines = content.splitlines()
            if len(lines) > preset.max_lines:
                content = "\n".join(lines[: preset.max_lines])
                content += f"\n... (truncated after {preset.max_lines} lines)"

        return content

    def get_file_specific_settings(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Get file-specific settings (security_check, max_file_size, etc.) for a file."""
        # Get the preset for this file
        preset = self.get_preset_for_file(file_path)
        if not preset:
            return None

        # Collect file-specific settings
        settings = {}

        if preset.security_check is not None:
            settings["security_check"] = preset.security_check
        if preset.max_file_size is not None:
            settings["max_file_size"] = preset.max_file_size
        if preset.include_dot_paths is not None:
            settings["include_dot_paths"] = preset.include_dot_paths
        if preset.include_binary_files is not None:
            settings["include_binary_files"] = preset.include_binary_files
        if preset.remove_scraped_metadata is not None:
            settings["remove_scraped_metadata"] = preset.remove_scraped_metadata

        return settings if settings else None

    def _minify_content(self, content: str, file_path: Path) -> str:
        """Minify content based on file type."""
        ext = file_path.suffix.lower()

        if ext in [".html", ".htm"]:
            # Basic HTML minification
            import re

            # Remove comments
            content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
            # Remove unnecessary whitespace
            content = re.sub(r"\s+", " ", content)
            content = re.sub(r">\s+<", "><", content)
        elif ext in [".css"]:
            # Basic CSS minification
            import re

            content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
            content = re.sub(r"\s+", " ", content)
            content = re.sub(r";\s*}", "}", content)
        elif ext in [".js"]:
            # Very basic JS minification (be careful!)
            lines = content.splitlines()
            minified = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith("//"):
                    minified.append(line)
            content = " ".join(minified)

        return content.strip()

    def _strip_tags(
        self, content: str, tags_to_strip: List[str], preserve_tags: List[str]
    ) -> str:
        """Strip HTML tags from content."""
        # If no specific tags provided, strip all tags
        if not tags_to_strip:
            # Use a simple regex to strip all HTML tags
            import re

            return re.sub(r"<[^>]+>", "", content)

        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(content, "html.parser")

            for tag in tags_to_strip:
                for element in soup.find_all(tag):
                    if preserve_tags and element.name in preserve_tags:
                        continue
                    element.decompose()

            return str(soup)
        except ImportError:
            logger.warning(
                "BeautifulSoup not installed - using regex fallback for tag stripping"
            )
            # Fallback to regex-based stripping
            import re

            for tag in tags_to_strip:
                if tag not in preserve_tags:
                    # Remove opening and closing tags
                    pattern = rf"<{tag}[^>]*>.*?</{tag}>"
                    content = re.sub(
                        pattern, "", content, flags=re.DOTALL | re.IGNORECASE
                    )
                    # Remove self-closing tags
                    pattern = rf"<{tag}[^>]*/?>"
                    content = re.sub(pattern, "", content, flags=re.IGNORECASE)
            return content

    def _strip_comments(self, content: str, file_path: Path) -> str:
        """Strip comments based on file type."""
        ext = file_path.suffix.lower()

        if ext in [".py"]:
            lines = content.splitlines()
            result = []
            in_docstring = False
            docstring_char = None

            for line in lines:
                stripped = line.strip()

                # Handle docstrings
                if '"""' in line or "'''" in line:
                    if not in_docstring:
                        in_docstring = True
                        docstring_char = '"""' if '"""' in line else "'''"
                    elif docstring_char in line:
                        in_docstring = False
                        docstring_char = None

                # Skip comment lines (but not in docstrings)
                if not in_docstring and stripped.startswith("#"):
                    continue

                # Remove inline comments
                if not in_docstring and "#" in line:
                    # Simple approach - might need refinement
                    line = line.split("#")[0].rstrip()

                result.append(line)

            content = "\n".join(result)

        elif ext in [".js", ".java", ".c", ".cpp"]:
            # Remove single-line comments
            import re

            content = re.sub(r"//.*$", "", content, flags=re.MULTILINE)
            # Remove multi-line comments
            content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)

        return content

    def _compress_whitespace(self, content: str) -> str:
        """Compress multiple whitespace characters."""
        import re

        # Replace multiple spaces with single space
        content = re.sub(r" +", " ", content)
        # Replace multiple newlines with double newline
        content = re.sub(r"\n\n+", "\n\n", content)
        return content

    def _remove_empty_lines(self, content: str) -> str:
        """Remove empty lines from content."""
        lines = content.splitlines()
        non_empty = [line for line in lines if line.strip()]
        return "\n".join(non_empty)

    def _join_paragraphs(self, content: str) -> str:
        """Join multi-line paragraphs into single lines for markdown files."""
        lines = content.splitlines()
        result = []
        current_paragraph = []
        in_code_block = False
        in_list = False
        list_indent = 0

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Check for code blocks
            if stripped.startswith("```"):
                # Flush current paragraph
                if current_paragraph:
                    result.append(" ".join(current_paragraph))
                    current_paragraph = []

                # Add code block as-is
                result.append(line)
                in_code_block = not in_code_block
                i += 1
                continue

            # If in code block, add line as-is
            if in_code_block:
                result.append(line)
                i += 1
                continue

            # Check for indented code block (4 spaces or tab)
            if line.startswith("    ") or line.startswith("\t"):
                # Flush current paragraph
                if current_paragraph:
                    result.append(" ".join(current_paragraph))
                    current_paragraph = []
                result.append(line)
                i += 1
                continue

            # Check for tables
            if "|" in line and (i == 0 or i > 0 and "|" in lines[i - 1]):
                # Flush current paragraph
                if current_paragraph:
                    result.append(" ".join(current_paragraph))
                    current_paragraph = []
                result.append(line)
                i += 1
                continue

            # Check for horizontal rules
            if stripped in ["---", "***", "___"] or (
                len(stripped) >= 3
                and all(c in "-*_" for c in stripped)
                and len(set(stripped)) == 1
            ):
                # Flush current paragraph
                if current_paragraph:
                    result.append(" ".join(current_paragraph))
                    current_paragraph = []
                result.append(line)
                i += 1
                continue

            # Check for headings
            if stripped.startswith("#"):
                # Flush current paragraph
                if current_paragraph:
                    result.append(" ".join(current_paragraph))
                    current_paragraph = []
                # Add heading on single line
                result.append(stripped)
                i += 1
                continue

            # Check for blockquotes
            if stripped.startswith(">"):
                # Flush current paragraph
                if current_paragraph:
                    result.append(" ".join(current_paragraph))
                    current_paragraph = []

                # Collect all consecutive blockquote lines
                blockquote_lines = []
                while i < len(lines) and lines[i].strip().startswith(">"):
                    # Remove the > prefix and join
                    content = lines[i].strip()[1:].strip()
                    if content:
                        blockquote_lines.append(content)
                    i += 1

                if blockquote_lines:
                    result.append("> " + " ".join(blockquote_lines))
                continue

            # Check for list items
            import re

            list_pattern = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)$", line)
            if list_pattern:
                # Flush current paragraph
                if current_paragraph:
                    result.append(" ".join(current_paragraph))
                    current_paragraph = []

                indent = list_pattern.group(1)
                marker = list_pattern.group(2)
                content = list_pattern.group(3)

                # Collect multi-line list item
                list_item_lines = [content] if content else []
                i += 1

                # Look for continuation lines
                while i < len(lines):
                    next_line = lines[i]
                    next_stripped = next_line.strip()

                    # Check if it's a new list item or other block element
                    if (
                        re.match(r"^\s*[-*+]\s+", next_line)
                        or re.match(r"^\s*\d+\.\s+", next_line)
                        or next_stripped.startswith("#")
                        or next_stripped.startswith(">")
                        or next_stripped.startswith("```")
                        or next_stripped in ["---", "***", "___"]
                        or not next_stripped
                    ):
                        break

                    # It's a continuation of the current list item
                    if next_line.startswith(
                        " " * (len(indent) + 2)
                    ) or next_line.startswith("\t"):
                        # Remove the indentation and add to current item
                        continuation = next_line[len(indent) + 2 :].strip()
                        if continuation:
                            list_item_lines.append(continuation)
                        i += 1
                    else:
                        break

                # Join the list item content
                joined_content = " ".join(list_item_lines) if list_item_lines else ""
                result.append(f"{indent}{marker} {joined_content}")
                continue

            # Empty line - flush current paragraph
            if not stripped:
                if current_paragraph:
                    result.append(" ".join(current_paragraph))
                    current_paragraph = []
                # Don't add empty lines
                i += 1
                continue

            # Regular paragraph line
            current_paragraph.append(stripped)
            i += 1

        # Flush any remaining paragraph
        if current_paragraph:
            result.append(" ".join(current_paragraph))

        return "\n".join(result)

    def _apply_custom_processor(
        self, content: str, processor_name: str, args: Dict[str, Any], file_path: Path
    ) -> str:
        """Apply a custom processor."""
        if processor_name in self._builtin_processors:
            return self._builtin_processors[processor_name](content, args, file_path)
        else:
            logger.warning(f"Unknown custom processor: {processor_name}")
            return content

    def _register_builtin_processors(self) -> Dict[str, callable]:
        """Register built-in custom processors."""
        return {
            "truncate": self._processor_truncate,
            "redact_secrets": self._processor_redact_secrets,
            "extract_functions": self._processor_extract_functions,
        }

    def _processor_truncate(
        self, content: str, args: Dict[str, Any], file_path: Path
    ) -> str:
        """Truncate content to specified length."""
        max_chars = args.get("max_chars", 1000)
        if len(content) > max_chars:
            return content[:max_chars] + f"\n... (truncated at {max_chars} chars)"
        return content

    def _processor_redact_secrets(
        self, content: str, args: Dict[str, Any], file_path: Path
    ) -> str:
        """Redact potential secrets."""
        import re

        patterns = args.get(
            "patterns",
            [
                r'(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*["\']?[\w-]+["\']?',
                r"(?i)bearer\s+[\w-]+",
            ],
        )

        for pattern in patterns:
            content = re.sub(pattern, "[REDACTED]", content)

        return content

    def _processor_extract_functions(
        self, content: str, args: Dict[str, Any], file_path: Path
    ) -> str:
        """Extract only function definitions."""
        if file_path.suffix.lower() != ".py":
            return content

        import ast

        try:
            tree = ast.parse(content)
            functions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Get function source
                    start_line = node.lineno - 1
                    end_line = node.end_lineno
                    lines = content.splitlines()
                    func_lines = lines[start_line:end_line]
                    functions.append("\n".join(func_lines))

            return "\n\n".join(functions) if functions else "# No functions found"
        except:
            return content


# Convenience function
def load_presets(
    preset_paths: Union[Path, List[Path]], auto_load_user_presets: bool = True
) -> PresetManager:
    """Load presets from one or more files."""
    from .config_loader import PresetConfigLoader

    manager = PresetManager()

    # Convert single path to list
    if isinstance(preset_paths, Path):
        preset_paths = [preset_paths]
    elif not preset_paths:
        preset_paths = []

    # Get all preset files to load
    all_preset_files = PresetConfigLoader.load_all_presets(
        project_presets=preset_paths,
        include_global=auto_load_user_presets,
        include_user=auto_load_user_presets,
    )

    # Load each file
    for path in all_preset_files:
        if path.exists():
            manager.load_preset_file(path)
            logger.debug(f"Loaded preset file: {path}")
        else:
            logger.warning(f"Preset file not found: {path}")

    return manager


def list_loaded_presets(manager: PresetManager) -> str:
    """Generate a summary of loaded presets."""
    lines = ["Loaded Preset Groups:"]

    # Sort by priority
    sorted_groups = sorted(
        manager.groups.items(), key=lambda x: x[1].priority, reverse=True
    )

    for name, group in sorted_groups:
        status = "enabled" if group.enabled else "disabled"
        lines.append(f"\n{name} (priority: {group.priority}, {status})")
        if group.description:
            lines.append(f"  Description: {group.description}")

        # Show global settings
        if group.globals and group.globals.extension_defaults:
            lines.append("  Global extensions:")
            for ext, preset in group.globals.extension_defaults.items():
                actions = (
                    [a.value for a in preset.actions] if preset.actions else ["none"]
                )
                lines.append(f"    {ext}: {', '.join(actions)}")

        # Show presets
        if group.file_presets:
            lines.append("  Presets:")
            for preset_name, preset in group.file_presets.items():
                if preset.extensions:
                    lines.append(f"    {preset_name}: {', '.join(preset.extensions)}")
                elif preset.patterns:
                    lines.append(f"    {preset_name}: {preset.patterns[0]}...")

    return "\n".join(lines)
