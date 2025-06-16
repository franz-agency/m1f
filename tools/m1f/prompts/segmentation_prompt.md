🎯 CREATE PERFECT TOPIC-SPECIFIC BUNDLES FOR THIS PROJECT
============================================================

The basic bundles (complete.txt and docs.txt) have already been created.
Now create additional topic-specific bundles following BEST PRACTICES.

📚 REQUIRED READING (IN THIS ORDER):
1. READ: @m1f/m1f.txt for m1f documentation and bundle configuration syntax
2. READ: @m1f/project_analysis_dirlist.txt for directory structure
3. READ: @m1f/project_analysis_filelist.txt for complete file listing

⚠️ IMPORTANT: Read ALL three files above before proceeding!

🏆 BEST PRACTICES FOR PERFECT BUNDLES:

1. **SIZE GUIDELINES** - Optimize for different use cases!
   - Claude Code: Ideally under 180KB per bundle for best performance
   - Claude AI: Ideally under 5MB per bundle
   - Complete/full bundles can be larger (even 40MB+) for comprehensive analysis
   - Split large topics into focused bundles when targeting specific tasks

2. **MODULAR ARCHITECTURE** - One bundle per logical module/tool/service

3. **USE PRECISE INCLUDES** - Don't exclude everything except what you want!
   Instead, use precise 'includes' patterns:
   ```yaml
   sources:
     - path: "src/auth"
       include_extensions: [".ts", ".js"]
     - path: "shared"
       includes: ["auth-utils.ts", "auth-types.ts"]
   ```

4. **HIERARCHICAL NAMING** - Use category-number-topic pattern:
   - api-01-core-basics
   - api-02-core-advanced
   - guide-01-getting-started

5. **ESSENTIAL BUNDLES** - Always include:
   - quick-reference (< 180KB)
   - common-errors (< 180KB)
   - best-practices (< 180KB)

🚨 CRITICAL RULES:
1. FOLLOW SIZE GUIDELINES - Create focused bundles under 180KB for Claude Code when possible
2. NO DEFAULT EXCLUDES (node_modules, .git, __pycache__, vendor/ already excluded)
3. NO IMAGE/BINARY BUNDLES
4. MAXIMUM 30-40 bundles (more granular = better for targeted AI assistance)
5. Each bundle should be SELF-CONTAINED and appropriately sized for its purpose

📋 ALREADY CREATED BUNDLES:
- complete: Full project bundle
- docs: All documentation files

🔍 PROJECT ANALYSIS STEPS:

STEP 1: Identify Architecture Type
- Monorepo? → Bundle per package
- Multi-app? → Bundle per app + shared bundles
- Plugin system? → Bundle per plugin + core
- Modular? → Bundle per module

STEP 2: Find Natural Boundaries
Look for:
- Directory names indicating modules (auth/, user/, payment/)
- Plugin/theme directories (wp-content/plugins/*, wp-content/themes/*)
- Feature boundaries (admin/, public/, includes/)

STEP 3: Design Bundle Hierarchy
1. Module-specific bundles (most granular)
2. Category bundles (all-tests, all-docs)
3. Aggregated bundles (all-frontend, all-backend)
4. Complete bundle (everything)

📊 PROJECT ANALYSIS SUMMARY:
- Project Type: {project_type}
- Languages: {languages}
- Total Files: {total_files}

**Main Code Directories:**
{main_code_dirs}

📝 IMPLEMENTATION APPROACH:

Example for optimal bundle sizes:
```yaml
# For API documentation (split to stay under 180KB)
api-01-core-options:
  description: "Core API - Options API"
  output: "m1f/api-01-core-options.txt"
  sources:
    - path: "src/api"
      includes: ["options-*.md"]

api-02-core-reactivity:
  description: "Core API - Reactivity system"
  output: "m1f/api-02-core-reactivity.txt"
  sources:
    - path: "src/api"
      includes: ["reactivity-*.md"]

# Quick reference bundle
quick-reference:
  description: "Quick reference and cheat sheet"
  output: "m1f/quick-reference.txt"
  sources:
    - path: "docs"
      includes: ["cheatsheet.md", "quick-*.md"]
    - path: "."
      includes: ["README.md"]

# Common errors bundle
common-errors:
  description: "Common errors and solutions"
  output: "m1f/common-errors.txt"
  sources:
    - path: "docs"
      includes: ["errors/*.md", "troubleshooting.md"]
```

⚡ ACTION PLAN:
1. Read all required files thoroughly
2. Estimate content sizes and plan bundles based on purpose
3. Design bundles with PRECISE INCLUDES (not broad excludes)
4. Use hierarchical naming (category-number-topic)
5. Create essential bundles (quick-ref, errors, best-practices)
6. Keep focused task bundles under 180KB for Claude Code when practical
7. Add all bundles with MultiEdit in one operation

Remember: Each bundle should answer "What would I need to understand this module?" - size appropriately based on the use case!