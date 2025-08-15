# m1f - Make One File 🚀

**Because your AI assistant deserves the full story, not just fragments.**

> **📦 Quick Update:** Already using m1f? Update with: `cd m1f && git pull && source ./scripts/install.sh`

## You know that moment when...

...you're trying to get Claude, ChatGPT, or Gemini to help with your codebase,
and you realize you'd need to upload 500+ files individually? Yeah, we've been
there.

Or when you're excited about Tailwind CSS 4, but your AI is stuck in 2024 and
keeps suggesting v3 syntax? Frustrating, right?

**That's why we built m1f.**

## The Big Idea 💡

m1f isn't just file concatenation—it's intelligent context engineering for AI. Automatically handles duplicates, respects gitignore patterns, converts encodings, scans for secrets, and optimizes content for LLM consumption. One command transforms your sprawling codebase into perfectly formatted AI context.

```bash
# Before: Wrestling with context limits
❌ 1,247 React components across 47 directories
❌ Mixed TypeScript, CSS, and markdown files  
❌ Accidentally including secrets and dependencies
❌ Hit token limits, lose context mid-conversation

# After: AI-ready intelligence
✅ One optimized bundle with just the essentials
✅ Smart deduplication and encoding normalization
✅ Security scanning prevents secret leaks
✅ Perfect for Claude's 200k context window

# The magic command:
m1f-init && m1f-update
```

## Key Features

- **Content Deduplication**: Automatically detects and skips duplicate files based on SHA256 checksums.
- **Smart Auto-Loading**: Automatically respects .gitignore and .m1fignore files without configuration.
- **Async I/O**: High-performance file operations with concurrent processing.
- **Smart Filtering**: Advanced file filtering with size limits, extensions, and gitignore-style patterns.
- **Symlink Support**: Intelligent symlink handling with cycle detection.
- **Professional Security**: Integration with `detect-secrets` for sensitive data detection.
- **Preset System**: Define file-specific processing rules for different file types within the same bundle.
- **Automatic Bundling**: Create multiple bundles from a single YAML config file.
- **Real-Time Progress**: Live streaming of operations with friendly progress indicators.

## Get Started in 30 Seconds

Works on Linux, macOS, and Windows. Because we don't discriminate.

```bash
# 1. Clone it
git clone https://github.com/franz-agency/m1f.git
cd m1f

# 2. Install it
source ./scripts/install.sh    # Linux/macOS
.\scripts\install.ps1          # Windows (restart your terminal)

# 3. Use it
cd /your/amazing/project
m1f-init

# 💥 Boom! Your AI just became a project expert.
```

## Your First 2 Minutes

```bash
# 1. Get it running (30 seconds)
git clone https://github.com/franz-agency/m1f.git && cd m1f
source ./scripts/install.sh

# 2. Initialize in your project (30 seconds)  
cd /your/project && m1f-init

# 3. Create your first bundle (60 seconds)
m1f-update
# ✅ Done! Check the m1f/ directory for your AI-ready files
```

**What just happened?**
- Analyzed your project structure and created `.m1f.config.yml`
- Generated multiple bundles: complete project, docs-only, frontend-only
- Auto-ignored node_modules, .git, and other noise
- Ready to paste into Claude, ChatGPT, or any LLM

## The Complete Toolkit 🛠️

### m1f

The intelligent core bundler with advanced preset system, security scanning, and async processing. Goes far beyond simple file concatenation.

```bash
# Smart bundling with auto-ignore
m1f -s ./src -o context.txt

# Advanced preset workflows  
m1f -s . -o bundle.txt --preset wordpress.m1f-presets.yml

# Security-aware bundling
m1f -s . -o secure-bundle.txt --security-check abort

# Multiple source directories
m1f -s ./frontend -s ./backend -o full-stack.txt
```

### m1f-init

One command to rule them all. Analyzes your project, creates a `.m1f.config.yml`, and generates instant default bundles.

```bash
m1f-init  # That's it. Seriously.
```

### m1f-claude

The ultimate meta tool: Controls Claude Code headlessly and automatically includes m1f's complete documentation in every prompt. This means Claude knows ALL m1f parameters and features without you explaining anything.

```bash
m1f-claude "Create bundles for my React project, separate frontend and backend"
```

### m1f-update

Regenerates all configured bundles from your `.m1f.config.yml`. The intelligent way to keep your AI context fresh.

