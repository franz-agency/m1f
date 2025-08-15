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
Shared CLI utilities for all m1f tools.

This module provides common argument parsing components to ensure
consistency across all tools and avoid code duplication.
"""

import argparse
import sys
from typing import Optional, NoReturn, Dict, Any, List
from pathlib import Path

from .colors import Colors, ColoredHelpFormatter, COLORAMA_AVAILABLE


class CustomArgumentParser(argparse.ArgumentParser):
    """Custom argument parser with better error messages.

    This class is used by all m1f tools for consistent error handling
    and formatting.
    """

    def error(self, message: str) -> NoReturn:
        """Display error message with colors if available."""
        error_msg = f"ERROR: {message}"

        if COLORAMA_AVAILABLE:
            error_msg = f"{Colors.RED}ERROR: {message}{Colors.RESET}"

        self.print_usage(sys.stderr)
        print(f"\n{error_msg}", file=sys.stderr)
        print(f"\nFor detailed help, use: {self.prog} --help", file=sys.stderr)
        self.exit(2)


class ArgumentBuilder:
    """Builder for common argument patterns used across m1f tools."""

    @staticmethod
    def add_version_argument(parser: argparse.ArgumentParser, version: str) -> None:
        """Add standard --version argument."""
        parser.add_argument(
            "--version",
            action="version",
            version=f"%(prog)s {version}",
            help="Show program version and exit",
        )

    @staticmethod
    def add_verbose_quiet_arguments(
        parser: argparse.ArgumentParser, group_name: str = "Output Control"
    ) -> argparse._ArgumentGroup:
        """Add standard verbose/quiet output control arguments.

        Returns the argument group for additional customization.
        """
        output_group = parser.add_argument_group(group_name)
        output_group.add_argument(
            "-v", "--verbose", action="store_true", help="Enable verbose output"
        )
        output_group.add_argument(
            "-q",
            "--quiet",
            action="store_true",
            help="Suppress all output except errors",
        )
        return output_group

    @staticmethod
    def add_output_arguments(
        parser: argparse.ArgumentParser,
        required: bool = False,
        default: Optional[Path] = None,
    ) -> argparse._ArgumentGroup:
        """Add standard output file/directory arguments."""
        output_group = parser.add_argument_group("Output Options")
        output_group.add_argument(
            "-o",
            "--output",
            type=Path,
            required=required,
            default=default,
            help="Output file or directory",
        )
        return output_group

    @staticmethod
    def add_force_argument(parser: argparse.ArgumentParser) -> None:
        """Add standard --force argument for overwriting."""
        parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            help="Overwrite existing files without prompting",
        )

    @staticmethod
    def add_config_argument(parser: argparse.ArgumentParser) -> None:
        """Add standard --config argument."""
        parser.add_argument("-c", "--config", type=Path, help="Configuration file path")

    @staticmethod
    def add_parallel_argument(
        parser: argparse.ArgumentParser, default: int = 5
    ) -> None:
        """Add standard parallel processing argument."""
        parser.add_argument(
            "--parallel",
            type=int,
            default=default,
            metavar="N",
            help=f"Number of parallel workers (default: {default})",
        )

    @staticmethod
    def add_dry_run_argument(parser: argparse.ArgumentParser) -> None:
        """Add standard --dry-run argument."""
        parser.add_argument(
            "--dry-run", action="store_true", help="Preview changes without executing"
        )

    @staticmethod
    def add_format_argument(
        parser: argparse.ArgumentParser, choices: List[str], default: str
    ) -> None:
        """Add standard --format argument."""
        parser.add_argument(
            "--format",
            choices=choices,
            default=default,
            help=f"Output format (default: {default})",
        )

    @staticmethod
    def add_log_file_argument(
        parser: argparse.ArgumentParser, group: Optional[argparse._ArgumentGroup] = None
    ) -> None:
        """Add standard --log-file argument."""
        target = group if group else parser
        target.add_argument("--log-file", type=Path, help="Write logs to file")


class BaseCLI:
    """Base class for m1f tool CLIs with common functionality."""

    def __init__(self, prog: str, version: str, description: str, epilog: str = ""):
        """Initialize base CLI.

        Args:
            prog: Program name
            version: Version string
            description: Program description for help
            epilog: Additional help text shown at the end
        """
        self.prog = prog
        self.version = version
        self.description = description
        self.epilog = epilog
        self.parser: Optional[CustomArgumentParser] = None

    def create_parser(self) -> CustomArgumentParser:
        """Create and configure the base argument parser.

        Subclasses should override this to add their specific arguments.
        """
        self.parser = CustomArgumentParser(
            prog=self.prog,
            description=self.description,
            epilog=self.epilog,
            formatter_class=ColoredHelpFormatter,
            add_help=True,
        )

        # Add standard version argument
        ArgumentBuilder.add_version_argument(self.parser, self.version)

        return self.parser

    def add_common_arguments(self) -> None:
        """Add common arguments used by most tools.

        This adds verbose/quiet and can be extended by subclasses.
        """
        if not self.parser:
            raise RuntimeError("Parser not created. Call create_parser() first.")

        # Add verbose/quiet arguments
        ArgumentBuilder.add_verbose_quiet_arguments(self.parser)

    def parse_args(self, argv: Optional[List[str]] = None) -> argparse.Namespace:
        """Parse command-line arguments."""
        if not self.parser:
            self.create_parser()
        return self.parser.parse_args(argv)

    def validate_args(self, args: argparse.Namespace) -> None:
        """Validate parsed arguments.

        Subclasses should override this to add specific validation.

        Args:
            args: Parsed arguments

        Raises:
            ValueError: If arguments are invalid
        """
        # Check for conflicting verbose/quiet
        if hasattr(args, "verbose") and hasattr(args, "quiet"):
            if args.verbose and args.quiet:
                raise ValueError("Cannot use both --verbose and --quiet")

    def run(self, argv: Optional[List[str]] = None) -> int:
        """Main entry point for the CLI.

        Subclasses should override this to implement their logic.

        Args:
            argv: Command-line arguments (None uses sys.argv)

        Returns:
            Exit code (0 for success)
        """
        try:
            args = self.parse_args(argv)
            self.validate_args(args)
            return self.execute(args)
        except KeyboardInterrupt:
            print("\nInterrupted by user", file=sys.stderr)
            return 130
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def execute(self, args: argparse.Namespace) -> int:
        """Execute the command with parsed arguments.

        Subclasses must implement this method.

        Args:
            args: Parsed and validated arguments

        Returns:
            Exit code (0 for success)
        """
        raise NotImplementedError("Subclasses must implement execute()")


class SubcommandCLI(BaseCLI):
    """Base class for CLIs with subcommands (like git)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subparsers: Optional[argparse._SubParsersAction] = None
        self.subcommands: Dict[str, argparse.ArgumentParser] = {}

    def create_parser(self) -> CustomArgumentParser:
        """Create parser with subcommand support."""
        parser = super().create_parser()

        self.subparsers = parser.add_subparsers(
            dest="command",
            help="Available commands",
            required=True,
            metavar="COMMAND",
        )

        return parser

    def add_subcommand(
        self, name: str, help_text: str, description: str = ""
    ) -> argparse.ArgumentParser:
        """Add a subcommand to the CLI.

        Args:
            name: Subcommand name
            help_text: Short help shown in command list
            description: Detailed description for subcommand help

        Returns:
            The subcommand parser for adding arguments
        """
        if not self.subparsers:
            raise RuntimeError("Parser not created. Call create_parser() first.")

        subparser = self.subparsers.add_parser(
            name,
            help=help_text,
            description=description or help_text,
            formatter_class=ColoredHelpFormatter,
        )

        self.subcommands[name] = subparser
        return subparser

    def execute(self, args: argparse.Namespace) -> int:
        """Route to appropriate subcommand handler."""
        if not args.command:
            self.parser.print_help()
            return 1

        # Call the appropriate handler method
        handler_name = f"handle_{args.command.replace('-', '_')}"
        handler = getattr(self, handler_name, None)

        if not handler:
            print(f"Error: No handler for command '{args.command}'", file=sys.stderr)
            return 1

        return handler(args)
