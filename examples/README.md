# Documentation Scraping Examples

This directory contains practical examples demonstrating how to scrape, convert, and bundle documentation websites into AI-friendly context files using the m1f toolkit.

## 🎯 Current Example

### `scrape_claude_code_docs.py` - Claude Code Documentation Scraper

A specialized Python script that demonstrates the complete m1f workflow for creating AI-ready documentation bundles. This example showcases the irony of Claude Code needing to scrape its own documentation to know itself!

**What it does:**
1. **Scrapes** Claude Code documentation from `docs.anthropic.com`
2. **Analyzes** HTML structure using Claude AI for intelligent content extraction
3. **Converts** HTML to clean Markdown using optimized selectors
4. **Initializes** the bundle with `m1f-init`
5. **Creates** `claude-code-doc.txt` - a single context file
6. **Configures** the bundle with `m1f-claude --advanced-setup`

**Key Features:**
- Cross-platform (Linux & Windows)
- Uses Claude AI for HTML analysis
- Automatic directory reorganization
- Content verification
- Token estimation
- Complete workflow automation

**Usage:**
```bash
# Run in current directory
python scrape_claude_code_docs.py

# Specify output directory
python scrape_claude_code_docs.py /path/to/output
```

**Output:**
- `claude-code-doc.txt` - The final bundle ready for use with m1f-claude
- `claude-code-html/` - Scraped HTML files (can be deleted after bundling)
- `claude-code-markdown/` - Converted Markdown files (can be deleted after bundling)
- `html2md_extract_config.yaml` - Claude's analysis configuration

## 🚀 The Workflow Pattern

This example demonstrates a reusable pattern for documentation scraping:

```
1. Scrape → HTML files
2. Analyze → Claude AI finds optimal selectors
3. Convert → Clean Markdown extraction
4. Initialize → m1f-init prepares bundle structure
5. Bundle → Single context file creation
6. Configure → Advanced setup with project metadata
```

## 📋 Future Examples

More examples following similar principles will be added here, including:
- Git-based documentation bundling (for open source projects)
- API documentation scraping
- Multi-language documentation handling
- Incremental documentation updates
- Custom extractor examples

## 🛠️ Requirements

- Python 3.10+
- m1f toolkit installed (`pip install m1f`)
- Claude Code (for AI-powered HTML analysis)
- Internet connection (for scraping)

## 💡 Why This Approach?

The pattern demonstrated in `scrape_claude_code_docs.py` shows how to:
- Transform any documentation website into AI-friendly context
- Use AI to intelligently analyze and extract content
- Create bundles that enhance AI assistance capabilities
- Automate the entire workflow from scraping to final bundle

This approach is particularly useful when documentation isn't available via Git repositories or when you need the most up-to-date version from live websites.

---

*The irony that Claude Code needs to scrape its own documentation to know itself is not lost on us! 🤖📚*