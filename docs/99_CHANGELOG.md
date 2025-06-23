# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **WebScraper Resume Functionality**: Interrupt and resume web scraping sessions
  - **SQLite Database Tracking**: Automatically tracks scraped URLs in `scrape_tracker.db`
    - Stores URL, status code, target filename, timestamp, and errors
    - Enables resuming interrupted scraping sessions
    - Database created in output directory for each scraping job
  - **Progress Display**: Real-time display of currently processed URLs
    - Shows "Processing: <URL> (page X)" for each page
    - Verbose mode displays detailed logging information
    - Resume shows "Resuming crawl - found X previously scraped URLs"
  - **Graceful Interruption**: Clean handling of Ctrl+C
    - Shows friendly message: "⚠️ Scraping interrupted by user"
    - Instructions to resume: "Run the same command again to resume where you left off"
    - No Python stack traces on interruption
  - **Smart Resume Strategy**: Analyzes previously scraped pages
    - Reads first 20 scraped pages to extract links
    - Populates URL queue with unvisited links from scraped pages
    - Shows "Found X URLs to visit after analyzing scraped pages"
  - **Enhanced CLI**: Better user experience
    - Added hint "Press Ctrl+C to interrupt and resume later" at startup
    - Logging configuration with `-v` flag for progress visibility
    - Fixed asyncio "Unclosed client session" warnings

- **m1f-claude --init Improvements**: Enhanced project initialization process
  - **Verbose Mode**: Added `--verbose` flag to show prompts and command parameters
    - Displays complete Claude Code command with permissions
    - Shows full prompt being sent for debugging
    - Helps troubleshoot initialization issues
  - **Project Analysis Files**: Create and preserve analysis artifacts in m1f/ directory
    - Generates `project_analysis_filelist.txt` with all project files
    - Generates `project_analysis_dirlist.txt` with directory structure
    - Files are kept for reference (no cleanup)
    - Respects .gitignore patterns during analysis
    - Explicitly excludes m1f/ directory to prevent recursion
  - **Better Bundle Strategy**: Improved initialization prompts for project-specific configs
    - Explicit instruction to read @m1f/m1f.txt documentation first
    - Removed global file size limits from defaults
    - Added proper meta file exclusions (LICENSE*, CLAUDE.md, *.lock)
    - Clear rules against creating test bundles when no tests exist
    - Emphasis on logical segmentation (complete/docs/code/components/config/styles)
    - Clarified that dotfiles are excluded by default
    - Added vendor/ to example excludes for PHP projects
  - **Clearer Instructions**: Made prompts more explicit about modifying files
    - Emphasizes that basic config is just a starter needing enhancement
    - Requires 3-5 project-specific bundles minimum
    - Explicit instruction to use Edit/MultiEdit tools
    - Stronger language about actually modifying the config file

