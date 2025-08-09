#!/usr/bin/env python3
"""
Tailscale Documentation Scraper
=================================

A focused Python script to scrape and bundle Tailscale documentation.
Works on both Linux and Windows.

This script:
1. Scrapes Tailscale docs starting at tailscale.com/kb  
2. Converts HTML to clean Markdown using html2md_config.tailscale.yml
3. Creates m1f bundles using .m1f.tailscale.config.yml
4. Returns the path to the created bundles

Usage:
    # Basic usage (downloads ~422 HTML files):
    python scrape_tailscale_docs.py ~/tailscale-docs

    # Force re-download and regenerate:
    python scrape_tailscale_docs.py ~/tailscale-docs --force-download

    # Skip download if HTML already exists:
    python scrape_tailscale_docs.py ~/tailscale-docs --skip-download

    # With logging to file and console:
    python scrape_tailscale_docs.py ~/tailscale-docs 2>&1 | tee scrape_log.txt
"""

import subprocess
import sys
import os
from pathlib import Path
import argparse
import shutil


# Configuration - tailored for Tailscale
TAILSCALE_DOCS_URL = "https://tailscale.com/kb"
SCRAPE_DELAY = 3  # Respectful delay between requests
EXPECTED_HTML_FILES = 422  # Approximately how many HTML files we expect
PROJECT_NAME = "Tailscale Documentation"
PROJECT_DESCRIPTION = "Official documentation and knowledge base for Tailscale"


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


def copy_config_file(config_name, source_dir, target_dir):
    """Copy config file from source to target directory"""
    source_config = source_dir / config_name
    target_config = target_dir / config_name
    
    if not source_config.exists():
        print(f"⚠️  Config file not found: {source_config}")
        return None
        
    try:
        shutil.copy2(str(source_config), str(target_config))
        print(f"✅ Copied {config_name} to: {target_config}")
        return target_config
    except Exception as e:
        print(f"❌ Failed to copy config file: {e}")
        return None


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Scrape Tailscale documentation and create a bundle",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Standard usage (downloads ~422 HTML files):
    python scrape_tailscale_docs.py ~/tailscale-docs
    
    # Force re-download:
    python scrape_tailscale_docs.py ~/tailscale-docs --force-download
    
    # Skip download if HTML already exists:
    python scrape_tailscale_docs.py ~/tailscale-docs --skip-download
    
    # With logging:
    python scrape_tailscale_docs.py ~/tailscale-docs 2>&1 | tee scrape_log.txt
    
This will create the documentation bundle in the specified directory.
The final bundles will be in the 'm1f' subdirectory of the markdown folder.

