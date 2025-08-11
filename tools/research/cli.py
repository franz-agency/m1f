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
Enhanced CLI interface for m1f-research with improved UX
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import asyncio
import logging
from datetime import datetime

from ..m1f.file_operations import (
    safe_exists,
)

from .config import ResearchConfig
from .orchestrator import EnhancedResearchOrchestrator
from .output import OutputFormatter, ProgressTracker

# Use unified colorama module
try:
    from ..shared.colors import Colors, ColoredHelpFormatter, COLORAMA_AVAILABLE, info
except ImportError:
    # Fallback to local implementation
    from .output import Colors, COLORAMA_AVAILABLE

    def info(msg):
        print(msg)

    class ColoredHelpFormatter(argparse.RawDescriptionHelpFormatter):
        """Fallback help formatter with colors if available."""

        def _format_action_invocation(self, action: argparse.Action) -> str:
            """Format action with colors."""
            parts = super()._format_action_invocation(action)

            if COLORAMA_AVAILABLE:
                # Color the option names
                parts = parts.replace("-", f"{Colors.CYAN}-")
                parts = f"{parts}{Colors.RESET}"

            return parts

        def _format_usage(
            self, usage: str, actions, groups, prefix: Optional[str]
        ) -> str:
            """Format usage line with colors."""
            result = super()._format_usage(usage, actions, groups, prefix)

            if COLORAMA_AVAILABLE and result:
                # Highlight the program name
                prog_name = self._prog
                colored_prog = f"{Colors.GREEN}{prog_name}{Colors.RESET}"
                result = result.replace(prog_name, colored_prog, 1)

            return result


# Import version
try:
    from .._version import __version__
except ImportError:
    __version__ = "3.8.0"


class EnhancedResearchCommand:
    """Enhanced CLI with better user experience"""

    def __init__(self):
        self.parser = self._create_parser()
        self.formatter: Optional[OutputFormatter] = None

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create enhanced argument parser"""
        parser = argparse.ArgumentParser(
            prog="m1f-research",
            description="AI-powered research tool with advanced job management",
            formatter_class=ColoredHelpFormatter,
            epilog=f"""
{Colors.BOLD}Examples:{Colors.RESET}
  {Colors.CYAN}# Start new research{Colors.RESET}
  m1f-research "microservices best practices"
  
  {Colors.CYAN}# List jobs with filters{Colors.RESET}
  m1f-research --list-jobs --search "python" --limit 10
  
  {Colors.CYAN}# Resume with progress tracking{Colors.RESET}
  m1f-research --resume abc123 --verbose
  
  {Colors.CYAN}# JSON output for automation{Colors.RESET}
  m1f-research --list-jobs --format json | jq '.[] | select(.status=="completed")'
  
  {Colors.CYAN}# Clean up old data{Colors.RESET}
  m1f-research --clean-raw abc123

{Colors.BOLD}For more help:{Colors.RESET}
  m1f-research --help-examples    # More usage examples
  m1f-research --help-filters     # Filtering guide
  m1f-research --help-providers   # LLM provider setup
