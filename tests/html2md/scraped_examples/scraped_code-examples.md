# Code Examples Test

Testing various code blocks, syntax highlighting, and language detection for
HTML to Markdown conversion.

## Programming Languages

### Python

```
#!/usr/bin/env python3
"""
HTML to Markdown Converter
A comprehensive tool for converting HTML files to Markdown format.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import asyncio

@dataclass
class ConversionOptions:
    """Options for HTML to Markdown conversion."""
    source_dir: Path
    destination_dir: Path
    outermost_selector: Optional[str] = None
    ignore_selectors: List[str] = None
    parallel: bool = False
    max_workers: int = 4

class HTML2MDConverter:
    def __init__(self, options: ConversionOptions):
        self.options = options
        self._setup_logging()

    async def convert_file(self, file_path: Path) -> str:
        """Convert a single HTML file to Markdown."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Parse and convert
            soup = BeautifulSoup(html_content, 'html.parser')

            if self.options.outermost_selector:
                content = soup.select_one(self.options.outermost_selector)
            else:
                content = soup.body or soup

            # Remove ignored elements
            if self.options.ignore_selectors:
                for selector in self.options.ignore_selectors:
                    for element in content.select(selector):
                        element.decompose()

            return markdownify(str(content))

        except Exception as e:
            logger.error(f"Error converting {file_path}: {e}")
            raise

# Example usage
if __name__ == "__main__":
    converter = HTML2MDConverter(
        ConversionOptions(
            source_dir=Path("./html"),
            destination_dir=Path("./markdown"),
            parallel=True
        )
    )
    asyncio.run(converter.convert_all())
```

### JavaScript / TypeScript

```
// TypeScript implementation of HTML2MD converter
interface ConversionOptions {
  sourceDir: string;
  destinationDir: string;
  outermostSelector?: string;
  ignoreSelectors?: string[];
  parallel?: boolean;
  maxWorkers?: number;
}

class HTML2MDConverter {
  private options: ConversionOptions;
  private logger: Logger;

  constructor(options: ConversionOptions) {
    this.options = {
      parallel: false,
      maxWorkers: 4,
      ...options
    };
    this.logger = new Logger('HTML2MD');
  }

  async convertFile(filePath: string): Promise {
    const html = await fs.readFile(filePath, 'utf-8');
    const $ = cheerio.load(html);

    // Apply selectors
    let content = this.options.outermostSelector
      ? $(this.options.outermostSelector)
      : $('body');

    // Remove ignored elements
    this.options.ignoreSelectors?.forEach(selector => {
      content.find(selector).remove();
    });

    // Convert to markdown
    return turndownService.turndown(content.html() || '');
  }

  async *convertDirectory(): AsyncGenerator {
    const files = await this.findHTMLFiles();

    for (const file of files) {
      try {
        const markdown = await this.convertFile(file);
        yield { file, markdown, success: true };
      } catch (error) {
        yield { file, error, success: false };
      }
    }
  }
}

// Usage example
const converter = new HTML2MDConverter({
  sourceDir: './html-docs',
  destinationDir: './markdown-docs',
  outermostSelector: 'main.content',
  ignoreSelectors: ['nav', '.sidebar', 'footer'],
  parallel: true
});

// Process files
for await (const result of converter.convertDirectory()) {
  if (result.success) {
    console.log(`✓ Converted: ${result.file}`);
  } else {
    console.error(`✗ Failed: ${result.file}`, result.error);
  }
}
```

### Bash / Shell Script

```
#!/bin/bash
# HTML2MD Batch Conversion Script
# Converts all HTML files in a directory to Markdown

set -euo pipefail

# Configuration
SOURCE_DIR="${1:-./html}"
DEST_DIR="${2:-./markdown}"
PARALLEL_JOBS="${3:-4}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check dependencies
check_dependencies() {
    local deps=("python3" "pip" "parallel")

    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "Missing dependency: $dep"
            exit 1
        fi
    done
}

# Convert single file
convert_file() {
    local input_file="$1"
    local output_file="${input_file%.html}.md"
    output_file="${DEST_DIR}/${output_file#${SOURCE_DIR}/}"

    # Create output directory
    mkdir -p "$(dirname "$output_file")"

    # Run conversion
    if python3 tools/html2md.py \
        --input "$input_file" \
        --output "$output_file" \
        --quiet; then
        echo "✓ $input_file"
    else
        echo "✗ $input_file" >&2
        return 1
    fi
}

# Main execution
main() {
    log_info "Starting HTML to Markdown conversion"
    log_info "Source: $SOURCE_DIR"
    log_info "Destination: $DEST_DIR"

    check_dependencies

    # Find all HTML files
    mapfile -t html_files < <(find "$SOURCE_DIR" -name "*.html" -type f)

    if [[ ${#html_files[@]} -eq 0 ]]; then
        log_warning "No HTML files found in $SOURCE_DIR"
        exit 0
    fi

    log_info "Found ${#html_files[@]} HTML files"

    # Export function for parallel
    export -f convert_file log_info log_error
    export SOURCE_DIR DEST_DIR

    # Run conversions in parallel
    printf '%s\n' "${html_files[@]}" | \
        parallel -j "$PARALLEL_JOBS" convert_file

    log_info "Conversion complete!"
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### SQL

```
-- HTML2MD Conversion Tracking Database Schema
-- Track conversion history and statistics

