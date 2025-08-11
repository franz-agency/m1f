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

"""Command-line interface for HTML to Markdown converter."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional
from collections import Counter

# Import safe file operations
from ..m1f.file_operations import (
    safe_exists,
    safe_is_file,
    safe_is_dir,
    safe_mkdir,
    safe_open,
    safe_read_text,
    safe_write_text,
)

# Use unified colorama module
from ..shared.colors import (
    Colors,
    ColoredHelpFormatter,
    success,
    error,
    warning,
    info,
    header,
    COLORAMA_AVAILABLE,
)
from ..shared.cli import CustomArgumentParser

from . import __version__
from .api import Html2mdConverter
from .config import Config, OutputFormat
from .claude_runner import ClaudeRunner


def create_parser() -> CustomArgumentParser:
    """Create the argument parser."""
    description = """m1f-html2md - HTML to Markdown Converter
=====================================

Convert HTML files to clean Markdown format with advanced content extraction options.
Supports both local processing and Claude AI-powered conversion for optimal results.

Perfect for:
• Converting scraped documentation to readable Markdown
• Extracting main content from complex HTML layouts
• Batch processing entire documentation sites
• AI-powered intelligent content extraction"""

    epilog = """Examples:
  %(prog)s convert file.html -o file.md
  %(prog)s convert ./html/ -o ./markdown/
  %(prog)s convert ./html/ -c config.yaml
  %(prog)s convert ./html/ -o ./md/ --content-selector "article.post"
  %(prog)s analyze ./html/ --claude
  %(prog)s analyze ./html/ --claude --analyze-files 10
  %(prog)s convert ./html/ -o ./markdown/ --claude --model opus
  
For more information, see the documentation."""

    parser = CustomArgumentParser(
        prog="m1f-html2md",
        description=description,
        epilog=epilog,
        formatter_class=ColoredHelpFormatter,
        add_help=True,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program version and exit",
    )

    # Output control group
    output_group = parser.add_argument_group("Output Control")
    output_group.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    output_group.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress all output except errors"
    )
    output_group.add_argument("--log-file", type=Path, help="Write logs to file")

    # Subcommands
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        required=True,
        metavar="COMMAND",
    )

    # Convert command
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert HTML files to Markdown",
        formatter_class=ColoredHelpFormatter,
    )
    add_convert_arguments(convert_parser)

    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze HTML structure for content extraction",
        formatter_class=ColoredHelpFormatter,
    )
    add_analyze_arguments(analyze_parser)

    # Config command
    config_parser = subparsers.add_parser(
        "config",
        help="Generate configuration file template",
        formatter_class=ColoredHelpFormatter,
    )
    add_config_arguments(config_parser)

    return parser


def add_convert_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for convert command."""
    # Positional arguments
    parser.add_argument("source", type=Path, help="Source HTML file or directory")
    parser.add_argument(
        "-o", "--output", type=Path, required=True, help="Output file or directory"
    )

    # Configuration group
    config_group = parser.add_argument_group("Configuration")
    config_group.add_argument(
        "-c", "--config", type=Path, help="Configuration file (YAML/JSON/TOML)"
    )
    config_group.add_argument(
        "--format",
        choices=["markdown", "m1f_bundle", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )

    # Content extraction group
    extraction_group = parser.add_argument_group("Content Extraction")
    extraction_group.add_argument(
        "--content-selector",
        metavar="SELECTOR",
        help="CSS selector for main content area",
    )
    extraction_group.add_argument(
        "--ignore-selectors",
        nargs="+",
        metavar="SELECTOR",
        help="CSS selectors to ignore (nav, header, footer, etc.)",
    )
    extraction_group.add_argument(
        "--extractor",
        type=Path,
        metavar="FILE",
        help="Path to custom extractor Python file",
    )

    # Processing options group
    processing_group = parser.add_argument_group("Processing Options")
    processing_group.add_argument(
        "--heading-offset",
        type=int,
        default=0,
        metavar="N",
        help="Offset heading levels by N (default: 0)",
    )
    processing_group.add_argument(
        "--no-frontmatter",
        action="store_true",
        help="Don't add YAML frontmatter to output",
    )
    processing_group.add_argument(
        "--parallel",
        action="store_true",
        help="Enable parallel processing for multiple files",
    )

    # Claude AI options group
    ai_group = parser.add_argument_group("Claude AI Options")
    ai_group.add_argument(
        "--claude",
        action="store_true",
        help="Use Claude AI for intelligent HTML to Markdown conversion",
    )
    ai_group.add_argument(
        "--model",
        choices=["opus", "sonnet"],
        default="sonnet",
        help="Claude model to use (default: sonnet)",
    )
    ai_group.add_argument(
        "--sleep",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="Delay between Claude API calls (default: 1.0)",
    )


def add_analyze_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for analyze command."""
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="HTML files or directories to analyze",
    )

    # Analysis options group
    analysis_group = parser.add_argument_group("Analysis Options")
    analysis_group.add_argument(
        "--show-structure",
        action="store_true",
        help="Show detailed HTML structure analysis",
    )
    analysis_group.add_argument(
        "--common-patterns",
        action="store_true",
        help="Find common patterns across multiple files",
    )
    analysis_group.add_argument(
        "--suggest-selectors",
        action="store_true",
        help="Suggest CSS selectors for content extraction",
    )

    # Claude AI options group
    ai_group = parser.add_argument_group("Claude AI Options")
    ai_group.add_argument(
        "--claude",
        action="store_true",
        help="Use Claude AI for intelligent analysis and selector suggestions",
    )
    ai_group.add_argument(
        "--analyze-files",
        type=int,
        default=5,
        metavar="N",
        help="Number of files to analyze with Claude (1-20, default: 5)",
    )
    ai_group.add_argument(
        "--parallel-workers",
        type=int,
        default=5,
        metavar="N",
        help="Number of parallel Claude sessions (1-10, default: 5)",
    )
    ai_group.add_argument(
        "--project-description",
        type=str,
        default="",
        metavar="TEXT",
        help="Project description for Claude context",
    )


def add_config_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for config command."""
    # Configuration options group
    config_group = parser.add_argument_group("Configuration Options")
    config_group.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("config.yaml"),
        help="Output configuration file (default: config.yaml)",
    )
    config_group.add_argument(
        "--format",
        choices=["yaml", "toml", "json"],
        default="yaml",
        help="Configuration file format (default: yaml)",
    )