```bash
m1f-update              # Regenerate all bundles
m1f-update frontend     # Update specific bundle  
m1f-update --list       # Show available bundles
```

### m1f-s1f (Split One File)

When an AI generates a perfect codebase in a single file and you need real files back.

```bash
m1f-s1f -i ai-generated-magic.txt -d ./actual-files/
```

### m1f-scrape

Enterprise-grade web scraper with multiple backends (Playwright, BeautifulSoup, Selectolax), security protections, and intelligent link adjustment.

```bash
# Multi-backend scraping with restrictions
m1f-scrape https://docs.react.dev --allowed-paths /reference/ /learn/

# Bulk documentation harvesting  
m1f-scrape https://tailwindcss.com --max-pages 100 --follow-external false
```

### m1f-html2md

Turns scraped HTML into clean, readable Markdown, ready for bundling.

```bash
m1f-html2md convert ./scraped-docs -o ./markdown/
```

### m1f-research

> ⚠️ **Early Alpha**: This tool is under heavy development. Expect significant changes.

Advanced AI research workflow with 7-phase automation: query expansion, web search, URL curation, deep crawling, content analysis, bundling, and AI synthesis.

```bash
# Interactive workflow with terminal UI
m1f-research "latest React 19 features and migration guide"

# Advanced configuration  
m1f-research "Vue.js vs React 2025" --crawl-depth 2 --analysis-type comparative

# Job management
m1f-research --list-jobs
m1f-research --resume abc123
```

**Key Features:**
- **Query Expansion**: AI generates multiple search variations
- **Interactive URL Review**: Terminal UI for curating sources  
- **Deep Crawling**: Recursive page discovery with configurable depth
- **Job Management**: Track, resume, and delete research projects
- **AI Analysis**: Generates separate analysis documents with insights

### m1f-token-counter

Know before you paste. Because context limits are real.

```bash
m1f-token-counter bundle.txt
# Output: 45,231 tokens (fits in Claude's 200k context!)
```

## Command-Line Options

<details>
<summary>Click to expand the full list of `m1f` command-line options</summary>

