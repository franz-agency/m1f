# Getting Started with m1f

This guide will walk you through installing m1f and creating your first bundles
using a real-world example.

> **📦 Already installed?** Update with: `cd m1f && git pull && source ./scripts/install.sh`

## Installation (3 Simple Steps)

### For Users

```bash
# Step 1: Clone the repository
git clone https://github.com/franz-agency/m1f.git

# Step 2: Navigate to the directory
cd m1f

# Step 3: Run the installer
source ./scripts/install.sh    # Linux/macOS
.\scripts\install.ps1          # Windows (restart your shell after)
```

That's it! The installer automatically:

- ✅ Checks for Python 3.10+
- ✅ Creates a virtual environment
- ✅ Installs all dependencies
- ✅ Sets up global command aliases
- ✅ Generates initial m1f bundles

### For Developers

If you want to contribute or modify m1f:

```bash
# Clone and enter directory
git clone https://github.com/franz-agency/m1f.git
cd m1f

# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate    # Linux/macOS
.venv\Scripts\activate       # Windows

# Install in development mode
pip install -e .
pip install -r requirements.txt
```

## Real Example: Bundling TailwindCSS Documentation

Let's walk through a complete example of bundling the TailwindCSS documentation
for use with AI assistants.

### Step 1: Get the Repository

```bash
git clone https://github.com/tailwindlabs/tailwindcss.com
cd tailwindcss.com
```

### Step 2: Initialize m1f

```bash
m1f-init
```

This command:

- Scans the entire repository
- Creates a `.m1f.config.yml` configuration file
- Generates two default bundles in the `m1f/` directory:
  - `tailwind_complete.txt` - All text files in the repository
  - `tailwind_docs.txt` - Documentation files only

### Step 3: Optional - Create Claude-Optimized Bundles

```bash
m1f-claude --setup
```

This creates additional bundles specifically optimized for Claude AI, with
proper formatting and structure.

### Using Your Bundles

Now you can:

1. **In Claude Desktop**: Reference files with `@m1f/tailwind_complete.txt`
2. **Copy & Paste**: Open the bundle file and paste into any LLM
3. **Check Token Count**: Run `m1f-token-counter m1f/tailwind_docs.txt`

## Understanding m1f-init

When you run `m1f-init` in any project directory:

1. **Scans the repository** - Analyzes file types and structure
2. **Creates `.m1f.config.yml`** - A configuration file with:
   - Default bundle definitions
   - Smart file patterns based on your project
   - Sensible exclusions (node_modules, .git, etc.)
3. **Generates bundles** - Creates initial bundles in the `m1f/` directory

## Customizing Your Bundles

After initialization, you can edit `.m1f.config.yml` to create custom bundles:

```yaml
bundles:
  # Existing bundles...

  # Add your custom bundle
  api-docs:
    description: "API documentation only"
    patterns:
      - "docs/api/**/*.md"
      - "src/**/README.md"
    exclude_patterns:
      - "**/*test*"
    output: "m1f/api_documentation.txt"
```

Then regenerate bundles:

```bash
m1f-update  # Updates all bundles
# or
m1f auto-bundle api-docs  # Update specific bundle
```

## Common Workflows

### 1. Documentation Sites

```bash
# Clone documentation
git clone https://github.com/vuejs/docs vuejs-docs
cd vuejs-docs

# Initialize and create bundles
m1f-init

# Feed to your AI
#  m1f/vuejs-docs_complete.txt
#  m1f/vuejs-docs_docs.txt
```

### 2. Your Own Projects

```bash
# In your project directory
# This creates a .m1f.config.yml with default bundles
m1f-init

# Let claude check your project to create smaller bundles sorted by topics
m1f-claude --setup

# Edit .m1f.config.yml to customize
# Then update bundles after code or config changes
m1f-update
```

### 3. Web Documentation

```bash
# Scrape online docs
m1f-scrape https://docs.python.org/3/ -o python-docs-html

# Convert to markdown
m1f-html2md convert python-docs-html -o python-docs-md

# Bundle for AI
cd python-docs-md
m1f-init
```

## Next Steps

- Learn about [configuration options](./25_m1f_config_examples.md)
- Explore [preset systems](./10_m1f_presets.md) for specialized file handling
- Set up [auto-bundling](./20_auto_bundle_guide.md) with git hooks
- Read the [complete m1f documentation](./00_m1f.md)

## Tips

- **Start Simple**: Use `m1f-init` first, customize later
- **Check Token Counts**: Always verify with `m1f-token-counter`
- **Use Presets**: For WordPress, documentation sites, etc.
- **Security**: m1f automatically scans for secrets before bundling

## Getting Help

- Run `m1f --help` for command options
- Check [troubleshooting guide](./03_troubleshooting.md)
- Visit [m1f.dev](https://m1f.dev) for updates
