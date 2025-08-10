# webscraper (Website Downloader)

A modern web scraping tool for downloading websites with multiple backend
options, async I/O, and intelligent crawling capabilities.

## Overview

The webscraper tool provides a robust solution for downloading websites for
offline viewing and analysis. Built with Python 3.10+ and modern async
architecture, it features pluggable scraper backends for different use cases.

**Primary Use Case**: Download online documentation to make it available to LLMs
(like Claude) for analysis and reference. The downloaded HTML files can be
converted to Markdown with html2md, then bundled into a single file with m1f for
optimal LLM context usage.

## Key Features

- **Multiple Scraper Backends**: Choose from BeautifulSoup (default), HTTrack,
  Scrapy, Playwright, or Selectolax
- **Async I/O**: High-performance concurrent downloading
- **Intelligent Crawling**: Automatically respects robots.txt, follows
  redirects, handles encoding
- **Duplicate Prevention**: Three-layer deduplication system:
  - Canonical URL checking (enabled by default)
  - Content-based deduplication (enabled by default)
  - GET parameter normalization (optional with `--ignore-get-params`)
- **Metadata Preservation**: Saves HTTP headers and metadata alongside HTML
  files
- **Domain Restriction**: Automatically restricts crawling to the starting
  domain
- **Subdirectory Restriction**: When URL contains a path, only scrapes within
  that subdirectory
- **Rate Limiting**: Configurable delays between requests
- **Progress Tracking**: Real-time download progress with file listing
- **Resume Support**: Interrupt and resume scraping sessions with SQLite
  tracking

## Quick Start

```bash
# Basic website download
m1f-scrape https://example.com -o ./downloaded_html

# Download with specific depth and page limits
m1f-scrape https://example.com -o ./html \
  --max-pages 50 \
  --max-depth 3

# Use different scraper backend
m1f-scrape https://example.com -o ./html --scraper httrack

# List downloaded files after completion (limited to 30 files for large sites)
m1f-scrape https://example.com -o ./html --list-files

# Save all scraped URLs to a file for later analysis
m1f-scrape https://example.com -o ./html --save-urls ./scraped_urls.txt

# Save list of all downloaded files to a file
m1f-scrape https://example.com -o ./html --save-files ./file_list.txt

# Resume interrupted scraping (with verbose mode to see progress)
m1f-scrape https://example.com -o ./html -v

# Force rescrape to update content (ignores cache)
m1f-scrape https://example.com -o ./html --force-rescrape

# Clear URLs and start fresh (keeps content checksums)
m1f-scrape https://example.com -o ./html --clear-urls
```

## Command Line Interface

```bash
m1f-scrape <url> -o <output> [options]
```

### Required Arguments

| Option         | Description                |
| -------------- | -------------------------- |
| `url`          | URL to start scraping from |
| `-o, --output` | Output directory           |

### Optional Arguments