| Option                      | Description                                                                                                                                                                                                                                                      |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `-s, --source-directory`    | Path to the directory containing files to process. Can be specified multiple times to include files from multiple directories (e.g., `-s dir1 -s dir2`)                                                                                                          |
| `-i, --input-file`          | Path to a file containing a list of files/directories to process. Can be used together with --source-directory to resolve relative paths in the input file against the source directory                                                                          |
| `-o, --output-file`         | Path for the combined output file                                                                                                                                                                                                                                |
| `-f, --force`               | Force overwrite of existing output file without prompting                                                                                                                                                                                                        |
| `-t, --add-timestamp`       | Add a timestamp (\_YYYYMMDD\_HHMMSS) to the output filename. Useful for versioning and preventing accidental overwrite of previous output files                                                                                                                   |
| `--filename-mtime-hash`     | Append a hash of file modification timestamps to the filename. The hash is created using all filenames and their modification dates, enabling caching mechanisms. Hash only changes when files are added/removed or their content changes                        |
| `--include-extensions`      | Space-separated list of file extensions to include (e.g., `--include-extensions .py .js .html` will only process files with these extensions)                                                                                                                    |
| `--exclude-extensions`      | Space-separated list of file extensions to exclude (e.g., `--exclude-extensions .log .tmp .bak` will skip these file types)                                                                                                                                      |
| `--includes`                | Space-separated list of gitignore-style patterns to include (e.g., `--includes "*.py" "src/**" "!test.py"`). When combined with `--include-extensions`, files must match both criteria                                                                           |
| `--docs-only`               | Include only documentation files (62 extensions including .md, .txt, .rst, .org, .tex, .info, etc.). Overrides include-extensions.                                                                                                                               |
| `--max-file-size`           | Skip files larger than the specified size (e.g., `--max-file-size 50KB` will exclude files over 50 kilobytes). Supports units: B, KB, MB, GB, TB. Useful for filtering out large generated files, logs, or binary data when merging text files for LLM context   |
| `--exclude-paths-file`      | Path to file containing paths or patterns to exclude. Supports both exact path lists and gitignore-style pattern formats. Can use a .gitignore file directly                                                                                                     |
| `--no-default-excludes`     | Disable default directory exclusions. By default, the following directories are excluded: vendor, node_modules, build, dist, cache, .git, .svn, .hg, \***\*pycache\*\*** (see [Default Excludes Guide](./26_default_excludes_guide.md) for complete list)        |
| `--excludes`                | Space-separated list of paths to exclude. Supports directory names, exact file paths, and gitignore-style patterns (e.g., `--excludes logs "config/settings.json" "*.log" "build/" "!important.log"`)                                                            |
| `--include-dot-paths`       | Include files and directories that start with a dot (e.g., .gitignore, .hidden/). By default, all dot files and directories are excluded.                                                                                                                        |
| `--include-binary-files`    | Attempt to include files with binary extensions                                                                                                                                                                                                                  |
| `--remove-scraped-metadata` | Remove scraped metadata (URL, timestamp) from HTML2MD files during processing. Automatically detects and removes metadata blocks at the end of markdown files created by HTML scraping tools                                                                     |
| `--separator-style`         | Style of separators between files (`Standard`, `Detailed`, `Markdown`, `MachineReadable`, `None`)                                                                                                                                                                |
| `--line-ending`             | Line ending for script-generated separators (`lf` or `crlf`)                                                                                                                                                                                                     |
| `--convert-to-charset`      | Convert all files to the specified character encoding (`utf-8` [default], `utf-16`, `utf-16-le`, `utf-16-be`, `ascii`, `latin-1`, `cp1252`). The original encoding is automatically detected and included in the metadata when using compatible separator styles |
| `--abort-on-encoding-error` | Abort processing if encoding conversion errors occur. Without this flag, characters that cannot be represented will be replaced                                                                                                                                  |
| `-v, --verbose`             | Enable verbose logging. Without this flag, only summary information is shown, and detailed file-by-file logs are written to the log file instead of the console                                                                                                  |
| `--minimal-output`          | Generate only the combined output file (no auxiliary files)                                                                                                                                                                                                      |
| `--skip-output-file`        | Execute operations but skip writing the final output file                                                                                                                                                                                                        |
| `-q, --quiet`               | Suppress all console output                                                                                                                                                                                                                                      |
| `--create-archive`          | Create a backup archive of all processed files                                                                                                                                                                                                                   |
| `--archive-type`            | Type of archive to create (`zip` or `tar.gz`)                                                                                                                                                                                                                    |
| `--security-check`          | Scan files for secrets before merging (`abort`, `skip`, `warn`)                                                                                                                                                                                                  |
| `--preset`                  | One or more preset configuration files for file-specific processing. Files are loaded in order with later files overriding earlier ones                                                                                                                          |
| `--preset-group`            | Specific preset group to use from the configuration. If not specified, all matching presets from all groups are considered                                                                                                                                       |
| `--disable-presets`         | Disable all preset processing even if preset files are loaded                                                                                                                                                                                                    |

</details>

## Configuration for Power Users

After `m1f-init`, tweak `.m1f.config.yml` to your heart's content. You can define multiple bundles, each with its own set of inclusion/exclusion patterns, and then generate them all with `m1f-update`.

```yaml
bundles:
  frontend:
    description: "React components and styles"
    patterns:
      - "src/components/**/*.{jsx,tsx}"
      - "src/styles/**/*.css"
    exclude_patterns:
      - "**/*.test.js"
    output: "m1f/frontend-brain.txt"

  api:
    description: "Backend API logic"
    patterns:
      - "api/**/*.py"
      - "!api/**/test_*.py" # Exclude tests
    output: "m1f/api-brain.txt"

  architecture:
    description: "High-level project structure"
    docs_only: true
    max_file_size: 100kb
    output: "m1f/architecture-overview.txt"
```

## Join the Revolution

We're building the future of AI-assisted development. Want to help?

- 🐛 [Report bugs](https://github.com/franz-agency/m1f/issues)
- 💡 [Suggest features](https://github.com/franz-agency/m1f/discussions)
- 🔧 [Contribute code](https://github.com/franz-agency/m1f/pulls)
- ⭐ [Star us on GitHub](https://github.com/franz-agency/m1f) (it makes us
  happy)

## Requirements

- Python 3.10+ (because we use the cool new features)
- A desire to feed your AI more context
- That's it. Really.

## License

Apache 2.0 - Use it, love it, build amazing things with it.

---

**Built with ❤️ by [franz.agency](https://franz.agency) - Where no AI has coded
before™**

_P.S. If you're reading this, you're probably the kind of developer who reads
documentation. We like you already._
