# HTML Structure Analysis for CSS Selectors

<deep-thinking>
The user wants me to analyze HTML files to determine the best CSS selectors for content extraction. This requires careful analysis of HTML structure to identify:
1. Main content areas vs navigation/metadata
2. Consistent patterns across multiple files
3. Elements that should be excluded (nav, ads, etc.)
4. The most reliable selectors that will work across all pages
</deep-thinking>

You are analyzing HTML files to determine optimal CSS selectors for extracting main content while excluding navigation, ads, and other non-content elements.

## HTML Files to Analyze:

{html_content}

## Task:
Analyze the HTML structure of these files and suggest:

1. **Primary content selector** - The main CSS selector that captures the article/documentation content
2. **Alternative selectors** - Backup selectors if the primary doesn't match
3. **Ignore selectors** - Elements to exclude (navigation, headers, footers, ads, etc.)
4. **Special considerations** - Any unique patterns or edge cases noticed

Please provide your analysis in the following YAML format:

```yaml
extractor:
  content_selector: "main"  # Primary selector for content
  alternative_selectors:    # Backup selectors to try
    - "article"
    - "[role='main']"
    - ".content"
  ignore_selectors:        # Elements to exclude
    - "nav"
    - "header"
    - "footer"
    - ".sidebar"
    - ".advertisement"
  
notes: |
  Brief explanation of why these selectors were chosen and any
  special patterns noticed in the HTML structure.
```

Focus on selectors that will work reliably across all provided files.