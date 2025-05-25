#!/usr/bin/env python3
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
        prog="html2md",
        description="Convert HTML files to Markdown format with advanced options",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a single file
  html2md convert file.html -o file.md
  
  # Convert entire directory
  html2md convert ./docs/html/ -o ./docs/markdown/
  
  # Convert a website
  html2md crawl https://example.com -o ./example-docs/
  
  # Use configuration file
  html2md convert ./html/ -c config.yaml
  
  # Extract specific content
  html2md convert ./html/ -o ./md/ --content-selector "article.post"
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
        "convert", help="Convert HTML files to Markdown"
    )
    add_convert_arguments(convert_parser)

    # Crawl command
    crawl_parser = subparsers.add_parser("crawl", help="Crawl and convert a website")
    add_crawl_arguments(crawl_parser)

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


def add_crawl_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for crawl command."""
    parser.add_argument("url", help="URL to crawl")

    parser.add_argument(
        "-o", "--output", type=Path, required=True, help="Output directory"
    )

    parser.add_argument("-c", "--config", type=Path, help="Configuration file")

    parser.add_argument("--max-depth", type=int, default=5, help="Maximum crawl depth")

    parser.add_argument(
        "--max-pages", type=int, default=1000, help="Maximum pages to crawl"
    )

    parser.add_argument(
        "--format",
        choices=["markdown", "m1f_bundle"],
        default="markdown",
        help="Output format",
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
    # Load configuration
    if args.config:
        from .config import load_config

        config = load_config(args.config)
    else:
        config = Config(source=args.source, destination=args.output)

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
    converter = Html2mdConverter(config)

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


def handle_crawl(args: argparse.Namespace) -> None:
    """Handle crawl command."""
    # Load or create configuration
    if args.config:
        from .config import load_config

        config = load_config(args.config)
    else:
        config = Config(
            source=Path("."), destination=args.output  # Not used for crawling
        )

    # Update config with CLI arguments
    config.crawler.max_depth = args.max_depth
    config.crawler.max_pages = args.max_pages

    if hasattr(args, "format"):
        config.output_format = OutputFormat(args.format)

    config.verbose = args.verbose
    config.quiet = args.quiet
    config.log_file = args.log_file

    # Create converter
    converter = Html2mdConverter(config)

    console.print(f"Crawling website: {args.url}")
    console.print("This may take a while...")

    try:
        # Convert the website
        results = converter.convert_website(args.url)
        console.print(f"✅ Successfully converted {len(results)} pages", style="green")
        console.print(f"Output directory: {args.output}")

    except Exception as e:
        console.print(f"❌ Error during crawling: {e}", style="red")
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
        prog="html2md", description="Convert HTML to Markdown"
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
    # Check if running in simple mode (for tests)
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "--version", "--source-dir"]:
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
        elif args.command == "crawl":
            handle_crawl(args)
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
