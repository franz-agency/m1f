# m1f v3.2 Feature Documentation

## Overview

Version 3.2 of the m1f toolkit introduces significant security enhancements, performance improvements, and new configuration options. This document provides a comprehensive overview of all v3.2 features and changes.

## Major Security Enhancements

### 1. Path Traversal Protection
- **What's New**: Comprehensive validation of all file paths to prevent directory traversal attacks
- **Impact**: Prevents malicious actors from accessing files outside intended directories
- **Implementation**: 
  - New `validate_safe_path()` utility function
  - Applied to all user inputs, preset paths, and configuration files
  - Symlink targets are now validated

### 2. SSRF Protection in Web Scrapers
- **What's New**: Blocks access to private IP ranges and cloud metadata endpoints
- **Protected Ranges**:
  - Private networks (10.x.x.x, 172.16.x.x, 192.168.x.x)
  - Localhost (127.0.0.1, ::1)
  - Link-local (169.254.x.x)
  - Cloud metadata (169.254.169.254)
- **Applies to**: All web scraping tools (BeautifulSoup, Playwright, Scrapy, Selectolax)

### 3. robots.txt Compliance
- **What's New**: All scrapers now automatically respect robots.txt files
- **Features**:
  - Automatic robots.txt fetching and parsing
  - Per-path access validation
  - User-agent specific rule support
  - No configuration needed - always enabled
- **Previously**: Only HTTrack respected robots.txt

### 4. SSL/TLS Certificate Validation
- **What's New**: SSL validation is now enabled by default
- **Configuration**:
  - New `--ignore-https-errors` flag for exceptions
  - Per-scraper SSL configuration
- **Security**: Prevents man-in-the-middle attacks

### 5. Command Injection Prevention
- **What's New**: Proper escaping of all shell commands
- **Implementation**: Uses `shlex.quote()` for all user inputs in commands
- **Affected Tools**: HTTrack scraper, git operations

### 6. JavaScript Execution Safety
- **What's New**: Validation of custom JavaScript in Playwright scraper
- **Features**:
  - Detects dangerous patterns (eval, Function constructor)
  - Warns about custom script execution
  - Encourages use of built-in actions

### 7. Custom Processor Validation
- **What's New**: Validates processor names to prevent injection attacks
- **Rules**: Only alphanumeric characters and underscores allowed
- **Impact**: Prevents code injection through preset files

## Performance Improvements

### 1. Parallel File Processing
- **Enabled by Default**: Parallel processing is now always active
- **Features**:
  - Concurrent file reading with automatic batch size optimization
  - Thread-safe checksum deduplication
  - Maintains deterministic file order in output
- **Performance**: Up to 3-5x faster for large file sets

### 2. Optimized Checksum Verification
- **What's Changed**: Stream-based file reading for checksums
- **Benefits**:
  - Reduced memory usage for large files
  - Prevents out-of-memory errors
  - 8KB chunk processing

### 3. Concurrent Write Limits in s1f
- **What's New**: Semaphore-based write limiting
- **Default**: 10 concurrent file operations
- **Benefits**: Prevents "too many open files" errors

### 4. Async I/O Improvements
- **Updates**:
  - Uses `aiofiles` for truly async file operations
  - Modern async patterns (asyncio.run())
  - Proper exception handling in async contexts

## Configuration Enhancements

### 1. Content Deduplication Control
- **New CLI Option**: `--allow-duplicate-files`
- **Preset Setting**: `enable_content_deduplication`
- **Default**: Deduplication enabled (False for allow-duplicate)
- **Use Case**: When you need to preserve duplicate content

### 2. UTF-8 Preference Control
- **New CLI Option**: `--no-prefer-utf8-for-text-files`
- **Preset Setting**: `prefer_utf8_for_text_files`
- **Default**: UTF-8 preferred (True)
- **Use Case**: Working with legacy encodings like windows-1252

### 3. Security Check Modes
- **Options**:
  - `error` (default): Stop on security issues
  - `warn`: Log warnings but continue
  - `skip`: Disable security scanning
- **CLI**: `--security-check {error|warn|skip}`
- **Preset**: `security_check` setting

### 4. File Size Limits
- **Preset Files**: Limited to 10MB
- **Benefits**: Prevents memory exhaustion attacks
- **Error Handling**: Clear error messages for oversized files

## Improved Patterns and Flexibility

### 1. Flexible Metadata Stripping
- **What's New**: More flexible regex for scraped content metadata
- **Supports**:
  - Various horizontal rule styles (`---`, `___`, `***`)
  - Different emphasis markers
  - Multiple formatting variations

