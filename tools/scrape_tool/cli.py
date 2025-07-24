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

"""Command-line interface for m1f-scrape."""

import argparse
import logging
import sqlite3
import sys
from pathlib import Path
from typing import Optional

# Use unified colorama module
from ..shared.colors import Colors, success, error, warning, info, header, COLORAMA_AVAILABLE

from . import __version__
from .config import Config, ScraperBackend
from .crawlers import WebCrawler


def show_database_info(db_path: Path, args: argparse.Namespace) -> None:
    """Show information from the scrape tracker database.

    Args:
        db_path: Path to the SQLite database
        args: Command line arguments
    """
    if not db_path.exists():
        warning(
            "No database found. Have you scraped anything yet?"
        )
        return

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        if args.show_db_stats:
            # Show statistics
            cursor.execute("SELECT COUNT(*) FROM scraped_urls")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM scraped_urls WHERE error IS NULL")
            successful = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM scraped_urls WHERE error IS NOT NULL")
            errors = cursor.fetchone()[0]

            header("Scraping Statistics:")
            info(f"Total URLs processed: {total}")
            info(f"Successfully scraped: {successful}")
            info(f"Errors encountered: {errors}")

            if total > 0:
                success_rate = (successful / total) * 100
                info(f"Success rate: {success_rate:.1f}%")

        if args.show_errors:
            # Show URLs with errors
            cursor.execute(
                "SELECT url, error FROM scraped_urls WHERE error IS NOT NULL"
            )
            errors = cursor.fetchall()

            if errors:
                header("URLs with Errors:")
                for url, error in errors:
                    info(f"{Colors.RED}✗{Colors.RESET} {url}")
                    info(f"    Error: {error}")
            else:
                success("No errors found!")

        if args.show_scraped_urls:
            # Show all scraped URLs
            cursor.execute(
                "SELECT url, status_code FROM scraped_urls ORDER BY scraped_at"
            )
            urls = cursor.fetchall()

            if urls:
                header("Scraped URLs:")
                for url, status_code in urls:
                    status_icon = (
                        "[green]✓[/green]"
                        if status_code == 200
                        else f"[yellow]{status_code}[/yellow]"
                    )
                    info(f"{status_icon} {url}")
            else:
                warning("No URLs found in database")

        conn.close()

    except sqlite3.Error as e:
        error(f"Database error: {e}")
    except Exception as e:
        error(f"Error reading database: {e}")


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="m1f-scrape",
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
    parser.add_argument(
        "url", nargs="?", help="URL to scrape (not needed for database queries)"
    )
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
        default=15.0,
        help="Delay between requests in seconds (default: 15.0 for Cloudflare protection)",
    )

    parser.add_argument(
        "--concurrent-requests",
        type=int,
        default=2,
        help="Number of concurrent requests (default: 2 for Cloudflare protection)",
    )

    parser.add_argument("--user-agent", type=str, help="Custom user agent string")

    parser.add_argument(
        "--ignore-get-params",
        action="store_true",
        help="Ignore GET parameters in URLs (e.g., ?tab=linux) to avoid duplicate content",
    )

    parser.add_argument(
        "--ignore-canonical",
        action="store_true",
        help="Ignore canonical URL tags (by default, pages with different canonical URLs are skipped)",
    )

    parser.add_argument(
        "--ignore-duplicates",
        action="store_true",
        help="Ignore duplicate content detection (by default, pages with identical text are skipped)",
    )

    # Output options
    parser.add_argument(
        "--list-files",
        action="store_true",
        help="List all downloaded files after completion",
    )

    # Database query options
    parser.add_argument(
        "--show-db-stats",
        action="store_true",
        help="Show scraping statistics from the database",
    )
    parser.add_argument(
        "--show-errors",
        action="store_true",
        help="Show URLs that had errors during scraping",
    )
    parser.add_argument(
        "--show-scraped-urls",
        action="store_true",
        help="List all scraped URLs from the database",
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

    config.crawler.ignore_get_params = args.ignore_get_params
    config.crawler.check_canonical = not args.ignore_canonical
    config.crawler.check_content_duplicates = not args.ignore_duplicates

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

    # Set up logging
    if args.verbose:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
    elif not args.quiet:
        logging.basicConfig(
            level=logging.WARNING, format="%(asctime)s - %(levelname)s - %(message)s"
        )

    # Check if only database query options are requested
    if args.show_db_stats or args.show_errors or args.show_scraped_urls:
        # Just show database info and exit
        db_path = args.output / "scrape_tracker.db"
        show_database_info(db_path, args)
        return

    # URL is required for scraping
    if not args.url:
        parser.error("URL is required for scraping")

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    info(f"Scraping website: {args.url}")
    info(f"Using scraper backend: {args.scraper}")
    info("This may take a while...")
    info("Press Ctrl+C to interrupt and resume later\n")

    try:
        # Create crawler and download the website
        crawler = WebCrawler(config.crawler)
        site_dir = crawler.crawl_sync(args.url, args.output)

        # Find all downloaded HTML files
        html_files = crawler.find_downloaded_files(site_dir)

        success(
            f"Successfully downloaded {len(html_files)} HTML files"
        )
        info(f"Output directory: {site_dir}")

        # List downloaded files if requested
        if args.list_files or config.verbose:
            info("\nDownloaded files:")
            for html_file in sorted(html_files):
                rel_path = html_file.relative_to(site_dir)
                info(f"  - {rel_path}")

    except KeyboardInterrupt:
        warning("⚠️  Scraping interrupted by user")
        info(
            "Run the same command again to resume where you left off"
        )
        sys.exit(0)
    except Exception as e:
        error(f"Error during scraping: {e}")
        if config.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
