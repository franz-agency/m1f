#!/usr/bin/env python3
"""
Claude Code Documentation Scraper
=================================

A focused Python script to scrape and bundle Claude Code documentation.
Works on both Linux and Windows.

This script:
1. Scrapes Claude Code docs from docs.anthropic.com
2. Converts HTML to clean Markdown
3. Runs m1f-init to create the documentation bundle
4. Returns the path to the created bundle

Usage: python scrape_claude_code_docs.py <target_directory>
"""

import subprocess
import sys
import os
from pathlib import Path
import argparse
import shutil


# Configuration - all hardcoded for Claude Code
CLAUDE_DOCS_URL = "https://docs.anthropic.com/en/docs/claude-code"
SCRAPE_DELAY = 15  # seconds between requests
CONTENT_SELECTOR = "main"
IGNORE_SELECTORS = ["nav", "header", "footer"]
PROJECT_NAME = "Claude Code Documentation"
PROJECT_DESCRIPTION = "Official documentation for Claude Code - Anthropic's AI coding assistant"


def run_command(cmd, description, capture_output=True):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    
    try:
        if capture_output:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, result.stdout
        else:
            subprocess.run(cmd, check=True)
            return True, None
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed!")
        if e.stderr:
            print(f"   Error: {e.stderr}")
        return False, None
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        print(f"   Make sure m1f tools are installed and in PATH")
        return False, None


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Scrape Claude Code documentation and create a bundle",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
    python scrape_claude_code_docs.py ~/claude-docs
    
