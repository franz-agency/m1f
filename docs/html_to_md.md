# html2md (HTML to Markdown Converter)

Converts HTML files to Markdown recursively with powerful content selection and
formatting options.

## Overview

The html2md tool provides a robust solution for converting HTML content to
Markdown format, with fine-grained control over the conversion process. It is
especially useful for transforming existing HTML documentation, extracting
specific content from web pages, and preparing content for use with Large
Language Models.

## Key Features

- Recursive directory scanning for batch conversion
- CSS selector support for extracting specific content
- Smart internal link handling (HTML → Markdown)
- Customizable element filtering and removal
- YAML frontmatter generation
- Heading level adjustment
- Code block language detection
- Character encoding detection and conversion
- Parallel processing for faster conversion

## Quick Start

```bash
# Basic conversion of all HTML files in a directory
python tools/html2md.py --source-dir ./website --destination-dir ./docs

# Extract only main content from HTML files
python tools/html2md.py --source-dir ./website --destination-dir ./docs \
  --outermost-selector "main.content" --ignore-selectors "nav" ".sidebar" "footer"

# Add YAML frontmatter and adjust heading levels
python tools/html2md.py --source-dir ./website --destination-dir ./docs \
  --add-frontmatter --heading-offset 1
```

## Command Line Options

| Option                  | Description                                                                  |
| ----------------------- | ---------------------------------------------------------------------------- |
| `--source-dir`          | Directory containing HTML files to process                                   |
| `--destination-dir`     | Directory where converted Markdown files will be written                     |
| `--outermost-selector`  | CSS selector to extract specific content (e.g., `main` or `article.content`) |
| `--ignore-selectors`    | CSS selectors for elements to remove (e.g., `nav` `.sidebar` `footer`)       |
| `--remove-elements`     | HTML elements to remove (default: script, style, iframe, noscript)           |
| `--include-extensions`  | File extensions to include (default: .html, .htm, .xhtml)                    |
| `--exclude-patterns`    | Patterns to exclude from processing                                          |
| `--exclude-dirs`        | Directory names to exclude from processing                                   |
| `--heading-offset`      | Number to add to heading levels (e.g., h1 → h2 if offset=1)                  |
| `--add-frontmatter`     | Add YAML frontmatter to the output Markdown                                  |
| `--frontmatter-fields`  | Custom frontmatter fields (format: key=value)                                |
| `--strip-classes`       | Strip class attributes from HTML elements (default: true)                    |
| `--add-line-breaks`     | Add line breaks between block elements (default: true)                       |
| `--convert-code-blocks` | Convert code blocks with language hints (default: true)                      |
| `--target-encoding`     | Convert all files to the specified character encoding                        |
| `--parallel`            | Enable parallel processing for faster conversion                             |
| `--max-workers`         | Maximum number of worker processes for parallel conversion                   |
| `-f, --force`           | Force overwrite of existing Markdown files                                   |
| `-v, --verbose`         | Enable verbose output                                                        |
| `-q, --quiet`           | Suppress all console output                                                  |

## Usage Examples

### Basic Conversion

```bash
# Simple conversion of all HTML files in a directory
python tools/html2md.py --source-dir ./website --destination-dir ./docs

# Convert files with verbose logging
python tools/html2md.py --source-dir ./website --destination-dir ./docs --verbose
```

### Content Selection

```bash
# Extract only the main content and ignore navigation elements
python tools/html2md.py --source-dir ./website --destination-dir ./docs \
  --outermost-selector "main" --ignore-selectors "nav" ".sidebar" "footer"

# Extract article content and remove additional elements
python tools/html2md.py --source-dir ./website --destination-dir ./docs \
  --outermost-selector "article.content" \
  --ignore-selectors ".author-bio" ".share-buttons" ".related-articles" \
  --remove-elements "script" "style" "iframe" "noscript" "div.comments"
```

### File Filtering

```bash
# Process only specific file types
python tools/html2md.py --source-dir ./website --destination-dir ./docs \
  --include-extensions .html .xhtml

# Exclude specific directories and patterns
python tools/html2md.py --source-dir ./website --destination-dir ./docs \
  --exclude-dirs "drafts" "archived" "temp" \
  --exclude-patterns "draft-" "temp-" "_private"
```