### 2. Code Block Detection in s1f
- **What's New**: Ignores separators inside code blocks
- **Benefits**: Prevents false positive file detection
- **Applies to**: Markdown code blocks (```)

### 3. Timezone-Aware Timestamps
- **What's Changed**: All timestamps now use UTC
- **Implementation**: `datetime.now(timezone.utc)`
- **Benefits**: Consistent timestamps across timezones

## CLI Updates

### New Options Summary

```bash
# Performance
--allow-duplicate-files         # Disable content deduplication

# Encoding
--no-prefer-utf8-for-text-files # Disable UTF-8 preference

# Security
--security-check {error|warn|skip}  # Security scanning mode
--ignore-https-errors              # Disable SSL validation (scraping)

# Existing options work as before
--source-directory, -s          # Source directory
--output-file, -o              # Output file
--preset                       # Use preset configuration
```

## Breaking Changes

### 1. Standard Separator Format
- **Change**: File separators no longer include checksums
- **Before**: `=== path/to/file.txt === SHA256: abc123...`
- **After**: `=== path/to/file.txt ===`
- **Impact**: s1f can still read old format files

### 2. SSL Validation Default
- **Change**: SSL validation now enabled by default
- **Impact**: May break scraping of sites with invalid certificates
- **Migration**: Use `--ignore-https-errors` if needed

### 3. Security Scanning Default
- **Change**: Security scanning in error mode by default
- **Impact**: Processing stops on sensitive data detection
- **Migration**: Use `--security-check warn` for old behavior

## Preset System Enhancements

### New Preset Settings

```yaml
# Performance
enable_content_deduplication: false  # Allow duplicate files

# Encoding
prefer_utf8_for_text_files: false   # Disable UTF-8 preference

# Security
security_check: warn              # Security check mode

# Per-file settings still work
per_file_settings:
  "*.min.js":
    processors:
      - minify_content
```

## Test Suite Improvements

- Fixed test isolation issues
- Added proper async test support
- Improved test server connectivity handling
- Enhanced security test coverage

## Migration Guide

### From v3.1 to v3.2

1. **Review Security Settings**:
   - Default security scanning may flag legitimate content
   - Use `--security-check warn` during migration

2. **Check SSL Requirements**:
   - Sites with self-signed certificates need `--ignore-https-errors`
   - Review and update scraping scripts

3. **Update Separator Parsing**:
   - If you parse m1f output, update to handle new separator format
   - s1f handles both formats automatically

4. **Performance Tuning**:
   - Parallel processing is automatic - no configuration needed
   - Monitor memory usage with large file sets

## Examples

### Using New Features

```bash
# Security in warn mode (parallel processing is automatic)
m1f -s ./src -o bundle.txt --security-check warn

# Allow duplicates with custom encoding handling
m1f -s ./legacy -o output.txt --allow-duplicate-files --no-prefer-utf8-for-text-files

# Secure web scraping (robots.txt compliance is automatic)
m1f-scrape https://example.com -o ./scraped

# Using new features in presets
m1f -s . -o bundle.txt --preset my-preset.yml
```

### Sample v3.2 Preset

```yaml
name: "Modern Web Project v3.2"
version: "3.2"

# Global settings with v3.2 features
settings:
  enable_content_deduplication: true
  prefer_utf8_for_text_files: true
  security_check: error
  
# File patterns remain the same
include_patterns:
  - "src/**/*.{js,ts,jsx,tsx}"
  - "**/*.md"

exclude_patterns:
  - "**/node_modules/**"
  - "**/.git/**"

# Per-file settings with processors
per_file_settings:
  "*.min.js":
    processors:
      - minify_content
```

## Performance Benchmarks

Typical improvements with v3.2:

- **Parallel Processing**: 3-5x faster for 1000+ files
- **Memory Usage**: 50% reduction for large files
- **s1f Extraction**: 2x faster with concurrent writes
- **Checksum Calculation**: Constant memory usage regardless of file size

## Security Audit Results

v3.2 addresses all HIGH and MEDIUM priority security issues:

- ✅ Path traversal vulnerabilities fixed
- ✅ SSRF protection implemented
- ✅ Command injection prevented
- ✅ SSL validation enforced
- ✅ robots.txt compliance added
- ✅ JavaScript execution validated
- ✅ Race conditions eliminated

## Support and Resources

- [Security Best Practices Guide](./40_security_best_practices.md)
- [CLI Reference](./02_cli_reference.md)
- [Preset System Guide](./10_m1f_presets.md)
- [Troubleshooting Guide](./03_troubleshooting.md)

For questions or issues, please refer to the project repository.