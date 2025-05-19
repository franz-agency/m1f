#!/usr/bin/env python3
"""Export WordPress content to Markdown files using WP CLI.

This utility fetches posts and pages from a WordPress installation via
WP CLI and saves each as a separate Markdown file.
"""

import argparse
import json
import subprocess
from pathlib import Path
from typing import Iterable

from markdownify import markdownify as md


def run_wp_cli(args: Iterable[str], wp_path: str | None = None) -> str:
    """Run a WP CLI command and return its standard output."""
    cmd = ["wp", *args]
    if wp_path:
        cmd.append(f"--path={wp_path}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def export_post(post_id: str, post_type: str, dest: Path, wp_path: str | None) -> None:
    """Export a single post to a Markdown file."""
    data = json.loads(run_wp_cli(["post", "get", post_id, "--format=json"], wp_path))
    title = data.get("post_title", "")
    slug = run_wp_cli(["post", "get", post_id, "--field=post_name"], wp_path) or post_id
    content = data.get("post_content", "")
    md_content = f"# {title}\n\n" + md(content)
    dest.mkdir(parents=True, exist_ok=True)
    outfile = dest / f"{slug}.md"
    outfile.write_text(md_content, encoding="utf-8")


def export_post_type(post_type: str, dest: Path, wp_path: str | None) -> None:
    """Export all posts of a given type."""
    ids = run_wp_cli(
        [
            "post",
            "list",
            f"--post_type={post_type}",
            "--format=ids",
        ],
        wp_path,
    )
    if not ids:
        return
    for post_id in ids.split():
        export_post(post_id, post_type, dest / post_type, wp_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export WordPress content to Markdown using WP CLI"
    )
    parser.add_argument(
        "--output-dir", required=True, help="Directory to write Markdown files"
    )
    parser.add_argument(
        "--post-types",
        default="post,page",
        help="Comma-separated list of post types to export (default: post,page)",
    )
    parser.add_argument(
        "--wp-path",
        default=None,
        help="Path to the WordPress installation for WP CLI",
    )
    args = parser.parse_args()
    dest = Path(args.output_dir)
    for pt in [p.strip() for p in args.post_types.split(",") if p.strip()]:
        export_post_type(pt, dest, args.wp_path)


if __name__ == "__main__":
    main()
