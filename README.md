# m1f - Make One File 🚀

**Feed your AI the whole story.**

## What is m1f?

m1f (Make One File) bundles your entire codebase into a single file that you can feed to Claude AI, ChatGPT, Google Gemini, or any LLM. Think of it as a context maximizer - it takes hundreds of files from your project and intelligently combines them into one mega-file that fits perfectly in an AI's context window.

## Real Example: Tailwind CSS Documentation

Here's the problem: Tailwind's documentation is constantly evolving, but most LLMs are stuck with outdated information. 

The solution? Three commands:

```bash
git clone https://github.com/tailwindlabs/tailwindcss.com
cd tailwindcss.com && m1f-init
m1f-claude --advanced-setup
```

Boom. Now Claude knows everything about the latest Tailwind CSS. The bundles are created in the `m1f/` directory - you can reference them in Claude with `@m1f/tailwind_complete.txt` or `@m1f/tailwind_docs.txt`. Your AI assistant just became an expert on bleeding-edge tech that didn't exist when it was trained. That's the power of m1f.

> **🔐 Security Note**: m1f automatically scans for secrets (API keys, passwords, tokens) using [`detect-secrets`](https://github.com/Yelp/detect-secrets) to prevent accidental exposure to LLMs. It'll warn you before bundling sensitive data!

## The Tool Suite

m1f isn't just one tool - it's a whole squad:

- **m1f** - The main bundler that creates your mega-files
- **m1f-s1f** - Splits bundles back into individual files  
- **m1f-scrape** - Downloads entire websites for offline processing
- **m1f-html2md** - Converts HTML docs to clean Markdown
- **m1f-token-counter** - Checks if your bundle fits in context windows
- **m1f-claude** - AI assistant that already knows your codebase

Want the full story? Check out `docs/` or hit up [m1f.dev](https://m1f.dev).

## Key Features of m1f

### 🎯 Dynamic & Always Fresh
- **Auto-updating bundles** - Configure once, always current
- **Dynamic paths** - Glob patterns, regex, whatever you need
- **Smart file selection** - Include/exclude by extension, size, path patterns
- **Watch mode** - Regenerate bundles on file changes
- **Git hooks** - Auto-bundle on every commit

### 🚀 Performance
- **Async I/O** - Blazing fast concurrent file processing
- **Smart deduplication** - Skip identical files automatically (SHA256)
- **Streaming architecture** - Handle massive codebases without breaking a sweat

### 🔒 Security First
- **Secret detection** - Powered by Yelp's [`detect-secrets`](https://github.com/Yelp/detect-secrets) - scans for API keys, passwords, tokens before bundling
- **Path traversal protection** - No sneaky directory escapes
- **SSRF protection** - Safe web scraping by default
- **robots.txt compliance** - Always respects crawl rules

### 🤖 AI-Optimized
- **Token counting** - Know before you paste
- **Smart separators** - Choose between human-readable or machine-readable formats
- **Metadata preservation** - Keep file paths, timestamps, encodings
- **Size filtering** - Skip those massive log files automatically

## The Squad

### 🎯 **m1f** - The Bundler

Combines multiple files into a single, AI-friendly mega-file. Smart enough to deduplicate content, handle any encoding, and even scan for secrets. Because nobody wants their API keys in a ChatGPT conversation.

```bash
# Bundle your entire project (but smart about it)
m1f -s ./your-project -o context.txt --preset presets/wordpress.m1f-presets.yml
```

### ✂️ **m1f-s1f** - The Splitter

Extracts files back from bundles. Perfect for when your AI assistant generates that perfect codebase and you need it back in actual files.

```bash
# Unbundle that AI-generated masterpiece
m1f-s1f -i bundle.txt -d ./extracted
```

### 🌐 **m1f-scrape** - The Collector

Downloads entire websites for offline processing. Multiple backends for different scenarios - from simple HTML to JavaScript-heavy SPAs.

```bash
# Scrape documentation sites for offline reference
m1f-scrape https://docs.anthropic.com/en/docs/claude-code -o ./claude-code-docs -v
```

### 📝 **m1f-html2md** - The Converter

Transforms HTML into clean Markdown. Use AI to analyze structure and suggest optimal selectors, then convert with precision.

```bash
# AI-powered analysis to find best selectors
m1f-html2md analyze ./html --claude

# Convert using the suggested selectors
m1f-html2md convert ./html -o ./markdown \
  --content-selector "main, article" \
  --ignore-selectors "nav, .sidebar"
```

### 🔢 **m1f-token-counter** - The Calculator

Counts tokens before you hit those pesky context limits. Support for all major LLM encodings.

```bash
# Will it fit?
m1f-token-counter ./bundle.txt
```

## Real-World Magic

### Feed Documentation to Your AI Assistant

```bash
# React Documentation - From Git Repository
git clone https://github.com/reactjs/react.dev
cd react.dev && m1f-init

# This creates two bundles:
# - m1f/react_complete.txt (full codebase)
# - m1f/react_docs.txt (docs only)

# Or create custom bundles
m1f -s ./src/content -o react-api-docs.txt \
  --include-extensions .md .mdx \
  --docs-only
```

### Smart WordPress Development

```bash
# Bundle your theme with intelligent filtering
m1f -s ./wp-content/themes/mytheme -o theme-context.txt \
    --preset presets/wordpress.m1f-presets.yml
```

### Auto-Bundle Your Project

```bash
# Set it and forget it
m1f-update
# Or watch for changes
./scripts/watch_and_bundle.sh
```

## Why You'll Love It

- **🧠 AI-First**: Built specifically for LLM context windows
- **⚡ Fast AF**: Async I/O, parallel processing, the works
- **🎨 Presets**: WordPress, web projects, documentation - we got you
- **🔒 Security**: Automatic secret detection (because accidents happen)
- **📦 All-in-One**: Download, convert, bundle, done

## Quick Start

### Linux/macOS (3 commands)

```bash
git clone https://github.com/franz-agency/m1f.git
cd m1f
source ./scripts/install.sh
```

### Windows (3 commands + restart)

```powershell
git clone https://github.com/franz-agency/m1f.git
cd m1f
.\scripts\install.ps1
# Restart PowerShell or run: . $PROFILE
```

That's it! ✨ The installer handles everything:

- ✅ Checks Python 3.10+
- ✅ Creates virtual environment
- ✅ Installs all dependencies
- ✅ Generates initial bundles
- ✅ Sets up global commands

Test it:

```bash
m1f --help
m1f-update
```

## Pro Tips

- Start small: Test with a few files before going wild
- Use presets: They're there for a reason
- Check token counts: Your LLM will thank you
- Read the docs: Seriously, they're pretty good

## Real Example: Scraping Claude Code Documentation 🤖

Want to give Claude its own Claude Code documentation? Here's how to scrape and bundle
the Anthropic docs:

It's completely baffling to us that Claude Code doesn't have its own documentation internally and has to look up parameters and syntax online. But now there's help: scrape the documentation, convert it to markdown files, and feed it to Claude Code!

```bash
# 1. Download Claude Code documentation (specific section only)
m1f-scrape https://docs.anthropic.com/en/docs/claude-code -o ./claude-code-html

# 2. Analyze HTML structure with AI to get optimal selectors
# Note: m1f-html2md now auto-detects Claude installations (including ~/.claude/local/claude)
m1f-html2md analyze ./claude-code-html --claude

# 3. Convert to clean Markdown using the suggested selectors
m1f-html2md convert ./claude-code-html -o ./claude-code-md \
  --content-selector "main, article" \
  --ignore-selectors "nav, .sidebar"

# 4. Create the mega-bundle for Claude
m1f -s ./claude-code-md -o claude-code-documentation.txt \
  --remove-scraped-metadata

# 5. Check if it fits (Claude can handle 200k tokens)
m1f-token-counter ./claude-code-documentation.txt
```

### The Result?

Now you can literally tell Claude: "Hey, here's your Claude Code documentation" and
paste the entire context. Perfect for:

- Building Claude-powered tools with accurate API knowledge
- Creating Claude Code integration guides
- Having Claude help debug its own API calls
- Getting Claude to write better prompts for itself (meta!)

### Pro tip: Keep It Fresh 🌿

Set up a weekly cron job to re-scrape and rebuild:

```bash
# Add to your crontab
0 0 * * 0 cd /path/to/m1f && ./scripts/scrape-claude-docs.sh
```

Where `scrape-claude-docs.sh` contains the full pipeline above.

## Beyond AI: Other Cool Uses

m1f isn't just for feeding LLMs. Here's what else you can do:

### 📦 **Backup & Versioning**
Bundle your project → timestamp it → instant versioned backups. Extract anywhere, anytime with m1f-s1f.

### 🎨 **CSS/JS Bundler**
Poor man's webpack? Bundle all your CSS and JS files into one. Perfect for simple projects that don't need the complexity of modern build tools.

### 🔄 **Universal File Converter**
Got mixed encodings? Latin-1, UTF-16, Windows-1252? m1f auto-detects and converts everything to UTF-8 (or whatever you want). One command, all files normalized.

### 🚚 **Project Migration**
Bundle on machine A → transfer one file → extract on machine B. All paths and metadata preserved. Like tar, but readable as text file.

```bash
# Example: Full project backup with timestamp
m1f -s . -o backup_$(date +%Y%m%d_%H%M%S).txt --add-timestamp

# Extract it anywhere
m1f-s1f -i backup_20250115_143022.txt -d ./restored_project
```

## License

Apache 2.0 - Go wild, just don't blame us.

---

Built with ❤️ by [Franz Agency](https://franz.agency) for developers who talk to
robots.
