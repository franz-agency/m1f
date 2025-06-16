# Analyze Scraped Documentation HTML for Markdown Conversion

## Context
These HTML files were scraped from a documentation website and need to be converted to clean Markdown files. The goal is to extract only the main documentation content while removing all navigation, headers, footers, sidebars, advertisements, and other non-content elements.

## Task
Analyze the HTML structure of these representative files and determine the optimal CSS selectors for:
1. **Content extraction**: The main documentation/article content
2. **Exclusions**: Elements that should be ignored (navigation, ads, etc.)

## Expected Output
Return ONLY a YAML configuration in this exact format:

```yaml
extractor:
  content_selector: "main"  # Primary selector for documentation content
  alternative_selectors:    # Backup selectors if primary doesn't match
    - "article"
    - "[role='main']"
  ignore_selectors:        # Elements to exclude from conversion
    - "nav"
    - "header"
    - "footer"
    - ".sidebar"
    - ".ads"
```

## HTML FILES TO ANALYZE:
{html_content}