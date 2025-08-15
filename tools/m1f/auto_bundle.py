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
Auto-bundle functionality for m1f.
Handles YAML configuration loading and bundle creation.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import logging
import yaml
import os
import subprocess
import sys

from .config import Config, OutputConfig, FilterConfig, SeparatorStyle, LineEnding
from .file_operations import (
    safe_exists,
    safe_open,
)

# Use unified colorama module
from shared.colors import Colors, info, success, error, warning

logger = logging.getLogger(__name__)


class AutoBundleConfig:
    """Configuration for auto-bundle functionality."""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config_data: Dict[str, Any] = {}
        self.bundles: Dict[str, Dict[str, Any]] = {}
        self.global_config: Dict[str, Any] = {}

    def load(self) -> bool:
        """Load configuration from YAML file."""
        if not safe_exists(self.config_path):
            return False

        try:
            with safe_open(self.config_path, "r", encoding="utf-8") as f:
                self.config_data = yaml.safe_load(f) or {}

            self.bundles = self.config_data.get("bundles", {})
            self.global_config = self.config_data.get("global", {})
            return True

        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            return False

    def get_bundle_names(self) -> List[str]:
        """Get list of available bundle names."""
        return list(self.bundles.keys())

    def get_bundle_config(self, bundle_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific bundle."""
        return self.bundles.get(bundle_name)


class AutoBundler:
    """Handles auto-bundling functionality."""

    def __init__(self, project_root: Path, verbose: bool = False, quiet: bool = False):
        self.project_root = project_root
        self.verbose = verbose
        self.quiet = quiet
        self.config_file = self._find_config_file(project_root)
        self.m1f_dir = project_root / "m1f"

    def _find_config_file(self, start_path: Path) -> Path:
        """Find .m1f.config.yml by searching from current directory up to root."""
        current = start_path.resolve()

        while True:
            config_path = current / ".m1f.config.yml"
            if safe_exists(config_path):
                if self.verbose:
                    self.print_info(f"Found config at: {config_path}")
                return config_path

            # Check if we've reached the root
            parent = current.parent
            if parent == current:
                # Return the original path's config file location (even if it doesn't exist)
                return start_path / ".m1f.config.yml"
            current = parent

    def check_config_exists(self) -> bool:
        """Check if auto-bundle config exists."""
        return safe_exists(self.config_file)

    def load_config(self) -> Optional[AutoBundleConfig]:
        """Load auto-bundle configuration."""
        config = AutoBundleConfig(self.config_file)
        if config.load():
            return config
        return None

    def print_info(self, msg: str):
        """Print info message."""
        if not self.quiet:
            if self.verbose:
                info(msg)
            else:
                info(msg)

    def print_success(self, msg: str):
        """Print success message."""
        if not self.quiet:
            success(msg)

    def print_error(self, msg: str):
        """Print error message."""
        error(msg)

    def print_warning(self, msg: str):
        """Print warning message."""
        if not self.quiet:
            warning(msg)

    def setup_directories(self, config: AutoBundleConfig):
        """Create necessary directories based on config."""
        created_dirs = set()

        for bundle_name, bundle_config in config.bundles.items():
            output = bundle_config.get("output", "")
            if output:
                from .utils import validate_path_traversal

                output_path = self.project_root / output
                # Validate output path doesn't use malicious traversal
                try:
                    output_path = validate_path_traversal(
                        output_path, base_path=self.project_root, allow_outside=True
                    )
                except ValueError as e:
                    self.print_error(
                        f"Invalid output path for bundle '{bundle_name}': {e}"
                    )
                    continue
                output_dir = output_path.parent

                if str(output_dir) not in created_dirs:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    created_dirs.add(str(output_dir))
                    if self.verbose:
                        self.print_info(f"Created directory: {output_dir}")

    def build_m1f_command(
        self,
        bundle_name: str,
        bundle_config: Dict[str, Any],
        global_config: Dict[str, Any],
    ) -> List[str]:
        """Build m1f command from bundle configuration."""
        cmd_parts = [sys.executable, "-m", "tools.m1f"]

        # Handle bundle-level include_files
        if "include_files" in bundle_config:
            for file in bundle_config["include_files"]:
                # Add .py extension if missing
                if not os.path.splitext(file)[1]:
                    test_path = self.project_root / file
                    if not safe_exists(test_path):
                        file += ".py"
                cmd_parts.extend(["-s", str(self.project_root / file)])

        # Process sources
        sources = bundle_config.get("sources", [])
        all_excludes = []  # Collect all excludes

        for source in sources:
            path = source.get("path", ".")

            # Handle include_files at source level
            if "include_files" in source:
                for file in source["include_files"]:
                    # Add .py extension if missing
                    if not os.path.splitext(file)[1]:
                        if path != ".":
                            test_path = self.project_root / path / file
                        else:
                            test_path = self.project_root / file
                        if not safe_exists(test_path):
                            file += ".py"

                    # Create full path
                    if path != ".":
                        full_path = os.path.join(path, file)
                    else:
                        full_path = file
                    cmd_parts.extend(["-s", str(self.project_root / full_path)])
            else:
                # Normal path processing
                cmd_parts.extend(["-s", str(self.project_root / path)])

                # Include extensions
                if "include_extensions" in source:
                    cmd_parts.append("--include-extensions")
                    cmd_parts.extend(source["include_extensions"])

            # Handle includes at source level
            if "includes" in source:
                # Add includes patterns
                cmd_parts.append("--includes")
                cmd_parts.extend(source["includes"])

            # Collect excludes from source
            if "excludes" in source:
                all_excludes.extend(source["excludes"])

        # Add global excludes
        global_excludes = global_config.get("global_excludes", [])
        if global_excludes:
            all_excludes.extend(global_excludes)

        # Add all excludes with a single --excludes flag
        if all_excludes:
            cmd_parts.append("--excludes")
            cmd_parts.extend(all_excludes)

        # Output file
        output = bundle_config.get("output", "")
        if output:
            from .utils import validate_path_traversal

            try:
                output_path = validate_path_traversal(
                    self.project_root / output,
                    base_path=self.project_root,
                    allow_outside=True,
                )
                cmd_parts.extend(["-o", str(output_path)])
            except ValueError as e:
                self.print_error(f"Invalid output path: {e}")
                return []

        # Separator style
        sep_style = bundle_config.get("separator_style", "Standard")
        cmd_parts.extend(["--separator-style", sep_style])

        # Preset
        if "preset" in bundle_config:
            from .utils import validate_path_traversal

            try:
                preset_path = validate_path_traversal(
                    self.project_root / bundle_config["preset"],
                    base_path=self.project_root,
                    from_preset=True,
                )
                cmd_parts.extend(["--preset", str(preset_path)])
            except ValueError as e:
                self.print_error(f"Invalid preset path: {e}")
                return []

        # Preset group
        if "preset_group" in bundle_config:
            cmd_parts.extend(["--preset-group", bundle_config["preset_group"]])

        # Exclude paths file(s) - check bundle config first, then global settings
        exclude_files = None
        if "exclude_paths_file" in bundle_config:
            exclude_files = bundle_config["exclude_paths_file"]
        elif (
            "global_settings" in global_config
            and "exclude_paths_file" in global_config["global_settings"]
        ):
            exclude_files = global_config["global_settings"]["exclude_paths_file"]

        if exclude_files:
            if isinstance(exclude_files, str):
                exclude_files = [exclude_files]
            cmd_parts.append("--exclude-paths-file")
            for file in exclude_files:
                cmd_parts.append(str(self.project_root / file))

        # Include paths file(s) - check bundle config first, then global settings
        include_files = None
        if "include_paths_file" in bundle_config:
            include_files = bundle_config["include_paths_file"]
        elif (
            "global_settings" in global_config
            and "include_paths_file" in global_config["global_settings"]
        ):
            include_files = global_config["global_settings"]["include_paths_file"]

        if include_files:
            if isinstance(include_files, str):
                include_files = [include_files]
            cmd_parts.append("--include-paths-file")
            for file in include_files:
                cmd_parts.append(str(self.project_root / file))

        # Other options
        if bundle_config.get("filename_mtime_hash"):
            cmd_parts.append("--filename-mtime-hash")

        if bundle_config.get("docs_only"):
            cmd_parts.append("--docs-only")

        if bundle_config.get("minimal_output", True):
            cmd_parts.append("--minimal-output")

        # Always add --quiet and -f
        cmd_parts.append("--quiet")
        cmd_parts.append("-f")

        return cmd_parts

    def create_bundle(
        self,
        bundle_name: str,
        bundle_config: Dict[str, Any],
        global_config: Dict[str, Any],
    ) -> bool:
        """Create a single bundle."""
        # Check if enabled
        if not bundle_config.get("enabled", True):
            self.print_info(f"Skipping disabled bundle: {bundle_name}")
            return True

        # Check conditional enabling
        enabled_if = bundle_config.get("enabled_if_exists", "")
        if enabled_if and not safe_exists(self.project_root / enabled_if):
            self.print_info(
                f"Skipping bundle {bundle_name} (condition not met: {enabled_if})"
            )
            return True

        description = bundle_config.get("description", "")
        self.print_info(f"Creating bundle: {bundle_name} - {description}")

        # Build and execute command
        cmd_parts = self.build_m1f_command(bundle_name, bundle_config, global_config)

        if self.verbose:
            self.print_info(f"Executing: {' '.join(cmd_parts)}")

        try:
            result = subprocess.run(cmd_parts, capture_output=True, text=True)
            if result.returncode != 0:
                self.print_error(f"Command failed: {result.stderr}")
                return False
            if self.verbose and result.stdout:
                info(result.stdout)
            self.print_success(f"Created: {bundle_name}")
            return True
        except Exception as e:
            self.print_error(f"Failed to execute command: {e}")
            return False

    def list_bundles(self, config: AutoBundleConfig):
        """List available bundles."""
        if not config.bundles:
            self.print_warning("No bundles defined in configuration")
            return

        # Group bundles by their group
        grouped_bundles = {}
        ungrouped_bundles = {}

        for bundle_name, bundle_config in config.bundles.items():
            group = bundle_config.get("group", None)
            if group:
                if group not in grouped_bundles:
                    grouped_bundles[group] = {}
                grouped_bundles[group][bundle_name] = bundle_config
            else:
                ungrouped_bundles[bundle_name] = bundle_config

        info("\nAvailable bundles:")
        info("-" * 60)

        # Show grouped bundles first
        for group_name in sorted(grouped_bundles.keys()):
            info(f"\nGroup: {group_name}")
            info("=" * 40)
            for bundle_name, bundle_config in grouped_bundles[group_name].items():
                self._print_bundle_info(bundle_name, bundle_config)

        # Show ungrouped bundles
        if ungrouped_bundles:
            if grouped_bundles:
                info("\nUngrouped bundles:")
                info("=" * 40)
            for bundle_name, bundle_config in ungrouped_bundles.items():
                self._print_bundle_info(bundle_name, bundle_config)

        info("-" * 60)

        # Show available groups
        if grouped_bundles:
            info("\nAvailable groups:")
            for group in sorted(grouped_bundles.keys()):
                count = len(grouped_bundles[group])
                info(f"  - {group} ({count} bundles)")

    def _print_bundle_info(self, bundle_name: str, bundle_config: Dict[str, Any]):
        """Print information about a single bundle."""
        enabled = bundle_config.get("enabled", True)
        description = bundle_config.get("description", "No description")
        output = bundle_config.get("output", "No output specified")

        status = "enabled" if enabled else "disabled"
        info(f"\n  {bundle_name} ({status})")
        info(f"    Description: {description}")
        info(f"    Output: {output}")

        # Show conditional enabling
        if "enabled_if_exists" in bundle_config:
            info(f"    Enabled if exists: {bundle_config['enabled_if_exists']}")

    def run(
        self,
        bundle_name: Optional[str] = None,
        list_bundles: bool = False,
        bundle_group: Optional[str] = None,
    ):
        """Run auto-bundle functionality."""
        # Check if config exists
        if not self.check_config_exists():
            self.print_error("No .m1f.config.yml configuration found!")
            self.print_info(
                "Searched from current directory up to root. No config file was found."
            )
            self.print_info(
                "Create a .m1f.config.yml file in your project root to use auto-bundle functionality."
            )
            self.print_info("See documentation: docs/01_m1f/06_auto_bundle_guide.md")
            return False

        # Load config
        config = self.load_config()
        if not config:
            self.print_error("Failed to load auto-bundle configuration")
            return False

        # List bundles if requested
        if list_bundles:
            self.list_bundles(config)
            return True

        # Setup directories
        self.setup_directories(config)

        # Filter bundles by group if specified
        bundles_to_create = {}

        if bundle_group:
            # Filter bundles by group
            for name, bundle_config in config.bundles.items():
                if bundle_config.get("group") == bundle_group:
                    bundles_to_create[name] = bundle_config

            if not bundles_to_create:
                self.print_error(f"No bundles found in group '{bundle_group}'")
                available_groups = set()
                for bundle_config in config.bundles.values():
                    if "group" in bundle_config:
                        available_groups.add(bundle_config["group"])
                if available_groups:
                    self.print_info(
                        f"Available groups: {', '.join(sorted(available_groups))}"
                    )
                else:
                    self.print_info("No bundle groups defined in configuration")
                return False
        elif bundle_name:
            # Create specific bundle
            bundle_config = config.get_bundle_config(bundle_name)
            if not bundle_config:
                self.print_error(f"Bundle '{bundle_name}' not found in configuration")
                self.print_info(
                    f"Available bundles: {', '.join(config.get_bundle_names())}"
                )
                return False
            bundles_to_create[bundle_name] = bundle_config
        else:
            # Create all bundles
            bundles_to_create = config.bundles

        # Create the selected bundles
        success = True
        for name, bundle_config in bundles_to_create.items():
            if not self.create_bundle(name, bundle_config, config.global_config):
                success = False
        return success
