# m1f v3.3.0 Release Notes

**Release Date:** 2025-06-24

We're excited to announce the release of m1f v3.3.0, a major update that brings significant enhancements to HTML-to-Markdown conversion with Claude AI integration, powerful web scraping improvements, and streamlined project initialization workflows.

## 🎯 Highlights

- **Enhanced Claude AI Integration**: Revolutionary improvements to HTML2MD's AI-powered analysis with external prompts and multi-phase workflows
- **Smart Web Scraping**: Advanced deduplication, resume functionality, and subdirectory restrictions
- **Simplified Setup**: New `m1f-init` tool consolidates initialization steps
- **Better Documentation**: Major README overhaul with real-world examples

## 📚 Documentation Improvements

### README.md Enhancements
- Clear explanation of what m1f is (Make One File)
- Added Tailwind CSS 4.0 example demonstrating real-world usage
- Comprehensive feature list emphasizing dynamic/auto-updating capabilities
- New "Beyond AI" section showing alternative uses (backups, bundling, encoding conversion)
- Bundle location and Claude reference syntax explanation
- Security note about detect-secrets integration

### HTML2MD Documentation Updates
- `--analyze-files` parameter documentation
- Project description prompt feature
- Subprocess handling improvements
- Updated examples with new features

## 🤖 HTML2MD Claude AI Integration Enhancements

### External Prompt System
All AI prompts are now externalized for better maintainability:
- `select_files_from_project.md`: Strategic selection of representative HTML files
- `analyze_selected_files.md`: Task-based analysis workflow
- `convert_html_to_md.md`: Enhanced HTML to Markdown conversion
- Easy customization without code changes

### Task-Based Analysis Workflow
Multi-phase analysis for superior accuracy:
- **Phase 1**: Individual file analysis with detailed findings
- **Phase 2**: Synthesis to create optimal configuration
- Deep structural analysis identifies content boundaries, navigation, and special content
- Transparent process with temporary analysis files

### Improved Integration
- Write tool permissions for analysis file creation
- `--add-dir` parameter for clean directory access
- Subprocess reliability improvements with 5-minute timeouts
- `--analyze-files` parameter (1-20 files, default: 5)

## 🕷️ WebScraper Enhancements

### Content Deduplication (Default: Enabled)
Memory-efficient duplicate prevention:
- Database-backed system using SQLite
- SHA-256 checksums of normalized plain text
- Three-layer deduplication:
  1. Canonical URL checking (`--ignore-canonical` to disable)
  2. Content deduplication (`--ignore-duplicates` to disable)
  3. GET parameter normalization (`--ignore-get-params` to enable)

### Resume Functionality
Interrupt and resume scraping sessions:
- SQLite database tracks progress
- Real-time URL processing display
- Graceful Ctrl+C handling
- Smart resume strategy analyzes scraped pages

### Subdirectory Restriction
Automatic path-based crawling limits:
- URLs like `https://example.com/docs` only scrape under `/docs`
- Prevents scope creep
- Works with all scraper backends

### URL Normalization
New `--ignore-get-params` flag:
- Prevents duplicate content from query string variations
- Treats `page.html?tab=linux` and `page.html?tab=windows` as identical

## 🛠️ Tool Improvements

### New m1f-init Tool
Replaces `m1f-link` with enhanced functionality:
- Cross-platform support (Windows, Linux, macOS)
- Automatic documentation linking
- Creates complete and docs bundles with project names
- Generates auxiliary files (filelist, dirlist)
- Platform-specific next steps guidance

### m1f-claude Refactoring
- Removed `--init` and `--quick-setup` parameters
- Now focuses on `--advanced-setup` for topic-specific bundles
- Requires `m1f-init` to be run first
- Linux/macOS only

### Enhanced Features
- `--docs-only` parameter for documentation-only bundles
- Centralized documentation file extensions (62 formats)
- Project-specific bundle naming
- Auxiliary file generation for all bundles

## 🐛 Bug Fixes

### HTML2MD Claude Integration
- Fixed subprocess hanging with Claude CLI
- Corrected m1f usage with `--skip-output-file`
- Fixed file reference syntax
- Resolved indentation and undefined variable errors

### Directory Structure
- Fixed `.m1f.config.yml` nested directory configuration
- Removed accidental triple nesting
- Created proper symlinks

### WebScraper
- Fixed duplicate content logging
- Graceful skip-based handling instead of exceptions

### PowerShell Installation
- Created missing `m1f_aliases.ps1` file
- Fixed hardcoded paths
- Added file existence checks

### m1f-claude
- Fixed project name extraction regex patterns
- Resolved async/await issues
- Improved error handling

## 📦 Dependencies

- Added: `anyio==4.9.0` (async support)
- Added: `claude-code-sdk>=0.0.10` (flexible version constraint)

## 💡 Usage Examples

### Initialize a New Project
```bash
m1f-init
```

### Analyze HTML with Claude AI
```bash
m1f-html2md analyze /path/to/html --claude --analyze-files 10
```

### Scrape with Resume Support
```bash
m1f-scrape https://docs.example.com -o ./html
# Press Ctrl+C to interrupt
# Run same command to resume
```

### Create Documentation-Only Bundle
```bash
m1f -s . -o docs.txt --docs-only
```

## 🔄 Migration Notes

- `m1f-link` users should switch to `m1f-init`
- Bundle files remain in `m1f/` directory
- All existing workflows continue to work

## 🙏 Acknowledgments

Thanks to all contributors and users who provided feedback for this release. Special thanks to the Claude AI team for their excellent API that powers our HTML analysis features.

---

For detailed changes, see the [full changelog](docs/99_CHANGELOG.md).