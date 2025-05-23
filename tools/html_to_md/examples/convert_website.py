#!/usr/bin/env python3
"""Example: Convert an entire website to Markdown using HTTrack."""

from pathlib import Path
from tools.html_to_md import HtmlToMarkdownConverter

# Configuration for website conversion
config = {
    "source": Path("."),
    "destination": Path("./output/markdown"),
    
    # Content extraction
    "extractor": {
        "content_selector": "main, article, .content",  # Common content areas
        "ignore_selectors": [
            "nav",
            "header",
            "footer",
            ".sidebar",
            ".menu",
            ".ads",
            "#cookie-notice"
        ],
        "extract_metadata": True,
        "extract_opengraph": True,
    },
    
    # Processing options
    "processor": {
        "heading_offset": 0,
        "link_handling": "convert",
        "normalize_whitespace": True,
        "line_breaks_between_blocks": True,
    },
    
    # HTTrack crawler settings
    "crawler": {
        "max_depth": 5,
        "max_pages": 1000,
        "allowed_domains": [],  # Will be auto-set from URL
        "respect_robots_txt": True,
        "concurrent_requests": 5,
        "request_delay": 0.1,
        "exclude_patterns": [
            "*.pdf",
            "*.zip",
            "*.exe",
            "*/download/*",
            "*/api/*"
        ],
    },
    
    # Enable parallel processing
    "parallel": True,
    "verbose": True,
}

def main():
    """Convert a website to Markdown."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python convert_website.py <URL>")
        print("Example: python convert_website.py https://docs.example.com")
        sys.exit(1)
    
    url = sys.argv[1]
    
    print(f"Converting website: {url}")
    print("This may take a while depending on the website size...")
    
    # Create converter
    converter = HtmlToMarkdownConverter(config)
    
    try:
        # Convert the website
        results = converter.convert_website(url)
        
        print(f"\nSuccess! Converted {len(results)} pages")
        print(f"Output directory: {config['destination']}")
        
        # Show first few converted files
        print("\nConverted files:")
        for i, (source, dest) in enumerate(list(results.items())[:5]):
            print(f"  {Path(source).name} → {dest}")
        if len(results) > 5:
            print(f"  ... and {len(results) - 5} more files")
            
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 