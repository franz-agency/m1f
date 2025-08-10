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
import time
from pathlib import Path
from typing import Optional

# Use unified colorama module
try:
    from ..shared.colors import (
        Colors,
        success,
        error,
        warning,
        info,
        header,
        COLORAMA_AVAILABLE,
        ColoredHelpFormatter,
    )
except ImportError:
    COLORAMA_AVAILABLE = False

    # Fallback formatter
    class ColoredHelpFormatter(argparse.RawDescriptionHelpFormatter):
        pass


from . import __version__
from .config import Config, ScraperBackend
from .crawlers import WebCrawler


class CustomArgumentParser(argparse.ArgumentParser):
    """Custom argument parser with better error messages."""

    def error(self, message: str) -> None:
        """Display error message with colors if available."""
        error_msg = f"ERROR: {message}"
        if COLORAMA_AVAILABLE:
            error_msg = f"{Colors.RED}ERROR: {message}{Colors.RESET}"
        self.print_usage(sys.stderr)
        print(f"\n{error_msg}", file=sys.stderr)
        print(f"\nFor detailed help, use: {self.prog} --help", file=sys.stderr)
        self.exit(2)


def cleanup_orphaned_sessions(db_path: Path) -> None:
    """Clean up sessions that were left in 'running' state.
    
    Args:
        db_path: Path to the SQLite database
    """
    if not db_path.exists():
        warning("No database found.")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if scraping_sessions table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='scraping_sessions'"
        )
        if not cursor.fetchone():
            warning("No sessions table found in database")
            conn.close()
            return
        
        # Find all running sessions
        cursor.execute(
            """
            SELECT id, start_url, start_time 
            FROM scraping_sessions 
            WHERE status = 'running'
            ORDER BY start_time DESC
            """
        )
        
        running_sessions = cursor.fetchall()
        
        if not running_sessions:
            info("No running sessions found")
            conn.close()
            return
        
        # Check which sessions are truly orphaned (no activity in last hour)
        from datetime import datetime, timedelta
        one_hour_ago = datetime.now() - timedelta(hours=1)
        orphaned_sessions = []
        active_sessions = []
        
        header(f"Found {len(running_sessions)} running session(s):")
        for session_id, start_url, start_time in running_sessions:
            # Get last activity time
            cursor.execute(
                """
                SELECT MAX(scraped_at), COUNT(*), 
                       COUNT(CASE WHEN error IS NULL THEN 1 END)
                FROM scraped_urls 
                WHERE session_id = ?
                """,
                (session_id,)
            )
            result = cursor.fetchone()
            last_activity, total, successful = result if result else (None, 0, 0)
            
            # Use start_time if no URLs scraped yet
            last_activity = last_activity or start_time
            
            # Convert string timestamp to datetime if needed
            if isinstance(last_activity, str):
                last_activity_dt = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
            else:
                last_activity_dt = last_activity
            
            is_orphaned = last_activity_dt < one_hour_ago
            
            info(f"  Session #{session_id}: {start_url}")
            info(f"    Started: {start_time}")
            info(f"    Last activity: {last_activity}")
            info(f"    Pages scraped: {successful}/{total}")
            
            if is_orphaned:
                info(f"    Status: ORPHANED (no activity for >1 hour)")
                orphaned_sessions.append((session_id, start_url, start_time))
            else:
                info(f"    Status: ACTIVE (recent activity)")
                active_sessions.append(session_id)
        
        if not orphaned_sessions:
            if active_sessions:
                info(f"\nAll {len(active_sessions)} session(s) appear to be actively running.")
            info("No orphaned sessions found.")
            conn.close()
            return
        
        # Ask for confirmation only for orphaned sessions
        info(f"\n{len(orphaned_sessions)} session(s) appear to be orphaned (no activity for >1 hour).")
        if active_sessions:
            info(f"{len(active_sessions)} session(s) are still active and will not be touched.")
        response = input("Mark orphaned sessions as 'interrupted'? (y/N): ")
        
        if response.lower() == 'y':
            for session_id, _, _ in orphaned_sessions:  # Only process orphaned sessions
                # Get final statistics
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN error IS NULL THEN 1 END) as successful,
                        COUNT(CASE WHEN error IS NOT NULL THEN 1 END) as failed
                    FROM scraped_urls 
                    WHERE session_id = ?
                    """,
                    (session_id,)
                )
                result = cursor.fetchone()
                total, successful, failed = result if result else (0, 0, 0)
                
                # Update session
                cursor.execute(
                    """
                    UPDATE scraping_sessions 
                    SET status = 'interrupted',
                        end_time = ?,
                        total_pages = ?,
                        successful_pages = ?,
                        failed_pages = ?
                    WHERE id = ?
                    """,
                    (datetime.now(), total, successful, failed, session_id)
                )
            
            conn.commit()
            success(f"Marked {len(orphaned_sessions)} orphaned session(s) as interrupted")
        else:
            info("No changes made")
        
        conn.close()
        
    except sqlite3.Error as e:
        error(f"Database error: {e}")
    except Exception as e:
        error(f"Error cleaning up sessions: {e}")


def show_scraping_sessions(db_path: Path, detailed: bool = False) -> None:
    """Show all scraping sessions from the database.
    
    Args:
        db_path: Path to the SQLite database
        detailed: If True, show detailed session information
    """
    if not db_path.exists():
        warning("No database found.")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if scraping_sessions table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='scraping_sessions'"
        )
        if not cursor.fetchone():
            # Fall back to old behavior if no sessions table
            cursor.execute("""
                SELECT 
                    DATE(scraped_at) as session_date,
                    MIN(TIME(scraped_at)) as start_time,
                    MAX(TIME(scraped_at)) as end_time,
                    COUNT(*) as url_count,
                    COUNT(CASE WHEN error IS NULL THEN 1 END) as successful,
                    COUNT(CASE WHEN error IS NOT NULL THEN 1 END) as failed
                FROM scraped_urls
                GROUP BY DATE(scraped_at)
                ORDER BY session_date DESC
            """)
            
            sessions = cursor.fetchall()
            
            if sessions:
                header("Scraping Sessions (Legacy):")
                info("Date       | Start    | End      | Total URLs | Success | Failed")
                info("-" * 70)
                for session in sessions:
                    date, start, end, total, success_count, failed = session
                    info(f"{date} | {start[:8] if start else 'N/A'} | {end[:8] if end else 'N/A'} | {total:10} | {success_count:7} | {failed:6}")
            else:
                warning("No scraping sessions found in database")
        else:
            # Use new sessions table
            cursor.execute("""
                SELECT 
                    id,
                    start_url,
                    start_time,
                    end_time,
                    status,
                    total_pages,
                    successful_pages,
                    failed_pages,
                    scraper_backend,
                    max_pages,
                    max_depth
                FROM scraping_sessions
                ORDER BY start_time DESC
            """)
            
            sessions = cursor.fetchall()
            
            if sessions:
                header("Scraping Sessions:")
                if detailed:
                    for session in sessions:
                        (session_id, start_url, start_time, end_time, status,
                         total, successful, failed, backend, max_pages, max_depth) = session
                        
                        info(f"\nSession #{session_id}:")
                        info(f"  URL: {start_url}")
                        info(f"  Started: {start_time}")
                        info(f"  Ended: {end_time if end_time else 'Still running'}")
                        info(f"  Status: {status}")
                        info(f"  Backend: {backend}")
                        info(f"  Pages: {successful} success, {failed} failed (total: {total})")
                        info(f"  Limits: max_pages={max_pages}, max_depth={max_depth}")
                else:
                    info("ID  | Status    | Started             | Pages | Success | Failed | URL")
                    info("-" * 100)
                    for session in sessions:
                        (session_id, start_url, start_time, end_time, status,
                         total, successful, failed, backend, _, _) = session
                        
                        # Truncate URL if too long
                        url_display = start_url[:40] + "..." if len(start_url) > 40 else start_url
                        
                        info(f"{session_id:3} | {status:9} | {start_time[:19]} | {total:5} | {successful:7} | {failed:6} | {url_display}")
            else:
                warning("No scraping sessions found in database")
        
        conn.close()
        
    except sqlite3.Error as e:
        error(f"Database error: {e}")
    except Exception as e:
        error(f"Error showing sessions: {e}")


def clear_session(db_path: Path, session_id: Optional[int] = None, delete_files: bool = False, auto_delete: bool = False) -> None:
    """Clear URLs from a specific scraping session or the last session.
    
    Args:
        db_path: Path to the SQLite database
        session_id: Specific session ID to clear, or None for the last session
        delete_files: Whether to also delete downloaded files
        auto_delete: If True, skip confirmation prompt for file deletion
    """
    if not db_path.exists():
        warning("No database found.")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if scraping_sessions table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='scraping_sessions'"
        )
        has_sessions_table = cursor.fetchone() is not None
        
        if has_sessions_table:
            # Use session-based deletion
            if session_id is None:
                # Find the most recent session
                cursor.execute(
                    "SELECT id FROM scraping_sessions ORDER BY start_time DESC LIMIT 1"
                )
                result = cursor.fetchone()
                if not result:
                    warning("No scraping sessions found in database")
                    conn.close()
                    return
                session_id = result[0]
            
            # Get session info
            cursor.execute(
                "SELECT start_url, start_time FROM scraping_sessions WHERE id = ?",
                (session_id,)
            )
            session_info = cursor.fetchone()
            if not session_info:
                warning(f"Session #{session_id} not found")
                conn.close()
                return
            
            start_url, start_time = session_info
            
            # Get file paths from this session
            cursor.execute(
                """SELECT target_filename 
                   FROM scraped_urls 
                   WHERE session_id = ? AND target_filename IS NOT NULL AND target_filename != ''""",
                (session_id,)
            )
            file_paths = [row[0] for row in cursor.fetchall()]
            
            # Get checksums of URLs from this session
            cursor.execute(
                """SELECT content_checksum 
                   FROM scraped_urls 
                   WHERE session_id = ? AND content_checksum IS NOT NULL""",
                (session_id,)
            )
            checksums = [row[0] for row in cursor.fetchall()]
            
            # Count URLs to be deleted
            cursor.execute(
                "SELECT COUNT(*) FROM scraped_urls WHERE session_id = ?",
                (session_id,)
            )
            url_count = cursor.fetchone()[0]
            
            # Handle file deletion if requested
            files_deleted = 0
            if delete_files and file_paths:
                # Build list of actual files to delete
                output_dir = db_path.parent
                files_to_delete = []
                for file_path in file_paths:
                    full_path = output_dir / file_path
                    if full_path.exists():
                        files_to_delete.append(full_path)
                    # Also check for metadata files
                    meta_path = full_path.with_suffix(full_path.suffix + '.meta.json')
                    if meta_path.exists():
                        files_to_delete.append(meta_path)
                
                if files_to_delete:
                    # Ask for confirmation if not auto-deleting
                    should_delete = auto_delete
                    if not auto_delete:
                        info(f"\nFound {len(files_to_delete)} files from session #{session_id}:")
                        # Show first 10 files as examples
                        for i, file in enumerate(files_to_delete[:10]):
                            info(f"  - {file.relative_to(output_dir)}")
                        if len(files_to_delete) > 10:
                            info(f"  ... and {len(files_to_delete) - 10} more files")
                        
                        response = input("\nAlso delete these downloaded files? (y/N): ")
                        should_delete = response.lower() == 'y'
                    
                    if should_delete:
                        import shutil
                        for file_path in files_to_delete:
                            try:
                                if file_path.is_dir():
                                    shutil.rmtree(file_path)
                                else:
                                    file_path.unlink()
                                files_deleted += 1
                            except Exception as e:
                                warning(f"Failed to delete {file_path}: {e}")
            
            # Delete URLs from session
            cursor.execute("DELETE FROM scraped_urls WHERE session_id = ?", (session_id,))
            
            # Delete the session record
            cursor.execute("DELETE FROM scraping_sessions WHERE id = ?", (session_id,))
            
            # Delete associated checksums
            checksum_count = 0
            if checksums:
                for checksum in checksums:
                    cursor.execute(
                        "DELETE FROM content_checksums WHERE checksum = ?",
                        (checksum,)
                    )
                    checksum_count += cursor.rowcount
            
            conn.commit()
            success(f"Cleared session #{session_id} ({url_count} URLs from {start_url} at {start_time})")
            if checksum_count > 0:
                info(f"Also cleared {checksum_count} associated content checksums")
            if files_deleted > 0:
                info(f"Deleted {files_deleted} downloaded files")
        else:
            # Fall back to date-based deletion for legacy databases
            cursor.execute(
                "SELECT MAX(DATE(scraped_at)) as last_date FROM scraped_urls"
            )
            result = cursor.fetchone()
            if not result or not result[0]:
                warning("No scraping sessions found in database")
                conn.close()
                return
            
            last_date = result[0]
            
            # Get file paths from last session
            cursor.execute(
                """SELECT target_filename 
                   FROM scraped_urls 
                   WHERE DATE(scraped_at) = ? AND target_filename IS NOT NULL AND target_filename != ''""",
                (last_date,)
            )
            file_paths = [row[0] for row in cursor.fetchall()]
            
            # Get checksums of URLs from last session
            cursor.execute(
                """SELECT content_checksum 
                   FROM scraped_urls 
                   WHERE DATE(scraped_at) = ? AND content_checksum IS NOT NULL""",
                (last_date,)
            )
            checksums = [row[0] for row in cursor.fetchall()]
            
            # Count URLs to be deleted
            cursor.execute(
                "SELECT COUNT(*) FROM scraped_urls WHERE DATE(scraped_at) = ?",
                (last_date,)
            )
            url_count = cursor.fetchone()[0]
            
            # Handle file deletion if requested (same logic as above)
            files_deleted = 0
            if delete_files and file_paths:
                output_dir = db_path.parent
                files_to_delete = []
                for file_path in file_paths:
                    full_path = output_dir / file_path
                    if full_path.exists():
                        files_to_delete.append(full_path)
                    meta_path = full_path.with_suffix(full_path.suffix + '.meta.json')
                    if meta_path.exists():
                        files_to_delete.append(meta_path)
                
                if files_to_delete:
                    should_delete = auto_delete
                    if not auto_delete:
                        info(f"\nFound {len(files_to_delete)} files from session {last_date}:")
                        for i, file in enumerate(files_to_delete[:10]):
                            info(f"  - {file.relative_to(output_dir)}")
                        if len(files_to_delete) > 10:
                            info(f"  ... and {len(files_to_delete) - 10} more files")
                        
                        response = input("\nAlso delete these downloaded files? (y/N): ")
                        should_delete = response.lower() == 'y'
                    
                    if should_delete:
                        import shutil
                        for file_path in files_to_delete:
                            try:
                                if file_path.is_dir():
                                    shutil.rmtree(file_path)
                                else:
                                    file_path.unlink()
                                files_deleted += 1
                            except Exception as e:
                                warning(f"Failed to delete {file_path}: {e}")
            
            # Delete URLs from last session
            cursor.execute("DELETE FROM scraped_urls WHERE DATE(scraped_at) = ?", (last_date,))
            
            # Delete associated checksums
            checksum_count = 0
            if checksums:
                for checksum in checksums:
                    cursor.execute(
                        "DELETE FROM content_checksums WHERE checksum = ?",
                        (checksum,)
                    )
                    checksum_count += cursor.rowcount
            
            conn.commit()
            success(f"Cleared {url_count} URLs from session {last_date}")
            if checksum_count > 0:
                info(f"Also cleared {checksum_count} associated content checksums")
            if files_deleted > 0:
                info(f"Deleted {files_deleted} downloaded files")
        
        conn.close()
        
    except sqlite3.Error as e:
        error(f"Database error: {e}")
    except Exception as e:
        error(f"Error clearing session: {e}")


def clear_urls_from_database(db_path: Path, pattern: str) -> None:
    """Clear URLs matching a pattern from the database.
    
    Also clears the associated content checksums to ensure pages can be re-scraped.
    
    Args:
        db_path: Path to the SQLite database
        pattern: Pattern to match URLs (uses SQL LIKE)
    """
    if not db_path.exists():
        warning("No database found. Nothing to clear.")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # First get the checksums of URLs to be deleted
        cursor.execute(
            "SELECT content_checksum FROM scraped_urls WHERE url LIKE ? AND content_checksum IS NOT NULL",
            (f"%{pattern}%",)
        )
        checksums = [row[0] for row in cursor.fetchall()]
        
        # Count how many URLs will be deleted
        cursor.execute(
            "SELECT COUNT(*) FROM scraped_urls WHERE url LIKE ?",
            (f"%{pattern}%",)
        )
        url_count = cursor.fetchone()[0]
        
        if url_count == 0:
            warning(f"No URLs found matching pattern: {pattern}")
        else:
            # Delete the URLs
            cursor.execute(
                "DELETE FROM scraped_urls WHERE url LIKE ?",
                (f"%{pattern}%",)
            )
            
            # Delete associated checksums
            checksum_count = 0
            if checksums:
                # Delete checksums one by one (SQLite doesn't support DELETE with IN and many values well)
                for checksum in checksums:
                    cursor.execute(
                        "DELETE FROM content_checksums WHERE checksum = ?",
                        (checksum,)
                    )
                    checksum_count += cursor.rowcount
            
            conn.commit()
            success(f"Cleared {url_count} URLs matching pattern: {pattern}")
            if checksum_count > 0:
                info(f"Also cleared {checksum_count} associated content checksums")
        
        conn.close()
        
    except sqlite3.Error as e:
        error(f"Database error: {e}")
    except Exception as e:
        error(f"Error clearing URLs: {e}")


def show_database_info(db_path: Path, args: argparse.Namespace) -> None:
    """Show information from the scrape tracker database.

    Args:
        db_path: Path to the SQLite database
        args: Command line arguments
    """
    if not db_path.exists():
        warning("No database found. Have you scraped anything yet?")
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
                    if status_code == 200:
                        status_icon = f"{Colors.GREEN}✓{Colors.RESET}"
                    else:
                        status_icon = f"{Colors.YELLOW}{status_code}{Colors.RESET}"
                    info(f"{status_icon} {url}")
            else:
                warning("No URLs found in database")

        conn.close()

    except sqlite3.Error as e:
        error(f"Database error: {e}")
    except Exception as e:
        error(f"Error reading database: {e}")


def create_parser() -> CustomArgumentParser:
    """Create the argument parser."""
    description = """m1f-scrape - Web Scraper Tool
