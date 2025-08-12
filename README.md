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

m1f transforms your sprawling codebase into AI-ready context bundles. One
command, and suddenly your entire project – thousands of files, millions of
lines – becomes a single, perfectly formatted file that any AI can digest.

```bash
# Turn this nightmare...
src/
├── components/     (247 files)
├── utils/          (89 files)
├── services/       (156 files)
└── ... (and 2000 more)

# Into this dream:
m1f/
├── project_complete.txt    ← Your entire codebase
├── project_docs.txt        ← Just the docs
└── custom_bundles/         ← Whatever you need
```

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

### 🔄 Updating an Existing Installation

**Already have m1f installed? Updating is simple:**

```bash
# Navigate to your m1f directory and update:
cd m1f
git pull && source ./scripts/install.sh    # Linux/macOS
git pull; .\scripts\install.ps1            # Windows

# That's it! The installer automatically:
# ✓ Detects your existing installation
# ✓ Migrates to the latest version
# ✓ Updates your PATH configuration
# ✓ Cleans up old files
```

**One command, zero hassle.** Your settings and configurations remain intact.

## Why This Changes Everything

### The Problem We All Face

Modern software isn't just code anymore. It's:

- 📁 Hundreds of source files across dozens of directories
- 📚 Documentation scattered everywhere
- ⚙️ Config files in every flavor (JSON, YAML, TOML, you name it)
- 🔧 Build scripts, test files, deployment configs
- 🎨 Assets, styles, templates

**You can't just "upload a project" to AI.** Until now.

### The m1f Solution

We didn't just build a file concatenator. We built an intelligent context
creator that:

#### 🧠 Thinks Like a Developer

