# Tailscale Documentation Scraper Example

This example downloads and processes the complete Tailscale documentation from `https://tailscale.com/kb` (~422 HTML pages).

## Prerequisites

- m1f tools installed and on PATH
- Python 3.10+
- ~500 MB free disk space

## Files in this directory

- `scrape_tailscale_docs.py` - Main script to download and process documentation
- `.m1f.tailscale.config.yml` - m1f configuration for creating 11 thematic bundles
- `html2md_config.tailscale.yml` - HTML to Markdown conversion configuration

## Quickstart

```bash
# Download ~422 HTML files and create bundles
python examples/tailscale_doc/scrape_tailscale_docs.py ~/tailscale-docs
```

This will:

1. **Scrape HTML** (~422 files) to `~/tailscale-docs/tailscale-kb-html/`
2. **Convert to Markdown** in `~/tailscale-docs/tailscale-kb-md/`
3. **Create 11 m1f bundles** in `~/tailscale-docs/tailscale-kb-md/m1f/`:
   - `00_complete.txt` - Complete documentation (2.4 MB)
   - `01_getting_started.txt` - Basic installation guides (27 KB)
   - `02_platform_install.txt` - Specialized platforms (374 KB)
   - `03_networking.txt` - Networking & DNS (200 KB)
   - `04_auth_security.txt` - Authentication & Security (418 KB)
   - `05_user_device_mgmt.txt` - User & Device Management (254 KB)
   - `06_remote_access.txt` - SSH, Serve, Funnel (181 KB)
   - `07_cloud_containers.txt` - Cloud & Kubernetes (450 KB)
   - `08_developer.txt` - API & Developer Tools (162 KB)
   - `09_admin_operations.txt` - Admin & Operations (257 KB)
   - `10_concepts_reference.txt` - Concepts & Reference (542 KB)

## Options

- `--force-download`: Re-download HTML even if already present
- `--skip-download`: Skip download if HTML files already exist
- `--delay <seconds>`: Request delay between pages (default: 3s)
- `--parallel`: Enable parallel HTML→Markdown conversion (default: on)

## Examples

### Skip download if HTML already exists
```bash
python examples/tailscale_doc/scrape_tailscale_docs.py \
  ~/tailscale-docs \
  --skip-download
```

### Force re-download everything
```bash
python examples/tailscale_doc/scrape_tailscale_docs.py \
  ~/tailscale-docs \
  --force-download
```

### Custom delay for polite scraping
```bash
python examples/tailscale_doc/scrape_tailscale_docs.py \
  ~/tailscale-docs \
  --delay 5
```

## Using the bundles

### Use complete documentation with Claude
```bash
m1f-claude ~/tailscale-docs/tailscale-kb-md/m1f/00_complete.txt
```

### Use specific topic bundle
```bash
# For networking questions
m1f-claude ~/tailscale-docs/tailscale-kb-md/m1f/03_networking.txt

# For Kubernetes questions
m1f-claude ~/tailscale-docs/tailscale-kb-md/m1f/07_cloud_containers.txt

# For security questions
m1f-claude ~/tailscale-docs/tailscale-kb-md/m1f/04_auth_security.txt
```

### Create symlinks for easy access
```bash
ln -s ~/tailscale-docs/tailscale-kb-md/m1f/00_complete.txt ~/tailscale-complete.txt
ln -s ~/tailscale-docs/tailscale-kb-md/m1f/03_networking.txt ~/tailscale-network.txt
```

## Time estimates

- **Full download**: ~21 minutes (422 files × 3s delay)
- **HTML to Markdown conversion**: ~1-2 minutes
- **Bundle creation**: <1 minute
- **Total (first run)**: ~25 minutes
- **Subsequent runs** (with --skip-download): ~3 minutes

## Disk usage

- HTML files: ~50 MB
- Markdown files: ~15 MB
- m1f bundles: ~5.3 MB total (2.4 MB complete + thematic bundles)
- Total: ~70 MB

## Configuration files

### `.m1f.tailscale.config.yml`
Defines the 11 bundles structure:
- Complete bundle with all documentation
- 10 thematic bundles for specific topics

### `html2md_config.tailscale.yml`
Optimized HTML extraction settings for Tailscale's documentation structure:
- Main content selector
- Elements to ignore (navigation, headers, footers)
- Processing options

## Cleanup (optional)

After creating the bundles, you can remove intermediate files:

```bash
# Remove HTML files (save 50 MB)
rm -rf ~/tailscale-docs/tailscale-kb-html

# Keep markdown files - they contain the bundles
# ~/tailscale-docs/tailscale-kb-md/
```

## Troubleshooting

### "Command not found" errors
Make sure m1f tools are installed:
```bash
# Linux/macOS
./scripts/install.sh

# Windows
.\scripts\install.ps1
```

### Fewer files than expected
The script expects ~422 HTML files. If significantly fewer are downloaded:
- Check your internet connection
- The site structure may have changed
- Try with `--force-download` to re-download

### Bundle creation fails
- Ensure `.m1f.tailscale.config.yml` exists in this directory
- Check that `html2md_config.tailscale.yml` exists
- Verify m1f-update is installed and working

## Notes

- The script respects robots.txt and uses polite delays
- GET parameters are stripped to avoid duplicate content
- The bundles are optimized for use with Claude and other LLMs
- Each thematic bundle focuses on specific aspects for targeted assistance