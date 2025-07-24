"""
Enhanced CLI interface for m1f-research with job management
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, List
import asyncio
import logging

from .config import ResearchConfig
from .orchestrator import EnhancedResearchOrchestrator

# Import version directly to avoid circular imports
try:
    from .._version import __version__
except ImportError:
    # Fallback for when running as a script
    __version__ = "3.8.0"


class EnhancedResearchCommand:
    """Enhanced command class for m1f-research with job support"""

    def __init__(self):
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser for m1f-research"""
        parser = argparse.ArgumentParser(
            prog="m1f-research",
            description="AI-powered research tool with job management and persistence",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Start new research
  m1f-research "microservices best practices"
  
  # Research with manual URL list
  m1f-research "react hooks" --urls-file my-links.txt
  
  # Resume existing job with more URLs
  m1f-research --resume abc123 --urls-file more-links.txt
  
  # List all jobs
  m1f-research --list-jobs
  
  # Check job status
  m1f-research --status abc123
  
  # List with filters
  m1f-research --list-jobs --limit 10 --search "react"
  m1f-research --list-jobs --date 2025-07-23
  m1f-research --list-jobs --date 2025-07 --limit 20
  
  # Clean up raw data  
  m1f-research --clean-raw abc123
  m1f-research --clean-all-raw
""",
        )

        # Main arguments
        parser.add_argument(
            "query", nargs="?", help="Research query (required for new jobs)"
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
            "--status", metavar="JOB_ID", help="Show status of a specific job"
        )

        job_group.add_argument(
            "--urls-file", type=Path, help="File containing URLs to add (one per line)"
        )

        # Enhanced list options
        list_group = parser.add_argument_group("list options")
        list_group.add_argument(
            "--limit", type=int, help="Limit number of results (for --list-jobs)"
        )

        list_group.add_argument(
            "--offset",
            type=int,
            default=0,
            help="Offset for pagination (for --list-jobs)",
        )

        list_group.add_argument("--date", help="Filter by date (Y-M-D or Y-M format)")

        list_group.add_argument("--search", help="Search jobs by query term")

        # Cleanup options
        cleanup_group = parser.add_argument_group("cleanup options")
        cleanup_group.add_argument(
            "--clean-raw",
            metavar="JOB_ID",
            help="Clean raw HTML data for a job (preserves aggregated data)",
        )

        cleanup_group.add_argument(
            "--clean-all-raw",
            action="store_true",
            help="Clean raw HTML data for all jobs",
        )

        # URL options
        url_group = parser.add_argument_group("url options")
        url_group.add_argument(
            "--urls",
            type=int,
            default=20,
            help="Number of URLs to search for (default: 20)",
        )

        url_group.add_argument(
            "--scrape",
            type=int,
            default=10,
            help="Maximum URLs to scrape (default: 10)",
        )

        # Output options
        output_group = parser.add_argument_group("output options")
        output_group.add_argument(
            "--output",
            "-o",
            type=Path,
            default=Path("./research-data"),
            help="Output directory (default: ./research-data)",
        )

        output_group.add_argument(
            "--name", "-n", help="Custom name for the research bundle"
        )

        # LLM provider options
        parser.add_argument(
            "--provider",
            "-p",
            choices=["claude", "claude-cli", "gemini", "gemini-cli", "openai"],
            default="claude",
            help="LLM provider to use (default: claude)",
        )

        parser.add_argument(
            "--model", "-m", help="Specific model to use (provider-dependent)"
        )

        parser.add_argument(
            "--template",
            "-t",
            choices=["general", "technical", "academic", "tutorial", "reference"],
            default="general",
            help="Analysis template to use (default: general)",
        )

        # Configuration options
        parser.add_argument(
            "--config", "-c", type=Path, help="Path to configuration file"
        )

        # Behavior options
        parser.add_argument(
            "--interactive", "-i", action="store_true", help="Start in interactive mode"
        )

        parser.add_argument(
            "--no-filter", action="store_true", help="Disable content filtering"
        )

        parser.add_argument(
            "--no-analysis",
            action="store_true",
            help="Skip AI analysis (just scrape and bundle)",
        )

        parser.add_argument(
            "--concurrent",
            type=int,
            default=5,
            help="Max concurrent scraping operations (default: 5)",
        )

        # Debug options
        parser.add_argument(
            "--verbose",
            "-v",
            action="count",
            default=0,
            help="Increase verbosity (use -vv for debug)",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without doing it",
        )

        # Version
        parser.add_argument(
            "--version", action="version", version=f"%(prog)s {__version__}"
        )

        return parser

    async def run(self, args=None):
        """Run the research command"""
        args = self.parser.parse_args(args)

        # Setup logging
        log_level = logging.WARNING
        if args.verbose == 1:
            log_level = logging.INFO
        elif args.verbose >= 2:
            log_level = logging.DEBUG

        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        # Handle job listing
        if args.list_jobs:
            return await self._list_jobs(args)

        # Handle job status
        if args.status:
            return await self._show_status(args)

        # Handle cleanup commands
        if args.clean_raw:
            return await self._clean_raw_data(args)

        if args.clean_all_raw:
            return await self._clean_all_raw_data(args)

        # Validate arguments for research
        if not args.query and not args.resume:
            self.parser.error("Either query or --resume is required")

        if args.resume and args.query:
            self.parser.error("Cannot specify both query and --resume")

        # Create config
        config = self._create_config(args)

        # Run research
        orchestrator = EnhancedResearchOrchestrator(config)

        try:
            # Determine query and job_id
            query = args.query
            job_id = args.resume

            # If resuming, get query from job
            if job_id:
                from .job_manager import JobManager

                job_manager = JobManager(config.output.directory)
                job = job_manager.get_job(job_id)
                if not job:
                    print(f"Error: Job {job_id} not found")
                    return 1
                query = job.query

            result = await orchestrator.research(
                query=query, job_id=job_id, urls_file=args.urls_file
            )

            # Print results
            print(f"\n✅ Research completed!")
            print(f"📋 Job ID: {result.job_id}")
            print(f"📁 Output: {result.output_dir}")
            print(f"🔗 URLs found: {result.urls_found}")
            print(f"📄 Pages scraped: {len(result.scraped_content)}")
            print(f"📊 Pages analyzed: {len(result.analyzed_content)}")

            if result.bundle_created:
                bundle_path = result.output_dir / "📚_RESEARCH_BUNDLE.md"
                print(f"\n📚 Research bundle: {bundle_path}")

                # Check for symlink
                latest_link = config.output.directory / "latest_research.md"
                if latest_link.exists():
                    print(f"🔗 Quick access: {latest_link}")

            return 0

        except KeyboardInterrupt:
            print("\n⚠️  Research cancelled by user")
            return 130
        except Exception as e:
            print(f"\n❌ Error: {e}")
            if args.verbose:
                import traceback

                traceback.print_exc()
            return 1

    async def _list_jobs(self, args):
        """List research jobs with filtering and pagination"""
        from .job_manager import JobManager

        job_manager = JobManager(args.output)

        # Get total count for pagination info
        total_count = job_manager.count_jobs(
            date_filter=args.date, search_term=args.search
        )

        # Get filtered jobs
        jobs = job_manager.list_jobs(
            limit=args.limit,
            offset=args.offset,
            date_filter=args.date,
            search_term=args.search,
        )

        if not jobs:
            if args.search or args.date:
                print("No research jobs found matching filters")
            else:
                print("No research jobs found")
            return 0

        # Show filter info
        filter_info = []
        if args.search:
            filter_info.append(f"search: '{args.search}'")
        if args.date:
            filter_info.append(f"date: {args.date}")

        filter_str = f" (filtered by {', '.join(filter_info)})" if filter_info else ""

        # Pagination info
        showing = len(jobs)
        if args.limit:
            page = (args.offset // args.limit) + 1
            total_pages = (total_count + args.limit - 1) // args.limit
            print(
                f"\n📋 Research Jobs - Page {page}/{total_pages} "
                f"(showing {showing} of {total_count}{filter_str})\n"
            )
        else:
            print(f"\n📋 Research Jobs ({total_count} total{filter_str})\n")

        print(f"{'ID':<10} {'Status':<10} {'Query':<40} {'Created':<20} {'Stats'}")
        print("-" * 100)

        for job in jobs:
            stats = job["stats"]
            stats_str = f"{stats['scraped_urls']}/{stats['total_urls']} scraped"
            if stats["analyzed_urls"]:
                stats_str += f", {stats['analyzed_urls']} analyzed"

            # Highlight search term if present
            query_display = job["query"][:40]
            if args.search and args.search.lower() in job["query"].lower():
                query_display = query_display.replace(
                    args.search, f"\033[1;33m{args.search}\033[0m"
                )

            print(
                f"{job['job_id']:<10} {job['status']:<10} "
                f"{query_display:<40} {job['created_at'][:19]:<20} {stats_str}"
            )

        # Show pagination hints
        if args.limit and total_count > args.limit:
            print("\nTip: Use --offset to see more results")
            if args.offset + args.limit < total_count:
                next_offset = args.offset + args.limit
                print(f"Next page: --offset {next_offset}")

        return 0

    async def _show_status(self, args):
        """Show status of a specific job"""
        from .job_manager import JobManager

        job_manager = JobManager(args.output)

        info = job_manager.get_job_info(job_manager.get_job(args.status))

        if "error" in info:
            print(f"Error: {info['error']}")
            return 1

        print(f"\n📋 Job Status: {info['job_id']}\n")
        print(f"Query: {info['query']}")
        print(f"Status: {info['status']}")
        print(f"Created: {info['created_at']}")
        print(f"Updated: {info['updated_at']}")
        print(f"Output: {info['output_dir']}")
        print(f"\nStatistics:")
        print(f"  Total URLs: {info['stats']['total_urls']}")
        print(f"  Scraped: {info['stats']['scraped_urls']}")
        print(f"  Filtered: {info['stats']['filtered_urls']}")
        print(f"  Analyzed: {info['stats']['analyzed_urls']}")

        if info["bundle_exists"]:
            print(f"\n✅ Research bundle available")

        return 0

    async def _clean_raw_data(self, args):
        """Clean raw HTML data for a specific job"""
        from .job_manager import JobManager

        job_manager = JobManager(args.output)

        print(f"🧹 Cleaning raw data for job {args.clean_raw}...")

        stats = job_manager.cleanup_job_raw_data(args.clean_raw)

        if "error" in stats:
            print(f"❌ Error: {stats['error']}")
            return 1

        print(f"✅ Cleanup complete:")
        print(f"  HTML files deleted: {stats.get('html_files_deleted', 0)}")
        print(f"  Space freed: {stats.get('space_freed_mb', 0)} MB")

        return 0

    async def _clean_all_raw_data(self, args):
        """Clean raw HTML data for all jobs"""
        from .job_manager import JobManager

        job_manager = JobManager(args.output)

        # Confirm action
        response = input("⚠️  This will delete all raw HTML data. Continue? (y/N): ")
        if response.lower() != "y":
            print("Cancelled")
            return 0

        print("🧹 Cleaning raw data for all jobs...")

        stats = job_manager.cleanup_all_raw_data()

        print(f"\n✅ Cleanup complete:")
        print(f"  Jobs cleaned: {stats['jobs_cleaned']}")
        print(f"  Files deleted: {stats['files_deleted']}")
        print(f"  Space freed: {stats['space_freed_mb']} MB")

        if stats["errors"]:
            print(f"\n⚠️  Errors encountered:")
            for error in stats["errors"][:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(stats["errors"]) > 5:
                print(f"  ... and {len(stats['errors']) - 5} more errors")

        return 0

    def _create_config(self, args) -> ResearchConfig:
        """Create configuration from arguments"""
        # Load base config from file if provided
        if args.config and args.config.exists():
            config = ResearchConfig.from_yaml(args.config)
        else:
            config = ResearchConfig()

        # Override with command line arguments
        config.llm.provider = args.provider
        if args.model:
            config.llm.model = args.model

        config.scraping.search_limit = args.urls
        config.scraping.scrape_limit = args.scrape
        config.scraping.max_concurrent = args.concurrent

        config.output.directory = args.output
        if args.name:
            config.output.name = args.name

        config.analysis.template = args.template

        config.interactive = args.interactive
        config.no_filter = args.no_filter
        config.no_analysis = args.no_analysis
        config.dry_run = args.dry_run
        config.verbose = args.verbose

        return config


def main():
    """Main entry point"""
    command = EnhancedResearchCommand()
    sys.exit(asyncio.run(command.run()))


if __name__ == "__main__":
    main()