| Option                  | Description                                                   | Default       |
| ----------------------- | ------------------------------------------------------------- | ------------- |
| `--scraper`             | Scraper backend to use (choices: httrack, beautifulsoup, bs4, | beautifulsoup |
|                         | selectolax, httpx, scrapy, playwright)                        |               |
| `--scraper-config`      | Path to scraper-specific config file (YAML/JSON)              | None          |
| `--max-depth`           | Maximum crawl depth                                           | 5             |
| `--max-pages`           | Maximum pages to crawl (-1 for unlimited)                     | 10000         |
| `--allowed-path`        | Restrict crawling to this path (legacy, single path)          | None          |
| `--allowed-paths`       | Restrict crawling to multiple paths (new, space-separated)    | None          |
| `--request-delay`       | Delay between requests in seconds (for Cloudflare protection) | 15.0          |
| `--concurrent-requests` | Number of concurrent requests (for Cloudflare protection)     | 2             |
| `--user-agent`          | Custom user agent string                                      | Mozilla/5.0   |
| `--ignore-get-params`   | Ignore GET parameters in URLs (e.g., ?tab=linux)              | False         |
| `--ignore-canonical`    | Ignore canonical URL tags (checking is enabled by default)    | False         |
| `--ignore-duplicates`   | Ignore duplicate content detection (enabled by default)       | False         |
| `--clear-urls`          | Clear all URLs from database and start fresh                  | False         |
| `--force-rescrape`      | Force rescraping of all URLs (ignores cached content)         | False         |
| `--list-files`          | List all downloaded files after completion (limited display)  | False         |
| `--save-urls`           | Save all scraped URLs to a file (one per line)                | None          |
| `--save-files`          | Save list of all downloaded files to a file (one per line)    | None          |
| `-v, --verbose`         | Enable verbose output (file listing limited to 30 files)      | False         |
| `-q, --quiet`           | Suppress all output except errors                             | False         |
| `--show-db-stats`       | Show scraping statistics from the database                    | False         |
| `--show-errors`         | Show URLs that had errors during scraping                     | False         |
| `--show-scraped-urls`   | List all scraped URLs from the database                       | False         |
| `--show-sessions`       | Show all scraping sessions with basic info                    | False         |
| `--show-sessions-detailed` | Show detailed information for all sessions                 | False         |
| `--clear-session`       | Clear a specific session by ID                                | None          |
| `--clear-last-session`  | Clear the most recent scraping session                        | False         |
| `--cleanup-sessions`    | Clean up orphaned sessions from crashes                       | False         |
| `--version`             | Show version information and exit                             | -             |

## Scraper Backends

### BeautifulSoup (default)

- **Best for**: General purpose scraping, simple websites
- **Features**: Fast HTML parsing, good encoding detection
- **Limitations**: No JavaScript support

```bash
m1f-scrape https://example.com -o ./html --scraper beautifulsoup
```

### HTTrack

- **Best for**: Complete website mirroring, preserving structure
- **Features**: External links handling, advanced mirroring options
- **Limitations**: Requires HTTrack to be installed separately

```bash
m1f-scrape https://example.com -o ./html --scraper httrack
```

### Scrapy

- **Best for**: Large-scale crawling, complex scraping rules
- **Features**: Advanced crawling settings, middleware support
- **Limitations**: More complex configuration

```bash
m1f-scrape https://example.com -o ./html --scraper scrapy
```

### Playwright

- **Best for**: JavaScript-heavy sites, SPAs
- **Features**: Full browser automation, JavaScript execution
- **Limitations**: Slower, requires more resources

```bash
m1f-scrape https://example.com -o ./html --scraper playwright
```

### Selectolax

- **Best for**: Speed-critical applications
- **Features**: Fastest HTML parsing, minimal overhead
- **Limitations**: Basic feature set

```bash
m1f-scrape https://example.com -o ./html --scraper selectolax
```

## Usage Examples

### Basic Website Download

```bash
# Download a simple website
m1f-scrape https://docs.example.com -o ./docs_html

# Download with verbose output
m1f-scrape https://docs.example.com -o ./docs_html -v
```

### Canonical URL Checking

By default, the scraper checks for canonical URLs to avoid downloading duplicate
content:

```bash
# Pages with different canonical URLs are automatically skipped
m1f-scrape https://example.com -o ./html

# Ignore canonical tags if you want all page versions
m1f-scrape https://example.com -o ./html --ignore-canonical
```

When enabled (default), the scraper:

- Checks the `<link rel="canonical">` tag on each page
- Skips pages where the canonical URL differs from the current URL
- Prevents downloading duplicate content (e.g., print versions, mobile versions)
- Logs skipped pages with their canonical URLs for transparency

This is especially useful for sites that have multiple URLs pointing to the same
content.

### Content Deduplication

By default, the scraper detects and skips pages with duplicate content based on
text-only checksums:

