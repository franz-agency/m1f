# Claude Code Documentation Scraper

Creates a bundled documentation file from the Claude Code documentation website.

## What it does

1. **Scrapes** ~31 HTML pages from docs.anthropic.com/claude-code
2. **Analyzes** HTML structure using Claude AI (or uses existing config)
3. **Converts** HTML to clean Markdown with parallel processing
4. **Creates** documentation bundle using m1f-init

## Usage

**Important**: Run from the m1f project root with virtual environment activated!

### Fast mode with existing config (recommended - saves 5-8 minutes!)

#### Linux/macOS
```bash
# From m1f project root:
source .venv/bin/activate
python examples/claude_code_doc/scrape_claude_code_docs.py ~/claude-docs \
    --use-config examples/claude_code_doc/html2md_claude_code_doc.config.yml
```

#### Windows
```powershell
# From m1f project root:
.venv\Scripts\activate
python examples\claude_code_doc\scrape_claude_code_docs.py %USERPROFILE%\claude-docs `
    --use-config examples\claude_code_doc\html2md_claude_code_doc.config.yml
```

### With full logging

#### Linux/macOS (using script command)
```bash
# Capture complete output including color codes
source .venv/bin/activate
script -c "python examples/claude_code_doc/scrape_claude_code_docs.py ~/claude-doc \
    --use-config examples/claude_code_doc/html2md_claude_code_doc.config.yml" \
    ~/claude-code-doc-scrape.log
```

#### Windows (using PowerShell)
```powershell
# Capture complete output with Start-Transcript
.venv\Scripts\activate
Start-Transcript -Path "$env:USERPROFILE\claude-code-doc-scrape.log"
python examples\claude_code_doc\scrape_claude_code_docs.py $env:USERPROFILE\claude-doc `
    --use-config examples\claude_code_doc\html2md_claude_code_doc.config.yml
Stop-Transcript
```

### Basic usage (with Claude analysis - slower)

#### Linux/macOS
```bash
# Analyzes HTML structure with Claude (adds 5-8 minutes)
source .venv/bin/activate
python examples/claude_code_doc/scrape_claude_code_docs.py ~/claude-docs
```

#### Windows
```powershell
.venv\Scripts\activate
python examples\claude_code_doc\scrape_claude_code_docs.py %USERPROFILE%\claude-docs
```

### Force re-download

#### Linux/macOS
```bash
# Re-download HTML files even if they exist
source .venv/bin/activate
python examples/claude_code_doc/scrape_claude_code_docs.py ~/claude-docs --force-download
```

#### Windows
```powershell
.venv\Scripts\activate
python examples\claude_code_doc\scrape_claude_code_docs.py %USERPROFILE%\claude-docs --force-download
```

### Show help
```bash
# Works on all platforms
python examples/claude_code_doc/scrape_claude_code_docs.py --help
```

## Timing

### Fast mode (using existing config) ⚡
⏱️ **Total: ~10 minutes**
- Scraping: 8 minutes (31 pages with 15s delays)
- ~~Claude analysis: SKIPPED~~
- Conversion & bundling: <1 minute

### With existing HTML files + config ⚡⚡
⏱️ **Total: ~1-2 minutes**
- ~~Scraping: SKIPPED~~
- ~~Claude analysis: SKIPPED~~
- Conversion & bundling: <1 minute

### Full process (with Claude analysis)
⏱️ **Total: ~18 minutes**
- Scraping: 8 minutes (31 pages with 15s delays)
- Claude analysis: 5-8 minutes
- Conversion & bundling: <2 minutes

## Logging

### Linux/macOS

#### Using script command (captures everything)
```bash
# From m1f project root - captures colors and progress bars
source .venv/bin/activate
script -c "python examples/claude_code_doc/scrape_claude_code_docs.py ~/claude-doc \
    --use-config examples/claude_code_doc/html2md_claude_code_doc.config.yml" \
    ~/claude-code-doc/scrape_$(date +%Y%m%d_%H%M%S).log
```

