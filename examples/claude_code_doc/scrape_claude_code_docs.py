#!/usr/bin/env python3
"""
Claude Code Documentation Scraper
=================================

A focused Python script to scrape and bundle Claude Code documentation.
Works on both Linux and Windows.

This script:
1. Scrapes Claude Code docs from docs.anthropic.com
2. Converts HTML to clean Markdown (optionally using existing config)
3. Runs m1f-init to create the documentation bundle
4. Returns the path to the created bundle

Usage:
    # Basic usage (with Claude analysis):
    python scrape_claude_code_docs.py ~/claude-docs

    # Use existing config (skip Claude analysis):
    python scrape_claude_code_docs.py ~/claude-docs --use-config html2md_claude_code_doc.config.yml

    # Force re-download and regenerate config:
    python scrape_claude_code_docs.py ~/claude-docs --force-download

    # With logging to file and console:
    python scrape_claude_code_docs.py ~/claude-docs 2>&1 | tee scrape_log.txt
"""

import subprocess
import sys
import os
from pathlib import Path
import argparse
import shutil
from datetime import datetime


# Configuration - all hardcoded for Claude Code
CLAUDE_DOCS_URL = "https://docs.anthropic.com/en/docs/claude-code"
SCRAPE_DELAY = 5  # Respectful delay between requests
CONTENT_SELECTOR = "main"
IGNORE_SELECTORS = ["nav", "header", "footer"]
PROJECT_NAME = "Claude Code Documentation"
PROJECT_DESCRIPTION = (
    "Official documentation for Claude Code - Anthropic's AI coding assistant"
)


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


def copy_config_file(config_path, target_dir):
    """Copy config file to target directory"""
    target_config = target_dir / "html2md_config.yaml"
    try:
        shutil.copy2(str(config_path), str(target_config))
        print(f"✅ Copied config file to: {target_config}")
        return target_config
    except Exception as e:
        print(f"❌ Failed to copy config file: {e}")
        return None


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Scrape Claude Code documentation and create a bundle",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # With Claude analysis (default):
    python scrape_claude_code_docs.py ~/claude-docs
    
    # Use existing config (skip Claude analysis - faster):
    python scrape_claude_code_docs.py ~/claude-docs --use-config html2md_claude_code_doc.config.yml
    
    # Force re-download:
    python scrape_claude_code_docs.py ~/claude-docs --force-download
    
    # With logging:
    python scrape_claude_code_docs.py ~/claude-docs 2>&1 | tee scrape_log.txt
    