def handle_convert(args: argparse.Namespace) -> None:
    """Handle convert command."""
    # If --claude flag is set, use Claude for conversion
    if args.claude:
        _handle_claude_convert(args)
        return

    # Load configuration
    from .config import Config

    if args.config:
        from .config import load_config
        import yaml

        # Load the config file to check its contents
        with safe_open(args.config, "r") as f:
            config_data = yaml.safe_load(f)

        # If the config only contains extractor settings (from Claude analysis),
        # create a full config with source and destination from CLI
        if "source" not in config_data and "destination" not in config_data:
            source_path = (
                args.source.parent if safe_is_file(args.source) else args.source
            )
            config = Config(source=source_path, destination=args.output)

            # Apply extractor settings from the config file
            if "extractor" in config_data:
                for key, value in config_data["extractor"].items():
                    if hasattr(config.extractor, key):
                        setattr(config.extractor, key, value)

            # Apply conversion settings from the config file
            if "conversion" in config_data:
                for key, value in config_data["conversion"].items():
                    if hasattr(config.conversion, key):
                        setattr(config.conversion, key, value)
        else:
            # Full config file - load it normally
            config = load_config(args.config)

            # IMPORTANT: CLI arguments should always override config file values
            # Only override if CLI args were explicitly provided
            cli_source_path = (
                args.source.parent if safe_is_file(args.source) else args.source
            )
            config.source = cli_source_path
            config.destination = args.output
    else:
        # When source is a file, use its parent directory as the source
        source_path = args.source.parent if safe_is_file(args.source) else args.source
        config = Config(source=source_path, destination=args.output)

    # Update config with CLI arguments
    if args.content_selector:
        config.conversion.outermost_selector = args.content_selector

    if args.ignore_selectors:
        config.conversion.ignore_selectors = args.ignore_selectors

    if args.heading_offset:
        config.processor.heading_offset = args.heading_offset

    if args.no_frontmatter:
        config.conversion.generate_frontmatter = False
        config.conversion.add_frontmatter = False

    if args.parallel:
        config.parallel = True

    if hasattr(args, "format"):
        config.output_format = OutputFormat(args.format)

    config.verbose = args.verbose
    config.quiet = args.quiet
    config.log_file = args.log_file

    # Create converter
    extractor = args.extractor if hasattr(args, "extractor") else None
    converter = Html2mdConverter(config, extractor=extractor)

    # Convert based on source type
    if safe_is_file(args.source):
        info(f"Converting file: {args.source}")
        output = converter.convert_file(args.source)
        success(f"Converted to: {output}")

    elif safe_is_dir(args.source):
        info(f"Converting directory: {args.source}")
        outputs = converter.convert_directory()
        success(f"Converted {len(outputs)} files")

    else:
        error(f"Source not found: {args.source}")
        sys.exit(1)


def handle_analyze(args: argparse.Namespace) -> None:
    """Handle analyze command."""
    from bs4 import BeautifulSoup
    from collections import Counter
    import json

    # Collect all HTML files from provided paths
    html_files = []
    for path in args.paths:
        if not safe_exists(path):
            error(f"Path not found: {path}")
            continue

        if safe_is_file(path):
            # Single file
            if path.suffix.lower() in [".html", ".htm"]:
                html_files.append(path)
            else:
                warning(f"Skipping non-HTML file: {path}")
        elif safe_is_dir(path):
            # Directory - find all HTML files recursively
            found_files = list(path.rglob("*.html")) + list(path.rglob("*.htm"))
            if found_files:
                html_files.extend(found_files)
                info(
                    f"{Colors.BLUE}Found {len(found_files)} HTML files in {path}{Colors.RESET}"
                )
            else:
                warning(f"No HTML files found in {path}")

    if not html_files:
        error("No HTML files to analyze")
        sys.exit(1)

    # If --claude flag is set, use Claude AI for analysis
    if args.claude:
        info(f"\nFound {len(html_files)} HTML files total")
        _handle_claude_analysis(
            html_files,
            args.analyze_files,
            args.parallel_workers,
            args.project_description,
        )
        return

    # Otherwise, do local analysis
    info(f"\nAnalyzing {len(html_files)} HTML files...")

    # Read and parse all files
    parsed_files = []
    for file_path in html_files:
        try:
            content = safe_read_text(file_path, encoding="utf-8")
            soup = BeautifulSoup(content, "html.parser")
            parsed_files.append((file_path, soup))
            # Show relative path from current directory for better identification
            try:
                relative_path = file_path.relative_to(Path.cwd())
            except ValueError:
                relative_path = file_path
            success(f"Parsed: {relative_path}")
        except Exception as e:
            error(f"Error parsing {file_path}: {e}")

    if not parsed_files:
        error("No files could be parsed")
        sys.exit(1)

    # Analyze structure
    if args.show_structure:
        header("HTML Structure Analysis:")
        for file_path, soup in parsed_files:
            info(f"\n{Colors.BLUE}{file_path.name}:{Colors.RESET}")
            _show_structure(soup)

    # Find common patterns
    if args.common_patterns:
        header("Common Patterns:")
        _find_common_patterns(parsed_files)

    # Suggest selectors
    if args.suggest_selectors or (not args.show_structure and not args.common_patterns):
        header("Suggested CSS Selectors:")
        suggestions = _suggest_selectors(parsed_files)

        info(f"\n{Colors.YELLOW}Content selectors:{Colors.RESET}")
        for selector, confidence in suggestions["content"]:
            info(f"  {selector} (confidence: {confidence:.0%})")

        info(f"\n{Colors.YELLOW}Elements to ignore:{Colors.RESET}")
        for selector in suggestions["ignore"]:
            info(f"  {selector}")

        # Print example configuration
        header("Example configuration:")
        info("```yaml")
        info("extractor:")
        if suggestions["content"]:
            info(f"  outermost_selector: \"{suggestions['content'][0][0]}\"")
        info("  ignore_selectors:")
        for selector in suggestions["ignore"]:
            info(f'    - "{selector}"')
        info("```")


