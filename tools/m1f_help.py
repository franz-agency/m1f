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
    from .shared.colors import Colors, success, error, warning, info, header, COLORAMA_AVAILABLE
except ImportError:
    try:
        # Try direct import if running as script
        sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
        from shared.colors import Colors, success, error, warning, info, header, COLORAMA_AVAILABLE
    except ImportError:
        # Fallback to no colors
        COLORAMA_AVAILABLE = False
        class Colors:
            GREEN = ""
            RED = ""
            YELLOW = ""
            BLUE = ""
            CYAN = ""
            MAGENTA = ""
            BOLD = ""
            DIM = ""
            RESET = ""
        
        def success(msg): print(f"✅ {msg}")
        def error(msg): print(f"❌ {msg}", file=sys.stderr)
        def warning(msg): print(f"⚠️  {msg}")
        def info(msg): print(msg)
        def header(title, subtitle=None):
            print(f"\n{title}")
            if subtitle:
                print(subtitle)


def show_help():
    """Display the main help information."""
    # Header with ASCII art
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                     m1f Tools Suite                          ║")
    print("║              Make One File - Bundle Everything               ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}")
    
    header("🛠️  Available Commands", "Your complete toolkit for bundling codebases")
    print()
    
    # Core tools
    print(f"{Colors.YELLOW}{Colors.BOLD}Core Tools:{Colors.RESET}")
    print(f"  {Colors.GREEN}m1f{Colors.RESET}               - {Colors.DIM}Main tool for combining files into AI-friendly bundles{Colors.RESET}")
    print(f"  {Colors.GREEN}m1f-s1f{Colors.RESET}           - {Colors.DIM}Split combined files back to original structure{Colors.RESET}")
    print(f"  {Colors.GREEN}m1f-update{Colors.RESET}        - {Colors.DIM}Update m1f's own bundle files{Colors.RESET}")
    print()
    
    # Conversion tools
    print(f"{Colors.YELLOW}{Colors.BOLD}Conversion Tools:{Colors.RESET}")
    print(f"  {Colors.BLUE}m1f-html2md{Colors.RESET}       - {Colors.DIM}Convert HTML to clean Markdown{Colors.RESET}")
    print(f"  {Colors.BLUE}m1f-scrape{Colors.RESET}        - {Colors.DIM}Download websites for offline viewing/conversion{Colors.RESET}")
    print(f"  {Colors.BLUE}m1f-research{Colors.RESET}      - {Colors.DIM}AI-powered web research and content aggregation{Colors.RESET}")
    print()
    
    # Utility tools
    print(f"{Colors.YELLOW}{Colors.BOLD}Utility Tools:{Colors.RESET}")
    print(f"  {Colors.MAGENTA}m1f-token-counter{Colors.RESET} - {Colors.DIM}Count tokens in files (for LLM context limits){Colors.RESET}")
    print(f"  {Colors.MAGENTA}m1f-claude{Colors.RESET}        - {Colors.DIM}Enhance prompts with m1f knowledge for Claude{Colors.RESET}")
    print(f"  {Colors.MAGENTA}m1f-help{Colors.RESET}          - {Colors.DIM}Show this help message{Colors.RESET}")
    print()
    
    # Quick start
    header("🚀 Quick Start Examples")
    print(f"{Colors.CYAN}# Bundle a Python project:{Colors.RESET}")
    print(f"  m1f -s ./my-project -o project-bundle.md")
    print()
    print(f"{Colors.CYAN}# Bundle with specific extensions:{Colors.RESET}")
    print(f"  m1f -s ./src --include-extensions .py .js .ts")
    print()
    print(f"{Colors.CYAN}# Convert a website to markdown:{Colors.RESET}")
    print(f"  m1f-scrape https://example.com -o ./site")
    print(f"  m1f-html2md convert ./site -o ./markdown")
    print()
    
    # Footer
    print(f"{Colors.DIM}{'─' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}For detailed help on each tool, use:{Colors.RESET} {Colors.CYAN}<tool> --help{Colors.RESET}")
    print(f"{Colors.BOLD}Documentation:{Colors.RESET} {Colors.BLUE}https://github.com/franzundfranz/m1f{Colors.RESET}")
    print()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Display help information for m1f tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False  # We'll handle help ourselves
    )
    
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )
    
    parser.add_argument(
        "-h", "--help",
        action="store_true",
        help="Show this help message"
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