"""Command-line interface for webscraper."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console

from . import __version__
from .config import Config, ScraperBackend
from .crawlers import WebCrawler

console = Console()


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="webscraper",
        description="Download websites for offline viewing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
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

    # Main arguments
    parser.add_argument("url", help="URL to scrape")
    parser.add_argument(
        "-o", "--output", type=Path, required=True, help="Output directory"
    )

    # Scraper options
    parser.add_argument(
        "--scraper",
        type=str,
        choices=[
            "httrack",
            "beautifulsoup",
            "bs4",
            "selectolax",
            "httpx",
            "scrapy",
            "playwright",
        ],
        default="beautifulsoup",
        help="Web scraper backend to use (default: beautifulsoup)",
    )

    parser.add_argument(
        "--scraper-config",
        type=Path,
        help="Path to scraper-specific configuration file (YAML/JSON)",
    )

    # Crawl options
    parser.add_argument("--max-depth", type=int, default=5, help="Maximum crawl depth")
    parser.add_argument(
        "--max-pages", type=int, default=1000, help="Maximum pages to crawl"
    )

    # Request options
    parser.add_argument(
        "--request-delay",
        type=float,
        default=0.5,
        help="Delay between requests in seconds (default: 0.5)",
    )

    parser.add_argument(
        "--concurrent-requests",
        type=int,
        default=5,
        help="Number of concurrent requests (default: 5)",
    )

    parser.add_argument("--user-agent", type=str, help="Custom user agent string")

    # Output options
    parser.add_argument(
        "--list-files",
        action="store_true",
        help="List all downloaded files after completion",
    )

    return parser


def main() -> None:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Create configuration
    config = Config()
    config.crawler.max_depth = args.max_depth
    config.crawler.max_pages = args.max_pages
    config.crawler.scraper_backend = ScraperBackend(args.scraper)
    config.crawler.request_delay = args.request_delay
    config.crawler.concurrent_requests = args.concurrent_requests
    config.crawler.respect_robots_txt = True  # Always respect robots.txt

    if args.user_agent:
        config.crawler.user_agent = args.user_agent

    # Load scraper-specific config if provided
    if args.scraper_config:
        import yaml
        import json

        if args.scraper_config.suffix == ".json":
            with open(args.scraper_config) as f:
                config.crawler.scraper_config = json.load(f)
        else:  # Assume YAML
            with open(args.scraper_config) as f:
                config.crawler.scraper_config = yaml.safe_load(f)

    config.verbose = args.verbose
    config.quiet = args.quiet

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    console.print(f"Scraping website: {args.url}")
    console.print(f"Using scraper backend: {args.scraper}")
    console.print("This may take a while...")

    try:
        # Create crawler and download the website
        crawler = WebCrawler(config.crawler)
        site_dir = crawler.crawl_sync(args.url, args.output)

        # Find all downloaded HTML files
        html_files = crawler.find_downloaded_files(site_dir)

        console.print(
            f"✅ Successfully downloaded {len(html_files)} HTML files", style="green"
        )
        console.print(f"Output directory: {site_dir}")

        # List downloaded files if requested
        if args.list_files or config.verbose:
            console.print("\nDownloaded files:")
            for html_file in sorted(html_files):
                rel_path = html_file.relative_to(site_dir)
                console.print(f"  - {rel_path}")

    except Exception as e:
        console.print(f"❌ Error during scraping: {e}", style="red")
        if config.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