def _show_structure(soup):
    """Show the structure of an HTML document."""
    # Find main content areas
    main_areas = soup.find_all(["main", "article", "section", "div"], limit=10)

    for area in main_areas:
        # Get identifying attributes
        attrs = []
        if area.get("id"):
            attrs.append(f"id=\"{area.get('id')}\"")
        if area.get("class"):
            classes = " ".join(area.get("class"))
            attrs.append(f'class="{classes}"')

        attr_str = " ".join(attrs) if attrs else ""
        info(f"  <{area.name} {attr_str}>")

        # Show child elements
        for child in area.find_all(recursive=False, limit=5):
            if child.name:
                child_attrs = []
                if child.get("id"):
                    child_attrs.append(f"id=\"{child.get('id')}\"")
                if child.get("class"):
                    child_classes = " ".join(child.get("class"))
                    child_attrs.append(f'class="{child_classes}"')
                child_attr_str = " ".join(child_attrs) if child_attrs else ""
                info(f"    <{child.name} {child_attr_str}>")


def _find_common_patterns(parsed_files):
    """Find common patterns across HTML files."""
    # Collect all class names and IDs
    all_classes = Counter()
    all_ids = Counter()
    tag_patterns = Counter()

    for _, soup in parsed_files:
        # Count classes
        for elem in soup.find_all(class_=True):
            for cls in elem.get("class", []):
                all_classes[cls] += 1

        # Count IDs
        for elem in soup.find_all(id=True):
            all_ids[elem.get("id")] += 1

        # Count tag patterns
        for elem in soup.find_all(
            ["main", "article", "section", "header", "footer", "nav", "aside"]
        ):
            tag_patterns[elem.name] += 1

    # Show most common patterns
    info(f"\n{Colors.YELLOW}Most common classes:{Colors.RESET}")
    for cls, count in all_classes.most_common(10):
        info(f"  .{cls} (found {count} times)")

    info(f"\n{Colors.YELLOW}Most common IDs:{Colors.RESET}")
    for id_name, count in all_ids.most_common(10):
        info(f"  #{id_name} (found {count} times)")

    info(f"\n{Colors.YELLOW}Common structural elements:{Colors.RESET}")
    for tag, count in tag_patterns.most_common():
        info(f"  <{tag}> (found {count} times)")