Expected result:
- Downloads ~422 HTML files from Tailscale KB
- Converts them to Markdown using html2md_config.tailscale.yml
- Creates 11 bundles (complete + 10 thematic bundles) using .m1f.tailscale.config.yml
        """,
    )
    parser.add_argument("path", help="Target directory path (required)")
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Force re-download even if HTML files exist",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip download step if HTML files already exist",
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
    script_dir = Path(__file__).parent

    print("🧭 Tailscale Documentation Scraper")
    print("=" * 50)
    print(f"Target: {TAILSCALE_DOCS_URL}")
    print(f"Output directory: {output_path}")
    print(f"Expected files: ~{EXPECTED_HTML_FILES} HTML pages")

    # Estimated time
    if args.skip_download:
        estimated_time = "~2-3 minutes (conversion + bundling only)"
    else:
        estimated_time = f"~{(EXPECTED_HTML_FILES * args.delay) // 60 + 5} minutes (full process)"
    
    print(f"Total time: {estimated_time}")
    print("=" * 50)

    # Create output directory if needed
    output_path.mkdir(parents=True, exist_ok=True)

    # Save current directory and change to output
    original_dir = Path.cwd()
    os.chdir(output_path)

    # Paths for intermediate files
    html_dir = Path("html")
    markdown_dir = Path("tailscale-kb-md")

    print(f"\n📁 Working directory: {output_path.absolute()}")

    # Check if HTML files already exist
    final_html_dir = Path("tailscale-kb-html")
    skip_scraping = args.skip_download

    if final_html_dir.exists() and not args.force_download:
        existing_html_files = list(final_html_dir.glob("**/*.html"))
        if len(existing_html_files) >= 50:  # Allow some margin
            print(f"📁 Found existing HTML files: {len(existing_html_files)} files")
            if args.skip_download:
                print("⏭️  Skipping download step as requested")
            else:
                print("⏭️  Skipping download step (use --force-download to re-download)")
            skip_scraping = True
            html_dir = final_html_dir

    if not skip_scraping:
        # Step 1: Scrape Tailscale documentation
        print(f"\n{'='*50}")
        print("STEP 1: Scraping Tailscale Documentation")
        print(f"{'='*50}")
        print(f"📄 Will download ~{EXPECTED_HTML_FILES} HTML pages from the Tailscale KB")
        print(
            f"⏱️  Expected duration: {(EXPECTED_HTML_FILES * args.delay) // 60} minutes ({args.delay}s delay between pages)"
        )

        scrape_cmd = [
            "m1f-scrape",
            TAILSCALE_DOCS_URL,
            "-o",
            str(html_dir),
            "--allowed-path",
            "/kb",
            "--request-delay",
            str(args.delay),
            "--ignore-get-params",
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

        # Find the actual scraped directory (tailscale.com/kb/...)
        scraped_root = html_dir / "tailscale.com"
        scraped_kb = scraped_root / "kb"
        if scraped_kb.exists():
            print(f"📁 Found scraped content in: {scraped_kb}")
            # Move content up and rename
            if final_html_dir.exists():
                shutil.rmtree(final_html_dir)
            shutil.move(str(scraped_kb), str(final_html_dir))
            # Clean up empty directories
            try:
                if scraped_root.exists():
                    shutil.rmtree(scraped_root)
            except Exception:
                pass
            try:
                if html_dir.exists() and not any(html_dir.iterdir()):
                    shutil.rmtree(html_dir)
            except Exception:
                pass
            html_dir = final_html_dir
            print(f"✅ Moved content to: {html_dir}")

    html_files = list(html_dir.glob("**/*.html"))
    print(f"✅ Found {len(html_files)} HTML files")

    if len(html_files) < EXPECTED_HTML_FILES * 0.8:  # Allow 20% margin
        print(
            f"⚠️  Warning: Fewer files than expected ({len(html_files)} vs ~{EXPECTED_HTML_FILES}). The site structure may have changed."
        )

    # Step 2: Copy html2md config
    print(f"\n{'='*50}")
    print("STEP 2: Preparing HTML to Markdown Conversion")
    print(f"{'='*50}")
    
    html2md_config = copy_config_file("html2md_config.tailscale.yml", script_dir, output_path)
    if not html2md_config:
        print("❌ Failed to copy html2md_config.tailscale.yml")
        return 1

    # Step 3: Convert HTML to Markdown
    print(f"\n{'='*50}")
    print("STEP 3: Converting to Markdown")
    print(f"{'='*50}")
    print(f"📄 Converting {len(html_files)} HTML files to Markdown")
    if args.parallel:
        print(f"⚡ Using parallel processing for faster conversion")
    print(f"⏱️  Expected duration: 1-2 minutes")

    convert_cmd = [
        "m1f-html2md", 
        "convert", 
        str(html_dir), 
        "-o", 
        str(markdown_dir),
        "-c",
        str(html2md_config)
    ]

    # Add parallel processing flag
    if args.parallel:
        convert_cmd.append("--parallel")

    success, _ = run_command(
        convert_cmd, "Converting HTML to Markdown", capture_output=False
    )
    if not success:
        print("❌ Failed to convert HTML to Markdown")
        return 1

    # Verify conversion
    if not markdown_dir.exists():
        print("❌ Markdown directory was not created!")
        return 1

    md_files = list(markdown_dir.glob("**/*.md"))
    if len(md_files) == 0:
        print("❌ No Markdown files were created!")
        return 1

    print(f"✅ Converted {len(md_files)} Markdown files")

    # Step 4: Copy m1f config and create bundles
    print(f"\n{'='*50}")
    print("STEP 4: Creating m1f Bundles")
    print(f"{'='*50}")
    
    # Copy the m1f config to the markdown directory
    m1f_config = copy_config_file(".m1f.tailscale.config.yml", script_dir, markdown_dir)
    if not m1f_config:
        print("❌ Failed to copy .m1f.tailscale.config.yml")
        return 1
    
    # Rename to .m1f.config.yml in the target directory
    target_config = markdown_dir / ".m1f.config.yml"
    try:
        shutil.move(str(m1f_config), str(target_config))
        print(f"✅ Renamed config to: {target_config}")
    except Exception as e:
        print(f"❌ Failed to rename config: {e}")
        return 1

    print(f"📦 Running m1f-update to create documentation bundles")
    print(f"   Creating 11 bundles (complete + 10 thematic)")
    print(f"⏱️  Expected duration: <1 minute")

    # Change to markdown directory for m1f-update
    os.chdir(markdown_dir)

    update_cmd = ["m1f-update"]
    success, _ = run_command(update_cmd, "Creating m1f bundles", capture_output=False)

    # Change back
    os.chdir(output_path)

    if not success:
        print("❌ m1f-update failed!")
        return 1

    # Find the bundle directory
    bundle_dir = markdown_dir / "m1f"
    if not bundle_dir.exists():
        print("❌ Bundle directory not created by m1f-update")
        return 1

    # List all bundle files
    bundle_files = sorted(list(bundle_dir.glob("*.txt")))
    if not bundle_files:
        print("❌ No bundle files found in m1f directory")
        return 1

    # Get bundle stats
    total_size = 0
    print("\n📦 Created bundles:")
    for bundle_file in bundle_files:
        if bundle_file.name != "m1f.txt":  # Skip symlink
            size_mb = bundle_file.stat().st_size / (1024 * 1024)
            total_size += size_mb
            print(f"   - {bundle_file.name}: {size_mb:.2f} MB")

    # Final summary
    print(f"\n{'='*50}")
    print("✅ DOCUMENTATION BUNDLES CREATED")
    print(f"{'='*50}")

    print(f"\n📦 Bundle location:")
    print(f"   {bundle_dir}")

    print(f"\n📊 Bundle statistics:")
    print(f"   Total size: {total_size:.2f} MB")
    print(f"   Bundle count: {len(bundle_files)} files")
    print(f"   Source: {len(html_files)} HTML → {len(md_files)} Markdown files")

    print(f"\n📋 Bundle files:")
    print(f"   00_complete.txt     - Complete documentation (2.4 MB)")
    print(f"   01_getting_started.txt - Basic installation guides")
    print(f"   02_platform_install.txt - Specialized platform installations")
    print(f"   03_networking.txt    - Networking & DNS")
    print(f"   04_auth_security.txt - Authentication & Security")
    print(f"   05_user_device_mgmt.txt - User & Device Management")
    print(f"   06_remote_access.txt - SSH, Serve, Funnel")
    print(f"   07_cloud_containers.txt - Cloud & Kubernetes")
    print(f"   08_developer.txt    - API & Developer Tools")
    print(f"   09_admin_operations.txt - Admin & Operations")
    print(f"   10_concepts_reference.txt - Concepts & Reference")

    print(f"\n💡 Usage options:")
    print(f"   1. Use complete bundle: m1f-claude {bundle_dir}/00_complete.txt")
    print(f"   2. Use specific bundle: m1f-claude {bundle_dir}/03_networking.txt")
    print(f"   3. Copy bundles: cp -r {bundle_dir} <destination>")

    print(f"\n🧹 Cleanup (optional):")
    print(f"   Remove HTML: rm -rf {output_path}/tailscale-kb-html")
    print(f"   Keep Markdown: {markdown_dir} (contains the bundles)")

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