- **m1f-claude Enhancements**: Major improvements for intelligent m1f setup assistance
  - **Session Persistence**: Implemented proper conversation continuity using Claude CLI's `-r` flag
    - Each conversation maintains its own session ID
    - Multiple users can work in the same directory simultaneously
    - Session IDs are extracted from JSON responses and reused
  - **Streaming Output**: Real-time feedback with `--output-format stream-json`
    - Shows Claude's responses as they arrive
    - Displays tool usage in debug mode
    - Provides immediate visual feedback during processing
  - **Tool Permissions**: Added `--allowedTools` parameter with sensible defaults
    - Default tools: Read, Edit, MultiEdit, Write, Glob, Grep, Bash
    - Customizable via `--allowed-tools` command line argument
    - Enables file operations and project analysis
  - **Enhanced Prompt System**: Sophisticated prompt enhancement for m1f setup
    - Deep thinking task list approach for systematic m1f configuration
    - Detects when users want to set up m1f (various phrase patterns)
    - Provides 5-phase task list: Analysis, Documentation Study, Design, Implementation, Validation
    - Always references @m1f/m1f.txt documentation (5+ references per prompt)
    - Detects and prioritizes AI context files (CLAUDE.md, .cursorrules, .windsurfrules)
    - Project-aware recommendations based on detected frameworks
    - Line-specific documentation references for key sections
  - **Debug Mode**: Added `--debug` flag for detailed output
    - Shows session IDs, costs, and API usage
    - Displays tool invocations and responses
    - Helps troubleshoot issues and monitor usage
  - **Interactive Mode UX**: Improved visual feedback
    - "Claude is thinking..." indicator during processing
    - Tool usage notifications: `[🔧 Using tool: Read]`
    - Response completion indicator: `[✅ Response complete]`
    - Better prompt spacing with newlines before "You:"
    - Clear separation between responses and new prompts
    - Interaction counter: prompts to continue after every 10 exchanges
    - Ctrl-C signal handling for graceful cancellation
    - Tool output preview: shows abbreviated results from Claude's tool usage
    - Emphasis on Standard separator (not Markdown) for AI-optimized bundles
  - **Exit Command**: Added `/e` command support like Claude CLI
    - Works alongside 'quit', 'exit', and 'q' commands
    - Updated help text and keyboard interrupt messages
  - **Initialization Command**: Fixed `--init` command async/await issues
    - Resolved RuntimeError with cancel scope in different task
    - Added graceful handling of missing 'cost_usd' field in Claude SDK responses
    - Implemented proper anyio task group management for async operations
    - Enhanced error handling with debug logging for SDK issues
    - Fixed subprocess hanging by displaying prompts for manual use instead of programmatic execution

### Changed

- **Dependencies**: Updated claude-code-sdk to use flexible version constraint
  - Changed from `claude-code-sdk==0.0.10` to `claude-code-sdk>=0.0.10`
  - Ensures automatic updates to latest compatible versions
  - Maintains backward compatibility with current version

