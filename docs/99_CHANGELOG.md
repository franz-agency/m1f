# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **m1f-scrape Session Management**: Complete session tracking system for scraping runs
  - Each scraping run creates a unique session with ID, timestamps, and statistics
  - Sessions track status: running, completed, interrupted, failed
  - Automatic cleanup of orphaned sessions (no activity >1 hour) on startup
  - Manual cleanup with `--cleanup-sessions` command
  - Session viewing with `--show-sessions` and `--show-sessions-detailed`
  - Clear specific sessions with `--clear-session ID` or `--clear-last-session`
  - Database migration to v2 with session support (auto-migrates existing DBs)
  - Session statistics calculated correctly at end of each run
  - Graceful handling of Ctrl+C, crashes, and kill signals
  - Long-running sessions (>1hr) not interrupted if still actively scraping
  - Optional file deletion when clearing sessions with `--delete-files` flag
  - Interactive confirmation prompt for file deletion (skipped with flag)

### Fixed

- **m1f-scrape Max-Pages Counting**: Fixed to count only successfully scraped pages
  - Previously counted all attempted URLs including errors and redirects
  - Now only increments counter for pages that were actually saved
  - Ensures --max-pages limit is respected correctly
  - Fixed issue where scraper would stop prematurely at 1001 URLs when more pages were available

- **m1f-scrape Test Infrastructure**: Fixed all 65 scraping tests to pass
  - Fixed test server startup issues by changing subprocess.PIPE to subprocess.DEVNULL
  - Fixed test server canonical parameter injection causing 500 errors
  - Fixed mock configuration for async context managers in tests
  - Fixed ScraperConfig/CrawlerConfig parameter mismatch
  - Fixed Playwright browser_config parameter handling
  - Fixed Selectolax allowed_path logic for start URL handling
  - Updated test expectations to match corrected behavior

### Added

- **m1f-scrape URL Support for allowed_path**: Parameter now accepts full URLs
  - Can use both paths (`/docs/`) and full URLs (`https://example.com/docs/`)
  - HTTrack properly extracts domain and path from URL-based allowed_path
  - BeautifulSoup validates URLs in should_crawl_url method
  - Useful for restricting crawl to specific subdomains or protocols

- **m1f-scrape Python Mirror Scraper**: New fallback scraper for HTTrack
  - Pure Python implementation for website mirroring
  - Automatically used when HTTrack fails or for localhost URLs
  - Preserves directory structure similar to HTTrack
  - Supports all standard scraper features (robots.txt, rate limiting, etc.)

### Improved

- **m1f-scrape Canonical URL Logic**: Better handling with allowed_path
  - Pages within allowed_path are now kept even if canonical points outside
  - Respects user's intent to scrape content within allowed boundaries
  - All scrapers (BeautifulSoup, HTTrack, Selectolax, Playwright) updated
  - Added comprehensive test coverage for canonical/allowed_path interaction

- **m1f-scrape Unlimited Pages Option**: Support for unlimited scraping
  - Changed default `max_pages` from 1000 to 10000 across all configurations
  - Added support for `-1` as unlimited pages (no limit)
  - Updated validation to allow up to 10 million pages
  - All scrapers now handle `-1` as unlimited:
    - playwright, selectolax, beautifulsoup, scrapy: Skip page limit check when -1
    - httrack: Uses very large number (999999999) for unlimited
  - Updated documentation to explain `-1` unlimited option
  - Added example for unlimited scraping with caution note

- **m1f-scrape Advanced Path Control**: New `--allowed-path` parameter
  - Allows starting from specific page while controlling crawling boundaries
  - Overrides automatic path restriction based on start URL
  - Start URL is always scraped regardless of path restrictions
  - Example: Start from `/Extensions/eZ-Publish-extensions.html` but crawl all `/Extensions/`
  - Useful for documentation sites where index pages link to different directories
  - Implemented across all scraper backends (BeautifulSoup, HTTrack, Selectolax, Playwright, Scrapy)
  - Added `check_ssrf` configuration parameter to enable/disable SSRF protection (defaults to enabled)
  - Fixed test server to support subdirectory routing for comprehensive testing
  - Added integration and unit tests with proper mocking

### Fixed

- **m1f-scrape Canonical URL Logic**: Fixed canonical URL handling with allowed_path
  - Pages within allowed_path are now kept even if canonical points outside
  - Properly handles canonical URLs when both current and canonical are within allowed_path
  - Fixed across all scrapers (BeautifulSoup, HTTrack, Selectolax, Playwright)
  - Added comprehensive tests to verify the behavior

### Improved

- **m1f-scrape Parameter Help Text**: Clarified confusing CLI parameter descriptions
  - `--ignore-canonical` now clearly states default behavior (pages with different canonical URLs are skipped)
  - `--ignore-duplicates` help text clarified to explain default duplicate detection
  - Better organization of parameters into logical groups

