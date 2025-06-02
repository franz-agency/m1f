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
- **Intelligent Crawling**: Respects robots.txt, follows redirects, handles
  encoding
- **Metadata Preservation**: Saves HTTP headers and metadata alongside HTML
  files
- **Domain Restriction**: Automatically restricts crawling to the starting
  domain
- **Rate Limiting**: Configurable delays between requests
- **Progress Tracking**: Real-time download progress with file listing

## Quick Start

```bash
# Basic website download
python -m tools.webscraper https://example.com -o ./downloaded_html

# Download with specific depth and page limits
python -m tools.webscraper https://example.com -o ./html \
  --max-pages 50 \
  --max-depth 3

# Use different scraper backend
python -m tools.webscraper https://example.com -o ./html --scraper httrack

# List downloaded files after completion
python -m tools.webscraper https://example.com -o ./html --list-files
```

## Command Line Interface

```bash
python -m tools.webscraper <url> -o <output> [options]
```

### Required Arguments

| Option         | Description                |
| -------------- | -------------------------- |
| `url`          | URL to start scraping from |
| `-o, --output` | Output directory           |

### Optional Arguments

| Option                  | Description                                      | Default       |
| ----------------------- | ------------------------------------------------ | ------------- |
| `--scraper`             | Scraper backend to use                           | beautifulsoup |
| `--scraper-config`      | Path to scraper-specific config file (YAML/JSON) | None          |
| `--max-depth`           | Maximum crawl depth                              | 5             |
| `--max-pages`           | Maximum pages to crawl                           | 1000          |
| `--request-delay`       | Delay between requests in seconds                | 0.5           |
| `--concurrent-requests` | Number of concurrent requests                    | 5             |
| `--user-agent`          | Custom user agent string                         | Mozilla/5.0   |
| `--list-files`          | List all downloaded files after completion       | False         |
| `-v, --verbose`         | Enable verbose output                            | False         |
| `-q, --quiet`           | Suppress all output except errors                | False         |

## Scraper Backends

### BeautifulSoup (default)

- **Best for**: General purpose scraping, simple websites
- **Features**: Fast HTML parsing, good encoding detection
- **Limitations**: No JavaScript support

```bash
python -m tools.webscraper https://example.com -o ./html --scraper beautifulsoup
```

### HTTrack

- **Best for**: Complete website mirroring, preserving structure
- **Features**: External links handling, advanced mirroring options
- **Limitations**: Requires HTTrack to be installed separately

```bash
python -m tools.webscraper https://example.com -o ./html --scraper httrack
```

### Scrapy

- **Best for**: Large-scale crawling, complex scraping rules
- **Features**: Advanced crawling settings, middleware support
- **Limitations**: More complex configuration

```bash
python -m tools.webscraper https://example.com -o ./html --scraper scrapy
```

### Playwright

- **Best for**: JavaScript-heavy sites, SPAs
- **Features**: Full browser automation, JavaScript execution
- **Limitations**: Slower, requires more resources

```bash
python -m tools.webscraper https://example.com -o ./html --scraper playwright
```

### Selectolax

- **Best for**: Speed-critical applications
- **Features**: Fastest HTML parsing, minimal overhead
- **Limitations**: Basic feature set

```bash
python -m tools.webscraper https://example.com -o ./html --scraper selectolax
```

## Usage Examples

### Basic Website Download

```bash
# Download a simple website
python -m tools.webscraper https://docs.example.com -o ./docs_html

# Download with verbose output
python -m tools.webscraper https://docs.example.com -o ./docs_html -v
```

### Controlled Crawling

```bash
# Limit crawl depth for shallow scraping
python -m tools.webscraper https://blog.example.com -o ./blog \
  --max-depth 2 \
  --max-pages 20

# Slow crawling to be respectful
python -m tools.webscraper https://example.com -o ./html \
  --request-delay 2.0 \
  --concurrent-requests 2
```

### Custom Configuration

```bash
# Use custom user agent
python -m tools.webscraper https://example.com -o ./html \
  --user-agent "MyBot/1.0 (Compatible)"

# Use scraper-specific configuration
python -m tools.webscraper https://example.com -o ./html \
  --scraper scrapy \
  --scraper-config ./scrapy-settings.yaml
```

## Output Structure

Downloaded files are organized to mirror the website structure:

```
output_directory/
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
python -m tools.webscraper https://docs.example.com -o ./html_files

# Step 2: Analyze HTML structure
python -m tools.html2md analyze ./html_files/*.html --suggest-selectors

# Step 3: Convert to Markdown
python -m tools.html2md convert ./html_files -o ./markdown \
  --content-selector "main.content" \
  --ignore-selectors "nav" ".sidebar"

# Step 4: Bundle for LLM consumption
python -m tools.m1f -s ./markdown -o ./docs_bundle.txt \
  --remove-scraped-metadata

# Now docs_bundle.txt contains all documentation in a single file
# that can be provided to Claude or other LLMs for analysis
```

### Complete Documentation Download Example

```bash
# Download React documentation for LLM analysis
python -m tools.webscraper https://react.dev/learn -o ./react_docs \
  --max-pages 100 \
  --max-depth 3

# Convert to clean Markdown
python -m tools.html2md convert ./react_docs -o ./react_md \
  --content-selector "article" \
  --ignore-selectors "nav" "footer" ".sidebar"

# Create single file for LLM
python -m tools.m1f -s ./react_md -o ./react_documentation.txt

# Now you can provide react_documentation.txt to Claude:
# "Here is the React documentation: <contents of react_documentation.txt>"
```

## Best Practices

1. **Respect robots.txt**: The tool automatically respects robots.txt files
2. **Use appropriate delays**: Set `--request-delay` to avoid overwhelming
   servers
3. **Limit concurrent requests**: Use `--concurrent-requests` responsibly
4. **Test with small crawls**: Start with `--max-pages 10` to test your settings
5. **Check output**: Use `--list-files` to verify what was downloaded

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

- [html2md Documentation](html2md.md) - For converting downloaded HTML to
  Markdown
- [m1f Documentation](m1f.md) - For bundling converted content for LLMs
