# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-05-25

### 🚀 Major Architectural Overhaul

This is a major release featuring complete architectural modernization of the m1f project, bringing it to Python 3.10+ standards with significant performance improvements and new features.

### Added
- **HTML2MD Converter**: New tool for converting HTML to Markdown with HTTrack integration for website scraping
  - CSS selector-based content extraction
  - Configurable crawl depth and domain restrictions
  - Metadata preservation and frontmatter generation
  - Integration with m1f for bundle creation
- **Content Deduplication**: Automatic detection and removal of duplicate file content based on SHA256 checksums
- **Symlink Support**: Smart symlink handling with cycle detection
- **File Size Filtering**: New `--max-file-size` parameter with unit support (B, KB, MB, GB, TB)
- **Metadata Removal**: New `--remove-scraped-metadata` option for cleaning HTML2MD scraped content
- **Colorized Output**: Beautiful console output with progress indicators
- **Async I/O**: Concurrent file operations for better performance
- **Type Hints**: Comprehensive type annotations using Python 3.10+ features
- **Test Infrastructure**: pytest-timeout for reliable test execution

### Changed
- **Complete Architecture Rewrite**: 
  - m1f transformed from monolithic script to modular package
  - s1f transformed from monolithic script to modular package  
  - Clean architecture with dependency injection and SOLID principles
- **Python Requirements**: Now requires Python 3.10+ (previously 3.9+)
- **Enhanced Security**: Improved security scanning and validation
- **Better Error Handling**: Custom exception hierarchies with specific error types
- **Improved Logging**: Structured logging with configurable levels and colors

### Fixed
- All test suite failures (205 tests now passing)
- S1F content normalization and timestamp tolerance issues
- M1F encoding tests with proper binary file support
- HTML2MD frontmatter generation and CLI integration
- Security warning log format handling
- Path resolution issues in tests
- Memory efficiency for large file handling

### Security
- Removed dangerous placeholder directory creation
- Enhanced input validation
- Better path sanitization
- Improved handling of sensitive data detection

### Breaking Changes
- Internal APIs completely reorganized (CLI remains compatible)
- Module structure changed from single files to packages
- Python 3.10+ now required (was 3.9+)
- Some internal functions renamed or relocated

---

## [1.4.0] - 2025-01-21

### Added
- WordPress content export functionality (`wp_export_md.py`)
- Support for exporting WordPress posts, pages, and custom post types
- Conversion of WordPress HTML content to clean Markdown
- Preservation of WordPress metadata (author, date, categories, tags)
- Flexible filtering options for content export

### Changed
- Improved documentation structure
- Enhanced error handling in export tools

### Fixed
- Various minor bug fixes and improvements

---

## [1.3.0] - 2024-12-15

### Added
- `--max-file-size` parameter for filtering large files
- Size unit support (B, KB, MB, GB, TB)
- Recommended 50KB limit for text file merging

### Changed
- Improved file size handling and validation
- Better error messages for size-related issues

### Fixed
- File size calculation accuracy
- Edge cases in size parsing

---

## [1.2.0] - 2024-11-30

### Added
- Symlink handling with `--include-symlinks` and `--ignore-symlinks` options
- Cycle detection for symlinks to prevent infinite loops
- `--security-check` option with configurable levels (skip, warn, fail)
- Integration with detect-secrets for sensitive data detection

### Changed
- Improved file path resolution
- Better handling of special file types

### Fixed
- Symlink recursion issues
- Security scanning false positives

---

## [1.1.0] - 2024-10-15

### Added
- Content deduplication feature
- `--filename-mtime-hash` option for tracking file changes
- Better support for various text encodings
- Custom argument parser with improved error messages

### Changed
- Optimized file reading for better performance
- Improved separator style formatting
- Enhanced logging output

### Fixed
- Encoding detection issues
- Hash generation consistency
- Memory usage for large projects

---

## [1.0.0] - 2024-09-01

### Added
- Initial release of m1f (Make One File)
- s1f (Split One File) companion tool
- Basic file combination functionality
- Multiple separator styles (XML, Markdown, Plain)
- Gitignore support
- Archive creation (ZIP, TAR)
- Token counting for LLM context estimation

### Features
- Combine multiple files into single output
- Preserve file structure and metadata
- Configurable file filtering
- Multiple output formats
- Cross-platform compatibility