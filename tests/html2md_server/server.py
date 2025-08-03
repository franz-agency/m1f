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
HTML2MD Test Server
A modern Flask server for testing mf1-html2md conversion with challenging HTML pages.
"""

import os
import sys
import time
from pathlib import Path
from flask import (
    Flask,
    render_template,
    send_from_directory,
    jsonify,
    send_file,
    request,
)
from flask_cors import CORS
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Add colorama imports
from tools.shared.colors import info, header

app = Flask(
    __name__,
    template_folder="templates",  # Changed back to templates for error pages only
    static_folder="static",
)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get test pages directory
TEST_PAGES_DIR = Path(__file__).parent / "test_pages"

# Dynamically build test pages configuration based on existing files
TEST_PAGES = {}
ALL_PAGES = {}  # Track all pages including subdirectories

# Define metadata for known pages
PAGE_METADATA = {
    "index": {
        "title": "HTML2MD Test Suite",
        "description": "Comprehensive test pages for mf1-html2md converter",
    },
    "m1f-documentation": {
        "title": "M1F Documentation",
        "description": "Complete documentation for Make One File tool",
    },
    "mf1-html2md-documentation": {
        "title": "HTML2MD Documentation",
        "description": "Complete documentation for HTML to Markdown converter",
    },
    "complex-layout": {
        "title": "Complex Layout Test",
        "description": "Tests complex HTML structures and layouts",
    },
    "code-examples": {
        "title": "Code Examples Test",
        "description": "Tests code blocks with various languages and syntax highlighting",
    },
    "edge-cases": {
        "title": "Edge Cases Test",
        "description": "Tests edge cases and unusual HTML structures",
    },
    "modern-features": {
        "title": "Modern HTML Features",
        "description": "Tests modern HTML5 elements and features",
    },
    "nested-structures": {
        "title": "Nested Structures Test",
        "description": "Tests deeply nested HTML elements",
    },
    "tables-and-lists": {
        "title": "Tables and Lists Test",
        "description": "Tests complex tables and nested lists",
    },
    "multimedia": {
        "title": "Multimedia Content Test",
        "description": "Tests images, videos, and other media elements",
    },
    # Subdirectory page metadata
    "docs/index": {
        "title": "Documentation Index",
        "description": "Main documentation page",
    },
    "api/overview": {
        "title": "API Overview",
        "description": "API documentation overview",
    },
    "api/endpoints": {
        "title": "API Endpoints",
        "description": "Available API endpoints",
    },
    "api/authentication": {
        "title": "API Authentication",
        "description": "API authentication methods",
    },
    "guides/getting-started": {
        "title": "Getting Started Guide",
        "description": "Introduction and getting started guide",
    },
}

# Build comprehensive page index including subdirectories
if TEST_PAGES_DIR.exists():
    # First, find all HTML files in root directory
    for html_file in TEST_PAGES_DIR.glob("*.html"):
        if html_file.name != "404.html":  # Skip error page
            page_name = html_file.stem
            page_path = page_name

            if page_name in PAGE_METADATA:
                metadata = PAGE_METADATA[page_name]
            else:
                # Add unknown pages with generic metadata
                metadata = {
                    "title": page_name.replace("-", " ").title(),
                    "description": f"Test page: {page_name}",
                }

            TEST_PAGES[page_name] = metadata
            ALL_PAGES[page_path] = {
                "file_path": html_file,
                "metadata": metadata,
                "url_path": f"/{page_name}.html" if page_name != "index" else "/",
            }

    # Then, find all HTML files in subdirectories
    for html_file in TEST_PAGES_DIR.glob("**/*.html"):
        if html_file.name != "404.html" and html_file.parent != TEST_PAGES_DIR:
            # Get relative path from test_pages directory
            rel_path = html_file.relative_to(TEST_PAGES_DIR)
            page_path = str(rel_path.with_suffix(""))  # Remove .html extension

            if page_path in PAGE_METADATA:
                metadata = PAGE_METADATA[page_path]
            else:
                # Generate metadata from path
                title = html_file.stem.replace("-", " ").replace("_", " ").title()
                metadata = {
                    "title": title,
                    "description": f"Test page: {page_path}",
                }

            ALL_PAGES[page_path] = {
                "file_path": html_file,
                "metadata": metadata,
                "url_path": f"/{rel_path}",
            }


@app.route("/")
def index():
    """Serve the test suite index page."""
    # Serve index.html as a static file to avoid template parsing
    test_pages_abs = str(TEST_PAGES_DIR.absolute())
    return send_from_directory(test_pages_abs, "index.html")


@app.route("/page/<page_name>")
def serve_page(page_name):
    """Serve individual test pages as static files."""
    # Handle query parameters for testing --ignore-get-params
    query_params = request.args

    # Check if page exists in our configuration
    if page_name in TEST_PAGES:
        template_file = f"{page_name}.html"
        file_path = TEST_PAGES_DIR / template_file

        if file_path.exists():
            # For testing canonical URLs, inject a canonical tag if requested
            if query_params.get("canonical"):
                try:
                    content = file_path.read_text()
                    canonical_url = query_params.get("canonical")
                    # Inject canonical tag into head
                    content = content.replace(
                        "</head>",
                        f'<link rel="canonical" href="{canonical_url}" />\n</head>',
                    )
                    return content
                except Exception as e:
                    app.logger.error(f"Error injecting canonical tag: {e}")
                    return f"Error processing canonical tag: {str(e)}", 500

            # For testing duplicate content with query params
            # The same content is returned regardless of ?tab=1, ?tab=2, etc.
            # This helps test --ignore-get-params functionality

            # Get absolute path for the test_pages directory
            test_pages_abs = str(TEST_PAGES_DIR.absolute())
            # Serve as static file to avoid Jinja2 template parsing
            return send_from_directory(test_pages_abs, template_file)
        else:
            # Return a placeholder if file doesn't exist yet
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{TEST_PAGES[page_name]['title']}</title>
                <link rel="stylesheet" href="/static/css/modern.css">
            </head>
            <body>
                <div class="container">
                    <h1>{TEST_PAGES[page_name]['title']}</h1>
                    <p>{TEST_PAGES[page_name]['description']}</p>
                    <p class="alert alert-info">This test page is under construction.</p>
                    <a href="/" class="btn">Back to Index</a>
                </div>
                <script src="/static/js/main.js"></script>
            </body>
            </html>
            """

    # Check if it's a page that exists but isn't in metadata
    file_path = TEST_PAGES_DIR / f"{page_name}.html"
    if file_path.exists():
        # Handle canonical parameter even for pages not in TEST_PAGES
        if query_params.get("canonical"):
            try:
                content = file_path.read_text()
                canonical_url = query_params.get("canonical")
                # Inject canonical tag into head
                content = content.replace(
                    "</head>",
                    f'<link rel="canonical" href="{canonical_url}" />\n</head>',
                )
                return content
            except Exception as e:
                app.logger.error(f"Error injecting canonical tag: {e}")
                return f"Error processing canonical tag: {str(e)}", 500

        test_pages_abs = str(TEST_PAGES_DIR.absolute())
        return send_from_directory(test_pages_abs, f"{page_name}.html")

    return "Page not found", 404


