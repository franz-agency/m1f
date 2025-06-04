# m1f - Make One File 🚀

**Feed your AI the whole story.** A powerful toolkit that turns messy codebases into AI-ready context bundles.

## What's This?

Ever tried explaining your entire project to Claude or ChatGPT? Yeah, that's what we thought. m1f makes it stupid simple to bundle your code, docs, and whatever else into perfectly digestible chunks for LLMs.

## The Squad

### 🎯 **m1f** - The Bundler
Combines multiple files into a single, AI-friendly mega-file. Smart enough to deduplicate content, handle any encoding, and even scan for secrets. Because nobody wants their API keys in a ChatGPT conversation.

```bash
# Bundle your entire project (but smart about it)
m1f -s ./your-project -o context.txt --preset wordpress
```

### ✂️ **s1f** - The Splitter  
Extracts files back from bundles. Perfect for when your AI assistant generates that perfect codebase and you need it back in actual files.

```bash
# Unbundle that AI-generated masterpiece
s1f -i bundle.txt -d ./extracted
```

### 🌐 **webscraper** - The Collector
Downloads entire websites for offline processing. Multiple backends for different scenarios - from simple HTML to JavaScript-heavy SPAs.

```bash
# Grab those docs
webscraper https://docs.example.com -o ./html --scraper playwright
```

### 📝 **html2md** - The Converter
Transforms HTML into clean Markdown. Analyzes structure, suggests optimal selectors, and handles even the messiest enterprise documentation.

```bash
# Make it readable
html2md convert ./html -o ./markdown --content-selector "article"
```

### 🔢 **token_counter** - The Calculator
Counts tokens before you hit those pesky context limits. Support for all major LLM encodings.

```bash
# Will it fit?
token_counter ./bundle.txt
```

## Real-World Magic

### Feed Documentation to Your AI Assistant
```bash
# Download → Convert → Bundle → Profit
webscraper https://react.dev -o ./react-html
html2md convert ./react-html -o ./react-md
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
./scripts/auto_bundle.sh complete
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

```bash
# Clone it
git clone https://github.com/franzundfriends/m1f.git
cd m1f

# Set it up
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Use it
python tools/m1f.py -s . -o bundle.txt
```

## Pro Tips

- Start small: Test with a few files before going wild
- Use presets: They're there for a reason
- Check token counts: Your LLM will thank you
- Read the docs: Seriously, they're pretty good

## Real Example: Scraping Claude's Documentation 🤖

Want to give Claude its own documentation? Here's how to scrape, process, and bundle the Anthropic docs:

### The Full Pipeline

```bash
# 1. Download Claude's documentation
webscraper https://docs.anthropic.com -o ./claude-docs-html \
  --max-pages 200 \
  --max-depth 4 \
  --request-delay 1.0

# 2. Analyze the HTML structure to find the best selectors
html2md analyze ./claude-docs-html/*.html --suggest-selectors

# 3. Convert to clean Markdown (adjust selectors based on analysis)
html2md convert ./claude-docs-html -o ./claude-docs-md \
  --content-selector "main.docs-content, article.documentation" \
  --ignore-selectors "nav" ".sidebar" ".footer" ".search-box"

# 4. Create the mega-bundle for Claude
m1f -s ./claude-docs-md -o claude-documentation.txt \
  --remove-scraped-metadata \
  --separator-style MachineReadable

# 5. Check if it fits (Claude can handle 200k tokens)
token_counter ./claude-documentation.txt
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

Now you can literally tell Claude: "Hey, here's your complete documentation" and paste the entire context. Perfect for:

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

## License

Apache 2.0 - Go wild, just don't blame us.

---

Built with ❤️ by [Franz Agency](https://franz.agency) for developers who talk to robots.