def _handle_claude_analysis(
    html_files, num_files_to_analyze=5, parallel_workers=5, project_description=""
):
    """Handle analysis using Claude AI with improved timeout handling and parallel processing."""
    import subprocess
    import os
    import tempfile
    import time
    from pathlib import Path
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from m1f.utils import validate_path_traversal

    # Try to use improved runner if available
    try:
        from .cli_claude import handle_claude_analysis_improved

        return handle_claude_analysis_improved(
            html_files, num_files_to_analyze, parallel_workers, project_description
        )
    except ImportError:
        pass

    header("Using Claude AI for intelligent analysis...")

    # Find the common parent directory of all HTML files
    if not html_files:
        error("No HTML files to analyze")
        return

    common_parent = Path(os.path.commonpath([str(f.absolute()) for f in html_files]))
    info(f"Analysis directory: {common_parent}")
    info(f"Total HTML files found: {len(html_files)}")

    # Check if we have enough files
    if len(html_files) == 0:
        error("No HTML files found in the specified directory")
        return

    # We'll work from the current directory and use --add-dir for Claude
    original_dir = Path.cwd()

    # Step 1: Create m1f and analysis directories if they don't exist
    m1f_dir = common_parent / "m1f"
    safe_mkdir(m1f_dir, exist_ok=True)
    analysis_dir = m1f_dir / "analysis"
    safe_mkdir(analysis_dir, exist_ok=True)

    # Clean old analysis files
    for old_file in analysis_dir.glob("*.txt"):
        if old_file.name != "log.txt":
            old_file.unlink()

    # Initialize analysis log
    from datetime import datetime

    log_file = analysis_dir / "log.txt"
    log_file.write_text(f"Analysis started: {datetime.now().isoformat()}\n")

    # Create a filelist with all HTML files using m1f
    info("\n🔧 Creating HTML file list using m1f...")
    info(f"Working with HTML directory: {common_parent}")

    # Run m1f to create only the filelist (not the content)
    m1f_cmd = [
        "m1f",
        "-s",
        str(common_parent),
        "-o",
        str(m1f_dir / "all_html_files.txt"),
        "--include-extensions",
        ".html",
        ".htm",
        "--skip-output-file",  # This creates only the filelist, not the content
        "--force",
    ]

    try:
        result = subprocess.run(m1f_cmd, capture_output=True, text=True, check=True)

        # The filelist will be created with this name
        html_filelist = m1f_dir / "all_html_files_filelist.txt"
        if not safe_exists(html_filelist):
            error("m1f filelist not created")
            return

        success(f"Created HTML file list: {html_filelist}")

    except subprocess.CalledProcessError as e:
        error(f"Failed to create HTML file list: {e.stderr}")
        return

    # Get relative paths from the common parent (still needed for filtering)
    relative_paths = []
    for f in html_files:
        try:
            rel_path = f.relative_to(common_parent)
            relative_paths.append(str(rel_path))
        except ValueError:
            relative_paths.append(str(f))

    # Step 1: Load the file selection prompt
    prompt_dir = Path(__file__).parent / "prompts"
    select_prompt_path = prompt_dir / "select_files_from_project.md"

    if not safe_exists(select_prompt_path):
        error(f"Prompt file not found: {select_prompt_path}")
        return

    # Load the prompt from external file
    simple_prompt_template = safe_read_text(select_prompt_path)

    # Validate and adjust number of files to analyze
    if num_files_to_analyze < 1:
        num_files_to_analyze = 1
        warning("Minimum is 1 file. Using 1.")
    elif num_files_to_analyze > 20:
        num_files_to_analyze = 20
        warning("Maximum is 20 files. Using 20.")

    if num_files_to_analyze > len(html_files):
        num_files_to_analyze = len(html_files)
        warning(f"Only {len(html_files)} files available. Will analyze all of them.")

    # Ask user for project description if not provided
    if not project_description:
        header("Project Context:")
        info(
            "Please briefly describe what this HTML project contains so Claude can better understand"
        )
        info(
            "what should be converted to Markdown. Example: 'Documentation for XY software - API section'"
        )
        info(
            "\nTip: If there are particularly important files to analyze, mention them in your description"
        )
        info("     so Claude will prioritize those files in the analysis.")
        project_description = input("\nProject description: ").strip()
    else:
        header(f"Project Context: {project_description}")

    # Update the prompt with the number of files
    simple_prompt_template = simple_prompt_template.replace(
        "5 representative", f"{num_files_to_analyze} representative"
    )
    simple_prompt_template = simple_prompt_template.replace(
        "select 5", f"select {num_files_to_analyze}"
    )
    simple_prompt_template = simple_prompt_template.replace(
        "EXACTLY 5 file paths", f"EXACTLY {num_files_to_analyze} file paths"
    )
    simple_prompt_template = simple_prompt_template.replace(
        "exactly 5 representative", f"exactly {num_files_to_analyze} representative"
    )

    # Add project description to the prompt
    if project_description:
        simple_prompt = (
            f"PROJECT CONTEXT: {project_description}\n\n{simple_prompt_template}"
        )
    else:
        simple_prompt = simple_prompt_template

    info(f"\nAsking Claude to select {num_files_to_analyze} representative files...")

    try:
        # Run claude using the same approach as m1f-claude
        cmd = [
            "claude",
            "--print",  # Use --print instead of -p
            "--allowedTools",
            "Read,Glob,Grep,Write",  # Allow file reading and writing tools
            "--add-dir",
            str(common_parent),  # Give Claude access to the HTML directory
        ]

        # Use subprocess.run() which works more reliably with Claude
        result = subprocess.run(
            cmd,
            input=simple_prompt,
            capture_output=True,
            text=True,
            timeout=180,  # 3 minutes for file selection
        )

        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd, output=result.stdout, stderr=result.stderr
            )
        selected_files = result.stdout.strip().split("\n")
        selected_files = [f.strip() for f in selected_files if f.strip()]

        # Filter out any lines that are not file paths (e.g., explanations)
        valid_files = []
        for f in selected_files:
            # Skip lines that look like explanations (contain "select" or start with lowercase or are too long)
            if (
                any(
                    word in f.lower()
                    for word in ["select", "based on", "analysis", "representative"]
                )
                or len(f) > 100
            ):
                continue
            # Only keep lines that look like file paths (contain .html or /)
            if ".html" in f or "/" in f:
                valid_files.append(f)

        selected_files = valid_files

        info(f"\nClaude selected {len(selected_files)} files:")
        for f in selected_files:
            info(f"  - {Colors.BLUE}{f}{Colors.RESET}")

    except subprocess.TimeoutExpired:
        warning("Timeout selecting files (3 minutes)")
        return
    except subprocess.CalledProcessError as e:
        error(f"Claude command failed: {e}")
        error(f"Error output: {e.stderr}")
        return
    except FileNotFoundError:
        # Try to find claude in common locations
        claude_paths = [
            Path.home() / ".claude" / "local" / "claude",
            Path("/usr/local/bin/claude"),
            Path("/usr/bin/claude"),
        ]

        claude_found = False
        for claude_path in claude_paths:
            if safe_exists(claude_path) and safe_is_file(claude_path):
                warning(f"Found claude at: {claude_path}")
                # Update the command to use the full path
                cmd[0] = str(claude_path)
                try:
                    result = subprocess.run(
                        cmd,
                        input=simple_prompt,
                        capture_output=True,
                        text=True,
                        timeout=180,
                    )

                    if result.returncode != 0:
                        raise subprocess.CalledProcessError(
                            result.returncode,
                            cmd,
                            output=result.stdout,
                            stderr=result.stderr,
                        )

                    selected_files = result.stdout.strip().split("\n")
                    selected_files = [f.strip() for f in selected_files if f.strip()]

                    # Filter out any lines that are not file paths (e.g., explanations)
                    valid_files = []
                    for f in selected_files:
                        if (
                            any(
                                word in f.lower()
                                for word in [
                                    "select",
                                    "based on",
                                    "analysis",
                                    "representative",
                                ]
                            )
                            or len(f) > 100
                        ):
                            continue
                        if ".html" in f or "/" in f:
                            valid_files.append(f)

                    selected_files = valid_files

                    info(f"\nClaude selected {len(selected_files)} files:")
                    for f in selected_files:
                        info(f"  - {Colors.BLUE}{f}{Colors.RESET}")

                    claude_found = True
                    break

                except Exception as e:
                    warning(f"Failed with {claude_path}: {e}")
                    continue

        if not claude_found:
            error("claude command not found. Please install Claude CLI.")
            warning(
                "If claude is installed as an alias, try adding it to your PATH or creating a symlink."
            )
            return

    # Step 2: Verify the selected files exist and save to file
    info("\nVerifying selected HTML files...")
    verified_files = []

    for file_path in selected_files[:num_files_to_analyze]:  # Limit to selected number
        file_path = file_path.strip()

        # Check if file exists (relative to common_parent)
        full_path = common_parent / file_path
        if safe_exists(full_path):
            verified_files.append(file_path)
            success(f"Found: {file_path}")
        else:
            warning(f"Not found: {file_path}")

    if not verified_files:
        error("No HTML files could be verified")
        return

    # Write the verified files to a reference list
    selected_files_path = m1f_dir / "selected_html_files.txt"
    with safe_open(selected_files_path, "w") as f:
        for file_path in verified_files:
            f.write(f"{file_path}\n")
    success(f"Wrote selected files list to: {selected_files_path}")

    # Step 3: Analyze each file individually with Claude
    info("\nAnalyzing each file individually with Claude...")

    # Load the individual analysis prompt template
    individual_prompt_path = prompt_dir / "analyze_individual_file.md"

    if not safe_exists(individual_prompt_path):
        error(f"Prompt file not found: {individual_prompt_path}")
        return

    individual_prompt_template = safe_read_text(individual_prompt_path)

    # Analyze each of the selected files
    for i, file_path in enumerate(verified_files, 1):
        info(f"\n📋 Analyzing file {i}/{len(verified_files)}: {file_path}")
        info(f"⏱️  Starting analysis at {time.strftime('%H:%M:%S')}")

        # Customize prompt for this specific file
        individual_prompt = individual_prompt_template.replace("{filename}", file_path)
        individual_prompt = individual_prompt.replace("{file_number}", str(i))

        # Add project context if provided
        if project_description:
            individual_prompt = (
                f"PROJECT CONTEXT: {project_description}\n\n{individual_prompt}"
            )

        try:
            # Run claude for this individual file
            # First try with 'claude' command, then fall back to known paths
            claude_cmd = "claude"
            claude_paths = [
                Path.home() / ".claude" / "local" / "claude",
                Path("/usr/local/bin/claude"),
                Path("/usr/bin/claude"),
            ]

            # Check if we need to use full path
            try:
                subprocess.run(["claude", "--version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Try to find claude in known locations
                for path in claude_paths:
                    if safe_exists(path) and safe_is_file(path):
                        claude_cmd = str(path)
                        break

            cmd = [
                claude_cmd,
                "--print",
                "--allowedTools",
                "Read,Glob,Grep,Write",
                "--add-dir",
                str(common_parent),
            ]

            # Use subprocess.run() which works more reliably with Claude
            result = subprocess.run(
                cmd,
                input=individual_prompt,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes per file analysis
            )

            # Debug: Show process details
            info(f"🔍 Process return code: {result.returncode}")
            if result.stderr:
                info(f"🔍 stderr: {result.stderr[:200]}...")

            if result.returncode != 0:
                error(f"Analysis failed for {file_path}: {result.stderr}")
                continue

            # Show Claude's response for transparency
            if result.stdout.strip():
                info(f"📄 Claude: {result.stdout.strip()}")

            success(f"Analysis completed for file {i}")

        except subprocess.TimeoutExpired:
            warning(f"Timeout analyzing {file_path} (5 minutes)")
            continue
        except Exception as e:
            error(f"Error analyzing {file_path}: {e}")
            continue

    # Step 4: Synthesize all analyses into final config
    info("\n🔬 Synthesizing analyses into final configuration...")

    # Load the synthesis prompt
    synthesis_prompt_path = prompt_dir / "synthesize_config.md"

    if not safe_exists(synthesis_prompt_path):
        error(f"Prompt file not found: {synthesis_prompt_path}")
        return

    synthesis_prompt = safe_read_text(synthesis_prompt_path)

    # Update the synthesis prompt with the actual number of files analyzed
    synthesis_prompt = synthesis_prompt.replace(
        "analyzed 5 HTML files", f"analyzed {len(verified_files)} HTML files"
    )
    synthesis_prompt = synthesis_prompt.replace(
        "You have analyzed 5 HTML files",
        f"You have analyzed {len(verified_files)} HTML files",
    )

    # Build the file list dynamically
    file_list = []
    for i in range(1, len(verified_files) + 1):
        file_list.append(f"- m1f/analysis/html_analysis_{i}.txt")

    # Replace the static file list with the dynamic one
    old_file_list = """Read the 5 analysis files:
- m1f/analysis/html_analysis_1.txt
- m1f/analysis/html_analysis_2.txt  
- m1f/analysis/html_analysis_3.txt
- m1f/analysis/html_analysis_4.txt
- m1f/analysis/html_analysis_5.txt"""

    new_file_list = f"Read the {len(verified_files)} analysis files:\n" + "\n".join(
        file_list
    )
    synthesis_prompt = synthesis_prompt.replace(old_file_list, new_file_list)

    # Update other references to "5 files"
    synthesis_prompt = synthesis_prompt.replace(
        "Analyzed 5 files", f"Analyzed {len(verified_files)} files"
    )
    synthesis_prompt = synthesis_prompt.replace(
        "works on X/5 files", f"works on X/{len(verified_files)} files"
    )
    synthesis_prompt = synthesis_prompt.replace(
        "found in X/5 files", f"found in X/{len(verified_files)} files"
    )
    synthesis_prompt = synthesis_prompt.replace(
        "(4-5 out of 5)",
        f"({len(verified_files)-1}-{len(verified_files)} out of {len(verified_files)})",
    )
    synthesis_prompt = synthesis_prompt.replace(
        "works on 4/5 files",
        f"works on {max(1, len(verified_files)-1)}/{len(verified_files)} files",
    )
    synthesis_prompt = synthesis_prompt.replace(
        "works on 3/5 files",
        f"works on {max(1, len(verified_files)//2)}/{len(verified_files)} files",
    )
    synthesis_prompt = synthesis_prompt.replace(
        "found in 3+ files", f"found in {max(2, len(verified_files)//2)}+ files"
    )

    # Add project context if provided
    if project_description:
        synthesis_prompt = (
            f"PROJECT CONTEXT: {project_description}\n\n{synthesis_prompt}"
        )

    try:
        # Run claude for synthesis
        # Use the same claude command detection as before
        claude_cmd = "claude"
        claude_paths = [
            Path.home() / ".claude" / "local" / "claude",
            Path("/usr/local/bin/claude"),
            Path("/usr/bin/claude"),
        ]

        # Check if we need to use full path
        try:
            subprocess.run(["claude", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Try to find claude in known locations
            for path in claude_paths:
                if safe_exists(path) and safe_is_file(path):
                    claude_cmd = str(path)
                    break

        cmd = [
            claude_cmd,
            "--print",
            "--allowedTools",
            "Read,Glob,Grep,Write",
            "--add-dir",
            str(common_parent),
        ]

        # Use subprocess.run() which works more reliably with Claude
        result = subprocess.run(
            cmd,
            input=synthesis_prompt,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes for synthesis
        )

        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd, output=result.stdout, stderr=result.stderr
            )

        header("Claude's Final Configuration:")
        info(result.stdout)

        # Try to parse the YAML config from Claude's output
        import yaml

        try:
            # Extract YAML from the output (between ```yaml and ```)
            output = result.stdout
            yaml_start = output.find("```yaml")
            yaml_end = output.find("```", yaml_start + 6)

            if yaml_start != -1 and yaml_end != -1:
                yaml_content = output[yaml_start + 7 : yaml_end].strip()
                config_data = yaml.safe_load(yaml_content)

                # Clean up the config - remove empty strings
                if "extractor" in config_data:
                    extractor = config_data["extractor"]
                    if "alternative_selectors" in extractor:
                        extractor["alternative_selectors"] = [
                            s for s in extractor["alternative_selectors"] if s
                        ]
                    if "ignore_selectors" in extractor:
                        extractor["ignore_selectors"] = [
                            s for s in extractor["ignore_selectors"] if s
                        ]

                # Save the config to a file with consistent name
                config_file = common_parent / "html2md_config.yaml"
                with safe_open(config_file, "w") as f:
                    yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

                success(f"Configuration saved to: {config_file}")

                # Show clear usage instructions
                info("\n" + "=" * 60)
                info(
                    f"{Colors.GREEN}{Colors.BOLD}✨ Analysis Complete! Here's how to convert your HTML files:{Colors.RESET}"
                )
                info("=" * 60 + "\n")

                info(
                    f"{Colors.BOLD}Option 1: Use the generated configuration (RECOMMENDED){Colors.RESET}"
                )
                info(
                    "This uses the CSS selectors Claude identified to extract only the main content:\n"
                )
                info(
                    f"{Colors.CYAN}m1f-html2md convert {common_parent} -o ./markdown -c {config_file}{Colors.RESET}\n"
                )

                info(
                    f"{Colors.BOLD}Option 2: Use Claude AI for each file{Colors.RESET}"
                )
                info(
                    "This uses Claude to intelligently extract content from each file individually:"
                )
                info("(Slower but may handle edge cases better)\n")
                info(
                    f"{Colors.CYAN}m1f-html2md convert {common_parent} -o ./markdown --claude{Colors.RESET}\n"
                )

                info(f"{Colors.BOLD}Option 3: Convert a single file{Colors.RESET}")
                info("To test the configuration on a single file first:\n")
                info(
                    f"{Colors.CYAN}m1f-html2md convert path/to/file.html -o test.md -c {config_file}{Colors.RESET}\n"
                )

                info("=" * 60)
            else:
                warning("Could not extract YAML configuration from Claude's response")
                info(
                    "Please manually create html2md_config.yaml based on the analysis above."
                )
                info(
                    "\nExpected format: The YAML should be between ```yaml and ``` markers."
                )

        except Exception as e:
            warning(f"Could not save configuration: {e}")
            info(
                f"Please manually create {common_parent}/html2md_config.yaml based on the analysis above."
            )

    except subprocess.TimeoutExpired:
        warning("Timeout synthesizing configuration (5 minutes)")
    except subprocess.CalledProcessError as e:
        error(f"Claude command failed: {e}")
        error(f"Error output: {e.stderr}")

    # Ask if temporary analysis files should be deleted
    header("Cleanup:")
    cleanup = input("Delete temporary analysis files (html_analysis_*.txt)? [Y/n]: ")

    if cleanup.lower() != "n":
        # Delete analysis files
        deleted_count = 0
        for i in range(1, num_files_to_analyze + 1):
            analysis_file = analysis_dir / f"html_analysis_{i}.txt"
            if safe_exists(analysis_file):
                try:
                    analysis_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    warning(f"Could not delete {analysis_file.name}: {e}")

        if deleted_count > 0:
            success(f"Deleted {deleted_count} temporary analysis files")
    else:
        info(
            f"{Colors.BLUE}ℹ️  Temporary analysis files kept in m1f/ directory{Colors.RESET}"
        )


def _suggest_selectors(parsed_files):
    """Suggest CSS selectors for content extraction."""
    suggestions = {"content": [], "ignore": []}

    # Common content selectors to try
    content_selectors = [
        "main",
        "article",
        "[role='main']",
        "#content",
        "#main",
        ".content",
        ".main-content",
        ".entry-content",
        ".post-content",
        ".page-content",
    ]

    # Common elements to ignore
    ignore_patterns = [
        "nav",
        "header",
        "footer",
        "aside",
        ".sidebar",
        ".navigation",
        ".menu",
        ".header",
        ".footer",
        ".ads",
        ".advertisement",
        ".cookie-notice",
        ".popup",
        ".modal",
        "#comments",
        ".comments",
    ]

    # Test content selectors
    for selector in content_selectors:
        found_count = 0
        total_files = len(parsed_files)

        for _, soup in parsed_files:
            if soup.select(selector):
                found_count += 1

        if found_count > 0:
            confidence = found_count / total_files
            suggestions["content"].append((selector, confidence))

    # Sort by confidence
    suggestions["content"].sort(key=lambda x: x[1], reverse=True)

    # Add ignore selectors that exist
    for _, soup in parsed_files:
        for pattern in ignore_patterns:
            if soup.select(pattern):
                if pattern not in suggestions["ignore"]:
                    suggestions["ignore"].append(pattern)

    return suggestions


def _handle_claude_convert(args: argparse.Namespace) -> None:
    """Handle conversion using Claude AI."""
    import subprocess
    import time
    from pathlib import Path
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from m1f.utils import validate_path_traversal

    # Try to use improved converter if available
    try:
        from .convert_claude import handle_claude_convert_improved

        return handle_claude_convert_improved(args)
    except ImportError:
        pass

    header("Using Claude AI to convert HTML to Markdown...")
    info(f"Model: {args.model}")
    info(f"Sleep between calls: {args.sleep} seconds")

    # Find all HTML files in source directory
    source_path = args.source
    if not safe_exists(source_path):
        error(f"Source path not found: {source_path}")
        sys.exit(1)

    html_files = []
    if safe_is_file(source_path):
        if source_path.suffix.lower() in [".html", ".htm"]:
            html_files.append(source_path)
        else:
            error(f"Source file is not HTML: {source_path}")
            sys.exit(1)
    elif safe_is_dir(source_path):
        # Find all HTML files recursively
        html_files = list(source_path.rglob("*.html")) + list(
            source_path.rglob("*.htm")
        )
        info(f"Found {len(html_files)} HTML files in {source_path}")

    if not html_files:
        error("No HTML files found to convert")
        sys.exit(1)

    # Prepare output directory
    output_path = args.output
    if safe_exists(output_path) and safe_is_file(output_path):
        error(f"Output path is a file, expected directory: {output_path}")
        sys.exit(1)

    if not safe_exists(output_path):
        safe_mkdir(output_path, parents=True, exist_ok=True)
        info(f"Created output directory: {output_path}")

    # Load conversion prompt
    prompt_path = Path(__file__).parent / "prompts" / "convert_html_to_md.md"
    if not safe_exists(prompt_path):
        error(f"Prompt file not found: {prompt_path}")
        sys.exit(1)

    prompt_template = safe_read_text(prompt_path)

    # Model parameter for Claude CLI (just use the short names)
    model_param = args.model

    # Process each HTML file
    converted_count = 0
    failed_count = 0

    for i, html_file in enumerate(html_files):
        tmp_html_path = None
        try:
            # Validate path to prevent traversal attacks
            validated_path = validate_path_traversal(
                html_file,
                base_path=(
                    source_path if safe_is_dir(source_path) else source_path.parent
                ),
                allow_outside=False,
            )

            # Read HTML content
            html_content = safe_read_text(validated_path, encoding="utf-8")

            # Determine output file path
            if safe_is_file(source_path):
                # Single file conversion
                output_file = output_path / html_file.with_suffix(".md").name
            else:
                # Directory conversion - maintain structure
                relative_path = html_file.relative_to(source_path)
                output_file = output_path / relative_path.with_suffix(".md")

            # Create output directory if needed
            output_file.parent.mkdir(parents=True, exist_ok=True)

            info(f"\n[{i+1}/{len(html_files)}] Converting: {html_file.name}")

            # Create a temporary file with the HTML content
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".html", delete=False, encoding="utf-8"
            ) as tmp_html:
                tmp_html.write(html_content)
                tmp_html_path = tmp_html.name

            # Prepare the prompt for the temporary file
            prompt = prompt_template.replace("{html_content}", f"@{tmp_html_path}")

            # Call Claude with the prompt referencing the file
            # Detect claude command location
            claude_cmd = "claude"
            claude_paths = [
                Path.home() / ".claude" / "local" / "claude",
                Path("/usr/local/bin/claude"),
                Path("/usr/bin/claude"),
            ]

            # Check if we need to use full path
            try:
                subprocess.run(["claude", "--version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Try to find claude in known locations
                for path in claude_paths:
                    if safe_exists(path) and safe_is_file(path):
                        claude_cmd = str(path)
                        break

            cmd = [claude_cmd, "-p", prompt, "--model", model_param]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Save the markdown output
            markdown_content = result.stdout.strip()
            output_file.write_text(markdown_content, encoding="utf-8")

            success(f"Converted to: {output_file}")
            converted_count += 1

            # Sleep between API calls (except for the last one)
            if i < len(html_files) - 1 and args.sleep > 0:
                info(f"Sleeping for {args.sleep} seconds...")
                time.sleep(args.sleep)

        except subprocess.CalledProcessError as e:
            error(f"Claude conversion failed: {e}")
            if e.stderr:
                error(f"Error: {e.stderr}")
            failed_count += 1
        except Exception as e:
            error(f"Error processing {html_file}: {e}")
            failed_count += 1
        finally:
            # Clean up temporary file
            if tmp_html_path:
                try:
                    Path(tmp_html_path).unlink()
                except:
                    pass

    # Summary
    header("Conversion Summary:")
    success(f"Successfully converted: {converted_count} files")
    if failed_count > 0:
        error(f"Failed to convert: {failed_count} files")

    if converted_count == 0:
        sys.exit(1)


def handle_config(args: argparse.Namespace) -> None:
    """Handle config command."""
    from .config import Config

    # Create default configuration
    config = Config(source=Path("./html"), destination=Path("./markdown"))

    # Generate config file
    config_dict = config.model_dump()

    if args.format == "yaml":
        import yaml

        content = yaml.dump(config_dict, default_flow_style=False, sort_keys=False)
    elif args.format == "toml":
        import toml

        content = toml.dumps(config_dict)
    elif args.format == "json":
        import json

        content = json.dumps(config_dict, indent=2)
    else:
        error(f"Unsupported format: {args.format}")
        sys.exit(1)

    # Write config file
    args.output.write_text(content, encoding="utf-8")
    success(f"Created configuration file: {args.output}")


def create_simple_parser() -> argparse.ArgumentParser:
    """Create a simple parser for test compatibility."""
    parser = argparse.ArgumentParser(
        prog="m1f-html2md", description="Convert HTML to Markdown"
    )

    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument("--source-dir", type=str, help="Source directory or URL")
    parser.add_argument("--destination-dir", type=Path, help="Destination directory")
    parser.add_argument(
        "--outermost-selector", type=str, help="CSS selector for content"
    )
    parser.add_argument("--ignore-selectors", nargs="+", help="CSS selectors to ignore")
    parser.add_argument("--include-patterns", nargs="+", help="Patterns to include")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    return parser


def main() -> None:
    """Main entry point."""
    # Check if running in simple mode (for tests) - but NOT for --help or --version
    if len(sys.argv) > 1 and sys.argv[1] in ["--source-dir"]:
        parser = create_simple_parser()
        args = parser.parse_args()

        if args.source_dir and args.destination_dir:
            # Simple conversion mode
            from .config import ConversionOptions

            options = ConversionOptions(
                source_dir=args.source_dir,
                destination_dir=args.destination_dir,
                outermost_selector=args.outermost_selector,
                ignore_selectors=args.ignore_selectors,
            )
            converter = Html2mdConverter(options)

            # For URL sources, convert them
            if args.source_dir.startswith("http"):
                info(f"Converting {args.source_dir}")

                # Handle include patterns if specified
                if args.include_patterns:
                    # Convert specific pages
                    import asyncio

                    urls = [
                        f"{args.source_dir}/{pattern}"
                        for pattern in args.include_patterns
                    ]
                    results = asyncio.run(converter.convert_directory_from_urls(urls))
                    info(f"Converted {len(results)} pages")
                else:
                    # Convert single URL
                    output_path = converter.convert_url(args.source_dir)
                    info(f"Converted to {output_path}")

                success("Conversion completed successfully")
            sys.exit(0)
        sys.exit(0)

    # Regular mode with subcommands
    parser = create_parser()
    args = parser.parse_args()

    # Handle no command
    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Configure console
    if args.quiet:
        # console.quiet - removed
        pass

    # Dispatch to command handlers
    try:
        if args.command == "convert":
            handle_convert(args)
        elif args.command == "analyze":
            handle_analyze(args)
        elif args.command == "config":
            handle_config(args)
        else:
            error(f"Unknown command: {args.command}")
            sys.exit(1)

    except KeyboardInterrupt:
        warning("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        error(f"Error: {e}")
        if args.verbose:
            import traceback

            info(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
