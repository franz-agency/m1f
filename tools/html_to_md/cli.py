#!/usr/bin/env python3
"""Command-line interface for HTML to Markdown converter."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from rich.console import Console

from . import __version__
from .api import HtmlToMarkdownConverter
from .config import Config, OutputFormat

console = Console()


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="html-to-md",
        description="Convert HTML files to Markdown format with advanced options",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a single file
  html-to-md convert file.html -o file.md
  
  # Convert entire directory
  html-to-md convert ./docs/html/ -o ./docs/markdown/
  
  # Convert a website
  html-to-md crawl https://example.com -o ./example-docs/
  
  # Use configuration file
  html-to-md convert ./html/ -c config.yaml
  
  # Extract specific content
  html-to-md convert ./html/ -o ./md/ --content-selector "article.post"
"""
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    # Global options
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress output"
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Write logs to file"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Convert command
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert HTML files to Markdown"
    )
    convert_parser.add_argument(
        "source",
        type=Path,
        help="Source file or directory"
    )
    convert_parser.add_argument(
        "-o", "--output",
        type=Path,
        required=True,
        help="Output file or directory"
    )
    convert_parser.add_argument(
        "-c", "--config",
        type=Path,
        help="Configuration file (YAML/TOML)"
    )
    
    # Content selection
    convert_parser.add_argument(
        "--content-selector",
        help="CSS selector for main content"
    )
    convert_parser.add_argument(
        "--ignore-selectors",
        nargs="+",
        help="CSS selectors to ignore"
    )
    
    # Processing options
    convert_parser.add_argument(
        "--heading-offset",
        type=int,
        default=0,
        help="Offset heading levels"
    )
    convert_parser.add_argument(
        "--no-frontmatter",
        action="store_true",
        help="Don't add YAML frontmatter"
    )
    
    # Output format
    convert_parser.add_argument(
        "--format",
        choices=["markdown", "m1f_bundle"],
        default="markdown",
        help="Output format"
    )
    
    # Crawl command
    crawl_parser = subparsers.add_parser(
        "crawl",
        help="Crawl and convert a website"
    )
    crawl_parser.add_argument(
        "url",
        help="Starting URL"
    )
    crawl_parser.add_argument(
        "-o", "--output",
        type=Path,
        required=True,
        help="Output directory"
    )
    crawl_parser.add_argument(
        "--max-depth",
        type=int,
        help="Maximum crawl depth"
    )
    crawl_parser.add_argument(
        "--max-pages",
        type=int,
        help="Maximum pages to crawl"
    )
    
    # Config command
    config_parser = subparsers.add_parser(
        "config",
        help="Generate configuration file"
    )
    config_parser.add_argument(
        "-o", "--output",
        type=Path,
        default="html-to-md.yaml",
        help="Output configuration file"
    )
    config_parser.add_argument(
        "--format",
        choices=["yaml", "toml", "json"],
        default="yaml",
        help="Configuration format"
    )
    
    return parser


def cmd_convert(args: argparse.Namespace) -> int:
    """Handle convert command."""
    # Build configuration
    config_dict = {
        "source": args.source,
        "destination": args.output,
        "verbose": args.verbose,
        "quiet": args.quiet,
    }
    
    if args.log_file:
        config_dict["log_file"] = args.log_file
    
    # Content extraction options
    if args.content_selector or args.ignore_selectors:
        config_dict["extractor"] = {}
        if args.content_selector:
            config_dict["extractor"]["content_selector"] = args.content_selector
        if args.ignore_selectors:
            config_dict["extractor"]["ignore_selectors"] = args.ignore_selectors
    
    # Processing options
    if args.heading_offset != 0:
        config_dict.setdefault("processor", {})["heading_offset"] = args.heading_offset
    
    # Output format
    if args.format == "m1f_bundle":
        config_dict["output_format"] = OutputFormat.M1F_BUNDLE
        config_dict.setdefault("m1f", {})["create_bundle"] = True
    
    # Load config file if provided
    if args.config:
        from .config import load_config
        config = load_config(args.config, config_dict)
    else:
        config = Config(**config_dict)
    
    # Create converter
    converter = HtmlToMarkdownConverter(config)
    
    # Convert based on source type
    if args.source.is_file():
        # Single file
        try:
            output = converter.convert_file(args.source)
            console.print(f"[green]✓[/green] Converted to {output}")
            return 0
        except Exception as e:
            console.print(f"[red]✗[/red] Error: {e}")
            return 1
    else:
        # Directory
        try:
            outputs = converter.convert_directory()
            console.print(f"[green]✓[/green] Converted {len(outputs)} files")
            
            # Generate m1f bundle if requested
            if config.output_format == OutputFormat.M1F_BUNDLE:
                bundle = converter.generate_m1f_bundle()
                console.print(f"[green]✓[/green] Created m1f bundle: {bundle}")
            
            return 0
        except Exception as e:
            console.print(f"[red]✗[/red] Error: {e}")
            return 1


def cmd_crawl(args: argparse.Namespace) -> int:
    """Handle crawl command."""
    config_dict = {
        "source": Path("."),  # Not used for crawling
        "destination": args.output,
        "verbose": args.verbose,
        "quiet": args.quiet,
        "crawler": {
            "follow_links": True,
            "max_depth": args.max_depth,
            "max_pages": args.max_pages,
        }
    }
    
    config = Config(**config_dict)
    converter = HtmlToMarkdownConverter(config)
    
    try:
        # Convert website (HTTrack runs synchronously)
        results = converter.convert_website(args.url)
        console.print(f"[green]✓[/green] Converted {len(results)} pages")
        return 0
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        return 1


def cmd_config(args: argparse.Namespace) -> int:
    """Handle config generation command."""
    # Create default config
    config = Config(
        source=Path("./html"),
        destination=Path("./markdown")
    )
    
    # Save config
    from .config import ConfigLoader
    loader = ConfigLoader()
    loader.config_data = config.model_dump()
    
    try:
        loader.save(args.output, format=args.format)
        console.print(f"[green]✓[/green] Created configuration file: {args.output}")
        return 0
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    if args.command == "convert":
        return cmd_convert(args)
    elif args.command == "crawl":
        return cmd_crawl(args)
    elif args.command == "config":
        return cmd_config(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 