### Formatting Options

```bash
# Adjust heading levels (e.g., h1 → h2, h2 → h3)
python tools/html2md.py --source-dir ./website --destination-dir ./docs \
  --heading-offset 1

# Add YAML frontmatter with custom fields
python tools/html2md.py --source-dir ./website --destination-dir ./docs \
  --add-frontmatter --frontmatter-fields "layout=post" "category=documentation"

# Preserve class attributes and disable line breaks adjustment
python tools/html2md.py --source-dir ./website --destination-dir ./docs \
  --strip-classes=False --add-line-breaks=False
```

### Performance Optimization

```bash
# Use parallel processing for faster conversion of large sites
python tools/html2md.py --source-dir ./website --destination-dir ./docs \
  --parallel --max-workers 4

# Force overwrite of existing files
python tools/html2md.py --source-dir ./website --destination-dir ./docs \
  --force
```

## Advanced Features

### YAML Frontmatter

When using the `--add-frontmatter` option, the converter will automatically
generate YAML frontmatter for each Markdown file, including:

- Title extracted from HTML title tag or first h1 element
- Source filename
- Conversion date
- Original file modification date

Custom frontmatter fields can be added using the `--frontmatter-fields` option:

```bash
python tools/html2md.py --source-dir ./website --destination-dir ./docs \
  --add-frontmatter --frontmatter-fields "layout=post" "author=John Doe" "category=tutorial"
```

This will add the following YAML frontmatter to each converted file:

```yaml
---
title: Extracted from HTML
source_file: original.html
date_converted: 2023-06-15T14:30:21
date_modified: 2023-06-12T10:15:33
layout: post
author: John Doe
category: tutorial
---
```

### Heading Level Adjustment

The `--heading-offset` option allows you to adjust the hierarchical structure of
the document by incrementing or decrementing heading levels. This is useful
when:

- Integrating content into an existing document with its own heading hierarchy
- Making h1 headings become h2 headings for better document structure
- Ensuring proper nesting of headings for better semantics

Positive values increase heading levels (e.g., h1 → h2), while negative values
decrease them (e.g., h2 → h1).

### Code Block Language Detection

The converter can automatically detect language hints from HTML code blocks that
use language classes, such as:

```html
<pre><code class="language-python">def example():
    return "Hello, world!"
</code></pre>
```

This will be converted to a properly formatted Markdown code block with language
hint:

````markdown
```python
def example():
    return "Hello, world!"
```
````

### Character Encoding Handling

The converter provides robust character encoding detection and conversion:

1. Automatically detects the encoding of source HTML files
2. Properly handles UTF-8, UTF-16, and other encodings
3. Can convert all files to a specified encoding using `--target-encoding`
4. Handles BOM (Byte Order Mark) detection for Unicode files

## Integration with m1f

The html2md tool works well with the m1f (Make One File) tool for
comprehensive documentation handling:

1. First convert HTML files to Markdown:

   ```bash
   python tools/html2md.py --source-dir ./html-docs --destination-dir ./markdown-docs
   ```

2. Then use m1f to combine the Markdown files:
   ```bash
   python tools/m1f.py --source-directory ./markdown-docs \
     --output-file ./combined-docs.m1f.txt --separator-style Markdown
   ```

This workflow is ideal for:

- Converting documentation from HTML to Markdown format
- Consolidating documentation from multiple sources
- Preparing content for LLM context windows
- Creating searchable knowledge bases

## Performance Considerations

- For large websites with many HTML files, use the `--parallel` option
- Conversion speed depends on file size, complexity, and number of files
- The `--max-workers` option can be used to control the number of parallel
  processes
- Memory usage scales with the number of worker processes and file sizes

## Requirements and Dependencies

- Python 3.9 or newer
- Required packages:
  - beautifulsoup4: For HTML parsing
  - markdownify: For HTML to Markdown conversion
- Optional packages:
  - chardet: For encoding detection
  - pyyaml: For frontmatter generation

Install dependencies:

```bash
pip install beautifulsoup4 markdownify chardet pyyaml
```