@app.route("/<path:subpath>")
def serve_subpath(subpath):
    """Serve pages from subdirectories with proper routing."""
    # Remove .html extension if present to match our page_path keys
    if subpath.endswith(".html"):
        page_path = subpath[:-5]  # Remove .html
    else:
        page_path = subpath

    # Check if this page exists in our ALL_PAGES registry
    if page_path in ALL_PAGES:
        page_info = ALL_PAGES[page_path]
        file_path = page_info["file_path"]

        if file_path.exists():
            # Serve the file directly
            return send_file(str(file_path.absolute()), mimetype="text/html")

    # If not found in registry, try to find the file directly
    # Handle both with and without .html extension
    possible_paths = [
        TEST_PAGES_DIR / f"{subpath}",
        TEST_PAGES_DIR / f"{subpath}.html",
    ]

    for file_path in possible_paths:
        if file_path.exists() and file_path.is_file():
            return send_file(str(file_path.absolute()), mimetype="text/html")

    return "Page not found", 404


@app.route("/api/test-pages")
def api_test_pages():
    """API endpoint to list all test pages."""
    return jsonify(TEST_PAGES)


@app.route("/api/all-pages")
def api_all_pages():
    """API endpoint to list all pages including subdirectories."""
    # Convert to a more useful format for the API
    result = {}
    for page_path, page_info in ALL_PAGES.items():
        result[page_path] = {
            "title": page_info["metadata"]["title"],
            "description": page_info["metadata"]["description"],
            "url": page_info["url_path"],
        }
    return jsonify(result)


