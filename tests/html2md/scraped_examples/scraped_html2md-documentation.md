## Overview

HTML2MD is a robust Python tool that converts HTML content to Markdown format
with fine-grained control over the conversion process. It's designed for
transforming web content, documentation, and preparing content for Large
Language Models.

### 🎯 Precise Selection

Use CSS selectors to extract exactly the content you need

### 🚀 Fast Processing

Parallel processing for converting large websites quickly

### 🔧 Highly Configurable

Extensive options for customizing the conversion process

## Key Features

Content Selection & Filtering

- **CSS Selectors:** Extract specific content using `--outermost-selector`
- **Element Removal:** Remove unwanted elements with `--ignore-selectors`
- **Smart Filtering:** Automatically remove scripts, styles, and other
  non-content elements

Formatting Options

- **Heading Adjustment:** Modify heading levels with `--heading-offset`
- **YAML Frontmatter:** Add metadata to converted files
- **Code Block Detection:** Preserve syntax highlighting information
- **Link Conversion:** Smart handling of internal and external links

Performance & Scalability

- **Parallel Processing:** Convert multiple files simultaneously
- **Batch Operations:** Process entire directories recursively
- **Memory Efficient:** Stream processing for large files

## Quick Start

```
# Install html2md
pip install beautifulsoup4 markdownify chardet pyyaml

# Basic conversion
m1f-html2md --source-dir ./website --destination-dir ./markdown

# Extract main content only
m1f-html2md \
    --source-dir ./website \
    --destination-dir ./markdown \
    --outermost-selector "main" \
    --ignore-selectors "nav" "footer" ".ads"
```

## Installation

### Requirements

- Python 3.9 or newer
- pip package manager

### Dependencies

```
# Install all dependencies
pip install -r requirements.txt

# Or install individually
pip install beautifulsoup4  # HTML parsing
pip install markdownify     # HTML to Markdown conversion
pip install chardet         # Encoding detection
pip install pyyaml         # YAML frontmatter support
```

### Verify Installation

```
# Check if html2md is working
m1f-html2md --help

# Test with a simple conversion
echo '<h1>Test</h1><p>Hello World</p>' > test.html
m1f-html2md --source-dir . --destination-dir output
```

## Detailed Usage

### Command Line Options

| Option                 | Description                         | Default                         |
| ---------------------- | ----------------------------------- | ------------------------------- |
| `--source-dir`         | Directory containing HTML files     | Required                        |
| `--destination-dir`    | Output directory for Markdown files | Required                        |
| `--outermost-selector` | CSS selector for content extraction | None (full page)                |
| `--ignore-selectors`   | CSS selectors to remove             | None                            |
| `--remove-elements`    | HTML elements to remove             | script, style, iframe, noscript |
| `--include-extensions` | File extensions to process          | .html, .htm, .xhtml             |
| `--exclude-patterns`   | Patterns to exclude                 | None                            |
| `--heading-offset`     | Adjust heading levels               | 0                               |
| `--add-frontmatter`    | Add YAML frontmatter                | False                           |
| `--parallel`           | Enable parallel processing          | False                           |

### Usage Examples

#### Example 1: Documentation Site Conversion

```
m1f-html2md \
    --source-dir ./docs-site \
    --destination-dir ./markdown-docs \
    --outermost-selector "article.documentation" \
    --ignore-selectors "nav.sidebar" "div.comments" "footer" \
    --add-frontmatter \
    --frontmatter-fields "layout=docs" "category=api" \
    --heading-offset 1
```

#### Example 2: Blog Migration

```
m1f-html2md \
    --source-dir ./wordpress-export \
    --destination-dir ./blog-markdown \
    --outermost-selector "div.post-content" \
    --ignore-selectors ".social-share" ".author-bio" ".related-posts" \
    --add-frontmatter \
    --frontmatter-fields "layout=post" \
    --preserve-images \
    --parallel --max-workers 4
```

#### Example 3: Knowledge Base Extraction

```
m1f-html2md \
    --source-dir ./kb-site \
    --destination-dir ./kb-markdown \
    --outermost-selector "main#content" \
    --ignore-selectors ".edit-link" ".breadcrumb" ".toc" \
    --remove-elements "script" "style" "iframe" "form" \
    --strip-classes=False \
    --convert-code-blocks \
    --target-encoding utf-8
```