""",
        )

        # Main query
        parser.add_argument(
            "query", nargs="?", help="Research query (required for new jobs)"
        )

        # Output format
        output_group = parser.add_argument_group("output options")
        output_group.add_argument(
            "--format",
            choices=["text", "json"],
            default="text",
            help="Output format (default: text)",
        )

        output_group.add_argument(
            "--quiet", "-q", action="store_true", help="Suppress non-error output"
        )

        output_group.add_argument(
            "--verbose",
            "-v",
            action="count",
            default=0,
            help="Increase verbosity (-vv for debug)",
        )

        output_group.add_argument(
            "--no-color", action="store_true", help="Disable colored output"
        )

        # Help extensions
        help_group = parser.add_argument_group("extended help")
        help_group.add_argument(
            "--help-examples", action="store_true", help="Show extended examples"
        )

        help_group.add_argument(
            "--help-filters", action="store_true", help="Show filtering guide"
        )

        help_group.add_argument(
            "--help-providers",
            action="store_true",
            help="Show LLM provider setup guide",
        )

        # Job management
        job_group = parser.add_argument_group("job management")
        job_group.add_argument(
            "--resume", metavar="JOB_ID", help="Resume an existing research job"
        )

        job_group.add_argument(
            "--list-jobs", action="store_true", help="List all research jobs"
        )

        job_group.add_argument(
            "--status", metavar="JOB_ID", help="Show detailed job status"
        )

        job_group.add_argument(
            "--watch", metavar="JOB_ID", help="Watch job progress in real-time"
        )

        job_group.add_argument(
            "--urls-file", type=Path, help="File containing URLs to add (one per line)"
        )

        # List filters
        filter_group = parser.add_argument_group("filtering options")
        filter_group.add_argument("--limit", type=int, help="Limit number of results")

        filter_group.add_argument(
            "--offset", type=int, default=0, help="Offset for pagination"
        )

        filter_group.add_argument("--date", help="Filter by date (Y-M-D, Y-M, or Y)")

        filter_group.add_argument("--search", help="Search jobs by query term")

        filter_group.add_argument(
            "--status-filter",
            choices=["active", "completed", "failed"],
            help="Filter by job status",
        )

        # Data management
        data_group = parser.add_argument_group("data management")
        data_group.add_argument(
            "--clean-raw", metavar="JOB_ID", help="Clean raw HTML data for a job"
        )

        data_group.add_argument(
            "--clean-all-raw",
            action="store_true",
            help="Clean raw HTML data for all jobs",
        )

        data_group.add_argument(
            "--export", metavar="JOB_ID", help="Export job data to JSON"
        )

        # Research options
        research_group = parser.add_argument_group("research options")
        research_group.add_argument(
            "--urls",
            type=int,
            default=20,
            help="Number of URLs to search for (default: 20)",
        )

        research_group.add_argument(
            "--scrape",
            type=int,
            default=10,
            help="Maximum URLs to scrape (default: 10)",
        )

        research_group.add_argument(
            "--provider",
            "-p",
            choices=["claude", "claude-cli", "gemini", "gemini-cli", "openai"],
            default="claude",
            help="LLM provider to use",
        )

        research_group.add_argument("--model", "-m", help="Specific model to use")

        research_group.add_argument(
            "--template",
            "-t",
            choices=["general", "technical", "academic", "tutorial", "reference"],
            default="general",
            help="Analysis template",
        )

        # Behavior options
        behavior_group = parser.add_argument_group("behavior options")
        behavior_group.add_argument(
            "--output",
            "-o",
            type=Path,
            default=Path("./research-data"),
            help="Output directory",
        )

        behavior_group.add_argument(
            "--name", "-n", help="Custom name for research bundle"
        )

        behavior_group.add_argument(
            "--config", "-c", type=Path, help="Configuration file path"
        )

        behavior_group.add_argument(
            "--interactive", "-i", action="store_true", help="Start in interactive mode"
        )

        behavior_group.add_argument(
            "--no-filter", action="store_true", help="Disable content filtering"
        )

        behavior_group.add_argument(
            "--no-analysis", action="store_true", help="Skip AI analysis"
        )

        behavior_group.add_argument(
            "--concurrent", type=int, default=5, help="Max concurrent operations"
        )

        behavior_group.add_argument(
            "--dry-run", action="store_true", help="Preview without executing"
        )

        behavior_group.add_argument(
            "--yes", "-y", action="store_true", help="Answer yes to all prompts"
        )

        # Version
        parser.add_argument(
            "--version", action="version", version=f"%(prog)s {__version__}"
        )

        return parser

    async def _validate_args(self, args) -> Optional[str]:
        """Validate arguments and return error message if invalid"""
        # Check for conflicting options
        if args.resume and args.query:
            return "Cannot specify both query and --resume"

        # Check required args for operations
        if not any(
            [
                args.query,
                args.resume,
                args.list_jobs,
                args.status,
                args.clean_raw,
                args.clean_all_raw,
                args.export,
                args.watch,
                args.help_examples,
                args.help_filters,
                args.help_providers,
                args.interactive,
            ]
        ):
            return "No operation specified. Use --help for usage"

        # Validate URLs file if provided
        if args.urls_file and not await safe_exists(args.urls_file):
            return f"URLs file not found: {args.urls_file}"

        # Validate numeric ranges
        if args.urls < 0:
            return "--urls must be non-negative"

        if args.scrape < 0:
            return "--scrape must be non-negative"

        if args.concurrent < 1:
            return "--concurrent must be at least 1"

        if args.limit and args.limit < 1:
            return "--limit must be positive"

        if args.offset < 0:
            return "--offset must be non-negative"

        # Validate date format
        if args.date:
            if not self._validate_date_format(args.date):
                return f"Invalid date format: {args.date}. Use Y-M-D, Y-M, or Y"

        return None

    def _validate_date_format(self, date_str: str) -> bool:
        """Validate date format"""
        try:
            if len(date_str) == 10:  # Y-M-D
                datetime.strptime(date_str, "%Y-%m-%d")
            elif len(date_str) == 7:  # Y-M
                datetime.strptime(date_str, "%Y-%m")
            elif len(date_str) == 4:  # Y
                datetime.strptime(date_str, "%Y")
            else:
                return False
            return True
        except ValueError:
            return False

    async def run(self, args=None):
        """Run the CLI with enhanced output"""
        args = self.parser.parse_args(args)

        # Handle extended help
        if args.help_examples:
            self._show_examples()
            return 0

        if args.help_filters:
            self._show_filters_guide()
            return 0

        if args.help_providers:
            self._show_providers_guide()
            return 0

        # Setup formatter
        if args.no_color:
            Colors.disable()

        self.formatter = OutputFormatter(
            format=args.format, verbose=args.verbose, quiet=args.quiet
        )

        # Validate arguments
        error = await self._validate_args(args)
        if error:
            self.formatter.error(error)
            return 1

        # Setup logging
        self._setup_logging(args)

        try:
            # Route to appropriate handler
            if args.list_jobs:
                return await self._list_jobs(args)
            elif args.status:
                return await self._show_status(args)
            elif args.watch:
                return await self._watch_job(args)
            elif args.clean_raw:
                return await self._clean_raw(args)
            elif args.clean_all_raw:
                return await self._clean_all_raw(args)
            elif args.export:
                return await self._export_job(args)
            elif args.interactive:
                return await self._interactive_mode(args)
            else:
                return await self._run_research(args)

        except KeyboardInterrupt:
            self.formatter.warning("Interrupted by user")
            return 130
        except Exception as e:
            self.formatter.error(str(e))
            if args.verbose > 0:
                import traceback

                traceback.print_exc()
            return 1
        finally:
            self.formatter.cleanup()

    def _setup_logging(self, args):
        """Setup logging based on verbosity"""
        if args.format == "json":
            # Suppress all logging in JSON mode
            logging.disable(logging.CRITICAL)
        else:
            level = logging.WARNING
            if args.verbose == 1:
                level = logging.INFO
            elif args.verbose >= 2:
                level = logging.DEBUG

            logging.basicConfig(
                level=level,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )

    def _show_examples(self):
        """Show extended examples"""
        examples = """
