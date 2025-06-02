#!/usr/bin/env python3
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
prepare_docs.py - Documentation Preparation Tool

This script automates the process of converting HTML documentation to Markdown
and maintaining the documentation structure. It works in conjunction with the
html2md.py tool to provide a streamlined documentation workflow.

Usage:
    python tools/prepare_docs.py --convert-html  # Convert HTML docs to Markdown
    python tools/prepare_docs.py --build-bundle  # Create a bundled documentation file
    python tools/prepare_docs.py --all  # Perform all documentation preparation steps
"""

import argparse
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("prepare_docs")

# Configuration
BASE_DIR = Path(__file__).parent.parent
HTML_DOCS_DIR = BASE_DIR / "tests" / "html2md" / "source" / "html"
MD_DOCS_DIR = BASE_DIR / "tests" / "html2md" / "output" / "markdown"
BUNDLE_OUTPUT = BASE_DIR / "tests" / "html2md" / "output" / "documentation-bundle.md"


def ensure_dir(directory: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    if not directory.exists():
        directory.mkdir(parents=True)
        logger.info(f"Created directory: {directory}")


def convert_html_to_markdown() -> bool:
    """Convert HTML documentation to Markdown using html2md.py.

    Returns:
        bool: True if conversion was successful, False otherwise
    """
    logger.info("Starting HTML to Markdown conversion...")
    ensure_dir(HTML_DOCS_DIR)
    ensure_dir(MD_DOCS_DIR)

    # Check if there are any HTML files to convert
    html_files = list(HTML_DOCS_DIR.glob("**/*.html")) + list(
        HTML_DOCS_DIR.glob("**/*.htm")
    )

    if not html_files:
        logger.warning(f"No HTML files found in {HTML_DOCS_DIR}")
        logger.info(
            f"You can add HTML files to the {HTML_DOCS_DIR} directory for conversion"
        )
        return False

    # Build command for html2md.py
    html2md_script = BASE_DIR / "tools" / "html2md.py"

    if not html2md_script.exists():
        logger.error(f"HTML to Markdown conversion script not found: {html2md_script}")
        return False

    try:
        # Run the HTML to Markdown conversion with optimal settings
        cmd = [
            sys.executable,
            str(html2md_script),
            "--source-dir",
            str(HTML_DOCS_DIR),
            "--destination-dir",
            str(MD_DOCS_DIR),
            "--add-frontmatter",
            "--convert-code-blocks",
            "--force",  # Overwrite existing files
            "--remove-elements",
            "script",
            "style",
            "iframe",
            "noscript",
            "nav",
            "footer",
            ".advertisement",
        ]

        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        logger.info(f"HTML to Markdown conversion completed successfully")
        logger.info(f"Converted files are available in: {MD_DOCS_DIR}")

        # Print any output from the command
        if result.stdout:
            for line in result.stdout.splitlines():
                logger.info(f"html2md: {line}")

        return True

    except subprocess.CalledProcessError as e:
        logger.error(
            f"HTML to Markdown conversion failed with exit code {e.returncode}"
        )
        if e.stdout:
            logger.info("Output:")
            for line in e.stdout.splitlines():
                logger.info(f"  {line}")
        if e.stderr:
            logger.error("Errors:")
            for line in e.stderr.splitlines():
                logger.error(f"  {line}")
        return False

    except Exception as e:
        logger.error(f"Error during HTML to Markdown conversion: {e}")
        return False


def build_documentation_bundle() -> bool:
    """Create a bundled documentation file using m1f.py.

    Returns:
        bool: True if bundling was successful, False otherwise
    """
    logger.info("Creating documentation bundle...")

    # Check if Markdown directory exists and has files
    if not MD_DOCS_DIR.exists():
        logger.warning(f"Markdown directory not found: {MD_DOCS_DIR}")
        logger.info("Run with --convert-html first to create Markdown files")
        return False

    md_files = list(MD_DOCS_DIR.glob("**/*.md"))
    if not md_files:
        logger.warning(f"No Markdown files found in {MD_DOCS_DIR}")
        return False

    # Build command for m1f.py
    m1f_script = BASE_DIR / "tools" / "m1f.py"

    if not m1f_script.exists():
        logger.error(f"m1f script not found: {m1f_script}")
        return False

    try:
        # Create docs directory if it doesn't exist
        ensure_dir(BUNDLE_OUTPUT.parent)

        # Run m1f to bundle the documentation
        cmd = [
            sys.executable,
            str(m1f_script),
            "--source-directory",
            str(MD_DOCS_DIR),
            "--output-file",
            str(BUNDLE_OUTPUT),
            "--separator-style",
            "Markdown",
            "--force",  # Overwrite existing bundle
            "--include-extensions",
            ".md",
        ]

        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        logger.info(f"Documentation bundle created successfully: {BUNDLE_OUTPUT}")

        # Print any output from the command
        if result.stdout:
            for line in result.stdout.splitlines():
                logger.info(f"m1f: {line}")

        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Documentation bundling failed with exit code {e.returncode}")
        if e.stdout:
            logger.info("Output:")
            for line in e.stdout.splitlines():
                logger.info(f"  {line}")
        if e.stderr:
            logger.error("Errors:")
            for line in e.stderr.splitlines():
                logger.error(f"  {line}")
        return False

    except Exception as e:
        logger.error(f"Error during documentation bundling: {e}")
        return False


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Documentation preparation tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--convert-html", action="store_true", help="Convert HTML docs to Markdown"
    )

    parser.add_argument(
        "--build-bundle",
        action="store_true",
        help="Create a bundled documentation file",
    )

    parser.add_argument(
        "--all", action="store_true", help="Perform all documentation preparation steps"
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    # Add the ability to override source and destination directories
    parser.add_argument(
        "--html-dir", help=f"Source HTML directory (default: {HTML_DOCS_DIR})"
    )

    parser.add_argument(
        "--markdown-dir",
        help=f"Destination Markdown directory (default: {MD_DOCS_DIR})",
    )

    parser.add_argument(
        "--output-bundle", help=f"Output bundle file path (default: {BUNDLE_OUTPUT})"
    )

    args = parser.parse_args()

    # Override directories if specified
    global HTML_DOCS_DIR, MD_DOCS_DIR, BUNDLE_OUTPUT
    if args.html_dir:
        HTML_DOCS_DIR = Path(args.html_dir)
    if args.markdown_dir:
        MD_DOCS_DIR = Path(args.markdown_dir)
    if args.output_bundle:
        BUNDLE_OUTPUT = Path(args.output_bundle)

    # If no arguments provided, show help
    if not (args.convert_html or args.build_bundle or args.all):
        parser.print_help()
        sys.exit(0)

    # Set logging level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
        logger.debug(f"HTML source directory: {HTML_DOCS_DIR}")
        logger.debug(f"Markdown output directory: {MD_DOCS_DIR}")
        logger.debug(f"Bundle output file: {BUNDLE_OUTPUT}")

    # Track execution time
    start_time = time.time()

    success = True

    # Perform requested operations
    if args.convert_html or args.all:
        if not convert_html_to_markdown():
            success = False

    if (args.build_bundle or args.all) and success:
        if not build_documentation_bundle():
            success = False

    # Calculate execution time
    execution_time = time.time() - start_time
    if execution_time >= 60:
        minutes, seconds = divmod(execution_time, 60)
        time_str = f"{int(minutes)}m {seconds:.2f}s"
    else:
        time_str = f"{execution_time:.2f}s"

    if success:
        logger.info(f"Documentation preparation completed successfully in {time_str}")
    else:
        logger.warning(f"Documentation preparation completed with errors in {time_str}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(130)  # Standard exit code for Ctrl+C
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)