-- Create database
CREATE DATABASE IF NOT EXISTS html2md_tracker;
USE html2md_tracker;

-- Conversion jobs table
CREATE TABLE conversion_jobs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    job_id VARCHAR(36) UNIQUE NOT NULL DEFAULT (UUID()),
    source_directory VARCHAR(500) NOT NULL,
    destination_directory VARCHAR(500) NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    status ENUM('running', 'completed', 'failed', 'cancelled') DEFAULT 'running',
    total_files INT DEFAULT 0,
    converted_files INT DEFAULT 0,
    failed_files INT DEFAULT 0,
    options JSON,
    INDEX idx_status (status),
    INDEX idx_started (started_at)
);

-- Individual file conversions
CREATE TABLE file_conversions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    job_id VARCHAR(36) NOT NULL,
    source_path VARCHAR(1000) NOT NULL,
    destination_path VARCHAR(1000) NOT NULL,
    file_size_bytes BIGINT,
    conversion_time_ms INT,
    status ENUM('pending', 'converting', 'completed', 'failed') DEFAULT 'pending',
    error_message TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES conversion_jobs(job_id) ON DELETE CASCADE,
    INDEX idx_job_status (job_id, status)
);

-- Conversion statistics view
CREATE VIEW conversion_statistics AS
SELECT
    DATE(started_at) as conversion_date,
    COUNT(DISTINCT j.id) as total_jobs,
    SUM(j.converted_files) as total_converted,
    SUM(j.failed_files) as total_failed,
    AVG(TIMESTAMPDIFF(SECOND, j.started_at, j.completed_at)) as avg_job_duration_seconds,
    SUM(f.file_size_bytes) / 1048576 as total_mb_processed
FROM conversion_jobs j
LEFT JOIN file_conversions f ON j.job_id = f.job_id
WHERE j.status = 'completed'
GROUP BY DATE(started_at);

-- Example queries
-- Get recent conversion jobs
SELECT
    job_id,
    source_directory,
    status,
    CONCAT(converted_files, '/', total_files) as progress,
    TIMESTAMPDIFF(MINUTE, started_at, IFNULL(completed_at, NOW())) as duration_minutes
FROM conversion_jobs
ORDER BY started_at DESC
LIMIT 10;
```

### Go

```
package main

import (
    "context"
    "fmt"
    "io/fs"
    "log"
    "os"
    "path/filepath"
    "sync"
    "time"

    "github.com/PuerkitoBio/goquery"
    "golang.org/x/sync/errgroup"
)

// ConversionOptions holds the configuration for HTML to Markdown conversion
type ConversionOptions struct {
    SourceDir        string
    DestinationDir   string
    OutermostSelector string
    IgnoreSelectors  []string
    Parallel         bool
    MaxWorkers       int
}

// HTML2MDConverter handles the conversion process
type HTML2MDConverter struct {
    options *ConversionOptions
    logger  *log.Logger
}

// NewConverter creates a new HTML2MD converter instance
func NewConverter(opts *ConversionOptions) *HTML2MDConverter {
    if opts.MaxWorkers <= 0 {
        opts.MaxWorkers = 4
    }

    return &HTML2MDConverter{
        options: opts,
        logger:  log.New(os.Stdout, "[HTML2MD] ", log.LstdFlags),
    }
}

