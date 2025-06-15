# m1f - Make One File 🚀

**Feed your AI the whole story.**

## What is m1f?

m1f (Make One File) bundles your entire codebase into a single file that you can feed to Claude AI, ChatGPT, Google Gemini, or any LLM. Think of it as a context maximizer - it takes hundreds of files from your project and intelligently combines them into one mega-file that fits perfectly in an AI's context window.

## Real Example: Tailwind CSS 4.0

Here's the problem: Tailwind 4.0 dropped in January 2025, but most LLMs are still stuck in 2024. They have no clue how the new version works. 

The solution? Three commands:

```bash
git clone https://github.com/tailwindlabs/tailwindcss
cd tailwindcss && m1f-init
m1f-claude --advanced-setup
```

Boom. Now Claude knows everything about Tailwind 4.0. Your AI assistant just became an expert on bleeding-edge tech that didn't exist when it was trained. That's the power of m1f.

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

Combines multiple files into a single, AI-friendly mega-file. Smart enough to
deduplicate content, handle any encoding, and even scan for secrets. Because
nobody wants their API keys in a ChatGPT conversation.

```bash
# Bundle your entire project (but smart about it)
m1f -s ./your-project -o context.txt --preset wordpress
```

### ✂️ **m1f-s1f** - The Splitter

Extracts files back from bundles. Perfect for when your AI assistant generates
that perfect codebase and you need it back in actual files.

```bash
# Unbundle that AI-generated masterpiece
m1f-s1f -i bundle.txt -d ./extracted
```

### 🌐 **m1f-scrape** - The Collector

Downloads entire websites for offline processing. Multiple backends for
different scenarios - from simple HTML to JavaScript-heavy SPAs.

```bash
# Grab those docs
m1f-scrape https://docs.example.com -o ./html --scraper playwright
```

### 📝 **m1f-html2md** - The Converter

Transforms HTML into clean Markdown. Analyzes structure, suggests optimal
selectors, and handles even the messiest enterprise documentation.

```bash
# Make it readable
m1f-html2md convert ./html -o ./markdown --content-selector "article"
```

### 🔢 **m1f-token-counter** - The Calculator

Counts tokens before you hit those pesky context limits. Support for all major
LLM encodings.

```bash
# Will it fit?
m1f-token-counter ./bundle.txt
```

## Real-World Magic

### Feed Documentation to Your AI Assistant

```bash
# Download → Convert → Bundle → Profit
m1f-scrape https://react.dev -o ./react-html
m1f-html2md convert ./react-html -o ./react-md
m1f -s ./react-md -o react-docs-for-claude.txt
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
git clone https://github.com/franzundfriends/m1f.git
cd m1f
source ./scripts/install.sh
```

### Windows (3 commands + restart)

```powershell
git clone https://github.com/franzundfriends/m1f.git
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

## Real Example: Scraping Claude's Documentation 🤖

Want to give Claude its own documentation? Here's how to scrape, process, and
bundle the Anthropic docs:

### The Full Pipeline

```bash
# 1. Download Claude's documentation
m1f-scrape https://docs.anthropic.com -o ./claude-docs-html \
  --max-pages 200 \
  --max-depth 4 \
  --request-delay 1.0

# 2. Analyze the HTML structure to find the best selectors
m1f-html2md analyze ./claude-docs-html/*.html --suggest-selectors

# 3. Convert to clean Markdown (adjust selectors based on analysis)
m1f-html2md convert ./claude-docs-html -o ./claude-docs-md \
  --content-selector "main.docs-content, article.documentation" \
  --ignore-selectors "nav" ".sidebar" ".footer" ".search-box"

# 4. Create the mega-bundle for Claude
m1f -s ./claude-docs-md -o claude-documentation.txt \
  --remove-scraped-metadata \
  --separator-style MachineReadable

# 5. Check if it fits (Claude can handle 200k tokens)
m1f-token-counter ./claude-documentation.txt
```

### Or Use the One-Liner Pro Move™

```bash
# Configure once
cat > claude-docs-config.yml << EOF
bundles:
  claude-docs:
    description: "Claude API Documentation"
    output: ".ai-context/claude-complete-docs.txt"
    sources:
      - path: "./claude-docs-md"
        include_extensions: [".md"]
    separator_style: "MachineReadable"
    priority: "high"
EOF

# Then auto-bundle whenever you need fresh docs
./scripts/auto_bundle.sh claude-docs
```

### The Result?

Now you can literally tell Claude: "Hey, here's your complete documentation" and
paste the entire context. Perfect for:

- Building Claude-powered tools with accurate API knowledge
- Creating Claude integration guides
- Having Claude help debug its own API calls
- Getting Claude to write better prompts for itself (meta!)

```bash
# Example usage in your prompt:
"Based on your documentation below, help me implement a streaming response handler:
[contents of claude-documentation.txt]"
```

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
Poor man's webpack? Bundle all your CSS and JS files into one. Add `--minify` if you're feeling frisky.

### 🔄 **Universal File Converter**
Got a mess of encodings? Latin-1, UTF-16, Windows-1252? m1f auto-detects and converts everything to UTF-8 (or whatever you want). One command, all files normalized.

### 🚚 **Project Migration**
Bundle on machine A → transfer one file → extract on machine B. All paths, permissions, and metadata preserved. Like tar, but smarter.

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
