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

from rich.console import Console

from . import __version__
from .api import Html2mdConverter
from .config import Config, OutputFormat

console = Console()


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="m1f-html2md",
        description="Convert HTML files to Markdown format with advanced options and optional Claude AI integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a single file
  m1f-html2md convert file.html -o file.md
  
  # Convert entire directory
  m1f-html2md convert ./docs/html/ -o ./docs/markdown/
  
  # Use configuration file
  m1f-html2md convert ./html/ -c config.yaml
  
  # Extract specific content
  m1f-html2md convert ./html/ -o ./md/ --content-selector "article.post"
  
  # Analyze HTML structure with AI assistance
  m1f-html2md analyze ./html/ --claude
  
  # Convert HTML to clean Markdown using AI
  m1f-html2md convert ./html/ -o ./markdown/ --claude --model opus
""",
    )

    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    # Global options
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress all output except errors"
    )

    parser.add_argument("--log-file", type=Path, help="Log to file")

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Convert command
    convert_parser = subparsers.add_parser(
        "convert", help="Convert HTML files to Markdown (supports Claude AI with --claude)"
    )
    add_convert_arguments(convert_parser)

    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze HTML structure for selector suggestions (supports Claude AI with --claude)"
    )
    add_analyze_arguments(analyze_parser)

    # Config command
    config_parser = subparsers.add_parser("config", help="Generate configuration file")
    add_config_arguments(config_parser)

    return parser


def add_convert_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for convert command."""
    parser.add_argument("source", type=Path, help="Source file or directory")

    parser.add_argument(
        "-o", "--output", type=Path, required=True, help="Output file or directory"
    )

    parser.add_argument("-c", "--config", type=Path, help="Configuration file")

    parser.add_argument(
        "--format",
        choices=["markdown", "m1f_bundle", "json"],
        default="markdown",
        help="Output format",
    )

    # Content extraction options
    parser.add_argument("--content-selector", help="CSS selector for main content")

    parser.add_argument("--ignore-selectors", nargs="+", help="CSS selectors to ignore")

    parser.add_argument(
        "--heading-offset", type=int, default=0, help="Offset heading levels"
    )

    parser.add_argument(
        "--no-frontmatter", action="store_true", help="Don't add YAML frontmatter"
    )

    parser.add_argument(
        "--parallel", action="store_true", help="Enable parallel processing"
    )

    parser.add_argument(
        "--extractor", type=Path, help="Path to custom extractor Python file"
    )
    
    # Claude AI conversion options
    parser.add_argument(
        "--claude", 
        action="store_true", 
        help="Use Claude AI to convert HTML to Markdown (content only, no headers/navigation)"
    )
    
    parser.add_argument(
        "--model",
        choices=["opus", "sonnet"],
        default="sonnet",
        help="Claude model to use (default: sonnet)"
    )
    
    parser.add_argument(
        "--sleep",
        type=float,
        default=1.0,
        help="Sleep time in seconds between Claude API calls (default: 1.0)"
    )