// ConvertFile converts a single HTML file to Markdown
func (c *HTML2MDConverter) ConvertFile(ctx context.Context, filePath string) error {
    // Read HTML file
    htmlContent, err := os.ReadFile(filePath)
    if err != nil {
        return fmt.Errorf("reading file: %w", err)
    }

    // Parse HTML
    doc, err := goquery.NewDocumentFromReader(strings.NewReader(string(htmlContent)))
    if err != nil {
        return fmt.Errorf("parsing HTML: %w", err)
    }

    // Apply selectors
    var selection *goquery.Selection
    if c.options.OutermostSelector != "" {
        selection = doc.Find(c.options.OutermostSelector)
    } else {
        selection = doc.Find("body")
    }

    // Remove ignored elements
    for _, selector := range c.options.IgnoreSelectors {
        selection.Find(selector).Remove()
    }

    // Convert to Markdown
    markdown := c.htmlToMarkdown(selection)

    // Write output file
    outputPath := c.getOutputPath(filePath)
    if err := c.writeOutput(outputPath, markdown); err != nil {
        return fmt.Errorf("writing output: %w", err)
    }

    c.logger.Printf("Converted: %s → %s", filePath, outputPath)
    return nil
}

// ConvertDirectory converts all HTML files in a directory
func (c *HTML2MDConverter) ConvertDirectory(ctx context.Context) error {
    start := time.Now()

    // Find all HTML files
    var files []string
    err := filepath.WalkDir(c.options.SourceDir, func(path string, d fs.DirEntry, err error) error {
        if err != nil {
            return err
        }

        if !d.IsDir() && filepath.Ext(path) == ".html" {
            files = append(files, path)
        }
        return nil
    })

    if err != nil {
        return fmt.Errorf("walking directory: %w", err)
    }

    c.logger.Printf("Found %d HTML files", len(files))

    // Convert files
    if c.options.Parallel {
        err = c.convertParallel(ctx, files)
    } else {
        err = c.convertSequential(ctx, files)
    }

    if err != nil {
        return err
    }

    c.logger.Printf("Conversion completed in %v", time.Since(start))
    return nil
}

func (c *HTML2MDConverter) convertParallel(ctx context.Context, files []string) error {
    g, ctx := errgroup.WithContext(ctx)

    // Create a semaphore to limit concurrent workers
    sem := make(chan struct{}, c.options.MaxWorkers)

    for _, file := range files {
        file := file // capture loop variable

        g.Go(func() error {
            select {
            case <-ctx.Done():
                return ctx.Err()
            case sem <- struct{}{}:
                defer func() { <-sem }()
                return c.ConvertFile(ctx, file)
            }
        })
    }

    return g.Wait()
}

func main() {
    converter := NewConverter(&ConversionOptions{
        SourceDir:        "./html-docs",
        DestinationDir:   "./markdown-docs",
        OutermostSelector: "article.content",
        IgnoreSelectors:  []string{"nav", ".sidebar", "footer"},
        Parallel:         true,
        MaxWorkers:       8,
    })

    ctx := context.Background()
    if err := converter.ConvertDirectory(ctx); err != nil {
        log.Fatal(err)
    }
}
```

### Rust

```
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tokio::fs as async_fs;
use tokio::sync::Semaphore;
use futures::stream::{self, StreamExt};
use scraper::{Html, Selector};
use anyhow::{Context, Result};

/// Options for HTML to Markdown conversion
#[derive(Debug, Clone)]
pub struct ConversionOptions {
    pub source_dir: PathBuf,
    pub destination_dir: PathBuf,
    pub outermost_selector: Option,
    pub ignore_selectors: Vec,
    pub parallel: bool,
    pub max_workers: usize,
}

/// HTML to Markdown converter
pub struct Html2MdConverter {
    options: ConversionOptions,
}

impl Html2MdConverter {
    /// Create a new converter with the given options
    pub fn new(options: ConversionOptions) -> Self {
        Self { options }
    }

    /// Convert a single HTML file to Markdown
    pub async fn convert_file(&self, file_path: &Path) -> Result {
        // Read HTML content
        let html_content = async_fs::read_to_string(file_path)
            .await
            .context("Failed to read HTML file")?;

        // Parse HTML
        let document = Html::parse_document(&html_content);

        // Apply outermost selector
        let content = if let Some(ref selector_str) = self.options.outermost_selector {
            let selector = Selector::parse(selector_str)
                .map_err(|e| anyhow::anyhow!("Invalid selector: {:?}", e))?;

            document
                .select(&selector)
                .next()
                .map(|el| el.html())
                .unwrap_or_else(|| document.html())
        } else {
            document.html()
        };

        // Remove ignored elements
        let mut processed_html = Html::parse_document(&content);
        for ignore_selector in &self.options.ignore_selectors {
            if let Ok(selector) = Selector::parse(ignore_selector) {
                // Note: In real implementation, we'd need to remove these elements
                // This is simplified for the example
            }
        }

        // Convert to Markdown (simplified)
        Ok(self.html_to_markdown(&processed_html))
    }

