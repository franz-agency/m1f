# HTML Structure Analysis for Optimal Content Extraction

The file @m1f/selected_html_files.txt contains 5 representative HTML files from the documentation site.

## Your Task:

### 1. Deep Analysis of Each File
Read each of the 5 HTML files using the Read tool and perform a thorough structural analysis:

**Main Content Detection:**
- Identify the exact element(s) containing the primary documentation content
- Look for semantic HTML5 tags (main, article, section with specific roles)
- Check for content-specific class names (e.g., .doc-content, .markdown-body, .prose)
- Note if content is split across multiple containers

**Navigation & UI Elements to Exclude:**
- Global navigation (top nav, breadcrumbs, sidebar navigation)
- Page metadata (author info, last updated, edit buttons)
- Interactive elements (search boxes, theme toggles, language selectors)
- Social sharing buttons and feedback widgets
- Table of contents (if separate from main content)
- Footer links and copyright notices

**Dynamic Content Patterns:**
- Code syntax highlighting wrappers
- Collapsible sections or tabs
- Alert/callout boxes that should be preserved
- Embedded examples or demos

### 2. Pattern Recognition Across Files
After analyzing all files, identify:

**Consistency Check:**
- Which selectors work on ALL 5 files?
- Which selectors work on most files (note the exceptions)?
- Are there different layouts for different content types?

**Selector Robustness:**
- Prefer semantic selectors over class-based when possible
- Use combination selectors for precision (e.g., main > article)
- Identify parent containers that reliably wrap content

**Edge Cases:**
- Landing pages vs. documentation pages
- API reference vs. guides
- Pages with multiple content sections

### 3. Build Intelligent Selector Strategy

## Output:

Create a YAML configuration with carefully chosen selectors:

```yaml
extractor:
  # Primary selector - should capture main content on most pages
  content_selector: "main.documentation-content, article.markdown-body"
  
  # Fallback selectors - tried in order if primary fails
  alternative_selectors:
    - "div[role='main'] > .content"
    - "#main-content article"
    - ".docs-content > .inner"
    - "section.content-section"
    - ".page-content"  # Generic fallback
  
  # Elements to remove - be specific to avoid over-removal
  ignore_selectors:
    # Navigation
    - "nav"
    - ".navigation"
    - ".sidebar-nav"
    - ".breadcrumb"
    
    # Headers/Footers (but not article headers!)
    - "body > header"
    - "body > footer"
    - ".site-header"
    - ".site-footer"
    
    # Page metadata
    - ".page-meta"
    - ".doc-tags"
    - ".last-updated"
    - ".edit-link"
    
    # Interactive elements
    - ".search-box"
    - ".theme-toggle"
    - ".language-selector"
    
    # Promotional/External
    - ".advertisement"
    - ".cookie-notice"
    - ".newsletter-signup"
    
    # Social/Sharing
    - ".social-share"
    - ".feedback-widget"
    
    # Table of contents (if separate)
    - ".toc-sidebar"
    - "aside.toc"

# Provide detailed analysis notes
notes: |
  Selector Strategy:
  - Primary selector targets: [describe what it matches]
  - Alternative selectors cover: [explain fallback scenarios]
  
  Content Patterns Observed:
  - [Pattern 1]: [Description]
  - [Pattern 2]: [Description]
  
  Special Considerations:
  - [Any special handling needed]
  - [Warnings about edge cases]
  
  Confidence Level: [High/Medium/Low] - [Explain why]
```

**CRITICAL REQUIREMENTS:**
1. Test each selector mentally against ALL 5 files
2. Prefer specific selectors that won't capture unwanted content
3. Order alternative selectors from most specific to most generic
4. Ensure ignore_selectors are specific enough to not remove actual content
5. Document your reasoning in the notes section