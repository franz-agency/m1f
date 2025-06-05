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
Configuration classes for m1f using dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional, Set, List, Union
import argparse

from .utils import parse_file_size


class SeparatorStyle(Enum):
    """Enumeration for separator styles."""

    STANDARD = "Standard"
    DETAILED = "Detailed"
    MARKDOWN = "Markdown"
    MACHINE_READABLE = "MachineReadable"
    NONE = "None"


class LineEnding(Enum):
    """Enumeration for line endings."""

    LF = "\n"
    CRLF = "\r\n"

    @classmethod
    def from_str(cls, value: str) -> LineEnding:
        """Create from string value."""
        if value.lower() == "lf":
            return cls.LF
        elif value.lower() == "crlf":
            return cls.CRLF
        else:
            raise ValueError(f"Invalid line ending: {value}")


class ArchiveType(Enum):
    """Enumeration for archive types."""

    ZIP = "zip"
    TAR_GZ = "tar.gz"


class SecurityCheckMode(Enum):
    """Security check modes."""

    ABORT = "abort"
    SKIP = "skip"
    WARN = "warn"


@dataclass(frozen=True)
class EncodingConfig:
    """Configuration for encoding settings."""

    target_charset: Optional[str] = None
    abort_on_error: bool = False


@dataclass(frozen=True)
class OutputConfig:
    """Configuration for output settings."""

    output_file: Path
    add_timestamp: bool = False
    filename_mtime_hash: bool = False
    force_overwrite: bool = False
    minimal_output: bool = False
    skip_output_file: bool = False
    separator_style: SeparatorStyle = SeparatorStyle.DETAILED
    line_ending: LineEnding = LineEnding.LF


@dataclass(frozen=True)
class FilterConfig:
    """Configuration for file filtering."""

    exclude_paths: Set[str] = field(default_factory=set)
    exclude_patterns: List[str] = field(default_factory=list)
    exclude_paths_file: Optional[Union[str, List[str]]] = None
    include_paths_file: Optional[Union[str, List[str]]] = None
    include_extensions: Set[str] = field(default_factory=set)
    exclude_extensions: Set[str] = field(default_factory=set)
    include_dot_paths: bool = False
    include_binary_files: bool = False
    include_symlinks: bool = False
    no_default_excludes: bool = False
    max_file_size: Optional[int] = None  # Size in bytes
    remove_scraped_metadata: bool = False


@dataclass(frozen=True)
class SecurityConfig:
    """Configuration for security settings."""

    security_check: Optional[SecurityCheckMode] = None


@dataclass(frozen=True)
class ArchiveConfig:
    """Configuration for archive settings."""

    create_archive: bool = False
    archive_type: ArchiveType = ArchiveType.ZIP


@dataclass(frozen=True)
class LoggingConfig:
    """Configuration for logging settings."""

    verbose: bool = False
    quiet: bool = False


@dataclass(frozen=True)
class PresetConfig:
    """Configuration for preset settings."""

    preset_files: List[Path] = field(default_factory=list)
    preset_group: Optional[str] = None
    disable_presets: bool = False