    /// Convert all HTML files in the source directory
    pub async fn convert_directory(&self) -> Result<()> {
        let html_files = self.find_html_files()?;
        println!("Found {} HTML files", html_files.len());

        if self.options.parallel {
            self.convert_parallel(html_files).await
        } else {
            self.convert_sequential(html_files).await
        }
    }

    /// Convert files in parallel with limited concurrency
    async fn convert_parallel(&self, files: Vec) -> Result<()> {
        let semaphore = Arc::new(Semaphore::new(self.options.max_workers));

        let tasks = stream::iter(files)
            .map(|file| {
                let sem = semaphore.clone();
                let converter = self.clone();

                async move {
                    let _permit = sem.acquire().await?;
                    converter.convert_file(&file).await
                }
            })
            .buffer_unordered(self.options.max_workers);

        tasks
            .for_each(|result| async {
                match result {
                    Ok(markdown) => println!("✓ Converted file"),
                    Err(e) => eprintln!("✗ Error: {}", e),
                }
            })
            .await;

        Ok(())
    }

    /// Find all HTML files in the source directory
    fn find_html_files(&self) -> Result> {
        let mut files = Vec::new();

        for entry in walkdir::WalkDir::new(&self.options.source_dir)
            .into_iter()
            .filter_map(|e| e.ok())
        {
            if entry.file_type().is_file() {
                if let Some(ext) = entry.path().extension() {
                    if ext == "html" || ext == "htm" {
                        files.push(entry.path().to_path_buf());
                    }
                }
            }
        }

        Ok(files)
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    let options = ConversionOptions {
        source_dir: PathBuf::from("./html-docs"),
        destination_dir: PathBuf::from("./markdown-docs"),
        outermost_selector: Some("article.content".to_string()),
        ignore_selectors: vec![
            "nav".to_string(),
            ".sidebar".to_string(),
            "footer".to_string(),
        ],
        parallel: true,
        max_workers: 8,
    };

    let converter = Html2MdConverter::new(options);
    converter.convert_directory().await?;

    Ok(())
}
```

## Inline Code Tests

### Mixed Content with Inline Code

When working with HTML to Markdown conversion, you might encounter various
inline code snippets like `document.querySelector('.content')` or shell commands
like `python tools/html2md.py --help`. The converter should preserve these
inline code blocks.

Here's a paragraph with multiple inline code elements: The `HTML2MDConverter`
class uses `BeautifulSoup` for parsing and `markdownify` for conversion. You can
configure it with options like `--outermost-selector` and `--ignore-selectors`.

#### File Paths and Commands

- Source file: `/home/user/documents/index.html`
- Output file: `./output/index.md`
- Config file: `~/.config/html2md/settings.yaml`
- Command: `npm install -g html-to-markdown`

#### Variable Names and Functions

The function `convertFile()` takes a parameter `filePath` and returns a
`Promise<string>`. Inside, it calls `fs.readFile()` and processes the content
with `cheerio.load()`.

## Special Cases

### Code with Special Characters

```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Special &amp; Characters &lt; Test &gt;</title>
    <style>
        /* CSS with special characters */
        .class[data-attr*="value"] {
            content: "Quote with \"escaped\" quotes";
            background: url('image.png');
        }
    </style>
</head>
<body>
    <h1>HTML Entities: &copy; &trade; &reg; &nbsp;</h1>
    <p>Math: 5 &lt; 10 &amp;&amp; 10 &gt; 5</p>
    <pre><code>
    // JavaScript with special characters
    const regex = /[a-z]+@[a-z]+\.[a-z]+/;
    const str = 'String with "quotes" and \'apostrophes\'';
    const obj = { "key": "value with <brackets>" };
    </code></pre>
</body>
</html>
```

### Nested Code Blocks

````
# Markdown with Code Examples

Here's how to include code in Markdown:

```python
def example():
    """This is a Python function."""
    return "Hello, World!"
````

And here's inline code: `variable = value`

## Nested Example

```html
<pre><code class="language-javascript">
// This is JavaScript inside HTML
const x = 42;
</code></pre>
```

```
### Code Without Language Specification

```

This is a code block without any language specification. It should still be
converted to a code block in Markdown. The converter should handle this
gracefully.