```bash
# Content deduplication is enabled by default
m1f-scrape https://example.com -o ./html

# Disable content deduplication if needed
m1f-scrape https://example.com -o ./html --ignore-duplicates
```

This feature:

- Enabled by default to avoid downloading duplicate content
- Extracts plain text from HTML (removes all tags, scripts, styles)
- Calculates SHA-256 checksum of the normalized text
- Skips pages with identical text content
- Useful for sites with multiple URLs serving the same content
- Works together with canonical URL checking for thorough deduplication

The scraper now has three levels of duplicate prevention, applied in this order:

1. **GET parameter normalization** (default: disabled) - Use
   `--ignore-get-params` to enable
2. **Canonical URL checking** (default: enabled) - Respects
   `<link rel="canonical">`
3. **Content deduplication** (default: enabled) - Compares text content

**Important**: All deduplication data is stored in the SQLite database
(`scrape_tracker.db`), which means:

- Content checksums persist across resume operations
- Canonical URL information is saved for each page
- The deduplication works correctly even when resuming interrupted scrapes
- Memory-efficient: checksums are queried from database, not loaded into memory
- Scales to large websites without excessive memory usage

### Subdirectory Restriction

When you specify a URL with a path, the scraper automatically restricts crawling
to that subdirectory:

```bash
# Only scrape pages under /docs subdirectory
m1f-scrape https://example.com/docs -o ./docs_only

# Only scrape API documentation pages
m1f-scrape https://api.example.com/v2/reference -o ./api_docs

# This will NOT scrape /products, /blog, etc. - only /tutorials/*
m1f-scrape https://learn.example.com/tutorials -o ./tutorials_only
```

### Advanced Path Control with --allowed-path and --allowed-paths

Sometimes you need to start from a specific page but allow crawling in different directories. 

#### Single Path (Legacy)
Use `--allowed-path` to override the automatic path restriction with a single path:

```bash
# Start from product page but allow crawling all products
m1f-scrape https://docs.example.com/products/widget.html -o ./products \
  --allowed-path /products/

# Start from a deep nested page but allow broader documentation crawling
m1f-scrape https://docs.example.com/v2/api/users/create.html -o ./api_docs \
  --allowed-path /v2/api/

# Start from main docs page but restrict to specific section
m1f-scrape https://docs.example.com/index.html -o ./guides \
  --allowed-path /guides/
```

#### Multiple Paths (New)
Use `--allowed-paths` to allow crawling in multiple directories:

```bash
# Scrape both documentation and API reference sections
m1f-scrape https://example.com -o ./docs \
  --allowed-paths /docs/ /api/ /reference/

# Start from main page but only scrape specific sections
m1f-scrape https://docs.example.com/index.html -o ./selected_docs \
  --allowed-paths /tutorials/ /how-to/ /faq/

# Combine multiple documentation areas
m1f-scrape https://framework.com/docs -o ./framework_docs \
  --allowed-paths /docs/core/ /docs/plugins/ /docs/api/
```

**Note**: You cannot use both `--allowed-path` and `--allowed-paths` in the same command. The `--allowed-path` option is maintained for backward compatibility.

The start URL is always scraped regardless of path restrictions, making it perfect for
documentation sites where the index page links to content in different directories.

### Controlled Crawling

```bash
# Limit crawl depth for shallow scraping
m1f-scrape https://blog.example.com -o ./blog \
  --max-depth 2 \
  --max-pages 20

# Unlimited scraping (use with caution!)
m1f-scrape https://docs.example.com -o ./docs \
  --max-pages -1 \
  --request-delay 2.0

# Slow crawling to be respectful
m1f-scrape https://example.com -o ./html \
  --request-delay 2.0 \
  --concurrent-requests 2

# Start from specific page but allow broader crawling area (single path)
m1f-scrape https://docs.example.com/api/index.html -o ./api_docs \
  --allowed-path /api/ \
  --max-pages 100

# Scrape multiple sections with the new --allowed-paths option
m1f-scrape https://docs.example.com -o ./docs \
  --allowed-paths /api/ /guides/ /reference/ \
  --max-pages 200
```