# Research Workflows

## Basic Research
m1f-research "python async programming"

## Research with Custom Settings
m1f-research "react hooks" \\
  --urls 50 \\
  --scrape 25 \\
  --template technical \\
  --output ~/research

## Using Manual URLs
# Create URL list
cat > urls.txt << EOF
https://docs.python.org/3/library/asyncio.html
https://realpython.com/async-io-python/
EOF

# Use in research
m1f-research "python async" --urls-file urls.txt

## Job Management

# List recent jobs
m1f-research --list-jobs --limit 10

# Find specific research
m1f-research --list-jobs --search "react" --date 2025-07

# Resume interrupted job
m1f-research --resume abc123

# Add more URLs to existing job
m1f-research --resume abc123 --urls-file more-urls.txt

## Automation

# Export job data
m1f-research --export abc123 > job-data.json

# List completed jobs as JSON
m1f-research --list-jobs --status-filter completed --format json

# Batch processing
for topic in "react hooks" "vue composition" "angular signals"; do
  m1f-research "$topic" --quiet
done

## Interactive Research
m1f-research --interactive
"""
        info(examples)

    def _show_filters_guide(self):
        """Show filtering guide"""
        guide = """
# Filtering Guide

## Date Filtering

Filter jobs by creation date:

  # Specific day
  m1f-research --list-jobs --date 2025-07-23
  
  # Specific month
  m1f-research --list-jobs --date 2025-07
  
  # Specific year
  m1f-research --list-jobs --date 2025