@dataclass(frozen=True)
class Config:
    """Main configuration class that combines all settings."""

    source_directory: Optional[Path]
    input_file: Optional[Path]
    input_include_files: List[Path]
    output: OutputConfig
    filter: FilterConfig
    encoding: EncodingConfig
    security: SecurityConfig
    archive: ArchiveConfig
    logging: LoggingConfig
    preset: PresetConfig

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> Config:
        """Create configuration from parsed arguments."""
        # First create the basic config from CLI args
        config = cls._create_from_cli_args(args)
        
        # Then apply preset overrides if presets are enabled
        if not config.preset.disable_presets and config.preset.preset_files:
            config = cls._apply_preset_overrides(config, args)
        
        # Validate that we have required inputs after preset application
        if not config.source_directory and not config.input_file:
            raise ValueError(
                "At least one of source_directory or input_file must be provided "
                "(either via CLI arguments or preset configuration)"
            )
        
        return config
    
    @classmethod
    def _create_from_cli_args(cls, args: argparse.Namespace) -> Config:
        """Create initial configuration from CLI arguments."""
        # Process source directory
        source_dir = (
            Path(args.source_directory).resolve() if args.source_directory else None
        )

        # Process input file
        input_file = Path(args.input_file).resolve() if args.input_file else None

        # Process include files
        include_files = []
        if hasattr(args, "input_include_files") and args.input_include_files:
            include_files = [Path(f).resolve() for f in args.input_include_files]

        # Create output configuration
        output_config = OutputConfig(
            output_file=Path(args.output_file).resolve(),
            add_timestamp=args.add_timestamp,
            filename_mtime_hash=getattr(args, "filename_mtime_hash", False),
            force_overwrite=args.force,
            minimal_output=getattr(args, "minimal_output", False),
            skip_output_file=getattr(args, "skip_output_file", False),
            separator_style=SeparatorStyle(args.separator_style),
            line_ending=LineEnding.from_str(args.line_ending),
        )

        # Parse max file size if provided
        max_file_size_bytes = None
        if hasattr(args, "max_file_size") and args.max_file_size:
            try:
                max_file_size_bytes = parse_file_size(args.max_file_size)
            except ValueError as e:
                raise ValueError(f"Invalid --max-file-size value: {e}")

        # Create filter configuration
        filter_config = FilterConfig(
            exclude_paths=set(getattr(args, "exclude_paths", [])),
            exclude_patterns=getattr(args, "excludes", []),
            exclude_paths_file=getattr(args, "exclude_paths_file", None),
            include_paths_file=getattr(args, "include_paths_file", None),
            include_extensions=set(
                normalize_extensions(getattr(args, "include_extensions", []))
            ),
            exclude_extensions=set(
                normalize_extensions(getattr(args, "exclude_extensions", []))
            ),
            include_dot_paths=getattr(args, "include_dot_paths", False),
            include_binary_files=getattr(args, "include_binary_files", False),
            include_symlinks=getattr(args, "include_symlinks", False),
            no_default_excludes=getattr(args, "no_default_excludes", False),
            max_file_size=max_file_size_bytes,
            remove_scraped_metadata=getattr(args, "remove_scraped_metadata", False),
        )

        # Create encoding configuration
        encoding_config = EncodingConfig(
            target_charset=getattr(args, "convert_to_charset", None),
            abort_on_error=getattr(args, "abort_on_encoding_error", False),
        )

        # Create security configuration
        security_mode = None
        if hasattr(args, "security_check") and args.security_check:
            security_mode = SecurityCheckMode(args.security_check)

        security_config = SecurityConfig(security_check=security_mode)

        # Create archive configuration
        archive_config = ArchiveConfig(
            create_archive=getattr(args, "create_archive", False),
            archive_type=ArchiveType(getattr(args, "archive_type", "zip")),
        )

        # Create logging configuration
        logging_config = LoggingConfig(
            verbose=args.verbose, quiet=getattr(args, "quiet", False)
        )

        # Create preset configuration
        preset_files = []
        if hasattr(args, "preset_files") and args.preset_files:
            preset_files = [Path(f).resolve() for f in args.preset_files]

        preset_config = PresetConfig(
            preset_files=preset_files,
            preset_group=getattr(args, "preset_group", None),
            disable_presets=getattr(args, "disable_presets", False),
        )

        return cls(
            source_directory=source_dir,
            input_file=input_file,
            input_include_files=include_files,
            output=output_config,
            filter=filter_config,
            encoding=encoding_config,
            security=security_config,
            archive=archive_config,
            logging=logging_config,
            preset=preset_config,
        )
    
    @classmethod
    def _apply_preset_overrides(cls, config: Config, args: argparse.Namespace) -> Config:
        """Apply preset overrides to configuration."""
        from .presets import load_presets
        
        # Load presets
        preset_manager = load_presets(config.preset.preset_files)
        global_settings = preset_manager.get_global_settings()
        
        if not global_settings:
            return config
        
        # Apply overrides - CLI arguments take precedence over presets
        
        # Input/Output overrides
        source_dir = config.source_directory
        input_file = config.input_file
        output_file = config.output.output_file
        input_include_files = config.input_include_files
        
        # Only override if not provided via CLI
        if not args.source_directory and global_settings.source_directory:
            source_dir = Path(global_settings.source_directory).resolve()
        
        if not args.input_file and global_settings.input_file:
            input_file = Path(global_settings.input_file).resolve()
        
        if not getattr(args, "_output_file_from_cli", True) and global_settings.output_file:
            output_file = Path(global_settings.output_file).resolve()
        
        if not args.input_include_files and global_settings.input_include_files:
            if isinstance(global_settings.input_include_files, str):
                input_include_files = [Path(global_settings.input_include_files).resolve()]
            else:
                input_include_files = [Path(f).resolve() for f in global_settings.input_include_files]
        
        # Create new OutputConfig with overrides
        output_config = OutputConfig(
            output_file=output_file,
            add_timestamp=args.add_timestamp if args.add_timestamp else (global_settings.add_timestamp or False),
            filename_mtime_hash=getattr(args, "filename_mtime_hash", False) or (global_settings.filename_mtime_hash or False),
            force_overwrite=args.force if args.force else (global_settings.force or False),
            minimal_output=getattr(args, "minimal_output", False) or (global_settings.minimal_output or False),
            skip_output_file=getattr(args, "skip_output_file", False) or (global_settings.skip_output_file or False),
            separator_style=SeparatorStyle(args.separator_style) if args.separator_style != "Detailed" else (
                SeparatorStyle(global_settings.separator_style) if global_settings.separator_style else SeparatorStyle.DETAILED
            ),
            line_ending=LineEnding.from_str(args.line_ending) if args.line_ending != "lf" else (
                LineEnding.from_str(global_settings.line_ending) if global_settings.line_ending else LineEnding.LF
            ),
        )
        
        # Create new ArchiveConfig with overrides
        archive_config = ArchiveConfig(
            create_archive=getattr(args, "create_archive", False) or (global_settings.create_archive or False),
            archive_type=ArchiveType(getattr(args, "archive_type", "zip")) if getattr(args, "archive_type", "zip") != "zip" else (
                ArchiveType(global_settings.archive_type) if global_settings.archive_type else ArchiveType.ZIP
            ),
        )
        
        # Create new LoggingConfig with overrides
        logging_config = LoggingConfig(
            verbose=args.verbose if args.verbose else (global_settings.verbose or False),
            quiet=getattr(args, "quiet", False) or (global_settings.quiet or False),
        )
        
        # Return new config with overrides applied
        return cls(
            source_directory=source_dir,
            input_file=input_file,
            input_include_files=input_include_files,
            output=output_config,
            filter=config.filter,  # Filter settings are handled separately in FileProcessor
            encoding=config.encoding,  # Encoding settings are handled separately
            security=config.security,  # Security settings are handled separately
            archive=archive_config,
            logging=logging_config,
            preset=config.preset,
        )


def normalize_extensions(extensions: List[str]) -> List[str]:
    """Normalize file extensions to ensure they start with a dot."""
    if not extensions:
        return []

    normalized = []
    for ext in extensions:
        if ext.startswith("."):
            normalized.append(ext.lower())
        else:
            normalized.append(f".{ext.lower()}")

    return normalized