### Custom Configuration

```bash
# Use custom user agent
m1f-scrape https://example.com -o ./html \
  --user-agent "MyBot/1.0 (Compatible)"

# Use scraper-specific configuration
m1f-scrape https://example.com -o ./html \
  --scraper scrapy \
  --scraper-config ./scrapy-settings.yaml
```

## Session Management

m1f-scrape tracks each scraping run as a session with full statistics and state management.

### Session Tracking

Every scraping run creates a session with:
- Unique session ID
- Start/end timestamps  
- Configuration parameters used
- Success/failure statistics
- Session status (running, completed, interrupted, failed)

### View Sessions

```bash
# Show all sessions with basic info
m1f-scrape --show-sessions -o ./html

# Show detailed session information
m1f-scrape --show-sessions-detailed -o ./html

# Example output:
ID  | Status    | Started             | Pages | Success | Failed | URL
----------------------------------------------------------------------------------------------------
3   | completed | 2025-08-03 14:23:12 | 142   | 140     | 2      | https://docs.example.com
2   | interrupted| 2025-08-03 13:45:00 | 45    | 45      | 0      | https://api.example.com/v2
1   | completed | 2025-08-03 12:00:00 | 250   | 248     | 2      | https://example.com
```

### Clean Up Sessions

```bash
# Clear the most recent session (database only, asks about files)
m1f-scrape --clear-last-session -o ./html

# Clear session and automatically delete files (no prompt)
m1f-scrape --clear-last-session --delete-files -o ./html

# Clear a specific session by ID (asks about files)
m1f-scrape --clear-session 2 -o ./html

# Clear session 2 and delete files without confirmation
m1f-scrape --clear-session 2 --delete-files -o ./html

# Clean up orphaned sessions (from crashes)
m1f-scrape --cleanup-sessions -o ./html
```

#### File Deletion Behavior

When clearing sessions, the scraper will:
1. **Always delete** database entries (URLs, checksums, session records)
2. **Optionally delete** downloaded HTML files and metadata files
3. **Ask for confirmation** by default when files would be deleted
4. **Skip confirmation** if `--delete-files` flag is provided

This allows you to:
- Keep downloaded files while cleaning the database
- Fully clean up both database and files
- Automate cleanup in scripts with `--delete-files`

### Automatic Cleanup

The scraper automatically:
- Detects sessions left in 'running' state from crashes
- Marks sessions as 'interrupted' if no URLs have been scraped for >1 hour
- Preserves statistics for interrupted sessions
- Does NOT interrupt long-running active sessions (they can run for many hours)

### Session Recovery

If a process is killed (kill -9, system crash, etc.), the session will be left in 'running' state. On the next run:

1. **Automatic cleanup**: Sessions older than 1 hour are automatically marked as interrupted
2. **Manual cleanup**: Use `--cleanup-sessions` to manually review and clean up
3. **Resume capability**: The scraping can still resume from where it left off

```bash
# After a crash, cleanup and resume
m1f-scrape --cleanup-sessions -o ./html
m1f-scrape https://example.com -o ./html  # Resumes from last position
```

## Scraping Summary and Statistics

After each scraping session, m1f-scrape displays a comprehensive summary with:

- **Session ID**: Unique identifier for this scraping run
- **Success metrics**: Number of successfully scraped pages
- **Error count**: Number of failed page downloads
- **Success rate**: Percentage of successful downloads
- **Time statistics**: Total duration and average time per page
- **File counts**: Number of HTML files saved