This will create the documentation bundle in the specified directory.
The final bundle will be in the 'm1f' subdirectory of the markdown folder.
        """,
    )
    parser.add_argument("path", help="Target directory path (required)")
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Force re-download even if HTML files exist",
    )
    parser.add_argument(
        "--use-config",
        metavar="CONFIG_FILE",
        help="Use existing config file (skip Claude analysis)",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        default=True,
        help="Enable parallel processing for HTML conversion (default: True)",
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=SCRAPE_DELAY,
        help=f"Delay between scraping requests in seconds (default: {SCRAPE_DELAY})",
    )
    args = parser.parse_args()

    # Determine output directory
    output_path = Path(args.path).absolute()

    print("🤖 Claude Code Documentation Scraper")
    print("=" * 50)
    print(f"Target: {CLAUDE_DOCS_URL}")
    print(f"Output directory: {output_path}")

    # Calculate estimated time based on options
    if args.use_config:
        if (
            output_path.joinpath("claude-code-html").exists()
            and not args.force_download
        ):
            estimated_time = "~1-2 minutes (using existing HTML + config)"
        else:
            estimated_time = (
                f"~{(31 * args.delay) // 60 + 2} minutes (scraping + conversion)"
            )
    else:
        estimated_time = f"~{(31 * args.delay) // 60 + 10} minutes (full process)"

    print(f"Total time: {estimated_time}")
    if args.use_config:
        print(f"Config: {args.use_config} (skipping Claude analysis)")
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

    # Check if HTML files already exist
    final_html_dir = Path("claude-code-html")
    skip_scraping = False

    if final_html_dir.exists() and not args.force_download:
        existing_html_files = list(final_html_dir.glob("**/*.html"))
        if len(existing_html_files) >= 25:  # Allow some margin for missing files
            print(f"📁 Found existing HTML files: {len(existing_html_files)} files")
            print("⏭️  Skipping download step (use --force-download to re-download)")
            skip_scraping = True
            html_dir = final_html_dir

    if not skip_scraping:
        # Step 1: Scrape Claude Code documentation
        print(f"\n{'='*50}")
        print("STEP 1: Scraping Claude Code Documentation")
        print(f"{'='*50}")
        print(f"📄 Will download ~31 HTML pages from Claude Code docs")
        print(
            f"⏱️  Expected duration: {(31 * args.delay) // 60} minutes ({args.delay}s delay between pages)"
        )

        scrape_cmd = [
            "m1f-scrape",
            CLAUDE_DOCS_URL,
            "-o",
            str(html_dir),
            "--request-delay",
            str(args.delay),
            "-v",
        ]

        success, _ = run_command(
            scrape_cmd, "Scraping documentation", capture_output=False
        )
        if not success:
            print("\n💡 Tip: Make sure m1f tools are installed:")
            print("   Run: ./scripts/install.sh (Linux/macOS)")
            print("   Run: .\\scripts\\install.ps1 (Windows)")
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
            if final_html_dir.exists():
                shutil.rmtree(final_html_dir)
            shutil.move(str(scraped_dir), str(final_html_dir))
            # Clean up empty directories
            shutil.rmtree(html_dir)
            html_dir = final_html_dir
            print(f"✅ Moved content to: {html_dir}")

    html_files = list(html_dir.glob("**/*.html"))
    print(f"✅ Found {len(html_files)} HTML files")

    if len(html_files) < 5:
        print(
            "⚠️  Warning: Fewer files than expected. The site structure may have changed."
        )

    # Check if we should skip analysis if markdown already exists
    skip_conversion = False
    if markdown_dir.exists() and not args.force_download:
        existing_md_files = list(markdown_dir.glob("**/*.md"))
        if len(existing_md_files) >= 25:
            if args.use_config:
                print(
                    f"\n📁 Found existing Markdown files: {len(existing_md_files)} files"
                )
                print("🔄 Re-converting with provided config file")
                # Create backup directory with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = output_path / f"claude-code-markdown_backup_{timestamp}"
                shutil.move(str(markdown_dir), str(backup_dir))
                print(f"📦 Backed up existing markdown to: {backup_dir.name}")
                # Don't skip conversion when using config
                skip_conversion = False
            else:
                print(
                    f"\n📁 Found existing Markdown files: {len(existing_md_files)} files"
                )
                print("⏭️  Skipping HTML analysis and conversion")
                skip_conversion = True
                md_files = existing_md_files

    if not skip_conversion:
        # Handle config file
        config_file = None
        use_config = False

        if args.use_config:
            # Use provided config file
            config_source = Path(args.use_config)
            if not config_source.is_absolute():
                # Try relative to original directory first
                config_source = original_dir / config_source
                if not config_source.exists():
                    # Try relative to script directory
                    script_dir = Path(__file__).parent
                    config_source = script_dir / args.use_config

            if config_source.exists():
                config_file = copy_config_file(config_source, html_dir)
                if config_file:
                    use_config = True
                    print(f"📊 Using existing config file (skipping Claude analysis)")
                else:
                    print(
                        "⚠️  Failed to copy config file, will fall back to Claude analysis"
                    )
            else:
                print(f"⚠️  Config file not found: {args.use_config}")
                print("   Will fall back to Claude analysis")

        if not use_config:
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
                "--project-description",
                PROJECT_DESCRIPTION,
            ]

            print("🤖 Using Claude AI for intelligent HTML analysis...")
            success, output = run_command(
                analyze_cmd, "Analyzing HTML with Claude", capture_output=False
            )

            # Check if Claude created the config file
            # The analyze command creates html2md_config.yaml in the HTML directory
            config_file = html_dir / "html2md_config.yaml"

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
        if args.parallel:
            print(f"⚡ Using parallel processing for faster conversion")
        print(f"⏱️  Expected duration: <1 minute")

        convert_cmd = ["m1f-html2md", "convert", str(html_dir), "-o", str(markdown_dir)]

        # Use config file if available
        if use_config and config_file and config_file.exists():
            convert_cmd.extend(["-c", str(config_file)])
            print(f"   📄 Using configuration file: {config_file.name}")
        else:
            # Use defaults
            convert_cmd.extend(["--content-selector", CONTENT_SELECTOR])
            for selector in IGNORE_SELECTORS:
                convert_cmd.extend(["--ignore-selectors", selector])
            print(f"   📌 Using default selectors")

        # Add parallel processing flag
        if args.parallel:
            convert_cmd.append("--parallel")

        success, _ = run_command(
            convert_cmd, "Converting HTML to Markdown", capture_output=False
        )
        if not success:
            return 1

        # Verify conversion
        if not markdown_dir.exists():
            print("❌ Markdown directory was not created!")
            print("   This might be due to configuration issues.")
            print("   Trying conversion with default settings...")

            # Retry with default settings
            convert_cmd = [
                "m1f-html2md",
                "convert",
                str(html_dir),
                "-o",
                str(markdown_dir),
            ]
            convert_cmd.extend(["--content-selector", CONTENT_SELECTOR])
            for selector in IGNORE_SELECTORS:
                convert_cmd.extend(["--ignore-selectors", selector])

            if args.parallel:
                convert_cmd.append("--parallel")

            success, _ = run_command(
                convert_cmd,
                "Converting HTML to Markdown (retry with defaults)",
                capture_output=False,
            )

            if not success or not markdown_dir.exists():
                print("❌ Failed to convert HTML to Markdown")
                return 1

        md_files = list(markdown_dir.glob("**/*.md"))
        if len(md_files) == 0:
            print("❌ No Markdown files were created!")
            print("   Check if the HTML files are in the expected location.")
            # List what's in the HTML directory
            print(f"\n📁 Contents of {html_dir}:")
            for item in html_dir.iterdir():
                print(f"   - {item.name}")
            return 1

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

        match = re.search(r"(\d+)\s*tokens", output)
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

    # Save config if it was generated by Claude
    if use_config and config_file and config_file.exists() and not args.use_config:
        config_backup = output_path / "html2md_claude_code_doc.config.yml"
        try:
            shutil.copy2(str(config_file), str(config_backup))
            print(f"\n💾 Config saved: {config_backup}")
            print(
                f"   Use --use-config {config_backup.name} next time to skip Claude analysis"
            )
        except:
            pass

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
