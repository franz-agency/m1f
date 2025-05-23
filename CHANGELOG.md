# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.2.0] - 2025-01-28

### 🚀 New HTML to Markdown Converter Tool

This release introduces a completely new, modern HTML to Markdown converter tool designed for processing entire websites and seamless integration with m1f.

#### ✨ Added
- **New `html_to_md` Package**: Modern, modular tool for HTML to Markdown conversion:
  - `html_to_md/__init__.py` - Package initialization and version info
  - `html_to_md/api.py` - High-level Python API for programmatic use
  - `html_to_md/cli.py` - Modern command-line interface with subcommands
  - `html_to_md/config/` - Pydantic-based configuration system with YAML/TOML support
  - `html_to_md/core/` - Core parsing and conversion functionality
  - `html_to_md/crawlers/` - HTTrack integration for website mirroring
  - `html_to_md/utils/` - Encoding detection and logging utilities
  - `html_to_md/__main__.py` - Module execution support

- **HTTrack Integration**: Professional website mirroring capabilities:
  - Complete website crawling with HTTrack
  - Configurable crawl depth and page limits
  - Domain restrictions and URL filtering
  - robots.txt compliance
  - Bandwidth and connection management

- **Advanced Content Extraction**:
  - CSS selectors for precise content targeting
  - Metadata extraction (OpenGraph, Schema.org, meta tags)
  - Smart heading hierarchy detection
  - Configurable element filtering (nav, sidebar, ads)

- **Modern Python Features**:
  - Python 3.10+ with type hints throughout
  - Pydantic models for configuration validation
  - Async support for web operations
  - Rich CLI with progress bars
  - Structured logging with color support

- **Processing Capabilities**:
  - Parallel file processing for large directories
  - Automatic encoding detection and conversion
  - Link conversion (HTML → Markdown)
  - Code block language detection
  - Heading level adjustment
  - Whitespace normalization

#### 🔧 Changed
- **REMOVED OLD TOOL**: Replaced monolithic `html_to_md.py` (992 lines) with modular package structure
- **IMPROVED ARCHITECTURE**: 
  - Clean separation of concerns with dedicated modules
  - Plugin-ready architecture for extensibility
  - Dependency injection pattern
  - Configuration-driven design

#### 🎯 Key Features
- **Multiple Input Sources**: Files, directories, URLs, entire websites
- **Flexible Configuration**: YAML/TOML config files or programmatic API
- **m1f Integration**: Direct creation of m1f bundles from converted content
- **Performance**: Parallel processing with configurable workers
- **Reliability**: Comprehensive error handling and logging

#### 📦 Dependencies
- **Required**: beautifulsoup4, markdownify, pydantic, rich, requests, chardet, pyyaml
- **Optional**: toml (for TOML configs), aiohttp (for async operations)
- **External**: HTTrack for website mirroring (system package)

#### 🚀 Usage Examples

**Command Line:**
```bash
# Convert single file
python -m tools.html_to_md convert index.html -o index.md

# Convert directory
python -m tools.html_to_md convert ./html/ -o ./markdown/

# Crawl website
python -m tools.html_to_md crawl https://example.com -o ./docs/

# With config file
python -m tools.html_to_md convert ./html/ -c config.yaml
```

**Python API:**
```python
from tools.html_to_md import HtmlToMarkdownConverter

# Simple conversion
converter = HtmlToMarkdownConverter({
    "source": "./html",
    "destination": "./markdown",
    "extractor": {
        "content_selector": "article.content",
        "ignore_selectors": ["nav", "footer"]
    }
})

# Convert website
results = converter.convert_website("https://example.com")
```

#### 🏗️ Architecture Overview
- **Config Layer**: Pydantic models for type-safe configuration
- **Core Layer**: HTML parsing and Markdown conversion engines
- **Crawler Layer**: HTTrack wrapper for website mirroring
- **API Layer**: High-level interface for users
- **CLI Layer**: Rich command-line interface

---

## [3.1.1] - 2025-01-27

### 🧪 Test Infrastructure Improvements

This patch release focuses on fixing critical test reliability issues and enhancing the test infrastructure for better maintainability.