- **m1f-claude Architecture**: Switched from SDK to subprocess for better control
  - Uses Claude CLI directly with proper session management
  - More reliable than the SDK for interactive sessions
  - Better error handling and fallback mechanisms
  - Removed misleading "subprocess fallback" message (it's the primary method now)

### Fixed

- **PowerShell Installation**: Fixed missing m1f_aliases.ps1 file
  - Created m1f_aliases.ps1 with all PowerShell functions and aliases
  - Added file existence check in setup_m1f_aliases.ps1 before sourcing
  - Fixed hardcoded path issue that caused PowerShell profile errors
  - Now uses correct relative paths based on actual m1f installation location
  - Added PowerShell profile path to warning message for easier debugging

- **m1f-claude Project Name Extraction**: Fixed regex patterns that were failing to extract project names
  - Replaced complex regex patterns with backreferences that were causing incorrect matches
  - Added simpler, more specific patterns for different name formats (quoted, unquoted, possessive)
  - Fixed issue where project names were always extracted as empty strings
  - Now correctly handles formats like "project called 'awesome-app'", "project named MyWebApp", "company's main project"

### Dependencies

- Added required dependencies for m1f-claude:
  - anyio==4.9.0 (async support)
  - claude-code-sdk==0.0.10 (Claude integration)

## [3.2.2] - 2025-07-06

### Changed

- **Documentation**: Updated all command examples to use installed bin commands
  - Replaced `python -m tools.m1f` with `m1f`
  - Replaced `python -m tools.s1f` with `m1f-s1f`
  - Replaced `python -m tools.scrape_tool` and `python -m tools.webscraper` with `m1f-scrape`
  - Replaced `python -m tools.html2md` and `python -m tools.html2md_tool` with `m1f-html2md`
  - Replaced `python tools/token_counter.py` with `m1f-token-counter`
  - Replaced `m1f auto-bundle` with `m1f-update` where appropriate
  - Updated all documentation, scripts, and examples for consistency

### Fixed

- **Scraper Config Files**: Fixed typo in YAML configs (mf1-html2md → m1f-scrape)
- **Documentation**: Improved command consistency across all user-facing documentation

## [3.2.1] - 2025-06-07

### Fixed

- **Wrapper Scripts**: Added PYTHONPATH to all wrapper scripts to ensure proper module imports
- **Pre-commit Hook**: Updated to use python3 and properly handle virtual environments
- **Bin Scripts**: All wrapper scripts now preserve current working directory

## [3.2.0] - 2025-06-06

### Added

- **Git Hooks Integration**: Automatic bundle generation on every commit

  - Pre-commit hook that runs `m1f auto-bundle` before each commit
  - Installation script with remote download support:
    `curl -sSL https://raw.githubusercontent.com/franzundfranz/m1f/main/scripts/install-git-hooks.sh | bash`
  - Auto-detection of m1f development repository vs. installed m1f
  - Automatic staging of generated bundles in `m1f/` directory
  - Comprehensive setup guide at `docs/05_development/56_git_hooks_setup.md`

- **Bundle Directory Migration**: Moved from `.m1f/` to `m1f/` for better AI
  tool compatibility

  - AI tools like Claude Code can now access bundled files directly
  - Generated bundles are included in version control by default
  - Automatic migration of configuration paths
  - Updated `m1f-link` command to create symlinks in `m1f/` directory
  - Added `m1f/README.md` explaining auto-generated files

- **Complete Preset Parameter Support**: ALL m1f parameters can now be
  configured via presets

  - Input/Output settings: source_directory, input_file, output_file,
    input_include_files
  - Output control: add_timestamp, filename_mtime_hash, force, minimal_output,
    skip_output_file
  - Archive settings: create_archive, archive_type
  - Runtime behavior: verbose, quiet
  - CLI arguments always take precedence over preset values
  - Enables simple commands like `m1f --preset production.yml`
  - Updated template-all-settings.m1f-presets.yml with all new parameters
  - Full documentation in docs/01_m1f/12_preset_reference.md

- **Auto-Bundle Subcommand**: Integrated auto-bundle functionality directly into
  m1f

  - New `auto-bundle` subcommand for creating multiple bundles from YAML config
  - Reads `.m1f.config.yml` from project root
  - Supports creating all bundles or specific bundles by name
  - `--list` option to show available bundles with descriptions
  - `--verbose` and `--quiet` options for output control
  - `m1f-update` command provides convenient access from anywhere
  - Full compatibility with existing `.m1f.config.yml` format
  - Supports all m1f options: presets, exclude/include files, conditional
    bundles
  - Updated `watch_and_bundle.sh` to use new auto-bundle functionality

- **Simplified Installation System**: Complete installer scripts for all
  platforms

  - New `install.sh` handles entire setup process (3 commands total!)
  - New `install.ps1` for Windows with full automation
  - Automatic Python 3.10+ version checking
  - Virtual environment creation and dependency installation
  - Initial bundle generation during setup
  - Smart shell detection for immediate PATH activation
  - `uninstall.sh` for clean removal

- **PATH-based Command System**: Replaced aliases with executable wrappers

  - Created `bin/` directory with standalone executable scripts
  - Each wrapper activates venv and runs appropriate tool
  - Works consistently across all shells and platforms
  - Optional symlink creation in ~/.local/bin

- **m1f-claude Command**: Smart prompt enhancement for Claude AI

  - New `m1f-claude` command that enhances prompts with m1f knowledge
  - Automatically injects m1f documentation context into prompts
  - Interactive mode for continued conversations
  - Project structure analysis for better suggestions
  - Contextual hints based on user intent (bundling, config, WordPress, AI
    context)
  - Integration with Claude Code CLI (if installed)
  - Comprehensive workflow guide at docs/01_m1f/30_claude_workflows.md

- **Enhanced Auto-Bundle Functionality**: Improved usability and flexibility

  - Config file search now traverses from current directory up to root
  - New `--group` parameter to create bundles by group (e.g.,
    `m1f auto-bundle --group documentation`)
  - Bundle grouping support in `.m1f.config.yml` with `group: "name"` field
  - Improved error messages when config file is not found
  - Enhanced `--list` output showing bundles organized by groups
  - Comprehensive documentation in `docs/01_m1f/20_auto_bundle_guide.md`
  - Examples for server-wide bundle management and automation

- **Join Paragraphs Feature**: Markdown optimization for LLMs

  - New `JOIN_PARAGRAPHS` processing action to compress markdown
  - Intelligently joins multi-line paragraphs while preserving structure
  - Preserves code blocks, tables, lists, and other markdown elements
  - Helps maximize content in the first 200 lines that LLMs read intensively
  - Available in presets for documentation bundles

- **S1F List Command**: Display archive contents without extraction

  - New `--list` flag to show files in m1f archives
  - Displays file information including size, encoding, and type
  - No longer shows SHA256 hashes for cleaner output
  - Useful for previewing archive contents before extraction

- **Configurable UTF-8 Preference**: Made UTF-8 encoding preference for text
  files configurable

  - Added `prefer_utf8_for_text_files` option to EncodingConfig (defaults to
    True)
  - New CLI flag `--no-prefer-utf8-for-text-files` to disable UTF-8 preference
  - Configurable via preset files through `prefer_utf8_for_text_files` setting
  - Affects only text files (.md, .markdown, .txt, .rst) when encoding detection
    is ambiguous

- **Configurable Content Deduplication**: Made content deduplication optional
  - Added `enable_content_deduplication` option to OutputConfig (defaults to
    True)
  - New CLI flag `--allow-duplicate-files` to include files with identical
    content
  - Configurable via preset files through `enable_content_deduplication` setting
  - Useful when you need to preserve all files regardless of duplicate content

### Fixed

- **Security**: Comprehensive path traversal protection across all tools

  - Added path validation to prevent directory traversal attacks
  - Block paths with `../` or `..\` patterns
  - Reject absolute paths in s1f extraction
  - Validate all user-provided file paths including symlink targets
  - Allow legitimate exceptions: home directory configs (~/.m1f/), output files

- **Markdown Format**: Fixed separator and content formatting issues

  - Content now properly starts on new line after code fence in markdown format
  - Added blank line between separator and content in parallel processing mode
  - Fixed S1F markdown parser to correctly handle language hint and newline
  - Fixed closing ``` for markdown format in parallel processing

- **S1F List Output**: Simplified file information display

  - Removed SHA256 hash display from list output
  - No longer shows "[Unknown]" for missing file sizes
  - Only displays file size when available

- **Standard Separator Format**: Removed checksum from display
  - Standard format now shows only file path without SHA256
  - Simplified output for better readability
  - Parser ignores separators inside code blocks to prevent false positives

### Changed

- **Parallel File Processing**: Enhanced performance for large projects

  - Added optional `--parallel` flag for concurrent file processing
  - Implemented asyncio-based batch handling with proper thread safety
  - Added locks for thread-safe checksum operations
  - Maintained file ordering in output despite parallel processing
  - Automatic fallback to sequential processing for single files

- **Auto-bundle config file** (`.m1f.config.yml`) updated with group
  categorization

  - Documentation bundles grouped under "documentation"
  - Source code bundles grouped under "source"
  - Complete project bundle in "complete" group

- **Command Naming Standardization**: All tools now use m1f- prefix

  - `s1f` → `m1f-s1f`
  - `html2md` → `m1f-html2md`
  - `webscraper` → `m1f-scrape`
  - `token-counter` → `m1f-token-counter`
  - Prevents naming conflicts with system commands

- **Module Execution**: Fixed import errors with proper module syntax

  - All scripts now use `python -m tools.m1f` format
  - Ensures reliable imports across different environments
  - Updated all documentation examples

- **WebScraper Rate Limiting**: Conservative defaults for Cloudflare protection

  - Changed default request delay from 0.5s to 15s
  - Reduced concurrent requests from 5 to 2
  - Added bandwidth limiting (100KB/s) and connection rate limits
  - Created cloudflare.yaml config with ultra-conservative 30s delays

- **Code Quality**: Comprehensive linting and formatting
  - Applied Black formatting to all Python code
  - Applied Prettier formatting to all Markdown files
  - Added/updated license headers across all source files
  - Removed deprecated test files and debug utilities

### Security

- **Path Traversal Protection**: Comprehensive validation across all tools

  - Prevents attackers from using paths like `../../../etc/passwd`
  - Validates resolved paths against project boundaries
  - Allows legitimate exceptions for configs and output files
  - Added extensive security tests

- **Scraper Security**: Enhanced security measures
  - Enforced robots.txt compliance with caching
  - Added URL validation to prevent SSRF attacks
  - Basic JavaScript validation to block dangerous scripts
  - Sanitized command arguments in HTTrack to prevent injection

### Improved

- **HTML2MD Enhancement**: Better file path handling

  - Improved source path logic for file inputs
  - Enhanced relative path resolution for edge cases
  - Consistent output path generation with fallback mechanisms
  - Removed hardcoded Anthropic-specific navigation selectors

- **Encoding Detection**: Enhanced fallback logic

  - Default to UTF-8 if chardet fails or returns empty
  - Prefer UTF-8 over Windows-1252 for markdown files
  - Expanded encoding map for better emoji support
  - Better handling of exotic encodings

- **Async I/O Support**: Performance optimizations

  - S1F now supports optional aiofiles for async file reading
  - Better handling of deprecated asyncio methods
  - Improved concurrent operation handling

- **Testing Infrastructure**: Comprehensive test improvements
  - Reorganized test structure for better clarity
  - Added path traversal security tests
  - Fixed all test failures (100% success rate)
  - Added pytest markers for test categorization
  - Improved test documentation

### Removed

- Obsolete scripts replaced by integrated functionality:
  - `scripts/auto_bundle.py` (now `m1f auto-bundle`)
  - `scripts/auto_bundle.sh` (now `m1f auto-bundle`)
  - `scripts/auto_bundle.ps1` (now `m1f auto-bundle`)
  - `scripts/update_m1f_files.sh` (now `m1f-update`)
  - `setup_m1f_aliases.sh` (replaced by bin/ directory)
  - Deprecated test files and debug utilities (~3000 lines removed)

## [3.1.0] - 2025-06-04

### Added - html2md

- **Custom Extractor System**: Site-specific content extraction
  - Pluggable extractor architecture for optimal HTML parsing
  - Support for function-based and class-based extractors
  - Extract, preprocess, and postprocess hooks
  - Dynamic loading of Python extractor files
  - Default extractor for basic navigation removal
- **Workflow Integration**: Organized .scrapes directory structure
  - Standard directory layout: html/, md/, extractors/
  - .scrapes directory added to .gitignore
  - Supports Claude-assisted extractor development
- **CLI Enhancement**: `--extractor` option for custom extraction logic
- **API Enhancement**: Extractor parameter in Html2mdConverter constructor

### Changed - html2md

- Removed all Anthropic-specific code from core modules
- Cleaned up api.py to remove hardcoded navigation selectors
- Improved modularity with separate extractor system

### Added - m1f

- **Multiple Exclude/Include Files Support**: Enhanced file filtering
  capabilities
  - `exclude_paths_file` and `include_paths_file` now accept multiple files
  - Files are merged in order, non-existent files are gracefully skipped
  - Include files work as whitelists - only matching files are processed
  - Full backward compatibility with single file syntax
  - CLI supports multiple files: `--exclude-paths-file file1 file2 file3`
  - YAML config supports both single file and list syntax

### Changed

- Enhanced file processor to handle pattern merging from multiple sources
- Updated CLI arguments to accept multiple files with `nargs="+"`
- Improved pattern matching for exact path excludes/includes

## [3.0.1] - 2025-06-04

### Fixed

- **Configuration Parsing**: Fixed YAML syntax error in .m1f.config.yml
  - Corrected array item syntax in include_files sections
  - Removed erroneous hyphens within square bracket array notation

## [3.0.0] - 2025-06-03

### Added

- **Python-based auto_bundle.py**: Cross-platform bundling implementation
  - Pure Python alternative to shell scripts
  - Improved include-extensions handling
  - Dynamic watcher ignores based on configuration
  - Global excludes support
  - Better error handling and logging
- **Enhanced Bundling Configuration**: Advanced m1f.config.yml structure
  - Config-based directory setup
  - Refined source rules for s1f-code and all bundles
  - Improved path handling for m1f/s1f separation
- **Depth-based Sorting**: Files and directories now sorted by depth for better
  organization
- **Improved Documentation**: Comprehensive updates to m1f documentation
  - Added CLI reference and troubleshooting guides
  - Enhanced preset system documentation
  - Clarified script invocation methods
  - Added quick reference guides
- **Testing Improvements**: Enhanced asyncio handling across test suites
  - Better pytest configuration for async tests
  - Preset configuration support in scrapers
  - Fixed import and linting issues
- **License Change**: Migrated from MIT to Apache 2.0 License
  - Added NOTICE file with proper attribution
  - Updated all license references throughout codebase

### Changed

- **Refactored Web Scraping Architecture**: Separated webscraper from HTML2MD
  - Cleaner separation of concerns
  - Better modularity for each tool
  - Improved maintainability
- **Build System Enhancements**: Overhauled build configuration
  - Optimized bundling for tool segregation
  - Added quiet flag to suppress unnecessary log file creation
  - Enhanced PowerShell support with auto_bundle.ps1
- **Documentation Structure**: Reorganized docs for better navigation
  - Renamed files for improved sorting
  - Moved changelog to dedicated location
  - Updated all references to new structure

### Fixed

- **Script Issues**: Multiple fixes for auto-bundling scripts
  - Corrected include-extensions parameter handling
  - Fixed config file parsing and argument handling
  - Resolved path resolution issues
- **Test Errors**: All test suite issues resolved
  - Fixed async test handling
  - Corrected import statements
  - Resolved linting issues (Black and Markdown)
- **Configuration Issues**: Fixed various config problems
  - Corrected output paths in m1f.config.yml
  - Fixed switch handling in scripts
  - Updated autobundler configurations

### Dependencies

- Updated aiohttp to 3.10.11 for security and performance improvements
- Added new packages to support enhanced functionality

---

### Original 3.0.0 Features (from earlier development)

- **Pluggable Web Scraper Backends**: HTML2MD now supports multiple scraper
  backends for different use cases
  - **Selectolax** (httpx + selectolax): Blazing fast HTML parsing with minimal
    resource usage
  - **Scrapy**: Industrial-strength web scraping framework with middleware
    support
  - **Playwright**: Browser automation for JavaScript-heavy sites and SPAs
  - Each scraper is optimized for specific scenarios:
    - Selectolax: Maximum performance for simple HTML (20+ concurrent requests)
    - Scrapy: Complex crawling with retry logic, caching, and auto-throttle
    - Playwright: Full JavaScript execution with multiple browser support
  - CLI option `--scraper` to select backend (beautifulsoup, httrack,
    selectolax, scrapy, playwright)
  - Backend-specific configuration files in `scrapers/configs/`
  - Graceful fallback when optional dependencies are not installed

### Changed

- **HTML2MD Version**: Bumped to 3.0.0 for major feature addition
- **Scraper Architecture**: Refactored to plugin-based system with abstract base
  class
- **Documentation**: Comprehensive updates for all scraper backends with
  examples
- **CLI**: Extended to support new scraper options and configuration
- **HTTrack Integration**: Replaced Python HTTrack module with native Linux
  httrack command
  - Now uses real HTTrack command-line tool for professional-grade website
    mirroring
  - Better performance, reliability, and standards compliance
  - Requires system installation: `sudo apt-get install httrack`
  - Enhanced command-line options mapping for HTTrack features

### Documentation

- Added Web Scraper Backends Guide (`docs/html2md_scraper_backends.md`)
- Updated HTML2MD documentation with new scraper examples
- Added configuration examples for each scraper backend

## [2.1.1] - 2025-05-25

### Changed

- Small documentation update
- Improved example consistency across documentation
- Updated file paths in test fixtures
- Cleaned up outdated references

## [2.1.0] - 2025-05-25

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

## [1.4.0] - 2025-05-19

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

## [1.3.0] - 2025-05-18

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

## [1.2.0] - 2025-05-17

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

## [1.1.0] - 2025-05-16

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

## [1.0.0] - 2025-05-15

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