## Advanced Features

### CSS Selector Examples

#### Basic Selectors

- `main` - Select main element
- `.content` - Select by class
- `#article` - Select by ID
- `article.post` - Element with class

#### Complex Selectors

- `main > article` - Direct child
- `div.content p` - Descendant
- `h2 + p` - Adjacent sibling
- `p:not(.ad)` - Negation

#### Multiple Selectors

- `nav, .sidebar, footer` - Multiple elements
- `.ad, .popup, .modal` - Remove all
- `[data-noconvert]` - Attribute selector

### YAML Frontmatter

When `--add-frontmatter` is enabled, each file gets metadata:

```
---
title: Extracted Page Title
source_file: original-page.html
date_converted: 2024-01-15T14:30:00
date_modified: 2024-01-10T09:15:00
layout: post
category: documentation
custom_field: value
---

# Page Content Starts Here
```

### Character Encoding

HTML2MD handles various encodings intelligently:

1. **Auto-detection:** Automatically detects file encoding
2. **BOM handling:** Properly handles Byte Order Marks
3. **Conversion:** Convert to UTF-8 with `--target-encoding utf-8`
4. **Fallback:** Graceful handling of encoding errors

### Code Block Handling

The converter preserves code formatting and language hints:

#### HTML Input

```
<pre><code class="language-python">
def hello():
    print("Hello, World!")
</code></pre>
```

#### Markdown Output

````
```python
def hello():
    print("Hello, World!")
````

```



## Python API

HTML2MD can also be used programmatically:

```

from html2md import HTML2MDConverter

# Initialize converter

converter = HTML2MDConverter( outermost_selector="article",
ignore_selectors=["nav", ".sidebar"], add_frontmatter=True, heading_offset=1 )

# Convert a single file

markdown = converter.convert_file("input.html") with open("output.md", "w") as
f: f.write(markdown)

# Convert directory

converter.convert_directory( source_dir="./html_files",
destination_dir="./markdown_files", parallel=True, max_workers=4 )

# Custom processing

def custom_processor(html_content, file_path): # Custom preprocessing
html_content = html_content.replace("old_domain", "new_domain")

    # Convert
    markdown = converter.convert(html_content)

    # Custom postprocessing
    markdown = markdown.replace("TODO", "**TODO**")

    return markdown

converter.set_processor(custom_processor)

```
### Event Hooks

```

# Add event listeners

converter.on("file_start", lambda path: print(f"Processing: {path}"))
converter.on("file_complete", lambda path, size: print(f"Done: {path} ({size}
bytes)")) converter.on("error", lambda path, error: print(f"Error in {path}:
{error}"))

# Progress tracking

from tqdm import tqdm

progress_bar = None

def on_start(total_files): global progress_bar progress_bar =
tqdm(total=total_files, desc="Converting")

def on_file_complete(path, size): progress_bar.update(1)

def on_complete(): progress_bar.close()

converter.on("conversion_start", on_start) converter.on("file_complete",
on_file_complete) converter.on("conversion_complete", on_complete)

```

## Troubleshooting

#### Common Issues

No content extracted
Check your CSS selector with browser DevTools. The selector might be too specific.
Broken formatting
Some HTML might have inline styles. Use `--strip-styles` to remove them.
Missing images
Images are converted to Markdown syntax but not downloaded. Use `--download-images` if needed.
Encoding errors
Try specifying `--source-encoding` or use `--target-encoding utf-8`

### Debug Mode

```

# Enable debug output

m1f-html2md \
 --source-dir ./website \
 --destination-dir ./output \
 --verbose \
 --debug \
 --log-file conversion.log

```

## Performance Tips

### For Large Sites

- Use `--parallel` with appropriate `--max-workers`
- Process in batches with `--batch-size`
- Enable `--skip-existing` for incremental updates

### Memory Usage

- Use `--streaming` for very large files
- Set `--max-file-size` to skip huge files
- Process files individually with lower `--max-workers`

### Quality vs Speed

- Disable `--convert-code-blocks` for faster processing
- Use simple selectors instead of complex ones
- Skip `--add-frontmatter` if not needed






---

*Scraped from: http://localhost:8080/page/html2md-documentation*

*Scraped at: 2025-05-23 11:55:26*

*Source URL: http://localhost:8080/page/html2md-documentation*
```