- **m1f-scrape Test Coverage**: Created meaningful integration tests
  - Real HTTP requests with local test server instead of mocks
  - Tests that verify actual functionality, not just configuration:
    - `test_ignore_get_params_actually_works` - Verifies URL normalization
    - `test_canonical_url_with_allowed_path_real_behavior` - Tests canonical/allowed_path interaction
    - `test_excluded_paths_actually_excludes` - Verifies paths are actually excluded
    - `test_duplicate_content_detection_actually_works` - Tests content deduplication
    - `test_max_depth_unlimited_actually_works` - Verifies unlimited depth crawling
    - `test_timeout_actually_enforced` - Tests timeout enforcement
  - Separate integration tests for each scraper backend
  - Fixed test server to properly handle canonical parameter injection

### Added

- **m1f-scrape Missing CLI Parameters**: Exposed configuration options in CLI
  - `--excluded-paths`: URL paths to exclude from crawling (can specify multiple)
  - `--timeout`: Request timeout in seconds (default: 30)
  - `--retry-count`: Number of retries for failed requests (default: 3)
  - `--disable-ssrf-check`: Disable SSRF vulnerability checks (allows localhost)
  - Note: Respecting robots.txt is mandatory and cannot be disabled

- **m1f-scrape Unlimited Depth**: Support for unlimited crawl depth
  - `--max-depth` now accepts -1 for unlimited depth (similar to --max-pages)
  - All scrapers updated to handle unlimited depth correctly
  - HTTrack uses very large number (999999) internally

### Removed

- **m1f-scrape Scrapy Support**: Completely removed Scrapy scraper implementation
  - Removed scrapy_scraper.py and all related tests
  - Removed Scrapy from ScraperBackend enum
  - Simplified scraper selection logic

- **m1f-scrape Comprehensive Parameter Tests**: New test suite for all parameters
  - Tests for content filtering (ignore-get-params, ignore-canonical, ignore-duplicates)
  - Tests for excluded paths functionality
  - Tests for request options (user-agent, timeout, retry-count)
  - Tests for different scraper backends
  - Tests for database query options
  - All tests use local test server (no external dependencies)

### Removed

- **m1f-scrape Scrapy Backend**: Removed Scrapy scraper implementation
  - Scrapy had different architecture that complicated maintenance
  - Other scrapers (BeautifulSoup, Selectolax, HTTrack, Playwright) provide sufficient coverage
  - Removed from CLI choices, configuration enum, and all tests
  - Simplifies codebase and reduces dependencies

### Changed

- **m1f-scrape Canonical URL Handling**: Improved canonical URL logic to respect allowed_path
  - Fixed issue where pages within allowed_path were skipped if canonical URL pointed outside
  - Pages within allowed_path are now kept even if their canonical URL points outside the restricted area
  - Added canonical URL checking to Playwright scraper (was previously missing)
  - Improved help text for content filtering options to be clearer:
    - `--ignore-get-params`: Now explains it strips query parameters
    - `--ignore-canonical`: Clarifies it disables canonical URL deduplication
    - `--ignore-duplicates`: Explains it disables content-based deduplication

- **m1f-scrape Help Output**: Improved organization with colorama support
  - Added colorama formatting to match m1f's help output style
  - Organized parameters into logical groups (Output Control, Scraper Options, etc.)
  - Added colored error messages for better visibility
  - Help text now renders with proper formatting on terminals that support it

- **m1f-scrape Real Integration Tests**: Replaced mocked tests with real server tests
  - Selectolax now has comprehensive integration tests using local test server
  - HTTrack tests check for installation and run real tests when available
  - Playwright tests verify JavaScript rendering and browser functionality
  - All integration tests use local test server to avoid external dependencies
  - Fixed test server environment issues for reliable testing

### Fixed

- **m1f-html2md Config Structure**: Fixed configuration structure mismatch
  - Config loader now properly handles nested configuration objects
  - CLI correctly maps arguments to `conversion.outermost_selector` and `conversion.ignore_selectors`
  - Fixed prompts that were generating incorrect config structure with `extractor.content_selector`
  - Updated all prompts to generate the correct structure: `conversion.outermost_selector`
  - Fixed output message to show "outermost_selector" instead of "content_selector"
  - Config files now work correctly with proper field mapping

- **Claude Code Documentation Scraper**: Fixed config file usage
  - When using `--use-config`, script now creates backup directory instead of deleting existing markdown
  - Backup directories named with timestamp: `claude-code-markdown_backup_YYYYMMDD_HHMMSS`
  - Ensures existing markdown files are preserved when re-converting with different config
  - Added datetime import for timestamp generation

## [3.8.0] - 2025-07-24

### Added

- **m1f-research Tool**: New intelligent research content organization tool

  - Smart content analysis with configurable templates (academic, technical,
    summary)
  - Hierarchical output directory structure with automatic organization
  - Database-driven job persistence and management
  - Parallelized scraping with progress tracking
  - LLM provider abstraction (Claude, Gemini, CLI tools)
  - Advanced filtering and search capabilities
  - Comprehensive documentation and examples

- **Shared Utilities Module**: Centralized common functionality

  - Unified colorama output system across all tools
  - Externalized all prompts to markdown templates
  - Shared validation and helper functions
  - Consistent error handling patterns

- **Symlink Deduplication**: Intelligent handling of symbolic links
  - Internal symlinks excluded when deduplication enabled (default)
  - External symlinks always included with their content
  - All symlinks included when using `--allow-duplicate-files`
  - Comprehensive test coverage for all scenarios