## Search Filtering

Find jobs by query content:

  # Simple search
  m1f-research --list-jobs --search "python"
  
  # Case-insensitive
  m1f-research --list-jobs --search "REACT"
  
  # Partial matches
  m1f-research --list-jobs --search "async"

## Status Filtering

Filter by job status:

  # Only completed jobs
  m1f-research --list-jobs --status-filter completed
  
  # Only failed jobs
  m1f-research --list-jobs --status-filter failed
  
  # Active jobs
  m1f-research --list-jobs --status-filter active

## Pagination

Handle large result sets:

  # First page (10 items)
  m1f-research --list-jobs --limit 10
  
  # Second page
  m1f-research --list-jobs --limit 10 --offset 10
  
  # Large page
  m1f-research --list-jobs --limit 50

## Combined Filters

Combine multiple filters:

  # Python jobs from July 2025
  m1f-research --list-jobs \\
    --search "python" \\
    --date 2025-07 \\
    --limit 20
  
  # Completed React jobs
  m1f-research --list-jobs \\
    --search "react" \\
    --status-filter completed \\
    --limit 10
"""
        info(guide)

    def _show_providers_guide(self):
        """Show providers setup guide"""
        guide = """
# LLM Provider Setup Guide

## Claude (Anthropic)

1. Get API key from https://console.anthropic.com/
2. Set environment variable:
   export ANTHROPIC_API_KEY="your-key-here"
3. Use in research:
   m1f-research "topic" --provider claude --model claude-3-opus-20240229

## Gemini (Google)

1. Get API key from https://makersuite.google.com/app/apikey
2. Set environment variable:
   export GOOGLE_API_KEY="your-key-here"
3. Use in research:
   m1f-research "topic" --provider gemini --model gemini-1.5-pro

## OpenAI

1. Get API key from https://platform.openai.com/api-keys
2. Set environment variable:
   export OPENAI_API_KEY="your-key-here"
3. Use in research:
   m1f-research "topic" --provider openai --model gpt-4

## CLI Providers

For enhanced integration:

# Claude Code SDK (uses proper Claude Code SDK integration)
m1f-research "topic" --provider claude-cli

# Gemini CLI (requires gemini-cli installed) 
m1f-research "topic" --provider gemini-cli

## Configuration File

Set default provider in .m1f.config.yml:

```yaml
research:
  llm:
    provider: claude
    model: claude-3-opus-20240229
```
"""
        info(guide)

    async def _run_research(self, args):
        """Run research with progress tracking"""
        config = await self._create_config(args)
        orchestrator = EnhancedResearchOrchestrator(config)

        # Show research plan
        self.formatter.header(
            f"🔍 Research: {args.query or 'Resuming job'}",
            f"Provider: {config.llm.provider} | URLs: {config.scraping.search_limit} | Scrape: {config.scraping.scrape_limit}",
        )

        # Add progress callback
        def progress_callback(phase: str, current: int, total: int):
            if phase == "searching":
                self.formatter.info(f"Searching for URLs... ({current}/{total})")
            elif phase == "scraping":
                self.formatter.progress(current, total, "Scraping URLs")
            elif phase == "analyzing":
                self.formatter.progress(current, total, "Analyzing content")

        # Set callback if orchestrator supports it
        if hasattr(orchestrator, "set_progress_callback"):
            orchestrator.set_progress_callback(progress_callback)

        # Run research
        result = await orchestrator.research(
            query=args.query, job_id=args.resume, urls_file=args.urls_file
        )

        # Show results
        self.formatter.success("Research completed!")

        if self.formatter.format == "json":
            self.formatter._json_buffer.append(
                {
                    "type": "result",
                    "job_id": result.job_id,
                    "output_dir": str(result.output_dir),
                    "urls_found": result.urls_found,
                    "pages_scraped": len(result.scraped_content),
                    "pages_analyzed": len(result.analyzed_content),
                    "bundle_created": result.bundle_created,
                }
            )
        else:
            self.formatter.info(f"Job ID: {result.job_id}")
            self.formatter.info(f"Output: {result.output_dir}")
            self.formatter.list_item(f"URLs found: {result.urls_found}")
            self.formatter.list_item(f"Pages scraped: {len(result.scraped_content)}")
            self.formatter.list_item(f"Pages analyzed: {len(result.analyzed_content)}")

            if result.bundle_created:
                bundle_path = result.output_dir / "📚_RESEARCH_BUNDLE.md"
                self.formatter.success(f"Research bundle: {bundle_path}")

        return 0

    async def _list_jobs(self, args):
        """List jobs with enhanced formatting"""
        from .job_manager import JobManager

        job_manager = JobManager(args.output)

        # Get total count
        total_count = job_manager.count_jobs(
            status=args.status_filter, date_filter=args.date, search_term=args.search
        )

        # Get jobs
        jobs = job_manager.list_jobs(
            status=args.status_filter,
            limit=args.limit,
            offset=args.offset,
            date_filter=args.date,
            search_term=args.search,
        )

        if not jobs:
            self.formatter.info("No jobs found matching criteria")
            return 0

        # Format for display
        if self.formatter.format == "json":
            self.formatter._json_buffer = jobs
        else:
            # Build filter description
            filters = []
            if args.search:
                filters.append(f"search: '{args.search}'")
            if args.date:
                filters.append(f"date: {args.date}")
            if args.status_filter:
                filters.append(f"status: {args.status_filter}")

            filter_str = f" (filtered by {', '.join(filters)})" if filters else ""

            # Show header
            if args.limit:
                page = (args.offset // args.limit) + 1 if args.limit else 1
                total_pages = (
                    (total_count + args.limit - 1) // args.limit if args.limit else 1
                )
                self.formatter.header(
                    f"📋 Research Jobs - Page {page}/{total_pages}",
                    f"Showing {len(jobs)} of {total_count}{filter_str}",
                )
            else:
                self.formatter.header(
                    f"📋 Research Jobs ({total_count} total{filter_str})"
                )

            # Prepare table data
            headers = ["ID", "Status", "Query", "Created", "Stats"]
            rows = []

            for job in jobs:
                stats = job["stats"]
                stats_str = f"{stats['scraped_urls']}/{stats['total_urls']}"
                if stats["analyzed_urls"]:
                    stats_str += f" ({stats['analyzed_urls']})"

                # Format status with color
                status = job["status"]
                if status == "completed":
                    status_display = f"{Colors.GREEN}{status}{Colors.RESET}"
                elif status == "active":
                    status_display = f"{Colors.YELLOW}{status}{Colors.RESET}"
                else:
                    status_display = f"{Colors.RED}{status}{Colors.RESET}"

                rows.append(
                    [
                        job["job_id"][:8],
                        status_display,
                        job["query"][:40],
                        job["created_at"][:16],
                        stats_str,
                    ]
                )

            self.formatter.table(headers, rows, highlight_search=args.search)

            # Pagination hints
            if args.limit and total_count > args.limit:
                self.formatter.info("")
                if args.offset + args.limit < total_count:
                    next_offset = args.offset + args.limit
                    self.formatter.info(f"Next page: --offset {next_offset}")
                if args.offset > 0:
                    prev_offset = max(0, args.offset - args.limit)
                    self.formatter.info(f"Previous page: --offset {prev_offset}")

        return 0

    async def _show_status(self, args):
        """Show job status with enhanced formatting"""
        from .job_manager import JobManager

        job_manager = JobManager(args.output)

        job = job_manager.get_job(args.status)
        if not job:
            self.formatter.error(f"Job not found: {args.status}")
            return 1

        info = await job_manager.get_job_info(job)

        if self.formatter.format == "json":
            self.formatter._json_buffer.append(info)
        else:
            self.formatter.job_status(info)

        return 0

    async def _clean_raw(self, args):
        """Clean raw data with confirmation"""
        from .job_manager import JobManager

        job_manager = JobManager(args.output)

        if not args.yes:
            if not self.formatter.confirm(f"Clean raw data for job {args.clean_raw}?"):
                self.formatter.info("Cancelled")
                return 0

        self.formatter.info(f"Cleaning raw data for job {args.clean_raw}...")

        stats = await job_manager.cleanup_job_raw_data(args.clean_raw)

        if "error" in stats:
            self.formatter.error(stats["error"])
            return 1

        self.formatter.success(
            f"Cleaned {stats.get('html_files_deleted', 0)} files, "
            f"freed {stats.get('space_freed_mb', 0)} MB"
        )

        return 0

    async def _clean_all_raw(self, args):
        """Clean all raw data with confirmation"""
        from .job_manager import JobManager

        job_manager = JobManager(args.output)

        if not args.yes:
            if not self.formatter.confirm(
                "⚠️  This will delete ALL raw HTML data. Continue?", default=False
            ):
                self.formatter.info("Cancelled")
                return 0

        self.formatter.info("Cleaning raw data for all jobs...")

        # Show progress
        all_jobs = job_manager.list_jobs()
        progress = ProgressTracker(self.formatter, len(all_jobs), "Cleaning jobs")

        stats = {"jobs_cleaned": 0, "files_deleted": 0, "space_freed_mb": 0}

        for i, job_info in enumerate(all_jobs):
            try:
                job_stats = await job_manager.cleanup_job_raw_data(job_info["job_id"])
                if "error" not in job_stats:
                    stats["jobs_cleaned"] += 1
                    stats["files_deleted"] += job_stats.get("html_files_deleted", 0)
                    stats["space_freed_mb"] += job_stats.get("space_freed_mb", 0)
            except Exception as e:
                self.formatter.debug(f"Error cleaning {job_info['job_id']}: {e}")

            progress.update()

        progress.complete("Cleanup complete")

        self.formatter.success(
            f"Cleaned {stats['jobs_cleaned']} jobs, "
            f"{stats['files_deleted']} files, "
            f"freed {stats['space_freed_mb']:.1f} MB"
        )

        return 0

    async def _export_job(self, args):
        """Export job data to JSON"""
        from .job_manager import JobManager

        job_manager = JobManager(args.output)

        job = job_manager.get_job(args.export)
        if not job:
            self.formatter.error(f"Job not found: {args.export}")
            return 1

        info = await job_manager.get_job_info(job)

        # Add content if available
        job_db = job_manager.get_job_database(job)
        content = job_db.get_content_for_bundle()
        info["content"] = content

        # Output as JSON
        import json

        print(json.dumps(info, indent=2, default=str))

        return 0

    async def _watch_job(self, args):
        """Watch job progress in real-time"""
        from .job_manager import JobManager
        import time

        job_manager = JobManager(args.output)

        self.formatter.info(f"Watching job {args.watch}... (Ctrl+C to stop)")

        last_stats = None
        while True:
            try:
                job = job_manager.get_job(args.watch)
                if not job:
                    self.formatter.error(f"Job not found: {args.watch}")
                    return 1

                info = await job_manager.get_job_info(job)
                stats = info["stats"]

                # Check if stats changed
                if stats != last_stats:
                    # Clear screen and show status
                    os.system("clear" if os.name == "posix" else "cls")
                    self.formatter.job_status(info)
                    last_stats = stats

                # Check if job is complete
                if info["status"] in ["completed", "failed"]:
                    break

                # Wait before next check
                await asyncio.sleep(2)

            except KeyboardInterrupt:
                break

        return 0

    async def _interactive_mode(self, args):
        """Run in interactive mode"""
        self.formatter.header("🔍 m1f-research Interactive Mode")
        self.formatter.info("Type 'help' for commands, 'exit' to quit\n")

        while True:
            try:
                command = input(f"{Colors.CYAN}research> {Colors.RESET}").strip()

                if not command:
                    continue

                if command.lower() in ["exit", "quit"]:
                    break

                if command.lower() == "help":
                    self._show_interactive_help()
                    continue

                # Parse command
                parts = command.split()
                if parts[0] == "research":
                    # New research
                    query = " ".join(parts[1:])
                    await self._run_research(
                        argparse.Namespace(
                            query=query, resume=None, urls_file=None, **vars(args)
                        )
                    )
                elif parts[0] == "list":
                    # List jobs
                    await self._list_jobs(args)
                elif parts[0] == "status" and len(parts) > 1:
                    # Show status
                    args.status = parts[1]
                    await self._show_status(args)
                elif parts[0] == "resume" and len(parts) > 1:
                    # Resume job
                    args.resume = parts[1]
                    args.query = None
                    await self._run_research(args)
                else:
                    self.formatter.warning(f"Unknown command: {command}")
                    self.formatter.info("Type 'help' for available commands")

            except KeyboardInterrupt:
                info("")  # New line after ^C
                continue
            except EOFError:
                break

        self.formatter.info("\n👋 Goodbye!")
        return 0

    def _show_interactive_help(self):
        """Show interactive mode help"""
        help_text = """