============================
Download websites for offline viewing with support for multiple scraper backends.

Perfect for:
• Creating offline documentation mirrors
• Archiving websites for research
• Converting HTML sites to Markdown with m1f-html2md
• Building AI training datasets"""

    epilog = """Examples:
  %(prog)s https://example.com/docs -o ./html
  %(prog)s https://example.com/docs -o ./html --max-pages 100
  %(prog)s https://example.com/docs -o ./html --allowed-paths /docs/ /api/ /guides/
  %(prog)s https://example.com/blog -o ./html --allowed-paths /blog/2024/
  %(prog)s https://example.com -o ./html --scraper httrack
  %(prog)s --show-db-stats -o ./html  # Show scraping statistics

For more information, see the documentation."""

    parser = CustomArgumentParser(
        prog="m1f-scrape",
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

    # Main arguments
    parser.add_argument(
        "url", nargs="?", help="URL to scrape (not needed for database queries)"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output directory for downloaded files",
    )

    # Output control group
    output_group = parser.add_argument_group("Output Control")
    output_group.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    output_group.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress all output except errors"
    )

    # Scraper options group
    scraper_group = parser.add_argument_group("Scraper Options")
    scraper_group.add_argument(
        "--scraper",
        type=str,
        choices=[
            "httrack",
            "beautifulsoup",
            "bs4",
            "selectolax",
            "httpx",
            "playwright",
        ],
        default="beautifulsoup",
        help="Web scraper backend to use (default: beautifulsoup)",
    )
    scraper_group.add_argument(
        "--scraper-config",
        type=Path,
        help="Path to scraper-specific configuration file (YAML/JSON)",
    )

    # Crawl configuration group
    crawl_group = parser.add_argument_group("Crawl Configuration")
    crawl_group.add_argument(
        "--max-depth",
        type=int,
        default=5,
        help="Maximum crawl depth (default: 5, use -1 for unlimited)",
    )
    crawl_group.add_argument(
        "--max-pages",
        type=int,
        default=10000,
        help="Maximum pages to crawl (default: 10000, use -1 for unlimited)",
    )
    
    # Path restriction options
    # --allowed-path is kept as a hidden alias for backward compatibility
    crawl_group.add_argument(
        "--allowed-paths", "--allowed-path",
        type=str,
        nargs="*",
        metavar="PATH",
        help="Restrict crawling to specified paths and subdirectories (e.g., /docs/ /api/)",
    )
    
    crawl_group.add_argument(
        "--excluded-paths",
        type=str,
        nargs="*",
        metavar="PATH",
        help="URL paths to exclude from crawling (can specify multiple)",
    )

    # Request options group
    request_group = parser.add_argument_group("Request Options")
    request_group.add_argument(
        "--request-delay",
        type=float,
        default=5.0,
        help="Delay between requests in seconds (default: 5.0)",
    )
    request_group.add_argument(
        "--concurrent-requests",
        type=int,
        default=2,
        help="Number of concurrent requests (default: 2)",
    )
    request_group.add_argument(
        "--user-agent", type=str, help="Custom user agent string"
    )
    request_group.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)",
    )
    request_group.add_argument(
        "--retry-count",
        type=int,
        default=3,
        help="Number of retries for failed requests (default: 3)",
    )

    # Content filtering group
    filter_group = parser.add_argument_group("Content Filtering")
    filter_group.add_argument(
        "--ignore-get-params",
        action="store_true",
        help="Strip query parameters from URLs (treats /page?tab=1 and /page?tab=2 as duplicates)",
    )
    filter_group.add_argument(
        "--ignore-canonical",
        action="store_true",
        help="Disable canonical URL deduplication (keeps pages even if they specify a different canonical URL)",
    )
    filter_group.add_argument(
        "--ignore-duplicates",
        action="store_true",
        help="Disable content-based deduplication (keeps pages even if their content is identical)",
    )
    
    # Asset download options
    filter_group.add_argument(
        "--download-assets",
        action="store_true",
        help="Download linked assets like images, PDFs, CSS, JS, and other files",
    )
    filter_group.add_argument(
        "--asset-types",
        type=str,
        nargs="*",
        help="File extensions to download (e.g., .pdf .jpg .png). Default: common web assets",
    )
    filter_group.add_argument(
        "--max-asset-size",
        type=int,
        metavar="BYTES",
        help="Maximum file size for asset downloads in bytes (default: 50MB)",
    )
    filter_group.add_argument(
        "--assets-subdirectory",
        type=str,
        default="assets",
        help="Subdirectory name for storing downloaded assets (default: assets)",
    )

    # Display options group
    display_group = parser.add_argument_group("Display Options")
    display_group.add_argument(
        "--list-files",
        action="store_true",
        help="List all downloaded files after completion",
    )
    display_group.add_argument(
        "--save-urls",
        type=Path,
        metavar="FILE",
        help="Save all scraped URLs to a file (one per line)",
    )
    display_group.add_argument(
        "--save-files",
        type=Path,
        metavar="FILE",
        help="Save list of all downloaded files to a file (one per line)",
    )

    # Security options group
    security_group = parser.add_argument_group("Security Options")
    security_group.add_argument(
        "--disable-ssrf-check",
        action="store_true",
        help="Disable SSRF vulnerability checks (allows crawling private IPs)",
    )
    security_group.add_argument(
        "--force-rescrape",
        action="store_true",
        help="Force re-scraping of all URLs, ignoring the database cache",
    )

    # Database options group
    db_group = parser.add_argument_group("Database Options")
    db_group.add_argument(
        "--show-db-stats",
        action="store_true",
        help="Show scraping statistics from the database",
    )
    db_group.add_argument(
        "--show-errors",
        action="store_true",
        help="Show URLs that had errors during scraping",
    )
    db_group.add_argument(
        "--show-scraped-urls",
        action="store_true",
        help="List all scraped URLs from the database",
    )
    db_group.add_argument(
        "--clear-urls",
        type=str,
        metavar="PATTERN",
        help="Clear URLs from database matching the pattern (e.g., '/Extensions/' or 'example.com')",
    )
    db_group.add_argument(
        "--clear-last-session",
        action="store_true",
        help="Clear URLs from the last scraping session",
    )
    db_group.add_argument(
        "--clear-session",
        type=int,
        metavar="ID",
        help="Clear a specific session by its ID",
    )
    db_group.add_argument(
        "--delete-files",
        action="store_true",
        help="Also delete downloaded files when clearing sessions (skips confirmation)",
    )
    db_group.add_argument(
        "--show-sessions",
        action="store_true",
        help="Show all scraping sessions with timestamps and URL counts",
    )
    db_group.add_argument(
        "--show-sessions-detailed",
        action="store_true",
        help="Show detailed information for all scraping sessions",
    )
    db_group.add_argument(
        "--cleanup-sessions",
        action="store_true",
        help="Clean up orphaned sessions (left in 'running' state from crashes)",
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
    # --allowed-path is now an alias for --allowed-paths
    config.crawler.allowed_path = None  # Deprecated, kept for compatibility
    config.crawler.allowed_paths = args.allowed_paths
    if args.excluded_paths:
        config.crawler.excluded_paths = args.excluded_paths
    config.crawler.scraper_backend = ScraperBackend(args.scraper)
    config.crawler.request_delay = args.request_delay
    config.crawler.concurrent_requests = args.concurrent_requests
    config.crawler.timeout = args.timeout
    config.crawler.retry_count = args.retry_count
    config.crawler.respect_robots_txt = True  # Always respect robots.txt
    config.crawler.check_ssrf = not args.disable_ssrf_check

    if args.user_agent:
        config.crawler.user_agent = args.user_agent

    config.crawler.ignore_get_params = args.ignore_get_params
    config.crawler.check_canonical = not args.ignore_canonical
    config.crawler.check_content_duplicates = not args.ignore_duplicates
    config.crawler.force_rescrape = args.force_rescrape
    
    # Asset download configuration
    config.crawler.download_assets = args.download_assets
    if args.asset_types:
        config.crawler.asset_types = args.asset_types
    if args.max_asset_size:
        config.crawler.max_asset_size = args.max_asset_size
    config.crawler.assets_subdirectory = args.assets_subdirectory

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

    # Check if clear-urls is requested
    if args.clear_urls:
        db_path = args.output / "scrape_tracker.db"
        clear_urls_from_database(db_path, args.clear_urls)
        return
    
    # Check if clear-last-session is requested
    if args.clear_last_session:
        db_path = args.output / "scrape_tracker.db"
        # If no --delete-files flag, ask for confirmation
        clear_session(db_path, delete_files=True, auto_delete=args.delete_files)
        return
    
    # Check if clear-session is requested
    if args.clear_session:
        db_path = args.output / "scrape_tracker.db"
        # If no --delete-files flag, ask for confirmation
        clear_session(db_path, args.clear_session, delete_files=True, auto_delete=args.delete_files)
        return
    
    # Check if cleanup-sessions is requested
    if args.cleanup_sessions:
        db_path = args.output / "scrape_tracker.db"
        cleanup_orphaned_sessions(db_path)
        return
    
    # Check if show-sessions is requested
    if args.show_sessions or args.show_sessions_detailed:
        db_path = args.output / "scrape_tracker.db"
        show_scraping_sessions(db_path, detailed=args.show_sessions_detailed)
        return
    
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

    # Track start time for statistics
    start_time = time.time()

    try:
        # Create crawler and download the website
        crawler = WebCrawler(config.crawler)
        crawl_result = crawler.crawl_sync_with_stats(args.url, args.output)
        site_dir = crawl_result["site_dir"]
        scraped_urls = crawl_result.get("scraped_urls", [])
        errors = crawl_result.get("errors", [])
        session_files = crawl_result.get("session_files", [])
        session_id = crawl_result.get("session_id")

        # Calculate statistics for this session only
        duration = time.time() - start_time
        total_urls = len(scraped_urls) + len(errors)
        successful_urls = len(scraped_urls)
        success_rate = (successful_urls / total_urls * 100) if total_urls > 0 else 0
        avg_time_per_page = duration / total_urls if total_urls > 0 else 0

        # Display summary statistics
        header("\n" + "=" * 60)
        header(f"Scraping Summary (Session #{session_id})" if session_id else "Scraping Summary (Current Session)")
        header("=" * 60)
        success(f"✓ Successfully scraped {successful_urls} pages")
        if errors:
            warning(f"⚠ Failed to scrape {len(errors)} pages")
        info(f"Total URLs processed: {total_urls}")
        info(f"Success rate: {success_rate:.1f}%")
        info(f"Total duration: {duration:.1f} seconds")
        info(f"Average time per page: {avg_time_per_page:.2f} seconds")
        info(f"Output directory: {site_dir}")
        info(f"HTML files saved in this session: {len(session_files)}")
        if session_id:
            info(f"\nSession ID: #{session_id}")
            info(f"To clear this session: m1f-scrape --clear-session {session_id} -o {args.output}")

        # Save URLs to file if requested
        if args.save_urls:
            try:
                with open(args.save_urls, 'w', encoding='utf-8') as f:
                    for url in scraped_urls:
                        f.write(f"{url}\n")
                success(f"Saved {len(scraped_urls)} URLs to {args.save_urls}")
            except Exception as e:
                error(f"Failed to save URLs to file: {e}")

        # Save file list if requested (for this session only)
        if args.save_files:
            try:
                with open(args.save_files, 'w', encoding='utf-8') as f:
                    for html_file in sorted(session_files):
                        f.write(f"{html_file}\n")
                success(f"Saved {len(session_files)} file paths to {args.save_files}")
            except Exception as e:
                error(f"Failed to save file list: {e}")

        # List downloaded files if requested (with limit for verbose output)
        if args.list_files or config.verbose:
            if session_files:
                info("\nDownloaded files in this session:")
                files_to_show = sorted(session_files)
                max_files_to_show = 30
                
                if len(files_to_show) > max_files_to_show:
                    # Show first 15 and last 15 files
                    for html_file in files_to_show[:15]:
                        rel_path = html_file.relative_to(site_dir)
                        info(f"  - {rel_path}")
                    info(f"  ... ({len(files_to_show) - max_files_to_show} more files) ...")
                    for html_file in files_to_show[-15:]:
                        rel_path = html_file.relative_to(site_dir)
                        info(f"  - {rel_path}")
                    info(f"\nTotal: {len(files_to_show)} files downloaded in this session")
                else:
                    for html_file in files_to_show:
                        rel_path = html_file.relative_to(site_dir)
                        info(f"  - {rel_path}")
            else:
                info("\nNo new files downloaded in this session (all URLs were already scraped)")

    except KeyboardInterrupt:
        warning("\n⚠️  Scraping interrupted by user")
        info("Run the same command again to resume where you left off")
        info(f"To view session details: m1f-scrape --show-sessions -o {args.output}")
        sys.exit(0)
    except Exception as e:
        error(f"Error during scraping: {e}")
        if config.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
