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
from pathlib import Path
from flask import Flask, render_template, send_from_directory, jsonify, send_file
from flask_cors import CORS
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

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
}

# Only include pages that actually exist
if TEST_PAGES_DIR.exists():
    for html_file in TEST_PAGES_DIR.glob("*.html"):
        if html_file.name != "404.html":  # Skip error page
            page_name = html_file.stem
            if page_name in PAGE_METADATA:
                TEST_PAGES[page_name] = PAGE_METADATA[page_name]
            else:
                # Add unknown pages with generic metadata
                TEST_PAGES[page_name] = {
                    "title": page_name.replace("-", " ").title(),
                    "description": f"Test page: {page_name}",
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
    # Check if page exists in our configuration
    if page_name in TEST_PAGES:
        template_file = f"{page_name}.html"
        file_path = TEST_PAGES_DIR / template_file

        if file_path.exists():
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
        test_pages_abs = str(TEST_PAGES_DIR.absolute())
        return send_from_directory(test_pages_abs, f"{page_name}.html")

    return "Page not found", 404


@app.route("/api/test-pages")
def api_test_pages():
    """API endpoint to list all test pages."""
    return jsonify(TEST_PAGES)


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
        print(
            f"""
╔══════════════════════════════════════════════════════════════╗
║                  HTML2MD Test Server                         ║
║                                                              ║
║  Server running at: http://localhost:{port:<4}                    ║
║                                                              ║
║  Available test pages ({len(TEST_PAGES)} found):            ║
"""
        )

        # Sort pages for consistent display
        for page in sorted(TEST_PAGES.keys()):
            info = TEST_PAGES[page]
            # Truncate title if too long
            title = info["title"][:25]
            print(f"║  • /page/{page:<20} - {title:<25} ║")

        if not TEST_PAGES:
            print("║  No test pages found in test_pages directory!               ║")

        print(
            """║                                                              ║
║  Press Ctrl+C to stop the server                            ║
╚══════════════════════════════════════════════════════════════╝
    """
        )

    # Disable debug mode when running in testing environment
    debug_mode = os.environ.get("FLASK_ENV") != "testing"

    app.run(host="0.0.0.0", port=port, debug=debug_mode)