### Changed

- **Output System Overhaul**: Complete migration to colorama helpers

  - Replaced all `print()` statements with semantic helpers (info, success,
    warning, error)
  - Consistent colored output across all tools
  - Improved user experience with visual feedback
  - Test files updated to use colorama helpers

- **Version Management**: Centralized version handling

  - All tools now import from `tools._version.py`
  - Single source of truth for version numbers
  - Simplified version bumping process

- **Claude Integration**: Enhanced headless operation
  - Fixed Claude CLI to use `-p` flag for headless mode
  - Improved timeout handling (increased to 120s)
  - Better error messages and debugging output

### Fixed

- **Test Warnings**: Resolved all AsyncMock and pytest warnings

  - Fixed AsyncMock usage with proper async functions
  - Renamed TestServer to HTML2MDTestServer to avoid pytest conflicts
  - Improved test reliability and performance

- **Import Errors**: Fixed module import issues across tools

  - Resolved circular imports in m1f-research
  - Fixed s1f module import errors
  - Corrected test file imports

- **Package Metadata**: Updated package.json
  - Fixed description to "Make One File - AI-ready codebase bundling toolkit"
  - Synchronized version numbers across all files

### Documentation

- **m1f-research**: Added comprehensive documentation

  - Job management guide
  - Template system reference
  - Integration examples
  - README for shared utilities

- **Colorama Guide**: Added unified output system documentation
  - Complete migration guide
  - Usage examples
  - Best practices

## [3.7.0] - 2025-07-21

### Added

- **Pre-commit Hook Enhancement**: Added Python (Black) and Markdown formatting
  to pre-commit hooks for better code quality enforcement
- **Script Help Parameters**: All scripts now support help parameter (`-h`,
  `--help`) for improved user experience
- **PowerShell Commands**: Added missing `m1f-init` and `m1f-claude` commands to
  PowerShell scripts and aliases
- **Documentation**: Added comprehensive Getting Started guide for easier
  onboarding

### Changed

- **README Overhaul**: Complete refresh with engaging, developer-friendly
  content
  - Clear problem statement and solution narrative
  - Enhanced m1f-claude explanation as headless Claude controller
  - Added personality while maintaining professional quality
  - Updated tagline: "Where no AI has coded before™"
  - Improved flow from problem → solution → examples → features
- **Project Structure**:
  - Moved `sync_version.py` to dev directory
  - Moved setup documentation to docs folder
  - Removed dev/ directory from version control
- **Installation Process**: Improved installation and uninstallation scripts
  with better error handling
- **Hooks System**: Completed migration to dual hook system for better
  flexibility
- **Presets Optimization**: Removed redundant defaults for better efficiency

### Fixed

- **Presets**: Removed incorrect `preserve_tags` usage with `strip_tags` to
  prevent configuration conflicts
- **m1f-claude**: Fixed attribute name for `--setup` argument
- **Examples**: Improved robustness of `scrape_claude_code_docs` script
- **Scripts**: Enhanced watcher ignore patterns and VS Code task integration
- **Hooks**:
  - Corrected installation instructions in git hooks installer
  - Removed unnecessary venv activation from m1f-update calls