#### Basic logging with tee
```bash
# Basic logging
source .venv/bin/activate
python examples/claude_code_doc/scrape_claude_code_docs.py ~/claude-docs \
    --use-config examples/claude_code_doc/html2md_claude_code_doc.config.yml \
    2>&1 | tee scrape_log.txt

# With timestamps (requires moreutils)
source .venv/bin/activate
python examples/claude_code_doc/scrape_claude_code_docs.py ~/claude-docs \
    --use-config examples/claude_code_doc/html2md_claude_code_doc.config.yml \
    2>&1 | ts '[%Y-%m-%d %H:%M:%S]' | tee scrape_log.txt
```

### Windows

#### Using PowerShell transcript
```powershell
# Capture all output including errors
.venv\Scripts\activate
Start-Transcript -Path "$env:USERPROFILE\claude-code-doc\scrape_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
python examples\claude_code_doc\scrape_claude_code_docs.py $env:USERPROFILE\claude-doc `
    --use-config examples\claude_code_doc\html2md_claude_code_doc.config.yml
Stop-Transcript
```

#### Basic logging with redirection
```powershell
# Basic logging with output redirection
.venv\Scripts\activate
python examples\claude_code_doc\scrape_claude_code_docs.py $env:USERPROFILE\claude-docs `
    --use-config examples\claude_code_doc\html2md_claude_code_doc.config.yml `
    2>&1 | Tee-Object -FilePath scrape_log.txt
```

## Output

The script creates:
```
<target_directory>/
├── claude-code-html/           # Downloaded HTML files
├── claude-code-markdown/       # Converted Markdown files
│   └── m1f/
│       └── *_docs.txt         # Final documentation bundle
└── html2md_claude_code_doc.config.yml  # Config (if generated by Claude)
```

### Using the bundle

#### Linux/macOS
```bash
# Create a symlink
ln -s ~/claude-code-doc/claude-code-markdown/m1f/*_docs.txt ~/claude-code-docs.txt

# Copy to another location
cp ~/claude-code-doc/claude-code-markdown/m1f/*_docs.txt /path/to/destination/

# Use with Claude
m1f-claude ~/claude-code-doc/claude-code-markdown/m1f/*_docs.txt
```

#### Windows
```powershell
# Create a symlink (requires admin privileges)
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\claude-code-docs.txt" `
    -Target "$env:USERPROFILE\claude-code-doc\claude-code-markdown\m1f\*_docs.txt"

# Or just copy the file
Copy-Item "$env:USERPROFILE\claude-code-doc\claude-code-markdown\m1f\*_docs.txt" `
    -Destination "C:\path\to\destination\"

# Use with Claude
m1f-claude "$env:USERPROFILE\claude-code-doc\claude-code-markdown\m1f\*_docs.txt"
```

## Configuration

The included `html2md_claude_code_doc.config.yml` file contains optimized selectors for Claude Code documentation:
- Extracts main content from `div.max-w-8xl.px-4.mx-auto`
- Removes navigation, sidebars, search UI, and other non-content elements
- Preserves code blocks and formatting

## Options

- `--use-config CONFIG_FILE`: Use existing config (skip Claude analysis) - **recommended**
- `--force-download`: Re-download HTML files even if they exist
- `--delay SECONDS`: Delay between requests (default: 15)
- `--parallel`: Enable parallel HTML conversion (default: enabled)

## Requirements

- Python 3.10+
- m1f toolkit installed (`pip install -e .` from m1f root)
- Activated virtual environment (`.venv`)
- Internet connection
- Claude API access (only if not using --use-config)

## Notes

- The scraping delay is set to 15 seconds to be respectful of the server
- Always run from the m1f project root directory
- Make sure the virtual environment is activated before running
- Using the provided config file saves 5-8 minutes by skipping Claude analysis
- On Windows, use PowerShell for better command support
- Windows paths use backslashes (`\`) instead of forward slashes (`/`)
