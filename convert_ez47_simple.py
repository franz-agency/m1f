#!/usr/bin/env python3
"""Simple converter for ezPublish 4.7 documentation."""

from pathlib import Path
from tools.html2md.api import convert_html
import logging

logging.basicConfig(level=logging.INFO)


def convert_file(input_path: Path, output_path: Path):
    """Convert a single HTML file to Markdown."""
    try:
        # Read HTML content
        with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
            html_content = f.read()

        # Convert to markdown
        markdown_content = convert_html(html_content)

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write markdown
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        return True
    except Exception as e:
        print(f"Error converting {input_path}: {e}")
        return False


def main():
    # Base directories
    base_input_47 = Path(
        "/home/fuf-user/ezdoc/ezpublishdoc.mugo.ca/eZ-Publish/Technical-manual/4.7"
    )
    base_input_4x = Path(
        "/home/fuf-user/ezdoc/ezpublishdoc.mugo.ca/eZ-Publish/Technical-manual/4.x"
    )
    base_output = Path("/home/fuf-user/git/ezdoc47/markdown")

    # Process both 4.7 and 4.x
    for version, base_input in [("4.7", base_input_47), ("4.x", base_input_4x)]:
        print(f"\nProcessing version {version}...")

        # Find all HTML files
        html_files = list(base_input.rglob("*.html")) + list(base_input.rglob("*.htm"))
        print(f"Found {len(html_files)} HTML files in {version}")

        converted = 0
        failed = 0

        for html_file in html_files:
            # Calculate relative path
            rel_path = html_file.relative_to(base_input.parent.parent)

            # Create output path
            output_path = base_output / rel_path.with_suffix(".md")

            if convert_file(html_file, output_path):
                converted += 1
                if converted % 50 == 0:
                    print(f"  Converted {converted} files...")
            else:
                failed += 1

        print(f"Version {version} complete: {converted} converted, {failed} failed")

    print("\nAll conversions complete!")


if __name__ == "__main__":
    main()
