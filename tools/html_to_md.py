#!/usr/bin/env python3
"""Convert HTML files to Markdown recursively.

This script walks a source directory, converts each HTML file to
Markdown, and writes the result to a destination directory while
recreating the directory structure. Only the content within the
specified outermost CSS selector is processed. Elements matching any
ignore selectors are removed. Script and style blocks as well as HTML
comments are discarded.
"""

import argparse
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Comment
from markdownify import markdownify


def adjust_internal_links(soup: BeautifulSoup) -> None:
    """Rewrite links to other HTML files so they point to Markdown."""
    for a in soup.find_all("a", href=True):
        href = a["href"]
        parsed = urlparse(href)
        if parsed.scheme or href.startswith("#"):
            # External link or in-page anchor
            continue
        path = Path(parsed.path)
        if path.suffix.lower() in {".html", ".htm"}:
            new_path = path.with_suffix(".md").as_posix()
            if parsed.fragment:
                new_path += f"#{parsed.fragment}"
            a["href"] = new_path


def convert_html(
    html: str, outer_selector: str, ignore_selectors: Iterable[str]
) -> str:
    """Convert HTML content to Markdown."""
    soup = BeautifulSoup(html, "html5lib")

    # Remove scripts, styles, and comments
    for tag in soup(["script", "style"]):
        tag.decompose()
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()

    root = soup
    if outer_selector:
        found = soup.select_one(outer_selector)
        if found:
            root = found

    for selector in ignore_selectors:
        for el in root.select(selector):
            el.decompose()

    adjust_internal_links(root)
    fragment = root.decode_contents()
    return markdownify(fragment)


def process_file(
    src: Path, dst: Path, outer_selector: str, ignore_selectors: Iterable[str]
) -> None:
    html = src.read_text(encoding="utf-8", errors="ignore")
    md = convert_html(html, outer_selector, ignore_selectors)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(md, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert HTML files in a directory tree to Markdown"
    )
    parser.add_argument("--source-dir", required=True, help="Directory with HTML files")
    parser.add_argument(
        "--destination-dir", required=True, help="Directory to write Markdown files"
    )
    parser.add_argument(
        "--outermost-selector",
        default="",
        help="CSS selector for the outermost element to convert",
    )
    parser.add_argument(
        "--ignore-selectors",
        nargs="*",
        default=[],
        help="CSS selectors to remove from the HTML before conversion",
    )
    args = parser.parse_args()

    src_root = Path(args.source_dir)
    dst_root = Path(args.destination_dir)

    for html_file in src_root.rglob("*.htm*"):
        rel = html_file.relative_to(src_root)
        dst_file = dst_root / rel
        dst_file = dst_file.with_suffix(".md")
        process_file(html_file, dst_file, args.outermost_selector, args.ignore_selectors)


if __name__ == "__main__":
    main()