This will create the documentation bundle in the specified directory.
The final bundle will be in the 'm1f' subdirectory of the markdown folder.
        """
    )
    parser.add_argument("path", help="Target directory path (required)")
    args = parser.parse_args()
    
    # Determine output directory
    output_path = Path(args.path).absolute()
    
    print("🤖 Claude Code Documentation Scraper")
    print("=" * 50)
    print(f"Target: {CLAUDE_DOCS_URL}")
    print(f"Output directory: {output_path}")
    print(f"Total time: ~15-20 minutes")
    print("=" * 50)
    
    # Create output directory if needed
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save current directory and change to output
    original_dir = Path.cwd()
    os.chdir(output_path)
    
    # Paths for intermediate files
    html_dir = Path("html")
    markdown_dir = Path("claude-code-markdown")
    
    print(f"\n📁 Working directory: {output_path.absolute()}")
    
    # Step 1: Scrape Claude Code documentation
    print(f"\n{'='*50}")
    print("STEP 1: Scraping Claude Code Documentation")
    print(f"{'='*50}")
    print(f"📄 Will download ~30 HTML pages from Claude Code docs")
    print(f"⏱️  Expected duration: 7-8 minutes (15s delay between pages)")
    
    scrape_cmd = [
        "m1f-scrape",
        CLAUDE_DOCS_URL,
        "-o", str(html_dir),
        "--request-delay", str(SCRAPE_DELAY),
        "-v"
    ]
    
    success, _ = run_command(scrape_cmd, "Scraping documentation", capture_output=False)
    if not success:
        print("\n💡 Tip: Make sure m1f-scrape is installed:")
        print("   pip install m1f")
        return 1
    
    # Verify scraping results
    if not html_dir.exists():
        print("❌ HTML directory not created")
        return 1
    
    # Find the actual scraped directory (docs.anthropic.com/en/docs/claude-code)
    scraped_dir = html_dir / "docs.anthropic.com" / "en" / "docs" / "claude-code"
    if scraped_dir.exists():
        print(f"📁 Found scraped content in: {scraped_dir}")
        # Move content up and rename
        new_html_dir = Path("claude-code-html")
        if new_html_dir.exists():
            shutil.rmtree(new_html_dir)
        shutil.move(str(scraped_dir), str(new_html_dir))
        # Clean up empty directories
        shutil.rmtree(html_dir)
        html_dir = new_html_dir
        print(f"✅ Moved content to: {html_dir}")
    
    html_files = list(html_dir.glob("**/*.html"))
    print(f"✅ Scraped {len(html_files)} HTML files")
    
    if len(html_files) < 5:
        print("⚠️  Warning: Fewer files than expected. The site structure may have changed.")
    
    # Step 2: Analyze HTML structure with Claude
    print(f"\n{'='*50}")
    print("STEP 2: Analyzing HTML Structure with Claude")
    print(f"{'='*50}")
    print(f"🤖 Claude will analyze 5 representative HTML files")
    print(f"⏱️  Expected duration: 5-8 minutes")
    
    analyze_cmd = [
        "m1f-html2md",
        "analyze",
        str(html_dir),
        "--claude",
        "--project-description", PROJECT_DESCRIPTION
    ]
    
    print("🤖 Using Claude AI for intelligent HTML analysis...")
    success, output = run_command(analyze_cmd, "Analyzing HTML with Claude", capture_output=False)
    
    # Check if Claude created the config file
    # The analyze command creates html2md_config.yaml in the HTML directory
    config_file = html_dir / "html2md_config.yaml"
    use_config = False
    
    if success and config_file.exists():
        print(f"📊 Claude analysis complete")
        print(f"   📌 Using Claude's config: {config_file}")
        use_config = True
    else:
        if not success:
            print("⚠️  Claude analysis failed, using defaults")
        if not config_file.exists():
            print("⚠️  Config file not created, using defaults")
    
    # Step 3: Convert HTML to Markdown
    print(f"\n{'='*50}")
    print("STEP 3: Converting to Markdown")
    print(f"{'='*50}")
    print(f"📄 Converting all {len(html_files)} HTML files to Markdown")
    print(f"⏱️  Expected duration: <1 minute")
    
    convert_cmd = [
        "m1f-html2md",
        "convert",
        str(html_dir),
        "-o", str(markdown_dir)
    ]
    
    # Use Claude's config file if it exists
    if use_config and config_file.exists():
        convert_cmd.extend(["-c", str(config_file)])
        print(f"   📄 Using Claude's configuration file")
    else:
        # Use defaults
        convert_cmd.extend(["--content-selector", CONTENT_SELECTOR])
        for selector in IGNORE_SELECTORS:
            convert_cmd.extend(["--ignore-selectors", selector])
        print(f"   📌 Using default selectors")
    
    success, _ = run_command(convert_cmd, "Converting HTML to Markdown", capture_output=False)
    if not success:
        return 1
    
    # Verify conversion
    md_files = list(markdown_dir.glob("**/*.md"))
    print(f"✅ Converted {len(md_files)} Markdown files")
    
    # Step 4: Run m1f-init in markdown directory
    print(f"\n{'='*50}")
    print("STEP 4: Creating m1f Bundle")
    print(f"{'='*50}")
    print(f"📦 Running m1f-init to create documentation bundle")
    print(f"⏱️  Expected duration: <1 minute")
    
    # Change to markdown directory for m1f-init
    original_output_dir = Path.cwd()
    os.chdir(markdown_dir)
    
    init_cmd = ["m1f-init"]
    success, _ = run_command(init_cmd, "Running m1f-init", capture_output=False)
    
    # Change back
    os.chdir(original_output_dir)
    
    if not success:
        print("❌ m1f-init failed!")
        return 1
    
    # Find the bundle created by m1f-init
    bundle_dir = markdown_dir / "m1f"
    if not bundle_dir.exists():
        print("❌ Bundle directory not created by m1f-init")
        return 1
    
    # Find the documentation bundle file
    bundle_files = list(bundle_dir.glob("*_docs.txt"))
    if not bundle_files:
        # Try to find any .txt file in the m1f directory
        bundle_files = list(bundle_dir.glob("*.txt"))
    
    if not bundle_files:
        print("❌ No bundle file found in m1f directory")
        return 1
    
    # Use the first bundle file found
    bundle_path = bundle_files[0].absolute()
    
    # Get bundle stats
    bundle_size = bundle_path.stat().st_size / (1024 * 1024)  # MB
    
    # Try to estimate tokens
    print("\n📊 Estimating tokens...")
    token_cmd = ["m1f-token-counter", str(bundle_path)]
    success, output = run_command(token_cmd, "Counting tokens")
    
    token_count = "unknown"
    if success and output:
        # Extract token count from output
        import re
        match = re.search(r'(\d+)\s*tokens', output)
        if match:
            token_count = f"{int(match.group(1)):,}"
    
    # Final summary
    print(f"\n{'='*50}")
    print("✅ DOCUMENTATION BUNDLE CREATED")
    print(f"{'='*50}")
    
    print(f"\n📦 Bundle location:")
    print(f"   {bundle_path}")
    
    print(f"\n📊 Bundle statistics:")
    print(f"   Size: {bundle_size:.2f} MB")
    print(f"   Tokens: ~{token_count}")
    print(f"   Source: {len(html_files)} HTML → {len(md_files)} Markdown files")
    
    print(f"\n💡 Usage options:")
    print(f"   1. Create a symlink: ln -s {bundle_path} ~/claude-code-docs.txt")
    print(f"   2. Copy the file: cp {bundle_path} <destination>")
    print(f"   3. Use with Claude: m1f-claude {bundle_path}")
    
    print(f"\n🧹 Cleanup (optional):")
    print(f"   Remove HTML: rm -rf {output_path}/claude-code-html")
    print(f"   Keep Markdown: {markdown_dir} (contains the bundle)")
    
    # Change back to original directory
    os.chdir(original_dir)
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)