#!/usr/bin/env python3
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
m1f-help: Display help information for m1f tools with nice formatting
"""

import sys
from pathlib import Path

# Use unified colorama module
try:
    from .shared.colors import (
        Colors,
        success,
        error,
        warning,
        info,
        header,
        COLORAMA_AVAILABLE,
    )
except ImportError:
    # Try direct import if running as script
    sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
    from shared.colors import (
        Colors,
        success,
        error,
        warning,
        info,
        header,
        COLORAMA_AVAILABLE,
    )


def show_help():
    """Display the main help information."""
    # Header with ASCII art
    info(
        f"{Colors.CYAN}{Colors.BOLD}================================================================"
    )
    info("|                     m1f Tools Suite                          |")
    info("|              Make One File - Bundle Everything               |")
    info(
        f"================================================================{Colors.RESET}"
    )
    info("")

    header("[Available Commands]", "Your complete toolkit for bundling codebases")
    info("")

    # Core tools
    info(f"{Colors.YELLOW}{Colors.BOLD}Core Tools:{Colors.RESET}")
    info(
        f"  {Colors.GREEN}m1f{Colors.RESET}               - {Colors.DIM}Main tool for combining files into AI-friendly bundles{Colors.RESET}"
    )
    info(
        f"  {Colors.GREEN}m1f-s1f{Colors.RESET}           - {Colors.DIM}Split combined files back to original structure{Colors.RESET}"
    )
    info(
        f"  {Colors.GREEN}m1f-update{Colors.RESET}        - {Colors.DIM}Update m1f's own bundle files{Colors.RESET}"
    )
    info("")

    # Conversion tools
    info(f"{Colors.YELLOW}{Colors.BOLD}Conversion Tools:{Colors.RESET}")
    info(
        f"  {Colors.BLUE}m1f-html2md{Colors.RESET}       - {Colors.DIM}Convert HTML to clean Markdown{Colors.RESET}"
    )
    info(
        f"  {Colors.BLUE}m1f-scrape{Colors.RESET}        - {Colors.DIM}Download websites for offline viewing/conversion{Colors.RESET}"
    )
    info(
        f"  {Colors.BLUE}m1f-research{Colors.RESET}      - {Colors.DIM}AI-powered web research and content aggregation{Colors.RESET}"
    )
    info("")

    # Utility tools
    info(f"{Colors.YELLOW}{Colors.BOLD}Utility Tools:{Colors.RESET}")
    info(
        f"  {Colors.MAGENTA}m1f-token-counter{Colors.RESET} - {Colors.DIM}Count tokens in files (for LLM context limits){Colors.RESET}"
    )
    info(
        f"  {Colors.MAGENTA}m1f-claude{Colors.RESET}        - {Colors.DIM}Enhance prompts with m1f knowledge for Claude{Colors.RESET}"
    )
    info(
        f"  {Colors.MAGENTA}m1f-help{Colors.RESET}          - {Colors.DIM}Show this help message{Colors.RESET}"
    )
    info("")

    # Quick start
    header("[Quick Start Examples]")
    info(f"{Colors.CYAN}# Bundle a Python project:{Colors.RESET}")
    info(f"  m1f -s ./my-project -o project-bundle.md")
    info("")
    info(f"{Colors.CYAN}# Bundle with specific extensions:{Colors.RESET}")
    info(f"  m1f -s ./src --include-extensions .py .js .ts")
    info("")
    info(f"{Colors.CYAN}# Convert a website to markdown:{Colors.RESET}")
    info(f"  m1f-scrape https://example.com -o ./site")
    info(f"  m1f-html2md convert ./site -o ./markdown")
    info("")

    # Footer
    info(f"{Colors.DIM}{'─' * 60}{Colors.RESET}")
    info(
        f"{Colors.BOLD}For detailed help on each tool, use:{Colors.RESET} {Colors.CYAN}<tool> --help{Colors.RESET}"
    )
    info(
        f"{Colors.BOLD}Documentation:{Colors.RESET} {Colors.BLUE}https://github.com/franzundfranz/m1f{Colors.RESET}"
    )
    info("")


def main():
    """Main entry point."""
    import argparse
    
    # Import version
    try:
        from _version import __version__
    except ImportError:
        __version__ = "dev"

    parser = argparse.ArgumentParser(
        description="Display help information for m1f tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # We'll handle help ourselves
    )

    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )

    parser.add_argument(
        "-h", "--help", action="store_true", help="Show this help message"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"m1f-help {__version__}",
        help="Show version information"
    )

    args = parser.parse_args()

    if args.help:
        show_help()
        return 0

    if args.no_color:
        # Disable colors
        global COLORAMA_AVAILABLE
        COLORAMA_AVAILABLE = False
        Colors.disable()

    show_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
