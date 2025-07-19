# Windows Test Fixes - Implementation Plan

## Test Results Summary
- **39 failed, 174 passed, 6 skipped, 4 errors**
- Main categories: File permissions, Path separators, Server connectivity, Encoding, Playwright

## Critical Issues Identified

### 1. File Permission Errors (WinError 32) - HIGH PRIORITY
**Problem**: Windows file locking during parallel processing and insufficient file handle cleanup
**Files affected**: 
- `tests/conftest.py:69-71, 108-109`
- `tools/m1f/file_processor.py:152-170`
- `tools/m1f/encoding_handler.py:91-96, 152-176`

**Root cause**: Inconsistent use of context managers and insufficient cleanup logic for Windows

### 2. Server Connectivity Failures - HIGH PRIORITY  
**Problem**: Test server startup timing and port conflicts
**Files affected**:
- `tests/html2md_server/server.py:52-58`
- `tests/test_html2md_server.py:49-58, 74-78`

**Root cause**: Fixed 2-second wait insufficient, no startup verification, port conflicts

### 3. Path Separator Issues - MEDIUM PRIORITY
**Problem**: Inconsistent path normalization between Windows and Unix
**Files affected**:
- `tools/m1f/utils.py:192-203`
- `tools/s1f/utils.py:25-29`
- `tests/m1f/test_cross_platform_paths.py:46-56`

**Root cause**: Some code paths bypass path normalization utilities

### 4. Unicode/Encoding Issues - MEDIUM PRIORITY
**Problem**: Windows charmap codec conflicts with UTF-8 content
**Files affected**:
- `tools/m1f/encoding_handler.py:85-152, 167-252`
- `tests/m1f/test_m1f_encoding.py:32-95`

**Root cause**: Windows cp1252 vs UTF-8 conflicts, optional chardet dependency

### 5. Playwright Browser Automation - LOW PRIORITY
**Problem**: Missing browser installation and headless mode issues
**Files affected**:
- `tools/scrape_tool/scrapers/playwright.py:24-34, 67-71`
- `tests/html2md/test_scrapers.py:42-47`

**Root cause**: Requires `playwright install` after pip install

## Implementation Tasks

### Task 1: Fix File Handle Cleanup (Critical)
- [ ] Audit all file operations for proper context manager usage
- [ ] Add Windows-specific cleanup logic in test fixtures
- [ ] Implement proper file handle management in encoding detection
- [ ] Fix parallel processing file locking issues

### Task 2: Improve Server Startup (Critical)
- [ ] Replace fixed delays with health check verification
- [ ] Implement dynamic port allocation
- [ ] Add proper process cleanup and zombie process prevention
- [ ] Improve server startup robustness

### Task 3: Enhance Encoding Detection (Medium)
- [ ] Make chardet a required dependency or improve fallback
- [ ] Fix Windows-1252 vs UTF-8 handling
- [ ] Improve error handling for encoding detection
- [ ] Add comprehensive encoding tests for Windows

### Task 4: Standardize Path Handling (Medium)
- [ ] Audit all path operations to use utility functions
- [ ] Fix path normalization consistency
- [ ] Improve UNC path support
- [ ] Add comprehensive cross-platform path tests

### Task 5: Configure Playwright (Low)
- [ ] Install Playwright browsers: `playwright install`
- [ ] Fix headless mode configuration for Windows
- [ ] Improve browser process cleanup
- [ ] Add proper browser dependency checks

## Success Criteria
- All 39 failed tests should pass
- No WinError 32 permission errors
- Server tests connect reliably
- Encoding issues resolved
- Playwright tests work with proper installation

## Notes
- Focus on file handle management first (affects most failures)
- Server issues block multiple test suites
- Path issues affect cross-platform compatibility
- Encoding issues are Windows-specific but critical
- Playwright can be addressed last as it's optional functionality