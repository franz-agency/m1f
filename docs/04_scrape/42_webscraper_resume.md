# WebScraper Resume Functionality

The m1f-scrape tool now supports interrupting and resuming web scraping sessions, making it ideal for large websites or unreliable connections.

## Overview

When scraping large websites, interruptions can occur due to:
- Network timeouts
- Rate limiting
- Manual interruption (Ctrl+C)
- System issues

The resume functionality ensures you don't lose progress and can continue where you left off.

## How It Works

### SQLite Database Tracking

m1f-scrape creates a SQLite database (`scrape_tracker.db`) in the output directory that tracks:
- URL of each scraped page
- HTTP status code
- Target filename (relative path)
- Timestamp of scraping
- Error messages (if any)

### Progress Display

During scraping, you'll see real-time progress:
```
Processing: https://example.com/page1 (page 1)
Processing: https://example.com/page2 (page 2)
```

### Graceful Interruption

Press Ctrl+C to interrupt at any time:
```
Press Ctrl+C to interrupt and resume later

^C
⚠️  Scraping interrupted by user
Run the same command again to resume where you left off
```

## Usage Examples

### Basic Scraping with Resume Support

```bash
# Start scraping
m1f-scrape https://example.com -o output/ --max-pages 100 -v

# Interrupt with Ctrl+C when needed
# Resume by running the exact same command
m1f-scrape https://example.com -o output/ --max-pages 100 -v
```

### Resuming a Previous Session

When resuming, you'll see:
```
Resuming crawl - found 25 previously scraped URLs
Analyzing previously scraped pages to find new URLs...
Found 187 URLs to visit after analyzing scraped pages
Processing: https://example.com/new-page (page 26)
```

### React Documentation Example

```bash
# Start scraping React docs
m1f-scrape https://react.dev/learn -o react_docs/ --max-pages 50 -v

# Resume after interruption
m1f-scrape https://react.dev/learn -o react_docs/ --max-pages 50 -v
```

## Database Structure

The `scrape_tracker.db` contains a single table:

```sql
CREATE TABLE scraped_urls (
    url TEXT PRIMARY KEY,
    status_code INTEGER,
    target_filename TEXT,
    scraped_at TIMESTAMP,
    error TEXT
);
```

### Viewing Database Contents

```bash
# List all scraped URLs
sqlite3 output/scrape_tracker.db "SELECT url, status_code FROM scraped_urls;"

# Count scraped pages
sqlite3 output/scrape_tracker.db "SELECT COUNT(*) FROM scraped_urls;"

# View errors
sqlite3 output/scrape_tracker.db "SELECT url, error FROM scraped_urls WHERE error IS NOT NULL;"
```

## Configuration Options

### Request Delays

To avoid overwhelming servers:
```bash
# Conservative scraping with 30-second delays
m1f-scrape https://example.com -o output/ --request-delay 30
```

### Concurrent Requests

Control parallelism:
```bash
# Single request at a time
m1f-scrape https://example.com -o output/ --concurrent-requests 1
```

## Best Practices

1. **Use Verbose Mode**: Always use `-v` to see progress and resume information
2. **Set Appropriate Delays**: Respect server resources with `--request-delay`
3. **Monitor Progress**: Check the database to track scraping status
4. **Keep Commands Consistent**: Use the exact same command to resume

## Troubleshooting

### Resume Not Working

If resume doesn't continue from where it left off:
1. Check if `scrape_tracker.db` exists in the output directory
2. Ensure you're using the same output directory
3. Verify the database isn't corrupted: `sqlite3 output/scrape_tracker.db "PRAGMA integrity_check;"`

### Missing Links on Resume

The scraper analyzes the first 20 previously scraped pages to find new links. If a page has many links, some might be missed. This is a trade-off for faster resume startup.

### Database Lock Errors

If you see database lock errors:
1. Ensure no other process is using the database
2. Check file permissions on the output directory
3. Try removing the `.db-journal` file if it exists

## Implementation Details

- **Progress Logging**: Uses Python's logging module with INFO level
- **Database Operations**: Thread-safe SQLite operations
- **Link Extraction**: BeautifulSoup parser extracts links from scraped pages
- **Resume Strategy**: Loads previously scraped URLs and extracts their links to continue crawling