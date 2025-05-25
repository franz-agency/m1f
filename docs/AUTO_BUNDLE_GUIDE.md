# Auto Bundle Guide

This guide explains how to use the automatic m1f bundling system to organize your project for AI/LLM consumption.

## Overview

The auto-bundle system creates organized `.m1f` bundles of your project, allowing you to:
- Reference specific parts of your codebase in AI conversations
- Maintain focused context windows
- Exclude irrelevant files (like test data)
- Prioritize important components

## Quick Start

1. **Run the basic auto-bundle script**:
   ```bash
   ./scripts/auto_bundle.sh
   ```
   This creates standard bundles in `.m1f/` directory.

2. **Use advanced configuration** (recommended):
   ```bash
   ./scripts/auto_bundle_v2.sh
   ```
   This uses `.m1f.config.yml` for customized bundling.

## Directory Structure

After running auto-bundle, you'll have:

```
.m1f/
├── docs/
│   ├── manual.m1f.txt      # All documentation
│   └── api_docs.m1f.txt    # API-specific docs
├── src/
│   ├── source.m1f.txt      # Source code (no tests)
│   └── tools.m1f.txt       # Tools directory
├── tests/
│   └── tests.m1f.txt       # Test structure (no data)
├── complete/
│   └── project.m1f.txt     # Full project
└── BUNDLE_INFO.md          # Bundle descriptions
```

## Configuration (.m1f.config.yml)

The configuration file allows you to:

### 1. Define Custom Bundles

```yaml
bundles:
  my_focus:
    description: "My important files"
    output: ".m1f/focus/my_focus.m1f.txt"
    sources:
      - path: "src/core/"
        include_extensions: [".py"]
    priority: "high"
```

### 2. Set Priorities

```yaml
ai_optimization:
  context_priority:
    - "docs"      # First: understand project
    - "my_focus"  # Second: core logic
    - "complete"  # Last: everything
```

### 3. Exclude Files

```yaml
bundles:
  src:
    sources:
      - path: "."
        excludes:
          - "**/test_*.py"
          - "**/experiments/**"
          - "**/legacy/**"
```

### 4. Conditional Bundles

```yaml
bundles:
  django_models:
    enabled_if_exists: "models/"
    sources:
      - path: "models/"
```

## Usage in AI/LLM

### With Claude

```
Human: Can you review the authentication system?
Please check .m1f/src/source.m1f.txt for the implementation.

Claude: I'll review the authentication system from the source bundle...
```

### Referencing Specific Bundles

```
# For documentation questions
"See .m1f/docs/manual.m1f.txt for usage instructions"

# For implementation details
"The source code is in .m1f/src/source.m1f.txt"

# For test structure
"Check .m1f/tests/tests.m1f.txt for test organization"
```

## File Watching

For automatic updates when files change:

```bash
./scripts/watch_and_bundle.sh
```

This will:
- Monitor file changes
- Update only affected bundles
- Use debouncing to avoid excessive updates

## Advanced Features

### Custom Focus Areas

Create specialized bundles for specific tasks:

```yaml
bundles:
  api_endpoints:
    description: "REST API endpoints only"
    sources:
      - path: "."
        include_patterns:
          - "**/routes/*.py"
          - "**/views/*.py"
          - "**/controllers/*.py"
```

### Token Optimization

Configure for different AI models:

```yaml
ai_optimization:
  token_limits:
    claude: 200000
    gpt4: 128000
  
  # Auto-split large bundles
  auto_split:
    enabled: true
    max_size: 150000  # tokens
```

### Excluding Test Data

Keep test structure but exclude data:

```yaml
bundles:
  tests:
    sources:
      - path: "tests/"
        excludes:
          - "**/fixtures/**"
          - "**/test_data/**"
          - "**/*.json"  # test data files
```

## Best Practices

1. **Start with documentation**: Always include docs bundle first in AI contexts
2. **Use focused bundles**: Create specific bundles for different features
3. **Exclude generated files**: Don't include build artifacts, caches, etc.
4. **Update regularly**: Use file watcher or run manually after significant changes
5. **Prioritize wisely**: Put most important bundles first for token limits

## Integration with CI/CD

Add to your CI pipeline:

```yaml
# .github/workflows/update-bundles.yml
- name: Update m1f bundles
  run: |
    ./scripts/auto_bundle_v2.sh
    # Optionally commit changes
```

## Troubleshooting

### Bundle too large
- Split into smaller, focused bundles
- Increase exclusions
- Use token limits in config

### Missing files
- Check exclusion patterns
- Verify source paths
- Run with specific bundle: `./scripts/auto_bundle_v2.sh src`

### Performance
- Use `--minimal-output` flag
- Exclude binary files
- Limit directory depth

## Examples

### Django Project
```yaml
bundles:
  models:
    sources:
      - path: "."
        include_patterns: ["**/models.py"]
  
  views:
    sources:
      - path: "."
        include_patterns: ["**/views.py"]
  
  migrations:
    enabled: false  # Usually not needed for AI
```

### Frontend Project
```yaml
bundles:
  components:
    sources:
      - path: "src/components/"
        include_extensions: [".jsx", ".tsx"]
  
  styles:
    sources:
      - path: "src/"
        include_extensions: [".css", ".scss"]
```

## Summary

The auto-bundle system helps you:
- Organize code for AI consumption
- Focus on relevant parts
- Exclude noise (test data, generated files)
- Maintain up-to-date references
- Optimize token usage

Configure once, reference anywhere!