Example output:
```
============================================================
Scraping Summary (Session #3)
============================================================
✓ Successfully scraped 142 pages
⚠ Failed to scrape 3 pages
Total URLs processed: 145
Success rate: 97.9%
Total duration: 435.2 seconds
Average time per page: 3.00 seconds
Output directory: ./html/example.com
HTML files saved in this session: 142

Session ID: #3
To clear this session: m1f-scrape --clear-session 3 -o ./html
```

## Output Structure

Downloaded files are organized to mirror the website structure:

```
output_directory/
├── scrape_tracker.db         # SQLite database for resume functionality
├── example.com/
│   ├── index.html
│   ├── index.meta.json
│   ├── about/
│   │   ├── index.html
│   │   └── index.meta.json
│   ├── blog/
│   │   ├── post1/
│   │   │   ├── index.html
│   │   │   └── index.meta.json
│   │   └── post2/
│   │       ├── index.html
│   │       └── index.meta.json
│   └── contact/
│       ├── index.html
│       └── index.meta.json
```

### Metadata Files

Each HTML file has an accompanying `.meta.json` file containing:

```json
{
  "url": "https://example.com/about/",
  "title": "About Us - Example",
  "encoding": "utf-8",
  "status_code": 200,
  "headers": {
    "Content-Type": "text/html; charset=utf-8",
    "Last-Modified": "2024-01-15T10:30:00Z"
  },
  "metadata": {
    "description": "Learn more about Example company",
    "og:title": "About Us",
    "canonical": "https://example.com/about/"
  }
}
```

## Integration with m1f Workflow

webscraper is designed as the first step in a workflow to provide documentation
to LLMs:

```bash
# Step 1: Download documentation website
m1f-scrape https://docs.example.com -o ./html_files

# Step 2: Analyze HTML structure
m1f-html2md analyze ./html_files/*.html --suggest-selectors

# Step 3: Convert to Markdown
m1f-html2md convert ./html_files -o ./markdown \
  --content-selector "main.content" \
  --ignore-selectors "nav" ".sidebar"

# Step 4: Bundle for LLM consumption
m1f -s ./markdown -o ./docs_bundle.txt \
  --remove-scraped-metadata

# Now docs_bundle.txt contains all documentation in a single file
# that can be provided to Claude or other LLMs for analysis
```

### Complete Documentation Download Example

```bash
# Download React documentation for LLM analysis
m1f-scrape https://react.dev/learn -o ./react_docs \
  --max-pages 100 \
  --max-depth 3

# Convert to clean Markdown
m1f-html2md convert ./react_docs -o ./react_md \
  --content-selector "article" \
  --ignore-selectors "nav" "footer" ".sidebar"

# Create single file for LLM
m1f -s ./react_md -o ./react_documentation.txt

# Now you can provide react_documentation.txt to Claude:
# "Here is the React documentation: <contents of react_documentation.txt>"
```

### Real-World Examples

The m1f project includes two complete documentation scraper examples:

#### Claude Code Documentation
Located in `examples/claude_code_doc/`:
- Scrapes ~31 pages from docs.anthropic.com/claude-code
- Includes optimized HTML extraction config (saves 5-8 minutes)
- Creates clean Markdown bundle for LLM consumption
- See the [README](../../examples/claude_code_doc/README.md) for usage

#### Tailscale Documentation  
Located in `examples/tailscale_doc/`:
- Scrapes ~422 pages from tailscale.com/kb
- Creates 11 thematic bundles (2.4MB total) organized by topic
- Includes parallel processing and skip-download options
- See the [README](../../examples/tailscale_doc/README.md) for details

Both examples demonstrate best practices for:
- Respectful scraping with delays
- Optimized HTML-to-Markdown conversion
- Bundle organization for LLM usage
- Configuration reuse to save time

## Resume Functionality

The scraper supports interrupting and resuming downloads, making it ideal for
large websites or unreliable connections.

### How It Works

- **SQLite Database**: Creates `scrape_tracker.db` in the output directory to
  track:
  - URL of each scraped page
  - HTTP status code and target filename
  - Timestamp and error messages (if any)
