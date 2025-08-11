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
File processor module for gathering and filtering files.
"""

from __future__ import annotations

import asyncio
import glob
import os
from pathlib import Path
from typing import List, Tuple, Set, Optional

import pathspec

from .config import Config, FilterConfig
from .constants import (
    DEFAULT_EXCLUDED_DIRS,
    DEFAULT_EXCLUDED_FILES,
    DEFAULT_EXCLUDED_PATTERNS,
    MAX_SYMLINK_DEPTH,
)
from .exceptions import FileNotFoundError, ValidationError
from .logging import LoggerManager
from .utils import (
    is_binary_file,
    is_hidden_path,
    get_relative_path,
    format_file_size,
    validate_path_traversal,
)


class FileProcessor:
    """Handles file discovery and filtering."""

    def __init__(self, config: Config, logger_manager: LoggerManager):
        self.config = config
        self.logger = logger_manager.get_logger(__name__)
        self._symlink_visited: Set[str] = set()
        self._processed_files: Set[str] = set()

        # Initialize preset manager for global settings
        self.preset_manager = None
        self.global_settings = None
        if not config.preset.disable_presets and config.preset.preset_files:
            try:
                from .presets import load_presets

                self.preset_manager = load_presets(config.preset.preset_files)
                self.global_settings = self.preset_manager.get_global_settings()
                self.logger.debug("Loaded global preset settings")
            except Exception as e:
                self.logger.warning(f"Failed to load preset settings: {e}")

        # Apply global filter settings first (before building exclusion sets)
        # This ensures global exclude_paths_file is available for _build_exclusion_sets
        self._apply_global_filter_settings()

        # Build exclusion sets (will now use merged config including global settings)
        self._build_exclusion_sets()

    def _build_exclusion_sets(self) -> None:
        """Build the exclusion sets from configuration."""
        # Directory exclusions
        self.excluded_dirs = set()
        if not self.config.filter.no_default_excludes:
            self.excluded_dirs = {d.lower() for d in DEFAULT_EXCLUDED_DIRS}

        # Collect all exclude patterns from config and global settings
        all_exclude_patterns = list(self.config.filter.exclude_patterns)
        if self.global_settings and self.global_settings.exclude_patterns:
            all_exclude_patterns.extend(self.global_settings.exclude_patterns)

        # Add default patterns unless disabled
        if not self.config.filter.no_default_excludes:
            all_exclude_patterns.extend(DEFAULT_EXCLUDED_PATTERNS)

        # Process exclude patterns - determine if they are directories or files
        for pattern in all_exclude_patterns:
            if "/" not in pattern and "*" not in pattern and "?" not in pattern:
                # Simple name without wildcards or paths
                if self.config.source_directories:
                    # Try to find the pattern in any of the source directories
                    potential_path = self.config.source_directories[0] / pattern
                    try:
                        if potential_path.exists():
                            if potential_path.is_dir():
                                self.excluded_dirs.add(pattern.lower())
                            # If it's a file, it will be handled by gitignore spec
                        else:
                            # If not found, assume it's a directory pattern for safety
                            self.excluded_dirs.add(pattern.lower())
                    except PermissionError:
                        # If we can't access the path due to permissions, log warning and skip
                        self.logger.warning(
                            f"Permission denied accessing '{potential_path}'. Skipping exclusion check for this path."
                        )
                        # Add to excluded dirs to avoid further permission issues
                        self.excluded_dirs.add(pattern.lower())
                else:
                    # No source directory specified, add to dirs for backward compatibility
                    self.excluded_dirs.add(pattern.lower())

        # File exclusions
        self.excluded_files = set()
        if not self.config.filter.no_default_excludes:
            self.excluded_files = DEFAULT_EXCLUDED_FILES.copy()

        # Load exclusions from file
        self.exact_excludes = set()
        self.gitignore_spec = None

        if self.config.filter.exclude_paths_file:
            self._load_exclude_patterns()

        # Auto-load .m1fignore and .gitignore files from source directories
        self._auto_load_ignore_files()

        # Load inclusions from file
        self.exact_includes = set()
        self.include_gitignore_spec = None

        # Load include patterns from files or config
        self._load_include_patterns()

        # Build gitignore spec from command-line patterns
        self._build_gitignore_spec()

    def _auto_load_ignore_files(self) -> None:
        """Automatically load .m1fignore and .gitignore files from source directories."""
        # Recursion protection - ensure this is only called once
        if hasattr(self, "_auto_load_ignore_files_called"):
            self.logger.warning("_auto_load_ignore_files called recursively - skipping")
            return
        self._auto_load_ignore_files_called = True

        if not self.config.source_directories:
            return

        # Track which files we've already loaded to avoid duplicates
        loaded_files = set()
        if self.config.filter.exclude_paths_file:
            if isinstance(self.config.filter.exclude_paths_file, (str, Path)):
                # Use strict=False to avoid issues with circular symlinks
                try:
                    loaded_files.add(
                        Path(self.config.filter.exclude_paths_file).resolve(
                            strict=False
                        )
                    )
                except Exception as e:
                    self.logger.warning(f"Could not resolve path: {e}")
            else:
                for f in self.config.filter.exclude_paths_file:
                    try:
                        loaded_files.add(Path(f).resolve(strict=False))
                    except Exception as e:
                        self.logger.warning(f"Could not resolve path: {e}")

        # Process each source directory
        for source_dir in self.config.source_directories:
            # Always load .m1fignore if it exists
            m1fignore_path = source_dir / ".m1fignore"
            try:
                m1fignore_resolved = m1fignore_path.resolve(strict=False)
                if m1fignore_path.exists() and m1fignore_resolved not in loaded_files:
                    self.logger.debug(f"Auto-loading .m1fignore from {source_dir}")
                    self._load_exclude_patterns_from_file(m1fignore_path)
                    loaded_files.add(m1fignore_resolved)
            except Exception as e:
                self.logger.warning(f"Error loading .m1fignore: {e}")

            # Load .gitignore unless disabled
            if not self.config.filter.no_auto_gitignore:
                gitignore_path = source_dir / ".gitignore"
                try:
                    gitignore_resolved = gitignore_path.resolve(strict=False)
                    if (
                        gitignore_path.exists()
                        and gitignore_resolved not in loaded_files
                    ):
                        self.logger.debug(f"Auto-loading .gitignore from {source_dir}")
                        self._load_exclude_patterns_from_file(gitignore_path)
                        loaded_files.add(gitignore_resolved)
                except Exception as e:
                    self.logger.warning(f"Error loading .gitignore: {e}")

    def _load_exclude_patterns(self) -> None:
        """Load exclusion patterns from file(s)."""
        exclude_files_param = self.config.filter.exclude_paths_file
        if not exclude_files_param:
            return

        # Convert to list if it's a single string/Path
        if isinstance(exclude_files_param, (str, Path)):
            exclude_files = [exclude_files_param]
        else:
            exclude_files = exclude_files_param

        all_gitignore_lines = []

        for exclude_file_str in exclude_files:
            exclude_file = Path(exclude_file_str)

            try:
                if not exclude_file.exists():
                    self.logger.info(
                        f"Exclude file not found (skipping): {exclude_file}"
                    )
                    continue
            except PermissionError:
                self.logger.warning(
                    f"Permission denied accessing exclude file '{exclude_file}'. Skipping."
                )
                continue

            try:
                with open(exclude_file, "r", encoding="utf-8") as f:
                    lines = [
                        line.strip()
                        for line in f
                        if line.strip() and not line.strip().startswith("#")
                    ]
                # Explicitly close file handle on Windows for immediate cleanup
                # The context manager should handle this, but ensure it's done
                f = None

                # Detect if it's gitignore format
                is_gitignore = exclude_file.name == ".gitignore" or any(
                    any(ch in line for ch in ["*", "?", "!"]) or line.endswith("/")
                    for line in lines
                )

                if is_gitignore:
                    self.logger.info(f"Processing {exclude_file} as gitignore format")
                    all_gitignore_lines.extend(lines)
                else:
                    self.logger.info(f"Processing {exclude_file} as exact path list")
                    for line in lines:
                        path = Path(line)
                        if not path.is_absolute() and self.config.source_directories:
                            # Use the first source directory as base
                            path = self.config.source_directories[0] / path
                        try:
                            validated_path = validate_path_traversal(path.resolve())
                            self.exact_excludes.add(str(validated_path))
                        except ValueError as e:
                            self.logger.warning(
                                f"Skipping invalid exclude path '{line}': {e}"
                            )

            except Exception as e:
                self.logger.warning(f"Error reading exclude file {exclude_file}: {e}")

        # Build combined gitignore spec from all collected lines
        if all_gitignore_lines:
            self.gitignore_spec = pathspec.PathSpec.from_lines(
                "gitwildmatch", all_gitignore_lines
            )

    def _load_include_patterns(self) -> None:
        """Load inclusion patterns from file(s) and/or config."""
        all_gitignore_lines = []

        # First, load patterns from include_paths_file if specified
        include_files_param = self.config.filter.include_paths_file
        if include_files_param:
            # Convert to list if it's a single string/Path
            if isinstance(include_files_param, (str, Path)):
                include_files = [include_files_param]
            else:
                include_files = include_files_param

            for include_file_str in include_files:
                include_file = Path(include_file_str)

                try:
                    if not include_file.exists():
                        self.logger.info(
                            f"Include file not found (skipping): {include_file}"
                        )
                        continue
                except PermissionError:
                    self.logger.warning(
                        f"Permission denied accessing include file '{include_file}'. Skipping."
                    )
                    continue

                try:
                    with open(include_file, "r", encoding="utf-8") as f:
                        lines = [
                            line.strip()
                            for line in f
                            if line.strip() and not line.strip().startswith("#")
                        ]
                    # Explicitly ensure file handle is released
                    f = None

                    # Detect if it's gitignore format
                    is_gitignore = any(
                        any(ch in line for ch in ["*", "?", "!"]) or line.endswith("/")
                        for line in lines
                    )

                    if is_gitignore:
                        self.logger.info(
                            f"Processing {include_file} as gitignore format"
                        )
                        all_gitignore_lines.extend(lines)
                    else:
                        self.logger.info(
                            f"Processing {include_file} as exact path list"
                        )
                        for line in lines:
                            path = Path(line)
                            if (
                                not path.is_absolute()
                                and self.config.source_directories
                            ):
                                # Use the first source directory as base
                                path = self.config.source_directories[0] / path
                            try:
                                validated_path = validate_path_traversal(path.resolve())
                                self.exact_includes.add(str(validated_path))
                            except ValueError as e:
                                self.logger.warning(
                                    f"Skipping invalid include path '{line}': {e}"
                                )

                except Exception as e:
                    self.logger.warning(
                        f"Error reading include file {include_file}: {e}"
                    )

        # Add include patterns from config
        if self.config.filter.include_patterns:
            all_gitignore_lines.extend(self.config.filter.include_patterns)

        # Build combined gitignore spec from all collected lines
        if all_gitignore_lines:
            self.include_gitignore_spec = pathspec.PathSpec.from_lines(
                "gitwildmatch", all_gitignore_lines
            )

    def _get_base_dir_for_path(self, path: Path) -> Path:
        """Get the appropriate base directory for a given path."""
        # Check if the path is under any of our source directories
        if self.config.source_directories:
            for source_dir in self.config.source_directories:
                try:
                    path.relative_to(source_dir)
                    return source_dir
                except ValueError:
                    continue
        # Default to the path's parent
        return path.parent

    def _build_gitignore_spec(self) -> None:
        """Build gitignore spec from command-line patterns."""
        patterns = []

        # Add default patterns unless disabled
        if not self.config.filter.no_default_excludes:
            patterns.extend(DEFAULT_EXCLUDED_PATTERNS)

        # ALL patterns should be processed, not just those with wildcards
        # This allows excluding specific files like "CLAUDE.md" without wildcards
        for pattern in self.config.filter.exclude_patterns:
            patterns.append(pattern)

        # Add global preset exclude patterns
        if self.global_settings and self.global_settings.exclude_patterns:
            for pattern in self.global_settings.exclude_patterns:
                patterns.append(pattern)

        if patterns:
            try:
                spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)
                if self.gitignore_spec:
                    # Combine with existing spec
                    all_patterns = list(self.gitignore_spec.patterns) + list(
                        spec.patterns
                    )
                    self.gitignore_spec = pathspec.PathSpec(all_patterns)
                else:
                    self.gitignore_spec = spec
            except Exception as e:
                self.logger.error(f"Error building gitignore spec: {e}")

    async def gather_files(self) -> List[Tuple[Path, str]]:
        """Gather all files to process based on configuration."""
        files_to_process = []

        if self.config.input_file:
            # Process from input file
            input_paths = await self._process_input_file()
            files_to_process = await self._gather_from_paths(input_paths)
        elif self.config.source_directories:
            # Process from source directories
            files_to_process = []
            for source_dir in self.config.source_directories:
                dir_files = await self._gather_from_directory(source_dir)
                files_to_process.extend(dir_files)
        else:
            raise ValidationError("No source directory or input file specified")

        # Sort by relative path
        files_to_process.sort(key=lambda x: x[1].lower())

        return files_to_process

    async def _process_input_file(self) -> List[Path]:
        """Process input file and return list of paths."""
        input_file = self.config.input_file
        paths = []

        base_dir = (
            self.config.source_directories[0]
            if self.config.source_directories
            else input_file.parent
        )

        try:
            with open(input_file, "r", encoding="utf-8") as f:
                content_lines = f.readlines()
            # Explicitly ensure file handle is released before processing
            f = None

            for line in content_lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Handle glob patterns
                if any(ch in line for ch in ["*", "?", "["]):
                    pattern_path = Path(line)
                    if not pattern_path.is_absolute():
                        pattern_path = base_dir / pattern_path

                    matches = glob.glob(str(pattern_path), recursive=True)
                    for m in matches:
                        try:
                            validated_path = validate_path_traversal(Path(m).resolve())
                            paths.append(validated_path)
                        except ValueError as e:
                            self.logger.warning(
                                f"Skipping invalid glob match '{m}': {e}"
                            )
                else:
                    path = Path(line)
                    if not path.is_absolute():
                        path = base_dir / path
                    try:
                        validated_path = validate_path_traversal(path.resolve())
                        paths.append(validated_path)
                    except ValueError as e:
                        self.logger.warning(f"Skipping invalid path '{line}': {e}")

            # Deduplicate paths
            paths = self._deduplicate_paths(paths)

            self.logger.info(f"Found {len(paths)} paths from input file")
            return paths

        except Exception as e:
            raise FileNotFoundError(f"Error processing input file: {e}")

    def _deduplicate_paths(self, paths: List[Path]) -> List[Path]:
        """Remove paths that are children of other paths in the list."""
        if not paths:
            return []

        # Sort by path depth
        paths.sort(key=lambda p: len(p.parts))

        # Keep only paths that aren't children of others
        keep_paths = set(paths)

        for i, path in enumerate(paths):
            if path not in keep_paths:
                continue

            for other_path in paths[i + 1 :]:
                try:
                    if other_path.is_relative_to(path):
                        keep_paths.discard(other_path)
                except (ValueError, RuntimeError):
                    continue

        return sorted(keep_paths)

    async def _gather_from_paths(self, paths: List[Path]) -> List[Tuple[Path, str]]:
        """Gather files from a list of paths."""
        files = []

        for path in paths:
            try:
                if not path.exists():
                    self.logger.warning(f"Path not found: {path}")
                    continue

                if path.is_file():
                    if await self._should_include_file(path, explicitly_included=True):
                        rel_path = get_relative_path(
                            path, self._get_base_dir_for_path(path)
                        )
                        files.append((path, rel_path))
                elif path.is_dir():
                    dir_files = await self._gather_from_directory(
                        path, explicitly_included=True
                    )
                    files.extend(dir_files)
            except PermissionError:
                self.logger.error(
                    f"Permission denied: Cannot access '{path}'. Please check file/directory permissions."
                )
                continue

        return files

    async def _gather_from_directory(
        self, directory: Path, explicitly_included: bool = False
    ) -> List[Tuple[Path, str]]:
        """Recursively gather files from a directory."""
        files = []

        # Use os.walk for efficiency
        for root, dirs, filenames in os.walk(
            directory, followlinks=self.config.filter.include_symlinks
        ):
            root_path = Path(root)

            # Filter directories
            dirs[:] = await self._filter_directories(root_path, dirs)

            # Process files
            for filename in filenames:
                file_path = root_path / filename

                if await self._should_include_file(file_path, explicitly_included):
                    # For symlinks when include_symlinks is True, preserve the symlink path
                    # instead of resolving it to the target path
                    if self.config.filter.include_symlinks and file_path.is_symlink():
                        try:
                            base_dir = self._get_base_dir_for_path(file_path)
                            rel_path = file_path.relative_to(base_dir).as_posix()
                        except ValueError:
                            # If file is not under base path, use absolute path
                            rel_path = str(file_path)
                    else:
                        rel_path = get_relative_path(
                            file_path, self._get_base_dir_for_path(file_path)
                        )

                    # Check for duplicates with improved symlink handling
                    if self.config.filter.include_symlinks and file_path.is_symlink():
                        # If allow_duplicate_files is set (content deduplication disabled),
                        # always use the symlink path to allow duplicates
                        if not self.config.output.enable_content_deduplication:
                            dedup_key = str(file_path)
                        else:
                            # Content deduplication is enabled, check if target is internal
                            target = file_path.resolve()
                            if self._is_target_within_sources(target):
                                # Target is internal - use resolved path for deduplication
                                # This will cause the symlink to be skipped if the target
                                # is already included
                                dedup_key = str(target)
                            else:
                                # Target is external - use symlink path to ensure it's included
                                dedup_key = str(file_path)
                    else:
                        # Not a symlink or symlinks not included - use resolved path
                        dedup_key = str(file_path.resolve())

                    if dedup_key not in self._processed_files:
                        files.append((file_path, rel_path))
                        self._processed_files.add(dedup_key)
                    else:
                        self.logger.debug(
                            f"Skipping duplicate: {file_path} (key: {dedup_key})"
                        )
                else:
                    self.logger.debug(f"File excluded by filter: {file_path}")

        return files

    async def _filter_directories(self, root: Path, dirs: List[str]) -> List[str]:
        """Filter directories based on exclusion rules."""
        filtered = []

        for dirname in dirs:
            dir_path = root / dirname

            # Check if directory is excluded by name
            if dirname.lower() in self.excluded_dirs:
                self.logger.debug(f"Directory excluded by name: {dir_path}")
                continue

            # Check dot directories
            if not self.config.filter.include_dot_paths and dirname.startswith("."):
                self.logger.debug(f"Dot directory excluded: {dir_path}")
                continue

            # Check symlinks
            if dir_path.is_symlink():
                if not self.config.filter.include_symlinks:
                    self.logger.debug(f"Symlink directory excluded: {dir_path}")
                    continue

                # Check for cycles
                if self._detect_symlink_cycle(dir_path):
                    self.logger.warning(f"Skipping symlink cycle: {dir_path}")
                    continue

            # Check gitignore patterns - this is the critical performance fix!
            if self.gitignore_spec:
                # Get relative path from source directory or current root
                base_dir = (
                    self.config.source_directories[0]
                    if self.config.source_directories
                    else Path.cwd()
                )
                try:
                    rel_path = dir_path.relative_to(base_dir)
                except ValueError:
                    # If dir_path is not relative to base_dir, use as is
                    rel_path = dir_path

                # For directory matching, we need to append a trailing slash
                # Always use forward slashes for gitignore pattern matching
                rel_path_str = str(rel_path).replace("\\", "/")
                if not rel_path_str.endswith("/"):
                    rel_path_str += "/"

                # Check if directory matches any exclude pattern
                if self.gitignore_spec.match_file(rel_path_str):
                    self.logger.debug(
                        f"Directory excluded by gitignore pattern: {dir_path}"
                    )
                    continue

            filtered.append(dirname)

        return filtered

    async def _should_include_file(
        self, file_path: Path, explicitly_included: bool = False
    ) -> bool:
        """Check if a file should be included based on filters."""
        # Check if file exists
        try:
            if not file_path.exists():
                return False
        except PermissionError:
            self.logger.warning(f"Permission denied accessing '{file_path}'. Skipping.")
            return False

        # Check docs_only filter first (highest priority)
        if self.config.filter.docs_only:
            from .constants import DOCUMENTATION_EXTENSIONS

            if file_path.suffix.lower() not in DOCUMENTATION_EXTENSIONS:
                return False

        # If explicitly included (from -i file), skip most filters but still check binary
        if explicitly_included:
            # Still check binary files even for explicitly included files
            include_binary = self.config.filter.include_binary_files
            if (
                hasattr(self, "_global_include_binary_files")
                and self._global_include_binary_files is not None
            ):
                include_binary = include_binary or self._global_include_binary_files

            if not include_binary and is_binary_file(file_path):
                return False

            return True

        # Get file-specific settings from presets
        file_settings = {}
        if self.preset_manager:
            file_settings = (
                self.preset_manager.get_file_specific_settings(file_path) or {}
            )

        # Check if we have include patterns - if yes, file must match one
        if self.exact_includes or self.include_gitignore_spec:
            include_matched = False

            # Check exact includes
            if str(file_path.resolve()) in self.exact_includes:
                include_matched = True

            # Check include gitignore patterns
            if not include_matched and self.include_gitignore_spec:
                rel_path = get_relative_path(
                    file_path, self._get_base_dir_for_path(file_path)
                )
                # Note: get_relative_path already returns forward slashes via as_posix()
                if self.include_gitignore_spec.match_file(rel_path):
                    include_matched = True

            # If we have include patterns but file doesn't match any, exclude it
            if not include_matched:
                return False

        # Check exact excludes
        if str(file_path.resolve()) in self.exact_excludes:
            return False

        # Check filename excludes
        if file_path.name in self.excluded_files:
            return False

        # Check gitignore patterns
        if self.gitignore_spec:
            rel_path = get_relative_path(
                file_path, self._get_base_dir_for_path(file_path)
            )
            # Note: get_relative_path already returns forward slashes via as_posix()
            if self.gitignore_spec.match_file(rel_path):
                return False

        # Check dot files
        include_dots = self.config.filter.include_dot_paths
        if (
            hasattr(self, "_global_include_dot_paths")
            and self._global_include_dot_paths is not None
        ):
            include_dots = include_dots or self._global_include_dot_paths
        # File-specific override
        if "include_dot_paths" in file_settings:
            include_dots = file_settings["include_dot_paths"]

        if not explicitly_included and not include_dots:
            if is_hidden_path(file_path):
                return False

        # Check binary files
        include_binary = self.config.filter.include_binary_files
        if (
            hasattr(self, "_global_include_binary_files")
            and self._global_include_binary_files is not None
        ):
            include_binary = include_binary or self._global_include_binary_files
        # File-specific override
        if "include_binary_files" in file_settings:
            include_binary = file_settings["include_binary_files"]

        if not include_binary:
            if is_binary_file(file_path):
                return False

        # Check extensions
        # Combine config and global preset include extensions
        include_exts = set(self.config.filter.include_extensions)
        if self.global_settings and self.global_settings.include_extensions:
            include_exts.update(
                ext.lower() if ext.startswith(".") else f".{ext.lower()}"
                for ext in self.global_settings.include_extensions
            )

        if include_exts:
            if file_path.suffix.lower() not in include_exts:
                return False

        # Combine config and global preset exclude extensions
        exclude_exts = set(self.config.filter.exclude_extensions)
        if self.global_settings and self.global_settings.exclude_extensions:
            exclude_exts.update(
                ext.lower() if ext.startswith(".") else f".{ext.lower()}"
                for ext in self.global_settings.exclude_extensions
            )

        if exclude_exts:
            if file_path.suffix.lower() in exclude_exts:
                return False

        # Check symlinks
        if file_path.is_symlink():
            include_symlinks = self.config.filter.include_symlinks
            if (
                hasattr(self, "_global_include_symlinks")
                and self._global_include_symlinks is not None
            ):
                include_symlinks = include_symlinks or self._global_include_symlinks

            if not include_symlinks:
                self.logger.debug(
                    f"Excluding symlink {file_path} (include_symlinks=False)"
                )
                return False

            # For file symlinks, we only need to check for cycles if it's a directory symlink
            # File symlinks don't create cycles in the same way directory symlinks do
            try:
                if file_path.is_dir() and self._detect_symlink_cycle(file_path):
                    self.logger.debug(f"Excluding symlink {file_path} (cycle detected)")
                    return False
            except PermissionError:
                self.logger.warning(
                    f"Permission denied checking symlink '{file_path}'. Skipping."
                )
                return False

            self.logger.debug(f"Including symlink {file_path} (include_symlinks=True)")

        # Check file size limit
        max_size = self.config.filter.max_file_size
        if (
            hasattr(self, "_global_max_file_size")
            and self._global_max_file_size is not None
        ):
            # Use the smaller of the two limits if both are set
            if max_size is not None:
                max_size = min(max_size, self._global_max_file_size)
            else:
                max_size = self._global_max_file_size

        # File-specific override
        if "max_file_size" in file_settings:
            from .utils import parse_file_size

            try:
                file_max_size = parse_file_size(file_settings["max_file_size"])
                # If file-specific limit is set, use it (not the minimum)
                max_size = file_max_size
            except ValueError as e:
                self.logger.warning(
                    f"Invalid file-specific max_file_size for {file_path}: {e}"
                )

        if max_size is not None:
            try:
                file_size = file_path.stat().st_size
                if file_size > max_size:
                    self.logger.info(
                        f"Skipping {file_path.name} due to size limit: "
                        f"{format_file_size(file_size)} > {format_file_size(max_size)}"
                    )
                    return False
            except OSError as e:
                self.logger.warning(f"Could not check size of {file_path}: {e}")
                return False

        return True

    def _detect_symlink_cycle(self, path: Path) -> bool:
        """Detect if following a symlink would create a cycle."""
        try:
            current = path
            depth = 0
            visited = self._symlink_visited.copy()

            while current.is_symlink() and depth < MAX_SYMLINK_DEPTH:
                target = current.readlink()
                if not target.is_absolute():
                    target = current.parent / target
                target = target.resolve(strict=False)

                # Validate symlink target doesn't traverse outside allowed directories
                try:
                    from .utils import validate_path_traversal

                    validate_path_traversal(
                        target, allow_outside=self.config.filter.include_symlinks
                    )
                except ValueError as e:
                    self.logger.warning(
                        f"Symlink target validation failed for {current}: {e}"
                    )
                    return False

                target_str = str(target)
                if target_str in visited:
                    return True

                # Check if target is ancestor
                try:
                    if current.parent.resolve(strict=False).is_relative_to(target):
                        return True
                except (ValueError, AttributeError):
                    # Not an ancestor or method not available
                    pass

                if target.is_symlink():
                    visited.add(target_str)

                current = target
                depth += 1

            if depth >= MAX_SYMLINK_DEPTH:
                return True

            # Update global visited set
            self._symlink_visited.update(visited)
            return False

        except (OSError, RuntimeError):
            return True

    def _is_target_within_sources(self, target_path: Path) -> bool:
        """Check if a path is within any of the source directories.

        Args:
            target_path: The path to check (should be resolved)

        Returns:
            True if the path is within any source directory, False otherwise
        """
        try:
            target_resolved = target_path.resolve()

            # Check against all source directories
            for source_dir in self.config.source_directories:
                try:
                    source_resolved = source_dir.resolve()
                    # Check if target is relative to this source directory
                    target_resolved.relative_to(source_resolved)
                    return True
                except ValueError:
                    # Not relative to this source directory
                    continue

            # Also check against any explicitly included paths
            for include_path in self.config.filter.include_paths:
                try:
                    include_resolved = Path(include_path).resolve()
                    if include_resolved.is_dir():
                        target_resolved.relative_to(include_resolved)
                        return True
                    elif target_resolved == include_resolved:
                        return True
                except (ValueError, PermissionError):
                    continue

            return False

        except Exception as e:
            self.logger.debug(f"Error checking if {target_path} is within sources: {e}")
            return False

    def _apply_global_filter_settings(self) -> None:
        """Apply global filter settings from presets."""
        if not self.global_settings:
            return

        # Apply global filter settings to config-like attributes
        if self.global_settings.include_dot_paths is not None:
            self._global_include_dot_paths = self.global_settings.include_dot_paths
        else:
            self._global_include_dot_paths = None

        if self.global_settings.include_binary_files is not None:
            self._global_include_binary_files = (
                self.global_settings.include_binary_files
            )
        else:
            self._global_include_binary_files = None

        if self.global_settings.include_symlinks is not None:
            self._global_include_symlinks = self.global_settings.include_symlinks
        else:
            self._global_include_symlinks = None

        if self.global_settings.no_default_excludes is not None:
            self._global_no_default_excludes = self.global_settings.no_default_excludes
            # Rebuild exclusion sets if needed
            if (
                self._global_no_default_excludes
                and not self.config.filter.no_default_excludes
            ):
                self.excluded_dirs.clear()
                self.excluded_files.clear()

        if self.global_settings.max_file_size:
            from .utils import parse_file_size

            try:
                self._global_max_file_size = parse_file_size(
                    self.global_settings.max_file_size
                )
            except ValueError as e:
                self.logger.warning(f"Invalid global max_file_size: {e}")
                self._global_max_file_size = None
        else:
            self._global_max_file_size = None

        # Apply exclude_paths_file from global settings
        if (
            self.global_settings.exclude_paths_file
            and not self.config.filter.exclude_paths_file
        ):
            # Only apply if not already set in config (config takes precedence)
            self.config.filter.exclude_paths_file = (
                self.global_settings.exclude_paths_file
            )

        # Apply include_paths_file from global settings
        if (
            self.global_settings.include_paths_file
            and not self.config.filter.include_paths_file
        ):
            # Only apply if not already set in config (config takes precedence)
            self.config.filter.include_paths_file = (
                self.global_settings.include_paths_file
            )

    def _load_exclude_patterns_from_file(self, exclude_file: Path) -> None:
        """Load exclusion patterns from a file (helper method)."""
        try:
            with open(exclude_file, "r", encoding="utf-8") as f:
                lines = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.strip().startswith("#")
                ]
            # Explicitly ensure file handle is released
            f = None

            # Add to gitignore spec if patterns found
            patterns = [
                line
                for line in lines
                if any(ch in line for ch in ["*", "?", "!"]) or line.endswith("/")
            ]
            if patterns:
                spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)
                if self.gitignore_spec:
                    # Combine with existing spec
                    all_patterns = list(self.gitignore_spec.patterns) + list(
                        spec.patterns
                    )
                    self.gitignore_spec = pathspec.PathSpec(all_patterns)
                else:
                    self.gitignore_spec = spec

        except Exception as e:
            self.logger.error(
                f"Error loading exclude patterns from {exclude_file}: {e}"
            )
