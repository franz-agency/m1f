# Claude + m1f: Your AI-Powered Project Assistant 🤖

Ever wished you had an AI buddy who actually understands your project structure?
That's what happens when you combine Claude with m1f. This guide shows you how
to turn Claude into your personal project assistant who knows exactly how to
bundle, organize, and process your code.

## The Power of m1f v3.2 + Claude ✨

With m1f v3.2's enhanced features, Claude can help you:

- Configure comprehensive security scanning
- Set up parallel processing for faster bundling
- Create sophisticated preset configurations
- Manage content deduplication strategies
- Handle complex encoding scenarios

## Getting Started with Claude

### Step 1: Give Claude the Power

First, let's get Claude up to speed on what m1f can do:

```bash
cd /your/awesome/project
m1f-link  # Creates m1f/m1f.txt symlink
```

Boom! 💥 Now you've got the complete m1f documentation sitting in your project.
Claude can read this and instantly become an m1f expert.

### Step 2: Start the Conversation

Here's where it gets fun. Just tell Claude what you need:

```
Hey Claude, I need help setting up m1f for my project.
Check out @m1f/m1f.txt to see what m1f can do.

My project is a Python web app with:
- Backend API in /api
- Frontend React code in /frontend
- Tests scattered around
- Some docs in /docs

Can you create a .m1f.config.yml that bundles these intelligently?
```

Claude will read the docs and create a perfect config for your project
structure. No more guessing at parameters!

## Real-World Workflows That Actually Work 🚀

### The "Security-First Bundle" Workflow

```
Claude, I need to create bundles for external review.
Using m1f v3.2's security features:

1. Create a config that scans for secrets (security_check: error)
2. Exclude any files with sensitive data
3. Set up proper path validation
4. Ensure no internal IPs or credentials leak through

Focus on making it safe to share with contractors.
```

### The "Performance Optimization" Workflow

```
Claude, my project has 5000+ files and bundling is slow.
Help me optimize using m1f v3.2's features:

1. Leverage parallel processing (enabled by default)
2. Set up smart file size limits
3. Use content deduplication to reduce bundle size
4. Create targeted bundles instead of one massive file

The goal is sub-10 second bundle generation.
```

### The "Multi-Environment Setup" Workflow

```
Claude, I need different bundles for dev/staging/prod.
Using m1f v3.2's preset system:

1. Create environment-specific presets
2. Use conditional presets (enabled_if_exists)
3. Set different security levels per environment
4. Configure appropriate output formats

Make it so I can just run: m1f --preset env.yml --preset-group production
```

## Using m1f-claude: The Smart Assistant 🧠

We've supercharged Claude with m1f knowledge. Here's how to use it:

```bash
# Basic usage - Claude already knows about m1f!
m1f-claude "Bundle my Python project for code review"

# Interactive mode - have a conversation
m1f-claude -i
> Help me organize my WordPress theme files
> Now create a bundle for just the custom post types
> Can you exclude all the vendor files?
```

### What Makes m1f-claude Special?

When you use `m1f-claude`, it automatically:

- Knows where to find m1f documentation
- Understands your project structure
- Suggests optimal parameters
- Can execute commands directly (with your permission)

## Working with Claude Code

If you're using Claude Code (claude.ai/code), you can leverage its file reading
capabilities:

```
# In Claude Code, you can directly reference files
Claude, please read my current .m1f.config.yml and suggest improvements
based on m1f v3.2 features like:
- Better security scanning
- Optimized performance settings
- Advanced preset configurations
```

## Advanced v3.2 Patterns 🎯

### The "Complete Configuration via Presets"

With v3.2, you can control everything through presets:

```yaml
# production.m1f-presets.yml
production:
  description: "Production-ready bundles with full security"

  global_settings:
    # Input/Output
    source_directory: "./src"
    output_file: "dist/prod-bundle.txt"
    input_include_files: ["README.md", "LICENSE"]

    # Security (v3.2)
    security_check: "error" # Stop on any secrets

    # Performance (v3.2)
    enable_content_deduplication: true
    prefer_utf8_for_text_files: true

    # Output control
    add_timestamp: true
    create_archive: true
    archive_type: "tar.gz"
    force: true
    minimal_output: true
    quiet: true

    # Processing
    separator_style: "MachineReadable"
    encoding: "utf-8"
    max_file_size: "1MB"

    # Exclusions
    exclude_patterns:
      - "**/*.test.js"
      - "**/*.spec.ts"
      - "**/node_modules/**"
      - "**/.env*"

  presets:
    minify_production:
      patterns: ["dist/**/*"]
      extensions: [".js", ".css"]
      actions: ["minify", "strip_comments"]
```

### The "AI Context Optimization" Pattern

```yaml
bundles:
  ai-context:
    description: "Optimized for Claude and other LLMs"
    output: "m1f/ai-context.txt"
    sources:
      - path: "src"
        include_extensions: [".py", ".js", ".ts", ".jsx", ".tsx"]
        exclude_patterns:
          - "**/*.test.*"
          - "**/*.spec.*"
          - "**/test/**"

    # v3.2 optimizations
    global_settings:
      # Security first
      security_check: "warn"

      # Performance
      enable_content_deduplication: true # Reduce token usage

      # AI-friendly format
      separator_style: "Markdown"
      max_file_size: "100KB" # Keep context focused

      # Clean output
      remove_scraped_metadata: true
      allow_duplicate_files: false
```

### The "Encoding-Aware Bundle" Pattern

