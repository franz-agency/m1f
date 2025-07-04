# Convert HTML to Clean, High-Quality Markdown

## Context:

You are converting scraped documentation HTML to clean Markdown. The HTML may
contain navigation, ads, and other non-content elements that must be excluded.

## Content Extraction Rules:

### INCLUDE:

- Main article/documentation content
- Headings within the content area
- Code blocks and inline code
- Lists (ordered and unordered)
- Tables
- Images with their alt text
- Links (convert to Markdown format)
- Blockquotes
- Important callouts/alerts within content

### EXCLUDE:

- Site navigation (top nav, sidebars, breadcrumbs)
- Headers and footers outside main content
- "Edit this page" or "Improve this doc" links
- Social sharing buttons
- Comment sections
- Related articles/suggestions
- Newsletter signup forms
- Cookie notices
- JavaScript-rendered placeholders
- Meta information (unless part of the content flow)
- Table of contents (unless embedded in content)
- Page view counters
- Advertisements

## Markdown Quality Standards:

### 1. Structure Preservation

- Maintain the original heading hierarchy
- Don't skip heading levels
- Preserve the logical flow of information

### 2. Code Formatting

````markdown
# Inline code

Use `backticks` for inline code, commands, or file names

# Code blocks

​`language code here ​`

# Shell commands

​`bash $ command here ​`
````

### 3. Special Content Types

**API Endpoints:** Format as inline code: `GET /api/v1/users`

**File Paths:** Format as inline code: `/etc/config.yaml`

**Callout Boxes:** Convert to blockquotes with type indicators:

> **Note:** Important information **Warning:** Critical warning **Tip:** Helpful
> suggestion

**Tables:** Use clean Markdown table syntax with proper alignment

### 4. Link Handling

- Convert relative links to proper Markdown: `[text](url)`
- Preserve anchor links: `[Section](#section-id)`
- Remove dead or navigation-only links

### 5. Image Handling

- Use descriptive alt text: `![Description of image](image-url)`
- If no alt text exists, describe the image content
- Skip purely decorative images

## Final Quality Checklist:

- ✓ No HTML tags remaining
- ✓ No broken Markdown syntax
- ✓ Clean, readable formatting
- ✓ Proper spacing between sections
- ✓ Consistent code block language tags
- ✓ No duplicate content
- ✓ No navigation elements
- ✓ Logical content flow preserved

{html_content}