def add_analyze_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for analyze command."""
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="HTML files or directories to analyze (automatically finds all HTML files in directories)",
    )

    parser.add_argument(
        "--show-structure", action="store_true", help="Show detailed HTML structure"
    )

    parser.add_argument(
        "--common-patterns",
        action="store_true",
        help="Find common patterns across files",
    )

    parser.add_argument(
        "--suggest-selectors",
        action="store_true",
        help="Suggest CSS selectors for content extraction",
    )
    
    parser.add_argument(
        "--claude",
        action="store_true",
        help="Use Claude AI to intelligently select representative files and suggest selectors",
    )


def add_config_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for config command."""
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("config.yaml"),
        help="Output configuration file",
    )

    parser.add_argument(
        "--format",
        choices=["yaml", "toml", "json"],
        default="yaml",
        help="Configuration format",
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
        with open(args.config, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # If the config only contains extractor settings (from Claude analysis),
        # create a full config with source and destination from CLI
        if 'source' not in config_data and 'destination' not in config_data:
            source_path = args.source.parent if args.source.is_file() else args.source
            config = Config(source=source_path, destination=args.output)
            
            # Apply extractor settings from the config file
            if 'extractor' in config_data:
                for key, value in config_data['extractor'].items():
                    if hasattr(config.extractor, key):
                        setattr(config.extractor, key, value)
        else:
            # Full config file - load it normally
            config = load_config(args.config)
    else:
        # When source is a file, use its parent directory as the source
        source_path = args.source.parent if args.source.is_file() else args.source
        config = Config(source=source_path, destination=args.output)

    # Update config with CLI arguments
    if args.content_selector:
        config.extractor.content_selector = args.content_selector

    if args.ignore_selectors:
        config.extractor.ignore_selectors = args.ignore_selectors

    if args.heading_offset:
        config.processor.heading_offset = args.heading_offset

    if args.no_frontmatter:
        config.processor.add_frontmatter = False

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
    if args.source.is_file():
        console.print(f"Converting file: {args.source}")
        output = converter.convert_file(args.source)
        console.print(f"✅ Converted to: {output}", style="green")

    elif args.source.is_dir():
        console.print(f"Converting directory: {args.source}")
        outputs = converter.convert_directory()
        console.print(f"✅ Converted {len(outputs)} files", style="green")

    else:
        console.print(f"❌ Source not found: {args.source}", style="red")
        sys.exit(1)


def handle_analyze(args: argparse.Namespace) -> None:
    """Handle analyze command."""
    from bs4 import BeautifulSoup
    from collections import Counter
    import json

    # Collect all HTML files from provided paths
    html_files = []
    for path in args.paths:
        if not path.exists():
            console.print(f"❌ Path not found: {path}", style="red")
            continue
        
        if path.is_file():
            # Single file
            if path.suffix.lower() in ['.html', '.htm']:
                html_files.append(path)
            else:
                console.print(f"⚠️  Skipping non-HTML file: {path}", style="yellow")
        elif path.is_dir():
            # Directory - find all HTML files recursively
            found_files = list(path.rglob("*.html")) + list(path.rglob("*.htm"))
            if found_files:
                html_files.extend(found_files)
                console.print(f"Found {len(found_files)} HTML files in {path}", style="blue")
            else:
                console.print(f"⚠️  No HTML files found in {path}", style="yellow")
    
    if not html_files:
        console.print("❌ No HTML files to analyze", style="red")
        sys.exit(1)
    
    # If --claude flag is set, use Claude AI for analysis
    if args.claude:
        console.print(f"\nFound {len(html_files)} HTML files total")
        _handle_claude_analysis(html_files)
        return
    
    # Otherwise, do local analysis
    console.print(f"\nAnalyzing {len(html_files)} HTML files...")

    # Read and parse all files
    parsed_files = []
    for file_path in html_files:
        try:
            content = file_path.read_text(encoding="utf-8")
            soup = BeautifulSoup(content, "html.parser")
            parsed_files.append((file_path, soup))
            # Show relative path from current directory for better identification
            try:
                relative_path = file_path.relative_to(Path.cwd())
            except ValueError:
                relative_path = file_path
            console.print(f"✅ Parsed: {relative_path}", style="green")
        except Exception as e:
            console.print(f"❌ Error parsing {file_path}: {e}", style="red")

    if not parsed_files:
        console.print("No files could be parsed", style="red")
        sys.exit(1)

    # Analyze structure
    if args.show_structure:
        console.print("\n[bold]HTML Structure Analysis:[/bold]")
        for file_path, soup in parsed_files:
            console.print(f"\n[blue]{file_path.name}:[/blue]")
            _show_structure(soup)

    # Find common patterns
    if args.common_patterns:
        console.print("\n[bold]Common Patterns:[/bold]")
        _find_common_patterns(parsed_files)

    # Suggest selectors
    if args.suggest_selectors or (not args.show_structure and not args.common_patterns):
        console.print("\n[bold]Suggested CSS Selectors:[/bold]")
        suggestions = _suggest_selectors(parsed_files)

        console.print("\n[yellow]Content selectors:[/yellow]")
        for selector, confidence in suggestions["content"]:
            console.print(f"  {selector} (confidence: {confidence:.0%})")

        console.print("\n[yellow]Elements to ignore:[/yellow]")
        for selector in suggestions["ignore"]:
            console.print(f"  {selector}")

        # Print example configuration
        console.print("\n[bold]Example configuration:[/bold]")
        console.print("```yaml")
        console.print("extractor:")
        if suggestions["content"]:
            console.print(f"  content_selector: \"{suggestions['content'][0][0]}\"")
        console.print("  ignore_selectors:")
        for selector in suggestions["ignore"]:
            console.print(f'    - "{selector}"')
        console.print("```")


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
        console.print(f"  <{area.name} {attr_str}>")

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
                console.print(f"    <{child.name} {child_attr_str}>")


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
    console.print("\n[yellow]Most common classes:[/yellow]")
    for cls, count in all_classes.most_common(10):
        console.print(f"  .{cls} (found {count} times)")

    console.print("\n[yellow]Most common IDs:[/yellow]")
    for id_name, count in all_ids.most_common(10):
        console.print(f"  #{id_name} (found {count} times)")

    console.print("\n[yellow]Common structural elements:[/yellow]")
    for tag, count in tag_patterns.most_common():
        console.print(f"  <{tag}> (found {count} times)")


def _handle_claude_analysis(html_files):
    """Handle analysis using Claude AI."""
    import subprocess
    import os
    import tempfile
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from m1f.utils import validate_path_traversal
    
    console.print("\n[bold]Using Claude AI for intelligent analysis...[/bold]")
    
    # Find the common parent directory of all HTML files
    if html_files:
        common_parent = Path(os.path.commonpath([str(f.absolute()) for f in html_files]))
        console.print(f"Analysis directory: {common_parent}")
        console.print(f"Total files to analyze: {len(html_files)}")
    else:
        console.print("❌ No HTML files to analyze", style="red")
        return
    
    # Save current directory
    original_dir = Path.cwd()
    
    try:
        # Change to the common parent directory
        os.chdir(common_parent)
        console.print(f"Changed to directory: {common_parent}")
        
        # Get relative paths from the common parent
        relative_paths = []
        for f in html_files:
            try:
                rel_path = f.relative_to(common_parent)
                relative_paths.append(str(rel_path))
            except ValueError:
                relative_paths.append(str(f))
        
        # Step 1: Load the file selection prompt
        prompt_dir = Path(__file__).parent / "prompts"
        select_prompt_path = prompt_dir / "select_files_prompt.md"
        
        if not select_prompt_path.exists():
            console.print(f"❌ Prompt file not found: {select_prompt_path}", style="red")
            return
        
        select_prompt = select_prompt_path.read_text()
        file_list = "\n".join(relative_paths)
        select_prompt = select_prompt.replace("{file_list}", file_list)
        
        console.print("\nAsking Claude to select representative files...")
        
        # Load the simple select prompt
        simple_prompt_path = prompt_dir / "select_files_simple.md"
        if not simple_prompt_path.exists():
            console.print(f"❌ Simple prompt file not found: {simple_prompt_path}", style="red")
            return
        
        simple_prompt = simple_prompt_path.read_text()
        simple_prompt = simple_prompt.replace("{file_list}", file_list)
        
        try:
            # Run claude with prompt directly
            cmd = [
                "claude",
                "-p", simple_prompt
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            selected_files = result.stdout.strip().split('\n')
            selected_files = [f.strip() for f in selected_files if f.strip()]
            
            console.print(f"\nClaude selected {len(selected_files)} files:")
            for f in selected_files:
                console.print(f"  - {f}", style="blue")
            
        except subprocess.CalledProcessError as e:
            console.print(f"❌ Claude command failed: {e}", style="red")
            console.print(f"Error output: {e.stderr}", style="red")
            return
        except FileNotFoundError:
            console.print("❌ claude command not found. Please install Claude CLI.", style="red")
            return
        
        # Step 2: Read the selected HTML files
        console.print("\nReading selected HTML files...")
        html_contents = []
        for file_path in selected_files[:5]:  # Limit to 5 files
            # Claude might return paths with redundant directory prefixes
            # since we already changed to common_parent directory
            file_path = file_path.strip()
            
            # Try to find the file
            full_path = None
            
            # Method 1: Direct path from current directory (where m1f-init ran)
            if Path(file_path).exists():
                full_path = Path(file_path)
            # Method 2: Go back to original directory and try
            elif (original_dir / file_path).exists():
                full_path = original_dir / file_path
            # Method 3: Strip the leading directories that match our current location
            else:
                # If the path starts with parts of our current directory name, remove them
                path_parts = file_path.split('/')
                # Look for where the actual file path begins
                for i in range(len(path_parts)):
                    test_path = '/'.join(path_parts[i:])
                    if Path(test_path).exists():
                        full_path = Path(test_path)
                        break
                    elif (original_dir / test_path).exists():
                        full_path = original_dir / test_path
                        break
            
            if full_path and full_path.exists():
                try:
                    # Validate path to prevent traversal attacks
                    validated_path = validate_path_traversal(
                        full_path, 
                        base_path=original_dir,
                        allow_outside=False
                    )
                    content = validated_path.read_text(encoding='utf-8')
                    # Limit content size to avoid overwhelming the prompt
                    if len(content) > 10000:
                        content = content[:10000] + "\n... (truncated)"
                    html_contents.append(f"### File: {file_path}\n```html\n{content}\n```\n")
                    console.print(f"✅ Read: {file_path}", style="green")
                except ValueError as e:
                    # Path traversal attempt
                    console.print(f"❌ Security error for {file_path}: {e}", style="red")
                except Exception as e:
                    console.print(f"❌ Error reading {file_path}: {e}", style="red")
            else:
                console.print(f"❌ File not found: {file_path}", style="red")
                console.print(f"   Tried: {common_parent / file_path}", style="yellow")
        
        if not html_contents:
            console.print("❌ No HTML files could be read", style="red")
            return
        
        # Step 3: Load the analysis prompt
        analyze_prompt_path = prompt_dir / "analyze_html_prompt.md"
        if not analyze_prompt_path.exists():
            console.print(f"❌ Prompt file not found: {analyze_prompt_path}", style="red")
            return
        
        analyze_prompt = analyze_prompt_path.read_text()
        html_content_str = "\n".join(html_contents)
        analyze_prompt = analyze_prompt.replace("{html_content}", html_content_str)
        
        console.print("\nAsking Claude to analyze HTML structure and suggest selectors...")
        
        # Load the simple analyze prompt
        simple_analyze_path = prompt_dir / "analyze_html_simple.md"
        if not simple_analyze_path.exists():
            console.print(f"❌ Simple analyze prompt file not found: {simple_analyze_path}", style="red")
            return
        
        simple_analyze_prompt = simple_analyze_path.read_text()
        simple_analyze_prompt = simple_analyze_prompt.replace("{html_content}", html_content_str)
        
        try:
            # Run claude with prompt directly
            cmd = [
                "claude",
                "-p", simple_analyze_prompt
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            console.print("\n[bold]Claude's Analysis:[/bold]")
            console.print(result.stdout)
            
            # Try to parse the YAML config from Claude's output
            import yaml
            try:
                # Extract YAML from the output (between ```yaml and ```)
                output = result.stdout
                yaml_start = output.find("```yaml")
                yaml_end = output.find("```", yaml_start + 6)
                
                if yaml_start != -1 and yaml_end != -1:
                    yaml_content = output[yaml_start + 7:yaml_end].strip()
                    config_data = yaml.safe_load(yaml_content)
                    
                    # Clean up the config - remove empty strings
                    if 'extractor' in config_data:
                        extractor = config_data['extractor']
                        if 'alternative_selectors' in extractor:
                            extractor['alternative_selectors'] = [s for s in extractor['alternative_selectors'] if s]
                        if 'ignore_selectors' in extractor:
                            extractor['ignore_selectors'] = [s for s in extractor['ignore_selectors'] if s]
                    
                    # Save the config to a file
                    config_file = common_parent / "html2md_config.yaml"
                    with open(config_file, 'w') as f:
                        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
                    
                    console.print(f"\n✅ Saved configuration to: {config_file}", style="green")
                    
                    # Show the user how to use it
                    console.print("\n[bold]Next Step:[/bold]")
                    console.print(f"To convert your HTML files using this configuration, run:\n")
                    console.print(f"[cyan]m1f-html2md convert {common_parent} -o ./markdown -c {config_file}[/cyan]\n")
                    console.print("This will extract only the main content based on Claude's analysis.")
                    
                    console.print("\n[bold]Alternative:[/bold]")
                    console.print("For AI-powered conversion (extracts clean content automatically):")
                    console.print(f"[cyan]m1f-html2md convert {common_parent} -o ./markdown --claude[/cyan]")
                else:
                    console.print("\n⚠️  Could not extract YAML configuration from Claude's response", style="yellow")
                    console.print("You can manually create a config file based on the analysis above.")
                    
            except Exception as e:
                console.print(f"\n⚠️  Could not save configuration: {e}", style="yellow")
                console.print("You can manually create a config file based on the analysis above.")
            
        except subprocess.CalledProcessError as e:
            console.print(f"❌ Claude command failed: {e}", style="red")
            console.print(f"Error output: {e.stderr}", style="red")
            
    finally:
        # Change back to original directory
        os.chdir(original_dir)
        console.print(f"\nReturned to original directory: {original_dir}")


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
    
    console.print(f"\n[bold]Using Claude AI to convert HTML to Markdown...[/bold]")
    console.print(f"Model: {args.model}")
    console.print(f"Sleep between calls: {args.sleep} seconds")
    
    # Find all HTML files in source directory
    source_path = args.source
    if not source_path.exists():
        console.print(f"❌ Source path not found: {source_path}", style="red")
        sys.exit(1)
    
    html_files = []
    if source_path.is_file():
        if source_path.suffix.lower() in ['.html', '.htm']:
            html_files.append(source_path)
        else:
            console.print(f"❌ Source file is not HTML: {source_path}", style="red")
            sys.exit(1)
    elif source_path.is_dir():
        # Find all HTML files recursively
        html_files = list(source_path.rglob("*.html")) + list(source_path.rglob("*.htm"))
        console.print(f"Found {len(html_files)} HTML files in {source_path}")
    
    if not html_files:
        console.print("❌ No HTML files found to convert", style="red")
        sys.exit(1)
    
    # Prepare output directory
    output_path = args.output
    if output_path.exists() and output_path.is_file():
        console.print(f"❌ Output path is a file, expected directory: {output_path}", style="red")
        sys.exit(1)
    
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)
        console.print(f"Created output directory: {output_path}")
    
    # Load conversion prompt
    prompt_path = Path(__file__).parent / "prompts" / "convert_html_to_md.md"
    if not prompt_path.exists():
        console.print(f"❌ Prompt file not found: {prompt_path}", style="red")
        sys.exit(1)
    
    prompt_template = prompt_path.read_text()
    
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
                base_path=source_path if source_path.is_dir() else source_path.parent,
                allow_outside=False
            )
            
            # Read HTML content
            html_content = validated_path.read_text(encoding='utf-8')
            
            # Determine output file path
            if source_path.is_file():
                # Single file conversion
                output_file = output_path / html_file.with_suffix('.md').name
            else:
                # Directory conversion - maintain structure
                relative_path = html_file.relative_to(source_path)
                output_file = output_path / relative_path.with_suffix('.md')
            
            # Create output directory if needed
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            console.print(f"\n[{i+1}/{len(html_files)}] Converting: {html_file.name}")
            
            # Create a temporary file with the HTML content
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as tmp_html:
                tmp_html.write(html_content)
                tmp_html_path = tmp_html.name
            
            # Prepare the prompt for the temporary file
            prompt = prompt_template.replace("{html_content}", f"@{tmp_html_path}")
            
            # Call Claude with the prompt referencing the file
            cmd = [
                "claude",
                "-p", prompt,
                "--model", model_param
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Save the markdown output
            markdown_content = result.stdout.strip()
            output_file.write_text(markdown_content, encoding='utf-8')
            
            console.print(f"✅ Converted to: {output_file}", style="green")
            converted_count += 1
            
            # Sleep between API calls (except for the last one)
            if i < len(html_files) - 1 and args.sleep > 0:
                console.print(f"Sleeping for {args.sleep} seconds...", style="dim")
                time.sleep(args.sleep)
            
        except subprocess.CalledProcessError as e:
            console.print(f"❌ Claude conversion failed: {e}", style="red")
            if e.stderr:
                console.print(f"Error: {e.stderr}", style="red")
            failed_count += 1
        except Exception as e:
            console.print(f"❌ Error processing {html_file}: {e}", style="red")
            failed_count += 1
        finally:
            # Clean up temporary file
            if tmp_html_path:
                try:
                    Path(tmp_html_path).unlink()
                except:
                    pass
    
    # Summary
    console.print(f"\n[bold]Conversion Summary:[/bold]")
    console.print(f"✅ Successfully converted: {converted_count} files", style="green")
    if failed_count > 0:
        console.print(f"❌ Failed to convert: {failed_count} files", style="red")
    
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
        console.print(f"❌ Unsupported format: {args.format}", style="red")
        sys.exit(1)

    # Write config file
    args.output.write_text(content, encoding="utf-8")
    console.print(f"✅ Created configuration file: {args.output}", style="green")


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
                console.print(f"Converting {args.source_dir}")

                # Handle include patterns if specified
                if args.include_patterns:
                    # Convert specific pages
                    import asyncio

                    urls = [
                        f"{args.source_dir}/{pattern}"
                        for pattern in args.include_patterns
                    ]
                    results = asyncio.run(converter.convert_directory_from_urls(urls))
                    console.print(f"Converted {len(results)} pages")
                else:
                    # Convert single URL
                    output_path = converter.convert_url(args.source_dir)
                    console.print(f"Converted to {output_path}")

                console.print("Conversion completed successfully")
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
        console.quiet = True

    # Dispatch to command handlers
    try:
        if args.command == "convert":
            handle_convert(args)
        elif args.command == "analyze":
            handle_analyze(args)
        elif args.command == "config":
            handle_config(args)
        else:
            console.print(f"❌ Unknown command: {args.command}", style="red")
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n❌ Interrupted by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        if args.verbose:
            import traceback

            console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
