#!/usr/bin/env python3
"""
Auto-bundle script for m1f - Python implementation
Handles both simple and advanced (YAML config) modes
"""

import os
import sys
import json
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


# Check if we should restart with venv Python
def check_venv():
    """Check if running in venv, restart with venv Python if not"""
    venv_path = Path(__file__).parent.parent / ".venv"

    # Check if venv exists
    if not venv_path.exists():
        return

    # Check if already running in venv
    if hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    ):
        return

    # Find venv Python executable
    if sys.platform == "win32":
        venv_python = venv_path / "Scripts" / "python.exe"
    else:
        venv_python = venv_path / "bin" / "python"

    if venv_python.exists():
        # Restart with venv Python
        import subprocess

        cmd = [str(venv_python)] + sys.argv
        sys.exit(subprocess.call(cmd))


# Check venv before proceeding
check_venv()

# Try to import YAML support
try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


# ANSI color codes
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


# Global verbose flag
_verbose = False


# Print functions
def print_header(msg: str):
    if _verbose:
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{msg:^60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")


def print_info(msg: str):
    if _verbose:
        print(f"{Colors.BLUE}[INFO]{Colors.ENDC} {msg}")


def print_success(msg: str):
    if _verbose:
        print(f"{Colors.GREEN}[SUCCESS]{Colors.ENDC} {msg}")


def print_warning(msg: str):
    # Warnings are always shown
    print(f"{Colors.YELLOW}[WARNING]{Colors.ENDC} {msg}")


def print_error(msg: str):
    # Errors are always shown
    print(f"{Colors.RED}[ERROR]{Colors.ENDC} {msg}")


class AutoBundler:
    def __init__(self, verbose=False):
        self.project_root = Path.cwd()
        self.m1f_dir = ".m1f"
        self.config_file = self.project_root / ".m1f.config.yml"
        self.m1f_tool = self.project_root / "tools" / "m1f.py"
        self.verbose = verbose

        # Simple mode bundles
        self.simple_bundles = {
            "docs": "Documentation files",
            "src": "Source code files",
            "tests": "Test files",
            "complete": "Complete project",
        }

    def check_prerequisites(self) -> bool:
        """Check if m1f tool exists"""
        if not self.m1f_tool.exists():
            print_error(f"m1f tool not found at: {self.m1f_tool}")
            return False
        return True

    def setup_directories_from_config(self, config: Dict[str, Any]):
        """Create directories based on output paths in config"""
        bundles = config.get("bundles", {})
        created_dirs = set()

        for bundle_name, bundle_config in bundles.items():
            output = bundle_config.get("output", "")
            if output:
                # Get the directory part of the output path
                output_path = self.project_root / output
                output_dir = output_path.parent

                # Create directory if not already created
                if str(output_dir) not in created_dirs:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    created_dirs.add(str(output_dir))
                    print_info(f"Created directory: {output_dir}")

    def setup_directories_simple(self):
        """Create .m1f directory structure for simple mode"""
        directories = ["docs", "src", "tests", "complete"]

        for dir_name in directories:
            dir_path = self.project_root / self.m1f_dir / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)

    def run_m1f_command(self, cmd_parts: List[str]) -> bool:
        """Execute m1f command"""
        cmd = " ".join(cmd_parts)
        print_info(f"Executing: {cmd}")

        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print_error(f"Command failed: {result.stderr}")
                return False
            if self.verbose and result.stdout:
                print(result.stdout)
            return True
        except Exception as e:
            print_error(f"Failed to execute command: {e}")
            return False

    def build_m1f_command(
        self, bundle_config: Dict[str, Any], bundle_name: str, config: Dict[str, Any]
    ) -> List[str]:
        """Build m1f command from bundle configuration"""
        cmd_parts = ["python", f'"{self.m1f_tool}"']

        # Handle bundle-level include_files
        if "include_files" in bundle_config:
            for file in bundle_config["include_files"]:
                # Add .py extension if missing
                if not os.path.splitext(file)[1]:
                    test_path = self.project_root / file
                    if not test_path.exists():
                        file += ".py"
                cmd_parts.extend(["-s", f'"{self.project_root / file}"'])

        # Process sources
        sources = bundle_config.get("sources", [])
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
                        if not test_path.exists():
                            file += ".py"

                    # Create full path
                    if path != ".":
                        full_path = os.path.join(path, file)
                    else:
                        full_path = file
                    cmd_parts.extend(["-s", f'"{self.project_root / full_path}"'])
            else:
                # Normal path processing
                cmd_parts.extend(["-s", f'"{self.project_root / path}"'])

                # Include extensions
                if "include_extensions" in source:
                    cmd_parts.append("--include-extensions")
                    cmd_parts.extend(source["include_extensions"])

            # Excludes from source
            if "excludes" in source:
                cmd_parts.append("--excludes")
                for exclude in source["excludes"]:
                    cmd_parts.append(f'"{exclude}"')

        # Add global excludes if they exist
        global_excludes = config.get("global", {}).get("global_excludes", [])
        if global_excludes and "--excludes" not in cmd_parts:
            cmd_parts.append("--excludes")
        for exclude in global_excludes:
            cmd_parts.append(f'"{exclude}"')

        # Output file
        output = bundle_config.get("output", "")
        if output:
            cmd_parts.extend(["-o", f'"{self.project_root / output}"'])

        # Separator style
        sep_style = bundle_config.get("separator_style", "Standard")
        cmd_parts.extend(["--separator-style", sep_style])

        # Preset
        if "preset" in bundle_config:
            cmd_parts.extend(
                ["--preset", f'"{self.project_root / bundle_config["preset"]}"']
            )

        # Preset group
        if "preset_group" in bundle_config:
            cmd_parts.extend(["--preset-group", bundle_config["preset_group"]])

        # Exclude paths file(s)
        if "exclude_paths_file" in bundle_config:
            exclude_files = bundle_config["exclude_paths_file"]
            if isinstance(exclude_files, str):
                exclude_files = [exclude_files]
            if exclude_files:
                cmd_parts.append("--exclude-paths-file")
                for file in exclude_files:
                    cmd_parts.append(f'"{self.project_root / file}"')

        # Include paths file(s)
        if "include_paths_file" in bundle_config:
            include_files = bundle_config["include_paths_file"]
            if isinstance(include_files, str):
                include_files = [include_files]
            if include_files:
                cmd_parts.append("--include-paths-file")
                for file in include_files:
                    cmd_parts.append(f'"{self.project_root / file}"')

        # Other options
        if bundle_config.get("filename_mtime_hash"):
            cmd_parts.append("--filename-mtime-hash")

        if bundle_config.get("minimal_output", True):
            cmd_parts.append("--minimal-output")

        # Note: m1f uses gitignore by default, there's no --use-gitignore flag

        # Always add --quiet and -f
        cmd_parts.append("--quiet")
        cmd_parts.append("-f")

        return cmd_parts

    def create_bundle_advanced(
        self, bundle_name: str, bundle_config: Dict[str, Any], config: Dict[str, Any]
    ) -> bool:
        """Create bundle in advanced mode"""
        # Check if enabled
        if not bundle_config.get("enabled", True):
            print_info(f"Skipping disabled bundle: {bundle_name}")
            return True

        # Check conditional enabling
        enabled_if = bundle_config.get("enabled_if_exists", "")
        if enabled_if and not (self.project_root / enabled_if).exists():
            print_info(
                f"Skipping bundle {bundle_name} (condition not met: {enabled_if})"
            )
            return True

        description = bundle_config.get("description", "")
        print_info(f"Creating bundle: {bundle_name} - {description}")

        # Build and execute command
        cmd_parts = self.build_m1f_command(bundle_config, bundle_name, config)

        if self.run_m1f_command(cmd_parts):
            print_success(f"Created: {bundle_name}")
            return True
        else:
            print_error(f"Failed to create bundle: {bundle_name}")
            return False

    def create_bundle_simple(self, bundle_type: str) -> bool:
        """Create bundle in simple mode"""
        if bundle_type == "docs":
            return self.create_docs_bundle()
        elif bundle_type == "src":
            return self.create_src_bundle()
        elif bundle_type == "tests":
            return self.create_tests_bundle()
        elif bundle_type == "complete":
            return self.create_complete_bundle()
        else:
            print_error(f"Unknown bundle type: {bundle_type}")
            return False

    def create_docs_bundle(self) -> bool:
        """Create documentation bundle"""
        output_file = self.project_root / self.m1f_dir / "docs" / "manual.m1f.txt"
        cmd_parts = [
            "python",
            f'"{self.m1f_tool}"',
            "-s",
            f'"{self.project_root}"',
            "-o",
            f'"{output_file}"',
            "--include-extensions",
            ".md",
            ".txt",
            ".rst",
            "--excludes",
            '"tests/**"',
            '"test_*"',
            "--minimal-output",
            "--quiet",
            "-f",
        ]

        if self.run_m1f_command(cmd_parts):
            print_success(f"Documentation bundle created: {output_file}")
            return True
        return False

    def create_src_bundle(self) -> bool:
        """Create source code bundle"""
        output_file = self.project_root / self.m1f_dir / "src" / "source.m1f.txt"
        cmd_parts = [
            "python",
            f'"{self.m1f_tool}"',
            "-s",
            f'"{self.project_root}"',
            "-o",
            f'"{output_file}"',
            "--include-extensions",
            ".py",
            "--excludes",
            '"tests/**"',
            '"test_*.py"',
            '"*_test.py"',
            "--minimal-output",
            "--quiet",
            "-f",
        ]

        if self.run_m1f_command(cmd_parts):
            print_success(f"Source bundle created: {output_file}")
            return True
        return False

    def create_tests_bundle(self) -> bool:
        """Create tests bundle"""
        output_file = self.project_root / self.m1f_dir / "tests" / "tests.m1f.txt"
        test_dir = self.project_root / "tests"

        if not test_dir.exists():
            print_warning("No tests directory found")
            return True

        cmd_parts = [
            "python",
            f'"{self.m1f_tool}"',
            "-s",
            f'"{test_dir}"',
            "-o",
            f'"{output_file}"',
            "--include-extensions",
            ".py",
            "--excludes",
            '"*/source/**"',
            '"*/output/**"',
            '"*/expected/**"',
            "--minimal-output",
            "--quiet",
            "-f",
        ]

        if self.run_m1f_command(cmd_parts):
            print_success(f"Tests bundle created: {output_file}")
            return True
        return False

    def create_complete_bundle(self) -> bool:
        """Create complete project bundle"""
        output_file = self.project_root / self.m1f_dir / "complete" / "project.m1f.txt"
        cmd_parts = [
            "python",
            f'"{self.m1f_tool}"',
            "-s",
            f'"{self.project_root}"',
            "-o",
            f'"{output_file}"',
            "--excludes",
            '"tests/*/source/**"',
            '"tests/*/output/**"',
            '"tests/*/expected/**"',
            '"**/.git/**"',
            '"**/node_modules/**"',
            '"**/__pycache__/**"',
            '"**/*.pyc"',
            '"**/.venv/**"',
            '"**/htmlcov/**"',
            "--minimal-output",
            "--quiet",
            "-f",
        ]

        if self.run_m1f_command(cmd_parts):
            print_success(f"Complete project bundle created: {output_file}")
            return True
        return False

    def load_config(self) -> Optional[Dict[str, Any]]:
        """Load YAML configuration"""
        if not self.config_file.exists():
            return None

        if not YAML_AVAILABLE:
            print_warning("PyYAML not installed. Running in simple mode.")
            return None

        try:
            with open(self.config_file, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            print_error(f"Failed to load config: {e}")
            return None

    def run_advanced_mode(
        self, config: Dict[str, Any], bundle_filter: Optional[str] = None
    ):
        """Run in advanced mode with YAML config"""
        print_header("M1F Auto-Bundle (Advanced Mode)")
        print_info(f"Using config: {self.config_file}")

        bundles = config.get("bundles", {})

        if bundle_filter:
            if bundle_filter in bundles:
                self.create_bundle_advanced(
                    bundle_filter, bundles[bundle_filter], config
                )
            else:
                print_error(f"Bundle '{bundle_filter}' not found in config")
        else:
            # Create all bundles
            for bundle_name, bundle_config in bundles.items():
                self.create_bundle_advanced(bundle_name, bundle_config, config)

    def run_simple_mode(self, bundle_filter: Optional[str] = None):
        """Run in simple mode without config"""
        print_header("M1F Auto-Bundle (Simple Mode)")

        if bundle_filter:
            if bundle_filter in self.simple_bundles:
                self.create_bundle_simple(bundle_filter)
            else:
                print_error(f"Unknown bundle type: {bundle_filter}")
        else:
            # Create all bundles
            for bundle_type in self.simple_bundles:
                self.create_bundle_simple(bundle_type)

    def list_presets(self):
        """List available presets with their groups"""
        presets_dir = self.project_root / "presets"

        print_header("Available Presets")

        if not presets_dir.exists():
            print_warning("No presets directory found")
            return

        for preset_file in sorted(presets_dir.glob("*.m1f-presets.yml")):
            name = preset_file.stem.replace(".m1f-presets", "")
            print(f"\n{Colors.BOLD}Preset: {name}{Colors.ENDC}")

            # Try to load and show groups
            if YAML_AVAILABLE:
                try:
                    with open(preset_file, "r") as f:
                        data = yaml.safe_load(f)

                    # Show description if available
                    if "description" in data:
                        print(f"  Description: {data['description']}")

                    # Show groups
                    groups = [
                        k for k in data.keys() if k not in ["globals", "description"]
                    ]
                    if groups:
                        print(f"  Groups: {', '.join(groups)}")

                    # Show per-file settings if available
                    if "globals" in data and "per_file_settings" in data["globals"]:
                        settings = list(data["globals"]["per_file_settings"].keys())
                        if settings:
                            print(
                                f"  Per-file settings: {', '.join(settings[:3])}"
                                + (" ..." if len(settings) > 3 else "")
                            )
                except Exception as e:
                    print(f"  (Could not parse preset: {e})")

    def create_focused_bundles(self, focus: str):
        """Create area-specific bundles"""
        print_info(f"Creating focused bundles for: {focus}")

        focus_configs = {
            "wordpress": [
                ("wordpress.m1f-presets.yml", "theme", "wp_theme"),
                ("wordpress.m1f-presets.yml", "plugin", "wp_plugin"),
            ],
            "web": [
                ("web-project.m1f-presets.yml", "frontend", "web_frontend"),
                ("web-project.m1f-presets.yml", "backend", "web_backend"),
            ],
            "docs": [
                ("documentation.m1f-presets.yml", None, "all_docs"),
            ],
        }

        if focus not in focus_configs:
            print_error(f"Unknown focus area: {focus}")
            print("Available: wordpress, web, docs")
            return False

        success = True
        for preset_file, group, output_name in focus_configs[focus]:
            preset_path = self.project_root / "presets" / preset_file

            if not preset_path.exists():
                print_warning(f"Preset not found: {preset_file}")
                continue

            # Create bundle config
            bundle_config = {
                "description": f"{focus} bundle",
                "output": f".m1f/m1f/{output_name}.txt",
                "sources": [{"path": "."}],
                "preset": f"presets/{preset_file}",
            }

            if group:
                bundle_config["preset_group"] = group

            # Use a dummy config with empty globals
            dummy_config = {"global": {}}

            if not self.create_bundle_advanced(
                output_name, bundle_config, dummy_config
            ):
                success = False

        return success

    def show_usage(self, mode: str):
        """Show usage information"""
        print("Usage: auto_bundle.py [command] [options]")
        print()
        print("Commands:")
        print("  (default)           Create bundles based on mode (config or simple)")
        print("  focus <area>        Create focused bundles for specific area")
        print("                      Areas: wordpress, web, docs")
        print("  list-presets        Show available presets and their groups")
        print()

        if mode == "advanced":
            print("Running in ADVANCED mode (using .m1f.config.yml)")
            print()
            print("Available bundles from config:")
            config = self.load_config()
            if config:
                bundles = config.get("bundles", {})
                for name, bundle in bundles.items():
                    desc = bundle.get("description", "No description")
                    print(f"  - {name}: {desc}")
        else:
            print("Running in SIMPLE mode (no config file found)")
            print()
            print("Bundle types:")
            for bundle_type, desc in self.simple_bundles.items():
                print(f"  - {bundle_type}: {desc}")

        print()
        print("Options:")
        print("  -h, --help     Show this help message")
        print("  -v, --verbose  Show verbose output")
        print("  --simple       Force simple mode (ignore config file)")
        print("  --show-stats   Show bundle statistics after creation")

    def show_statistics(self):
        """Show bundle statistics"""
        print_info("Bundle Statistics:")
        print("-" * 40)

        for bundle_type in ["docs", "src", "tests", "complete", "tools", "m1f"]:
            bundle_dir = self.project_root / self.m1f_dir / bundle_type
            if bundle_dir.exists():
                files = list(bundle_dir.glob("*.txt")) + list(
                    bundle_dir.glob("*.m1f.txt")
                )
                if files:
                    total_size = sum(f.stat().st_size for f in files)
                    size_mb = total_size / (1024 * 1024)
                    print(f"{bundle_type}: {len(files)} files, {size_mb:.2f} MB")

        print("-" * 40)


def main():
    parser = argparse.ArgumentParser(
        description="M1F Auto-Bundle Tool", usage="%(prog)s [command] [options]"
    )

    # Positional arguments
    parser.add_argument(
        "command",
        nargs="?",
        default="bundle",
        help="Command to run: bundle (default), focus, list-presets",
    )
    parser.add_argument("args", nargs="*", help="Command arguments")

    # Options
    parser.add_argument("--simple", action="store_true", help="Force simple mode")
    parser.add_argument(
        "--show-stats", action="store_true", help="Show statistics after bundling"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show verbose output"
    )

    args = parser.parse_args()

    # Set global verbose flag
    global _verbose
    _verbose = args.verbose

    bundler = AutoBundler(verbose=args.verbose)

    # Check prerequisites
    if not bundler.check_prerequisites():
        return 1

    # Handle commands
    if args.command == "list-presets":
        bundler.list_presets()
        return 0

    elif args.command == "focus":
        if not args.args:
            print_error("Focus area required")
            print("Available: wordpress, web, docs")
            return 1

        # Setup directories
        bundler.setup_directories_from_config({"bundles": {}})

        # Create focused bundles
        if bundler.create_focused_bundles(args.args[0]):
            if args.show_stats:
                bundler.show_statistics()
            return 0
        else:
            return 1

    elif args.command in ["bundle", None]:
        # Default bundle command
        bundle_name = args.args[0] if args.args else None

        # Determine mode
        config = None
        if not args.simple:
            config = bundler.load_config()

        # Setup directories based on mode
        if config:
            bundler.setup_directories_from_config(config)
        else:
            bundler.setup_directories_simple()

        # Run bundling
        start_time = datetime.now()

        if config:
            bundler.run_advanced_mode(config, bundle_name)
        else:
            bundler.run_simple_mode(bundle_name)

    else:
        # Check if command is a bundle name (backward compatibility)
        config = bundler.load_config()
        if config and args.command in config.get("bundles", {}):
            # Setup and run as bundle
            bundler.setup_directories_from_config(config)
            start_time = datetime.now()
            bundler.run_advanced_mode(config, args.command)
        else:
            print_error(f"Unknown command: {args.command}")
            bundler.show_usage("advanced" if config else "simple")
            return 1

    # Show statistics if requested
    if args.show_stats:
        bundler.show_statistics()

    # Show completion time
    elapsed = (datetime.now() - start_time).total_seconds()
    if _verbose:
        print()
        print_success(f"Auto-bundling completed in {elapsed:.2f} seconds")

    return 0


if __name__ == "__main__":
    sys.exit(main())