    Indented lines should be preserved.
    Special characters: < > & " ' should be handled correctly.

```
### Mixed Language Examples

#### Frontend (React)

```

import React, { useState, useEffect } from 'react'; import {
convertHtmlToMarkdown } from './converter';

const ConverterComponent = () => { const [html, setHtml] = useState(''); const
[markdown, setMarkdown] = useState(''); const [loading, setLoading] =
useState(false);

const handleConvert = async () => { setLoading(true); try { const result = await
convertHtmlToMarkdown(html, { outermostSelector: 'article', ignoreSelectors:
['nav', '.ads'] }); setMarkdown(result); } catch (error) {
console.error('Conversion failed:', error); } finally { setLoading(false); } };

return ( <div className="converter"> <textarea value={html} onChange={(e) =>
setHtml(e.target.value)} placeholder="Paste HTML here..." />
<button onClick={handleConvert} disabled={loading}> {loading ? 'Converting...' :
'Convert to Markdown'} </button> <pre>{markdown}</pre> </div> ); };

```

#### Backend (Node.js)

```

const express = require('express'); const { JSDOM } = require('jsdom'); const
TurndownService = require('turndown');

const app = express(); app.use(express.json());

// Initialize Turndown service const turndownService = new TurndownService({
headingStyle: 'atx', codeBlockStyle: 'fenced' });

// API endpoint for HTML to Markdown conversion app.post('/api/convert', async
(req, res) => { try { const { html, options = {} } = req.body;

    // Parse HTML with JSDOM
    const dom = new JSDOM(html);
    const document = dom.window.document;

    // Apply selectors if provided
    let content = document.body;
    if (options.outermostSelector) {
      content = document.querySelector(options.outermostSelector) || content;
    }

    // Remove ignored elements
    if (options.ignoreSelectors) {
      options.ignoreSelectors.forEach(selector => {
        content.querySelectorAll(selector).forEach(el => el.remove());
      });
    }

    // Convert to Markdown
    const markdown = turndownService.turndown(content.innerHTML);

    res.json({
      success: true,
      markdown,
      stats: {
        inputLength: html.length,
        outputLength: markdown.length
      }
    });

} catch (error) { res.status(500).json({ success: false, error: error.message
}); } });

const PORT = process.env.PORT || 3000; app.listen(PORT, () => {
console.log(`HTML2MD API running on port ${PORT}`); });

```

### Configuration Files

```

# html2md.config.yaml

# Configuration for HTML to Markdown converter

conversion:

# Source and destination directories

source_dir: ./html-docs destination_dir: ./markdown-docs

# Selector options

selectors: outermost: "main.content, article.post, div.documentation" ignore: -
"nav" - "header.site-header" - "footer.site-footer" - ".advertisement" -
".social-share" - "#comments"

# File handling

files: include*extensions: [".html", ".htm", ".xhtml"] exclude_patterns: -
"**/node_modules/**" - "**/dist/**" - "\**/\_.min.html" max_file_size_mb: 10

# Processing options

processing: parallel: true max_workers: 4 encoding: utf-8 preserve_whitespace:
false

# Output options

output: add_frontmatter: true frontmatter_fields: layout: "post" generator:
"html2md" heading_offset: 0 code_block_style: "fenced"

# Logging configuration

logging: level: "info" file: "./logs/html2md.log" format: "json"

```
### JSON Configuration

```

{ "name": "html2md-converter", "version": "2.0.0", "description": "Convert HTML
files to Markdown with advanced options", "main": "index.js", "scripts": {
"start": "node index.js", "convert": "node cli.js --config html2md.config.json",
"test": "jest --coverage", "lint": "eslint src/\*_/_.js" }, "dependencies": {
"cheerio": "^1.0.0-rc.12", "turndown": "^7.1.2", "glob": "^8.0.3", "yargs":
"^17.6.2", "p-limit": "^4.0.0" }, "devDependencies": { "jest": "^29.3.1",
"eslint": "^8.30.0", "@types/node": "^18.11.18" }, "config": { "defaultOptions":
{ "parallel": true, "maxWorkers": 4, "encoding": "utf-8" } } }

```

## Edge Case Code Blocks

### Empty Code Block

### Code with Only Whitespace

```

```
### Very Long Single Line

```

const veryLongLine = "This is a very long line of code that should not wrap in
the code block but might cause horizontal scrolling in the rendered output.
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua.";

```
### Unicode in Code

```

# Unicode test

emoji = "🚀 🎨 🔧 ✨" chinese = "你好世界" arabic = "مرحبا بالعالم" math =
"∑(i=1 to n) = n(n+1)/2"

def print_unicode(): print(f"Emoji: {emoji}") print(f"Chinese: {chinese}")
print(f"Arabic: {arabic}") print(f"Math: {math}") print("Special: α β γ δ ε ζ η
θ")

```




---

*Scraped from: http://localhost:8080/page/code-examples*

*Scraped at: 2025-05-23 11:55:26*

*Source URL: http://localhost:8080/page/code-examples*
```
