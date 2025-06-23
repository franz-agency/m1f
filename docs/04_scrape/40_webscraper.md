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
- **Metadata Preservation**: Saves HTTP headers and metadata alongside HTML
  files
- **Domain Restriction**: Automatically restricts crawling to the starting
  domain
- **Rate Limiting**: Configurable delays between requests
- **Progress Tracking**: Real-time download progress with file listing
- **Resume Support**: Interrupt and resume scraping sessions with SQLite tracking

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

# List downloaded files after completion
m1f-scrape https://example.com -o ./html --list-files

# Resume interrupted scraping (with verbose mode to see progress)
m1f-scrape https://example.com -o ./html -v
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
| `--max-pages`           | Maximum pages to crawl                                        | 1000          |
| `--request-delay`       | Delay between requests in seconds (for Cloudflare protection) | 15.0          |
| `--concurrent-requests` | Number of concurrent requests (for Cloudflare protection)     | 2             |
| `--user-agent`          | Custom user agent string                                      | Mozilla/5.0   |
| `--list-files`          | List all downloaded files after completion                    | False         |
| `-v, --verbose`         | Enable verbose output                                         | False         |
| `-q, --quiet`           | Suppress all output except errors                             | False         |
| `--show-db-stats`       | Show scraping statistics from the database                    | False         |
| `--show-errors`         | Show URLs that had errors during scraping                     | False         |
| `--show-scraped-urls`   | List all scraped URLs from the database                       | False         |
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

### Controlled Crawling

```bash
# Limit crawl depth for shallow scraping
m1f-scrape https://blog.example.com -o ./blog \
  --max-depth 2 \
  --max-pages 20

# Slow crawling to be respectful
m1f-scrape https://example.com -o ./html \
  --request-delay 2.0 \
  --concurrent-requests 2
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

## Resume Functionality

The scraper supports interrupting and resuming downloads, making it ideal for large websites or unreliable connections.

### How It Works

- **SQLite Database**: Creates `scrape_tracker.db` in the output directory to track:
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

## Best Practices

1. **Respect robots.txt**: The tool automatically respects robots.txt files
2. **Use appropriate delays**: Set `--request-delay` to avoid overwhelming
   servers (default: 15 seconds)
3. **Limit concurrent requests**: Use `--concurrent-requests` responsibly
   (default: 2 connections)
4. **Test with small crawls**: Start with `--max-pages 10` to test your settings
5. **Check output**: Use `--list-files` to verify what was downloaded
6. **Use verbose mode**: Add `-v` flag to see progress and resume information
7. **Keep commands consistent**: Use the exact same command to resume a session

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