- **Progress Display**: Shows real-time progress in verbose mode:
  ```
  Processing: https://example.com/page1 (page 1)
  Processing: https://example.com/page2 (page 2)
  ```
- **Graceful Interruption**: Press Ctrl+C to interrupt cleanly:
  ```
  Press Ctrl+C to interrupt and resume later
  ^C
  ⚠️  Scraping interrupted by user
  Run the same command again to resume where you left off
  ```

### Resume Example

```bash
# Start scraping with verbose mode
m1f-scrape https://docs.example.com -o ./docs --max-pages 100 -v

# Interrupt with Ctrl+C when needed
# Resume by running the exact same command:
m1f-scrape https://docs.example.com -o ./docs --max-pages 100 -v

# You'll see:
# Resuming crawl - found 25 previously scraped URLs
# Populating queue from previously scraped pages...
# Found 187 URLs to visit after analyzing scraped pages
# Processing: https://docs.example.com/new-page (page 26)
```

### Overriding Resume Behavior

You can override the resume functionality using the new flags:

```bash
# Force rescraping all pages even if already in database
m1f-scrape https://docs.example.com -o ./docs --force-rescrape

# Clear all URLs and start from the beginning
m1f-scrape https://docs.example.com -o ./docs --clear-urls

# Both together for a complete fresh start
m1f-scrape https://docs.example.com -o ./docs --clear-urls --force-rescrape
```

### Database Inspection

```bash
# Show scraping statistics
m1f-scrape -o docs/ --show-db-stats

# View all scraped URLs with status codes
m1f-scrape -o docs/ --show-scraped-urls

# Check for errors
m1f-scrape -o docs/ --show-errors

# Combine multiple queries
m1f-scrape -o docs/ --show-db-stats --show-errors
```

## Force Rescraping and Clearing URLs

The scraper provides two options for managing cached content and URLs in the database:

### --clear-urls: Start Fresh

The `--clear-urls` option removes all URL tracking from the database while preserving content checksums:

```bash
# Clear all URLs and start a fresh scrape
m1f-scrape https://docs.example.com -o ./docs --clear-urls

# This will:
# - Remove all URL records from the database
# - Keep content checksums for deduplication
# - Start scraping from the beginning
```

**Use cases:**
- Website structure has changed significantly
- Want to re-crawl all pages without resetting content deduplication
- Need to update navigation paths while avoiding duplicate content

### --force-rescrape: Ignore Cached Content

The `--force-rescrape` option forces the scraper to re-download all pages, ignoring the cache:

```bash
# Force rescraping all pages (ignores cache)
m1f-scrape https://docs.example.com -o ./docs --force-rescrape

# Combine with clear-urls for complete reset
m1f-scrape https://docs.example.com -o ./docs --clear-urls --force-rescrape
```

**Use cases:**
- Content has been updated on the website
- Need fresh copies of all pages
- Want to override resume functionality temporarily

### Interaction with Content Checksums

Content checksums are preserved even when using `--clear-urls`, which means:

```bash
# First scrape - downloads all content
m1f-scrape https://example.com -o ./html

# Clear URLs but keep checksums
m1f-scrape https://example.com -o ./html --clear-urls

# Second scrape - URLs are re-crawled but duplicate content is still detected
# Pages with identical text content will be skipped based on checksums
```

To completely reset everything including checksums:

```bash
# Option 1: Delete the database file
rm ./html/scrape_tracker.db
m1f-scrape https://example.com -o ./html

# Option 2: Use both flags together
m1f-scrape https://example.com -o ./html --clear-urls --force-rescrape
```

### Examples of Force Rescraping Scenarios

#### Scenario 1: Documentation Update
```bash
# Initial scrape of documentation
m1f-scrape https://docs.framework.com -o ./docs_v1

# Framework releases new version with updated docs
# Force rescrape to get all updated content
m1f-scrape https://docs.framework.com -o ./docs_v2 --force-rescrape
```