@app.route("/test/slow")
def test_slow_response():
    """Test endpoint that responds slowly (for timeout testing)."""
    delay = request.args.get("delay", "10")
    try:
        delay_seconds = float(delay)
        time.sleep(delay_seconds)
        return f"Response after {delay_seconds} seconds"
    except ValueError:
        return "Invalid delay parameter", 400


@app.route("/test/duplicate/<int:page_id>")
def test_duplicate_content(page_id):
    """Test endpoint that returns identical content for different URLs."""
    # Always return the same content regardless of page_id
    # This helps test --ignore-duplicates functionality
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Duplicate Content Test</title>
    </head>
    <body>
        <h1>This content is identical across all page IDs</h1>
        <p>Whether you access /test/duplicate/1 or /test/duplicate/2 or any other ID,
        you will always get this exact same content. This is useful for testing
        duplicate content detection.</p>
    </body>
    </html>
    """


@app.route("/static/<path:path>")
def send_static(path):
    """Serve static files."""
    static_dir = Path(__file__).parent / "static"
    return send_from_directory(str(static_dir.absolute()), path)


@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 page."""
    return render_template("404.html"), 404


if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("HTML2MD_SERVER_PORT", 8080))

    # Ensure TEST_PAGES is populated
    if not TEST_PAGES:
        logger.warning("No test pages found! Please check the test_pages directory.")

    # Only print banner in non-testing mode
    if os.environ.get("FLASK_ENV") != "testing":
        header("HTML2MD Test Server")
        info(f"Server running at: http://localhost:{port}")
        info(f"\nAvailable test pages ({len(ALL_PAGES)} total found):")

        # Sort pages for consistent display - show root pages first, then subdirectories
        root_pages = [p for p in ALL_PAGES.keys() if "/" not in p]
        subdir_pages = [p for p in ALL_PAGES.keys() if "/" in p]

        info(f"\nRoot pages ({len(root_pages)}):")
        for page_path in sorted(root_pages):
            page_info = ALL_PAGES[page_path]
            title = page_info["metadata"]["title"][:30]
            url = page_info["url_path"]
            info(f"  • {url:<25} - {title}")

        if subdir_pages:
            info(f"\nSubdirectory pages ({len(subdir_pages)}):")
            for page_path in sorted(subdir_pages):
                page_info = ALL_PAGES[page_path]
                title = page_info["metadata"]["title"][:30]
                url = page_info["url_path"]
                info(f"  • {url:<25} - {title}")

        if not ALL_PAGES:
            info("  No test pages found in test_pages directory!")

        info(f"\nAPI endpoints:")
        info(f"  • /api/test-pages      - Root pages only")
        info(f"  • /api/all-pages       - All pages including subdirs")

        info("\nPress Ctrl+C to stop the server")
        info("=" * 60)

    # Disable debug mode when running in testing environment
    debug_mode = os.environ.get("FLASK_ENV") != "testing"

    # Clear Werkzeug environment variables that might cause issues
    for key in list(os.environ.keys()):
        if key.startswith("WERKZEUG_"):
            del os.environ[key]

    app.run(host="0.0.0.0", port=port, debug=debug_mode)