#### ✨ Added
- **New Refactored Large File Tests**: 
  - `test_large_file_refactored.py` - Complete rewrite of large file handling tests
  - Better separation of concerns with focused test methods
  - Platform-specific timeout handling (Unix signals vs Windows threading)
  - Progress indicators for large file creation to prevent apparent hangs
  - Comprehensive smoke test to verify m1f functionality before running complex tests

- **Enhanced Test Configuration**:
  - `pytest-timeout` plugin integration for test execution timeouts
  - Default 300-second timeout for all tests in pytest.ini
  - Custom timeout markers for different test categories
  - Better test isolation and cleanup mechanisms

- **Improved Test Utilities**:
  - Safe file size calculation using proper byte handling
  - Iteration limits to prevent infinite loops in test file generation
  - Enhanced mock input handling for various prompt types
  - Better error reporting and debugging output during test failures

#### 🔧 Changed
- **FIXED PATH RESOLUTION ISSUES**: 
  - Tests now use absolute paths instead of relative paths to prevent file not found errors
  - Proper working directory handling for m1f command execution
  - Fixed argument name mapping (`--target-encoding` → `--convert-to-charset`)

- **IMPROVED TEST RELIABILITY**:
  - Added timeout protection to prevent indefinite test hangs
  - Fixed infinite loop in `_create_large_test_file` method through proper byte counting
  - Enhanced SystemExit handling for async m1f execution
  - Better cleanup of temporary files and directories

- **MODERNIZED TEST ARCHITECTURE**:
  - Split large monolithic test into focused test methods
  - Added factory methods for test file creation
  - Improved error handling and debugging capabilities
  - Better test data management with structured content patterns

#### 🐛 Fixed
- **Critical Bug**: Fixed infinite loop in large file test creation that was caused by incorrect byte vs character size calculations
- **Path Resolution**: Fixed "Path not found" warnings by using absolute paths in test input files
- **Argument Compatibility**: Fixed incompatible command line arguments for the new m1f version
- **Timeout Issues**: Added proper timeout handling to prevent tests from hanging indefinitely
- **Mock Input Handling**: Enhanced input mocking to handle various prompt scenarios

#### ⚡ Performance Improvements
- **Faster Test Execution**: Eliminated redundant file operations and improved test data generation
- **Better Resource Management**: Proper cleanup of temporary files and directories
- **Optimized File Creation**: More efficient algorithm for generating test files of specific sizes

#### 🏗️ Test Infrastructure Enhancements
- **Cross-Platform Compatibility**: Different timeout mechanisms for Unix vs Windows systems
- **Better Test Isolation**: Each test method properly cleans up after itself
- **Enhanced Debugging**: Comprehensive logging and progress reporting during test execution
- **Modular Test Design**: Reusable components for test file creation and m1f execution

#### 📦 Dependencies
- **Added**: `pytest-timeout==2.4.0` for reliable test execution timeouts
- **Updated**: pytest.ini configuration with timeout markers and settings

#### 🔄 Migration Notes
- All existing tests continue to work without modification
- New refactored tests provide better coverage of large file scenarios
- Enhanced test reliability reduces flaky test failures
- Improved debugging output helps identify test issues faster

---

## [3.1.0] - 2025-01-27

### 🧪 Complete Test Suite Modernization

This release modernizes the entire test suite to use Python 3.10+ features and best practices, matching the architectural improvements made to the m1f and s1f tools.

#### ✨ Added
- **Modern Test Structure**:
  - Global `conftest.py` with shared fixtures and configuration
  - `base_test.py` with reusable test utilities and base classes
  - Tool-specific conftest files for m1f and s1f
  - Comprehensive test documentation in `tests/README.md`

- **New Test Modules**:
  - `test_m1f_basic.py` - Basic functionality tests
  - `test_m1f_advanced.py` - Advanced features (archives, filtering, extensions)
  - `test_m1f_encoding.py` - Comprehensive encoding tests
  - `test_m1f_edge_cases.py` - Edge cases and special scenarios
  - `test_m1f_file_hash.py` - Filename mtime hash functionality
  - `test_m1f_integration.py` - Integration and CLI tests
  - `test_s1f_basic.py` - Basic s1f functionality
  - `test_s1f_encoding.py` - s1f encoding tests
  - `test_s1f_async.py` - Async functionality tests

