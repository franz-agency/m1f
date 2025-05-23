#!/usr/bin/env python3
"""
Local Scraping Test
Test HTML to Markdown conversion by scraping from the local test server.

This script scrapes test pages from the local development server and converts
them to Markdown format. It now places scraped metadata (URL, timestamp) at
the end of each generated file, making them compatible with the m1f tool's
--remove-scraped-metadata option.

Usage:
    python test_local_scraping.py

Requirements:
    - Local test server running at http://localhost:8080
    - Start server with: cd tests/html2md_server && python server.py

Features:
    - Scrapes multiple test pages with different configurations
    - Applies CSS selectors to extract specific content
    - Removes unwanted elements (nav, footer, etc.)
    - Places scraped metadata at the end of files (new format)
    - Compatible with m1f --remove-scraped-metadata option
"""

import requests
import sys
from pathlib import Path
from bs4 import BeautifulSoup
import markdownify
from urllib.parse import urljoin
import time

# Test server configuration
TEST_SERVER_URL = "http://localhost:8080"

def test_server_connectivity():
    """Test if the test server is running and accessible."""
    try:
        response = requests.get(TEST_SERVER_URL, timeout=5)
        if response.status_code == 200:
            print(f"✅ Test server is running at {TEST_SERVER_URL}")
            return True
        else:
            print(f"❌ Test server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to test server at {TEST_SERVER_URL}")
        print("   Make sure the server is running with: cd tests/html2md_server && python server.py")
        return False
    except Exception as e:
        print(f"❌ Error connecting to test server: {e}")
        return False

def scrape_and_convert(page_name, outermost_selector=None, ignore_selectors=None):
    """Scrape a page from the test server and convert it to Markdown."""
    url = f"{TEST_SERVER_URL}/page/{page_name}"
    
    print(f"\n🔍 Scraping: {url}")
    
    try:
        # Fetch HTML
        headers = {
            'User-Agent': 'HTTrack/3.49-2 (+http://www.httrack.com/)'  # HTTrack default user agent
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        print(f"   📄 Fetched {len(response.text)} characters")
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Apply outermost selector if specified
        if outermost_selector:
            content = soup.select_one(outermost_selector)
            if content:
                print(f"   🎯 Applied selector: {outermost_selector}")
                soup = BeautifulSoup(str(content), 'html.parser')
            else:
                print(f"   ⚠️  Selector '{outermost_selector}' not found, using full page")
        
        # Remove ignored elements
        if ignore_selectors:
            for selector in ignore_selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"   🗑️  Removed {len(elements)} elements matching '{selector}'")
                    for element in elements:
                        element.decompose()
        
        # Convert to Markdown
        html_content = str(soup)
        markdown = markdownify.markdownify(
            html_content,
            heading_style='atx',
            bullets='-'
        )
        
        print(f"   ✅ Converted to {len(markdown)} characters of Markdown")
        
        # Save to file
        output_dir = Path("tests/html2md/scraped_examples")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"scraped_{page_name}.md"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)
            f.write("\n\n---\n\n")
            f.write(f"*Scraped from: {url}*\n\n")
            f.write(f"*Scraped at: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            f.write(f"*Source URL: {url}*")
        
        print(f"   💾 Saved to: {output_path}")
        
        return {
            'success': True,
            'url': url,
            'html_length': len(response.text),
            'markdown_length': len(markdown),
            'output_file': output_path
        }
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {
            'success': False,
            'url': url,
            'error': str(e)
        }

def main():
    """Run local scraping tests."""
    print("🚀 HTML2MD Local Scraping Test")
    print("=" * 50)
    
    # Check server connectivity
    if not test_server_connectivity():
        sys.exit(1)
    
    # Test pages to scrape
    test_cases = [
        {
            'name': 'm1f-documentation',
            'description': 'M1F Documentation (simple conversion)',
            'outermost_selector': None,
            'ignore_selectors': ['nav', 'footer']
        },
        {
            'name': 'html2md-documentation', 
            'description': 'HTML2MD Documentation (with code blocks)',
            'outermost_selector': 'main',
            'ignore_selectors': ['nav', '.sidebar', 'footer']
        },
        {
            'name': 'complex-layout',
            'description': 'Complex Layout (challenging structure)',
            'outermost_selector': 'article, main',
            'ignore_selectors': ['nav', 'header', 'footer', '.sidebar']
        },
        {
            'name': 'code-examples',
            'description': 'Code Examples (syntax highlighting test)',
            'outermost_selector': 'main.container',
            'ignore_selectors': ['nav', 'footer', 'aside']
        }
    ]
    
    results = []
    
    print(f"\n📋 Running {len(test_cases)} test cases...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] {test_case['description']}")
        
        result = scrape_and_convert(
            test_case['name'],
            test_case['outermost_selector'],
            test_case['ignore_selectors']
        )
        
        results.append({**result, **test_case})
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SCRAPING TEST SUMMARY")
    print("=" * 50)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    
    if successful:
        print(f"\n📄 Generated Markdown files:")
        for result in successful:
            print(f"   • {result['output_file']} ({result['markdown_length']} chars)")
    
    if failed:
        print(f"\n❌ Failed conversions:")
        for result in failed:
            print(f"   • {result['name']}: {result['error']}")
    
    print(f"\n🔗 Test server: {TEST_SERVER_URL}")
    print("💡 You can now examine the generated .md files to see conversion quality")

if __name__ == "__main__":
    main() 