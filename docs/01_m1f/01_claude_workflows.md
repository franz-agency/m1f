# Claude + m1f: Your AI-Powered Project Assistant 🤖

Ever wished you had an AI buddy who actually understands your project structure? That's what happens when you combine Claude with m1f. This guide shows you how to turn Claude into your personal project assistant who knows exactly how to bundle, organize, and process your code.

## The Magic Setup ✨

### Step 1: Give Claude the Power

First, let's get Claude up to speed on what m1f can do:

```bash
cd /your/awesome/project
m1f-link  # Creates .m1f/m1f-docs.txt
```

Boom! 💥 Now you've got the complete m1f documentation sitting in your project. Claude can read this and instantly become an m1f expert.

### Step 2: Start the Conversation

Here's where it gets fun. Just tell Claude what you need:

```
Hey Claude, I need help setting up m1f for my project. 
Check out @.m1f/m1f-docs.txt to see what m1f can do.

My project is a Python web app with:
- Backend API in /api
- Frontend React code in /frontend  
- Tests scattered around
- Some docs in /docs

Can you create a .m1f.config.yml that bundles these intelligently?
```

Claude will read the docs and create a perfect config for your project structure. No more guessing at parameters!

## Real-World Workflows That Actually Work 🚀

### The "I Need Context for My AI" Workflow

```
Claude, I want to use Cursor/Windsurf to refactor my code.
Based on @.m1f/m1f-docs.txt, create bundles that give 
the AI perfect context without overwhelming it.

Focus on:
- Core business logic (not tests)
- Related config files
- Keep each bundle under 100KB for fast processing
```

### The "My Docs Are a Mess" Workflow

```
Claude, I scraped our docs site and now I have 500 HTML files.
Using @.m1f/m1f-docs.txt as reference:

1. Help me analyze the HTML structure
2. Create a preprocessing config to clean them up
3. Convert to clean Markdown
4. Bundle by topic for our new docs site

The HTML files are in ./scraped-docs/
```

### The "Deploy Day Documentation" Workflow

```
Claude, we're deploying tomorrow. I need you to:

1. Create a bundle with all deployment-related files
2. Include configs, scripts, and deployment docs
3. Exclude all test files and development configs
4. Make it readable for the ops team

Check @.m1f/m1f-docs.txt for the right parameters.
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

## Pro Tips from the Trenches 💪

### 1. Let Claude Learn Your Project

First time? Let Claude explore:

```
Claude, analyze my project structure and suggest 
how to organize it with m1f bundles. Consider:
- What files change together
- Logical groupings for different use cases
- Size limits for AI context windows

Use @.m1f/m1f-docs.txt to understand all available options.
```

### 2. Create Reusable Configs

```
Claude, based on our discussion, create a .m1f.config.yml
that I can commit to the repo. Include:
- Development bundles for coding
- Documentation bundles for writing
- Deployment bundles for ops
- AI context bundles for assistants
```

### 3. Automate the Boring Stuff

```
Claude, write a GitHub Action that:
1. Runs m1f-update on every push
2. Creates bundles for different purposes
3. Uploads them as artifacts
4. Comments on the PR with bundle stats

Here's what m1f can do: @.m1f/m1f-docs.txt
```

## Common Patterns That Just Work 🎯

### The "AI Context Special"

```yaml
# Claude will generate something like this
bundles:
  ai-context:
    description: "Optimized for AI assistants"
    output: ".m1f/ai-context.txt"
    sources:
      - path: "."
        include_extensions: [".py", ".js", ".md"]
        excludes: 
          - "**/test_*"
          - "**/node_modules/**"
          - "**/__pycache__/**"
    separator_style: "Markdown"  # Best for AI readability
    max_file_size: "100KB"       # Keep context focused
```

### The "Documentation Bundle"

```yaml
bundles:
  docs-all:
    description: "All documentation for new developers"
    output: ".m1f/docs-complete.txt"
    sources:
      - path: "."
        include_files: ["README.md", "CONTRIBUTING.md"]
      - path: "docs"
        include_extensions: [".md", ".rst"]
      - path: "examples"
        include_extensions: [".py", ".js"]
    separator_style: "Detailed"
```

### The "Code Review Bundle"

```yaml
bundles:
  pr-changes:
    description: "Changed files for PR review"
    output: ".m1f/pr-review.txt"
    sources:
      - path: "."
        include_files: ${CHANGED_FILES}  # From git diff
    filename_mtime_hash: true  # Track changes
```

## Troubleshooting Like a Pro 🔧

### "Claude doesn't understand my project"

Solution: Be specific about your stack:

```
Claude, this is a Django project with:
- Django 4.2
- PostgreSQL
- Redis for caching
- Celery for tasks

Given this stack and @.m1f/m1f-docs.txt, 
how should I bundle for deployment?
```

### "The bundles are too big"

Ask Claude to optimize:

```
Claude, my bundles are huge. Using @.m1f/m1f-docs.txt,
help me:
1. Split into smaller logical chunks
2. Use the preset system to process files
3. Exclude unnecessary files
4. Set appropriate size limits
```

### "I need different bundles for different teams"

Claude's got you:

```
Claude, create bundles for:
- Frontend team (React/TypeScript only)
- Backend team (Python/Django only)
- DevOps (configs/scripts only)
- QA team (tests/fixtures only)

Check @.m1f/m1f-docs.txt for the best approach.
```

## Advanced Wizardry 🧙‍♂️

### Custom Processing Rules

```
Claude, I need custom processing:
- Minify all CSS/JS in production bundles
- Strip comments from Python files
- Remove console.logs from JavaScript
- Keep markdown files pristine

Create a preset configuration based on @.m1f/m1f-docs.txt
```

### Dynamic Bundle Generation

```
Claude, write a Python script that:
1. Checks which modules changed
2. Creates targeted bundles for just those modules
3. Includes related tests and docs
4. Uses m1f's auto-bundle feature

Reference @.m1f/m1f-docs.txt for the API.
```

### Integration with Your Workflow

```
Claude, integrate m1f into our workflow:
1. Pre-commit hook for documentation bundles
2. CI/CD bundle generation
3. Automatic context for our AI coding assistant
4. Daily bundle reports via Slack

You know what m1f can do from @.m1f/m1f-docs.txt
```

## The One-Liner Wonders 🎪

Some quick commands that make life easier:

```bash
# "Just make it work for my Python project"
m1f-claude "Setup m1f for a typical Python project with tests and docs"

# "Help me understand this codebase"
m1f-claude "Create bundles to help a new developer understand this project"

# "Prep for the AI apocalypse"
m1f-claude "Optimize my project for AI assistants with proper context windows"

# "Friday afternoon deployment special"
m1f-claude "Bundle everything needed for production deployment, exclude the scary stuff"
```

## Your Turn! 🎮

Now you're ready to turn Claude into your personal m1f expert. Remember:

1. Always start with `m1f-link` to give Claude the docs
2. Be specific about what you want to achieve
3. Let Claude suggest optimal configurations
4. Iterate and refine based on results

The best part? Claude remembers your conversations, so it gets better at understanding your project over time.

Happy bundling! 🚀

---

*P.S. - If Claude suggests something that seems off, just ask "Are you sure about that? Check @.m1f/m1f-docs.txt again." Works every time! 😉*