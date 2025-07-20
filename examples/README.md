# m1f Examples

## scrape_claude_code_docs.py

Creates a bundled documentation file from the Claude Code documentation website.

### What it does

1. **Scrapes** ~30 HTML pages from docs.anthropic.com/claude-code
2. **Analyzes** HTML structure using Claude AI  
3. **Converts** HTML to clean Markdown
4. **Creates** documentation bundle using m1f-init

### Usage

```bash
python examples/scrape_claude_code_docs.py <target_directory>
```

Example:
```bash
python examples/scrape_claude_code_docs.py ~/claude-doc
```

### Timing

⏱️ **Total duration: ~15-20 minutes**
- Scraping: 7-8 minutes (30 pages with 15s delays)
- Claude analysis: 5-8 minutes
- Conversion & bundling: <2 minutes

### Capture output to file

To save the entire process log:

```bash
cd /path/to/m1f
script -c "python examples/scrape_claude_code_docs.py ~/claude-doc" ~/claude-code-doc-scrape.txt
```

### Output

The script creates a documentation bundle at:
```
<target_directory>/claude-code-markdown/m1f/claude-code-markdown_docs.txt
```

You can then:
- Create a symlink: `ln -s <bundle_path> ~/claude-code-docs.txt`
- Copy the file: `cp <bundle_path> <destination>`
- Use with Claude: `m1f-claude <bundle_path>`

### Requirements

- Python 3.10+
- m1f toolkit installed (`pip install m1f`)
- Internet connection