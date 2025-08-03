# m1f-scrape Parameter Test Coverage Analysis

## All Available Parameters

### Input/Output
- `url` - ❌ Not tested with local server (only mocked)
- `-o, --output` - ✅ Tested in integration tests

### Output Control
- `-v, --verbose` - ❌ Not tested
- `-q, --quiet` - ❌ Not tested

### Scraper Options
- `--scraper` - ✅ Partially tested (only beautifulsoup in integration)
- `--scraper-config` - ❌ Not tested

### Crawl Configuration
- `--max-depth` - ✅ Tested (value: 2-3)
- `--max-pages` - ✅ Tested (value: 20)
- `--allowed-path` - ✅ Tested extensively
- `--excluded-paths` - ❌ Not tested (NEW)

### Request Options
- `--request-delay` - ✅ Tested (value: 0.1)
- `--concurrent-requests` - ✅ Tested (value: 2)
- `--user-agent` - ❌ Not tested
- `--timeout` - ❌ Not tested (NEW)
- `--retry-count` - ❌ Not tested (NEW)

### Content Filtering
- `--ignore-get-params` - ❌ Not tested
- `--ignore-canonical` - ❌ Not tested with local server
- `--ignore-duplicates` - ❌ Not tested

### Display Options
- `--list-files` - ❌ Not tested

### Security Options
- `--disable-ssrf-check` - ✅ Implicitly tested (check_ssrf=False used)

### Database Options
- `--show-db-stats` - ❌ Not tested
- `--show-errors` - ❌ Not tested
- `--show-scraped-urls` - ❌ Not tested

## Summary

**Tested with local server (7/24):**
- output, scraper (partial), max-depth, max-pages, allowed-path, request-delay, concurrent-requests, disable-ssrf-check (implicit)

**Not tested with local server (17/24):**
- url, verbose, quiet, scraper-config, excluded-paths, user-agent, timeout, retry-count, ignore-get-params, ignore-canonical, ignore-duplicates, list-files, show-db-stats, show-errors, show-scraped-urls

## Missing Test Coverage

### High Priority (Core functionality)
1. Different scraper backends (httrack, selectolax, playwright)
2. Content filtering (ignore-get-params, ignore-canonical, ignore-duplicates)
3. Excluded paths functionality
4. User agent customization

### Medium Priority (Important options)
1. Timeout and retry behavior
2. Database query options
3. List files option
4. Verbose/quiet output

### Low Priority (Less critical)
1. Scraper-specific config files