- **Modern Testing Features**:
  - Python 3.10+ type hints with union operator (`|`)
  - Async test support with `pytest.mark.asyncio`
  - Parametrized tests for better coverage
  - Factory fixtures for test data creation
  - Log capture fixture for testing output
  - Platform-specific fixtures (Windows/Unix)

#### 🔧 Changed
- **ELIMINATED TEST DUPLICATION**: Reduced from 6,569 lines of duplicated tests to ~4,500 lines of clean, modular tests
- **MODERN PYTHON FEATURES**: 
  - Type hints throughout all test code
  - `from __future__ import annotations` for better type support
  - Modern pathlib usage instead of os.path
  - Context managers for resource handling

- **IMPROVED TEST ORGANIZATION**:
  - Tests split by functionality instead of one monolithic file
  - Clear test markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`, `@pytest.mark.encoding`
  - Reusable fixtures instead of repeated setup code
  - Base test classes for common functionality

- **ENHANCED FIXTURES**:
  - `temp_dir` - Automatic temporary directory creation and cleanup
  - `create_test_file` - Factory for creating test files
  - `create_test_directory_structure` - Create complex directory structures from dictionaries
  - `capture_logs` - Capture and examine log output
  - `run_m1f`/`run_s1f` - Run tools with proper cleanup
  - `m1f_cli_runner`/`s1f_cli_runner` - Test CLI as subprocess

#### 📊 Test Coverage Improvements
- **Better Edge Case Coverage**: Unicode handling, symlinks, special filenames, circular references
- **Async Testing**: Comprehensive tests for s1f's async functionality
- **Error Handling**: Tests for various error scenarios and graceful degradation
- **Performance Tests**: Tests for handling many files and large files
- **Integration Tests**: End-to-end testing of complex scenarios

#### 🏗️ Test Architecture
- **Base Test Classes**: `BaseToolTest`, `BaseM1FTest`, `BaseS1FTest` with common utilities
- **Fixture Hierarchy**: Global → Tool-specific → Test-specific fixtures
- **Clean Test Isolation**: Each test is independent with proper setup/teardown
- **Modern pytest Configuration**: Updated pytest.ini with markers and coverage settings

#### 🔄 Migration from Old Tests
- **100% Feature Parity**: All test scenarios from old suite are covered
- **No Breaking Changes**: Tests verify backward compatibility
- **Improved Diagnostics**: Better error messages and test output
- **Faster Execution**: Eliminated redundant test runs

---

## [3.0.0] - 2025-05-23

### 🚀 Complete Architectural Modernization of s1f

This major release represents a complete ground-up refactoring of `s1f.py` following modern Python best practices and architectural patterns, similar to the m1f refactoring in v2.1.0.

#### ✨ Added
- **Modular Package Structure**: Complete transformation from monolithic 1,367-line script to organized package:
  - `s1f/__init__.py` - Package initialization and public API
  - `s1f/exceptions.py` - Custom exception hierarchy with specific error types
  - `s1f/models.py` - Data models using dataclasses for type safety
  - `s1f/config.py` - Configuration management with validation
  - `s1f/logging.py` - Structured logging with color support and async cleanup
  - `s1f/utils.py` - Utility functions for common operations
  - `s1f/parsers.py` - Abstract parser framework with format-specific implementations
  - `s1f/writers.py` - Async file writing with concurrent operations
  - `s1f/core.py` - Main orchestration logic
  - `s1f/cli.py` - Modern command-line interface
  - `s1f/__main__.py` - Module execution support

- **Modern Python Features**:
  - Type hints throughout (Python 3.10+ style with union operator)
  - Dataclasses for configuration and data models
  - Async/await for I/O operations with fallback support
  - Abstract base classes with proper inheritance
  - Context managers for resource management
  - Dependency injection pattern

- **Enhanced Parser Architecture**:
  - `SeparatorParser` abstract base class
  - Dedicated parsers for each format (PYMK1F, MachineReadable, Markdown, Detailed, Standard)
  - `CombinedFileParser` coordinator with automatic format detection
  - Proper content extraction with format-specific handling

- **Advanced File Writing**:
  - Async file operations using `aiofiles` (with sync fallback)
  - Concurrent file writing for improved performance
  - Smart encoding detection and handling
  - Checksum verification with line ending normalization
  - Timestamp preservation with timezone support

#### 🔧 Changed
- **COMPLETE ARCHITECTURE OVERHAUL**: 
  - Transformed monolithic 1,367-line script into modular package
  - Applied SOLID principles throughout the codebase
  - Implemented proper separation of concerns
  - Clean interfaces between modules with dependency injection

- **MODERN COMMAND-LINE INTERFACE**:
  - Supports both legacy (`--input-file`, `--destination-directory`) and modern (positional) argument styles
  - Backward compatibility maintained for existing scripts and tests
  - Enhanced help formatting with optional color support
  - Better error messages and validation

- **ADVANCED ERROR HANDLING**:
  - Custom exception hierarchy (`S1FError`, `FileParsingError`, `FileWriteError`, etc.)
  - Specific exit codes for different error types
  - Graceful fallbacks for missing optional dependencies
  - Better error context and debugging information

- **IMPROVED LOGGING SYSTEM**:
  - Structured logging with configurable levels
  - Color support with graceful fallback
  - Async cleanup for proper resource management
  - Better debugging output with execution summaries

#### ⚡ Performance Improvements
- **Async I/O Operations**: Concurrent file writing when `aiofiles` is available
- **Memory Efficiency**: Streaming content processing for large files
- **Reduced Overhead**: Eliminated redundant operations and optimized data flow
- **Smart Caching**: Reduced file system operations through better data management

#### 🏗️ Architecture Improvements
- **Dependency Injection**: Clean separation between configuration, logging, and business logic
- **Factory Pattern**: Automatic parser selection based on content analysis
- **Strategy Pattern**: Format-specific parsing strategies with common interface
- **Observer Pattern**: Structured logging and progress reporting
- **Single Responsibility**: Each module has a clear, focused purpose

#### 📊 Code Quality Metrics
- **Modularity**: From 1 monolithic file to 11 focused modules
- **Type Safety**: 100% type hint coverage for better IDE support
- **Test Coverage**: All existing tests pass without modification
- **Maintainability**: Significantly improved through modular design
- **Documentation**: Comprehensive docstrings and inline comments

#### 🔄 Migration Notes
- **100% Backward Compatibility**: All existing functionality preserved
- **Command-Line Interface**: Supports both old and new argument styles
- **Test Suite**: All existing tests pass without modification
- **Drop-in Replacement**: Existing scripts continue to work unchanged

#### 🎯 Benefits for Developers
- **Modern Python**: Leverages Python 3.10+ features and best practices
- **Better IDE Support**: Full type hints enable better code completion and error detection
- **Easier Testing**: Modular design enables focused unit testing
- **Faster Development**: Clear interfaces and separation of concerns
- **Better Debugging**: Structured logging and error handling

#### 🔌 Optional Dependencies
- `aiofiles`: For async file operations (graceful fallback to sync if not available)
- `colorama`: For colored output (graceful fallback to plain text)

---

### Technical Implementation Details

#### Parser Framework
- Abstract `SeparatorParser` base class with template method pattern
- Format-specific parsers: `PYMK1FParser`, `MachineReadableParser`, `MarkdownParser`, `DetailedParser`, `StandardParser`
- Automatic format detection and content extraction
- Robust error handling with detailed logging

#### Async Architecture
- Modern async/await patterns throughout
- Concurrent file writing for performance
- Graceful fallback to synchronous operations
- Proper resource cleanup with context managers

#### Data Models
- `FileMetadata`: Type-safe metadata representation
- `ExtractedFile`: Container for file data and metadata
- `ExtractionResult`: Summary statistics and metrics
- `SeparatorMatch`: Parser result representation

#### Error Handling
- Hierarchical exception system with specific error types
- Proper exit codes for different failure modes
- Detailed error context for debugging
- Graceful handling of edge cases

---

*This modernization brings s1f into alignment with contemporary Python development practices while maintaining complete backward compatibility and significantly improving maintainability, performance, and developer experience.*

## [2.1.0] - 2025-05-23

### 🎯 Major Refactoring and Code Quality Improvements

This release focuses on significant code quality improvements, performance optimizations, and maintainability enhancements while preserving all existing functionality.

#### ✨ Added
- New modular separator generation functions for better code organization
- Helper functions for path extraction and processing
- Unified path list writing functionality
- Better error handling with graceful fallbacks
- Enhanced encoding name normalization

#### 🔧 Changed
- **BREAKING DOWN MONOLITHIC FUNCTIONS**: Split massive 236-line `get_file_separator()` into focused, single-purpose functions:
  - `_gather_file_metadata()` - Extract common file metadata
  - `_create_standard_separator()` - Generate Standard style separators
  - `_create_detailed_separator()` - Generate Detailed style separators  
  - `_create_markdown_separator()` - Generate Markdown style separators
  - `_create_machine_readable_separator()` - Generate MachineReadable style separators
  - `_normalize_encoding_name()` - Consistent encoding name handling

- **CONSOLIDATED DUPLICATE CODE**: Unified `_write_file_paths_list()` and `_write_directory_paths_list()` into:
  - `_extract_paths_from_files()` - Common path extraction logic
  - `_write_paths_list()` - Generic path list writer with type parameter
  - Maintained backward compatibility with wrapper functions

- **ELIMINATED REDUNDANT FILE OPERATIONS**: 
  - Modified `get_file_separator()` to accept pre-read file content
  - Updated `_calculate_file_checksum()` to work on content strings instead of file paths
  - Reduced file I/O operations significantly for better performance

- **SIMPLIFIED ARGUMENT PARSER**: Streamlined `CustomArgumentParser` from 200+ lines to clean, maintainable code:
  - Removed complex formatting logic
  - Simplified error messages with optional color support
  - Better user experience with clearer error output

- **STREAMLINED ARGUMENT PROCESSING**: 
  - Created `normalize_extensions()` helper function
  - Simplified extension validation logic
  - Used safer `getattr()` calls for attribute access
  - Reduced code duplication in argument handling

#### 🗑️ Removed
- Overly complex argument parser formatting logic (200+ lines)
- Redundant debug logging statements
- Unused commented-out argument parsing code
- Redundant suppressed arguments
- Dead code and unnecessary complexity

#### 🐛 Fixed
- Fixed problematic walrus operator usage that caused syntax errors
- Improved error handling with proper exception management
- Better handling of missing attributes with safe `getattr()` usage
- Fixed potential issues with argument validation

#### ⚡ Performance Improvements
- **Reduced I/O Operations**: Files now read once instead of multiple times for checksums
- **Memory Efficiency**: Better data structures and improved data flow
- **CPU Efficiency**: Eliminated redundant computations and file operations
- **Startup Time**: Removed complex initialization logic

#### 🏗️ Architecture Improvements
- **Better Separation of Concerns**: Clear boundaries between metadata gathering, formatting, and file operations
- **Enhanced Maintainability**: Smaller, focused functions following Single Responsibility Principle
- **Improved Testability**: Isolated concerns make unit testing much easier
- **Cleaner Interfaces**: Better function signatures and parameter passing

#### 📊 Code Metrics
- **Lines of Code**: Reduced from 3,830 to 3,577 lines (-253 lines, -6.6%)
- **Function Complexity**: Significantly reduced with smaller, focused functions
- **Code Duplication**: Eliminated redundant patterns and consolidated similar logic
- **Maintainability Index**: Substantially improved through modular design

#### 🔄 Migration Notes
- All existing functionality preserved - no breaking changes to user-facing features
- Internal API changes are transparent to end users
- Command-line interface remains exactly the same
- All configuration options and features work as before

#### 🎯 Benefits for Developers
- **Easier Debugging**: Smaller functions with clear, single responsibilities
- **Better Code Navigation**: Self-documenting function names and logical organization
- **Reduced Risk**: Modular design minimizes impact of changes
- **Faster Development**: Cleaner architecture enables quicker feature additions

---

### Technical Details

#### Refactored Functions
- `get_file_separator()`: Split into 5 focused functions
- `_write_file_paths_list()` & `_write_directory_paths_list()`: Unified into generic `_write_paths_list()`
- `CustomArgumentParser`: Simplified from complex formatter to clean error handler
- `_calculate_file_checksum()`: Optimized to work on content strings

#### Performance Optimizations
- Eliminated multiple file reads for checksum calculation
- Reduced memory allocations through better data flow
- Optimized string operations and path handling
- Streamlined argument processing pipeline

#### Code Quality Improvements
- Applied DRY (Don't Repeat Yourself) principle throughout
- Enhanced function naming for better self-documentation
- Improved error handling and edge case management
- Better adherence to Python best practices and conventions

---

