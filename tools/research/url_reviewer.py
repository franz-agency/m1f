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
Interactive URL review interface for research curation
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import re

try:
    from shared.colors import Colors, info, success, warning, error
except ImportError:
    # Fallback if colors not available
    class Colors:
        CYAN = ""
        GREEN = ""
        YELLOW = ""
        RED = ""
        BOLD = ""
        DIM = ""
        RESET = ""

    def info(msg):
        print(msg)

    def success(msg):
        print(msg)

    def warning(msg):
        print(msg)

    def error(msg):
        print(msg)


logger = logging.getLogger(__name__)


@dataclass
class URLItem:
    """Represents a URL for review"""

    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    status: str = "pending"
    index: Optional[int] = None


class URLReviewer:
    """Interactive interface for reviewing and curating URLs"""

    def __init__(self, url_manager=None):
        """
        Initialize the URL reviewer

        Args:
            url_manager: URLManager instance for database operations
        """
        self.url_manager = url_manager
        self.urls: List[URLItem] = []
        self.deleted_urls: List[URLItem] = []
        self.filter_term: Optional[str] = None

    def load_urls(self, urls: List[Dict]) -> None:
        """
        Load URLs for review

        Args:
            urls: List of URL dictionaries with url, title, description
        """
        self.urls = []
        for i, url_data in enumerate(urls):
            if isinstance(url_data, dict):
                item = URLItem(
                    url=url_data.get("url", ""),
                    title=url_data.get("title"),
                    description=url_data.get("description"),
                    source=url_data.get("source", "search"),
                    status=url_data.get("status", "pending"),
                    index=i + 1,
                )
            else:
                # Handle plain URL strings
                item = URLItem(url=str(url_data), index=i + 1)

            self.urls.append(item)

        logger.info(f"Loaded {len(self.urls)} URLs for review")

    async def interactive_review(self) -> Tuple[List[Dict], bool]:
        """
        Run interactive review session

        Returns:
            Tuple of (reviewed URLs list, confirm to proceed)
        """
        if not self.urls:
            warning("No URLs to review")
            return [], False

        info(f"\n{Colors.BOLD}=== URL Review Interface ==={Colors.RESET}")
        info(f"Total URLs: {len(self.urls)}")
        info("Type 'help' for commands\n")

        while True:
            # Display current URLs
            self._display_urls()

            # Get user command
            try:
                command = input(f"\n{Colors.CYAN}review> {Colors.RESET}").strip()
            except (EOFError, KeyboardInterrupt):
                info("\nReview cancelled")
                return [], False

            if not command:
                continue

            # Process command
            result = self._process_command(command)

            if result == "confirm":
                # User confirmed, return filtered URLs
                final_urls = [
                    {
                        "url": item.url,
                        "title": item.title,
                        "description": item.description,
                        "source": item.source,
                    }
                    for item in self.urls
                    if item.status != "deleted"
                ]

                success(f"\n✓ Proceeding with {len(final_urls)} URLs")
                return final_urls, True

            elif result == "cancel":
                warning("\nReview cancelled")
                return [], False

    def _display_urls(self, page_size: int = 20) -> None:
        """Display URLs in a formatted table"""
        # Apply filter if set
        display_urls = self._get_filtered_urls()

        if not display_urls:
            warning("No URLs to display (all filtered/deleted)")
            return

        # Table header
        print(
            f"\n{Colors.BOLD}{'ID':<4} {'Status':<10} {'Title/URL':<60} {'Source':<10}{Colors.RESET}"
        )
        print("─" * 85)

        # Display URLs
        for item in display_urls[:page_size]:
            # Status color
            if item.status == "deleted":
                status_color = Colors.RED
                status_symbol = "✗"
            elif item.status == "reviewed":
                status_color = Colors.GREEN
                status_symbol = "✓"
            else:
                status_color = Colors.YELLOW
                status_symbol = "?"

            # Display title or URL
            display_text = (
                item.title[:57] + "..."
                if item.title and len(item.title) > 60
                else (item.title or item.url[:60])
            )

            print(
                f"{item.index:<4} {status_color}{status_symbol} {item.status:<8}{Colors.RESET} {display_text:<60} {item.source or 'unknown':<10}"
            )

        if len(display_urls) > page_size:
            info(
                f"\n... and {len(display_urls) - page_size} more. Use 'show all' to see all URLs"
            )

        # Summary
        total = len(self.urls)
        deleted = len([u for u in self.urls if u.status == "deleted"])
        reviewed = len([u for u in self.urls if u.status == "reviewed"])
        pending = total - deleted - reviewed

        print(
            f"\n{Colors.DIM}Total: {total} | Pending: {pending} | Reviewed: {reviewed} | Deleted: {deleted}{Colors.RESET}"
        )

    def _get_filtered_urls(self) -> List[URLItem]:
        """Get URLs based on current filter"""
        if not self.filter_term:
            return [u for u in self.urls if u.status != "deleted"]

        term = self.filter_term.lower()
        filtered = []

        for item in self.urls:
            if item.status == "deleted":
                continue

            # Search in URL, title, and description
            if (
                term in item.url.lower()
                or (item.title and term in item.title.lower())
                or (item.description and term in item.description.lower())
            ):
                filtered.append(item)

        return filtered

    def _process_command(self, command: str) -> Optional[str]:
        """Process user command"""
        parts = command.split()
        if not parts:
            return None

        cmd = parts[0].lower()

        if cmd == "help" or cmd == "h":
            self._show_help()

        elif cmd == "delete" or cmd == "d":
            if len(parts) > 1:
                self._delete_urls(parts[1])
            else:
                error("Usage: delete <id> or delete <id1,id2,id3>")

        elif cmd == "keep" or cmd == "k":
            if len(parts) > 1:
                self._keep_urls(parts[1])
            else:
                error("Usage: keep <id> or keep <id1,id2,id3>")

        elif cmd == "search" or cmd == "s":
            if len(parts) > 1:
                search_term = " ".join(parts[1:])
                self.filter_term = search_term
                info(f"Filtering URLs containing: {search_term}")
            else:
                error("Usage: search <term>")

        elif cmd == "clear":
            self.filter_term = None
            info("Filter cleared")

        elif cmd == "show":
            if len(parts) > 1 and parts[1] == "all":
                self._display_urls(page_size=1000)
            elif len(parts) > 1 and parts[1] == "deleted":
                self._show_deleted()
            else:
                self._display_urls()

        elif cmd == "restore":
            if len(parts) > 1:
                self._restore_urls(parts[1])
            else:
                error("Usage: restore <id> or restore <id1,id2,id3>")

        elif cmd == "confirm" or cmd == "c":
            remaining = len([u for u in self.urls if u.status != "deleted"])
            if remaining == 0:
                error("No URLs remaining. Add URLs or restore deleted ones.")
            else:
                response = (
                    input(f"Proceed with {remaining} URLs? [y/N]: ").strip().lower()
                )
                if response == "y":
                    return "confirm"

        elif cmd == "cancel" or cmd == "quit" or cmd == "q":
            return "cancel"

        elif cmd == "stats":
            self._show_stats()

        else:
            warning(f"Unknown command: {cmd}. Type 'help' for commands")

        return None

    def _show_help(self) -> None:
        """Show help message"""
        help_text = f"""
{Colors.BOLD}Available Commands:{Colors.RESET}
  {Colors.CYAN}delete <id>{Colors.RESET}    - Delete URL(s). Examples: delete 1  delete 1,2,3  delete 1-5
  {Colors.CYAN}keep <id>{Colors.RESET}      - Mark URL(s) as reviewed/kept
  {Colors.CYAN}search <term>{Colors.RESET}  - Filter URLs containing term
  {Colors.CYAN}clear{Colors.RESET}          - Clear current filter
  {Colors.CYAN}show all{Colors.RESET}       - Show all URLs (no pagination)
  {Colors.CYAN}show deleted{Colors.RESET}   - Show deleted URLs
  {Colors.CYAN}restore <id>{Colors.RESET}   - Restore deleted URL(s)
  {Colors.CYAN}stats{Colors.RESET}          - Show review statistics
  {Colors.CYAN}confirm{Colors.RESET}        - Confirm and proceed with remaining URLs
  {Colors.CYAN}cancel{Colors.RESET}         - Cancel review and exit
  {Colors.CYAN}help{Colors.RESET}           - Show this help

{Colors.DIM}Shortcuts: d=delete, k=keep, s=search, c=confirm, q=quit{Colors.RESET}
"""
        print(help_text)

    def _delete_urls(self, id_spec: str) -> None:
        """Delete specified URLs"""
        ids = self._parse_id_spec(id_spec)
        deleted_count = 0

        for url_id in ids:
            for item in self.urls:
                if item.index == url_id and item.status != "deleted":
                    item.status = "deleted"
                    deleted_count += 1
                    break

        if deleted_count > 0:
            success(f"Deleted {deleted_count} URL(s)")
        else:
            warning("No matching URLs found to delete")

    def _keep_urls(self, id_spec: str) -> None:
        """Mark URLs as reviewed/kept"""
        ids = self._parse_id_spec(id_spec)
        kept_count = 0

        for url_id in ids:
            for item in self.urls:
                if item.index == url_id and item.status != "deleted":
                    item.status = "reviewed"
                    kept_count += 1
                    break

        if kept_count > 0:
            success(f"Marked {kept_count} URL(s) as reviewed")
        else:
            warning("No matching URLs found")

    def _restore_urls(self, id_spec: str) -> None:
        """Restore deleted URLs"""
        ids = self._parse_id_spec(id_spec)
        restored_count = 0

        for url_id in ids:
            for item in self.urls:
                if item.index == url_id and item.status == "deleted":
                    item.status = "pending"
                    restored_count += 1
                    break

        if restored_count > 0:
            success(f"Restored {restored_count} URL(s)")
        else:
            warning("No deleted URLs found to restore")

    def _parse_id_spec(self, id_spec: str) -> List[int]:
        """Parse ID specification (e.g., "1", "1,2,3", "1-5")"""
        ids = []

        # Handle comma-separated IDs
        if "," in id_spec:
            for part in id_spec.split(","):
                part = part.strip()
                if "-" in part:
                    # Range within comma-separated list
                    ids.extend(self._parse_range(part))
                else:
                    try:
                        ids.append(int(part))
                    except ValueError:
                        pass

        # Handle range
        elif "-" in id_spec:
            ids = self._parse_range(id_spec)

        # Single ID
        else:
            try:
                ids.append(int(id_spec))
            except ValueError:
                pass

        return ids

    def _parse_range(self, range_spec: str) -> List[int]:
        """Parse range specification (e.g., "1-5")"""
        try:
            parts = range_spec.split("-")
            if len(parts) == 2:
                start = int(parts[0])
                end = int(parts[1])
                return list(range(start, end + 1))
        except ValueError:
            pass
        return []

    def _show_deleted(self) -> None:
        """Show deleted URLs"""
        deleted = [u for u in self.urls if u.status == "deleted"]

        if not deleted:
            info("No deleted URLs")
            return

        print(f"\n{Colors.BOLD}Deleted URLs:{Colors.RESET}")
        print("─" * 60)

        for item in deleted:
            display_text = item.title or item.url[:50]
            print(f"{Colors.DIM}{item.index:<4} {display_text}{Colors.RESET}")

        info(f"\nTotal deleted: {len(deleted)}")
        info("Use 'restore <id>' to restore URLs")

    def _show_stats(self) -> None:
        """Show review statistics"""
        total = len(self.urls)
        deleted = len([u for u in self.urls if u.status == "deleted"])
        reviewed = len([u for u in self.urls if u.status == "reviewed"])
        pending = total - deleted - reviewed

        # Count by source
        sources = {}
        for item in self.urls:
            if item.status != "deleted":
                source = item.source or "unknown"
                sources[source] = sources.get(source, 0) + 1

        print(f"\n{Colors.BOLD}Review Statistics:{Colors.RESET}")
        print("─" * 40)
        print(f"Total URLs:     {total}")
        print(f"Pending:        {pending}")
        print(f"Reviewed:       {reviewed}")
        print(f"Deleted:        {deleted}")
        print(f"Remaining:      {total - deleted}")

        if sources:
            print(f"\n{Colors.BOLD}Sources:{Colors.RESET}")
            for source, count in sorted(
                sources.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"  {source:<15} {count}")
