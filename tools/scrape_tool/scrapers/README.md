# HTML2MD Web Scrapers

This module provides a pluggable architecture for web scraping backends in the
HTML2MD tool.

## Architecture

The scraper system is built around:

- `WebScraperBase`: Abstract base class defining the scraper interface
- `ScraperConfig`: Configuration dataclass for all scrapers
- `create_scraper()`: Factory function to instantiate scrapers
- `SCRAPER_REGISTRY`: Registry of available backends

## Available Scrapers

### BeautifulSoup (`beautifulsoup`, `bs4`)

- **Purpose**: General-purpose web scraping for static sites
- **Features**: Async support, encoding detection, metadata extraction
- **Best for**: Most websites without JavaScript requirements

### HTTrack (`httrack`)

- **Purpose**: Complete website mirroring
- **Features**: Professional mirroring, preserves structure
- **Best for**: Creating offline copies of entire websites
- **Requires**: System installation of HTTrack

## Usage

```python
from tools.html2md.scrapers import create_scraper, ScraperConfig

# Configure scraper
config = ScraperConfig(
    max_depth=5,
    max_pages=100,
    request_delay=0.5,
    user_agent="Mozilla/5.0 ..."
)

# Create scraper instance
scraper = create_scraper('beautifulsoup', config)

# Use scraper
async with scraper:
    # Scrape single page
    page = await scraper.scrape_url('https://example.com')

    # Scrape entire site
    async for page in scraper.scrape_site('https://example.com'):
        print(f"Scraped: {page.url}")
```

## Adding New Scrapers

To add a new scraper backend:

1. Create a new file in this directory (e.g., `playwright.py`)
2. Create a class inheriting from `WebScraperBase`
3. Implement required methods:
   - `scrape_url()`: Scrape a single URL
   - `scrape_site()`: Scrape an entire website
4. Register in `__init__.py`:

   ```python
   from .playwright import PlaywrightScraper

   SCRAPER_REGISTRY['playwright'] = PlaywrightScraper
   ```

## Configuration

All scrapers share common configuration options through `ScraperConfig`:

- `max_depth`: Maximum crawl depth
- `max_pages`: Maximum pages to scrape
- `allowed_domains`: List of allowed domains
- `exclude_patterns`: URL patterns to exclude
- `request_delay`: Delay between requests
- `concurrent_requests`: Number of concurrent requests
- `user_agent`: User agent string
- `timeout`: Request timeout in seconds

Backend-specific options can be added as needed in the scraper implementation.
