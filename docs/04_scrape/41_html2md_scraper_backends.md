# Web Scraper Backends

The HTML2MD tool supports multiple web scraping backends, each optimized for
different use cases. Choose the right backend based on your specific needs for
optimal results.

## Overview

The HTML2MD scraper backend system provides flexibility to choose the most
appropriate tool for your web scraping needs:

- **Static websites**: BeautifulSoup4 (default) - Fast and lightweight
- **Complete mirroring**: HTTrack - Professional website copying
- **JavaScript-heavy sites**: Playwright (coming soon)
- **Large-scale scraping**: Scrapy (coming soon)
- **Performance-critical**: httpx + selectolax (coming soon)

## Available Backends

### BeautifulSoup4 (Default)

BeautifulSoup4 is the default backend, ideal for scraping static HTML websites.

**Pros:**

- Easy to use and lightweight
- Fast for simple websites
- Good encoding detection
- Excellent HTML parsing capabilities

**Cons:**

- No JavaScript support
- Basic crawling capabilities
- Single-threaded by default

**Usage:**

```bash
# Default backend (no need to specify)
python -m tools.scrape_tool https://example.com -o output/

# Explicitly specify BeautifulSoup
python -m tools.scrape_tool https://example.com -o output/ --scraper beautifulsoup

# With custom options
python -m tools.scrape_tool https://example.com -o output/ \
  --scraper beautifulsoup \
  --max-depth 3 \
  --max-pages 100 \
  --request-delay 1.0
```

### HTTrack

HTTrack is a professional website copier that creates complete offline mirrors.

**Pros:**

- Complete website mirroring
- Preserves directory structure
- Handles complex websites well
- Resume interrupted downloads
- Built-in robots.txt support

**Cons:**

- Requires system installation
- Less flexible for custom parsing
- Larger resource footprint

**Installation:**

```bash
# Ubuntu/Debian
sudo apt-get install httrack

# macOS
brew install httrack

# Windows
# Download from https://www.httrack.com/
```

**Usage:**

```bash
python -m tools.scrape_tool https://example.com -o output/ --scraper httrack

# With HTTrack-specific options
python -m tools.scrape_tool https://example.com -o output/ \
  --scraper httrack \
  --max-depth 5 \
  --concurrent-requests 8
```

## Configuration Options

### Command Line Options

Common options for all scrapers:

```bash
--scraper BACKEND           # Choose scraper backend (beautifulsoup, bs4, httrack, 
                           # selectolax, httpx, scrapy, playwright)
--max-depth N               # Maximum crawl depth (default: 5)
--max-pages N               # Maximum pages to crawl (default: 1000)
--request-delay SECONDS     # Delay between requests (default: 15.0)
--concurrent-requests N     # Number of concurrent requests (default: 2)
--user-agent STRING         # Custom user agent
--scraper-config PATH       # Path to scraper-specific config file (YAML/JSON)
--list-files                # List all downloaded files after completion
-v, --verbose               # Enable verbose output
-q, --quiet                 # Suppress all output except errors
--version                   # Show version information
```

Note: robots.txt is always respected and cannot be disabled.

### Configuration File

You can specify scraper-specific settings in a YAML or JSON configuration file:

```yaml
# beautifulsoup-config.yaml
parser: "html.parser"  # Options: "html.parser", "lxml", "html5lib"
features: "lxml"
encoding: "auto"  # Or specific encoding like "utf-8"
```

```yaml
# httrack-config.yaml
mirror_options:
  - "--assume-insecure"  # For HTTPS issues
  - "--robots=3"  # Strict robots.txt compliance
extra_filters:
  - "+*.css"
  - "+*.js"
  - "-*.zip"
```

Use with:

```bash
python -m tools.scrape_tool https://example.com -o output/ \
  --scraper beautifulsoup \
  --scraper-config beautifulsoup-config.yaml
```

### Backend-Specific Configuration

Each backend can have specific configuration options:

#### BeautifulSoup Configuration

Create a `beautifulsoup.yaml`:

```yaml
scraper_config:
  parser: "lxml" # Options: "html.parser", "lxml", "html5lib"
  features: "lxml"
  encoding: "auto" # Or specific encoding like "utf-8"
```

#### HTTrack Configuration

Create a `httrack.yaml`:

```yaml
scraper_config:
  mirror_options:
    - "--assume-insecure" # For HTTPS issues
    - "--robots=3" # Strict robots.txt compliance
  extra_filters:
    - "+*.css"
    - "+*.js"
    - "-*.zip"
```

## Use Cases and Recommendations

### Static Documentation Sites

For sites with mostly static HTML content:

```bash
python -m tools.scrape_tool https://docs.example.com -o docs/ \
  --scraper beautifulsoup \
  --max-depth 10 \
  --request-delay 0.2
```

### Complete Website Backup

For creating a complete offline mirror:

```bash
python -m tools.scrape_tool https://example.com -o backup/ \
  --scraper httrack \
  --max-pages 10000
```

### Rate-Limited APIs

For sites with strict rate limits:

```bash
python -m tools.scrape_tool https://api.example.com/docs -o api-docs/ \
  --scraper beautifulsoup \
  --request-delay 2.0 \
  --concurrent-requests 1
```

## Troubleshooting

### BeautifulSoup Issues

**Encoding Problems:**

