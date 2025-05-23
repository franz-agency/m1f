#!/usr/bin/env python3
"""
HTML2MD Test Server
A modern Flask server for testing html2md conversion with challenging HTML pages.
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, send_from_directory, jsonify
from flask_cors import CORS
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

app = Flask(__name__, 
            template_folder='test_pages',
            static_folder='static')
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test pages configuration
TEST_PAGES = {
    'index': {
        'title': 'HTML2MD Test Suite',
        'description': 'Comprehensive test pages for html2md converter'
    },
    'm1f-documentation': {
        'title': 'M1F Documentation',
        'description': 'Complete documentation for Make One File tool'
    },
    'html2md-documentation': {
        'title': 'HTML2MD Documentation',
        'description': 'Complete documentation for HTML to Markdown converter'
    },
    'complex-layout': {
        'title': 'Complex Layout Test',
        'description': 'Tests complex HTML structures and layouts'
    },
    'code-examples': {
        'title': 'Code Examples Test',
        'description': 'Tests code blocks with various languages and syntax highlighting'
    },
    'edge-cases': {
        'title': 'Edge Cases Test',
        'description': 'Tests edge cases and unusual HTML structures'
    },
    'modern-features': {
        'title': 'Modern HTML Features',
        'description': 'Tests modern HTML5 elements and features'
    },
    'nested-structures': {
        'title': 'Nested Structures Test',
        'description': 'Tests deeply nested HTML elements'
    },
    'tables-and-lists': {
        'title': 'Tables and Lists Test',
        'description': 'Tests complex tables and nested lists'
    },
    'multimedia': {
        'title': 'Multimedia Content Test',
        'description': 'Tests images, videos, and other media elements'
    }
}

@app.route('/')
def index():
    """Serve the test suite index page."""
    return render_template('index.html', pages=TEST_PAGES)

@app.route('/page/<page_name>')
def serve_page(page_name):
    """Serve individual test pages."""
    if page_name in TEST_PAGES:
        template_file = f'{page_name}.html'
        if os.path.exists(os.path.join(app.template_folder, template_file)):
            return render_template(template_file, 
                                 page_info=TEST_PAGES[page_name],
                                 current_time=datetime.now())
        else:
            # Return a placeholder if template doesn't exist yet
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
    return "Page not found", 404

@app.route('/api/test-pages')
def api_test_pages():
    """API endpoint to list all test pages."""
    return jsonify(TEST_PAGES)

@app.route('/static/<path:path>')
def send_static(path):
    """Serve static files."""
    return send_from_directory('static', path)

@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 page."""
    return render_template('404.html'), 404

if __name__ == '__main__':
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                  HTML2MD Test Server                         ║
║                                                              ║
║  Server running at: http://localhost:8080                    ║
║                                                              ║
║  Available test pages:                                       ║
""")
    for page, info in TEST_PAGES.items():
        print(f"║  • /page/{page:<20} - {info['title']:<25} ║")
    print("""║                                                              ║
║  Press Ctrl+C to stop the server                            ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=8080, debug=True) 