- Respects your `.gitignore` (because `node_modules` shouldn't go to AI)
- Deduplicates files automatically (why send the same content twice?)
- Handles symlinks properly (no infinite loops here)
- Detects secrets before they leak (your AWS keys are safe)

#### 🚀 Works at Scale

- Async everything (because waiting is so 2010)
- Streaming processing (10GB repo? No problem)

#### 🔒 Security First

- Automatic secret scanning with
  [`detect-secrets`](https://github.com/Yelp/detect-secrets)
- No passwords, API keys, or tokens in your AI conversations
- Path traversal protection (hackers hate this one trick)

## Real Magic: Teaching AI New Tricks ✨

Here's where it gets really cool. Your AI has a knowledge cutoff, but your
projects don't wait. When Tailwind CSS 4 drops and Claude is still thinking v3,
here's what you do:

```bash
# 1. Grab the latest docs
git clone https://github.com/tailwindlabs/tailwindcss.com
cd tailwindcss.com

# 2. Create AI brain food
m1f-init
# Creates: m1f/tailwind_complete.txt and m1f/tailwind_docs.txt

# 3. Get fancy with topic bundles (optional but awesome)
m1f-claude --setup
# AI analyzes and creates:
# - m1f/tailwind_utilities.txt
# - m1f/tailwind_components.txt
# - m1f/tailwind_configuration.txt

# 4. Link to your project
cd ~/your-awesome-project
ln -s ~/tailwindcss.com/m1f/tailwind_docs.txt m1f/

# 5. Blow your AI's mind
# "Hey @m1f/tailwind_docs.txt, show me how to use the new v4 grid system"
# *AI proceeds to give you perfect v4 code*
```

## The Complete Toolkit 🛠️

### m1f

The core bundler. Smart, fast, and secure.

```bash
m1f -s ./src -o context.txt --preset code-review
```

### m1f-init

One command to rule them all. Analyzes your project and creates instant bundles.

```bash
m1f-init  # That's it. Seriously.
```

### m1f-claude

The ultimate meta tool: Controls Claude Code headlessly and automatically
includes m1f's complete documentation in every prompt. This means Claude knows
ALL m1f parameters and features without you explaining anything.

```bash
# Ask Claude to create custom bundles for you
m1f-claude "Create bundles for my React project, separate frontend and backend"

# Claude now operates m1f for you with full knowledge
m1f-claude "Bundle only TypeScript files modified in the last week"

# Advanced project setup with AI-organized topics
m1f-claude --setup  # Claude analyzes your project and creates topic bundles
```

Since m1f-claude feeds the complete m1f documentation to Claude automatically,
you can ask it to do anything m1f can do - it's like having an expert m1f user
as your assistant.

### m1f-s1f (Split One File)

When AI generates that perfect codebase and you need real files back.

```bash
m1f-s1f -i ai-generated-magic.txt -d ./actual-files/
```

### m1f-scrape

Because not all docs live in git repos.

```bash
m1f-scrape https://shiny-new-framework.dev -o ./docs/
```

### m1f-html2md

Turn that scraped HTML into beautiful Markdown.

```bash
m1f-html2md convert ./scraped-docs -o ./markdown/
```

### m1f-research

AI-powered research assistant that finds, scrapes, analyzes, and bundles the
best resources into comprehensive research bundles.

```bash
# Research any topic with AI guidance
m1f-research "the best MCPs for Claude Code AI 2025 and how they function"

# Custom configuration with specific analysis
m1f-research --config research.yml --template academic "machine learning transformers"
```

### m1f-token-counter

Know before you paste. Because context limits are real.

```bash
m1f-token-counter bundle.txt
# Output: 45,231 tokens (fits in Claude's 200k context!)
```

## Use Cases That'll Make You Smile 😊

### 1. Code Review Prep

```bash
# Get changed files from git and bundle them
git diff --name-only HEAD~10 | xargs m1f --input-files -o review.txt
# Or use a code review preset if you have one
m1f --preset presets/code-review.m1f-presets.yml
```

### 2. Documentation Deep Dive

```bash
m1f --docs-only -o project-knowledge.txt
# Pure documentation, no code noise
```

### 3. Architecture Overview

```bash
m1f --include "**/*.py" --include "**/README.md" \
    --max-file-size 50kb -o architecture.txt
# High-level view without implementation details
```

### 4. The "New Developer Onboarding" Special

```bash
m1f-init && m1f-claude --setup
# Generate organized bundles for different aspects of your project
# Share with new team members → instant project experts
```

## Smart Defaults Because We Get You

Out of the box, m1f:

- ✅ Ignores `node_modules/`, `vendor/`, `.git/`, and other noise
- ✅ Skips binary files (unless you really want them)
- ✅ Handles any text encoding (UTF-8, UTF-16, that weird Windows-1252 file
  from 2003)
- ✅ Respects `.gitignore` rules (that wasn't easy ;-)
- ✅ Warns about potential secrets
- ✅ Adds clear file separators

## Configuration for Power Users

After `m1f-init`, tweak `.m1f.config.yml` to your heart's content:

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

## Beyond AI: Surprise Use Cases 🎁

### Universal File Normalizer

```bash
# Got files in 17 different encodings?
m1f --normalize-to utf-8 --output clean-project.txt
m1f-s1f -i clean-project.txt -d ./clean/
# Boom. Everything is UTF-8 now.
```

### Time Capsule Creator

```bash
m1f --add-timestamps -o "backup_$(date +%Y%m%d).txt"
# Perfect snapshot of your project at this moment
```

### The "Poor Developer's Docker"

```bash
# Bundle on machine A
m1f -o myproject.txt
# Transfer one file
scp myproject.txt user@machine-b:
# Extract on machine B
m1f-s1f -i myproject.txt -d ./project/
# Entire project structure preserved!
```

## Pro Tips from the Trenches 🏆

1. **Start with `m1f-init`** - It's smarter than you think
2. **Use presets** - We've included configs for WordPress, Django, React, and
   more
3. **Chain tools** - `m1f-scrape` → `m1f-html2md` → `m1f` = Documentation power
   combo. Or use `m1f-research` for AI-guided research and analysis
4. **Set up watches** - `./scripts/watch_and_bundle.sh` for auto-updates
5. **Check token counts** - Always know what you're pasting

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
