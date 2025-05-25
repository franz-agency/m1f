# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.1.1] - 2025-01-25

### Changed

- Small documentation update
- Improved example consistency across documentation
- Updated file paths in test fixtures
- Cleaned up outdated references

## [2.1.0] - 2025-01-25

### Added

- **Preset System**: Flexible file-specific processing rules

  - Hierarchical preset loading: global (~/.m1f/) → user → project
  - Global settings: encoding, separator style, line endings, includes/excludes
  - Extension-specific processing: HTML minification, CSS compression, comment
    stripping
  - Built-in actions: minify, strip_tags, strip_comments, compress_whitespace,
    remove_empty_lines
  - Custom processors: truncate, redact_secrets, extract_functions
  - CLI options: `--preset`, `--preset-group`, `--disable-presets`
  - Example presets: WordPress, web projects, documentation
  - **Per-file-type overrides**: Different settings for different extensions
    - `security_check`: Enable/disable security scanning per file type
    - `max_file_size`: Different size limits for CSS, JS, PHP, etc.
    - `remove_scraped_metadata`: Clean HTML2MD files selectively
    - `include_dot_paths`, `include_binary_files`: File-type specific filtering
  - **Auto-bundling with presets**: New scripts and VS Code tasks
    - `scripts/auto_bundle_preset.sh` - Preset-based intelligent bundling
    - `tasks/auto_bundle.json` - 11 VS Code tasks for automated bundling
    - Focus areas: WordPress, web projects, documentation
    - Integration with preset system for file-specific processing
  - **Test suite**: Basic preset functionality tests
    - Global settings and file filtering tests
    - File-specific action processing tests
    - Integration verification

- **Auto-bundling System**: Automatic project organization for AI/LLM
  consumption
  - `scripts/auto_bundle.sh` - Basic bundling with predefined categories
  - `scripts/auto_bundle_v2.sh` - Advanced bundling with YAML configuration
  - `.m1f.config.yml` - Customizable bundle definitions and priorities
  - `scripts/watch_and_bundle.sh` - File watcher for automatic updates
  - Bundle types: docs, src, tests, complete, and custom focus areas
- **Claude Code Integration** (optional): AI-powered tool automation

  - `tools/claude_orchestrator.py` - Natural language command processing
  - Integration with Claude Code CLI for workflow automation
  - Project-specific `.claude/settings.json` configuration
  - Example workflows and documentation

- **HTML2MD Preprocessing System**: Configurable HTML cleaning
  - `tools/html2md/analyze_html.py` - Analyze HTML for preprocessing patterns
  - `tools/html2md/preprocessors.py` - Generic preprocessing framework
  - Removed hardcoded project-specific logic
  - Support for custom preprocessing configurations per project

### Changed

- HTML2MD now uses configurable preprocessing instead of hardcoded rules
- Updated documentation structure to include new features

### Fixed

- Preset `strip_tags` action now properly strips all HTML tags when no specific
  tags are specified
- Added missing `get_file_specific_settings` method to PresetManager class

### Documentation

- Added Preset System Guide (`docs/m1f_presets.md`)
- Added Auto Bundle Guide (`docs/AUTO_BUNDLE_GUIDE.md`)
- Added Claude Code Integration Guide (`docs/CLAUDE_CODE_INTEGRATION.md`)
- Added example workflows (`examples/claude_workflows.md`)
- Updated main documentation index with new features

## [2.0.1] - 2025-05-25

### Fixed

- All test suite failures now pass (100% success rate)
  - S1F: Fixed content normalization and timestamp tolerance issues
  - M1F: Fixed encoding test with proper binary file handling
  - HTML2MD: Fixed server tests and API implementation
  - Security: Fixed warning log format detection with ANSI codes
- Documentation formatting and consistency issues

### Changed

- Applied Black formatting to all Python code
- Applied Prettier formatting to all Markdown files
- Updated all documentation to consistently use module execution syntax

### Documentation

- Updated all docs to reflect v2.0.0 architecture changes
- Added architecture sections to all tool documentation
- Modernized API examples with async/await patterns
- Updated token limits for latest LLM models

## [2.0.0] - 2025-05-25

### 🚀 Major Architectural Overhaul

This is a major release featuring complete architectural modernization of the
m1f project, bringing it to Python 3.10+ standards with significant performance
improvements and new features.

### Added

- **HTML2MD Converter**: New tool for converting HTML to Markdown with HTTrack
  integration for website scraping
  - CSS selector-based content extraction
  - Configurable crawl depth and domain restrictions
  - Metadata preservation and frontmatter generation
  - Integration with m1f for bundle creation
- **Content Deduplication**: Automatic detection and removal of duplicate file
  content based on SHA256 checksums
- **Symlink Support**: Smart symlink handling with cycle detection
- **File Size Filtering**: New `--max-file-size` parameter with unit support (B,
  KB, MB, GB, TB)
- **Metadata Removal**: New `--remove-scraped-metadata` option for cleaning
  HTML2MD scraped content
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
- **Better Error Handling**: Custom exception hierarchies with specific error
  types
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
