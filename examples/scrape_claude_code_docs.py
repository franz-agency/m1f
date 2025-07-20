#!/usr/bin/env python3
"""
Claude Code Documentation Scraper
=================================

A focused Python script to scrape and bundle Claude Code documentation.
Works on both Linux and Windows.

This script:
1. Scrapes Claude Code docs from docs.anthropic.com
2. Converts HTML to clean Markdown
3. Runs m1f-init to prepare the bundle
4. Runs m1f-claude with advanced setup
5. Creates claude-code-doc.txt for Claude to use
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
BUNDLE_NAME = "claude-code-doc.txt"
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
    parser = argparse.ArgumentParser(description="Scrape Claude Code documentation")
    parser.add_argument("path", nargs="?", help="Output directory path (optional)")
    args = parser.parse_args()
    
    # Determine output directory
    if args.path:
        output_path = Path(args.path).absolute()
    else:
        output_path = Path.cwd()
    
    print("🤖 Claude Code Documentation Scraper")
    print("=" * 50)
    print(f"Target: {CLAUDE_DOCS_URL}")
    print(f"Output: {output_path / BUNDLE_NAME}")
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
    print(f"⏱️  This will take ~5-10 minutes due to {SCRAPE_DELAY}s delays...")
    
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
    config_file = Path("html2md_extract_config.yaml")
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
    print("STEP 4: Initializing m1f Bundle")
    print(f"{'='*50}")
    
    # Change to markdown directory for m1f-init
    original_output_dir = Path.cwd()
    os.chdir(markdown_dir)
    
    init_cmd = ["m1f-init"]
    success, _ = run_command(init_cmd, "Running m1f-init", capture_output=False)
    
    # Change back
    os.chdir(original_output_dir)
    
    if not success:
        print("⚠️  m1f-init failed, continuing anyway...")
    
    # Step 5: Create bundle
    print(f"\n{'='*50}")
    print("STEP 5: Creating Bundle")
    print(f"{'='*50}")
    
    bundle_path = Path(BUNDLE_NAME)
    
    bundle_cmd = [
        "m1f",
        "-s", str(markdown_dir),
        "-o", str(bundle_path),
        "-v"
    ]
    
    success, _ = run_command(bundle_cmd, "Creating bundle", capture_output=False)
    if not success:
        return 1
    
    # Verify bundle
    if not bundle_path.exists():
        print("❌ Bundle file not created")
        return 1
    
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
    
    # Step 6: Run m1f-claude with advanced setup
    print(f"\n{'='*50}")
    print("STEP 6: Running m1f-claude Advanced Setup")
    print(f"{'='*50}")
    
    # Prepare input for m1f-claude
    claude_input = f"{PROJECT_NAME}\n{PROJECT_DESCRIPTION}\n"
    
    claude_cmd = [
        "m1f-claude",
        str(bundle_path),
        "--setup"
    ]
    
    print(f"📝 Providing project info:")
    print(f"   Name: {PROJECT_NAME}")
    print(f"   Description: {PROJECT_DESCRIPTION}")
    
    try:
        # Run m1f-claude with input
        process = subprocess.Popen(
            claude_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=claude_input)
        
        if process.returncode == 0:
            print("✅ m1f-claude advanced setup completed")
        else:
            print("⚠️  m1f-claude setup had issues, but bundle is still created")
            if stderr:
                print(f"   Error: {stderr}")
    except Exception as e:
        print(f"⚠️  Could not run m1f-claude: {e}")
        print("   Bundle is still created and usable")
    
    # Step 7: Verify content
    print(f"\n{'='*50}")
    print("STEP 7: Verifying Content")
    print(f"{'='*50}")
    
    with open(bundle_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for expected Claude Code content
    checks = {
        "Keyboard shortcuts": ["Ctrl+", "Cmd+"],
        "CLI parameters": ["allowedTools", "disallowedTools"],
        "MCP servers": ["mcp", "server"],
        "Interactive mode": ["interactive", "mode"],
        "Slash commands": ["slash", "command"]
    }
    
    print("🔍 Content verification:")
    all_good = True
    for check_name, keywords in checks.items():
        found = sum(1 for kw in keywords if kw in content)
        if found > 0:
            print(f"  ✅ {check_name}: Found {found}/{len(keywords)} keywords")
        else:
            print(f"  ❌ {check_name}: Not found")
            all_good = False
    
    # Final summary
    print(f"\n{'='*50}")
    print("📝 FINAL SUMMARY")
    print(f"{'='*50}")
    
    print(f"✅ Bundle created successfully!")
    print(f"📁 Location: {bundle_path.absolute()}")
    print(f"📏 Size: {bundle_size:.2f} MB")
    print(f"🔢 Tokens: ~{token_count}")
    print(f"📄 Source files: {len(html_files)} HTML → {len(md_files)} Markdown")
    
    if all_good:
        print(f"\n✨ Content verification: PASSED")
    else:
        print(f"\n⚠️  Content verification: Some expected content missing")
    
    print(f"\n💡 Usage:")
    print(f"   m1f-claude {bundle_path.absolute()}")
    
    print(f"\n🧹 Cleanup (optional):")
    print(f"   Remove HTML files: rm -rf claude-code-html (Linux) or rmdir /s claude-code-html (Windows)")
    print(f"   Remove Markdown files: rm -rf {markdown_dir} (Linux) or rmdir /s {markdown_dir} (Windows)")
    
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