Available commands:
  research <query>     Start new research
  list                 List all jobs
  status <job_id>      Show job status
  resume <job_id>      Resume a job
  help                 Show this help
  exit/quit           Exit interactive mode

Examples:
  research python async programming
  list
  status abc123
  resume abc123
"""
        info(help_text)

    async def _create_config(self, args) -> ResearchConfig:
        """Create configuration from arguments"""
        # Load base config
        if args.config and await safe_exists(args.config):
            config = await ResearchConfig.from_yaml(args.config)
        else:
            config = ResearchConfig()

        # Apply CLI overrides
        config.llm.provider = args.provider
        if args.model:
            config.llm.model = args.model

        # Set scraping config properly
        config.url_count = args.urls
        config.scrape_count = args.scrape
        config.scraping.max_concurrent = args.concurrent
        config.scraping.search_limit = args.urls  # Add for compatibility
        config.scraping.scrape_limit = args.scrape  # Add for compatibility

        config.output.directory = args.output
        if args.name:
            config.output.name = args.name

        # Set template in analysis config
        config.template = args.template

        config.interactive = args.interactive
        config.no_filter = args.no_filter
        config.no_analysis = args.no_analysis
        config.dry_run = args.dry_run
        config.verbose = args.verbose

        return config


def main():
    """Main entry point"""
    cli = EnhancedResearchCommand()
    sys.exit(asyncio.run(cli.run()))


if __name__ == "__main__":
    main()