- **Documentation**:
  - Fixed misleading examples and clarified feature availability
  - Fixed incorrect `--since` flag example (doesn't exist in m1f)
  - Simplified and corrected script paths in installation instructions

### Removed

- **Version Management**: Removed version management section from README
- **Version Bumper**: Removed version bumper from repository
- **Advanced Terminology**: Removed remaining "advanced" terminology from setup
- **Cleanup**: Removed leftover files and test artifacts

## [3.6.0] - 2025-07-19

### Changed

- **m1f-claude**: Renamed `--advanced-setup` parameter to `--setup` for
  simplicity
- **m1f**: Ensure cross-platform compatibility by using forward slashes in
  bundle paths
- **Project Organization**: Cleaned up project root directory
  - Moved `perfect_bundle_prompt.md` to `tools/m1f/prompts/`
  - Moved `wp-cli.example.yml` to `examples/` directory

### Fixed

- **Windows Compatibility**: Major improvements for Windows platform support
  - **m1f**: Fixed path separators to always use forward slashes in bundles for
    cross-platform compatibility
    - Bundles created on Windows can now be extracted on Unix systems and vice
      versa
    - Added comprehensive cross-platform path tests
  - **m1f-claude**: Improved Claude executable detection on Windows
  - **m1f-claude**: Enhanced subprocess handling and timeout behavior for
    Windows
  - **m1f**: Fixed npx execution method compatibility on Windows
  - **m1f-init**: Improved project type detection across platforms
  - **Dependencies**: Downgraded httpx to 0.27.2 for better Windows
    compatibility
  - **Tests**: Added cross-platform test suite with Windows-specific timeout
    handling
  - **Installation**: Fixed PowerShell installation scripts and path handling

## [3.5.0] - 2025-07-18

### Added

- **m1f-claude**: Add project description and priorities input functionality

### Fixed

- **m1f-init**: Correct project type detection to use file count for all
  languages
- **m1f**: Support npx execution method for m1f tool
- **m1f-init**: Preserve dots in project names for bundle generation

### Changed

- Updated package dependencies

## [3.4.2] - 2025-07-08

### Fixed

- **Version Conflict**: Resolved version conflict issues
- **httpx Compatibility**: Downgraded httpx from newer version to 0.27.2 for
  improved compatibility
- **Configuration Consistency**: Updated `source_directory` to
  `source_directories` in configuration for consistency
- **m1f-claude Subprocess Handling**: Improved subprocess handling and timeout
  behavior for Claude executable detection

### Changed

- **Dependencies Update**: Updated multiple dependencies to newer versions for
  improved compatibility and performance

### Removed

- Removed unnecessary documentation files

## [3.4.0] - 2025-07-04

### Added

- **m1f-init Enhancements**: Improved project initialization tool

  - Added `--no-symlink` parameter to skip creating symlink to m1f documentation
  - Added file tracking to show only actually created files in output
  - Improved output formatting with "Here is your file:" / "Here are your
    files:" section
  - Added proper spacing and bullet points for created files list
  - Now runs `m1f-update` when `.m1f.config.yml` already exists instead of
    creating default bundles

- **Multiple Source Directories**: m1f now supports multiple `-s` source
  directories

  - Use `-s dir1 -s dir2` to combine files from multiple directories
  - All source directories are processed and files are merged into single output
  - Useful for documentation bundles that need files from different locations

- **Include Patterns**: Added `--includes` parameter for pattern-based file
  filtering
  - Works with gitignore-style patterns (e.g., `*.py`, `src/**`, `!test.py`)
  - When combined with `--include-extensions`, files must match both criteria
  - Allows precise control over which files to include in bundles

### Changed

- **m1f-init Git Detection**: Improved Git repository detection messages

  - Simplified output for parent directory Git repositories (no longer shows
    paths)
  - Only shows messages for current directory Git repos or no Git repo at all
  - Better handling of subdirectories within larger Git projects

- **m1f-init Language Detection**: Enhanced programming language detection
  - Changed "Not detected" to "No programming languages detected" for clarity
  - Added file counting for all supported languages (Java, C#, Go, Rust, Ruby)
  - Only shows "Programming Languages:" line when languages are actually
    detected
  - Better label clarity with "Programming Languages:" instead of just
    "Languages:"

### Fixed

- **m1f-init .gitignore Handling**: Fixed .gitignore usage in subdirectories

  - Now only uses .gitignore from current directory, not parent directories
  - Prevents errors when running m1f-init in subdirectories without their own
    .gitignore
  - All m1f commands now check for .gitignore existence before using
    --exclude-paths-file

- **m1f-init Python Project Detection**: Fixed language detection prioritization

  - Now prioritizes by file count to correctly identify primary language
  - Python projects are now properly detected even with mixed language codebases

- **m1f-init Behavior with Existing Config**: Fixed to run m1f-update when
  config exists

  - No longer creates default bundles when `.m1f.config.yml` already exists
  - Automatically runs `m1f-update` to use existing configuration

- **m1f Directory Exclusion Performance**: Fixed severe performance issue with
  directory filtering

  - Directory exclusions from .gitignore now properly applied at directory
    traversal level
  - Reduced bundle creation time from 42+ seconds to ~1.2 seconds (35x
    improvement)
  - Fixed tmp/ directory exclusion that was scanning 362,419 unnecessary files

- **m1f Multiple Source Directories**: Fixed CLI to support multiple source
  directories

  - Changed from single source to List[Path] throughout codebase
  - Now properly processes all specified source directories with
    `-s dir1 -s dir2`
  - All files from multiple sources are combined into single output

- **m1f Include Patterns**: Fixed include pattern filtering

  - Include patterns now properly applied from config files
  - Fixed \_load_include_patterns() to run even without include_paths_file
  - Patterns correctly filter files when combined with extension filters

- **m1f Bundle Configuration**: Fixed output directory exclusion pattern

  - Changed `/m1f/**` to `m1f/m1f/**` to only exclude output directory
  - Previously excluded all directories named "m1f" anywhere in the project

- **m1f-html2md Streaming**: Fixed streaming output for Claude AI analysis

  - Fixed common_parent variable scope issue (used before definition)
  - Implemented proper streaming in run_claude_streaming method
  - Fixed ColoredFormatter modifying LogRecord objects (causing ANSI codes in
    logs)
  - Added elapsed time tracking for progress messages
  - Improved subprocess handling for reliable Claude CLI integration

- **m1f-html2md Config Loading**: Made configuration more robust
  - Config loader now handles unknown fields gracefully (with warnings)
  - Automatic conversion of string paths to Path objects
  - Better error handling for Claude-generated configurations

## [3.3.0] - 2025-07-03

### Documentation

- **README.md Enhancements**: Major improvements to project documentation
  - Added clear explanation of what m1f is (Make One File)
  - Added Tailwind CSS 4.0 example demonstrating real-world usage
  - Added concise tool suite overview with links to docs and m1f.dev
  - Added comprehensive feature list emphasizing dynamic/auto-updating
    capabilities
  - Added security note about detect-secrets with link to GitHub repository
  - Added "Beyond AI" section showing alternative uses (backups, bundling,
    encoding conversion)
  - Added bundle location and Claude reference syntax explanation
  - Improved overall structure with developer-friendly tone
  - **Claude Code Integration**: Enhanced documentation for Claude binary
    auto-detection
  - **Example Updates**: Improved clarity for Tailwind CSS and Claude Code usage
    examples
- **HTML2MD Documentation Updates**: Enhanced Claude AI integration
  documentation
  - Added `--analyze-files` parameter documentation
  - Documented project description prompt feature
  - Added subprocess handling improvements
  - Updated examples with new features

### Added

- **HTML2MD Claude AI Integration Enhancements**: Major improvements to
  AI-powered HTML analysis

  - **External Prompt System**: All prompts now loaded from external markdown
    files in `prompts/` directory
    - `select_files_from_project.md`: Strategic selection of 5 representative
      HTML files
    - `analyze_selected_files.md`: Task-based analysis workflow with individual
      file processing
    - `convert_html_to_md.md`: Enhanced HTML to Markdown conversion with quality
      standards
    - Improved maintainability and customization of AI prompts
  - **Task-Based Analysis Workflow**: Multi-phase analysis for better accuracy
    - Phase 1: Individual file analysis with detailed findings saved to separate
      files
    - Phase 2: Synthesis of all analyses to create optimal configuration
    - Deep structural analysis with content boundaries, navigation elements, and
      special content types
    - Creates temporary analysis files in m1f directory for transparency
  - **Write Tool Permission**: Claude now has write permissions for creating
    analysis files
    - Automatically creates individual analysis files (html_analysis_1.txt
      through html_analysis_5.txt)
    - Enables iterative analysis and refinement process
    - Includes cleanup functionality to remove temporary files after user
      confirmation
  - **Directory Access Improvements**: Enhanced Claude integration workflow
    - Uses `--add-dir` parameter instead of changing directories
    - Maintains clean working directory structure
    - Prevents directory traversal issues during analysis
  - **Improved Error Handling**: Better subprocess management and error
    reporting
    - Fixed indentation errors in subprocess.Popen calls
    - Applied black formatting for consistent code style
    - Enhanced logging and progress indicators
    - Changed all subprocess.Popen + communicate() to subprocess.run() for
      reliable Claude CLI integration
    - Added 5-minute timeout handling for subprocess operations
  - **User Experience Improvements**: Enhanced workflow and configuration
    - Added `--analyze-files` parameter to specify number of files to analyze
      (1-20, default: 5)
    - Project description prompt now includes tip about specifying important
      files
    - Output configuration saved as `html2md_extract_config.yaml` instead of
      generic name
    - Fixed file references to use m1f/ instead of @m1f directory
    - Added debug output for transparency during analysis process
    - Cleanup functionality removes temporary analysis files after confirmation
    - **Increased Claude timeouts**: Extended timeout from 5 to 30 minutes for
      large analyses
    - **Improved configuration templates**: Better organized YAML templates for
      extraction rules

- **WebScraper Content Deduplication**: Memory-efficient duplicate prevention
  system (enabled by default)

  - **Database-Backed Deduplication**: Optimized for large scraping sessions
    - Uses SQLite queries instead of loading all checksums into memory
    - Stores checksums in `content_checksums` table with first URL and timestamp
    - Scrapers use callback mechanism to check checksums via database
    - Significantly reduces memory usage for large scraping sessions
    - Maintains deduplication state across resume operations
  - **Content-Based Detection**: SHA-256 checksums of normalized plain text
    - Extracts plain text from HTML (removes all tags, scripts, styles)
    - Decodes HTML entities (&nbsp;, &lt;, etc.)
    - Normalizes whitespace (multiple spaces become single space)
    - Skips pages with identical text content
  - **Three-Layer Deduplication System**:
    1. Canonical URL checking (default: enabled) - Use `--ignore-canonical` to
       disable
    2. Content deduplication (default: enabled) - Use `--ignore-duplicates` to
       disable
    3. GET parameter normalization (default: disabled) - Use
       `--ignore-get-params` to enable
  - **Improved Logging**: Graceful handling of duplicate detection
    - No longer logs duplicates as "unexpected errors"
    - Clear informational messages when skipping duplicate content
    - Transparent reporting of deduplication effectiveness

- **WebScraper Subdirectory Restriction**: Automatic crawling restriction to
  specified paths

  - When URL contains a path (e.g., `https://example.com/docs`), only pages
    under that path are scraped
  - Prevents crawling outside the specified subdirectory (e.g., won't scrape
    `/products` when `/docs` is specified)
  - Works with all scraper backends (BeautifulSoup, HTTrack, Selectolax)
  - Useful for downloading specific documentation sections without the entire
    website
  - Example: `m1f-scrape https://api.example.com/v2/reference` only scrapes
    pages under `/v2/reference`

- **WebScraper Ignore GET Parameters**: New option to prevent duplicate content
  from URLs with different query strings

  - **--ignore-get-params Flag**: Strips GET parameters from URLs during
    scraping
    - Prevents duplicate downloads from URLs like `page.html?tab=linux` and
      `page.html?tab=windows`
    - Normalized URLs are used for visited tracking and file saving
    - Works with all scraper backends (BeautifulSoup, HTTrack, Selectolax)
    - HTTrack uses `-N0` flag to disable query string parsing
    - Useful for documentation sites that use GET parameters for UI state
  - **Example**:
    `m1f-scrape https://docs.example.com -o ./html --ignore-get-params`
    - Will treat `docs.html?version=1` and `docs.html?version=2` as the same
      page

- **WebScraper Canonical URL Checking**: Automatically skip duplicate pages
  based on canonical URLs
  - **Default Behavior**: Checks `<link rel="canonical">` tags on every page
    - Skips pages where canonical URL differs from current URL
    - Prevents downloading duplicate content (print versions, mobile versions,
      etc.)
    - Works with all scraper backends (BeautifulSoup, HTTrack, Selectolax)
    - Logs skipped pages with their canonical URLs for transparency
  - **--ignore-canonical Flag**: Ignore canonical tags when needed
    - Use when you want all page versions regardless of canonical tags
    - Example: `m1f-scrape https://example.com -o ./html --ignore-canonical`
  - **Use Cases**:
    - Documentation sites with multiple URL formats for same content
    - E-commerce sites with product URLs containing tracking parameters
    - News sites with print and mobile versions of articles

### Fixed

- **HTML2MD Claude Integration Issues**: Resolved multiple issues with Claude
  CLI integration
  - Fixed subprocess hanging when using `Popen` + `communicate()` with Claude
    CLI
  - Fixed incorrect m1f usage (now properly uses `--skip-output-file` for
    filelist generation)
  - Fixed file references from embedded content to proper @ syntax
  - Fixed indentation errors in subprocess calls
  - Fixed undefined variable errors (removed unused `html_contents`)
  - Fixed test failure for outdated CLI parameters
  - **Auto-detection of Claude binary**: m1f-html2md --claude now automatically
    detects claude binary location
    - Searches common installation paths including ~/.local/bin/claude
    - Falls back to system PATH if not found in common locations
    - Provides helpful error message if claude CLI is not installed
- **m1f Directory Structure**: Corrected nested directory configuration
  - Fixed .m1f.config.yml to use proper m1f/m1f/ structure
  - Removed accidental triple nesting (m1f/m1f/m1f/)
  - Created proper symlink from m1f/m1f.txt to m1f/m1f/87_m1f_only_docs.txt
- **WebScraper Logging**: Fixed duplicate content detection logging

  - Duplicates no longer logged as "unexpected errors"
  - Changed from exception-based to graceful skip-based handling

- **WebScraper Resume Functionality**: Interrupt and resume web scraping
  sessions
  - **SQLite Database Tracking**: Automatically tracks scraped URLs in
    `scrape_tracker.db`
    - Stores URL, status code, target filename, timestamp, and errors
    - Enables resuming interrupted scraping sessions
    - Database created in output directory for each scraping job
  - **Progress Display**: Real-time display of currently processed URLs
    - Shows "Processing: <URL> (page X)" for each page
    - Verbose mode displays detailed logging information
    - Resume shows "Resuming crawl - found X previously scraped URLs"
  - **Graceful Interruption**: Clean handling of Ctrl+C
    - Shows friendly message: "⚠️ Scraping interrupted by user"
    - Instructions to resume: "Run the same command again to resume where you
      left off"
    - No Python stack traces on interruption
  - **Smart Resume Strategy**: Analyzes previously scraped pages
    - Reads first 20 scraped pages to extract links
    - Populates URL queue with unvisited links from scraped pages
    - Shows "Found X URLs to visit after analyzing scraped pages"
  - **Enhanced CLI**: Better user experience - Added hint "Press Ctrl+C to
    interrupt and resume later" at startup - Logging configuration with `-v`
    flag for progress visibility - Fixed asyncio "Unclosed client session"
    warnings =======
- **m1f-html2md Claude AI Integration**: Intelligent HTML analysis and
  conversion using Claude

  - **Analyze Command Enhancement**: Added `--claude` flag for AI-powered
    analysis
    - Automatically finds all HTML files in directories (no need to specify
      individual files)
    - Uses Claude to intelligently select 5 representative files from scraped
      documentation
    - Analyzes HTML structure and suggests optimal CSS selectors for content
      extraction
    - Excludes navigation, headers, footers, sidebars, and advertisements
    - Runs `m1f-init` automatically in the analysis directory
    - Outputs YAML configuration with content and ignore selectors
  - **Convert Command Enhancement**: Added `--claude` flag for batch HTML to
    Markdown conversion
    - Converts all HTML files in a directory to clean Markdown using Claude AI
    - Supports model selection with `--model` parameter (opus or sonnet)
    - Configurable sleep delay between API calls with `--sleep` parameter
    - Maintains directory structure in output
    - Progress tracking with conversion summary
  - **Prompt Templates**: All prompts stored as markdown files in `prompts/`
    directory
    - `select_files_simple.md` - Selects representative HTML files
    - `analyze_html_simple.md` - Analyzes HTML and suggests CSS selectors
    - `convert_html_to_md.md` - Converts HTML to clean Markdown
  - **Security**: Path traversal protection using existing
    `validate_path_traversal` function
  - **Import Fix**: Fixed ModuleNotFoundError with try/except import pattern

- **--docs-only Parameter**: New command-line flag for documentation-only
  bundles

  - Filters to include only 62 documentation file extensions
  - Simplifies command: `m1f -s . -o docs.txt --docs-only`
  - Replaces verbose `--include-extensions` with 62 extensions
  - Available in presets via `docs_only: true` configuration
  - Overrides include-extensions when set

- **Documentation File Extensions**: Centralized definition in constants.py

  - Added DOCUMENTATION_EXTENSIONS constant with 62 file extensions
  - Added UTF8_PREFERRED_EXTENSIONS constant with 45 UTF-8 preferred formats
  - Includes man pages, markup formats, text files, and developer docs
  - Removed binary formats (.doc, .so) that were incorrectly included
  - Added is_documentation_file() utility function for consistent checks
  - Updated encoding handler to use centralized UTF-8 preference list
  - Documentation extensions now available system-wide for all tools
    > > > > > > > a5263cc2954dda4397238b4001d4bbae4cea973d

- **m1f-claude --init Improvements**: Enhanced project initialization process

  - **Choice-Based Setup**: Users can choose between quick and advanced
    initialization modes
    - Interactive prompt asks for setup preference (1 for quick, 2 for advanced)
    - Command-line parameters: `--quick-setup` and `--setup` for scripting
    - Quick setup: Creates bundles in 30 seconds without Claude
    - Advanced setup: Claude analyzes project and creates topic-specific bundles
  - **Project-Specific Bundle Naming**: All bundles include project directory
    name
    - Example: `m1f_complete.txt`, `m1f_docs.txt` for the m1f project
    - Auxiliary files also include project name: `m1f_complete_filelist.txt`,
      `m1f_complete_dirlist.txt`
    - Makes it easier to identify bundles when working with multiple projects
  - **Auxiliary File Generation**: Both bundles now generate filelist and
    dirlist files
    - Complete bundle creates: `{project}_complete_filelist.txt` and
      `{project}_complete_dirlist.txt`
    - Docs bundle creates: `{project}_docs_filelist.txt` and
      `{project}_docs_dirlist.txt`
    - Provides overview of included files and directory structure
  - **Streamlined Workflow**: Automatic bundle creation without Claude
    dependency
    - Automatically creates complete.txt bundle with all project files
    - Automatically creates docs.txt bundle with 62 documentation extensions
    - Uses --docs-only parameter for efficient documentation bundling
    - Claude Code only invoked for advanced topic-specific segmentation
    - Simplified workflow: git clone → m1f-link → m1f-claude --init → done!
  - **Verbose Mode**: Added `--verbose` flag to show prompts and command
    parameters
    - Displays complete Claude Code command with permissions

- **m1f-init Tool**: New cross-platform initialization tool
  - Replaces m1f-link functionality (m1f-link has been removed)
  - Integrates documentation linking into initialization process
  - Works on Windows, Linux, and macOS
  - Creates complete and docs bundles with project-specific names
  - Generates auxiliary files (filelist, dirlist) for all bundles
  - Creates basic .m1f.config.yml configuration
  - Shows platform-specific next steps
  - On Linux/macOS: Suggests `m1f-claude --setup` for topic bundles

### Changed

- **m1f-claude Refactoring**: Removed initialization from m1f-claude
  - Removed --init, --quick-setup parameters
  - Now only handles --setup for topic-specific bundles
  - Requires m1f-init to be run first (checks for prerequisites)
  - Focuses solely on Claude-assisted advanced configuration
  - Not available on Windows (Linux/macOS only)

### Removed

- **m1f-link Command**: Functionality integrated into m1f-init
  - Documentation linking now happens automatically during m1f-init
  - Simplifies workflow by combining two steps into one

### Enhanced

- **Auxiliary File Documentation**: Added comprehensive documentation

  - Documented filelist and dirlist generation in main m1f documentation
  - Added "Output Files" section explaining all generated files
  - Included examples of working with file lists for custom bundles
  - Updated Quick Start to show all files created by m1f-init
  - Added file list editing workflows to development documentation
    - Shows full prompt being sent for debugging
    - Helps troubleshoot initialization issues
  - **Project Analysis Files**: Create and preserve analysis artifacts in m1f/
    directory
    - Generates `project_analysis_filelist.txt` with all project files
    - Generates `project_analysis_dirlist.txt` with directory structure
    - Files are kept for reference (no cleanup)
    - Respects .gitignore patterns during analysis
    - Explicitly excludes m1f/ directory to prevent recursion
  - **Better Bundle Strategy**: Improved initialization prompts for
    project-specific configs
    - Explicit instruction to read @m1f/m1f.txt documentation first
    - Removed global file size limits from defaults
    - Added proper meta file exclusions (LICENSE*, CLAUDE.md, *.lock)
    - Clear rules against creating test bundles when no tests exist
    - Emphasis on logical segmentation
      (complete/docs/code/components/config/styles)
    - Clarified that dotfiles are excluded by default
    - Added vendor/ to example excludes for PHP projects
  - **Clearer Instructions**: Made prompts more explicit about modifying files
    - Emphasizes that basic config is just a starter needing enhancement
    - Requires 3-5 project-specific bundles minimum
    - Explicit instruction to use Edit/MultiEdit tools
    - Stronger language about actually modifying the config file

- **m1f-claude Enhancements**: Major improvements for intelligent m1f setup
  assistance
  - **Session Persistence**: Implemented proper conversation continuity using
    Claude CLI's `-r` flag
    - Each conversation maintains its own session ID
    - Multiple users can work in the same directory simultaneously
    - Session IDs are extracted from JSON responses and reused
  - **Streaming Output**: Real-time feedback with `--output-format stream-json`
    - Shows Claude's responses as they arrive
    - Displays tool usage in debug mode
    - Provides immediate visual feedback during processing
  - **Tool Permissions**: Added `--allowedTools` parameter with sensible
    defaults
    - Default tools: Read, Edit, MultiEdit, Write, Glob, Grep, Bash
    - Customizable via `--allowed-tools` command line argument
    - Enables file operations and project analysis
  - **Enhanced Prompt System**: Sophisticated prompt enhancement for m1f setup
    - Deep thinking task list approach for systematic m1f configuration
    - Detects when users want to set up m1f (various phrase patterns)
    - Provides 5-phase task list: Analysis, Documentation Study, Design,
      Implementation, Validation
    - Always references @m1f/m1f.txt documentation (5+ references per prompt)
    - Detects and prioritizes AI context files (CLAUDE.md, .cursorrules,
      .windsurfrules)
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
    - Added graceful handling of missing 'cost_usd' field in Claude SDK
      responses
    - Implemented proper anyio task group management for async operations
    - Enhanced error handling with debug logging for SDK issues
    - Fixed subprocess hanging by displaying prompts for manual use instead of
      programmatic execution

### Changed

- **m1f-claude --init Workflow**: Completely redesigned initialization process

  - Now automatically creates complete.txt and docs.txt bundles without Claude
  - Generates .m1f.config.yml with both bundles pre-configured
  - Uses new --docs-only parameter for documentation bundle creation
  - Claude Code only used for advanced topic-specific segmentation
  - Simplified workflow: git clone → m1f-link → m1f-claude --init → done!

- **Dependencies**: Updated claude-code-sdk to use flexible version constraint

  - Changed from `claude-code-sdk==0.0.10` to `claude-code-sdk>=0.0.10`
  - Ensures automatic updates to latest compatible versions
  - Maintains backward compatibility with current version

- **m1f-claude Architecture**: Switched from SDK to subprocess for better
  control
  - Uses Claude CLI directly with proper session management
  - More reliable than the SDK for interactive sessions
  - Better error handling and fallback mechanisms
  - Removed misleading "subprocess fallback" message (it's the primary method
    now)

### Fixed

- **m1f-claude --init Command**: Fixed Claude Code subprocess execution

  - Resolved parameter ordering issue with `--add-dir` flag
  - Changed from stdin-based prompt delivery to `-p` parameter method
  - Implemented fallback to display manual command when subprocess hangs
  - Now shows clear instructions for manual execution with proper parameters
  - Ensures Claude has directory access permissions for file operations

- **PowerShell Installation**: Fixed missing m1f_aliases.ps1 file

  - Created m1f_aliases.ps1 with all PowerShell functions and aliases
  - Added file existence check in setup_m1f_aliases.ps1 before sourcing
  - Fixed hardcoded path issue that caused PowerShell profile errors
  - Now uses correct relative paths based on actual m1f installation location
  - Added PowerShell profile path to warning message for easier debugging

- **m1f-claude Project Name Extraction**: Fixed regex patterns that were failing
  to extract project names
  - Replaced complex regex patterns with backreferences that were causing
    incorrect matches
  - Added simpler, more specific patterns for different name formats (quoted,
    unquoted, possessive)
  - Fixed issue where project names were always extracted as empty strings
  - Now correctly handles formats like "project called 'awesome-app'", "project
    named MyWebApp", "company's main project"

### Dependencies

- Added required dependencies for m1f-claude:
  - anyio==4.9.0 (async support)
  - claude-code-sdk==0.0.10 (Claude integration)

## [3.2.2] - 2025-07-06

### Changed

- **Documentation**: Updated all command examples to use installed bin commands
  - Replaced `python -m tools.m1f` with `m1f`
  - Replaced `python -m tools.s1f` with `m1f-s1f`
  - Replaced `python -m tools.scrape_tool` and `python -m tools.webscraper` with
    `m1f-scrape`
  - Replaced `python -m tools.html2md` and `python -m tools.html2md_tool` with
    `m1f-html2md`
  - Replaced `python tools/token_counter.py` with `m1f-token-counter`
  - Replaced `m1f auto-bundle` with `m1f-update` where appropriate
  - Updated all documentation, scripts, and examples for consistency

### Fixed

- **Scraper Config Files**: Fixed typo in YAML configs (mf1-html2md →
  m1f-scrape)
- **Documentation**: Improved command consistency across all user-facing
  documentation

## [3.2.1] - 2025-06-07

### Fixed

- **Wrapper Scripts**: Added PYTHONPATH to all wrapper scripts to ensure proper
  module imports
- **Pre-commit Hook**: Updated to use python3 and properly handle virtual
  environments
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