#### Scenario 2: Partial Scrape Recovery
```bash
# Scrape was interrupted or had errors
m1f-scrape https://large-site.com -o ./site --max-pages 1000

# Clear URLs and try again with different settings
m1f-scrape https://large-site.com -o ./site \
  --clear-urls \
  --max-pages 500 \
  --request-delay 30
```

#### Scenario 3: Testing Different Scraper Backends
```bash
# Try with BeautifulSoup first
m1f-scrape https://complex-site.com -o ./test --max-pages 10

# Site has JavaScript - clear and try with Playwright
m1f-scrape https://complex-site.com -o ./test \
  --clear-urls \
  --scraper playwright \
  --max-pages 10
```

## Best Practices

1. **Respect robots.txt**: The tool automatically respects robots.txt files
2. **Use appropriate delays**: Set `--request-delay` to avoid overwhelming
   servers (default: 15 seconds)
3. **Limit concurrent requests**: Use `--concurrent-requests` responsibly
   (default: 2 connections)
4. **Test with small crawls**: Start with `--max-pages 10` to test your settings
5. **Check output**: Use `--list-files` to verify what was downloaded (limited to 30 files for large sites)
6. **Save URLs for analysis**: Use `--save-urls` to keep a record of all scraped URLs
7. **Track downloaded files**: Use `--save-files` to maintain a list of all downloaded files
8. **Use verbose mode**: Add `-v` flag to see progress and resume information
9. **Keep commands consistent**: Use the exact same command to resume a session
10. **Monitor statistics**: Check the summary statistics to verify scraping efficiency

## Dealing with Cloudflare Protection

Many websites use Cloudflare or similar services to protect against bots. The
scraper now includes conservative defaults to help avoid detection:

### Default Conservative Settings

- **Request delay**: 15 seconds between requests
- **Concurrent requests**: 2 simultaneous connections
- **HTTrack backend**: Limited to 0.5 connections/second max
- **Bandwidth limiting**: 100KB/s for HTTrack backend
- **Robots.txt**: Always respected (cannot be disabled)

### For Heavy Cloudflare Protection

For heavily protected sites, manually set very conservative values:

```bash
m1f-scrape https://protected-site.com -o ./output \
  --request-delay 30 \
  --concurrent-requests 1 \
  --max-pages 50 \
  --scraper httrack
```

### Cloudflare Avoidance Tips

1. **Start conservative**: Begin with 30-60 second delays
2. **Use realistic user agents**: The default is a current Chrome browser
3. **Limit scope**: Download only what you need with `--max-pages`
4. **Single connection**: Use `--concurrent-requests 1` for sensitive sites
5. **Respect robots.txt**: Always enabled by default
6. **Add randomness**: Consider adding random delays in custom scripts

### When Cloudflare Still Blocks

If conservative settings don't work:

1. **Try Playwright backend**: Uses real browser automation

   ```bash
   m1f-scrape https://site.com -o ./output --scraper playwright
   ```

2. **Manual download**: Some sites require manual browsing
3. **API access**: Check if the site offers an API
4. **Contact site owner**: Request permission or access

## Troubleshooting

### No files downloaded

- Check if the website blocks automated access
- Try a different scraper backend
- Verify the URL is accessible

### Incomplete downloads

- Increase `--max-depth` if pages are deeply nested
- Increase `--max-pages` if hitting the limit
- Check for JavaScript-rendered content (use Playwright)

### Encoding issues

- The tool automatically detects encoding
- Check `.meta.json` files for encoding information
- Use html2md with proper encoding settings for conversion

## See Also

- [html2md Documentation](../03_html2md/30_html2md.md) - For converting
  downloaded HTML to Markdown
- [m1f Documentation](../01_m1f/00_m1f.md) - For bundling converted content for
  LLMs