```bash
# Create a config file with UTF-8 encoding
echo 'encoding: utf-8' > bs-config.yaml
python -m tools.scrape_tool https://example.com -o output/ \
  --scraper beautifulsoup \
  --scraper-config bs-config.yaml
```

**Parser Issues:**

```bash
# Create a config file with different parser
echo 'parser: html5lib' > bs-config.yaml
python -m tools.scrape_tool https://example.com -o output/ \
  --scraper beautifulsoup \
  --scraper-config bs-config.yaml
```

### HTTrack Issues

**SSL Certificate Problems:**

```bash
# Create a config file to ignore SSL errors (use with caution)
echo 'mirror_options: ["--assume-insecure"]' > httrack-config.yaml
python -m tools.scrape_tool https://example.com -o output/ \
  --scraper httrack \
  --scraper-config httrack-config.yaml
```

**Incomplete Downloads:** HTTrack creates a cache that allows resuming. Check
the `.httrack` directory in your output folder.

## Performance Comparison

| Backend       | Speed     | Memory Usage | JavaScript | Accuracy  |
| ------------- | --------- | ------------ | ---------- | --------- |
| BeautifulSoup | Fast      | Low          | No         | High      |
| HTTrack       | Medium    | Medium       | No         | Very High |
| Selectolax    | Fastest   | Very Low     | No         | Medium    |
| Scrapy        | Very Fast | Low-Medium   | No         | High      |
| Playwright    | Slow      | High         | Yes        | Very High |

## Additional Backends

### Selectolax (httpx + selectolax)

The fastest HTML parsing solution using httpx for networking and selectolax for
parsing.

**Pros:**

- Blazing fast performance (C-based parser)
- Minimal memory footprint
- Excellent for large-scale simple scraping
- Modern async HTTP/2 support

**Cons:**

- No JavaScript support
- Limited parsing features compared to BeautifulSoup
- Less mature ecosystem

**Installation:**

```bash
pip install httpx selectolax
```

**Usage:**

```bash
# Basic usage
python -m tools.scrape_tool https://example.com -o output/ --scraper selectolax

# With custom configuration
python -m tools.scrape_tool https://example.com -o output/ \
  --scraper selectolax \
  --concurrent-requests 20 \
  --request-delay 0.1

# Using httpx alias
python -m tools.scrape_tool https://example.com -o output/ --scraper httpx
```

### Scrapy

Industrial-strength web scraping framework with advanced features.

**Pros:**

- Battle-tested in production
- Built-in retry logic and error handling
- Auto-throttle based on server response
- Extensive middleware system
- Distributed crawling support
- Advanced caching and queuing

**Cons:**

- Steeper learning curve
- Heavier than simple scrapers
- Twisted-based (different async model)

**Installation:**

```bash
pip install scrapy
```

**Usage:**

```bash
# Basic usage
python -m tools.scrape_tool https://example.com -o output/ --scraper scrapy

# With auto-throttle and caching
python -m tools.scrape_tool https://example.com -o output/ \
  --scraper scrapy \
  --scraper-config scrapy.yaml

# Large-scale crawling
python -m tools.scrape_tool https://example.com -o output/ \
  --scraper scrapy \
  --max-pages 10000 \
  --concurrent-requests 16
```

### Playwright

Browser automation for JavaScript-heavy websites and SPAs.

**Pros:**

- Full JavaScript execution
- Handles SPAs and dynamic content
- Multiple browser engines (Chromium, Firefox, WebKit)
- Screenshot and PDF generation
- Mobile device emulation
- Network interception

**Cons:**

- High resource usage
- Slower than HTML-only scrapers
- Requires browser installation

**Installation:**

```bash
pip install playwright
playwright install  # Install browser binaries
```

**Usage:**

```bash
# Basic usage
python -m tools.scrape_tool https://example.com -o output/ --scraper playwright

# With custom browser settings
python -m tools.scrape_tool https://example.com -o output/ \
  --scraper playwright \
  --scraper-config playwright.yaml

# For SPA with wait conditions
python -m tools.scrape_tool https://spa-example.com -o output/ \
  --scraper playwright \
  --request-delay 2.0 \
  --concurrent-requests 2
```

## API Usage

You can also use the scraper backends programmatically:

```python
import asyncio
from tools.html2md.scrapers import create_scraper, ScraperConfig

async def scrape_example():
    # Configure scraper
    config = ScraperConfig(
        max_depth=5,
        max_pages=100,
        request_delay=0.5
    )

    # Create scraper instance
    scraper = create_scraper('beautifulsoup', config)

    # Scrape single page
    async with scraper:
        page = await scraper.scrape_url('https://example.com')
        print(f"Title: {page.title}")
        print(f"Content length: {len(page.content)}")

    # Scrape entire site
    async with scraper:
        async for page in scraper.scrape_site('https://example.com'):
            print(f"Scraped: {page.url}")

# Run the example
asyncio.run(scrape_example())
```

## Contributing

To add a new scraper backend:

1. Create a new file in `tools/html2md/scrapers/`
2. Inherit from `WebScraperBase`
3. Implement required methods: `scrape_url()` and `scrape_site()`
4. Register in `SCRAPER_REGISTRY` in `__init__.py`
5. Add tests in `tests/html2md/test_scrapers.py`
6. Update this documentation

See the BeautifulSoup implementation for a complete example.
