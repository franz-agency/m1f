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
Enhanced output formatting for m1f-research CLI
"""

import sys
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
import shutil
from pathlib import Path

# Use unified colorama module
from shared.colors import Colors, COLORAMA_AVAILABLE


class OutputFormatter:
    """Handles formatted output for m1f-research"""

    def __init__(self, format: str = "text", verbose: int = 0, quiet: bool = False):
        self.format = format
        self.verbose = verbose
        self.quiet = quiet

        # Disable colors if not TTY or if requested
        if not sys.stdout.isatty() or format == "json":
            Colors.disable()

        # Track if we're in JSON mode
        self._json_buffer = [] if format == "json" else None

    def print(self, message: str = "", level: str = "info", end: str = "\n", **kwargs):
        """Print a message with appropriate formatting"""
        if self.quiet and level != "error":
            return

        if self.format == "json":
            self._json_buffer.append(
                {
                    "type": "message",
                    "level": level,
                    "message": message,
                    "timestamp": datetime.now().isoformat(),
                    **kwargs,
                }
            )
        else:
            print(message, end=end)

    def success(self, message: str, **kwargs):
        """Print success message"""
        if self.format == "json":
            self._json_buffer.append({"type": "success", "message": message, **kwargs})
        else:
            self.print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

    def error(self, message: str, suggestion: Optional[str] = None, **kwargs):
        """Print error message with optional suggestion"""
        if self.format == "json":
            self._json_buffer.append(
                {
                    "type": "error",
                    "message": message,
                    "suggestion": suggestion,
                    **kwargs,
                }
            )
        else:
            self.print(f"{Colors.RED}❌ Error: {message}{Colors.RESET}", level="error")
            if suggestion:
                self.print(f"{Colors.YELLOW}💡 Suggestion: {suggestion}{Colors.RESET}")

    def warning(self, message: str, **kwargs):
        """Print warning message"""
        if self.format == "json":
            self._json_buffer.append({"type": "warning", "message": message, **kwargs})
        else:
            self.print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")

    def info(self, message: str, **kwargs):
        """Print info message"""
        if self.format == "json":
            self._json_buffer.append({"type": "info", "message": message, **kwargs})
        else:
            self.print(f"{Colors.CYAN}ℹ️  {message}{Colors.RESET}")

    def debug(self, message: str, **kwargs):
        """Print debug message (only if verbose)"""
        if self.verbose < 2:
            return

        if self.format == "json":
            self._json_buffer.append({"type": "debug", "message": message, **kwargs})
        else:
            self.print(f"{Colors.BRIGHT_BLACK}🔍 {message}{Colors.RESET}")

    def header(self, title: str, subtitle: Optional[str] = None):
        """Print a section header"""
        if self.format == "json":
            self._json_buffer.append(
                {"type": "header", "title": title, "subtitle": subtitle}
            )
        else:
            self.print()
            self.print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
            if subtitle:
                self.print(f"{Colors.DIM}{subtitle}{Colors.RESET}")
            self.print()

    def progress(self, current: int, total: int, message: str = ""):
        """Show progress bar"""
        if self.quiet or self.format == "json":
            return

        # Calculate percentage
        percentage = (current / total * 100) if total > 0 else 0

        # Terminal width
        term_width = shutil.get_terminal_size().columns
        bar_width = min(40, term_width - 30)

        # Build progress bar
        filled = int(bar_width * current / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_width - filled)

        # Build message
        msg = f"\r{Colors.CYAN}[{bar}] {percentage:>5.1f}% {message}{Colors.RESET}"

        # Print without newline
        sys.stdout.write(msg)
        sys.stdout.flush()

        # Add newline when complete
        if current >= total:
            self.print()

    def table(
        self,
        headers: List[str],
        rows: List[List[str]],
        highlight_search: Optional[str] = None,
    ):
        """Print a formatted table"""
        if self.format == "json":
            self._json_buffer.append(
                {"type": "table", "headers": headers, "rows": rows}
            )
            return

        # Calculate column widths
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(str(cell)))

        # Ensure we don't exceed terminal width
        term_width = shutil.get_terminal_size().columns
        total_width = sum(widths) + len(widths) * 3 - 1

        if total_width > term_width:
            # Scale down widths proportionally
            scale = term_width / total_width
            widths = [int(w * scale) for w in widths]

        # Print header
        header_line = " | ".join(h.ljust(w)[:w] for h, w in zip(headers, widths))
        self.print(f"{Colors.BOLD}{header_line}{Colors.RESET}")
        self.print("-" * len(header_line))

        # Print rows
        for row in rows:
            row_cells = []
            for cell, width in zip(row, widths):
                cell_str = str(cell)[:width].ljust(width)

                # Highlight search term if present
                if highlight_search and highlight_search.lower() in cell_str.lower():
                    cell_str = cell_str.replace(
                        highlight_search,
                        f"{Colors.YELLOW}{Colors.BOLD}{highlight_search}{Colors.RESET}",
                    )

                row_cells.append(cell_str)

            self.print(" | ".join(row_cells))

    def job_status(self, job: Dict[str, Any]):
        """Print formatted job status"""
        if self.format == "json":
            self._json_buffer.append({"type": "job_status", "job": job})
            return

        self.header(f"📋 Job Status: {job['job_id']}")

        # Basic info
        self.print(f"{Colors.BOLD}Query:{Colors.RESET} {job['query']}")

        # Color-code status
        status = job["status"]
        if status == "completed":
            status_colored = f"{Colors.GREEN}{status}{Colors.RESET}"
        elif status == "active":
            status_colored = f"{Colors.YELLOW}{status}{Colors.RESET}"
        else:
            status_colored = f"{Colors.RED}{status}{Colors.RESET}"

        self.print(f"{Colors.BOLD}Status:{Colors.RESET} {status_colored}")

        self.print(f"{Colors.BOLD}Created:{Colors.RESET} {job['created_at']}")
        self.print(f"{Colors.BOLD}Updated:{Colors.RESET} {job['updated_at']}")
        self.print(f"{Colors.BOLD}Output:{Colors.RESET} {job['output_dir']}")

        # Statistics
        self.print(f"\n{Colors.BOLD}Statistics:{Colors.RESET}")
        stats = job["stats"]
        self.print(f"  Total URLs: {stats['total_urls']}")
        self.print(f"  Scraped: {stats['scraped_urls']}")
        self.print(f"  Filtered: {stats['filtered_urls']}")
        self.print(f"  Analyzed: {stats['analyzed_urls']}")

        if job.get("bundle_exists"):
            self.print(f"\n{Colors.GREEN}✅ Research bundle available{Colors.RESET}")

    def list_item(self, item: str, indent: int = 0):
        """Print a list item"""
        if self.format == "json":
            self._json_buffer.append(
                {"type": "list_item", "item": item, "indent": indent}
            )
        else:
            prefix = "  " * indent + "• "
            self.print(f"{prefix}{item}")

    def confirm(self, prompt: str, default: bool = False) -> bool:
        """Ask for user confirmation"""
        if self.format == "json" or self.quiet:
            return default

        suffix = " [Y/n]" if default else " [y/N]"
        response = input(f"{Colors.YELLOW}{prompt}{suffix}: {Colors.RESET}").lower()

        if not response:
            return default

        return response in ("y", "yes")

    def get_json_output(self) -> str:
        """Get JSON output (for JSON format)"""
        if self.format != "json":
            return ""

        return json.dumps(self._json_buffer, indent=2)

    def cleanup(self):
        """Clean up and output JSON if needed"""
        if self.format == "json" and self._json_buffer:
            print(self.get_json_output())


class ProgressTracker:
    """Track and display progress for long operations"""

    def __init__(self, formatter: OutputFormatter, total: int, message: str = ""):
        self.formatter = formatter
        self.total = total
        self.current = 0
        self.message = message
        self.start_time = datetime.now()

    def update(self, increment: int = 1, message: Optional[str] = None):
        """Update progress"""
        self.current += increment
        if message:
            self.message = message

        # Calculate ETA
        if self.current > 0:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            rate = self.current / elapsed
            remaining = (self.total - self.current) / rate if rate > 0 else 0
            eta = f" ETA: {int(remaining)}s" if remaining > 1 else ""
        else:
            eta = ""

        self.formatter.progress(self.current, self.total, f"{self.message}{eta}")

    def complete(self, message: Optional[str] = None):
        """Mark as complete"""
        self.current = self.total
        if message:
            self.message = message
        self.formatter.progress(self.current, self.total, self.message)