```yaml
bundles:
  legacy-code:
    description: "Handle mixed encoding legacy code"
    output: "m1f/legacy-bundle.txt"

    global_settings:
      # v3.2 encoding features
      prefer_utf8_for_text_files: false # Respect original encoding
      convert_to_charset: "utf-8" # But convert output
      abort_on_encoding_error: false # Continue on errors

      # Include everything
      include_binary_files: false
      include_dot_paths: true
```

## Pro Tips for Claude Interactions 💪

### 1. Let Claude Learn Your Project

First time? Let Claude explore:

```
Claude, analyze my project structure and suggest
how to organize it with m1f bundles. Consider:
- What files change together
- Logical groupings for different use cases
- Size limits for AI context windows

Use @m1f/m1f.txt to understand all available options.
```

### 2. Provide Clear Context

```
Claude, here's my project structure from m1f:
- Total files: 500
- Main languages: Python (60%), JavaScript (30%), Docs (10%)
- Special requirements: HIPAA compliance, no credential exposure
- Target use: Sharing with external auditors

Create a secure bundling strategy using m1f v3.2's security features.
Check @m1f/m1f.txt for security parameters.
```

### 3. Iterative Refinement

```
Claude, the bundle is too large (50MB). Help me:
1. Use content deduplication more aggressively
2. Set up file size limits
3. Create multiple smaller bundles by component
4. Exclude generated files and build artifacts
```

### 4. Preset Composition

```
Claude, I want layered presets:
1. base.yml - Company-wide standards
2. project.yml - Project-specific rules
3. personal.yml - My personal preferences

Show me how to use them together with proper override behavior.
```

## Security-First Workflows 🔒

### Preparing Code for Review

```
Claude, I need to share code with a contractor. Create a config that:
1. Runs strict security scanning (security_check: error)
2. Validates all file paths
3. Excludes .env files and secrets
4. Redacts any hardcoded credentials
5. Creates an audit trail

Use m1f v3.2's security features to make this bulletproof.
```

### Automated Security Checks

```
Claude, write a Git pre-commit hook that:
1. Runs m1f with security scanning
2. Blocks commits if secrets are found
3. Auto-generates safe bundles
4. Updates the m1f/ directory

Make it work with m1f v3.2's git hooks setup.
```

## Performance Optimization Strategies 🚀

### Large Codebase Handling

```
Claude, optimize m1f for our monorepo (10K+ files):

1. Set up smart exclusion patterns
2. Use size-based filtering
3. Create focused bundles per team
4. Leverage parallel processing
5. Implement caching strategies

Goal: Bundle generation under 30 seconds.
```

### Memory-Efficient Processing

```yaml
# Claude might suggest this for large files
large_files:
  description: "Handle massive log files"

  global_settings:
    max_file_size: "10MB" # Skip huge files
    enable_content_deduplication: true

  presets:
    truncate_logs:
      extensions: [".log", ".txt"]
      custom_processor: "truncate"
      processor_args:
        max_lines: 1000
        add_marker: true
```

## Troubleshooting with Claude 🔧

### Common Issues and Solutions

```
Claude, m1f is flagging false positives for secrets. Help me:
1. Configure security_check levels appropriately
2. Create patterns to exclude test fixtures
3. Set up per-file security overrides
4. Document why certain warnings are acceptable
```

### Performance Debugging

```
Claude, bundling takes 5 minutes. Analyze this verbose output
and suggest optimizations:
[paste m1f --verbose output]

Consider:
- File count and sizes
- Duplicate detection overhead
- Encoding detection delays
- Security scanning bottlenecks
```

## Integration Patterns 🔌

### CI/CD Integration

```
Claude, create a GitHub Action that:
1. Triggers on PR creation
2. Generates comparison bundles (before/after)
3. Posts bundle statistics as PR comment
4. Fails if bundle size increases >10%
5. Runs security scanning on changed files

Use m1f v3.2's features for efficiency.
```

### Documentation Automation

```
Claude, automate our documentation workflow:
1. Scrape our docs site weekly
2. Convert HTML to Markdown
3. Bundle by section with m1f
4. Remove outdated metadata
5. Create versioned archives

Leverage m1f's web scraping and processing features.
```

## Quick Reference Commands 🎪

Some powerful one-liners for common tasks:

```bash
# Give Claude m1f superpowers
m1f-link

# Quick m1f setup for your project
m1f-claude "Setup m1f for a typical Python project with tests and docs"

# Interactive Claude session
m1f-claude -i

# Security audit bundle
m1f -s . -o audit.txt --security-check error --minimal-output

# Fast development bundle (no security checks)
m1f -s ./src -o dev.txt --security-check skip

# Documentation bundle with metadata
m1f -s ./docs -o docs.txt --separator-style Detailed

# Clean bundle for AI consumption
m1f -s . -o ai-context.txt --allow-duplicate-files false

# Help me understand this codebase
m1f-claude "Create bundles to help a new developer understand this project"

# Prep for the AI apocalypse
m1f-claude "Optimize my project for AI assistants with proper context windows"
```

## Your Turn! 🎮

Now you're ready to turn Claude into your personal m1f expert. Remember:

1. Always start with `m1f-link` to give Claude the docs
2. Be specific about what you want to achieve
3. Let Claude suggest optimal configurations based on the documentation
4. Iterate and refine based on results
5. Test security settings thoroughly before sharing

The best part? Claude remembers your conversations, so it gets better at
understanding your project over time.

Happy bundling! 🚀

---

_P.S. - If Claude suggests something that seems off, just ask "Are you sure
about that? Check @m1f/m1f.txt again." Works every time! 😉_
